# ============================================================================
# FINANCE vs REAL ECONOMY MODULE - StarCruiser Dashboard v8.0
# ============================================================================
# Financialization metrics, credit-investment nexus, financial stress composite
# Data: FRED money/banking, GDP, financial stress
# ============================================================================

financial_real_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_credit_gdp"), width = 3),
      valueBoxOutput(ns("vbox_fed_gdp"), width = 3),
      valueBoxOutput(ns("vbox_m2_gdp"), width = 3),
      valueBoxOutput(ns("vbox_stress"), width = 3)
    ),

    # Financialization trend
    fluidRow(
      box(title = "Financial Sector Size Relative to GDP",
          echarts4rOutput(ns("fin_gdp_chart"), height = "400px"),
          helpText("Rising ratio = financialization. The financial sector growing faster than the real economy."),
          width = 12, solidHeader = TRUE, status = "danger")
    ),

    # Credit vs investment
    fluidRow(
      box(title = "Total Bank Credit vs GDP",
          echarts4rOutput(ns("credit_gdp"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "primary"),
      box(title = "Fed Balance Sheet vs GDP",
          echarts4rOutput(ns("fed_gdp"), height = "350px"),
          helpText("QE expanded the Fed balance sheet from $1T to $9T. QT is slowly unwinding."),
          width = 6, solidHeader = TRUE, status = "warning")
    ),

    # Money velocity
    fluidRow(
      box(title = "Money Velocity (M2)",
          echarts4rOutput(ns("velocity_chart"), height = "350px"),
          helpText("Falling velocity = money circulating slower through the economy. Secular decline since 1997."),
          width = 6, solidHeader = TRUE, status = "info"),
      box(title = "Unified Financial Stress Index",
          echarts4rOutput(ns("stress_composite"), height = "350px"),
          helpText("Composite of VIX, bond spreads, NFCI, STLFSI4. Higher = more stress."),
          width = 6, solidHeader = TRUE, status = "danger")
    )
  )
}

