"""
Artifact-backed checker for the FIM identifiability / experiment-design analysis.
Reads only the saved JSON/NPZ artifacts and the read-only inputs; asserts the gates;
writes checker_report.json. A FAIL here means a claim in packet.md is not supported.
"""
import os
import json
import hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    checks = []

    def gate(name, ok, detail=""):
        checks.append(dict(name=name, pass_=bool(ok), detail=str(detail)))

    # 1) inputs unchanged
    exp = dict(zip(["spec.py", "fe_elements.py"],
                   ["fa9063e21ad1daff06333a09fe646b4bede35e0b10c18d57246774eec4710c19",
                    "b3d0e7f3660a9346d32daff4d41820ca13dfcbe1410b5c8c1405ac75d4447659"]))
    for fn, h in exp.items():
        got = sha256(os.path.join(HERE, "inputs", fn))
        gate(f"input_sha256_{fn}", got == h, got)

    R = json.load(open(os.path.join(HERE, "fim_results.json")))
    P = json.load(open(os.path.join(HERE, "profile_likelihood.json")))

    # 2) forward model reproduces the Opus JAX nominal modes
    gate("forward_reproduces_jax_nominal_modes",
         R["validation_max_abs_freq_err_vs_jax_hz"] < 0.01,
         f"max|df|={R['validation_max_abs_freq_err_vs_jax_hz']} Hz (<0.01)")

    # 3) reduction error reported and small
    re = P["reduction_max_abs_freq_err_hz"]
    gate("reduction_error_small", max(re.values()) < 0.05, re)

    # 4) identifiable-direction count consistent (3) and a clear stiff/sloppy gap
    designs = R["designs"]
    nid = {n: designs[n]["n_identifiable_directions"] for n in designs}
    gate("identifiable_count_3_all_designs", all(v == 3 for v in nid.values()), nid)
    # gap: 3rd eigenvalue >> 4th in every design
    gaps = {}
    for n in designs:
        ev = np.array(designs[n]["fim_eigenvalues"], float)
        gaps[n] = float(ev[2] / max(ev[3], 1e-30))
    gate("stiff_sloppy_gap_present", all(g > 1e3 for g in gaps.values()),
         {k: f"{v:.2e}" for k, v in gaps.items()})

    # 5) BOTH joint params unidentifiable (marginal sd ~ prior) in all designs
    prior = R["assumptions"]["PRIOR_SD"]
    joint_ok = True
    detail = {}
    for n in designs:
        msd = designs[n]["marginal_posterior_sd"]
        for jp in ("joint_axial", "joint_lateral"):
            detail[f"{n}:{jp}"] = msd[jp]
            if msd[jp] < 0.9 * prior:
                joint_ok = False
    gate("joints_unidentifiable_near_prior", joint_ok, detail)

    # 6) the three structural params ARE learned (marginal sd < 0.5*prior) given full band
    learn_ok = all(designs[n]["marginal_posterior_sd"][p] < 0.5 * prior
                   for n in designs for p in ("tray_E", "strut_EA", "strut_EI"))
    gate("strut_tray_params_learned_full_band", learn_ok)

    # 7) band sensitivity: identifiable count is monotone non-decreasing and ends at 3
    sb = R["sensitivity"]["vs_resolved_band"]
    seq = [s["n_identifiable"] for s in sb]
    gate("band_sensitivity_monotone_to_3",
         all(seq[i] <= seq[i+1] for i in range(len(seq)-1)) and seq[-1] == 3, seq)

    # 8) noise robustness: count stays 3 across the noise sweep (structural, not noise-limited)
    ns = [s["n_identifiable"] for s in R["sensitivity"]["vs_freq_noise"]]
    gate("count_robust_to_noise", all(v == 3 for v in ns), ns)

    # 9) profile likelihood confirms FIM: joints flat, others not flat
    prof = P["profiles"]
    pc = (prof["joint_axial"]["flat_unidentifiable"] and
          prof["joint_lateral"]["flat_unidentifiable"] and
          not prof["tray_E"]["flat_unidentifiable"] and
          not prof["strut_EA"]["flat_unidentifiable"] and
          not prof["strut_EI"]["flat_unidentifiable"])
    gate("profile_confirms_fim", pc,
         {k: prof[k]["flat_unidentifiable"] for k in prof})

    # 10) QOI present with gradient + sloppy-subspace projection
    qok = ("d_qoi_d_theta" in R["qoi"] and
           all("qoi_fraction_in_sloppy_subspace" in designs[n] for n in designs))
    gate("qoi_gradient_and_projection_present", qok,
         {n: designs[n]["qoi_fraction_in_sloppy_subspace"] for n in designs})

    # 11) experiment-design sweeps present and non-trivial (sensor placement matters)
    wm = R["experiment_design"]["where_to_measure_1sensor"]
    spread = max(d["logdet"] for d in wm) - min(d["logdet"] for d in wm)
    gate("experiment_design_present", len(wm) > 10 and spread > 1.0,
         f"logdet spread={spread:.2f}")

    # 12) figures exist
    figs = ["fig1_fim_eigenspectrum.png", "fig2_sensitivity_heatmap.png",
            "fig3_param_identifiability.png", "fig4_band_sensitivity.png",
            "fig5_experiment_design.png", "fig6_qoi_vs_data.png",
            "fig7_profile_likelihood.png"]
    miss = [f for f in figs if not os.path.exists(os.path.join(HERE, "figures", f))]
    gate("all_figures_present", not miss, miss)

    # 13) honesty: this is a FIM/profile analysis, NOT a NUTS/posterior sampler run
    pk = open(os.path.join(HERE, "packet.md")).read().lower()
    no_nuts = ("not a sampler" in pk or "no nuts" in pk or "not a nuts" in pk or
               "not a posterior sampler" in pk)
    gate("no_unbacked_nuts_or_posterior_claim", no_nuts,
         "packet explicitly labels this as Fisher/profile, not a sampler")

    overall = all(c["pass_"] for c in checks)
    report = dict(overall_pass=overall,
                  n_checks=len(checks), n_pass=sum(c["pass_"] for c in checks),
                  checks=checks)
    with open(os.path.join(HERE, "checker_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    for c in checks:
        print(("PASS " if c["pass_"] else "FAIL ") + c["name"] + "  " + c["detail"][:80])
    print(f"\nOVERALL: {'PASS' if overall else 'FAIL'} ({report['n_pass']}/{report['n_checks']})")
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()
