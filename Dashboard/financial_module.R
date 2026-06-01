# ============================================================================
# FINANCIAL CONDITIONS MODULE - StarCruiser Dashboard v7.0
# ============================================================================
# VIX, corporate bond spreads, financial conditions indices, M2, Fed balance sheet
# Data: fred_financial_stress, fred_money_banking
# ============================================================================

financial_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_vix"), width = 3),
      valueBoxOutput(ns("vbox_hy_spread"), width = 3),
      valueBoxOutput(ns("vbox_nfci"), width = 3),
      valueBoxOutput(ns("vbox_m2"), width = 3)
    ),
    fluidRow(
      box(title = "VIX Volatility Index (Fear Gauge)",
          echarts4rOutput(ns("vix_chart"), height = "400px"),
          helpText("<15 Calm | 15-25 Elevated | 25-35 Stressed | >35 Panic"),
          width = 12, solidHeader = TRUE, status = "danger")
    ),
    fluidRow(
      box(title = "Corporate Bond Spreads",
          echarts4rOutput(ns("spreads_chart"), height = "350px"),
          helpText("High yield spread widens during stress; narrows during risk-on"),
          width = 6, solidHeader = TRUE, status = "warning"),
      box(title = "Financial Conditions Indices",
          echarts4rOutput(ns("fci_chart"), height = "350px"),
          helpText("Positive = tighter than average; Negative = looser than average"),
          width = 6, solidHeader = TRUE, status = "info")
    ),
    fluidRow(
      box(title = "Money Supply (M1 & M2)",
          echarts4rOutput(ns("money_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "primary"),
      box(title = "Federal Reserve Balance Sheet (Total Assets)",
          echarts4rOutput(ns("fed_bs_chart"), height = "350px"),
          helpText("Rises during QE, falls during QT"),
          width = 6, solidHeader = TRUE, status = "success")
    ),
    fluidRow(
      box(title = "Bank Lending",
          echarts4rOutput(ns("lending_chart"), height = "350px"),
          width = 12, solidHeader = TRUE, status = "primary")
    )
  )
}

financial_server <- function(id, financial_data, money_data, date_range) {
  moduleServer(id, function(input, output, session) {

    fin_filtered <- reactive({
      req(financial_data); dr <- date_range()
      financial_data[date >= dr[1] & date <= dr[2]]
    })

    money_filtered <- reactive({
      req(money_data); dr <- date_range()
      money_data[date >= dr[1] & date <= dr[2]]
    })

    output$vbox_vix <- renderValueBox({
      if (is.null(financial_data)) return(valueBox("N/A", "VIX", icon = icon("heartbeat"), color = "gray"))
      latest <- financial_data[series_id == "VIXCLS"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "VIX", icon = icon("heartbeat"), color = "gray"))
      color <- if (latest$value > 35) "red" else if (latest$value > 25) "orange"
               else if (latest$value > 15) "yellow" else "green"
      valueBox(round(latest$value, 1), paste("VIX -", latest$date),
               icon = icon("heartbeat"), color = color)
    })

    output$vbox_hy_spread <- renderValueBox({
      if (is.null(financial_data)) return(valueBox("N/A", "HY Spread", icon = icon("chart-area"), color = "gray"))
      latest <- financial_data[series_id == "BAMLH0A0HYM2"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "HY Spread", icon = icon("chart-area"), color = "gray"))
      color <- if (latest$value > 6) "red" else if (latest$value > 4) "yellow" else "green"
      valueBox(paste0(round(latest$value, 2), "%"), paste("HY Spread -", latest$date),
               icon = icon("chart-area"), color = color)
    })

    output$vbox_nfci <- renderValueBox({
      if (is.null(financial_data)) return(valueBox("N/A", "NFCI", icon = icon("balance-scale"), color = "gray"))
      latest <- financial_data[series_id == "NFCI"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "NFCI", icon = icon("balance-scale"), color = "gray"))
      color <- if (latest$value > 0.5) "red" else if (latest$value > 0) "yellow" else "green"
      valueBox(round(latest$value, 2), paste("Chicago NFCI -", latest$date),
               icon = icon("balance-scale"), color = color)
    })

    output$vbox_m2 <- renderValueBox({
      if (is.null(money_data)) return(valueBox("N/A", "M2", icon = icon("money-bill"), color = "gray"))
      latest <- money_data[series_id == "M2SL"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "M2", icon = icon("money-bill"), color = "gray"))
      valueBox(paste0("$", round(latest$value / 1000, 1), "T"), paste("M2 Money Supply -", latest$date),
               icon = icon("money-bill"), color = "blue")
    })

    output$vix_chart <- renderEcharts4r({
      dt <- fin_filtered()[series_id == "VIXCLS"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#dd4b39", sampling = "lttb", name = "VIX") %>%
        e_mark_line(data = list(yAxis = 20), lineStyle = list(color = "#f39c12", type = "dashed"),
                    label = list(formatter = "Calm/Elevated: 20")) %>%
        e_mark_line(data = list(yAxis = 35), lineStyle = list(color = "#dd4b39", type = "dashed"),
                    label = list(formatter = "Panic: 35")) %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "VIX Index")
      add_recession_bands(chart, date_range())
    })

    output$spreads_chart <- renderEcharts4r({
      dt <- fin_filtered()[series_id %chin% c("BAMLH0A0HYM2", "BAMLC0A0CM")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "Spread (%)")
      add_recession_bands(chart, date_range())
    })

    output$fci_chart <- renderEcharts4r({
      dt <- fin_filtered()[series_id %chin% c("NFCI", "STLFSI4", "ANFCI")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "#333")) %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "Index (0 = avg)")
      add_recession_bands(chart, date_range())
    })

    output$money_chart <- renderEcharts4r({
      dt <- money_filtered()[series_id %chin% c("M1SL", "M2SL")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "Billions $")
      add_recession_bands(chart, date_range())
    })

    output$fed_bs_chart <- renderEcharts4r({
      dt <- money_filtered()[series_id == "WALCL"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_area(value, symbol = "none", color = "#00a65a", sampling = "lttb", name = "Fed Total Assets") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Millions $")
      add_recession_bands(chart, date_range())
    })

    output$lending_chart <- renderEcharts4r({
      dt <- money_filtered()[series_id %chin% c("BUSLOANS", "CONSUMER", "REALLN")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% group_by(series_id) %>% e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>% e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>% e_y_axis(name = "Billions $")
      add_recession_bands(chart, date_range())
    })
  })
}
