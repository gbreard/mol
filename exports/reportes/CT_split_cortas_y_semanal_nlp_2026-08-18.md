# [PARALELOS] Split de las cortas de CT + corrida semanal de NLP (2026-08-18)

## 1. El split — veredicto: NULL-de-guarda, 73/73

La ventana de salud vigente (`metrics/salud_scrape.json`, corrida 2026-08-18 08:00, ventana 3 días) marca **computrabajo 73/518 cortas (14,1%, alerta)** — el "63" del encargo corresponde a una corrida previa del histórico (68 el 06-08; el número fluctúa por ventana móvil).

Split de las 73 con el MISMO SQL del chequeo (`LENGTH(COALESCE(descripcion,'')) < 300`, portal='computrabajo', 3 días):

| Categoría | n |
|---|---|
| **NULL/vacía (guarda del fix J: el wall que el JSON-LD no salvó → no se guarda muda)** | **73** |
| Texto <300 con firma de boilerplate (template CT: "somos la comunidad", "publica tu cv"…) | **0** |
| Texto corto genuino | **0** |

**Veredicto: NULLs honestos, cero boilerplate filtrándose.** La guarda del scraper funciona exactamente como se diseñó — la alerta del 14,1% mide walls de Cloudflare/JSON-LD ausente, no contaminación. La alerta del semáforo queda como está (es señal de salud del portal, no bug nuestro).

## 2. La corrida semanal de NLP — programada

**Cron agregado (local WSL, cron activo verificado):**
```
5 9 * * 6 cd /mnt/d/OEDE/Webscrapping && OLLAMA_HOST=172.17.0.1 scripts/ops/run_con_tmpfs.sh /usr/bin/python3 scripts/run_validated_pipeline.py --limit 2000 >> /tmp/mol_nlp_semanal.log 2>&1
```

**Criterio operativo documentado:**
- **Sábado 09:05**: después de los dos ciclos scrape+sync de la semana (VPS lun/jue 08:00 + syncs locales), máquina típicamente sin sesiones de trabajo (el wrapper tmpfs exige write-lock exclusivo de la BD y aborta si está en uso — un día de semana chocaría con sesiones activas); 09:05 y no 09:00 para no correr contra el arranque del auto_sync horario.
- **Camino de I/O**: `run_con_tmpfs.sh` (BD a /dev/shm con sha256 + sync-back verificado — el patrón institucionalizado del incidente 9p del FRENTE D).
- **Entry point**: `run_validated_pipeline.py --limit 2000` — el canónico (nota: `launch_nlp_batch.py` ya no existe en el repo; CLAUDE.md lo cita — desactualizado).
- **Primera corrida: sábado 2026-08-22, 09:05** (la instrucción llegó cortada en "primera corrida =" — default operativo: el primer slot programado; si se quería una corrida inmediata, es un comando: `scripts/ops/run_con_tmpfs.sh python scripts/run_validated_pipeline.py --limit 2000` con Ollama arriba).

**Decisión pendiente anotada (no es de este frente):** el backlog histórico sin NLP es **26.559** ofertas. La semanal de 2.000 acompaña el flujo fresco (~2-3K/semana) pero NO come el histórico — eso pide una corrida dedicada tipo FRENTE D (lote grande, varios días), a laudar aparte.

## 3. El paquete de las 71 (tarea 1)

`exports/cyn_backlog/paquete_71_reglas_2026-08-18.md`: las 71 reglas post-export con condición/destino/volumen + 5-8 avisos c/u en el formato pedido por JD (id | título | tareas | decisión), ordenadas por volumen, con las «primas» señaladas (la muestra ya lo justifica sola: R353 está decidiendo «Operarios de producción» con tareas de sobadora y máquinas de corte como mozo-de-almacén). Sección nueva: **el satélite 3343.1** — 229 títulos «auxiliar/asistente administrativo» que la telemetría v3 detectó cayendo al dict grueso ISCO:4110, con muestra de 8 y la pregunta binaria para Cyn (¿división fina ahora o espera el hub de oficina?).
