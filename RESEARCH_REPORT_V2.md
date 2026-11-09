# GARCH Forecasting and Economic Value — Research Report V2

## 1. Executive summary

The preserved Phase 1 baseline was reproduced before changing its implementation.
The primary nine-test family supports lower GARCH forecast loss after Holm adjustment
at 5% for: **SPY QLIKE, QQQ QLIKE**. Negative estimates alone are not evidence of significance.
The aligned-horizon, 5-bp, unlevered trading comparison is:

| Ticker | Strategy | CAGR | Gross CAGR | Sharpe (rf=0) | Maximum Drawdown | Average Exposure | Annualized Turnover |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | GARCH | 12.45% | 12.80% | 0.9375 | -19.55% | 89.28% | 6.3249 |
| SPY | Rolling | 12.32% | 12.48% | 0.9385 | -19.30% | 88.15% | 2.7891 |
| QQQ | GARCH | 15.44% | 15.87% | 1.0276 | -21.71% | 78.03% | 7.4459 |
| QQQ | Rolling | 15.72% | 15.97% | 1.0485 | -21.65% | 77.74% | 4.3448 |
| IWM | GARCH | 4.61% | 4.95% | 0.3761 | -24.32% | 74.14% | 6.5998 |
| IWM | Rolling | 4.06% | 4.32% | 0.3358 | -26.27% | 75.67% | 4.9689 |

Better volatility prediction is distinct from robust economic value. The cost,
exposure-matched, chronological, and uncertainty results below qualify this conclusion.
No configuration was selected to maximize an observed Sharpe ratio.

## 2. Research question and hypotheses

Does GARCH's forecast accuracy produce meaningful economic value after trading costs,
frequency, and exposure differences? The primary statistical family contains nine
Gaussian GARCH-minus-rolling mean loss hypotheses (3 ETFs × MSE/MAE/QLIKE). Two-sided
HAC tests reject equal average loss; a negative rejected estimate favors GARCH.
Economic comparisons ask whether paired net Sharpe differences survive uncertainty,
costs, earlier-period exposure calibration, and changing market periods. These are
observational backtests, not causal identification or investment recommendations.

Phase 2 choices were recorded in `../RESEARCH_AUDIT.md` before its analysis was run.
They are prespecified within this upgrade, not preregistered before seeing this history.

## 3. Data and methodology

Use the unchanged SPY/QQQ/IWM adjusted-close and volume dataset, 2015–2025, 2,766 rows
per ETF. Baseline comparison dates remain 2017-07-07–2025-12-31 (2,134 returns), so
results reproduce Phase 1 despite its additional threshold warmup. Hashes, versions,
configuration, and archived baseline inputs are in `phase2_metadata.json`.

The original implementation correctly used percent log returns for estimation,
decimal daily variance for forecasts, annualized volatility sqrt(252*h), simple
returns for P&L, monthly trailing-window refits, drift-aware actual-notional fees,
initial investment costs, and drawdown relative to starting capital. All four Phase 1
strategies and its full sensitivity grid are preserved in `../archive/phase1/`.
The baseline reproduction record is in `review/baseline_reproduction_comparison.csv`;
the final clean-environment comparison is in `review/clean_reproduction_comparison.csv`.

**Horizon A:** after close t, use h[t+1|t], execute close t+1, earn r[t+2]. It is causal
but its forecast is stale. **Horizon B:** at the same signal and execution times, use
h[t+2|t]=omega+(alpha+beta)*h[t+1|t]. This is the actual holding day's conditional
variance, not h[t+1]+h[t+2]. Rolling assumes local constant variance at both horizons.
No order uses information first observed after its execution close. Statistical
one-step losses align forecasts with r[t+1]^2; horizon-2 losses align with r[t+2]^2.
`horizon_comparison.csv` and `horizon_statistical_tests.csv` retain both comparisons.
The second-horizon tests form a separate exploratory nine-test Holm family.

This is a fractional-notional, idealized close-fill backtest. Target fractions are
chosen earlier, but the accounting assumes they can be attained exactly at the next
closing price after fees. Real market-on-close quantity sizing and fills need not
achieve these fractions. Signal timing is causal; execution precision is an assumption.

Unchanged baseline: 504-session rolling fits, 21-session refits, 20-session rolling
volatility, zero mean, 15% target, 100% cap, 1% volatility floor, 5-bp one-way fees,
zero cash. A fixed 5-percentage-point target-change band is an exploratory mechanism:
at the signal origin, compare desired allocation with the last accepted target;
precommit the trade flag, shift it two sessions, and hold shares otherwise. No band
is evaluated using the unknown execution close. This is not a drift-band rule.

## 4. Forecast accuracy results

