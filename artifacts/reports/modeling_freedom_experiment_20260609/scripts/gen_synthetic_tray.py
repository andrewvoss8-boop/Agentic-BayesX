#!/usr/bin/env python3
"""
Synthetic 'tray' modal substrate for the MODELING-FREEDOM / anti-overfitting experiment.

Purpose (methodology, not science): produce a controlled testbed with KNOWN ground truth
so we can later check whether the anti-overfitting protocol's vault/LOO estimate tracks the
TRUE generalization error, and whether a deliberately over-flexible discrepancy that fits the
dev data fails on the held-out vault.

Design (plain English):
- TRUE structure = a 12-DOF cantilever mass-spring chain (one end grounded -> no rigid-body
  zero mode). Springs grouped into 4 stiffness GROUPS; the candidate model the runner will
  calibrate has exactly these 4 group scale factors theta (4 unknowns).
- MODEL-FORM ERROR (the irreducible part the candidate CANNOT represent): the TRUTH adds a
  cross-link 'joint' spring between two non-adjacent nodes (LOCATION + stiffness SEALED in the
  vault). The candidate's chain topology has no such cross-link, so no value of theta can match
  the truth exactly. This is the analog
  of 'missing physics / missing modes' from the project's own lessons. It is precisely what an
  over-flexible additive discrepancy can absorb on dev data but NOT generalize to a held-out
  transfer path -> that is the overfitting we want the vault to expose.
- OBSERVATIONS = first M modal frequencies (Hz) + mode-shape components at S sensor DOFs, each
  with iid Gaussian noise, repeated over several noisy 'tests' (realizations).
- QOI = peak modal-receptance magnitude over a band for a reference forcing path, and a SECOND
  held-out forcing path (different transfer path = an out-of-distribution regime).

Truth (theta_true, joint, noiseless modes, both QOIs, the secret seed) is written ONLY to the
vault dir. The committed public config carries the MODEL FORM and noise levels (which the runner
is allowed to know) but NO truth values and NO seed.

Run:
  SYNTH_SEED=<int> .venv_nuts/bin/python scripts/gen_synthetic_tray.py
If SYNTH_SEED is unset, a random secret seed is drawn and sealed to the vault.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN = os.path.join(HERE, "runner_opus", "inputs", "train")
DEV   = os.path.join(HERE, "runner_opus", "inputs", "dev")
VAULT = os.path.join(HERE, "vault", "tray")
for d in (TRAIN, DEV, VAULT):
    os.makedirs(d, exist_ok=True)

# ---- fixed, PUBLIC structural config (runner is allowed to know these) -------------------
N        = 12          # DOFs (nodes), masses all = 1.0 (synthetic kg)
GROUPS   = 4           # stiffness groups; springs split contiguously into GROUPS
K0       = 3.0e6       # nominal per-spring stiffness (synthetic N/m); scaled to a structural band
M_MODES  = 6           # number of modal frequencies observed
SENSOR_DOFS = [0, 2, 3, 5, 6, 8, 9, 11]   # 8 sensor DOFs (0-indexed)
ZETA     = 0.02        # modal damping ratio used for the QOI receptance
FREQ_BAND_HZ = (10.0, 600.0)
QOI_REF_PATH     = {"out": 11, "in": 0}   # reference forcing/response transfer path
QOI_HELDOUT_PATH = {"out": 5,  "in": 8}   # held-out (different) transfer path = OOD regime
N_TRAIN, N_DEV, N_VAULT = 8, 4, 6         # noisy realizations ('tests') per split
SIGMA_F_REL = 0.005    # frequency noise: 0.5% of each modal frequency
SIGMA_PHI   = 0.02     # mode-shape component noise (on unit-normalized shapes)

# ---- SECRET truth parameters: REDACTED after sealing -------------------------------------
# At generation time this block defined THETA_TRUE (the 4 true group stiffness scale factors)
# and JOINT (the hidden cross-link that causes the model-form error). Those VALUES are exactly
# the answer the runner must not see, so they are redacted here and preserved ONLY in the sealed
# vault truth (vault/tray/truth.json -> uploaded to Google Drive, deleted locally).
# To reproduce the exact dataset at grading: restore vault/tray/truth.json and read
# truth["theta_true"] and truth["joint"], then re-run with the sealed SYNTH_SEED.
# (As committed, this script will NOT reproduce the data — that is intentional; the truth is vaulted.)
THETA_TRUE = None  # SEALED — vault/tray/truth.json["theta_true"]
JOINT = None       # SEALED — vault/tray/truth.json["joint"]
if THETA_TRUE is None:
    raise SystemExit("gen_synthetic_tray.py is SEALED: truth params redacted. "
                     "Restore vault/tray/truth.json (theta_true, joint, secret_seed) to re-generate.")


def build_K(theta, joint=None):
    """Assemble the 12x12 stiffness for the grounded chain. theta scales 4 contiguous groups.
    Optional cross-link joint (the model-form error) added between two non-adjacent nodes."""
    n_springs = N  # N internal/ground springs for a grounded chain of N masses
    # map each spring to a group
    edges = []
    # ground spring: node 0 to ground
    edges.append(("ground", 0))
    # chain springs: node i to node i+1
    for i in range(N - 1):
        edges.append((i, i + 1))
    assert len(edges) == n_springs
    group_of = np.floor(np.arange(n_springs) / (n_springs / GROUPS)).astype(int)
    group_of = np.clip(group_of, 0, GROUPS - 1)
    K = np.zeros((N, N))
    for s, (a, b) in enumerate(edges):
        k = K0 * theta[group_of[s]]
        if a == "ground":
            K[b, b] += k
        else:
            K[a, a] += k; K[b, b] += k; K[a, b] -= k; K[b, a] -= k
    if joint is not None:
        i, j, kj = joint["i"], joint["j"], joint["k"]
        K[i, i] += kj; K[j, j] += kj; K[i, j] -= kj; K[j, i] -= kj
    return K


def modes(K):
    """Generalized modes with M=I. Returns freqs(Hz) ascending and unit-norm, sign-fixed shapes."""
    w2, V = np.linalg.eigh(K)            # M = identity
    w2 = np.clip(w2, 0, None)
    f = np.sqrt(w2) / (2 * np.pi)
    # sign convention: largest-magnitude component positive
    for m in range(V.shape[1]):
        k = np.argmax(np.abs(V[:, m]))
        if V[k, m] < 0:
            V[:, m] *= -1
    return f, V


def qoi_peak_receptance(K, path, zeta=ZETA, band=FREQ_BAND_HZ, n=2000):
    """Peak |H_{out,in}(f)| over the band, modal receptance with uniform modal damping."""
    f, V = modes(K)
    w = 2 * np.pi * f
    fs = np.linspace(band[0], band[1], n)
    ws = 2 * np.pi * fs
    out, inn = path["out"], path["in"]
    H = np.zeros_like(ws, dtype=complex)
    for m in range(len(w)):
        num = V[out, m] * V[inn, m]
        H += num / (w[m] ** 2 - ws ** 2 + 2j * zeta * w[m] * ws)
    return float(np.max(np.abs(H)))


def main():
    seed_env = os.environ.get("SYNTH_SEED")
    if seed_env is None:
        secret_seed = int(np.random.SeedSequence().generate_state(1)[0])
    else:
        secret_seed = int(seed_env)
    rng = np.random.default_rng(secret_seed)

    K_true = build_K(THETA_TRUE, JOINT)
    f_true, V_true = modes(K_true)
    f_obs_true = f_true[:M_MODES]
    phi_obs_true = V_true[np.ix_(SENSOR_DOFS, range(M_MODES))]  # (S, M)

    # sanity: model-form error is real (candidate chain w/o joint cannot match truth at theta_true)
    K_nojoint = build_K(THETA_TRUE, None)
    f_nojoint, _ = modes(K_nojoint)
    modeform_shift_hz = np.abs(f_true[:M_MODES] - f_nojoint[:M_MODES])

    qoi_ref = qoi_peak_receptance(K_true, QOI_REF_PATH)
    qoi_heldout = qoi_peak_receptance(K_true, QOI_HELDOUT_PATH)

    def draw(n_real):
        F = np.empty((n_real, M_MODES))
        P = np.empty((n_real, len(SENSOR_DOFS), M_MODES))
        for r in range(n_real):
            F[r] = f_obs_true * (1 + rng.normal(0, SIGMA_F_REL, M_MODES))
            P[r] = phi_obs_true + rng.normal(0, SIGMA_PHI, phi_obs_true.shape)
        return F, P

    Ftr, Ptr = draw(N_TRAIN)
    Fdev, Pdev = draw(N_DEV)
    Fvault, Pvault = draw(N_VAULT)

    public_cfg = dict(
        substrate="synthetic_tray_modal", N=N, groups=GROUPS, k0_nominal=K0,
        m_modes=M_MODES, sensor_dofs=SENSOR_DOFS, zeta=ZETA, freq_band_hz=list(FREQ_BAND_HZ),
        qoi_ref_path=QOI_REF_PATH, qoi_heldout_path=QOI_HELDOUT_PATH,
        sigma_f_rel=SIGMA_F_REL, sigma_phi=SIGMA_PHI,
        n_train=N_TRAIN, n_dev=N_DEV, n_vault=N_VAULT,
        candidate_model="grounded 12-DOF chain, 4 group stiffness scale factors theta; "
                        "NO cross-link joint (the model-form error the runner must contend with)",
        note="Truth values, the joint, noiseless modes, both QOIs, and the seed are NOT here. "
             "They are sealed in the vault.",
    )

    # ---- write runner inputs (train + dev): observations + public config only ----
    np.savez(os.path.join(TRAIN, "train.npz"), freqs_hz=Ftr, shapes=Ptr,
             sensor_dofs=np.array(SENSOR_DOFS))
    np.savez(os.path.join(DEV, "dev.npz"), freqs_hz=Fdev, shapes=Pdev,
             sensor_dofs=np.array(SENSOR_DOFS))
    for d in (TRAIN, DEV):
        with open(os.path.join(d, "config_public.json"), "w") as fh:
            json.dump(public_cfg, fh, indent=2)

    # ---- write VAULT (sealed truth) ----
    np.savez(os.path.join(VAULT, "vault_observations.npz"),
             freqs_hz=Fvault, shapes=Pvault, sensor_dofs=np.array(SENSOR_DOFS))
    truth = dict(
        secret_seed=secret_seed,
        theta_true=THETA_TRUE.tolist(),
        joint=JOINT,
        true_modal_freqs_hz=f_true[:M_MODES].tolist(),
        modeform_shift_hz=modeform_shift_hz.tolist(),
        qoi_ref_truth=qoi_ref,
        qoi_heldout_truth=qoi_heldout,
        qoi_ref_path=QOI_REF_PATH, qoi_heldout_path=QOI_HELDOUT_PATH,
        noise=dict(sigma_f_rel=SIGMA_F_REL, sigma_phi=SIGMA_PHI),
        notes="Grade finalists against qoi_ref_truth (in-regime) and qoi_heldout_truth (OOD). "
              "True generalization error is computable here because truth is known.",
    )
    with open(os.path.join(VAULT, "truth.json"), "w") as fh:
        json.dump(truth, fh, indent=2)

    # ---- non-secret validation summary (safe to print/commit) ----
    print("[synthetic tray generated]")
    print("  observed modal band (Hz):", np.round(f_obs_true, 2).tolist())
    print("  model-form shift truth-vs-noJoint (Hz):", np.round(modeform_shift_hz, 2).tolist(),
          "  -> max", round(float(modeform_shift_hz.max()), 2),
          "(this is the irreducible error a flexible discrepancy can overfit)")
    print("  realizations: train", N_TRAIN, "dev", N_DEV, "vault", N_VAULT)
    print("  QOI defined; truth values sealed to vault/tray/truth.json")
    print("  seed sealed to vault (not printed).")


if __name__ == "__main__":
    main()
