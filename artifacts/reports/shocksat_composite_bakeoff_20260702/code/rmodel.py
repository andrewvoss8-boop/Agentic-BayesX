#!/usr/bin/env python3
"""Shared engine for the composite bake-off: candidate reduced model (tier-2 package) + QOI forward +
statFEM F(k) band builder + held-out answer keys + the three NUTS likelihoods (S0 freq / S1 freq+MAC /
S2 Beck shape field). M0 and M1 arms run through THIS code identically (D7). float64 everywhere.

Conventions (quantity_contracts.md): net-CG force per drive G_d(w) = sum_i g_i phi_d,i w^2 / D_i;
frozen Hungarian pairing from tier-2 (trap-2); no per-mode amplitude fitting in any score (trap-1;
LSQ participation appears ONLY in answer-key construction, D2); full in-band mode set (P5).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
NETCG = WS.parent / "shocksat_netcg_method_selection_20260701"
sys.path.insert(0, str(BASE / "code"))
sys.path.insert(0, str(NETCG / "code"))
import netcg_qoi as NC          # octave_smooth, coverage_vs_truth, grms, FGRID, tier sigmas (read-only)

BAND = (45.0, 260.0); ZETA = 0.01
FGRID = NC.FGRID
SD_F_M, SD_A_M, SD_F_U, SD_A_U = NC.SD_F_M, NC.SD_A_M, NC.SD_F_U, NC.SD_A_U
NSIG_THETA = 0.25
GNAMES = ["bottom_box", "steel_welds", "top_box", "al_welds", "angle_brackets",
          "cross_beam", "plates", "joints", "contact"]
DRIVE_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_xy_990xy", "m_zpos_900z", "m_ypos_990y"]
DRIVE_LABEL = {"m_xpos_990x": "+X", "m_zpos_990z": "+Z(990)", "m_xy_990xy": "+XY",
               "m_zpos_900z": "+Z(900)", "m_ypos_990y": "+Y"}
CACHE_DIR = NETCG / "data" / "multiref_modal"
MM = WS.parent / "shocksat_fem_modal_twin_20260609" / "measured_modes.npz"


class CModel:
    """Reduced 80-dim model from a tier-2 package. K(theta) = sum_p theta_p Kblk_p + K_fixed; mass = I."""

    def __init__(self, cid):
        z = np.load(WS / "out" / "tier2" / f"{cid}.npz", allow_pickle=True)
        self.cid = cid
        names = [str(n) for n in z["blk_names"]]
        Kall = np.asarray(z["Kblk"], np.float64)
        self.free_names = [n for n in names if n != "_fixed_bush99"]     # 9 groups (+ couple_x if present)
        order = [names.index(n) for n in GNAMES] + \
                [names.index(n) for n in self.free_names if n not in GNAMES]
        self.free_names = GNAMES + [n for n in self.free_names if n not in GNAMES]
        self.A = Kall[order]                                             # (n_free, 80, 80)
        self.A_fix = Kall[names.index("_fixed_bush99")]
        self.np_ = len(self.free_names)
        self.ash = np.asarray(z["ash"], np.float64)                      # (n_live, 80)
        self.sens = np.asarray(z["sens"], np.float64)                    # (n_ch, 80)
        self.sens_daq = [int(d) for d in z["sens_daq"]]
        self.tray = np.asarray(z["tray"], np.float64)                    # (3, 80)
        self.drives = {k: np.asarray(z[f"drive_{k}"], np.float64) for k in DRIVE_KEYS}
        self.pairs = np.asarray(z["pairs"])                              # (n_pair, 3): ash_r, fem_k, mac
        self.mfreqs = np.asarray(z["mfreqs"], np.float64)                # 33 .ash freqs [Hz]
        f1, _ = self.modes(np.ones(self.np_))
        self.inb = np.where((f1 >= BAND[0]) & (f1 <= BAND[1]))[0]
        self.nM = len(self.inb)
        femk = self.pairs[:, 1].astype(int)
        self.femk = femk                                                 # matched FEM mode indices (frozen)
        self.ashr = self.pairs[:, 0].astype(int)
        self.is_meas = np.isin(self.inb, femk)
        m2f = {int(k): float(self.mfreqs[r]) for r, k in zip(self.ashr, femk)}
        self.meas_f = np.array([m2f.get(int(k), f1[k]) for k in self.inb])
        # measured shapes at live DOFs for the matched modes, unit-normalized
        mm = np.load(MM, allow_pickle=True)
        live = np.asarray(mm["measured"]).reshape(-1)
        sh = np.asarray(mm["shapes"], np.float64).reshape(33, -1)[:, live]
        phm = sh[self.ashr].T                                            # (n_live, n_pair)
        self.phm = phm / (np.linalg.norm(phm, axis=0, keepdims=True) + 1e-30)

    def K(self, theta):
        return self.A_fix + np.einsum("g,gij->ij", np.asarray(theta, np.float64), self.A)

    def modes(self, theta):
        lam, Q = np.linalg.eigh(self.K(theta))
        return np.sqrt(np.clip(lam, 1e-9, None)) / (2 * np.pi), Q

    # ---------------- QOI forward (netcg conventions) ----------------
    def _coef(self, theta, axis, dkey, shapes=None):
        """(coef_i, f_i) for the modal sum. dkey=None -> flat modal drive (netcg spectrum() convention, the
        sharpness/truth-ensemble reference). shapes: {inb_position: (g_j, phid_j, f_j|None)} S2 overrides."""
        f, Q = self.modes(theta)
        fi = f[self.inb].copy()
        g = self.tray[axis] @ Q[:, self.inb]
        phid = self.drives[dkey] @ Q[:, self.inb] if dkey is not None else np.ones(self.nM)
        if shapes is not None:
            for j, (gj, pj, fj) in shapes.items():
                g[j] = gj
                if dkey is not None:
                    phid[j] = pj
                if fj is not None:
                    fi[j] = fj
        return g * phid, fi

    def spectrum_drive(self, theta, axis, dkey, amp=None, fscale=None, shapes=None):
        """net-CG |G|(FGRID); per-drive if dkey given (includes phi_drive), flat modal drive if dkey=None."""
        coef, fi = self._coef(theta, axis, dkey, shapes)
        if fscale is not None:
            fi = fi * fscale
        if amp is not None:
            coef = coef * amp
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        return np.abs(((coef[:, None] * wi[:, None] ** 2) / D).sum(0))

    def spectrum(self, theta, axis, amp=None, fscale=None, shapes=None):
        return self.spectrum_drive(theta, axis, None, amp=amp, fscale=fscale, shapes=shapes)

    def unmeas_frac(self, theta, axis, dkey, hidden=None, shapes=None):
        coef, fi = self._coef(theta, axis, dkey, shapes)
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        contrib = np.abs((coef[:, None] * wi[:, None] ** 2) / D)
        meas = self.is_meas.copy()
        if hidden is not None:
            meas[np.asarray(hidden)] = False
        return contrib[~meas].sum(0) / (contrib.sum(0) + 1e-300)


def truth_ensemble(model, axis, theta_map, extra_hidden=None, n=200, seed=7):
    """Epistemic net-CG truth ensemble (netcg convention): measured tier (1%/0.35), unmeasured tier (6%/0.80);
    extra_hidden demotes measured modes (leave-modes-out truth)."""
    rng = np.random.default_rng(seed)
    meas = model.is_meas.copy()
    if extra_hidden is not None:
        meas[np.asarray(extra_hidden)] = False
    sdf = np.where(meas, SD_F_M, SD_F_U); sda = np.where(meas, SD_A_M, SD_A_U)
    out = []
    for _ in range(n):
        amp = np.exp(rng.normal(0, 1, model.nM) * sda)
        fsc = 1 + rng.normal(0, 1, model.nM) * sdf
        out.append(model.spectrum(theta_map, axis, amp=amp, fscale=fsc))
    return np.array(out)


def statfem_fk_band(model, theta_post, axis, dkey, hidden=None, shapes_fn=None, n_theta=48, n_disc=30, seed=0):
    """statFEM F(k) ensemble band (ALWAYS-ON discrepancy; netcg formulation, A4): smooth 1-oct-correlated
    log-amplitude field, marginal ramping 0.25 -> SD_A_U where unmeasured/hidden modes drive the response.
    dkey=None -> flat modal drive (sharpness/truth reference). shapes_fn(s) -> S2 shapes dict for draw s."""
    rng = np.random.default_rng(seed)
    idx = np.linspace(0, len(theta_post) - 1, min(n_theta, len(theta_post))).astype(int)
    specs = []
    for s in idx:
        th = theta_post[s]
        shp = shapes_fn(s) if shapes_fn is not None else None
        base = model.spectrum_drive(th, axis, dkey, shapes=shp)
        ufrac = model.unmeas_frac(th, axis, dkey, hidden=hidden, shapes=shp)
        marg = 0.25 + (SD_A_U - 0.25) * ufrac
        for _ in range(n_disc):
            zc = np.log(NC.octave_smooth(FGRID, np.exp(rng.normal(0, 1, len(FGRID))), 1.0))
            zc = (zc - zc.mean()) / (zc.std() + 1e-9)
            specs.append(base * np.exp(marg * zc))
    E = np.array(specs)
    return (np.percentile(E, 2.5, 0), np.percentile(E, 50, 0), np.percentile(E, 97.5, 0))


def beck_shapes_fn(model, post, axis, dkey, sub_map):
    """Factory: draw s -> {inb_position: (g, phid, f_rayleigh)} from the S2 inferred shape field.
    sub_map maps ensemble draw index -> posterior row. Unit-normalized inferred shapes (mass = I)."""
    pos_of = {int(k): j for j, k in enumerate(model.inb)}
    positions = [pos_of[int(k)] for k in model.femk]

    def fn(s):
        row = sub_map(s)
        phi = post["phi0"] + post["tau"] * post["raw"][row]          # (80, nm)
        phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
        th = post["theta_post"][row]
        K = model.K(th)
        ray = np.einsum("ik,ij,jk->k", phi, K, phi)
        fr = np.sqrt(np.clip(ray, 1e-9, None)) / (2 * np.pi)
        g = model.tray[axis] @ phi
        pd = model.drives[dkey] @ phi if dkey is not None else np.ones(len(model.femk))
        return {p: (g[j], pd[j], fr[j]) for j, p in enumerate(positions)}

    return fn


# ---------------- held-out-drive answer key (D2: LSQ lives ONLY here) ----------------
def load_cache(dkey):
    c = np.load(CACHE_DIR / f"{dkey}.npz", allow_pickle=True)
    return {"daq": [int(d) for d in c["daq"]], "H1": np.asarray(c["H1"]),
            "freqs": np.asarray(c["freqs"], float), "xyz": tuple(float(x) for x in c["xyz"])}


def answer_key(model, theta_map, axis, dkey, cache, ridge=1e-3):
    """Reconstruct the held-out drive's net-CG force from ITS OWN measured FRFs (truth reconstruction)."""
    f, Q = model.modes(theta_map)
    common = [d for d in cache["daq"] if d in model.sens_daq]
    srows = np.array([model.sens[model.sens_daq.index(d)] for d in common]) @ Q[:, model.inb]  # (Ns,nM)
    H1 = np.array([cache["H1"][cache["daq"].index(d)] for d in common])                        # (Ns,Nf)
    fc = cache["freqs"]; wc = 2 * np.pi * fc
    mi = np.where(model.is_meas)[0]
    fi = model.meas_f[mi]; wi = 2 * np.pi * fi
    D = wi[:, None] ** 2 - wc[None, :] ** 2 + 2j * ZETA * wi[:, None] * wc[None, :]
    phid = model.drives[dkey] @ Q[:, model.inb]
    basis = (-(wc[None, :, None] ** 2)) * (srows[:, None, mi] * phid[mi][None, None, :]) / D.T[None, :, :]
    A = basis.reshape(-1, len(mi)); b = H1.reshape(-1)
    AhA = A.conj().T @ A + ridge * np.eye(len(mi)) * (np.real(np.trace(A.conj().T @ A)) / len(mi))
    a = np.linalg.solve(AhA, A.conj().T @ b)
    g = model.tray[axis] @ Q[:, model.inb]
    coef = a * g[mi] * phid[mi]
    w = 2 * np.pi * FGRID
    Dq = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
    return np.abs(((coef[:, None] * wi[:, None] ** 2) / Dq).sum(0)), len(common)


