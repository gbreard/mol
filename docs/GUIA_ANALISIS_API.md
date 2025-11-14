# Guía de Análisis de API de ZonaJobs

## 🔍 Método 1: Inspección Manual con DevTools

### Paso 1: Abrir DevTools
1. Abre Chrome/Edge/Firefox
2. Ve a https://www.zonajobs.com.ar/
3. Presiona `F12` o `Ctrl+Shift+I` para abrir DevTools
4. Ve a la pestaña **Network** (Red)

### Paso 2: Capturar las Llamadas API
1. **Filtrar solicitudes**:
   - Haz clic en el filtro "XHR" o "Fetch/XHR"
   - Esto filtra solo las llamadas AJAX/API

2. **Recargar la página**:
   - Presiona `Ctrl+R` con DevTools abierto
   - Observa las solicitudes que aparecen

3. **Interactuar con el sitio**:
   - Haz una búsqueda de empleos
   - Cambia de página
   - Aplica filtros
   - Observa qué nuevas llamadas aparecen

### Paso 3: Analizar las Llamadas
Para cada llamada API importante:

**Headers:**
```
- Request URL: La URL del endpoint
- Request Method: GET, POST, etc.
- Authorization: ¿Requiere token?
- Content-Type: application/json, etc.
```

**Payload (si es POST):**
- Haz clic derecho > Copy > Copy as fetch
- Guarda el JSON del body

**Response:**
- Ve a la pestaña "Response"
- Copia el JSON de respuesta
- Analiza la estructura de datos

### Paso 4: Endpoints Comunes a Buscar

```
✓ /api/jobs/search
✓ /api/v1/jobs
✓ /api/search
✓ /api/offers
✓ /graphql (si usan GraphQL)
✓ /api/listings
```

---

## 🐍 Método 2: Interceptar con Selenium

### Instalación
```bash
pip install selenium
pip install selenium-wire  # Para interceptar requests
pip install webdriver-manager
```

### Script de Interceptación
Ver: `intercept_api_calls.py`

---

## 🎭 Método 3: Usar Playwright con Network Interception

### Instalación
```bash
pip install playwright
playwright install chromium
```

### Script de Interceptación
Ver: `playwright_intercept.py`

---

## 📋 Información a Recopilar

### 1. Endpoint de Búsqueda
- **URL completa**
- **Parámetros de query**: ?q=python&location=buenos+aires&page=1
- **Headers requeridos**
- **Método**: GET/POST

### 2. Estructura de Respuesta
```json
{
  "jobs": [...],
  "total": 1234,
  "page": 1,
  "per_page": 20
}
```

### 3. Paginación
- ¿Usa offset/limit?
- ¿Usa page numbers?
- ¿Scroll infinito?

### 4. Rate Limiting
- ¿Cuántas requests puedes hacer?
- ¿Necesitas delays?
- ¿Requiere autenticación?

### 5. Datos de Cada Oferta
- ID del trabajo
- Título
- Empresa
- Ubicación
- Salario (si está disponible)
- Descripción
- Fecha de publicación
- URL del detalle

---

## ⚠️ Consideraciones Legales

1. **Lee los Términos de Servicio**: https://www.zonajobs.com.ar/terminos-y-condiciones
2. **Respeta robots.txt**: https://www.zonajobs.com.ar/robots.txt
3. **Implementa rate limiting**: No sobrecargues el servidor
4. **Identifícate**: Usa un User-Agent descriptivo
5. **Uso ético**: Solo para investigación/análisis personal

---

## 📊 Próximos Pasos

1. ✅ Ejecutar uno de los scripts de interceptación
2. ✅ Documentar los endpoints encontrados
3. ✅ Analizar la estructura de datos
4. ✅ Crear scraper basado en la API
5. ✅ Implementar almacenamiento de datos
6. ✅ Programar ejecución periódica (si aplica)
