# ============================================================================
# DATA LOADER - StarCruiser Dashboard v9.0
# ============================================================================
# Purpose: Load ALL 17 FRED economic data categories + derived data
# Data Sources: the data pipeline (primary) or source FRED store (fallback)
# Created: 2025-11-28 | Updated: 2026-05-02 (v9.0 - data-pipeline architecture)
# ============================================================================

library(data.table)

# Data roots (override via environment variables; neutral defaults for local run)
#   DATA_ROOT   - where source/input data is READ from
#   OUTPUT_ROOT - where the project's own outputs are WRITTEN
DATA_ROOT   <- Sys.getenv("DATA_ROOT", "data")
OUTPUT_ROOT <- Sys.getenv("OUTPUT_ROOT", "outputs")

# Data directories — prepared dashboard data first, source store fallback
DATA_PREPARED   <- "data"  # repo-relative (app runs with wd = Dashboard/)
DATA_SOURCE_FRED <- file.path(DATA_ROOT, "API_MODULES/FRED/data")
DATA_SOURCE_RAW  <- file.path(DATA_ROOT, "raw-data/fred")

#' Load Inflation Data (CPI/PCE) - FST or CSV
#' @return data.table with CPI and PCE series
load_inflation_data <- function() {
  fst_path <- file.path(DATA_PREPARED, "inflation.fst")
  nicky_path <- file.path(DATA_PREPARED, "fred_inflation.csv")
  source_path <- file.path(DATA_SOURCE_FRED, "[2025.10.07] fred_inflation_20250929.csv")

  message("Loading inflation data...")

  if (file.exists(fst_path)) {
    message("  Using FST format (fast)")
    dt <- read_fst(fst_path, as.data.table = TRUE)
  } else if (file.exists(nicky_path)) {
    message("  Using pipeline CSV")
    dt <- fread(nicky_path)
  } else if (file.exists(source_path)) {
    message("  Fallback: source CSV")
    dt <- fread(source_path)
  } else {
    stop("Inflation data not found (checked FST, the data pipeline, the source store)")
  }

  # Convert date column to Date type
  dt[, date := as.Date(date)]

  # Convert value to numeric (in case it's character)
  dt[, value := as.numeric(value)]

  # Sort by series and date
  setorder(dt, series_id, date)

  message(sprintf("  Loaded %s records, %d series",
                  format(nrow(dt), big.mark = ","),
                  uniqueN(dt$series_id)))

  return(dt)
}

#' Load Interest Rates Data (Yield Curve) - FST or CSV
#' @return data.table with Treasury yields and other interest rates
load_interest_rates <- function() {
  fst_path <- file.path(DATA_PREPARED, "interest_rates.fst")
  nicky_path <- file.path(DATA_PREPARED, "fred_interest_rates.csv")
  source_path <- file.path(DATA_SOURCE_FRED, "[2025.09.29] fred_interest_rates_20250929.csv")

  message("Loading interest rates data...")

  if (file.exists(fst_path)) {
    message("  Using FST format (fast)")
    dt <- read_fst(fst_path, as.data.table = TRUE)
  } else if (file.exists(nicky_path)) {
    message("  Using pipeline CSV")
    dt <- fread(nicky_path)
  } else if (file.exists(source_path)) {
    message("  Fallback: source CSV")
    dt <- fread(source_path)
  } else {
    stop("Interest rates data not found (checked FST, the data pipeline, the source store)")
  }

  # Convert date column to Date type
  dt[, date := as.Date(date)]

  # Convert value to numeric
  dt[, value := as.numeric(value)]

  # Sort by series and date
  setorder(dt, series_id, date)

  message(sprintf("  Loaded %s records, %d series",
                  format(nrow(dt), big.mark = ","),
                  uniqueN(dt$series_id)))

  return(dt)
}

#' Load Employment Data - FST or CSV
#' @return data.table with employment series (UNRATE, PAYEMS, sectors)
load_employment_data <- function() {
  fst_path <- file.path(DATA_PREPARED, "employment.fst")
  nicky_path <- file.path(DATA_PREPARED, "fred_employment.csv")
  source_path <- file.path(DATA_SOURCE_FRED, "[2025.09.29] fred_employment_20250929.csv")

  message("Loading employment data...")

  if (file.exists(fst_path)) {
    message("  Using FST format (fast)")
    dt <- read_fst(fst_path, as.data.table = TRUE)
  } else if (file.exists(nicky_path)) {
    message("  Using pipeline CSV")
    dt <- fread(nicky_path)
  } else if (file.exists(source_path)) {
    message("  Fallback: source CSV")
    dt <- fread(source_path)
  } else {
    stop("Employment data not found (checked FST, the data pipeline, the source store)")
  }

  # Convert date column to Date type
  dt[, date := as.Date(date)]

  # Convert value to numeric
  dt[, value := as.numeric(value)]

  # Sort by series and date
  setorder(dt, series_id, date)

  message(sprintf("  Loaded %s records, %d series",
                  format(nrow(dt), big.mark = ","),
                  uniqueN(dt$series_id)))

  return(dt)
}

