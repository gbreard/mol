# ✅ SISTEMA DE FEEDBACK - PRÓXIMOS PASOS

## 🎉 ¡YA ESTÁ CASI LISTO!

He agregado el **botón flotante de feedback** a tu dashboard. Ahora solo necesitas:

1. Crear el Google Form (10 minutos)
2. Pegar el enlace en el código
3. Re-deployar a shinyapps.io

---

## 📋 PASO 1: CREAR GOOGLE FORM (10 minutos)

### Sigue las instrucciones detalladas en:
📄 **`INSTRUCCIONES_GOOGLE_FORM.md`**

### Resumen rápido:
1. Ve a https://forms.google.com/
2. Crea nuevo formulario
3. Agrega las **10 preguntas guiadas** del documento
4. Conecta con Google Sheets
5. Activa notificaciones por email
6. **COPIA EL ENLACE CORTO** (ej: `https://forms.gle/ABC123xyz`)

---

## 📋 PASO 2: ACTUALIZAR EL ENLACE EN EL CÓDIGO (1 minuto)

Una vez que tengas tu enlace del Google Form:

### Abre el archivo `app.R`

Busca esta línea (línea 165 aproximadamente):

```r
onclick = "window.open('AQUI_VA_TU_ENLACE_DE_GOOGLE_FORM', '_blank')",
```

### Reemplaza con tu enlace:

```r
onclick = "window.open('https://forms.gle/TU_ENLACE_REAL', '_blank')",
```

**Ejemplo:**
```r
onclick = "window.open('https://forms.gle/ABC123xyz', '_blank')",
```

---

## 📋 PASO 3: PROBAR LOCALMENTE (1 minuto)

Antes de deployar, prueba que funciona:

```r
# En R o RStudio:
shiny::runApp("C:/Users/gbrea/OneDrive/Documentos/OEDE/Webscrapping")
```

1. Abre el dashboard
2. Verás el botón flotante **"💬 Enviar Feedback"** abajo a la derecha
3. Tiene animación de "pulso" para llamar la atención
4. Click en el botón → debe abrir tu Google Form
5. **Si funciona, continúa al Paso 4**

---

## 📋 PASO 4: RE-DEPLOYAR A SHINYAPPS.IO (2 minutos)

### Opción A: Desde R/RStudio

```r
# Configurar cuenta (si no lo has hecho)
rsconnect::setAccountInfo(
  name='dos1tv-gerardo-breard',
  token='45DB90EA461FAD11B32AEBEE28454644',
  secret='/qJ1pA35CIQRQeosn7x4LalIWPVxMjQAh+gEzmBd'
)

# Deployar actualización
setwd("C:/Users/gbrea/OneDrive/Documentos/OEDE/Webscrapping")
rsconnect::deployApp(
  appName = "ofertas-dashboard",
  forceUpdate = TRUE
)
```

### Opción B: Usar el script que creé

```r
source("C:/Users/gbrea/OneDrive/Documentos/OEDE/Webscrapping/configurar_y_deployar.R")
```

---

## 🎨 CÓMO SE VERÁ

### El botón flotante:
- 📍 **Ubicación:** Abajo a la derecha (fixed)
- 🎨 **Estilo:** Gradiente morado elegante
- ✨ **Animación:** Pulso suave para llamar la atención
- 💬 **Texto:** "Enviar Feedback" con ícono de comentario
- 🖱️ **Hover:** Se eleva y cambia de color
- 👁️ **Visible:** En TODAS las pestañas del dashboard

### Cuando el usuario hace click:
1. Se abre el Google Form en **nueva pestaña**
2. El usuario ve las **10 preguntas guiadas**
3. Completa el formulario (2-3 minutos)
4. Click "Enviar"
5. Ve mensaje de agradecimiento
6. **La respuesta llega a tu Google Sheet** automáticamente
7. **Recibes notificación por email** (si la activaste)

---

## 📊 LAS 10 PREGUNTAS GUIADAS INCLUYEN:

1. ✉️ **Email (opcional)** - Para contacto
2. 📊 **Pestaña del dashboard** - Identificar sección
3. 🏷️ **Tipo de feedback** - Categorizar (sugerencia/error/análisis/etc)
4. ☑️ **Preguntas específicas guiadas** - Casillas con opciones comunes
5. ⭐ **Nivel de prioridad** - Escala 1-5
6. 📅 **Frecuencia de uso** - Entender audiencia
7. 📝 **Detalle del feedback** - Comentario principal con guía
8. 💼 **Impacto en el trabajo** - Cómo les ayudaría
9. 😊 **Nivel de satisfacción** - Escala 1-5
10. 📸 **Captura de pantalla (opcional)** - Para mostrar errores

### ¿Por qué tantas preguntas?

Las preguntas guiadas ayudan al usuario a:
- ✅ Estructurar mejor su feedback
- ✅ No olvidar detalles importantes
- ✅ Clasificar automáticamente su comentario
- ✅ Priorizar qué tan crítico es

Y a ti te ayudan a:
- ✅ Entender mejor el contexto
- ✅ Priorizar qué implementar primero
- ✅ Medir satisfacción general
- ✅ Identificar patrones (ej: todos reportan el mismo error)

---

## 📈 ANALIZAR FEEDBACK RECIBIDO

### Ver resumen en Google Forms:
1. Abre tu formulario en https://forms.google.com/
2. Click en "Respuestas"
3. Verás:
   - **Total de respuestas**
   - **Gráficos** por cada pregunta
   - **Promedios** de satisfacción y prioridad
   - **Nube de palabras** de comentarios (si hay muchas)

