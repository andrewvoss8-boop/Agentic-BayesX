#!/usr/bin/env python3
"""Known-answer tests for zipdir.py and zipfetch.py.

Run:  python3 test_zip_tools.py            (offline tests only)
      python3 test_zip_tools.py --network  (adds one real ranged download from PyPI)

Every test compares against Python's standard zipfile module, which serves as the
independent reference implementation.
"""
import hashlib
import http.server
import io
import json
import os
import random
import re
import socketserver
import sys
import tempfile
import threading
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zipdir      # noqa: E402
import zipfetch    # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append({"test": name, "pass": bool(cond), "detail": str(detail)[:300]})
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def build_zip(path):
    rnd = random.Random(20261116)
    members = {
        "a/stored.bin": bytes(rnd.getrandbits(8) for _ in range(70_001)),
        "a/deflated_text.txt": (b"burst random survey " * 40_000),
        "a/deflated_random.bin": bytes(rnd.getrandbits(8) for _ in range(300_003)),
        "a/empty.dat": b"",
        "a/b/Modéle_φ.txt": "mode shape φ".encode("utf-8") * 100,
    }
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("a/"), b"")
        zf.writestr("a/stored.bin", members["a/stored.bin"], compress_type=zipfile.ZIP_STORED)
        zf.writestr("a/deflated_text.txt", members["a/deflated_text.txt"], compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("a/deflated_random.bin", members["a/deflated_random.bin"], compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("a/empty.dat", b"")
        zf.writestr("a/b/Modéle_φ.txt", members["a/b/Modéle_φ.txt"], compress_type=zipfile.ZIP_DEFLATED)
        # streamed member: written with a trailing data descriptor (flag bit 3)
        data = bytes(rnd.getrandbits(8) for _ in range(123_457)) + b"x" * 50_000
        zi = zipfile.ZipInfo("a/streamed_descriptor.bin"); zi.compress_type = zipfile.ZIP_DEFLATED
        with zf.open(zi, "w") as fh:
            fh.write(data)
        members["a/streamed_descriptor.bin"] = data
        # member whose headers carry ZIP64 extra fields although it is small
        data = b"zip64 " * 20_000
        zi = zipfile.ZipInfo("a/forced_zip64.bin"); zi.compress_type = zipfile.ZIP_DEFLATED
        with zf.open(zi, "w", force_zip64=True) as fh:
            fh.write(data)
        members["a/forced_zip64.bin"] = data
    return members


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    """Static file server with single-range support; '/norange/...' ignores Range."""
    def log_message(self, *a):
        pass

    def do_HEAD(self):
        self._serve(head=True)

    def do_GET(self):
        self._serve(head=False)

    def _serve(self, head):
        ignore = self.path.startswith("/norange/")
        rel = self.path[len("/norange"):] if ignore else self.path
        fp = os.path.join(self.directory, rel.lstrip("/"))
        if not os.path.isfile(fp):
            self.send_error(404); return
        size = os.path.getsize(fp)
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d+)-(\d*)", rng or "")
        with open(fp, "rb") as fh:
            if m and not ignore:
                a = int(m.group(1)); b = int(m.group(2)) if m.group(2) else size - 1
                b = min(b, size - 1)
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
                self.send_header("Content-Length", str(b - a + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                if not head:
                    fh.seek(a); self.wfile.write(fh.read(b - a + 1))
            else:
                self.send_response(200)
                self.send_header("Content-Length", str(size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                if not head:
                    self.wfile.write(fh.read())


def serve(directory):
    handler = lambda *a, **k: RangeHandler(*a, directory=directory, **k)  # noqa: E731
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def offline_tests():
    tmp = tempfile.mkdtemp(prefix="ziptest_")
    zp = os.path.join(tmp, "t.zip")
    members = build_zip(zp)
    raw = open(zp, "rb").read()
    size = len(raw)
    ref = {i.filename: i for i in zipfile.ZipFile(zp).infolist()}

    # 1. a tail that is too short reports how many bytes are needed
    try:
        zipdir.parse_tail(raw[-60:], size); short_ok = False; need = None
    except zipdir.ZipTailError as exc:
        m = re.search(r"need at least (\d+) trailing bytes", str(exc)); short_ok = bool(m); need = int(m.group(1)) if m else None
    check("short tail asks for a specific number of bytes", short_ok, need)
    d = zipdir.parse_tail(raw[-(need + 8):], size)
    check("directory parsed from the minimum tail", d.n_entries == len(ref), (d.n_entries, len(ref)))

    # 2. every field agrees with zipfile
    ok = True; why = ""
    for e in d.entries:
        r = ref.get(e.name)
        if r is None or (e.crc32, e.csize, e.usize, e.lho, e.method) != (r.CRC, r.compress_size, r.file_size, r.header_offset, r.compress_type):
            ok = False; why = e.name; break
    check("names, CRC, sizes, offsets and methods match zipfile for all entries", ok, why)
    check("non-ASCII name decoded", any("φ" in e.name for e in d.entries))
    c = zipdir.consistency(d)
    check("layout consistency has no violations", not c["layout_violations"] and c["eocd_plus_dir_reaches_eof"] and c["first_member_at_zero"], c)
    check("archive size inferred from the tail equals the true size", zipdir.infer_total_size(raw[-(need + 8):]) == size)

    # 3. spans tile the archive exactly: no gaps, no overlaps, ends at the directory
    es = sorted(d.entries, key=lambda e: e.lho)
    tiles = es[0].lho == 0 and all(a.span_end == b.lho for a, b in zip(es, es[1:])) and es[-1].span_end == d.cd_offset
    check("member spans tile [0, directory offset) exactly", tiles)

    # 4. ranged fetch over HTTP reproduces every member byte for byte
    srv, port = serve(tmp)
    url = f"http://127.0.0.1:{port}/t.zip"
    info = zipfetch.probe(url)
    check("probe reports size and range support", info["content_length"] == size and info["accept_ranges"] == "bytes", info)
    d2 = zipfetch.open_directory(url, tail_bytes=64)   # forces the grow-the-tail path
    check("remote directory equals local directory", [e.to_json() for e in d2.entries] == [e.to_json() for e in d.entries])
    out = os.path.join(tmp, "out"); all_ok = True; bad = ""
    for e in d2.files():
        rec = zipfetch.fetch_member(url, e, os.path.join(out, e.name))
        got = open(rec["dest"], "rb").read()
        if got != members[e.name]:
            all_ok = False; bad = e.name
    check("all members fetched by byte range are byte-identical to the originals", all_ok, bad)
    pl = zipfetch.plan(d2, zipfetch.select(d2, r"^a/(stored|deflated_text)"))
    check("plan merges adjacent members into one contiguous run", len(pl["contiguous_runs"]) == 1 and pl["n_members"] == 2, pl["contiguous_runs"])

    # 5. a server that ignores Range must be refused, not silently downloaded whole
    try:
        zipfetch.read_range(f"http://127.0.0.1:{port}/norange/t.zip", 10, 20); refused = False
    except zipfetch.IntegrityError:
        refused = True
    check("server that ignores Range is refused", refused)

    # 6. corrupted member data fails the CRC check and leaves no file behind
    bad_raw = bytearray(raw)
    e = d.find("a/stored.bin")
    bad_raw[e.lho + 30 + len(e.name) + 5] ^= 0xFF
    open(os.path.join(tmp, "bad.zip"), "wb").write(bad_raw)
    dest = os.path.join(tmp, "bad_out", "stored.bin")
    try:
        zipfetch.fetch_member(f"http://127.0.0.1:{port}/bad.zip", e, dest); caught = False
    except zipfetch.IntegrityError:
        caught = True
    check("corrupted bytes fail the CRC check", caught and not os.path.exists(dest) and not os.path.exists(dest + ".part"))

    # 6b. archive written to an UNSEEKABLE stream: zipfile then sets flag bit 3 and writes a
    # data descriptor after each member, and the local header carries zero sizes. The fetcher
    # must rely on the central directory, not on the local header.
    class Unseekable(io.RawIOBase):
        def __init__(self, fh): self.fh = fh; self.n = 0
        def writable(self): return True
        def seekable(self): return False
        def write(self, b): self.n += len(b); return self.fh.write(b)
        def tell(self): return self.n
    sp = os.path.join(tmp, "stream.zip")
    payload = {"s/one.bin": os.urandom(50_000) + b"y" * 30_000, "s/two.txt": b"descriptor " * 9_000}
    with open(sp, "wb") as raw_fh:
        with zipfile.ZipFile(Unseekable(raw_fh), "w", zipfile.ZIP_DEFLATED) as zf:
            for k, v in payload.items():
                zf.writestr(k, v)
    sraw = open(sp, "rb").read()
    ds = zipdir.parse_tail(sraw[-4096:], len(sraw))
    surplus = [e.span - 30 - len(e.name.encode()) - e.csize for e in ds.entries]
    check("streamed archive sets the data-descriptor flag on every member", all(e.flags & 0x8 for e in ds.entries), [e.flags for e in ds.entries])
    check("data-descriptor surplus is 12 to 24 bytes per member", all(12 <= x <= 24 for x in surplus), surplus)
    okd = True
    for e in ds.files():
        rec = zipfetch.fetch_member(f"http://127.0.0.1:{port}/stream.zip", e, os.path.join(tmp, "sout", e.name))
        okd = okd and open(rec["dest"], "rb").read() == payload[e.name]
    check("members of a data-descriptor archive fetch byte-identically", okd)

    # 7. unreachable host maps to the dedicated exit code
    rc = zipfetch.main(["probe", "http://127.0.0.1:9/none.zip"])
    check("unreachable host returns exit code 2", rc == 2, rc)
    srv.shutdown()


def network_test():
    """One real-world ranged download: a wheel on PyPI is a ZIP served with Range support."""
    import requests
    meta = requests.get("https://pypi.org/pypi/six/1.16.0/json", timeout=60).json()
    w = [u for u in meta["urls"] if u["filename"].endswith(".whl")][0]
    url = w["url"]
    d = zipfetch.open_directory(url, tail_bytes=4096)
    full = requests.get(url, timeout=120).content
    check("PyPI: sha256 of the full wheel matches the index", hashlib.sha256(full).hexdigest() == w["digests"]["sha256"])
    zf = zipfile.ZipFile(io.BytesIO(full))
    ref = {i.filename: i for i in zf.infolist()}
    ok = len(ref) == d.n_entries and all((e.crc32, e.usize, e.lho) == (ref[e.name].CRC, ref[e.name].file_size, ref[e.name].header_offset) for e in d.entries)
    check("PyPI: directory read by Range equals zipfile on the full download", ok, (len(ref), d.n_entries))
    tmp = tempfile.mkdtemp(prefix="zipnet_")
    e = max(d.files(), key=lambda x: x.usize)
    rec = zipfetch.fetch_member(url, e, os.path.join(tmp, e.name))
    check("PyPI: largest member fetched by Range is byte-identical", open(rec["dest"], "rb").read() == zf.read(e.name), e.name)
    RESULTS.append({"network_target": url, "member": e.name, "member_bytes": e.usize, "archive_bytes": d.total_size})


if __name__ == "__main__":
    offline_tests()
    if "--network" in sys.argv:
        network_test()
    n_fail = sum(1 for r in RESULTS if r.get("pass") is False)
    out = {"n_tests": sum(1 for r in RESULTS if "pass" in r), "n_fail": n_fail, "results": RESULTS}
    dest = os.path.join(HERE, "..", "qa", "zip_tools_unit.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(out, open(dest, "w"), indent=1)
    print(f"{out['n_tests']} tests, {n_fail} failed -> qa/zip_tools_unit.json")
    sys.exit(1 if n_fail else 0)
