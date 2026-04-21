-- Migration 057: Tabla de tendencia de demanda por ISCO
-- Calculada por scripts/calculate_demand_trends.py
-- Leída por el dashboard en M3 Futuro Laboral

CREATE TABLE IF NOT EXISTS isco_demand_trend (
  isco_code         TEXT PRIMARY KEY,
  trend_slope       REAL,           -- pendiente normalizada (share/mes)
  trend_pvalue      REAL,           -- significancia estadística
  trend_r2          REAL,           -- bondad de ajuste
  trend_label       TEXT,           -- 'creciendo' | 'estable' | 'cayendo' | 'insuficiente'
  volatility_cv     REAL,           -- coef variación de residuos
  volatility_label  TEXT,           -- 'estable' | 'variable' | 'volatil'
  ofertas_total     INT,            -- ofertas en ventana de análisis
  meses_con_datos   INT,            -- meses con >= 1 oferta
  portales_usados   INT,            -- portales estables usados en cálculo
  proyeccion_3m     REAL,           -- share proyectado a 3 meses
  proyeccion_ci     REAL,           -- intervalo de confianza (±)
  monthly_counts    JSONB,          -- array de counts mensuales para sparkline
  monthly_labels    JSONB,          -- array de etiquetas "YYYY-MM"
  suficiente        BOOLEAN DEFAULT false, -- cumple criterios mínimos para estimar
  calculated_at     TIMESTAMPTZ DEFAULT now()
);

-- RLS: lectura pública
ALTER TABLE isco_demand_trend ENABLE ROW LEVEL SECURITY;
CREATE POLICY "isco_demand_trend_read" ON isco_demand_trend FOR SELECT USING (true);

-- Index para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_isco_trend_label ON isco_demand_trend(trend_label) WHERE suficiente = true;
