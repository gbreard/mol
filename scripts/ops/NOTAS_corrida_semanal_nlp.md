# Corrida semanal de NLP — notas de operación

**Crontab actual (local, sáb 09:05):**
```
5 9 * * 6 cd /mnt/d/OEDE/Webscrapping && OLLAMA_HOST=172.17.0.1 scripts/ops/run_con_tmpfs.sh /usr/bin/python3 scripts/run_validated_pipeline.py --limit 2000 >> /tmp/mol_nlp_semanal.log 2>&1
```

## EXPERIMENTO PENDIENTE (2026-08-23): `--max-nlp-iterations 1`

**Qué:** una tanda de prueba el **próximo sábado (2026-08-29)** con `--max-nlp-iterations 1` (default actual: 2 — el paso 5 re-procesa NLP de los bloqueados por el gate y re-valida, hasta 2 iteraciones).

**Hipótesis (del cierre del backlog):** la segunda iteración de NLP aporta poco (el auto-corrector ya arregla lo arreglable) y cuesta ~un tercio del tiempo de tanda; con 1 iteración el throughput sube sin degradar el gate.

**Cómo correrlo (una sola vez, manual o editando el cron SOLO esa semana):**
```
OLLAMA_HOST=172.17.0.1 scripts/ops/run_con_tmpfs.sh /usr/bin/python3 \
  scripts/run_validated_pipeline.py --limit 2000 --max-nlp-iterations 1
```

**Qué comparar contra la corrida anterior (mismas métricas del gate):**
- % bloqueadas por el NLP Gate al cierre (aprobado/bloqueado en `nlp_gate_status`)
- errores `error_nlp_%` persistidos en `validation_errors` por 1.000 ofertas
- escaladas a Claude (`escalado_claude=1`)
- duración total de la tanda (log `/tmp/mol_nlp_semanal.log`)

**Decisión:** si el gate no empeora (>1pp) y la tanda acelera, cambiar el default de la corrida semanal a 1 iteración (editar crontab + esta nota). Si empeora, cerrar el experimento y anotar acá.
