# ============================================================================
# DATA LOADER - StarCruiser Dashboard (PORTABLE VERSION)
# ============================================================================
# Purpose: Load FRED economic data for CPI/PCE, Yield Curve, and Employment
# Data Sources: Data/FRED/ (uses 'here' package for portability)
# Created: 2025-11-28
# Modified: 2025-12-07 - Made portable with here package
# ============================================================================

library(data.table)
library(here)

# Data directories - PORTABLE (uses here() for project-root-relative paths)
# Works from ANY working directory as long as .here file exists in project root
DATA_FRED <- here("Data", "FRED")
DATA_LABOR <- here("Data", "LABOR_DYNAMICS")
DATA_CATALOGS <- here("Data", "CATALOGS")

#' Load Inflation Data (CPI/PCE)
#' @return data.table with CPI and PCE series
load_inflation_data <- function() {
  file_path <- file.path(DATA_FRED, "[2025.10.07] fred_inflation_20250929.csv")

  if (!file.exists(file_path)) {
    stop("Inflation data file not found: ", file_path)
  }

  message("Loading inflation data...")
  dt <- fread(file_path)

  # Convert date column to Date type
  dt[, date := as.Date(date)]

  # Convert value to numeric (in case it's character)
  dt[, value := as.numeric(value)]

  # Sort by series and date
  setorder(dt, series_id, date)

  message(sprintf(
    "  Loaded %s records, %d series",
    format(nrow(dt), big.mark = ","),
    uniqueN(dt$series_id)
  ))

  return(dt)
}

#' Load Interest Rates Data (Yield Curve)
#' @return data.table with Treasury yields and other interest rates
load_interest_rates <- function() {
  file_path <- file.path(DATA_FRED, "[2025.09.29] fred_interest_rates_20250929.csv")

  if (!file.exists(file_path)) {
    stop("Interest rates data file not found: ", file_path)
  }

  message("Loading interest rates data...")
  dt <- fread(file_path)

  # Convert date column to Date type
  dt[, date := as.Date(date)]

  # Convert value to numeric
  dt[, value := as.numeric(value)]

  # Sort by series and date
  setorder(dt, series_id, date)

  message(sprintf(
    "  Loaded %s records, %d series",
    format(nrow(dt), big.mark = ","),
    uniqueN(dt$series_id)
  ))

  return(dt)
}

#' Load Employment Data
#' @return data.table with employment series (UNRATE, PAYEMS, sectors)
load_employment_data <- function() {
  file_path <- file.path(DATA_FRED, "[2025.09.29] fred_employment_20250929.csv")

  if (!file.exists(file_path)) {
    stop("Employment data file not found: ", file_path)
  }

  message("Loading employment data...")
  dt <- fread(file_path)

  # Convert date column to Date type
  dt[, date := as.Date(date)]

  # Convert value to numeric
  dt[, value := as.numeric(value)]

  # Sort by series and date
  setorder(dt, series_id, date)

  message(sprintf(
    "  Loaded %s records, %d series",
    format(nrow(dt), big.mark = ","),
    uniqueN(dt$series_id)
  ))

  return(dt)
}

#' Load Master Catalog (for Data Quality Dashboard)
#' @return data.table with quality tiers and metadata
load_master_catalog <- function() {
  file_path <- file.path(DATA_CATALOGS, "MASTER_CATALOG.csv")

  if (!file.exists(file_path)) {
    warning("Master catalog not found: ", file_path)
    return(NULL)
  }

  message("Loading master catalog...")
  dt <- fread(file_path)

  message(sprintf("  Loaded %d datasets", nrow(dt)))

  return(dt)
}

#' Load Cluster Data (for Geographic Analysis)
#' @return data.table with cluster assignments
load_cluster_data <- function() {
  file_path <- file.path(DATA_CATALOGS, "CLUSTER_DATA.csv")

  if (!file.exists(file_path)) {
    warning("Cluster data not found: ", file_path)
    return(NULL)
  }

  message("Loading cluster data...")
  dt <- fread(file_path)

  message(sprintf("  Loaded %d clusters", nrow(dt)))

  return(dt)
}

#' Load Labor Dynamics Data (Beveridge Curve, Flows, HP Decomposition)
#' @return list of data.tables
load_labor_dynamics <- function() {
  result <- list()

  # Beveridge curve data
  beveridge_path <- file.path(DATA_LABOR, "beveridge_curve_data.csv")
  if (file.exists(beveridge_path)) {
    result$beveridge <- fread(beveridge_path)
    result$beveridge[, date := as.Date(date)]
    message(sprintf("  Loaded Beveridge curve: %d records", nrow(result$beveridge)))
  }

  # Labor flows
  flows_path <- file.path(DATA_LABOR, "labor_market_flows.csv")
  if (file.exists(flows_path)) {
    result$flows <- fread(flows_path)
    result$flows[, date := as.Date(date)]
    message(sprintf("  Loaded labor flows: %d records", nrow(result$flows)))
  }

  # HP decomposition
  hp_path <- file.path(DATA_LABOR, "employment_hp_decomposition.csv")
  if (file.exists(hp_path)) {
    result$hp_decomposition <- fread(hp_path)
    result$hp_decomposition[, date := as.Date(date)]
    message(sprintf("  Loaded HP decomposition: %d records", nrow(result$hp_decomposition)))
  }

  # Rolling correlations
  corr_path <- file.path(DATA_LABOR, "rolling_correlations.csv")
  if (file.exists(corr_path)) {
    result$correlations <- fread(corr_path)
    result$correlations[, date := as.Date(date)]
    message(sprintf("  Loaded correlations: %d records", nrow(result$correlations)))
  }

  return(result)
}
