# Data Provenance Record: STAR_PRODUCTIVE_LABOR_SHARE

> **CONSTRUCTED CLASSIFICATION — heterodox (Shaikh-Tonak). NOT an official BLS series.**

## Quick Reference

| Field | Value |
|-------|-------|
| Series ID | STAR_PRODUCTIVE_LABOR_SHARE |
| Name | Productive labor share of employment (Shaikh-Tonak classification) |
| Source | Shaikh-Tonak classification over BLS CES |
| Units | percent of total nonfarm payroll employment |
| Frequency | A (annual, complete-year-only) |
| Period | 1964-01-01 to 2025-01-01 |
| Observations | 62 |
| Construction | formula |
| Category | heterodox |
| Status | active |

## Formula / Construction

`100 * (USMINE + USCONS + MANEMP + (USTPU - USTRADE - USWTRADE)) / PAYEMS, annual mean of monthly CES employment`

CONSTRUCTED CLASSIFICATION - heterodox (Shaikh-Tonak), NOT an official BLS series. Productive = mining, construction, manufacturing, and the transport/warehousing/utilities part of CES Trade-Transportation-Utilities. Judgment calls: Information and Professional & Business Services assigned unproductive; agriculture excluded (not in CES nonfarm). See PRODUCTIVE_UNPRODUCTIVE_DPR_EPR.md.

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
