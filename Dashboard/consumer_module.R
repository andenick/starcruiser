# ============================================================================
# CONSUMER & SPENDING MODULE - StarCruiser Dashboard v7.0
# ============================================================================
# Retail sales, savings rate, consumer sentiment, credit, durable goods
# Data: fred_income_spending, fred_housing (UMCSENT)
# ============================================================================

consumer_ui <- function(id) {
  ns <- NS(id)
  tagList(
    fluidRow(
      valueBoxOutput(ns("vbox_retail"), width = 3),
      valueBoxOutput(ns("vbox_savings"), width = 3),
      valueBoxOutput(ns("vbox_sentiment"), width = 3),
      valueBoxOutput(ns("vbox_credit"), width = 3)
    ),
    fluidRow(
      box(title = "Retail Sales (Ex-Auto)",
          echarts4rOutput(ns("retail_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "primary"),
      box(title = "Personal Savings Rate",
          echarts4rOutput(ns("savings_chart"), height = "350px"),
          helpText("Spikes during recessions (precautionary saving), falls during expansions"),
          width = 6, solidHeader = TRUE, status = "info")
    ),
    fluidRow(
      box(title = "Consumer Sentiment (U. Michigan)",
          echarts4rOutput(ns("sentiment_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "warning"),
      box(title = "Consumer Credit Outstanding",
          echarts4rOutput(ns("credit_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "success")
    ),
    fluidRow(
      box(title = "Durable Goods New Orders",
          echarts4rOutput(ns("durables_chart"), height = "350px"),
          helpText("Leading indicator of business investment intentions"),
          width = 6, solidHeader = TRUE, status = "primary"),
      box(title = "Personal Income (Real)",
          echarts4rOutput(ns("income_chart"), height = "350px"),
          width = 6, solidHeader = TRUE, status = "info")
    )
  )
}

consumer_server <- function(id, spending_data, housing_data, date_range) {
  moduleServer(id, function(input, output, session) {

    spend_filtered <- reactive({
      req(spending_data); dr <- date_range()
      spending_data[date >= dr[1] & date <= dr[2]]
    })

    housing_filtered <- reactive({
      req(housing_data); dr <- date_range()
      housing_data[date >= dr[1] & date <= dr[2]]
    })

    output$vbox_retail <- renderValueBox({
      if (is.null(spending_data)) return(valueBox("N/A", "Retail Sales", icon = icon("shopping-cart"), color = "gray"))
      latest <- spending_data[series_id == "RSXFS"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Retail Sales", icon = icon("shopping-cart"), color = "gray"))
      valueBox(paste0("$", round(latest$value / 1000, 1), "B"),
               paste("Retail Sales ex-Auto -", latest$date),
               icon = icon("shopping-cart"), color = "blue")
    })

    output$vbox_savings <- renderValueBox({
      if (is.null(spending_data)) return(valueBox("N/A", "Savings Rate", icon = icon("piggy-bank"), color = "gray"))
      latest <- spending_data[series_id == "PSAVERT"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Savings Rate", icon = icon("piggy-bank"), color = "gray"))
      color <- if (latest$value > 10) "green" else if (latest$value > 5) "yellow" else "red"
      valueBox(paste0(round(latest$value, 1), "%"), paste("Savings Rate -", latest$date),
               icon = icon("piggy-bank"), color = color)
    })

    output$vbox_sentiment <- renderValueBox({
      if (is.null(housing_data)) return(valueBox("N/A", "Consumer Sentiment", icon = icon("smile"), color = "gray"))
      latest <- housing_data[series_id == "UMCSENT"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Sentiment", icon = icon("smile"), color = "gray"))
      color <- if (latest$value > 90) "green" else if (latest$value > 70) "yellow" else "red"
      valueBox(round(latest$value, 1), paste("Consumer Sentiment -", latest$date),
               icon = icon("smile"), color = color)
    })

    output$vbox_credit <- renderValueBox({
      if (is.null(spending_data)) return(valueBox("N/A", "Consumer Credit", icon = icon("credit-card"), color = "gray"))
      latest <- spending_data[series_id == "TOTALSL"][order(-date)][1]
      if (nrow(latest) == 0) return(valueBox("N/A", "Consumer Credit", icon = icon("credit-card"), color = "gray"))
      valueBox(paste0("$", round(latest$value / 1000, 1), "T"),
               paste("Consumer Credit -", latest$date),
               icon = icon("credit-card"), color = "purple")
    })

    output$retail_chart <- renderEcharts4r({
      dt <- spend_filtered()[series_id == "RSXFS"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#3c8dbc", sampling = "lttb", name = "Retail Sales ex-Auto") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Millions $")
      add_recession_bands(chart, date_range())
    })

    output$savings_chart <- renderEcharts4r({
      dt <- spend_filtered()[series_id == "PSAVERT"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_area(value, symbol = "none", color = "#00a65a", sampling = "lttb", name = "Savings Rate") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Percent")
      add_recession_bands(chart, date_range())
    })

    output$sentiment_chart <- renderEcharts4r({
      dt <- housing_filtered()[series_id == "UMCSENT"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#f39c12", sampling = "lttb", name = "Consumer Sentiment") %>%
        e_mark_line(data = list(yAxis = 80), lineStyle = list(color = "#aaa", type = "dashed")) %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Index")
      add_recession_bands(chart, date_range())
    })

    output$credit_chart <- renderEcharts4r({
      dt <- spend_filtered()[series_id == "TOTALSL"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#9b59b6", sampling = "lttb", name = "Consumer Credit") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Billions $")
      add_recession_bands(chart, date_range())
    })

    output$durables_chart <- renderEcharts4r({
      dt <- spend_filtered()[series_id == "DGORDER"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#3c8dbc", sampling = "lttb", name = "Durable Goods Orders") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Millions $")
      add_recession_bands(chart, date_range())
    })

    output$income_chart <- renderEcharts4r({
      dt <- spend_filtered()[series_id == "DSPIC96"]
      if (is.null(dt) || nrow(dt) == 0) return(NULL)
      chart <- dt %>% e_charts(date) %>%
        e_line(value, symbol = "none", color = "#00a65a", sampling = "lttb", name = "Real Disposable Income") %>%
        e_tooltip(trigger = "axis") %>% e_datazoom(type = "slider") %>%
        e_y_axis(name = "Billions (2012 $)")
      add_recession_bands(chart, date_range())
    })
  })
}