#' Load Master Catalog (for Data Quality Dashboard)
#' @return data.table with quality tiers and metadata
load_master_catalog <- function() {
  file_path <- file.path(OUTPUT_ROOT, "CATALOGS/MASTER_CATALOG.csv")

  if (!file.exists(file_path)) {
    warning("Master catalog not found: ", file_path)
    return(NULL)
  }

  message("Loading master catalog...")
  dt <- fread(file_path)

  message(sprintf("  Loaded %d datasets", nrow(dt)))

  return(dt)
}

# ============================================================================
# GENERIC FRED LOADER (used by all new category loaders)
# ============================================================================

.load_fred_category <- function(category_name, fst_name, csv_filename) {
  fst_path <- file.path(DATA_PREPARED, fst_name)
  csv_path <- file.path(DATA_SOURCE_FRED, csv_filename)

  message(sprintf("Loading %s data...", category_name))

  if (file.exists(fst_path)) {
    message("  Using FST format (fast)")
    dt <- read_fst(fst_path, as.data.table = TRUE)
  } else if (file.exists(csv_path)) {
    dt <- fread(csv_path)
  } else {
    warning(sprintf("%s data not found (checked FST and CSV)", category_name))
    return(NULL)
  }

  dt[, date := as.Date(date)]
  dt[, value := as.numeric(value)]
  setorder(dt, series_id, date)

  message(sprintf("  Loaded %s records, %d series",
                  format(nrow(dt), big.mark = ","),
                  uniqueN(dt$series_id)))
  return(dt)
}

# ============================================================================
# v7.0 NEW CATEGORY LOADERS
# ============================================================================

load_gdp_data <- function() {
  .load_fred_category("GDP & Growth", "gdp_growth.fst",
    "[2025.09.29] fred_gdp_growth_20250929.csv")
}

load_housing_data <- function() {
  .load_fred_category("Housing", "housing.fst",
    "[2025.09.29] fred_housing_20250929.csv")
}

load_production_data <- function() {
  .load_fred_category("Production", "production.fst",
    "[2025.09.29] fred_production_20250929.csv")
}

load_trade_data <- function() {
  .load_fred_category("Trade", "trade.fst",
    "[2025.09.29] fred_trade_20250929.csv")
}

load_financial_stress_data <- function() {
  .load_fred_category("Financial Stress", "financial_stress.fst",
    "[2025.09.29] fred_financial_stress_20250929.csv")
}

load_fiscal_data <- function() {
  .load_fred_category("Fiscal", "fiscal.fst",
    "[2025.09.29] fred_fiscal_20250929.csv")
}

load_money_banking_data <- function() {
  .load_fred_category("Money & Banking", "money_banking.fst",
    "[2025.09.29] fred_money_banking_20250929.csv")
}

load_income_spending_data <- function() {
  .load_fred_category("Income & Spending", "income_spending.fst",
    "[2025.09.29] fred_income_spending_20250929.csv")
}

load_demographics_data <- function() {
  .load_fred_category("Demographics", "demographics.fst",
    "[2025.09.29] fred_demographics_20250929.csv")
}

load_business_data <- function() {
  .load_fred_category("Business", "business.fst",
    "[2025.10.07] fred_business_20250929.csv")
}

load_labor_productivity_data <- function() {
  .load_fred_category("Labor Productivity", "labor_productivity.fst",
    "[2025.09.29] fred_labor_productivity_20250929.csv")
}

load_regional_data <- function() {
  .load_fred_category("Regional", "regional.fst",
    "[2025.09.29] fred_regional_20250929.csv")
}

# ============================================================================
# v8.0 BEA REGIONAL & NIPA LOADERS
# ============================================================================

DATA_BEA <- file.path(DATA_ROOT, "API_MODULES/BEA/data")
DATA_FDIC <- file.path(DATA_ROOT, "API_MODULES/FDIC_BANKFIND_DATA/DATA")

