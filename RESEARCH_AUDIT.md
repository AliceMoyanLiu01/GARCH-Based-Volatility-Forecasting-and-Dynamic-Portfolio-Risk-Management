# Phase 2 research audit

## Baseline preservation and reproduction (completed before implementation changes)

Read the original source, tests, README, report, configurations, metadata, and
saved result tables/ledgers. `archive/phase1/` preserves the original source,
real data, and outputs; `archive_manifest.json` hashes every archived file.
Reexecuted the unchanged full pipeline into `outputs/baseline_reproduced/`.
Summary, daily ledgers, and all sensitivity results reproduce exactly as parsed
CSV values. Regime/forecast tables differ by at most 1.65e-13 because the originals
were regenerated from rounded CSV ledgers; tolerance rtol=1e-10, atol=1e-12.
The deliberately tighter initial comparison detected this numerical round-trip
variation, not an economic discrepancy. See `reproduction_comparison.csv`.
The independent baseline accounting validator passed for 25,608 strategy-days.

## Confirmed correct

- arch Gaussian zero-mean GARCH likelihood, 504-session rolling samples,
  21-session parameter refits, and causal intervening variance recursion.
- Percent-return fitting to decimal daily variance conversion (divide by 10,000),
  annual volatility sqrt(252*h), and log/simple return separation.
- Forecast origin t paired with return t+1 for statistical scores; exposure is
  shifted two sessions for tradable close t+1→t+2 P&L.
- Exact post-fee target weights, actual-notional turnover including market drift,
  cash conservation, initial entry costs, no artificial buy-and-hold rebalancing.
- Common OOS calendars, past-only threshold quantiles, drawdown including initial
  capital, and continuous-account regime slices without fictitious reentry fees.
- Historical ETF data is unchanged and passes complete exchange-calendar checks.

## Weaknesses and clarification

1. **Horizon mismatch, not future leakage.** A one-step forecast predicts r[t+1],
   but the delayed executed position earns r[t+2]. Compare original A against B:
   estimate E_t[h[t+2]]=omega+(alpha+beta)*h[t+1], still execute at close t+1.
   This is the second day's variance, NOT summed two-day return variance. Rolling
   uses its constant local variance for both horizons. No same-close execution.
2. Forecast loss rankings lack sampling uncertainty/multiplicity correction.
   Add Bartlett HAC, circular moving-block bootstrap, and Holm adjustment.
   MAE targets a median and is not generally robust to a noisy variance proxy;
   MSE/QLIKE interpretation still needs conditional-unbiasedness assumptions.
3. Equal target vols do not imply equal exposures or realized risk. Freeze an
   exposure benchmark using 2017–2019 executable GARCH allocations, then evaluate
   2020–2025. Later-period comparisons cannot use its own mean allocation.
4. Cash/borrowing were zero; add a lagged official overnight-rate proxy, separately
   priced borrowing, and excess-return Sharpe. Historical broker financing is
   unavailable; a 100-bp borrowing spread will be an assumption, not observed data.
5. Trading costs, rebound participation, and weight correlation need decomposition.
   Use exact arithmetic daily return differences; CAGR differences are not additive.
6. Integrated-boundary fits converge but need not be stable. Retain diagnostics
   and flag alternative-model failure/fallback. More models create exploratory
   hypotheses, not new confirmatory evidence.
7. 2023–2025 was already inspected. It can be retrospective chronological
   validation, never a genuinely untouched holdout. Freeze Phase 2 choices before
   executing its results; do not pick a model or band based on these outcomes.

## Fixed Phase 2 specification

Primary family: 3 ETFs × 3 losses for Gaussian GARCH vs rolling at h=1, on the
original 2017-07-07–2025-12-31 calendar. Two-sided asymptotic normal HAC tests;
primary lag floor(4*(n/100)^(2/9)), sensitivity lags 0/5/10/21/63. Holm controls
familywise error for the nine primary p-values. Bootstrap: circular moving blocks,
20 sessions, 2,000 replications, seed 20261031; block lengths 5 and 60 are sensitivity
checks. All intervals are pointwise, not simultaneous; no equivalent-model claim
from failure to reject. An exploratory matched-date Sharpe-difference bootstrap
will quantify economic uncertainty as well.

