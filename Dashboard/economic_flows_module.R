# ============================================================================
# ECONOMIC FLOWS MODULE - StarCruiser Dashboard v8.0
# ============================================================================
# Sankey diagrams for GDP component flows, sectoral treemaps
# Data: BEA NIPA tables
# ============================================================================

economic_flows_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      box(title = "GDP Component Flows (Sankey Diagram)", width = 12,
          helpText("How does GDP decompose into its major components?"),
          echarts4rOutput(ns("gdp_sankey"), height = "500px"),
          solidHeader = TRUE, status = "primary")
    ),
    fluidRow(
      box(title = "National Income by Industry (Treemap)", width = 12,
          selectInput(ns("nipa_year"), "Year:", choices = 2000:2025, selected = 2024),
          echarts4rOutput(ns("sector_treemap"), height = "500px"),
          solidHeader = TRUE, status = "info")
    ),
    fluidRow(
      box(title = "Government Receipts vs Expenditures Flow", width = 12,
          echarts4rOutput(ns("govt_sankey"), height = "400px"),
          solidHeader = TRUE, status = "success")
    )
  )
}

economic_flows_server <- function(id, bea_nipa, gdp_data) {
  moduleServer(id, function(input, output, session) {

    # GDP Sankey diagram
    output$gdp_sankey <- renderEcharts4r({
      if (is.null(bea_nipa) && is.null(gdp_data)) return(NULL)

      # Build GDP flow from latest available data
      # GDP -> Consumption (C), Investment (I), Government (G), Net Exports (NX)
      if (!is.null(gdp_data)) {
        latest <- gdp_data[, .SD[which.max(date)], by = series_id]
        get_val <- function(sid) {
          v <- latest[series_id == sid]$value
          if (length(v) == 0) return(0)
          abs(v)
        }

        gdp_val <- get_val("GDP")
        pce_val <- get_val("PCEC")
        gpdi_val <- get_val("GPDI")
        gce_val <- get_val("GCE")
        netexp_val <- get_val("NETEXP")

        if (gdp_val == 0) {
          # Estimate from known components
          gdp_val <- pce_val + gpdi_val + gce_val
        }
      } else {
        # Use NIPA data
        nipa_latest <- bea_nipa[TableName == "T10101"][order(-TimePeriod)][1:20]
        gdp_val <- nipa_latest[LineDescription == "Gross domestic product"]$DataValue[1]
        pce_val <- nipa_latest[grepl("Personal consumption", LineDescription)]$DataValue[1]
        gpdi_val <- nipa_latest[grepl("Gross private domestic investment", LineDescription)]$DataValue[1]
        gce_val <- nipa_latest[grepl("Government consumption", LineDescription)]$DataValue[1]
        netexp_val <- nipa_latest[grepl("Net exports", LineDescription)]$DataValue[1]
      }

      # Create Sankey data
      nodes <- data.table(name = c(
        "GDP", "Consumption (C)", "Investment (I)",
        "Government (G)", "Net Exports (NX)"
      ))

      links <- data.table(
        source = c("GDP", "GDP", "GDP", "GDP"),
        target = c("Consumption (C)", "Investment (I)", "Government (G)", "Net Exports (NX)"),
        value = c(
          max(1, pce_val),
          max(1, gpdi_val),
          max(1, gce_val),
          max(1, abs(netexp_val))
        )
      )

      e_charts() %>%
        e_sankey(links, source, target, value,
                 layoutIterations = 0,
                 nodeAlign = "left",
                 orient = "horizontal") %>%
        e_tooltip(trigger = "item") %>%
        e_title(subtext = paste("GDP:", format(round(gdp_val), big.mark = ","), "($B)"))
    })

    # Sector treemap from NIPA
    output$sector_treemap <- renderEcharts4r({
      if (is.null(bea_nipa)) return(NULL)

      # Get GDP by industry from T50100 or T10101
      sector_data <- bea_nipa[TableName == "T50100" &
                               grepl(paste0("^", input$nipa_year), TimePeriod)]
      if (nrow(sector_data) == 0) {
        sector_data <- bea_nipa[TableName == "T10101" &
                                 grepl(paste0("^", input$nipa_year), TimePeriod)]
      }
      if (nrow(sector_data) == 0) return(NULL)

      # Filter to positive values and meaningful line items
      sector_data <- sector_data[DataValue > 0 & LineNumber > 1]

      # Build treemap
      sector_data %>%
        e_charts() %>%
        e_treemap(DataValue, LineDescription) %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>$' + params.value.toLocaleString() + 'B';
          }
        "))
    })

    # Government flows Sankey
    output$govt_sankey <- renderEcharts4r({
      if (is.null(bea_nipa)) return(NULL)

      # Get government receipts vs expenditures from T30100
      govt <- bea_nipa[TableName == "T30100"][order(-TimePeriod)]
      if (nrow(govt) == 0) return(NULL)

      # Get latest year
      latest_period <- govt$TimePeriod[1]
      govt_latest <- govt[TimePeriod == latest_period & DataValue > 0]

      if (nrow(govt_latest) < 2) return(NULL)

      # Simplified: show main categories
      govt_latest[, category := fifelse(grepl("receipt|tax|contribution", LineDescription, ignore.case = TRUE),
                                        "Revenue", "Spending")]

      revenue <- govt_latest[category == "Revenue"]
      spending <- govt_latest[category == "Spending"]

      if (nrow(revenue) == 0 || nrow(spending) == 0) return(NULL)

      # Build links from Revenue sources -> Government -> Spending categories
      links <- rbindlist(list(
        revenue[, .(source = LineDescription, target = "Government", value = DataValue)],
        spending[, .(source = "Government", target = LineDescription, value = DataValue)]
      ))

      links <- links[value > 0][1:min(15, nrow(links))]  # Limit for readability

      e_charts() %>%
        e_sankey(links, source, target, value, orient = "horizontal") %>%
        e_tooltip(trigger = "item")
    })
  })
}
