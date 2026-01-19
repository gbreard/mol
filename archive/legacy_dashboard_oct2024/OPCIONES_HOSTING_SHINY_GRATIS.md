# 🚀 OPCIONES DE HOSTING GRATUITO PARA SHINY APPS (2025)

Comparativa completa de servidores gratuitos donde puedes subir tu dashboard de Shiny.

---

## 📊 COMPARATIVA RÁPIDA

| Plataforma | Dificultad | Apps Gratis | Horas/Mes | RAM | Desventajas | Recomendación |
|------------|------------|-------------|-----------|-----|-------------|---------------|
| **shinyapps.io** | ⭐ Muy Fácil | 5 apps | 25h totales | 1 GB | Horas limitadas | ✅ **MEJOR PARA EMPEZAR** |
| **Hugging Face Spaces** | ⭐⭐ Fácil | Ilimitado | Ilimitadas | 16 GB | Requiere Git | ✅ **MÁS RECURSOS** |
| **Render.com** | ⭐⭐⭐ Media | Ilimitado | 750h/app | 512 MB | Duerme tras 15min | ⚠️ Requiere Docker |
| **Shiny Server** | ⭐⭐⭐⭐ Difícil | Ilimitado | Ilimitadas | Tu server | Necesitas server | ❌ Solo si tienes VPS |

---

## 1️⃣ shinyapps.io (RECOMENDADO PARA PRINCIPIANTES)

**🏢 Proveedor:** Posit (antes RStudio) - la empresa creadora de Shiny
**🌐 Web:** https://www.shinyapps.io/
**💰 Precio:** GRATIS (con limitaciones)

### ✅ Ventajas
- **Súper fácil de usar** - Deploy con 1 comando desde RStudio
- **Oficial** - Mantenido por los creadores de Shiny
- **No requiere servidor** - Todo en la nube
- **SSL gratis** - HTTPS incluido
- **Sin configuración** - Funciona out-of-the-box

### ❌ Desventajas
- **Solo 25 horas/mes TOTALES** entre todas tus apps
- **Máximo 5 aplicaciones**
- **1 GB de RAM** por app
- **1 GB límite de upload**
- Si tus apps son populares, se quedan sin horas rápido

### 📦 Plan Gratuito Incluye:
- 5 aplicaciones
- 25 horas activas/mes (compartidas entre todas)
- 1 GB RAM por app
- 1 GB tamaño máximo de deploy
- Subdominio: `tu-usuario.shinyapps.io`

### 🚀 Cómo Deployar

```r
# 1. Instalar paquete
install.packages("rsconnect")

# 2. Configurar cuenta (obtén token en shinyapps.io)
rsconnect::setAccountInfo(
  name = "tu-usuario",
  token = "TU_TOKEN",
  secret = "TU_SECRET"
)

# 3. Deployar app (desde el directorio de tu app)
rsconnect::deployApp(appName = "ofertas-dashboard")
```

### 💡 Tips para Aprovechar Mejor las 25 Horas:
1. **Pon la app en "sleep"** cuando no la uses
2. **Usa archivos .RData** pre-procesados en vez de cargar Excel cada vez
3. **Implementa caché** con `memoise` para cálculos pesados
4. **Cierra apps de prueba** que ya no uses

### 🎯 Ideal Para:
- ✅ Prototipos y demos
- ✅ Apps de uso interno (pocas personas)
- ✅ Comenzar rápido sin complicaciones
- ✅ Tu caso: dashboard de 1,156 ofertas laborales

---

## 2️⃣ Hugging Face Spaces (MÁS RECURSOS GRATIS)

**🏢 Proveedor:** Hugging Face
**🌐 Web:** https://huggingface.co/spaces
**💰 Precio:** GRATIS (plan básico)

### ✅ Ventajas
- **16 GB de RAM** - ¡16x más que shinyapps.io!
- **2 CPU cores**
- **50 GB de disco**
- **Sin límite de horas** - App 24/7 online
- **Apps ilimitadas**
- **Integración con Git** - Deploy vía GitHub
- **Comunidad ML** - Ideal si tu app usa modelos de IA

