# StarCruiser Economic Dashboard

**Version**: 4.0 (Phase 4 Treasury & Inflation Analysis)
**Created**: November 28, 2025
**Last Updated**: December 5, 2025
**Framework**: Shiny Dashboard (shinydashboard)

---

## Overview

The StarCruiser Economic Dashboard is a comprehensive, interactive visualization tool for analyzing:
- **CPI/PCE Inflation** - Headline vs core, component breakdown, year-over-year changes
- **Treasury Market** - Yield curve analysis, spreads, real yields, breakeven inflation
- **Inflation Deep Dive** - Component contributions, CPI vs PCE wedge, alternative measures
- **Employment Statistics** - National unemployment, payrolls, industry sectors
- **Geographic Analysis** - County clusters, shift-share decomposition, regional patterns
- **Data Quality** - Transparency about data sources, quality tiers, and 2025 degradation

**Data Scale**: 300K+ observations across CPI/PCE, interest rates, and employment series
**Sources**: Federal Reserve Economic Data (FRED), Bureau of Labor Statistics (BLS)

---

## Quick Start

### 1. Install Required Packages

```r
install.packages(c(
  "shiny",           # >= 1.8.0
  "shinydashboard",  # >= 0.7.2
  "data.table",      # >= 1.14.8 (CRITICAL for performance)
  "echarts4r",       # >= 0.4.5 (fast interactive plotting)
  "DT",              # >= 0.30 (data tables)
  "lubridate"        # >= 1.9.0 (date handling)
))
```

### 2. Run the Dashboard

```r
# Set working directory to Dashboard folder
setwd("Dashboard/")

# Run the app
shiny::runApp()
```

**Or from command line**:
```r
shiny::runApp("Dashboard/")
```

The dashboard will open in your default web browser at `http://127.0.0.1:XXXX`

> **Data:** the app loads prepared CSV/FST files when present, and otherwise reads
> source data from `$DATA_ROOT/API_MODULES/...`. See `data/MANIFEST.md` and
> `.env.example` for how to set `DATA_ROOT` and obtain the public source data.

---

## Dashboard Features

### Tab 1: Overview
- **Value Boxes**: Latest CPI, unemployment rate, 10Y-2Y spread
- **Charts**: CPI vs PCE comparison, unemployment rate trend

### Tab 2: CPI/PCE Inflation
- **Headline vs Core**: Compare CPIAUCSL, CPILFESL, PCEPI, PCEPILFE (with recession bands)
- **Year-over-Year Changes**: Percentage changes calculated with 12-month lag (with recession bands)
- **Month-over-Month Changes**: NEW - Short-term inflation trends side-by-side with YoY
- **Component Breakdown**: Energy, Food, Housing, Medical, Transportation
  - NEW - **Toggle View**: Switch between line chart (time series) and bar chart (latest values)
- **Download**: Export inflation data as CSV with smart filenames

### Tab 3: Yield Curve
- **Yield Curve Snapshot**: View Treasury yields (3mo, 2Y, 5Y, 10Y, 30Y) for any date
- **Spread Analysis** (with recession bands):
  - 10Y-2Y spread (recession indicator)
  - 10Y-3mo spread
  - Negative values (inversions) highlighted
- **Multi-Date Comparison**: Overlay up to 3 yield curves
- **Download**: Export yield data and spreads as CSV

### Tab 4: Employment
- **Value Boxes**: Current unemployment rate, total payrolls, month-over-month change
- **National Time Series** (with recession bands): Unemployment rate, total nonfarm payrolls
- **Industry Sectors** (with recession bands): Manufacturing, Construction, Retail, Financial, Professional Services, Education/Health, Leisure/Hospitality
- **Interactive**: Select which sectors to display
- **Download**: Export employment data as CSV

### Tab 5: Geographic Analysis
- **Value Boxes**: Counties analyzed, cluster types, total employment, average growth
- **County Clusters**: 8 typologies from K-means clustering (Manufacturing, Service, Tourism, etc.)
- **Cluster Distribution**: Bar chart showing county distribution across clusters
- **Cluster Characteristics**: Summary table with avg employment, growth, regional effects
- **Shift-Share Decomposition**:
  - Top 15 counties by regional competitive advantage
  - Bottom 15 counties by regional competitive disadvantage
