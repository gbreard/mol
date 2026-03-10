#!/bin/bash
# MOL - Scraping automático multi-portal + export incremental
# Ejecutado por cron: Lunes y Jueves 08:00 Argentina
#
# Portales activos:
#   1. Bumeran (API searchV2 + keywords, ~5,000 ofertas, ~15 min)
#   2. ZonaJobs (API searchV2 + keywords, ~5,000 ofertas, ~12 min)
#   3. ComputRabajo (HTML scraping + keywords, ~1,000+ ofertas, ~3-4 horas)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/opt/mol/logs/scraping_${TIMESTAMP}.log"

echo "=== MOL Scraping Multi-Portal: $(date) ===" >> "$LOG_FILE"
echo "Portal 1: Bumeran" >> "$LOG_FILE"
echo "Portal 2: ZonaJobs" >> "$LOG_FILE"
echo "Portal 3: ComputRabajo" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

cd /opt/mol

# =====================================================================
# Paso 1: Bumeran (~15 min)
# =====================================================================
echo "=== [1/4] Bumeran scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 run_scheduler.py --test >> "$LOG_FILE" 2>&1
echo "=== Bumeran finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 2: ZonaJobs (~12 min)
# =====================================================================
echo "=== [2/4] ZonaJobs scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 scripts/scraping/run_zonajobs_vps.py --estrategia exhaustiva >> "$LOG_FILE" 2>&1
echo "=== ZonaJobs finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 3: ComputRabajo (~3-4 horas con descripción)
# =====================================================================
echo "=== [3/4] ComputRabajo scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 scripts/scraping/run_computrabajo_vps.py --estrategia exhaustiva --max-paginas 5 >> "$LOG_FILE" 2>&1
echo "=== ComputRabajo finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 4: Export incremental (para sync a local)
# =====================================================================
echo "=== [4/4] Export incremental: $(date) ===" >> "$LOG_FILE"
python3 scripts/export_nuevas.py >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "=== TODO FINALIZADO: $(date) ===" >> "$LOG_FILE"

# Limpiar logs viejos (>30 días)
find /opt/mol/logs -name "scraping_*.log" -mtime +30 -delete 2>/dev/null
# Limpiar exports viejos (>30 días)
find /opt/mol/data/export -name "ofertas_export_*.sql" -mtime +30 -delete 2>/dev/null
