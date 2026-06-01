# Data Manifest — StarCruiser

StarCruiser ships **code only**. The economic data (~160 GB at full scale) is not
included; everything here comes from free, public sources you can re-download.

This file lists the inputs each part of the pipeline expects and where to get
them. Point the `DATA_ROOT` environment variable at the directory where you keep
these inputs (see `.env.example` / README). The project writes its own derived
products under `OUTPUT_ROOT`.

## Environment variables

| Variable      | Meaning                                   | Default     |
|---------------|-------------------------------------------|-------------|
| `DATA_ROOT`   | Root for source/input data (read)         | `data`      |
| `OUTPUT_ROOT` | Root for project outputs (write)          | `outputs`   |
| `PIPELINE_ROOT` | Prepared pipeline outputs for the Dash app | `Technical/pipeline` |

## Public data sources

| Source | What it provides | Free access | Key env var |
|--------|------------------|-------------|-------------|
| **FRED** (Federal Reserve Economic Data) | Inflation (CPI/PCE), interest rates, employment, GDP, housing, production, trade, fiscal, money & banking, income & spending, demographics, business, labor productivity, regional series | <https://fred.stlouisfed.org/> · API: <https://fred.stlouisfed.org/docs/api/api_key.html> | `FRED_API_KEY` |
| **BLS** (Bureau of Labor Statistics) | Employment, wages, hours, JOLTS, productivity | <https://www.bls.gov/data/> · bulk FTP/HTTP | (none required for bulk files) |
| **BEA** (Bureau of Economic Analysis) | NIPA tables, regional GDP/income, fixed assets, GDP-by-industry | <https://apps.bea.gov/API/signup/> | `BEA_API_KEY` |
| **Census** | County Business Patterns (CBP), ACS employment | <https://api.census.gov/data/key_signup.html> | `CENSUS_API_KEY` |
| **FDIC** BankFind | Bank registry, bank universe (assets, deposits, ROA/ROE) | <https://banks.data.fdic.gov/docs/> | (none) |
| **NBER** macrohistory | Long-run historical macro series | <https://www.nber.org/research/data/nber-macrohistory-database> | (none) |
| **OECD** | Cross-country social/labor indicators | <https://data-explorer.oecd.org/> | (none) |
| **World Bank** WDI | World Development Indicators (employment) | <https://datacatalog.worldbank.org/search/dataset/0037712> | (none) |
| **JST** Macrohistory | Jordà-Schularick-Taylor long-run financial series | <https://www.macrohistory.net/database/> | (none) |
| **Maddison Project** | Long-run GDP/population | <https://www.rug.nl/ggdc/historicaldevelopment/maddison/> | (none) |
| **Bank of England** Millennium dataset | Long-run UK macro/financial series | <https://www.bankofengland.co.uk/statistics/research-datasets> | (none) |
| **ILO** | International labour statistics | <https://ilostat.ilo.org/data/> | (none) |

## Expected layout under `DATA_ROOT`

The import/extract scripts under `Technical/` read source files from paths like:

```
$DATA_ROOT/API_MODULES/FRED/data/...      # FRED category CSV exports
$DATA_ROOT/API_MODULES/BEA/data/...       # BEA regional/NIPA CSVs
$DATA_ROOT/API_MODULES/BLS/data/...       # BLS bulk files
$DATA_ROOT/API_MODULES/CENSUS/data/...    # Census CBP/ACS
$DATA_ROOT/API_MODULES/FDIC_BANKFIND_DATA/DATA/...
$DATA_ROOT/DATA/{JST,Maddison,BoE,WorldBank,FRED}/...
$DATA_ROOT/raw-data/fred/...              # raw FRED pulls
```

You can satisfy these by downloading from the sources above and arranging files
under `DATA_ROOT`, or by adapting the loader scripts in `Technical/` to your own
download locations. The dashboards fall back to a small set of prepared CSV/FST
files under `Dashboard/data/` (R) and `PIPELINE_ROOT` (Dash) when present.

## API keys (bring your own)

All keys are free. See the README "API keys" section and `.env.example`.
Never commit real keys — `.env` is git-ignored.
