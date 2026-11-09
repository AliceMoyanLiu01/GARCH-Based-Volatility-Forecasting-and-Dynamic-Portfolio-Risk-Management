# Project summary: GARCH forecasting and portfolio risk

**Motivation.** Can a more accurate volatility forecast improve portfolio risk
management after trading costs? This project separates statistical forecast quality
from realized economic value, rather than assuming a more complex model must help.

**Data and methods.** SPY, QQQ and IWM daily adjusted prices and volume, 2015–2025;
shared historical OOS period 2017-07-07–2025-12-31 (2,134 returns). Compare trailing
GARCH(1,1) with 20-session historical volatility, using a 15% annual risk target,
100% exposure cap, 5-bp actual-notional fees and self-financing accounting. Signals
trade one close later; the aligned strategy forecasts the actual holding day's
variance. HAC tests, Holm adjustment and seeded block bootstrap quantify uncertainty.
Costs, cash/financing, earlier-period frozen exposure and chronological panels test
sensitivity; existing asymmetric models remain exploratory.

**Main findings.** Primary one-step QLIKE Holm-adjusted p-values are SPY
0.0301, QQQ 0.0353, IWM 0.0739. Only SPY and QQQ pass 5%; no primary
MSE/MAE comparison passes. Aligned net GARCH-minus-rolling Sharpe differences are
-0.0010, -0.0209 and +0.0402, respectively. All paired 95% intervals include
zero. Results do not establish consistent incremental net Sharpe gains or model equivalence.

**Why prediction gains did not consistently become trading gains.** Forecasts are
highly correlated; caps make allocations similar. Predicting variance does not
predict the direction of returns. De-risking can miss rebounds. Greater turnover
adds fees, while average exposure and realized risk differ across strategies.
Cost attribution is exact for arithmetic daily returns; CAGR is not additively decomposed.

**Numerical finding.** EGARCH has unresolved optimizer and recursion instability.
The broad unchanged guard still admits abnormal forecasts: SPY Gaussian EGARCH's
worst 20 observations produce 97.25% of squared loss. Fallback usage and its loss
contributions are disclosed; EGARCH is excluded from the central investment conclusion.

**Limitations and future work.** Previously inspected 2023–2025 data is retrospective,
not untouched. Three correlated ETFs, noisy squared-return proxies, idealized closing
fills, vendor revisions and assumed funding limit generalization. Freeze a specification
for genuinely new data, improve realized-variance measurement and execution modeling,
and validate EGARCH using likelihood-based numerical checks before investment analysis.

**Research engineering.** 50 clean-environment tests passed; 283,650 strategy-days independently
reconciled; 204 scientific CSV outputs reproduced. No guard or parameter was tuned to
improve investment performance during the final review.

[Final report](FINAL_RESEARCH_REPORT.md) · [Technical report](RESEARCH_REPORT_V2.md) · [Reproduce](README.md)
