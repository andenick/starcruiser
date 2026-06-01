# ============================================================================
# TRADE & FISCAL MODULE - StarCruiser Dashboard v7.0
# ============================================================================
# Trade balance, exchange rates, federal debt, deficit
# Data: fred_trade, fred_fiscal
# ============================================================================

trade_fiscal_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_trade_bal"), width = 3),
      valueBoxOutput(ns("vbox_usd_index"), width = 3),
      valueBoxOutput(ns("vbox_debt_gdp"), width = 3),
      valueBoxOutput(ns("vbox_deficit"), width = 3)
    ),
    fluidRow(
      box(title = "Trade Balance (Goods & Services)",
          echarts4rOutput(ns("trade_bal_chart"), height = "400px"),
          width = 12, solidHeader = TRUE, status = "primary")
    ),
    fluidRow(
      box(title = "Imports vs Exports",
          echarts4rOutput(ns("imp_exp_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "info"),
      box(title = "Exchange Rates (USD per Foreign Currency)",
          echarts4rOutput(ns("fx_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "success")
    ),
    fluidRow(
      box(title = "Trade-Weighted US Dollar Index",
          echarts4rOutput(ns("usd_index_chart"), height = "350px"),
          helpText("Rising = stronger dollar = cheaper imports, harder exports"),
          width = 6, solidHeader = TRUE, status = "warning"),
      box(title = "Federal Debt as % of GDP",
          echarts4rOutput(ns("debt_gdp_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "danger")
    ),
    fluidRow(
      box(title = "Federal Receipts vs Expenditures",
          echarts4rOutput(ns("receipts_exp_chart"), height = "350px"),
          helpText("Gap = federal deficit"),
          width = 12, solidHeader = TRUE, status = "primary")
    )
  )
}

trade_fiscal_server <- function(id, trade_data, fiscal_data, date_range) {
  moduleServer(id, function(input, output, session) {

    trade_filtered <- reactive({
      req(trade_data); dr <- date_range()
      trade_data[date >= dr[1] & date <= dr[2]]
    })

    fiscal_filtered <- reactive({
      req(fiscal_data); dr <- date_range()
      fiscal_data[date >= dr[1] & date <= dr[2]]
    })

    output$vbox_trade_bal <- renderValueBox({
      if (is.null(trade_data)) return(valueBox("N/A", "Trade Balance", icon = icon("ship"), color = "gray"))
      latest <- trade_data[series_id == "BOPGSTB"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Trade Balance", icon = icon("ship"), color = "gray"))
      color <- if (latest$value < 0) "red" else "green"
      valueBox(paste0("$", round(latest$value / 1000, 1), "B"), paste("Trade Balance -", latest$date),
               icon = icon("ship"), color = color)
    })

    output$vbox_usd_index <- renderValueBox({
      if (is.null(trade_data)) return(valueBox("N/A", "USD Index", icon = icon("dollar-sign"), color = "gray"))
      latest <- trade_data[series_id == "DTWEXBGS"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "USD Index", icon = icon("dollar-sign"), color = "gray"))
      valueBox(round(latest$value, 1), paste("Trade-Weighted USD -", latest$date),
               icon = icon("dollar-sign"), color = "blue")
    })

    output$vbox_debt_gdp <- renderValueBox({
      if (is.null(fiscal_data)) return(valueBox("N/A", "Debt/GDP", icon = icon("landmark"), color = "gray"))
      latest <- fiscal_data[series_id == "GFDEGDQ188S"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Debt/GDP", icon = icon("landmark"), color = "gray"))
      color <- if (latest$value > 100) "red" else if (latest$value > 80) "yellow" else "green"
      valueBox(paste0(round(latest$value), "%"), paste("Debt/GDP -", latest$date),
               icon = icon("landmark"), color = color)
    })

    output$vbox_deficit <- renderValueBox({
      if (is.null(fiscal_data)) return(valueBox("N/A", "Deficit/GDP", icon = icon("chart-pie"), color = "gray"))
      latest <- fiscal_data[series_id == "FYFSDFYGDP"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Deficit/GDP", icon = icon("chart-pie"), color = "gray"))
      color <- if (latest$value < -5) "red" else if (latest$value < -3) "yellow" else "green"
      valueBox(paste0(round(latest$value, 1), "%"), paste("Deficit/GDP -", latest$date),
               icon = icon("chart-pie"), color = color)
    })

    output$trade_bal_chart <- renderEcharts4r({
      dt <- trade_filtered()[series_id == "BOPGSTB"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_area(value, symbol = "none", sampling = "lttb", name = "Trade Balance",
               itemStyle = list(color = htmlwidgets::JS("
                 function(params) { return params.value[1] >= 0 ? '#00a65a' : '#dd4b39'; }
               "))) %>%
        e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "#333")) %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Millions $") %>% e_legend(show = FALSE)
      add_recession_bands(chart, date_range())
    })

    output$imp_exp_chart <- renderEcharts4r({
      dt <- trade_filtered()[series_id %chin% c("IMPGS", "EXPGS")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "Billions $")
      add_recession_bands(chart, date_range())
    })

    output$fx_chart <- renderEcharts4r({
      dt <- trade_filtered()[series_id %chin% c("DEXUSEU", "DEXJPUS", "DEXCAUS")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "USD per unit")
    })

    output$usd_index_chart <- renderEcharts4r({
      dt <- trade_filtered()[series_id == "DTWEXBGS"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#3c8dbc", sampling = "lttb", name = "TWD Index") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Index (Jan 2006 = 100)")
      add_recession_bands(chart, date_range())
    })

    output$debt_gdp_chart <- renderEcharts4r({
      dt <- fiscal_filtered()[series_id == "GFDEGDQ188S"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_area(value, symbol = "none", color = "#dd4b39", sampling = "lttb", name = "Debt/GDP") %>%
        e_mark_line(data = list(yAxis = 100), lineStyle = list(color = "#333", type = "dashed"),
                    label = list(formatter = "100% GDP")) %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Percent of GDP")
      add_recession_bands(chart, date_range())
    })

    output$receipts_exp_chart <- renderEcharts4r({
      dt <- fiscal_filtered()[series_id %chin% c("FYFR", "FYFSGDA188S")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "% of GDP")
      add_recession_bands(chart, date_range())
    })
  })
}
