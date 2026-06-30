# Data Provenance Record: STAR_LABOR_SHARE_CORP_BEA

> **Constructed (formula) series — heterodox interpretive layer (labeled).**

## Quick Reference

| Field | Value |
|-------|-------|
| Series ID | STAR_LABOR_SHARE_CORP_BEA |
| Name | Corporate-business labor share (BEA-native) |
| Source | BEA NIPA T1.14 |
| Units | percent |
| Frequency | A (annual, complete-year-only) |
| Period | 1929-01-01 to 2024-01-01 |
| Observations | 96 |
| Construction | formula |
| Category | heterodox |
| Status | active |

## Formula / Construction

`100 * T1.14 line 4 (Compensation of employees, corporate) / line 1 (Gross value added, corporate)`



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