All baseline mean loss differences are saved in `forecast_loss_differentials.csv`.
Squared log returns are noisy proxies; MSE and QLIKE require suitable proxy conditions
for latent-variance model rankings. MAE generally does not preserve such rankings
under noisy measurement and targets a median rather than a conditional mean.

| Ticker | Loss | n | mean_difference |
| --- | --- | --- | --- |
| SPY | MSE | 2134 | -5.74739e-08 |
| SPY | MAE | 2134 | -1.28933e-05 |
| SPY | QLIKE | 2134 | -0.116184 |
| QQQ | MSE | 2134 | -5.28196e-08 |
| QQQ | MAE | 2134 | -1.11017e-05 |
| QQQ | QLIKE | 2134 | -0.0825441 |
| IWM | MSE | 2134 | -6.47331e-08 |
| IWM | MAE | 2134 | -8.64224e-06 |
| IWM | QLIKE | 2134 | -0.0500189 |

## 5. Statistical inference

HAC uses an intercept-only Bartlett/Newey-West long-run variance estimator with
n-denominator autocovariances and no degrees-of-freedom correction. Primary bandwidth
is floor(4*(n/100)^(2/9)); asymptotic normal two-sided p-values and 95% intervals.
Lags 0,5,10,21,63 are sensitivity checks; lag 0 intentionally omits serial dependence.
No finite-sample DM correction is claimed. These are DM-style equal predictive-loss
tests with overlapping rolling parameter estimates and a single historical path.
Holm familywise correction is applied to the nine primary p-values only; sensitivity
lags are not alternative routes to a preferred rejection.

| Ticker | Loss | hac_lag | statistic | p_value | p_holm | ci_low | ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | MSE | 7 | -1.5263 | 0.1269 | 0.4224 | -1.31277e-07 | 1.63293e-08 |
| SPY | MAE | 7 | -1.8680 | 0.0618 | 0.3706 | -2.64214e-05 | 6.34773e-07 |
| SPY | QLIKE | 7 | -2.9343 | 0.0033 | 0.0301 | -0.193791 | -0.038578 |
| QQQ | MSE | 7 | -1.4732 | 0.1407 | 0.4224 | -1.23091e-07 | 1.74518e-08 |
| QQQ | MAE | 7 | -1.7775 | 0.0755 | 0.3774 | -2.33427e-05 | 1.13933e-06 |
| QQQ | QLIKE | 7 | -2.8473 | 0.0044 | 0.0353 | -0.139364 | -0.0257243 |
| IWM | MSE | 7 | -1.4522 | 0.1465 | 0.4224 | -1.52102e-07 | 2.2636e-08 |
| IWM | MAE | 7 | -1.6182 | 0.1056 | 0.4224 | -1.91095e-05 | 1.82503e-06 |
| IWM | QLIKE | 7 | -2.5569 | 0.0106 | 0.0739 | -0.0883606 | -0.0116772 |

Circular moving-block bootstrap: uniform block starts, wrap at the sample boundary,
concatenate/truncate to n, block length 20 sessions, 2,000 replications, seed 20261031
with fixed ticker/loss offsets. Percentile 2.5%/97.5% intervals; blocks 5 and 60 are
saved sensitivity checks. These bootstrap intervals and HAC intervals are pointwise,
not multiplicity-adjusted simultaneous intervals.

| Ticker | Loss | bootstrap_low | bootstrap_high |
| --- | --- | --- | --- |
| SPY | MSE | -1.50958e-07 | -1.08367e-10 |
| SPY | MAE | -3.11603e-05 | -8.17839e-07 |
| SPY | QLIKE | -0.192326 | -0.0453763 |
| QQQ | MSE | -1.36081e-07 | 1.1777e-09 |
| QQQ | MAE | -2.62244e-05 | 9.91982e-07 |
| QQQ | QLIKE | -0.141749 | -0.0318725 |
| IWM | MSE | -1.75338e-07 | -2.06043e-10 |
| IWM | MAE | -2.2301e-05 | 1.40698e-06 |
| IWM | QLIKE | -0.087811 | -0.0146375 |


Pointwise HAC/bootstrap zero-exclusion disagreements: SPY MSE, SPY MAE, IWM MSE. HAC uses a symmetric normal approximation; percentile blocks capture a skewed finite-sample distribution and a different dependence bandwidth. Rare crisis observations can dominate squared-error losses; intervals near zero are sensitive to resampling. Neither method is selected because it favors GARCH. Dependence stationarity/mixing, finite relevant moments, and reasonable bandwidth/block choices are assumptions, potentially strained by structural breaks. An insignificant result is not proof of equivalence.


## 6. Strategy performance and economic attribution

Matched-date weight and forecast correlations, exposure in market drawdowns below
−10%, trading frequency, costs, and both gross/net results are in
`performance_attribution.csv` and `strategy_summary_v2.csv`.

