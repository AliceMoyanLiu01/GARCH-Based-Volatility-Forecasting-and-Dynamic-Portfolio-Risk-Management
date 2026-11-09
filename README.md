# GARCH volatility forecasting and portfolio risk management

A reproducible undergraduate quantitative finance study of whether improved volatility
forecasts translate into better portfolio decisions after costs.

**Finding:** Gaussian GARCH improves selected forecast losses, but this history does
not establish a consistent net Sharpe advantage over rolling-volatility targeting.
The project reports uncertainty, negative results and numerical failures explicitly.

- [Final research report](FINAL_RESEARCH_REPORT.md)
- [One-page project summary](PROJECT_SUMMARY.md)
- [Final independent review](docs/FINAL_REVIEW_NOTES.md)
- [EGARCH instability appendix](docs/EGARCH_REVIEW.md)

## Study design

SPY, QQQ and IWM adjusted daily prices and volume, 2015–2025. Each ETF is a separate
sleeve. Shared historical OOS dates: 2017-07-07–2025-12-31, following estimation/warmup.

- GARCH(1,1), 504-session trailing fits, refitted every 21 sessions.
- Benchmark: 20-session historical volatility; 15% annual risk target, 100% cap,
  1% annual forecast-volatility floor; 5-bp fees per dollar of actual traded notional.
- Signal after close t; trade at close t+1; earn return ending t+2. The aligned
  strategy uses that holding day's conditional variance. Exact fractional closing
  fills are an execution approximation.
- Log returns for estimation; simple returns for P&L; self-financing accounting
  includes drift turnover, initial entry and exact fees.
- HAC/Newey–West tests, nine-test primary Holm family, seeded circular-block bootstrap,
  cost/turnover experiments, earlier-only exposure calibration and chronological panels.
- Cash is zero in the headline panel; lagged official EFFR and separately assumed
  borrowing costs are additional scenarios. See [data sources](docs/DATA_SOURCES.md).

| ETF | Primary one-step QLIKE adjusted p | Aligned GARCH − rolling Sharpe |
| --- | ---: | ---: |
| SPY | 0.0301 | −0.0010 |
| QQQ | 0.0353 | −0.0209 |
| IWM | 0.0739 | +0.0402 |

All paired 95% Sharpe-difference intervals include zero. Non-rejection does not imply
equivalence. All years, including 2023–2025, were previously inspected; later-period
results are retrospective, not untouched holdout evidence.

## Reproduce in a fresh environment

The reference environment is **Python 3.13**. Run commands from this repository root.
Installation needs internet; analysis uses the supplied real-data snapshot offline.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
python -m pytest -q
python phase2.py
python validate_phase2.py
python final_review.py
python make_portfolio_reports.py
```

Detailed ledgers and current processed datasets are generated locally and excluded
from publication. **Run `phase2.py` before validation or the final diagnostics** in a
fresh clone. `requirements.txt` provides version ranges for exploration; exact
numerical reproduction was checked with `requirements-lock.txt` and the saved raw
prices. Small input-rounding changes can alter unstable EGARCH optimization.

The report builder uses retained clean-review evidence in `outputs/review/`; running
pytest prints your own new test result. That builder does not silently certify a new
environment. To preserve a new certification, save its test console output and audit
records explicitly before rebuilding the reports.

To check a separate full rerun:

```bash
python phase2.py --output-dir .local/reproduction
python validate_phase2.py --output-dir .local/reproduction
python validate_phase2.py --compare-to .local/reproduction
```

Only measured runtime columns are excluded from scientific CSV comparison. Repeated
full-run directories and detailed ledgers are local artifacts; do not commit them.

Optional downloads (not needed to reproduce the supplied snapshot):

```bash
python download_data.py
python download_cash.py
```

Vendor redownloads may revise history. Preserve the included hashes when comparing
this study. `--zero-cash-only --output-dir .local/zero_cash` explicitly omits the cash
scenario if reliable rate data is unavailable; it never invents observations.

## Results and code

| Location | Content |
| --- | --- |
| `garch_research/` | Existing data, models, strategies, accounting, inference, evaluation and reporting modules |
| `phase2.py` | Complete research extension; settings in `garch_research/phase2_config.py` |
| `project.py` | Original baseline workflow; use a separate output directory for legacy runs |
| `validate_phase2.py` | Independent accounting, timing, inference, calibration and provenance audit |
| `final_review.py` | Report-to-CSV checks, EGARCH loss attribution and diagnostic likelihood replays |
| `make_portfolio_reports.py` | Concise reports generated from saved reviewed results |
| `tests/` | 50 tests covering legacy behavior, causality, inference, funding and review regressions |
| `data/raw/`, `data/cash/` | Canonical real input snapshots and download provenance |
| `outputs/*.csv` | Forecast tests, strategy/cost attribution, risk comparisons and chronology |
| `outputs/phase2_models/` | All alternative-model origin forecasts and fit diagnostics |
| `outputs/figures/` | PNG and vector PDF figures |
| `outputs/review/` | Clean-environment evidence, claim audit, EGARCH diagnostics and loss contributions |
| `archive/phase1/` | Deliberately frozen original source, data and results required for baseline/provenance checks |
| `archive/final_review_reference/` | Original V2 report/metadata and files changed during final review |


## Numerical and research limits

EGARCH is an unresolved exploratory specification. Some converged fits produce
abnormal variances, and the broad unchanged numerical guard does not guarantee
reasonable forecasts. Fallback counts and loss contributions are preserved; no guard
was tuned to improve returns during the final review. Student-t EGARCH second-horizon
forecasts are not supplied because the required exponential moments can diverge.
The headline result uses Gaussian GARCH and rolling targeting.

Other limits: three correlated surviving equity ETFs, noisy squared-return variance
proxies, dependent historical data, approximate execution, no market impact or taxes,
revised vendor prices, incomplete cash vintages and assumed rather than observed
broker financing. Neither causal investment effects nor validated alpha are claimed.

## Publication

`.gitignore` excludes environments, caches, processed duplicates, detailed generated
ledgers, rerun directories, logs and export bundles. The frozen original archive is
retained intentionally because the pipeline checks its input/source hashes.

```bash
python prepare_publication.py
```

This writes `PUBLICATION_MANIFEST.json` and a curated
`dist/garch_volatility_research.zip`; it does not commit, push or upload anything.
Third-party data remains subject to provider terms; the download scripts are retained.
No software license has been selected by the project owner.
