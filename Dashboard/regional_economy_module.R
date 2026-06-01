# ============================================================================
# REGIONAL ECONOMY MODULE - StarCruiser Dashboard v8.0
# ============================================================================
# State GDP comparison, GDP by industry, personal income by state
# Data: BEA Regional Accounts (50 states + DC + 8 regions)
# ============================================================================

# BEA region groupings for aggregation
BEA_REGIONS <- c("Far West", "Great Lakes", "Mideast", "New England",
                 "Plains", "Rocky Mountain", "Southeast", "Southwest")

regional_economy_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      box(title = "State Selection", width = 12,
        fluidRow(
          column(4, selectInput(ns("year"), "Year:", choices = 2010:2025, selected = 2024)),
          column(4, selectInput(ns("metric"), "Metric:",
            choices = c("GDP (Real)" = "CAGDP1-1", "Personal Income" = "CAINC1-1"),
            selected = "CAGDP1-1")),
          column(4, selectInput(ns("compare_states"), "Compare States:",
            choices = NULL, multiple = TRUE, selected = NULL))
        )
      )
    ),

    # State GDP ranking
    fluidRow(
      box(title = "State GDP Ranking",
          echarts4rOutput(ns("state_ranking"), height = "500px"),
          width = 6, solidHeader = TRUE, status = "primary"),
      box(title = "State GDP Growth Rates",
          echarts4rOutput(ns("state_growth"), height = "500px"),
          width = 6, solidHeader = TRUE, status = "info")
    ),

    # GDP by industry for selected state
    fluidRow(
      box(title = "State GDP by Industry (Treemap)",
          selectInput(ns("treemap_state"), "Select State:", choices = NULL),
          echarts4rOutput(ns("industry_treemap"), height = "450px"),
          width = 12, solidHeader = TRUE, status = "success")
    ),

    # Personal income comparison
    fluidRow(
      box(title = "Personal Income by State (Time Series)",
          echarts4rOutput(ns("income_chart"), height = "400px"),
          width = 12, solidHeader = TRUE, status = "warning")
    )
  )
}

regional_economy_server <- function(id, bea_state_gdp, bea_state_gdp_industry,
                                     bea_state_income) {
  moduleServer(id, function(input, output, session) {

    # Populate state choices
    observe({
      if (!is.null(bea_state_gdp)) {
        states <- sort(unique(bea_state_gdp[!GeoName %in% c("United States", BEA_REGIONS)]$GeoName))
        updateSelectInput(session, "compare_states", choices = states,
                          selected = c("California", "Texas", "New York"))
        updateSelectInput(session, "treemap_state", choices = states, selected = "California")
      }
    })

    # State GDP ranking bar chart
    output$state_ranking <- renderEcharts4r({
      req(bea_state_gdp, input$year)
      dt <- bea_state_gdp[TimePeriod == as.integer(input$year) &
                           !GeoName %in% c("United States", BEA_REGIONS)]
      if (nrow(dt) == 0) return(NULL)

      # Convert to billions
      dt[, gdp_billions := DataValue / 1e6]
      dt <- dt[order(-gdp_billions)][1:25]  # Top 25

      dt %>%
        e_charts(GeoName) %>%
        e_bar(gdp_billions, name = "GDP (Billions $)") %>%
        e_flip_coords() %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>GDP: $' +
                   params.value[0].toLocaleString(undefined, {maximumFractionDigits: 0}) + 'B';
          }
        ")) %>%
        e_x_axis(name = "GDP (Billions $)") %>%
        e_legend(show = FALSE) %>%
        e_color("#3c8dbc") %>%
        e_grid(left = "25%")
    })

    # State GDP growth rates
    output$state_growth <- renderEcharts4r({
      req(bea_state_gdp, input$year)
      yr <- as.integer(input$year)
      if (yr <= 2010) return(NULL)

      current <- bea_state_gdp[TimePeriod == yr & !GeoName %in% c("United States", BEA_REGIONS)]
      prev <- bea_state_gdp[TimePeriod == yr - 1 & !GeoName %in% c("United States", BEA_REGIONS)]

      if (nrow(current) == 0 || nrow(prev) == 0) return(NULL)

      merged <- merge(current[, .(GeoName, current = DataValue)],
                      prev[, .(GeoName, prev = DataValue)], by = "GeoName")
      merged[, growth := (current / prev - 1) * 100]
      merged <- merged[order(-growth)]
      merged[, color := ifelse(growth >= 0, "#00a65a", "#dd4b39")]

      merged %>%
        e_charts(GeoName) %>%
        e_bar(growth, itemStyle = list(color = htmlwidgets::JS("
          function(params) { return params.value[1] >= 0 ? '#00a65a' : '#dd4b39'; }
        "))) %>%
        e_flip_coords() %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>Growth: ' + params.value[0].toFixed(1) + '%';
          }
        ")) %>%
        e_x_axis(name = "GDP Growth (%)") %>%
        e_mark_line(data = list(xAxis = 0), lineStyle = list(color = "#333")) %>%
        e_legend(show = FALSE) %>%
        e_grid(left = "25%")
    })

    # Industry treemap for selected state
    output$industry_treemap <- renderEcharts4r({
      req(bea_state_gdp_industry, input$treemap_state, input$year)
      dt <- bea_state_gdp_industry[grepl(input$treemap_state, GeoName) &
                                    TimePeriod == as.integer(input$year)]
      if (nrow(dt) == 0) return(NULL)

      # Filter to major industries (Code contains industry codes)
      dt <- dt[DataValue > 0]
      dt[, value := DataValue / 1e3]  # Millions
      dt[, name := paste0(Code, " ($", round(value, 0), "M)")]

      # echarts4r treemap needs specific format
      dt %>%
        e_charts() %>%
        e_treemap(value, name, levels = list(
          list(itemStyle = list(borderWidth = 2, borderColor = "#333"))
        )) %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>$' + params.value.toLocaleString() + 'M';
          }
        "))
    })

    # Personal income time series
    output$income_chart <- renderEcharts4r({
      req(bea_state_income, input$compare_states)
      dt <- bea_state_income[GeoName %in% input$compare_states]
      if (nrow(dt) == 0) return(NULL)

      dt[, income_billions := DataValue / 1e6]

      dt %>%
        group_by(GeoName) %>%
        e_charts(TimePeriod) %>%
        e_line(income_billions, symbol = "circle", symbolSize = 6) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_x_axis(name = "Year") %>%
        e_y_axis(name = "Personal Income (Billions $)")
    })
  })
}
