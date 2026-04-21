#!/bin/bash
# Pipeline loop: procesa todas las ofertas sin NLP en lotes de 1000.
# Uso:
#   ./scripts/run_pipeline_loop.sh > /tmp/pipeline_loop.log 2>&1 &

set -e
export OLLAMA_HOST=172.17.0.1
export PYTHONUNBUFFERED=1

cd "$(dirname "$0")/.."

echo "$(date '+%Y-%m-%d %H:%M:%S') — Pipeline loop iniciado"
echo "================================================="

ITERATION=0

while true; do
    ITERATION=$((ITERATION + 1))

    # Contar ofertas sin NLP
    SIN_NLP=$(python3 -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db', timeout=30)
count = conn.execute(\"\"\"
    SELECT COUNT(*) FROM ofertas o
    WHERE NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = o.id_oferta)
\"\"\").fetchone()[0]
print(count)
conn.close()
")

    echo ""
    echo "$(date '+%H:%M:%S') — Iteración $ITERATION — Sin NLP: $SIN_NLP"

    if [ "$SIN_NLP" -eq 0 ] || [ "$SIN_NLP" = "0" ]; then
        echo "Todas las ofertas procesadas."
        break
    fi

    # Correr un lote
    echo "$(date '+%H:%M:%S') — Corriendo pipeline --limit 1000..."
    python3 scripts/run_validated_pipeline.py \
        --force-new-batch --limit 1000 --max-nlp-iterations 1 \
        || echo "$(date '+%H:%M:%S') — Pipeline terminó con error (continuando...)"

    # Estado post-lote
    python3 -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db', timeout=30)
sin_nlp = conn.execute('SELECT COUNT(*) FROM ofertas o WHERE NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = o.id_oferta)').fetchone()[0]
vc = conn.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = \"validado_claude\"').fetchone()[0]
p = conn.execute('SELECT COUNT(*) FROM ofertas_esco_matching WHERE estado_validacion = \"pendiente\"').fetchone()[0]
print(f'  Sin NLP: {sin_nlp} | validado_claude: {vc} | pendiente: {p}')
conn.close()
"

    echo "$(date '+%H:%M:%S') — Lote terminado. Pausa 30s..."
    sleep 30
done

# Al terminar, sync a Supabase
echo ""
echo "$(date '+%H:%M:%S') — Sincronizando a Supabase..."
python3 scripts/exports/sync_to_supabase.py

echo "$(date '+%H:%M:%S') — Todo listo."
