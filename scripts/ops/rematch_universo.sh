#!/bin/bash
# rematch_universo.sh — [FRENTE L] Re-matching masivo por tandas, parametrizado para re-uso.
#
# Re-decide el matching (SOLO matching, --skip-nlp) de todas las ofertas con NLP cuyo
# matching_version sea anterior a la actual, en tandas, bajo run_con_tmpfs.sh.
# El universo se recomputa en cada tanda (idempotente/reanudable: lo ya re-matcheado
# sale del universo por su matching_version nueva).
#
# CANDADO (F0.4b): excluye SIEMPRE estado_validacion IN (validado, en_revision) y
# occupation_match_method='rule_manual_fix'. El trigger de BD protege ademas 'validado'.
#
# Coordinacion (arbitraje tmpfs): NO arranca si hay un run_validated_pipeline vivo
# (ese proceso tendria el archivo real abierto por inode y sus escrituras divergirian
# del sync-back). Una vez adentro del tmpfs, lo que el poller lance escribe al symlink
# y queda capturado. Espera pasiva con reintentos.
#
# Uso:  scripts/ops/rematch_universo.sh [chunk=2500] [tanda_grande=4]
#   (tanda_grande = cada cuantos chunks corre el TEST rapido del evaluador)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CHUNK="${1:-2500}"
TG="${2:-4}"
LOG=/tmp/mol_rematch_l.log

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# 1) esperar a que no haya pipeline vivo NI sesion tmpfs ajena (arbitraje:
#    nosotros primero al tmpfs). El symlink cubre la ventana de sync-back del
#    backlog NLP, cuando ya no hay run_validated_pipeline pero la BD sigue en RAM.
esperar_bd() {
    while pgrep -f "run_validated_pipeline" >/dev/null 2>&1 \
          || [ -L "$REPO/database/bumeran_scraping.db" ]; do
        log "BD tomada (pipeline vivo o sesion tmpfs ajena) — espero 300s (arbitraje: el re-matching arranca primero o no arranca)"
        sleep 300
    done
}

# 2) tomar la BD con reintento: si run_con_tmpfs.sh pierde la carrera contra
#    otro frente (symlink / write-lock / shm ocupado por la sesion saliente),
#    NO es error — se espera y reintenta (mismo patron que backlog_nlp_run.sh).
#    Cualquier otro ABORT (hash, integridad) o un fallo del inner corta en serio.
SALIDA=/tmp/mol_rematch_l_tmpfs.out
while true; do
    esperar_bd
    log "BD libre — arrancando sesion tmpfs"
    "$REPO/scripts/ops/run_con_tmpfs.sh" /bin/bash "$REPO/scripts/ops/rematch_universo_inner.sh" "$CHUNK" "$TG" > "$SALIDA" 2>&1
    rc=$?
    if grep -qE "ABORT: la BD ya es un symlink|ABORT: la BD esta en uso|ABORT: espacio insuficiente" "$SALIDA"; then
        log "perdi la carrera por la BD (no es error) — reintento en 300s"
        sleep 300
        continue
    fi
    tail -5 "$SALIDA" | tee -a "$LOG" >/dev/null
    if [ $rc -ne 0 ]; then
        log "sesion tmpfs termino rc=$rc — corto para diagnostico (ver $SALIDA)"
        exit $rc
    fi
    break
done
log "driver: fin ok"
