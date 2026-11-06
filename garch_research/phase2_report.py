"""V2 report generated solely from saved, executed research tables."""
from pathlib import Path
import json
import pandas as pd
from .report import table


def write_report_v2(out):
    out=Path(out)
    read=lambda name:pd.read_csv(out/name)
    stats=read('statistical_tests.csv'); primary=stats[stats.primary_lag]
    strategy=read('strategy_summary_v2.csv'); attr=read('performance_attribution.csv')
    risk=read('risk_matched_comparison.csv'); models=read('extended_model_comparison.csv')
    chrono=read('chronological_validation.csv'); events=read('drawdown_episode_analysis.csv')
    uncertainty=read('economic_bootstrap.csv'); calibration=read('exposure_calibration.csv')
    aligned=strategy[(strategy.Convention=='B_aligned_h2')&(strategy.Rule=='daily')&(strategy['Cost bps']==5)]
    baseattr=attr[(attr.Convention=='B_aligned_h2')&(attr.Rule=='daily')&(attr['Cost bps']==5)]
    sig=primary[(primary.p_holm<.05)&(primary.mean_difference<0)]
    pct=lambda x:f'{x:.2%}'
    fmt={name:pct for name in ['CAGR','Gross CAGR','Annualized Volatility','Maximum Drawdown','Average Exposure',
        'Frozen exposure','Trading frequency','Total Return','Annual differential fee drag','Annual gross difference',
        'Average exposure component','Timing covariance component','Annual net difference','Mean abs weight difference']}
    sci={name:lambda x:f'{x:.6g}' for name in ['mean_difference','ci_low','ci_high','bootstrap_low','bootstrap_high']}
    qualified=', '.join(sig.Ticker+' '+sig.Loss) if len(sig) else 'none'
    sections=[f'''# GARCH Forecasting and Economic Value — Research Report V2

## 1. Executive summary

The preserved Phase 1 baseline was reproduced before changing its implementation.
The primary nine-test family supports lower GARCH forecast loss after Holm adjustment
at 5% for: **{qualified}**. Negative estimates alone are not evidence of significance.
The aligned-horizon, 5-bp, unlevered trading comparison is:

{table(aligned[['Ticker','Strategy','CAGR','Gross CAGR','Sharpe (rf=0)','Maximum Drawdown','Average Exposure','Annualized Turnover']],fmt)}

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

{table(primary[['Ticker','Loss','n','mean_difference']],sci)}

## 5. Statistical inference

HAC uses an intercept-only Bartlett/Newey-West long-run variance estimator with
n-denominator autocovariances and no degrees-of-freedom correction. Primary bandwidth
is floor(4*(n/100)^(2/9)); asymptotic normal two-sided p-values and 95% intervals.
Lags 0,5,10,21,63 are sensitivity checks; lag 0 intentionally omits serial dependence.
No finite-sample DM correction is claimed. These are DM-style equal predictive-loss
tests with overlapping rolling parameter estimates and a single historical path.
Holm familywise correction is applied to the nine primary p-values only; sensitivity
lags are not alternative routes to a preferred rejection.

{table(primary[['Ticker','Loss','hac_lag','statistic','p_value','p_holm','ci_low','ci_high']],sci)}

Circular moving-block bootstrap: uniform block starts, wrap at the sample boundary,
concatenate/truncate to n, block length 20 sessions, 2,000 replications, seed 20261031
with fixed ticker/loss offsets. Percentile 2.5%/97.5% intervals; blocks 5 and 60 are
saved sensitivity checks. These bootstrap intervals and HAC intervals are pointwise,
not multiplicity-adjusted simultaneous intervals.

{table(primary[['Ticker','Loss','bootstrap_low','bootstrap_high']],sci)}
''']
    disagreements=[]
    for _,r in primary.iterrows():
        hac=r.ci_high<0 or r.ci_low>0
        boot=r.bootstrap_high<0 or r.bootstrap_low>0
        if hac!=boot: disagreements.append(f'{r.Ticker} {r.Loss}')
    sections.append('Pointwise HAC/bootstrap zero-exclusion disagreements: '+(', '.join(disagreements) if disagreements else 'none')+
        '. HAC uses a symmetric normal approximation; percentile blocks capture a skewed finite-sample distribution and a different dependence bandwidth. '
        'Rare crisis observations can dominate squared-error losses; intervals near zero are sensitive to resampling. '
        'Neither method is selected because it favors GARCH. Dependence stationarity/mixing, finite relevant moments, '
        'and reasonable bandwidth/block choices are assumptions, potentially strained by structural breaks. '
        'An insignificant result is not proof of equivalence.\n')
    sections.append(f'''## 6. Strategy performance and economic attribution

Matched-date weight and forecast correlations, exposure in market drawdowns below
−10%, trading frequency, costs, and both gross/net results are in
`performance_attribution.csv` and `strategy_summary_v2.csv`.

{table(baseattr[['Ticker','Forecast correlation','Weight correlation','Mean abs weight difference',
                'Annual gross difference','Annual differential fee drag','Annual net difference']],fmt)}

For each day, net return = gross return − fee_fraction*(1+gross_return). Thus
annualized arithmetic GARCH-minus-rolling net difference equals gross difference
minus differential fee drag exactly. The gross difference is further decomposed
as mean(delta_weight)*mean(market_return) plus the population covariance term.
This is descriptive exposure/timing accounting, not a causal estimate.

{table(baseattr[['Ticker','Average exposure component','Timing covariance component','Annual gross difference']],fmt)}

CAGR differences are separately reported and are **not** an additive decomposition.
The 0/5/10-bp runs share all other settings. Gross CAGR is the compounded gross
return of each ledger's actual weights; no performance ranking was used to choose
fees. The paired circular-block Sharpe intervals resample the same dates for both
strategies, preserving cross-strategy dependence and treating fitted realized
strategy returns as given (not re-estimating all models in every resample):

{table(uncertainty)}

Turnover-control comparison at aligned horizon and 5 bps:

{table(strategy[(strategy.Convention=='B_aligned_h2')&(strategy['Cost bps']==5)][
    ['Ticker','Strategy','Rule','CAGR','Sharpe (rf=0)','Annualized Turnover','Trading frequency']],fmt)}

## 7. Risk-matched comparisons and cash

Exposure is calibrated using only executable GARCH h=2 allocations before 2020,
then frozen as a constant-mix benchmark for 2020–2025. It rebalances to that fixed
fraction and pays actual fees. Calibration is independent of subsequent returns;
the realized later average GARCH exposure need not equal the frozen value.

{table(calibration,fmt)}

GARCH/rolling receive the same 15% ex-ante risk budget, caps, fees, cash assumptions,
and evaluation dates. Buy-and-hold and frozen exposure are comparison benchmarks,
not strategies claimed to have that risk budget. Realized risk is reported explicitly.

{table(risk[risk.Cap==1][['Ticker','Cash scenario','Strategy','CAGR','Annualized Volatility',
    'Excess Sharpe','Maximum Drawdown','Average Exposure']],fmt)}

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

{table(models[['Ticker','Model','MSE','MAE','QLIKE','CAGR','Sharpe (rf=0)','Failed fits','Fallback share','Compute seconds']],
    {**fmt,'MSE':lambda x:f'{x:.5e}','MAE':lambda x:f'{x:.5e}','Fallback share':pct})}

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

{table(chrono[(chrono.Convention=='B_aligned_h2')&(~chrono.Period.isin(['COVID stress','2022 tightening']))][
    ['Ticker','Period','Model','CAGR','Sharpe (rf=0)','Maximum Drawdown']],fmt)}

Three deepest nonoverlapping market drawdowns per ETF are selected **ex post for
description only**. Decline excludes the peak date and includes the trough; recovery
excludes the trough and includes the first recovered peak, or sample end if censored.
Saved event rows record market returns, strategy returns, exposures, and the first
half-peak de-risking / 90%-of-peak re-risking exposure date. These response measures
are descriptive thresholds, not trading rules.

{table(events[['Ticker','Episode','Phase','Strategy','Total Return','Average Exposure','Unrecovered']],fmt)}

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
''')
    sections.append(f'1. **Forecast significance:** {qualified} pass the primary Holm threshold; '
        'other non-rejections do not establish equivalence.\n')
    for t in ('SPY','QQQ','IWM'):
        g=aligned[(aligned.Ticker==t)&(aligned.Strategy=='GARCH')].iloc[0]
        r=aligned[(aligned.Ticker==t)&(aligned.Strategy=='Rolling')].iloc[0]
        a=baseattr[baseattr.Ticker==t].iloc[0]
        u=uncertainty[(uncertainty.Ticker==t)&(uncertainty.Convention=='B_aligned_h2')].iloc[0]
        sections.append(f"- {t}: aligned net GARCH-minus-rolling Sharpe {g['Sharpe (rf=0)']-r['Sharpe (rf=0)']:+.4f}, "
            f"paired 95% interval [{u['Sharpe CI low']:.4f}, {u['Sharpe CI high']:.4f}]; "
            f"CAGR difference {(g.CAGR-r.CAGR)*100:+.3f} percentage points; annual arithmetic differential fee drag "
            f"{a['Annual differential fee drag']*100:.3f} percentage points.\n")
    for t in ('SPY','QQQ','IWM'):
        subset=risk[(risk.Ticker==t)&(risk.Cap==1)&(risk['Cash scenario']=='Lagged EFFR')]
        if subset.empty: subset=risk[(risk.Ticker==t)&(risk.Cap==1)&(risk['Cash scenario']=='Zero cash')]
        s=subset.set_index('Strategy')
        sections.append(f"- {t}: later-period GARCH excess Sharpe {s.loc['GARCH','Excess Sharpe']:.3f}, "
            f"frozen-exposure benchmark {s.loc['Frozen exposure','Excess Sharpe']:.3f}; realized annual vol "
            f"{s.loc['GARCH','Annualized Volatility']:.2%} vs {s.loc['Frozen exposure','Annualized Volatility']:.2%}. "
            'This comparison controls an earlier exposure estimate, not exact realized test-period risk.\n')
    for t in ('SPY','QQQ','IWM'):
        m=models[models.Ticker==t].set_index('Model')
        qdiff=m.loc['GJR_normal','QLIKE']-m.loc['GARCH_normal','QLIKE']
        sdiff=m.loc['GJR_normal','Sharpe (rf=0)']-m.loc['GARCH_normal','Sharpe (rf=0)']
        sections.append(f"- {t}: exploratory normal GJR minus normal GARCH QLIKE {qdiff:+.4f}; "
            f"net Sharpe difference {sdiff:+.4f} under the common delayed convention. "
            f"EGARCH normal/t rejected-fit counts are {int(m.loc['EGARCH_normal','Failed fits'])}/"
            f"{int(m.loc['EGARCH_t','Failed fits'])}; its results require the recorded fallback policy.\n")
    sections.append('2. **Economic value and exposure:** the paired intervals and frozen-exposure comparisons above '
        'must be read alongside the raw Sharpe rankings. Equal risk budgets do not equal realized risk. '
        'The arithmetic exposure/timing decomposition is descriptive, not proof that reduced exposure is the sole cause.\n\n'
        '3. **Turnover:** differential fee drag measures the cost of more responsive allocation. Gross gains can '
        'be offset by trading; band outcomes are reported without presuming improvement.\n\n'
        '4. **Cross-ETF consistency and rebounds:** forecast and investment rankings differ across assets and '
        'time blocks. Event tables quantify capital protection and missed recovery gains; ex-post event selection '
        'cannot establish causal timing skill.\n\n'
        '5. **Practical risk management:** treat GARCH as a candidate risk-control input, not a demonstrated '
        'return-enhancement rule. Before deployment, freeze a specification for genuinely unseen future data, '
        'verify executable fills and cash/funding terms, and assess whether improvements exceed estimation '
        'and trading uncertainty. Do not choose a winner from this already-inspected grid.\n\n'
        'All new artifact paths are listed in `PHASE2_OUTPUTS.md`; code changes, executed test results, '
        'and validation are recorded in `../PROJECT_PROGRESS.md` and `phase2_validation.json`.\n\n'
        'Method references: [arch forecasting](https://arch.readthedocs.io/en/stable/univariate/forecasting.html), '
        '[Newey-West implementation conventions](https://www.statsmodels.org/dev/generated/statsmodels.stats.sandwich_covariance.cov_hac.html), '
        '[official EFFR](https://www.newyorkfed.org/markets/reference-rates/effr), '
        '[publication and revision policy](https://www.newyorkfed.org/markets/reference-rates/additional-information-about-reference-rates).\n')
    (out/'RESEARCH_REPORT_V2.md').write_text('\n\n'.join(sections))
    # Keep the full initial report; append an idempotent pointer to the upgraded work.
    original=Path('archive/phase1/outputs/RESEARCH_REPORT.md')
    if original.exists():
        (out/'RESEARCH_REPORT.md').write_text(original.read_text()+
            '\n\n## Phase 2 research upgrade\n\nThe initial report above is preserved as historical context. '
            'Its lack-of-inference and zero-cash limitations are addressed in the new '
            '[V2 report](RESEARCH_REPORT_V2.md), with qualified conclusions, explicit horizon alignment, '
            'statistical uncertainty, cash/financing sensitivities, and exposure controls. '
            'The original results were reproduced before modifications.\n')
