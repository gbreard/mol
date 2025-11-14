# 💬 SISTEMA DE FEEDBACK PARA SHINY DASHBOARD

## Opciones para Implementar Feedback

---

## 🟢 OPCIÓN 1: BOTÓN DE FEEDBACK CON GOOGLE FORMS (MÁS SIMPLE)

**Dificultad:** ⭐ Muy Fácil
**Costo:** Gratis
**Tiempo:** 10 minutos

### Cómo funciona:
- Botón "💬 Feedback" en cada pestaña
- Click abre Google Form en nueva ventana
- Las respuestas se guardan automáticamente en Google Sheets

### Ventajas:
- ✅ Súper rápido de implementar
- ✅ No requiere base de datos
- ✅ Google maneja todo (almacenamiento, notificaciones)
- ✅ Exportas a Excel cuando quieras

### Desventajas:
- ❌ Abre nueva ventana (no integrado)
- ❌ Usuario debe llenar su email manualmente

### Implementación:

**Paso 1: Crear Google Form**
1. Ve a https://forms.google.com/
2. Crea nuevo formulario
3. Agrega campos:
   - Email (opcional)
   - Pestaña del dashboard (opción múltiple)
   - Tipo de feedback (Mejora/Error/Sugerencia)
   - Comentario (texto largo)
4. Click en "Enviar" → Copiar enlace

**Paso 2: Agregar botón en Shiny**

```r
# En el UI, dentro de cada tabItem:
fluidRow(
  column(12,
    div(style = "position: absolute; top: 10px; right: 20px; z-index: 1000;",
      actionButton(
        "btn_feedback_resumen",
        "💬 Enviar Feedback",
        icon = icon("comment"),
        class = "btn-info btn-sm",
        onclick = "window.open('https://forms.gle/TU_ENLACE_AQUI', '_blank')"
      )
    )
  )
)
```

**Listo!** Cada botón abre el formulario de Google.

---

## 🟡 OPCIÓN 2: MODAL DE FEEDBACK INTEGRADO (RECOMENDADO)

**Dificultad:** ⭐⭐ Fácil
**Costo:** Gratis
**Tiempo:** 30 minutos

### Cómo funciona:
- Botón "💬 Feedback" en cada pestaña
- Click abre modal (ventana emergente) dentro de la app
- Formulario integrado en el dashboard
- Feedback se guarda en Google Sheets automáticamente

### Ventajas:
- ✅ Experiencia integrada (no sale de la app)
- ✅ Captura automáticamente la pestaña actual
- ✅ Puede pre-llenar email del usuario (si hay login)
- ✅ Google Sheets como backend (gratis)

### Desventajas:
- ⚠️ Requiere configurar Google Sheets API (15 min extra)

### Implementación Completa:

#### **Paso 1: Instalar paquete googlesheets4**

```r
install.packages("googlesheets4")
```

#### **Paso 2: Código del Sistema de Feedback**

```r
# =======================
# UI - Agregar en cada tabItem
# =======================

# Botón flotante de feedback (agregar al final de cada tabItem)
absolutePanel(
  top = 10, right = 20,
  actionButton(
    "btn_feedback",
    "💬 Feedback",
    icon = icon("comment-dots"),
    class = "btn-info btn-sm"
  )
)

# =======================
# SERVER - Agregar en server function
# =======================

library(googlesheets4)

# Desactivar autenticación para escritura pública
gs4_deauth()

# ID de tu Google Sheet (crear primero, ver instrucciones abajo)
FEEDBACK_SHEET_ID <- "TU_GOOGLE_SHEET_ID_AQUI"

# Observar click en botón de feedback
observeEvent(input$btn_feedback, {
  showModal(
    modalDialog(
      title = "💬 Enviar Feedback",
      size = "m",

      textInput(
        "feedback_email",
        "📧 Tu email (opcional):",
        placeholder = "tu@email.com"
      ),

      selectInput(
        "feedback_pestaña",
        "📊 ¿Sobre qué pestaña?",
        choices = c(
          "Resumen General",
          "Análisis por Fuente",
          "Tendencias",
          "Mapa Geográfico",
          "Análisis de Texto",
          "Empresas",
          "Temporalidad",
          "Ubicación",
          "Modalidad",
          "Ocupaciones",
          "Calidad de Datos",
          "Datos Crudos",
          "General"
        )
      ),

      selectInput(
        "feedback_tipo",
        "🏷️ Tipo de feedback:",
        choices = c(
          "💡 Sugerencia de mejora",
          "🐛 Reportar error",
          "📊 Solicitud de análisis",
          "❓ Pregunta",
          "👍 Comentario positivo",
          "💬 Otro"
        )
      ),

      textAreaInput(
        "feedback_texto",
        "✍️ Tu comentario:",
        rows = 5,
        placeholder = "Describe tu sugerencia, error, o comentario..."
      ),

      footer = tagList(
        modalButton("Cancelar"),
        actionButton("btn_enviar_feedback", "📤 Enviar", class = "btn-primary")
      )
    )
  )
})

# Enviar feedback a Google Sheets
observeEvent(input$btn_enviar_feedback, {

  # Validar que hay texto
  req(input$feedback_texto)

  if (nchar(trimws(input$feedback_texto)) == 0) {
    showNotification(
      "⚠️ Por favor escribe un comentario",
      type = "warning"
    )
    return()
  }

  # Preparar datos
  feedback_data <- data.frame(
    Fecha = as.character(Sys.time()),
    Email = ifelse(is.null(input$feedback_email) || input$feedback_email == "",
                   "Anónimo", input$feedback_email),
    Pestaña = input$feedback_pestaña,
    Tipo = input$feedback_tipo,
    Comentario = input$feedback_texto,
    stringsAsFactors = FALSE
  )

  # Intentar guardar en Google Sheets
  tryCatch({
    sheet_append(
      ss = FEEDBACK_SHEET_ID,
      data = feedback_data
    )

    # Cerrar modal
    removeModal()

    # Mostrar notificación de éxito
    showNotification(
      "✅ ¡Gracias! Tu feedback fue enviado exitosamente",
      type = "message",
      duration = 5
    )

    # Limpiar campos
    updateTextInput(session, "feedback_email", value = "")
    updateTextInput(session, "feedback_texto", value = "")

  }, error = function(e) {
    showNotification(
      paste("❌ Error al enviar:", e$message),
      type = "error",
      duration = 10
    )
  })
})
```

