# 📝 CREAR GOOGLE FORM CON PREGUNTAS GUIADAS

## PASO 1: Crear el Formulario

1. Ve a: **https://forms.google.com/**
2. Click en **"+"** (Formulario en blanco)
3. Título: **"Feedback - Dashboard Ofertas Laborales OEDE"**
4. Descripción:
   ```
   Tu opinión es muy valiosa para mejorar este dashboard.
   Por favor, tómate unos minutos para compartir tus sugerencias,
   reportar problemas, o solicitar nuevos análisis.
   ```

---

## PASO 2: Agregar Preguntas Guiadas

### ✅ PREGUNTA 1: Email (opcional)

**Tipo:** `Respuesta corta`
**Pregunta:** `Tu email (opcional)`
**Descripción:** `Si quieres que te respondamos o mantengamos contacto sobre tu sugerencia`
- ☐ Marcar como opcional (sin asterisco)

---

### ✅ PREGUNTA 2: Pestaña del Dashboard

**Tipo:** `Opción múltiple`
**Pregunta:** `¿Sobre qué sección del dashboard es tu feedback?`
**Descripción:** `Selecciona la pestaña o sección a la que te refieres`

**Opciones:**
```
○ 📊 Resumen General
○ 🔍 Análisis por Fuente
○ 📈 Tendencias
○ 🗺️ Mapa Geográfico
○ ☁️ Análisis de Texto
○ 🏢 Empresas
○ 📅 Temporalidad
○ 📍 Ubicación
○ 💼 Modalidad
○ 👔 Ocupaciones
○ ✅ Calidad de Datos
○ 📄 Datos Crudos
○ 🎨 Diseño General / Navegación
○ 💬 Otro / General
```

- ☑️ Obligatorio

---

### ✅ PREGUNTA 3: Tipo de Feedback

**Tipo:** `Opción múltiple`
**Pregunta:** `¿Qué tipo de feedback nos quieres dar?`
**Descripción:** `Selecciona la categoría que mejor describe tu comentario`

**Opciones:**
```
○ 💡 Sugerencia de mejora
○ 🐛 Reportar un error o problema
○ 📊 Solicitar nuevo análisis o visualización
○ 📉 Solicitar nuevos filtros o campos
○ ❓ Pregunta sobre cómo usar el dashboard
○ 🎨 Sugerencia de diseño o usabilidad
○ 📱 Problema de visualización (móvil/tablet)
○ ⚡ Problema de rendimiento (muy lento)
○ 👍 Comentario positivo / Reconocimiento
○ 💬 Otro
```

- ☑️ Obligatorio

---

### ✅ PREGUNTA 4: Preguntas Guiadas (Condicional)

**Tipo:** `Casillas de verificación`
**Pregunta:** `Para ayudarte mejor, ¿podrías decirnos más? (selecciona las que apliquen)`
**Descripción:** `Marca todas las opciones que describan tu situación`

**Opciones:**
```
☐ Me gustaría ver esta información de manera diferente
☐ Me gustaría agregar un nuevo tipo de análisis
☐ Hay datos que no se muestran correctamente
☐ Los filtros no funcionan como esperaba
☐ El dashboard es difícil de navegar
☐ Necesito exportar datos en otro formato
☐ Me gustaría comparar datos entre períodos
☐ Necesito más información sobre las empresas
☐ Me gustaría ver análisis por región más detallado
☐ Necesito análisis por ocupación más específico
☐ El dashboard es lento al cargar
☐ No encuentro la información que busco
☐ Otro (especificar en comentarios)
```

- ☐ Opcional

---

### ✅ PREGUNTA 5: Nivel de Prioridad

**Tipo:** `Escala lineal`
**Pregunta:** `¿Qué tan importante es esto para tu trabajo?`
**Descripción:** `1 = Poco importante | 5 = Muy importante / crítico`

**Configuración:**
- Mínimo: `1`
- Máximo: `5`
- Etiqueta 1: `Poco importante`
- Etiqueta 5: `Muy importante / Crítico`

- ☑️ Obligatorio

---

### ✅ PREGUNTA 6: Frecuencia de Uso

**Tipo:** `Opción múltiple`
**Pregunta:** `¿Con qué frecuencia usas el dashboard?`
**Descripción:** `Esto nos ayuda a priorizar mejoras`

**Opciones:**
```
○ Diariamente
○ Varias veces por semana
○ Semanalmente
○ Mensualmente
○ Es mi primera vez usándolo
○ Lo uso esporádicamente
```

- ☑️ Obligatorio

---

### ✅ PREGUNTA 7: Detalle del Feedback (PRINCIPAL)

**Tipo:** `Párrafo`
**Pregunta:** `Cuéntanos tu sugerencia, problema, o solicitud en detalle`
**Descripción:**
```
Por favor incluye:
• ¿Qué intentabas hacer?
• ¿Qué esperabas que pasara?
• ¿Qué pasó realmente? (si aplica)
• ¿Cómo te gustaría que funcionara?

Ejemplos:
- "Me gustaría ver un gráfico de tendencias por provincia"
- "El filtro de ciudad no muestra todas las opciones"
- "Sería útil poder exportar la tabla de empresas a Excel"
```

