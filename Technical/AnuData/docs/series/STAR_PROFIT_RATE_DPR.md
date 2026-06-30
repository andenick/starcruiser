# Data Provenance Record: STAR_PROFIT_RATE

> **Constructed (formula) series — heterodox interpretive layer (labeled).**

## Quick Reference

| Field | Value |
|-------|-------|
| Series ID | STAR_PROFIT_RATE |
| Name | Economy-wide profit rate (corporate profits / private net capital stock) |
| Source | BEA NIPA T1.14 + BEA Fixed Assets 3.1ESI |
| Units | percent |
| Frequency | A (annual, complete-year-only) |
| Period | 1947-01-01 to 2024-01-01 |
| Observations | 78 |
| Construction | formula |
| Category | heterodox |
| Status | active |

## Formula / Construction

`100 * T1.14 line 11 (total corporate profits w/ IVA+CCAdj) / FAAt301ESI line 1 (current-cost net stock of private fixed assets)`



## Provenance

Built in the StarCruiser Phase 2 publish build from on-disk BEA NIPA Table 1.14
(value added by sector) and BEA Fixed Assets 3.1ESI, plus a live FRED pull for
PRS85006173, and (for the productive/unproductive split) the Shaikh-Tonak
reconstruction over BLS CES major-industry employment. See full build notes:
`data/int-data/heterodox/BUILD_NOTES.md` and
`data/int-data/heterodox/PRODUCTIVE_UNPRODUCTIVE_DPR_EPR.md`.
Chopped output: `data/final-data/chopped/heterodox_chopped.csv`.

## Authenticity

No synthetic data, no unlabeled proxies. Complete years only. Where a value could
not be honestly obtained the series is marked `status: data_unavailable` with no
fabricated values.
