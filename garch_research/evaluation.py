"""Net performance, continuous-account regime slices, and variance forecast losses."""
import numpy as np
import pandas as pd
from .config import TRADING_DAYS, STRATEGIES, REGIMES


def drawdown(returns):
    equity = (1 + returns).cumprod()
    # Include initial wealth 1 even when the first observed return is negative.
    return equity / equity.cummax().clip(lower=1.) - 1


def performance(net_returns, weight, turnover=None, cost=None, cost_value=None, nav_before=None):
    r = net_returns.astype(float)
    if len(r) == 0 or not np.isfinite(r).all() or (r <= -1).any():
        raise ValueError('Need finite, solvent portfolio returns')
    growth = float(np.prod(1+r))
    cagr = growth**(TRADING_DAYS/len(r)) - 1
    vol = float(r.std(ddof=1) * np.sqrt(TRADING_DAYS)) if len(r) > 1 else 0.
    mdd = float(drawdown(r).min())
    result = {'Observations': len(r), 'Start': str(r.index[0].date()), 'End': str(r.index[-1].date()),
        'Total Return': growth-1, 'CAGR': cagr, 'Annualized Volatility': vol,
        'Sharpe (rf=0)': float(r.mean()*TRADING_DAYS/vol) if vol > 0 else np.nan,
        'Maximum Drawdown': mdd, 'Calmar': cagr/abs(mdd) if mdd < 0 else np.nan,
        'Average Exposure': float(weight.mean())}
    # Never reconstruct actual turnover from target-weight differences.
    result['Annualized Turnover'] = float(turnover.mean()*TRADING_DAYS) if turnover is not None else np.nan
    result['Position Changes'] = int((turnover > 1e-10).sum()) if turnover is not None else np.nan
    result['Sum Cost Fractions'] = float(cost.sum()) if cost is not None else np.nan
    result['Total Costs / Starting Capital'] = (float(cost_value.sum()/nav_before.iloc[0])
        if cost_value is not None and nav_before is not None else np.nan)
    return result


def summarize(d):
    rows = []
    for s in STRATEGIES:
        def col(name):
            return d[s + '_' + name]
        rows.append({'Strategy': s, **performance(col('net_return'), col('weight'),
            col('turnover'), col('cost'), col('cost_value'), col('nav_before'))})
    return pd.DataFrame(rows)


def regimes(d):
    rows = []
    for regime, (start, end) in REGIMES.items():
        subset = d.loc[start:end]
        if len(subset) >= 2:
            m = summarize(subset)
            m.insert(0, 'Regime', regime)
            rows.append(m)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def forecast_losses(d):
    rows = []
    segments = {'All OOS': (d.index.min(), d.index.max()), **REGIMES}
    for regime, (start, end) in segments.items():
        sub = d.loc[start:end]
        if len(sub) < 2:
            continue
        realized = sub.log_return.pow(2)
        for model in ('rolling', 'garch'):
            h = sub[model + '_variance']
            if not (np.isfinite(h).all() and (h > 0).all()):
                raise ValueError('Invalid variance forecasts in evaluation')
            error = h - realized
            rows.append({'Regime': regime, 'Model': model, 'Observations': len(sub),
                'MSE variance': float(error.pow(2).mean()), 'MAE variance': float(error.abs().mean()),
                'QLIKE': float((np.log(h) + realized/h).mean())})
    return pd.DataFrame(rows)
