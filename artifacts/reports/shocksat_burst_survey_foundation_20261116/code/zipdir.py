#!/usr/bin/env python3
"""Read a ZIP archive's table of contents from its last bytes only.

Why this exists: the NASA ShockSat archives are 0.5 to 8 GB each, and this project
must not store them whole. A ZIP file keeps its table of contents (the "central
directory") at the END of the file, so the last few megabytes are enough to list
every member with its exact size, checksum and byte position. With those byte
positions a single member can later be downloaded on its own with an HTTP Range
request (see zipfetch.py).

Terms (plain English):
- central directory: the table of contents at the end of a ZIP file.
- local header: a small record stored immediately before each member's data.
- CRC-32: a 32-bit checksum of the UNCOMPRESSED member, stored in the directory.
- ZIP64: the extension used when a size or offset does not fit in 32 bits.

Units: every offset and size is in bytes; offsets are absolute positions from the
first byte of the archive.

Reference: PKWARE APPNOTE.TXT "ZIP File Format Specification" sections 4.3.6-4.3.16
and 4.5.3 (ZIP64 extended information extra field).
"""
from __future__ import annotations

import dataclasses
import datetime as _dt
import struct
from typing import List, Optional

SIG_EOCD = b"PK\x05\x06"
SIG_Z64_LOCATOR = b"PK\x06\x07"
SIG_Z64_EOCD = b"PK\x06\x06"
SIG_CDH = b"PK\x01\x02"
SIG_LFH = b"PK\x03\x04"

LFH_FIXED = 30  # bytes in a local file header before the name
CDH_FIXED = 46  # bytes in a central directory header before the name


class ZipTailError(ValueError):
    """The supplied tail cannot be parsed as the end of a ZIP archive."""


@dataclasses.dataclass
class Entry:
    name: str
    method: int            # 0 = stored, 8 = deflate
    flags: int
    crc32: int
    csize: int             # compressed size, bytes
    usize: int             # uncompressed size, bytes
    lho: int               # absolute offset of the local file header
    name_len: int          # length of the name field in the CENTRAL header
    extra_len: int         # length of the extra field in the CENTRAL header
    dos_time: int
    dos_date: int
    is_dir: bool
    span_end: Optional[int] = None  # absolute offset where the next member (or the directory) starts

    @property
    def modified(self) -> str:
        d, t = self.dos_date, self.dos_time
        try:
            return _dt.datetime(((d >> 9) & 0x7F) + 1980, (d >> 5) & 0xF, d & 0x1F,
                                (t >> 11) & 0x1F, (t >> 5) & 0x3F, (t & 0x1F) * 2).isoformat()
        except ValueError:
            return ""

    @property
    def span(self) -> Optional[int]:
        """Bytes from this member's local header to the start of the next member."""
        return None if self.span_end is None else self.span_end - self.lho

    def to_json(self) -> dict:
        d = dataclasses.asdict(self)
        d["crc32"] = f"{self.crc32:08x}"
        d["modified"] = self.modified
        d["span"] = self.span
        for k in ("dos_time", "dos_date", "name_len", "extra_len", "flags"):
            d.pop(k)
        return d


@dataclasses.dataclass
class Directory:
    total_size: int        # size of the whole archive, bytes
    cd_offset: int         # absolute offset of the central directory
    cd_size: int           # central directory size, bytes
    n_entries: int
    zip64: bool
    entries: List[Entry]
    eocd_offset: int       # absolute offset of the end-of-central-directory record
    trailing_bytes: int    # bytes after the end-of-central-directory record and its comment

    def files(self) -> List[Entry]:
        return [e for e in self.entries if not e.is_dir]

    def find(self, name: str) -> Entry:
        for e in self.entries:
            if e.name == name:
                return e
        raise KeyError(name)


def _decode_name(raw: bytes, flags: int) -> str:
    return raw.decode("utf-8" if flags & 0x800 else "cp437", errors="replace")


