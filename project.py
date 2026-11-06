"""End-to-end CLI; core implementation lives in garch_research modules."""
import argparse
from dataclasses import replace
from pathlib import Path
import importlib.metadata
import json
import platform
import hashlib
import pandas as pd
import numpy as np
from garch_research.config import Config, TRADING_DAYS
from garch_research.data import prepare, download, validate_frame
from garch_research.models import forecast, garch_one_day_ahead
from garch_research.backtesting import run_backtest
from garch_research.evaluation import performance, summarize, regimes, forecast_losses


def load_prices(path, ticker):
    return validate_frame(pd.read_csv(path), ticker)['Adj Close'].rename(ticker)


def backtest(prices, target_vol=.15, max_exposure=1., cost_bps=5., training_days=504, refit_every=21):
    config = replace(Config(), target_vol=target_vol, max_exposure=max_exposure, cost_bps=cost_bps,
                     training_days=training_days, refit_every=refit_every)
    forecasts, _ = forecast(np.log(prices).diff(), config)
    daily = run_backtest(prices, forecasts, config)
    return daily, summarize(daily).set_index('Strategy')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--skip-robustness', action='store_true')
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    parser.add_argument('--target-vol', type=float, default=Config.target_vol)
    parser.add_argument('--max-exposure', type=float, default=Config.max_exposure)
    parser.add_argument('--cost-bps', type=float, default=Config.cost_bps)
    parser.add_argument('--training-days', type=int, default=Config.training_days)
    parser.add_argument('--refit-every', type=int, default=Config.refit_every)
    args = parser.parse_args()
    c = replace(Config(), **{k: getattr(args, k) for k in
                ('target_vol', 'max_exposure', 'cost_bps', 'training_days', 'refit_every')})
    out = args.output_dir
    for folder in ('figures', 'forecasts', 'diagnostics'):
        (out/folder).mkdir(parents=True, exist_ok=True)
    if args.download:
        download(args.data_dir, c)
    frames = prepare(args.data_dir, c)
    from garch_research.visualization import exploratory, strategy_plots, comparison, sensitivity
    exploratory(frames, out/'figures')
    summaries, regime_rows, losses, baseline = [], [], [], {}
    for ticker, frame in frames.items():
        forecasts, fits = forecast(frame.log_return, c)
        baseline[ticker] = forecasts
        forecasts.to_csv(out/'forecasts'/f'{ticker}.csv')
        fits.to_csv(out/'diagnostics'/f'{ticker}_fits.csv', index=False)
        daily = run_backtest(frame['Adj Close'], forecasts, c)
        daily.to_csv(out/f'{ticker}_daily.csv')
        for collection, table in [(summaries, summarize(daily)), (regime_rows, regimes(daily)),
                                   (losses, forecast_losses(daily))]:
            table.insert(0, 'Ticker', ticker)
            collection.append(table)
        strategy_plots(daily, ticker, out/'figures')
        print(f'{ticker}: {len(daily)} OOS sessions, {daily.index[0].date()}–{daily.index[-1].date()}; '
              f'{int((~fits.accepted).sum())}/{len(fits)} failed fits', flush=True)
    summary = pd.concat(summaries, ignore_index=True)
    summary.to_csv(out/'summary.csv', index=False)
    pd.concat(regime_rows, ignore_index=True).to_csv(out/'regime_summary.csv', index=False)
    pd.concat(losses, ignore_index=True).to_csv(out/'forecast_diagnostics.csv', index=False)
    comparison(summary, out/'figures')
    robust = None
    if not args.skip_robustness:
        from garch_research.robustness import run_robustness
        robust = run_robustness(frames, baseline, c, out)
        sensitivity(robust, out/'figures')
    versions = {p: importlib.metadata.version(p) for p in
                ('numpy', 'pandas', 'scipy', 'arch', 'matplotlib', 'yfinance', 'exchange-calendars', 'pytest')}
    sources = list(Path('garch_research').glob('*.py')) + [Path('project.py'), Path('requirements.txt')]
    metadata = {'config': c.to_dict(), 'python': platform.python_version(), 'packages': versions,
                'robustness_executed': robust is not None,
                'data_quality': pd.read_csv(args.data_dir/'processed'/'quality.csv').to_dict('records'),
                'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (out/'run_metadata.json').write_text(json.dumps(metadata, indent=2))
    from garch_research.report import write_report
    write_report(out, c, robust is not None)
    print(summary[['Ticker', 'Strategy', 'CAGR', 'Sharpe (rf=0)', 'Maximum Drawdown']].to_string(index=False))
    print(f'Complete: {out.resolve()}/RESEARCH_REPORT.md', flush=True)

if __name__ == '__main__':
    main()