| Ticker | Forecast correlation | Weight correlation | Mean abs weight difference | Annual gross difference | Annual differential fee drag | Annual net difference |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | 0.8818 | 0.8606 | 4.97% | 0.31% | 0.18% | 0.13% |
| QQQ | 0.8936 | 0.8917 | 6.81% | -0.07% | 0.16% | -0.23% |
| IWM | 0.8998 | 0.8591 | 7.74% | 0.54% | 0.08% | 0.46% |

For each day, net return = gross return − fee_fraction*(1+gross_return). Thus
annualized arithmetic GARCH-minus-rolling net difference equals gross difference
minus differential fee drag exactly. The gross difference is further decomposed
as mean(delta_weight)*mean(market_return) plus the population covariance term.
This is descriptive exposure/timing accounting, not a causal estimate.

| Ticker | Average exposure component | Timing covariance component | Annual gross difference |
| --- | --- | --- | --- |
| SPY | 0.18% | 0.13% | 0.31% |
| QQQ | 0.06% | -0.13% | -0.07% |
| IWM | -0.17% | 0.70% | 0.54% |

CAGR differences are separately reported and are **not** an additive decomposition.
The 0/5/10-bp runs share all other settings. Gross CAGR is the compounded gross
return of each ledger's actual weights; no performance ranking was used to choose
fees. The paired circular-block Sharpe intervals resample the same dates for both
strategies, preserving cross-strategy dependence and treating fitted realized
strategy returns as given (not re-estimating all models in every resample):

| Ticker | Convention | Sharpe difference | Sharpe CI low | Sharpe CI high | block_length | bootstrap_reps |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | A_delayed_h1 | 0.0017 | -0.1112 | 0.1193 | 20 | 2000 |
| SPY | B_aligned_h2 | -0.0010 | -0.1155 | 0.1155 | 20 | 2000 |
| QQQ | A_delayed_h1 | -0.0157 | -0.1160 | 0.0855 | 20 | 2000 |
| QQQ | B_aligned_h2 | -0.0209 | -0.1203 | 0.0821 | 20 | 2000 |
| IWM | A_delayed_h1 | 0.0344 | -0.0702 | 0.1367 | 20 | 2000 |
| IWM | B_aligned_h2 | 0.0402 | -0.0658 | 0.1439 | 20 | 2000 |

Turnover-control comparison at aligned horizon and 5 bps:

| Ticker | Strategy | Rule | CAGR | Sharpe (rf=0) | Annualized Turnover | Trading frequency |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | GARCH | daily | 12.45% | 0.9375 | 6.3249 | 41.47% |
| SPY | Rolling | daily | 12.32% | 0.9385 | 2.7891 | 40.21% |
| SPY | GARCH | band5pp | 12.20% | 0.9282 | 5.3574 | 20.81% |
| SPY | Rolling | band5pp | 12.26% | 0.9390 | 1.9199 | 7.92% |
| QQQ | GARCH | daily | 15.44% | 1.0276 | 7.4459 | 75.21% |
| QQQ | Rolling | daily | 15.72% | 1.0485 | 4.3448 | 67.67% |
| QQQ | GARCH | band5pp | 15.38% | 1.0358 | 5.4521 | 24.65% |
| QQQ | Rolling | band5pp | 15.67% | 1.0444 | 3.0957 | 13.73% |
| IWM | GARCH | daily | 4.61% | 0.3761 | 6.5998 | 81.87% |
| IWM | Rolling | daily | 4.06% | 0.3358 | 4.9689 | 77.55% |
| IWM | GARCH | band5pp | 4.30% | 0.3587 | 4.6641 | 20.52% |
| IWM | Rolling | band5pp | 4.00% | 0.3317 | 3.3401 | 14.71% |

## 7. Risk-matched comparisons and cash

Exposure is calibrated using only executable GARCH h=2 allocations before 2020,
then frozen as a constant-mix benchmark for 2020–2025. It rebalances to that fixed
fraction and pays actual fees. Calibration is independent of subsequent returns;
the realized later average GARCH exposure need not equal the frozen value.

| Ticker | Cap | Calibration start | Calibration end | Observations | Frozen exposure | Test start |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | 1.0000 | 2017-07-07 | 2019-12-31 | 626 | 95.01% | 2020-01-02 |
| SPY | 1.5000 | 2017-07-07 | 2019-12-31 | 626 | 127.20% | 2020-01-02 |
| QQQ | 1.0000 | 2017-07-07 | 2019-12-31 | 626 | 88.99% | 2020-01-02 |
| QQQ | 1.5000 | 2017-07-07 | 2019-12-31 | 626 | 100.90% | 2020-01-02 |
| IWM | 1.0000 | 2017-07-07 | 2019-12-31 | 626 | 92.72% | 2020-01-02 |
| IWM | 1.5000 | 2017-07-07 | 2019-12-31 | 626 | 102.74% | 2020-01-02 |

