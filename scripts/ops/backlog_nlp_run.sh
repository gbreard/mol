#!/bin/bash
# backlog_nlp_run.sh — corrida dedicada del backlog historico de NLP (tipo FRENTE D).
#
# Come las ~26.6K ofertas sin NLP en tandas, mas recientes primero. Cada tanda
# corre con la BD en tmpfs (run_con_tmpfs.sh: sha256 + sync-back verificado) y
# sale con el matching v3.6.0 completo — este backlog NO necesita re-matching.
#
# Entre tandas la BD vuelve a disco: esa es la ventana de coordinacion con los
# otros frentes (K3, L, auto_sync horario, poller). Si una tanda no puede tomar
# la BD porque otro proceso la tiene, NO es error: espera y reintenta.
#
# Uso: scripts/ops/backlog_nlp_run.sh [TAMANO_TANDA] [MAX_TANDAS]
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

SIZE="${1:-3000}"
MAX_TANDAS="${2:-40}"
RUNDIR="${RUNDIR:-$REPO/exports/reportes/backlog_nlp_$(date +%Y%m%d_%H%M)}"
mkdir -p "$RUNDIR"
MAESTRO="$RUNDIR/run.log"

export OLLAMA_HOST="${OLLAMA_HOST:-172.17.0.1}"

# Espera entre reintentos cuando la BD esta tomada por otro frente.
ESPERA_LOCK=600          # 10 min
MAX_ESPERAS=144          # hasta 24 h esperando por tanda antes de rendirse

log() { echo "[$(date '+%F %T')] $*" | tee -a "$MAESTRO"; }

salud() {
  # Devuelve 0 si el entorno esta sano para arrancar una tanda.
  local ok=0
  if ! curl -s -m 15 "http://$OLLAMA_HOST:11434/api/tags" | grep -q "qwen2.5:7b"; then
    log "  SALUD: Ollama no responde o falta qwen2.5:7b en $OLLAMA_HOST"; ok=1
  fi
  local shm_avail db_size disco_avail ram_avail
  shm_avail=$(df --output=avail -B1 /dev/shm | tail -1)
  db_size=$(stat -Lc %s database/bumeran_scraping.db)
  if [ "$shm_avail" -lt $(( db_size * 5 / 4 )) ]; then
    log "  SALUD: /dev/shm sin espacio ($((shm_avail/1024/1024/1024))G libre, BD $((db_size/1024/1024/1024))G)"; ok=1
  fi
  disco_avail=$(df --output=avail -B1 "$REPO" | tail -1)
  if [ "$disco_avail" -lt $(( db_size * 5 / 2 )) ]; then
    log "  SALUD: disco del repo sin margen para el sync-back ($((disco_avail/1024/1024/1024))G)"; ok=1
  fi
  ram_avail=$(awk '/MemAvailable/{print $2*1024}' /proc/meminfo)
  log "  SALUD: shm libre $((shm_avail/1024/1024/1024))G | RAM disp $((ram_avail/1024/1024/1024))G | disco $((disco_avail/1024/1024/1024))G"
  return $ok
}

log "=========================================================="
log "BACKLOG NLP — corrida dedicada | tanda=$SIZE max_tandas=$MAX_TANDAS"
log "rundir=$RUNDIR | matcher=$(cat database/MATCHER_VERSION) nlp=$(cat database/NLP_VERSION)"
log "=========================================================="

for (( n=1; n<=MAX_TANDAS; n++ )); do
  log "--- TANDA $n/$MAX_TANDAS ---"

  # 1. Chequeo de salud; si falla, esperar y reintentar (no abortar la corrida).
  esperas=0
  until salud; do
    esperas=$(( esperas + 1 ))
    if [ "$esperas" -ge "$MAX_ESPERAS" ]; then
      log "ABORTA: entorno insano tras $esperas chequeos"; exit 1
    fi
    log "  entorno insano — reintento en $((ESPERA_LOCK/60)) min (intento $esperas)"
    sleep "$ESPERA_LOCK"
  done

  # 2. Tanda con la BD en tmpfs. Si la BD esta tomada por otro frente
  #    (K3 aplicando, frente L, auto_sync, poller) el wrapper aborta antes de
  #    tocar nada: esperamos y reintentamos.
  esperas=0
  while true; do
    SALIDA="$RUNDIR/tmpfs_tanda_${n}.out"
    scripts/ops/run_con_tmpfs.sh /usr/bin/python3 scripts/ops/backlog_nlp_tanda.py \
        --size "$SIZE" --tanda "$n" --rundir "$RUNDIR" > "$SALIDA" 2>&1
    rc=$?
    # Todas estas condiciones son TRANSITORIAS y significan "otro frente esta
    # usando la BD ahora": esperar es la respuesta correcta, no abortar.
    #   - "esta en uso"        -> write-lock tomado (pipeline ajeno, auto_sync, poller)
    #   - "ya es un symlink"   -> otra sesion tmpfs activa
    #   - "BD no encontrada"   -> ventana de sync-back ajeno: el wrapper del otro
    #                             frente borra el symlink, copia 4,6 GB a .sync_tmp
    #                             y recien despues hace el mv. Durante esos ~8 min
    #                             la BD NO EXISTE en disco. Observado en el
    #                             traspaso del 2026-08-20 20:07.
    #   - "espacio insuficiente" -> el otro frente todavia tiene su copia en RAM
    if grep -qE "ABORT: la BD esta en uso|ABORT: la BD ya es un symlink|ABORT: BD no encontrada|ABORT: espacio insuficiente" "$SALIDA"; then
      esperas=$(( esperas + 1 ))
      if [ "$esperas" -ge "$MAX_ESPERAS" ]; then
        log "ABORTA: BD tomada por otro proceso tras $esperas reintentos"; exit 1
      fi
      log "  BD tomada por otro frente (no es error) — reintento en $((ESPERA_LOCK/60)) min (intento $esperas)"
      sleep "$ESPERA_LOCK"
      continue
    fi
    tail -20 "$SALIDA" | tee -a "$MAESTRO" >/dev/null
    break
  done

  if [ -f "$RUNDIR/BACKLOG_VACIO" ]; then
    log "BACKLOG AGOTADO en la tanda $n. Fin de la corrida."
    break
  fi

  if [ $rc -ne 0 ]; then
    log "  tanda $n termino rc=$rc (ver $RUNDIR/tanda_$(printf %02d $n).log)"
  fi

  # 3. Reporte corto de progreso de la tanda.
  /usr/bin/python3 scripts/ops/backlog_nlp_reporte.py --rundir "$RUNDIR" | tee -a "$MAESTRO"

  # Respiro entre tandas: deja la BD en disco para los otros frentes.
  sleep 60
done

log "=========================================================="
log "CORRIDA TERMINADA"
/usr/bin/python3 scripts/ops/backlog_nlp_reporte.py --rundir "$RUNDIR" --final | tee -a "$MAESTRO"
