# Dashboard de Ofertas Laborales
# Análisis de ofertas scrapeadas

# Limpiar entorno
rm(list = ls())
gc()

# Cargar librerías básicas
library(shiny)
library(shinydashboard)
library(readxl)
library(dplyr)
library(ggplot2)
library(plotly)
library(lubridate)
library(DT)

# Cargar librerías avanzadas
library(leaflet)     # Mapas interactivos
library(tidytext)    # Análisis de texto
library(wordcloud2)  # Word clouds
library(tm)          # Text mining
library(openxlsx)    # Excel avanzado
library(zoo)         # Series temporales
library(scales)      # Escalas y formateo

# Configurar encoding para caracteres especiales
Sys.setlocale("LC_ALL", "es_ES.UTF-8")

# Datos de geocodificación de provincias argentinas
provincias_geo <- data.frame(
  provincia = c("Buenos Aires", "Buenos Aires-GBA", "CABA", "Córdoba", "Santa Fe",
                "Mendoza", "Tucumán", "Entre Ríos", "Salta", "Misiones",
                "Neuquén", "Chaco", "San Luis"),
  lat = c(-36.68, -34.60, -34.60, -31.42, -31.63,
          -32.89, -26.81, -31.73, -24.78, -27.36,
          -38.95, -27.45, -33.30),
  lng = c(-60.56, -58.38, -58.38, -64.19, -60.70,
          -68.85, -65.22, -60.50, -65.42, -55.90,
          -68.06, -59.02, -66.34)
)