#### **Paso 3: Configurar Google Sheets**

1. **Crear Google Sheet:**
   - Ve a https://sheets.google.com/
   - Crea nueva hoja
   - Nómbrala "Feedback Dashboard OEDE"
   - Agrega estos headers en la primera fila:
     ```
     Fecha | Email | Pestaña | Tipo | Comentario
     ```

2. **Hacer la hoja pública para escritura:**
   - Click en "Compartir"
   - Cambiar a "Cualquiera con el enlace"
   - Permisos: "Editor"
   - Copiar ID del Sheet (está en la URL):
     ```
     https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
     ```

3. **Pegar ID en el código:**
   ```r
   FEEDBACK_SHEET_ID <- "PEGA_TU_ID_AQUI"
   ```

---

## 🟠 OPCIÓN 3: FEEDBACK CON PERMISOS DE USUARIO

**Dificultad:** ⭐⭐⭐ Media
**Costo:** Gratis
**Tiempo:** 1-2 horas

### Cómo funciona:
- Sistema de login simple
- Solo usuarios autorizados pueden dejar feedback
- Captura automáticamente quién dejó el feedback

### Implementación:

```r
# Instalar paquete de autenticación
install.packages("shinymanager")

library(shinymanager)

# Crear base de usuarios
credentials <- data.frame(
  user = c("gerardo", "admin", "analista1"),
  password = c("pass123", "admin456", "ana789"),
  permisos = c("admin", "admin", "viewer"),
  stringsAsFactors = FALSE
)

# Envolver UI con autenticación
ui <- secure_app(
  ui = dashboardPage(...),
  choose_language = FALSE
)

# En el server
server <- function(input, output, session) {

  # Verificar credenciales
  res_auth <- secure_server(
    check_credentials = check_credentials(credentials)
  )

  # Obtener usuario actual
  output$user_name <- renderText({
    paste("Usuario:", res_auth$user)
  })

  # En el feedback, pre-llenar con usuario actual
  observeEvent(input$btn_feedback, {
    showModal(
      modalDialog(
        title = "💬 Enviar Feedback",

        # Email automático del usuario logueado
        textInput(
          "feedback_email",
          "📧 Usuario:",
          value = res_auth$user,
          disabled = TRUE  # No editable
        ),

        # ... resto del formulario igual
      )
    )
  })
}
```

---

## 🔴 OPCIÓN 4: SISTEMA COMPLETO CON BASE DE DATOS

**Dificultad:** ⭐⭐⭐⭐ Avanzada
**Costo:** Gratis (SQLite) o $7/mes (PostgreSQL en Railway)
**Tiempo:** 3-5 horas

### Características:
- Base de datos propia (SQLite o PostgreSQL)
- Dashboard admin para ver/responder feedback
- Estados: Nuevo/En revisión/Resuelto
- Notificaciones por email
- Export a Excel

### Código Básico con SQLite:

```r
library(DBI)
library(RSQLite)

# Crear/conectar a BD
con <- dbConnect(SQLite(), "feedback.db")

# Crear tabla (solo primera vez)
dbExecute(con, "
  CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    usuario TEXT,
    pestaña TEXT,
    tipo TEXT,
    comentario TEXT,
    estado TEXT DEFAULT 'nuevo',
    respuesta TEXT
  )
")

# Guardar feedback
guardar_feedback <- function(usuario, pestaña, tipo, comentario) {
  dbExecute(con, "
    INSERT INTO feedback (fecha, usuario, pestaña, tipo, comentario)
    VALUES (?, ?, ?, ?, ?)
  ", params = list(
    as.character(Sys.time()),
    usuario,
    pestaña,
    tipo,
    comentario
  ))
}

# Leer feedback
leer_feedback <- function() {
  dbGetQuery(con, "SELECT * FROM feedback ORDER BY fecha DESC")
}

# En el server:
observeEvent(input$btn_enviar_feedback, {
  guardar_feedback(
    usuario = res_auth$user,
    pestaña = input$feedback_pestaña,
    tipo = input$feedback_tipo,
    comentario = input$feedback_texto
  )

  showNotification("✅ Feedback guardado", type = "message")
  removeModal()
})
```

---

## 📊 COMPARACIÓN DE OPCIONES

| Característica | Google Forms | Modal + Sheets | Con Login | Con BD |
|----------------|--------------|----------------|-----------|---------|
| **Dificultad** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Tiempo setup** | 10 min | 30 min | 1-2 hrs | 3-5 hrs |
| **Integrado** | ❌ | ✅ | ✅ | ✅ |
| **Control usuarios** | ❌ | ❌ | ✅ | ✅ |
| **Dashboard admin** | ❌ | ❌ | ❌ | ✅ |
| **Notificaciones** | ✅ (Google) | ⚠️ | ⚠️ | ✅ |
| **Exportar** | ✅ | ✅ | ✅ | ✅ |
| **Costo** | Gratis | Gratis | Gratis | Gratis/Pago |

---

## 🎯 MI RECOMENDACIÓN PARA TU CASO

### EMPEZAR CON: **Opción 2 - Modal + Google Sheets**

**¿Por qué?**
1. ✅ Integrado en la app (buena UX)
2. ✅ Fácil de implementar (30 minutos)
3. ✅ Gratis y escalable
4. ✅ No necesitas servidor de BD
5. ✅ Fácil de exportar y analizar

### MIGRAR A: **Opción 3 - Con Login** (cuando crezca)

Si necesitas:
- Controlar quién deja feedback
- Trazabilidad de usuarios
- Diferentes permisos

---

## 🚀 IMPLEMENTACIÓN RÁPIDA (15 MINUTOS)

### Versión Simplificada sin Google Sheets:

Si quieres algo **súper rápido** mientras configuras Google Sheets:

```r
# En el server:
observeEvent(input$btn_enviar_feedback, {

  # Guardar en archivo CSV local
  feedback_file <- "feedback_dashboard.csv"

  feedback_data <- data.frame(
    Fecha = Sys.time(),
    Pestaña = input$feedback_pestaña,
    Tipo = input$feedback_tipo,
    Comentario = input$feedback_texto
  )

  # Append a CSV
  write.table(
    feedback_data,
    file = feedback_file,
    append = file.exists(feedback_file),
    col.names = !file.exists(feedback_file),
    row.names = FALSE,
    sep = ","
  )

  showNotification("✅ Feedback guardado", type = "message")
  removeModal()
})
```

**Luego descargas el CSV desde el servidor.**

---

## 📧 BONUS: ENVIAR POR EMAIL

Si prefieres recibir feedback por email:

```r
# Instalar
install.packages("blastula")

library(blastula)

# Configurar SMTP (Gmail)
create_smtp_creds_key(
  id = "gmail",
  user = "tu-email@gmail.com",
  provider = "gmail"
)

# Enviar email con feedback
observeEvent(input$btn_enviar_feedback, {

  email <- compose_email(
    body = md(sprintf("
## Nuevo Feedback

**Pestaña:** %s
**Tipo:** %s
**Comentario:**
%s

---
*Enviado desde Dashboard OEDE*
    ",
    input$feedback_pestaña,
    input$feedback_tipo,
    input$feedback_texto
    ))
  )

  smtp_send(
    email,
    to = "tu-email@gmail.com",
    from = "dashboard@oede.com",
    subject = sprintf("[Dashboard] Feedback: %s", input$feedback_tipo),
    credentials = creds_key("gmail")
  )

  showNotification("✅ Feedback enviado", type = "message")
  removeModal()
})
```

---

## ✅ PRÓXIMOS PASOS

### Opción Recomendada (30 min):

1. **Crear Google Sheet** (5 min)
2. **Instalar googlesheets4** (2 min)
3. **Copiar código del modal** (10 min)
4. **Probar localmente** (5 min)
5. **Re-deployar a shinyapps.io** (5 min)

¿Quieres que implemente la Opción 2 (Modal + Google Sheets) en tu dashboard ahora mismo?