- **Employment Growth by Cluster**: Compare growth rates across all 8 typologies
- **Industry Composition**: View top 10 industries for any selected cluster
- **County Details Table**: Searchable, filterable table with all 3,221 counties
- **Download**: Export full county dataset as CSV

### Tab 6: Data Quality
- **Quality Metrics**: Data freshness, series count, quality tier
- **Data Sources & Attribution**: Complete FRED attribution with citation format
- **2025 Warning**: Information about data degradation due to Trump admin budget cuts
- **Summary Statistics by Category**: High-level stats (total series, records, date ranges, freshness, quality tier)
- **Data Series Catalog**: Complete catalog of all series with date ranges and observation counts
- **Download**: Export data catalog as CSV

---

## Data Sources

### Inflation Data
**File**: `$DATA_ROOT/API_MODULES/FRED/data/[2025.10.07] fred_inflation_20250929.csv`
**Records**: 17,332
**Series**: CPIAUCSL, CPILFESL, PCEPI, PCEPILFE, CPIENGSL, CPIFABSL, CPIHOSSL, CPIMEDSL, CPITRNSL

### Interest Rates
**File**: `$DATA_ROOT/API_MODULES/FRED/data/[2025.09.29] fred_interest_rates_20250929.csv`
**Records**: 248,052
**Series**: DGS3MO, DGS2, DGS5, DGS10, DGS30, FEDFUNDS, etc.

### Employment
**File**: `$DATA_ROOT/API_MODULES/FRED/data/[2025.09.29] fred_employment_20250929.csv`
**Records**: 34,335
**Series**: UNRATE, PAYEMS, MANEMP, USCONS, USTRADE, USFIRE, USPBS, USEHS, USLAH

---

## File Structure

```
Dashboard/
├── app.R                   # Main Shiny application (UI + Server logic)
├── data_loader.R           # Data loading functions
├── global.R                # Package loading, data initialization, helper functions
├── README.md               # This file
└── www/                    # Static assets (CSS, images, etc.)
```

**Total Lines of Code**: ~800 lines across 3 R files

---

## Performance Notes

### Current Performance (Phase 1)
- **Initial Load**: 3-5 seconds (loads 300K+ records)
- **Tab Switching**: < 500ms
- **Filter Updates**: < 200ms (with 500ms debouncing)
- **Chart Rendering**: < 1 second

### Optimizations Implemented
- **data.table**: 10x faster than base R for data manipulation
- **echarts4r**: Fast interactive plotting with WebGL support
- **Debouncing**: Date range changes wait 500ms before recomputing
- **Pre-computation**: YoY changes and yield spreads calculated at startup
- **Downsampling**: Helper function ready for large datasets (not yet needed)

### Future Performance Improvements (Phase 3)
- Convert CSVs to FST format (10x faster loading: 3s → 300ms)
- Implement reactive caching with memoise
- Add server-side pagination for data tables
- Profile with profvis and optimize bottlenecks

---

## Data Quality Notes

### Quality Tier System
- **Tier 1**: Administrative data (95%+ coverage) - BEA NIPA
- **Tier 2**: Official surveys pre-2025 - FRED historical, BLS, Census
- **Tier 3**: Academic estimates + 2025 degraded survey data
- **Tier 4**: Private data with coverage bias - ADP, Indeed

### 2025 Data Degradation
**Context**: Trump administration budget cuts and staffing reductions

**Impacts**:
- BLS lost 25% of staff since February 2025
- Response rates declined: CES 64%→43%, CPS 69%→62%
- **Sept-Oct 2025: NO DATA** (43-day government shutdown)
- All 2025 survey data downgraded to Tier 3

**Recommendation**: Use Tier 1-2 data for critical analyses, cross-validate 2025 data.

**Reference**: `$OUTPUT_ROOT/DOCUMENTATION/TRUMP_DATA_POLICY_IMPACT_REPORT.md`

---

## Known Limitations

### Current Limitations (Phase 1 MVP)
1. **No ALFRED Vintage Tracking**: Directory is empty, feature deferred to Phase 2
2. **No Geographic Breakdown**: State/county employment maps pending data availability
3. **Static Data**: Manual refresh required (restart app to reload data)
4. **Single-User**: Not optimized for concurrent users

### Data Gaps (Documented)
1. **Gig Economy**: 15-20% of workforce systematically undercounted
2. **Sept-Oct 2025**: Missing data (government shutdown)
3. **Small County Suppression**: 500-800 counties have suppressed industry detail
4. **Informal Economy**: 10-15% US workforce not captured

