# ============================================================================
# StarCruiser Dashboard - Package Installer
# ============================================================================
# Run this script ONCE on a new computer to install required packages
# Usage: Open R and run: source("install_packages.R")
# ============================================================================

# Required packages
packages <- c(
    "shiny", # Web application framework
    "shinydashboard", # Dashboard layout
    "data.table", # Fast data manipulation
    "echarts4r", # Interactive charts
    "DT", # Data tables
    "lubridate", # Date handling
    "here" # Portable path handling
)

# Check and install missing packages
install_if_missing <- function(pkg) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
        message(sprintf("Installing %s...", pkg))
        install.packages(pkg, repos = "https://cloud.r-project.org/")
    } else {
        message(sprintf("%s already installed", pkg))
    }
}

message("=========================================")
message("StarCruiser Dashboard - Package Installer")
message("=========================================\n")

for (pkg in packages) {
    install_if_missing(pkg)
}

message("\n=========================================")
message("All packages installed!")
message("=========================================")
message("\nTo launch the dashboard, run:")
message("  setwd('Dashboard')")
message("  shiny::runApp()")
message("\nOr double-click 'launch_dashboard.bat' (Windows)")
message("=========================================")
