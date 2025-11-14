# ============================================================================
# DASHBOARD MEJORADO DE OFERTAS LABORALES - OEDE
# Versión 3.0 - Dashboard Completo con Análisis Avanzados
# ============================================================================

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

# Cargar librerías avanzadas (con manejo de errores)
tryCatch({
  library(leaflet)
  library(tidytext)
  library(wordcloud2)
  library(tm)
  library(openxlsx)
  library(zoo)
  library(scales)
}, error = function(e) {
  cat("Advertencia: Algunas librerías avanzadas no están instaladas.\n")
  cat("Ejecuta: source('instalar_paquetes_avanzados.R')\n")
})

# Configurar encoding
Sys.setlocale("LC_ALL", "es_ES.UTF-8")

# ============================================================================
# DATOS DE GEOCODIFICACIÓN DE PROVINCIAS ARGENTINAS
# ============================================================================
provincias_geo <- data.frame(
  provincia = c("Buenos Aires", "Buenos Aires-GBA", "CABA", "Córdoba", "Santa Fe",
                "Mendoza", "Tucumán", "Entre Ríos", "Salta", "Misiones",
                "Chaco", "Corrientes", "Santiago del Estero", "San Juan", "Jujuy",
                "Río Negro", "Neuquén", "Formosa", "Chubut", "San Luis",
                "Catamarca", "La Rioja", "La Pampa", "Santa Cruz", "Tierra del Fuego"),
  lat = c(-36.6769, -34.6037, -34.6037, -31.4201, -31.6333,
          -32.8895, -26.8083, -31.7333, -24.7821, -27.3621,
          -27.4511, -27.4806, -27.7834, -31.5375, -24.1857,
          -40.8135, -38.9516, -26.1775, -43.2994, -33.3017,
          -28.4696, -29.4131, -36.6156, -51.6226, -54.8019),
  lng = c(-60.5588, -58.3816, -58.3816, -64.1888, -60.7000,
          -68.8458, -65.2176, -60.5000, -65.4232, -55.9007,
          -59.0225, -58.8341, -64.2642, -68.5364, -65.2995,
          -63.0000, -68.0591, -58.1781, -65.1023, -66.3378,
          -65.7795, -66.8558, -64.2843, -69.2168, -68.3029)
)

