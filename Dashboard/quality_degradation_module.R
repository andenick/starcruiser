# ============================================================================
# QUALITY DEGRADATION MODULE - StarCruiser Dashboard
# ============================================================================
# Track A2.1: Visualize 2025 data quality crisis
# Features: Response rate trends, policy event timeline, quality tier distribution
# Data: Outputs/QUALITY/response_rate_timeline.csv, policy_events.csv
# ============================================================================

# UI
quality_degradation_ui <- function(id) {
  ns <- NS(id)
  tagList(
    # Value boxes
    fluidRow(
      valueBoxOutput(ns("vbox_ces_rate"), width = 4),
      valueBoxOutput(ns("vbox_cps_rate"), width = 4),
      valueBoxOutput(ns("vbox_unfilled"), width = 4)
    ),

    # Response rate chart
    fluidRow(
      box(
        title = "Survey Response Rate Trends",
        echarts4rOutput(ns("response_rate_chart"), height = "400px"),
        helpText("Lower response rates mean more data is imputed (estimated) rather than observed."),
        width = 12, solidHeader = TRUE, status = "danger"
      )
    ),

    # Policy timeline
    fluidRow(
      box(
        title = "Policy Events Impacting Data Quality",
        echarts4rOutput(ns("policy_timeline"), height = "300px"),
        width = 8, solidHeader = TRUE, status = "warning"
      ),
      box(
        title = "Current Quality Tier Distribution",
        echarts4rOutput(ns("tier_pie"), height = "300px"),
        width = 4, solidHeader = TRUE, status = "info"
      )
    ),

    # Events table
    fluidRow(
      box(
        title = "Policy Event Details",
        DTOutput(ns("events_table")),
        width = 12, solidHeader = TRUE, status = "info",
        collapsible = TRUE, collapsed = TRUE
      )
    )
  )
}

# SERVER
quality_degradation_server <- function(id) {
  moduleServer(id, function(input, output, session) {

    # Load response rate data
    response_data <- reactive({
      path <- file.path(Sys.getenv("OUTPUT_ROOT", "outputs"), "QUALITY/response_rate_timeline.csv")
      if (!file.exists(path)) return(NULL)
      dt <- fread(path)
      dt[, date := as.Date(date)]
      dt
    })

    # Load policy events
    events_data <- reactive({
      path <- file.path(Sys.getenv("OUTPUT_ROOT", "outputs"), "QUALITY/policy_events.csv")
      if (!file.exists(path)) return(NULL)
      dt <- fread(path)
      dt[, date := as.Date(date)]
      dt
    })

    # Value boxes
    output$vbox_ces_rate <- renderValueBox({
      dt <- response_data()
      if (is.null(dt)) {
        return(valueBox("N/A", "CES Response Rate", icon = icon("chart-line"), color = "gray"))
      }

      latest <- dt[survey == "CES" & !is.na(response_rate)][order(-date)][1]
      if (nrow(latest) == 0) {
        return(valueBox("N/A", "CES Response Rate", icon = icon("chart-line"), color = "gray"))
      }

      color <- if (latest$response_rate < 50) "red" else if (latest$response_rate < 60) "yellow" else "green"
      valueBox(
        value = paste0(latest$response_rate, "%"),
        subtitle = paste("CES Response Rate -", latest$date),
        icon = icon("chart-line"),
        color = color
      )
    })

    output$vbox_cps_rate <- renderValueBox({
      dt <- response_data()
      if (is.null(dt)) {
        return(valueBox("N/A", "CPS Response Rate", icon = icon("users"), color = "gray"))
      }

      latest <- dt[survey == "CPS" & !is.na(response_rate)][order(-date)][1]
      if (nrow(latest) == 0) {
        return(valueBox("N/A", "CPS Response Rate", icon = icon("users"), color = "gray"))
      }

      color <- if (latest$response_rate < 65) "red" else if (latest$response_rate < 75) "yellow" else "green"
      valueBox(
        value = paste0(latest$response_rate, "%"),
        subtitle = paste("CPS Response Rate -", latest$date),
        icon = icon("users"),
        color = color
      )
    })

    output$vbox_unfilled <- renderValueBox({
      valueBox(
        value = "1,300+",
        subtitle = "BLS Unfilled Positions",
        icon = icon("user-slash"),
        color = "red"
      )
    })

    # Response rate chart
    output$response_rate_chart <- renderEcharts4r({
      dt <- response_data()
      if (is.null(dt)) {
        return(data.table(x = 1, y = 1) %>% e_charts(x) %>%
          e_text(y, text = "No data. Run extract_quality_metrics.py first."))
      }

      dt_plot <- dt[!is.na(response_rate)]

      chart <- dt_plot %>%
        group_by(survey) %>%
        e_charts(date) %>%
        e_line(response_rate, symbol = "circle", symbolSize = 6, sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Response Rate (%)", min = 30, max = 90) %>%
        e_mark_line(
          data = list(yAxis = 50),
          lineStyle = list(color = "#dd4b39", type = "dashed"),
          label = list(formatter = "Critical: 50%")
        )

      add_recession_bands(chart)
    })

    # Policy timeline
    output$policy_timeline <- renderEcharts4r({
      dt <- events_data()
      if (is.null(dt)) return(NULL)

      # Map impact to size
      dt[, size := fifelse(impact == "HIGH", 20, fifelse(impact == "MEDIUM", 12, 8))]
      dt[, color := fifelse(impact == "HIGH", "#dd4b39", fifelse(impact == "MEDIUM", "#f39c12", "#3c8dbc"))]

      # Create a y-value based on category for visual spread
      cat_y <- c(Shutdown = 4, Staffing = 3, Budget = 2, `Data Quality` = 1,
                 `Executive Order` = 2, Election = 3, Inauguration = 4, Methodology = 1,
                 `Data Gap` = 1)
      dt[, y_val := sapply(category, function(c) {
        if (c %in% names(cat_y)) cat_y[c] else 2
      })]

      dt %>%
        e_charts(date) %>%
        e_scatter(y_val, symbol_size = size) %>%
        e_tooltip(
          formatter = htmlwidgets::JS("
            function(params) {
              return params.value[0] + '<br><strong>' +
                     params.data.event + '</strong><br>' +
                     'Impact: ' + params.data.impact;
            }
          ")
        ) %>%
        e_y_axis(show = FALSE, min = 0, max = 5) %>%
        e_x_axis(name = "Date") %>%
        e_legend(show = FALSE)
    })

    # Quality tier pie chart
    output$tier_pie <- renderEcharts4r({
      tier_data <- data.table(
        tier = c("Tier 1 (Official)", "Tier 2 (Pre-2025)", "Tier 3 (2025 Survey)", "Tier 4 (Experimental)"),
        count = c(15, 8, 5, 3)
      )

      tier_data %>%
        e_charts(tier) %>%
        e_pie(count, radius = c("40%", "70%")) %>%
        e_tooltip() %>%
        e_legend(orient = "vertical", right = "5%", top = "20%") %>%
        e_color(c("#00a65a", "#3c8dbc", "#f39c12", "#dd4b39"))
    })

    # Events table
    output$events_table <- renderDT({
      dt <- events_data()
      if (is.null(dt)) return(NULL)

      datatable(
        dt[order(-date)],
        options = list(pageLength = 15, dom = "ft"),
        rownames = FALSE
      ) %>%
        formatStyle("impact",
          backgroundColor = styleEqual(
            c("HIGH", "MEDIUM", "LOW"),
            c("#f2dede", "#fcf8e3", "#dff0d8")
          )
        )
    })
  })
}
