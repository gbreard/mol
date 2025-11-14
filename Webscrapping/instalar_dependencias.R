# Script de Instalación de Dependencias
# Dashboard de Ofertas Laborales

cat("==============================================\n")
cat("   INSTALADOR DE DEPENDENCIAS\n")
cat("   Dashboard de Ofertas Laborales\n")
cat("==============================================\n\n")

# Lista de paquetes necesarios
paquetes_necesarios <- c(
  "shiny",
  "shinydashboard",
  "readxl",
  "dplyr",
  "ggplot2",
  "plotly",
  "lubridate",
  "DT"
)

# Función para instalar y cargar paquetes
instalar_si_necesario <- function(paquete) {
  if (!require(paquete, character.only = TRUE, quietly = TRUE)) {
    cat(paste0("Instalando ", paquete, "...\n"))
    install.packages(paquete, dependencies = TRUE)

    if (require(paquete, character.only = TRUE, quietly = TRUE)) {
      cat(paste0("  ✓ ", paquete, " instalado correctamente\n"))
      return(TRUE)
    } else {
      cat(paste0("  ✗ ERROR al instalar ", paquete, "\n"))
      return(FALSE)
    }
  } else {
    cat(paste0("  ✓ ", paquete, " ya está instalado\n"))
    return(TRUE)
  }
}

# Instalar todos los paquetes
cat("\nVerificando e instalando paquetes necesarios...\n\n")
resultados <- sapply(paquetes_necesarios, instalar_si_necesario)

# Resumen
cat("\n==============================================\n")
cat("   RESUMEN DE INSTALACIÓN\n")
cat("==============================================\n")
cat(paste0("Total de paquetes: ", length(paquetes_necesarios), "\n"))
cat(paste0("Instalados correctamente: ", sum(resultados), "\n"))
cat(paste0("Fallaron: ", sum(!resultados), "\n"))

if (all(resultados)) {
  cat("\n✓ TODAS LAS DEPENDENCIAS INSTALADAS CORRECTAMENTE\n")
  cat("\nPara ejecutar la aplicación:\n")
  cat("  1. Abre app.R en RStudio\n")
  cat("  2. Haz click en 'Run App'\n")
  cat("  O ejecuta: shiny::runApp('app.R')\n")
} else {
  cat("\n✗ ALGUNOS PAQUETES NO SE INSTALARON\n")
  cat("Paquetes con error:\n")
  print(paquetes_necesarios[!resultados])
  cat("\nIntenta instalarlos manualmente con:\n")
  cat("install.packages('nombre_del_paquete')\n")
}

cat("\n==============================================\n")
