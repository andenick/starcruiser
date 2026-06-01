# ============================================================================
# GDP & OUTPUT MODULE - StarCruiser Dashboard v7.0
# ============================================================================
# Real GDP growth, industrial production, capacity utilization, GDP components
# Data: fred_gdp_growth, fred_production
# ============================================================================

gdp_output_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_gdp_growth"), width = 3),
      valueBoxOutput(ns("vbox_indpro"), width = 3),
      valueBoxOutput(ns("vbox_caputil"), width = 3),
      valueBoxOutput(ns("vbox_gdp_deflator"), width = 3)
    ),
    fluidRow(
      box(title = "Real GDP Growth (Quarterly, Annualized)",
          echarts4rOutput(ns("gdp_growth_chart"), height = "400px"),
          width = 12, solidHeader = TRUE, status = "primary")
    ),
    fluidRow(
      box(title = "GDP Components",
          echarts4rOutput(ns("gdp_components_chart"), height = "400px"),
          helpText("PCE = Consumption, GPDI = Investment, GCE = Government, NETEXP = Net Exports"),
          width = 12, solidHeader = TRUE, status = "info")
    ),
    fluidRow(
      box(title = "Industrial Production Index",
          echarts4rOutput(ns("indpro_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "success"),
      box(title = "Capacity Utilization",
          echarts4rOutput(ns("caputil_chart"), height = "350px"),
          helpText("80%+ threshold historically signals inflationary pressure"),
          width = 6, solidHeader = TRUE, status = "warning")
    ),
    fluidRow(
      box(title = "Download Data", width = 12,
          downloadButton(ns("download_gdp"), "Download GDP & Output Data (CSV)", icon = icon("download")))
    )
  )
}

gdp_output_server <- function(id, gdp_data, production_data, date_range) {
  moduleServer(id, function(input, output, session) {

    gdp_filtered <- reactive({
      req(gdp_data)
      dr <- date_range()
      gdp_data[date >= dr[1] & date <= dr[2]]
    })

    prod_filtered <- reactive({
      req(production_data)
      dr <- date_range()
      production_data[date >= dr[1] & date <= dr[2]]
    })

    output$vbox_gdp_growth <- renderValueBox({
      if (is.null(gdp_data)) return(valueBox("N/A", "GDP Growth", icon = icon("chart-bar"), color = "gray"))
      latest <- gdp_data[series_id == "A191RL1Q225SBEA"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "GDP Growth", icon = icon("chart-bar"), color = "gray"))
      color <- if (latest$value > 2) "green" else if (latest$value > 0) "yellow" else "red"
      valueBox(paste0(round(latest$value, 1), "%"), paste("GDP Growth (QoQ ann.) -", latest$date),
               icon = icon("chart-bar"), color = color)
    })

    output$vbox_indpro <- renderValueBox({
      if (is.null(production_data)) return(valueBox("N/A", "Industrial Production", icon = icon("industry"), color = "gray"))
      latest <- production_data[series_id == "INDPRO"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Industrial Production", icon = icon("industry"), color = "gray"))
      valueBox(round(latest$value, 1), paste("INDPRO Index -", latest$date),
               icon = icon("industry"), color = "blue")
    })

    output$vbox_caputil <- renderValueBox({
      if (is.null(production_data)) return(valueBox("N/A", "Capacity Utilization", icon = icon("tachometer-alt"), color = "gray"))
      latest <- production_data[series_id == "TCU"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Capacity Utilization", icon = icon("tachometer-alt"), color = "gray"))
      color <- if (latest$value > 80) "red" else if (latest$value > 75) "yellow" else "green"
      valueBox(paste0(round(latest$value, 1), "%"), paste("Capacity Util -", latest$date),
               icon = icon("tachometer-alt"), color = color)
    })

    output$vbox_gdp_deflator <- renderValueBox({
      if (is.null(gdp_data)) return(valueBox("N/A", "GDP Deflator", icon = icon("dollar-sign"), color = "gray"))
      latest <- gdp_data[series_id == "GDPDEF"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "GDP Deflator", icon = icon("dollar-sign"), color = "gray"))
      valueBox(round(latest$value, 1), paste("GDP Deflator -", latest$date),
               icon = icon("dollar-sign"), color = "purple")
    })

    output$gdp_growth_chart <- renderEcharts4r({
      dt <- gdp_filtered()[series_id == "A191RL1Q225SBEA"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      dt[, color := ifelse(value >= 0, "#00a65a", "#dd4b39")]
      chart <- dt %>%
        e_charts(date) %>%
        e_bar(value, itemStyle = list(color = htmlwidgets::JS("
          function(params) { return params.value[1] >= 0 ? '#00a65a' : '#dd4b39'; }
        ")), name = "GDP Growth %") %>%
        e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "#333")) %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Annualized % Change") %>%
        e_legend(show = FALSE)
      add_recession_bands(chart, date_range())
    })

    output$gdp_components_chart <- renderEcharts4r({
      dt <- gdp_filtered()[series_id %chin% c("PCEC", "GPDI", "GCE", "NETEXP")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Billions $")
      add_recession_bands(chart, date_range())
    })

    output$indpro_chart <- renderEcharts4r({
      dt <- prod_filtered()[series_id %chin% c("INDPRO", "IPMAN")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Index (2017=100)")
      add_recession_bands(chart, date_range())
    })

    output$caputil_chart <- renderEcharts4r({
      dt <- prod_filtered()[series_id %chin% c("TCU", "MCUMFN")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_mark_line(data = list(yAxis = 80), lineStyle = list(color = "#dd4b39", type = "dashed"),
                    label = list(formatter = "Inflationary: 80%")) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Percent")
      add_recession_bands(chart, date_range())
    })

    output$download_gdp <- downloadHandler(
      filename = function() paste0("StarCruiser_GDP_Output_", Sys.Date(), ".csv"),
      content = function(file) {
        combined <- rbindlist(list(gdp_filtered(), prod_filtered()), fill = TRUE)
        fwrite(combined, file)
      }
    )
  })
}
