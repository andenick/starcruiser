# ============================================================================
# WAGES & HOURS MODULE - StarCruiser Dashboard
# ============================================================================
# Purpose: Wage growth and hours worked analysis
# Features:
#   - Average hourly earnings trends
#   - Real vs nominal wage growth
#   - Average weekly hours
#   - Employment Cost Index
#   - Wage-unemployment relationship
# ============================================================================

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

#' Load wages and hours data from comprehensive employment file
#' @return data.table with wages and hours series
load_wages_data <- function() {
    # Look for comprehensive employment file
    files <- list.files("../Inputs/source/FRED",
        pattern = "fred_comprehensive_employment.*\\.csv$",
        full.names = TRUE
    )

    if (length(files) == 0) {
        message("Warning: Comprehensive employment data not found")
        return(NULL)
    }

    dt <- fread(files[1])
    dt[, date := as.Date(date)]

    # Filter to wages and hours series
    wages_series <- c("AHETPI", "CES0500000003", "ECIWAG", "AWHAETP", "AWHI")
    wages_dt <- dt[series_id %chin% wages_series]

    return(wages_dt)
}

#' Load inflation data for real wage calculations
#' @return data.table with CPI data
load_cpi_for_wages <- function() {
    files <- list.files("../Inputs/source/FRED",
        pattern = "fred_inflation.*\\.csv$",
        full.names = TRUE
    )

    if (length(files) == 0) {
        message("Warning: Inflation data not found")
        return(NULL)
    }

    dt <- fread(files[1])
    dt[, date := as.Date(date)]

    # Get CPI-U series
    cpi <- dt[series_id == "CPIAUCSL"]

    return(cpi)
}

#' Calculate real wages
#' @param wages_dt data.table with nominal wages
#' @param cpi_dt data.table with CPI data
#' @return data.table with real wage calculations
calculate_real_wages <- function(wages_dt, cpi_dt) {
    if (is.null(wages_dt) || is.null(cpi_dt)) {
        return(NULL)
    }

    # Get average hourly earnings
    ahe <- wages_dt[series_id == "AHETPI", .(date, nominal_wage = value)]

    # Get CPI and merge
    cpi <- cpi_dt[, .(date, cpi = value)]

    merged <- merge(ahe, cpi, by = "date")
    merged <- merged[order(date)]

    # Calculate real wage (indexed to latest CPI)
    latest_cpi <- merged[order(-date)][1]$cpi
    merged[, real_wage := nominal_wage * (latest_cpi / cpi)]

    # Calculate YoY growth rates
    merged[, nominal_yoy := (nominal_wage / shift(nominal_wage, 12) - 1) * 100]
    merged[, cpi_yoy := (cpi / shift(cpi, 12) - 1) * 100]
    merged[, real_yoy := nominal_yoy - cpi_yoy]

    return(merged)
}

# ============================================================================
# UI FUNCTION
# ============================================================================

wages_hours_ui <- function(id) {
    ns <- NS(id)

    tagList(
        fluidRow(
            # Value boxes
            valueBoxOutput(ns("ahe_box"), width = 3),
            valueBoxOutput(ns("real_wage_growth_box"), width = 3),
            valueBoxOutput(ns("weekly_hours_box"), width = 3),
            valueBoxOutput(ns("eci_box"), width = 3)
        ),
        fluidRow(
            # Nominal vs Real Wage Growth
            box(
                title = "Wage Growth: Nominal vs Real (YoY %)",
                status = "primary",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("wage_growth_chart"), height = "350px"),
                helpText("Real wage growth = Nominal wage growth - CPI inflation")
            ),

            # Average Hourly Earnings Level
            box(
                title = "Average Hourly Earnings: Total Private ($/hr)",
                status = "primary",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("ahe_level_chart"), height = "350px"),
                helpText("Nominal average hourly earnings for all private employees")
            )
        ),
        fluidRow(
            # Weekly Hours
            box(
                title = "Average Weekly Hours",
                status = "info",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("hours_chart"), height = "350px"),
                helpText("Total private sector and manufacturing hours")
            ),

            # Wage-Price Dynamics
            box(
                title = "Wage Growth vs Inflation",
                status = "info",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("wage_inflation_chart"), height = "350px"),
                helpText("Comparing wage growth to CPI inflation (wage-price dynamics)")
            )
        ),

        # Data source attribution
        fluidRow(
            box(
                width = 12,
                status = "info",
                solidHeader = FALSE,
                tags$div(
                    style = "font-size: 11px; color: #666;",
                    tags$strong("Data Sources: "),
                    "Bureau of Labor Statistics via FRED API. ",
                    "AHETPI = Average Hourly Earnings: Total Private. ",
                    "Real wages calculated using CPI-U (CPIAUCSL) deflator indexed to current period."
                )
            )
        )
    )
}

# ============================================================================
# SERVER FUNCTION
# ============================================================================