GARCH/rolling receive the same 15% ex-ante risk budget, caps, fees, cash assumptions,
and evaluation dates. Buy-and-hold and frozen exposure are comparison benchmarks,
not strategies claimed to have that risk budget. Realized risk is reported explicitly.

| Ticker | Cash scenario | Strategy | CAGR | Annualized Volatility | Excess Sharpe | Maximum Drawdown | Average Exposure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | Zero cash | GARCH | 12.52% | 14.02% | 0.9120 | -19.55% | 86.90% |
| SPY | Zero cash | Rolling | 12.25% | 13.96% | 0.8980 | -19.30% | 86.42% |
| SPY | Zero cash | Frozen exposure | 14.34% | 19.71% | 0.7787 | -32.25% | 95.01% |
| SPY | Zero cash | Buy-and-Hold | 15.02% | 20.74% | 0.7789 | -33.72% | 100.00% |
| SPY | Lagged EFFR | GARCH | 12.76% | 14.02% | 0.7276 | -19.38% | 86.90% |
| SPY | Lagged EFFR | Rolling | 12.52% | 13.96% | 0.7147 | -19.10% | 86.42% |
| SPY | Lagged EFFR | Frozen exposure | 14.50% | 19.71% | 0.6439 | -32.24% | 95.01% |
| SPY | Lagged EFFR | Buy-and-Hold | 15.02% | 20.74% | 0.6442 | -33.72% | 100.00% |
| QQQ | Zero cash | GARCH | 14.82% | 15.28% | 0.9812 | -21.71% | 73.48% |
| QQQ | Zero cash | Rolling | 15.39% | 15.47% | 1.0033 | -21.65% | 74.49% |
| QQQ | Zero cash | Frozen exposure | 18.06% | 22.53% | 0.8501 | -31.67% | 88.99% |
| QQQ | Zero cash | Buy-and-Hold | 20.10% | 25.31% | 0.8507 | -35.12% | 100.00% |
| QQQ | Lagged EFFR | GARCH | 15.48% | 15.28% | 0.8361 | -21.38% | 73.48% |
| QQQ | Lagged EFFR | Rolling | 16.03% | 15.47% | 0.8587 | -20.99% | 74.49% |
| QQQ | Lagged EFFR | Frozen exposure | 18.43% | 22.53% | 0.7397 | -31.59% | 88.99% |
| QQQ | Lagged EFFR | Buy-and-Hold | 20.10% | 25.31% | 0.7403 | -35.12% | 100.00% |
| IWM | Zero cash | GARCH | 3.83% | 15.32% | 0.3220 | -24.32% | 66.43% |
| IWM | Zero cash | Rolling | 3.10% | 16.14% | 0.2701 | -26.27% | 69.87% |
| IWM | Zero cash | Frozen exposure | 7.82% | 24.71% | 0.4290 | -38.60% | 92.72% |
| IWM | Zero cash | Buy-and-Hold | 8.19% | 26.65% | 0.4294 | -41.07% | 100.00% |
| IWM | Lagged EFFR | GARCH | 4.70% | 15.32% | 0.1942 | -22.91% | 66.43% |
| IWM | Lagged EFFR | Rolling | 3.83% | 16.14% | 0.1402 | -25.19% | 69.87% |
| IWM | Lagged EFFR | Frozen exposure | 8.04% | 24.71% | 0.3241 | -38.59% | 92.72% |
| IWM | Lagged EFFR | Buy-and-Hold | 8.19% | 26.65% | 0.3245 | -41.07% | 100.00% |

The optional cash proxy is official New York Fed EFFR, buffered back to December
2014 only for availability at the start of the fixed ETF history. It is an overnight
reference rate, not an investable Treasury return. The rate is normally published
next business day around 9 a.m.; ordinary revisions occur that publication day.
We conservatively assign availability two US federal business days after observation,
then use only quotes available by the holding-start close. Saved alignment files
include observation date, availability date, holding start, and calendar-day count.
Cash accrues lagged annual percent/100 × actual days/360, including weekends.
Borrowing uses the same lagged base plus an **assumed** 100 bp spread, separately
charged only on negative cash. The 150% cap is a financing sensitivity. Real historical
broker funding terms were not obtained. `data/cash/manifest.json` preserves source and hash.

The current official historical file is not a complete vintage archive. Normal
same-day revisions precede our use; extraordinary later revisions cannot be ruled
out. Rate values are never used to select volatility models or target weights.
Thus this is a lagged cash/financing sensitivity, not proof of perfect point-in-time
rate reconstruction. Both zero-cash and lagged-rate scenarios are retained.
Excess Sharpe uses portfolio return minus the same dated cash return, and the SD
of that excess return; the legacy rf=0 Sharpe is also retained.

## 8. Alternative volatility models