# ============================================================================
# UI - INTERFAZ DE USUARIO
# ============================================================================
ui <- dashboardPage(
  skin = "blue",

  # HEADER
  dashboardHeader(
    title = "Ofertas Laborales - OEDE",
    titleWidth = 300
  ),

  # SIDEBAR
  dashboardSidebar(
    width = 300,
    sidebarMenu(
      id = "tabs",
      menuItem("🏠 Resumen General", tabName = "resumen", icon = icon("dashboard")),
      menuItem("📊 Análisis por Fuente", tabName = "fuentes", icon = icon("database")),
      menuItem("📈 Tendencias Temporales", tabName = "tendencias", icon = icon("chart-line")),
      menuItem("🗺️ Mapa Geográfico", tabName = "mapa", icon = icon("map-marked-alt")),
      menuItem("🏢 Empresas", tabName = "empresas", icon = icon("building")),
      menuItem("📅 Temporalidad", tabName = "temporalidad", icon = icon("calendar")),
      menuItem("📍 Ubicación", tabName = "ubicacion", icon = icon("map")),
      menuItem("💼 Modalidad", tabName = "modalidad", icon = icon("laptop-house")),
      menuItem("👔 Ocupaciones", tabName = "ocupaciones", icon = icon("briefcase")),
      menuItem("📝 Análisis de Texto", tabName = "texto", icon = icon("file-alt")),
      menuItem("🔍 Calidad de Datos", tabName = "calidad", icon = icon("check-circle")),
      menuItem("📄 Datos Crudos", tabName = "datos", icon = icon("table"))
    ),

    # FILTROS GLOBALES
    hr(),
    h4("⚙️ Filtros Globales", style = "padding-left: 15px; color: white;"),

    dateRangeInput("fecha_rango",
                   "📅 Rango de fechas:",
                   start = Sys.Date() - 90,
                   end = Sys.Date(),
                   format = "yyyy-mm-dd",
                   language = "es"),

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
                "⏰ Tipo de Trabajo:",
                choices = c("Todos" = "todos"),
                selected = "todos"),

    textInput("buscar_texto",
              "🔎 Buscar en título:",
              placeholder = "Ej: desarrollador, analista..."),

    tags$small("Los filtros se aplican automáticamente",
               style = "padding-left: 15px; color: #aaa;")
  ),

  # BODY
  dashboardBody(
    tags$head(
      tags$style(HTML("
        .box { margin-bottom: 15px; }
        .info-box { min-height: 100px; }
        .small-box { border-radius: 5px; }
        .value-box { font-size: 24px; font-weight: bold; }
        .main-header .logo { font-weight: bold; }
        .skin-blue .main-header .navbar { background-color: #3c8dbc; }
      "))
    ),

    tabItems(
      # =====================================================================
      # PESTAÑA: RESUMEN GENERAL
      # =====================================================================
      tabItem(tabName = "resumen",
        h2("📊 Resumen General de Ofertas Laborales"),

        fluidRow(
          valueBoxOutput("vbox_total_vacantes", width = 3),
          valueBoxOutput("vbox_total_empresas", width = 3),
          valueBoxOutput("vbox_total_provincias", width = 3),
          valueBoxOutput("vbox_total_ocupaciones", width = 3)
        ),

        fluidRow(
          box(
            title = "📈 Evolución de Vacantes por Fecha",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("resumen_fecha_plot"),
            width = 6
          ),
          box(
            title = "🏢 Top 10 Empresas con Más Vacantes",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("resumen_empresas_plot"),
            width = 6
          )
        ),

        fluidRow(
          box(
            title = "📍 Distribución por Provincia",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("resumen_provincia_plot"),
            width = 6
          ),
          box(
            title = "💼 Distribución por Modalidad",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("resumen_modalidad_plot"),
            width = 6
          )
        ),

        fluidRow(
          box(
            title = "🔍 Distribución por Fuente de Datos",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("resumen_fuente_plot"),
            width = 6
          ),
          box(
            title = "⏰ Distribución por Tipo de Trabajo",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("resumen_tipo_trabajo_plot"),
            width = 6
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: ANÁLISIS POR FUENTE
      # =====================================================================
      tabItem(tabName = "fuentes",
        h2("📊 Análisis por Fuente de Scraping"),

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
            width = 6,
            height = 450
          ),
          box(
            title = "📊 Comparativa de Fuentes",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("fuente_barras"),
            width = 6,
            height = 450
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

      # =====================================================================
      # PESTAÑA: TENDENCIAS TEMPORALES
      # =====================================================================
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
            title = "📅 Heatmap - Ofertas por Día de la Semana y Semana",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("tendencia_heatmap"),
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

      # =====================================================================
      # PESTAÑA: MAPA GEOGRÁFICO
      # =====================================================================
      tabItem(tabName = "mapa",
        h2("🗺️ Mapa Interactivo de Ofertas Laborales"),

        fluidRow(
          box(
            title = "🗺️ Distribución Geográfica de Ofertas en Argentina",
            status = "primary",
            solidHeader = TRUE,
            leafletOutput("mapa_argentina", height = 600),
            width = 12,
            footer = tags$div(
              tags$p("💡 Haz clic en los círculos para ver detalles por provincia"),
              tags$p("📍 El tamaño del círculo representa la cantidad de ofertas"),
              style = "font-size: 12px; color: #666;"
            )
          )
        ),

        fluidRow(
          box(
            title = "🏙️ Top 10 Ciudades con Más Ofertas",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("mapa_ciudades_plot"),
            width = 12
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: EMPRESAS (Mejorada)
      # =====================================================================
      tabItem(tabName = "empresas",
        h2("🏢 Análisis Detallado de Empresas"),

        fluidRow(
          valueBoxOutput("emp_total_empresas", width = 3),
          valueBoxOutput("emp_promedio_ofertas", width = 3),
          valueBoxOutput("emp_empresa_top", width = 3),
          valueBoxOutput("emp_empresas_activas", width = 3)
        ),

        fluidRow(
          box(
            title = "🏆 Top 20 Empresas por Cantidad de Vacantes",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("empresas_top_plot"),
            width = 12
          )
        ),

        fluidRow(
          box(
            title = "📊 Distribución de Ofertas por Empresa",
            status = "info",
            solidHeader = TRUE,
            plotlyOutput("empresas_distribucion"),
            width = 6
          ),
          box(
            title = "📈 Empresas Más Activas por Período",
            status = "success",
            solidHeader = TRUE,
            plotlyOutput("empresas_temporal"),
            width = 6
          )
        ),

        fluidRow(
          box(
            title = "📋 Tabla Completa de Empresas",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("empresas_table"),
            width = 12
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: TEMPORALIDAD
      # =====================================================================
      tabItem(tabName = "temporalidad",
        h2("📅 Análisis Temporal Detallado"),

        fluidRow(
          box(
            title = "📈 Vacantes por Fecha (Gráfico de Área)",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("temporal_area_plot"),
            width = 12
          )
        ),

        fluidRow(
          box(
            title = "📋 Detalle por Fecha",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("temporal_tabla"),
            width = 12
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: UBICACIÓN
      # =====================================================================
      tabItem(tabName = "ubicacion",
        h2("📍 Análisis por Ubicación"),

        fluidRow(
          box(
            title = "📊 Top 20 Provincias",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("ubicacion_provincias_plot"),
            width = 6
          ),
          box(
            title = "🏙️ Top 15 Ciudades",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("ubicacion_ciudades_plot"),
            width = 6
          )
        ),

        fluidRow(
          box(
            title = "📋 Tabla de Provincias",
            status = "info",
            solidHeader = TRUE,
            DTOutput("ubicacion_provincias_tabla"),
            width = 6
          ),
          box(
            title = "📋 Tabla de Ciudades",
            status = "info",
            solidHeader = TRUE,
            DTOutput("ubicacion_ciudades_tabla"),
            width = 6
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: MODALIDAD
      # =====================================================================
      tabItem(tabName = "modalidad",
        h2("💼 Análisis por Modalidad de Trabajo"),

        fluidRow(
          valueBoxOutput("mod_presencial", width = 3),
          valueBoxOutput("mod_remoto", width = 3),
          valueBoxOutput("mod_hibrido", width = 3),
          valueBoxOutput("mod_sin_especificar", width = 3)
        ),

        fluidRow(
          box(
            title = "📊 Distribución por Modalidad",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("modalidad_detalle_plot"),
            width = 12
          )
        ),

        fluidRow(
          box(
            title = "📋 Tabla de Modalidades",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("modalidad_table"),
            width = 12
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: OCUPACIONES
      # =====================================================================
      tabItem(tabName = "ocupaciones",
        h2("👔 Análisis de Ocupaciones"),

        fluidRow(
          box(
            title = "🏆 Top 20 Ocupaciones Más Solicitadas",
            status = "primary",
            solidHeader = TRUE,
            plotlyOutput("ocupaciones_plot"),
            width = 12
          )
        ),

        fluidRow(
          box(
            title = "📋 Tabla Completa de Ocupaciones",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("ocupaciones_table"),
            width = 12
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: ANÁLISIS DE TEXTO
      # =====================================================================
      tabItem(tabName = "texto",
        h2("📝 Análisis de Contenido Textual"),

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
            footer = "Las palabras más grandes son las más frecuentes en los títulos de las ofertas"
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
            title = "📋 Tabla de Frecuencia de Términos",
            status = "info",
            solidHeader = TRUE,
            DTOutput("texto_terminos_tabla"),
            width = 6
          )
        )
      ),

      # =====================================================================
      # PESTAÑA: CALIDAD DE DATOS
      # =====================================================================
      tabItem(tabName = "calidad",
        h2("🔍 Dashboard de Calidad de Datos"),

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

      # =====================================================================
      # PESTAÑA: DATOS CRUDOS
      # =====================================================================
      tabItem(tabName = "datos",
        h2("📄 Base de Datos Completa"),

        fluidRow(
          box(
            title = "💾 Exportar Datos",
            status = "success",
            solidHeader = TRUE,
            downloadButton("descargar_csv", "📥 Descargar CSV"),
            downloadButton("descargar_excel", "📥 Descargar Excel"),
            width = 12
          )
        ),

        fluidRow(
          box(
            title = "📋 Tabla de Datos Filtrados",
            status = "primary",
            solidHeader = TRUE,
            DTOutput("datos_crudos_table"),
            width = 12
          )
        )
      )
    )
  )
)

# ============================================================================
# SERVER - LÓGICA DEL SERVIDOR
# ============================================================================
server <- function(input, output, session) {

  # ==========================================================================
  # CARGA Y PROCESAMIENTO DE DATOS
  # ==========================================================================

  datos_base <- reactive({
    req(file.exists("ofertas_consolidadas.xlsx"))

    tryCatch({
      df <- read_excel("ofertas_consolidadas.xlsx", sheet = "BASE")

      # Procesar fechas
      if ("Periodo" %in% names(df)) {
        df <- df %>%
          mutate(Fecha = as.Date(Periodo, format = "%Y-%m-%d"))
      } else {
        df$Fecha <- Sys.Date()
      }

      # Agregar columnas auxiliares
      df <- df %>%
        mutate(
          dia_semana = weekdays(Fecha),
          semana = week(Fecha),
          mes = month(Fecha, label = TRUE),
          año = year(Fecha)
        )

      validate(need(nrow(df) > 0, "No hay datos en el archivo Excel"))

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

    # Filtro de fecha
    if (!is.null(input$fecha_rango)) {
      df <- df %>%
        filter(Fecha >= input$fecha_rango[1] & Fecha <= input$fecha_rango[2])
    }

    # Filtro de fuente
    if (!is.null(input$filtro_fuente) && input$filtro_fuente != "todas") {
      df <- df %>%
        filter(`_metadata.source` == input$filtro_fuente)
    }

    # Filtro de provincia
    if (!is.null(input$filtro_provincia) && input$filtro_provincia != "todas" && "ubicacion.provincia" %in% names(df)) {
      df <- df %>%
        filter(ubicacion.provincia == input$filtro_provincia)
    }

    # Filtro de ciudad
    if (!is.null(input$filtro_ciudad) && input$filtro_ciudad != "todas" && "ubicacion.ciudad" %in% names(df)) {
      df <- df %>%
        filter(ubicacion.ciudad == input$filtro_ciudad)
    }

    # Filtro de modalidad
    if (!is.null(input$filtro_modalidad) && input$filtro_modalidad != "todas" && "modalidad.modalidad_trabajo" %in% names(df)) {
      df <- df %>%
        filter(modalidad.modalidad_trabajo == input$filtro_modalidad)
    }

    # Filtro de tipo de trabajo
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

  # Actualizar opciones de filtros dinámicamente
  observe({
    df <- datos_base()

    if (nrow(df) > 0) {
      # Actualizar fuentes
      fuentes <- df %>%
        pull(`_metadata.source`) %>%
        unique() %>%
        sort()

      updateSelectInput(session, "filtro_fuente",
                        choices = c("Todas" = "todas", setNames(fuentes, fuentes)))

      # Actualizar provincias
      if ("ubicacion.provincia" %in% names(df)) {
        provincias <- df %>%
          filter(!is.na(ubicacion.provincia)) %>%
          pull(ubicacion.provincia) %>%
          unique() %>%
          sort()

        updateSelectInput(session, "filtro_provincia",
                          choices = c("Todas" = "todas", setNames(provincias, provincias)))
      }

      # Actualizar ciudades (top 20)
      if ("ubicacion.ciudad" %in% names(df)) {
        ciudades_top <- df %>%
          filter(!is.na(ubicacion.ciudad)) %>%
          count(ubicacion.ciudad, sort = TRUE) %>%
          head(20) %>%
          pull(ubicacion.ciudad)

        updateSelectInput(session, "filtro_ciudad",
                          choices = c("Todas" = "todas", setNames(ciudades_top, ciudades_top)))
      }

      # Actualizar modalidades
      if ("modalidad.modalidad_trabajo" %in% names(df)) {
        modalidades <- df %>%
          filter(!is.na(modalidad.modalidad_trabajo)) %>%
          pull(modalidad.modalidad_trabajo) %>%
          unique() %>%
          sort()

        updateSelectInput(session, "filtro_modalidad",
                          choices = c("Todas" = "todas", setNames(modalidades, modalidades)))
      }

      # Actualizar tipos de trabajo
      if ("modalidad.tipo_trabajo" %in% names(df)) {
        tipos <- df %>%
          filter(!is.na(modalidad.tipo_trabajo)) %>%
          pull(modalidad.tipo_trabajo) %>%
          unique() %>%
          sort()

        updateSelectInput(session, "filtro_tipo_trabajo",
                          choices = c("Todos" = "todos", setNames(tipos, tipos)))
      }
    }
  })

  # Continúa en la siguiente parte...

