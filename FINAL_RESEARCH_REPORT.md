# GARCH-Based Volatility Forecasting and Dynamic Portfolio Risk Management

## Research question

Does more accurate volatility forecasting create useful portfolio risk control and
better net investment performance? I study SPY, QQQ and IWM to distinguish prediction
accuracy from economic value. The main result is conditional: GARCH improves selected
forecast-loss measures, but this study does not establish a consistent incremental
net Sharpe advantage over simple rolling volatility.

## Data and design

The dataset contains daily adjusted close and volume from Yahoo Finance for 2015–2025,
with 2,766 price observations per ETF. Historical out-of-sample comparisons cover
2017-07-07–2025-12-31, or 2,134 returns, following estimation and shared warmup.
Log returns estimate variance; simple adjusted-price returns calculate portfolio P&L.
Adjusted prices approximate reinvested distributions, rather than modeling dividend
cash flows separately.

The core model is zero-mean Gaussian GARCH(1,1), estimated on 504 trailing returns and
refitted every 21 sessions. The benchmark is 20-session historical volatility.
Both size exposure toward 15% annual volatility with a 100% cap and a 1% forecast
volatility floor. Proportional transaction costs are 5 bps of actual traded notional;
0/10-bp costs and a fixed allocation band are sensitivity experiments. Each ETF is
an individual sleeve, not a jointly optimized portfolio.

Signals observed after close t execute at close t+1 and earn the return ending at
t+2. The headline strategy uses the second holding-day variance forecast,
`h[t+2|t] = omega + (alpha+beta) h[t+1|t]`. The original stale one-step convention is
retained as a comparison. Fractional post-fee targets and exact closing fills are
idealizations; the earlier signal does not guarantee a feasible real-world closing
quantity or fill. Cash is zero in the headline panel. A separate, identically dated
2020–2025 comparison uses a lagged official overnight-rate proxy and exposure fixed
from pre-2020 calibration.

## Forecast accuracy and economic results

The p-values below test **one-step** QLIKE differences; the trading columns evaluate
the **holding-horizon-aligned** strategies. CAGR is net of trading fees; Sharpe uses
risk-free=0. Sharpe differences are GARCH minus rolling.

| ETF | QLIKE adjusted p | GARCH CAGR | Rolling CAGR | Sharpe difference | 95% interval |
| --- | --- | --- | --- | --- | --- |
| SPY | 0.0301 | 12.45% | 12.32% | -0.0010 | [-0.1155, 0.1155] |
| QQQ | 0.0353 | 15.44% | 15.72% | -0.0209 | [-0.1203, 0.0821] |
| IWM | 0.0739 | 4.61% | 4.06% | +0.0402 | [-0.0658, 0.1439] |

Nine primary comparisons span three ETFs and three losses. Two-sided Newey–West/HAC
tests, with Holm familywise adjustment, support lower GARCH QLIKE for SPY and QQQ
at 5%. IWM QLIKE and all MSE/MAE comparisons do not pass that adjustment. This does
not establish equal predictive ability. Daily squared log returns are noisy variance
proxies; MAE is particularly difficult to interpret as latent-variance accuracy.

Paired circular-block bootstrap intervals use 20-session blocks, 2,000 replications
and a fixed seed. Every aligned Sharpe-difference interval includes zero. They are
pointwise intervals conditional on the fitted strategies, not simultaneous confidence
bounds or a full re-estimation bootstrap. Some forecast-loss HAC and percentile
bootstrap intervals disagree; both results and lag/block sensitivities are retained.

## Why better predictions did not consistently improve trading

| ETF | Forecast correlation | Mean absolute weight gap | Extra annual fee drag (pp) |
| --- | --- | --- | --- |
| SPY | 0.882 | 4.97% | 0.177 |
| QQQ | 0.894 | 6.81% | 0.155 |
| IWM | 0.900 | 7.74% | 0.081 |