Normal and standardized Student-t innovations are fitted for GARCH(1,1),
GJR-GARCH(1,1,1), and asymmetric EGARCH(p=1,o=1,q=1), using identical trailing
samples, refit schedule, origins, and scored dates. All trade under the same original
h=1 delayed convention in this exploratory model panel. This keeps the forecast
and trading comparisons common across all six; it does not fix A's stale horizon.

| Ticker | Model | MSE | MAE | QLIKE | CAGR | Sharpe (rf=0) | Failed fits | Fallback share | Compute seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | GARCH_normal | 2.40776e-07 | 1.46977e-04 | -8.3318 | 12.44% | 0.9402 | 0 | 0.00% | 0.4895 |
| SPY | GARCH_t | 2.42174e-07 | 1.48979e-04 | -8.3393 | 12.53% | 0.9567 | 0 | 0.00% | 0.8213 |
| SPY | GJR_normal | 2.53930e-07 | 1.46591e-04 | -8.3813 | 11.88% | 0.9188 | 0 | 0.00% | 0.6847 |
| SPY | GJR_t | 2.53404e-07 | 1.48813e-04 | -8.3821 | 11.76% | 0.9211 | 0 | 0.00% | 0.9518 |
| SPY | EGARCH_normal | 5.37827e-02 | 2.30175e-02 | -8.2195 | 11.67% | 0.8928 | 5 | 2.95% | 1.1275 |
| SPY | EGARCH_t | 2.49220e-07 | 1.41151e-04 | -2.4552 | 11.63% | 0.8969 | 6 | 6.28% | 2.8434 |
| SPY | Rolling | 2.98250e-07 | 1.59871e-04 | -8.2156 | 12.32% | 0.9385 | 0 | 0.00% | — |
| QQQ | GARCH_normal | 3.64732e-07 | 2.28269e-04 | -7.7268 | 15.52% | 1.0328 | 0 | 0.00% | 0.4859 |
| QQQ | GARCH_t | 3.64712e-07 | 2.30699e-04 | -7.7298 | 15.15% | 1.0277 | 0 | 0.00% | 0.8225 |
| QQQ | GJR_normal | 3.58629e-07 | 2.19953e-04 | -7.7674 | 15.56% | 1.0440 | 0 | 0.00% | 0.6217 |
| QQQ | GJR_t | 3.60798e-07 | 2.24271e-04 | -7.7627 | 15.26% | 1.0433 | 0 | 0.00% | 1.4268 |
| QQQ | EGARCH_normal | 3.62924e-07 | 2.14671e-04 | -7.6935 | 15.32% | 1.0075 | 2 | 1.97% | 1.0811 |
| QQQ | EGARCH_t | 3.63985e-07 | 2.19050e-04 | -7.6768 | 14.98% | 1.0092 | 3 | 2.95% | 1.6202 |
| QQQ | Rolling | 4.17552e-07 | 2.39371e-04 | -7.6443 | 15.72% | 1.0485 | 0 | 0.00% | — |
| IWM | GARCH_normal | 4.51254e-07 | 2.32946e-04 | -7.6664 | 4.51% | 0.3702 | 0 | 0.00% | 0.5239 |
| IWM | GARCH_t | 4.51586e-07 | 2.32759e-04 | -7.6553 | 4.60% | 0.3760 | 0 | 0.00% | 1.0643 |
| IWM | GJR_normal | 4.66511e-07 | 2.32746e-04 | -7.6870 | 4.93% | 0.3927 | 1 | 0.98% | 0.8173 |
| IWM | GJR_t | 4.69624e-07 | 2.33238e-04 | -7.6773 | 4.95% | 0.3953 | 0 | 0.00% | 1.3653 |
| IWM | EGARCH_normal | 4.55244e-05 | 8.64333e-04 | -7.5829 | 4.55% | 0.3685 | 6 | 2.95% | 1.2463 |
| IWM | EGARCH_t | 4.58446e-07 | 2.27920e-04 | -7.6231 | 4.47% | 0.3636 | 8 | 5.90% | 2.9919 |
| IWM | Rolling | 5.15987e-07 | 2.41588e-04 | -7.6164 | 4.06% | 0.3358 | 0 | 0.00% | — |

Convergence flags, fitted coefficients, persistence ranges, near-boundary indicators,
and failures are retained. Invalid fits/recursions switch explicitly to trailing
historical variance until the next scheduled fit. One-step failures do not silently
remove dates from a model's score. `extended_statistical_tests.csv` applies Holm to
all 54 exploratory ETF×model×loss tests versus rolling, separately from the primary
family. This is not an independent confirmatory model-selection exercise.

