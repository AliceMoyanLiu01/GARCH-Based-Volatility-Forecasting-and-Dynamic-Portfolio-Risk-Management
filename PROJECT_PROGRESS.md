# Project progress

## Repository audit

Read all five starter source/config files and the existing tests. No AGENTS.md found.
The starter likelihood incorrectly scores a shock against a variance already updated
with that shock; the claimed zero mean also conflicts with demeaning. Diagnostics
compare volatility with absolute returns instead of variance losses. Target-weight
differences omit drift turnover; buy-and-hold and drawdown inception need explicit
accounting. Missing: volume/calendar validation, convergence records, threshold
strategy, sensitivity runs, full visualizations, and an empirical research report.

## Implementation plan / checklist

- [x] Inspect repository and README; audit methodology and timing.
- [x] Centralize configuration; implement adjusted-price/volume validation and provenance.
- [x] Replace incorrect likelihood with arch GARCH; record fits and causal forecasts.
- [x] Implement causal strategies and self-financing transaction-cost accounting.
- [x] Write and execute timing, leakage, accounting, and validation tests.
- [x] Download and validate actual SPY, QQQ, IWM data, 2015–2025.
- [x] Execute baseline, regimes, forecast losses, and prespecified robustness runs.
- [x] Generate CSVs, figures, and a report derived from executed results.
- [x] Update reproduction instructions and document limitations.

## Fixed research choices

Baseline: zero-mean normal GARCH(1,1), 504 returns, 21-session refits;
20-session historical volatility; 15% annual target; 1.0 cap; 5 bps costs.
Use a conservative extra execution lag: signal after close t, rebalance at close
t+1, earn close t+1 to t+2 return. One-step forecast accuracy is assessed separately
against return t+1. This makes the executable strategy forecast one session stale.
Cash and financing rates are zero. No parameters selected using OOS performance.
Threshold allocation is an additional prespecified experiment (the supplied README
does not specify numerical thresholds): historical 25th/75th volatility percentiles,
exposures 1.0/0.5/0.0, at least 126 prior forecasts.

## Executed validation and results

- Installed `arch` and `exchange-calendars` into `.venv`; the initial restricted-network
  install failed, then the authorized network retry succeeded. No outstanding blocker.
- Downloaded actual Yahoo Finance data for all three ETFs: 2,766 rows each,
  2015-01-02 through 2025-12-31. Strict calendar validation includes exceptional
  closures. Raw/processed data and provenance hashes are retained.
- Fixed a holiday-boundary calendar error detected during initial download.
- `.venv/bin/python -m pytest -q`: **23 passed in 9.77s** on the final source.
  Tests cover causal prefix invariance across refits; direct agreement with arch;
  recurrence; future-price shocks and held weights; two-session execution alignment;
  threshold history; exact fees and cash conservation; drift turnover; buy-and-hold;
  initial-loss drawdown; variance losses; convergence failure; missing returns;
  data/calendar validation and invalid configuration.
- `.venv/bin/python project.py`: completed baseline, figures, all sensitivity
  experiments, and generated report. Baseline is 2,134 OOS sessions per ETF,
  2017-07-07 through 2025-12-31. All four strategies share this calendar.
- GARCH baseline: 108 scheduled fits per ETF, zero optimizer failures; near-integrated
  fits are flagged (17 SPY, 17 QQQ, 19 IWM), so convergence is not equated with stability.
- Sensitivity: 135 configurations per ETF, 405 total; shared OOS calendar
  2018-07-09 through 2025-12-31. Including the four strategies and seven periods,
  `outputs/robustness.csv` contains 11,340 metric rows.
- `.venv/bin/python validate_results.py`: **passed**. Independently reconciled
  25,608 strategy-days, verified input/source hashes, forecast/execution dates,
  exact traded-notional costs, cash/risky holdings conservation, interday holdings,
  wealth/CAGR/drawdown, buy-and-hold fees, and sensitivity calendar/grid completeness.
  Audit record: `outputs/validation.json`.
- `.venv/bin/python analyze_results.py`: executed successfully against saved ledgers.
- Visually inspected performance-comparison and forecast plots; saved all 16 figures
  as both high-resolution PNG and vector PDF.
- Saved an exact 50-package dependency lock and full execution metadata.

## Findings and remaining limitations

Baseline GARCH Sharpe exceeds buy-and-hold for SPY and QQQ, not IWM. Its CAGR is
lower than buy-and-hold for all three. It has lower variance MSE/MAE/QLIKE than
rolling on the shared baseline OOS period, but this does not translate into a
consistent trading advantage. All three have smaller COVID/2022 drawdowns than
buy-and-hold; all three have slightly worse 2022 drawdowns than rolling targeting.
The report presents the actual measured comparisons and sensitivity results.

Limitations are research assumptions, not execution blockers: zero cash/financing,
stale executable signals, idealized closing fills, adjusted vendor data rather
than point-in-time vintages, noisy squared-return variance proxies, near-integrated
fits, three correlated equity ETFs, and no formal significance/uncertainty inference.
No parameters were selected by test-period performance; no synthetic empirical
data or unexecuted performance claims were used.

