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
IDS_PREV=""
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
    # Guarda anti-estancamiento: si el selector devuelve EXACTAMENTE lo mismo
    # que la vuelta anterior, esas ofertas no salen del universo (el pipeline
    # las saltea sin tocar matching_version — p.ej. padres multi-posicion).
    # Sin esta guarda el loop es infinito (observado 2026-08-22: 13 ofertas,
    # ~1.950 vueltas). Se cortan como remanente documentado, no como error.
    if [ "$IDS" = "$IDS_PREV" ]; then
        log "universo ESTANCADO: la misma seleccion dos veces seguidas ($(echo "$IDS" | tr ',' '\n' | wc -l) ofertas que el pipeline no re-matchea). Remanente: $IDS"
        log "re-matching COMPLETO (con remanente estancado) tras $N chunks"
        break
    fi
    IDS_PREV="$IDS"
    N=$((N + 1))
    NIDS=$(echo "$IDS" | tr ',' '\n' | wc -l)
    log "chunk $N: $NIDS ofertas"
    # OLLAMA_HOST queda SIN setear a proposito: la validacion LLM de
    # multi-perfil degrada a SINGLE (0 expandidas) y eso es lo correcto por
    # alcance — el frente L re-decide SOLO el matching; sub-ofertas nuevas
    # sin NLP contaminarian el universo y los cohorts de medicion.
    /usr/bin/python3 scripts/run_validated_pipeline.py --ids "$IDS" --skip-nlp --quiet >> "$LOG" 2>&1
    rc=$?
    # rc=1 con --ids = "hay errores que requieren atencion" (patrones_claude):
    # resultado esperado del re-matching masivo — quedan persistidos en
    # validation_errors y se analizan en la medicion P3. Solo rc>1 (crash
    # real del pipeline) corta la corrida.
    if [ $rc -eq 1 ]; then
        log "chunk $N: rc=1 (errores esperados, persistidos en validation_errors) — sigo"
    elif [ $rc -ne 0 ]; then
        log "chunk $N FALLO (rc=$rc) — corto para diagnostico (reanudable: el universo se recomputa)"
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