Forecasts are strongly correlated, and the cap often maps differing predictions into
similar positions. Avoiding volatility errors is also different from timing the sign
of equity returns. More responsive forecasts can cut risk after losses and remain
underinvested during a rebound. Historical drawdown/recovery analyses show this
tradeoff descriptively; they do not identify a causal timing effect.

GARCH incurs higher turnover and differential fee drag. The attribution uses the exact
daily identity `net return = gross return − fee_fraction × (1+gross return)`.
Annualized arithmetic differences can therefore be decomposed into gross differences
and fees. Compounded CAGR differences cannot be added in that way. A common ex-ante
risk target also does not guarantee equal realized risk. The pre-2020 frozen-exposure
benchmarks help contextualize risk reduction, but do not match the realized exposure
or risk of the later sample exactly.

Chronological results vary across ETFs and market periods. Reduced drawdowns and
reduced equity participation can coexist; neither lower drawdown nor a higher sample
Sharpe alone proves that a forecast adds investment value.

## EGARCH: a documented unresolved issue

Asymmetric models are exploratory. The EGARCH implementation is not reliable enough
to support the headline conclusion. Some optimizer-success fits have extreme shock
coefficients. The package bounds its in-sample variance recursion, while its next-day
forecast and the project's subsequent recursion can produce extreme values. A
persistence check on beta alone cannot detect this problem.

The unchanged broad numerical guard still permits SPY Gaussian EGARCH daily variance
as high as 2.651531 (daily volatility 162.8%).
Its MSE is 0.0537827; the largest 20 errors account for 97.25% of squared
loss. IWM Gaussian EGARCH MSE is 4.55244e-05, with 98.99% in its top 20 errors.
These failures are driven by accepted model forecasts, rather than fallback forecasts.
Fallback dates comprise 1.97%–6.28% of the scored samples,
and their loss contributions are explicitly saved. Model-plus-fallback scores must
not be described as pure successful-model performance.

Diagnostic likelihood replays show sensitivity to starting values and to roughly
1e-14 changes in percent returns from a CSV round trip. These are numerical
robustness failures despite exact reproduction with the pinned raw-input workflow.
The diagnostic refits do not replace any published forecasts. Guard thresholds,
models and trading rules were not tuned during this review. See the
[EGARCH appendix](docs/EGARCH_REVIEW.md) for counts, dates, parameters and source-level evidence.

## Limitations and conclusion

All years, including 2023–2025, were inspected previously. Later chronological panels
are retrospective historical OOS evaluations, **not untouched holdout tests**.
Other limitations include three correlated surviving US equity ETFs, noisy variance
proxies, vendor revisions, near-integrated parameters, simplified closing execution,
no market impact or taxes, and dependent observations. HAC/bootstrap assumptions may
be strained by structural breaks. The lagged overnight-rate file is not a complete
vintage archive; borrowing uses an assumed 100-bp spread rather than observed broker
funding. Student-t EGARCH's second horizon is not supplied because the exponential
moment may diverge.

The evidence supports volatility forecasting as a risk-management research input,
while economic gains over rolling targeting remain uncertain and asset-dependent.
A useful next study would freeze a specification before collecting genuinely new
returns, use better realized-variance data, and model executable fills and funding.
EGARCH needs likelihood-based numerical validation before further performance claims.
No causal effect or guaranteed return enhancement is claimed.

## Verification and supporting material

A fresh Python 3.13 virtual environment, without system packages, installed the exact
pinned dependencies. **50 tests passed**. Independent accounting/inference checks
reconciled **147 ledgers and 283,650 strategy-days**;
**204 scientific CSV artifacts reproduced**, excluding only runtime columns.
The V2 report passed **1,317 claim checks across 13 tables** and its numerical
conclusions; method assumptions were separately reviewed. These checks establish
internal consistency, not truth of the modeling assumptions.

- [Full methods and results](RESEARCH_REPORT_V2.md)
- [One-page summary](PROJECT_SUMMARY.md)
- [Review evidence and unresolved issues](docs/FINAL_REVIEW_NOTES.md)
- [Reproduction instructions](README.md)