### ❌ Desventajas
- **Más complejo** - Requiere crear Dockerfile
- **No tan directo** como shinyapps.io
- **Puede dormir** si no tiene tráfico (pero se despierta rápido)
- **Requiere cuenta GitHub/GitLab**

### 📦 Plan Gratuito Incluye:
- CPU: 2 vCPUs
- RAM: 16 GB
- Disco: 50 GB
- Ancho de banda: Razonable
- Subdominio: `huggingface.co/spaces/tu-usuario/app-nombre`

### 🚀 Cómo Deployar

**Opción 1: Usar Template de Posit**

1. Ve a https://huggingface.co/spaces/posit/shiny-for-r-template
2. Click en "Use this template"
3. Nombre tu Space
4. Sube tu `app.R` y archivos
5. El template ya tiene todo configurado

**Opción 2: Desde Cero**

Crea estos archivos en tu repo:

**`Dockerfile`:**
```dockerfile
FROM rocker/shiny-verse:latest

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libcurl4-gnutls-dev \
    libssl-dev

# Instalar paquetes R
RUN R -e "install.packages(c('shinydashboard', 'plotly', 'DT', 'readxl', 'dplyr', 'ggplot2', 'lubridate', 'leaflet', 'tidytext', 'wordcloud2', 'tm', 'openxlsx', 'zoo', 'scales'))"

# Copiar app
COPY app.R /srv/shiny-server/app.R
COPY ofertas_consolidadas.xlsx /srv/shiny-server/ofertas_consolidadas.xlsx

# Exponer puerto
EXPOSE 3838

# Comando de inicio
CMD ["R", "-e", "shiny::runApp('/srv/shiny-server/app.R', host='0.0.0.0', port=3838)"]
```

**`README.md`:**
```markdown
---
title: Dashboard Ofertas Laborales
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 3838
---

Dashboard de análisis de ofertas laborales scrapeadas
```

### 🎯 Ideal Para:
- ✅ Apps que necesitan más RAM
- ✅ Apps con tráfico constante
- ✅ Si ya usas GitHub
- ✅ Apps con procesamiento ML/AI
- ✅ **Tu dashboard SI procesas muchos datos**

---

## 3️⃣ Render.com (OPCIÓN DOCKER)

**🏢 Proveedor:** Render
**🌐 Web:** https://render.com/
**💰 Precio:** GRATIS (con auto-sleep)

### ✅ Ventajas
- **750 horas/mes por app** (31 días completos)
- **Apps ilimitadas** (cada una con 750h)
- **Deploy vía Git** - Push automático
- **Soporta Docker** - Muy flexible
- **512 MB RAM** (más que shinyapps.io)

### ❌ Desventajas
- **Duerme tras 15 min de inactividad** 🔴
- **Cold start de ~25 segundos** al despertar
- **Requiere Dockerfile** - Más técnico
- **Requiere tarjeta de crédito** para verificación (no cobra)

### 📦 Plan Gratuito Incluye:
- 750 horas/mes por servicio
- 512 MB RAM
- 100 GB ancho de banda/mes
- Auto-sleep tras 15 min inactividad
- Subdominio: `tu-app.onrender.com`

### 🚀 Cómo Deployar

1. **Crear Dockerfile** (similar al de Hugging Face)
2. **Subir a GitHub**
3. **En Render:**
   - New > Web Service
   - Conectar repo GitHub
   - Environment: Docker
   - Deploy

**Truco para evitar el sleep:**
Usa un servicio como **UptimeRobot** (gratis) para hacer ping cada 10 min:
```
https://uptimerobot.com/
→ Agregar monitor HTTP
→ URL: https://tu-app.onrender.com
→ Intervalo: cada 10 minutos
```

### 🎯 Ideal Para:
- ✅ Apps con tráfico esporádico
- ✅ Si no te molesta el cold start
- ✅ Si sabes usar Docker
- ⚠️ **NO ideal si necesitas respuesta instantánea**

---

## 4️⃣ Shiny Server Open Source (SI TIENES VPS)

