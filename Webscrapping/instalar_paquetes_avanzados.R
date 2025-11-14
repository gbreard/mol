# Instalar paquetes avanzados para dashboard mejorado
options(repos = c(CRAN = "https://cloud.r-project.org"))

paquetes_avanzados <- c(
  "leaflet",      # Mapas interactivos
  "tidytext",     # Análisis de texto
  "wordcloud2",   # Word clouds
  "tm",           # Text mining
  "openxlsx",     # Excel avanzado
  "zoo",          # Series temporales
  "scales"        # Escalas y formateo
)

cat("Instalando paquetes avanzados...\n\n")

for (paquete in paquetes_avanzados) {
  if (!requireNamespace(paquete, quietly = TRUE)) {
    cat(paste0("Instalando ", paquete, "...\n"))
    install.packages(paquete, quiet = FALSE)
  } else {
    cat(paste0(paquete, " ya está instalado\n"))
  }
}

cat("\n¡Paquetes avanzados instalados!\n")
