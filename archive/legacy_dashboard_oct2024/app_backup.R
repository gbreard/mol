# Dashboard de Ofertas Laborales
# Análisis de ofertas scrapeadas

# Limpiar entorno
rm(list = ls())
gc()

# Cargar librerías
library(shiny)
library(shinydashboard)
library(readxl)
library(dplyr)
library(ggplot2)
library(plotly)
library(lubridate)
library(DT)

# Configurar encoding para caracteres especiales
Sys.setlocale("LC_ALL", "es_ES.UTF-8")

# UI del Dashboard
ui <- dashboardPage(
  dashboardHeader(title = "Tablero de Ofertas Laborales"),

  dashboardSidebar(
    sidebarMenu(
      menuItem("Resumen General", tabName = "resumen", icon = icon("dashboard")),
      menuItem("Empresas", tabName = "empresas", icon = icon("building")),
      menuItem("Temporalidad", tabName = "temporalidad", icon = icon("calendar")),
      menuItem("Ubicación", tabName = "ubicacion", icon = icon("map")),
      menuItem("Modalidad", tabName = "modalidad", icon = icon("laptop-house")),
      menuItem("Ocupaciones", tabName = "ocupaciones", icon = icon("briefcase")),
      menuItem("Datos Crudos", tabName = "datos", icon = icon("table"))
    ),

    # Filtros globales
    hr(),
    h4("Filtros Globales", style = "padding-left: 15px;"),
    p("Los filtros se aplican automáticamente", style = "padding-left: 15px; font-size: 12px; color: #777;"),
    dateRangeInput("fecha_rango",
                   "Rango de fechas:",
                   start = Sys.Date() - 30,
                   end = Sys.Date(),
                   format = "yyyy-mm-dd"),
    selectInput("filtro_provincia",
                "Provincia:",
                choices = c("Todas" = "todas"),
                selected = "todas"),
    selectInput("filtro_modalidad",
                "Modalidad:",
                choices = c("Todas" = "todas"),
                selected = "todas")
  ),

  dashboardBody(
    tags$head(
      tags$style(HTML("
        .box { margin-bottom: 15px; }
        .info-box { min-height: 100px; }
        .small-box { border-radius: 5px; }
      "))
    ),

    tabItems(
      # Pestaña de Resumen General
      tabItem(tabName = "resumen",
        fluidRow(
          valueBoxOutput("total_vacantes", width = 3),
          valueBoxOutput("total_empresas", width = 3),
          valueBoxOutput("total_provincias", width = 3),
          valueBoxOutput("total_ocupaciones", width = 3)
        ),

        fluidRow(
          box(
            title = "Distribución de Vacantes por Fecha",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("fecha_plot"),
            width = 6
          ),
          box(
            title = "Top 10 Empresas con Más Vacantes",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("empresas_plot"),
            width = 6
          )
        ),

        fluidRow(
          box(
            title = "Distribución por Provincia",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("provincia_plot"),
            width = 6
          ),
          box(
            title = "Distribución por Modalidad",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("modalidad_plot"),
            width = 6
          )
        )
      ),

      # Pestaña de Empresas
      tabItem(tabName = "empresas",
        fluidRow(
          box(
            title = "Top 20 Empresas por Cantidad de Vacantes",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("top_empresas_plot"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "Tabla de Empresas",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("empresas_table"),
            width = 12
          )
        )
      ),

      # Pestaña de Temporalidad
      tabItem(tabName = "temporalidad",
        fluidRow(
          box(
            title = "Vacantes por Fecha",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("vacantes_fecha_plot"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "Vacantes por Fecha (Detalle)",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("fecha_table"),
            width = 12
          )
        )
      ),

      # Pestaña de Ubicación
      tabItem(tabName = "ubicacion",
        fluidRow(
          box(
            title = "Vacantes por Provincia",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("vacantes_provincia_plot"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "Tabla de Provincias",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("provincia_table"),
            width = 12
          )
        )
      ),

      # Pestaña de Modalidad
      tabItem(tabName = "modalidad",
        fluidRow(
          box(
            title = "Distribución por Modalidad de Trabajo",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("modalidad_detalle_plot"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "Tabla de Modalidades",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("modalidad_table"),
            width = 12
          )
        )
      ),

      # Pestaña de Ocupaciones
      tabItem(tabName = "ocupaciones",
        fluidRow(
          box(
            title = "Top 20 Ocupaciones más Solicitadas",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("ocupaciones_plot"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "Tabla de Ocupaciones",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("ocupaciones_table"),
            width = 12
          )
        )
      ),

      # Nueva pestaña de Datos Crudos
      tabItem(tabName = "datos",
        fluidRow(
          box(
            title = "Base de Datos Completa",
            status = "primary",
            solidHeader = TRUE,
            downloadButton("descargar_datos", "Descargar Excel"),
            hr(),
            DTOutput("datos_crudos_table"),
            width = 12
          )
        )
      )
    )
  )
)

# Server logic
server <- function(input, output, session) {

  # Cargar datos del Excel con manejo de errores
  datos_base <- reactive({
    req(file.exists("ofertas_consolidadas.xlsx"))

    tryCatch({
      # Leer la hoja BASE que tiene todos los datos
      df <- read_excel("ofertas_consolidadas.xlsx", sheet = "BASE")

      # Procesar columna de fecha
      if ("Periodo" %in% names(df)) {
        df <- df %>%
          mutate(Fecha = as.Date(Periodo, format = "%Y-%m-%d"))
      } else {
        df$Fecha <- Sys.Date()
      }

      # Verificar que hay datos
      validate(
        need(nrow(df) > 0, "No hay datos en el archivo Excel")
      )

      return(df)

    }, error = function(e) {
      showNotification(
        paste("Error al cargar datos:", e$message),
        type = "error",
        duration = 10
      )
      return(data.frame())
    })
  })

  # Datos filtrados según selección del usuario
  datos_filtrados <- reactive({
    df <- datos_base()

    if (nrow(df) == 0) return(df)

    # Aplicar filtro de fecha
    if (!is.null(input$fecha_rango)) {
      df <- df %>%
        filter(Fecha >= input$fecha_rango[1] & Fecha <= input$fecha_rango[2])
    }

    # Aplicar filtro de provincia
    if (!is.null(input$filtro_provincia) && input$filtro_provincia != "todas" && "ubicacion.provincia" %in% names(df)) {
      df <- df %>%
        filter(ubicacion.provincia == input$filtro_provincia)
    }

    # Aplicar filtro de modalidad
    if (!is.null(input$filtro_modalidad) && input$filtro_modalidad != "todas" && "modalidad.modalidad_trabajo" %in% names(df)) {
      df <- df %>%
        filter(modalidad.modalidad_trabajo == input$filtro_modalidad)
    }

    return(df)
  })

  # Actualizar opciones de filtros basados en los datos
  observe({
    df <- datos_base()

    if (nrow(df) > 0) {
      # Actualizar provincias
      if ("ubicacion.provincia" %in% names(df)) {
        provincias <- df %>%
          filter(!is.na(ubicacion.provincia)) %>%
          pull(ubicacion.provincia) %>%
          unique() %>%
          sort()

        updateSelectInput(session, "filtro_provincia",
                          choices = c("Todas" = "todas", provincias))
      }

      # Actualizar modalidades
      if ("modalidad.modalidad_trabajo" %in% names(df)) {
        modalidades <- df %>%
          filter(!is.na(modalidad.modalidad_trabajo)) %>%
          pull(modalidad.modalidad_trabajo) %>%
          unique() %>%
          sort()

        updateSelectInput(session, "filtro_modalidad",
                          choices = c("Todas" = "todas", modalidades))
      }
    }
  })

  # Agregar datos reactivos para cada análisis (usando datos filtrados)
  hoja1_data <- reactive({
    df <- datos_filtrados()
    if (nrow(df) == 0) return(data.frame(Empresa = character(), Vacantes = numeric()))

    df %>%
      count(`_metadata.source`, name = "Vacantes") %>%
      rename(Empresa = `_metadata.source`) %>%
      arrange(desc(Vacantes))
  })

  c1_data <- reactive({
    df <- datos_filtrados()
    if (nrow(df) == 0) return(data.frame(Fecha = Date(), Vacantes = numeric()))

    df %>%
      filter(!is.na(Fecha)) %>%
      count(Fecha, name = "Vacantes") %>%
      arrange(Fecha)
  })

  c2_data <- reactive({
    df <- datos_filtrados()
    if (nrow(df) == 0) return(data.frame(Provincia = character(), Vacantes = numeric()))

    col_provincia <- "ubicacion.provincia"

    if (col_provincia %in% names(df)) {
      df %>%
        filter(!is.na(!!sym(col_provincia))) %>%
        count(!!sym(col_provincia), name = "Vacantes") %>%
        rename(Provincia = !!sym(col_provincia)) %>%
        arrange(desc(Vacantes))
    } else {
      data.frame(Provincia = character(), Vacantes = numeric())
    }
  })

  c3_data <- reactive({
    df <- datos_filtrados()
    if (nrow(df) == 0) return(data.frame(Modalidad = character(), Vacantes = numeric()))

    col_modalidad <- "modalidad.modalidad_trabajo"

    if (col_modalidad %in% names(df)) {
      df %>%
        mutate(Modalidad = ifelse(is.na(!!sym(col_modalidad)), "(en blanco)", !!sym(col_modalidad))) %>%
        count(Modalidad, name = "Vacantes") %>%
        arrange(desc(Vacantes))
    } else {
      data.frame(Modalidad = character(), Vacantes = numeric())
    }
  })

  c4_data <- reactive({
    df <- datos_filtrados()
    if (nrow(df) == 0) return(data.frame(Ocupacion = character(), Vacantes = numeric()))

    col_ocupacion <- "informacion_basica.titulo_normalizado"

    if (col_ocupacion %in% names(df)) {
      df %>%
        filter(!is.na(!!sym(col_ocupacion))) %>%
        count(!!sym(col_ocupacion), name = "Vacantes") %>%
        rename(Ocupacion = !!sym(col_ocupacion)) %>%
        arrange(desc(Vacantes))
    } else {
      data.frame(Ocupacion = character(), Vacantes = numeric())
    }
  })

  # Value Boxes para resumen (actualizados con filtros)
  output$total_vacantes <- renderValueBox({
    valueBox(
      nrow(datos_filtrados()),
      "Total Vacantes",
      icon = icon("users"),
      color = "blue"
    )
  })

  output$total_empresas <- renderValueBox({
    n_empresas <- hoja1_data() %>% nrow()
    valueBox(
      n_empresas,
      "Empresas",
      icon = icon("building"),
      color = "green"
    )
  })

  output$total_provincias <- renderValueBox({
    n_provincias <- c2_data() %>% nrow()
    valueBox(
      n_provincias,
      "Provincias",
      icon = icon("map"),
      color = "yellow"
    )
  })

  output$total_ocupaciones <- renderValueBox({
    n_ocupaciones <- c4_data() %>% nrow()
    valueBox(
      n_ocupaciones,
      "Ocupaciones",
      icon = icon("briefcase"),
      color = "red"
    )
  })

  # Gráficos para Resumen General
  output$fecha_plot <- renderPlotly({
    data <- c1_data()
    validate(need(nrow(data) > 0, "No hay datos de fechas disponibles"))

    p <- ggplot(data, aes(x = Fecha, y = Vacantes)) +
      geom_line(color = "#1f77b4", size = 1) +
      geom_point(color = "#1f77b4", size = 2) +
      labs(title = "Evolución de Vacantes por Fecha",
           x = "Fecha",
           y = "Número de Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$empresas_plot <- renderPlotly({
    data <- hoja1_data() %>% head(10)
    validate(need(nrow(data) > 0, "No hay datos de empresas disponibles"))

    p <- ggplot(data, aes(x = reorder(Empresa, Vacantes), y = Vacantes)) +
      geom_bar(stat = "identity", fill = "#2E86AB") +
      coord_flip() +
      labs(title = "Top 10 Empresas", x = "Empresa", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$provincia_plot <- renderPlotly({
    data <- c2_data() %>% head(10)
    validate(need(nrow(data) > 0, "No hay datos de provincias disponibles"))

    p <- ggplot(data, aes(x = reorder(Provincia, Vacantes), y = Vacantes)) +
      geom_bar(stat = "identity", fill = "#A23B72") +
      coord_flip() +
      labs(title = "Top 10 Provincias", x = "Provincia", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$modalidad_plot <- renderPlotly({
    data <- c3_data()
    validate(need(nrow(data) > 0, "No hay datos de modalidad disponibles"))

    p <- ggplot(data, aes(x = "", y = Vacantes, fill = Modalidad)) +
      geom_bar(stat = "identity", width = 1) +
      coord_polar("y", start = 0) +
      labs(title = "Distribución por Modalidad", fill = "Modalidad") +
      theme_void()

    ggplotly(p)
  })

  # Gráficos para Empresas
  output$top_empresas_plot <- renderPlotly({
    data <- hoja1_data() %>% head(20)
    validate(need(nrow(data) > 0, "No hay datos disponibles"))

    p <- ggplot(data, aes(x = reorder(Empresa, Vacantes), y = Vacantes)) +
      geom_bar(stat = "identity", fill = "#2E86AB") +
      coord_flip() +
      labs(title = "Top 20 Empresas", x = "Empresa", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$empresas_table <- renderDT({
    datatable(
      hoja1_data(),
      options = list(
        pageLength = 25,
        language = list(url = '//cdn.datatables.net/plug-ins/1.10.11/i18n/Spanish.json')
      ),
      filter = 'top'
    )
  })

  # Gráficos para Temporalidad
  output$vacantes_fecha_plot <- renderPlotly({
    data <- c1_data()
    validate(need(nrow(data) > 0, "No hay datos disponibles"))

    p <- ggplot(data, aes(x = Fecha, y = Vacantes)) +
      geom_area(fill = "#F18F01", alpha = 0.5) +
      geom_line(color = "#F18F01", size = 1) +
      geom_point(color = "#F18F01", size = 2) +
      labs(title = "Vacantes por Fecha", x = "Fecha", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$fecha_table <- renderDT({
    datatable(
      c1_data(),
      options = list(
        pageLength = 25,
        order = list(list(0, 'desc')),
        language = list(url = '//cdn.datatables.net/plug-ins/1.10.11/i18n/Spanish.json')
      ),
      filter = 'top'
    )
  })

  # Gráficos para Ubicación
  output$vacantes_provincia_plot <- renderPlotly({
    data <- c2_data() %>% head(20)
    validate(need(nrow(data) > 0, "No hay datos disponibles"))

    p <- ggplot(data, aes(x = reorder(Provincia, Vacantes), y = Vacantes)) +
      geom_bar(stat = "identity", fill = "#A23B72") +
      coord_flip() +
      labs(title = "Top 20 Provincias", x = "Provincia", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$provincia_table <- renderDT({
    datatable(
      c2_data(),
      options = list(
        pageLength = 25,
        language = list(url = '//cdn.datatables.net/plug-ins/1.10.11/i18n/Spanish.json')
      ),
      filter = 'top'
    )
  })

  # Gráficos para Modalidad
  output$modalidad_detalle_plot <- renderPlotly({
    data <- c3_data()
    validate(need(nrow(data) > 0, "No hay datos disponibles"))

    p <- ggplot(data, aes(x = reorder(Modalidad, Vacantes), y = Vacantes)) +
      geom_bar(stat = "identity", fill = "#C73E1D") +
      coord_flip() +
      labs(title = "Vacantes por Modalidad", x = "Modalidad", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$modalidad_table <- renderDT({
    datatable(
      c3_data(),
      options = list(
        pageLength = 25,
        language = list(url = '//cdn.datatables.net/plug-ins/1.10.11/i18n/Spanish.json')
      ),
      filter = 'top'
    )
  })

  # Gráficos para Ocupaciones
  output$ocupaciones_plot <- renderPlotly({
    data <- c4_data() %>% head(20)
    validate(need(nrow(data) > 0, "No hay datos disponibles"))

    p <- ggplot(data, aes(x = reorder(Ocupacion, Vacantes), y = Vacantes)) +
      geom_bar(stat = "identity", fill = "#3F784C") +
      coord_flip() +
      labs(title = "Top 20 Ocupaciones", x = "Ocupación", y = "Vacantes") +
      theme_minimal()

    ggplotly(p)
  })

  output$ocupaciones_table <- renderDT({
    datatable(
      c4_data(),
      options = list(
        pageLength = 25,
        language = list(url = '//cdn.datatables.net/plug-ins/1.10.11/i18n/Spanish.json')
      ),
      filter = 'top'
    )
  })

  # Nueva tabla de datos crudos (con filtros aplicados)
  output$datos_crudos_table <- renderDT({
    datatable(
      datos_filtrados(),
      options = list(
        pageLength = 25,
        scrollX = TRUE,
        language = list(url = '//cdn.datatables.net/plug-ins/1.10.11/i18n/Spanish.json')
      ),
      filter = 'top'
    )
  })

  # Descarga de datos (con filtros aplicados)
  output$descargar_datos <- downloadHandler(
    filename = function() {
      paste("ofertas_laborales_", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(datos_filtrados(), file, row.names = FALSE, fileEncoding = "UTF-8")
    }
  )
}

# Run the application
shinyApp(ui, server)
