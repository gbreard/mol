#!/bin/bash
# rematch_universo_inner.sh — corre DENTRO de run_con_tmpfs.sh (BD ya en RAM via symlink).
set -uo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
CHUNK="${1:-2500}"
TG="${2:-4}"
LOG=/tmp/mol_rematch_l.log
cd "$REPO"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

N=0
while true; do
    IDS=$(/usr/bin/python3 - "$CHUNK" <<'PY'
import sqlite3, sys
con = sqlite3.connect('database/bumeran_scraping.db')
rows = con.execute("""
  SELECT m.id_oferta FROM ofertas_esco_matching m
  JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
  WHERE n.titulo_limpio != ''
    AND COALESCE(m.matching_version,'') NOT LIKE '3.6%'
    AND COALESCE(m.estado_validacion,'') NOT IN ('validado','en_revision')
    AND COALESCE(m.occupation_match_method,'') != 'rule_manual_fix'
  LIMIT ?""", (int(sys.argv[1]),)).fetchall()
print(','.join(str(r[0]) for r in rows))
PY
)
    if [ -z "$IDS" ]; then
        log "universo agotado — re-matching COMPLETO tras $N chunks"
        break
    fi
    N=$((N + 1))
    NIDS=$(echo "$IDS" | tr ',' '\n' | wc -l)
    log "chunk $N: $NIDS ofertas"
    if ! /usr/bin/python3 scripts/run_validated_pipeline.py --ids "$IDS" --skip-nlp --quiet >> "$LOG" 2>&1; then
        log "chunk $N FALLO (exit $?) — corto para diagnostico (reanudable: el universo se recomputa)"
        exit 1
    fi
    if [ $((N % TG)) -eq 0 ]; then
        log "TEST rapido del evaluador (tanda grande #$((N / TG)))"
        if ! "$HOME/.local/bin/pytest" tests/matching/test_traductor_contexto.py tests/matching/test_subordinacion_l4.py -q >> "$LOG" 2>&1; then
            log "TEST FALLO — corto"
            exit 2
        fi
    fi
done
log "fin ok"
