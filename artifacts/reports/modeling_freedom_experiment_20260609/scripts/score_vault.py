#!/usr/bin/env python3
"""
HUMAN-ONLY vault scoring. Run by Andrew at grading time, AFTER:
  (1) the runner has committed runner_opus/finalists.json + finalists.sha256, and
  (2) vault/tray has been re-downloaded from Google Drive and its SHA256 verified against
      the pinned value in manifest.sha256.

Do NOT run this during the search. It reads the sealed truth.

finalists.json schema (each finalist):
{
  "finalists": [
    {"id": "modelA", "pred_theta": [..4..], "pred_qoi_ref": <float>,
     "pred_qoi_heldout": <float>, "pred_modes_hz": [..6..], "dev_score": <float>}
  ],
  "n_configs_tried": <int>
}
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRUTH = os.path.join(HERE, "vault", "tray", "truth.json")
FINALISTS = os.path.join(HERE, "runner_opus", "finalists.json")


def main():
    if not os.path.exists(TRUTH):
        sys.exit("vault/tray/truth.json missing — re-download from Google Drive and verify SHA256 first.")
    truth = json.load(open(TRUTH))
    fin = json.load(open(FINALISTS))
    th = np.array(truth["theta_true"]); qr = truth["qoi_ref_truth"]; qh = truth["qoi_heldout_truth"]
    tm = np.array(truth["true_modal_freqs_hz"])
    print(f"# vault grading — {len(fin['finalists'])} finalists, N_configs_tried = {fin.get('n_configs_tried','?')}")
    print(f"{'id':12s} {'theta_relRMSE':>13s} {'modes_relRMSE':>13s} {'qoi_ref_err%':>12s} {'qoi_HELDOUT_err%':>16s} {'dev_score':>10s}")
    rows = []
    for f in fin["finalists"]:
        pt = np.array(f["pred_theta"]); pm = np.array(f["pred_modes_hz"])
        theta_rmse = float(np.sqrt(np.mean(((pt - th) / th) ** 2)))
        modes_rmse = float(np.sqrt(np.mean(((pm - tm) / tm) ** 2)))
        eref = 100 * abs(f["pred_qoi_ref"] - qr) / qr
        ehel = 100 * abs(f["pred_qoi_heldout"] - qh) / qh
        rows.append((f["id"], theta_rmse, modes_rmse, eref, ehel, f.get("dev_score", float("nan"))))
        print(f"{f['id']:12s} {theta_rmse:13.4f} {modes_rmse:13.4f} {eref:12.2f} {ehel:16.2f} {f.get('dev_score',float('nan')):10.4f}")
    print("\n# The OVERFITTING SIGNAL: a finalist with a good dev_score but a large HELD-OUT QOI")
    print("# error (qoi_HELDOUT_err%) overfit the in-distribution data. Compare dev_score rank")
    print("# vs held-out rank; if they disagree, the dev score was an optimistic (leaky) proxy.")
    out = os.path.join(HERE, "vault_grading_result.json")
    json.dump({"rows": rows, "n_configs_tried": fin.get("n_configs_tried")}, open(out, "w"), indent=2)
    print(f"\nwrote {out}")
    print("ShockSat pyro-regime grading is separate/manual (real data, no oracle) — see contract.md s2.")


if __name__ == "__main__":
    main()