**🏢 Proveedor:** Posit (open source)
**🌐 Web:** https://posit.co/products/open-source/shiny-server/
**💰 Precio:** GRATIS (software) + costo de servidor

### ✅ Ventajas
- **Apps ilimitadas**
- **Sin límites de tiempo**
- **Control total** del servidor
- **Sin restricciones** de RAM/CPU
- **Gratis** el software

### ❌ Desventajas
- **Necesitas un servidor Linux** (VPS/Cloud)
- **Instalación manual** compleja
- **Mantenimiento** tú mismo
- **Seguridad** tú la gestionas
- **Costo de VPS** (aunque hay opciones gratis)

### 💻 Opciones de VPS Gratuitos:

**Oracle Cloud Free Tier** (MEJOR OPCIÓN GRATIS):
- 2 VMs con 1 GB RAM cada una
- GRATIS PARA SIEMPRE (no es trial)
- Ubuntu/Linux incluido
- https://www.oracle.com/cloud/free/

**AWS EC2 Free Tier**:
- 750 horas/mes (1 año gratis)
- 1 GB RAM
- Después del año, hay que pagar
- https://aws.amazon.com/free/

**Google Cloud Free Tier**:
- 1 f1-micro instance
- 0.6 GB RAM
- GRATIS SIEMPRE (con límites)
- https://cloud.google.com/free

### 🚀 Instalación Básica (Ubuntu)

```bash
# Instalar R
sudo apt-get update
sudo apt-get install r-base

# Instalar Shiny Server
sudo su - -c "R -e \"install.packages('shiny')\""
wget https://download3.rstudio.org/ubuntu-18.04/x86_64/shiny-server-1.5.20.1002-amd64.deb
sudo gdebi shiny-server-1.5.20.1002-amd64.deb

# Tu app va en:
# /srv/shiny-server/
```

### 🎯 Ideal Para:
- ✅ Si ya tienes experiencia con servidores Linux
- ✅ Apps empresariales con alta demanda
- ✅ Si quieres control total
- ❌ **NO recomendado para principiantes**

---

## 5️⃣ OTRAS OPCIONES

### Posit Cloud (antes RStudio Cloud)
- **Web:** https://posit.cloud/
- **Plan gratuito:** 25 horas/mes de compute
- **Ventaja:** Editor R online incluido
- **Desventaja:** Más para desarrollo que para producción

### Railway.app
- **Web:** https://railway.app/
- **Plan gratuito:** $5 crédito/mes
- **Ventaja:** Deploy fácil con Docker
- **Desventaja:** Crédito se acaba rápido

### Fly.io
- **Web:** https://fly.io/
- **Plan gratuito:** 3 VMs pequeñas
- **Ventaja:** Buena performance
- **Desventaja:** Configuración compleja

---

## 🎯 RECOMENDACIÓN PARA TU DASHBOARD

Basándome en tu dashboard de ofertas laborales (1,156 registros, múltiples visualizaciones):

### OPCIÓN 1: shinyapps.io (COMENZAR AQUÍ)
**🟢 FÁCIL | 🟡 25 horas/mes**

```r
# Deploy en 3 comandos:
install.packages("rsconnect")
rsconnect::setAccountInfo(name="...", token="...", secret="...")
rsconnect::deployApp(appName = "ofertas-oede")
```

**Usa esto si:**
- ✅ Quieres publicar HOY mismo
- ✅ Lo usarán pocas personas (equipo interno)
- ✅ No sabes Docker/Git
- ✅ Solo necesitas demo/prototipo

**URL final:** `https://tu-usuario.shinyapps.io/ofertas-oede`

---

### OPCIÓN 2: Hugging Face Spaces (SI NECESITAS MÁS)
**🟡 MEDIA | 🟢 Ilimitado**

Si tu app se queda sin horas en shinyapps.io, migra a HF:
- 16 GB RAM (vs 1 GB)
- Sin límite de tiempo
- Apps ilimitadas

**Usa esto si:**
- ✅ Tu app necesita más recursos
- ✅ Sabes usar Git/GitHub
- ✅ Quieres que esté 24/7 online
- ✅ Te animas a crear un Dockerfile básico

