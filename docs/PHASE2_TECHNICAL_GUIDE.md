# Archived Phase 2 technical guide

Commands assume the repository root. The current entry point is [README](../README.md).

# GARCH-Based Volatility Forecasting and Dynamic Portfolio Risk Management

## Phase 2: forecasting significance versus economic value

The upgraded study is complete in [RESEARCH_REPORT_V2.md](../RESEARCH_REPORT_V2.md).
The research audit records baseline verification, horizon alignment,
and methodological choices. The original code, data, and results remain unchanged in
`archive/phase1/`; a full baseline rerun is in `outputs/baseline_reproduced/`.

Reproduce the upgrade with the included real ETF and official cash-rate files:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python phase2.py
.venv/bin/python validate_phase2.py
```

For a new environment, create `.venv` and install `requirements-lock.txt` (the exact
Python 3.13 dependency closure) or `requirements.txt`. No new ETF download is needed.
`python download_cash.py` retrieves the official NY Fed EFFR proxy if the cash file
is missing. `python phase2.py --zero-cash-only --output-dir outputs_zero_cash` explicitly
runs only the zero-cash alternative; it never fabricates missing rates.

To independently rerun and compare every scientific CSV:

```bash
.venv/bin/python phase2.py --output-dir outputs/phase2_reproduced
.venv/bin/python validate_phase2.py --compare-to outputs/phase2_reproduced
```

Only measured runtime columns (`fit_seconds`, `Compute seconds`) are excluded from
numerical comparisons. Reports/plots contain those results, but their formatting,
PDF timestamps, and execution timing are not scientific reproducibility criteria.

Validate the preserved baseline against its archived source:

```bash
.venv/bin/python validate_results.py --output-dir outputs/baseline_reproduced \
  --source-root archive/phase1/source
```

To rerun the archived original implementation itself:

```bash
(cd archive/phase1/source && ../../../.venv/bin/python project.py \
  --data-dir ../data --output-dir ../../../outputs/original_rerun)
```

The original report at `outputs/RESEARCH_REPORT.md` remains intact with a pointer
to V2. Running the legacy `project.py` into that same directory regenerates the
initial report; use a different output directory for legacy experiments.

The V2 changes extend the existing modules instead of replacing the original model:

- `inference.py`, `statistical_stage.py`: daily loss differences; scaled Bartlett
  HAC; nine-test primary Holm family; seeded circular-block percentile intervals
  and bandwidth/block sensitivity; paired Sharpe intervals.
- `extended_models.py`, `model_stage.py`: causal normal/t GARCH, GJR, asymmetric
  EGARCH; separate h=1 and h=2 variances; fit/recursion diagnostics and runtimes.
- `backtesting.py`: backward-compatible dated cash, separate borrowing, and
  precommitted trade flags, reusing the original self-financing fee accounting.
- `economic_analysis.py`, `economic_stage.py`: horizon A/B, gross/net attribution,
  0/5/10-bp costs, fixed signal-time allocation band, and descriptive drawdown/recovery events.
- `cash.py`, `risk_matching.py`: official EFFR, conservative publication lag,
  ACT/360 calendar-day accrual, separate assumed borrowing spread, and earlier-only
  frozen exposure calibration.
- `chronological.py`: pre-2020, 2020–2022, 2023–2025 and stress comparisons.
- `phase2_config.py`, `phase2_visualization.py`, `phase2_report.py`,
  `phase2_artifacts.py`: fixed research settings, figures, report, and exact artifact inventory.
- `validate_phase2.py` and `tests/test_phase2.py`: independent accounting/inference
  checks and additional timing, inference, financing, failure, and reproducibility tests.

Primary settings: Gaussian GARCH vs rolling, original common OOS calendar, three
losses × three ETFs, two-sided HAC with automatic Bartlett lag, Holm familywise
adjustment. Circular blocks of 20 sessions, 2,000 replicates, seed 20261031;
blocks 5/60 and HAC lags 0/5/10/21/63 are sensitivity checks. Statistical intervals
are pointwise; non-rejection is not equivalence. Broader model tests are exploratory.

Timing A retains the delayed one-step signal. Timing B uses the second holding-day
conditional variance forecast, still observing at close t and executing at close
t+1 for return t+2. A two-step **single-day** variance is not the sum of two days'
variances. No order uses the execution close to decide whether to trade. The fixed
5-pp band compares origin-date targets with the last accepted target, holds shares
between scheduled trades, and is applied only in the unlevered experiment.

The optional cash proxy uses quotes conservatively available two US federal business
days after observation, known by holding start, with actual calendar days/360.
It is a rate-based cash approximation, not a traded EFFR asset. Current official
history is not a complete vintage archive; extraordinary later revisions cannot
be ruled out. Leverage sensitivity uses an **assumed** 100-bp funding spread, not
observed historical brokerage financing. Zero-cash results remain available.

Some converged EGARCH fits produce explosive or collapsing variances. A broad
numerical guard rejects forecasts outside [1e-6,1e6] times trailing sample variance,
retains attempted values, and records the historical-variance fallback. This was
added after a numerical failure, not optimized for returns. EGARCH-t day-2 variance
is not supplied because its exponential moment can diverge; all six model variants
are compared fairly using one-step forecasts and the same delayed trading rule.

The later 2023–2025 panel was already inspected in Phase 1 and is **retrospective**,
not untouched. There is no genuinely unseen holdout in this project. Read the report
for statistical versus economic conclusions and all negative/unstable outcomes.

Every exact output path, including ledgers, model fits, figures, archived files,
and reproduction files, is listed in PHASE2_OUTPUTS.md
and `outputs/phase2_artifacts.json`.

## Original project guide

This executed research project asks whether GARCH(1,1) forecasts improve risk-adjusted
performance through dynamic sizing of SPY, QQQ, and IWM. It compares buy-and-hold,
20-session historical-volatility targeting, GARCH targeting, and an exploratory
past-only percentile allocation. Daily adjusted prices and volume cover
2015-01-01–2025-12-31. Each ETF is a separate sleeve, not a combined portfolio.

Read [the generated research report](../FINAL_RESEARCH_REPORT.md) for the actual
findings, [performance CSV](../summary.csv) for the complete metric table,
and [project progress](../PROJECT_PROGRESS.md) for the audit and validation record.
No synthetic observations are used in empirical results. Artificial fixtures exist
only in automated tests.

## Reproduce

Python 3.11+ is recommended; this execution used Python 3.13. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python project.py --download
python validate_results.py
```

