# ============================================================================
# ECONOMIC HEALTH SCORE MODULE - StarCruiser Dashboard v7.0
# ============================================================================
# Composite Economic Health Index (0-100) synthesizing 11 weighted components
# across output, labor, inflation, financial, housing, and consumer dimensions
# ============================================================================

# Component definitions: series_id, weight, good_threshold, bad_threshold, invert
HEALTH_COMPONENTS <- list(
  list(name = "GDP Growth", series = "A191RL1Q225SBEA", weight = 0.20,
       good = 3.0, bad = 0.0, invert = FALSE, source = "gdp"),
  list(name = "Unemployment", series = "UNRATE", weight = 0.15,
       good = 4.0, bad = 6.0, invert = TRUE, source = "employment"),
  list(name = "Industrial Production", series = "INDPRO", weight = 0.10,
       good = 2.0, bad = -2.0, invert = FALSE, source = "production", use_yoy = TRUE),
  list(name = "Inflation (vs 2%)", series = "CPIAUCSL", weight = 0.10,
       good = 1.0, bad = 3.0, invert = TRUE, source = "inflation", use_deviation = TRUE),
  list(name = "Housing Starts", series = "HOUST", weight = 0.08,
       good = 5.0, bad = -15.0, invert = FALSE, source = "housing", use_yoy = TRUE),
  list(name = "Consumer Sentiment", series = "UMCSENT", weight = 0.08,
       good = 90, bad = 70, invert = FALSE, source = "housing"),
  list(name = "Financial Stress", series = "NFCI", weight = 0.08,
       good = 0, bad = 0.5, invert = TRUE, source = "financial"),
  list(name = "Yield Curve", series = "spread_2_10", weight = 0.08,
       good = 1.0, bad = 0, invert = FALSE, source = "yield_spreads"),
  list(name = "Retail Sales", series = "RSXFS", weight = 0.05,
       good = 3.0, bad = -2.0, invert = FALSE, source = "spending", use_yoy = TRUE),
  list(name = "Initial Claims", series = "ICSA", weight = 0.05,
       good = 225000, bad = 300000, invert = TRUE, source = "employment"),
  list(name = "VIX", series = "VIXCLS", weight = 0.03,
       good = 20, bad = 30, invert = TRUE, source = "financial")
)

#' Normalize a value to 0-100 scale based on good/bad thresholds
#' @param value The raw value
#' @param good The "good" threshold (100 score)
#' @param bad The "bad" threshold (0 score)
#' @param invert If TRUE, lower values are better
normalize_score <- function(value, good, bad, invert = FALSE) {
  if (is.na(value)) return(NA_real_)
  if (invert) {
    # Lower is better (e.g., unemployment, VIX)
    score <- (bad - value) / (bad - good) * 100
  } else {
    # Higher is better (e.g., GDP growth)
    score <- (value - bad) / (good - bad) * 100
  }
  pmin(100, pmax(0, score))
}

# UI
health_score_ui <- function(id) {
  ns <- NS(id)
  tagList(
    # Main gauge
    fluidRow(
      box(title = "Composite Economic Health Index", width = 4,
          echarts4rOutput(ns("health_gauge"), height = "300px"),
          solidHeader = TRUE, status = "primary"),
      box(title = "Component Breakdown", width = 8,
          echarts4rOutput(ns("component_bars"), height = "300px"),
          solidHeader = TRUE, status = "info")
    ),
    # Historical score
    fluidRow(
      box(title = "Economic Health Score Over Time", width = 12,
          echarts4rOutput(ns("health_timeline"), height = "350px"),
          helpText("Composite score: 0 = severe recession, 50 = neutral, 100 = strong expansion"),
          solidHeader = TRUE, status = "primary")
    )
  )
}

