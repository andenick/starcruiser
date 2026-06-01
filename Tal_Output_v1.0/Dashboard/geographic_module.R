# ============================================================================
# GEOGRAPHIC MODULE - StarCruiser Dashboard
# ============================================================================
# Purpose: County-level geographic analysis with cluster visualization
# Data: Census CBP cluster analysis results, shift-share decomposition
# Created: 2025-12-05
# Updated: 2025-12-05 (Added leaflet map)
# ============================================================================

# ============================================================================
# LOAD GEOGRAPHIC DATA
# ============================================================================

#' Load cluster assignments for all counties
#' @return data.table with cluster assignments
load_cluster_data <- function() {
  # Find the most recent cluster file
  cluster_dir <- "../Outputs/CLUSTERS"

  if (!dir.exists(cluster_dir)) {
    message("Warning: CLUSTERS directory not found")
    return(NULL)
  }

  # Find CSV files
  csv_files <- list.files(cluster_dir, pattern = "cluster_assignments\\.csv$", full.names = TRUE)

  if (length(csv_files) == 0) {
    message("Warning: No cluster assignment files found")
    return(NULL)
  }

  # Use most recent file
  csv_file <- csv_files[length(csv_files)]
  message(paste("Loading cluster data from:", basename(csv_file)))

  dt <- fread(csv_file)

  # Create FIPS code (5-digit: 2-digit state + 3-digit county)
  dt[, fips := sprintf("%02d%03d", state, county)]

  # Add cluster names
  cluster_names <- c(
    "0" = "Growing Manufacturing",
    "1" = "Service & Retail (Small)",
    "2" = "Service & Retail (Large)",
    "3" = "Extreme Manufacturing",
    "4" = "Agricultural Services",
    "5" = "Tourism & Hospitality",
    "6" = "Boom Counties (Mining)",
    "7" = "Education & Healthcare"
  )

  dt[, cluster_name := cluster_names[as.character(cluster)]]

  # Add state names for display
  state_names <- c(
    "01"="Alabama", "02"="Alaska", "04"="Arizona", "05"="Arkansas", "06"="California",
    "08"="Colorado", "09"="Connecticut", "10"="Delaware", "11"="DC", "12"="Florida",
    "13"="Georgia", "15"="Hawaii", "16"="Idaho", "17"="Illinois", "18"="Indiana",
    "19"="Iowa", "20"="Kansas", "21"="Kentucky", "22"="Louisiana", "23"="Maine",
    "24"="Maryland", "25"="Massachusetts", "26"="Michigan", "27"="Minnesota",
    "28"="Mississippi", "29"="Missouri", "30"="Montana", "31"="Nebraska", "32"="Nevada",
    "33"="New Hampshire", "34"="New Jersey", "35"="New Mexico", "36"="New York",
    "37"="North Carolina", "38"="North Dakota", "39"="Ohio", "40"="Oklahoma",
    "41"="Oregon", "42"="Pennsylvania", "44"="Rhode Island", "45"="South Carolina",
    "46"="South Dakota", "47"="Tennessee", "48"="Texas", "49"="Utah", "50"="Vermont",
    "51"="Virginia", "53"="Washington", "54"="West Virginia", "55"="Wisconsin", "56"="Wyoming",
    "72"="Puerto Rico"
  )
  dt[, state_name := state_names[sprintf("%02d", state)]]

  return(dt)
}

#' Load shift-share decomposition results
#' @return data.table with shift-share components
load_shift_share_data <- function() {
  shift_share_dir <- "../Outputs/SHIFT_SHARE"

  if (!dir.exists(shift_share_dir)) {
    message("Warning: SHIFT_SHARE directory not found")
    return(NULL)
  }

  # Find CSV files
  csv_files <- list.files(shift_share_dir, pattern = "shift_share_summary\\.csv$", full.names = TRUE)

  if (length(csv_files) == 0) {
    message("Warning: No shift-share summary files found")
    return(NULL)
  }

  csv_file <- csv_files[length(csv_files)]
  message(paste("Loading shift-share data from:", basename(csv_file)))

  dt <- fread(csv_file)
  dt[, fips := sprintf("%02d%03d", state_fips, county_fips)]

  return(dt)
}

# ============================================================================
# CLUSTER COLOR PALETTE
# ============================================================================