The first alternative-model run exposed converged but explosive EGARCH fits, including
overflow in squared losses and collapsing variance estimates. A broad numerical
guard now rejects forecasts outside [one millionth, one million] times the trailing
sample variance, uniformly for all model families. HAC calculations normalize
losses before forming products to avoid overflow for large but finite differences.
It is a numerical stability safeguard added after observing failure, not a tuned
investment parameter. Attempted values, bounds, and reasons are saved; explosive
one-step fits use the explicit historical fallback, and unusable second horizons
are flagged unavailable. Scores therefore describe the model-plus-fallback policy,
not a pristine successful EGARCH process. Fallback dependence weakens comparisons.

The final review found that the broad guard still admits economically abnormal
forecasts and optimizer convergence does not establish a reliable EGARCH fit.
EGARCH remains an unresolved exploratory specification; its results are excluded
from the headline economic conclusion. See `../docs/EGARCH_REVIEW.md` and the
loss-by-source audit in `review/`. No model parameters or guard thresholds were
changed to improve portfolio performance during that review.

GJR includes a negative-shock squared-return term; EGARCH includes signed standardized
shocks. `asymmetry_response.csv` evaluates +2% and −2% shocks at fixed 1% conditional
volatility for every accepted fit, isolating the fitted response shape without
claiming a causal market effect. Computational time is measured wall-clock time;
its variation across reruns is not a scientific reproducibility failure.

EGARCH Gaussian day-2 variance uses the analytic folded-normal exponential moment.
For Student-t EGARCH, the corresponding exponential moment generally diverges;
we explicitly mark h=2 unavailable, rather than substitute a misleading finite
Monte Carlo estimate. Its valid one-step forecasts are still fully evaluated.

## 9. Regime and chronological analysis

2015–2019 supplies initial estimation/exploratory history; available pre-2020 OOS
results start in July 2017. 2020–2022 is development/validation; 2023–2025 is a
**retrospective later-period evaluation**. All these years were already inspected
in Phase 1. Fixed specifications and chronological ordering do not turn the last
period into an untouched holdout. Rolling re-estimation continues using information
observed before each origin; there is no random train/test shuffle.

| Ticker | Period | Model | CAGR | Sharpe (rf=0) | Maximum Drawdown |
| --- | --- | --- | --- | --- | --- |
| SPY | Exploratory OOS 2017-2019 | GARCH | 12.24% | 1.0136 | -17.41% |
| SPY | Exploratory OOS 2017-2019 | Rolling | 12.46% | 1.0639 | -15.37% |
| SPY | Development 2020-2022 | GARCH | 6.91% | 0.5322 | -19.55% |
| SPY | Development 2020-2022 | Rolling | 6.07% | 0.4700 | -19.30% |
| SPY | Retrospective 2023-2025 | GARCH | 18.48% | 1.3268 | -18.07% |
| SPY | Retrospective 2023-2025 | Rolling | 18.84% | 1.4007 | -15.65% |
| QQQ | Exploratory OOS 2017-2019 | GARCH | 16.93% | 1.1431 | -17.35% |
| QQQ | Exploratory OOS 2017-2019 | Rolling | 16.49% | 1.1730 | -15.43% |
| QQQ | Development 2020-2022 | GARCH | 7.63% | 0.5598 | -21.71% |
| QQQ | Development 2020-2022 | Rolling | 7.22% | 0.5191 | -21.65% |
| QQQ | Retrospective 2023-2025 | GARCH | 22.55% | 1.4020 | -18.15% |
| QQQ | Retrospective 2023-2025 | Rolling | 24.26% | 1.5174 | -16.64% |
| IWM | Exploratory OOS 2017-2019 | GARCH | 6.48% | 0.5176 | -23.06% |
| IWM | Exploratory OOS 2017-2019 | Rolling | 6.38% | 0.5292 | -20.95% |
| IWM | Development 2020-2022 | GARCH | -0.36% | 0.0549 | -22.48% |
| IWM | Development 2020-2022 | Rolling | -0.35% | 0.0594 | -22.53% |
| IWM | Retrospective 2023-2025 | GARCH | 8.24% | 0.6026 | -20.99% |
| IWM | Retrospective 2023-2025 | Rolling | 6.71% | 0.4833 | -23.12% |

Three deepest nonoverlapping market drawdowns per ETF are selected **ex post for
description only**. Decline excludes the peak date and includes the trough; recovery
excludes the trough and includes the first recovered peak, or sample end if censored.
Saved event rows record market returns, strategy returns, exposures, and the first
half-peak de-risking / 90%-of-peak re-risking exposure date. These response measures
are descriptive thresholds, not trading rules.

