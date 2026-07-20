#!/usr/bin/env python3
"""Parse the Femap/Simcenter Nastran deck `Test Stand FEA.dat` into structured arrays.

Fixed-width small-field (8-column) parser. Handles:
  - mixed CRLF / bare-CR line endings (normalized first; D18),
  - `+` continuation lines (PBEAM 3-line cards, MAT1, CORD2x),
  - Nastran shorthand floats: `2.9+7` -> 2.9e7, `7.324-4` -> 7.324e-4,
  - run-together fields (`58.38377-28.999921.36607` splits at 8-char boundaries).

FORCE/LOAD cards are counted and DROPPED (static thrust case, irrelevant; card rule).
Output: out/parsed_deck.json + out/parse_summary.json.

Units: inch-lbf-second (psi, lbf*s^2/in^4). Runner: FABLE, 2026-06-11.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
DECK = os.path.join(WS, "..", "..", "..", "MPL test stand", "FEM", "Test Stand FEA.dat")

SHORTHAND = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d+)$")


def nfloat(tok, default=0.0):
    """Convert a Nastran 8-char field to float (shorthand exponents supported)."""
    t = tok.strip()
    if not t:
        return default
    m = SHORTHAND.match(t)
    if m:
        t = m.group(1) + "e" + m.group(2)
    return float(t)


def nint(tok, default=0):
    t = tok.strip()
    return int(t) if t else default


def fields_of(line):
    """Data fields of a small-field line: cols 9-72 in 8-char chunks (field 1 = name)."""
    body = line[8:72]
    body = body + " " * (64 - len(body))
    return [body[i:i + 8] for i in range(0, 64, 8)]


def main():
    raw = open(DECK, "rb").read().decode("ascii")
    n_crlf = raw.count("\r\n")
    raw = raw.replace("\r\n", "\n")
    n_cr = raw.count("\r")  # bare CR remaining
    raw = raw.replace("\r", "\n")
    lines = raw.split("\n")

    # ---- gather logical cards in the bulk section ----
    in_bulk = False
    cards = []  # list of [name, fields...] ; continuations appended
    counts = {}
    for line in lines:
        if line.startswith("BEGIN BULK"):
            in_bulk = True
            continue
        if not in_bulk:
            continue
        if line.startswith("ENDDATA"):
            break
        if not line.strip() or line.startswith("$"):
            continue
        name = line[:8].strip()
        if line.startswith("PARAM"):
            cards.append(("PARAM", [p.strip() for p in line.split(",")[1:]]))
            counts["PARAM"] = counts.get("PARAM", 0) + 1
            continue
        if name.startswith("+"):
            # continuation of the previous card
            cards[-1][1].extend(fields_of(line))
            continue
        cards.append((name, fields_of(line)))
        counts[name] = counts.get(name, 0) + 1

    grids = {}          # id -> dict(cp, x, y, z, cd)
    cbeams = []         # eid, pid, ga, gb, v(3)
    pbeams = {}         # pid -> dict(mid, A, I1, I2, I12, J, NSM, K1, K2)
    cquads = []         # eid, pid, g1..g4
    pshells = {}        # pid -> dict(mid1, t, mid2, bend_ratio, mid3, ts_t, nsm)
    cbushes = []        # eid, pid, ga, gb, cid
    pbushes = {}        # pid -> [k1..k6]
    rbe2s = []          # eid, gn, cm, [gm...]
    mats = {}           # mid -> dict(E, G, nu, rho)
    spc1 = []           # (sid, comp, [grids])
    params = {}
    n_force = 0
    cord_ids = []

    for name, f in cards:
        if name == "GRID":
            gid = nint(f[0])
            grids[gid] = dict(cp=nint(f[1]), x=nfloat(f[2]), y=nfloat(f[3]),
                              z=nfloat(f[4]), cd=nint(f[5]))
        elif name == "CBEAM":
            cbeams.append(dict(eid=nint(f[0]), pid=nint(f[1]), ga=nint(f[2]),
                               gb=nint(f[3]),
                               v=[nfloat(f[4]), nfloat(f[5]), nfloat(f[6])]))
        elif name == "PBEAM":
            # base: PID MID A I1 I2 I12 J NSM | cont1: C1 C2 D1 D2 E1 E2 F1 F2
            # cont2: SO(YESA) X/XB | cont3: K1 K2 ...
            pid = nint(f[0])
            d = dict(mid=nint(f[1]), A=nfloat(f[2]), I1=nfloat(f[3]),
                     I2=nfloat(f[4]), I12=nfloat(f[5]), J=nfloat(f[6]),
                     nsm=nfloat(f[7]))
            # continuation layout (verified on this deck): fields 8..15 = stress pts,
            # 16..17 = SO/X-XB ('YESA', 1.0), 24..25 = K1, K2
            d["so"] = f[16].strip() if len(f) > 16 else ""
            d["K1"] = nfloat(f[24], 0.0) if len(f) > 24 else 0.0
            d["K2"] = nfloat(f[25], 0.0) if len(f) > 25 else 0.0
            d["stress_pts"] = [nfloat(f[i]) for i in range(8, 16)] if len(f) > 15 else []
            pbeams[pid] = d
        elif name == "CQUAD4":
            cquads.append(dict(eid=nint(f[0]), pid=nint(f[1]),
                               g=[nint(f[2]), nint(f[3]), nint(f[4]), nint(f[5])]))
        elif name == "PSHELL":
            pid = nint(f[0])
            pshells[pid] = dict(mid1=nint(f[1]), t=nfloat(f[2]), mid2=nint(f[3]),
                                bend_ratio=nfloat(f[4], 1.0), mid3=nint(f[5]),
                                ts_t=nfloat(f[6], 0.833333), nsm=nfloat(f[7]))
        elif name == "CBUSH":
            cbushes.append(dict(eid=nint(f[0]), pid=nint(f[1]), ga=nint(f[2]),
                                gb=nint(f[3]), cid=nint(f[7], -1)))
        elif name == "PBUSH":
            pid = nint(f[0])
            assert f[1].strip() == "K", f"PBUSH flag {f[1]!r} unsupported"
            pbushes[pid] = [nfloat(f[i]) for i in range(2, 8)]
        elif name == "RBE2":
            eid, gn, cm = nint(f[0]), nint(f[1]), nint(f[2])
            gms = [nint(t) for t in f[3:] if t.strip()]
            rbe2s.append(dict(eid=eid, gn=gn, cm=cm, gm=gms))
        elif name == "MAT1":
            mid = nint(f[0])
            E = nfloat(f[1])
            G = nfloat(f[2], 0.0)
            nu = nfloat(f[3], 0.0)
            if G == 0.0:
                G = E / (2.0 * (1.0 + nu))
            mats[mid] = dict(E=E, G=G, nu=nu, rho=nfloat(f[4]))
        elif name == "SPC1":
            sid, comp = nint(f[0]), f[1].strip()
            gs = [nint(t) for t in f[2:] if t.strip()]
            spc1.append(dict(sid=sid, comp=comp, grids=gs))
        elif name in ("CORD2C", "CORD2S"):
            cord_ids.append(nint(f[0]))
        elif name == "FORCE":
            n_force += 1
        elif name == "PARAM":
            params[f[0]] = f[1] if len(f) > 1 else None
        # MAT4 (thermal) and everything else: ignored on purpose

    # ---- verification facts ----
    cp_vals = sorted({g["cp"] for g in grids.values()})
    cd_vals = sorted({g["cd"] for g in grids.values()})
    cords_referenced = any(c in cp_vals or c in cd_vals for c in cord_ids)
    # distinct beam sections
    sec_keys = {}
    for pid, d in pbeams.items():
        key = (round(d["A"], 6), round(d["I1"], 6), round(d["I2"], 6), round(d["J"], 6))
        sec_keys.setdefault(key, []).append(pid)
    # RBE2 dependent-grid duplicates?
    dep_all = [g for r in rbe2s for g in r["gm"]]
    dep_dupes = sorted({g for g in dep_all if dep_all.count(g) > 1})

    out = dict(grids=grids, cbeams=cbeams, pbeams=pbeams, cquads=cquads,
               pshells=pshells, cbushes=cbushes, pbushes=pbushes, rbe2s=rbe2s,
               mats=mats, spc1=spc1, params=params)
    os.makedirs(os.path.join(WS, "out"), exist_ok=True)
    with open(os.path.join(WS, "out", "parsed_deck.json"), "w") as fh:
        json.dump(out, fh)

    xs = [g["x"] for g in grids.values()]
    ys = [g["y"] for g in grids.values()]
    zs = [g["z"] for g in grids.values()]
    summary = dict(
        deck=os.path.relpath(os.path.abspath(DECK), os.path.abspath(WS)),
        line_endings=dict(crlf=n_crlf, bare_cr=n_cr),
        counts=dict(GRID=len(grids), CBEAM=len(cbeams), PBEAM=len(pbeams),
                    CQUAD4=len(cquads), PSHELL=len(pshells), CBUSH=len(cbushes),
                    PBUSH=len(pbushes), RBE2=len(rbe2s), MAT1=len(mats),
                    SPC1=len(spc1), FORCE_dropped=n_force),
        expected=dict(GRID=1415, CBEAM=1288, PBEAM=37, CQUAD4=72, PSHELL=1,
                      CBUSH=70, PBUSH=1, RBE2=39, MAT1=1, SPC1=4),
        grid_cp_values=cp_vals, grid_cd_values=cd_vals,
        cord_ids_defined=cord_ids, cords_referenced_by_grids=bool(cords_referenced),
        distinct_beam_sections={str(k): v for k, v in sec_keys.items()},
        n_distinct_beam_sections=len(sec_keys),
        rbe2_duplicate_dependents=dep_dupes,
        spc_grids=sorted({g for s in spc1 for g in s["grids"]}),
        bbox=dict(x=[min(xs), max(xs)], y=[min(ys), max(ys)], z=[min(zs), max(zs)]),
        params=params,
        mat1=mats,
        pshell=pshells,
        pbush=pbushes,
        units="inch-lbf-second (E psi, rho lbf*s^2/in^4, lengths in)",
    )
    with open(os.path.join(WS, "out", "parse_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)

    ok = all(summary["counts"].get(k) == v for k, v in summary["expected"].items())
    print(json.dumps({k: summary[k] for k in
                      ("counts", "n_distinct_beam_sections", "grid_cp_values",
                       "grid_cd_values", "cords_referenced_by_grids",
                       "rbe2_duplicate_dependents", "bbox", "spc_grids")}, indent=1))
    print("COUNTS MATCH EXPECTED:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
