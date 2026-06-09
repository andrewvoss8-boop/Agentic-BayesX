"""Load + sign-align synthetic modal observations.

Mode shapes from an eigensolver are defined up to sign. We align every realization's mode j
to a common reference (the sign-aligned train mean) so the Gaussian shape likelihood is valid.
Signs are consistent across noisy realizations of one truth, so this is a benign preprocessing.
"""
import numpy as np
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_npz(name):
    d = np.load(os.path.join(_HERE, "inputs", name, f"{name}.npz"))
    return np.asarray(d["freqs_hz"]), np.asarray(d["shapes"])  # (R,6),(R,8,6)


def _build_reference(shapes):
    """shapes: (R,8,6). Return reference (8,6) unit-norm, sign-stable."""
    R, S, M = shapes.shape
    ref = shapes[0].copy()
    for _ in range(3):  # a couple of passes for a stable mean
        acc = np.zeros((S, M))
        for r in range(R):
            for j in range(M):
                s = np.sign(shapes[r, :, j] @ ref[:, j]) or 1.0
                acc[:, j] += s * shapes[r, :, j]
        acc /= R
        ref = acc / np.linalg.norm(acc, axis=0, keepdims=True)
    return ref


def _align(shapes, ref):
    out = shapes.copy()
    R, S, M = shapes.shape
    for r in range(R):
        for j in range(M):
            s = np.sign(shapes[r, :, j] @ ref[:, j]) or 1.0
            out[r, :, j] = s * shapes[r, :, j]
    return out


def load_aligned():
    ftr, str_ = _load_npz("train")
    fdv, sdv = _load_npz("dev")
    ref = _build_reference(np.concatenate([str_, sdv], axis=0))
    return {
        "train_f": ftr, "train_phi": _align(str_, ref),
        "dev_f": fdv, "dev_phi": _align(sdv, ref),
        "ref": ref,
    }


def coarsen(data, keep_modes):
    """Resolution-ablation: keep only the first `keep_modes` modes."""
    out = dict(data)
    out["train_f"] = data["train_f"][:, :keep_modes]
    out["train_phi"] = data["train_phi"][:, :, :keep_modes]
    out["dev_f"] = data["dev_f"][:, :keep_modes]
    out["dev_phi"] = data["dev_phi"][:, :, :keep_modes]
    out["ref"] = data["ref"][:, :keep_modes]
    return out


if __name__ == "__main__":
    d = load_aligned()
    print("train_f", d["train_f"].shape, "train_phi", d["train_phi"].shape)
    print("ref norms", np.linalg.norm(d["ref"], axis=0))
    # check alignment: cross-realization MAC near 1
    p = d["train_phi"]
    macs = []
    for j in range(6):
        a = p[0, :, j]; b = p[1, :, j]
        macs.append((a @ b) ** 2 / ((a @ a) * (b @ b)))
    print("realiz0-vs-1 MAC per mode", np.round(macs, 4))