# SERVER
health_score_server <- function(id, inflation_data, employment_data,
                                 gdp_data, production_data, housing_data,
                                 financial_data, spending_data, yield_spreads) {
  moduleServer(id, function(input, output, session) {

    # Get latest value for a series from a dataset
    get_latest <- function(data, series_id_val) {
      if (is.null(data)) return(NA_real_)
      latest <- data[series_id == series_id_val][order(-date)][1]
      if (nrow(latest) == 0) return(NA_real_)
      latest$value
    }

    get_latest_yoy <- function(data, series_id_val) {
      if (is.null(data)) return(NA_real_)
      dt <- data[series_id == series_id_val][order(date)]
      if (nrow(dt) < 13) return(NA_real_)
      current <- dt[.N]$value
      year_ago <- dt[.N - 12]$value
      if (is.na(current) || is.na(year_ago) || year_ago == 0) return(NA_real_)
      (current / year_ago - 1) * 100
    }

    # Compute current component scores
    component_scores <- reactive({
      scores <- data.table(
        Component = character(0),
        Raw_Value = numeric(0),
        Score = numeric(0),
        Weight = numeric(0),
        Weighted = numeric(0)
      )

      for (comp in HEALTH_COMPONENTS) {
        # Get the data source
        data_src <- switch(comp$source,
          "gdp" = gdp_data,
          "employment" = employment_data,
          "production" = production_data,
          "inflation" = inflation_data,
          "housing" = housing_data,
          "financial" = financial_data,
          "spending" = spending_data,
          "yield_spreads" = NULL
        )

        # Get value
        if (comp$source == "yield_spreads") {
          if (!is.null(yield_spreads)) {
            latest <- yield_spreads[!is.na(spread_2_10)][order(-date)][1]
            raw_val <- if (nrow(latest) > 0) latest$spread_2_10 else NA_real_
          } else {
            raw_val <- NA_real_
          }
        } else if (!is.null(comp$use_yoy) && comp$use_yoy) {
          raw_val <- get_latest_yoy(data_src, comp$series)
        } else if (!is.null(comp$use_deviation) && comp$use_deviation) {
          raw_val <- abs(get_latest_yoy(data_src, comp$series) - 2.0)  # Deviation from 2% target
        } else {
          raw_val <- get_latest(data_src, comp$series)
        }

        score <- normalize_score(raw_val, comp$good, comp$bad, comp$invert)
        weighted <- if (!is.na(score)) score * comp$weight else 0

        scores <- rbind(scores, data.table(
          Component = comp$name,
          Raw_Value = round(raw_val, 2),
          Score = round(score, 0),
          Weight = comp$weight * 100,
          Weighted = round(weighted, 1)
        ))
      }

      scores
    })

    composite_score <- reactive({
      scores <- component_scores()
      sum(scores$Weighted, na.rm = TRUE)
    })

    # Gauge
    output$health_gauge <- renderEcharts4r({
      val <- round(composite_score())

      data.table(name = "Health", value = val) %>%
        e_charts() %>%
        e_gauge(value, name = "Economic Health",
          min = 0, max = 100,
          axisLine = list(lineStyle = list(width = 20, color = list(
            list(0.20, "#c23531"),  # 0-20 Severe
            list(0.40, "#ee6666"),  # 20-40 Weak
            list(0.60, "#fac858"),  # 40-60 Neutral
            list(0.80, "#91cc75"),  # 60-80 Good
            list(1.00, "#3ba272")   # 80-100 Strong
          ))),
          detail = list(formatter = "{value}", fontSize = 32,
                        offsetCenter = list(0, "60%")),
          pointer = list(length = "60%")
        ) %>%
        e_tooltip()
    })

    # Component bars
    output$component_bars <- renderEcharts4r({
      scores <- component_scores()
      if (nrow(scores) == 0) return(NULL)

      scores[order(-Score)] %>%
        e_charts(Component) %>%
        e_bar(Score, itemStyle = list(color = htmlwidgets::JS("
          function(params) {
            var v = params.value[1];
            if (v >= 80) return '#3ba272';
            if (v >= 60) return '#91cc75';
            if (v >= 40) return '#fac858';
            if (v >= 20) return '#ee6666';
            return '#c23531';
          }
        "))) %>%
        e_flip_coords() %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>Score: ' + params.value[0] + '/100';
          }
        ")) %>%
        e_x_axis(name = "Score (0-100)", min = 0, max = 100) %>%
        e_legend(show = FALSE) %>%
        e_grid(left = "30%")
    })

    # Historical timeline (simplified -- use latest available data to compute score over time)
    output$health_timeline <- renderEcharts4r({
      # Use unemployment as a proxy timeline (available monthly, long history)
      if (is.null(employment_data)) return(NULL)

      unrate <- employment_data[series_id == "UNRATE"][order(date)]
      if (nrow(unrate) < 12) return(NULL)

      # Simple historical health proxy: inverted unemployment score
      unrate[, health_proxy := pmin(100, pmax(0, (6 - value) / (6 - 4) * 100))]

      chart <- unrate %>%
        e_charts(date) %>%
        e_line(health_proxy, symbol = "none", color = "#3c8dbc", sampling = "lttb",
               name = "Health Score (labor proxy)") %>%
        e_mark_line(data = list(yAxis = 50), lineStyle = list(color = "#aaa", type = "dashed"),
                    label = list(formatter = "Neutral")) %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Health Score", min = 0, max = 100) %>%
        e_legend(show = FALSE)

      add_recession_bands(chart)
    })
  })
}
