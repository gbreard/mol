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
# La salida se CAPTURA para poder decidir el early-exit con ESTA corrida.
echo "[1/3] Sync VPS → Local..."
SALIDA_SYNC=$(python3 scripts/sync_from_vps.py 2>&1 | tail -5)
echo "$SALIDA_SYNC"

# Paso 2: Monitor (scraping_live_stats + daily) — SIEMPRE, desde la BD local.
# Va ANTES del early-exit a propósito: el monitor debe quedar fresco aunque no
# haya ofertas nuevas (las ventanas "hoy"/"7d" y la vejez son relativas al reloj).
# Es barato (unos upserts), a diferencia del sync pesado de ofertas.
# scraping_live_stats = fuente de verdad del monitor (los 6 portales, incl.
# indeed/portalempleo locales). Antes lo escribía el VPS desde SU BD y congelaba
# indeed/PE — 2026-09-01.
echo "[2/3] Monitor scraping (stats + daily)..."
python3 scripts/sync_scraping_stats.py 2>&1 | tail -3
python3 scripts/sync_scraping_daily.py --days 7 2>&1 | tail -3
python3 scripts/sync_scraping_dinamica.py --days 7 2>&1 | tail -3

# Si no hay ofertas nuevas, no hace falta el sync pesado de ofertas a Supabase.
#
# BUG CORREGIDO 2026-09-07: antes esto era
#     grep -q "No hay ofertas nuevas" /tmp/mol_auto_sync.log
# que mira el log ACUMULADO (el cron escribe con >>), no la corrida actual. La
# frase aparecio en la linea 6 del archivo, asi que el grep la encontraba
# SIEMPRE: 136 corridas saltearon el paso 3 y sync_to_supabase.py no corrio NI
# UNA VEZ. Resultado: ofertas_dashboard congelado (fecha_sync 2026-08-24) y
# sistema_estado en 2026-02-02, con el dashboard mostrando datos de febrero.
# Ahora se evalua la salida capturada de ESTA corrida.
if echo "$SALIDA_SYNC" | grep -q "No hay ofertas nuevas"; then
    echo "Sin ofertas nuevas en esta corrida. Saltando sync de ofertas a Supabase."
    echo "=== Fin: $(date +%H:%M:%S) ==="
    exit 0
fi

# Paso 3: Sync Local → Supabase (ofertas procesadas) — solo si hubo novedades.
echo "[3/3] Sync Local → Supabase..."
python3 scripts/exports/sync_to_supabase.py 2>&1 | tail -5

echo "=== Fin: $(date +%H:%M:%S) ==="
