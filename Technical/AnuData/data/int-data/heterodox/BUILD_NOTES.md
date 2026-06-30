# Heterodox Macro Series — Build Notes

**Build date:** 2026-06-30
**Output dir:** `Technical/AnuData/data/int-data/heterodox/`
**Files:** `heterodox_macro_annual.csv`, `BUILD_NOTES.md`, `registry_entries.json`
**Honesty policy:** public-source data only; no synthetic data, no unlabeled proxies, no fabrication.
Complete years only — the incomplete final year is dropped from every BEA-derived series.

## Sources (provider / access / vintage)

| Source | Provider | Access | Vintage / as-of | Units |
|---|---|---|---|---|
| NIPA Table 1.14, value added by sector | U.S. BEA | on-disk `data/raw-data/bea/bea_nipa_T11400_value_added_by_sector.csv` | ~2025.09 | millions USD (UNIT_MULT=6), annual 1929–2025 |
| Fixed Assets Table 3.1ESI (current-cost NET stock of private fixed assets by industry) | U.S. BEA | on-disk `data/raw-data/bea/bea_fixed_assets_FAAt301ESI.csv` | ~2025.09 | millions USD (UNIT_MULT=6), annual 1947–2024 |
| PRS85006173 (nonfarm business sector: labor share, index) | U.S. BLS via FRED | **live FRED pull** (St. Louis Fed API) on 2026-06-30 | through 2026Q1 | index (2017=100), quarterly → annual mean |

**DataValue parsing:** commas stripped; `''`, `...`, `(D)` treated as missing. Ratios cancel the
shared UNIT_MULT=6, so numerator and denominator are used in raw millions.

**Complete-year rule:** the BEA source file vintage is ~2025.09, so its 2025 annual figures are
preliminary/incomplete (built from partial-year data). All BEA-derived series are therefore capped
at **2024**. The BLS/FRED PRS series has all four quarters for 2025 (BLS productivity full-year 2025
published early 2026), so PRS extends to **2025**; 2026 is dropped (only Q1 present).