| Ticker | Episode | Phase | Strategy | Total Return | Average Exposure | Unrecovered |
| --- | --- | --- | --- | --- | --- | --- |
| SPY | 1 | Decline | Buy-and-Hold | -33.72% | 100.00% | False |
| SPY | 1 | Decline | Rolling | -16.85% | 51.68% | False |
| SPY | 1 | Decline | GARCH | -14.19% | 42.47% | False |
| SPY | 1 | Recovery | Buy-and-Hold | 51.18% | 100.00% | False |
| SPY | 1 | Recovery | Rolling | 17.87% | 53.78% | False |
| SPY | 1 | Recovery | GARCH | 20.01% | 62.52% | False |
| SPY | 2 | Decline | Buy-and-Hold | -24.50% | 100.00% | False |
| SPY | 2 | Decline | Rolling | -18.96% | 68.14% | False |
| SPY | 2 | Decline | GARCH | -19.13% | 70.36% | False |
| SPY | 2 | Recovery | Buy-and-Hold | 34.03% | 100.00% | False |
| SPY | 2 | Recovery | Rolling | 26.26% | 89.48% | False |
| SPY | 2 | Recovery | GARCH | 27.32% | 88.94% | False |
| SPY | 3 | Decline | Buy-and-Hold | -19.35% | 100.00% | False |
| SPY | 3 | Decline | Rolling | -15.37% | 79.71% | False |
| SPY | 3 | Decline | GARCH | -17.41% | 86.47% | False |
| SPY | 3 | Recovery | Buy-and-Hold | 24.37% | 100.00% | False |
| SPY | 3 | Recovery | Rolling | 17.58% | 84.93% | False |
| SPY | 3 | Recovery | GARCH | 19.01% | 89.98% | False |
| QQQ | 1 | Decline | Buy-and-Hold | -35.12% | 100.00% | False |
| QQQ | 1 | Decline | Rolling | -19.94% | 49.40% | False |
| QQQ | 1 | Decline | GARCH | -21.11% | 49.86% | False |
| QQQ | 1 | Recovery | Buy-and-Hold | 56.04% | 100.00% | False |
| QQQ | 1 | Recovery | Rolling | 39.72% | 78.03% | False |
| QQQ | 1 | Recovery | GARCH | 38.47% | 72.52% | False |
| QQQ | 2 | Decline | Buy-and-Hold | -28.56% | 100.00% | False |
| QQQ | 2 | Decline | Rolling | -14.58% | 53.26% | False |
| QQQ | 2 | Decline | GARCH | -13.42% | 46.94% | False |
| QQQ | 2 | Recovery | Buy-and-Hold | 40.10% | 100.00% | False |
| QQQ | 2 | Recovery | Rolling | 10.76% | 35.29% | False |
| QQQ | 2 | Recovery | GARCH | 12.96% | 42.76% | False |
| QQQ | 3 | Decline | Buy-and-Hold | -22.80% | 100.00% | False |
| QQQ | 3 | Decline | Rolling | -15.43% | 68.82% | False |
| QQQ | 3 | Decline | GARCH | -17.35% | 73.79% | False |
| QQQ | 3 | Recovery | Buy-and-Hold | 29.73% | 100.00% | False |
| QQQ | 3 | Recovery | Rolling | 18.35% | 77.08% | False |
| QQQ | 3 | Recovery | GARCH | 19.22% | 78.20% | False |
| IWM | 1 | Decline | Buy-and-Hold | -41.13% | 100.00% | False |
| IWM | 1 | Decline | Rolling | -23.14% | 84.06% | False |
| IWM | 1 | Decline | GARCH | -21.71% | 86.10% | False |
| IWM | 1 | Recovery | Buy-and-Hold | 71.60% | 100.00% | False |
| IWM | 1 | Recovery | Rolling | 19.08% | 50.71% | False |
| IWM | 1 | Recovery | GARCH | 19.35% | 50.84% | False |
| IWM | 2 | Decline | Buy-and-Hold | -31.91% | 100.00% | False |
| IWM | 2 | Decline | Rolling | -22.52% | 58.57% | False |
| IWM | 2 | Decline | GARCH | -22.48% | 58.76% | False |
| IWM | 2 | Recovery | Buy-and-Hold | 49.63% | 100.00% | False |
| IWM | 2 | Recovery | Rolling | 31.29% | 73.62% | False |
| IWM | 2 | Recovery | GARCH | 32.01% | 68.60% | False |
| IWM | 3 | Decline | Buy-and-Hold | -27.50% | 100.00% | False |
| IWM | 3 | Decline | Rolling | -23.12% | 78.55% | False |
| IWM | 3 | Decline | GARCH | -20.99% | 73.65% | False |
| IWM | 3 | Recovery | Buy-and-Hold | 38.12% | 100.00% | False |
| IWM | 3 | Recovery | Rolling | 20.85% | 69.63% | False |
| IWM | 3 | Recovery | GARCH | 23.09% | 68.09% | False |

## 10. Robustness checks