cluster_colors <- c(
  "Growing Manufacturing" = "#1f77b4",      # Blue
  "Service & Retail (Small)" = "#ff7f0e",   # Orange
  "Service & Retail (Large)" = "#2ca02c",   # Green
  "Extreme Manufacturing" = "#d62728",       # Red
  "Agricultural Services" = "#9467bd",       # Purple
  "Tourism & Hospitality" = "#8c564b",       # Brown
  "Boom Counties (Mining)" = "#e377c2",      # Pink
  "Education & Healthcare" = "#17becf"       # Cyan
)

# ============================================================================
# UI COMPONENTS
# ============================================================================

geographic_ui <- function() {
  tabItem(
    tabName = "geographic",
    h2("County Employment Analysis"),

    # Summary boxes
    fluidRow(
      valueBoxOutput("vbox_counties", width = 3),
      valueBoxOutput("vbox_clusters", width = 3),
      valueBoxOutput("vbox_total_emp", width = 3),
      valueBoxOutput("vbox_avg_growth", width = 3)
    ),

    # State selector and map metrics
    fluidRow(
      box(
        title = "Geographic Filters",
        selectInput("state_filter", "Filter by State:",
                    choices = c("All States" = "all"),
                    selected = "all"),
        selectInput("cluster_filter", "Filter by Cluster:",
                    choices = c("All Clusters" = "all",
                               "Growing Manufacturing",
                               "Service & Retail (Small)",
                               "Service & Retail (Large)",
                               "Agricultural Services",
                               "Tourism & Hospitality",
                               "Boom Counties (Mining)",
                               "Education & Healthcare"),
                    selected = "all"),
        width = 3
      ),

      # State summary
      box(
        title = "State Summary",
        htmlOutput("state_summary_html"),
        width = 3
      ),

      # Cluster distribution (moved up)
      box(
        title = "Cluster Distribution",
        echarts4rOutput("plot_cluster_pie", height = "250px"),
        width = 6
      )
    ),

    # Main charts row
    fluidRow(
      # Cluster distribution bar
      box(
        title = "County Clusters by Type",
        echarts4rOutput("plot_cluster_dist", height = "350px"),
        width = 6,
        solidHeader = TRUE,
        status = "primary"
      ),

      # Cluster characteristics
      box(
        title = "Cluster Characteristics",
        DT::dataTableOutput("table_cluster_summary"),
        width = 6,
        solidHeader = TRUE,
        status = "primary"
      )
    ),

    # Shift-share analysis
    fluidRow(
      box(
        title = "Top 15 Counties by Regional Competitive Advantage",
        echarts4rOutput("plot_shift_share_top", height = "400px"),
        width = 6,
        solidHeader = TRUE,
        status = "success"
      ),

      box(
        title = "Bottom 15 Counties by Regional Competitive Advantage",
        echarts4rOutput("plot_shift_share_bottom", height = "400px"),
        width = 6,
        solidHeader = TRUE,
        status = "danger"
      )
    ),

    # Growth by cluster
    fluidRow(
      box(
        title = "Employment Growth Rate by Cluster (2017-2022)",
        echarts4rOutput("plot_growth_by_cluster", height = "350px"),
        width = 12,
        solidHeader = TRUE,
        status = "primary"
      )
    ),

    # Industry composition
    fluidRow(
      box(
        title = "Industry Composition by Cluster",
        selectInput("cluster_select", "Select Cluster:",
                    choices = c("Growing Manufacturing",
                               "Service & Retail (Small)",
                               "Service & Retail (Large)",
                               "Agricultural Services",
                               "Tourism & Hospitality",
                               "Boom Counties (Mining)",
                               "Education & Healthcare"),
                    selected = "Growing Manufacturing"),
        echarts4rOutput("plot_industry_comp", height = "350px"),
        width = 12,
        solidHeader = TRUE,
        status = "primary"
      )
    ),

    # Data table
    fluidRow(
      box(
        title = "County Details",
        downloadButton("download_county_data", "Download CSV"),
        DT::dataTableOutput("table_county_details"),
        width = 12,
        solidHeader = TRUE
      )
    )
  )
}

# ============================================================================
# SERVER COMPONENTS
# ============================================================================

