# ============================================================================
# TREASURY MARKET MODULE - StarCruiser Dashboard
# ============================================================================
# Purpose: Treasury market analysis visualizations
# Features:
#   - Yield curve visualization
#   - Yield spread analysis (2s10s, 3mo10y)
#   - Real yields and breakeven inflation
#   - Fed policy analysis
#   - Foreign holdings (TIC data)
# ============================================================================

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

#' Load treasury data from the rates dataset
#' @return data.table with treasury yields
load_treasury_data <- function() {
  # Use the already-loaded rates_data from global.R
  if (!exists("rates_data") || is.null(rates_data)) {
    message("Warning: rates_data not available")
    return(NULL)
  }

  return(rates_data)
}

#' Calculate yield spreads
#' @param dt data.table with treasury data
#' @return data.table with yield spreads
calculate_spreads <- function(dt) {
  if (is.null(dt)) return(NULL)

  # Pivot to wide format
  wide <- dcast(dt, date ~ series_id, value.var = "value")

  # Calculate spreads
  spreads <- data.table(date = wide$date)

  # 2s10s spread
  if ("DGS2" %in% names(wide) && "DGS10" %in% names(wide)) {
    spreads[, spread_2s10s := wide$DGS10 - wide$DGS2]
  }

  # 3mo10y spread
  if ("DTB3" %in% names(wide) && "DGS10" %in% names(wide)) {
    spreads[, spread_3mo10y := wide$DGS10 - wide$DTB3]
  }

  # 2s30s spread
  if ("DGS2" %in% names(wide) && "DGS30" %in% names(wide)) {
    spreads[, spread_2s30s := wide$DGS30 - wide$DGS2]
  }

  # Fed funds vs 2-year
  if ("DFF" %in% names(wide) && "DGS2" %in% names(wide)) {
    spreads[, fed_vs_2y := wide$DGS2 - wide$DFF]
  }

  return(spreads)
}

#' Get latest yield curve data
#' @param dt data.table with treasury data
#' @param target_date Date to get curve for (defaults to latest)
#' @return data.table with maturity and yield
get_yield_curve <- function(dt, target_date = NULL) {
  if (is.null(dt)) return(NULL)

  if (is.null(target_date)) {
    target_date <- max(dt$date, na.rm = TRUE)
  }

  # Define maturity mapping
  maturity_map <- data.table(
    series_id = c("DTB3", "DTB6", "DGS1", "DGS2", "DGS5", "DGS7", "DGS10", "DGS20", "DGS30"),
    maturity = c(0.25, 0.5, 1, 2, 5, 7, 10, 20, 30),
    label = c("3M", "6M", "1Y", "2Y", "5Y", "7Y", "10Y", "20Y", "30Y")
  )

  # Get data for target date
  day_data <- dt[date == target_date]

  # Merge with maturity mapping
  curve <- merge(day_data, maturity_map, by = "series_id")
  curve <- curve[order(maturity)]

  return(curve)
}

# ============================================================================
# UI FUNCTION
# ============================================================================