#' Load BEA State GDP data (all 50 states)
load_bea_state_gdp <- function() {
  file_path <- file.path(DATA_BEA, "[2025.09.29] regional_CAGDP1_STATE_2010_2025.csv")
  if (!file.exists(file_path)) { warning("BEA state GDP not found"); return(NULL) }
  message("Loading BEA state GDP data...")
  dt <- fread(file_path)
  dt[, DataValue := as.numeric(DataValue)]
  dt[, TimePeriod := as.integer(TimePeriod)]
  message(sprintf("  Loaded %d records, %d states", nrow(dt), uniqueN(dt$GeoName)))
  dt
}

#' Load BEA State GDP by Industry
load_bea_state_gdp_industry <- function() {
  file_path <- file.path(DATA_BEA, "[2025.09.29] regional_CAGDP2_STATE_2010_2025.csv")
  if (!file.exists(file_path)) { warning("BEA GDP by industry not found"); return(NULL) }
  message("Loading BEA state GDP by industry...")
  dt <- fread(file_path)
  dt[, DataValue := as.numeric(DataValue)]
  dt[, TimePeriod := as.integer(TimePeriod)]
  message(sprintf("  Loaded %d records", nrow(dt)))
  dt
}

#' Load BEA State Personal Income
load_bea_state_income <- function() {
  file_path <- file.path(DATA_BEA, "[2025.09.29] regional_CAINC1_STATE_2010_2025.csv")
  if (!file.exists(file_path)) { warning("BEA state income not found"); return(NULL) }
  message("Loading BEA state personal income...")
  dt <- fread(file_path)
  dt[, DataValue := as.numeric(DataValue)]
  dt[, TimePeriod := as.integer(TimePeriod)]
  message(sprintf("  Loaded %d records, %d states", nrow(dt), uniqueN(dt$GeoName)))
  dt
}

#' Load BEA NIPA tables (expanded - 21 tables, quarterly GDP components)
load_bea_nipa <- function() {
  file_path <- file.path(DATA_BEA, "[2025.09.29] expanded_nipa_20250929.csv")
  if (!file.exists(file_path)) { warning("BEA NIPA not found"); return(NULL) }
  message("Loading BEA NIPA tables...")
  dt <- fread(file_path)
  dt[, DataValue := as.numeric(DataValue)]
  message(sprintf("  Loaded %d records, %d tables", nrow(dt), uniqueN(dt$TableName)))
  dt
}

#' Load FDIC Bank Registry (tiered - key columns only)
load_fdic_banks <- function() {
  file_path <- file.path(DATA_FDIC, "tiered_bank_registry.csv")
  if (!file.exists(file_path)) { warning("FDIC bank registry not found"); return(NULL) }
  message("Loading FDIC bank registry...")
  dt <- fread(file_path, select = c(
    "CERT", "NAME", "CITY", "STNAME", "STALP", "ASSET", "ASSET_MILLIONS",
    "DEP", "NETINC", "CHARTER", "BKCLASS", "REGAGNT", "TIER_NUM", "TIER_NAME",
    "IS_GSIB", "IS_DFAST"
  ))
  dt[, ASSET_MILLIONS := as.numeric(ASSET_MILLIONS)]
  dt[, DEP := as.numeric(DEP)]
  dt[, NETINC := as.numeric(NETINC)]
  message(sprintf("  Loaded %d banks", nrow(dt)))
  dt
}

#' Load FDIC Bank Universe (full - for ROA/ROE analysis)
load_fdic_bank_universe <- function() {
  file_path <- file.path(DATA_FDIC, "bank_universe_complete.csv")
  if (!file.exists(file_path)) { warning("FDIC bank universe not found"); return(NULL) }
  message("Loading FDIC bank universe...")
  dt <- fread(file_path, select = c(
    "CERT", "NAME", "STNAME", "STALP", "ASSET", "DEP", "NETINC",
    "ROA", "ROAPTX", "ROE", "ROEQ", "BKCLASS", "CHARTER",
    "CBSA_METRO_NAME", "CBSA_METRO_FLG", "TIER_NUM", "TIER_NAME",
    "CITY", "OFFICES"
  ))
  dt[, ASSET := as.numeric(ASSET)]
  dt[, DEP := as.numeric(DEP)]
  dt[, ROA := as.numeric(ROA)]
  dt[, ROE := as.numeric(ROE)]
  message(sprintf("  Loaded %d banks", nrow(dt)))
  dt
}
