# StarCruiser

**StarCruiser** is a macroeconomic employment & inflation intelligence toolkit.
It aggregates employment-, inflation-, and financial-market data from a wide set
of free public sources (FRED, BLS, BEA, Census, FDIC, NBER, OECD, World Bank,
JST, Maddison, Bank of England, ILO) into a unified analytical dataset spanning
~600 economic series, and ships **two interactive dashboards**:

- a **Plotly Dash** app (Python) — `Dashboard/app.py`
- an **R Shiny** app — `Dashboard/app.R` (+ modules)

The repository contains **code only**. The underlying data is large and public —
re-download it from the sources listed in [`data/MANIFEST.md`](data/MANIFEST.md).

## What's inside

| Path | Contents |
|------|----------|
| `Technical/*.py` | Data import / extraction / analysis scripts (FRED, BLS, BEA, Census CBP, JST, Maddison, BoE, WDI, OECD, NBER, FDIC), catalog builders, geographic clustering, shift-share, Beveridge-curve, inflation decomposition, quality monitoring. |
| `Technical/convert_csv_to_fst.R` | Converts source CSVs to fast FST files for the R dashboard. |
| `Technical/DATA_DICTIONARY.md` | Series definitions, metadata, and provenance. |
| `Dashboard/app.py` | Plotly Dash dashboard. |
| `Dashboard/*.R` | R Shiny dashboard + modules. |
| `Tal_Output_v1.0/` | A trimmed, standalone snapshot of the R dashboard. |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For the R dashboard, install the R packages (in R):

```r
source("Dashboard/install_packages.R")
```

### 2. Configure paths and keys

Copy `.env.example` to `.env` and set:

- **`DATA_ROOT`** — directory where the project **reads** source/input data
  (lay it out as described in [`data/MANIFEST.md`](data/MANIFEST.md)).
- **`OUTPUT_ROOT`** — directory where the project **writes** its outputs.

Then export them in your shell (the env vars are read by both Python and R):

```bash
export DATA_ROOT=/path/to/your/data
export OUTPUT_ROOT=/path/to/your/outputs
```

If unset, they default to `./data` and `./outputs` (repo-relative).

### 3. API keys — bring your own

All keys are **free**. Sign up and set the corresponding environment variable:

| Service | Get a free key | Env var |
|---------|----------------|---------|
| FRED   | <https://fred.stlouisfed.org/docs/api/api_key.html> | `FRED_API_KEY` |
| Census | <https://api.census.gov/data/key_signup.html>       | `CENSUS_API_KEY` |
| BEA    | <https://apps.bea.gov/API/signup/>                  | `BEA_API_KEY` |

BLS bulk files, FDIC, NBER, OECD, World Bank, JST, Maddison, and BoE downloads
do not require a key. See `.env.example` for the full list.

## Run

### Plotly Dash dashboard (Python)

```bash
python Dashboard/app.py
# serves on http://localhost:8050
```

### R Shiny dashboard

```bash
Rscript Dashboard/launch_dashboard.R
# or, in R:  setwd("Dashboard"); shiny::runApp()
```

The R dashboard prefers prepared FST/CSV files under `Dashboard/data/`; generate
them with `Rscript Technical/convert_csv_to_fst.R` after placing source CSVs
under `DATA_ROOT` (see the manifest).

### Build the dataset

The scripts in `Technical/` import each source into `DATA_ROOT`/`OUTPUT_ROOT`.
Most can be run standalone, e.g.:

```bash
python Technical/import_bea_data.py
python Technical/download_census_cbp.py
python Technical/build_master_catalog.py
```

## Data

StarCruiser does not redistribute any source data. Everything is publicly
available — see [`data/MANIFEST.md`](data/MANIFEST.md) for the source list,
free-access links, and the expected directory layout under `DATA_ROOT`.

## License

No license is included; all rights reserved by default.
