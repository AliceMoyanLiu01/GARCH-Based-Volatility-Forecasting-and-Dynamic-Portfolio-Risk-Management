"""Prespecified factorial sensitivities on an identical OOS calendar."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import pandas as pd
from .config import Config
from .models import forecast
from .strategies import executable_weights
from .backtesting import run_backtest
from .evaluation import summarize, regimes


def run_robustness(frames, baseline_forecasts, config, out):
    out = Path(out)
    combinations = sorted(set([(w, config.refit_every) for w in config.robust_windows] +
                              [(config.training_days, f) for f in config.robust_refits]))
    cache = {}
    common = None
    for ticker, frame in frames.items():
        for window, refit in combinations:
            c = replace(config, training_days=window, refit_every=refit)
            if (window, refit) == (config.training_days, config.refit_every):
                forecasts = baseline_forecasts[ticker]
            else:
                forecasts, fits = forecast(frame.log_return, c)
                fits.to_csv(out/'diagnostics'/f'{ticker}_fits_w{window}_r{refit}.csv', index=False)
                forecasts.to_csv(out/'forecasts'/f'{ticker}_w{window}_r{refit}.csv')
            cache[ticker, window, refit] = forecasts
            valid = executable_weights(forecasts, c).dropna().index
            common = valid if common is None else common.intersection(valid)
    if common is None or len(common) < 2:
        raise ValueError('No common robustness period')
    records = []
    # All settings were specified before results. Do not rank or select a winner.
    for ticker, frame in frames.items():
        print(f'Robustness: {ticker}, common OOS {common[0].date()}–{common[-1].date()}', flush=True)
        for (window, refit), target, cost, cap in product(combinations, config.robust_targets,
                                                        config.robust_costs, config.robust_caps):
            c = replace(config, training_days=window, refit_every=refit,
                        target_vol=target, cost_bps=cost, max_exposure=cap)
            d = run_backtest(frame['Adj Close'], cache[ticker, window, refit], c, common)
            overall = summarize(d)
            overall.insert(0, 'Period', 'Common OOS')
            periods = regimes(d).rename(columns={'Regime': 'Period'})
            stats = pd.concat([overall, periods], ignore_index=True)
            for key, value in {'Ticker': ticker, 'Window': window, 'Refit': refit,
                               'Target': target, 'Cost bps': cost, 'Cap': cap}.items():
                stats.insert(0, key, value)
            records.append(stats)
    result = pd.concat(records, ignore_index=True)
    result.to_csv(out/'robustness.csv', index=False)
    return result