wages_hours_server <- function(id) {
    moduleServer(id, function(input, output, session) {
        # Load data
        wages_data <- reactive({
            load_wages_data()
        })

        cpi_data <- reactive({
            load_cpi_for_wages()
        })

        real_wages <- reactive({
            calculate_real_wages(wages_data(), cpi_data())
        })

        # ========================================================================
        # VALUE BOXES
        # ========================================================================

        output$ahe_box <- renderValueBox({
            dt <- wages_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "Avg Hourly Earnings", icon = icon("dollar-sign"), color = "green")
            } else {
                ahe <- dt[series_id == "AHETPI"][order(-date)][1]
                if (nrow(ahe) == 0 || is.na(ahe$value)) {
                    valueBox("N/A", "Avg Hourly Earnings", icon = icon("dollar-sign"), color = "green")
                } else {
                    valueBox(
                        paste0("$", round(ahe$value, 2)),
                        paste0("Avg Hourly Earnings (", format(ahe$date, "%b %Y"), ")"),
                        icon = icon("dollar-sign"),
                        color = "green"
                    )
                }
            }
        })

        output$real_wage_growth_box <- renderValueBox({
            dt <- real_wages()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "Real Wage Growth", icon = icon("chart-line"), color = "blue")
            } else {
                latest <- dt[order(-date)][1]
                if (is.na(latest$real_yoy)) {
                    valueBox("N/A", "Real Wage Growth", icon = icon("chart-line"), color = "blue")
                } else {
                    color <- if (latest$real_yoy > 0) "green" else "red"
                    valueBox(
                        paste0(sprintf("%+.1f", latest$real_yoy), "%"),
                        "Real Wage Growth (YoY)",
                        icon = icon("chart-line"),
                        color = color
                    )
                }
            }
        })

        output$weekly_hours_box <- renderValueBox({
            dt <- wages_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "Weekly Hours", icon = icon("clock"), color = "purple")
            } else {
                hours <- dt[series_id == "AWHAETP"][order(-date)][1]
                if (nrow(hours) == 0 || is.na(hours$value)) {
                    valueBox("N/A", "Weekly Hours", icon = icon("clock"), color = "purple")
                } else {
                    valueBox(
                        round(hours$value, 1),
                        "Avg Weekly Hours (Private)",
                        icon = icon("clock"),
                        color = "purple"
                    )
                }
            }
        })

        output$eci_box <- renderValueBox({
            dt <- wages_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "ECI Wages", icon = icon("chart-bar"), color = "yellow")
            } else {
                eci <- dt[series_id == "ECIWAG"][order(-date)][1]
                if (nrow(eci) == 0 || is.na(eci$value)) {
                    valueBox("N/A", "ECI Wages", icon = icon("chart-bar"), color = "yellow")
                } else {
                    valueBox(
                        round(eci$value, 1),
                        "Employment Cost Index (Wages)",
                        icon = icon("chart-bar"),
                        color = "yellow"
                    )
                }
            }
        })

        # ========================================================================
        # WAGE GROWTH CHART (Nominal vs Real)
        # ========================================================================

        output$wage_growth_chart <- renderEcharts4r({
            dt <- real_wages()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            # Filter to valid data
            plot_data <- dt[!is.na(real_yoy)]

            chart <- plot_data %>%
                e_charts(date) %>%
                e_line(nominal_yoy,
                    name = "Nominal Wage Growth",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#3498db")
                ) %>%
                e_line(real_yoy,
                    name = "Real Wage Growth",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#27ae60")
                ) %>%
                e_mark_line(
                    data = list(yAxis = 0),
                    lineStyle = list(type = "dashed", color = "#e74c3c")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "YoY Change (%)") %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 70, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })

        # ========================================================================
        # AVERAGE HOURLY EARNINGS LEVEL CHART
        # ========================================================================

        output$ahe_level_chart <- renderEcharts4r({
            dt <- wages_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            ahe <- dt[series_id == "AHETPI"]

            if (nrow(ahe) == 0) {
                return(e_charts() %>% e_title("No AHE data available"))
            }

            chart <- ahe %>%
                e_charts(date) %>%
                e_line(value,
                    name = "Avg Hourly Earnings ($/hr)",
                    lineStyle = list(width = 2),
                    areaStyle = list(opacity = 0.3),
                    itemStyle = list(color = "#27ae60")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "$/hr", min = 0) %>%
                e_tooltip(
                    trigger = "axis",
                    formatter = htmlwidgets::JS("
                    function(params) {
                      return params[0].axisValueLabel + '<br/>' +
                             '$' + params[0].value[1].toFixed(2) + '/hr';
                    }
                  ")
                ) %>%
                e_legend(show = FALSE) %>%
                e_datazoom(type = "slider", start = 50, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })

        # ========================================================================
        # WEEKLY HOURS CHART
        # ========================================================================

        output$hours_chart <- renderEcharts4r({
            dt <- wages_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            # Get both hours series
            hours_private <- dt[series_id == "AWHAETP", .(date, hours_private = value)]
            hours_mfg <- dt[series_id == "AWHI", .(date, hours_mfg = value)]

            combined <- merge(hours_private, hours_mfg, by = "date", all = TRUE)
            combined <- combined[order(date)]

            chart <- combined %>%
                e_charts(date) %>%
                e_line(hours_private,
                    name = "Total Private",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#3498db")
                ) %>%
                e_line(hours_mfg,
                    name = "Manufacturing",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#9b59b6")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "Hours/Week") %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 70, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })

        # ========================================================================
        # WAGE VS INFLATION CHART
        # ========================================================================

        output$wage_inflation_chart <- renderEcharts4r({
            dt <- real_wages()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            plot_data <- dt[!is.na(nominal_yoy) & !is.na(cpi_yoy)]

            chart <- plot_data %>%
                e_charts(date) %>%
                e_line(nominal_yoy,
                    name = "Wage Growth (YoY)",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#27ae60")
                ) %>%
                e_line(cpi_yoy,
                    name = "CPI Inflation (YoY)",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#e74c3c")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "YoY Change (%)") %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 70, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })
    })
}