financial_real_server <- function(id, money_data, gdp_data, financial_data, date_range) {
  moduleServer(id, function(input, output, session) {

    money_f <- reactive({
      req(money_data); dr <- date_range()
      money_data[date >= dr[1] & date <= dr[2]]
    })

    gdp_f <- reactive({
      req(gdp_data); dr <- date_range()
      gdp_data[date >= dr[1] & date <= dr[2]]
    })

    fin_f <- reactive({
      req(financial_data); dr <- date_range()
      financial_data[date >= dr[1] & date <= dr[2]]
    })

    # Value boxes
    output$vbox_credit_gdp <- renderValueBox({
      if (is.null(money_data) || is.null(gdp_data)) return(valueBox("N/A", "Credit/GDP", icon = icon("percentage"), color = "gray"))
      credit <- money_data[series_id == "TOTBKCR"][order(-date)][1]$value
      gdp <- gdp_data[series_id == "GDP"][order(-date)][1]$value
      if (is.na(credit) || is.na(gdp) || gdp == 0) return(valueBox("N/A", "Credit/GDP", icon = icon("percentage"), color = "gray"))
      ratio <- round(credit / gdp * 100)
      valueBox(paste0(ratio, "%"), "Bank Credit / GDP",
               icon = icon("percentage"), color = if (ratio > 50) "red" else "yellow")
    })

    output$vbox_fed_gdp <- renderValueBox({
      if (is.null(money_data) || is.null(gdp_data)) return(valueBox("N/A", "Fed/GDP", icon = icon("university"), color = "gray"))
      fed <- money_data[series_id == "WALCL"][order(-date)][1]$value
      gdp <- gdp_data[series_id == "GDP"][order(-date)][1]$value
      if (is.na(fed) || is.na(gdp) || gdp == 0) return(valueBox("N/A", "Fed/GDP", icon = icon("university"), color = "gray"))
      # WALCL in millions, GDP in billions
      ratio <- round(fed / (gdp * 1000) * 100)
      valueBox(paste0(ratio, "%"), "Fed Assets / GDP",
               icon = icon("university"), color = if (ratio > 30) "red" else "yellow")
    })

    output$vbox_m2_gdp <- renderValueBox({
      if (is.null(money_data) || is.null(gdp_data)) return(valueBox("N/A", "M2/GDP", icon = icon("money-bill"), color = "gray"))
      m2 <- money_data[series_id == "M2SL"][order(-date)][1]$value
      gdp <- gdp_data[series_id == "GDP"][order(-date)][1]$value
      if (is.na(m2) || is.na(gdp) || gdp == 0) return(valueBox("N/A", "M2/GDP", icon = icon("money-bill"), color = "gray"))
      ratio <- round(m2 / gdp * 100)
      valueBox(paste0(ratio, "%"), "M2 / GDP",
               icon = icon("money-bill"), color = "blue")
    })

    output$vbox_stress <- renderValueBox({
      if (is.null(financial_data)) return(valueBox("N/A", "Stress", icon = icon("heartbeat"), color = "gray"))
      nfci <- financial_data[series_id == "NFCI"][order(-date)][1]$value
      if (is.na(nfci)) return(valueBox("N/A", "Stress", icon = icon("heartbeat"), color = "gray"))
      color <- if (nfci > 0.5) "red" else if (nfci > 0) "yellow" else "green"
      valueBox(round(nfci, 2), "Financial Stress (NFCI)",
               icon = icon("heartbeat"), color = color)
    })

    # Financial sector vs GDP
    output$fin_gdp_chart <- renderEcharts4r({
      m <- money_f()
      g <- gdp_f()
      if (is.null(m) || is.null(g)) return(NULL)

      # Use TOTBKCR (total bank credit) and WALCL (Fed assets) relative to GDP
      credit <- m[series_id == "TOTBKCR", .(date, credit = value)]
      fed <- m[series_id == "WALCL", .(date, fed = value)]
      gdp <- g[series_id == "GDP", .(date, gdp = value)]

      # Merge on monthly
      credit[, month := floor_date(date, "month")]
      credit_m <- credit[, .(credit = last(credit)), by = month]
      fed[, month := floor_date(date, "month")]
      fed_m <- fed[, .(fed = last(fed)), by = month]
      gdp[, month := floor_date(date, "month")]
      gdp_m <- gdp[, .(gdp = last(gdp)), by = month]

      merged <- Reduce(function(a, b) merge(a, b, by = "month", all = TRUE),
                       list(credit_m, fed_m, gdp_m))
      merged <- merged[!is.na(gdp) & gdp > 0]
      merged[, credit_pct := credit / gdp * 100]
      merged[, fed_pct := fed / (gdp * 1000) * 100]  # WALCL in millions

      chart <- merged %>%
        e_charts(month) %>%
        e_line(credit_pct, symbol = "none", color = "#dd4b39", sampling = "lttb",
               name = "Bank Credit/GDP (%)") %>%
        e_line(fed_pct, symbol = "none", color = "#3c8dbc", sampling = "lttb",
               name = "Fed Assets/GDP (%)") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "% of GDP")

      add_recession_bands(chart, date_range())
    })

    # Credit vs GDP
    output$credit_gdp <- renderEcharts4r({
      m <- money_f()[series_id == "TOTBKCR"]
      g <- gdp_f()[series_id == "GDP"]
      if (nrow(m) == 0 || nrow(g) == 0) return(NULL)

      chart <- rbindlist(list(
        m[, .(date, value, series_id = "Bank Credit")],
        g[, .(date, value, series_id = "GDP")]
      )) %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Billions $")

      add_recession_bands(chart, date_range())
    })

    # Fed balance sheet vs GDP
    output$fed_gdp <- renderEcharts4r({
      fed <- money_f()[series_id == "WALCL"]
      if (nrow(fed) == 0) return(NULL)

      chart <- fed %>%
        e_charts(date) %>%
        e_area(value, symbol = "none", color = "#9b59b6", sampling = "lttb",
               name = "Fed Total Assets") %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Millions $")

      add_recession_bands(chart, date_range())
    })

    # Money velocity
    output$velocity_chart <- renderEcharts4r({
      vel <- money_f()[series_id == "M2V"]
      if (nrow(vel) == 0) return(NULL)

      chart <- vel %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", color = "#f39c12", sampling = "lttb",
               name = "M2 Velocity") %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Velocity (GDP/M2)")

      add_recession_bands(chart, date_range())
    })

    # Unified stress composite
    output$stress_composite <- renderEcharts4r({
      dt <- fin_f()[series_id %chin% c("NFCI", "STLFSI4")]
      if (nrow(dt) == 0) return(NULL)

      chart <- dt %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "#333", type = "dashed")) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Stress Index (0 = average)")

      add_recession_bands(chart, date_range())
    })
  })
}
