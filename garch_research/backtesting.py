"""Self-financing daily accounting with fees on actual traded notional."""
import numpy as np
import pandas as pd
from .config import Config, TRADING_DAYS, STRATEGIES
from .strategies import executable_weights


def simulate(simple_returns, weights, cost_bps=5., cash_annual=0., *,
             cash_returns=None, borrowing_returns=None, trade_mask=None):
    """Weights are fractions of *post-fee* NAV held over each dated return.

    Let a be risky holdings/pretrade NAV, w target, k proportional cost. Solve
    c = k*abs(w*(1-c)-a) exactly. The risky holding drifts with market returns,
    so unchanged fractional targets may still require trades. Initial holdings
    are cash; ending positions are marked to market without forced liquidation.
    """
    if not simple_returns.index.equals(weights.index):
        raise ValueError('Returns and weights must have identical dates')
    if not np.isfinite(simple_returns).all() or not np.isfinite(weights).all():
        raise ValueError('Returns and weights must be finite')
    if (simple_returns <= -1).any() or (weights < 0).any() or cost_bps < 0:
        raise ValueError('Invalid simple return, weight, or cost')
    k = cost_bps / 10000
    if (weights * k >= 1).any() or cash_annual <= -1:
        raise ValueError('Invalid financing/cost assumptions')
    cash = (1 + cash_annual)**(1 / TRADING_DAYS) - 1
    advanced = any(v is not None for v in (cash_returns, borrowing_returns, trade_mask))
    def aligned(series, default):
        if series is None:
            return np.full(len(weights), default)
        if not series.index.equals(weights.index) or not np.isfinite(series).all():
            raise ValueError('Cash, financing and trade schedules must be finite and aligned')
        return series.to_numpy()
    cash_values = aligned(cash_returns, cash)
    borrow_values = aligned(borrowing_returns, cash)
    trade_values = aligned(trade_mask, True)
    if (cash_values <= -1).any() or (borrow_values <= -1).any():
        raise ValueError('Invalid cash or borrowing returns')
    nav, drifted = 1., 0.
    rows = []
    for r, target, cash, borrow, trade in zip(simple_returns.to_numpy(), weights.to_numpy(),
                                            cash_values, borrow_values, trade_values):
        # A false trade flag was committed at the earlier signal origin. Holding
        # shares lets exposure drift; this is not same-close signal generation.
        w = target if trade else drifted
        change = w - drifted
        fee_fraction = k * abs(change) / (1 + k * w * np.sign(change))
        turnover = abs(w * (1 - fee_fraction) - drifted)
        gross = (1 + w*r + max(1-w, 0)*cash - max(w-1, 0)*borrow) if advanced else 1 + w*r + (1-w)*cash
        if gross <= 0 or fee_fraction >= 1:
            raise ValueError('Portfolio insolvency; leverage assumptions invalid')
        cost_value = nav * fee_fraction
        net = (1-fee_fraction)*gross - 1
        prior_nav = nav
        nav *= 1 + net
        rows.append({'weight': w, 'pretrade_weight': drifted, 'turnover': turnover,
                     'cost': fee_fraction, 'cost_value': cost_value, 'nav_before': prior_nav,
                     'net_return': net, 'equity': nav})
        if advanced:
            rows[-1].update({'target_weight': target, 'trade_scheduled': bool(trade),
                'cost_bps': cost_bps,
                'market_return': r, 'cash_return': cash, 'borrowing_return': borrow,
                'risky_pnl': w*r, 'cash_income': max(1-w, 0)*cash,
                'financing_cost': max(w-1, 0)*borrow, 'gross_return': gross-1,
                'fee_drag': fee_fraction*gross})
        drifted = w * (1 + r) / gross
    return pd.DataFrame(rows, index=simple_returns.index)


def run_backtest(prices, forecasts, config=Config(), evaluation_index=None):
    simple = prices.pct_change(fill_method=None).reindex(forecasts.index)
    weights = executable_weights(forecasts, config)
    index = weights.dropna().index
    if evaluation_index is not None:
        if not evaluation_index.isin(index).all():
            raise ValueError('Requested period includes unavailable forecasts/weights')
        index = evaluation_index
    if len(index) < 2:
        raise ValueError('Insufficient shared OOS observations, including threshold warmup')
    d = pd.DataFrame({'market_return': simple.reindex(index),
                      'log_return': forecasts.log_return.reindex(index)}, index=index)
    # One-step accuracy predictors are lag 1; executed positions use lag >=2.
    for model in ('rolling', 'garch'):
        d[model + '_variance'] = forecasts[model + '_variance'].shift(1).reindex(index)
        d[model + '_vol'] = np.sqrt(d[model + '_variance']*TRADING_DAYS)
        d[model + '_execution_vol'] = forecasts[model + '_vol'].shift(config.execution_lag).reindex(index)
    origins = pd.Series(forecasts.index, index=forecasts.index)
    d['forecast_origin'] = origins.shift(1).reindex(index)
    d['signal_origin'] = origins.shift(config.execution_lag).reindex(index)
    d['execution_date'] = origins.shift(1).reindex(index)
    d['garch_status'] = forecasts.garch_status.shift(1).reindex(index)
    for strategy in STRATEGIES:
        s = simulate(d.market_return, weights.loc[index, strategy], config.cost_bps, config.cash_annual)
        for col in s:
            d[strategy + '_' + col] = s[col]
    d.index.name = 'Date'
    return d
