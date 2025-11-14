# Instalar rsconnect para deploy en shinyapps.io

if (!requireNamespace("rsconnect", quietly = TRUE)) {
  install.packages("rsconnect", repos = "https://cloud.r-project.org")
  cat("✓ rsconnect instalado exitosamente\n")
} else {
  cat("✓ rsconnect ya está instalado\n")
}

# Verificar versión
cat("\nVersión de rsconnect:", as.character(packageVersion("rsconnect")), "\n")
