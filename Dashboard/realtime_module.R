# ============================================================================
# REAL-TIME INDICATORS MODULE - StarCruiser Dashboard
# ============================================================================
# Track C2.1: Real-time leading indicators dashboard tab
# Features: Weekly UI claims, Google Trends, claims vs UNRATE overlay
# Data: Outputs/REALTIME/ (from update_ui_claims.py, extract_google_trends.py)
# ============================================================================

# UI
realtime_ui <- function(id) {
  ns <- NS(id)
  tagList(
    # Info/value boxes
    fluidRow(
      infoBoxOutput(ns("last_updated"), width = 4),
      valueBoxOutput(ns("initial_claims"), width = 4),
      valueBoxOutput(ns("continued_claims"), width = 4)
    ),

    # Claims charts
    fluidRow(
      box(
        title = "Weekly Initial Claims (ICSA)",
        echarts4rOutput(ns("claims_chart"), height = "350px"),
        helpText("Seasonally adjusted initial unemployment insurance claims. 4-week moving average in red."),
        width = 6, solidHeader = TRUE, status = "primary"
      ),
      box(
        title = "Continued Claims (CCSA)",
        echarts4rOutput(ns("continued_chart"), height = "350px"),
        width = 6, solidHeader = TRUE, status = "primary"
      )
    ),

    # Google Trends
    fluidRow(
      box(
        title = "Google Trends: Labor Market Search Interest",
        echarts4rOutput(ns("trends_chart"), height = "350px"),
        helpText("Search interest (0-100 scale) for labor market keywords. Spikes may signal rising unemployment."),
        width = 12, solidHeader = TRUE, status = "info"
      )
    ),

    # Leading indicator overlay
    fluidRow(
      box(
        title = "Leading Indicator: Initial Claims vs Unemployment Rate",
        echarts4rOutput(ns("claims_vs_unrate"), height = "400px"),
        helpText("Initial claims (left axis) typically lead unemployment rate (right axis) by 1-2 months."),
        width = 12, solidHeader = TRUE, status = "warning"
      )
    ),

    # Data availability notice
    fluidRow(
      box(
        title = "Data Sources", width = 12, collapsible = TRUE, collapsed = TRUE,
        HTML("
          <ul>
            <li><strong>UI Claims</strong>: FRED API (ICSA, CCSA series). Updated weekly on Thursdays.</li>
            <li><strong>Google Trends</strong>: pytrends API. Keywords: 'unemployment benefits', 'file for unemployment', 'jobs near me', etc.</li>
          </ul>
          <p>To refresh data, run:</p>
          <pre>python Technical/update_ui_claims.py
python Technical/extract_google_trends.py</pre>
        ")
      )
    )
  )
}

# SERVER
realtime_server <- function(id, employment_data) {
  moduleServer(id, function(input, output, session) {

    # Load UI claims data
    claims_data <- reactive({
      claims_dir <- file.path(Sys.getenv("OUTPUT_ROOT", "outputs"), "REALTIME")
      if (!dir.exists(claims_dir)) return(NULL)

      files <- list.files(claims_dir, pattern = "ui_claims.*\\.csv$", full.names = TRUE)
      if (length(files) == 0) {
        # Also check Inputs/External
        input_dir <- file.path("..", "Inputs/External/UI_Claims")
        if (dir.exists(input_dir)) {
          files <- list.files(input_dir, pattern = ".*claims.*\\.csv$", full.names = TRUE)
        }
      }
      if (length(files) == 0) return(NULL)

      tryCatch({
        dt <- fread(files[length(files)])
        if ("date" %in% names(dt)) dt[, date := as.Date(date)]
        dt
      }, error = function(e) {
        message("Error loading UI claims: ", e$message)
        NULL
      })
    })

    # Load Google Trends data
    trends_data <- reactive({
      trends_dir <- file.path(Sys.getenv("OUTPUT_ROOT", "outputs"), "REALTIME")
      if (!dir.exists(trends_dir)) return(NULL)

      files <- list.files(trends_dir, pattern = "google_trends.*\\.csv$", full.names = TRUE)
      if (length(files) == 0) {
        input_dir <- file.path("..", "Inputs/External/Google_Trends")
        if (dir.exists(input_dir)) {
          files <- list.files(input_dir, pattern = ".*trends.*\\.csv$", full.names = TRUE)
        }
      }
      if (length(files) == 0) return(NULL)

      tryCatch({
        dt <- fread(files[length(files)])
        if ("date" %in% names(dt)) dt[, date := as.Date(date)]
        dt
      }, error = function(e) {
        message("Error loading Google Trends: ", e$message)
        NULL
      })
    })

    # Value boxes
    output$last_updated <- renderInfoBox({
      claims <- claims_data()
      if (is.null(claims) || !("date" %in% names(claims))) {
        return(infoBox("Last Updated", "No data", icon = icon("calendar"),
                       subtitle = "Run update_ui_claims.py", color = "gray"))
      }

      latest_date <- max(claims$date, na.rm = TRUE)
      days_old <- as.numeric(Sys.Date() - latest_date)
      color <- if (days_old < 7) "green" else if (days_old < 30) "yellow" else "red"

      infoBox("Last Updated", format(latest_date, "%B %d, %Y"),
              subtitle = paste(days_old, "days ago"),
              icon = icon("calendar"), color = color)
    })

    output$initial_claims <- renderValueBox({
      claims <- claims_data()
      if (is.null(claims)) {
        return(valueBox("N/A", "Initial Claims", icon = icon("file-alt"), color = "gray"))
      }

      # Find ICSA series
      icsa <- NULL
      if ("series_id" %in% names(claims)) {
        icsa <- claims[series_id == "ICSA"][order(-date)][1]
      } else if ("ICSA" %in% names(claims)) {
        # Wide format
        icsa <- claims[order(-date)][1]
        icsa_val <- icsa$ICSA
      }

      if (is.null(icsa) || nrow(icsa) == 0) {
        return(valueBox("N/A", "Initial Claims", icon = icon("file-alt"), color = "gray"))
      }

      val <- if ("value" %in% names(icsa)) icsa$value else icsa$ICSA
      color <- if (val > 300000) "red" else if (val > 225000) "yellow" else "green"

      valueBox(
        value = format(round(val), big.mark = ","),
        subtitle = "Initial Claims (latest)",
        icon = icon("file-alt"),
        color = color
      )
    })

    output$continued_claims <- renderValueBox({
      claims <- claims_data()
      if (is.null(claims)) {
        return(valueBox("N/A", "Continued Claims", icon = icon("users"), color = "gray"))
      }

      ccsa <- NULL
      if ("series_id" %in% names(claims)) {
        ccsa <- claims[series_id == "CCSA"][order(-date)][1]
      } else if ("CCSA" %in% names(claims)) {
        ccsa <- claims[order(-date)][1]
      }

      if (is.null(ccsa) || nrow(ccsa) == 0) {
        return(valueBox("N/A", "Continued Claims", icon = icon("users"), color = "gray"))
      }

      val <- if ("value" %in% names(ccsa)) ccsa$value else ccsa$CCSA

      valueBox(
        value = format(round(val), big.mark = ","),
        subtitle = "Continued Claims (latest)",
        icon = icon("users"),
        color = "blue"
      )
    })

    # Claims chart
    output$claims_chart <- renderEcharts4r({
      claims <- claims_data()
      if (is.null(claims)) {
        return(NULL)
      }

      # Extract ICSA series
      if ("series_id" %in% names(claims)) {
        icsa <- claims[series_id == "ICSA"][order(date)]
      } else if ("ICSA" %in% names(claims)) {
        icsa <- claims[, .(date, value = ICSA)][order(date)]
      } else {
        return(NULL)
      }

      if (nrow(icsa) == 0) return(NULL)

      # Add 4-week moving average
      icsa[, ma4 := frollmean(value, 4)]

      chart <- icsa %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", color = "#3c8dbc", sampling = "lttb",
               name = "Weekly Claims") %>%
        e_line(ma4, symbol = "none", color = "#dd4b39", sampling = "lttb",
               name = "4-Week MA", lineStyle = list(width = 2)) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Claims")

      add_recession_bands(chart)
    })

    # Continued claims chart
    output$continued_chart <- renderEcharts4r({
      claims <- claims_data()
      if (is.null(claims)) return(NULL)

      if ("series_id" %in% names(claims)) {
        ccsa <- claims[series_id == "CCSA"][order(date)]
      } else if ("CCSA" %in% names(claims)) {
        ccsa <- claims[, .(date, value = CCSA)][order(date)]
      } else {
        return(NULL)
      }

      if (nrow(ccsa) == 0) return(NULL)

      chart <- ccsa %>%
        e_charts(date) %>%
        e_line(value, symbol = "none", color = "#00a65a", sampling = "lttb",
               name = "Continued Claims") %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Claims")

      add_recession_bands(chart)
    })

    # Google Trends chart
    output$trends_chart <- renderEcharts4r({
      trends <- trends_data()
      if (is.null(trends)) {
        return(NULL)
      }

      # Handle different possible column formats
      if ("keyword" %in% names(trends) && "interest" %in% names(trends)) {
        # Long format
        chart <- trends %>%
          group_by(keyword) %>%
          e_charts(date) %>%
          e_line(interest, symbol = "none", sampling = "lttb") %>%
          e_tooltip(trigger = "axis") %>%
          e_legend(bottom = "5%", type = "scroll") %>%
          e_datazoom(type = "slider") %>%
          e_y_axis(name = "Search Interest (0-100)")

        add_recession_bands(chart)
      } else {
        # Wide format - plot all numeric columns except date
        num_cols <- setdiff(names(trends)[sapply(trends, is.numeric)], c("date"))
        if (length(num_cols) == 0) return(NULL)

        # Melt to long for echarts
        long <- melt(trends, id.vars = "date", measure.vars = num_cols,
                     variable.name = "keyword", value.name = "interest")

        chart <- long %>%
          group_by(keyword) %>%
          e_charts(date) %>%
          e_line(interest, symbol = "none", sampling = "lttb") %>%
          e_tooltip(trigger = "axis") %>%
          e_legend(bottom = "5%", type = "scroll") %>%
          e_datazoom(type = "slider") %>%
          e_y_axis(name = "Search Interest (0-100)")

        add_recession_bands(chart)
      }
    })

    # Claims vs UNRATE overlay
    output$claims_vs_unrate <- renderEcharts4r({
      claims <- claims_data()
      emp <- employment_data()
      if (is.null(claims)) return(NULL)

      # Get ICSA data
      if ("series_id" %in% names(claims)) {
        icsa <- claims[series_id == "ICSA", .(date, claims = value)][order(date)]
      } else if ("ICSA" %in% names(claims)) {
        icsa <- claims[, .(date, claims = ICSA)][order(date)]
      } else {
        return(NULL)
      }

      # Get UNRATE data
      unrate <- emp[series_id == "UNRATE", .(date, unrate = value)][order(date)]

      # Merge on date (approximate - claims is weekly, UNRATE is monthly)
      # Aggregate claims to monthly
      icsa[, month := floor_date(date, "month")]
      icsa_monthly <- icsa[, .(claims = mean(claims, na.rm = TRUE)), by = month]
      setnames(icsa_monthly, "month", "date")

      merged <- merge(icsa_monthly, unrate, by = "date", all = TRUE)
      merged <- merged[!is.na(claims) | !is.na(unrate)][order(date)]

      if (nrow(merged) == 0) return(NULL)

      chart <- merged %>%
        e_charts(date) %>%
        e_line(claims, symbol = "none", color = "#3c8dbc", sampling = "lttb",
               name = "Initial Claims (monthly avg)", y_index = 0) %>%
        e_line(unrate, symbol = "none", color = "#dd4b39", sampling = "lttb",
               name = "Unemployment Rate (%)", y_index = 1) %>%
        e_y_axis(
          index = 0, name = "Initial Claims",
          nameLocation = "middle", nameGap = 50
        ) %>%
        e_y_axis(
          index = 1, name = "Unemployment Rate (%)",
          nameLocation = "middle", nameGap = 40
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_datazoom(type = "slider")

      add_recession_bands(chart)
    })
  })
}
