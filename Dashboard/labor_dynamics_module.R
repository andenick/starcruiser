# ============================================================================
# LABOR DYNAMICS MODULE - StarCruiser Dashboard
# ============================================================================
# Purpose: Labor market dynamics analysis visualizations
# Features:
#   - Beveridge Curve (job openings vs unemployment)
#   - V/U Ratio (labor market tightness)
#   - Labor market flows (hires, quits, separations)
#   - HP filter trend/cycle decomposition
#   - Rolling correlations
# ============================================================================

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

#' Load Beveridge curve data
#' @return data.table with Beveridge curve data
load_beveridge_data <- function() {
    path <- "../Outputs/LABOR_DYNAMICS/beveridge_curve_data.csv"

    if (!file.exists(path)) {
        message("Warning: Beveridge curve data not found at ", path)
        return(NULL)
    }

    dt <- fread(path)
    dt[, date := as.Date(date)]

    return(dt)
}

#' Load labor market flows data
#' @return data.table with flows data
load_labor_flows <- function() {
    path <- "../Outputs/LABOR_DYNAMICS/labor_market_flows.csv"

    if (!file.exists(path)) {
        message("Warning: Labor flows data not found at ", path)
        return(NULL)
    }

    dt <- fread(path)
    dt[, date := as.Date(date)]

    return(dt)
}

#' Load HP decomposition data
#' @return data.table with trend/cycle decomposition
load_hp_decomposition <- function() {
    path <- "../Outputs/LABOR_DYNAMICS/employment_hp_decomposition.csv"

    if (!file.exists(path)) {
        message("Warning: HP decomposition data not found at ", path)
        return(NULL)
    }

    dt <- fread(path)
    dt[, date := as.Date(date)]

    return(dt)
}

#' Load rolling correlations data
#' @return data.table with correlations
load_rolling_correlations <- function() {
    path <- "../Outputs/LABOR_DYNAMICS/rolling_correlations.csv"

    if (!file.exists(path)) {
        message("Warning: Rolling correlations data not found at ", path)
        return(NULL)
    }

    dt <- fread(path)
    dt[, date := as.Date(date)]

    return(dt)
}

# ============================================================================
# UI FUNCTION
# ============================================================================

labor_dynamics_ui <- function(id) {
    ns <- NS(id)

    tagList(
        fluidRow(
            # Value boxes row
            valueBoxOutput(ns("vu_ratio_box"), width = 3),
            valueBoxOutput(ns("vacancy_rate_box"), width = 3),
            valueBoxOutput(ns("quits_rate_box"), width = 3),
            valueBoxOutput(ns("hires_rate_box"), width = 3)
        ),
        fluidRow(
            # Beveridge Curve
            box(
                title = "Beveridge Curve: Job Openings vs Unemployment",
                status = "primary",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("beveridge_chart"), height = "400px"),
                helpText("Labor market matching efficiency. Outward shifts indicate structural changes.")
            ),

            # V/U Ratio over time
            box(
                title = "Labor Market Tightness (V/U Ratio)",
                status = "primary",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("vu_ratio_chart"), height = "400px"),
                helpText("Ratio > 1: More openings than unemployed (tight). < 1: More slack.")
            )
        ),
        fluidRow(
            # Labor flows
            box(
                title = "Labor Market Flows",
                status = "info",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("flows_chart"), height = "350px"),
                helpText("Monthly hiring and separation rates. Quits indicate worker confidence.")
            ),

            # Quits vs Layoffs
            box(
                title = "Separations Breakdown: Quits vs Layoffs",
                status = "info",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("separations_chart"), height = "350px"),
                helpText("Voluntary (quits) vs involuntary (layoffs) separations.")
            )
        ),
        fluidRow(
            # HP Filter decomposition
            box(
                title = "Employment Trend/Cycle Decomposition (HP Filter)",
                status = "warning",
                solidHeader = TRUE,
                width = 6,
                selectInput(ns("hp_series"), "Select Series:",
                    choices = c(
                        "Unemployment Rate" = "UNRATE",
                        "Employment-Pop Ratio" = "EMRATIO",
                        "Labor Force Participation" = "CIVPART",
                        "Nonfarm Payrolls" = "PAYEMS"
                    ),
                    selected = "UNRATE"
                ),
                echarts4rOutput(ns("hp_chart"), height = "300px"),
                helpText("HP filter separates long-term trend from cyclical fluctuations.")
            ),

            # Rolling correlations
            box(
                title = "Rolling Correlations with Unemployment (24-month window)",
                status = "warning",
                solidHeader = TRUE,
                width = 6,
                echarts4rOutput(ns("correlation_chart"), height = "350px"),
                helpText("Time-varying correlations between unemployment and labor market indicators.")
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
                    "BLS Job Openings and Labor Turnover Survey (JOLTS) via FRED API. ",
                    "Unemployment and employment data from Bureau of Labor Statistics. ",
                    tags$br(),
                    tags$strong("Note: "),
                    "V/U ratio = Job Openings Rate / Unemployment Rate. ",
                    "HP filter uses λ=129,600 for monthly data (Ravn-Uhlig recommendation)."
                )
            )
        )
    )
}

