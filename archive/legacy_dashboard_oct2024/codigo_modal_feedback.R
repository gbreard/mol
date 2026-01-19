# ========================================
# CÓDIGO PARA MODAL DE FEEDBACK INTEGRADO
# ========================================
# Este código se agrega al app.R existente
# NO requiere crear Google Form

# ========================================
# PARTE 1: EN EL SERVER (agregar al final)
# ========================================

# Observar click en botón de feedback
observeEvent(input$btn_feedback, {
  showModal(
    modalDialog(
      title = div(
        icon("comment-dots"),
        "Enviar Feedback",
        style = "color: #667eea; font-size: 24px;"
      ),
      size = "l",
      easyClose = TRUE,
      footer = tagList(
        modalButton("Cancelar"),
        actionButton("btn_enviar_feedback", "📤 Enviar Feedback",
                     class = "btn-primary",
                     icon = icon("paper-plane"))
      ),

      # Formulario
      fluidRow(
        column(12,
          p("Tu opinión es muy valiosa. Por favor ayúdanos a mejorar el dashboard.",
            style = "color: #666; margin-bottom: 20px;")
        )
      ),

      fluidRow(
        # Columna izquierda
        column(6,
          textInput(
            "feedback_email",
            "✉️ Tu email (opcional)",
            placeholder = "tu@email.com"
          ),

          selectInput(
            "feedback_pestana",
            "📊 ¿Sobre qué sección?",
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
              "💬 Otro" = "Otro"
            )
          ),

          selectInput(
            "feedback_tipo",
            "🏷️ Tipo de feedback",
            choices = c(
              "Selecciona..." = "",
              "💡 Sugerencia de mejora" = "Sugerencia",
              "🐛 Reportar error" = "Error",
              "📊 Solicitar análisis" = "Solicitud análisis",
              "📉 Solicitar filtros" = "Solicitud filtros",
              "❓ Pregunta" = "Pregunta",
              "🎨 Mejora de diseño" = "Diseño",
              "⚡ Problema de rendimiento" = "Rendimiento",
              "👍 Comentario positivo" = "Positivo",
              "💬 Otro" = "Otro"
            )
          )
        ),

        # Columna derecha
        column(6,
          sliderInput(
            "feedback_prioridad",
            "⭐ ¿Qué tan importante?",
            min = 1,
            max = 5,
            value = 3,
            step = 1,
            ticks = TRUE
          ),

          selectInput(
            "feedback_frecuencia",
            "📅 ¿Con qué frecuencia usas el dashboard?",
            choices = c(
              "Selecciona..." = "",
              "Diariamente" = "Diario",
              "Varias veces por semana" = "Semanal+",
              "Semanalmente" = "Semanal",
              "Mensualmente" = "Mensual",
              "Primera vez" = "Primera vez",
              "Esporádicamente" = "Esporádico"
            )
          ),

          sliderInput(
            "feedback_satisfaccion",
            "😊 Satisfacción general",
            min = 1,
            max = 5,
            value = 4,
            step = 1,
            ticks = TRUE
          )
        )
      ),

      fluidRow(
        column(12,
          checkboxGroupInput(
            "feedback_opciones",
            "☑️ Marca las que apliquen:",
            choices = c(
              "Me gustaría ver esta información de manera diferente" = "Ver diferente",
              "Me gustaría agregar un nuevo análisis" = "Nuevo análisis",
              "Hay datos incorrectos" = "Datos incorrectos",
              "Los filtros no funcionan bien" = "Filtros",
              "Es difícil de navegar" = "Navegación",
              "Necesito exportar en otro formato" = "Exportar",
              "Quiero comparar períodos" = "Comparar períodos",
              "Necesito más info de empresas" = "Info empresas",
              "El dashboard es lento" = "Lento",
              "No encuentro lo que busco" = "No encuentro"
            ),
            inline = FALSE
          )
        )
      ),

      fluidRow(
        column(12,
          textAreaInput(
            "feedback_comentario",
            "✍️ Cuéntanos en detalle (obligatorio)",
            rows = 5,
            placeholder = "Por favor describe:
• ¿Qué intentabas hacer?
• ¿Qué esperabas que pasara?
• ¿Qué pasó realmente? (si aplica)
• ¿Cómo te gustaría que funcionara?

Ejemplo: 'Me gustaría ver un gráfico de tendencias mensuales por provincia para identificar patrones estacionales...'"
          )
        )
      ),

      fluidRow(
        column(12,
          textAreaInput(
            "feedback_impacto",
            "💼 ¿Cómo te ayudaría esto? (opcional)",
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
    showNotification("⚠️ Por favor selecciona una sección", type = "warning")
    return()
  }

  if (is.null(input$feedback_tipo) || input$feedback_tipo == "") {
    showNotification("⚠️ Por favor selecciona el tipo de feedback", type = "warning")
    return()
  }

  if (is.null(input$feedback_frecuencia) || input$feedback_frecuencia == "") {
    showNotification("⚠️ Por favor indica con qué frecuencia usas el dashboard", type = "warning")
    return()
  }

  if (is.null(input$feedback_comentario) || nchar(trimws(input$feedback_comentario)) == 0) {
    showNotification("⚠️ Por favor escribe tu comentario", type = "warning")
    return()
  }

  # Preparar datos
  feedback_data <- data.frame(
    Timestamp = format(Sys.time(), "%Y-%m-%d %H:%M:%S"),
    Email = ifelse(is.null(input$feedback_email) || input$feedback_email == "",
                   "Anónimo", input$feedback_email),
    Sección = input$feedback_pestana,
    Tipo = input$feedback_tipo,
    Prioridad = input$feedback_prioridad,
    Frecuencia = input$feedback_frecuencia,
    Satisfacción = input$feedback_satisfaccion,
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

    # Mostrar notificación de éxito
    showNotification(
      div(
        icon("check-circle"),
        "¡Gracias por tu feedback! Tu opinión es muy valiosa."
      ),
      type = "message",
      duration = 5
    )

    # Limpiar campos (para próxima vez)
    updateTextInput(session, "feedback_email", value = "")
    updateSelectInput(session, "feedback_pestana", selected = "")
    updateSelectInput(session, "feedback_tipo", selected = "")
    updateSelectInput(session, "feedback_frecuencia", selected = "")
    updateTextInput(session, "feedback_comentario", value = "")
    updateTextInput(session, "feedback_impacto", value = "")
    updateCheckboxGroupInput(session, "feedback_opciones", selected = character(0))

  }, error = function(e) {
    showNotification(
      paste("❌ Error al guardar feedback:", e$message),
      type = "error",
      duration = 10
    )
  })
})

# ========================================
# PARTE 2: CAMBIAR EL BOTÓN EN EL UI
# ========================================

# En el UI, donde está el botón flotante, cambiar:
# ANTES:
#   onclick = "window.open('AQUI_VA_TU_ENLACE_DE_GOOGLE_FORM', '_blank')",

# DESPUÉS:
#   id = "btn_feedback",

# Código completo del botón:
tags$div(
  class = "feedback-btn-container",
  actionButton(
    "btn_feedback",
    HTML("<i class='fa fa-comment-dots' style='font-size: 18px;'></i><span>Enviar Feedback</span>"),
    class = "feedback-btn feedback-pulse"
  )
)

# ========================================
# NOTAS IMPORTANTES
# ========================================

# 1. El feedback se guarda en: feedback_dashboard.csv
#    (en el mismo directorio que app.R)

# 2. Para ver el feedback:
#    - Descarga el archivo desde shinyapps.io, O
#    - Usa RStudio Connect que permite acceso a archivos, O
#    - Implementa versión con Google Sheets (requiere API)

# 3. Para shinyapps.io:
#    El archivo CSV se guarda en el servidor temporal
#    Tienes que descargarlo periódicamente desde:
#    https://www.shinyapps.io/admin/#/applications/TU_APP_ID/logs

# 4. MEJOR OPCIÓN para shinyapps.io:
#    Usar Google Sheets API (siguiente código)
