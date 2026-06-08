#!/usr/bin/env python3
"""litfetch -- resolve, search, fetch, and read OPEN-ACCESS papers from the shell.

No admin rights, no browser extension. Uses free scholarly APIs:
  - Crossref / OpenAlex  : metadata + full-text *search* (no key)
  - Unpaywall / arXiv    : locate a legal OPEN-ACCESS PDF
  - PyMuPDF (fitz) or pypdf : extract text from the downloaded PDF

It will only download files that are actually PDFs and only OA copies that
Unpaywall/arXiv/OpenAlex expose. Paywalled full text is NOT fetched.

Usage:
  python3 scripts/litfetch.py doi 10.1073/pnas.2015006118       # verified metadata
  python3 scripts/litfetch.py search "statfem kalman filter" --rows 6
  python3 scripts/litfetch.py fetch 10.1073/pnas.2015006118     # metadata + OA PDF + text

PDFs -> references/pdfs/<slug>.pdf ; extracted text -> references/pdfs/<slug>.txt
"""
import sys, json, os, re, argparse, urllib.request, urllib.parse

EMAIL = "andrewvoss8@gmail.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFDIR = os.path.join(ROOT, "references", "pdfs")
HDRS = {"User-Agent": f"AgenticBayesX-litfetch/1.0 (mailto:{EMAIL})"}


def _get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=timeout)


def _json(url, timeout=30):
    with _get(url, timeout) as r:
        return json.load(r)


def crossref(doi):
    it = _json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto={EMAIL}")["message"]
    au = "; ".join((a.get("family", "") + ", " + a.get("given", "")) for a in it.get("author", [])[:10])
    yr = (it.get("issued", {}).get("date-parts", [[None]])[0] or [None])[0]
    return {"title": (it.get("title") or [""])[0], "authors": au, "year": yr,
            "venue": (it.get("container-title") or [""])[0], "doi": it.get("DOI", ""),
            "url": it.get("URL", "")}


def search(query, rows=6):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {"search": query, "per-page": rows, "mailto": EMAIL})
    out = []
    for w in _json(url).get("results", []):
        loc = w.get("best_oa_location") or {}
        out.append({
            "title": w.get("title", "") or "",
            "year": w.get("publication_year"),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or "",
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "oa_pdf": loc.get("pdf_url") or (w.get("open_access") or {}).get("oa_url"),
            "authors": "; ".join(a["author"]["display_name"] for a in (w.get("authorships") or [])[:8]),
        })
    return out


def oa_candidates(doi):
    """Return an ordered list of candidate OA PDF URLs (best first), from
    Unpaywall (all locations) then a Europe PMC fallback. Direct PDFs preferred."""
    cands = []
    try:
        d = _json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={EMAIL}")
        locs = ([d.get("best_oa_location")] or []) + (d.get("oa_locations") or [])
        for loc in [x for x in locs if x]:
            if loc.get("url_for_pdf"):
                cands.append(loc["url_for_pdf"])
        for loc in [x for x in locs if x]:           # non-pdf landing pages last
            if loc.get("url") and loc["url"] not in cands:
                cands.append(loc["url"])
    except Exception:
        pass
    # Europe PMC: open-access render-PDF for any indexed PMCID
    try:
        q = urllib.parse.urlencode({"query": f"DOI:{doi}", "format": "json", "resultType": "core"})
        r = _json(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{q}")
        for res in (r.get("resultList", {}) or {}).get("result", []):
            pmcid = res.get("pmcid")
            if pmcid and res.get("isOpenAccess") == "Y":
                cands.append(f"https://europepmc.org/articles/{pmcid}?pdf=render")
    except Exception:
        pass
    # de-dup, drop bare doi.org links (they redirect to publisher HTML)
    seen, out = set(), []
    for u in cands:
        if u and u not in seen and "doi.org/" not in u:
            seen.add(u); out.append(u)
    return out


def _slug(s):
    return re.sub(r"[^a-zA-Z0-9]+", "_", (s or "paper")).strip("_")[:70]


def download(url, path):
    try:
        with _get(url, 90) as r:
            data = r.read()
    except Exception as e:
        return False, f"error: {e}"
    if data[:5] != b"%PDF-":
        return False, f"not-a-pdf ({len(data)} bytes; likely HTML landing page)"
    with open(path, "wb") as f:
        f.write(data)
    return True, len(data)


def extract_text(pdf_path):
    try:
        import fitz
        return "\n".join(p.get_text() for p in fitz.open(pdf_path))
    except Exception:
        try:
            import pypdf
            return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(pdf_path).pages)
        except Exception as e:
            return f"[extraction failed: {e}]"


def fetch(doi):
    os.makedirs(PDFDIR, exist_ok=True)
    meta = crossref(doi)
    print(json.dumps(meta, indent=2))
    cands = oa_candidates(doi)
    print(f"OA candidates ({len(cands)}):")
    for c in cands:
        print("  -", c)
    if not cands:
        print("No OA PDF found. Try: litfetch search <title>  (arXiv/repository copy).")
        return
    slug = _slug(f"{meta['year']}_{meta['authors'].split(',')[0]}_{meta['title']}")
    pdf_path = os.path.join(PDFDIR, slug + ".pdf")
    n = None
    for c in cands:
        ok, n = download(c, pdf_path)
        print(f"  try {c[:70]} -> {'OK' if ok else n}")
        if ok:
            break
    if not ok:
        print("No candidate yielded a real PDF (all paywalled/HTML). Open-access copy may not exist.")
        return
    print(f"Saved {n} bytes -> {pdf_path}")
    txt = extract_text(pdf_path)
    with open(pdf_path[:-4] + ".txt", "w") as f:
        f.write(txt)
    print(f"Extracted {len(txt)} chars -> {pdf_path[:-4]}.txt")
    print("---- first 1200 chars ----")
    print(txt[:1200])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doi").add_argument("doi")
    ps = sub.add_parser("search"); ps.add_argument("query"); ps.add_argument("--rows", type=int, default=6)
    sub.add_parser("fetch").add_argument("doi")
    a = ap.parse_args()
    if a.cmd == "doi":
        print(json.dumps(crossref(a.doi), indent=2))
    elif a.cmd == "search":
        for i, r in enumerate(search(a.query, a.rows), 1):
            print(f"[{i}] {r['year']} | {r['title'][:92]}")
            print(f"     {r['authors'][:92]}")
            print(f"     {r['venue'][:55]} | DOI:{r['doi']} | OA:{r['oa_pdf']}")
    elif a.cmd == "fetch":
        fetch(a.doi)


if __name__ == "__main__":
    main()
