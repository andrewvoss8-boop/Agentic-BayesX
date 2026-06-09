"""Config-driven numpyro model + vectorized prediction for the synthetic modal task.

Likelihood (whole modal vector, the default):
  log f_obs[r,j] ~ Normal( log f_model_j(theta) + d_j , sigma_f )
  phi_obs[r,:,j] ~ Normal( s_j * phi_model_sens[:,j] + g[:,j] , sigma_phi )
where d_j is a per-mode frequency discrepancy and g a per-mode shape discrepancy.

Discrepancy variants (cfg['disc']):
  'none'        : no d, no g (pure theta; misspecified by the missing joint)
  'freq'        : per-mode shared d_j ~ Normal(0, tau_f)            [earns-its-keep candidate]
  'freqshape'   : freq + per-mode shape g[:,j] ~ Normal(0, tau_phi)
  'probe'       : per-mode-per-REALIZATION d[r,j] ~ Normal(0, tau)  [deliberate overfit]

cfg knobs: prior_width (theta logN sd), tau_f_scale, tau_phi_scale, like ('full'|'freq'),
           noncentered (bool), infer_noise (bool).
"""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np
import numpyro
import numpyro.distributions as dist
from forward import modes_sens, SENSORS

EPS = 1e-12


def _model_modes(theta, nmodes):
    f, Vs = modes_sens(theta, nmodes)          # f:(M,), Vs:(8,M)
    return jnp.log(f), Vs


def _align_sign(Vs, ref):
    # ref:(8,M). s_j = sign(<Vs_j, ref_j>); locally constant -> ok for HMC
    s = jnp.sign(jnp.sum(Vs * ref, axis=0) + EPS)
    return Vs * s[None, :]


def make_model(cfg, ref):
    M = cfg["nmodes"]
    disc = cfg["disc"]
    pw = cfg["prior_width"]
    like = cfg.get("like", "full")
    nc = cfg.get("noncentered", True)
    infer_noise = cfg.get("infer_noise", True)
    refj = jnp.asarray(ref)

    def model(train_f, train_phi):
        R = train_f.shape[0]
        log_theta = numpyro.sample("log_theta", dist.Normal(jnp.zeros(4), pw))
        theta = numpyro.deterministic("theta", jnp.exp(log_theta))
        logf_m, Vs = _model_modes(theta, M)
        Vs = _align_sign(Vs, refj)

        # noise
        if infer_noise:
            sigma_f = numpyro.sample("sigma_f", dist.HalfNormal(0.02))
            sigma_phi = numpyro.sample("sigma_phi", dist.HalfNormal(0.05))
        else:
            sigma_f = cfg.get("sigma_f_fixed", 0.005)
            sigma_phi = cfg.get("sigma_phi_fixed", 0.02)

        # frequency discrepancy
        if disc in ("freq", "freqshape"):
            tau_f = numpyro.sample("tau_f", dist.HalfNormal(cfg.get("tau_f_scale", 0.05)))
            if nc:
                z = numpyro.sample("d_z", dist.Normal(jnp.zeros(M), 1.0))
                d = numpyro.deterministic("d", tau_f * z)
            else:
                d = numpyro.sample("d", dist.Normal(jnp.zeros(M), tau_f))
            logf_pred = logf_m + d
        elif disc == "probe":
            tau = numpyro.sample("tau", dist.HalfNormal(cfg.get("tau_f_scale", 0.2)))
            if nc:
                z = numpyro.sample("d_z", dist.Normal(jnp.zeros((R, M)), 1.0))
                d = numpyro.deterministic("d", tau * z)             # per realization!
            else:
                d = numpyro.sample("d", dist.Normal(jnp.zeros((R, M)), tau))
            logf_pred = logf_m[None, :] + d                         # (R,M)
        else:  # none
            logf_pred = logf_m

        # shape discrepancy
        if disc == "freqshape":
            tau_phi = numpyro.sample("tau_phi", dist.HalfNormal(cfg.get("tau_phi_scale", 0.05)))
            if nc:
                zg = numpyro.sample("g_z", dist.Normal(jnp.zeros((8, M)), 1.0))
                g = numpyro.deterministic("g", tau_phi * zg)
            else:
                g = numpyro.sample("g", dist.Normal(jnp.zeros((8, M)), tau_phi))
            Vs_pred = Vs + g
        else:
            Vs_pred = Vs

        # frequency likelihood
        if logf_pred.ndim == 1:
            numpyro.sample("y_f", dist.Normal(logf_pred[None, :], sigma_f), obs=jnp.log(train_f))
        else:
            numpyro.sample("y_f", dist.Normal(logf_pred, sigma_f), obs=jnp.log(train_f))

        # shape likelihood (whole modal vector unless like=='freq')
        if like == "full":
            numpyro.sample("y_phi", dist.Normal(Vs_pred[None, :, :], sigma_phi), obs=train_phi)

    return model


