# ============================================================================
# CORRELATION & LEAD-LAG ANALYSIS MODULE - StarCruiser Dashboard
# ============================================================================
# Track A1.1: Discover relationships between economic indicators
# Features: Correlation matrix heatmap, cross-correlation, rolling correlations,
#           Granger causality tests
# ============================================================================

# Key series for correlation analysis
CORRELATION_SERIES <- c(
  "CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE",  # Inflation
  "UNRATE", "PAYEMS", "CIVPART",                   # Employment
  "DGS2", "DGS10", "DTB3", "DGS30",               # Treasury yields
  "FEDFUNDS"                                        # Fed policy
)

SERIES_LABELS <- c(
  CPIAUCSL = "CPI (All)", CPILFESL = "Core CPI", PCEPI = "PCE", PCEPILFE = "Core PCE",
  UNRATE = "Unemployment", PAYEMS = "Nonfarm Payrolls", CIVPART = "LFPR",
  DGS2 = "2Y Yield", DGS10 = "10Y Yield", DTB3 = "3mo T-Bill",
  DGS30 = "30Y Yield", FEDFUNDS = "Fed Funds",
  spread_2_10 = "2s10s Spread"
)

# UI
correlation_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      box(
        title = "Series Selection", width = 12, collapsible = TRUE,
        fluidRow(
          column(4,
            selectInput(ns("series_x"), "Series X:",
              choices = setNames(names(SERIES_LABELS), SERIES_LABELS),
              selected = "UNRATE"
            )
          ),
          column(4,
            selectInput(ns("series_y"), "Series Y:",
              choices = setNames(names(SERIES_LABELS), SERIES_LABELS),
              selected = "spread_2_10"
            )
          ),
          column(4,
            sliderInput(ns("window_months"), "Rolling Window (months):",
              min = 12, max = 240, value = 60, step = 12
            )
          )
        )
      )
    ),

    fluidRow(
      box(
        title = "Correlation Matrix (Monthly Data)",
        echarts4rOutput(ns("correlation_heatmap"), height = "500px"),
        width = 12, solidHeader = TRUE, status = "primary"
      )
    ),

    fluidRow(
      box(
        title = "Cross-Correlation Function (Lead-Lag)",
        echarts4rOutput(ns("lead_lag_chart"), height = "400px"),
        helpText("Positive lags = X leads Y. Negative lags = Y leads X."),
        width = 6, solidHeader = TRUE, status = "info"
      ),
      box(
        title = "Rolling Correlation",
        echarts4rOutput(ns("rolling_corr_chart"), height = "400px"),
        width = 6, solidHeader = TRUE, status = "info"
      )
    ),

    fluidRow(
      box(
        title = "Granger Causality Tests",
        DTOutput(ns("granger_table")),
        helpText("p < 0.05 suggests the row variable helps predict the column variable."),
        width = 12, solidHeader = TRUE, status = "warning"
      )
    ),

    fluidRow(
      box(
        title = "Download Results", width = 12,
        downloadButton(ns("download_corr"), "Download Correlation Matrix (CSV)", icon = icon("download"))
      )
    )
  )
}

