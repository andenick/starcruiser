# Data Provenance Record: STAR_PROFIT_RATE_NFC

> **Constructed (formula) series — heterodox interpretive layer (labeled).**

## Quick Reference

| Field | Value |
|-------|-------|
| Series ID | STAR_PROFIT_RATE_NFC |
| Name | Sector-matched NFC profit rate (NOT constructed) |
| Source | BEA |
| Units | percent |
| Frequency | A (annual, complete-year-only) |
| Period | None to None |
| Observations | 0 |
| Construction | formula |
| Category | heterodox |
| Status | data_unavailable |

## Formula / Construction

`NFC profits (line 27) / NFC net fixed assets — data_unavailable: no sector-matched NFC net capital stock on disk (FAAt tables are by-industry NAICS, not by sector/legal form)`



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
