#!/usr/bin/env python3
"""Task Card E `_Fable` — literature claim ceiling, verified directly from the PDFs.

Extracts the actual equations from the two named papers and records page-located excerpts so the claim
"the requested learned frequency x location MEAN is absent from these two papers" is artifact-backed.
Writes out/literature_check_fable.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_fable as C  # noqa: E402

FEBR = C.REPO / "references/pdfs/digital-twinning-of-self-sensing-structures-using-the-statistical-finite-element-method.pdf"
SCHN = C.REPO / ("references/pdfs/Bayesian parameter updating in linear structural dynamics with "
                 "frequency transformed data using rational surrogate models.pdf")

QUERIES = {
    "febrianto": [
        ("zero_prior_mean_discrepancy", r"multivariate Gaussian.{0,80}N\s*.{0,3}0,\s*Cd"),
        ("zero_mean_gp_prior_general", r"zero mean and prescribed covariance"),
        ("squared_exponential_space_only", r"squared-exponential kernel"),
        ("load_scaled_variance_not_mean", r"γk|gamma_k|∥\s*fk\s*∥"),
        ("frequency_only_as_sampling_rate", r"sampling\s+frequency"),
    ],
    "schneider": [
        ("zero_mean_log_magnitude_and_phase", r"zero-mean Gaussian distribution"),
        ("additive_correlation_eq19", r"\(19\)"),
        ("rho_z_exponential_eq20", r"\(20\)"),
        ("rho_f_exponential_eq21", r"\(21\)"),
        ("posterior_r_0p82", r"0\.82"),
    ],
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    import fitz
    out = {"method": "text extracted with PyMuPDF from the PDFs in references/pdfs/; excerpts are verbatim "
                     "with whitespace collapsed, and carry the PDF page number",
           "papers": {}}
    for tag, path in [("febrianto", FEBR), ("schneider", SCHN)]:
        if not path.exists():
            out["papers"][tag] = {"error": f"missing {path}"}
            continue
        doc = fitz.open(path)
        pages = [p.get_text() for p in doc]
        rec = {"file": str(path.relative_to(C.REPO)), "sha256": sha256(path), "n_pages": len(pages),
               "findings": {}}
        for name, pat in QUERIES[tag]:
            hits = []
            for i, t in enumerate(pages):
                for m in re.finditer(pat, t, re.I | re.S):
                    s, e = max(0, m.start() - 130), min(len(t), m.end() + 200)
                    hits.append({"pdf_page": i + 1, "excerpt": " ".join(t[s:e].split())})
            rec["findings"][name] = hits[:2]
        out["papers"][tag] = rec

    out["conclusions"] = {
        "febrianto": "Zero-mean discrepancy prior d ~ N(0, C_d); squared-exponential kernel in SPACE ONLY; "
                     "quasi-static strain; gamma_k scales the discrepancy VARIANCE with load magnitude, it is "
                     "not a mean function. Non-sensor predictive mean moves through the conditioned FE state. "
                     "A non-zero frequency x location discrepancy MEAN is NOT in this paper.",
        "schneider": "Zero-mean Gaussian in log-magnitude and phase (Eq. 18); additive frequency + "
                     "accelerometer-location CORRELATION (Eqs. 19-21) with posterior l_co,z ~ 49.8 m, "
                     "l_co,f ~ 10.1 Hz, r = 0.82. Transformed-space zero mean, NOT a structured mean. "
                     "Nuance: the multiplicative amplitude error is lognormal, so its arithmetic mean in the "
                     "original amplitude space need not be 1.",
        "allowed_claim": "The requested learned frequency x location MEAN is absent from these two papers.",
        "forbidden_claim": "No literature-wide novelty gap is claimed; that needs a systematic review this "
                           "run did not perform.",
        "kernel_form_deviation": {
            "schneider_published": "rho(dz,df) = r exp(-df/l_co,f) + (1-r) exp(-dz/l_co,z), i.e. "
                                   "r K_f (x) ones + (1-r) ones (x) K_z",
            "frozen_in_project_and_card": "sigma_u^2 [ r K_f (x) I_x + (1-r) I_f (x) K_x ] with K_f "
                                          "SQUARED-exponential in frequency",
            "why_it_matters": "under the published form two different sensors at the same frequency line "
                              "correlate >= r = 0.82, so a zero-mean GP transfers strongly to a held-out "
                              "channel; under the (x) I form the same pair correlates only ~0.18. Primary "
                              "arms follow the card; SENS-4 tests the published form.",
        },
    }
    (C.OUT / "literature_check_fable.json").write_text(json.dumps(out, indent=2))
    for tag, rec in out["papers"].items():
        n = sum(len(v) for v in rec.get("findings", {}).values())
        print(f"  {tag}: {rec.get('n_pages')} pages, {n} located excerpts")
    print("literature_check_fable.json written")


if __name__ == "__main__":
    main()