# ----------------- vectorized prediction (outside the model) -----------------
_modes_batch = jax.jit(jax.vmap(lambda th, nm: modes_sens(th, nm), in_axes=(0, None)),
                       static_argnums=(1,))


def predict_pointwise(draws, f_obs, phi_obs, cfg, ref):
    """Return pointwise log predictive density arrays for a set of observations.
    Uses the posterior draws to form the predictive mixture.
    Returns dict with 'll_f' (D,R,M) and 'll_phi' (D,R,M) (shape ll summed over 8 sensors).
    """
    M = cfg["nmodes"]
    like = cfg.get("like", "full")
    theta = np.asarray(draws["theta"])                      # (D,4)
    D = theta.shape[0]
    R = f_obs.shape[0]
    f_m, Vs = _modes_batch(jnp.asarray(theta), M)           # (D,M) FREQUENCY,(D,8,M)
    logf_m = np.log(np.asarray(f_m)); Vs = np.asarray(Vs)   # convert to log-frequency
    refn = np.asarray(ref)
    s = np.sign(np.sum(Vs * refn[None, :, :], axis=1) + EPS)  # (D,M)
    Vs = Vs * s[:, None, :]

    if cfg.get("infer_noise", True):
        sf = np.asarray(draws["sigma_f"])                   # (D,)
        sp = np.asarray(draws["sigma_phi"])
    else:
        sf = np.full(D, cfg.get("sigma_f_fixed", 0.005))
        sp = np.full(D, cfg.get("sigma_phi_fixed", 0.02))

    disc = cfg["disc"]
    if disc in ("freq", "freqshape"):
        d = np.asarray(draws["d"])                          # (D,M)
        logf_pred = logf_m + d                              # (D,M)
        logf_pred = logf_pred[:, None, :]                   # (D,1,M) broadcast over R
    elif disc == "probe":
        # per-realization d only defined for TRAIN realizations; for held-out we must
        # marginalize using tau (the discrepancy hyperprior) -> predictive includes tau.
        tau = np.asarray(draws["tau"])                      # (D,)
        logf_pred = logf_m[:, None, :]                      # (D,1,M); extra var added below
        probe_extra = tau                                   # used to inflate sigma for held-out
    else:
        logf_pred = logf_m[:, None, :]

    logf_obs = np.log(f_obs)                                # (R,M)
    # freq loglik (D,R,M)
    if disc == "probe":
        var = sf[:, None, None] ** 2 + (probe_extra[:, None, None] ** 2)
        ll_f = -0.5 * np.log(2 * np.pi * var) - 0.5 * (logf_obs[None] - logf_pred) ** 2 / var
    else:
        var = sf[:, None, None] ** 2
        ll_f = -0.5 * np.log(2 * np.pi * var) - 0.5 * (logf_obs[None] - logf_pred) ** 2 / var

    if like == "full":
        if disc == "freqshape":
            g = np.asarray(draws["g"])                      # (D,8,M)
            Vs_pred = Vs + g
        else:
            Vs_pred = Vs
        Vs_pred = Vs_pred[:, None, :, :]                    # (D,1,8,M)
        diff = phi_obs[None] - Vs_pred                      # (D,R,8,M)
        vp = sp[:, None, None, None] ** 2
        ll_phi = np.sum(-0.5 * np.log(2 * np.pi * vp) - 0.5 * diff ** 2 / vp, axis=2)  # (D,R,M)
    else:
        ll_phi = np.zeros_like(ll_f)
    return {"ll_f": ll_f, "ll_phi": ll_phi}


def lpd_total(pw):
    """Held-out log predictive density: sum over observation units of logsumexp_draws - logD."""
    from scipy.special import logsumexp
    ll = pw["ll_f"] + pw["ll_phi"]                          # (D,R,M)
    D = ll.shape[0]
    per_unit = logsumexp(ll, axis=0) - np.log(D)            # (R,M)
    return float(np.sum(per_unit))


def waic(pw):
    from scipy.special import logsumexp
    ll = (pw["ll_f"] + pw["ll_phi"]).reshape(pw["ll_f"].shape[0], -1)  # (D, units)
    D = ll.shape[0]
    lppd = logsumexp(ll, axis=0) - np.log(D)
    p_waic = np.var(ll, axis=0, ddof=1)
    elpd = lppd - p_waic
    return float(np.sum(elpd)), float(np.sum(p_waic))