The final analysis command downloads real data, validates it, runs all strategies
and sensitivity experiments, and writes the report and figures. Network access is
needed for installation and download. To reproduce from the included real data:

```bash
.venv/bin/python project.py
.venv/bin/python validate_results.py
```

For a fresh environment with the exact dependency versions used in this run, install
`requirements-lock.txt` instead of `requirements.txt`. Runtime versions, settings,
source hashes, and input hashes are also saved in `outputs/run_metadata.json`.
A new vendor download may revise adjusted historical prices; reuse the saved raw
CSV files and compare hashes when exact numerical reproduction matters.

Additional commands:

```bash
python download_data.py                  # Download only; retries failed requests
python analyze_results.py                # Rebuild regime and forecast-loss CSVs
python project.py --skip-robustness --output-dir outputs_baseline
python project.py --target-vol 0.10 --max-exposure 1 --cost-bps 10 \
  --training-days 504 --refit-every 21 --output-dir outputs_alternative
```

Use a separate output directory for alternative runs. `--data-dir` and
`--output-dir` are available. All research defaults and sensitivity grids are in
[garch_research/config.py](../garch_research/config.py). The CLI overrides the baseline;
the prespecified target/cost/cap sensitivity grid remains unchanged.

## Data contract

`download_data.py` requests Yahoo Finance via `yfinance`, with `auto_adjust=False`
and actions enabled. `Adj Close` is the adjusted price; volume is unadjusted trading
volume. The exclusive end is 2026-01-01. Raw data includes OHLC, adjusted close,
volume, splits, and distributions when provided. `data/download_manifest.json`
records retrieval metadata and hashes.

External real data can instead be placed in `data/raw/{SPY,QQQ,IWM}.csv` (or the
legacy `data/{ticker}.csv` location). Each file **must** contain `Date`, `Adj Close`,
and `Volume`; do not relabel unadjusted prices as adjusted prices. The entire
study-period XNYS calendar must be present and identical across ETFs. Inputs are
sorted; duplicate/invalid dates, nonfinite/nonpositive values, missing sessions,
and noninteger volume are rejected. No weekend/holiday padding or forward filling
is performed. Exceptional closures are included by `exchange_calendars`.

Processed data saves both daily log returns (for variance modeling) and daily
simple returns (for traded P&L). No results are produced from generated substitutes
if data access fails; fix access or supply compliant real data and run `python project.py`.

## Models, timing, and accounting

- Zero-mean Gaussian GARCH(1,1), `h[t+1]=omega+alpha*r[t]^2+beta*h[t]`, fitted with
  `arch` to a trailing 504-session sample of percent log returns. Refit every 21
  sessions; update conditional variance using only observed shocks between fits.
  Forecast files use origin dates and daily decimal variance. Annual volatility is
  `sqrt(252*h)`. Fit diagnostics retain parameters, convergence, and warnings.
- Fits at the integrated boundary are permitted by the package and flagged when
  persistence >=0.995. An invalid/failed fit falls back explicitly to trailing
  sample variance until the next scheduled refit. No preset parameter fallback.
- Rolling benchmark: trailing 20-session log-return sample variance (`ddof=1`).
  Forecast scores use the following session's squared log return: variance MSE,
  MAE, and QLIKE=`log(h)+r^2/h` (lower better; negative scores are valid). Squared
  daily returns are noisy proxies, not observed conditional variance.
- Dynamic target: `min(cap, target_vol / max(forecast_vol, vol_floor))`. Defaults:
  15% annual target, 100% cap, 1% annual floor. Buy-and-hold always holds 100%.
- Additional threshold experiment: compare GARCH volatility with the expanding
  25th/75th percentiles of **earlier** GARCH forecasts; use 100%/50%/0% exposure,
  subject to cap. Require 126 prior forecasts. These numerical choices were absent
  from the original README and were fixed before executing results.