Trading: retain 15% target, 100% cap, 5 bps baseline. Cost grid 0/5/10 bps;
turnover control is a fixed 5-percentage-point band relative to the last accepted
target, with the trade/no-trade decision fixed at the prior signal origin. A drift
band evaluated at the execution close would require unobserved same-close inputs;
the implemented target-change band avoids that assumption. Hold shares between
scheduled trades. The band experiment is unlevered (cap 100%); no band tuning.
Calibration ends 2019-12-31; matched tests
begin 2020-01-02. Same dates/risk budgets/costs/cash assumptions within every panel.

Alternative families: GARCH, GJR-GARCH, asymmetric EGARCH, each normal/Student-t,
identical rolling samples/refits/origins. Compare one-step forecasts and the same
original delayed trading convention for all six. Gaussian EGARCH h=2 has an
analytic expectation; Student-t EGARCH generally has no finite exponential moment
for h=2, so do not manufacture a finite variance with a small Monte Carlo sample.
Mark that horizon unavailable while retaining its valid one-step comparison.

Descriptive events: three deepest nonoverlapping buy-and-hold drawdown episodes
per ETF in OOS; identify trough/recovery ex post only for attribution, never sizing.
Chronological panels: available OOS through 2019, 2020–2022, and 2023–2025; also
retain fixed COVID and 2022 stress windows. No random time-series train/test split.

## Executed outcomes and implementation refinements

The full upgrade and its second independent run completed. Original/new tests pass
(47 total). Independent Phase 2 accounting and inference validation passes for 147
ledgers and 283,650 strategy-days. All 204 scientific CSV artifacts reproduce,
excluding measured runtime columns. Archive and original ETF data hashes match.

A numerical problem appeared during alternative-model execution: some EGARCH fits
claimed convergence while emitting explosive or collapsing variance. A broad,
uniform guard rejects forecasts outside [1e-6,1e6] times trailing historical
variance, records attempted values/reasons, and invokes the explicit fallback.
This guard was added after the observed numerical failure, not prespecified as an
investment improvement or tuned on Sharpe. Large finite loss values also motivated
scale-normalized HAC covariance products; the statistic is scale invariant and is
tested against statsmodels and at extreme scales. These changes are documented in
V2 rather than concealed as part of the initial fixed specification.

Official EFFR was retrieved from the NY Fed API. Availability is conservatively
two US federal business days after observation, then constrained to holding start;
calendar-day cash/borrowing accrual is ACT/360. The current official history lacks a
complete vintage archive; extraordinary later revisions remain a limitation. Actual
historical broker funding was not obtained; a 100-bp spread is explicitly assumed.

Primary forecast evidence is strongest for SPY/QQQ QLIKE after Holm correction.
All paired aligned GARCH-versus-rolling Sharpe intervals include zero. Neither
finding implies model equivalence or a causal investment effect. See the generated
V2 report for measured results, negative findings, and stability diagnostics.

## Final independent review — 2026-11-01

Fresh package-isolated Python 3.13 environment: original 47 tests passed; the final
suite has 50 passing tests. A clean full run reproduced 204 scientific CSV outputs,
with 147 ledgers / 283,650 strategy-days independently reconciled. All 13 V2 tables
and numerical conclusions passed 1,317 recorded claim checks. No model or numerical
threshold was changed; a missing-ledger audit defect was fixed and regression-tested.

EGARCH remains unreliable. SPY Gaussian EGARCH MSE=0.05378269 is dominated by accepted
abnormal forecasts, with 97.25% of squared error in 20 observations. The broad guard
still admits daily variance 2.651531. Source and likelihood replays identify extreme
shock coefficients, bounded-filter/unbounded-endpoint extrapolation, weak local
likelihood solutions, and sensitivity to ~1e-14 changes in percent-return inputs.
Fallback contributions are explicitly decomposed without deleting failure dates.
No diagnostic restart was selected using trading performance or substituted into
published results. See `docs/EGARCH_REVIEW.md` and `outputs/review/`.

Clarified exact fractional closing execution as an assumption. Primary significance
is within a fixed retrospective family, not proof against all research-selection
bias. Non-rejection is not equivalence; later years are not untouched. The concise
final report and one-page summary present these qualifications for a portfolio reader.
