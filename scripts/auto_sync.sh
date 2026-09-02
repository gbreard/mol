#!/bin/bash
# Auto-sync: VPS → Local → Supabase
# Corre cada hora via cron o Task Scheduler
#
# Instalar (Linux/WSL):
#   crontab -e
#   0 * * * * /mnt/d/OEDE/Webscrapping/scripts/auto_sync.sh >> /tmp/mol_auto_sync.log 2>&1
#
# Instalar (Windows Task Scheduler):
#   Acción: wsl.exe -e /mnt/d/OEDE/Webscrapping/scripts/auto_sync.sh

cd /mnt/d/OEDE/Webscrapping

TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)
echo "=== Auto-sync: $TIMESTAMP ==="

# Paso 1: Sync VPS → Local
echo "[1/3] Sync VPS → Local..."
python3 scripts/sync_from_vps.py 2>&1 | tail -5

# Si no hay ofertas nuevas, parar
if grep -q "No hay ofertas nuevas" /tmp/mol_auto_sync.log 2>/dev/null; then
    echo "Sin ofertas nuevas. Saltando sync a Supabase."
    echo "=== Fin: $(date +%H:%M:%S) ==="
    exit 0
fi

# Paso 2: Sync Local → Supabase (solo ofertas ya procesadas)
echo "[2/3] Sync Local → Supabase..."
python3 scripts/exports/sync_to_supabase.py 2>&1 | tail -5

# Paso 3: Actualizar scraping_daily
echo "[3/3] Sync scraping stats + daily..."
# scraping_live_stats = fuente de verdad del monitor, recalculada desde la BD
# LOCAL (los 6 portales, incl. indeed/portalempleo locales). Antes lo escribía
# el VPS (run_scraping_vps.sh) desde SU BD y congelaba indeed/PE — 2026-09-01.
python3 scripts/sync_scraping_stats.py 2>&1 | tail -3
python3 scripts/sync_scraping_daily.py --days 7 2>&1 | tail -3
python3 scripts/sync_scraping_dinamica.py --days 7 2>&1 | tail -3

echo "=== Fin: $(date +%H:%M:%S) ==="
