# 💬 CÓDIGO PARA AGREGAR FEEDBACK SIMPLE (5 MINUTOS)

## ✅ Solución: Botón que abre Google Form

**Características:**
- Cualquier usuario puede dar feedback (sin login)
- Anónimo o con email opcional
- 100% gratis
- 5 minutos de setup

---

## PASO 1: Crear Google Form (3 minutos)

1. Ve a: **https://forms.google.com/**
2. Click en **"+"** (nuevo formulario)
3. Título: **"Feedback - Dashboard Ofertas Laborales"**
4. Descripción: **"Ayúdanos a mejorar el dashboard con tus comentarios"**

### Agrega estas preguntas:

**Pregunta 1: Email (opcional)**
- Tipo: `Respuesta corta`
- Texto: `Tu email (opcional si quieres que te respondamos)`
- ☑️ Marcar como "Opcional"

**Pregunta 2: Pestaña del dashboard**
- Tipo: `Opción múltiple`
- Texto: `¿Sobre qué pestaña del dashboard es tu feedback?`
- Opciones:
  ```
  - Resumen General
  - Análisis por Fuente
  - Tendencias
  - Mapa Geográfico
  - Análisis de Texto
  - Empresas
  - Temporalidad
  - Ubicación
  - Modalidad
  - Ocupaciones
  - Calidad de Datos
  - Datos Crudos
  - General / Toda la app
  ```

**Pregunta 3: Tipo de feedback**
- Tipo: `Opción múltiple`
- Texto: `¿Qué tipo de feedback es?`
- Opciones:
  ```
  - 💡 Sugerencia de mejora
  - 🐛 Reportar un error
  - 📊 Solicitud de nuevo análisis
  - ❓ Pregunta
  - 👍 Comentario positivo
  - 💬 Otro
  ```

**Pregunta 4: Comentario**
- Tipo: `Párrafo`
- Texto: `Cuéntanos tu sugerencia, error, o comentario`
- ☑️ Marcar como "Obligatorio"

5. Click en **"Enviar"** (botón morado arriba)
6. Click en el ícono de **enlace** 🔗
7. ☑️ Marcar "Acortar URL"
8. **Copiar el enlace** (algo como: `https://forms.gle/ABC123xyz`)

---

## PASO 2: Agregar Botón Flotante en Shiny (2 minutos)

### Opción A: Botón flotante en TODAS las pestañas (RECOMENDADO)

Agrega este CSS y el botón flotante en tu `app.R`:

```r
# ==========================================
# EN EL UI - Dentro de dashboardBody, ANTES de tabItems
# ==========================================

dashboardBody(

  # CSS para botón flotante
  tags$head(
    tags$style(HTML("
      .feedback-btn-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
      }

      .feedback-btn {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .feedback-btn:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
      }

      .feedback-btn i {
        margin-right: 8px;
      }
    "))
  ),

  # Botón flotante (visible en TODAS las pestañas)
  tags$div(
    class = "feedback-btn-container",
    tags$button(
      class = "feedback-btn",
      onclick = "window.open('https://forms.gle/TU_ENLACE_AQUI', '_blank')",
      HTML("<i class='fa fa-comment-dots'></i> Enviar Feedback")
    )
  ),

  # El resto de tu código (tabItems, etc.)
  tabItems(
    # ... tus pestañas existentes ...
  )
)
```

**Importante:** Reemplaza `'https://forms.gle/TU_ENLACE_AQUI'` con el enlace que copiaste del Google Form.

---

### Opción B: Botón en cada pestaña individual

Si prefieres un botón dentro de cada pestaña (no flotante), agrega esto al INICIO de cada `tabItem`:

```r
tabItem(tabName = "resumen",

  # Botón de feedback
  fluidRow(
    column(12,
      div(style = "text-align: right; margin-bottom: 10px;",
        actionButton(
          "btn_feedback_resumen",
          "💬 Enviar Feedback",
          icon = icon("comment-dots"),
          class = "btn-info btn-sm",
          onclick = "window.open('https://forms.gle/TU_ENLACE_AQUI', '_blank')"
        )
      )
    )
  ),

  # ... resto del contenido de la pestaña ...
)
```

---

## PASO 3: Ver Respuestas

### Ver en Google Forms:
1. Ve a tu formulario en https://forms.google.com/
2. Click en "Respuestas"
3. Verás un resumen y todas las respuestas individuales

### Exportar a Google Sheets:
1. En "Respuestas", click en el ícono de Google Sheets 📊
2. Se creará automáticamente una hoja con todas las respuestas
3. Cada nueva respuesta se agrega automáticamente