**Fixed-asset measure choice:** three candidate FAAt tables were on disk. Line-1 ("Private fixed
assets") values confirm the measure:
- `FAAt301ESI` (Current Dollars): 1947 = 516,636 → 2024 = 70,276,521 → **net STOCK** (the large,
  growing capital level we want). **CHOSEN.**
- `FAAt304ESI` (Current Dollars): 1947 = 17,736 → 2024 = 3,992,907 → small flow = current-cost
  **depreciation**, not a stock. Rejected.
- `FAAt307ESI` (Historical Cost): 1947 = 37,391 → 2024 = 5,142,683 → historical-cost depreciation
  flow. Rejected (also not current-cost, not a stock).

So `FAAt301ESI` is the defensible **current-cost net stock** capital base.

---

## (A) Labor share — chart 12

### `labor_share_prs` — PRS85006173 (official series, direct)
- **Formula:** annual mean of the four quarterly PRS85006173 observations.
- **Classification:** OFFICIAL BLS series (construction = *direct*; no transformation beyond
  quarterly→annual averaging).
- **Source/access:** live FRED pull, 2026-06-30 (317 quarterly obs returned, 1947Q1–2026Q1).
- **Units:** index (BLS labor-share index, 2017=100). NOT a percent.
- **Frequency:** A (from quarterly mean). **Period:** 1947–2025. **obs_count:** 79.
- **Caveat:** this is an *index*, not a share level — it shows the *direction/trend* of the labor
  share, not its level. Declining index ⇒ falling labor share (consistent with the BEA-native level).

### `labor_share_corp_bea` — BEA-native cross-check (constructed)
- **Formula:** `100 × T1.14 line 4 (Compensation of employees, corporate business) ÷ T1.14 line 1
  (Gross value added of corporate business)`.
- **Classification:** CONSTRUCTED (source BEA NIPA T1.14). This is the honest *level* of the
  corporate-business labor share and is the primary labor-share level if the FRED index is ever
  unavailable.
- **Units:** percent. **Frequency:** A. **Period:** 1929–2024. **obs_count:** 96.
- **Caveat:** corporate-business basis (compensation as a share of *gross* corporate value added,
  which includes consumption of fixed capital and production taxes), so the level (~56–67%) is not
  identical to the whole-economy or net-value-added labor share. Trend is the comparable signal.

---

## (B) Corporate profit share / markup proxy — chart 13

### `profit_share_nfc` — nonfinancial corporate (constructed, PRIMARY)
- **Formula:** `100 × T1.14 line 27 (Corporate profits with IVA and CCAdj, nonfinancial corporate)
  ÷ T1.14 line 17 (Gross value added of nonfinancial corporate business)`.
- **Classification:** CONSTRUCTED (source BEA NIPA T1.14). This profits-to-value-added ratio is the
  standard markup / profit-share proxy used in heterodox macro.
- **Units:** percent. **Frequency:** A. **Period:** 1929–2024. **obs_count:** 96.

### `profit_share_corp` — total corporate (constructed, SECONDARY)
- **Formula:** `100 × T1.14 line 11 (Corporate profits with IVA and CCAdj, total corporate)
  ÷ T1.14 line 1 (Gross value added of corporate business)`.
- **Classification:** CONSTRUCTED (source BEA NIPA T1.14).
- **Units:** percent. **Frequency:** A. **Period:** 1929–2024. **obs_count:** 96.

**Sanity note:** profit share of *gross value added* runs in the mid-to-high teens (≈17–18% recently,
record-high 2024 profits), which is higher than the commonly-cited ~10–12% profit *share of GDP*
because the denominator here is sector value added, not GDP. The NIPA decomposition was verified
exact for 2024: NFC GVA(17) = CFC(18)+Comp(20)+Taxes(23)+NOS(24) to the dollar, and NOS(24) =
Interest(25)+Transfers(26)+Profits(27) to the dollar — confirming correct line selection/parsing.

---

## (C) Economy-wide profit rate — chart 14

### `profit_rate` — economy-wide (constructed)
- **Formula:** `100 × T1.14 line 11 (Corporate profits with IVA and CCAdj, total corporate)
  ÷ FAAt301ESI line 1 (current-cost net stock of private fixed assets)`.
- **Classification:** CONSTRUCTED (source BEA NIPA T1.14 + BEA Fixed Assets 3.1ESI).
- **Units:** percent. **Frequency:** A (annual numerator and annual stock).
- **Period:** 1947–2024 (overlap; capital stock begins 1947, BEA complete years end 2024).
- **obs_count:** 78.
- **Vintage:** both BEA inputs as-of ~2025.09.
- **Caveat (capital base):** the numerator is *corporate* profits but the denominator is the
  *economy-wide private* net fixed-asset stock (it includes noncorporate business and residential
  capital). This dilutes the level downward (≈4–5%). It is labeled clearly as an economy-wide
  approximate profit rate, not a corporate-matched one.

### `profit_rate_nfc` — sector-matched variant: **DATA_UNAVAILABLE**
- A clean sector-matched nonfinancial-corporate profit rate (NFC profits ÷ NFC net fixed assets)
  could **not** be honestly constructed: the on-disk BEA Fixed Assets tables (FAAt301/304/307 ESI)
  are **by-industry (NAICS)** cuts, not a nonfinancial-corporate (legal-form/sector) net-stock
  measure. Pairing NFC profits (line 27) with the economy-wide private net stock would be a
  *mismatched* numerator/denominator (misleading), so this column is intentionally left **empty**
  rather than fabricated. To build it would require BEA's sector net-stock data (e.g.
  Flow-of-Funds / Integrated Macroeconomic Accounts nonfinancial-corporate net fixed assets), which
  is not present on disk.

---

## Sanity table (first 3 + last 3 complete years)

### labor_share_prs (index, 2017=100)
| year | value |  | year | value |
|---|---|---|---|---|
| 1947 | 115.3125 |  | 2023 | 96.4348 |
| 1948 | 114.5215 |  | 2024 | 96.7703 |
| 1949 | 113.3435 |  | 2025 | 96.5800 |

### labor_share_corp_bea (%)
| year | value |  | year | value |
|---|---|---|---|---|
| 1929 | 62.4786 |  | 2022 | 55.5001 |
| 1930 | 63.9462 |  | 2023 | 55.5665 |
| 1931 | 67.0322 |  | 2024 | 55.6764 |

### profit_share_nfc (%)
| year | value |  | year | value |
|---|---|---|---|---|
| 1929 | 17.7885 |  | 2022 | 17.1794 |
| 1930 | 14.7882 |  | 2023 | 18.0822 |
| 1931 |  6.8810 |  | 2024 | 17.8258 |

### profit_share_corp (%)
| year | value |  | year | value |
|---|---|---|---|---|
| 1929 | 19.3428 |  | 2022 | 19.0119 |
| 1930 | 15.2788 |  | 2023 | 19.4981 |
| 1931 |  7.8080 |  | 2024 | 19.7167 |

### profit_rate (%)
| year | value |  | year | value |
|---|---|---|---|---|
| 1947 | 4.4863 |  | 2022 | 4.3931 |
| 1948 | 5.3601 |  | 2023 | 4.6229 |
| 1949 | 4.8069 |  | 2024 | 4.7586 |

### profit_rate_nfc
data_unavailable (see section C — no sector-matched NFC net capital stock on disk).
