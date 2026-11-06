# Publication bundle check — 2026-11-01

The curated bundle was extracted to a fresh directory outside the workspace, using
the independent dependency-isolated Python environment. It initially contains no
current processed data or detailed Phase 2 ledgers.

Executed from the extracted repository:

1. `python -m pytest -q`: **50 passed in 11.13s**.
2. `python phase2.py`: full research run completed from canonical raw inputs.
3. `python validate_phase2.py`: **passed**, 147 ledgers / 283,650 strategy-days.
4. `python final_review.py`: **passed**, 1,317 report checks across 13 tables;
   EGARCH diagnostics/likelihood replays completed.
5. Scientific CSV comparison against the workspace: **204 matched**, excluding
   only the measured runtime columns.

The first packaging check caught an omitted historical execution log referenced
by the immutable baseline manifest. The exporter was corrected to include every
manifest-required frozen file, while continuing to exclude new temporary logs.
Validation passed after restoring that exact file. The final zip is checked for
all 102 baseline-manifest members and their hashes. Numerical model code, guards,
forecasts and strategy choices were unchanged by the packaging fix.

The final export includes source, tests, canonical raw/rate snapshots, frozen
baseline, summary/diagnostic evidence, figures and reports. It excludes environments,
caches, current processed duplicates, detailed regenerated ledgers and duplicated
reproduction runs. The 102-file baseline is intentional provenance, not a rerun.

The clean environment was on the same host. This does not establish cross-platform
numerical identity, particularly for the unstable EGARCH optimizer. No Git commit,
remote repository creation, upload or push was performed.