def _zip64_extra(extra: bytes, usize: int, csize: int, lho: int):
    """Apply the ZIP64 extended-information field (header id 0x0001) if present."""
    i = 0
    while i + 4 <= len(extra):
        hid, hlen = struct.unpack_from("<HH", extra, i)
        body = extra[i + 4:i + 4 + hlen]
        if hid == 0x0001:
            j = 0
            if usize == 0xFFFFFFFF:
                usize = struct.unpack_from("<Q", body, j)[0]; j += 8
            if csize == 0xFFFFFFFF:
                csize = struct.unpack_from("<Q", body, j)[0]; j += 8
            if lho == 0xFFFFFFFF:
                lho = struct.unpack_from("<Q", body, j)[0]; j += 8
            break
        i += 4 + hlen
    return usize, csize, lho


def parse_tail(tail: bytes, total_size: int) -> Directory:
    """Parse the central directory from `tail`, the LAST len(tail) bytes of an archive
    whose full size is `total_size` bytes.

    Raises ZipTailError when the tail is too short to contain the whole directory;
    the message states how many trailing bytes are needed.
    """
    if len(tail) > total_size:
        raise ZipTailError("tail is longer than the stated archive size")
    base = total_size - len(tail)  # absolute offset of tail[0]

    # The end-of-central-directory record is the LAST one whose comment length
    # runs exactly to the end of the file (guards against the signature bytes
    # appearing by chance inside member data or a comment).
    pos = len(tail)
    eocd = -1
    while True:
        pos = tail.rfind(SIG_EOCD, 0, pos)
        if pos < 0:
            break
        if pos + 22 <= len(tail):
            clen = struct.unpack_from("<H", tail, pos + 20)[0]
            if pos + 22 + clen <= len(tail):
                eocd = pos
                trailing = len(tail) - (pos + 22 + clen)
                if trailing == 0:
                    break
        if pos == 0:
            break
    if eocd < 0:
        raise ZipTailError("no end-of-central-directory record in the supplied tail")
    clen = struct.unpack_from("<H", tail, eocd + 20)[0]
    trailing = len(tail) - (eocd + 22 + clen)

    (_, disk, cd_disk, n_disk, n_total, cd_size, cd_offset, _c) = struct.unpack_from("<4sHHHHIIH", tail, eocd)
    zip64 = False
    if eocd >= 20 and tail[eocd - 20:eocd - 16] == SIG_Z64_LOCATOR:
        _, _d, z64_off, _nd = struct.unpack_from("<4sIQI", tail, eocd - 20)
        rel = z64_off - base
        if rel < 0:
            raise ZipTailError(f"ZIP64 record starts {-rel} bytes before the supplied tail; "
                               f"need at least {total_size - z64_off} trailing bytes")
        if tail[rel:rel + 4] != SIG_Z64_EOCD:
            raise ZipTailError("ZIP64 locator does not point at a ZIP64 end record")
        (_, _sz, _vm, _vn, disk, cd_disk, n_disk, n_total, cd_size, cd_offset) = struct.unpack_from(
            "<4sQHHIIQQQQ", tail, rel)
        zip64 = True
    if disk != 0 or cd_disk != 0:
        raise ZipTailError("multi-disk archives are not supported")

    rel = cd_offset - base
    if rel < 0:
        raise ZipTailError(f"central directory starts {-rel} bytes before the supplied tail; "
                           f"need at least {total_size - cd_offset} trailing bytes")
    entries: List[Entry] = []
    p = rel
    end = rel + cd_size
    while p < end:
        if tail[p:p + 4] != SIG_CDH:
            raise ZipTailError(f"bad central header signature at directory byte {p - rel}")
        (_, _vm, _vn, flags, method, mtime, mdate, crc, csize, usize, nlen, elen, cmlen,
         _dsk, _ia, eattr, lho) = struct.unpack_from("<4sHHHHHHIIIHHHHHII", tail, p)
        name_raw = tail[p + CDH_FIXED:p + CDH_FIXED + nlen]
        extra = tail[p + CDH_FIXED + nlen:p + CDH_FIXED + nlen + elen]
        usize, csize, lho = _zip64_extra(extra, usize, csize, lho)
        name = _decode_name(name_raw, flags)
        entries.append(Entry(name=name, method=method, flags=flags, crc32=crc, csize=csize, usize=usize,
                             lho=lho, name_len=nlen, extra_len=elen, dos_time=mtime, dos_date=mdate,
                             is_dir=name.endswith("/")))
        p += CDH_FIXED + nlen + elen + cmlen
    if p != end:
        raise ZipTailError("central directory length does not match its headers")
    if len(entries) != n_total:
        raise ZipTailError(f"directory lists {len(entries)} entries but the end record says {n_total}")

    # span_end: where the next member starts in archive order (or the directory).
    order = sorted(range(len(entries)), key=lambda i: entries[i].lho)
    for a, b in zip(order, order[1:]):
        entries[a].span_end = entries[b].lho
    if order:
        entries[order[-1]].span_end = cd_offset
    return Directory(total_size=total_size, cd_offset=cd_offset, cd_size=cd_size, n_entries=n_total,
                     zip64=zip64, entries=entries, eocd_offset=base + eocd, trailing_bytes=trailing)