treasury_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      # Controls
      box(
        title = "Treasury Market Controls",
        width = 12,
        status = "primary",
        solidHeader = TRUE,
        collapsible = TRUE,
        collapsed = FALSE,
        fluidRow(
          column(4,
            dateRangeInput(
              ns("date_range"),
              "Date Range:",
              start = Sys.Date() - 365 * 2,
              end = Sys.Date(),
              min = "2000-01-01",
              max = Sys.Date()
            )
          ),
          column(4,
            selectInput(
              ns("spread_type"),
              "Spread Type:",
              choices = c(
                "2s10s (Classic)" = "spread_2s10s",
                "3mo10y (Fed Preferred)" = "spread_3mo10y",
                "2s30s" = "spread_2s30s",
                "Fed Funds vs 2Y" = "fed_vs_2y"
              ),
              selected = "spread_2s10s"
            )
          ),
          column(4,
            checkboxInput(
              ns("show_recession"),
              "Show Recession Shading",
              value = TRUE
            )
          )
        )
      )
    ),

    # Value boxes row
    fluidRow(
      valueBoxOutput(ns("vb_fed_funds"), width = 3),
      valueBoxOutput(ns("vb_10y"), width = 3),
      valueBoxOutput(ns("vb_2s10s"), width = 3),
      valueBoxOutput(ns("vb_breakeven"), width = 3)
    ),

    # Yield curve row
    fluidRow(
      box(
        title = "Current Yield Curve",
        width = 6,
        status = "info",
        solidHeader = TRUE,
        echarts4rOutput(ns("yield_curve_chart"), height = "350px")
      ),
      box(
        title = "Yield Curve Table",
        width = 6,
        status = "info",
        solidHeader = TRUE,
        DTOutput(ns("yield_curve_table"))
      )
    ),

    # Spread analysis row
    fluidRow(
      box(
        title = "Yield Spread History",
        width = 12,
        status = "warning",
        solidHeader = TRUE,
        echarts4rOutput(ns("spread_chart"), height = "350px"),
        p(class = "text-muted",
          "Shaded areas indicate periods when the yield curve was inverted (negative spread).
           Inversions have historically preceded recessions by 12-18 months.")
      )
    ),

    # Real yields row
    fluidRow(
      box(
        title = "Real Yields (TIPS)",
        width = 6,
        status = "success",
        solidHeader = TRUE,
        echarts4rOutput(ns("real_yields_chart"), height = "300px")
      ),
      box(
        title = "Breakeven Inflation (Market Expectations)",
        width = 6,
        status = "success",
        solidHeader = TRUE,
        echarts4rOutput(ns("breakeven_chart"), height = "300px")
      )
    ),

    # Treasury rates row
    fluidRow(
      box(
        title = "Key Treasury Rates",
        width = 12,
        status = "primary",
        solidHeader = TRUE,
        echarts4rOutput(ns("rates_chart"), height = "350px")
      )
    )
  )
}

# ============================================================================
# SERVER FUNCTION
# ============================================================================

