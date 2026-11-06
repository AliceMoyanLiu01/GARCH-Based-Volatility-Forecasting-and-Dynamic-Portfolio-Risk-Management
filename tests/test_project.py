"""Artificial fixtures are used ONLY in tests, never as empirical observations."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from arch import arch_model
from garch_research.config import Config
from garch_research.models import forecast
from garch_research.strategies import target_weights, executable_weights
from garch_research.backtesting import simulate, run_backtest
from garch_research.evaluation import performance, summarize, regimes, forecast_losses
from garch_research.data import validate_frame, expected_sessions

@pytest.fixture
def sample():
    rng = np.random.default_rng(31)
    idx = pd.bdate_range('2019-01-01', periods=220)
    prices = pd.Series(100*np.exp(np.cumsum(rng.normal(.0002, .012, len(idx)))), index=idx)
    config = replace(Config(), training_days=60, refit_every=21, threshold_history=20)
    f, fits = forecast(np.log(prices).diff(), config)
    return prices, config, f, fits


def test_no_future_leakage_across_refits(sample):
    prices, c, f, _ = sample
    r = np.log(prices).diff()
    changed = r.copy()
    cutoff = 143
    changed.iloc[cutoff:] = .08
    other, _ = forecast(changed, c)
    pd.testing.assert_frame_equal(f.loc[:r.index[cutoff-1]], other.loc[:r.index[cutoff-1]])
    prefix, _ = forecast(r.iloc[:cutoff], c)
    pd.testing.assert_frame_equal(prefix, f.loc[prefix.index])


def test_refit_forecast_matches_arch(sample):
    prices, c, f, fits = sample
    x = np.log(prices).diff().dropna().iloc[:c.training_days]*100
    result = arch_model(x.to_numpy(), mean='Zero', p=1, q=1, rescale=False).fit(disp='off', options={'maxiter':500})
    expected = result.forecast(horizon=1, reindex=False).variance.iloc[-1, 0]/10000
    assert f.garch_variance.iloc[c.training_days-1] == pytest.approx(expected)
    assert (fits.training_end == fits.origin).all()
    assert fits.accepted.all()


def test_between_refit_recursion(sample):
    _, c, f, fits = sample
    t = c.training_days
    p = fits.iloc[0]
    expected = p.omega_percent_squared/10000 + p.alpha*f.log_return.iloc[t]**2 + p.beta*f.garch_variance.iloc[t-1]
    assert f.garch_variance.iloc[t] == pytest.approx(expected)


def test_execution_and_forecast_alignment(sample):
    prices, c, f, _ = sample
    d = run_backtest(prices, f, c)
    w = target_weights(f, c).shift(2)
    np.testing.assert_allclose(d.GARCH_weight, w.loc[d.index, 'GARCH'])
    np.testing.assert_allclose(d.garch_variance, f.garch_variance.shift(1).loc[d.index])
    assert (d.signal_origin < d.execution_date).all()
    assert (d.execution_date < d.index).all()
    expected = (1-d.GARCH_cost)*(1+d.GARCH_weight*d.market_return)-1
    np.testing.assert_allclose(d.GARCH_net_return, expected)


def test_current_and_future_prices_cannot_change_held_exposure(sample):
    prices, c, f, _ = sample
    d = run_backtest(prices, f, c)
    changed = prices.copy()
    cutoff = 160
    changed.iloc[cutoff:] *= 1.5
    other, _ = forecast(np.log(changed).diff(), c)
    new = run_backtest(changed, other, c)
    # Shock at close cutoff cannot affect holdings until cutoff+2.
    for s in ('GARCH', 'Rolling Vol', 'GARCH Threshold'):
        pd.testing.assert_series_equal(d[s+'_weight'].loc[:prices.index[cutoff+1]],
                                       new[s+'_weight'].loc[:prices.index[cutoff+1]])


def test_threshold_reference_excludes_today_and_future(sample):
    _, c, f, _ = sample
    t = 140
    vol = f.garch_vol.iloc[t]
    past = f.garch_vol.iloc[:t].dropna()
    expected = 1. if vol <= past.quantile(.25) else (.5 if vol <= past.quantile(.75) else 0.)
    weights = target_weights(f, c)
    assert weights['GARCH Threshold'].iloc[t] == expected
    changed = f.copy()
    changed.loc[changed.index[t+1:], 'garch_vol'] = 100.
    pd.testing.assert_frame_equal(weights.iloc[:t+1], target_weights(changed, c).iloc[:t+1])


def test_buy_hold_has_only_initial_fee():
    idx = pd.bdate_range('2020-01-01', periods=3)
    r = pd.Series([.1, -.2, .05], index=idx)
    d = simulate(r, pd.Series(1., index=idx), cost_bps=5)
    assert d.cost.iloc[0] == pytest.approx(.0005/1.0005)
    np.testing.assert_allclose(d.turnover.iloc[1:], 0., atol=1e-14)
    assert d.equity.iloc[-1] == pytest.approx(np.prod(1+r)/1.0005)


def test_self_financing_fees_drift_and_sales():
    idx = pd.bdate_range('2020-01-01', periods=3)
    r = pd.Series([.1, -.1, 0], index=idx)
    d = simulate(r, pd.Series([.5, .5, .2], index=idx), cost_bps=10)
    assert d.pretrade_weight.iloc[1] == pytest.approx(.55/1.05)
    assert d.turnover.iloc[1] > 0  # Same target still requires a sale after market rise.
    for row in d.itertuples():
        risky_before = row.nav_before * row.pretrade_weight
        risky_after = row.weight * (row.nav_before - row.cost_value)
        assert row.cost_value == pytest.approx(abs(risky_after-risky_before)*.001)
        cash_before = row.nav_before-risky_before
        cash_after = cash_before-(risky_after-risky_before)-row.cost_value
        assert risky_after+cash_after == pytest.approx(row.nav_before-row.cost_value)


def test_cash_and_leverage():
    idx = pd.bdate_range('2020-01-01', periods=2)
    r = pd.Series([.02, -.01], index=idx)
    d = simulate(r, pd.Series(0., index=idx), cash_annual=.05)
    assert d.equity.iloc[-1] == pytest.approx(1.05**(2/252))
    lev = simulate(r, pd.Series(1.5, index=idx), cost_bps=0)
    np.testing.assert_allclose(lev.net_return, 1.5*r)


def test_initial_loss_in_drawdown():
    idx = pd.bdate_range('2020-01-01', periods=2)
    r = pd.Series([-.1, 0], index=idx)
    m = performance(r, pd.Series(1., index=idx))
    assert m['Maximum Drawdown'] == pytest.approx(-.1)


def test_zero_return_performance():
    idx = pd.bdate_range('2024-01-01', periods=25)
    m = performance(pd.Series(0., index=idx), pd.Series(1., index=idx))
    assert m['CAGR'] == 0 and m['Annualized Volatility'] == 0
    assert np.isnan(m['Sharpe (rf=0)'])


def test_segment_does_not_charge_reentry(sample):
    prices, c, f, _ = sample
    d = run_backtest(prices, f, c)
    sub = d.iloc[10:30]
    row = summarize(sub).set_index('Strategy').loc['Buy-and-Hold']
    assert row['Position Changes'] == 0
    assert row['Total Costs / Starting Capital'] == 0


def test_variance_losses_use_aligned_forecast_and_log_return(sample):
    prices, c, f, _ = sample
    d = run_backtest(prices, f, c)
    diag = forecast_losses(d)
    row = diag[(diag.Regime=='All OOS') & (diag.Model=='garch')].iloc[0]
    y, h = d.log_return**2, d.garch_variance
    assert row['MSE variance'] == pytest.approx(((h-y)**2).mean())
    assert row['MAE variance'] == pytest.approx((h-y).abs().mean())
    assert row.QLIKE == pytest.approx((np.log(h)+y/h).mean())


def test_model_failure_is_flagged_and_causal(sample, monkeypatch):
    import garch_research.models as models
    prices, c, _, _ = sample
    def fail(sample):
        raise RuntimeError('intentional optimizer failure')
    monkeypatch.setattr(models, 'fit_garch', fail)
    f, fits = models.forecast(np.log(prices).diff(), c)
    assert not fits.accepted.any()
    assert (f.garch_status.iloc[c.training_days-1:] == 'historical_fallback').all()
    expected = np.log(prices).diff().dropna().iloc[:c.training_days].var(ddof=1)
    assert f.garch_variance.iloc[c.training_days-1] == pytest.approx(expected)


def test_low_volatility_floor_and_cap(sample):
    _, c, f, _ = sample
    f['garch_vol'] = 0.
    f['rolling_vol'] = 1e-20
    weights = target_weights(f, c)
    assert (weights.GARCH == 1).all()
    assert np.isfinite(weights['Rolling Vol']).all()


def test_data_quality():
    idx = pd.bdate_range('2020-01-01', periods=3)
    d = pd.DataFrame({'Date': idx, 'Adj Close': [100, 102, 101], 'Volume': [10, 20, 30]})
    good = validate_frame(d, 'TEST', idx)
    assert good.log_return.iloc[1] == pytest.approx(np.log(1.02))
    assert good.simple_return.iloc[1] == pytest.approx(.02)
    for bad in [pd.concat([d, d.iloc[:1]]), d.drop(index=1), d.assign(Volume=np.nan),
                d.assign(**{'Adj Close': -1}), d.rename(columns={'Adj Close': 'Close'})]:
        with pytest.raises(ValueError):
            validate_frame(bad, 'TEST', idx)


def test_calendar_includes_special_closures():
    dates = expected_sessions(Config())
    assert pd.Timestamp('2025-01-09') not in dates
    assert pd.Timestamp('2018-12-05') not in dates
    assert pd.Timestamp('2025-12-31') in dates


@pytest.mark.parametrize('kwargs', [{'execution_lag':1}, {'cost_bps':-1}, {'target_vol':float('nan')},
                                    {'training_days':0}, {'threshold_low':.9}])
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        replace(Config(), **kwargs)


def test_internal_missing_return_is_rejected(sample):
    prices, c, _, _ = sample
    r = np.log(prices).diff()
    r.iloc[100] = np.nan
    with pytest.raises(ValueError, match='finite'):
        forecast(r, c)