# Phase 2 research upgrade

## Sequential execution checklist

- [x] Phase 1: audited all code/results, preserved original source/data/outputs in
  `archive/phase1/`, then reproduced the unchanged full baseline in
  `outputs/baseline_reproduced/` before modifying the accounting extension.
- [x] Phase 2: saved daily MSE/MAE/QLIKE differences, HAC inference with lag
  sensitivity, seeded circular-block bootstrap with block sensitivity, and the
  nine-test primary Holm family.
- [x] Phase 3: compared original delayed h=1 versus aligned h=2 execution;
  measured correlations/exposure, exact arithmetic cost attribution, 0/5/10-bp
  runs, a precommitted fixed 5-pp allocation band, and ex-post drawdown/recovery events.
- [x] Phase 4: calibrated frozen exposure only before 2020; evaluated 2020–2025
  under common risk budgets and dates; downloaded official EFFR and added dated
  ACT/360 cash and separate assumed borrowing costs, preserving zero-cash panels.
- [x] Phase 5: evaluated normal/t GARCH, GJR, and asymmetric EGARCH, with common
  samples/origins/calendar; saved fit diagnostics, failures, asymmetric responses,
  runtimes, and an exploratory 54-test Holm family.
- [x] Phase 6: evaluated pre-2020 OOS, 2020–2022, 2023–2025, COVID and 2022 stress
  panels; explicitly labeled later years previously inspected and retrospective.
- [x] Phase 7: generated the complete 12-section V2 report, retained the initial
  report with an upgrade pointer, and generated all six required figures as PNG/PDF.
- [x] Phase 8: executed original/new tests, independent audits, and a second full
  pipeline run with a numerical comparison of all 204 scientific CSV artifacts.

## Code changes

The original one-step model, strategy definitions, performance metrics and legacy
CLI remain available. Extended `simulate` with optional dated cash/borrowing series
and precommitted trade flags, preserving identical default results. New modules
cover inference, horizon/model extensions, economic attribution, risk matching,
chronological evaluation, figures/report/inventory, and fixed Phase 2 settings.
`validate_results.py` accepts an archived source root. `validate_phase2.py` audits
new results; `phase2.py` is the reproducible entry point. Added `pytest.ini` to keep
archived copies out of test discovery and explicitly declared statsmodels.

## Executed tests and audits

- Original tests before modifications: **23 passed in 11.52s**.
- Final `.venv/bin/python -m pytest -q`: **47 passed in 2.66s** (23 original and
  24 additional cases). Actual console output is saved in `outputs/phase2_tests.txt`.
- Baseline summary, three daily ledgers, and all sensitivity results reproduced
  exactly as parsed CSVs. Regime/forecast table differences are <=1.65e-13 from
  prior CSV round trips. See `outputs/baseline_reproduced/reproduction_comparison.csv`.
- Baseline accounting validator passed with `--source-root archive/phase1/source`.
- Final Phase 2 independent audit: **passed**, **147 ledger files** and
  **283,650 strategy-days** reconciled. Checked source/input/archive hashes,
  cash/risky holdings, dated funding, actual fees/turnover, trade timing, no-trade
  holdings, exact return attribution, HAC against statsmodels, Holm, calibration,
  cash publication availability and common risk dates.
- Independently repeated the full upgraded pipeline in `outputs/phase2_reproduced/`.
  **204 scientific CSV artifacts matched**, excluding only measured runtime columns.
  Both runs passed independent validation. Comparison details are saved in
  `outputs/phase2_reproducibility.csv`.
- Visually inspected forecast-inference and model-comparison figures; refined
  axis labels/scales and regenerated figures in both runs. This presentation-only
  post-run step is explicitly recorded in each metadata file; scientific CSVs
  were unchanged.
- Original archive hashes and ETF data bytes remain unchanged.

## Empirical findings

Primary Holm-adjusted QLIKE p-values: SPY 0.0301, QQQ 0.0353, IWM 0.0739. Only
SPY/QQQ QLIKE pass 5%; no MSE/MAE comparison passes the primary adjustment. Some
pointwise HAC/bootstrap conclusions disagree; both are reported, with sensitivity.

Aligned h=2 GARCH-minus-rolling Sharpe differences at 5 bps are -0.0010 SPY,
-0.0209 QQQ, +0.0402 IWM. Every paired 95% bootstrap interval includes zero.
The annual arithmetic extra fee drag is approximately 0.177, 0.155 and 0.081
percentage points respectively. Improved statistical forecasting therefore does
not establish a consistent incremental net Sharpe benefit over rolling volatility.
Frozen-exposure and chronological comparisons also vary across ETFs and periods.

GJR often improves QLIKE, with mixed trading effects. EGARCH exhibits converged
but explosive or collapsing forecasts: recorded rejected fits and fallback use
qualify its results. A broad symmetric numerical guard ([1e-6,1e6] times trailing
variance) was added after the observed failure, not selected for returns. Attempted
values are retained. HAC calculations scale inputs before covariance products to
avoid overflow without changing the test statistic. No best model/band was chosen.

