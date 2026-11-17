#!/usr/bin/env python3
"""Download single members of a remote ZIP archive with HTTP Range requests.

Nothing but the requested members is ever written to disk. Each member is read as a
stream, decompressed on the fly, and verified against the CRC-32 checksum and the
uncompressed size recorded in the archive's central directory, so a wrong or
truncated transfer cannot pass silently.

Command line:
  zipfetch.py list  URL [--match REGEX] [--json OUT]
  zipfetch.py plan  URL --match REGEX --json OUT
  zipfetch.py fetch URL --match REGEX --dest DIR [--max-bytes N]
  zipfetch.py probe URL            (headers only: reachable? size? Range support?)

Exit codes: 0 success; 2 host unreachable or refused (for example a network policy
denial); 3 integrity failure; 4 usage or archive-format error.

Units: bytes for all sizes and offsets.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import time
import zlib
from typing import Iterator, List, Optional

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zipdir  # noqa: E402

UA = "zipfetch/1.0 (python-requests)"
CHUNK = 1 << 20


class Unreachable(RuntimeError):
    pass


class IntegrityError(RuntimeError):
    pass


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    s.headers["Accept-Encoding"] = "identity"  # never let a proxy re-encode ranged bytes
    return s


def probe(url: str, session: Optional[requests.Session] = None, timeout: float = 60.0) -> dict:
    """Headers-only request. Returns status, size, and whether byte ranges are offered."""
    s = session or _session()
    try:
        r = s.head(url, allow_redirects=True, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        raise Unreachable(f"{type(exc).__name__}: {exc}") from exc
    out = {
        "url": url,
        "final_url": r.url,
        "status": r.status_code,
        "content_length": int(r.headers["Content-Length"]) if "Content-Length" in r.headers else None,
        "accept_ranges": r.headers.get("Accept-Ranges"),
        "etag": r.headers.get("ETag"),
        "last_modified": r.headers.get("Last-Modified"),
    }
    if r.status_code >= 400:
        raise Unreachable(f"HTTP {r.status_code} for {url}")
    return out


def get_range(url: str, start: int, end: int, session: Optional[requests.Session] = None,
              timeout: float = 120.0, retries: int = 4) -> Iterator[bytes]:
    """Yield bytes [start, end] inclusive. Resumes from the last received byte after a
    dropped connection, and refuses a server that ignores the Range header."""
    s = session or _session()
    pos = start
    attempt = 0
    while pos <= end:
        try:
            with s.get(url, headers={"Range": f"bytes={pos}-{end}"}, stream=True,
                       timeout=timeout, allow_redirects=True) as r:
                if r.status_code == 200:
                    raise IntegrityError("server ignored the Range header (HTTP 200); refusing a full download")
                if r.status_code != 206:
                    raise Unreachable(f"HTTP {r.status_code} for range {pos}-{end}")
                cr = r.headers.get("Content-Range", "")
                m = re.match(r"bytes (\d+)-(\d+)/(\d+|\*)", cr)
                if not m or int(m.group(1)) != pos:
                    raise IntegrityError(f"unexpected Content-Range {cr!r} for requested start {pos}")
                for chunk in r.iter_content(CHUNK):
                    if not chunk:
                        continue
                    if pos + len(chunk) - 1 > end:
                        chunk = chunk[: end - pos + 1]
                    pos += len(chunk)
                    yield chunk
            attempt = 0
        except requests.exceptions.ProxyError as exc:
            # A proxy refusal is a network-policy decision, not a transient fault: never retry it.
            raise Unreachable(f"proxy refused the connection: {exc}") from exc
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout) as exc:
            attempt += 1
            if attempt > retries:
                raise Unreachable(f"gave up after {retries} retries at byte {pos}: {exc}") from exc
            time.sleep(2 ** attempt)


def read_range(url: str, start: int, end: int, session=None) -> bytes:
    return b"".join(get_range(url, start, end, session))


def open_directory(url: str, session=None, tail_bytes: int = 1 << 20) -> zipdir.Directory:
    """Read the table of contents with one or two ranged requests."""
    s = session or _session()
    info = probe(url, s)
    size = info["content_length"]
    if size is None:
        raise Unreachable("server did not report a content length")
    n = min(tail_bytes, size)
    while True:
        tail = read_range(url, size - n, size - 1, s)
        try:
            return zipdir.parse_tail(tail, size)
        except zipdir.ZipTailError as exc:
            m = re.search(r"need at least (\d+) trailing bytes", str(exc))
            if not m or int(m.group(1)) <= n:
                raise
            n = min(size, int(m.group(1)) + 64)


def member_data_range(url: str, e: zipdir.Entry, session=None) -> tuple:
    """Locate the first and last byte of a member's compressed data by reading its
    local header (the local extra field can differ in length from the directory's)."""
    head = read_range(url, e.lho, e.lho + zipdir.LFH_FIXED - 1, session)
    if head[:4] != zipdir.SIG_LFH:
        raise IntegrityError(f"no local header at byte {e.lho} for {e.name}")
    (_, _vn, _fl, method, _t, _d, _crc, _cs, _us, nlen, elen) = struct.unpack("<4sHHHHHIIIHH", head)
    if method != e.method:
        raise IntegrityError(f"method mismatch for {e.name}: local {method}, directory {e.method}")
    start = e.lho + zipdir.LFH_FIXED + nlen + elen
    return start, start + e.csize - 1


def fetch_member(url: str, e: zipdir.Entry, dest_path: str, session=None) -> dict:
    """Stream one member to dest_path, verifying size and CRC-32."""
    if e.method not in (0, 8):
        raise IntegrityError(f"unsupported compression method {e.method} for {e.name}")
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    t0 = time.time()
    crc = 0
    n_out = 0
    n_in = 0
    tmp = dest_path + ".part"
    with open(tmp, "wb") as fh:
        if e.csize > 0:
            start, end = member_data_range(url, e, session)
            dec = zlib.decompressobj(-15) if e.method == 8 else None
            for chunk in get_range(url, start, end, session):
                n_in += len(chunk)
                out = dec.decompress(chunk) if dec else chunk
                if out:
                    crc = zlib.crc32(out, crc)
                    n_out += len(out)
                    fh.write(out)
            if dec:
                out = dec.flush()
                if out:
                    crc = zlib.crc32(out, crc)
                    n_out += len(out)
                    fh.write(out)
    ok = (n_out == e.usize) and ((crc & 0xFFFFFFFF) == e.crc32) and (n_in == e.csize)
    if not ok:
        os.remove(tmp)
        raise IntegrityError(f"{e.name}: got {n_out} bytes crc {crc & 0xFFFFFFFF:08x}, "
                             f"expected {e.usize} bytes crc {e.crc32:08x}")
    os.replace(tmp, dest_path)
    return {"name": e.name, "bytes_in": n_in, "bytes_out": n_out, "crc32": f"{e.crc32:08x}",
            "seconds": round(time.time() - t0, 3), "dest": dest_path}


def select(d: zipdir.Directory, pattern: str) -> List[zipdir.Entry]:
    rx = re.compile(pattern)
    return [e for e in d.files() if rx.search(e.name)]


def plan(d: zipdir.Directory, entries: List[zipdir.Entry]) -> dict:
    """Summarise what a fetch would transfer, and whether the members are contiguous."""
    es = sorted(entries, key=lambda e: e.lho)
    runs = []
    for e in es:
        if runs and runs[-1][1] == e.lho:
            runs[-1][1] = e.span_end
        else:
            runs.append([e.lho, e.span_end])
    return {
        "archive_size": d.total_size,
        "n_members": len(es),
        "compressed_bytes": sum(e.csize for e in es),
        "uncompressed_bytes": sum(e.usize for e in es),
        "contiguous_runs": [{"start": a, "end_exclusive": b, "bytes": b - a} for a, b in runs],
        "members": [e.to_json() for e in es],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("probe", "list", "plan", "fetch"):
        p = sub.add_parser(name)
        p.add_argument("url")
        if name != "probe":
            p.add_argument("--match", default=".")
            p.add_argument("--json")
        if name == "fetch":
            p.add_argument("--dest", required=True)
            p.add_argument("--max-bytes", type=int, default=None,
                           help="refuse to start if the selected uncompressed total exceeds this")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "probe":
            print(json.dumps(probe(a.url), indent=1))
            return 0
        s = _session()
        d = open_directory(a.url, s)
        es = select(d, a.match)
        pl = plan(d, es)
        if a.cmd in ("list", "plan"):
            if a.json:
                with open(a.json, "w") as fh:
                    json.dump(pl, fh, indent=1)
            for e in sorted(es, key=lambda e: e.lho):
                print(f"{e.usize:>13} {e.csize:>13} {e.lho:>13}  {e.name}")
            print(f"# {pl['n_members']} members, {pl['compressed_bytes']} compressed bytes, "
                  f"{pl['uncompressed_bytes']} uncompressed bytes, {len(pl['contiguous_runs'])} contiguous run(s)")
            return 0
        if a.max_bytes is not None and pl["uncompressed_bytes"] > a.max_bytes:
            print(f"refusing: selection is {pl['uncompressed_bytes']} bytes > --max-bytes {a.max_bytes}", file=sys.stderr)
            return 4
        log = []
        for e in sorted(es, key=lambda e: e.lho):
            dest = os.path.join(a.dest, e.name)
            if os.path.exists(dest) and os.path.getsize(dest) == e.usize:
                with open(dest, "rb") as fh:
                    c = 0
                    for blk in iter(lambda: fh.read(CHUNK), b""):
                        c = zlib.crc32(blk, c)
                if (c & 0xFFFFFFFF) == e.crc32:
                    log.append({"name": e.name, "skipped": "already present and verified"})
                    continue
            log.append(fetch_member(a.url, e, dest, s))
            print(json.dumps(log[-1]))
        if a.json:
            with open(a.json, "w") as fh:
                json.dump({"plan": pl, "log": log}, fh, indent=1)
        return 0
    except Unreachable as exc:
        print(f"UNREACHABLE: {exc}", file=sys.stderr)
        return 2
    except IntegrityError as exc:
        print(f"INTEGRITY: {exc}", file=sys.stderr)
        return 3
    except zipdir.ZipTailError as exc:
        print(f"FORMAT: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(main())