- **Execution:** observe signal after close t, trade at close t+1, earn the
  close t+1→t+2 return. Target weights are shifted **two rows**. Accuracy evaluation
  instead shifts forecast variance **one row**. This conservative execution rule
  makes the traded one-step forecast one session stale. All baseline strategies
  use the same OOS start, including threshold warmup; 2015–2016 are not treated as
  traded test performance. Exact close execution remains an approximation.
- Fees: 5 bps per dollar of actual one-way traded notional, including initial entry.
  Pretrade risky exposure drifts with prices. For risky fraction `a`, target `w`,
  fee rate `k`, solve fee fraction `c=k*abs(w-a)/(1+k*w*sign(w-a))`. Set risky dollars
  to `w*(NAV-fees)` and earn `(1-c)*(1+w*r+(1-w)*cash)-1`. No fees are invented for
  holding buy-and-hold; maintaining a fractional target can require rebalancing.
- Cash and borrowing rates are zero; no market impact, taxes, or forced final
  liquidation. Sensitivity caps above 100% therefore assume free financing.
- CAGR uses 252 sessions/year; Sharpe uses arithmetic daily mean with risk-free=0;
  annual volatility uses sample SD; drawdown includes initial capital. Actual
  turnover and monetary fees are retained rather than inferred from target changes.
  `Total Costs / Starting Capital` sums dollar costs divided by beginning capital;
  `Sum Cost Fractions` is a different, also saved, quantity.

## Regimes and robustness

COVID stress: 2020-02-19–2020-06-30, including the rebound. Monetary tightening:
calendar 2022. Also evaluate full calendar 2020, pre-2020 OOS, 2020–2022, and
2023–2025. Slices retain actual historical positions/costs, without reentry fees;
regime wealth/drawdown is rebased at the start. Annualized short-period statistics
are descriptive.

The full sensitivity experiment uses targets 10/15/20%, fees 0/5/10 bps, and caps
75/100/150%. Fit windows 252/504/756 at 21-session refits, plus 5/63-session refits
at window 504, yield five model schedules × 27 sizing/cost settings = 135 scenarios
per ETF. All use an identical later OOS calendar determined by the longest warmup.
No best configuration is selected. Comparisons across sensitivity settings use
this common calendar, not the earlier baseline start. Benchmark rows repeat across
irrelevant settings; scenario counts and win shares are not independent evidence.

## Files and outputs

| Location | Purpose |
| --- | --- |
| `garch_research/config.py` | Central parameters, regimes, sensitivity grids |
| `garch_research/data.py` | Download, provenance, calendar validation, returns |
| `garch_research/models.py` | Causal GARCH and historical forecasts, fit diagnostics |
| `garch_research/strategies.py` | Volatility targeting and past-only threshold signals |
| `garch_research/backtesting.py` | Self-financing positions, fees, drift, wealth |
| `garch_research/evaluation.py` | Performance, regimes, variance losses |
| `garch_research/robustness.py` | Common-period sensitivity experiments |
| `garch_research/visualization.py` | Publication-resolution PNG and vector PDF plots |
| `garch_research/report.py` | Research report generated from executed CSVs |
| `tests/test_project.py` | Timing, leakage, accounting, model, and data tests |
| `validate_results.py` | Independent checks on the saved empirical artifacts |
| `data/raw/`, `data/processed/` | Real source and cleaned data, quality audit |
| `outputs/forecasts/` | Forecast-origin files for baseline and alternative models |
| `outputs/diagnostics/` | Every scheduled fit and parameter/convergence record |
| `outputs/*_daily.csv` | Return-date ledgers: forecasts, origins, weights, fees, turnover, wealth |
| `outputs/summary.csv` | Baseline performance by ETF and strategy |
| `outputs/regime_summary.csv` | Continuous-account regime performance |
| `outputs/forecast_diagnostics.csv` | Aligned variance MSE, MAE, QLIKE by period |
| `outputs/robustness.csv` | All sensitivity results and time slices |
| `outputs/robustness_comparison.csv` | Matched Sharpe comparisons across scenarios |
| `outputs/figures/` | Exploratory, forecast, wealth, drawdown, exposure, sensitivity figures |
| `outputs/RESEARCH_REPORT.md` | Methods, measured findings, limitations, conclusions |
| `outputs/run_metadata.json` | Configuration, package versions, input/source hashes |

## Limitations

These three US equity ETFs are correlated and selected survivors. Daily squared
returns are noisy; symmetric Gaussian GARCH omits heavy tails and asymmetric shocks;
near-integrated fits may be unstable. Adjusted vendor history is not a point-in-time
archive. Execution costs are simplified, cash and financing are zero, and no
confidence intervals or statistical-superiority claims are made. Reduced drawdown
can accompany lower CAGR. Full-period tuning or selecting the best grid cell would
risk overfitting. Consult the report for measured outcomes rather than assuming
GARCH performs better.

References: [arch forecast alignment](https://arch.readthedocs.io/en/stable/univariate/forecasting.html)
and [yfinance download parameters](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html).