## Assumptions and limitations

2023–2025 was already examined; there is no untouched holdout. EFFR is an official
lagged reference-rate proxy with conservative availability, not a directly traded
asset or a complete vintage archive. Ordinary revisions precede the imposed lag;
extraordinary later revisions cannot be ruled out. Historical brokerage financing
was unavailable; borrowing is EFFR plus an assumed 100 bps. EGARCH-t's second horizon
is not supplied because its exponential moment may diverge; its one-step forecasts
and delayed trading comparison are retained. Close execution, proportional costs,
no market impact, three correlated ETF survivors, noisy variance proxies, and
stationarity/moment assumptions remain limitations. No causal or equivalence
claim is inferred from an observational backtest or a non-rejection.

All exact output paths are enumerated in `outputs/PHASE2_OUTPUTS.md` and
`outputs/phase2_artifacts.json`. Main deliverable: `outputs/RESEARCH_REPORT_V2.md`.

# Final research-quality review — 2026-11-01

- [x] Installed the exact 50-package lock in a new Python 3.13 virtual environment
  with system-site-packages disabled; `pip check` found no broken requirements.
- [x] Independently reran the original 47 tests: 47 passed in 6.42s. Added three
  review regressions; the complete clean-environment suite passed **50 tests in 2.85s**.
- [x] Reexecuted the full research pipeline in the isolated environment. All
  **204 scientific CSV artifacts** reproduced within rtol=1e-10/atol=1e-12,
  excluding only measured wall-clock runtime columns. Reconciled **147 ledgers /
  283,650 strategy-days**; archive and ETF input hashes match.
- [x] Audited all **13 V2 tables and numerical conclusion statements**, with
  **1,317 checks**. No material numerical discrepancy was found. Methodology,
  dates/configuration, execution precision, multiplicity and holdout wording were
  reviewed separately; agreement with CSVs is not proof of modeling assumptions.
- [x] Investigated EGARCH without changing models, numerical guards, strategy
  settings or investment outcomes. Archived before-review metadata/report; verified
  the same hashes for 12 modeling/strategy/inference/accounting modules.
- [x] Saved failure counts, attempted values, extreme-observation attribution,
  loss-by-source decomposition and diagnostic likelihood replays in `outputs/review/`.
- [x] Created `FINAL_RESEARCH_REPORT.md` (~1,200 words), `PROJECT_SUMMARY.md`
  (364 words), `docs/EGARCH_REVIEW.md` and `docs/FINAL_REVIEW_NOTES.md`.
- [x] Strengthened output validation: a missing/empty or incomplete ledger set
  now fails explicitly instead of allowing an empty accounting audit to pass.
  Prior audits had complete actual ledgers; this does not invalidate those checks.
- [x] Replaced machine-specific inventories with relative paths; excluded caches,
  virtual environments, detailed regenerated ledgers, temporary logs and duplicated
  runs from publication. Moved old reruns to ignored `.local/reproduction_history/`.
  Frozen Phase 1 inputs/results remain intentionally retained for provenance.
- [x] Added a curated publication exporter and manifest; no commit/upload is made.

## EGARCH findings and remaining issues

Gaussian EGARCH for SPY still admits daily variance 2.651531 under the broad
unchanged guard; its MSE is 0.05378269. The 20 largest squared errors account for
97.25% of total squared loss. IWM Gaussian EGARCH MSE is 4.552439e-5, with 98.99%
in the top 20. Fallback is used on 1.97%–6.28% of scored dates across the six EGARCH
panels; the large normal-EGARCH MSEs are overwhelmingly driven by accepted forecasts.

Converged fits can have extreme/unbounded shock coefficients. arch bounds the
in-sample variance filter but the one-step endpoint and subsequent direct recursion
can extrapolate badly. A beta persistence check does not detect this failure.
Diagnostic changes to likelihood starting values and ~1e-14-percent-return CSV
rounding can radically alter unstable fits. They were NOT used to replace study
forecasts or select a profitable rule. EGARCH remains unresolved/exploratory and
is excluded from headline economic claims.

The central result remains: selected QLIKE improvements survive the stated primary
Holm family, but all aligned GARCH-minus-rolling Sharpe intervals include zero.
The project is suitable as transparent undergraduate research, not a validated
alpha/production-trading claim. 2023–2025 remains previously inspected retrospective
history. Closing fills, vendor revisions, rate vintages, funding and statistical
regularity assumptions remain limits. Cross-platform numerical identity was not
established; clean-environment verification was on the same host.

Publication extraction check completed: 50 tests passed in 11.13s, full pipeline
regenerated missing processed data/ledgers, independent validation and all 1,317
report checks passed. Scientific comparison again matched 204 CSV artifacts.
A packaging omission of a manifest-required historical log was caught and fixed;
all 102 immutable baseline members are verified by hash in the final bundle.
See `docs/PUBLICATION_CHECK.md` and retained console/audit evidence.
