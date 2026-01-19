# Configurar mirror de CRAN
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Paquetes necesarios
paquetes <- c("shiny", "shinydashboard", "readxl", "dplyr", "ggplot2", "plotly", "lubridate", "DT")

# Instalar solo los que faltan
for (paquete in paquetes) {
  if (!requireNamespace(paquete, quietly = TRUE)) {
    cat(paste0("Instalando ", paquete, "...\n"))
    install.packages(paquete, quiet = TRUE)
  } else {
    cat(paste0(paquete, " ya está instalado\n"))
  }
}

cat("\n¡Listo!\n")
