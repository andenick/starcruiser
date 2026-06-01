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

    # =====================================================
    # LEAFLET MAP (Track B1.2)
    # =====================================================
    fluidRow(
      box(
        title = "Interactive County Map", width = 12,
        solidHeader = TRUE, status = "primary",
        fluidRow(
          column(4,
            selectInput("map_metric", "Color by:",
              choices = c("Cluster" = "cluster_name",
                          "Employment Growth %" = "employment_growth_rate",
                          "Total Employment" = "total_emp",
                          "Regional Effect (per 1K)" = "regional_share_effect_per_1k"))
          ),
          column(8,
            helpText("Click a county for details. Zoom and pan to explore.")
          )
        ),
        leafletOutput("county_map", height = "500px")
      )
    ),

    # County detail panel (appears on click)
    fluidRow(
      box(
        title = "Selected County Detail", width = 12,
        collapsible = TRUE, collapsed = TRUE,
        uiOutput("county_detail_panel")
      )
    ),

    # =====================================================
    # STATE COMPARISON (Track B1.3)
    # =====================================================
    fluidRow(
      box(
        title = "State Comparison", width = 12,
        selectInput("compare_states", "Select States (2-5):",
          choices = NULL, multiple = TRUE,
          selected = c("California", "Texas"))
      )
    ),
    fluidRow(
      box(
        title = "Employment by State",
        echarts4rOutput("state_bar", height = "350px"),
        width = 6, solidHeader = TRUE, status = "info"
      ),
      box(
        title = "Cluster Distribution by State",
        echarts4rOutput("state_cluster_bar", height = "350px"),
        width = 6, solidHeader = TRUE, status = "info"
      )
    ),

    # =====================================================
    # LEADING COUNTIES (Track B1.4)
    # =====================================================
    fluidRow(
      box(
        title = "Employment Growth Leaders",
        echarts4rOutput("leading_chart", height = "400px"),
        helpText("Counties with consistently above-average employment growth."),
        width = 6, solidHeader = TRUE, status = "success"
      ),
      box(
        title = "Leading County Rankings",
        DTOutput("leading_table"),
        width = 6, solidHeader = TRUE, status = "success"
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

  # =====================================================
  # LEAFLET MAP SERVER (Track B1.2)
  # =====================================================

  # Load county GeoJSON shapes
  county_shapes <- reactive({
    geojson_path <- file.path("data", "counties_with_clusters.geojson")
    if (!file.exists(geojson_path)) return(NULL)
    tryCatch(
      sf::st_read(geojson_path, quiet = TRUE),
      error = function(e) {
        message("Error loading GeoJSON: ", e$message)
        NULL
      }
    )
  })

  output$county_map <- renderLeaflet({
    shapes <- county_shapes()

    if (is.null(shapes)) {
      # Fallback: show a base map with a message
      return(
        leaflet() %>%
          addProviderTiles(providers$CartoDB.Positron) %>%
          setView(lng = -96, lat = 39, zoom = 4) %>%
          addControl(
            html = "<div style='background:white;padding:10px;border-radius:5px;'>
                     <b>County map not available.</b><br>
                     Run <code>python Technical/prepare_county_geojson.py</code> first.
                    </div>",
            position = "topright"
          )
      )
    }

    # Apply filters
    if (!is.null(input$state_filter) && input$state_filter != "all") {
      if ("STUSPS" %in% names(shapes)) {
        # Map state name back to abbreviation
        state_abbrs <- c(
          "Alabama"="AL","Alaska"="AK","Arizona"="AZ","Arkansas"="AR","California"="CA",
          "Colorado"="CO","Connecticut"="CT","Delaware"="DE","DC"="DC","Florida"="FL",
          "Georgia"="GA","Hawaii"="HI","Idaho"="ID","Illinois"="IL","Indiana"="IN",
          "Iowa"="IA","Kansas"="KS","Kentucky"="KY","Louisiana"="LA","Maine"="ME",
          "Maryland"="MD","Massachusetts"="MA","Michigan"="MI","Minnesota"="MN",
          "Mississippi"="MS","Missouri"="MO","Montana"="MT","Nebraska"="NE","Nevada"="NV",
          "New Hampshire"="NH","New Jersey"="NJ","New Mexico"="NM","New York"="NY",
          "North Carolina"="NC","North Dakota"="ND","Ohio"="OH","Oklahoma"="OK",
          "Oregon"="OR","Pennsylvania"="PA","Rhode Island"="RI","South Carolina"="SC",
          "South Dakota"="SD","Tennessee"="TN","Texas"="TX","Utah"="UT","Vermont"="VT",
          "Virginia"="VA","Washington"="WA","West Virginia"="WV","Wisconsin"="WI","Wyoming"="WY"
        )
        abbr <- state_abbrs[input$state_filter]
        if (!is.na(abbr)) shapes <- shapes[shapes$STUSPS == abbr, ]
      }
    }

    metric <- input$map_metric

    if (metric == "cluster_name" && "cluster_name" %in% names(shapes)) {
      pal <- colorFactor(
        palette = unname(cluster_colors),
        domain = names(cluster_colors),
        na.color = "#cccccc"
      )

      leaflet(shapes) %>%
        addProviderTiles(providers$CartoDB.Positron) %>%
        addPolygons(
          fillColor = ~pal(cluster_name),
          fillOpacity = 0.7,
          weight = 0.5,
          color = "#333",
          label = ~paste0(NAME, " (", cluster_name, ")"),
          layerId = ~GEOID,
          highlightOptions = highlightOptions(
            weight = 2, color = "#000", fillOpacity = 0.9
          )
        ) %>%
        addLegend("bottomright", pal = pal,
                  values = names(cluster_colors), title = "Cluster")
    } else if (metric %in% names(shapes)) {
      vals <- shapes[[metric]]
      if (is.numeric(vals)) {
        pal <- colorNumeric("YlOrRd", domain = vals, na.color = "#cccccc")

        leaflet(shapes) %>%
          addProviderTiles(providers$CartoDB.Positron) %>%
          addPolygons(
            fillColor = ~pal(shapes[[metric]]),
            fillOpacity = 0.7,
            weight = 0.5,
            color = "#333",
            label = ~paste0(NAME, ": ", round(shapes[[metric]], 2)),
            layerId = ~GEOID,
            highlightOptions = highlightOptions(
              weight = 2, color = "#000", fillOpacity = 0.9
            )
          ) %>%
          addLegend("bottomright", pal = pal,
                    values = vals, title = gsub("_", " ", metric))
      } else {
        leaflet(shapes) %>%
          addProviderTiles(providers$CartoDB.Positron) %>%
          setView(lng = -96, lat = 39, zoom = 4)
      }
    } else {
      leaflet(shapes) %>%
        addProviderTiles(providers$CartoDB.Positron) %>%
        setView(lng = -96, lat = 39, zoom = 4)
    }
  })

  # County click handler
  observeEvent(input$county_map_shape_click, {
    click <- input$county_map_shape_click
    req(click$id)
    req(cluster_data)

    county_info <- cluster_data[fips == click$id]

    output$county_detail_panel <- renderUI({
      if (nrow(county_info) == 0) {
        return(HTML(paste0("<p>No data for FIPS: ", click$id, "</p>")))
      }

      row <- county_info[1]
      tagList(
        h4(paste(row$state_name, "- County FIPS:", row$county)),
        fluidRow(
          column(3, p(strong("Cluster:"), row$cluster_name)),
          column(3, p(strong("Employment:"), format(row$total_emp, big.mark = ","))),
          column(3, p(strong("Growth Rate:"), paste0(round(row$employment_growth_rate, 1), "%"))),
          column(3, p(strong("Regional Effect:"), format(round(row$regional_share_effect), big.mark = ",")))
        )
      )
    })
  })

  # =====================================================
  # STATE COMPARISON SERVER (Track B1.3)
  # =====================================================

  # Update state comparison choices
  observe({
    req(cluster_data)
    states <- sort(unique(cluster_data$state_name))
    updateSelectInput(session, "compare_states",
                      choices = states,
                      selected = if (length(states) >= 2) states[1:2] else states)
  })

  output$state_bar <- renderEcharts4r({
    req(cluster_data, input$compare_states)
    req(length(input$compare_states) >= 2)

    state_summary <- cluster_data[state_name %in% input$compare_states,
      .(total_emp = sum(total_emp, na.rm = TRUE),
        avg_growth = weighted.mean(employment_growth_rate, total_emp, na.rm = TRUE),
        n_counties = .N),
      by = state_name
    ][order(-total_emp)]

    state_summary %>%
      e_charts(state_name) %>%
      e_bar(total_emp, name = "Total Employment") %>%
      e_tooltip(trigger = "axis",
        formatter = htmlwidgets::JS("
          function(params) {
            return params[0].name + '<br>Employment: ' +
                   Math.round(params[0].value).toLocaleString();
          }
        ")
      ) %>%
      e_x_axis(axisLabel = list(rotate = 30)) %>%
      e_y_axis(name = "Employment") %>%
      e_legend(show = FALSE) %>%
      e_color("#3c8dbc")
  })

  output$state_cluster_bar <- renderEcharts4r({
    req(cluster_data, input$compare_states)
    req(length(input$compare_states) >= 2)

    cluster_by_state <- cluster_data[state_name %in% input$compare_states,
      .N, by = .(state_name, cluster_name)]

    if (nrow(cluster_by_state) == 0) return(NULL)

    cluster_by_state %>%
      group_by(cluster_name) %>%
      e_charts(state_name) %>%
      e_bar(N, stack = "cluster") %>%
      e_tooltip(trigger = "axis") %>%
      e_legend(bottom = "0%", type = "scroll") %>%
      e_x_axis(axisLabel = list(rotate = 30)) %>%
      e_y_axis(name = "Counties")
  })

  # =====================================================
  # LEADING COUNTIES SERVER (Track B1.4)
  # =====================================================

  leading_county_data <- reactive({
    # Load from JSON if available
    json_dir <- file.path(Sys.getenv("OUTPUT_ROOT", "outputs"), "LEADING_COUNTIES")
    if (!dir.exists(json_dir)) return(NULL)

    json_files <- list.files(json_dir, pattern = "leading_counties.*\\.json$", full.names = TRUE)
    if (length(json_files) > 0) {
      tryCatch(
        jsonlite::fromJSON(json_files[length(json_files)]),
        error = function(e) NULL
      )
    } else {
      # Fallback: compute from cluster_data (top growth leaders)
      NULL
    }
  })

  output$leading_chart <- renderEcharts4r({
    req(cluster_data)

    # Use cluster_data to find growth leaders
    leaders <- cluster_data[!is.na(employment_growth_rate)][order(-employment_growth_rate)][1:20]
    leaders[, label := paste0(state_name, " (", county, ")")]

    leaders %>%
      e_charts(label) %>%
      e_bar(employment_growth_rate, name = "Growth Rate (%)") %>%
      e_flip_coords() %>%
      e_tooltip(
        formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>Growth: ' + params.value[0].toFixed(1) + '%';
          }
        ")
      ) %>%
      e_x_axis(name = "Growth Rate (%)") %>%
      e_legend(show = FALSE) %>%
      e_color("#00a65a") %>%
      e_grid(left = "30%")
  })

  output$leading_table <- renderDT({
    req(cluster_data)

    leaders <- cluster_data[!is.na(employment_growth_rate)][order(-employment_growth_rate)][1:30]

    display <- leaders[, .(
      State = state_name,
      County = county,
      Cluster = cluster_name,
      Employment = format(total_emp, big.mark = ","),
      `Growth %` = round(employment_growth_rate, 1)
    )]

    datatable(display,
      options = list(pageLength = 10, dom = "ft"),
      rownames = FALSE
    )
  })

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
