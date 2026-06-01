# ============================================================================
# CSV to FST Conversion Script - StarCruiser Dashboard
# ============================================================================
# Track A3.1: Convert CSV data files to FST format for 10x faster loading
# Run: Rscript convert_csv_to_fst.R
# ============================================================================

library(fst)
library(data.table)

# Path roots (override via environment; neutral defaults)
DATA_ROOT   <- Sys.getenv("DATA_ROOT", "data")
OUTPUT_ROOT <- Sys.getenv("OUTPUT_ROOT", "outputs")
FRED_SRC    <- file.path(DATA_ROOT, "API_MODULES/FRED/data")

message("========================================")
message("StarCruiser FST Conversion")
message("========================================\n")

# Output directory for FST files
fst_dir <- file.path("..", "Dashboard", "data")
dir.create(fst_dir, showWarnings = FALSE, recursive = TRUE)

# Define conversions: source CSV -> target FST
conversions <- list(
  list(
    name = "Inflation (CPI/PCE)",
    src = file.path(FRED_SRC, "[2025.10.07] fred_inflation_20250929.csv"),
    dst = file.path(fst_dir, "inflation.fst")
  ),
  list(
    name = "Interest Rates (Treasury Yields)",
    src = file.path(FRED_SRC, "[2025.09.29] fred_interest_rates_20250929.csv"),
    dst = file.path(fst_dir, "interest_rates.fst")
  ),
  list(
    name = "Employment (BLS)",
    src = file.path(FRED_SRC, "[2025.09.29] fred_employment_20250929.csv"),
    dst = file.path(fst_dir, "employment.fst")
  ),
  list(
    name = "County Clusters",
    src = {
      cluster_files <- list.files(file.path(OUTPUT_ROOT, "CLUSTERS"),
                                  pattern = "cluster_assignments\\.csv$", full.names = TRUE)
      if (length(cluster_files) > 0) cluster_files[length(cluster_files)] else ""
    },
    dst = file.path(fst_dir, "clusters.fst")
  ),
  # v7.0 - All remaining FRED categories
  list(
    name = "GDP & Growth",
    src = file.path(FRED_SRC, "[2025.09.29] fred_gdp_growth_20250929.csv"),
    dst = file.path(fst_dir, "gdp_growth.fst")
  ),
  list(
    name = "Housing",
    src = file.path(FRED_SRC, "[2025.09.29] fred_housing_20250929.csv"),
    dst = file.path(fst_dir, "housing.fst")
  ),
  list(
    name = "Production",
    src = file.path(FRED_SRC, "[2025.09.29] fred_production_20250929.csv"),
    dst = file.path(fst_dir, "production.fst")
  ),
  list(
    name = "Trade",
    src = file.path(FRED_SRC, "[2025.09.29] fred_trade_20250929.csv"),
    dst = file.path(fst_dir, "trade.fst")
  ),
  list(
    name = "Financial Stress",
    src = file.path(FRED_SRC, "[2025.09.29] fred_financial_stress_20250929.csv"),
    dst = file.path(fst_dir, "financial_stress.fst")
  ),
  list(
    name = "Fiscal",
    src = file.path(FRED_SRC, "[2025.09.29] fred_fiscal_20250929.csv"),
    dst = file.path(fst_dir, "fiscal.fst")
  ),
  list(
    name = "Money & Banking",
    src = file.path(FRED_SRC, "[2025.09.29] fred_money_banking_20250929.csv"),
    dst = file.path(fst_dir, "money_banking.fst")
  ),
  list(
    name = "Income & Spending",
    src = file.path(FRED_SRC, "[2025.09.29] fred_income_spending_20250929.csv"),
    dst = file.path(fst_dir, "income_spending.fst")
  ),
  list(
    name = "Demographics",
    src = file.path(FRED_SRC, "[2025.09.29] fred_demographics_20250929.csv"),
    dst = file.path(fst_dir, "demographics.fst")
  ),
  list(
    name = "Business",
    src = file.path(FRED_SRC, "[2025.10.07] fred_business_20250929.csv"),
    dst = file.path(fst_dir, "business.fst")
  ),
  list(
    name = "Labor Productivity",
    src = file.path(FRED_SRC, "[2025.09.29] fred_labor_productivity_20250929.csv"),
    dst = file.path(fst_dir, "labor_productivity.fst")
  ),
  list(
    name = "Regional",
    src = file.path(FRED_SRC, "[2025.09.29] fred_regional_20250929.csv"),
    dst = file.path(fst_dir, "regional.fst")
  )
)

# Process each conversion
results <- data.table(
  Dataset = character(0),
  CSV_Size_MB = numeric(0),
  FST_Size_MB = numeric(0),
  Compression = character(0),
  Records = integer(0),
  Status = character(0)
)

for (conv in conversions) {
  message(sprintf("Converting: %s", conv$name))

  if (!file.exists(conv$src)) {
    message(sprintf("  SKIPPED: Source not found: %s", conv$src))
    results <- rbind(results, data.table(
      Dataset = conv$name, CSV_Size_MB = NA, FST_Size_MB = NA,
      Compression = NA, Records = NA, Status = "SKIPPED"
    ))
    next
  }

  tryCatch({
    # Read CSV
    dt <- fread(conv$src)
    csv_size <- file.info(conv$src)$size / 1024^2

    # Convert date columns if present
    if ("date" %in% names(dt)) {
      dt[, date := as.Date(date)]
    }

    # Write FST with compression
    write_fst(dt, conv$dst, compress = 85)
    fst_size <- file.info(conv$dst)$size / 1024^2

    ratio <- sprintf("%.0f%%", (1 - fst_size / csv_size) * 100)

    message(sprintf("  CSV: %.1f MB -> FST: %.1f MB (%s smaller) | %s records",
                    csv_size, fst_size, ratio, format(nrow(dt), big.mark = ",")))

    results <- rbind(results, data.table(
      Dataset = conv$name, CSV_Size_MB = round(csv_size, 1),
      FST_Size_MB = round(fst_size, 1), Compression = ratio,
      Records = nrow(dt), Status = "OK"
    ))
  }, error = function(e) {
    message(sprintf("  ERROR: %s", e$message))
    results <- rbind(results, data.table(
      Dataset = conv$name, CSV_Size_MB = NA, FST_Size_MB = NA,
      Compression = NA, Records = NA, Status = paste("ERROR:", e$message)
    ))
  })
}

message("\n========================================")
message("Conversion Summary")
message("========================================")
print(results)

total_csv <- sum(results$CSV_Size_MB, na.rm = TRUE)
total_fst <- sum(results$FST_Size_MB, na.rm = TRUE)
message(sprintf("\nTotal: %.1f MB CSV -> %.1f MB FST (%.0f%% smaller)",
                total_csv, total_fst, (1 - total_fst / total_csv) * 100))

message("\nFST files written to: ", fst_dir)
message("Dashboard will auto-detect FST files on next launch.")
