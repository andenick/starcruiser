# StarCruiser Dashboard v5.0 - Portable Package

**Employment & Macroeconomic Exploration Tool**

## Quick Start

### 1. Prerequisites

- R (version 4.0+): <https://cran.r-project.org/>
- RStudio (optional but recommended): <https://posit.co/downloads/>

### 2. Install Required Packages (First Time Only)

Open R or RStudio and run:

```r
source("install_packages.R")
```

This installs: shiny, shinydashboard, data.table, echarts4r, DT, lubridate, here

### 3. Launch the Dashboard

**Option A: Windows (Easy)**

- Double-click `launch_dashboard.bat`

**Option B: From R/RStudio**

```r
setwd("path/to/Tal_Output_v1.0/Dashboard")
shiny::runApp()
```

**Option C: Command Line**

```bash
cd Tal_Output_v1.0/Dashboard
Rscript -e "shiny::runApp()"
```

## Dashboard Features (10 Tabs)

1. **Overview** - Key economic indicators and trends
2. **Inflation** - CPI/PCE analysis, components breakdown
3. **Employment** - Unemployment, payrolls, sectoral employment
4. **Treasury** - Yield curve analysis, rate spreads
5. **Geographic** - Regional clustering and patterns
6. **Data Quality** - Dataset validation and tier ratings
7. **Analysis** - Time series comparisons, custom views
8. **Market Watch** - Real-time market indicators
9. **Labor Dynamics** - Beveridge curve, V/U ratio, HP filter decomposition
10. **Wages & Hours** - Wage analysis, hours worked, real wages

## Data Included

### FRED Economic Data (538,133 records)

- **Inflation**: CPI, PCE, components (19 series)
- **Interest Rates**: Treasury yields, Fed Funds, spreads (47 series)
- **Employment**: Unemployment, payrolls, sectoral employment (31 series)
- **JOLTS**: Job openings, hires, separations, quits (10 series)
- **Wages**: Average hourly earnings, weekly hours

### Labor Dynamics Analysis

- Beveridge curve data (V/U ratio over time)
- Labor market flows (EU/UE rates)
- HP filter decomposition (trend/cycle)
- Rolling correlations

## Folder Structure

```
Tal_Output_v1.0/
├── Dashboard/           # R Shiny application
│   ├── app.R            # Main application
│   ├── global.R         # Configuration
│   ├── data_loader.R    # Data loading (portable paths)
│   ├── geographic_module.R
│   ├── treasury_module.R
│   ├── inflation_module.R
│   ├── labor_dynamics_module.R
│   ├── wages_hours_module.R
│   └── www/             # Static assets
├── Data/
│   ├── FRED/            # Economic time series (19 CSVs)
│   ├── LABOR_DYNAMICS/  # Beveridge, HP decomposition
│   └── CATALOGS/        # Master catalog
├── install_packages.R   # Package installer
├── launch_dashboard.bat # Windows launcher
└── README.md            # This file
```

## Data Sources

- **FRED** (Federal Reserve Economic Data) - via the FRED API collector
- **BLS JOLTS** (Job Openings and Labor Turnover Survey)

## Technical Notes

- Uses **here** package for portable paths - works from any working directory
- Uses **data.table** for fast in-memory data manipulation
- Uses **echarts4r** for interactive JavaScript charts
- Data is pre-loaded at startup for optimal performance
- The `.here` file marks the project root - do not delete it

## Version History

- **v5.0** (2025-12-07): Added Labor Dynamics & Wages tabs, JOLTS data
- **v4.0** (2025-11-28): Full dashboard with 8 tabs
- **v3.0**: Basic CPI/PCE analysis

## Troubleshooting

**"Package not found" errors:**

```r
source("install_packages.R")
```

**Data not loading:**

- Ensure you're running from the `Dashboard/` directory
- Check that `../Data/` folder exists with CSV files

**Charts not displaying:**

- Update echarts4r: `install.packages("echarts4r")`

---
*Built with the StarCruiser project*
*Data: public economic data sources*