treasury_server <- function(id, treasury_data) {
  moduleServer(id, function(input, output, session) {

    # Reactive for filtered data
    filtered_data <- reactive({
      req(treasury_data())

      dt <- treasury_data()
      dt <- dt[date >= input$date_range[1] & date <= input$date_range[2]]

      return(dt)
    })

    # Calculate spreads reactively
    spreads_data <- reactive({
      req(filtered_data())
      calculate_spreads(filtered_data())
    })

    # Get yield curve
    yield_curve_data <- reactive({
      req(treasury_data())
      get_yield_curve(treasury_data())
    })

    # ---- VALUE BOXES ----

    output$vb_fed_funds <- renderValueBox({
      req(treasury_data())
      latest <- treasury_data()[series_id == "DFF"][order(-date)][1]
      val <- if (nrow(latest) > 0 && !is.na(latest$value)) {
        sprintf("%.2f%%", latest$value)
      } else "N/A"

      valueBox(
        val,
        "Fed Funds Rate",
        icon = icon("university"),
        color = "blue"
      )
    })

    output$vb_10y <- renderValueBox({
      req(treasury_data())
      latest <- treasury_data()[series_id == "DGS10"][order(-date)][1]
      val <- if (nrow(latest) > 0 && !is.na(latest$value)) {
        sprintf("%.2f%%", latest$value)
      } else "N/A"

      valueBox(
        val,
        "10-Year Treasury",
        icon = icon("chart-line"),
        color = "green"
      )
    })

    output$vb_2s10s <- renderValueBox({
      req(spreads_data())
      latest <- spreads_data()[order(-date)][1]
      val <- if (nrow(latest) > 0 && !is.na(latest$spread_2s10s)) {
        sprintf("%.2f%%", latest$spread_2s10s)
      } else "N/A"

      # Color based on inversion
      color <- if (!is.na(latest$spread_2s10s) && latest$spread_2s10s < 0) "red" else "yellow"

      valueBox(
        val,
        "2s10s Spread",
        icon = icon("exchange-alt"),
        color = color
      )
    })

    output$vb_breakeven <- renderValueBox({
      req(treasury_data())
      latest <- treasury_data()[series_id == "T10YIE"][order(-date)][1]
      val <- if (nrow(latest) > 0 && !is.na(latest$value)) {
        sprintf("%.2f%%", latest$value)
      } else "N/A"

      valueBox(
        val,
        "10Y Breakeven Inflation",
        icon = icon("fire"),
        color = "orange"
      )
    })

    # ---- YIELD CURVE CHART ----

    output$yield_curve_chart <- renderEcharts4r({
      req(yield_curve_data())
      curve <- yield_curve_data()

      if (nrow(curve) == 0) {
        return(e_charts() %>% e_title("No data available"))
      }

      curve %>%
        e_charts(label) %>%
        e_line(value, smooth = TRUE, symbol = "circle", symbolSize = 10) %>%
        e_area(value, smooth = TRUE) %>%
        e_y_axis(
          name = "Yield (%)",
          nameLocation = "middle",
          nameGap = 40,
          axisLabel = list(formatter = "{value}%")
        ) %>%
        e_x_axis(name = "Maturity") %>%
        e_tooltip(
          trigger = "axis",
          formatter = htmlwidgets::JS("
            function(params) {
              return params[0].name + ': ' + params[0].value[1].toFixed(3) + '%';
            }
          ")
        ) %>%
        e_title(
          text = paste("Yield Curve -", format(max(curve$date), "%Y-%m-%d")),
          left = "center"
        ) %>%
        e_legend(show = FALSE) %>%
        e_color("#3498db") %>%
        e_grid(left = "10%", right = "5%", bottom = "15%") %>%
        e_toolbox_feature(feature = "saveAsImage")
    })

    # ---- YIELD CURVE TABLE ----

    output$yield_curve_table <- renderDT({
      req(yield_curve_data())
      curve <- yield_curve_data()

      display <- data.table(
        Maturity = curve$label,
        Yield = sprintf("%.3f%%", curve$value)
      )

      datatable(
        display,
        options = list(
          pageLength = 10,
          dom = 't',
          ordering = FALSE
        ),
        rownames = FALSE
      )
    })

    # ---- SPREAD CHART ----

    output$spread_chart <- renderEcharts4r({
      req(spreads_data())
      spreads <- spreads_data()
      spread_col <- input$spread_type

      if (!spread_col %in% names(spreads)) {
        return(e_charts() %>% e_title("Spread data not available"))
      }

      # Prepare data
      plot_data <- spreads[!is.na(get(spread_col))]
      setnames(plot_data, spread_col, "spread", skip_absent = TRUE)

      # Identify inversions
      plot_data[, inverted := spread < 0]

      chart <- plot_data %>%
        e_charts(date) %>%
        e_line(spread, smooth = FALSE, symbol = "none", name = "Spread") %>%
        e_mark_line(
          data = list(yAxis = 0),
          lineStyle = list(color = "red", type = "dashed"),
          label = list(show = FALSE)
        ) %>%
        e_y_axis(
          name = "Spread (%)",
          nameLocation = "middle",
          nameGap = 40,
          axisLabel = list(formatter = "{value}%")
        ) %>%
        e_x_axis(type = "time") %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_legend(show = TRUE, bottom = 30) %>%
        e_grid(left = "10%", right = "5%", bottom = "20%") %>%
        e_toolbox_feature(feature = "saveAsImage")

      # Add recession shading if enabled
      if (input$show_recession) {
        chart <- add_recession_bands(chart, input$date_range)
      }

      chart
    })

    # ---- REAL YIELDS CHART ----

    output$real_yields_chart <- renderEcharts4r({
      req(filtered_data())

      real_series <- c("DFII5", "DFII10", "DFII30")
      real_data <- filtered_data()[series_id %chin% real_series]

      if (nrow(real_data) == 0) {
        return(e_charts() %>% e_title("TIPS data not available"))
      }

      # Pivot
      wide <- dcast(real_data, date ~ series_id, value.var = "value")

      chart <- wide %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(
          name = "Real Yield (%)",
          nameLocation = "middle",
          nameGap = 40
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_grid(left = "12%", right = "5%", bottom = "15%") %>%
        e_toolbox_feature(feature = "saveAsImage")

      if ("DFII5" %in% names(wide)) {
        chart <- chart %>% e_line(DFII5, name = "5Y TIPS", smooth = FALSE, symbol = "none")
      }
      if ("DFII10" %in% names(wide)) {
        chart <- chart %>% e_line(DFII10, name = "10Y TIPS", smooth = FALSE, symbol = "none")
      }
      if ("DFII30" %in% names(wide)) {
        chart <- chart %>% e_line(DFII30, name = "30Y TIPS", smooth = FALSE, symbol = "none")
      }

      chart
    })

    # ---- BREAKEVEN CHART ----

    output$breakeven_chart <- renderEcharts4r({
      req(filtered_data())

      be_series <- c("T5YIE", "T10YIE", "T5YIFR")
      be_data <- filtered_data()[series_id %chin% be_series]

      if (nrow(be_data) == 0) {
        return(e_charts() %>% e_title("Breakeven data not available"))
      }

      # Pivot
      wide <- dcast(be_data, date ~ series_id, value.var = "value")

      chart <- wide %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(
          name = "Breakeven (%)",
          nameLocation = "middle",
          nameGap = 40
        ) %>%
        e_mark_line(
          data = list(yAxis = 2),
          lineStyle = list(color = "green", type = "dashed"),
          label = list(formatter = "2% Target", position = "end")
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_grid(left = "12%", right = "5%", bottom = "15%") %>%
        e_toolbox_feature(feature = "saveAsImage")

      if ("T5YIE" %in% names(wide)) {
        chart <- chart %>% e_line(T5YIE, name = "5Y Breakeven", smooth = FALSE, symbol = "none")
      }
      if ("T10YIE" %in% names(wide)) {
        chart <- chart %>% e_line(T10YIE, name = "10Y Breakeven", smooth = FALSE, symbol = "none")
      }
      if ("T5YIFR" %in% names(wide)) {
        chart <- chart %>% e_line(T5YIFR, name = "5Y5Y Forward", smooth = FALSE, symbol = "none")
      }

      chart
    })

    # ---- KEY RATES CHART ----

    output$rates_chart <- renderEcharts4r({
      req(filtered_data())

      key_series <- c("DFF", "DGS2", "DGS10", "DGS30")
      rates <- filtered_data()[series_id %chin% key_series]

      if (nrow(rates) == 0) {
        return(e_charts() %>% e_title("Rates data not available"))
      }

      # Pivot
      wide <- dcast(rates, date ~ series_id, value.var = "value")

      chart <- wide %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(
          name = "Yield (%)",
          nameLocation = "middle",
          nameGap = 40
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_datazoom(type = "slider") %>%
        e_grid(left = "10%", right = "5%", bottom = "20%") %>%
        e_toolbox_feature(feature = "saveAsImage")

      if ("DFF" %in% names(wide)) {
        chart <- chart %>% e_line(DFF, name = "Fed Funds", smooth = FALSE, symbol = "none")
      }
      if ("DGS2" %in% names(wide)) {
        chart <- chart %>% e_line(DGS2, name = "2Y Treasury", smooth = FALSE, symbol = "none")
      }
      if ("DGS10" %in% names(wide)) {
        chart <- chart %>% e_line(DGS10, name = "10Y Treasury", smooth = FALSE, symbol = "none")
      }
      if ("DGS30" %in% names(wide)) {
        chart <- chart %>% e_line(DGS30, name = "30Y Treasury", smooth = FALSE, symbol = "none")
      }

      # Add recession shading
      if (input$show_recession) {
        chart <- add_recession_bands(chart, input$date_range)
      }

      chart
    })

  })
}
