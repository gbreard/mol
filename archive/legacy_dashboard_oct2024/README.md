# Dashboard de Ofertas Laborales Scrapeadas 📊

Dashboard interactivo desarrollado en Shiny (R) para visualizar y analizar ofertas laborales scrapeadas de diversas fuentes.

## 📋 Características

### ✅ **Mejoras Implementadas**

- ✅ **Datos Reales**: Conectado a `ofertas_consolidadas.xlsx` (1,156 ofertas)
- ✅ **Seguridad**: Credenciales removidas del código
- ✅ **Encoding Correcto**: Soporte completo para caracteres especiales (español)
- ✅ **Manejo de Errores**: Validaciones y notificaciones de errores
- ✅ **Filtros Interactivos**:
  - Rango de fechas
  - Provincia
  - Modalidad de trabajo
- ✅ **Exportación**: Descarga de datos en CSV
- ✅ **Nueva Pestaña**: Vista de datos crudos completos

### 📊 **Análisis Disponibles**

1. **Resumen General**
   - Total de vacantes, empresas, provincias y ocupaciones
   - Evolución temporal de ofertas
   - Top 10 empresas
   - Distribución geográfica
   - Distribución por modalidad (presencial/remoto/híbrido)

2. **Análisis por Empresas**
   - Top 20 empresas con más vacantes
   - Tabla completa filtrable

3. **Análisis Temporal**
   - Evolución de vacantes por fecha
   - Gráfico de área con tendencias

4. **Análisis Geográfico**
   - Distribución por provincia
   - Top 20 provincias

5. **Modalidad de Trabajo**
   - Distribución presencial vs remoto vs híbrido

6. **Ocupaciones**
   - Top 20 ocupaciones más demandadas
   - Tabla completa de ocupaciones

7. **Datos Crudos**
   - Acceso completo a la base de datos
   - Exportación a CSV

## 🚀 Instalación

### Requisitos Previos

1. **R** (versión 4.0 o superior)
2. **RStudio** (opcional, pero recomendado)

### Instalar Paquetes Necesarios

Abre R o RStudio y ejecuta:

```r
install.packages(c(
  "shiny",
  "shinydashboard",
  "readxl",
  "dplyr",
  "ggplot2",
  "plotly",
  "lubridate",
  "DT"
))
```

## ▶️ Ejecutar la Aplicación

### Opción 1: Desde RStudio

1. Abre el archivo `app.R` en RStudio
2. Haz click en el botón **"Run App"** en la esquina superior derecha

### Opción 2: Desde la Consola de R

```r
shiny::runApp("ruta/al/directorio/Webscrapping")
```

### Opción 3: Desde Terminal/CMD

```bash
cd "C:\Users\gbrea\OneDrive\Documentos\OEDE\Webscrapping"
Rscript -e "shiny::runApp('app.R')"
```

## 📁 Estructura de Archivos

```
Webscrapping/
├── app.R                          # Aplicación principal (NUEVO - MEJORADO)
├── ofertas_consolidadas.xlsx      # Base de datos con 1,156 ofertas
├── deepseek_r_20251022_10594a.r  # Versión antigua (con datos hardcoded)
└── README.md                      # Este archivo
```

## 🎨 Uso del Dashboard

### Filtros Globales

En el panel lateral izquierdo encontrarás:

- **Rango de Fechas**: Selecciona el período a analizar
- **Provincia**: Filtra por ubicación geográfica
- **Modalidad**: Filtra por tipo de trabajo (presencial/remoto/híbrido)
- **Botón "Aplicar Filtros"**: Actualiza todos los gráficos con los filtros seleccionados

### Navegación

Usa el menú lateral para navegar entre las diferentes pestañas de análisis.

### Exportación de Datos

En la pestaña **"Datos Crudos"**:
- Click en **"Descargar Excel"** para exportar los datos filtrados a CSV

## 🔧 Configuración para Deployment

### ShinyApps.io (Recomendado)

1. Instala el paquete rsconnect:
```r
install.packages('rsconnect')
```

2. Configura tu cuenta (crea una gratis en https://www.shinyapps.io):
```r
rsconnect::setAccountInfo(
  name="tu-usuario",
  token="TU-TOKEN-AQUI",
  secret="TU-SECRET-AQUI"
)
```

3. Despliega la aplicación:
```r
rsconnect::deployApp(
  appDir = "C:/Users/gbrea/OneDrive/Documentos/OEDE/Webscrapping",
  appName = "dashboard-ofertas-laborales"
)
```

### Shiny Server (Auto-hospedado)

1. Instala Shiny Server en tu servidor
2. Copia los archivos a `/srv/shiny-server/`
3. Accede vía `http://tu-servidor:3838/`

## 📈 Datos

### Fuente de Datos

- **Archivo**: `ofertas_consolidadas.xlsx`
- **Hoja principal**: `BASE` (1,156 registros, 91 columnas)
- **Fuentes de scraping**: Bumeran y otras plataformas

### Campos Principales

- `_metadata.source`: Fuente de la oferta
- `Periodo`: Fecha de publicación
- `informacion_basica.titulo_normalizado`: Título de la ocupación
- `informacion_basica.ubicacion.provincia`: Provincia
- `informacion_basica.modalidad`: Modalidad de trabajo

## 🐛 Troubleshooting

### Error: "No se encuentra el archivo Excel"

Asegúrate de que `ofertas_consolidadas.xlsx` está en el mismo directorio que `app.R`

### Error: "Paquete no encontrado"

Instala los paquetes faltantes con:
```r
install.packages("nombre_del_paquete")
```

### Problemas con Encoding

El dashboard usa UTF-8. Si ves caracteres raros:
1. Asegúrate de que tu sesión de R use UTF-8
2. En Windows, ejecuta: `Sys.setlocale("LC_ALL", "Spanish")`

## 🔄 Diferencias con Versión Anterior

| Aspecto | Versión Anterior | Nueva Versión |
|---------|------------------|---------------|
| Datos | Hardcoded (falsos) | Lee Excel real |
| Seguridad | Credenciales expuestas | Sin credenciales |
| Encoding | Caracteres rotos | UTF-8 correcto |
| Errores | Sin manejo | Validaciones completas |
| Filtros | No disponibles | Interactivos |
| Exportación | No disponible | CSV download |
| Datos crudos | No accesibles | Pestaña completa |

## 📝 Próximas Mejoras Sugeridas

- [ ] Agregar análisis de salarios (si hay datos)
- [ ] Gráficos de correlación entre variables
- [ ] Análisis de texto en descripciones de ofertas
- [ ] Mapa interactivo de Argentina con ofertas por región
- [ ] Comparativa temporal (mes a mes)
- [ ] Dashboard de KPIs con métricas de rendimiento del scraper
- [ ] Alertas automáticas para nuevas ofertas matching criterios
- [ ] Integración con base de datos SQL para mejor performance

## 👨‍💻 Autor

Desarrollado para OEDE (Observatorio de Empleo y Dinámica Empresarial)

## 📄 Licencia

Uso interno OEDE

---

**Última actualización**: Octubre 2025
**Versión**: 2.0 (Mejorada)
