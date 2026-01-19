# 🚀 GUÍA DE DEPLOY EN SHINYAPPS.IO

## ✅ PREPARACIÓN COMPLETADA

- ✅ Código revisado y listo
- ✅ Sin paths absolutos
- ✅ Sin credenciales hardcoded
- ✅ Excel: 1.6 MB (dentro del límite)
- ✅ rsconnect v1.5.1 instalado

---

## 📋 PASO 1: CREAR CUENTA EN SHINYAPPS.IO

### 1.1 Registrarse
1. Ve a: **https://www.shinyapps.io/**
2. Click en **"Sign Up"** (arriba derecha)
3. Regístrate con:
   - Google
   - GitHub
   - O email/password

### 1.2 Confirma tu email
- Revisa tu correo
- Click en el link de confirmación

### 1.3 Crea tu nombre de usuario
- Elige un nombre corto y profesional
- Ejemplo: `oede`, `ofertas-lab`, `tu-nombre`
- Este será tu URL: `https://tu-usuario.shinyapps.io`

---

## 📋 PASO 2: OBTENER TOKEN DE AUTENTICACIÓN

### 2.1 Ir a Tokens
Una vez logueado en shinyapps.io:
1. Click en tu nombre (arriba derecha)
2. Click en **"Tokens"**
3. O ve directamente a: **https://www.shinyapps.io/admin/#/tokens**

### 2.2 Copiar comando de configuración
1. Click en el botón **"Show"** junto a tu token
2. Verás algo como:

```r
rsconnect::setAccountInfo(
  name='tu-usuario',
  token='ABC123DEF456',
  secret='xyz789uvw012'
)
```

3. **COPIA TODO ESE COMANDO** (lo usaremos en el siguiente paso)

⚠️ **IMPORTANTE:**
- NO compartas este token con nadie
- Es como tu password
- Si lo expones, regenera uno nuevo

---

## 📋 PASO 3: CONFIGURAR RSCONNECT EN R

### 3.1 Abrir RStudio (o R)

### 3.2 Ejecutar comando de configuración
Pega el comando que copiaste en el Paso 2.2:

```r
rsconnect::setAccountInfo(
  name='tu-usuario',
  token='ABC123DEF456',
  secret='xyz789uvw012'
)
```

Deberías ver:
```
Account registered successfully: tu-usuario
```

---

## 📋 PASO 4: DEPLOYAR LA APLICACIÓN

### 4.1 Ir al directorio de tu app

```r
setwd("C:/Users/gbrea/OneDrive/Documentos/OEDE/Webscrapping")
```

O desde la terminal de Claude Code (que ya estás ahí).

### 4.2 Verificar archivos necesarios

Asegúrate de tener en el directorio:
- ✅ `app.R` (tu aplicación)
- ✅ `ofertas_consolidadas.xlsx` (datos)

### 4.3 Deployar!

Ejecuta este comando:

```r
rsconnect::deployApp(
  appName = "ofertas-dashboard",
  appTitle = "Dashboard Ofertas Laborales OEDE",
  appFiles = c("app.R", "ofertas_consolidadas.xlsx"),
  forceUpdate = TRUE
)
```

**Explicación de parámetros:**
- `appName`: nombre de tu app (aparecerá en la URL)
- `appTitle`: título descriptivo
- `appFiles`: archivos a subir (app + datos)
- `forceUpdate`: actualizar si ya existe

### 4.4 Esperar el deploy

Verás algo como:

```
Preparing to deploy app... DONE
Uploading bundle for app: 123456... DONE
Deploying bundle: 7890123 for app: ofertas-dashboard ...
Waiting for task: 456789
  building: Processing bundle: 7890123
  building: Building image: 111222
  building: Installing packages
  deploying: Starting instances
  success: Stopping old instances
── Deployment completed ──────────────────────────────────
URL: https://tu-usuario.shinyapps.io/ofertas-dashboard/
```

⏱️ **Primera vez:** puede tomar 3-5 minutos (instala todos los paquetes)
⏱️ **Actualizaciones:** 1-2 minutos

---

## 📋 PASO 5: VERIFICAR QUE FUNCIONA

### 5.1 Abrir la URL
La URL final será:
```
https://tu-usuario.shinyapps.io/ofertas-dashboard/
```

### 5.2 Revisar que todo carga:
- ✅ Dashboard se carga sin errores
- ✅ Filtros funcionan
- ✅ Gráficos se muestran
- ✅ Mapa aparece
- ✅ Word cloud funciona

### 5.3 Ver logs (si hay errores)
En shinyapps.io:
1. Dashboard → Applications → ofertas-dashboard
2. Click en "Logs"
3. Revisa errores en rojo

---

## 📋 PASO 6: COMPARTIR LA APP

### 6.1 Opciones de visibilidad

Por defecto, tu app es **pública** (cualquiera con la URL puede verla).

**Para cambiar:**
1. Ve a: https://www.shinyapps.io/admin/#/applications
2. Click en "ofertas-dashboard"
3. Settings → Access
4. Opciones:
   - **Public**: Cualquiera puede ver
   - **Private**: Solo tú
   - **Password**: Requiere password (solo en plan pago)

