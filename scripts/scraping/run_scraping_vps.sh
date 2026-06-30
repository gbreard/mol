#!/bin/bash
# MOL - Scraping automático multi-portal + export incremental
# Ejecutado por cron: Lunes y Jueves 08:00 Argentina
#
# Portales activos:
#   1. Bumeran (API searchV2 + keywords, ~5,000 ofertas, ~15 min)
#   2. ZonaJobs (API searchV2 + keywords, ~5,000 ofertas, ~12 min)
#   3. ComputRabajo (HTML scraping + keywords, ~1,000+ ofertas, ~3-4 horas)
#   4. CABA Portal de Trabajo (HTML scraping, ~10-50 ofertas, ~30 seg)
#   5. Portal Empleo Nacional (HTML scraping, ~400-500 ofertas, ~13 min)
#   6. Indeed (curl_cffi + keywords, ~2,000-3,000 ofertas, ~2.5 horas)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/opt/mol/logs/scraping_${TIMESTAMP}.log"

echo "=== MOL Scraping Multi-Portal: $(date) ===" >> "$LOG_FILE"
echo "Portal 1: Bumeran" >> "$LOG_FILE"
echo "Portal 2: ZonaJobs" >> "$LOG_FILE"
echo "Portal 3: ComputRabajo" >> "$LOG_FILE"
echo "Portal 4: CABA" >> "$LOG_FILE"
echo "Portal 5: Portal Empleo Nacional" >> "$LOG_FILE"
echo "Portal 6: Indeed" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

cd /opt/mol

# =====================================================================
# Paso 1: Bumeran (~15 min)
# =====================================================================
echo "=== [1/7] Bumeran scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 run_scheduler.py --test >> "$LOG_FILE" 2>&1
echo "=== Bumeran finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 2: ZonaJobs (~12 min)
# =====================================================================
echo "=== [2/7] ZonaJobs scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 scripts/scraping/run_zonajobs_vps.py --estrategia exhaustiva >> "$LOG_FILE" 2>&1
echo "=== ZonaJobs finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 3: ComputRabajo (~3-4 horas con descripción)
# =====================================================================
echo "=== [3/7] ComputRabajo scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 scripts/scraping/run_computrabajo_vps.py --estrategia exhaustiva --max-paginas 5 >> "$LOG_FILE" 2>&1
echo "=== ComputRabajo finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 4: CABA Portal de Trabajo (~30 seg)
# =====================================================================
echo "=== [4/7] CABA scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 scripts/scraping/run_caba_vps.py >> "$LOG_FILE" 2>&1
echo "=== CABA finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 5: Portal Empleo Nacional (~13 min)
# =====================================================================
echo "=== [5/7] Portal Empleo Nacional scraping: $(date) ===" >> "$LOG_FILE"
PYTHONUNBUFFERED=1 python3 scripts/scraping/run_portalempleo_vps.py >> "$LOG_FILE" 2>&1
echo "=== Portal Empleo finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 6: Indeed (~2.5 horas con detalles, multi-keyword)
# =====================================================================
echo "=== [6/7] Indeed scraping: $(date) ===" >> "$LOG_FILE"
# Indeed corre local (VPS bloqueado por Cloudflare). Se encola via Supabase → poller local.
PYTHONUNBUFFERED=1 python3 scripts/scraping/queue_indeed_local.py >> "$LOG_FILE" 2>&1
echo "=== Indeed finalizado: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 7: Export incremental — DESACTIVADO (2026-06-30)
# =====================================================================
# Bug "watermark robado": export_nuevas.py comparte el cursor data/sync_log.json
# con el sync local (sync_from_vps.py, horario). Si el cron exporta acá, avanza
# el watermark a un .sql que queda en el VPS y que NADIE importa, dejando afuera
# del sync local los portales scrapeados al final del cron (CABA 11:23, Portal
# Empleo 11:23-11:27). El sync local es el ÚNICO consumidor real y debe ser el
# único dueño del watermark. NO reactivar este paso.
echo "=== [7/7] Export incremental: DESACTIVADO (lo hace el sync local) ===" >> "$LOG_FILE"
# python3 scripts/export_nuevas.py >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "=== TODO FINALIZADO: $(date) ===" >> "$LOG_FILE"

# Limpiar logs viejos (>30 días)
find /opt/mol/logs -name "scraping_*.log" -mtime +30 -delete 2>/dev/null
# Limpiar exports viejos (>30 días)
find /opt/mol/data/export -name "ofertas_export_*.sql" -mtime +30 -delete 2>/dev/null

# Sync scraping stats a Supabase (para dashboard)
echo "=== [STATS] Subiendo stats a Supabase ===" >> "$LOG_FILE"
cd /opt/mol && python3 scripts/sync_scraping_stats.py && python3 scripts/sync_scraping_daily.py --days 7 >> "$LOG_FILE" 2>&1
