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

# =====================================================================
# Guarda anti-concurrencia (2026-08-25)
# =====================================================================
# Hasta 2026-08-25 este script corría DOS veces cada lunes y jueves: una
# por el cron (`0 8 * * 1,4`) y otra por el disparo programado del
# vps_command_poller.py. Ambas instancias escribían la misma SQLite y se
# pisaban ("database is locked" ×5 el 2026-08-24).
#
# El disparo duplicado ya fue eliminado en el poller, pero este lock queda
# como defensa en profundidad: si vuelve a aparecer un segundo disparo
# (schedule reactivado, comando manual encima del cron, cron mal editado),
# la segunda instancia aborta en lugar de corromper la corrida en curso.
#
# El rechazo NO crea un scraping_*.log propio — se registra en un archivo
# aparte, para que siga habiendo exactamente un log por corrida real.
LOCK_FILE="/tmp/mol_scraping.lock"
LOCK_REJECT_LOG="/opt/mol/logs/scraping_lock_rejects.log"

acquire_lock() {
    # `set -o noclobber` hace el create atómico: si el archivo ya existe,
    # la redirección falla en vez de sobrescribirlo. Evita la ventana de
    # carrera de un `if [ -e ... ]` seguido de un `echo >`.
    if ( set -o noclobber; echo $$ > "$LOCK_FILE" ) 2>/dev/null; then
        return 0
    fi

    local lock_pid
    lock_pid=$(cat "$LOCK_FILE" 2>/dev/null)

    # ¿El dueño del lock sigue vivo?
    if [ -n "$lock_pid" ] && kill -0 "$lock_pid" 2>/dev/null; then
        return 1
    fi

    # Lock huérfano (proceso muerto sin limpiar: kill -9, reboot, OOM).
    echo "[$(date)] Lock huérfano de PID ${lock_pid:-vacío} reclamado por PID $$" >> "$LOCK_REJECT_LOG"
    rm -f "$LOCK_FILE"
    ( set -o noclobber; echo $$ > "$LOCK_FILE" ) 2>/dev/null || return 1
    return 0
}

if ! acquire_lock; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    LOCK_SINCE=$(ps -o lstart= -p "$LOCK_PID" 2>/dev/null | sed 's/^ *//')
    {
        echo "[$(date)] ABORTADO: ya hay un scraping en curso."
        echo "    Instancia dueña : PID $LOCK_PID (desde ${LOCK_SINCE:-desconocido})"
        echo "    Instancia actual: PID $$ — no se ejecuta nada."
        echo "    Lock: $LOCK_FILE"
    } >> "$LOCK_REJECT_LOG"
    echo "ABORTADO: ya hay un scraping en curso (PID $LOCK_PID). Ver $LOCK_REJECT_LOG" >&2
    exit 1
fi

# Liberar el lock pase lo que pase (fin normal, error, Ctrl-C, kill).
# Se instala DESPUÉS de adquirirlo: si abortamos arriba por lock ajeno,
# este trap no existe y por lo tanto no borramos el lock de otro.
trap 'rm -f "$LOCK_FILE"' EXIT INT TERM

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/opt/mol/logs/scraping_${TIMESTAMP}.log"

echo "=== MOL Scraping Multi-Portal: $(date) ===" >> "$LOG_FILE"
echo "Lock adquirido: $LOCK_FILE (PID $$)" >> "$LOG_FILE"
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
# Paso 5: Portal Empleo — DESACTIVADO (2026-09-01)
# =====================================================================
# La IP del VPS quedó bloqueada SOLO contra portalempleo.gob.ar
# (connection reset a todo el dominio; buenosaires.gob.ar y CABA siguen
# OK desde el VPS). El scraper es HTTP puro (requests+BS4, sin browser),
# así que pasa a correr LOCAL por cron dedicado. El sitio tiene ~105
# ofertas activas hoy (no 400-500: cifra histórica desactualizada).
# Diagnóstico: fix/portalempleo-local (2026-09-01).
echo "=== [5/7] Portal Empleo: DESACTIVADO en VPS — corre local ===" >> "$LOG_FILE"
# PYTHONUNBUFFERED=1 python3 scripts/scraping/run_portalempleo_vps.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"

# =====================================================================
# Paso 6: Indeed — DESACTIVADO (2026-09-01)
# =====================================================================
# Indeed pasó a scraping LOCAL HEADED (chromium real bajo xvfb): curl_cffi
# quedó bloqueado por Cloudflare (403 "Security Check") y el modo headless da
# "Blocked - Indeed.com" (detección de headless, NO baneo de IP). El motor
# headed corre por un cron local dedicado 1×/día (05:00), no desde el VPS.
# Dejar este enqueue acá lo dispararía DOS veces los Lun/Jue (cron local +
# poller). Spec: exports/reportes/SPEC_indeed_scraper_headed_2026-09-01.md
# (El botón admin sigue disponible: pipeline_commands → poller → headed.)
echo "=== [6/7] Indeed: DESACTIVADO en VPS — corre local headed 05:00 ===" >> "$LOG_FILE"
# PYTHONUNBUFFERED=1 python3 scripts/scraping/queue_indeed_local.py >> "$LOG_FILE" 2>&1
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
