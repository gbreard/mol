-- Migration 034: Scraping live stats — stats reales del VPS
-- El VPS sube esto después de cada corrida de scraping

CREATE TABLE IF NOT EXISTS scraping_live_stats (
  id TEXT PRIMARY KEY DEFAULT 'current',
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  total_ofertas INTEGER DEFAULT 0,
  portales JSONB DEFAULT '{}'::jsonb,  -- {bumeran: {total, ultimo_scraping}, ...}
  ultimo_scraping TIMESTAMPTZ
);

INSERT INTO scraping_live_stats (id) VALUES ('current') ON CONFLICT DO NOTHING;

ALTER TABLE scraping_live_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "scraping_live_stats_read" ON scraping_live_stats
  FOR SELECT USING (true);

CREATE POLICY "scraping_live_stats_write" ON scraping_live_stats
  FOR ALL USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