# ============================================================================
# SERVER FUNCTION
# ============================================================================

labor_dynamics_server <- function(id) {
    moduleServer(id, function(input, output, session) {
        # Load data
        beveridge_data <- reactive({
            load_beveridge_data()
        })

        flows_data <- reactive({
            load_labor_flows()
        })

        hp_data <- reactive({
            load_hp_decomposition()
        })

        correlation_data <- reactive({
            load_rolling_correlations()
        })

        # ========================================================================
        # VALUE BOXES
        # ========================================================================

        output$vu_ratio_box <- renderValueBox({
            dt <- beveridge_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "V/U Ratio", icon = icon("chart-line"), color = "blue")
            } else {
                latest <- dt[order(-date)][1]
                ratio <- round(latest$vu_ratio, 2)

                color <- if (ratio > 1.2) "green" else if (ratio < 0.8) "red" else "yellow"

                valueBox(
                    ratio,
                    paste0("V/U Ratio (", format(latest$date, "%b %Y"), ")"),
                    icon = icon("balance-scale"),
                    color = color
                )
            }
        })

        output$vacancy_rate_box <- renderValueBox({
            dt <- beveridge_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "Vacancy Rate", icon = icon("briefcase"), color = "blue")
            } else {
                latest <- dt[order(-date)][1]
                valueBox(
                    paste0(round(latest$vacancy_rate, 1), "%"),
                    paste0("Job Openings Rate"),
                    icon = icon("briefcase"),
                    color = "blue"
                )
            }
        })

        output$quits_rate_box <- renderValueBox({
            dt <- flows_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "Quits Rate", icon = icon("walking"), color = "purple")
            } else {
                latest <- dt[order(-date)][1]
                valueBox(
                    paste0(round(latest$quits_rate, 1), "%"),
                    "Quits Rate (Worker Confidence)",
                    icon = icon("walking"),
                    color = "purple"
                )
            }
        })

        output$hires_rate_box <- renderValueBox({
            dt <- flows_data()
            if (is.null(dt) || nrow(dt) == 0) {
                valueBox("N/A", "Hires Rate", icon = icon("user-plus"), color = "green")
            } else {
                latest <- dt[order(-date)][1]
                valueBox(
                    paste0(round(latest$hires_rate, 1), "%"),
                    "Hires Rate",
                    icon = icon("user-plus"),
                    color = "green"
                )
            }
        })

        # ========================================================================
        # BEVERIDGE CURVE CHART
        # ========================================================================

        output$beveridge_chart <- renderEcharts4r({
            dt <- beveridge_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            # Color by year for trajectory visualization
            dt[, year_group := cut(year,
                breaks = c(2000, 2007, 2010, 2015, 2020, 2022, 2026),
                labels = c(
                    "2001-2007", "2008-2010", "2011-2015",
                    "2016-2020", "2021-2022", "2023-2025"
                ),
                include.lowest = TRUE
            )]

            dt %>%
                e_charts(unemployment_rate) %>%
                e_scatter(vacancy_rate,
                    symbol_size = 8,
                    itemStyle = list(opacity = 0.7)
                ) %>%
                e_visual_map(year,
                    inRange = list(color = c("#3498db", "#2ecc71", "#f39c12", "#e74c3c")),
                    dimension = 0,
                    show = TRUE,
                    right = 10,
                    top = 50
                ) %>%
                e_x_axis(name = "Unemployment Rate (%)", nameLocation = "center", nameGap = 30) %>%
                e_y_axis(name = "Job Openings Rate (%)", nameLocation = "center", nameGap = 40) %>%
                e_tooltip(
                    formatter = htmlwidgets::JS("
            function(params) {
              return 'Unemployment: ' + params.value[0].toFixed(1) + '%<br/>' +
                     'Openings: ' + params.value[1].toFixed(1) + '%<br/>' +
                     'Year: ' + params.value[2];
            }
          ")
                ) %>%
                e_legend(show = FALSE) %>%
                e_grid(left = "15%", right = "15%", bottom = "15%") %>%
                e_toolbox_feature(feature = "saveAsImage")
        })

        # ========================================================================
        # V/U RATIO CHART
        # ========================================================================

        output$vu_ratio_chart <- renderEcharts4r({
            dt <- beveridge_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            chart <- dt %>%
                e_charts(date) %>%
                e_line(vu_ratio,
                    name = "V/U Ratio", smooth = TRUE,
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#3498db")
                ) %>%
                e_mark_line(
                    data = list(yAxis = 1),
                    label = list(formatter = "Balance (V/U = 1)", position = "end"),
                    lineStyle = list(type = "dashed", color = "#e74c3c")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "V/U Ratio", min = 0) %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(show = FALSE) %>%
                e_datazoom(type = "slider", start = 50, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            # Add recession shading
            add_recession_bands(chart)
        })

        # ========================================================================
        # LABOR FLOWS CHART
        # ========================================================================

        output$flows_chart <- renderEcharts4r({
            dt <- flows_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            chart <- dt %>%
                e_charts(date) %>%
                e_line(hires_rate,
                    name = "Hires Rate", smooth = TRUE,
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#27ae60")
                ) %>%
                e_line(separations_rate,
                    name = "Separations Rate", smooth = TRUE,
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#e74c3c")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "Rate (%)", min = 0) %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 70, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })

        # ========================================================================
        # SEPARATIONS BREAKDOWN CHART
        # ========================================================================

        output$separations_chart <- renderEcharts4r({
            dt <- flows_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            chart <- dt %>%
                e_charts(date) %>%
                e_area(quits_rate,
                    name = "Quits (Voluntary)", stack = "sep",
                    areaStyle = list(opacity = 0.7),
                    itemStyle = list(color = "#9b59b6")
                ) %>%
                e_area(layoffs_rate,
                    name = "Layoffs (Involuntary)", stack = "sep",
                    areaStyle = list(opacity = 0.7),
                    itemStyle = list(color = "#e74c3c")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "Rate (%)", min = 0) %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 70, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })

        # ========================================================================
        # HP FILTER DECOMPOSITION CHART
        # ========================================================================

        output$hp_chart <- renderEcharts4r({
            dt <- hp_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            series <- input$hp_series
            plot_data <- dt[series_id == series]

            if (nrow(plot_data) == 0) {
                return(e_charts() %>% e_title("No data for selected series"))
            }

            plot_data %>%
                e_charts(date) %>%
                e_line(value,
                    name = "Actual",
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#3498db")
                ) %>%
                e_line(trend,
                    name = "Trend (HP)",
                    lineStyle = list(width = 2, type = "dashed"),
                    itemStyle = list(color = "#e74c3c")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = series) %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 60, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")
        })

        # ========================================================================
        # ROLLING CORRELATION CHART
        # ========================================================================

        output$correlation_chart <- renderEcharts4r({
            dt <- correlation_data()
            if (is.null(dt) || nrow(dt) == 0) {
                return(e_charts() %>% e_title("No data available"))
            }

            chart <- dt %>%
                e_charts(date) %>%
                e_line(UNRATE_vs_JTSJOR,
                    name = "vs Job Openings", smooth = TRUE,
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#3498db")
                ) %>%
                e_line(UNRATE_vs_JTSQUR,
                    name = "vs Quits Rate", smooth = TRUE,
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#9b59b6")
                ) %>%
                e_line(UNRATE_vs_ICSA,
                    name = "vs Initial Claims", smooth = TRUE,
                    lineStyle = list(width = 2),
                    itemStyle = list(color = "#e74c3c")
                ) %>%
                e_mark_line(
                    data = list(yAxis = 0),
                    lineStyle = list(type = "dashed", color = "#95a5a6")
                ) %>%
                e_x_axis(type = "time") %>%
                e_y_axis(name = "Correlation", min = -1, max = 1) %>%
                e_tooltip(trigger = "axis") %>%
                e_legend(top = 5) %>%
                e_datazoom(type = "slider", start = 50, end = 100) %>%
                e_toolbox_feature(feature = "saveAsImage")

            add_recession_bands(chart)
        })
    })
}
