# EGARCH numerical review

## Scope and unchanged policy

This is a diagnostic review of the existing normal/t asymmetric EGARCH. It adds no
model family, changes no parameters or guard thresholds, and does not replace
forecasts with diagnostic refits. Daily decimal variance is converted from percent
return squared by division by 10,000. Large errors are not unit conversion mistakes.

## Failure rates and loss concentration

| Ticker | Distribution | Failed fits | Converged rejected fits | Fallback forecasts | Fallback share | MSE | Top 20 MSE share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY | normal | 5 | 4 | 63 | 2.95% | 5.378269e-02 | 97.25% |
| SPY | t | 6 | 2 | 134 | 6.28% | 2.492200e-07 | 85.35% |
| QQQ | normal | 2 | 1 | 42 | 1.97% | 3.629241e-07 | 76.32% |
| QQQ | t | 3 | 2 | 63 | 2.95% | 3.639853e-07 | 76.04% |
| IWM | normal | 6 | 4 | 63 | 2.95% | 4.552439e-05 | 98.99% |
| IWM | t | 8 | 5 | 126 | 5.90% | 4.584465e-07 | 81.46% |

Counts of failed fits span all estimation origins; fallback shares use the 2,134
scored return dates. They are different denominators. Execution uses a two-row lag,
so fallback-execution day counts can differ from one-step scored fallback counts.

`outputs/review/egarch_fallback_loss_attribution.csv` partitions each loss into
accepted-model and fallback contributions to the **same full-period mean**. Their
sum recovers the reported mean. Conditional-subset scores are diagnostic only:
subset selection depends on failures, so they are not a fair replacement ranking.
The 504-session historical-only reference uses only earlier data; it is a diagnostic
comparison, not a newly selected investment strategy. Fallback rows equal that
historical variance exactly within CSV precision.

SPY Gaussian EGARCH: 63 fallback forecasts (2.95%);
fallback contributes 5.893923e-09 of total squared loss, while the
largest 20 squared errors contribute 97.25%. IWM Gaussian EGARCH's
fallback contribution is 2.419211e-05; its top 20 contribute 98.99%.
Accepted pathological forecasts, not fallback, drive those large MSEs. SPY-t also
has an accepted very small variance: the single-day QLIKE on 2018-01-22
is 11884.231, illustrating underprediction sensitivity.

## Root causes

1. EGARCH estimates shock coefficients alpha/gamma without finite coefficient
   bounds. A convergence code of zero and beta below one are inadequate checks.
   The accepted SPY 2017-11-01 fit has alpha about -12.22 and gamma about -37.66.
   Its conditional variance becomes economically implausible despite passing the
   intentionally broad [1e-6,1e6] × historical-variance guard.
2. Source inspection of installed arch 8.0.0 (`EGARCH.bounds`,
   `egarch_recursion_python`, `VolatilityProcess._one_step_forecast`) shows bounded
   in-sample variance filtering and a final forecast observation with bounds
   [0,infinity]. The project's between-refit EGARCH update implements the equation
   directly, followed by its own broad guard. Bounded in-sample likelihood behavior
   therefore does not establish safe extrapolation.
3. Likelihood optimization is ill-conditioned. The following replays use the exact
   trailing input reconstructed from raw prices and one fixed, conventional starting
   vector. The changed starts are used **only to diagnose likelihood sensitivity**.
   They are not selected using portfolio returns or used to replace study results.

| Ticker | Fit origin | Starting values | Convergence flag | Log likelihood | Forecast variance |
| --- | --- | --- | --- | --- | --- |
| SPY | 2017-11-01 | default | 0 | -2988.4258 | 2.344173e+00 |
| SPY | 2017-11-01 | fixed_diagnostic_start | 0 | -444.8576 | 1.033710e-05 |
| IWM | 2017-07-05 | default | 0 | -2099.1238 | 6.521737e-02 |
| IWM | 2017-07-05 | fixed_diagnostic_start | 0 | -725.2341 | 9.887676e-05 |
| QQQ | 2024-06-07 | default | 0 | -128596271.4142 | 2.427121e-225 |
| QQQ | 2024-06-07 | fixed_diagnostic_start | 0 | -825.0475 | 1.058683e-04 |
| SPY | 2020-03-06 | default | 0 | -590.5970 | 6.993453e-04 |
| SPY | 2020-03-06 | fixed_diagnostic_start | 0 | -590.5970 | 6.993419e-04 |

4. Reloading processed log returns from CSV changes percent returns by about 1e-14
   and can alter optimizer outcomes sharply. Full replay details preserve both raw
   recomputation and CSV round-trip cases. Exact pinned-workflow reproduction thus
   coexists with weak numerical robustness; a different runtime or input formatting
   could produce different EGARCH fits.

The same fixed diagnostic start also fails on some rounded inputs; it is not a
proven universal fix or evidence of a global likelihood optimum. A future study
should predefine likelihood-based multiple starts, inspect filtered-bound activity,
parameter covariance and convergence, and validate on new data before trading.
The guard remains unchanged to keep the present review independent of performance tuning.
Student-t EGARCH second-horizon forecasts remain unavailable because the needed
exponential moments can diverge.

## Disposition

EGARCH results are retained as exploratory failed/unstable specifications. They
are unsuitable for headline forecasting-superiority or investment claims until
numerical robustness is resolved. The main Gaussian GARCH/rolling conclusions
are unchanged. Source references: [arch EGARCH documentation](https://arch.readthedocs.io/en/latest/univariate/generated/generated/arch.univariate.EGARCH.forecast.html)
and the installed package source listed above.
