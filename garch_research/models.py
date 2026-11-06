"""Causal rolling GARCH and historical variance forecasts, indexed by origin date."""
import warnings
import numpy as np
import pandas as pd
from arch import arch_model
from .config import Config, TRADING_DAYS


def fit_garch(sample):
    """Percent log returns, genuinely zero mean; arch handles likelihood initialization."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = arch_model(np.asarray(sample, dtype=float), mean='Zero', vol='GARCH',
                            p=1, q=1, dist='normal', rescale=False).fit(
                            disp='off', show_warning=False, options={'maxiter': 500})
    p = result.params
    omega, alpha, beta = (float(p[k]) for k in ('omega', 'alpha[1]', 'beta[1]'))
    variance = float(result.forecast(horizon=1, reindex=False).variance.iloc[-1, 0])
    valid = (result.convergence_flag == 0 and np.isfinite([omega, alpha, beta, variance]).all()
             and omega > 0 and min(alpha, beta) >= 0 and alpha + beta <= 1 + 1e-8
             and variance > 0)
    diag = {'omega_percent_squared': omega, 'alpha': alpha, 'beta': beta,
            'persistence': alpha + beta, 'near_integrated': alpha + beta >= .995,
            'convergence_flag': int(result.convergence_flag), 'accepted': bool(valid),
            'optimizer_message': str(result.optimization_result.message),
            'loglikelihood': float(result.loglikelihood),
            'warnings': '; '.join(str(w.message) for w in caught)}
    return (omega, alpha, beta), variance, diag


def forecast(log_returns, config=Config()):
    """Rows are close-t origins; variance predicts squared log return at t+1.

    Monthly refits use only the trailing sample. Between refits update the last
    forecast with the newly observed shock. A failed fit uses trailing historical
    variance until the next scheduled refit, and is explicitly flagged.
    """
    # Permit only the first undefined return; internal gaps must not compress time.
    r = log_returns.astype(float)
    if len(r) and pd.isna(r.iloc[0]):
        r = r.iloc[1:]
    if not r.index.is_monotonic_increasing or r.index.has_duplicates or not np.isfinite(r).all():
        raise ValueError('Returns require finite values and unique increasing dates')
    if len(r) < config.training_days:
        raise ValueError('Insufficient returns for training window')
    x = r.to_numpy() * 100
    out = pd.DataFrame(index=r.index)
    out['log_return'] = r
    out['rolling_variance'] = r.rolling(config.rolling_days).var(ddof=1)
    vout = np.full(len(r), np.nan)
    status = np.full(len(r), 'warmup', dtype=object)
    records = []
    params, v = None, None
    first = config.training_days - 1
    for t in range(first, len(r)):
        if (t - first) % config.refit_every == 0:
            sample = x[t - config.training_days + 1:t + 1]
            try:
                candidate, next_v, diag = fit_garch(sample)
                params, v = (candidate, next_v) if diag['accepted'] else (None, None)
            except Exception as exc:
                params, v = None, None
                diag = {'accepted': False, 'convergence_flag': -1,
                        'optimizer_message': f'{type(exc).__name__}: {exc}'}
            records.append({'origin': r.index[t], 'training_start': r.index[t-config.training_days+1],
                            'training_end': r.index[t], 'observations': len(sample), **diag})
        elif params is not None:
            omega, alpha, beta = params
            v = omega + alpha * x[t]**2 + beta * v
        if params is None:
            vout[t] = max(float(np.var(x[t-config.training_days+1:t+1], ddof=1))/10000, 1e-12)
            status[t] = 'historical_fallback'
        else:
            vout[t] = v / 10000
            status[t] = 'garch'
    out['garch_variance'] = vout
    out['garch_status'] = status
    for model in ('rolling', 'garch'):
        out[model + '_vol'] = np.sqrt(out[model + '_variance'] * TRADING_DAYS)
    out.index.name = 'origin'
    return out, pd.DataFrame(records)


def garch_one_day_ahead(log_returns, training_days=504, refit_every=21):
    from dataclasses import replace
    return forecast(log_returns, replace(Config(), training_days=training_days,
                    refit_every=refit_every))[0]['garch_vol'].rename('garch_forecast')
