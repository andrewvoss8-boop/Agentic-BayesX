#!/usr/bin/env python3
"""Plate-test REHEARSAL — synthetic end-to-end validation of the >200 Hz drumhead test design.

Question: does the promised normal-Z buy-down (5.4x -> 3.5x @ 12 plate Z-sensors,
netcg pretest_design.json) survive the ACTUAL Bayesian pipeline (joint NUTS on simulated noisy
plate data with honest un-representable fine structure)? Pre-registered criteria: question_framing.md.

Per (arm, seed):
  1. TRUTH: theta_true ~ L5 posterior draw; target drumhead-mode true shapes = model shapes mixed
     across the drumhead basis + OUT-OF-BAND plate modes (fine structure the array cannot capture),
     scales calibrated so sd(ln|g_true/g_model|) ~= SD_A_U_TRUTH. Non-target amps: netcg tiers.
  2. DATA: mode-shape samples at the arm's sensors (+10% RMS noise) + target frequencies (1%).
  3. INFERENCE: ONE numpyro NUTS: log_theta(9) + sigma_w2 + shape coeffs c (n_tgt x n_basis)
     + sigma_y. Freq likelihood = L5 (Kiran Eq 25) on existing measured modes + targets.
     Shape basis frozen at theta_MAP (A9; truth does NOT share this simplification).
  4. DELIVERY: theta draws x {target amp from c-posterior x A10 inflation for un-captured
     structure; non-target tiers} -> normal-Z 95% band -> band factor + coverage vs truth.
Resumable: skips (arm,seed) with existing out/runs/<arm>_<seed>.json. float64, threads pinned.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import numpy as np

WS = Path(__file__).resolve().parent.parent
NETCG = WS.parent / "shocksat_netcg_method_selection_20260701"
sys.path.insert(0, str(NETCG / "code"))
import netcg_qoi as NC                      # noqa: E402  (also wires psd_envelope realfrf path)

import jax, jax.numpy as jnp                # noqa: E402
import numpyro, numpyro.distributions as dist   # noqa: E402
from numpyro.diagnostics import summary as nuts_summary  # noqa: E402
from numpyro.infer import MCMC, NUTS, init_to_median     # noqa: E402
jax.config.update("jax_enable_x64", True)

DRUM = (228.0, 260.0); TRAY_Z = 55.0
SD_F_M, SD_A_M, SD_F_U, SD_A_U = NC.SD_F_M, NC.SD_A_M, NC.SD_F_U, NC.SD_A_U   # 0.01/0.35/0.06/0.80
NOISE_FRAC = 0.10          # sensor noise, fraction of per-mode plate-field RMS (A7)
JITTER_IN = 1.5            # placement jitter radius, inches (A8)
N_EXTRA = 6                # out-of-band plate modes carried in the TRUTH (fine structure) (A4)
NSIG_THETA = 0.25          # L5 prior sd on log_theta (rf.core.NSIG_THETA)
WARMUP, SAMPLES, CHAINS = 700, 700, 4
TARGET_ACCEPT = float(os.environ.get("TARGET_ACCEPT", "0.9"))   # retune pass uses 0.98 (D9)
N_TH_DEL, N_REP_DEL = 60, 40               # delivery ensemble: theta draws x amp reps (A11)

ARMS = {  # name: (n_sensors, jitter, sd_truth, seeds)
    "A0_1sensor":  (1, False, 0.80, list(range(8))),
    "A1_12sensor": (12, False, 0.80, list(range(8))),
    "A2_20sensor": (20, False, 0.80, list(range(8))),
    "A3_12jitter": (12, True, 0.80, list(range(8))),
    "S_sd04":      (12, False, 0.40, [0, 1]),
    "S_sd16":      (12, False, 1.60, [0, 1]),
}


class Setup:
    """Everything theta-independent, built ONCE at theta_MAP: plate field, targets, basis, sensors."""

    def __init__(self):
        self.model = NC.QOIModel()
        z = np.load(NETCG / "out" / "theta_post_L5.npz", allow_pickle=True)
        self.theta_post = np.asarray(z["theta_post"], np.float64)
        self.theta_map = np.median(self.theta_post, 0)
        m = self.model
        f, Q = m.modes(self.theta_map)
        self.Qmap = Q
        R = m.R
        keep_arr = np.empty(len(R.keeprow), np.int64)
        for dof, row in R.keeprow.items():
            keep_arr[row] = dof
        node_of, axis_of = keep_arr // 6, keep_arr % 6
        U = np.asarray(R.vk[:, :80], np.float64) @ R.T
        zc = R.xyz[node_of, 2]
        self.plate_mask = (zc >= TRAY_Z) & (axis_of == 2)
        self.coords = R.xyz[node_of[self.plate_mask]]          # (n_plate, 3)
        # target drumhead modes: in-band, unmeasured, real normal participation (pretest definition)
        g = m.g_axis(Q, 2); part = np.abs(g) / (np.abs(g).sum() + 1e-30)
        self.tgt = np.array([j for j in range(m.nM)
                             if DRUM[0] <= m.fnom[j] <= DRUM[1] and not m.is_meas[j] and part[j] > 0.01])
        # inference BASIS = ALL in-band drumhead-region modes (targets + pure-cancel partners)
        self.basis = np.array([j for j in range(m.nM) if DRUM[0] <= m.fnom[j] <= DRUM[1]])
        # TRUTH extra basis = next plate-heavy modes ABOVE the band (fine structure; NOT in inference)
        f_all = f; above = np.where(f_all > NC.BAND[1])[0]
        fieldZ_all = U[self.plate_mask] @ Q                    # (n_plate, 74)
        plate_energy = (fieldZ_all[:, above] ** 2).sum(0)
        self.extra = above[np.argsort(plate_energy)[::-1][:N_EXTRA]]
        # plate-Z fields
        self.F_basis = fieldZ_all[:, m.inb[self.basis]]        # (n_plate, n_basis)
        self.F_extra = fieldZ_all[:, self.extra]               # (n_plate, n_extra)
        # net-Z participation of basis & extra (tray uniform-mass integral)
        self.g_basis = np.array([m.Utray[2] @ Q[:, m.inb[j]] for j in self.basis])
        self.g_extra = np.array([m.Utray[2] @ Q[:, k] for k in self.extra])
        self.g_map = m.g_axis(Q, 2)
        # candidate grid + greedy captured-energy placement (pretest algorithm)
        rad = np.sqrt(self.coords[:, 0] ** 2 + self.coords[:, 1] ** 2)
        cand = []
        for rr in np.linspace(0, rad.max(), 6):
            ring = np.where(np.abs(rad - rr) < 1.0)[0]
            if len(ring):
                for th in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                    x, y = rr * np.cos(th), rr * np.sin(th)
                    k = ring[np.argmin((self.coords[ring, 0] - x) ** 2 + (self.coords[ring, 1] - y) ** 2)]
                    cand.append(int(k))
        self.cand = sorted(set(cand))
        tix = [int(np.where(self.basis == t)[0][0]) for t in self.tgt]
        Phi = self.F_basis[self.cand][:, tix]                  # target shapes on candidates
        full_e = (Phi ** 2).sum(0) + 1e-30
        sel, avail = [], list(range(len(self.cand)))
        while len(sel) < min(20, len(self.cand)):
            best, bj = -1e18, None
            for jj in avail:
                sc = ((Phi[sel + [jj]] ** 2).sum(0) / full_e).min()
                if sc > best:
                    best, bj = sc, jj
            sel.append(bj); avail.remove(bj)
        self.greedy_nodes = [self.cand[s] for s in sel]        # plate-node indices, greedy order
        self.Phi_cand_full_e = full_e; self.tix = np.array(tix)
        # A0 sensor: nearest plate node to the CURRENT plate-Z sensor (from netcg pretest figdata)
        fz = np.load(NETCG / "out" / "pretest_figdata.npz", allow_pickle=True)
        cur = np.atleast_2d(fz["cur_xy"])[0]
        self.a0_node = int(np.argmin((self.coords[:, 0] - cur[0]) ** 2 + (self.coords[:, 1] - cur[1]) ** 2))
        # calibrate truth-mix scale kappa per sd_truth target (module MC, seed-independent) (A4)
        self._kappa = {}

    def sensors(self, arm):
        n, jit, _, _ = ARMS[arm]
        nodes = [self.a0_node] if n == 1 else list(self.greedy_nodes[:n])
        return nodes, jit

    def captured_frac(self, nodes):
        """per-target captured energy fraction of the sensor set vs the dense candidate array."""
        tixn = self.tix
        Phi_sel = self.F_basis[nodes][:, tixn]
        return np.clip((Phi_sel ** 2).sum(0) / self.Phi_cand_full_e, 0, 1)

    def kappa(self, sd_truth, rng0=np.random.default_rng(123), nmc=400):
        """global mix scale s.t. sd(ln|g_true/g_map|) over targets ~= sd_truth."""
        if sd_truth in self._kappa:
            return self._kappa[sd_truth]
        lo, hi = 0.01, 5.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            etas = []
            for _ in range(nmc):
                for ti, t in enumerate(self.tgt):
                    bi = self.tix[ti]
                    c = np.zeros(len(self.basis)); c[bi] = 1.0
                    c += rng0.normal(0, mid, len(self.basis))
                    d = rng0.normal(0, mid, len(self.extra))
                    g_true = c @ self.g_basis + d @ self.g_extra
                    etas.append(np.log(abs(g_true) / (abs(self.g_map[t]) + 1e-30) + 1e-12))
            s = float(np.std(etas))
            if s > sd_truth:
                hi = mid
            else:
                lo = mid
        self._kappa[sd_truth] = 0.5 * (lo + hi)
        return self._kappa[sd_truth]


def make_truth(S: Setup, seed, sd_truth):
    """theta_true, per-mode truth amps (signed, len nM), true target shapes on the plate."""
    rng = np.random.default_rng(1000 + seed)
    m = S.model
    theta_true = S.theta_post[rng.integers(len(S.theta_post))]
    kap = S.kappa(sd_truth)
    amp = np.ones(m.nM)
    # non-target tiers (A5)
    for j in range(m.nM):
        if j in S.tgt:
            continue
        sd = SD_A_M if m.is_meas[j] else SD_A_U
        amp[j] = np.exp(rng.normal(0, sd))
    phi_true = {}
    for ti, t in enumerate(S.tgt):
        bi = S.tix[ti]
        c = np.zeros(len(S.basis)); c[bi] = 1.0
        c += rng.normal(0, kap, len(S.basis))
        d = rng.normal(0, kap, len(S.extra))
        g_true = c @ S.g_basis + d @ S.g_extra
        amp[t] = g_true / (S.g_map[t] + 1e-30)       # signed ratio bookkeeping
        phi_true[int(t)] = S.F_basis @ c + S.F_extra @ d
    f_true, _ = m.modes(theta_true)
    truth_spec = m.spectrum(theta_true, 2, amp=amp,
                            fscale=f_true[m.inb] / (m.fnom + 1e-30))  # truth at theta_true freqs
    return theta_true, amp, phi_true, f_true, truth_spec


def simulate_data(S: Setup, arm, seed, sd_truth):
    rng = np.random.default_rng(2000 + seed)
    m = S.model
    theta_true, amp_true, phi_true, f_true, truth_spec = make_truth(S, seed, sd_truth)
    nodes, jit = S.sensors(arm)
    if jit:   # placement jitter: relocate each sensor to a random plate node within JITTER_IN
        jn = []
        for nd in nodes:
            d2 = ((S.coords[:, :2] - S.coords[nd, :2]) ** 2).sum(1)
            near = np.where(d2 <= JITTER_IN ** 2)[0]
            jn.append(int(rng.choice(near)))
        nodes_used = jn
    else:
        nodes_used = list(nodes)
    Y = np.empty((len(nodes_used), len(S.tgt)))          # shape samples (A7)
    sig_true = np.empty(len(S.tgt))
    for ti, t in enumerate(S.tgt):
        ph = phi_true[int(t)]
        sig = NOISE_FRAC * float(np.sqrt(np.mean(ph ** 2)))
        sig_true[ti] = sig
        Y[:, ti] = ph[nodes_used] + rng.normal(0, sig, len(nodes_used))
    # target frequency observations at measured tier (A6)
    f_obs_tgt = f_true[m.inb[S.tgt]] * (1 + rng.normal(0, SD_F_M, len(S.tgt)))
    return dict(theta_true=theta_true, amp_true=amp_true, truth_spec=truth_spec,
                nodes_nominal=nodes, nodes_used=nodes_used, Y=Y, sig_true=sig_true,
                f_obs_tgt=f_obs_tgt)


def run_nuts(S: Setup, data, seed, sd_truth):
    """Joint NUTS: log_theta(9)+sigma_w2 (freq lik, L5) + c(n_tgt,n_basis)+sigma_y (shape lik)."""
    m = S.model; R = m.R
    kap = S.kappa(sd_truth)   # c prior scale = the tier-consistent truth-mix scale (D8)
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    meas_idx = m.inb[m.is_meas]                        # existing measured modes (full-eig index)
    obs_idx = np.concatenate([meas_idx, m.inb[S.tgt]])
    obs_w2 = jnp.asarray(np.concatenate(
        [(m.meas_f[m.is_meas] * 2 * np.pi) ** 2,
         (np.asarray(data["f_obs_tgt"]) * 2 * np.pi) ** 2]))
    obs_idx_j = jnp.asarray(obs_idx)
    # shape likelihood pieces (basis frozen at theta_MAP — A9/D4; NOMINAL sensor rows: the
    # inference does not know the jitter, exactly as a real test analysis would not)
    Phi_s = jnp.asarray(S.F_basis[data["nodes_nominal"]])     # (n_s, n_basis)
    Yobs = jnp.asarray(data["Y"])                             # (n_s, n_tgt)
    rms = float(np.sqrt(np.mean(S.F_basis[:, S.tix] ** 2)))
    n_tgt, n_basis = len(S.tgt), len(S.basis)
    e_diag = np.zeros((n_tgt, n_basis)); e_diag[np.arange(n_tgt), S.tix] = 1.0
    e_diag = jnp.asarray(e_diag)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([9]).to_event(1))
        sig_w = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(lt), A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)
        w2 = lam[obs_idx_j]
        var = (sig_w * obs_w2) ** 2
        numpyro.factor("lik_freq", -0.5 * jnp.sum((obs_w2 - w2) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        c = numpyro.sample("c", dist.Normal(e_diag, kap).to_event(2))      # (n_tgt, n_basis) prior = truth scale (D8)
        sig_y = numpyro.sample("sigma_y", dist.HalfNormal(0.2 * rms))
        pred = Phi_s @ c.T                                                  # (n_s, n_tgt)
        numpyro.sample("y", dist.Normal(pred, sig_y), obs=Yobs)

    kernel = NUTS(model, target_accept_prob=TARGET_ACCEPT, init_strategy=init_to_median,
                  dense_mass=False, max_tree_depth=8)
    mcmc = MCMC(kernel, num_warmup=WARMUP, num_samples=SAMPLES, num_chains=CHAINS,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(3000 + seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    stats = nuts_summary(g, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    flat = {k: np.asarray(v).reshape((-1,) + tuple(np.asarray(v).shape[2:])) for k, v in g.items()}
    diag = {"max_rhat": round(max_rhat, 4), "min_ess": round(min_ess, 1), "divergences": div,
            "div_frac": round(div / (CHAINS * SAMPLES), 4), "target_accept": TARGET_ACCEPT,
            "converged": bool(max_rhat <= 1.05 and min_ess >= 200 and div < 0.02 * CHAINS * SAMPLES)}
    return flat, diag


def deliver(S: Setup, flat, data, arm, sd_truth):
    """Delivered normal-Z ensemble -> band factor + coverage vs the seed's truth (A10/A11).

    Target amps = c-POSTERIOR draws through the net integral + OUT-OF-BASIS structure carried as
    explicit prior-scale d-draws (D8: the sensors cannot see out-of-basis modes; the delivery
    carries them at the same scale the design assumed — no double-counted inflation)."""
    m = S.model
    rng = np.random.default_rng(9)
    kap = S.kappa(sd_truth)
    theta = np.exp(flat["log_theta"])                      # (Ndraw, 9)
    c_post = flat["c"]                                     # (Ndraw, n_tgt, n_basis)
    cap = S.captured_frac(data["nodes_nominal"])           # per-target captured fraction (diagnostic)
    sdf = np.where(m.is_meas, SD_F_M, SD_F_U).copy()
    sdf[S.tgt] = SD_F_M                                    # targets: freq now measured (A6)
    sda = np.where(m.is_meas, SD_A_M, SD_A_U).copy()       # non-target tiers
    idx = np.linspace(0, len(theta) - 1, N_TH_DEL).astype(int)
    specs, grms_s = [], []
    for k, s in enumerate(idx):
        th = theta[s]
        f, Q = m.modes(th)
        fi = f[m.inb]; gg = m.g_axis(Q, 2)
        wi_base = 2 * np.pi * fi; w = 2 * np.pi * NC.FGRID
        for _ in range(N_REP_DEL):
            amp = np.exp(rng.normal(0, 1, m.nM) * sda)
            # target amps: c-posterior draw (signed) + out-of-basis d at prior scale (D8)
            cd = c_post[rng.integers(len(c_post))]
            dd = rng.normal(0, kap, (len(S.tgt), len(S.extra)))
            g_tgt = cd @ S.g_basis + dd @ S.g_extra                        # (n_tgt,)
            amp[S.tgt] = g_tgt / (S.g_map[S.tgt] + 1e-30)
            fsc = 1 + rng.normal(0, 1, m.nM) * sdf
            wi = wi_base * fsc
            g = gg * amp
            D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * NC.ZETA * wi[:, None] * w[None, :]
            sp = np.abs(((g[:, None] * wi[:, None] ** 2) / D).sum(0))
            specs.append(sp)
            grms_s.append(NC.grms(NC.octave_smooth(NC.FGRID, sp)))
    specs = np.array(specs); grms_s = np.array(grms_s)
    lo, hi = np.percentile(specs, 2.5, 0), np.percentile(specs, 97.5, 0)
    p = np.percentile(grms_s, [2.5, 97.5])
    band_factor = float(p[1] / max(p[0], 1e-30))
    cov = NC.coverage_vs_truth(lo, hi, [data["truth_spec"]], NC.FGRID)
    # amplitude recovery per target: posterior of ln|g_tgt/g_map| vs truth (incl out-of-basis d)
    dd = rng.normal(0, kap, (len(c_post), len(S.tgt), len(S.extra)))
    g_all = c_post @ S.g_basis + dd @ S.g_extra
    eta_post = np.log(np.abs(g_all) / (np.abs(S.g_map[S.tgt])[None, :] + 1e-30) + 1e-12)
    eta_true = np.log(np.abs(data["amp_true"][S.tgt]) + 1e-12)
    return dict(band_factor=round(band_factor, 3), coverage=cov,
                captured_frac=[round(float(x), 3) for x in cap],
                eta_post_mean=[round(float(x), 3) for x in eta_post.mean(0)],
                eta_post_sd=[round(float(x), 3) for x in eta_post.std(0)],
                eta_true=[round(float(x), 3) for x in eta_true],
                lo=lo.tolist(), hi=hi.tolist())


def run_one(S: Setup, arm, seed):
    outp = WS / "out" / "runs" / f"{arm}_s{seed}.json"
    if outp.exists():
        print(f"[skip] {arm} s{seed}"); return
    t0 = time.time()
    _, _, sd_truth, _ = ARMS[arm]
    data = simulate_data(S, arm, seed, sd_truth)
    flat, diag = run_nuts(S, data, seed, sd_truth)
    dl = deliver(S, flat, data, arm, sd_truth)
    rec = {"arm": arm, "seed": seed, "sd_truth": sd_truth,
           "n_sensors": len(data["nodes_nominal"]), "nuts": diag, **dl,
           "truth_spec": np.asarray(data["truth_spec"]).tolist(),
           "runtime_s": round(time.time() - t0, 1)}
    outp.write_text(json.dumps(rec))
    print(f"[done] {arm} s{seed}: band {dl['band_factor']}x cov {dl['coverage']['weighted_coverage']} "
          f"rhat {diag['max_rhat']} ess {diag['min_ess']} div {diag['divergences']} "
          f"({rec['runtime_s']}s)", flush=True)


def summarize(S: Setup):
    runs = []
    for p in sorted((WS / "out" / "runs").glob("*.json")):
        runs.append(json.loads(p.read_text()))
    arms = {}
    for a in ARMS:
        rs = [r for r in runs if r["arm"] == a]
        ok = [r for r in rs if r["nuts"]["converged"]]
        if not rs:
            continue
        bf = [r["band_factor"] for r in ok]
        wc = [r["coverage"]["weighted_coverage"] for r in ok]
        arms[a] = {"n_runs": len(rs), "n_converged": len(ok),
                   "median_band_factor": round(float(np.median(bf)), 2) if bf else None,
                   "band_factors": bf, "mean_weighted_coverage": round(float(np.mean(wc)), 3) if wc else None,
                   "coverages": wc,
                   "seeds_cov_ge_085": int(np.sum(np.array(wc) >= 0.85)) if wc else 0,
                   "worst_rhat": max(r["nuts"]["max_rhat"] for r in rs),
                   "min_ess": min(r["nuts"]["min_ess"] for r in rs),
                   "median_eta_post_sd": round(float(np.median([x for r in ok for x in r["eta_post_sd"]])), 3) if ok else None}
    ref = json.load(open(NETCG / "out" / "pretest_design.json"))
    summary = {"arms": arms,
               "analytic_reference": {"current_1sensor": ref["buy_down_curve"][0]["normal_band_factor"],
                                       "promised_12sensor": ref["buy_down_curve"][-1]["normal_band_factor"],
                                       "floor": ref["fully_resolved_floor_band_factor"]},
               "target_modes_hz": [round(float(S.model.fnom[t]), 1) for t in S.tgt],
               "n_basis": len(S.basis), "n_extra_truth_modes": len(S.extra),
               "config": {"warmup": WARMUP, "samples": SAMPLES, "chains": CHAINS,
                          "noise_frac": NOISE_FRAC, "jitter_in": JITTER_IN,
                          "delivery": [N_TH_DEL, N_REP_DEL]}}
    (WS / "out" / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({a: {k: v for k, v in d.items() if not isinstance(v, list)}
                      for a, d in arms.items()}, indent=1))


if __name__ == "__main__":
    S = Setup()
    print(f"targets: {[round(float(S.model.fnom[t]),1) for t in S.tgt]} Hz | basis {len(S.basis)} "
          f"| extra {len(S.extra)} | cand {len(S.cand)}", flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "summarize":
        summarize(S)
    elif len(sys.argv) > 1 and sys.argv[1] == "retune":
        # D9: uniform retune policy — re-run every non-converged (arm,seed) with the CURRENT
        # TARGET_ACCEPT (set env TARGET_ACCEPT=0.98). Data/seeds identical; only sampler tuning.
        for p in sorted((WS / "out" / "runs").glob("*.json")):
            r = json.loads(p.read_text())
            if not r["nuts"]["converged"]:
                print(f"[retune] {r['arm']} s{r['seed']} (was div_frac {r['nuts']['div_frac']}, "
                      f"rhat {r['nuts']['max_rhat']})", flush=True)
                p.unlink()
                run_one(S, r["arm"], r["seed"])
        summarize(S)
    else:
        for arm, (_, _, _, seeds) in ARMS.items():
            for sd in seeds:
                run_one(S, arm, sd)
        summarize(S)
