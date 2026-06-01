# ============================================================================
# GLOBAL CONFIGURATION - StarCruiser Dashboard
# ============================================================================
# Purpose: Package loading, global data initialization, helper functions
# This file runs once when the app starts
# ============================================================================

# Load required packages
suppressPackageStartupMessages({
  library(shiny)
  library(shinydashboard)
  library(data.table)
  library(echarts4r)
  library(DT)
  library(lubridate)
  # Track A: Analytics
  library(lmtest)     # Granger causality tests
  library(fst)        # Fast file format (10x speedup)
  library(memoise)    # Reactive caching
  # Track B: Geographic
  library(leaflet)    # Interactive county maps
  library(sf)         # Spatial data handling
  library(jsonlite)   # Parse leading counties JSON
})

# Source data loading functions
source("data_loader.R", local = TRUE)
source("geographic_module.R", local = TRUE)
source("treasury_module.R", local = TRUE)
source("inflation_module.R", local = TRUE)
source("labor_dynamics_module.R", local = TRUE)
source("wages_hours_module.R", local = TRUE)
# Track A modules
source("correlation_module.R", local = TRUE)
source("recession_cycle_module.R", local = TRUE)
source("quality_degradation_module.R", local = TRUE)
# Track C module
source("realtime_module.R", local = TRUE)
# v7.0 Economy modules
source("gdp_output_module.R", local = TRUE)
source("consumer_module.R", local = TRUE)
source("housing_module.R", local = TRUE)
source("financial_module.R", local = TRUE)
source("trade_fiscal_module.R", local = TRUE)
source("health_score_module.R", local = TRUE)
# v8.0 Economic Intelligence modules
source("regional_economy_module.R", local = TRUE)
source("state_comparison_module.R", local = TRUE)
source("productive_economy_module.R", local = TRUE)
source("economic_flows_module.R", local = TRUE)
source("banking_sector_module.R", local = TRUE)
source("financial_real_module.R", local = TRUE)

# ============================================================================
# LOAD DATA AT STARTUP (runs once)
# ============================================================================

message("========================================")
message("StarCruiser Dashboard - Initializing...")
message("========================================")

# Load CORE datasets (original 3)
inflation_data <- load_inflation_data()
rates_data <- load_interest_rates()
employment_data <- load_employment_data()
master_catalog <- load_master_catalog()

# Load v7.0 EXPANDED datasets (10 new categories)
message("\n--- Loading expanded economy datasets (v7.0) ---")
gdp_data <- tryCatch(load_gdp_data(), error = function(e) { message("  Skip: ", e$message); NULL })
housing_data <- tryCatch(load_housing_data(), error = function(e) { message("  Skip: ", e$message); NULL })
production_data <- tryCatch(load_production_data(), error = function(e) { message("  Skip: ", e$message); NULL })
trade_data <- tryCatch(load_trade_data(), error = function(e) { message("  Skip: ", e$message); NULL })
financial_data <- tryCatch(load_financial_stress_data(), error = function(e) { message("  Skip: ", e$message); NULL })
fiscal_data <- tryCatch(load_fiscal_data(), error = function(e) { message("  Skip: ", e$message); NULL })
money_data <- tryCatch(load_money_banking_data(), error = function(e) { message("  Skip: ", e$message); NULL })
spending_data <- tryCatch(load_income_spending_data(), error = function(e) { message("  Skip: ", e$message); NULL })
demographics_data <- tryCatch(load_demographics_data(), error = function(e) { message("  Skip: ", e$message); NULL })
business_data <- tryCatch(load_business_data(), error = function(e) { message("  Skip: ", e$message); NULL })

# Load v8.0 BEA Regional, NIPA, and FDIC data
message("\n--- Loading BEA Regional & FDIC data (v8.0) ---")
bea_state_gdp <- tryCatch(load_bea_state_gdp(), error = function(e) { message("  Skip: ", e$message); NULL })
bea_state_gdp_industry <- tryCatch(load_bea_state_gdp_industry(), error = function(e) { message("  Skip: ", e$message); NULL })
bea_state_income <- tryCatch(load_bea_state_income(), error = function(e) { message("  Skip: ", e$message); NULL })
bea_nipa <- tryCatch(load_bea_nipa(), error = function(e) { message("  Skip: ", e$message); NULL })
fdic_banks <- tryCatch(load_fdic_banks(), error = function(e) { message("  Skip: ", e$message); NULL })
fdic_universe <- tryCatch(load_fdic_bank_universe(), error = function(e) { message("  Skip: ", e$message); NULL })

