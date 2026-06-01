# ============================================================================
# PACKAGE INSTALLATION SCRIPT - StarCruiser Dashboard
# ============================================================================
# Purpose: Install all required R packages for the dashboard
# Run this once before launching the dashboard for the first time
# ============================================================================

cat("========================================\n")
cat("StarCruiser Dashboard - Package Setup\n")
cat("========================================\n\n")

# List of required packages
required_packages <- c(
  "shiny",           # >= 1.8.0  - Shiny framework
  "shinydashboard",  # >= 0.7.2  - Dashboard layout
  "data.table",      # >= 1.14.8 - Fast data manipulation (CRITICAL)
  "echarts4r",       # >= 0.4.5  - Interactive plotting
  "DT",              # >= 0.30   - Data tables
  "lubridate"        # >= 1.9.0  - Date handling
)

# Optional packages (for Phase 2+)
optional_packages <- c(
  "leaflet",         # Geographic maps
  "plotly",          # Alternative plotting
  "memoise",         # Advanced caching
  "profvis",         # Performance profiling
  "fst",             # Fast binary storage (Phase 3)
  "shinybusy"        # Loading indicators
)

# Function to install missing packages
install_if_missing <- function(packages, optional = FALSE) {
  new_packages <- packages[!(packages %in% installed.packages()[,"Package"])]

  if (length(new_packages) > 0) {
    cat(sprintf("Installing %d %s package(s):\n",
                length(new_packages),
                ifelse(optional, "optional", "required")))
    cat(paste("  -", new_packages, collapse = "\n"), "\n\n")

    install.packages(new_packages, dependencies = TRUE)

    cat(sprintf("✓ Installed %d package(s)\n\n", length(new_packages)))
  } else {
    cat(sprintf("✓ All %s packages already installed\n\n",
                ifelse(optional, "optional", "required")))
  }
}

# Install required packages
cat("Step 1: Installing required packages\n")
cat("-------------------------------------\n")
install_if_missing(required_packages, optional = FALSE)

# Ask about optional packages
cat("Step 2: Optional packages\n")
cat("-------------------------\n")
cat("Install optional packages for Phase 2+ features? (y/n): ")
response <- tolower(trimws(readline()))

if (response == "y" || response == "yes") {
  install_if_missing(optional_packages, optional = TRUE)
} else {
  cat("Skipping optional packages\n\n")
}

# Verify installations
cat("Step 3: Verification\n")
cat("--------------------\n")

all_installed <- TRUE
for (pkg in required_packages) {
  if (pkg %in% installed.packages()[,"Package"]) {
    cat(sprintf("✓ %s installed\n", pkg))
  } else {
    cat(sprintf("✗ %s MISSING\n", pkg))
    all_installed <- FALSE
  }
}

cat("\n========================================\n")
if (all_installed) {
  cat("SUCCESS! All required packages installed.\n")
  cat("========================================\n\n")
  cat("You can now run the dashboard:\n")
  cat('  shiny::runApp("Dashboard")\n\n')
} else {
  cat("WARNING: Some packages failed to install.\n")
  cat("========================================\n\n")
  cat("Please install missing packages manually:\n")
  cat('  install.packages(c("package1", "package2"))\n\n')
}
