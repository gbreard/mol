# ========================================
# SCRIPT DE DEPLOY PARA SHINYAPPS.IO
# ========================================

cat("\n")
cat("🚀 DEPLOY DEL DASHBOARD DE OFERTAS LABORALES\n")
cat("=============================================\n\n")

# Verificar que rsconnect está instalado
if (!requireNamespace("rsconnect", quietly = TRUE)) {
  stop("❌ rsconnect no está instalado. Ejecuta: install.packages('rsconnect')")
}

# ========================================
# PASO 1: CONFIGURAR CREDENCIALES
# ========================================
#
# INSTRUCCIONES:
# 1. Ve a https://www.shinyapps.io/admin/#/tokens
# 2. Click en "Show" para ver tu token
# 3. Copia los valores y pégalos abajo:
#
# IMPORTANTE: Descomenta las líneas y completa con tus datos

# rsconnect::setAccountInfo(
#   name   = "TU-USUARIO-AQUI",      # Tu nombre de usuario en shinyapps.io
#   token  = "TU-TOKEN-AQUI",         # Tu token (cadena larga de letras/números)
#   secret = "TU-SECRET-AQUI"         # Tu secret (otra cadena larga)
# )

cat("✓ Paso 1: Configurar credenciales\n")
cat("  → Ve a: https://www.shinyapps.io/admin/#/tokens\n")
cat("  → Descomenta y completa las líneas 17-21 de este script\n")
cat("  → Vuelve a ejecutar este script\n\n")

# Verificar si ya está configurado
accounts <- rsconnect::accounts()

if (nrow(accounts) == 0) {
  cat("⚠️  AÚN NO HAS CONFIGURADO TUS CREDENCIALES\n")
  cat("   Sigue las instrucciones arriba ↑\n\n")
  stop("Configuración incompleta")
}

cat("✓ Cuenta configurada:", accounts$name[1], "\n\n")

# ========================================
# PASO 2: VERIFICAR ARCHIVOS NECESARIOS
# ========================================

cat("🔍 Verificando archivos necesarios...\n")

required_files <- c("app.R", "ofertas_consolidadas.xlsx")
missing_files <- c()

for (file in required_files) {
  if (file.exists(file)) {
    size <- file.info(file)$size / 1024 / 1024  # Convertir a MB
    cat(sprintf("  ✓ %s (%.2f MB)\n", file, size))
  } else {
    cat(sprintf("  ❌ %s - NO ENCONTRADO\n", file))
    missing_files <- c(missing_files, file)
  }
}

if (length(missing_files) > 0) {
  stop(sprintf("❌ Faltan archivos: %s", paste(missing_files, collapse = ", ")))
}

cat("\n")

# ========================================
# PASO 3: CONFIRMAR DEPLOY
# ========================================

cat("📋 RESUMEN DEL DEPLOY\n")
cat("==========================================\n")
cat("Cuenta:        ", accounts$name[1], "\n")
cat("Nombre app:     ofertas-dashboard\n")
cat("URL final:      https://", accounts$name[1], ".shinyapps.io/ofertas-dashboard/\n", sep = "")
cat("Archivos:       app.R, ofertas_consolidadas.xlsx\n")
cat("==========================================\n\n")

cat("⏱️  El deploy puede tomar 3-5 minutos la primera vez...\n\n")

# Preguntar confirmación (comentar si quieres deploy automático)
respuesta <- readline(prompt = "¿Continuar con el deploy? (s/n): ")

if (tolower(respuesta) != "s" && tolower(respuesta) != "si") {
  cat("\n❌ Deploy cancelado por el usuario\n")
  stop("Cancelado")
}

# ========================================
# PASO 4: DEPLOYAR!
# ========================================

cat("\n🚀 Iniciando deploy...\n\n")

tryCatch({
  rsconnect::deployApp(
    appName = "ofertas-dashboard",
    appTitle = "Dashboard Ofertas Laborales OEDE",
    appFiles = c("app.R", "ofertas_consolidadas.xlsx"),
    forceUpdate = TRUE,
    launch.browser = TRUE  # Abre automáticamente en el navegador
  )

  cat("\n")
  cat("════════════════════════════════════════\n")
  cat("✅ ¡DEPLOY EXITOSO! 🎉\n")
  cat("════════════════════════════════════════\n")
  cat("\n")
  cat("Tu app está disponible en:\n")
  cat("👉 https://", accounts$name[1], ".shinyapps.io/ofertas-dashboard/\n\n", sep = "")
  cat("📊 Dashboard: https://www.shinyapps.io/admin/#/dashboard\n")
  cat("📝 Logs:      https://www.shinyapps.io/admin/#/logs\n")
  cat("\n")

}, error = function(e) {
  cat("\n")
  cat("❌ ERROR EN EL DEPLOY\n")
  cat("═══════════════════════\n")
  cat("Mensaje de error:\n")
  cat(conditionMessage(e), "\n\n")
  cat("🔍 SOLUCIONES COMUNES:\n")
  cat("1. Verifica que todos los paquetes estén instalados localmente\n")
  cat("2. Revisa los logs en: https://www.shinyapps.io/admin/#/logs\n")
  cat("3. Intenta deployar de nuevo con: source('deploy_app.R')\n")
  cat("\n")
  stop(e)
})

# ========================================
# PASO 5: INFORMACIÓN POST-DEPLOY
# ========================================

cat("📌 PRÓXIMOS PASOS:\n")
cat("══════════════════════════════════════\n")
cat("1. Prueba tu app en el navegador\n")
cat("2. Verifica que todos los filtros funcionen\n")
cat("3. Comparte la URL con tu equipo\n")
cat("4. Monitorea las horas usadas en el dashboard\n")
cat("\n")
cat("💡 TIPS:\n")
cat("══════════════════════════════════════\n")
cat("• Plan gratis: 25 horas/mes compartidas entre todas tus apps\n")
cat("• Para actualizar la app: vuelve a ejecutar este script\n")
cat("• Para ver logs: https://www.shinyapps.io/admin/#/logs\n")
cat("• Si te quedas sin horas, considera Hugging Face Spaces (gratis ilimitado)\n")
cat("\n")
