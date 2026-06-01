# ============================================================================
# INFLATION DECOMPOSITION MODULE - StarCruiser Dashboard
# ============================================================================
# Purpose: Comprehensive inflation analysis visualizations
# Features:
#   - Headline vs Core decomposition
#   - CPI vs PCE comparison
#   - Component contributions
#   - Alternative measures (Sticky CPI, Trimmed Mean PCE)
#   - Breakeven inflation expectations
# ============================================================================

# ============================================================================
# CONFIGURATION
# ============================================================================

# CPI component weights (2024 basis)
CPI_WEIGHTS <- list(
  Food = 0.137,
  Energy = 0.066,
  Shelter = 0.347,
  Medical = 0.086,
  Transportation = 0.158
)

# Series definitions
INFLATION_SERIES <- list(
  # Headline
  CPIAUCSL = list(name = "CPI All Items", type = "headline", measure = "CPI"),
  PCEPI = list(name = "PCE", type = "headline", measure = "PCE"),

  # Core
  CPILFESL = list(name = "Core CPI", type = "core", measure = "CPI"),
  PCEPILFE = list(name = "Core PCE", type = "core", measure = "PCE"),

  # Components
  CPIENGSL = list(name = "Energy", type = "component", measure = "CPI"),
  CPIFABSL = list(name = "Food", type = "component", measure = "CPI"),
  CPIHOSSL = list(name = "Shelter", type = "component", measure = "CPI"),
  CPIMEDSL = list(name = "Medical", type = "component", measure = "CPI"),
  CPITRNSL = list(name = "Transportation", type = "component", measure = "CPI"),

  # Alternative
  CORESTICKM159SFRBATL = list(name = "Sticky Price CPI", type = "alternative", measure = "CPI"),
  PCETRIM12M159SFRBDAL = list(name = "Trimmed Mean PCE", type = "alternative", measure = "PCE")
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

#' Calculate component contributions to headline inflation
#' @param dt data.table with inflation data
#' @return data.table with contributions
calculate_contributions <- function(dt) {
  if (is.null(dt)) return(NULL)

  # Define components and their weights
  components <- data.table(
    series_id = c("CPIENGSL", "CPIFABSL", "CPIHOSSL", "CPIMEDSL", "CPITRNSL"),
    name = c("Energy", "Food", "Shelter", "Medical", "Transportation"),
    weight = c(0.066, 0.137, 0.347, 0.086, 0.158)
  )

  # Get component data
  comp_data <- dt[series_id %chin% components$series_id]

  if (nrow(comp_data) == 0) return(NULL)

  # Calculate YoY for each component
  comp_data <- comp_data[order(series_id, date)]
  comp_data[, yoy := (value / shift(value, 12) - 1) * 100, by = series_id]

  # Merge with weights
  comp_data <- merge(comp_data, components, by = "series_id")

  # Calculate contribution
  comp_data[, contribution := yoy * weight]

  return(comp_data)
}

#' Compare CPI and PCE measures
#' @param dt data.table with inflation data
#' @return data.table with comparison
compare_cpi_pce <- function(dt) {
  if (is.null(dt)) return(NULL)

  # Get headline and core series
  series_ids <- c("CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE")
  data <- dt[series_id %chin% series_ids]

  if (nrow(data) == 0) return(NULL)

  # Calculate YoY
  data <- data[order(series_id, date)]
  data[, yoy := (value / shift(value, 12) - 1) * 100, by = series_id]

  # Pivot wide
  wide <- dcast(data[!is.na(yoy)], date ~ series_id, value.var = "yoy")

  # Calculate wedges
  if ("CPIAUCSL" %in% names(wide) && "PCEPI" %in% names(wide)) {
    wide[, headline_wedge := CPIAUCSL - PCEPI]
  }
  if ("CPILFESL" %in% names(wide) && "PCEPILFE" %in% names(wide)) {
    wide[, core_wedge := CPILFESL - PCEPILFE]
  }

  return(wide)
}

# ============================================================================
# UI FUNCTION
# ============================================================================

inflation_ui <- function(id) {
  ns <- NS(id)

  tagList(
    fluidRow(
      # Controls
      box(
        title = "Inflation Analysis Controls",
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
              start = Sys.Date() - 365 * 5,
              end = Sys.Date(),
              min = "1990-01-01",
              max = Sys.Date()
            )
          ),
          column(4,
            selectInput(
              ns("measure_type"),
              "Primary Measure:",
              choices = c(
                "CPI (Consumer Price Index)" = "CPI",
                "PCE (Personal Consumption)" = "PCE"
              ),
              selected = "CPI"
            )
          ),
          column(4,
            checkboxInput(
              ns("show_target"),
              "Show 2% Target Line",
              value = TRUE
            )
          )
        )
      )
    ),

    # Value boxes
    fluidRow(
      valueBoxOutput(ns("vb_headline"), width = 3),
      valueBoxOutput(ns("vb_core"), width = 3),
      valueBoxOutput(ns("vb_energy"), width = 3),
      valueBoxOutput(ns("vb_shelter"), width = 3)
    ),

    # Headline vs Core
    fluidRow(
      box(
        title = "Headline vs Core Inflation",
        width = 12,
        status = "info",
        solidHeader = TRUE,
        echarts4rOutput(ns("headline_core_chart"), height = "350px"),
        p(class = "text-muted",
          "Core inflation excludes volatile food and energy prices.
           The Fed targets 2% PCE inflation.")
      )
    ),

    # CPI vs PCE comparison
    fluidRow(
      box(
        title = "CPI vs PCE Comparison",
        width = 6,
        status = "warning",
        solidHeader = TRUE,
        echarts4rOutput(ns("cpi_pce_chart"), height = "300px"),
        p(class = "text-muted small",
          "CPI uses fixed basket (Laspeyres), PCE uses chain-weighted (Fisher).
           CPI typically runs 0.2-0.4pp higher than PCE.")
      ),
      box(
        title = "CPI-PCE Wedge",
        width = 6,
        status = "warning",
        solidHeader = TRUE,
        echarts4rOutput(ns("wedge_chart"), height = "300px"),
        p(class = "text-muted small",
          "The wedge reflects substitution bias and methodological differences.")
      )
    ),

    # Component contributions
    fluidRow(
      box(
        title = "CPI Component Contributions",
        width = 12,
        status = "success",
        solidHeader = TRUE,
        echarts4rOutput(ns("contributions_chart"), height = "400px"),
        p(class = "text-muted",
          "Stacked bar shows how each component contributes to headline CPI inflation.
           Shelter is the largest component (~35% weight).")
      )
    ),

    # Alternative measures
    fluidRow(
      box(
        title = "Alternative Inflation Measures",
        width = 12,
        status = "primary",
        solidHeader = TRUE,
        echarts4rOutput(ns("alternative_chart"), height = "350px"),
        fluidRow(
          column(6,
            h5("Sticky Price CPI (Atlanta Fed)"),
            p(class = "text-muted small",
              "Measures prices that change infrequently. More forward-looking
               as these prices embed inflation expectations.")
          ),
          column(6,
            h5("Trimmed Mean PCE (Dallas Fed)"),
            p(class = "text-muted small",
              "Removes extreme price changes to reveal underlying trend.
               Less affected by outliers than core measures.")
          )
        )
      )
    ),

    # Historical context
    fluidRow(
      box(
        title = "Inflation Component YoY Changes",
        width = 12,
        status = "info",
        solidHeader = TRUE,
        DTOutput(ns("component_table"))
      )
    )
  )
}

# ============================================================================
# SERVER FUNCTION
# ============================================================================

inflation_server <- function(id, inflation_data) {
  moduleServer(id, function(input, output, session) {

    # Reactive for filtered data
    filtered_data <- reactive({
      req(inflation_data())

      dt <- inflation_data()
      dt <- dt[date >= input$date_range[1] & date <= input$date_range[2]]

      return(dt)
    })

    # ---- VALUE BOXES ----

    output$vb_headline <- renderValueBox({
      req(inflation_data())
      series <- if (input$measure_type == "CPI") "CPIAUCSL" else "PCEPI"
      data <- inflation_data()[series_id == series][order(-date)]

      if (nrow(data) > 12) {
        latest <- data$value[1]
        year_ago <- data$value[13]
        yoy <- (latest / year_ago - 1) * 100
        val <- sprintf("%.1f%%", yoy)
      } else {
        val <- "N/A"
      }

      valueBox(
        val,
        paste("Headline", input$measure_type, "YoY"),
        icon = icon("chart-line"),
        color = "blue"
      )
    })

    output$vb_core <- renderValueBox({
      req(inflation_data())
      series <- if (input$measure_type == "CPI") "CPILFESL" else "PCEPILFE"
      data <- inflation_data()[series_id == series][order(-date)]

      if (nrow(data) > 12) {
        latest <- data$value[1]
        year_ago <- data$value[13]
        yoy <- (latest / year_ago - 1) * 100
        val <- sprintf("%.1f%%", yoy)
      } else {
        val <- "N/A"
      }

      color <- if (!is.na(yoy) && yoy > 3) "red" else if (!is.na(yoy) && yoy > 2.5) "yellow" else "green"

      valueBox(
        val,
        paste("Core", input$measure_type, "YoY"),
        icon = icon("bullseye"),
        color = color
      )
    })

    output$vb_energy <- renderValueBox({
      req(inflation_data())
      data <- inflation_data()[series_id == "CPIENGSL"][order(-date)]

      if (nrow(data) > 12) {
        latest <- data$value[1]
        year_ago <- data$value[13]
        yoy <- (latest / year_ago - 1) * 100
        val <- sprintf("%+.1f%%", yoy)
      } else {
        val <- "N/A"
      }

      color <- if (!is.na(yoy) && yoy > 10) "red" else if (!is.na(yoy) && yoy < -10) "green" else "yellow"

      valueBox(
        val,
        "Energy YoY",
        icon = icon("gas-pump"),
        color = color
      )
    })

    output$vb_shelter <- renderValueBox({
      req(inflation_data())
      data <- inflation_data()[series_id == "CPIHOSSL"][order(-date)]

      if (nrow(data) > 12) {
        latest <- data$value[1]
        year_ago <- data$value[13]
        yoy <- (latest / year_ago - 1) * 100
        val <- sprintf("%.1f%%", yoy)
      } else {
        val <- "N/A"
      }

      valueBox(
        val,
        "Shelter YoY",
        icon = icon("home"),
        color = "purple"
      )
    })

    # ---- HEADLINE VS CORE CHART ----

    output$headline_core_chart <- renderEcharts4r({
      req(filtered_data())

      # Get series based on measure type
      if (input$measure_type == "CPI") {
        series_ids <- c("CPIAUCSL", "CPILFESL")
        labels <- c("Headline CPI", "Core CPI")
      } else {
        series_ids <- c("PCEPI", "PCEPILFE")
        labels <- c("Headline PCE", "Core PCE")
      }

      data <- filtered_data()[series_id %chin% series_ids]

      if (nrow(data) == 0) {
        return(e_charts() %>% e_title("No data available"))
      }

      # Calculate YoY
      data <- data[order(series_id, date)]
      data[, yoy := (value / shift(value, 12) - 1) * 100, by = series_id]
      data <- data[!is.na(yoy)]

      # Pivot
      wide <- dcast(data, date ~ series_id, value.var = "yoy")
      setnames(wide, series_ids, labels, skip_absent = TRUE)

      chart <- wide %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(
          name = "YoY Change (%)",
          nameLocation = "middle",
          nameGap = 40
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_datazoom(type = "slider") %>%
        e_grid(left = "10%", right = "5%", bottom = "20%") %>%
        e_toolbox_feature(feature = "saveAsImage")

      for (label in labels) {
        if (label %in% names(wide)) {
          chart <- chart %>% e_line_(label, smooth = FALSE, symbol = "none")
        }
      }

      # Add 2% target line
      if (input$show_target) {
        chart <- chart %>%
          e_mark_line(
            data = list(yAxis = 2),
            lineStyle = list(color = "green", type = "dashed"),
            label = list(formatter = "2% Target", position = "end")
          )
      }

      # Add recession shading
      chart <- add_recession_bands(chart, input$date_range)

      chart
    })

    # ---- CPI VS PCE CHART ----

    output$cpi_pce_chart <- renderEcharts4r({
      req(filtered_data())

      comparison <- compare_cpi_pce(filtered_data())

      if (is.null(comparison) || nrow(comparison) == 0) {
        return(e_charts() %>% e_title("Comparison data not available"))
      }

      comparison %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(name = "YoY (%)") %>%
        e_line(CPIAUCSL, name = "CPI Headline", smooth = FALSE, symbol = "none") %>%
        e_line(PCEPI, name = "PCE Headline", smooth = FALSE, symbol = "none") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_grid(left = "12%", right = "5%", bottom = "15%") %>%
        e_toolbox_feature(feature = "saveAsImage")
    })

    # ---- WEDGE CHART ----

    output$wedge_chart <- renderEcharts4r({
      req(filtered_data())

      comparison <- compare_cpi_pce(filtered_data())

      if (is.null(comparison) || !"headline_wedge" %in% names(comparison)) {
        return(e_charts() %>% e_title("Wedge data not available"))
      }

      comparison %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(name = "CPI - PCE (pp)") %>%
        e_bar(headline_wedge, name = "CPI-PCE Wedge") %>%
        e_mark_line(
          data = list(yAxis = 0),
          lineStyle = list(color = "black", type = "solid")
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = FALSE) %>%
        e_grid(left = "12%", right = "5%", bottom = "10%") %>%
        e_toolbox_feature(feature = "saveAsImage")
    })

    # ---- CONTRIBUTIONS CHART ----

    output$contributions_chart <- renderEcharts4r({
      req(filtered_data())

      contributions <- calculate_contributions(filtered_data())

      if (is.null(contributions) || nrow(contributions) == 0) {
        return(e_charts() %>% e_title("Component data not available"))
      }

      # Get latest 36 months for cleaner display
      recent_dates <- sort(unique(contributions$date), decreasing = TRUE)[1:36]
      contributions <- contributions[date %in% recent_dates]

      # Pivot for stacking
      wide <- dcast(contributions, date ~ name, value.var = "contribution")

      chart <- wide %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(name = "Contribution (pp)")

      # Add each component as stacked bar
      component_names <- c("Shelter", "Food", "Transportation", "Medical", "Energy")
      colors <- c("#2ecc71", "#e74c3c", "#3498db", "#9b59b6", "#f39c12")

      for (i in seq_along(component_names)) {
        name <- component_names[i]
        if (name %in% names(wide)) {
          chart <- chart %>% e_bar_(name, stack = "total")
        }
      }

      chart <- chart %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_grid(left = "10%", right = "5%", bottom = "15%") %>%
        e_color(colors) %>%
        e_toolbox_feature(feature = "saveAsImage")

      chart
    })

    # ---- ALTERNATIVE MEASURES CHART ----

    output$alternative_chart <- renderEcharts4r({
      req(filtered_data())

      alt_series <- c("CORESTICKM159SFRBATL", "PCETRIM12M159SFRBDAL", "CPILFESL", "PCEPILFE")
      data <- filtered_data()[series_id %chin% alt_series]

      if (nrow(data) == 0) {
        return(e_charts() %>% e_title("Alternative measures not available"))
      }

      # For core measures, calculate YoY; alternative measures are already in rate form
      data <- data[order(series_id, date)]

      # Calculate YoY for index series
      data[series_id %in% c("CPILFESL", "PCEPILFE"),
           value := (value / shift(value, 12) - 1) * 100,
           by = series_id]

      data <- data[!is.na(value)]

      # Rename for display
      data[series_id == "CORESTICKM159SFRBATL", series_id := "Sticky CPI"]
      data[series_id == "PCETRIM12M159SFRBDAL", series_id := "Trimmed Mean PCE"]
      data[series_id == "CPILFESL", series_id := "Core CPI"]
      data[series_id == "PCEPILFE", series_id := "Core PCE"]

      # Pivot
      wide <- dcast(data, date ~ series_id, value.var = "value")

      chart <- wide %>%
        e_charts(date) %>%
        e_x_axis(type = "time") %>%
        e_y_axis(name = "YoY (%)") %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(show = TRUE, bottom = 0) %>%
        e_datazoom(type = "slider") %>%
        e_grid(left = "10%", right = "5%", bottom = "20%") %>%
        e_toolbox_feature(feature = "saveAsImage")

      for (col in c("Sticky CPI", "Trimmed Mean PCE", "Core CPI", "Core PCE")) {
        if (col %in% names(wide)) {
          chart <- chart %>% e_line_(col, smooth = FALSE, symbol = "none")
        }
      }

      # Add target
      if (input$show_target) {
        chart <- chart %>%
          e_mark_line(
            data = list(yAxis = 2),
            lineStyle = list(color = "green", type = "dashed")
          )
      }

      chart
    })

    # ---- COMPONENT TABLE ----

    output$component_table <- renderDT({
      req(inflation_data())

      # Calculate current YoY for all components
      components <- c("CPIAUCSL", "CPILFESL", "CPIENGSL", "CPIFABSL",
                     "CPIHOSSL", "CPIMEDSL", "CPITRNSL", "PCEPI", "PCEPILFE")

      data <- inflation_data()[series_id %chin% components]
      data <- data[order(series_id, -date)]

      # Get latest YoY
      results <- data[, {
        if (.N >= 13) {
          latest <- value[1]
          year_ago <- value[13]
          yoy <- (latest / year_ago - 1) * 100
          mom_ann <- ((value[1] / value[2]) ^ 12 - 1) * 100
          data.table(
            latest_date = date[1],
            yoy = yoy,
            mom_ann = mom_ann
          )
        } else {
          data.table(latest_date = date[1], yoy = NA_real_, mom_ann = NA_real_)
        }
      }, by = series_id]

      # Add names
      name_map <- c(
        CPIAUCSL = "CPI Headline",
        CPILFESL = "CPI Core",
        CPIENGSL = "Energy",
        CPIFABSL = "Food",
        CPIHOSSL = "Shelter",
        CPIMEDSL = "Medical",
        CPITRNSL = "Transportation",
        PCEPI = "PCE Headline",
        PCEPILFE = "PCE Core"
      )

      results[, name := name_map[series_id]]

      display <- results[, .(
        Component = name,
        `YoY (%)` = sprintf("%.2f", yoy),
        `MoM Ann. (%)` = sprintf("%.2f", mom_ann),
        `Latest Date` = format(latest_date, "%Y-%m")
      )]

      datatable(
        display,
        options = list(
          pageLength = 10,
          dom = 'tip',
          ordering = TRUE
        ),
        rownames = FALSE
      )
    })

  })
}