# ---------------- NUTS likelihoods (S0 / S1 / S2) ----------------
def run_nuts(model, kind, seed=20260702, warmup=1000, samples=1000, chains=4,
             tau=0.3, target_accept=0.9, max_tree=9):
    """kind in {S0, S1, S2}. Returns dict with theta_post (N, np_), diag, extras (raw shapes for S2)."""
    import jax, jax.numpy as jnp
    jax.config.update("jax_enable_x64", True)
    import numpyro, numpyro.distributions as dist
    from numpyro.diagnostics import summary as nuts_summary
    from numpyro.infer import MCMC, NUTS, init_to_median

    A = jnp.asarray(model.A); A_fix = jnp.asarray(model.A_fix)
    npar = model.np_
    femk = jnp.asarray(model.femk)
    tgt = jnp.asarray((model.mfreqs[model.ashr] * 2 * np.pi) ** 2)
    Gash = jnp.asarray(model.ash); phm = jnp.asarray(model.phm)
    nm = len(model.femk)
    phi0 = None
    if kind in ("S1", "S2"):
        lam0_np, Q1 = np.linalg.eigh(model.K(np.ones(npar)))
        phi0 = Q1[:, model.femk]                                       # (80, nm) FEM shapes at theta=1
    phi0j = jnp.asarray(phi0) if phi0 is not None else None
    # S1 degeneracy-safe first-order shape derivative (A7 mitigation; card "subspace-projected forms"):
    # phi_k(theta) = phi0_k + Phi0 @ [ reg_jk * <phi0_j, dK phi0_k> ], reg_jk = D0/(D0^2+delta^2) with
    # D0 = lam0_k - lam0_j (frozen). delta (Tikhonov floor) CAPS the near-degenerate 246-258 Hz denominators
    # so the eigenvector gradient cannot blow up; delta is a documented smoothing (AGENTS Sampler Decision).
    s1_delta = None
    if kind == "S1":
        Phi0_full = jnp.asarray(Q1)                                    # (80, 80) frozen basis
        lam0_all = jnp.asarray(lam0_np)                               # (80,)
        lam0_k = jnp.asarray(lam0_np[model.femk])                     # (nm,)
        gaps = np.diff(np.sort(lam0_np))
        s1_delta = float(0.5 * np.median(gaps))                       # ~half the median modal gap
        K0j = A_fix + jnp.sum(A, 0)                                    # K(theta=1)
        D0 = lam0_k[None, :] - lam0_all[:, None]                      # (80, nm)
        reg = jnp.where(jnp.abs(D0) > 1e-9, D0 / (D0 ** 2 + s1_delta ** 2), 0.0)
        femk_col = jnp.asarray(model.femk)

    def m_S0():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([npar]).to_event(1))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(lt), A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)
        var = (sig * tgt) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt - lam[femk]) ** 2 / var + jnp.log(2 * jnp.pi * var)))

    def m_S1():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([npar]).to_event(1))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        sig_mac = numpyro.sample("sigma_mac", dist.HalfNormal(0.3))
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(lt), A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)            # eigenVALUES only: stable at degeneracy
        var = (sig * tgt) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt - lam[femk]) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        # regularized first-order shape (no eigenVECTOR differentiation of K(theta)):
        dK = K - K0j
        B = Phi0_full.T @ (dK @ Phi0_full[:, femk_col])               # (80, nm) modal participations
        phi = Phi0_full[:, femk_col] + Phi0_full @ (reg * B)          # (80, nm) perturbed shapes
        gp = Gash @ phi
        mac = jnp.sum(gp * phm, 0) ** 2 / (jnp.sum(gp * gp, 0) * jnp.sum(phm * phm, 0) + 1e-30)
        numpyro.factor("mac", -0.5 * jnp.sum((1.0 - mac) ** 2 / sig_mac ** 2
                                             + jnp.log(2 * jnp.pi * sig_mac ** 2)))

    def m_S2():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([npar]).to_event(1))
        raw = numpyro.sample("raw", dist.Normal(0, 1).expand([80, nm]).to_event(2))
        phi = phi0j + tau * raw
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        sig_p = numpyro.sample("sigma_phi", dist.HalfNormal(0.3))
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(lt), A)
        ray = jnp.sum(phi * (K @ phi), 0) / (jnp.sum(phi * phi, 0) + 1e-30)
        var = (sig * tgt) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt - ray) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        gp = Gash @ phi
        mac = jnp.sum(gp * phm, 0) ** 2 / (jnp.sum(gp * gp, 0) * jnp.sum(phm * phm, 0) + 1e-30)
        numpyro.factor("shape", -0.5 * jnp.sum((1.0 - mac) ** 2 / sig_p ** 2
                                               + jnp.log(2 * jnp.pi * sig_p ** 2)))

    mdl = {"S0": m_S0, "S1": m_S1, "S2": m_S2}[kind]
    dense = kind != "S2"                                                # S2 has 80*nm latents -> diag mass
    kern = NUTS(mdl, target_accept_prob=target_accept, init_strategy=init_to_median,
                dense_mass=dense, max_tree_depth=max_tree)
    mcmc = MCMC(kern, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    st = nuts_summary(g, group_by_chain=True)
    diag = {"max_rhat": round(max(float(np.nanmax(v["r_hat"])) for v in st.values()), 4),
            "min_ess": round(min(float(np.nanmin(v["n_eff"])) for v in st.values()), 1),
            "divergences": int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum()),
            "n_chains": chains, "draws": chains * samples}
    diag["div_frac"] = diag["divergences"] / diag["draws"]
    diag["converged"] = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02)
    if kind == "S1":
        diag["s1_shape_deriv"] = "regularized first-order (Tikhonov modal denominators)"
        diag["s1_delta_lambda_floor"] = s1_delta
    out = {"theta_post": np.exp(flat["log_theta"]), "diag": diag,
           "sigma_w2": flat.get("sigma_w2")}
    if kind == "S1":
        out["sigma_mac"] = flat.get("sigma_mac")
    if kind == "S2":
        out["raw"] = flat["raw"]; out["phi0"] = phi0; out["tau"] = tau
        out["sigma_phi"] = flat.get("sigma_phi")
    return out
