-- ============================================
-- Tabla sistema_estado para /admin/scraping
-- Estado del sistema de scraping (Fase 1)
-- ============================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS sistema_estado (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  timestamp TIMESTAMPTZ DEFAULT NOW(),

  -- Fase 1: Adquisición (Scraping)
  fase1_ofertas_totales INTEGER DEFAULT 0,
  fase1_ofertas_activas INTEGER DEFAULT 0,
  fase1_ofertas_cerradas INTEGER DEFAULT 0,
  fase1_ultimo_scraping TEXT,
  fase1_dias_desde_scraping INTEGER DEFAULT 0,
  fase1_fuentes JSONB DEFAULT '{"bumeran": 0, "zonajobs": 0, "computrabajo": 0}'::jsonb,

  -- Fase 2: Procesamiento (NLP, Matching)
  fase2_con_nlp INTEGER DEFAULT 0,
  fase2_con_matching INTEGER DEFAULT 0,
  fase2_validadas INTEGER DEFAULT 0,
  fase2_errores_pendientes INTEGER DEFAULT 0,
  fase2_reglas_negocio INTEGER DEFAULT 0,

  -- Fase 3: Presentación (Dashboard)
  fase3_ofertas_supabase INTEGER DEFAULT 0,
  fase3_pendientes_sync INTEGER DEFAULT 0
);

-- 2. Índice para ordenar por timestamp
CREATE INDEX IF NOT EXISTS idx_sistema_estado_timestamp ON sistema_estado(timestamp DESC);

-- 3. Insertar estado inicial (ejemplo)
-- Este INSERT se hace desde sync_to_supabase.py
INSERT INTO sistema_estado (
  fase1_ofertas_totales,
  fase1_ofertas_activas,
  fase1_ofertas_cerradas,
  fase1_ultimo_scraping,
  fase1_dias_desde_scraping,
  fase1_fuentes,
  fase2_con_nlp,
  fase2_con_matching,
  fase2_validadas,
  fase3_ofertas_supabase
) VALUES (
  5000,  -- ofertas totales (ajustar con datos reales)
  3500,  -- activas
  1500,  -- cerradas
  '2026-02-05',
  1,
  '{"bumeran": 1500, "zonajobs": 1200, "computrabajo": 800, "indeed": 300, "linkedin": 200}'::jsonb,
  4800,
  4500,
  538,
  538
);

-- 4. Verificar
SELECT * FROM sistema_estado ORDER BY timestamp DESC LIMIT 1;