### Notificaciones por email:
1. En "Respuestas", click en ⋮ (tres puntos)
2. "Recibir notificaciones por correo electrónico para nuevas respuestas"
3. ✅ Activar
4. Recibirás un email cada vez que alguien envíe feedback

---

## 🎨 PERSONALIZACIÓN DEL BOTÓN

### Cambiar color del botón:

```css
.feedback-btn {
  background-color: #e74c3c;  /* Rojo */
  /* o */
  background-color: #27ae60;  /* Verde */
  /* o */
  background-color: #f39c12;  /* Naranja */
}
```

### Cambiar posición del botón flotante:

```css
.feedback-btn-container {
  bottom: 20px;    /* Distancia desde abajo */
  right: 20px;     /* Distancia desde la derecha */

  /* O si prefieres arriba a la derecha: */
  top: 80px;       /* Distancia desde arriba */
  right: 20px;

  /* O abajo a la izquierda: */
  bottom: 20px;
  left: 20px;
}
```

### Cambiar texto del botón:

```html
HTML("<i class='fa fa-comment-dots'></i> Sugerencias")
<!-- o -->
HTML("<i class='fa fa-comment-dots'></i> Dejanos tu opinión")
<!-- o -->
HTML("<i class='fa fa-comment-dots'></i> Feedback")
```

---

## 📊 EJEMPLO COMPLETO

### app.R con feedback integrado:

```r
library(shiny)
library(shinydashboard)
# ... tus otras librerías ...

ui <- dashboardPage(
  dashboardHeader(title = "Tablero de Ofertas Laborales"),

  dashboardSidebar(
    # ... tu sidebar ...
  ),

  dashboardBody(

    # ========================================
    # CSS PARA BOTÓN FLOTANTE
    # ========================================
    tags$head(
      tags$style(HTML("
        .feedback-btn-container {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 9999;
        }

        .feedback-btn {
          background-color: #3498db;
          color: white;
          border: none;
          border-radius: 50px;
          padding: 12px 24px;
          font-size: 16px;
          font-weight: bold;
          box-shadow: 0 4px 8px rgba(0,0,0,0.2);
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .feedback-btn:hover {
          background-color: #2980b9;
          transform: translateY(-2px);
          box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }

        .feedback-btn i {
          margin-right: 8px;
        }
      "))
    ),

    # ========================================
    # BOTÓN FLOTANTE DE FEEDBACK
    # ========================================
    tags$div(
      class = "feedback-btn-container",
      tags$button(
        class = "feedback-btn",
        onclick = "window.open('https://forms.gle/ABC123xyz', '_blank')",
        HTML("<i class='fa fa-comment-dots'></i> Enviar Feedback")
      )
    ),

    # ========================================
    # RESTO DE TU APP
    # ========================================
    tabItems(
      tabItem(tabName = "resumen",
        # ... tu contenido ...
      ),
      # ... más pestañas ...
    )
  )
)

server <- function(input, output, session) {
  # Tu código del server (sin cambios)
}

shinyApp(ui, server)
```

---

## ✅ VENTAJAS DE ESTA SOLUCIÓN

1. **Sin código complicado** - Solo CSS + botón HTML
2. **Sin dependencias** - No necesitas instalar paquetes extra
3. **Funciona offline** - Google Forms funciona siempre
4. **Gratis 100%** - Sin costos ocultos
5. **Anónimo opcional** - Usuarios deciden si dejar email
6. **Sin login** - Cualquiera puede dar feedback
7. **Notificaciones** - Recibes email con cada feedback
8. **Export fácil** - Descarga respuestas a Excel

---

## ❌ LIMITACIONES

1. Abre nueva ventana (no modal integrado)
2. Usuario sale del dashboard momentáneamente
3. No hay control de spam (pero Google Forms tiene captcha)

---

## 🎯 ALTERNATIVA: Modal Integrado (15 min más)

Si NO quieres que abra nueva ventana, puedo implementar un modal integrado que se abre DENTRO del dashboard. Esto requiere:
- Instalar `googlesheets4`
- Configurar Google Sheets API
- 15 minutos más de setup

Pero la experiencia es mucho mejor (no sale del dashboard).

---

## ¿QUÉ PREFIERES?

**OPCIÓN A:** Botón simple que abre Google Form (5 min - LO IMPLEMENTO AHORA)
**OPCIÓN B:** Modal integrado en el dashboard (30 min - más profesional)

Dime cuál prefieres y lo agrego a tu app 🚀