def consistency(d: Directory) -> dict:
    """Internal checks that need no member data.

    For every member the bytes between its local header and the next member must be
    at least 30 + name + compressed data, and the surplus (local extra field plus an
    optional 12 to 24 byte data descriptor) must be small. A failure means the
    directory and the archive layout disagree.
    """
    worst_surplus = 0
    bad = []
    for e in d.entries:
        need = LFH_FIXED + len(e.name.encode("utf-8" if e.flags & 0x800 else "cp437", errors="replace")) + e.csize
        surplus = e.span - need
        if surplus < 0 or surplus > 65535 + 24:
            bad.append({"name": e.name, "surplus": surplus})
        worst_surplus = max(worst_surplus, surplus)
    files = d.files()
    return {
        "n_entries": d.n_entries,
        "n_files": len(files),
        "sum_usize": sum(e.usize for e in files),
        "sum_csize": sum(e.csize for e in files),
        "cd_offset": d.cd_offset,
        "cd_size": d.cd_size,
        "total_size": d.total_size,
        "zip64": d.zip64,
        "eocd_plus_dir_reaches_eof": d.cd_offset + d.cd_size <= d.eocd_offset and d.trailing_bytes == 0,
        "first_member_at_zero": min((e.lho for e in d.entries), default=0) == 0,
        "max_span_surplus_bytes": worst_surplus,
        "layout_violations": bad,
    }


def infer_total_size(tail: bytes) -> int:
    """Best-effort archive size when only the tail is known and nothing follows the
    end record: size = directory offset + directory size + end records. Used only to
    cross-check a size obtained independently (for example an HTTP content-length)."""
    eocd = tail.rfind(SIG_EOCD)
    if eocd < 0:
        raise ZipTailError("no end-of-central-directory record")
    (_, _d, _cd, _n, _nt, cd_size, cd_offset, clen) = struct.unpack_from("<4sHHHHIIH", tail, eocd)
    if eocd >= 20 and tail[eocd - 20:eocd - 16] == SIG_Z64_LOCATOR:
        # ZIP64: the 20-byte locator sits immediately before the end record, so the end
        # record's absolute offset is the ZIP64 record offset + that record's length + 20.
        _, _dd, z64_off, _nd = struct.unpack_from("<4sIQI", tail, eocd - 20)
        z64_len = None
        for k in range(eocd - 20 - 56, -1, -1):  # search backwards for the ZIP64 end record
            if tail[k:k + 4] == SIG_Z64_EOCD:
                z64_len = struct.unpack_from("<Q", tail, k + 4)[0] + 12
                if k + z64_len == eocd - 20:
                    break
                z64_len = None
        if z64_len is None:
            raise ZipTailError("ZIP64 end record not found in the supplied tail")
        return z64_off + z64_len + 20 + 22 + clen
    return cd_offset + cd_size + 22 + clen