# Load geographic/cluster data (Track B outputs)
message("\nLoading geographic cluster data...")
cluster_data <- tryCatch(
  load_cluster_data(),
  error = function(e) {
    message("Warning: Could not load cluster data - ", e$message)
    NULL
  }
)

message("========================================")
message("Data loading complete!")
message("========================================\n")

# ============================================================================
# PRE-COMPUTATIONS (calculated once at startup)
# ============================================================================

# Pre-compute YoY changes for inflation
message("Pre-computing YoY changes for inflation...")
inflation_data[, yoy_change := (value / shift(value, 12) - 1) * 100, by = series_id]

# Pre-compute MoM changes for inflation
message("Pre-computing MoM changes for inflation...")
inflation_data[, mom_change := (value / shift(value, 1) - 1) * 100, by = series_id]

# Pre-compute yield spreads
message("Pre-computing yield curve spreads...")
# Note: 3-month rate is DTB3 (T-bill) not DGS3MO in this dataset
yield_spreads <- dcast(rates_data[series_id %chin% c("DGS2", "DGS10", "DTB3")],
  date ~ series_id,
  value.var = "value"
)

# Calculate spreads only where both values exist
yield_spreads[, spread_2_10 := DGS10 - DGS2]
if ("DTB3" %in% names(yield_spreads)) {
  yield_spreads[, spread_3mo_10yr := DGS10 - DTB3]
}

# Pre-compute Sahm Rule (Track A1.2)
message("Pre-computing Sahm Rule indicator...")
sahm_data <- employment_data[series_id == "UNRATE"][order(date)]
sahm_data[, ma3 := frollmean(value, 3)]
sahm_data[, min_ma3_12m := frollapply(ma3, 12, min)]
sahm_data[, sahm_value := ma3 - min_ma3_12m]

message("Pre-computations complete!\n")

# ============================================================================
# RECESSION PERIOD DATA (NBER Official Dates)
# ============================================================================

# NBER recession dates from 2000-present
recession_periods <- data.table(
  start = as.Date(c("2001-03-01", "2007-12-01", "2020-02-01")),
  end = as.Date(c("2001-11-01", "2009-06-01", "2020-04-01")),
  name = c("Dot-com Recession", "Great Recession", "COVID-19 Recession")
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

#' Add recession shading to echarts4r plots
#' @param chart echarts4r plot object
#' @param date_range Vector with start and end dates (optional filter)
#' @return echarts4r plot with recession bands added
add_recession_bands <- function(chart, date_range = NULL) {
  # Filter recession periods to visible date range if provided
  recessions <- copy(recession_periods)

  if (!is.null(date_range) && length(date_range) == 2) {
    # Only show recessions that overlap with the visible range
    recessions <- recessions[end >= date_range[1] & start <= date_range[2]]

    # Trim recession dates to visible range
    recessions[start < date_range[1], start := date_range[1]]
    recessions[end > date_range[2], end := date_range[2]]
  }

  # If no recessions in range, return chart as-is
  if (nrow(recessions) == 0) {
    return(chart)
  }

  # Add gray shading for each recession period
  for (i in 1:nrow(recessions)) {
    chart <- chart %>%
      e_mark_area(
        data = list(
          list(
            xAxis = format(recessions$start[i], "%Y-%m-%d"),
            yAxis = "min"
          ),
          list(
            xAxis = format(recessions$end[i], "%Y-%m-%d"),
            yAxis = "max"
          )
        ),
        itemStyle = list(
          color = "rgba(0, 0, 0, 0.05)", # Light gray with transparency
          borderWidth = 0
        )
      )
  }

  return(chart)
}

#' Get latest value for a series
#' @param data data.table with date, series_id, value columns
#' @param series_id_val Character, series ID to filter
#' @return List with latest date and value
get_latest_value <- function(data, series_id_val) {
  latest <- data[series_id == series_id_val][order(-date)][1]

  if (nrow(latest) == 0) {
    return(list(date = NA, value = NA))
  }

  list(
    date = latest$date,
    value = latest$value
  )
}

#' Downsample data if too many points
#' @param dt data.table
#' @param max_points Maximum number of points to keep
#' @return data.table with at most max_points rows
downsample_if_large <- function(dt, max_points = 5000) {
  n <- nrow(dt)
  if (n <= max_points) {
    return(dt)
  }

  step <- ceiling(n / max_points)
  dt[seq(1, n, by = step)]
}

message("========================================")
message("StarCruiser Dashboard - Ready!")
message("========================================\n")