Preserved Phase 1: 405 target/cost/cap/window/refit scenarios. New checks: trading
horizon A/B, HAC lag selection, bootstrap blocks 5/20/60, costs 0/5/10 bps, fixed
5-pp band, earlier-period frozen exposure, zero/lagged cash, separate borrowing
with cap 150%, six volatility specifications, and chronological/stress panels.
Alternative-model and horizon tests are exploratory families. Pointwise Sharpe
bootstrap intervals are not adjusted for all these explorations. Results cannot
support selecting the best cell as a deployable strategy.

## 11. Research limitations

Three correlated surviving equity ETFs and a single sample; vendor-adjusted prices
rather than point-in-time revisions; no intraday realized variance; stationarity,
finite-moment, bandwidth and block assumptions; near-integrated parameters; exact
close fills and proportional fees without capacity, taxes or market impact; no
historical broker financing contract; incomplete cash vintage reconstruction;
return-based Sharpe resampling does not integrate parameter-estimation uncertainty;
no untouched future test. Negative Sharpe values during stress can behave counter-
intuitively when volatility shrinks, so absolute returns and drawdowns also matter.
No backtest result identifies a causal effect of forecast quality on investment gains.

## 12. Conclusions and next steps


1. **Forecast significance:** SPY QLIKE, QQQ QLIKE pass the primary Holm threshold; other non-rejections do not establish equivalence.


- SPY: aligned net GARCH-minus-rolling Sharpe -0.0010, paired 95% interval [-0.1155, 0.1155]; CAGR difference +0.127 percentage points; annual arithmetic differential fee drag 0.177 percentage points.


- QQQ: aligned net GARCH-minus-rolling Sharpe -0.0209, paired 95% interval [-0.1203, 0.0821]; CAGR difference -0.276 percentage points; annual arithmetic differential fee drag 0.155 percentage points.


- IWM: aligned net GARCH-minus-rolling Sharpe +0.0402, paired 95% interval [-0.0658, 0.1439]; CAGR difference +0.544 percentage points; annual arithmetic differential fee drag 0.081 percentage points.


- SPY: later-period GARCH excess Sharpe 0.728, frozen-exposure benchmark 0.644; realized annual vol 14.02% vs 19.71%. This comparison controls an earlier exposure estimate, not exact realized test-period risk.


- QQQ: later-period GARCH excess Sharpe 0.836, frozen-exposure benchmark 0.740; realized annual vol 15.28% vs 22.53%. This comparison controls an earlier exposure estimate, not exact realized test-period risk.


- IWM: later-period GARCH excess Sharpe 0.194, frozen-exposure benchmark 0.324; realized annual vol 15.32% vs 24.71%. This comparison controls an earlier exposure estimate, not exact realized test-period risk.


- SPY: exploratory normal GJR minus normal GARCH QLIKE -0.0495; net Sharpe difference -0.0213 under the common delayed convention. EGARCH normal/t rejected-fit counts are 5/6; its results require the recorded fallback policy.


- QQQ: exploratory normal GJR minus normal GARCH QLIKE -0.0406; net Sharpe difference +0.0111 under the common delayed convention. EGARCH normal/t rejected-fit counts are 2/3; its results require the recorded fallback policy.


- IWM: exploratory normal GJR minus normal GARCH QLIKE -0.0206; net Sharpe difference +0.0225 under the common delayed convention. EGARCH normal/t rejected-fit counts are 6/8; its results require the recorded fallback policy.


2. **Economic value and exposure:** the paired intervals and frozen-exposure comparisons above must be read alongside the raw Sharpe rankings. Equal risk budgets do not equal realized risk. The arithmetic exposure/timing decomposition is descriptive, not proof that reduced exposure is the sole cause.

3. **Turnover:** differential fee drag measures the cost of more responsive allocation. Gross gains can be offset by trading; band outcomes are reported without presuming improvement.

4. **Cross-ETF consistency and rebounds:** forecast and investment rankings differ across assets and time blocks. Event tables quantify capital protection and missed recovery gains; ex-post event selection cannot establish causal timing skill.

5. **Practical risk management:** treat GARCH as a candidate risk-control input, not a demonstrated return-enhancement rule. Before deployment, freeze a specification for genuinely unseen future data, verify executable fills and cash/funding terms, and assess whether improvements exceed estimation and trading uncertainty. Do not choose a winner from this already-inspected grid.

All new artifact paths are listed in `PHASE2_OUTPUTS.md`; code changes, executed test results, and validation are recorded in `../PROJECT_PROGRESS.md` and `phase2_validation.json`.

Method references: [arch forecasting](https://arch.readthedocs.io/en/stable/univariate/forecasting.html), [Newey-West implementation conventions](https://www.statsmodels.org/dev/generated/statsmodels.stats.sandwich_covariance.cov_hac.html), [official EFFR](https://www.newyorkfed.org/markets/reference-rates/effr), [publication and revision policy](https://www.newyorkfed.org/markets/reference-rates/additional-information-about-reference-rates).
