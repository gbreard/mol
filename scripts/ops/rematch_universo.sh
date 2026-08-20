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

# 1) esperar a que no haya pipeline vivo (arbitraje: nosotros primero al tmpfs)
while pgrep -f "run_validated_pipeline" >/dev/null 2>&1; do
    log "pipeline ajeno vivo — espero 300s (arbitraje tmpfs: el re-matching arranca primero o no arranca)"
    sleep 300
done
log "BD sin pipelines vivos — arrancando sesion tmpfs"

exec "$REPO/scripts/ops/run_con_tmpfs.sh" /bin/bash "$REPO/scripts/ops/rematch_universo_inner.sh" "$CHUNK" "$TG"