**URL final:** `https://huggingface.co/spaces/tu-usuario/ofertas-oede`

---

### COMBINACIÓN ÓPTIMA (MI RECOMENDACIÓN):

1. **FASE 1 - AHORA:** Deploy en **shinyapps.io**
   - Toma 10 minutos
   - Muéstraselo a tu equipo
   - Evalúa si las 25 horas alcanzan

2. **FASE 2 - SI SE QUEDA CORTO:** Migra a **Hugging Face Spaces**
   - Más recursos
   - Sin límite de tiempo
   - Gratis para siempre

3. **FASE 3 - SI SE USA MUCHO:** Considera plan pago
   - shinyapps.io Basic: $9/mes (100 horas)
   - Hugging Face PRO: $9/mes (CPU mejorado)

---

## 📋 CHECKLIST DE PREPARACIÓN

Antes de deployar, asegúrate de:

### ✅ Código Limpio
- [ ] Eliminar credenciales hardcoded
- [ ] Paths relativos (no `C:\Users\...`)
- [ ] Comentarios en español/inglés consistentes
- [ ] Sin `View()`, `browser()`, o debugs

### ✅ Archivos Necesarios
- [ ] `app.R` (tu aplicación)
- [ ] `ofertas_consolidadas.xlsx` (datos)
- [ ] `.gitignore` (si usas Git)
- [ ] `requirements.R` o similar con `library()` statements

### ✅ Optimización
- [ ] Comprimir Excel si es muy grande (>10 MB)
- [ ] Usar `read_excel()` solo una vez (no en cada reactive)
- [ ] Cache de datos con `reactiveFileReader()` si actualizas datos

### ✅ Testing Local
- [ ] Funciona en `http://localhost:3838`
- [ ] Sin errores en consola
- [ ] Todos los filtros funcionan
- [ ] Mapas/gráficos se cargan

---

## 🚀 PRÓXIMOS PASOS RECOMENDADOS

### AHORA (5 minutos):
1. Crea cuenta en https://www.shinyapps.io/
2. Ve a Account > Tokens > Show
3. Copia el comando de configuración

### HOY (15 minutos):
```r
# En RStudio, en el directorio de tu app:
install.packages("rsconnect")

rsconnect::setAccountInfo(
  name = "TU_NOMBRE",
  token = "TU_TOKEN",
  secret = "TU_SECRET"
)

rsconnect::deployApp(appName = "ofertas-dashboard")
```

### ESTA SEMANA:
- Comparte la URL con tu equipo
- Monitorea las horas usadas en shinyapps.io/dashboard
- Si se queda corto, aprende Docker para HF Spaces

---

## ❓ FAQ

**P: ¿Cuál es REALMENTE gratis para siempre?**
R: Hugging Face Spaces (básico) y shinyapps.io (con limitaciones)

**P: ¿Cuál es más fácil?**
R: shinyapps.io, sin duda. Deploy con 1 comando.

**P: ¿Cuál soporta más tráfico?**
R: Hugging Face Spaces (16 GB RAM)

**P: ¿Puedo usar mi propio dominio?**
R: Solo en planes pagos. En gratis usas subdominio.

**P: ¿Puedo monetizar mi app?**
R: Sí, en todos. Lee los ToS de cada plataforma.

**P: ¿Necesito saber programar Docker?**
R: Solo para HF Spaces y Render. shinyapps.io NO lo requiere.

---

## 📚 RECURSOS ÚTILES

### Tutoriales shinyapps.io:
- https://shiny.posit.co/r/articles/share/shinyapps/
- https://docs.posit.co/shinyapps.io/

### Tutoriales Hugging Face:
- https://shiny.posit.co/blog/posts/shiny-on-hugging-face/
- https://huggingface.co/docs/hub/spaces-sdks-docker-shiny

### Comunidad:
- Reddit: r/RShiny
- Posit Community: https://community.rstudio.com/
- Stack Overflow: tag [shiny]

---

**Última actualización:** Enero 2025
**Creado para:** Dashboard de Ofertas Laborales OEDE
**Recomendación principal:** Empieza con shinyapps.io, migra a HF Spaces si crece