### 6.2 Compartir URL
Simplemente comparte:
```
https://tu-usuario.shinyapps.io/ofertas-dashboard/
```

---

## 📊 PASO 7: MONITOREAR USO

### 7.1 Ver horas consumidas
1. Ve a: https://www.shinyapps.io/admin/#/dashboard
2. Verás:
   - **Active hours:** Horas usadas este mes
   - **Included hours:** 25 horas totales (plan gratis)
   - **Remaining:** Horas restantes

### 7.2 Ver métricas
- **Uptime:** Tiempo que la app estuvo disponible
- **Instance hours:** Tiempo activo de la app
- **Request count:** Número de visitas

### 7.3 Tips para ahorrar horas:
1. **Pausa apps que no uses:**
   - Applications → ofertas-dashboard → Settings → Archive

2. **Usa modo sleep:**
   - Settings → Instance Idle Timeout → 5 minutos

3. **Optimiza código:**
   - Cache datos con `reactiveFileReader()`
   - No recargues Excel en cada reactive

---

## 🔄 PASO 8: ACTUALIZAR LA APP

Cuando hagas cambios en el código:

### Opción 1: Desde R
```r
rsconnect::deployApp(
  appName = "ofertas-dashboard",
  forceUpdate = TRUE
)
```

### Opción 2: Desde RStudio
1. Click en el botón azul "Publish" (arriba derecha del editor)
2. Select "Publish just this app"
3. Choose "Update existing"
4. Click "Publish"

---

## ❌ SOLUCIÓN DE PROBLEMAS COMUNES

### Error: "Unable to deploy - package not found"
**Solución:**
Instala el paquete faltante localmente primero:
```r
install.packages("nombre-del-paquete")
```

### Error: "App timed out during startup"
**Solución:**
- Tu app tarda mucho en cargar
- Reduce tamaño del Excel o usa .RData
- Simplifica cálculos en inicio

### Error: "App crashed during startup"
**Solución:**
1. Revisa logs en shinyapps.io
2. Busca línea que dice "Error:"
3. Arregla el error localmente
4. Re-deploy

### App funciona local pero no en shinyapps.io
**Posibles causas:**
1. **Paquete no instalado:** Agrega `library()` al inicio de app.R
2. **Path absoluto:** Cambia a path relativo
3. **Encoding:** Puede fallar con caracteres especiales
4. **Memoria:** App muy pesada (>1 GB RAM)

---

## 📝 COMANDOS DE REFERENCIA RÁPIDA

### Configurar cuenta (solo una vez):
```r
rsconnect::setAccountInfo(name="...", token="...", secret="...")
```

### Deployar app:
```r
rsconnect::deployApp(appName = "ofertas-dashboard")
```

### Ver apps deployadas:
```r
rsconnect::applications()
```

### Terminar app:
```r
rsconnect::terminateApp(appName = "ofertas-dashboard")
```

### Eliminar app:
```r
rsconnect::purgeApp(appName = "ofertas-dashboard")
```

### Ver logs:
```r
rsconnect::showLogs(appName = "ofertas-dashboard")
```

---

## 🎯 PRÓXIMOS PASOS DESPUÉS DEL DEPLOY

### Inmediato (hoy):
- [ ] Compartir URL con tu equipo
- [ ] Revisar que todo funcione correctamente
- [ ] Probar todos los filtros y pestañas

### Esta semana:
- [ ] Monitorear horas consumidas
- [ ] Recopilar feedback de usuarios
- [ ] Ajustar visualizaciones según necesidad

### Largo plazo:
- [ ] Si te quedas sin horas, considerar:
  - Plan Basic ($9/mes - 100 horas)
  - Hugging Face Spaces (gratis ilimitado)
- [ ] Optimizar performance si es lento
- [ ] Agregar nuevas funcionalidades

---

## 🆘 SOPORTE

### Documentación oficial:
- **Guía de deploy:** https://docs.posit.co/shinyapps.io/
- **Troubleshooting:** https://docs.posit.co/shinyapps.io/troubleshooting.html
- **API reference:** https://docs.posit.co/shinyapps.io/api.html

### Comunidad:
- **Posit Community:** https://community.rstudio.com/
- **Stack Overflow:** https://stackoverflow.com/questions/tagged/shiny
- **Reddit:** r/RShiny

---

## 📌 RESUMEN DE URL IMPORTANTES

| Servicio | URL |
|----------|-----|
| **shinyapps.io** | https://www.shinyapps.io/ |
| **Dashboard** | https://www.shinyapps.io/admin/#/dashboard |
| **Applications** | https://www.shinyapps.io/admin/#/applications |
| **Tokens** | https://www.shinyapps.io/admin/#/tokens |
| **Logs** | https://www.shinyapps.io/admin/#/logs |
| **Billing** | https://www.shinyapps.io/admin/#/billing |
| **Tu app** | https://TU-USUARIO.shinyapps.io/ofertas-dashboard/ |

---

**¡LISTO!** 🎉

Tu dashboard estará disponible en:
```
https://tu-usuario.shinyapps.io/ofertas-dashboard/
```

**Siguiente paso:** Ve al Paso 1 y crea tu cuenta en shinyapps.io