### Ver detalle en Google Sheets:
1. Click en el ícono de Google Sheets 📊 (en "Respuestas")
2. Verás tabla con TODAS las respuestas
3. Puedes:
   - **Filtrar** por tipo de feedback
   - **Ordenar** por prioridad
   - **Exportar** a Excel
   - **Crear gráficos** personalizados
   - **Responder** directamente a usuarios (si dejaron email)

### Crear Dashboard de Feedback (BONUS):

En Google Sheets, agrega una hoja nueva llamada "Dashboard":

```
=QUERY('Respuestas del formulario 1'!A:K,
  "SELECT C, COUNT(C)
   WHERE C IS NOT NULL
   GROUP BY C
   ORDER BY COUNT(C) DESC
   LABEL COUNT(C) 'Cantidad'")
```

Esto te mostrará cuántos feedbacks hay por **tipo**.

---

## 🔔 NOTIFICACIONES POR EMAIL

Si activaste las notificaciones, recibirás emails como:

```
De: Google Forms <no-reply@google.com>
Asunto: Respuesta nueva en "Feedback - Dashboard Ofertas Laborales OEDE"

Nueva respuesta en tu formulario:

Email: usuario@ejemplo.com
Pestaña: Tendencias
Tipo: Sugerencia de mejora
Prioridad: 5
Comentario: Me gustaría ver tendencias por provincia...

Ver respuesta completa: [enlace]
```

---

## 💡 TIPS PARA GESTIONAR FEEDBACK

### 1. Revisa semanalmente:
- Dedica 15 minutos cada viernes
- Lee todos los nuevos feedbacks
- Marca como "Revisado" (agrega columna en Sheets)

### 2. Prioriza por:
- **Frecuencia:** ¿Varios usuarios piden lo mismo?
- **Prioridad:** ¿El usuario marcó 4-5?
- **Impacto:** ¿Mejorará el trabajo de muchos?
- **Complejidad:** ¿Fácil o difícil de implementar?

### 3. Responde a usuarios:
Si alguien dejó email y su feedback es importante:
```
Hola [Nombre],

Gracias por tu feedback sobre [tema].
Lo hemos revisado y [planeamos implementarlo / está en la lista / necesitamos más info].

Saludos,
Equipo OEDE
```

### 4. Comparte mejoras:
Cuando implementes una sugerencia, avisa:
- En la próxima actualización del dashboard
- Agrega nota: "Gracias a [usuario] por sugerir esta mejora"
- Genera engagement y más feedback

---

## 🎯 MÉTRICAS A SEGUIR

### Mensuales:
- Total de feedbacks recibidos
- % por tipo (sugerencia/error/análisis/etc)
- Promedio de satisfacción (1-5)
- Promedio de prioridad de sugerencias
- Tasa de respuesta (cuántos respondiste)

### KPIs importantes:
- **Tasa de feedback:** feedbacks / usuarios únicos
- **Tasa de implementación:** sugerencias implementadas / total sugerencias
- **Tiempo promedio de respuesta:** días hasta responder
- **Incremento de satisfacción:** comparar promedios mes a mes

---

## 🚀 MEJORAS FUTURAS (OPCIONAL)

Si el sistema funciona bien y quieres mejorarlo:

### 1. Modal integrado (30 min):
- No abre nueva ventana
- Formulario dentro del dashboard
- Mejor experiencia de usuario
- Requiere `googlesheets4` y Google Sheets API

### 2. Sistema de login (1-2 hrs):
- Solo usuarios autorizados
- Captura automática de quién envía
- Control de permisos

### 3. Dashboard de gestión (3-5 hrs):
- Pestaña "Admin" en el dashboard
- Ver/responder feedback directamente
- Cambiar estados (nuevo/revisado/implementado/cerrado)
- Base de datos propia

---

## ✅ CHECKLIST FINAL

Antes de considerar el sistema completo:

- [ ] Google Form creado con 10 preguntas
- [ ] Google Sheet conectado
- [ ] Notificaciones por email activadas
- [ ] Enlace del form copiado
- [ ] Enlace pegado en `app.R` (línea 165)
- [ ] Probado localmente (botón funciona)
- [ ] Re-deployado a shinyapps.io
- [ ] Probado en producción
- [ ] Feedback de prueba enviado
- [ ] Recibida notificación por email
- [ ] Respuesta visible en Google Sheets
- [ ] ¡Sistema funcionando! 🎉

---

## 🆘 PROBLEMAS COMUNES

### El botón no aparece:
- Verifica que `app.R` tenga el código actualizado
- Busca errores en la consola de R
- Asegúrate de que re-deployaste

### El botón aparece pero no abre nada:
- Verifica que pusiste el enlace correcto del Google Form
- El enlace debe empezar con `https://forms.gle/` o `https://docs.google.com/forms/`

### El formulario se abre pero no guarda respuestas:
- Verifica que el formulario esté "Aceptando respuestas"
- En Google Forms → Configuración → Aceptar respuestas (debe estar ON)

### No recibo notificaciones por email:
- Verifica en Respuestas → ⋮ → Recibir notificaciones (debe estar ON)
- Revisa tu carpeta de spam

---

## 📞 CONTACTO

Si tienes problemas o dudas:
1. Revisa este documento
2. Revisa `INSTRUCCIONES_GOOGLE_FORM.md`
3. Revisa `SISTEMA_FEEDBACK_SHINY.md` (guía completa)

---

## 🎉 ¡PRÓXIMO PASO!

**Crea el Google Form ahora mismo** siguiendo:
📄 **`INSTRUCCIONES_GOOGLE_FORM.md`**

Luego avísame y te ayudo a actualizar el enlace y re-deployar 🚀
