#!/usr/bin/env python3
"""MC over channel splits for L8b Beck-on-.ash (D22): does inferring the mode-shape FIELD sharpen the held-out
amplitude ACROSS splits (not just seed 0)? Per split: held-out peak interval score with FEM shapes vs inferred
shapes (same matched modes), + convergence. Output: out/mc_beck_summary.json.

Beck mode-matching-free method: Beck, Au & Vanik (2001), Comput.-Aided Civ. Infrastruct. Eng. 16:1-11.
"""
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modal_beck_ash as b

WS = Path(__file__).resolve().parent.parent


def run(n_splits=25, warmup=700, samples=700, n_draws=150):
    rows = []
    for s in range(n_splits):
        r = b.run(seed=s, n_modes=12, warmup=warmup, samples=samples, chains=4, n_draws=n_draws, force=True)
        f, i = r["heldout_peak_FEM_shapes"], r["heldout_peak_INFERRED_shapes"]
        rows.append(dict(seed=s, converged=bool(r["diag"]["converged"]), rhat=r["diag"]["max_rhat"],
                         div=r["diag"]["divergences"], match_MAC=r["match_MAC_mean"],
                         fem_IS=f["interval_score"], inf_IS=i["interval_score"],
                         fem_cov=f["coverage"], inf_cov=i["coverage"], inf_sig=i["sigma_qoi"], fem_sig=f["sigma_qoi"]))
        print(f"  split {s:2d}: conv {rows[-1]['converged']} | FEM IS {f['interval_score']:.0f} -> "
              f"INFERRED IS {i['interval_score']:.0f} (cov {i['coverage']:.2f})", flush=True)
    fem = np.array([r["fem_IS"] for r in rows]); inf = np.array([r["inf_IS"] for r in rows])
    ratio = inf / np.maximum(fem, 1e-9)
    summ = dict(method="L8b_Beck_on_ash (Beck/Au/Vanik 2001)", n_splits=n_splits,
                converged_frac=float(np.mean([r["converged"] for r in rows])),
                fem_IS_median=float(np.median(fem)), inf_IS_median=float(np.median(inf)),
                inf_vs_fem_ratio_median=float(np.median(ratio)),
                inf_vs_fem_ratio_p5=float(np.percentile(ratio, 5)), inf_vs_fem_ratio_p95=float(np.percentile(ratio, 95)),
                n_splits_sharper=int(np.sum(inf < fem)),
                inf_coverage_median=float(np.median([r["inf_cov"] for r in rows])),
                per_split=rows)
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "mc_beck_summary.json").write_text(json.dumps(summ, indent=2))
    print(f"\nMC-BECK DONE: {n_splits} splits, converged {summ['converged_frac']*100:.0f}%")
    print(f"  held-out peak IS median: FEM {summ['fem_IS_median']:.0f} -> INFERRED {summ['inf_IS_median']:.0f} "
          f"(ratio median {summ['inf_vs_fem_ratio_median']:.2f}; sharper in {summ['n_splits_sharper']}/{n_splits} splits)")
    print(f"  inferred-shape coverage median {summ['inf_coverage_median']:.2f}")
    return summ


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