**Configuración:**
- Validación: `Respuesta larga`

- ☑️ Obligatorio

---

### ✅ PREGUNTA 8: ¿Cómo te ayudaría esto?

**Tipo:** `Párrafo`
**Pregunta:** `¿Cómo mejoraría tu trabajo si implementamos esto?`
**Descripción:** `Opcional: ayúdanos a entender el impacto de tu sugerencia`

**Ejemplos en descripción:**
```
Ejemplos:
- "Me permitiría identificar patrones por región más rápido"
- "Facilitaría crear reportes semanales para mi equipo"
- "Ayudaría a tomar mejores decisiones de contratación"
```

- ☐ Opcional

---

### ✅ PREGUNTA 9: ¿Qué tan satisfecho estás con el dashboard actual?

**Tipo:** `Escala lineal`
**Pregunta:** `En general, ¿qué tan satisfecho estás con el dashboard?`
**Descripción:** `1 = Muy insatisfecho | 5 = Muy satisfecho`

**Configuración:**
- Mínimo: `1`
- Máximo: `5`
- Etiqueta 1: `Muy insatisfecho`
- Etiqueta 5: `Muy satisfecho`

- ☑️ Obligatorio

---

### ✅ PREGUNTA 10: Captura de Pantalla (Opcional)

**Tipo:** `Subida de archivos`
**Pregunta:** `¿Tienes una captura de pantalla que ayude a explicar tu feedback?`
**Descripción:** `Opcional: sube una imagen si ayuda a explicar tu problema o sugerencia`

**Configuración:**
- Permitir subir solo: `Imágenes`
- Número máximo de archivos: `3`

- ☐ Opcional

---

## PASO 3: Configurar Respuestas

1. Click en **"Respuestas"** (arriba)
2. Click en el ícono de Google Sheets 📊
3. Se creará automáticamente una hoja de cálculo
4. Las respuestas se guardarán ahí en tiempo real

---

## PASO 4: Configurar Notificaciones

1. En "Respuestas", click en **⋮** (tres puntos)
2. **"Recibir notificaciones por correo electrónico para nuevas respuestas"**
3. ☑️ Activar
4. Recibirás email cada vez que alguien envíe feedback

---

## PASO 5: Personalizar Apariencia

1. Click en el ícono de **paleta de colores** 🎨 (arriba)
2. Selecciona:
   - **Color del tema:** Azul (o el color de OEDE)
   - **Imagen de encabezado:** (opcional) logo de OEDE
3. Click **Aceptar**

---

## PASO 6: Configurar Confirmación

1. Click en **Configuración** ⚙️ (arriba)
2. En "Presentación":
   - ☑️ Mostrar barra de progreso
   - ☑️ Barajar el orden de las preguntas: **NO**
3. En "Mensaje de confirmación", cambiar a:
   ```
   ¡Gracias por tu feedback!
   Tu opinión es muy valiosa y nos ayudará a mejorar el dashboard.
   Revisaremos tu comentario y te contactaremos si dejaste tu email.
   ```

---

## PASO 7: Obtener Enlace

1. Click en **"Enviar"** (botón morado, arriba derecha)
2. Click en el ícono de **enlace** 🔗
3. ☑️ Marcar **"Acortar URL"**
4. **COPIAR EL ENLACE**
   - Será algo como: `https://forms.gle/ABC123xyz`
5. **GUÁRDALO** - lo necesitarás en el siguiente paso

---

## PASO 8: Crear Vista de Análisis (BONUS)

En tu Google Sheet de respuestas, puedes crear:

### Hoja "Dashboard de Feedback":
```
=QUERY(Respuestas!A:K, "SELECT B, C, COUNT(C) WHERE B IS NOT NULL GROUP BY B, C")
```

Esto te mostrará:
- Cuántos feedbacks por pestaña
- Cuántos por tipo
- Más fácil de analizar

---

## 📊 ANÁLISIS DE RESPUESTAS

Google Forms automáticamente te da:
- **Resumen:** Gráficos de todas las respuestas
- **Individual:** Ver cada respuesta una por una
- **Sheets:** Todas las respuestas en tabla

### Ver estadísticas:
1. Click en "Respuestas"
2. Verás:
   - Total de respuestas
   - Gráficos por pregunta
   - Promedio de satisfacción
   - Tipos de feedback más comunes

---

## ✅ CHECKLIST

- [ ] Formulario creado
- [ ] 10 preguntas agregadas
- [ ] Google Sheet conectado
- [ ] Notificaciones activadas
- [ ] Apariencia personalizada
- [ ] Mensaje de confirmación configurado
- [ ] Enlace corto copiado
- [ ] ¡LISTO PARA USAR!

---

## 🔗 PRÓXIMO PASO

Una vez que tengas el enlace del formulario (ej: `https://forms.gle/ABC123xyz`),
dímelo y lo agregaré al código del dashboard.

**Tu enlace:** `_______________________` (complétalo cuando lo tengas)
