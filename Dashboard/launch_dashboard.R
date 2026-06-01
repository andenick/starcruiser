# ============================================================================
# QUICK LAUNCHER - StarCruiser Dashboard
# ============================================================================
# Purpose: One-click launch script for the dashboard
# Simply run this file in RStudio or from command line
# ============================================================================

# Set working directory to this script's (the Dashboard) location.
# Works when sourced from RStudio or run via Rscript; falls back to the
# current directory if the script path cannot be determined.
.this_file <- tryCatch({
  args <- commandArgs(trailingOnly = FALSE)
  fa <- grep("^--file=", args, value = TRUE)
  if (length(fa) > 0) {
    sub("^--file=", "", fa[1])
  } else if (!is.null(sys.frame(1)$ofile)) {
    sys.frame(1)$ofile
  } else {
    NA_character_
  }
}, error = function(e) NA_character_)
if (!is.na(.this_file)) setwd(dirname(normalizePath(.this_file)))

# Check if required packages are installed
required_packages <- c("shiny", "shinydashboard", "data.table",
                       "echarts4r", "DT", "lubridate")

missing_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]

if (length(missing_packages) > 0) {
  cat("========================================\n")
  cat("ERROR: Missing required packages\n")
  cat("========================================\n\n")
  cat("The following packages need to be installed:\n")
  cat(paste("  -", missing_packages, collapse = "\n"), "\n\n")
  cat("Run the installation script first:\n")
  cat('  source("install_packages.R")\n\n')
  cat("Or install manually:\n")
  cat(sprintf('  install.packages(c(%s))\n\n',
              paste(sprintf('"%s"', missing_packages), collapse = ", ")))
  stop("Cannot launch dashboard - missing packages")
}

# Launch the dashboard
cat("========================================\n")
cat("Launching StarCruiser Dashboard...\n")
cat("========================================\n\n")

shiny::runApp()
