-- 025_pipeline_observabilidad.sql
-- SPEC S1C-F0.3 — Observabilidad del Eje 1: acta de corrida + alertas
-- Fecha: 2026-06-16
--
-- ADITIVA: no toca pipeline_runs (matching-scoped) ni la tabla legacy 'alertas'.
-- Crea dos tablas nuevas locales:
--   pipeline_run_actas  -> acta a nivel-corrida (fuente de verdad), escrita por run_validated_pipeline.py
--   pipeline_alertas    -> registro estructurado de fallos del pipeline

-- ── Acta de corrida ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_run_actas (
    acta_id            TEXT PRIMARY KEY,   -- acta_YYYYMMDD_HHMMSS
    started_at         TEXT NOT NULL,      -- inicio (al entrar a run_full_pipeline)
    finished_at        TEXT,               -- fin; NULL mientras corre
    invocador          TEXT,               -- 'poller' | 'terminal'
    args               TEXT,               -- flags de invocacion (limit/ids/skip-*)
    alcance_entrada    INTEGER,            -- ofertas que entraron
    alcance_procesado  INTEGER,            -- ofertas efectivamente procesadas
    resultado          TEXT,               -- 'ok' | 'fallida' | 'incompleta' | NULL (en curso)
    fallos             TEXT,               -- JSON array de alertas-clave de esta corrida
    matching_run_id    TEXT,               -- FK logica a pipeline_runs.run_id (si llego a matching)
    pid                INTEGER,            -- PID del proceso que abrio el acta
    host               TEXT                -- hostname (PID solo comparable dentro del mismo host)
);

-- Buscar actas abiertas (barrido de huerfanas) y ordenar por recencia
CREATE INDEX IF NOT EXISTS idx_actas_abiertas   ON pipeline_run_actas(finished_at);
CREATE INDEX IF NOT EXISTS idx_actas_started     ON pipeline_run_actas(started_at);

-- ── Registro de alertas ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_alertas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    severidad   TEXT NOT NULL,             -- 'info' | 'warning' | 'error' | 'critico'
    tipo        TEXT NOT NULL,             -- ollama_down | nlp_fallo | paso_bloqueante
                                           --   | sync_no_corrio | corrida_incompleta | export_fallo
    mensaje     TEXT NOT NULL,             -- texto claro y accionable
    acta_id     TEXT,                      -- corrida asociada (NULL si no aplica)
    contexto    TEXT                       -- JSON con detalle
);

CREATE INDEX IF NOT EXISTS idx_alertas_timestamp ON pipeline_alertas(timestamp);
CREATE INDEX IF NOT EXISTS idx_alertas_acta      ON pipeline_alertas(acta_id);
