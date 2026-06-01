# ============================================================================
# STARCRUISER ECONOMIC DASHBOARD
# ============================================================================
# Framework: Shiny Dashboard
# Data: CPI/PCE Inflation, Treasury Yield Curve, Employment Statistics
# Created: 2025-11-28
# ============================================================================

# UI DEFINITION
ui <- dashboardPage(
  skin = "blue",

  # HEADER
  dashboardHeader(title = "StarCruiser v7.0"),

  # SIDEBAR
  dashboardSidebar(
    sidebarMenu(
      id = "sidebarMenu",
      menuItem("Command Center", tabName = "overview", icon = icon("rocket")),

      menuItem("Real Economy", icon = icon("industry"),
        menuSubItem("GDP & Output", tabName = "gdp_output"),
        menuSubItem("Consumer & Spending", tabName = "consumer"),
        menuSubItem("Housing Market", tabName = "housing"),
        menuSubItem("Trade & Fiscal", tabName = "trade_fiscal"),
        menuSubItem("Productive Capacity", tabName = "productive"),
        menuSubItem("Economic Flows", tabName = "flows")
      ),

      menuItem("Labor Market", icon = icon("users"),
        menuSubItem("Employment", tabName = "employment"),
        menuSubItem("Labor Dynamics", tabName = "labor_dynamics"),
        menuSubItem("Wages & Hours", tabName = "wages_hours")
      ),

      menuItem("Prices & Rates", icon = icon("chart-line"),
        menuSubItem("CPI/PCE Inflation", tabName = "inflation"),
        menuSubItem("Inflation Deep Dive", tabName = "inflation_deep"),
        menuSubItem("Yield Curve", tabName = "yields"),
        menuSubItem("Treasury Market", tabName = "treasury")
      ),

      menuItem("Financial System", icon = icon("chart-bar"),
        menuSubItem("Financial Conditions", tabName = "financial"),
        menuSubItem("Banking Sector", tabName = "banking"),
        menuSubItem("Finance vs Real Economy", tabName = "fin_real")
      ),

      menuItem("Regional", icon = icon("map-marked-alt"),
        menuSubItem("State Economies", tabName = "regional"),
        menuSubItem("State Comparison", tabName = "state_compare"),
        menuSubItem("County Geographic", tabName = "geographic")
      ),

      menuItem("Analytics", icon = icon("brain"),
        menuSubItem("Correlation & Lead-Lag", tabName = "analytics"),
        menuSubItem("Recession Risk", tabName = "recession")
      ),

      menuItem("Real-Time Indicators", tabName = "realtime", icon = icon("bolt")),
      menuItem("Data Quality", tabName = "quality", icon = icon("shield-alt"))
    ),
    hr(),
    # Global date range selector
    dateRangeInput(
      "date_range",
      "Date Range:",
      start = Sys.Date() - 365 * 5, # Default: last 5 years
      end = Sys.Date(),
      min = as.Date("1947-01-01"),
      max = Sys.Date()
    )
  ),

  # BODY
  dashboardBody(
    tabItems(

      # =======================================================================
      # TAB 1: OVERVIEW
      # =======================================================================
      tabItem(
        tabName = "overview",
        h2("Command Center: Economy at a Glance"),

        # Health Score (Phase 3)
        health_score_ui("health_score_module"),

        hr(),

        # Original overview value boxes + charts
        fluidRow(
          valueBoxOutput("vbox_cpi", width = 4),
          valueBoxOutput("vbox_unrate", width = 4),
          valueBoxOutput("vbox_spread", width = 4)
        ),

        fluidRow(
          box(
            title = "Inflation: CPI vs PCE",
            echarts4rOutput("plot_overview_inflation", height = "350px"),
            width = 6, solidHeader = TRUE, status = "primary"
          ),
          box(
            title = "Unemployment Rate",
            echarts4rOutput("plot_overview_employment", height = "350px"),
            width = 6, solidHeader = TRUE, status = "primary"
          )
        )
      ),

      # =======================================================================
      # TAB 2: CPI/PCE INFLATION
      # =======================================================================
      tabItem(
        tabName = "inflation",
        h2("CPI and PCE Analysis"),
        fluidRow(
          box(
            title = tagList(
              "Headline vs Core Inflation",
              tags$small(
                style = "font-weight: normal; color: #666; margin-left: 10px;",
                "| Source: FRED (Federal Reserve Economic Data)"
              )
            ),
            echarts4rOutput("plot_inflation_main", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "primary"
          )
        ),
        fluidRow(
          box(
            title = "Year-over-Year Changes",
            echarts4rOutput("plot_inflation_yoy", height = "400px"),
            width = 6,
            solidHeader = TRUE,
            status = "info"
          ),
          box(
            title = "Month-over-Month Changes",
            echarts4rOutput("plot_inflation_mom", height = "400px"),
            width = 6,
            solidHeader = TRUE,
            status = "success"
          )
        ),
        fluidRow(
          box(
            title = "CPI Component Breakdown",
            fluidRow(
              column(
                width = 8,
                checkboxGroupInput(
                  "cpi_components",
                  "Select Components:",
                  choices = c(
                    "All Items (Headline)" = "CPIAUCSL",
                    "Core (Less Food/Energy)" = "CPILFESL",
                    "Energy" = "CPIENGSL",
                    "Food & Beverages" = "CPIFABSL",
                    "Housing" = "CPIHOSSL",
                    "Medical Care" = "CPIMEDSL",
                    "Transportation" = "CPITRNSL"
                  ),
                  selected = c("CPIAUCSL", "CPILFESL")
                )
              ),
              column(
                width = 4,
                radioButtons(
                  "cpi_chart_type",
                  "Chart Type:",
                  choices = c("Line (Time Series)" = "line", "Bar (Latest Values)" = "bar"),
                  selected = "line"
                )
              )
            ),
            echarts4rOutput("plot_inflation_components", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "warning"
          )
        ),

        # Download section
        fluidRow(
          box(
            title = "Download Data",
            downloadButton("download_inflation", "Download Inflation Data (CSV)", icon = icon("download")),
            p(
              style = "margin-top: 10px; font-size: 12px; color: #666;",
              "Downloads filtered inflation data with YoY changes for the selected date range."
            ),
            width = 12,
            status = "info"
          )
        )
      ),

      # =======================================================================
      # TAB 3: YIELD CURVE
      # =======================================================================
      tabItem(
        tabName = "yields",
        h2("Treasury Yield Curve Analysis"),
        fluidRow(
          box(
            title = "Yield Curve Snapshot",
            dateInput(
              "yield_snapshot_date",
              "Select Date:",
              value = Sys.Date(),
              max = Sys.Date()
            ),
            echarts4rOutput("plot_yield_snapshot", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "primary"
          )
        ),
        fluidRow(
          box(
            title = "10Y-2Y Spread (Recession Indicator)",
            p("Negative values (inversions) may signal recession risk."),
            echarts4rOutput("plot_spread_2_10", height = "400px"),
            width = 6,
            solidHeader = TRUE,
            status = "danger"
          ),
          box(
            title = "10Y-3mo Spread",
            echarts4rOutput("plot_spread_3mo_10yr", height = "400px"),
            width = 6,
            solidHeader = TRUE,
            status = "warning"
          )
        ),
        fluidRow(
          box(
            title = "Multi-Date Yield Curve Comparison",
            dateInput("yield_date_1", "Date 1:", value = Sys.Date()),
            dateInput("yield_date_2", "Date 2:", value = Sys.Date() - 365),
            dateInput("yield_date_3", "Date 3:", value = Sys.Date() - 730),
            echarts4rOutput("plot_yield_overlay", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "info"
          )
        ),

        # Download section
        fluidRow(
          box(
            title = "Download Data",
            downloadButton("download_yields", "Download Yield Data (CSV)", icon = icon("download")),
            p(
              style = "margin-top: 10px; font-size: 12px; color: #666;",
              "Downloads yield curve data and spreads for the selected date range."
            ),
            width = 12,
            status = "info"
          )
        )
      ),

      # =======================================================================
      # TAB 4: EMPLOYMENT
      # =======================================================================
      tabItem(
        tabName = "employment",
        h2("Labor Market Indicators"),

        # Value boxes
        fluidRow(
          valueBoxOutput("vbox_unrate_detail", width = 4),
          valueBoxOutput("vbox_payems", width = 4),
          valueBoxOutput("vbox_emp_change", width = 4)
        ),

        # Charts
        fluidRow(
          box(
            title = "Unemployment Rate Over Time",
            echarts4rOutput("plot_employment_unrate", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "primary"
          )
        ),
        fluidRow(
          box(
            title = "Total Nonfarm Payrolls",
            echarts4rOutput("plot_employment_payems", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "success"
          )
        ),
        fluidRow(
          box(
            title = "Employment by Industry Sector",
            checkboxGroupInput(
              "employment_sectors",
              "Select Sectors:",
              choices = c(
                "Manufacturing" = "MANEMP",
                "Construction" = "USCONS",
                "Retail Trade" = "USTRADE",
                "Financial Activities" = "USFIRE",
                "Professional & Business Services" = "USPBS",
                "Education & Health Services" = "USEHS",
                "Leisure & Hospitality" = "USLAH"
              ),
              selected = c("MANEMP", "USCONS", "USTRADE")
            ),
            echarts4rOutput("plot_employment_sectors", height = "400px"),
            width = 12,
            solidHeader = TRUE,
            status = "info"
          )
        ),

        # Gig Economy Adjustment (Track A2.2)
        fluidRow(
          box(
            title = "Gig Economy Adjustment", width = 12,
            collapsible = TRUE, collapsed = TRUE,
            fluidRow(
              column(4,
                radioButtons("gig_scenario", "Adjustment Scenario:",
                  choices = c("None (Official)" = "none", "Low (+10%)" = "low",
                              "Medium (+15%)" = "medium", "High (+20%)" = "high"))
              ),
              column(8,
                helpText("Adjusts official employment statistics for estimated gig economy undercount (15-20%).
                          Uncertainty bands show +/- 2% around the adjustment."),
                echarts4rOutput("plot_adjusted_employment", height = "350px")
              )
            )
          )
        ),

        # Download section
        fluidRow(
          box(
            title = "Download Data",
            downloadButton("download_employment", "Download Employment Data (CSV)", icon = icon("download")),
            p(
              style = "margin-top: 10px; font-size: 12px; color: #666;",
              "Downloads filtered employment data for the selected date range."
            ),
            width = 12,
            status = "info"
          )
        )
      ),

      # =======================================================================
      # TAB 5: LABOR DYNAMICS (NEW)
      # =======================================================================
      tabItem(
        tabName = "labor_dynamics",
        h2("Labor Market Dynamics"),
        labor_dynamics_ui("labor_dynamics_module")
      ),

      # =======================================================================
      # TAB 6: WAGES & HOURS (NEW)
      # =======================================================================
      tabItem(
        tabName = "wages_hours",
        h2("Wages & Hours Analysis"),
        wages_hours_ui("wages_hours_module")
      ),

      # =======================================================================
      # TAB: CORRELATION & LEAD-LAG (Track A1.1)
      # =======================================================================
      tabItem(
        tabName = "analytics",
        h2("Correlation & Lead-Lag Analysis"),
        correlation_ui("correlation_module")
      ),

      # =======================================================================
      # TAB: RECESSION RISK (Track A1.2+A1.3)
      # =======================================================================
      tabItem(
        tabName = "recession",
        h2("Recession Risk & Business Cycle"),
        recession_ui("recession_module")
      ),

      # =======================================================================
      # TAB: GDP & OUTPUT (v7.0)
      # =======================================================================
      tabItem(
        tabName = "gdp_output",
        h2("GDP & Industrial Output"),
        gdp_output_ui("gdp_output_module")
      ),

      # =======================================================================
      # TAB: CONSUMER & SPENDING (v7.0)
      # =======================================================================
      tabItem(
        tabName = "consumer",
        h2("Consumer & Spending"),
        consumer_ui("consumer_module")
      ),

      # =======================================================================
      # TAB: HOUSING MARKET (v7.0)
      # =======================================================================
      tabItem(
        tabName = "housing",
        h2("Housing Market"),
        housing_ui("housing_module")
      ),

      # =======================================================================
      # TAB: TRADE & FISCAL (v7.0)
      # =======================================================================
      tabItem(
        tabName = "trade_fiscal",
        h2("Trade & Government Finance"),
        trade_fiscal_ui("trade_fiscal_module")
      ),

      # =======================================================================
      # TAB: PRODUCTIVE CAPACITY (v8.0)
      # =======================================================================
      tabItem(
        tabName = "productive",
        h2("Productive Capacity & Real Economy"),
        productive_economy_ui("productive_module")
      ),

      # =======================================================================
      # TAB: ECONOMIC FLOWS (v8.0 - Sankey/Treemap)
      # =======================================================================
      tabItem(
        tabName = "flows",
        h2("Economic Flows & Interdependencies"),
        economic_flows_ui("flows_module")
      ),

      # =======================================================================
      # TAB: FINANCIAL CONDITIONS (v7.0)
      # =======================================================================
      tabItem(
        tabName = "financial",
        h2("Financial Conditions & Monetary"),
        financial_ui("financial_module")
      ),

      # =======================================================================
      # TAB: BANKING SECTOR (v8.0)
      # =======================================================================
      tabItem(
        tabName = "banking",
        h2("Banking Sector Structure & Health"),
        banking_sector_ui("banking_module")
      ),

      # =======================================================================
      # TAB: FINANCE vs REAL ECONOMY (v8.0)
      # =======================================================================
      tabItem(
        tabName = "fin_real",
        h2("Finance vs Real Economy"),
        financial_real_ui("fin_real_module")
      ),

      # =======================================================================
      # TAB: STATE ECONOMIES (v8.0)
      # =======================================================================
      tabItem(
        tabName = "regional",
        h2("State Economic Profiles"),
        regional_economy_ui("regional_module")
      ),

      # =======================================================================
      # TAB: STATE COMPARISON (v8.0)
      # =======================================================================
      tabItem(
        tabName = "state_compare",
        h2("Multi-Dimensional State Comparison"),
        state_comparison_ui("state_compare_module")
      ),

      # =======================================================================
      # TAB: GEOGRAPHIC ANALYSIS (Enhanced Track B)
      # =======================================================================
      geographic_ui(),

      # =======================================================================
      # TAB: REAL-TIME INDICATORS (Track C2.1)
      # =======================================================================
      tabItem(
        tabName = "realtime",
        h2("Real-Time Leading Indicators"),
        realtime_ui("realtime_module")
      ),

      # =======================================================================
      # TAB 8: TREASURY MARKET
      # =======================================================================
      tabItem(
        tabName = "treasury",
        h2("Treasury Market Analysis"),
        treasury_ui("treasury_module")
      ),

      # =======================================================================
      # TAB 7: INFLATION DEEP DIVE
      # =======================================================================
      tabItem(
        tabName = "inflation_deep",
        h2("Inflation Decomposition Analysis"),
        inflation_ui("inflation_module")
      ),

      # TAB: DATA QUALITY (Enhanced with Track A2.1)
      # =======================================================================
      tabItem(
        tabName = "quality",
        h2("Data Quality & Metadata"),

        # Quality Degradation Dashboard (Track A2.1 - embedded here)
        quality_degradation_ui("quality_degradation_module"),

        hr(),
        h3("Data Coverage"),

        fluidRow(
          infoBoxOutput("info_data_freshness", width = 4),
          infoBoxOutput("info_data_coverage", width = 4),
          infoBoxOutput("info_quality_tier", width = 4)
        ),
        fluidRow(
          box(
            title = "Data Sources & Attribution",
            status = "info",
            solidHeader = TRUE,
            width = 12,
            HTML("
              <strong>Federal Reserve Economic Data (FRED)</strong><br>
              <ul style='margin-top: 5px;'>
                <li><strong>Inflation</strong>: 17,332 records | Quality Tier 1 (BEA/BLS Official Data)</li>
                <li><strong>Interest Rates</strong>: 248,052 records | Quality Tier 1 (Federal Reserve Official Data)</li>
                <li><strong>Employment</strong>: 34,335 records | Quality Tier 2 (pre-2025) / Tier 3 (2025+)</li>
              </ul>

              <strong>Citation</strong>: StarCruiser Economic Dashboard (v2.0), powered by FRED,
              Federal Reserve Bank of St. Louis, November 2025.<br><br>

              <strong>Data Provider</strong>: Federal Reserve Bank of St. Louis<br>
              <strong>Website</strong>: <a href='https://fred.stlouisfed.org' target='_blank'>https://fred.stlouisfed.org</a>
            ")
          )
        ),
        fluidRow(
          box(
            title = "2025 Data Quality Warning",
            status = "warning",
            solidHeader = TRUE,
            width = 12,
            p(strong("Due to Trump administration budget cuts and staffing reductions:")),
            tags$ul(
              tags$li("BLS lost 25% of staff since February 2025"),
              tags$li("Response rates declined: CES 64%→43%, CPS 69%→62%"),
              tags$li("Sept-Oct 2025: NO DATA (43-day government shutdown)"),
              tags$li("All 2025 survey data downgraded to Tier 3")
            ),
            p(strong("Recommendation:"), "Use Tier 1-2 data for critical analyses, cross-validate 2025 data.")
          )
        ),
        fluidRow(
          box(
            title = "Summary Statistics by Category",
            DTOutput("table_summary_stats"),
            width = 12,
            solidHeader = TRUE,
            status = "success"
          )
        ),
        fluidRow(
          box(
            title = "Data Series Catalog",
            DTOutput("table_data_summary"),
            width = 12,
            solidHeader = TRUE,
            status = "primary"
          )
        ),

        # Download section
        fluidRow(
          box(
            title = "Download Data",
            downloadButton("download_catalog", "Download Data Catalog (CSV)", icon = icon("download")),
            p(
              style = "margin-top: 10px; font-size: 12px; color: #666;",
              "Downloads the complete data catalog with series metadata."
            ),
            width = 12,
            status = "info"
          )
        )
      )
    ),

    # Footer
    tags$footer(
      style = "text-align: center; padding: 15px; margin-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;",
      HTML("
        <strong>Data Source</strong>: FRED (Federal Reserve Bank of St. Louis) |
        <strong>Dashboard</strong>: StarCruiser v8.0 - Economic Intelligence Platform |
        <strong>Last Updated</strong>: March 30, 2026<br>
        <span style='font-size: 11px;'>
          For data quality information and known limitations, see the Data Quality tab.
        </span>
      ")
    )
  )
)

# SERVER LOGIC
server <- function(input, output, session) {
  # ========================================================================
  # REACTIVE DATA FILTERING
  # ========================================================================

  # Debounce date range input (wait 500ms after user stops changing)
  date_range_debounced <- reactive({
    input$date_range
  }) %>% debounce(500)

  # Filtered inflation data
  inflation_filtered <- reactive({
    req(date_range_debounced())
    inflation_data[date >= date_range_debounced()[1] & date <= date_range_debounced()[2]]
  })

  # Filtered rates data
  rates_filtered <- reactive({
    req(date_range_debounced())
    rates_data[date >= date_range_debounced()[1] & date <= date_range_debounced()[2]]
  })

  # Filtered employment data
  employment_filtered <- reactive({
    req(date_range_debounced())
    employment_data[date >= date_range_debounced()[1] & date <= date_range_debounced()[2]]
  })

  # ========================================================================
  # OVERVIEW TAB OUTPUTS
  # ========================================================================

  output$vbox_cpi <- renderValueBox({
    latest <- get_latest_value(inflation_data, "CPIAUCSL")

    valueBox(
      value = if (!is.na(latest$value)) round(latest$value, 1) else "N/A",
      subtitle = paste("CPI (All Urban) -", latest$date),
      icon = icon("chart-line"),
      color = "blue"
    )
  })

  output$vbox_unrate <- renderValueBox({
    latest <- get_latest_value(employment_data, "UNRATE")

    valueBox(
      value = if (!is.na(latest$value)) paste0(latest$value, "%") else "N/A",
      subtitle = paste("Unemployment Rate -", latest$date),
      icon = icon("users"),
      color = "green"
    )
  })

  output$vbox_spread <- renderValueBox({
    latest <- yield_spreads[!is.na(spread_2_10)][order(-date)][1]

    if (nrow(latest) > 0 && !is.na(latest$spread_2_10)) {
      color <- ifelse(latest$spread_2_10 < 0, "red", "yellow")
      value_text <- paste0(round(latest$spread_2_10 * 100, 0), " bps")
    } else {
      color <- "gray"
      value_text <- "N/A"
    }

    valueBox(
      value = value_text,
      subtitle = paste("10Y-2Y Spread -", if (nrow(latest) > 0) latest$date else "N/A"),
      icon = icon("chart-area"),
      color = color
    )
  })

  output$plot_overview_inflation <- renderEcharts4r({
    plot_data <- inflation_filtered()[series_id %chin% c("CPIAUCSL", "PCEPI")]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    chart <- plot_data %>%
      group_by(series_id) %>%
      e_charts(date) %>%
      e_line(value, symbol = "none", sampling = "lttb") %>%
      e_tooltip(trigger = "axis") %>%
      e_legend(bottom = "5%") %>%
      e_datazoom(type = "slider", start = 80) %>%
      e_y_axis(name = "Index Value")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_overview_employment <- renderEcharts4r({
    plot_data <- employment_filtered()[series_id == "UNRATE"]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    chart <- plot_data %>%
      e_charts(date) %>%
      e_line(value, symbol = "none", color = "#3c8dbc", sampling = "lttb") %>%
      e_tooltip(trigger = "axis") %>%
      e_datazoom(type = "slider", start = 80) %>%
      e_y_axis(name = "Unemployment Rate (%)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  # ========================================================================
  # INFLATION TAB OUTPUTS
  # ========================================================================

  output$plot_inflation_main <- renderEcharts4r({
    plot_data <- inflation_filtered()[series_id %chin% c("CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE")]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    plot_data %>%
      group_by(series_id) %>%
      e_charts(date) %>%
      e_line(value, symbol = "none", sampling = "lttb") %>%
      e_tooltip(trigger = "axis") %>%
      e_legend(bottom = "5%") %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Index Value")
  })

  output$plot_inflation_yoy <- renderEcharts4r({
    plot_data <- inflation_filtered()[series_id %chin% c("CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE") & !is.na(yoy_change)]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    chart <- plot_data %>%
      group_by(series_id) %>%
      e_charts(date) %>%
      e_line(yoy_change, symbol = "none", sampling = "lttb") %>%
      e_tooltip(trigger = "axis", formatter = htmlwidgets::JS("
        function(params) {
          return params.map(function(p) {
            return p.seriesName + ': ' + p.value[1].toFixed(2) + '%';
          }).join('<br/>');
        }
      ")) %>%
      e_legend(bottom = "5%") %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Year-over-Year Change (%)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_inflation_mom <- renderEcharts4r({
    plot_data <- inflation_filtered()[series_id %chin% c("CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE") & !is.na(mom_change)]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    chart <- plot_data %>%
      group_by(series_id) %>%
      e_charts(date) %>%
      e_line(mom_change, symbol = "none", sampling = "lttb") %>%
      e_tooltip(trigger = "axis", formatter = htmlwidgets::JS("
        function(params) {
          return params.map(function(p) {
            return p.seriesName + ': ' + p.value[1].toFixed(2) + '%';
          }).join('<br/>');
        }
      ")) %>%
      e_legend(bottom = "5%") %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Month-over-Month Change (%)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_inflation_components <- renderEcharts4r({
    req(length(input$cpi_components) > 0)

    plot_data <- inflation_filtered()[series_id %chin% input$cpi_components]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    # Check chart type selection
    if (input$cpi_chart_type == "bar") {
      # Bar chart: show latest values for each component
      latest_values <- plot_data[, .SD[which.max(date)], by = series_id]

      chart <- latest_values %>%
        e_charts(series_id) %>%
        e_bar(value, name = "Latest Value") %>%
        e_tooltip(trigger = "axis") %>%
        e_x_axis(axisLabel = list(rotate = 45, interval = 0)) %>%
        e_y_axis(name = "Index Value") %>%
        e_color("#3c8dbc")

      return(chart)
    } else {
      # Line chart: time series (existing behavior)
      plot_data %>%
        group_by(series_id) %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", sampling = "lttb") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Index Value")
    }
  })

  # ========================================================================
  # YIELD CURVE TAB OUTPUTS
  # ========================================================================

  output$plot_yield_snapshot <- renderEcharts4r({
    snapshot_date <- input$yield_snapshot_date

    yields <- rates_data[date == snapshot_date &
      series_id %chin% c("DTB3", "DGS2", "DGS5", "DGS10", "DGS30")]

    validate(
      need(nrow(yields) > 0, paste("No yield data available for", snapshot_date))
    )

    # Add maturity column
    yields[, maturity := fcase(
      series_id == "DTB3", 0.25,
      series_id == "DGS2", 2,
      series_id == "DGS5", 5,
      series_id == "DGS10", 10,
      series_id == "DGS30", 30
    )]

    setorder(yields, maturity)

    yields %>%
      e_charts(maturity) %>%
      e_line(value, symbol = "circle", symbolSize = 8, color = "#3c8dbc") %>%
      e_tooltip() %>%
      e_x_axis(name = "Maturity (Years)") %>%
      e_y_axis(name = "Yield (%)")
  })

  output$plot_spread_2_10 <- renderEcharts4r({
    spread_data <- yield_spreads[date >= date_range_debounced()[1] &
      date <= date_range_debounced()[2] &
      !is.na(spread_2_10)]

    if (nrow(spread_data) == 0) {
      return(NULL)
    }

    chart <- spread_data %>%
      e_charts(date) %>%
      e_line(spread_2_10, symbol = "none", color = "#3c8dbc", sampling = "lttb") %>%
      e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "red", type = "dashed")) %>%
      e_tooltip(trigger = "axis", formatter = htmlwidgets::JS("
        function(params) {
          var val = params[0].value[1];
          return 'Spread: ' + (val * 100).toFixed(0) + ' bps';
        }
      ")) %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Spread (percentage points)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_spread_3mo_10yr <- renderEcharts4r({
    spread_data <- yield_spreads[date >= date_range_debounced()[1] &
      date <= date_range_debounced()[2] &
      !is.na(spread_3mo_10yr)]

    if (nrow(spread_data) == 0) {
      return(NULL)
    }

    chart <- spread_data %>%
      e_charts(date) %>%
      e_line(spread_3mo_10yr, symbol = "none", color = "#00a65a", sampling = "lttb") %>%
      e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "red", type = "dashed")) %>%
      e_tooltip(trigger = "axis", formatter = htmlwidgets::JS("
        function(params) {
          var val = params[0].value[1];
          return 'Spread: ' + (val * 100).toFixed(0) + ' bps';
        }
      ")) %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Spread (percentage points)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_yield_overlay <- renderEcharts4r({
    dates <- c(input$yield_date_1, input$yield_date_2, input$yield_date_3)

    yields <- rates_data[date %chin% dates &
      series_id %chin% c("DTB3", "DGS2", "DGS5", "DGS10", "DGS30")]

    validate(
      need(nrow(yields) > 0, "No yield data available for selected dates")
    )

    # Add maturity column
    yields[, maturity := fcase(
      series_id == "DTB3", 0.25,
      series_id == "DGS2", 2,
      series_id == "DGS5", 5,
      series_id == "DGS10", 10,
      series_id == "DGS30", 30
    )]

    yields %>%
      group_by(date) %>%
      e_charts(maturity) %>%
      e_line(value, symbol = "circle", symbolSize = 6) %>%
      e_tooltip() %>%
      e_legend(bottom = "5%") %>%
      e_x_axis(name = "Maturity (Years)") %>%
      e_y_axis(name = "Yield (%)")
  })

  # ========================================================================
  # EMPLOYMENT TAB OUTPUTS
  # ========================================================================

  output$vbox_unrate_detail <- renderValueBox({
    latest <- get_latest_value(employment_data, "UNRATE")

    valueBox(
      value = if (!is.na(latest$value)) paste0(latest$value, "%") else "N/A",
      subtitle = paste("Unemployment -", latest$date),
      icon = icon("percentage"),
      color = "aqua"
    )
  })

  output$vbox_payems <- renderValueBox({
    latest <- get_latest_value(employment_data, "PAYEMS")

    # PAYEMS is in thousands
    value_text <- if (!is.na(latest$value)) {
      format(latest$value * 1000, big.mark = ",", scientific = FALSE)
    } else {
      "N/A"
    }

    valueBox(
      value = value_text,
      subtitle = paste("Nonfarm Payrolls -", latest$date),
      icon = icon("briefcase"),
      color = "green"
    )
  })

  output$vbox_emp_change <- renderValueBox({
    payems <- employment_data[series_id == "PAYEMS"][order(-date)][1:2]

    if (nrow(payems) == 2) {
      change <- (payems$value[1] - payems$value[2]) * 1000
      color <- ifelse(change > 0, "green", "red")
      icon_val <- ifelse(change > 0, "arrow-up", "arrow-down")
      value_text <- format(round(change), big.mark = ",")
    } else {
      color <- "gray"
      icon_val <- "question"
      value_text <- "N/A"
    }

    valueBox(
      value = value_text,
      subtitle = "MoM Change (thousands)",
      icon = icon(icon_val),
      color = color
    )
  })

  output$plot_employment_unrate <- renderEcharts4r({
    plot_data <- employment_filtered()[series_id == "UNRATE"]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    chart <- plot_data %>%
      e_charts(date) %>%
      e_line(value, symbol = "none", color = "#3c8dbc", sampling = "lttb") %>%
      e_tooltip(trigger = "axis") %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Unemployment Rate (%)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_employment_payems <- renderEcharts4r({
    plot_data <- employment_filtered()[series_id == "PAYEMS"]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    # Convert to thousands
    plot_data[, value_thousands := value * 1000]

    chart <- plot_data %>%
      e_charts(date) %>%
      e_line(value_thousands, symbol = "none", color = "#00a65a", sampling = "lttb") %>%
      e_tooltip(trigger = "axis", formatter = htmlwidgets::JS("
        function(params) {
          var val = params[0].value[1];
          return 'Payrolls: ' + val.toLocaleString() + ' thousand';
        }
      ")) %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Nonfarm Payrolls (thousands)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  output$plot_employment_sectors <- renderEcharts4r({
    req(length(input$employment_sectors) > 0)

    plot_data <- employment_filtered()[series_id %chin% input$employment_sectors]

    if (nrow(plot_data) == 0) {
      return(NULL)
    }

    # Convert to thousands
    plot_data[, value_thousands := value * 1000]

    chart <- plot_data %>%
      group_by(series_id) %>%
      e_charts(date) %>%
      e_line(value_thousands, symbol = "none", sampling = "lttb") %>%
      e_tooltip(trigger = "axis") %>%
      e_legend(bottom = "5%") %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Employment (thousands)")

    # Add recession bands
    add_recession_bands(chart, date_range_debounced())
  })

  # ========================================================================
  # GIG ECONOMY ADJUSTMENT (Track A2.2)
  # ========================================================================

  output$plot_adjusted_employment <- renderEcharts4r({
    req(input$gig_scenario)
    if (input$gig_scenario == "none") return(NULL)

    multiplier <- switch(input$gig_scenario,
      "low" = 1.10, "medium" = 1.15, "high" = 1.20, 1.0)

    payems <- employment_filtered()[series_id == "PAYEMS"]
    if (nrow(payems) == 0) return(NULL)

    plot_dt <- payems[, .(date, official = value * 1000,
                          adjusted = value * 1000 * multiplier,
                          upper = value * 1000 * multiplier * 1.02,
                          lower = value * 1000 * multiplier * 0.98)]

    chart <- plot_dt %>%
      e_charts(date) %>%
      e_line(official, symbol = "none", color = "#3c8dbc", sampling = "lttb",
             name = "Official Payrolls") %>%
      e_line(adjusted, symbol = "none", color = "#dd4b39", sampling = "lttb",
             name = paste0("Adjusted (+", (multiplier - 1) * 100, "%)"),
             lineStyle = list(type = "dashed")) %>%
      e_band2(lower, upper, color = "rgba(221,75,57,0.1)",
              itemStyle = list(borderWidth = 0)) %>%
      e_tooltip(trigger = "axis") %>%
      e_legend(bottom = "5%") %>%
      e_datazoom(type = "slider") %>%
      e_y_axis(name = "Nonfarm Payrolls (thousands)")

    add_recession_bands(chart, date_range_debounced())
  })

  # ========================================================================
  # DATA QUALITY TAB OUTPUTS
  # ========================================================================

  output$info_data_freshness <- renderInfoBox({
    latest_date <- max(c(
      max(inflation_data$date, na.rm = TRUE),
      max(employment_data$date, na.rm = TRUE)
    ))

    days_old <- as.numeric(Sys.Date() - latest_date)

    color <- ifelse(days_old < 30, "green", ifelse(days_old < 90, "yellow", "red"))

    infoBox(
      title = "Data Freshness",
      value = paste(days_old, "days old"),
      subtitle = paste("Latest:", latest_date),
      icon = icon("calendar"),
      color = color
    )
  })

  output$info_data_coverage <- renderInfoBox({
    total_series <- length(unique(c(
      inflation_data$series_id,
      rates_data$series_id,
      employment_data$series_id
    )))

    infoBox(
      title = "Series Count",
      value = total_series,
      subtitle = "Unique time series loaded",
      icon = icon("database"),
      color = "blue"
    )
  })

  output$info_quality_tier <- renderInfoBox({
    infoBox(
      title = "Data Quality",
      value = "Tier 1-2",
      subtitle = "FRED/BLS official sources",
      icon = icon("certificate"),
      color = "green"
    )
  })

  output$table_summary_stats <- renderDT({
    # Create high-level summary statistics by category
    stats_df <- data.table(
      Category = c("Inflation (CPI/PCE)", "Interest Rates (Treasury Yields)", "Employment (BLS)"),
      `Total Series` = c(
        length(unique(inflation_data$series_id)),
        length(unique(rates_data$series_id)),
        length(unique(employment_data$series_id))
      ),
      `Total Records` = c(
        nrow(inflation_data),
        nrow(rates_data),
        nrow(employment_data)
      ),
      `Date Range Start` = c(
        min(inflation_data$date),
        min(rates_data$date),
        min(employment_data$date)
      ),
      `Date Range End` = c(
        max(inflation_data$date),
        max(rates_data$date),
        max(employment_data$date)
      ),
      `Data Freshness (days)` = c(
        as.numeric(Sys.Date() - max(inflation_data$date)),
        as.numeric(Sys.Date() - max(rates_data$date)),
        as.numeric(Sys.Date() - max(employment_data$date))
      ),
      `Quality Tier` = c("Tier 1 (BEA/BLS)", "Tier 1 (Federal Reserve)", "Tier 2/3 (BLS)")
    )

    datatable(
      stats_df,
      options = list(
        pageLength = 10,
        dom = "t",
        ordering = FALSE
      ),
      rownames = FALSE
    ) %>%
      formatDate(c("Date Range Start", "Date Range End"), method = "toLocaleDateString") %>%
      formatRound("Total Records", digits = 0, mark = ",")
  })

  output$table_data_summary <- renderDT({
    summary_df <- rbindlist(list(
      inflation_data[, .(
        Category = "Inflation",
        `Series ID` = series_id,
        `First Date` = min(date),
        `Last Date` = max(date),
        Observations = .N,
        `Latest Value` = last(value)
      ), by = series_id],
      employment_data[, .(
        Category = "Employment",
        `Series ID` = series_id,
        `First Date` = min(date),
        `Last Date` = max(date),
        Observations = .N,
        `Latest Value` = last(value)
      ), by = series_id]
    ))

    datatable(
      summary_df,
      options = list(
        pageLength = 15,
        scrollX = TRUE,
        order = list(list(0, "asc"))
      ),
      filter = "top",
      rownames = FALSE
    )
  })

  # ========================================================================
  # DOWNLOAD HANDLERS
  # ========================================================================

  # Download inflation data
  output$download_inflation <- downloadHandler(
    filename = function() {
      paste0(
        "StarCruiser_Inflation_",
        format(date_range_debounced()[1], "%Y%m%d"), "_to_",
        format(date_range_debounced()[2], "%Y%m%d"), "_",
        format(Sys.Date(), "%Y%m%d"), ".csv"
      )
    },
    content = function(file) {
      data_to_export <- inflation_filtered()[, .(date, series_id, value, yoy_change)]
      fwrite(data_to_export, file)
    }
  )

  # Download yield curve data
  output$download_yields <- downloadHandler(
    filename = function() {
      paste0(
        "StarCruiser_Yields_",
        format(date_range_debounced()[1], "%Y%m%d"), "_to_",
        format(date_range_debounced()[2], "%Y%m%d"), "_",
        format(Sys.Date(), "%Y%m%d"), ".csv"
      )
    },
    content = function(file) {
      # Include rates data and spreads
      rates_export <- rates_filtered()[, .(date, series_id, value)]
      spreads_export <- yield_spreads[
        date >= date_range_debounced()[1] &
          date <= date_range_debounced()[2],
        .(
          date,
          spread_2_10,
          spread_3mo_10yr
        )
      ]

      # Combine rates and spreads
      combined_export <- merge(rates_export, spreads_export, by = "date", all.x = TRUE)
      fwrite(combined_export, file)
    }
  )

  # Download employment data
  output$download_employment <- downloadHandler(
    filename = function() {
      paste0(
        "StarCruiser_Employment_",
        format(date_range_debounced()[1], "%Y%m%d"), "_to_",
        format(date_range_debounced()[2], "%Y%m%d"), "_",
        format(Sys.Date(), "%Y%m%d"), ".csv"
      )
    },
    content = function(file) {
      data_to_export <- employment_filtered()[, .(date, series_id, value)]
      fwrite(data_to_export, file)
    }
  )

  # Download data catalog
  output$download_catalog <- downloadHandler(
    filename = function() {
      paste0(
        "StarCruiser_DataCatalog_",
        format(Sys.Date(), "%Y%m%d"), ".csv"
      )
    },
    content = function(file) {
      # Export the data summary table
      summary_df <- rbindlist(list(
        inflation_data[, .(
          Category = "Inflation",
          Series_ID = series_id,
          First_Date = min(date),
          Last_Date = max(date),
          Observations = .N,
          Latest_Value = last(value)
        ), by = series_id],
        employment_data[, .(
          Category = "Employment",
          Series_ID = series_id,
          First_Date = min(date),
          Last_Date = max(date),
          Observations = .N,
          Latest_Value = last(value)
        ), by = series_id]
      ))
      fwrite(summary_df, file)
    }
  )

  # ========================================================================
  # GEOGRAPHIC TAB SERVER
  # ========================================================================
  geographic_server(input, output, session, cluster_data, NULL)

  # ========================================================================
  # TREASURY MODULE SERVER
  # ========================================================================
  treasury_server("treasury_module", reactive({
    rates_data
  }))

  # ========================================================================
  # INFLATION MODULE SERVER
  # ========================================================================
  inflation_server("inflation_module", reactive({
    inflation_data
  }))

  # ========================================================================
  # LABOR DYNAMICS MODULE SERVER
  # ========================================================================
  labor_dynamics_server("labor_dynamics_module")

  # ========================================================================
  # WAGES & HOURS MODULE SERVER
  # ========================================================================
  wages_hours_server("wages_hours_module")

  # ========================================================================
  # CORRELATION MODULE SERVER (Track A1.1)
  # ========================================================================
  correlation_server("correlation_module",
    reactive({ inflation_data }),
    reactive({ employment_data }),
    reactive({ rates_data })
  )

  # ========================================================================
  # RECESSION/CYCLE MODULE SERVER (Track A1.2+A1.3)
  # ========================================================================
  recession_server("recession_module",
    reactive({ employment_data }),
    reactive({ rates_data }),
    reactive({ inflation_data }),
    yield_spreads,
    sahm_data,
    recession_periods
  )

  # ========================================================================
  # QUALITY DEGRADATION MODULE SERVER (Track A2.1)
  # ========================================================================
  quality_degradation_server("quality_degradation_module")

  # ========================================================================
  # REAL-TIME INDICATORS MODULE SERVER (Track C2.1)
  # ========================================================================
  realtime_server("realtime_module", reactive({ employment_data }))

  # ========================================================================
  # v7.0 ECONOMY MODULE SERVERS
  # ========================================================================
  gdp_output_server("gdp_output_module",
    gdp_data, production_data, date_range_debounced)

  consumer_server("consumer_module",
    spending_data, housing_data, date_range_debounced)

  housing_server("housing_module",
    housing_data, date_range_debounced)

  financial_server("financial_module",
    financial_data, money_data, date_range_debounced)

  trade_fiscal_server("trade_fiscal_module",
    trade_data, fiscal_data, date_range_debounced)

  health_score_server("health_score_module",
    inflation_data, employment_data, gdp_data,
    production_data, housing_data, financial_data,
    spending_data, yield_spreads)

  # ========================================================================
  # v8.0 ECONOMIC INTELLIGENCE MODULE SERVERS
  # ========================================================================
  regional_economy_server("regional_module",
    bea_state_gdp, bea_state_gdp_industry, bea_state_income)

  state_comparison_server("state_compare_module",
    bea_state_gdp, bea_state_income, fdic_banks, employment_data)

  productive_economy_server("productive_module",
    production_data, gdp_data, money_data, bea_nipa, date_range_debounced)

  economic_flows_server("flows_module",
    bea_nipa, gdp_data)

  banking_sector_server("banking_module",
    fdic_banks, fdic_universe)

  financial_real_server("fin_real_module",
    money_data, gdp_data, financial_data, date_range_debounced)
}

# RUN APPLICATION
shinyApp(ui = ui, server = server)
