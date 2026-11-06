# Final research-quality review — 2026-11-01

## Independent execution

Created a fresh Python 3.13 venv under /tmp with `include-system-site-packages=false`,
installed `requirements-lock.txt`, and ran tests and the full pipeline against
unchanged saved real data. The original 47 tests passed independently. After adding
three review regressions, **50 tests passed**. Saved console evidence is
`outputs/review/clean_tests.txt`; versions and pip check are recorded alongside it.
Independent validation passed for 147 ledgers / 283,650 strategy-days.
All 204 existing scientific CSV artifacts matched a clean run; only compute
and fit wall-clock times were excluded. Input/archive hashes passed.

## Report claims

Verified all 13 V2 tables and numerical conclusions with 1,317 checks;
`outputs/review/report_claim_audit.csv` records every comparison. No material numerical
discrepancy was found. Dates, sample counts, targets, fees, inference family, seed,
replications and block conventions were cross-checked against configuration and
source. Narrative causal/equivalence/holdout language was reviewed separately.
This check proves agreement with the CSVs, not the truth of statistical assumptions.

## Methodological findings

- Forecast information sets and two-row execution lag are causal; future-shock and
  prefix tests pass. h=2 predicts the actual next holding day's variance rather
  than summing two days. The original h=1 delayed comparison is deliberately stale.
- Exact post-fee fractional targets at the closing price are idealized execution.
  Real share sizing and closing fills may not achieve them; this limitation was
  made explicit in V2 and the final report.
- Equal ex-ante budgets do not equate realized risk. Frozen exposure uses only
  pre-2020 allocations; later periods remain previously inspected retrospective data.
- Holm adjustment controls the stated primary family, not all historical research
  choices. HAC and block bootstrap assume sufficient dependence regularity; pointwise
  economic intervals are not simultaneous. Non-rejection is not equivalence.
- EGARCH instability remains unresolved; see the separate appendix and loss-source
  decomposition. No guard/model/trading parameter was changed during review.
- Found and fixed a validation defect: an empty/missing ledger directory previously
  allowed the accounting loop to do no work. Validation now requires the complete
  expected ledger set. The historical audits had actual complete ledgers, so this
  fix does not invalidate their reconciliations.

## Publication cleanup

Canonical source/data, frozen baseline, summary results, model forecasts/diagnostics,
figures and review evidence remain publishable. Environment/cache directories,
duplicated reproduction runs, generated detailed ledgers, machine-specific inventories,
logs and export files are excluded. `prepare_publication.py` produces a manifest and
zip containing the curated repository; it neither commits nor uploads anything.
Detailed ledgers and processed current datasets regenerate from scripts.

## Readiness

Ready as an undergraduate quantitative research portfolio project with the disclosed
limitations. Suitable resume claims concern implementation, causal historical
backtesting, uncertainty assessment, reproducibility and diagnosis of instability.
Do not claim validated alpha, a proven net Sharpe improvement, untouched holdout
performance, or a production-ready EGARCH/execution system. No genuinely untouched
future test or observed historical brokerage funding contract is available.