# UI del Dashboard
ui <- dashboardPage(
  dashboardHeader(title = "Tablero de Ofertas Laborales"),

  dashboardSidebar(
    width = 280,
    sidebarMenu(
      menuItem("📊 Resumen General", tabName = "resumen", icon = icon("dashboard")),
      menuItem("🔍 Análisis por Fuente", tabName = "fuentes", icon = icon("database")),
      menuItem("📈 Tendencias", tabName = "tendencias", icon = icon("chart-line")),
      menuItem("🗺️ Mapa Geográfico", tabName = "mapa", icon = icon("map-marked-alt")),
      menuItem("☁️ Análisis de Texto", tabName = "texto", icon = icon("cloud")),
      menuItem("🏢 Empresas", tabName = "empresas", icon = icon("building")),
      menuItem("📅 Temporalidad", tabName = "temporalidad", icon = icon("calendar")),
      menuItem("📍 Ubicación", tabName = "ubicacion", icon = icon("map")),
      menuItem("💼 Modalidad", tabName = "modalidad", icon = icon("laptop-house")),
      menuItem("👔 Ocupaciones", tabName = "ocupaciones", icon = icon("briefcase")),
      menuItem("✅ Calidad de Datos", tabName = "calidad", icon = icon("check-circle")),
      menuItem("📄 Datos Crudos", tabName = "datos", icon = icon("table")),
      menuItem("⚙️ Admin", tabName = "admin", icon = icon("cog"))
    ),

    # Filtros globales mejorados
    hr(),
    h4("⚙️ Filtros", style = "padding-left: 15px; color: white;"),

    dateRangeInput("fecha_rango",
                   "📅 Fechas:",
                   start = Sys.Date() - 90,
                   end = Sys.Date(),
                   format = "yyyy-mm-dd"),

    selectInput("filtro_fuente",
                "🔍 Fuente:",
                choices = c("Todas" = "todas"),
                selected = "todas"),

    selectInput("filtro_provincia",
                "📍 Provincia:",
                choices = c("Todas" = "todas"),
                selected = "todas"),

    selectInput("filtro_ciudad",
                "🏙️ Ciudad:",
                choices = c("Todas" = "todas"),
                selected = "todas"),

    selectInput("filtro_modalidad",
                "💼 Modalidad:",
                choices = c("Todas" = "todas"),
                selected = "todas"),

    selectInput("filtro_tipo_trabajo",
                "⏰ Tipo:",
                choices = c("Todos" = "todos"),
                selected = "todos"),

    textInput("buscar_texto",
              "🔎 Buscar:",
              placeholder = "título de oferta..."),

    tags$small("Filtros automáticos",
               style = "padding-left: 15px; color: #aaa;")
  ),

  dashboardBody(
    tags$head(
      tags$style(HTML("
        .box { margin-bottom: 15px; }
        .info-box { min-height: 100px; }
        .small-box { border-radius: 5px; }

        /* Estilos para botón flotante de feedback */
        .feedback-btn-container {
          position: fixed;
          bottom: 30px;
          right: 30px;
          z-index: 9999;
        }

        .feedback-btn {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 50px;
          padding: 15px 30px;
          font-size: 16px;
          font-weight: bold;
          box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .feedback-btn:hover {
          transform: translateY(-3px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
          background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }

        .feedback-btn:active {
          transform: translateY(-1px);
        }

        .feedback-pulse {
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4); }
          50% { box-shadow: 0 6px 30px rgba(102, 126, 234, 0.7); }
          100% { box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4); }
        }
      "))
    ),

    # Botón flotante de feedback (visible en todas las pestañas)
    tags$div(
      class = "feedback-btn-container",
      actionButton(
        "btn_feedback",
        HTML("<i class='fa fa-comment-dots' style='font-size: 18px;'></i><span style='margin-left: 8px;'>Enviar Feedback</span>"),
        class = "feedback-btn feedback-pulse"
      )
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

      # Pestaña de Análisis por Fuente
      tabItem(tabName = "fuentes",
        h2("🔍 Análisis por Fuente de Scraping"),
        fluidRow(
          valueBoxOutput("fuente_total", width = 3),
          valueBoxOutput("fuente_principal", width = 3),
          valueBoxOutput("fuente_diversidad", width = 3),
          valueBoxOutput("fuente_completitud", width = 3)
        ),
        fluidRow(
          box(
            title = "🥧 Distribución de Ofertas por Fuente",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("fuente_pie_chart"),
            width = 6
          ),
          box(
            title = "📊 Comparativa de Fuentes",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("fuente_barras"),
            width = 6
          )
        ),
        fluidRow(
          box(
            title = "📈 Evolución Temporal por Fuente",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("fuente_temporal"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "📊 Calidad de Datos por Fuente",
            status = "warning",
            solidHeader = TRUE,
            DTOutput("fuente_calidad_tabla"),
            width = 12
          )
        )
      ),

      # Pestaña de Tendencias Temporales
      tabItem(tabName = "tendencias",
        h2("📈 Análisis de Tendencias Temporales"),
        fluidRow(
          valueBoxOutput("tend_total_periodo", width = 3),
          valueBoxOutput("tend_promedio_dia", width = 3),
          valueBoxOutput("tend_dia_mas_activo", width = 3),
          valueBoxOutput("tend_crecimiento", width = 3)
        ),
        fluidRow(
          box(
            title = "📈 Serie Temporal con Tendencia y Media Móvil",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("tendencia_serie"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "📊 Crecimiento Mensual",
            status = "success",
            solidHeader = TRUE,
            DTOutput("tendencia_mensual_tabla"),
            width = 12
          )
        )
      ),

      # Pestaña de Mapa Geográfico
      tabItem(tabName = "mapa",
        h2("🗺️ Mapa Interactivo de Ofertas Laborales"),
        fluidRow(
          box(
            title = "🗺️ Distribución Geográfica en Argentina",
            status = "primary",
            solidHeader = TRUE,
            leafletOutput("mapa_argentina", height = 600),
            width = 12,
            footer = tags$div(
              tags$p("💡 Haz clic en los círculos para ver detalles"),
              tags$p("📍 El tamaño representa la cantidad de ofertas"),
              style = "font-size: 12px; color: #666;"
            )
          )
        ),
        fluidRow(
          box(
            title = "🏙️ Top 15 Ciudades",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("mapa_ciudades_plot"),
            width = 12
          )
        )
      ),

      # Pestaña de Análisis de Texto
      tabItem(tabName = "texto",
        h2("☁️ Análisis de Contenido Textual"),
        fluidRow(
          valueBoxOutput("texto_con_titulo", width = 4),
          valueBoxOutput("texto_palabras_unicas", width = 4),
          valueBoxOutput("texto_promedio_palabras", width = 4)
        ),
        fluidRow(
          box(
            title = "☁️ Nube de Palabras - Títulos de Ofertas",
            status = "primary",
            solidHeader = TRUE,
            wordcloud2Output("wordcloud_titulos", height = "400px"),
            width = 12,
            footer = "Las palabras más grandes son las más frecuentes"
          )
        ),
        fluidRow(
          box(
            title = "📊 Top 20 Términos Más Frecuentes",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("texto_top_terminos"),
            width = 6
          ),
          box(
            title = "📋 Tabla de Frecuencia",
            status = "info",
            solidHeader = TRUE,
            DTOutput("texto_terminos_tabla"),
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

      # Pestaña de Calidad de Datos
      tabItem(tabName = "calidad",
        h2("✅ Dashboard de Calidad de Datos"),
        fluidRow(
          valueBoxOutput("cal_completitud_general", width = 3),
          valueBoxOutput("cal_registros_completos", width = 3),
          valueBoxOutput("cal_campos_criticos", width = 3),
          valueBoxOutput("cal_score_calidad", width = 3)
        ),
        fluidRow(
          box(
            title = "📊 Completitud por Campo Principal",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("calidad_completitud_plot"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "📋 Análisis Detallado de Completitud",
            status = "info",
            solidHeader = TRUE,
            DTOutput("calidad_tabla_detalle"),
            width = 12
          )
        ),
        fluidRow(
          box(
            title = "⚠️ Inconsistencias Detectadas",
            status = "warning",
            solidHeader = TRUE,
            htmlOutput("calidad_inconsistencias"),
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
      ),

      # Pestaña de Administración
      tabItem(tabName = "admin",
        fluidRow(
          box(
            title = "⚙️ Panel de Administración",
            status = "warning",
            solidHeader = TRUE,
            width = 12,

            h4(icon("comment-dots"), " Gestión de Feedback"),
            p("Desde aquí puedes descargar todos los feedbacks recibidos de los usuarios."),
            hr(),

            fluidRow(
              column(4,
                valueBoxOutput("total_feedbacks", width = 12)
              ),
              column(4,
                valueBoxOutput("feedback_reciente", width = 12)
              ),
              column(4,
                downloadButton("descargar_feedback",
                               "📥 Descargar Feedback (CSV)",
                               class = "btn-success btn-lg",
                               style = "margin-top: 15px;")
              )
            ),

            hr(),

            h4(icon("table"), " Vista Previa del Feedback"),
            p("Últimos 10 feedbacks recibidos:"),
            DTOutput("feedback_preview_table")
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

    # Aplicar filtro de fuente
    if (!is.null(input$filtro_fuente) && input$filtro_fuente != "todas") {
      df <- df %>%
        filter(`_metadata.source` == input$filtro_fuente)
    }

    # Aplicar filtro de ciudad
    if (!is.null(input$filtro_ciudad) && input$filtro_ciudad != "todas" && "ubicacion.ciudad" %in% names(df)) {
      df <- df %>%
        filter(ubicacion.ciudad == input$filtro_ciudad)
    }

    # Aplicar filtro de tipo de trabajo
    if (!is.null(input$filtro_tipo_trabajo) && input$filtro_tipo_trabajo != "todos" && "modalidad.tipo_trabajo" %in% names(df)) {
      df <- df %>%
        filter(modalidad.tipo_trabajo == input$filtro_tipo_trabajo)
    }

    # Búsqueda por texto en título
    if (!is.null(input$buscar_texto) && input$buscar_texto != "") {
      df <- df %>%
        filter(grepl(input$buscar_texto, informacion_basica.titulo, ignore.case = TRUE))
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

      # Actualizar fuentes
      fuentes <- df %>%
        pull(`_metadata.source`) %>%
        unique() %>%
        sort()

      updateSelectInput(session, "filtro_fuente",
                        choices = c("Todas" = "todas", fuentes))

      # Actualizar ciudades (top 20)
      if ("ubicacion.ciudad" %in% names(df)) {
        ciudades_top <- df %>%
          filter(!is.na(ubicacion.ciudad)) %>%
          count(ubicacion.ciudad, sort = TRUE) %>%
          head(20) %>%
          pull(ubicacion.ciudad)

        updateSelectInput(session, "filtro_ciudad",
                          choices = c("Todas" = "todas", ciudades_top))
      }

      # Actualizar tipos de trabajo
      if ("modalidad.tipo_trabajo" %in% names(df)) {
        tipos <- df %>%
          filter(!is.na(modalidad.tipo_trabajo)) %>%
          pull(modalidad.tipo_trabajo) %>%
          unique() %>%
          sort()

        updateSelectInput(session, "filtro_tipo_trabajo",
                          choices = c("Todos" = "todos", tipos))
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

  # ======================================================================
  # OUTPUTS PARA ANÁLISIS POR FUENTE
  # ======================================================================
  output$fuente_total <- renderValueBox({
    n_fuentes <- datos_filtrados() %>% pull(`_metadata.source`) %>% n_distinct()
    valueBox(n_fuentes, "Fuentes de Datos", icon = icon("database"), color = "blue")
  })

  output$fuente_principal <- renderValueBox({
    fuente_top <- datos_filtrados() %>%
      count(`_metadata.source`, sort = TRUE) %>%
      head(1) %>%
      pull(`_metadata.source`)
    valueBox(fuente_top, "Fuente Principal", icon = icon("trophy"), color = "green")
  })

  output$fuente_diversidad <- renderValueBox({
    diversidad <- datos_filtrados() %>%
      count(`_metadata.source`) %>%
      summarise(sd = sd(n, na.rm = TRUE)) %>%
      pull(sd) %>%
      round(1)
    valueBox(paste0("±", diversidad), "Variabilidad", icon = icon("chart-bar"), color = "yellow")
  })

  output$fuente_completitud <- renderValueBox({
    pct <- (nrow(datos_filtrados()) / nrow(datos_base())) * 100
    valueBox(paste0(round(pct, 1), "%"), "Del Total", icon = icon("percent"), color = "purple")
  })

  output$fuente_pie_chart <- renderPlotly({
    data <- datos_filtrados() %>%
      count(`_metadata.source`, name = "Cantidad") %>%
      mutate(Porcentaje = round(Cantidad / sum(Cantidad) * 100, 1))

    plot_ly(data, labels = ~`_metadata.source`, values = ~Cantidad, type = 'pie',
            textinfo = 'label+percent',
            hoverinfo = 'text',
            text = ~paste0(`_metadata.source`, ': ', Cantidad, ' ofertas')) %>%
      layout(title = "")
  })

  output$fuente_barras <- renderPlotly({
    data <- datos_filtrados() %>%
      count(`_metadata.source`, sort = TRUE)

    plot_ly(data, x = ~n, y = ~reorder(`_metadata.source`, n), type = 'bar',
            orientation = 'h', marker = list(color = '#2E86AB')) %>%
      layout(xaxis = list(title = "Cantidad de Ofertas"),
             yaxis = list(title = ""))
  })

  output$fuente_temporal <- renderPlotly({
    data <- datos_filtrados() %>%
      filter(!is.na(Fecha)) %>%
      count(Fecha, `_metadata.source`)

    plot_ly(data, x = ~Fecha, y = ~n, color = ~`_metadata.source`,
            type = 'scatter', mode = 'lines+markers') %>%
      layout(xaxis = list(title = "Fecha"),
             yaxis = list(title = "Ofertas"))
  })

  output$fuente_calidad_tabla <- renderDT({
    df <- datos_base()
    calidad <- df %>%
      group_by(Fuente = `_metadata.source`) %>%
      summarise(
        `Total Ofertas` = n(),
        `Con Provincia` = sum(!is.na(ubicacion.provincia)),
        `Con Ciudad` = sum(!is.na(ubicacion.ciudad)),
        `Con Modalidad` = sum(!is.na(modalidad.modalidad_trabajo)),
        `Score` = round((sum(!is.na(ubicacion.provincia)) + sum(!is.na(modalidad.modalidad_trabajo))) / n() * 100, 1)
      )

    datatable(calidad, options = list(pageLength = 10))
  })

  # ======================================================================
  # OUTPUTS PARA TENDENCIAS TEMPORALES
  # ======================================================================
  output$tend_total_periodo <- renderValueBox({
    total <- nrow(datos_filtrados())
    valueBox(total, "Total Período", icon = icon("calendar-check"), color = "blue")
  })

  output$tend_promedio_dia <- renderValueBox({
    promedio <- datos_filtrados() %>%
      count(Fecha) %>%
      summarise(prom = mean(n, na.rm = TRUE)) %>%
      pull(prom) %>%
      round(1)
    valueBox(promedio, "Promedio/Día", icon = icon("chart-line"), color = "green")
  })

  output$tend_dia_mas_activo <- renderValueBox({
    dia <- datos_filtrados() %>%
      count(Fecha, sort = TRUE) %>%
      head(1) %>%
      pull(Fecha) %>%
      format("%d/%m/%Y")
    valueBox(dia, "Día Más Activo", icon = icon("star"), color = "yellow")
  })

  output$tend_crecimiento <- renderValueBox({
    crec <- datos_filtrados() %>%
      arrange(Fecha) %>%
      mutate(mes = floor_date(Fecha, "month")) %>%
      count(mes) %>%
      arrange(desc(mes)) %>%
      head(2) %>%
      summarise(cambio = (n[1] - n[2]) / n[2] * 100) %>%
      pull(cambio) %>%
      round(1)
    valueBox(paste0(ifelse(crec > 0, "+", ""), crec, "%"), "vs Mes Anterior",
             icon = icon(ifelse(crec > 0, "arrow-up", "arrow-down")),
             color = ifelse(crec > 0, "green", "red"))
  })

  output$tendencia_serie <- renderPlotly({
    data <- datos_filtrados() %>%
      count(Fecha) %>%
      arrange(Fecha) %>%
      mutate(ma_7 = rollmean(n, k = 7, fill = NA, align = "right"))

    plot_ly(data) %>%
      add_trace(x = ~Fecha, y = ~n, type = 'scatter', mode = 'markers',
                name = 'Real', marker = list(color = '#1f77b4', size = 6)) %>%
      add_trace(x = ~Fecha, y = ~ma_7, type = 'scatter', mode = 'lines',
                name = 'Media Móvil 7 días', line = list(color = '#ff7f0e', width = 3)) %>%
      layout(xaxis = list(title = "Fecha"),
             yaxis = list(title = "Cantidad de Ofertas"),
             hovermode = 'x unified')
  })

  output$tendencia_mensual_tabla <- renderDT({
    tabla <- datos_filtrados() %>%
      mutate(Mes = floor_date(Fecha, "month")) %>%
      count(Mes, name = "Ofertas") %>%
      arrange(desc(Mes)) %>%
      mutate(
        `Mes` = format(Mes, "%B %Y"),
        `Cambio` = paste0(ifelse((Ofertas - lag(Ofertas)) > 0, "+", ""),
                          round((Ofertas - lag(Ofertas)) / lag(Ofertas) * 100, 1), "%")
      ) %>%
      select(Mes, Ofertas, Cambio)

    datatable(tabla, options = list(pageLength = 12, dom = 't'))
  })

  # ======================================================================
  # OUTPUTS PARA MAPA GEOGRÁFICO
  # ======================================================================
  output$mapa_argentina <- renderLeaflet({
    data_mapa <- datos_filtrados() %>%
      filter(!is.na(ubicacion.provincia)) %>%
      count(ubicacion.provincia, name = "Ofertas") %>%
      left_join(provincias_geo, by = c("ubicacion.provincia" = "provincia"))

    leaflet(data_mapa) %>%
      addTiles() %>%
      setView(lng = -64, lat = -38, zoom = 4) %>%
      addCircleMarkers(
        lng = ~lng,
        lat = ~lat,
        radius = ~sqrt(Ofertas) * 3,
        fillColor = "#A23B72",
        color = "#ffffff",
        weight = 2,
        opacity = 1,
        fillOpacity = 0.7,
        popup = ~paste0("<b>", ubicacion.provincia, "</b><br>",
                        "Ofertas: ", Ofertas)
      )
  })

  output$mapa_ciudades_plot <- renderPlotly({
    data <- datos_filtrados() %>%
      filter(!is.na(ubicacion.ciudad)) %>%
      count(ubicacion.ciudad, sort = TRUE) %>%
      head(15)

    plot_ly(data, x = ~n, y = ~reorder(ubicacion.ciudad, n), type = 'bar',
            orientation = 'h', marker = list(color = '#3F784C')) %>%
      layout(xaxis = list(title = "Ofertas"),
             yaxis = list(title = ""))
  })

  # ======================================================================
  # OUTPUTS PARA ANÁLISIS DE TEXTO
  # ======================================================================
  output$texto_con_titulo <- renderValueBox({
    con_titulo <- datos_filtrados() %>%
      filter(!is.na(informacion_basica.titulo)) %>%
      nrow()
    valueBox(con_titulo, "Con Título", icon = icon("file-alt"), color = "blue")
  })

  output$texto_palabras_unicas <- renderValueBox({
    palabras <- datos_filtrados() %>%
      filter(!is.na(informacion_basica.titulo)) %>%
      pull(informacion_basica.titulo) %>%
      paste(collapse = " ") %>%
      tolower() %>%
      strsplit("\\s+") %>%
      unlist() %>%
      unique() %>%
      length()
    valueBox(palabras, "Palabras Únicas", icon = icon("font"), color = "green")
  })

  output$texto_promedio_palabras <- renderValueBox({
    promedio <- datos_filtrados() %>%
      filter(!is.na(informacion_basica.titulo)) %>%
      mutate(palabras = str_count(informacion_basica.titulo, "\\S+")) %>%
      summarise(prom = mean(palabras, na.rm = TRUE)) %>%
      pull(prom) %>%
      round(1)
    valueBox(promedio, "Promedio/Título", icon = icon("calculator"), color = "yellow")
  })

  output$wordcloud_titulos <- renderWordcloud2({
    titulos <- datos_filtrados() %>%
      filter(!is.na(informacion_basica.titulo)) %>%
      pull(informacion_basica.titulo)

    if (length(titulos) == 0) return(NULL)

    palabras <- titulos %>%
      paste(collapse = " ") %>%
      tolower() %>%
      removePunctuation() %>%
      removeNumbers() %>%
      strsplit("\\s+") %>%
      unlist()

    # Palabras a excluir (stopwords español)
    stopwords_es <- c("el", "la", "de", "en", "y", "a", "los", "las", "del", "un", "una",
                      "por", "para", "con", "sin", "sobre", "entre", "hasta", "desde")

    freq <- table(palabras)
    freq <- freq[!names(freq) %in% stopwords_es]
    freq <- freq[nchar(names(freq)) > 2]  # Solo palabras >2 letras

    df_palabras <- data.frame(word = names(freq), freq = as.numeric(freq)) %>%
      arrange(desc(freq)) %>%
      head(100)

    wordcloud2(df_palabras, size = 0.7, color = "random-light", backgroundColor = "white")
  })

  output$texto_top_terminos <- renderPlotly({
    titulos <- datos_filtrados() %>%
      filter(!is.na(informacion_basica.titulo)) %>%
      pull(informacion_basica.titulo)

    if (length(titulos) == 0) return(NULL)

    palabras <- titulos %>%
      paste(collapse = " ") %>%
      tolower() %>%
      removePunctuation() %>%
      strsplit("\\s+") %>%
      unlist()

    stopwords_es <- c("el", "la", "de", "en", "y", "a", "los", "las", "del", "un", "una")

    freq_data <- as.data.frame(table(palabras), stringsAsFactors = FALSE) %>%
      filter(!palabras %in% stopwords_es, nchar(palabras) > 2) %>%
      arrange(desc(Freq)) %>%
      head(20)

    plot_ly(freq_data, x = ~Freq, y = ~reorder(palabras, Freq), type = 'bar',
            orientation = 'h', marker = list(color = '#F18F01')) %>%
      layout(xaxis = list(title = "Frecuencia"),
             yaxis = list(title = ""))
  })

  output$texto_terminos_tabla <- renderDT({
    titulos <- datos_filtrados() %>%
      filter(!is.na(informacion_basica.titulo)) %>%
      pull(informacion_basica.titulo)

    if (length(titulos) == 0) return(NULL)

    palabras <- titulos %>%
      paste(collapse = " ") %>%
      tolower() %>%
      removePunctuation() %>%
      strsplit("\\s+") %>%
      unlist()

    stopwords_es <- c("el", "la", "de", "en", "y", "a", "los", "las", "del", "un", "una")

    freq_data <- as.data.frame(table(palabras), stringsAsFactors = FALSE) %>%
      filter(!palabras %in% stopwords_es, nchar(palabras) > 2) %>%
      arrange(desc(Freq)) %>%
      head(50) %>%
      rename(Término = palabras, Frecuencia = Freq)

    datatable(freq_data, options = list(pageLength = 20))
  })

  # ======================================================================
  # OUTPUTS PARA CALIDAD DE DATOS
  # ======================================================================
  output$cal_completitud_general <- renderValueBox({
    df <- datos_base()
    campos <- c("informacion_basica.empresa", "ubicacion.provincia", "ubicacion.ciudad", "modalidad.modalidad_trabajo")
    completitud <- mean(sapply(campos, function(col) if(col %in% names(df)) sum(!is.na(df[[col]])) / nrow(df) else 0)) * 100
    valueBox(paste0(round(completitud, 1), "%"), "Completitud", icon = icon("check-circle"), color = "blue")
  })

  output$cal_registros_completos <- renderValueBox({
    df <- datos_base()
    completos <- df %>%
      filter(!is.na(informacion_basica.empresa), !is.na(ubicacion.provincia)) %>%
      nrow()
    valueBox(completos, "Registros OK", icon = icon("clipboard-check"), color = "green")
  })

  output$cal_campos_criticos <- renderValueBox({
    df <- datos_base()
    criticos <- sum(!is.na(df$informacion_basica.empresa) & !is.na(df$ubicacion.provincia)) / nrow(df) * 100
    valueBox(paste0(round(criticos, 1), "%"), "Campos Críticos", icon = icon("exclamation-triangle"), color = "yellow")
  })

  output$cal_score_calidad <- renderValueBox({
    df <- datos_base()
    score <- (sum(!is.na(df$informacion_basica.empresa)) / nrow(df) +
              sum(!is.na(df$ubicacion.provincia)) / nrow(df)) / 2 * 100
    valueBox(round(score, 0), "Score Global", icon = icon("star"), color = "purple")
  })

  output$calidad_completitud_plot <- renderPlotly({
    df <- datos_base()
    campos <- c("Empresa" = "informacion_basica.empresa",
                "Provincia" = "ubicacion.provincia",
                "Ciudad" = "ubicacion.ciudad",
                "Modalidad" = "modalidad.modalidad_trabajo",
                "Tipo Trabajo" = "modalidad.tipo_trabajo")

    completitud_data <- data.frame(
      Campo = names(campos),
      Completitud = sapply(campos, function(col) {
        if(col %in% names(df)) sum(!is.na(df[[col]])) / nrow(df) * 100 else 0
      })
    )

    plot_ly(completitud_data, x = ~Completitud, y = ~reorder(Campo, Completitud),
            type = 'bar', orientation = 'h',
            marker = list(color = ~Completitud,
                         colorscale = list(c(0, "red"), c(0.5, "yellow"), c(1, "green")),
                         cmin = 0, cmax = 100)) %>%
      layout(xaxis = list(title = "% Completitud", range = c(0, 100)),
             yaxis = list(title = ""))
  })

  output$calidad_tabla_detalle <- renderDT({
    df <- datos_base()
    campos <- c("Empresa", "Provincia", "Ciudad", "Modalidad", "Tipo Trabajo")
    cols <- c("informacion_basica.empresa", "ubicacion.provincia", "ubicacion.ciudad",
              "modalidad.modalidad_trabajo", "modalidad.tipo_trabajo")

    detalle <- data.frame(
      Campo = campos,
      Completos = sapply(cols, function(col) if(col %in% names(df)) sum(!is.na(df[[col]])) else 0),
      Vacíos = sapply(cols, function(col) if(col %in% names(df)) sum(is.na(df[[col]])) else nrow(df)),
      Completitud = sapply(cols, function(col) {
        if(col %in% names(df)) paste0(round(sum(!is.na(df[[col]])) / nrow(df) * 100, 1), "%") else "0%"
      })
    )

    datatable(detalle, options = list(dom = 't'))
  })

  output$calidad_inconsistencias <- renderUI({
    df <- datos_base()
    inconsistencias <- list()

    # Detectar provincias sospechosas
    if ("ubicacion.provincia" %in% names(df)) {
      prov_sosp <- df %>%
        filter(nchar(ubicacion.provincia) < 3 | ubicacion.provincia %in% c("B", "AR")) %>%
        count(ubicacion.provincia)

      if (nrow(prov_sosp) > 0) {
        inconsistencias <- c(inconsistencias, list(
          tags$p(icon("exclamation-triangle"), " Provincias sospechosas detectadas:",
                 paste(prov_sosp$ubicacion.provincia, collapse = ", "))
        ))
      }
    }

    # Total de inconsistencias
    inconsistencias <- c(inconsistencias, list(
      tags$p(style = "margin-top: 20px;",
             "Total inconsistencias detectadas: ", length(inconsistencias))
    ))

    do.call(tagList, inconsistencias)
  })

  # ========================================
  # PANEL DE ADMINISTRACIÓN - FEEDBACK
  # ========================================

  # Botón de descarga de feedback
  output$descargar_feedback <- downloadHandler(
    filename = function() {
      paste0("feedback_dashboard_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".csv")
    },
    content = function(file) {
      feedback_file <- "feedback_dashboard.csv"

      if (file.exists(feedback_file)) {
        # Leer y copiar el archivo
        file.copy(feedback_file, file)
      } else {
        # Si no existe, crear CSV vacío con headers
        empty_data <- data.frame(
          Timestamp = character(),
          Seccion = character(),
          Tipo = character(),
          Prioridad = numeric(),
          Opciones = character(),
          Comentario = character(),
          Impacto = character(),
          stringsAsFactors = FALSE
        )
        write.csv(empty_data, file, row.names = FALSE)
      }
    }
  )

  # Métricas de feedback
  output$total_feedbacks <- renderValueBox({
    feedback_file <- "feedback_dashboard.csv"

    total <- 0
    if (file.exists(feedback_file)) {
      df <- tryCatch({
        read.csv(feedback_file, stringsAsFactors = FALSE)
      }, error = function(e) { data.frame() })

      total <- nrow(df)
    }

    valueBox(
      total,
      "Feedbacks Recibidos",
      icon = icon("comments"),
      color = "blue"
    )
  })

  output$feedback_reciente <- renderValueBox({
    feedback_file <- "feedback_dashboard.csv"

    fecha_text <- "Sin feedback aún"
    if (file.exists(feedback_file)) {
      df <- tryCatch({
        read.csv(feedback_file, stringsAsFactors = FALSE)
      }, error = function(e) { data.frame() })

      if (nrow(df) > 0) {
        ultima_fecha <- max(as.POSIXct(df$Timestamp))
        fecha_text <- format(ultima_fecha, "%d/%m/%Y %H:%M")
      }
    }

    valueBox(
      fecha_text,
      "Último Feedback",
      icon = icon("clock"),
      color = "green"
    )
  })

  # Tabla de preview del feedback
  output$feedback_preview_table <- renderDT({
    feedback_file <- "feedback_dashboard.csv"

    if (file.exists(feedback_file)) {
      df <- tryCatch({
        read.csv(feedback_file, stringsAsFactors = FALSE)
      }, error = function(e) { data.frame() })

      if (nrow(df) > 0) {
        # Ordenar por timestamp descendente y tomar los últimos 10
        df <- df[order(as.POSIXct(df$Timestamp), decreasing = TRUE), ]
        df_preview <- head(df, 10)

        # Limpiar columnas para display
        df_display <- df_preview %>%
          select(Timestamp, Seccion, Tipo, Prioridad, Comentario) %>%
          mutate(
            Comentario = ifelse(nchar(Comentario) > 50,
                               paste0(substr(Comentario, 1, 50), "..."),
                               Comentario)
          )

        datatable(
          df_display,
          options = list(
            pageLength = 10,
            dom = 't',
            language = list(
              emptyTable = "No hay feedbacks aún"
            )
          ),
          rownames = FALSE,
          colnames = c("Fecha", "Sección", "Tipo", "Prioridad", "Comentario")
        )
      } else {
        datatable(
          data.frame(Mensaje = "No hay feedbacks recibidos aún"),
          options = list(dom = 't'),
          rownames = FALSE
        )
      }
    } else {
      datatable(
        data.frame(Mensaje = "No hay feedbacks recibidos aún"),
        options = list(dom = 't'),
        rownames = FALSE
      )
    }
  })

  # ========================================
  # SISTEMA DE FEEDBACK INTEGRADO
  # ========================================

  # Observar click en botón de feedback
  observeEvent(input$btn_feedback, {
    showModal(
      modalDialog(
        title = div(
          icon("comment-dots"),
          " Enviar Feedback",
          style = "color: #667eea; font-size: 24px; font-weight: bold;"
        ),
        size = "l",
        easyClose = TRUE,
        footer = tagList(
          modalButton("Cancelar"),
          actionButton("btn_enviar_feedback", "📤 Enviar Feedback",
                       class = "btn-primary btn-lg",
                       icon = icon("paper-plane"))
        ),

        # Introducción
        fluidRow(
          column(12,
            div(
              style = "background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;",
              p(icon("heart"), " Tu opinión es muy valiosa. Por favor ayúdanos a mejorar el dashboard.",
                style = "color: #666; margin: 0; font-size: 15px;")
            )
          )
        ),

        # Formulario - Fila 1
        fluidRow(
          column(6,
            selectInput(
              "feedback_pestana",
              div(icon("th-large"), " ¿Sobre qué sección?"),
              choices = c(
                "Selecciona..." = "",
                "📊 Resumen General" = "Resumen General",
                "🔍 Análisis por Fuente" = "Análisis por Fuente",
                "📈 Tendencias" = "Tendencias",
                "🗺️ Mapa Geográfico" = "Mapa Geográfico",
                "☁️ Análisis de Texto" = "Análisis de Texto",
                "🏢 Empresas" = "Empresas",
                "📅 Temporalidad" = "Temporalidad",
                "📍 Ubicación" = "Ubicación",
                "💼 Modalidad" = "Modalidad",
                "👔 Ocupaciones" = "Ocupaciones",
                "✅ Calidad de Datos" = "Calidad de Datos",
                "📄 Datos Crudos" = "Datos Crudos",
                "🎨 Diseño General" = "Diseño General",
                "💬 Otro / General" = "Otro"
              )
            )
          ),
          column(6,
            selectInput(
              "feedback_tipo",
              div(icon("tag"), " Tipo de feedback"),
              choices = c(
                "Selecciona..." = "",
                "💡 Sugerencia de mejora" = "Sugerencia",
                "🐛 Reportar error" = "Error",
                "📊 Solicitar análisis nuevo" = "Solicitud análisis",
                "📉 Solicitar nuevos filtros" = "Solicitud filtros",
                "❓ Pregunta sobre uso" = "Pregunta",
                "🎨 Mejora de diseño" = "Diseño",
                "⚡ Problema de rendimiento" = "Rendimiento",
                "👍 Comentario positivo" = "Positivo",
                "💬 Otro" = "Otro"
              )
            )
          )
        ),

        # Formulario - Fila 2 (Prioridad)
        fluidRow(
          column(12,
            div(style = "margin-bottom: 10px; margin-top: 15px;",
              strong(icon("star"), " ¿Qué tan importante es esto?")
            ),
            sliderInput(
              "feedback_prioridad",
              NULL,
              min = 1,
              max = 5,
              value = 3,
              step = 1,
              ticks = TRUE
            ),
            div(style = "display: flex; justify-content: space-between; margin-top: -10px; font-size: 12px; color: #999;",
              span("Poco importante"),
              span("Muy importante")
            )
          )
        ),

        # Opciones múltiples
        fluidRow(
          column(12,
            div(style = "margin-top: 15px; margin-bottom: 10px;",
              strong(icon("check-square"), " Marca las que apliquen (opcional):")
            ),
            checkboxGroupInput(
              "feedback_opciones",
              NULL,
              choices = list(
                "Me gustaría ver esta información de manera diferente" = "Ver diferente",
                "Me gustaría agregar un nuevo tipo de análisis" = "Nuevo análisis",
                "Hay datos que no se muestran correctamente" = "Datos incorrectos",
                "Los filtros no funcionan como esperaba" = "Filtros",
                "El dashboard es difícil de navegar" = "Navegación",
                "Necesito exportar datos en otro formato" = "Exportar",
                "Me gustaría comparar datos entre períodos" = "Comparar períodos",
                "Necesito más información sobre las empresas" = "Info empresas",
                "El dashboard es lento al cargar" = "Lento",
                "No encuentro la información que busco" = "No encuentro"
              ),
              inline = FALSE
            )
          )
        ),

        # Comentario principal
        fluidRow(
          column(12,
            div(style = "margin-top: 15px;",
              strong(icon("edit"), " Cuéntanos en detalle (obligatorio):")
            ),
            textAreaInput(
              "feedback_comentario",
              NULL,
              rows = 5,
              placeholder = "Por favor describe:
• ¿Qué intentabas hacer?
• ¿Qué esperabas que pasara?
• ¿Qué pasó realmente? (si es un error)
• ¿Cómo te gustaría que funcionara?

Ejemplo: 'Me gustaría ver un gráfico de tendencias mensuales por provincia para identificar patrones estacionales. Esto me ayudaría a crear reportes trimestrales más rápido.'"
            )
          )
        ),

        # Impacto
        fluidRow(
          column(12,
            div(style = "margin-top: 10px;",
              strong(icon("briefcase"), " ¿Cómo te ayudaría esto en tu trabajo? (opcional):")
            ),
            textAreaInput(
              "feedback_impacto",
              NULL,
              rows = 2,
              placeholder = "Ej: 'Me permitiría crear reportes semanales más rápido para mi equipo'"
            )
          )
        )
      )
    )
  })

  # Enviar feedback
  observeEvent(input$btn_enviar_feedback, {

    # Validar campos obligatorios
    if (is.null(input$feedback_pestana) || input$feedback_pestana == "") {
      showNotification(
        "⚠️ Por favor selecciona una sección del dashboard",
        type = "warning",
        duration = 5
      )
      return()
    }

    if (is.null(input$feedback_tipo) || input$feedback_tipo == "") {
      showNotification(
        "⚠️ Por favor selecciona el tipo de feedback",
        type = "warning",
        duration = 5
      )
      return()
    }

    if (is.null(input$feedback_comentario) || nchar(trimws(input$feedback_comentario)) == 0) {
      showNotification(
        "⚠️ Por favor escribe tu comentario en detalle",
        type = "warning",
        duration = 5
      )
      return()
    }

    # Preparar datos
    feedback_data <- data.frame(
      Timestamp = format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
      Seccion = input$feedback_pestana,
      Tipo = input$feedback_tipo,
      Prioridad = input$feedback_prioridad,
      Opciones = paste(input$feedback_opciones, collapse = "; "),
      Comentario = input$feedback_comentario,
      Impacto = ifelse(is.null(input$feedback_impacto) || input$feedback_impacto == "",
                       "", input$feedback_impacto),
      stringsAsFactors = FALSE
    )

    # Guardar en archivo CSV
    feedback_file <- "feedback_dashboard.csv"

    tryCatch({
      # Si el archivo existe, agregar. Si no, crear con headers
      if (file.exists(feedback_file)) {
        write.table(
          feedback_data,
          file = feedback_file,
          append = TRUE,
          col.names = FALSE,
          row.names = FALSE,
          sep = ",",
          quote = TRUE,
          fileEncoding = "UTF-8"
        )
      } else {
        write.table(
          feedback_data,
          file = feedback_file,
          append = FALSE,
          col.names = TRUE,
          row.names = FALSE,
          sep = ",",
          quote = TRUE,
          fileEncoding = "UTF-8"
        )
      }

      # Cerrar modal
      removeModal()

      # Mostrar notificación de éxito con estilo
      showNotification(
        div(
          style = "font-size: 16px;",
          icon("check-circle", style = "color: #28a745; margin-right: 8px;"),
          strong("¡Gracias por tu feedback!"),
          br(),
          span("Tu opinión es muy valiosa y nos ayudará a mejorar el dashboard.",
               style = "font-size: 14px;")
        ),
        type = "message",
        duration = 7,
        closeButton = TRUE
      )

    }, error = function(e) {
      showNotification(
        div(
          icon("exclamation-triangle"),
          " Error al guardar feedback: ", e$message,
          br(),
          "Por favor intenta nuevamente o contacta al administrador."
        ),
        type = "error",
        duration = 10
      )
    })
  })

}

# Run the application
shinyApp(ui, server)