geographic_server <- function(input, output, session, cluster_data, shift_share_data) {

  # Update state filter choices based on data
  observe({
    req(cluster_data)
    states <- sort(unique(cluster_data$state_name))
    updateSelectInput(session, "state_filter",
                      choices = c("All States" = "all", setNames(states, states)))
  })

  # Filtered data reactive
  filtered_data <- reactive({
    req(cluster_data)
    dt <- copy(cluster_data)

    if (!is.null(input$state_filter) && input$state_filter != "all") {
      dt <- dt[state_name == input$state_filter]
    }

    if (!is.null(input$cluster_filter) && input$cluster_filter != "all") {
      dt <- dt[cluster_name == input$cluster_filter]
    }

    dt
  })

  # Value boxes
  output$vbox_counties <- renderValueBox({
    n <- nrow(filtered_data())
    valueBox(
      format(n, big.mark = ","),
      "Counties",
      icon = icon("map-marker"),
      color = "blue"
    )
  })

  output$vbox_clusters <- renderValueBox({
    n <- length(unique(filtered_data()$cluster))
    valueBox(
      n,
      "Cluster Types",
      icon = icon("layer-group"),
      color = "green"
    )
  })

  output$vbox_total_emp <- renderValueBox({
    emp <- sum(filtered_data()$total_emp, na.rm = TRUE)
    valueBox(
      paste0(round(emp / 1e6, 1), "M"),
      "Total Employment",
      icon = icon("users"),
      color = "purple"
    )
  })

  output$vbox_avg_growth <- renderValueBox({
    growth <- mean(filtered_data()$employment_growth_rate, na.rm = TRUE)
    valueBox(
      paste0(round(growth, 1), "%"),
      "Avg Growth 2017-22",
      icon = icon("chart-line"),
      color = "yellow"
    )
  })

  # State summary HTML
  output$state_summary_html <- renderUI({
    dt <- filtered_data()

    if (nrow(dt) == 0) {
      return(HTML("<p>No data available</p>"))
    }

    # Calculate summary stats
    n_counties <- nrow(dt)
    total_emp <- sum(dt$total_emp, na.rm = TRUE)
    avg_growth <- mean(dt$employment_growth_rate, na.rm = TRUE)
    top_cluster <- dt[, .N, by = cluster_name][order(-N)][1, cluster_name]

    HTML(paste0(
      "<p><strong>Counties:</strong> ", format(n_counties, big.mark = ","), "</p>",
      "<p><strong>Employment:</strong> ", format(round(total_emp), big.mark = ","), "</p>",
      "<p><strong>Avg Growth:</strong> ", round(avg_growth, 1), "%</p>",
      "<p><strong>Top Cluster:</strong> ", top_cluster, "</p>"
    ))
  })

  # Cluster pie chart
  output$plot_cluster_pie <- renderEcharts4r({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    cluster_counts <- dt[, .(count = .N), by = cluster_name][order(-count)]

    cluster_counts |>
      e_charts(cluster_name) |>
      e_pie(count, radius = c("40%", "70%")) |>
      e_tooltip(trigger = "item") |>
      e_legend(show = FALSE)
  })

  # Cluster distribution chart
  output$plot_cluster_dist <- renderEcharts4r({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    cluster_summary <- dt[, .(
      count = .N,
      total_emp = sum(total_emp, na.rm = TRUE)
    ), by = cluster_name]

    cluster_summary[order(-count)] |>
      e_charts(cluster_name) |>
      e_bar(count, name = "Number of Counties") |>
      e_x_axis(axisLabel = list(rotate = 45, interval = 0)) |>
      e_y_axis(name = "Counties") |>
      e_tooltip(trigger = "axis") |>
      e_legend(show = FALSE)
  })

  # Cluster summary table
  output$table_cluster_summary <- DT::renderDataTable({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    summary_dt <- dt[, .(
      Counties = .N,
      `Avg Employment` = format(round(mean(total_emp, na.rm = TRUE)), big.mark = ","),
      `Avg Growth %` = round(mean(employment_growth_rate, na.rm = TRUE), 1),
      `Avg Regional Effect` = round(mean(regional_share_effect_per_1k, na.rm = TRUE), 1)
    ), by = .(Cluster = cluster_name)]

    summary_dt[order(-Counties)]
  }, options = list(pageLength = 8, dom = 't'), rownames = FALSE)

  # Shift-share top counties
  output$plot_shift_share_top <- renderEcharts4r({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    top_counties <- dt[order(-regional_share_effect)][1:min(15, nrow(dt))]
    top_counties[, label := paste0(state_name, " (", county, ")")]

    top_counties |>
      e_charts(label) |>
      e_bar(regional_share_effect, name = "Regional Share Effect") |>
      e_x_axis(axisLabel = list(rotate = 45, interval = 0)) |>
      e_y_axis(name = "Jobs") |>
      e_tooltip(
        formatter = htmlwidgets::JS(
          "function(params) {
            return params.name + '<br/>' +
                   'Jobs: ' + Math.round(params.value).toLocaleString();
          }"
        )
      ) |>
      e_legend(show = FALSE) |>
      e_color("#2ca02c")
  })

  # Shift-share bottom counties
  output$plot_shift_share_bottom <- renderEcharts4r({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    bottom_counties <- dt[order(regional_share_effect)][1:min(15, nrow(dt))]
    bottom_counties[, label := paste0(state_name, " (", county, ")")]

    bottom_counties |>
      e_charts(label) |>
      e_bar(regional_share_effect, name = "Regional Share Effect") |>
      e_x_axis(axisLabel = list(rotate = 45, interval = 0)) |>
      e_y_axis(name = "Jobs") |>
      e_tooltip(
        formatter = htmlwidgets::JS(
          "function(params) {
            return params.name + '<br/>' +
                   'Jobs: ' + Math.round(params.value).toLocaleString();
          }"
        )
      ) |>
      e_legend(show = FALSE) |>
      e_color("#d62728")
  })

  # Growth by cluster boxplot
  output$plot_growth_by_cluster <- renderEcharts4r({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    # Calculate summary stats for each cluster
    growth_summary <- dt[, .(
      avg_growth = mean(employment_growth_rate, na.rm = TRUE),
      median_growth = median(employment_growth_rate, na.rm = TRUE),
      q25 = quantile(employment_growth_rate, 0.25, na.rm = TRUE),
      q75 = quantile(employment_growth_rate, 0.75, na.rm = TRUE),
      n = .N
    ), by = cluster_name][order(-avg_growth)]

    growth_summary |>
      e_charts(cluster_name) |>
      e_bar(avg_growth, name = "Average Growth Rate (%)") |>
      e_x_axis(axisLabel = list(rotate = 45, interval = 0)) |>
      e_y_axis(name = "Growth Rate (%)") |>
      e_tooltip(
        formatter = htmlwidgets::JS(
          "function(params) {
            return params.name + '<br/>' +
                   'Avg Growth: ' + params.value.toFixed(1) + '%';
          }"
        )
      ) |>
      e_legend(show = FALSE)
  })

  # Industry composition by cluster
  output$plot_industry_comp <- renderEcharts4r({
    req(cluster_data, input$cluster_select)

    cluster_subset <- cluster_data[cluster_name == input$cluster_select]
    req(nrow(cluster_subset) > 0)

    # Calculate average industry shares
    industry_cols <- grep("^share_", names(cluster_subset), value = TRUE)

    industry_avgs <- sapply(industry_cols, function(col) {
      mean(cluster_subset[[col]], na.rm = TRUE) * 100
    })

    industry_dt <- data.table(
      Industry = gsub("share_", "", names(industry_avgs)),
      Share = round(industry_avgs, 1)
    )[order(-Share)][1:10]  # Top 10 industries

    # Clean industry names
    industry_dt[, Industry := gsub("_", " ", Industry)]
    industry_dt[, Industry := tools::toTitleCase(Industry)]

    industry_dt |>
      e_charts(Industry) |>
      e_bar(Share, name = "Industry Share (%)") |>
      e_x_axis(axisLabel = list(rotate = 45, interval = 0)) |>
      e_y_axis(name = "Share (%)") |>
      e_tooltip() |>
      e_legend(show = FALSE)
  })

  # County details table
  output$table_county_details <- DT::renderDataTable({
    dt <- filtered_data()
    req(nrow(dt) > 0)

    display_dt <- dt[, .(
      State = state_name,
      `County FIPS` = county,
      FIPS = fips,
      Cluster = cluster_name,
      Employment = format(total_emp, big.mark = ","),
      `Growth %` = round(employment_growth_rate, 1),
      `Regional Effect` = format(round(regional_share_effect), big.mark = ","),
      `Industry Mix` = format(round(industry_mix_effect), big.mark = ",")
    )]

    display_dt
  }, options = list(pageLength = 15, scrollX = TRUE), rownames = FALSE, filter = "top")

  # Download handler
  output$download_county_data <- downloadHandler(
    filename = function() {
      paste0("StarCruiser_County_Data_", Sys.Date(), ".csv")
    },
    content = function(file) {
      fwrite(filtered_data(), file)
    }
  )
}
