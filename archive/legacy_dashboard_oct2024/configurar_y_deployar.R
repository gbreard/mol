# Configurar cuenta de shinyapps.io
rsconnect::setAccountInfo(
  name='dos1tv-gerardo-breard',
  token='45DB90EA461FAD11B32AEBEE28454644',
  secret='/qJ1pA35CIQRQeosn7x4LalIWPVxMjQAh+gEzmBd'
)

cat("✓ Cuenta configurada exitosamente\n")
cat("Usuario:", rsconnect::accounts()$name[1], "\n\n")

# Deployar la aplicación
cat("🚀 Iniciando deploy...\n\n")

rsconnect::deployApp(
  appName = "ofertas-dashboard",
  appTitle = "Dashboard Ofertas Laborales OEDE",
  appFiles = c("app.R", "ofertas_consolidadas.xlsx"),
  forceUpdate = TRUE,
  launch.browser = FALSE
)
