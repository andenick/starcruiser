# ============================================================================
# STATE COMPARISON MODULE - StarCruiser Dashboard v8.0
# ============================================================================
# Multi-dimensional state comparison with parallel coordinates
# Data: BEA Regional, FDIC Banks, Census data
# ============================================================================

state_comparison_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      box(title = "Multi-Dimensional State Comparison", width = 12,
          helpText("Each line represents a state. Drag on axes to filter. Compare economic profiles across dimensions."),
          echarts4rOutput(ns("parallel_chart"), height = "500px"),
          solidHeader = TRUE, status = "primary")
    ),
    fluidRow(
      box(title = "State Economic Profile Table", width = 12,
          DTOutput(ns("state_table")),
          solidHeader = TRUE, status = "info")
    ),
    fluidRow(
      box(title = "Banking Presence by State",
          echarts4rOutput(ns("bank_state_chart"), height = "400px"),
          width = 6, solidHeader = TRUE, status = "success"),
      box(title = "Bank Assets by State",
          echarts4rOutput(ns("bank_assets_chart"), height = "400px"),
          width = 6, solidHeader = TRUE, status = "warning")
    )
  )
}

state_comparison_server <- function(id, bea_state_gdp, bea_state_income,
                                     fdic_banks, employment_data) {
  moduleServer(id, function(input, output, session) {

    # Build state summary table
    state_profiles <- reactive({
      if (is.null(bea_state_gdp)) return(NULL)

      BEA_REGIONS <- c("Far West", "Great Lakes", "Mideast", "New England",
                       "Plains", "Rocky Mountain", "Southeast", "Southwest")

      # Latest GDP
      latest_year <- max(bea_state_gdp$TimePeriod, na.rm = TRUE)
      gdp <- bea_state_gdp[TimePeriod == latest_year &
                            !GeoName %in% c("United States", BEA_REGIONS),
                           .(State = GeoName, GDP_B = DataValue / 1e6)]

      # GDP growth
      prev_year <- latest_year - 1
      gdp_prev <- bea_state_gdp[TimePeriod == prev_year &
                                 !GeoName %in% c("United States", BEA_REGIONS),
                                .(State = GeoName, GDP_prev = DataValue / 1e6)]
      gdp <- merge(gdp, gdp_prev, by = "State", all.x = TRUE)
      gdp[, GDP_Growth := (GDP_B / GDP_prev - 1) * 100]

      # Income
      if (!is.null(bea_state_income)) {
        income <- bea_state_income[TimePeriod == latest_year &
                                   !GeoName %in% c("United States", BEA_REGIONS),
                                  .(State = GeoName, Income_B = DataValue / 1e6)]
        gdp <- merge(gdp, income, by = "State", all.x = TRUE)
      }

      # Banking
      if (!is.null(fdic_banks)) {
        bank_summary <- fdic_banks[, .(
          Banks = .N,
          Bank_Assets_B = sum(ASSET_MILLIONS, na.rm = TRUE) / 1000
        ), by = .(State = STNAME)]
        gdp <- merge(gdp, bank_summary, by = "State", all.x = TRUE)
      }

      gdp[, GDP_prev := NULL]
      gdp
    })

    # Parallel coordinates chart
    output$parallel_chart <- renderEcharts4r({
      profiles <- state_profiles()
      if (is.null(profiles) || nrow(profiles) < 5) return(NULL)

      # Select numeric columns for parallel coordinates
      num_cols <- names(profiles)[sapply(profiles, is.numeric)]
      num_cols <- num_cols[num_cols != "GDP_prev"]

      if (length(num_cols) < 3) return(NULL)

      profiles %>%
        e_charts() %>%
        e_parallel(GDP_B, GDP_Growth, Income_B, Banks, Bank_Assets_B,
                   opts = list(
                     parallelAxis = lapply(seq_along(num_cols), function(i) {
                       list(dim = i - 1, name = gsub("_", " ", num_cols[i]))
                     })
                   )) %>%
        e_tooltip()
    })

    # State table
    output$state_table <- renderDT({
      profiles <- state_profiles()
      if (is.null(profiles)) return(NULL)

      display <- copy(profiles)
      display[, GDP_B := round(GDP_B, 1)]
      display[, GDP_Growth := round(GDP_Growth, 1)]
      if ("Income_B" %in% names(display)) display[, Income_B := round(Income_B, 1)]
      if ("Bank_Assets_B" %in% names(display)) display[, Bank_Assets_B := round(Bank_Assets_B, 1)]

      datatable(display[order(-GDP_B)],
        options = list(pageLength = 20, scrollX = TRUE),
        rownames = FALSE, filter = "top"
      )
    })

    # Banking by state
    output$bank_state_chart <- renderEcharts4r({
      if (is.null(fdic_banks)) return(NULL)

      bank_count <- fdic_banks[, .N, by = STNAME][order(-N)][1:20]

      bank_count %>%
        e_charts(STNAME) %>%
        e_bar(N, name = "Number of Banks") %>%
        e_flip_coords() %>%
        e_tooltip() %>%
        e_legend(show = FALSE) %>%
        e_color("#3c8dbc") %>%
        e_grid(left = "25%") %>%
        e_x_axis(name = "Banks")
    })

    # Bank assets by state
    output$bank_assets_chart <- renderEcharts4r({
      if (is.null(fdic_banks)) return(NULL)

      assets <- fdic_banks[, .(assets_b = sum(ASSET_MILLIONS, na.rm = TRUE) / 1000),
                           by = STNAME][order(-assets_b)][1:20]

      assets %>%
        e_charts(STNAME) %>%
        e_bar(assets_b, name = "Total Assets ($B)") %>%
        e_flip_coords() %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>$' + params.value[0].toFixed(0) + 'B';
          }
        ")) %>%
        e_legend(show = FALSE) %>%
        e_color("#00a65a") %>%
        e_grid(left = "25%") %>%
        e_x_axis(name = "Total Bank Assets ($B)")
    })
  })
}