# SERVER
correlation_server <- function(id, inflation_data, employment_data, rates_data) {
  moduleServer(id, function(input, output, session) {

    # Build combined monthly dataset (wide format)
    combined_wide <- reactive({
      # Collect all three datasets
      inf <- inflation_data()
      emp <- employment_data()
      rat <- rates_data()

      all_data <- rbindlist(list(inf, emp, rat), use.names = TRUE, fill = TRUE)

      # Filter to series of interest
      all_data <- all_data[series_id %chin% CORRELATION_SERIES]

      # Aggregate to monthly (last value per month for daily series)
      all_data[, month := floor_date(date, "month")]
      monthly <- all_data[, .(value = last(value)), by = .(series_id, month)]

      # Pivot to wide format
      wide <- dcast(monthly, month ~ series_id, value.var = "value")

      # Add yield spread if both DGS2 and DGS10 present
      if (all(c("DGS2", "DGS10") %in% names(wide))) {
        wide[, spread_2_10 := DGS10 - DGS2]
      }

      # Sort by month
      setorder(wide, month)

      # Remove rows with too many NAs
      series_cols <- setdiff(names(wide), "month")
      wide <- wide[rowSums(!is.na(wide[, ..series_cols])) >= 3]

      wide
    })

    # Correlation matrix
    corr_matrix <- reactive({
      wide <- combined_wide()
      series_cols <- intersect(names(SERIES_LABELS), names(wide))
      if (length(series_cols) < 2) return(NULL)

      mat <- cor(wide[, ..series_cols], use = "pairwise.complete.obs")
      mat
    })

    # Heatmap
    output$correlation_heatmap <- renderEcharts4r({
      mat <- corr_matrix()
      req(mat)

      # Convert to long format for echarts heatmap
      labels <- SERIES_LABELS[rownames(mat)]
      n <- nrow(mat)

      heatmap_data <- data.table(
        x = rep(labels, each = n),
        y = rep(labels, times = n),
        value = as.vector(mat)
      )

      heatmap_data %>%
        e_charts(x) %>%
        e_heatmap(y, value) %>%
        e_visual_map(
          value,
          inRange = list(color = c("#2166ac", "#f7f7f7", "#b2182b")),
          min = -1, max = 1,
          calculable = TRUE
        ) %>%
        e_tooltip(
          formatter = htmlwidgets::JS("
            function(params) {
              return params.value[0] + ' vs ' + params.value[1] +
                     '<br>Correlation: ' + params.value[2].toFixed(3);
            }
          ")
        ) %>%
        e_x_axis(axisLabel = list(rotate = 45, interval = 0, fontSize = 10)) %>%
        e_y_axis(axisLabel = list(fontSize = 10)) %>%
        e_grid(left = "20%", bottom = "20%")
    })

    # Cross-correlation function
    output$lead_lag_chart <- renderEcharts4r({
      wide <- combined_wide()
      req(input$series_x %in% names(wide), input$series_y %in% names(wide))

      x <- wide[[input$series_x]]
      y <- wide[[input$series_y]]

      # Remove NAs (pairwise)
      valid <- !is.na(x) & !is.na(y)
      x <- x[valid]
      y <- y[valid]

      if (length(x) < 30) return(NULL)

      # Compute CCF manually
      max_lag <- 24
      lags <- seq(-max_lag, max_lag)
      ccf_vals <- numeric(length(lags))

      for (i in seq_along(lags)) {
        lag <- lags[i]
        if (lag >= 0) {
          ccf_vals[i] <- cor(x[1:(length(x) - lag)], y[(1 + lag):length(y)], use = "complete.obs")
        } else {
          alag <- abs(lag)
          ccf_vals[i] <- cor(x[(1 + alag):length(x)], y[1:(length(y) - alag)], use = "complete.obs")
        }
      }

      ccf_dt <- data.table(lag = lags, correlation = round(ccf_vals, 4))

      # Color bars: positive = blue, negative = red
      ccf_dt[, color := ifelse(correlation >= 0, "#3c8dbc", "#dd4b39")]

      x_label <- SERIES_LABELS[input$series_x]
      y_label <- SERIES_LABELS[input$series_y]

      ccf_dt %>%
        e_charts(lag) %>%
        e_bar(correlation, itemStyle = list(color = htmlwidgets::JS("
          function(params) {
            return params.value[1] >= 0 ? '#3c8dbc' : '#dd4b39';
          }
        "))) %>%
        e_tooltip(
          formatter = htmlwidgets::JS(sprintf("
            function(params) {
              var lag = params.value[0];
              var dir = lag > 0 ? '%s leads %s by ' + lag + ' months' :
                        lag < 0 ? '%s leads %s by ' + Math.abs(lag) + ' months' :
                        'Contemporaneous';
              return dir + '<br>Correlation: ' + params.value[1].toFixed(3);
            }
          ", x_label, y_label, y_label, x_label))
        ) %>%
        e_x_axis(name = "Lag (months)") %>%
        e_y_axis(name = "Correlation", min = -1, max = 1) %>%
        e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "#333", type = "solid"))
    })

    # Rolling correlation
    output$rolling_corr_chart <- renderEcharts4r({
      wide <- combined_wide()
      req(input$series_x %in% names(wide), input$series_y %in% names(wide))

      window <- input$window_months
      x <- wide[[input$series_x]]
      y <- wide[[input$series_y]]
      dates <- wide$month

      n <- length(x)
      if (n < window) return(NULL)

      # Compute rolling correlation
      roll_corr <- numeric(n)
      roll_corr[1:(window - 1)] <- NA

      for (i in window:n) {
        idx <- (i - window + 1):i
        xi <- x[idx]
        yi <- y[idx]
        valid <- !is.na(xi) & !is.na(yi)
        if (sum(valid) >= 10) {
          roll_corr[i] <- cor(xi[valid], yi[valid])
        } else {
          roll_corr[i] <- NA
        }
      }

      roll_dt <- data.table(date = dates, correlation = round(roll_corr, 4))
      roll_dt <- roll_dt[!is.na(correlation)]

      chart <- roll_dt %>%
        e_charts(date) %>%
        e_line(correlation, symbol = "none", color = "#3c8dbc", sampling = "lttb") %>%
        e_mark_line(data = list(yAxis = 0), lineStyle = list(color = "#333", type = "dashed")) %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Correlation", min = -1, max = 1) %>%
        e_x_axis(name = "Date")

      # Add recession bands
      add_recession_bands(chart)
    })

    # Granger causality tests
    output$granger_table <- renderDT({
      wide <- combined_wide()

      # Test key pairs
      test_pairs <- list(
        c("spread_2_10", "UNRATE"),
        c("UNRATE", "PAYEMS"),
        c("FEDFUNDS", "UNRATE"),
        c("CPIAUCSL", "FEDFUNDS"),
        c("DGS10", "UNRATE"),
        c("PAYEMS", "CPIAUCSL"),
        c("spread_2_10", "PAYEMS"),
        c("CIVPART", "UNRATE")
      )

      results <- rbindlist(lapply(test_pairs, function(pair) {
        x_name <- pair[1]
        y_name <- pair[2]

        if (!all(c(x_name, y_name) %in% names(wide))) {
          return(data.table(
            `Predictor` = SERIES_LABELS[x_name],
            `Predicted` = SERIES_LABELS[y_name],
            `Lag (months)` = NA_integer_,
            `F-statistic` = NA_real_,
            `p-value` = NA_real_,
            Significant = "N/A"
          ))
        }

        dt <- wide[!is.na(get(x_name)) & !is.na(get(y_name)), c("month", x_name, y_name), with = FALSE]
        if (nrow(dt) < 30) return(NULL)

        rbindlist(lapply(c(3, 6, 12), function(lag) {
          tryCatch({
            test <- lmtest::grangertest(
              as.formula(paste(y_name, "~", x_name)),
              order = lag,
              data = dt
            )
            data.table(
              Predictor = SERIES_LABELS[x_name],
              Predicted = SERIES_LABELS[y_name],
              `Lag (months)` = lag,
              `F-statistic` = round(test$F[2], 3),
              `p-value` = round(test$`Pr(>F)`[2], 4),
              Significant = ifelse(test$`Pr(>F)`[2] < 0.05, "Yes", "No")
            )
          }, error = function(e) {
            data.table(
              Predictor = SERIES_LABELS[x_name],
              Predicted = SERIES_LABELS[y_name],
              `Lag (months)` = lag,
              `F-statistic` = NA_real_,
              `p-value` = NA_real_,
              Significant = "Error"
            )
          })
        }))
      }))

      datatable(
        results,
        options = list(pageLength = 25, dom = "ft", ordering = TRUE),
        rownames = FALSE
      ) %>%
        formatStyle("Significant",
          backgroundColor = styleEqual(c("Yes", "No"), c("#dff0d8", "#f2dede"))
        )
    })

    # Download handler
    output$download_corr <- downloadHandler(
      filename = function() {
        paste0("StarCruiser_Correlations_", format(Sys.Date(), "%Y%m%d"), ".csv")
      },
      content = function(file) {
        mat <- corr_matrix()
        if (!is.null(mat)) {
          write.csv(mat, file)
        }
      }
    )
  })
}
