# Productive vs Unproductive Labor — Employment Split (US, annual)

> **⚠️ CONSTRUCTED CLASSIFICATION — heterodox (Shaikh-Tonak). NOT an official BLS series.**
> This series applies the Marxian productive/unproductive-labor distinction of Shaikh & Tonak,
> *Measuring the Wealth of Nations* (Cambridge UP, 1994), to BLS Current Employment Statistics
> (CES) major-industry payroll employment. The **classification** is the heterodox/analytical
> contribution; the **underlying employment counts** are official BLS data. BLS does **not**
> publish a "productive/unproductive labor" series and never has. Sector-to-class assignment
> involves analytical judgment calls (documented below) and is contestable. Do not present this
> as, or alongside, an official statistic without this flag.

- **DPR/EPR id:** STAR_DPR_EPR_PRODUCTIVE_UNPRODUCTIVE_LABOR
- **Chart:** 15 (productive vs unproductive employment split)
- **Frequency:** Annual (A)
- **Units:** Employment in thousands of jobs (levels); percent of total nonfarm payroll employment (shares)
- **Period:** 1964–2025 (complete calendar years only)
- **obs_count:** 62 years
- **Output data:** `productive_unproductive_annual.csv`
- **Build date:** 2026-06-30
- **Data integrity:** Honest public-source data only. NO synthetic data, NO fabrication, NO
  gap-filling. Incomplete years (e.g. 2026, only 5 months on disk) are dropped, not imputed.

---

## 1. Classification source

The productive/unproductive distinction follows Shaikh & Tonak (1994), *Measuring the Wealth of
Nations*, esp. Ch. 2 (the conceptual production/non-production distinction) and Appendix A/B (the
industry-to-class correspondence). Productive labor produces surplus value (it is engaged in the
production, and the completion-of-production transport, of commodities); unproductive labor is
engaged in the **circulation** of value (trade, finance), in **social maintenance/reproduction**,
and in activities that consume rather than produce surplus value. Shaikh & Tonak's production
sectors are, at the major-industry level: agriculture, mining, construction, manufacturing, and
the productive part of transportation/communication/public utilities. Trade (wholesale + retail),
finance-insurance-real-estate (FIRE), most "other" private services, and general government are
unproductive.

This is the *conventional major-sector reading* of the S&T scheme, consistent with the project's
own correspondence note (`TECHNICAL_DATA/docs/appendices/[2025.09.22]
APPENDIX_INDUSTRY_CORRESPONDENCE.md`), which confirms agriculture and utilities map cleanly while
"Services" is explicitly flagged low-confidence and "requires expert decision," and FIRE was
grouped by S&T but NAICS splits it (52/53). The judgment calls below resolve those flagged cases
for this build.

### Why the historical Shaikh-Tonak reconstructed data is NOT used for the split

