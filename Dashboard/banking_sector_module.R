# ============================================================================
# BANKING SECTOR MODULE - StarCruiser Dashboard v8.0
# ============================================================================
# Bank structure treemap, health indicators, geographic distribution
# Data: FDIC BankFind (4,364 banks)
# ============================================================================

banking_sector_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_total_banks"), width = 3),
      valueBoxOutput(ns("vbox_total_assets"), width = 3),
      valueBoxOutput(ns("vbox_top10_share"), width = 3),
      valueBoxOutput(ns("vbox_gsib_count"), width = 3)
    ),

    # Bank size distribution treemap
    fluidRow(
      box(title = "Banking System Structure (by Asset Size)",
          echarts4rOutput(ns("bank_treemap"), height = "500px"),
          helpText("Size = total assets. Click to zoom into tiers."),
          width = 12, solidHeader = TRUE, status = "primary")
    ),

    # Tier distribution
    fluidRow(
      box(title = "Banks by Asset Tier",
          echarts4rOutput(ns("tier_chart"), height = "400px"),
          width = 6, solidHeader = TRUE, status = "info"),
      box(title = "Deposits by Asset Tier",
          echarts4rOutput(ns("tier_deposits"), height = "400px"),
          width = 6, solidHeader = TRUE, status = "success")
    ),

    # Bank health
    fluidRow(
      box(title = "Return on Assets (ROA) Distribution",
          echarts4rOutput(ns("roa_dist"), height = "350px"),
          helpText("Most healthy banks: ROA 0.5-1.5%. Negative ROA = unprofitable."),
          width = 6, solidHeader = TRUE, status = "warning"),
      box(title = "Top 20 Banks by Total Assets",
          DTOutput(ns("top_banks_table")),
          width = 6, solidHeader = TRUE, status = "primary")
    ),

    # Geographic
    fluidRow(
      box(title = "Banking Concentration by State",
          echarts4rOutput(ns("bank_geo_chart"), height = "400px"),
          width = 12, solidHeader = TRUE, status = "info")
    )
  )
}

