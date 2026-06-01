# ============================================================================
# PRODUCTIVE ECONOMY MODULE - StarCruiser Dashboard v8.0
# ============================================================================
# Output gap, capacity utilization deep dive, investment composition,
# sectoral transformation (long-run structural change)
# Data: FRED production, BEA NIPA, FRED GDP
# ============================================================================

productive_economy_ui <- function(id) {
  ns <- NS(id)
  tagList(
    # Capacity utilization deep dive
    fluidRow(
      box(title = "Capacity Utilization: Total vs Manufacturing",
          echarts4rOutput(ns("caputil_detail"), height = "400px"),
          helpText("Above 80% = inflationary pressure. Below 70% = significant slack."),
          width = 12, solidHeader = TRUE, status = "primary")
    ),

    # Investment composition
    fluidRow(
      box(title = "Private Investment Components (NIPA)",
          echarts4rOutput(ns("investment_chart"), height = "400px"),
          helpText("GPDI = Gross Private Domestic Investment. Shows structural shift from structures to IP."),
          width = 12, solidHeader = TRUE, status = "info")
    ),

    # Sectoral transformation
    fluidRow(
      box(title = "Sectoral Output Shares (Structural Transformation)",
          echarts4rOutput(ns("sectoral_chart"), height = "400px"),
          helpText("Long-run shift from goods production to services and FIRE sector"),
          width = 12, solidHeader = TRUE, status = "success")
    ),

    # Real investment vs GDP
    fluidRow(
      box(title = "Investment / GDP Ratio",
          echarts4rOutput(ns("invest_gdp_ratio"), height = "350px"),
          helpText("Private fixed investment as share of GDP -- measures productive capital formation"),
          width = 6, solidHeader = TRUE, status = "warning"),
      box(title = "Credit vs Real Investment",
          echarts4rOutput(ns("credit_invest"), height = "350px"),
          helpText("Is bank credit flowing into real investment or financial speculation?"),
          width = 6, solidHeader = TRUE, status = "danger")
    )
  )
}

productive_economy_server <- function(id, production_data, gdp_data,
                                       money_data, bea_nipa, date_range) {
  moduleServer(id, function(input, output, session) {

    prod_filtered <- reactive({
      req(production_data); dr <- date_range()
      production_data[date >= dr[1] & date <= dr[2]]
    })

    gdp_filtered <- reactive({
      req(gdp_data); dr <- date_range()
      gdp_data[date >= dr[1] & date <= dr[2]]
    })

    # Capacity utilization detail
    output$caputil_detail <- renderEcharts4r({
      dt <- prod_filtered()[series_id %chin% c("TCU", "MCUMFN")]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)

      chart <- dt %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_mark_line(data = list(yAxis = 80),
          lineStyle = list(color = "#dd4b39", type = "dashed"),
          label = list(formatter = "Inflationary: 80%")) %>%
        e_mark_line(data = list(yAxis = 70),
          lineStyle = list(color = "#f39c12", type = "dotted"),
          label = list(formatter = "Slack: 70%")) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Capacity Utilization (%)", min = 60, max = 90)

      add_recession_bands(chart, date_range())
    })

    # Investment components from NIPA
    output$investment_chart <- renderEcharts4r({
      # Use FRED GDP data for investment series
      dt <- gdp_filtered()[series_id %chin% c("GPDI", "GPDIC1")]
      if (is.null(dt) || nrow(dt) == 0) {
        # Fallback: try NIPA tables
        if (!is.null(bea_nipa)) {
          nipa_inv <- bea_nipa[TableName == "T10101" &
                               grepl("investment|GPDI", LineDescription, ignore.case = TRUE)]
          if (nrow(nipa_inv) > 0) {
            nipa_inv[, date := as.Date(paste0(TimePeriod, "-01-01"))]
            chart <- nipa_inv %>%
              group_by(LineDescription) %>%
              e_charts(date) %>%
              e_line(DataValue, symbol = "none") %>%
              e_tooltip(trigger = "axis") %>%
              e_legend(bottom = "5%", type = "scroll") %>%
              e_y_axis(name = "Value")
            return(chart)
          }
        }
        return(NULL)
      }

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

    # Sectoral transformation
    output$sectoral_chart <- renderEcharts4r({
      if (is.null(bea_nipa)) return(NULL)

      # Get GDP components from T10101 or T50100 (national income by industry)
      sector_data <- bea_nipa[TableName == "T50100" &
                               LineNumber %in% c(1, 3, 6, 11, 19, 26)]
      if (nrow(sector_data) == 0) {
        # Try GDP components instead
        sector_data <- bea_nipa[TableName == "T10101" &
                                 LineNumber %in% c(1, 2, 7, 13, 19)]
      }
      if (nrow(sector_data) == 0) return(NULL)

      sector_data[, date := as.Date(paste0(TimePeriod, "-01-01"))]

      chart <- sector_data %>%
        group_by(LineDescription) %>%
        e_charts(date) %>%
        e_area(DataValue, stack = "sector", symbol = "none") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "0%", type = "scroll") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Value")

      chart
    })

    # Investment/GDP ratio
    output$invest_gdp_ratio <- renderEcharts4r({
      gdp_series <- gdp_filtered()[series_id %chin% c("GPDI", "GDP")]
      if (is.null(gdp_series) || nrow(gdp_series) == 0) return(NULL)

      wide <- dcast(gdp_series, date ~ series_id, value.var = "value")
      if (!all(c("GPDI", "GDP") %in% names(wide))) return(NULL)

      wide[, ratio := GPDI / GDP * 100]
      wide <- wide[!is.na(ratio)]

      chart <- wide %>%
        e_charts(date) %>%
        e_line(ratio, symbol = "none", color = "#3c8dbc", sampling = "lttb",
               name = "Investment/GDP (%)") %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "GPDI/GDP (%)")

      add_recession_bands(chart, date_range())
    })

    # Credit vs real investment
    output$credit_invest <- renderEcharts4r({
      if (is.null(money_data) || is.null(gdp_data)) return(NULL)

      dr <- date_range()
      loans <- money_data[series_id == "BUSLOANS" & date >= dr[1] & date <= dr[2]]
      invest <- gdp_data[series_id == "GPDI" & date >= dr[1] & date <= dr[2]]

      if (nrow(loans) == 0 || nrow(invest) == 0) return(NULL)

      # Aggregate both to monthly
      loans[, month := floor_date(date, "month")]
      loans_monthly <- loans[, .(loans = last(value)), by = month]
      invest[, month := floor_date(date, "month")]
      invest_monthly <- invest[, .(invest = last(value)), by = month]

      merged <- merge(loans_monthly, invest_monthly, by = "month")
      if (nrow(merged) == 0) return(NULL)

      chart <- merged %>%
        e_charts(month) %>%
        e_line(loans, symbol = "none", color = "#dd4b39", sampling = "lttb",
               name = "Business Loans", y_index = 0) %>%
        e_line(invest, symbol = "none", color = "#3c8dbc", sampling = "lttb",
               name = "Fixed Investment (GPDI)", y_index = 1) %>%
        e_y_axis(index = 0, name = "Loans ($B)") %>%
        e_y_axis(index = 1, name = "Investment ($B)") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider")

      add_recession_bands(chart, date_range())
    })
  })
}
