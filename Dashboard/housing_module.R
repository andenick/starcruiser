# ============================================================================
# HOUSING MARKET MODULE - StarCruiser Dashboard v7.0
# ============================================================================
# Housing starts, building permits, Case-Shiller, new home sales, inventory
# Data: fred_housing
# ============================================================================

housing_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_starts"), width = 3),
      valueBoxOutput(ns("vbox_permits"), width = 3),
      valueBoxOutput(ns("vbox_caseshiller"), width = 3),
      valueBoxOutput(ns("vbox_supply"), width = 3)
    ),
    fluidRow(
      box(title = "Housing Starts (Annualized, Thousands)",
          echarts4rOutput(ns("starts_chart"), height = "400px"),
          helpText("Leading indicator: declines 12-18 months before recessions"),
          width = 12, solidHeader = TRUE, status = "primary")
    ),
    fluidRow(
      box(title = "Building Permits (Leading Indicator)",
          echarts4rOutput(ns("permits_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "info"),
      box(title = "Case-Shiller Home Price Index",
          echarts4rOutput(ns("caseshiller_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "success")
    ),
    fluidRow(
      box(title = "New Home Sales",
          echarts4rOutput(ns("sales_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "warning"),
      box(title = "Months Supply of Homes (Inventory)",
          echarts4rOutput(ns("supply_chart"), height = "350px"),
          helpText("Low supply = tight market, high prices. High supply = buyer's market."),
          width = 6, solidHeader = TRUE, status = "danger")
    )
  )
}

housing_server <- function(id, housing_data, date_range) {
  moduleServer(id, function(input, output, session) {

    filtered <- reactive({
      req(housing_data); dr <- date_range()
      housing_data[date >= dr[1] & date <= dr[2]]
    })

    output$vbox_starts <- renderValueBox({
      if (is.null(housing_data)) return(valueBox("N/A", "Housing Starts", icon = icon("home"), color = "gray"))
      latest <- housing_data[series_id == "HOUST"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Housing Starts", icon = icon("home"), color = "gray"))
      valueBox(paste0(round(latest$value), "K"), paste("Housing Starts -", latest$date),
               icon = icon("home"), color = "blue")
    })

    output$vbox_permits <- renderValueBox({
      if (is.null(housing_data)) return(valueBox("N/A", "Building Permits", icon = icon("file-alt"), color = "gray"))
      latest <- housing_data[series_id == "PERMIT"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Building Permits", icon = icon("file-alt"), color = "gray"))
      valueBox(paste0(round(latest$value), "K"), paste("Building Permits -", latest$date),
               icon = icon("file-alt"), color = "green")
    })

    output$vbox_caseshiller <- renderValueBox({
      if (is.null(housing_data)) return(valueBox("N/A", "Home Prices", icon = icon("chart-line"), color = "gray"))
      latest <- housing_data[series_id == "CSUSHPISA"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Home Prices", icon = icon("chart-line"), color = "gray"))
      valueBox(round(latest$value, 1), paste("Case-Shiller Index -", latest$date),
               icon = icon("chart-line"), color = "purple")
    })

    output$vbox_supply <- renderValueBox({
      if (is.null(housing_data)) return(valueBox("N/A", "Months Supply", icon = icon("warehouse"), color = "gray"))
      latest <- housing_data[series_id == "MSACSR"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Months Supply", icon = icon("warehouse"), color = "gray"))
      color <- if (latest$value > 6) "red" else if (latest$value > 4) "yellow" else "green"
      valueBox(paste0(round(latest$value, 1), " mo"), paste("Months Supply -", latest$date),
               icon = icon("warehouse"), color = color)
    })

    output$starts_chart <- renderEcharts4r({
      dt <- filtered()[series_id %chin% c("HOUST", "HOUST1F", "HOUST5F")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "Thousands (Annualized)")
      add_recession_bands(chart, date_range())
    })

    output$permits_chart <- renderEcharts4r({
      dt <- filtered()[series_id == "PERMIT"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#00a65a", sampling = "lttb", name = "Building Permits") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Thousands")
      add_recession_bands(chart, date_range())
    })

    output$caseshiller_chart <- renderEcharts4r({
      dt <- filtered()[series_id == "CSUSHPISA"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#9b59b6", sampling = "lttb", name = "Case-Shiller US") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Index (Jan 2000 = 100)")
      add_recession_bands(chart, date_range())
    })

    output$sales_chart <- renderEcharts4r({
      dt <- filtered()[series_id == "HSN1F"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#f39c12", sampling = "lttb", name = "New Home Sales") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Thousands")
      add_recession_bands(chart, date_range())
    })

    output$supply_chart <- renderEcharts4r({
      dt <- filtered()[series_id == "MSACSR"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_area(value, symbol = "none", color = "#dd4b39", sampling = "lttb", name = "Months Supply") %>%
        e_mark_line(data = list(yAxis = 6), lineStyle = list(color = "#333", type = "dashed"),
                    label = list(formatter = "Balanced: 6 months")) %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Months")
      add_recession_bands(chart, date_range())
    })
  })
}