banking_sector_server <- function(id, fdic_banks, fdic_universe) {
  moduleServer(id, function(input, output, session) {

    output$vbox_total_banks <- renderValueBox({
      n <- if (!is.null(fdic_banks)) nrow(fdic_banks) else 0
      valueBox(format(n, big.mark = ","), "FDIC-Insured Banks",
               icon = icon("landmark"), color = "blue")
    })

    output$vbox_total_assets <- renderValueBox({
      if (is.null(fdic_banks)) return(valueBox("N/A", "Total Assets", icon = icon("dollar-sign"), color = "gray"))
      total <- sum(fdic_banks$ASSET_MILLIONS, na.rm = TRUE)
      valueBox(paste0("$", round(total / 1000, 1), "T"), "Total Banking Assets",
               icon = icon("dollar-sign"), color = "green")
    })

    output$vbox_top10_share <- renderValueBox({
      if (is.null(fdic_banks)) return(valueBox("N/A", "Top 10 Share", icon = icon("chart-pie"), color = "gray"))
      total <- sum(fdic_banks$ASSET_MILLIONS, na.rm = TRUE)
      top10 <- sum(fdic_banks[order(-ASSET_MILLIONS)][1:10]$ASSET_MILLIONS, na.rm = TRUE)
      share <- round(top10 / total * 100)
      valueBox(paste0(share, "%"), "Top 10 Banks Asset Share",
               icon = icon("chart-pie"), color = if (share > 60) "red" else "yellow")
    })

    output$vbox_gsib_count <- renderValueBox({
      if (is.null(fdic_banks)) return(valueBox("N/A", "G-SIBs", icon = icon("globe"), color = "gray"))
      gsib <- sum(fdic_banks$IS_GSIB == 1, na.rm = TRUE)
      valueBox(gsib, "G-SIB Banks", icon = icon("globe"), color = "purple")
    })

    # Bank treemap by tier
    output$bank_treemap <- renderEcharts4r({
      if (is.null(fdic_banks)) return(NULL)

      # Top 50 banks as individual items
      top_banks <- fdic_banks[order(-ASSET_MILLIONS)][1:50]
      top_banks[, label := paste0(NAME, " ($", round(ASSET_MILLIONS / 1000, 0), "B)")]

      top_banks %>%
        e_charts() %>%
        e_treemap(ASSET_MILLIONS, label, levels = list(
          list(itemStyle = list(borderWidth = 2, borderColor = "#333", gapWidth = 1))
        )) %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) {
            return params.name + '<br>Assets: $' +
                   (params.value / 1000).toFixed(1) + 'B';
          }
        "))
    })

    # Tier distribution
    output$tier_chart <- renderEcharts4r({
      if (is.null(fdic_banks)) return(NULL)

      tier_counts <- fdic_banks[!is.na(TIER_NAME), .N, by = TIER_NAME][order(-N)]

      tier_counts %>%
        e_charts(TIER_NAME) %>%
        e_bar(N, name = "Number of Banks") %>%
        e_flip_coords() %>%
        e_tooltip() %>%
        e_legend(show = FALSE) %>%
        e_color("#3c8dbc") %>%
        e_grid(left = "35%") %>%
        e_x_axis(name = "Banks")
    })

    output$tier_deposits <- renderEcharts4r({
      if (is.null(fdic_banks)) return(NULL)

      tier_deps <- fdic_banks[!is.na(TIER_NAME),
        .(deposits_b = sum(DEP, na.rm = TRUE) / 1e6), by = TIER_NAME][order(-deposits_b)]

      tier_deps %>%
        e_charts(TIER_NAME) %>%
        e_bar(deposits_b, name = "Deposits ($B)") %>%
        e_flip_coords() %>%
        e_tooltip(formatter = htmlwidgets::JS("
          function(params) { return params.name + '<br>$' + params.value[0].toFixed(0) + 'B'; }
        ")) %>%
        e_legend(show = FALSE) %>%
        e_color("#00a65a") %>%
        e_grid(left = "35%") %>%
        e_x_axis(name = "Total Deposits ($B)")
    })

    # ROA distribution
    output$roa_dist <- renderEcharts4r({
      if (is.null(fdic_universe)) return(NULL)

      roa <- fdic_universe[!is.na(ROA) & ROA > -5 & ROA < 5]$ROA

      # Create histogram bins
      breaks <- seq(-3, 4, by = 0.25)
      hist_data <- data.table(
        bin = head(breaks, -1) + 0.125,
        count = as.numeric(table(cut(roa, breaks)))
      )

      hist_data %>%
        e_charts(bin) %>%
        e_bar(count, name = "Banks", itemStyle = list(color = htmlwidgets::JS("
          function(params) {
            var v = params.value[0];
            if (v < 0) return '#dd4b39';
            if (v < 0.5) return '#f39c12';
            if (v < 1.5) return '#00a65a';
            return '#3c8dbc';
          }
        "))) %>%
        e_mark_line(data = list(xAxis = 0), lineStyle = list(color = "#dd4b39", type = "dashed"),
                    label = list(formatter = "Break-even")) %>%
        e_tooltip() %>%
        e_legend(show = FALSE) %>%
        e_x_axis(name = "ROA (%)") %>%
        e_y_axis(name = "Number of Banks")
    })

    # Top banks table
    output$top_banks_table <- renderDT({
      if (is.null(fdic_banks)) return(NULL)

      top <- fdic_banks[order(-ASSET_MILLIONS)][1:20, .(
        Name = NAME,
        State = STALP,
        `Assets ($B)` = round(ASSET_MILLIONS / 1000, 1),
        `Deposits ($B)` = round(DEP / 1e6, 1),
        Tier = TIER_NAME
      )]

      datatable(top, options = list(pageLength = 20, dom = "t"), rownames = FALSE)
    })

    # Geographic concentration
    output$bank_geo_chart <- renderEcharts4r({
      if (is.null(fdic_banks)) return(NULL)

      state_data <- fdic_banks[, .(
        banks = .N,
        assets_b = sum(ASSET_MILLIONS, na.rm = TRUE) / 1000,
        avg_size_m = mean(ASSET_MILLIONS, na.rm = TRUE)
      ), by = STNAME][order(-assets_b)][1:25]

      state_data %>%
        e_charts(STNAME) %>%
        e_bar(assets_b, name = "Total Assets ($B)") %>%
        e_bar(banks, name = "Number of Banks", y_index = 1) %>%
        e_y_axis(index = 0, name = "Total Assets ($B)") %>%
        e_y_axis(index = 1, name = "Number of Banks") %>%
        e_flip_coords() %>%
        e_tooltip(trigger = "axis") %>%
        e_legend(bottom = "5%") %>%
        e_grid(left = "25%")
    })
  })
}
