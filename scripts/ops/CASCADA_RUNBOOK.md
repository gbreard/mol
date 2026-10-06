# [CASCADA v12.4] RUNBOOK — pausar / reanudar / monitorear la re-extracción P1

> La corrida es **resumible por diseño**: escribe a `database/cascada_staging.db` y el runner
> saltea lo ya hecho (`WHERE id NOT IN staging`). Pausar = matar el proceso (pierde solo la
> oferta en curso; commitea cada 10). Reanudar = relanzar. Nada se re-procesa.

## Estado / ¿está corriendo?
```bash
cd /mnt/d/OEDE/Webscrapping
pgrep -af "reextraccion_tareas_v124" | grep python3    # muestra PID si corre
```

## Progreso (agnóstico de esquema)
```bash
cd /mnt/d/OEDE/Webscrapping
python3 - <<'PY'
import sqlite3
c=sqlite3.connect('file:database/cascada_staging.db?mode=ro',uri=True)
tot=c.execute("SELECT COUNT(*) FROM ofertas_nlp_tareas_v124").fetchone()[0]
vac=c.execute("SELECT COUNT(*) FROM ofertas_nlp_tareas_v124 WHERE n_tareas=0").fetchone()[0]
print(f"hechas={tot} / ~116.900  ({100*tot/116900:.1f}%)   vacías={vac} ({100*vac/max(tot,1):.1f}%)")
PY
```

## ⏸ PAUSAR la corrida
```bash
pkill -f "reextraccion_tareas_v124"          # o: kill <PID>
sleep 3; pgrep -af reextraccion_tareas_v124 | grep python3 || echo "pausada (progreso guardado)"
```
Seguro: el último commit fue ≤10 ofertas atrás; esas ≤10 se re-hacen al reanudar. No corrompe.

## ▶ REANUDAR (continúa donde quedó, saltea lo hecho)
```bash
cd /mnt/d/OEDE/Webscrapping
OLLAMA_HOST=172.17.0.1 MODEL_TAREAS=qwen2.5:14b \
  nohup python3 scripts/ops/reextraccion_tareas_v124.py --limit 15000 --tanda dNN \
  > /tmp/cascada_dNN.log 2>&1 &
tail -f /tmp/cascada_dNN.log      # Ctrl-C para dejar de mirar (la corrida sigue)
```
- Cambiá `dNN` por la próxima etiqueta (d03, d04, …) — es solo metadato de tanda.
- `--limit` = cuántas ofertas en esta tanda (~15.000 ≈ 1 día). Para el resto completo: `--limit 200000`.
- Orden automático: **re-extracciones primero, primeras-extracciones después** (el shadow P3 necesita las re-ext). No hay que indicarlo.
- (Claude normalmente la lanza harness-tracked para que le avise al cerrar; este `nohup &` es el equivalente manual.)

## 🔁 Reanudación tras reinicio de WSL / máquina
Igual que REANUDAR: el staging persiste en disco. Relanzás y continúa.

---

# Ventana de pausa de ESCRITORES (solo para el SWAP del gate P3 — NO para la re-extracción)

La re-extracción NO necesita esto (escribe a su DB propia). Esto es para el **swap
staging→tabla viva** (gate P3, antes de P4), donde SÍ se escribe el main DB. Ver
`exports/reportes/CASCADA_DISEÑO_swap_P3.md`.

```bash
# 1. backup del crontab y sacar el poller (cron cada minuto que escribe el main)
crontab -l > /tmp/crontab.bak
crontab -l | grep -v pipeline_command_poller | crontab -
# 2. confirmar que no haya sync activo
pgrep -af "sync_scraping_dinamica|sync_from_vps" || echo "sin sync activo — OK"
# 3. elegir ventana fuera de crons: NO :00 (auto_sync), NO 0/3h (indeed), NO 6:15, NO 7:00
# 4. ... correr el swap ...
# 5. restaurar el crontab
crontab /tmp/crontab.bak
```