An internal Shaikh-Tonak reconstruction dataset (an integrated 1958–2025 profit-rate panel) is a
**profit-rate** reconstruction. Its labor columns — `klems_labor_hours`,
`klems_labor_compensation_col`, `klems_labor_compensation_nocol` — are **economy-wide aggregates
with no sector dimension and no productive/unproductive partition**. There is therefore no
sector-level productive-vs-unproductive *employment* series in that dataset to splice from. (That
reconstruction's extension also applies ad-hoc scaling factors, e.g. `S* = Corporate_Profits ×
3.0`, appropriate only for its profit-rate target and explicitly NOT used here.) Consequently the
**entire** 1964–2025 employment split is constructed from one consistent source — BLS CES
major-industry employment — under the S&T classification. This avoids a fabricated or
level-mismatched splice. The `segment` column is therefore `ces_extension` for every row; there is
no `shaikh_historical` segment (see §4).

---

## 2. Sector → class mapping (the assignment actually used)

CES major-sector (supersector) payroll employment, NAICS basis. Total control = PAYEMS (total
nonfarm). The mapping below sums **exactly** to PAYEMS in every year (verified, residual = 0).

| CES sector | FRED series_id | Class | Basis / note |
|---|---|---|---|
| Mining & logging | USMINE | **Productive** | S&T production sector |
| Construction | USCONS | **Productive** | S&T production sector |
| Manufacturing | MANEMP | **Productive** | S&T production sector (core) |
| Transportation, warehousing & utilities | **USTPU − USTRADE − USWTRADE** | **Productive** | Productive part of S&T transport/communication/utilities; isolated by removing the trade component from the combined Trade-Transportation-Utilities supersector |
| Wholesale trade | USWTRADE | Unproductive | Circulation (commerce) |
| Retail trade | USTRADE | Unproductive | Circulation (commerce) |
| Financial activities (FIRE) | USFIRE | Unproductive | Circulation of money/credit, real estate |
| Professional & business services | USPBS | Unproductive | *Judgment call* — see §3 |
| Education & health services (private) | USEHS | Unproductive | Social reproduction/maintenance services |
| Leisure & hospitality | USLAH | Unproductive | Non-production services |
| Other services | USSERV | Unproductive | Non-production services |
| Information | USINFO | Unproductive | *Judgment call* — see §3 |
| Federal government | CES9091000001 | Unproductive | General government (non-production) |
| State government | CES9092000001 | Unproductive | General government (non-production) |
| Local government | CES9093000001 | Unproductive | General government (non-production) |

**Productive total** = USMINE + USCONS + MANEMP + (USTPU − USTRADE − USWTRADE)
**Unproductive total** = USWTRADE + USTRADE + USFIRE + USPBS + USEHS + USLAH + USSERV + USINFO + (Federal + State + Local government)
**Identity check:** Productive + Unproductive = PAYEMS, residual ≈ 0 thousand in all 62 years.

### Judgment calls (analytically contestable)

- **Information (USINFO) → unproductive.** Shaikh & Tonak's era treated *communication* (telephone/
  telegraph) as productive infrastructure. The modern NAICS *Information* supersector is dominated
  by publishing, broadcasting, motion pictures, data and information services — largely
  circulation/information activity — with telecom a minority. CES does not split telecom out of
  USINFO, so the whole supersector is assigned to unproductive. Sensitivity: USINFO is ~1.8–2.0%
  of nonfarm employment; reassigning all of it to productive would raise the 2025 productive share
  from 18.1% to ~20.0% and lower the 1964 productive share change only marginally — it does **not**
  alter the direction or magnitude of the long-run decline.
- **Professional & business services (USPBS) → unproductive.** Contains a productive minority
  (e.g., architectural/engineering/scientific services that are arguably part of production) mixed
  with management, administrative, advertising, and clerical-circulation services. The supersector
  cannot be split in CES at this level; assigned wholly to unproductive (its dominant character).
  This is the largest single judgment call by size (USPBS ≈ 14% of nonfarm by 2025). A reader who
  treats USPBS as productive would still see the productive share **fall** over 1964–2025, just
  from a higher base — the deindustrialization conclusion is robust to this choice.
- **Agriculture is absent.** CES nonfarm payrolls exclude agriculture (an S&T productive sector).
  In 1964 agriculture was still a non-trivial share of total US employment; its exclusion means the
  *level* of the productive share here is biased **downward** relative to a whole-economy S&T
  computation, especially in the early years. The series should be read as "productive share of
  **nonfarm payroll** employment," not of total employment. This is a coverage limitation, not an
  error, and is consistent across all years (so the trend is unaffected).
- **Government enterprises.** S&T separate productive government enterprises (e.g., USPS, public
  utilities) from general government. CES government supersectors are not split this way on disk;
  all government is assigned to unproductive. Minor downward bias on the productive level.

---

## 3. Data sources

- **Employment counts:** BLS Current Employment Statistics (CES), seasonally-unadjusted-equivalent
  monthly series retrieved via FRED, on disk at
  `Technical/AnuData/data/raw-data/fred/fred_employment.csv` (USMINE, USCONS, MANEMP, USTPU,
  USTRADE, USWTRADE, USFIRE, USPBS, USEHS, USLAH, USSERV, USINFO, PAYEMS) and
  `fred_industry_detail.csv` (CES9091000001 Federal, CES9092000001 State, CES9093000001 Local
  government). All series cover 1939-01 → 2026-05 with full monthly data.
- **Classification:** Shaikh & Tonak (1994), *Measuring the Wealth of Nations*; project
  correspondence note `APPENDIX_INDUSTRY_CORRESPONDENCE.md`.
- No live FRED pull was required — every needed series was already on disk.

### Annualization

Each monthly CES series is averaged to a calendar-year mean. A year is **complete** only if all 12
months are present; otherwise it is dropped. 2026 (5 months on disk) is therefore excluded. Result:
1964–2025, 62 complete years, no imputation.

---

## 4. Splice / extension method and divergence (EPR)

There is **no splice**. Because the S&T reconstructed dataset contains no sectoral productive/
unproductive *employment* breakdown (§1), the series is built from a single consistent source (BLS
CES) across the whole 1964–2025 span under one fixed classification. The `segment` flag is
`ces_extension` for all 62 rows.

**Cross-check against Shaikh & Tonak's published findings (consistency, not splice):** S&T and the
subsequent productive-labor literature (e.g., Mohun 2006; Paitaridis & Tsoulfidis 2012) report the
productive share of US employment as a **declining minority** through the postwar period — on the
order of the high-30s percent in the 1960s falling toward the high-teens/low-20s by the 2000s. This
build's 38.7% (1964) → 18.1% (2025) sits squarely in that range and reproduces the expected
secular decline, which is the primary validation available without a direct overlapping S&T
employment series. **Divergence note:** the *level* runs slightly low versus a whole-economy S&T
figure because (a) agriculture is excluded by CES and (b) USPBS/USINFO are assigned wholly to
unproductive (§2 judgment calls). These bias the level down but not the trend.

---

## 5. Sanity table (first 3 / last 3 years)

| year | productive_emp (000s) | unproductive_emp (000s) | productive_share % | unproductive_share % | segment |
|---|---|---|---|---|---|
| 1964 | 22,581.8 | 35,812.6 | 38.67 | 61.33 | ces_extension |
| 1965 | 23,510.5 | 37,368.2 | 38.62 | 61.38 | ces_extension |
| 1966 | 24,747.9 | 39,277.1 | 38.65 | 61.35 | ces_extension |
| … | … | … | … | … | … |
| 2023 | 28,686.5 | 127,208.8 | 18.40 | 81.60 | ces_extension |
| 2024 | 28,847.4 | 128,846.4 | 18.29 | 81.71 | ces_extension |
| 2025 | 28,748.7 | 129,690.2 | 18.14 | 81.86 | ces_extension |

**Headline finding.** The productive-labor share of nonfarm payroll employment **roughly halves**
over the period — 38.7% (1964) → 18.1% (2025) — while the unproductive share rises from 61.3% to
81.9%. This is the expected deindustrialization / rise-of-circulation-and-services pattern.
(Productive employment is essentially flat in *levels*, ~22.6M → ~28.7M, while total nonfarm grows
from ~58M to ~158M; the entire net job growth is in unproductive sectors.) Note that under this
nonfarm-only, USPBS/USINFO-unproductive classification, unproductive labor is already a majority in
1964 — a real feature of the classification (large government + trade + services even then), not a
sign of error; the substantive result is the **near-halving of the productive share**.

## 6. data_unavailable flags

- **2026:** incomplete (5 of 12 months on disk) → dropped (no partial-year value emitted).
- **Pre-1964:** out of requested scope (data exist back to 1939 if extension is later wanted).
- No within-series gaps: all 62 emitted years have full 12-month coverage for every input series.
