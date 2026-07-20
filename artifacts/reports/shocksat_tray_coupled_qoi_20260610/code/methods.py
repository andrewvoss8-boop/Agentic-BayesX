"""Environment synthesis + the three analysis methods (contracts C6, C7, C9).

- synth_input: band-limited Gaussian stationary base acceleration (C7).
  Synthesized in the frequency domain with iid complex Gaussian coefficients
  -> the record is periodic-stationary, so FRF multiplication is the EXACT
  linear time-history solution (no circular-convolution leakage; D5/A18).
- srs: maximax absolute-acceleration SRS, Smallwood ramp-invariant filter.
- modal_srs_force / miles_force: the two shortcut methods under test.

Units: SI (m/s^2, N, Hz); input spec given in g^2/Hz for readability.
"""
import numpy as np
from scipy.signal import lfilter

G0 = 9.80665


def synth_input(seed, T=20.0, fs=2048.0, f1=20.0, f2=250.0, W0_g2=0.01):
    """One 3-axis realization. Returns dict(t, a (N,3) m/s^2, freqs (nf,),
    A (nf,3) rfft coefficients, df, W0_SI, grms_SI)."""
    rng = np.random.default_rng(seed)
    N = int(T * fs)
    freqs = np.fft.rfftfreq(N, 1/fs)
    nf = len(freqs)
    band = (freqs >= f1) & (freqs <= f2)
    df = freqs[1] - freqs[0]
    W0 = W0_g2 * G0**2                       # (m/s^2)^2/Hz one-sided
    # one-sided PSD W0 over band: E|X_k|^2 = W0*df*(N/ ... using numpy rfft
    # convention x = irfft(X): X_k = sum x_n e^{-2pi i k n/N}; PSD_k =
    # 2|X_k|^2/(N*fs) => |X_k| = sqrt(W0*N*fs/2) on average.
    amp = np.sqrt(W0 * N * fs / 2.0)
    A = np.zeros((nf, 3), complex)
    z = (rng.standard_normal((band.sum(), 3)) +
         1j*rng.standard_normal((band.sum(), 3))) / np.sqrt(2.0)
    A[band] = amp * z
    a = np.fft.irfft(A, n=N, axis=0)
    grms = float(np.sqrt(np.mean(a**2)))
    return dict(t=np.arange(N)/fs, a=a, freqs=freqs, A=A, df=df,
                W0_SI=W0, f1=f1, f2=f2, fs=fs, N=N,
                grms_SI_target=float(np.sqrt(W0*(f2-f1))), grms_SI=grms,
                seed=int(seed))


def srs(accel, fs, fn, Q):
    """Maximax absolute-acceleration SRS (contract C6).
    accel: (N,) m/s^2; fn: array of natural freqs [Hz]; Q scalar.
    Smallwood ramp-invariant digital recursive filter (1981).
    Returns (len(fn),) peak |absolute acceleration| in m/s^2."""
    accel = np.asarray(accel, float)
    out = np.zeros(len(fn))
    dt = 1.0 / fs
    zeta = 1.0 / (2.0*Q)
    for i, f in enumerate(np.asarray(fn, float)):
        wn = 2*np.pi*f
        wd = wn*np.sqrt(1 - zeta**2)
        E = np.exp(-zeta*wn*dt)
        K = wd*dt
        C = E*np.cos(K)
        S = E*np.sin(K)
        Sp = S/K
        b0 = 1.0 - Sp
        b1 = 2.0*(Sp - C)
        b2 = E**2 - Sp
        a1 = -2.0*C
        a2 = E**2
        y = lfilter([b0, b1, b2], [1.0, a1, a2], accel)
        out[i] = np.max(np.abs(y))
    return out


def srs_grid(f_lo=10.0, f_hi=1000.0, per_octave=24):
    n = int(np.ceil(per_octave*np.log2(f_hi/f_lo))) + 1
    return f_lo * 2.0**(np.arange(n)/per_octave)


def modal_srs_force(chain, env, Q, f_band=(10.0, 1000.0), srs_cache=None):
    """Modal-SRS force estimate per axis (contract C6).
    F_d = sqrt( sum_k [m_eff*SRS_d(f_k,Q)]^2 + [m_resid*peak|a_d|]^2 ).
    Uses chain fixed-base modes; m_eff,k,d = Gamma[k,d]^2.
    srs_cache: optional dict {(seed,Q): (fn_grid, SRS (nfn,3))} to reuse."""
    f = chain["f"]
    use = (f >= f_band[0]) & (f <= f_band[1])
    G2 = chain["Gamma"][use, :3]**2          # m_eff (nm_use, 3) translations
    fk = f[use]
    key = (env["seed"], Q)
    if srs_cache is not None and key in srs_cache:
        fn, S = srs_cache[key]
    else:
        fn = srs_grid(f_band[0], f_band[1])
        S = np.stack([srs(env["a"][:, d], env["fs"], fn, Q) for d in range(3)], 1)
        if srs_cache is not None:
            srs_cache[key] = (fn, S)
    Sk = np.stack([np.interp(np.log(fk), np.log(fn), S[:, d]) for d in range(3)], 1)
    m_rb = np.diag(chain["M_rb"])[:3]
    m_resid = np.clip(m_rb - G2.sum(axis=0), 0.0, None)
    peak_a = np.max(np.abs(env["a"]), axis=0)
    F = np.sqrt(np.sum((G2*Sk)**2, axis=0) + (m_resid*peak_a)**2)
    return dict(F=F, m_resid=m_resid.tolist(), n_modes=int(use.sum()),
                Q=Q, combination="SRSS+residual")


def miles_force(chain, env, Q, f_band=(10.0, 1000.0)):
    """PSD/Miles 3-sigma envelope per axis (contract C9).
    sigma_F^2 = sum_k [m_eff*sqrt((pi/2) f_k Q W(f_k))]^2 + [m_resid*grms]^2;
    report 3*sigma. W = the ANALYTIC flat input PSD (zero outside band)."""
    f = chain["f"]
    use = (f >= f_band[0]) & (f <= f_band[1])
    fk = f[use]
    G2 = chain["Gamma"][use, :3]**2
    W = np.where((fk >= env["f1"]) & (fk <= env["f2"]), env["W0_SI"], 0.0)
    sig_modal2 = np.sum((G2 * np.sqrt((np.pi/2)*fk*Q*W)[:, None])**2, axis=0)
    m_rb = np.diag(chain["M_rb"])[:3]
    m_resid = np.clip(m_rb - G2.sum(axis=0), 0.0, None)
    grms = env["grms_SI_target"]
    sig = np.sqrt(sig_modal2 + (m_resid*grms)**2)
    n_edge = int(np.sum((fk > env["f2"]) | (fk < env["f1"])))
    return dict(F=3.0*sig, sigma=sig, m_resid=m_resid.tolist(),
                n_modes_outside_band=n_edge, Q=Q,
                label="3-sigma ENVELOPE (true ~20s Gaussian peak factor ~3.9-4.2 sigma)")


def peak_force_time(F_spec, N):
    """Per-axis peak |F_d(t)| from interface force spectra (nf,6) -> (3,)."""
    Ft = np.fft.irfft(F_spec[:, :3], n=N, axis=0)
    return np.max(np.abs(Ft), axis=0), Ft
