# 🕵️ Web Scraping de ZonaJobs - Análisis y Extracción de Datos

Este proyecto contiene herramientas para analizar y extraer datos de ZonaJobs.com.ar mediante diferentes técnicas de web scraping.

## 📋 Contenido

- **GUIA_ANALISIS_API.md**: Guía completa para analizar e identificar endpoints API
- **intercept_api_calls.py**: Script con Selenium Wire para interceptar llamadas API
- **playwright_intercept.py**: Script con Playwright para interceptar llamadas API (recomendado)
- **requirements.txt**: Dependencias del proyecto

## 🚀 Instalación

### 1. Crear entorno virtual (recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# Si usas Playwright, instalar navegadores
playwright install chromium
```

## 📖 Uso

### Opción 1: Usar Playwright (Recomendado)

Playwright es más moderno, rápido y estable que Selenium.

```bash
python playwright_intercept.py
```

**Características:**
- ✅ Más rápido y eficiente
- ✅ Mejor manejo de SPA
- ✅ API más limpia
- ✅ Menos propenso a detección

### Opción 2: Usar Selenium Wire

```bash
python intercept_api_calls.py
```

**Características:**
- ✅ Más familiar si ya conoces Selenium
- ✅ Amplia documentación
- ⚠️  Requiere ChromeDriver

## 🎯 Flujo de Trabajo

### Paso 1: Interceptar Llamadas API

```bash
# Ejecutar uno de los scripts
python playwright_intercept.py
```

El script:
1. Abrirá un navegador Chrome
2. Navegará a ZonaJobs
3. Capturará todas las llamadas API
4. Guardará los resultados en JSON

### Paso 2: Analizar Resultados

Los resultados se guardan en:
- `api_calls_playwright.json`: Todas las llamadas capturadas
- `api_endpoints_summary.json`: Resumen de endpoints únicos

Revisa estos archivos para identificar:
- URLs de endpoints
- Parámetros requeridos
- Estructura de respuestas
- Headers necesarios

### Paso 3: Crear Scraper Personalizado

Una vez identificados los endpoints, puedes crear un scraper que:
1. Haga requests directas a la API (más rápido)
2. O use Selenium/Playwright si es necesario

## 📊 Estructura de Datos Capturados

Cada llamada API capturada contiene:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "method": "GET",
  "url": "https://api.zonajobs.com.ar/...",
  "status": 200,
  "headers": {...},
  "request_headers": {...},
  "post_data": null,
  "response_body": {...}
}
```

## 🔧 Configuración Avanzada

### Modo Headless

Para ejecutar sin interfaz gráfica (más rápido):

```python
# En playwright_intercept.py, línea ~250:
interceptor.setup_browser(headless=True)
```

### Cambiar User Agent

```python
# En playwright_intercept.py, editar la configuración del context
user_agent='Tu User Agent personalizado'
```

### Aumentar Tiempo de Espera

```python
# En cualquier script, modificar el parámetro wait_time:
interceptor.navigate_and_capture(url, wait_time=15)
```

## ⚖️ Consideraciones Legales y Éticas

### ⚠️ IMPORTANTE

Antes de ejecutar cualquier script, asegúrate de:

1. **Leer los Términos de Servicio**
   - URL: https://www.zonajobs.com.ar/terminos-y-condiciones
   - Verifica que el scraping esté permitido

2. **Revisar robots.txt**
   - URL: https://www.zonajobs.com.ar/robots.txt
   - Respeta las directivas establecidas

3. **Implementar Rate Limiting**
   ```python
   import time
   time.sleep(2)  # Esperar entre requests
   ```

4. **Identificarte correctamente**
   - Usa un User-Agent descriptivo
   - Incluye información de contacto si es posible

5. **Uso responsable**
   - No sobrecargues el servidor
   - No extraigas datos personales sensibles
   - Usa los datos solo para propósitos legítimos

## 🛠️ Solución de Problemas

### Error: "chromedriver not found"

```bash
# Reinstalar webdriver-manager
pip install --upgrade webdriver-manager
```

### Error: "playwright not installed"

```bash
# Instalar Playwright y navegadores
pip install playwright
playwright install chromium
```

### No se capturan llamadas API

1. Aumenta el `wait_time`
2. Verifica que el sitio no esté bloqueando bots
3. Revisa la consola del navegador para errores

### El navegador se cierra muy rápido

En el script, busca la línea:
```python
interceptor.close()
```

Y añade antes:
```python
input("Presiona Enter para cerrar...")
```

## 📈 Próximos Pasos

Una vez que hayas identificado los endpoints:

1. **Crear scraper de producción**
   - Hacer requests directas a la API
   - Implementar manejo de errores
   - Agregar logging

2. **Almacenar datos**
   - Base de datos (PostgreSQL, MongoDB)
   - Archivos CSV/Excel
   - Data warehouse

3. **Automatizar**
   - Cron jobs (Linux)
   - Task Scheduler (Windows)
   - Airflow para workflows complejos

4. **Análisis de datos**
   - Pandas para procesamiento
   - Matplotlib/Seaborn para visualización
   - Power BI/Tableau para dashboards

## 📞 Soporte

Para más información:
- Lee la **GUIA_ANALISIS_API.md**
- Revisa los comentarios en los scripts
- Consulta la documentación de [Playwright](https://playwright.dev/python/) o [Selenium](https://selenium-python.readthedocs.io/)

## 📝 Licencia

Este código es para propósitos educativos y de investigación.
Asegúrate de cumplir con las leyes y términos de servicio aplicables.

---

**Última actualización**: 2024
**Versión**: 1.0
