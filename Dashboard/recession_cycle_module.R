# ============================================================================
# RECESSION PREDICTION & ECONOMIC CYCLE MODULE - StarCruiser Dashboard
# ============================================================================
# Track A1.2+A1.3: Sahm Rule, Composite Recession Index, Business Cycle
# Features: Recession probability gauge, backtest against NBER dates,
#           cycle timeline, current phase diagnosis
# ============================================================================

# UI
recession_ui <- function(id) {
  ns <- NS(id)
  tagList(
    # Value boxes
    fluidRow(
      valueBoxOutput(ns("vbox_sahm"), width = 3),
      valueBoxOutput(ns("vbox_inversion_days"), width = 3),
      valueBoxOutput(ns("vbox_composite"), width = 3),
      valueBoxOutput(ns("vbox_cycle_phase"), width = 3)
    ),

    # Gauge + Sahm Rule chart
    fluidRow(
      box(
        title = "Composite Recession Index",
        echarts4rOutput(ns("recession_gauge"), height = "300px"),
        helpText("0 = No recession risk, 100 = High recession risk"),
        width = 4, solidHeader = TRUE, status = "danger"
      ),
      box(
        title = "Sahm Rule Indicator",
        echarts4rOutput(ns("sahm_chart"), height = "300px"),
        helpText("Triggered when 3-month avg unemployment rises >= 0.50 pp above its 12-month low."),
        width = 8, solidHeader = TRUE, status = "warning"
      )
    ),

    # Composite index timeline
    fluidRow(
      box(
        title = "Recession Risk Over Time",
        echarts4rOutput(ns("composite_timeline"), height = "400px"),
        width = 12, solidHeader = TRUE, status = "primary"
      )
    ),

    # Backtest results
    fluidRow(
      box(
        title = "Historical Backtest: Model vs NBER Recession Dates",
        DTOutput(ns("backtest_table")),
        width = 12, solidHeader = TRUE, status = "info"
      )
    ),

    # Business Cycle Timeline (A1.3)
    fluidRow(
      box(
        title = "Business Cycle Timeline",
        echarts4rOutput(ns("cycle_timeline"), height = "250px"),
        width = 12, solidHeader = TRUE, status = "success"
      )
    ),

    # Cycle statistics
    fluidRow(
      box(
        title = "Business Cycle Statistics",
        DTOutput(ns("cycle_stats")),
        width = 12, solidHeader = TRUE, status = "success"
      )
    ),

    # Methodology
    fluidRow(
      box(
        title = "Methodology", width = 12, collapsible = TRUE, collapsed = TRUE,
        HTML("
          <h4>Composite Recession Index Components</h4>
          <ul>
            <li><strong>Yield Curve (40%)</strong>: 10Y-2Y Treasury spread. Fully triggered at -50 bps inversion.</li>
            <li><strong>Sahm Rule (30%)</strong>: 3-month avg unemployment minus 12-month low. Triggered at +0.50 pp.</li>
            <li><strong>Payroll Deceleration (20%)</strong>: When 3-month payroll growth falls below 12-month growth.</li>
            <li><strong>CPI Acceleration (10%)</strong>: When headline CPI YoY exceeds core CPI YoY by >0.5 pp.</li>
          </ul>
          <h4>Sahm Rule</h4>
          <p>Developed by economist Claudia Sahm. The rule triggers when the 3-month moving average of
          the national unemployment rate rises by 0.50 percentage points or more relative to its low
          during the previous 12 months. Has correctly identified every recession since 1970.</p>
          <h4>Business Cycle Dating</h4>
          <p>Uses NBER official recession dates. Expansions are periods between recessions.
          Current phase estimated by position within average expansion duration.</p>
        ")
      )
    )
  )
}

# SERVER
recession_server <- function(id, employment_data, rates_data, inflation_data,
                              yield_spreads, sahm_data, recession_periods) {
  moduleServer(id, function(input, output, session) {

    # ---- Compute Sahm Rule from pre-computed data ----
    sahm_current <- reactive({
      req(sahm_data)
      latest <- sahm_data[!is.na(sahm_value)][order(-date)][1]
      if (nrow(latest) == 0) return(list(value = NA, date = NA))
      list(value = latest$sahm_value, date = latest$date)
    })

    # ---- Yield curve inversion streak ----
    inversion_streak <- reactive({
      req(yield_spreads)
      spreads <- yield_spreads[!is.na(spread_2_10)][order(-date)]
      if (nrow(spreads) == 0) return(0)

      # Count consecutive inverted days from most recent
      streak <- 0
      for (i in 1:nrow(spreads)) {
        if (spreads$spread_2_10[i] < 0) {
          streak <- streak + 1
        } else {
          break
        }
      }
      streak
    })

    # ---- Composite Recession Index ----
    composite_data <- reactive({
      emp <- employment_data()
      rat <- rates_data()
      inf <- inflation_data()

      # 1. Yield curve component (40%)
      spread_dt <- copy(yield_spreads)[!is.na(spread_2_10)]
      spread_dt[, month := floor_date(date, "month")]
      spread_monthly <- spread_dt[, .(spread_2_10 = last(spread_2_10)), by = month]

      # 2. Sahm component (30%)
      sahm_dt <- copy(sahm_data)[!is.na(sahm_value)]
      sahm_dt[, month := floor_date(date, "month")]

      # 3. Payroll deceleration (20%)
      payems <- emp[series_id == "PAYEMS"][order(date)]
      payems[, month := floor_date(date, "month")]
      payems[, growth_3mo := (value / shift(value, 3) - 1) * 100 * 4]  # annualized
      payems[, growth_12mo := (value / shift(value, 12) - 1) * 100]

      # 4. CPI acceleration (10%)
      cpi_all <- inf[series_id == "CPIAUCSL"][order(date)]
      cpi_all[, month := floor_date(date, "month")]
      cpi_core <- inf[series_id == "CPILFESL"][order(date)]
      cpi_core[, month := floor_date(date, "month")]

      # Merge all on month
      composite <- spread_monthly[, .(month, spread_2_10)]
      composite <- merge(composite, sahm_dt[, .(month, sahm_value)], by = "month", all.x = TRUE)
      composite <- merge(composite, payems[, .(month, growth_3mo, growth_12mo)], by = "month", all.x = TRUE)

      # CPI YoY
      cpi_all_yoy <- cpi_all[!is.na(yoy_change), .(month, cpi_yoy = yoy_change)]
      cpi_core_yoy <- cpi_core[!is.na(yoy_change), .(month, core_yoy = yoy_change)]
      composite <- merge(composite, cpi_all_yoy, by = "month", all.x = TRUE)
      composite <- merge(composite, cpi_core_yoy, by = "month", all.x = TRUE)

      setorder(composite, month)

      # Calculate components
      composite[, yc_component := pmin(1, pmax(0, -spread_2_10 / 0.50)) * 40]
      composite[, sahm_component := pmin(1, pmax(0, sahm_value / 0.50)) * 30]
      composite[, payroll_component := fifelse(
        !is.na(growth_3mo) & !is.na(growth_12mo) & growth_12mo > 0,
        pmin(1, pmax(0, (growth_12mo - growth_3mo) / growth_12mo)) * 20,
        0
      )]
      composite[, cpi_component := fifelse(
        !is.na(cpi_yoy) & !is.na(core_yoy),
        pmin(1, pmax(0, (cpi_yoy - core_yoy - 0.5) / 1.0)) * 10,
        0
      )]

      composite[, composite_index := yc_component + sahm_component + payroll_component + cpi_component]

      composite
    })

    # ---- Value Boxes ----
    output$vbox_sahm <- renderValueBox({
      s <- sahm_current()
      color <- if (is.na(s$value)) "gray"
               else if (s$value >= 0.5) "red"
               else if (s$value >= 0.3) "yellow"
               else "green"

      valueBox(
        value = if (!is.na(s$value)) paste0(round(s$value, 2), " pp") else "N/A",
        subtitle = paste("Sahm Rule -", if (!is.na(s$date)) s$date else ""),
        icon = icon("exclamation-triangle"),
        color = color
      )
    })

    output$vbox_inversion_days <- renderValueBox({
      days <- inversion_streak()
      color <- if (days > 60) "red" else if (days > 0) "yellow" else "green"

      valueBox(
        value = days,
        subtitle = "Days Curve Inverted (streak)",
        icon = icon("chart-area"),
        color = color
      )
    })

    output$vbox_composite <- renderValueBox({
      comp <- composite_data()
      latest <- comp[!is.na(composite_index)][order(-month)][1]

      if (nrow(latest) == 0) {
        valueBox("N/A", "Composite Index", icon = icon("tachometer-alt"), color = "gray")
      } else {
        val <- round(latest$composite_index)
        color <- if (val >= 50) "red" else if (val >= 25) "yellow" else "green"
        valueBox(
          value = paste0(val, " / 100"),
          subtitle = "Composite Recession Index",
          icon = icon("tachometer-alt"),
          color = color
        )
      }
    })

    output$vbox_cycle_phase <- renderValueBox({
      # Determine current cycle phase based on last recession end
      last_recession_end <- max(recession_periods$end)
      months_since <- as.numeric(difftime(Sys.Date(), last_recession_end, units = "days")) / 30.44

      # Average expansion is ~65 months (post-WWII)
      avg_expansion <- 65
      pct <- months_since / avg_expansion

      phase <- if (pct < 0.33) "Early Expansion"
               else if (pct < 0.66) "Mid Expansion"
               else "Late Expansion"

      color <- if (pct < 0.33) "green" else if (pct < 0.66) "blue" else "yellow"

      valueBox(
        value = phase,
        subtitle = paste0(round(months_since), " months since last recession"),
        icon = icon("sync"),
        color = color
      )
    })

    # ---- Gauge Chart ----
    output$recession_gauge <- renderEcharts4r({
      comp <- composite_data()
      latest <- comp[!is.na(composite_index)][order(-month)][1]

      val <- if (nrow(latest) > 0) round(latest$composite_index) else 0

      data.table(name = "Risk", value = val) %>%
        e_charts() %>%
        e_gauge(value, name = "Risk",
          min = 0, max = 100,
          axisLine = list(
            lineStyle = list(
              width = 20,
              color = list(
                list(0.25, "#91cc75"),  # Green: 0-25
                list(0.50, "#fac858"),  # Yellow: 25-50
                list(0.75, "#ee6666"),  # Orange: 50-75
                list(1.0, "#c23531")    # Red: 75-100
              )
            )
          ),
          detail = list(
            formatter = "{value}",
            fontSize = 28,
            offsetCenter = list(0, "60%")
          ),
          pointer = list(length = "60%")
        ) %>%
        e_tooltip()
    })

    # ---- Sahm Rule Chart ----
    output$sahm_chart <- renderEcharts4r({
      dt <- sahm_data[!is.na(sahm_value)]
      if (nrow(dt) == 0) return(NULL)

      chart <- dt %>%
        e_charts(date) %>%
        e_line(sahm_value, symbol = "none", color = "#dd4b39", sampling = "lttb",
               name = "Sahm Rule") %>%
        e_mark_line(
          data = list(yAxis = 0.5),
          lineStyle = list(color = "#c23531", type = "dashed", width = 2),
          label = list(formatter = "Trigger: 0.50 pp")
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Sahm Value (pp)")

      add_recession_bands(chart)
    })

    # ---- Composite Timeline ----
    output$composite_timeline <- renderEcharts4r({
      comp <- composite_data()[!is.na(composite_index)]
      if (nrow(comp) == 0) return(NULL)

      chart <- comp %>%
        e_charts(month) %>%
        e_line(composite_index, symbol = "none", color = "#c23531", sampling = "lttb",
               name = "Composite Index") %>%
        e_area(composite_index, itemStyle = list(opacity = 0.15), name = "Risk Zone") %>%
        e_mark_line(
          data = list(yAxis = 50),
          lineStyle = list(color = "#dd4b39", type = "dashed"),
          label = list(formatter = "High Risk Threshold")
        ) %>%
        e_tooltip(trigger = "axis") %>%
        e_datazoom(type = "slider") %>%
        e_y_axis(name = "Composite Index", min = 0, max = 100)

      add_recession_bands(chart)
    })

    # ---- Backtest Table ----
    output$backtest_table <- renderDT({
      comp <- composite_data()

      backtest <- rbindlist(lapply(1:nrow(recession_periods), function(i) {
        rec_start <- recession_periods$start[i]
        rec_name <- recession_periods$name[i]

        # Find first date composite > 50 before recession start
        pre_recession <- comp[month < rec_start & composite_index > 50][order(month)]

        if (nrow(pre_recession) > 0) {
          first_signal <- pre_recession$month[1]
          lead_months <- round(as.numeric(difftime(rec_start, first_signal, units = "days")) / 30.44)
          signal_value <- round(pre_recession$composite_index[1])
        } else {
          # Check if it triggered during recession
          during <- comp[month >= rec_start & month <= recession_periods$end[i] & composite_index > 50]
          if (nrow(during) > 0) {
            first_signal <- during$month[1]
            lead_months <- -round(as.numeric(difftime(first_signal, rec_start, units = "days")) / 30.44)
            signal_value <- round(during$composite_index[1])
          } else {
            first_signal <- NA
            lead_months <- NA
            signal_value <- NA
          }
        }

        data.table(
          Recession = rec_name,
          `NBER Start` = rec_start,
          `NBER End` = recession_periods$end[i],
          `First Signal Date` = first_signal,
          `Lead Time (months)` = lead_months,
          `Signal Value` = signal_value,
          `Detected` = ifelse(!is.na(first_signal), "Yes", "No")
        )
      }))

      datatable(
        backtest,
        options = list(pageLength = 10, dom = "t", ordering = FALSE),
        rownames = FALSE
      ) %>%
        formatStyle("Detected",
          backgroundColor = styleEqual(c("Yes", "No"), c("#dff0d8", "#f2dede"))
        )
    })

    # ---- Business Cycle Timeline (A1.3) ----
    output$cycle_timeline <- renderEcharts4r({
      # Build expansion/contraction periods
      n <- nrow(recession_periods)
      periods <- data.table(
        name = character(0), start = as.Date(character(0)),
        end = as.Date(character(0)), type = character(0)
      )

      # Add recessions
      for (i in 1:n) {
        periods <- rbind(periods, data.table(
          name = recession_periods$name[i],
          start = recession_periods$start[i],
          end = recession_periods$end[i],
          type = "Contraction"
        ))
      }

      # Add expansions between recessions
      for (i in 1:(n - 1)) {
        periods <- rbind(periods, data.table(
          name = paste0("Expansion (", format(recession_periods$end[i], "%Y"), "-",
                        format(recession_periods$start[i + 1], "%Y"), ")"),
          start = recession_periods$end[i],
          end = recession_periods$start[i + 1],
          type = "Expansion"
        ))
      }

      # Current expansion
      periods <- rbind(periods, data.table(
        name = paste0("Current Expansion (", format(recession_periods$end[n], "%Y"), "-present)"),
        start = recession_periods$end[n],
        end = Sys.Date(),
        type = "Expansion"
      ))

      # Duration in months
      periods[, duration := round(as.numeric(difftime(end, start, units = "days")) / 30.44)]

      setorder(periods, start)

      # Use horizontal bar chart
      periods[, color := ifelse(type == "Contraction", "#dd4b39", "#00a65a")]

      periods %>%
        e_charts(name) %>%
        e_bar(duration, itemStyle = list(
          color = htmlwidgets::JS("
            function(params) {
              var colors = {Contraction: '#dd4b39', Expansion: '#00a65a'};
              return colors[params.data.type] || '#3c8dbc';
            }
          ")
        )) %>%
        e_flip_coords() %>%
        e_tooltip(
          formatter = htmlwidgets::JS("
            function(params) {
              return params.name + '<br>Duration: ' + params.value[0] + ' months';
            }
          ")
        ) %>%
        e_x_axis(name = "Duration (months)") %>%
        e_legend(show = FALSE) %>%
        e_grid(left = "35%")
    })

    # ---- Cycle Statistics Table ----
    output$cycle_stats <- renderDT({
      n <- nrow(recession_periods)
      stats <- rbindlist(lapply(1:n, function(i) {
        duration <- round(as.numeric(difftime(
          recession_periods$end[i], recession_periods$start[i], units = "days"
        )) / 30.44)

        data.table(
          Cycle = recession_periods$name[i],
          Type = "Contraction",
          Start = recession_periods$start[i],
          End = recession_periods$end[i],
          `Duration (months)` = duration
        )
      }))

      # Add expansions
      for (i in 1:(n - 1)) {
        duration <- round(as.numeric(difftime(
          recession_periods$start[i + 1], recession_periods$end[i], units = "days"
        )) / 30.44)

        stats <- rbind(stats, data.table(
          Cycle = paste0("Expansion (", format(recession_periods$end[i], "%Y"), "-",
                         format(recession_periods$start[i + 1], "%Y"), ")"),
          Type = "Expansion",
          Start = recession_periods$end[i],
          End = recession_periods$start[i + 1],
          `Duration (months)` = duration
        ))
      }

      # Current
      current_duration <- round(as.numeric(difftime(Sys.Date(), recession_periods$end[n], units = "days")) / 30.44)
      stats <- rbind(stats, data.table(
        Cycle = "Current Expansion",
        Type = "Expansion",
        Start = recession_periods$end[n],
        End = Sys.Date(),
        `Duration (months)` = current_duration
      ))

      setorder(stats, Start)

      datatable(
        stats,
        options = list(pageLength = 10, dom = "t", ordering = FALSE),
        rownames = FALSE
      ) %>%
        formatStyle("Type",
          backgroundColor = styleEqual(c("Contraction", "Expansion"), c("#f2dede", "#dff0d8"))
        )
    })
  })
}
