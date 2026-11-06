"""Generate research prose and tables directly from executed CSV results."""
from pathlib import Path
import pandas as pd
from .config import Config


def table(frame, formats=None):
    formats = formats or {}
    def cell(value, col):
        if pd.isna(value):
            return '—'
        if col in formats:
            return formats[col](value)
        if isinstance(value, float):
            return f'{value:.4f}'
        return str(value).replace('|', '/')
    lines = ['| ' + ' | '.join(map(str, frame.columns)) + ' |',
             '| ' + ' | '.join(['---']*len(frame.columns)) + ' |']
    lines += ['| ' + ' | '.join(cell(row[col], col) for col in frame.columns) + ' |'
              for _, row in frame.iterrows()]
    return '\n'.join(lines)


PERCENT = lambda x: f'{x:.2%}'
FORMATS = {name: PERCENT for name in ('CAGR', 'Annualized Volatility', 'Maximum Drawdown',
           'Average Exposure', 'Total Return', 'Total Costs / Starting Capital', 'Sharpe win share vs BH',
           'Sharpe win share vs Rolling', 'CAGR difference', 'MDD difference', 'Fallback share')}


def write_report(out, config=Config(), has_robustness=True):
    out = Path(out)
    summary = pd.read_csv(out/'summary.csv')
    regime = pd.read_csv(out/'regime_summary.csv')
    losses = pd.read_csv(out/'forecast_diagnostics.csv')
    first, last = summary.Start.min(), summary.End.max()
    quality = pd.read_json(out/'run_metadata.json', typ='series')['data_quality']
    quality = pd.DataFrame(quality)
    cols = ['Ticker', 'Strategy', 'CAGR', 'Annualized Volatility', 'Sharpe (rf=0)',
            'Maximum Drawdown', 'Calmar', 'Average Exposure']
    sections = [f'''# GARCH-Based Volatility Forecasting and Dynamic Portfolio Risk Management

## Research question and motivation

Can conditional variance forecasts improve risk-adjusted ETF investment performance
through dynamic exposure sizing? Volatility clusters, so a forecast may help control
risk, but reducing exposure can also forgo equity gains, miss rebounds, and incur fees.
This study compares separate SPY, QQQ, and IWM sleeves, not an optimized joint portfolio.
All reported numerical findings below come from executed real-data CSV outputs.

## Dataset and preprocessing

Yahoo Finance daily adjusted close and unadjusted trading volume, retrieved with
`yfinance`, from {config.start} through {config.end}. The download end is exclusive,
so the request uses the next calendar date. Raw OHLC, distributions, splits, and volume
are retained. Adjusted-close returns are treated as a reinvested-distribution total-return
proxy; share-level dividend cash flows are not modeled separately.

{table(quality[['Ticker', 'Rows', 'Start', 'End', 'Missing sessions', 'Absolute log return >20%']])}

Dates must match the XNYS trading calendar, including exceptional closures. The three
ETFs must have identical dates. Invalid/duplicate dates, nonpositive prices/volume,
missing sessions, and nonfinite observations cause failure. Holidays are not filled;
missing trading prices are never forward-filled. The first return is undefined and
excluded. Raw-file SHA256 hashes and package versions are in `run_metadata.json`;
retrieval metadata is in `../data/download_manifest.json`. Large moves are flagged,
not winsorized. Yahoo data may be revised; retain the supplied files to reproduce this run.

Log returns `log(P_t/P_(t-1))` estimate variance; simple returns `P_t/P_(t-1)-1`
calculate portfolio P&L. Prices and return histograms, 20-day volatility, return
clustering, and squared-return autocorrelations appear in `figures/exploratory.*`
and `figures/volatility_clustering.*`. Stress windows are shaded.

## Model specification and forecast assessment

The zero-mean Gaussian GARCH(1,1) is
`h_(t+1) = omega + alpha * r_t^2 + beta * h_t`.
Fits use percent log returns for numerical conditioning; saved variance forecasts
use decimal daily return squared units. Fit window: {config.training_days} sessions;
refit interval: {config.refit_every} sessions. Parameters are estimated only from the
trailing history ending at the forecast origin. `arch` supplies the correctly timed
likelihood and filtered endpoint; intervening updates consume only the newly observed
shock. No full-sample parameter fit is used for OOS forecasts. Annualized volatility
is `sqrt(252*h)`. Historical variance uses {config.rolling_days} log returns with ddof=1.

Fit logs record sample dates, convergence flag, optimizer message, parameters,
persistence, and warnings. The package permits persistence at the integrated boundary;
alpha+beta >=0.995 is flagged as near-integrated. This is a stability warning, not
proof of stationary long-run variance. Failed/invalid fits use trailing-window sample
variance until the next scheduled fit; each affected forecast is explicitly flagged.

Forecasts indexed by origin t are evaluated against squared log return at t+1.
MSE and MAE are computed on daily *variance*, not annualized volatility. QLIKE is
`mean(log(h) + r^2/h)`; lower is better, and it can be negative because this form
omits an outcome-only constant. It remains defined when the realized return is zero.
Daily squared returns are extremely noisy proxies for latent conditional variance;
this study has no intraday realized variance or formal forecast-superiority test.

## Strategies and execution assumptions

- Buy-and-hold invests 100% in each ETF and pays only the initial trading fee.
- Rolling and GARCH targeting set `w=min(cap, target/max(forecast_vol, floor))`.
  Target={config.target_vol:.0%}, cap={config.max_exposure:.0%}, annual volatility floor={config.annual_vol_floor:.0%}.
- GARCH threshold uses the past-only expanding {config.threshold_low:.0%}/{config.threshold_high:.0%}
  quantiles of earlier GARCH forecasts, excluding the current forecast. Exposure is
  100%, 50%, or 0%, respectively, capped at the configured limit. At least
  {config.threshold_history} prior forecasts are required. The supplied README did not
  define threshold levels; these were fixed before execution and are exploratory.

A signal observed after close t is submitted for execution at close t+1. It earns
close t+1 to close t+2 P&L (two-row lag from signal to return). This avoids trading
at a close that was needed to calculate the signal. Exact closing fills remain an
execution approximation. The one-step volatility forecast is therefore one session
stale when traded; forecast accuracy and trading effectiveness are distinct questions.
Baseline strategies share {first} through {last}; threshold warmup intentionally delays
all strategies to maintain an identical comparison period. The 2015 history is used
for estimation, not counted as traded OOS performance.

Fees are {config.cost_bps:g} bps times actual traded notional, including initial entry.
Weights are fractions of post-fee NAV. If a is the pretrade risky fraction, w the
target, k the fee rate, then `c = k*abs(w-a)/(1+k*w*sign(w-a))` is the exact fee/NAV
solution. Turnover is `abs(w*(1-c)-a)`. The portfolio earns
`(1-c)*(1+w*r+(1-w)*cash)-1`; next day's risky fraction includes market drift.
Unchanged fractional targets may require trades. End holdings are marked to market;
no forced liquidation fee is charged. Cash and financing return are fixed at zero
in the baseline and all sensitivity scenarios. Leverage-cap scenarios above 100%
therefore assume free financing and are optimistic stress checks, not recommendations.

CAGR uses 252 sessions/year; volatility uses sample daily standard deviation times
sqrt(252); Sharpe is arithmetic mean divided by standard deviation, annualized,
with risk-free rate zero. Drawdown includes starting wealth 1; Calmar=CAGR/abs(MDD).
Turnover is one-way traded notional/pretrade NAV, annualized by 252. Cost fractions
sum is distinct from cash fees divided by starting capital; both are saved. Position
changes count nonzero actual trades. Regime slices retain original trading history
and fees, with no invented reentry; wealth/drawdown is rebased at each regime start.
Annualized short-window statistics are descriptive and can be unstable.

## Empirical baseline results

{table(summary[cols], FORMATS)}

Detailed costs and trading activity:

{table(summary[['Ticker', 'Strategy', 'Annualized Turnover', 'Total Costs / Starting Capital', 'Position Changes']], FORMATS)}
''']
    for ticker, group in summary.groupby('Ticker', sort=False):
        s = group.set_index('Strategy')
        g, b, r = (s.loc[name] for name in ('GARCH', 'Buy-and-Hold', 'Rolling Vol'))
        sections.append(f"{ticker}: GARCH Sharpe is {g['Sharpe (rf=0)']:.3f}, versus "
            f"{b['Sharpe (rf=0)']:.3f} for buy-and-hold and {r['Sharpe (rf=0)']:.3f} for rolling. "
            f"Its CAGR is {g['CAGR']:.2%}, a {(g['CAGR']-b['CAGR'])*100:+.2f} percentage-point "
            f"difference from buy-and-hold. Its MDD is {g['Maximum Drawdown']:.2%}, versus "
            f"{b['Maximum Drawdown']:.2%} for buy-and-hold. These distinguish risk-adjusted performance "
            "from the absolute-return cost of holding less equity.\n")
    diag_rows = []
    for ticker in config.tickers:
        fits = pd.read_csv(out/'diagnostics'/f'{ticker}_fits.csv')
        daily = pd.read_csv(out/f'{ticker}_daily.csv')
        diag_rows.append({'Ticker': ticker, 'Fits': len(fits), 'Failed fits': int((~fits.accepted).sum()),
            'Near-integrated fits': int(fits.get('near_integrated', pd.Series(dtype=bool)).fillna(False).sum()),
            'Fallback share': float((daily.garch_status=='historical_fallback').mean()),
            'Min persistence': fits.persistence.min() if 'persistence' in fits else float('nan'),
            'Max persistence': fits.persistence.max() if 'persistence' in fits else float('nan')})
    sections.append('## Forecast accuracy and stability\n\n' + table(
        losses.loc[losses.Regime=='All OOS', ['Ticker', 'Model', 'Observations', 'MSE variance', 'MAE variance', 'QLIKE']],
        {'MSE variance': lambda x: f'{x:.6e}', 'MAE variance': lambda x: f'{x:.6e}'}) +
        '\n\n' + table(pd.DataFrame(diag_rows), FORMATS) + '\n')
    for ticker in config.tickers:
        x = losses[(losses.Ticker==ticker) & (losses.Regime=='All OOS')].set_index('Model')
        sections.append(f"{ticker}: GARCH minus rolling QLIKE = {x.loc['garch','QLIKE']-x.loc['rolling','QLIKE']:+.4f}; "
                        'a negative difference favors GARCH for this loss.\n')
    chosen = regime[regime.Regime.isin(['COVID stress 2020', '2022 tightening'])]
    sections.append('## Market regime analysis\n\nCOVID stress is 2020-02-19–2020-06-30; tightening is '
        '2022-01-01–2022-12-31 (actual exchange sessions). These are descriptive event windows; '
        'the COVID window includes the rebound. Full calendar 2020 and additional chronological '
        'periods are available in `regime_summary.csv`.\n\n' + table(chosen[
        ['Ticker', 'Regime', 'Strategy', 'Observations', 'Total Return', 'Sharpe (rf=0)',
         'Maximum Drawdown', 'Average Exposure']], FORMATS) + '\n')
    for (ticker, label), group in chosen.groupby(['Ticker', 'Regime'], sort=False):
        x = group.set_index('Strategy')
        delta = x.loc['GARCH','Maximum Drawdown']-x.loc['Buy-and-Hold','Maximum Drawdown']
        rolling_delta = x.loc['GARCH','Maximum Drawdown']-x.loc['Rolling Vol','Maximum Drawdown']
        sections.append(f'{ticker}, {label}: GARCH MDD difference versus buy-and-hold is '
            f'{delta*100:+.2f} percentage points and versus rolling is {rolling_delta*100:+.2f} points '
            '(positive means a smaller drawdown).\n')
    sections.append('## Robustness and sensitivity\n')
    if has_robustness:
        robust = pd.read_csv(out/'robustness.csv')
        all_oos = robust[robust.Period=='Common OOS']
        keys = ['Ticker', 'Window', 'Refit', 'Target', 'Cost bps', 'Cap', 'Period']
        pivot = robust.pivot(index=keys, columns='Strategy', values='Sharpe (rf=0)').reset_index()
        rows = []
        for (ticker, period), group in pivot.groupby(['Ticker', 'Period'], sort=False):
            rows.append({'Ticker': ticker, 'Period': period, 'Scenarios': len(group),
                'Sharpe win share vs BH': (group.GARCH>group['Buy-and-Hold']).mean(),
                'Sharpe win share vs Rolling': (group.GARCH>group['Rolling Vol']).mean(),
                'GARCH min Sharpe': group.GARCH.min(), 'GARCH max Sharpe': group.GARCH.max()})
        robustness_summary = pd.DataFrame(rows)
        robustness_summary.to_csv(out/'robustness_comparison.csv', index=False)
        common = robustness_summary[robustness_summary.Period=='Common OOS']
        chronological = robustness_summary[robustness_summary.Period.isin(
            ['Pre-COVID OOS', '2020–2022', '2023–2025'])]
        sections.append(f'''Prespecified target vols 10%, 15%, 20%; fees 0, 5, 10 bps; caps 75%, 100%, 150%.
Estimation windows 252, 504, 756 sessions use the baseline refit schedule;
refits every 5, 21, 63 sessions are also tested at the baseline estimation window.
These five window/refit pairs are crossed with all target/cost/cap combinations,
producing {int(common.Scenarios.iloc[0])} scenarios per ETF. All scenarios start from
cash on a common OOS calendar: {all_oos.Start.min()}–{all_oos.End.max()}, excluding
the longest estimation and threshold warmup. Buy-and-hold stays at 100% even when
the *dynamic-strategy* cap is 75%. Threshold exposure does not depend on target
volatility, so some benchmark rows intentionally repeat across grid cells.

{table(common.drop(columns='Period'), FORMATS)}

Chronological sensitivity (the pre-COVID slice starts at the common OOS date):

{table(chronological, FORMATS)}

Chronological and stress-window comparisons use continuous slices of these same
ledgers; see `robustness_comparison.csv` and all {len(robust):,} metric rows in
`robustness.csv`. Scenario win shares describe sensitivity, not probabilities or
independent experiments; grid cells are strongly dependent. No best setting is
selected, no model is tuned to OOS results, and no statistical significance is claimed.
A different OOS start from the baseline means robustness levels must be compared
within their own common calendar. Alternative fit logs and forecasts are retained.
''')
        alt = []
        for path in sorted((out/'diagnostics').glob('*_fits_w*_r*.csv')):
            fit = pd.read_csv(path)
            alt.append({'Model file': path.name, 'Fits': len(fit),
                        'Failed': int((~fit.accepted).sum()),
                        'Near-integrated': int(fit.get('near_integrated', pd.Series(dtype=bool)).fillna(False).sum())})
        if alt:
            sections.append('Alternative-model stability:\n\n' + table(pd.DataFrame(alt)) + '\n')
    else:
        sections.append('Robustness was explicitly skipped for this run; no sensitivity conclusion is available.\n')
    wins_bh = wins_roll = 0
    for _, group in summary.groupby('Ticker'):
        x = group.set_index('Strategy')['Sharpe (rf=0)']
        wins_bh += int(x.GARCH>x['Buy-and-Hold'])
        wins_roll += int(x.GARCH>x['Rolling Vol'])
    sections.append(f'''## Limitations and conclusion

In the baseline, GARCH's Sharpe exceeds buy-and-hold in {wins_bh}/{len(config.tickers)} ETFs and
rolling targeting in {wins_roll}/{len(config.tickers)} ETFs. The detailed CAGR and drawdown
comparisons above quantify any tradeoff between risk reduction and foregone equity gains.
Forecast-loss improvements, when present, do not by themselves establish investment value.
These are empirical descriptive findings for the supplied history, not guaranteed returns.

Limitations: only three surviving US equity ETFs; one historical test path; correlated
assets; adjusted vendor prices rather than point-in-time data vintages; Gaussian symmetric
GARCH omits skew, heavy tails, leverage effects and structural breaks; near-integrated fits
may be unstable; one-day squared returns are noisy; trading signals are stale by design;
exact close fills, proportional costs, and no market impact or capacity model; cash/risk-free
and borrowing rates set to zero; ETF taxes and discrete share restrictions omitted;
no confidence intervals or multiple-testing correction. Positive actual cash rates could
materially change the relative performance of defensive strategies. The threshold rule
and large grid are exploratory checks; interpreting the best observed configuration as a
selected strategy would overfit this history. Follow-up research should use reserved
future data, richer realized variance, realistic cash/financing, and execution stress tests.

Figures are available as 220-dpi PNG and vector PDF in `figures/`: adjusted history,
return distributions, clustering, forecasts, wealth, drawdowns, exposure, performance
comparison, and robustness Sharpe distributions. Daily ledgers and forecast-origin
CSV files allow independent timing and cost audits. Reproduction and tests are documented
in `../README.md`; execution metadata is in `run_metadata.json`.

## Method references

- [arch forecasting documentation](https://arch.readthedocs.io/en/stable/univariate/forecasting.html): conditional variance forecasting and origin alignment.
- [yfinance download API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html): adjustment options and exclusive end date.
- [NYSE January 9, 2025 closure announcement](https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx): exceptional trading-calendar closure.
''')
    (out/'RESEARCH_REPORT.md').write_text('\n\n'.join(sections))