**Full Documentation**: a data-gap registry is maintained internally and is not distributed with this code-only release.

---

## Troubleshooting

### Problem: "Error loading inflation data file not found"
**Solution**: Verify data file paths in `data_loader.R` match your system

### Problem: "Package 'echarts4r' not found"
**Solution**: Install missing packages (see Quick Start section)

### Problem: "Chart not rendering"
**Solution**:
1. Check browser console for JavaScript errors
2. Try different browser (Chrome recommended)
3. Clear browser cache

### Problem: "App is slow"
**Solution**:
1. Reduce date range (use last 5 years instead of all-time)
2. Deselect unused components/sectors
3. Consider implementing Phase 3 optimizations (FST files)

---

## Phase 2 Enhancements (COMPLETED - November 29, 2025)

### Features Implemented

1. **Recession Context Bands** (NBER Official Dates)
   - Gray shading on 8 time-series charts
   - Dot-com Recession (2001), Great Recession (2007-2009), COVID-19 (2020)
   - Automatically filters to visible date range

2. **Month-over-Month Inflation Analysis**
   - New chart showing short-term inflation trends
   - Side-by-side with Year-over-Year chart
   - Pre-computed at startup for performance

3. **Data Export Functionality**
   - CSV downloads on all 4 tabs (Inflation, Yields, Employment, Data Quality)
   - Smart filenames: `StarCruiser_[Tab]_[StartDate]_to_[EndDate]_[ExportDate].csv`
   - Chart image export built into echarts4r (save as PNG/JPEG)

4. **3-Level Attribution System**
   - Level 1: Chart subtitles with FRED source
   - Level 2: Comprehensive attribution box in Data Quality tab
   - Level 3: Dashboard footer with citation format

5. **CPI Component Visualization Toggle**
   - Switch between Line chart (time series) and Bar chart (latest values)
   - Radio button selector for flexible analysis

6. **Summary Statistics Table**
   - High-level stats by category (Inflation, Rates, Employment)
   - Total series, records, date ranges, freshness, quality tiers
   - Professional DT table with formatting

### Code Improvements
- Added `add_recession_bands()` helper function
- Pre-computed MoM changes alongside YoY

---

## Future Enhancements

### Phase 3: Performance Optimization (Pending)
- [ ] CPI component decomposition (stacked area chart)
- [ ] ALFRED vintage tracking (revision history)
- [ ] Employment geographic breakdown (if data available)

### Phase 3: Performance Optimization (continued)
- [ ] Convert CSVs to FST format (10x faster loading)
- [ ] Implement reactive caching
- [ ] Add loading indicators
- [ ] Profile and optimize bottlenecks

### Phase 4: Data Quality & Polish
- [ ] Expand Data Quality dashboard
- [ ] Add export functionality (CSV, PNG)
- [ ] Custom theming
- [ ] Mobile responsiveness

### Phase 5: Modularization (Week 3+, if needed)
- [ ] Split app.R into modules (if exceeds 800-1000 lines)
- [ ] Create reusable UI components
- [ ] Implement unit tests

---

## Deployment Options

### Local Development
```r
shiny::runApp("Dashboard/")
```

### RStudio Connect
Professional deployment with authentication, scheduling, and monitoring

### Shinyapps.io
Free tier: 5 apps, 25 active hours/month
```r
library(rsconnect)
deployApp("Dashboard/")
```

### Docker
Create `Dockerfile` for reproducible deployment

---

## Contact & Maintenance

**Project**: StarCruiser Economic Dashboard
**Dashboard Location**: `Dashboard/`
**Data Location**: `$DATA_ROOT/API_MODULES/FRED/data/` (see `data/MANIFEST.md` for the full layout)

**Created**: November 28, 2025
**Last Updated**: December 5, 2025
**Status**: Phase 4 (Treasury & Inflation Analysis)

---

## Success Metrics

### Phase 1 Targets (Achieved)
- [x] App runs without errors
- [x] All 4 tabs functional
- [x] Data updates when date range changes
- [x] Charts render in < 3 seconds
- [x] Deployable via `shiny::runApp()`

### User Experience Targets
- [x] Professional appearance
- [x] Intuitive navigation
- [x] Clear data labels
- [x] Helpful error messages
- [x] Fast and responsive

---

**Ready to explore economic data.**

For questions or issues, see the project `README.md` and `data/MANIFEST.md`.
