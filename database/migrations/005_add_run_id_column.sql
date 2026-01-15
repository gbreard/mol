-- Migration 005: Add run_id column to ofertas_esco_matching
-- Date: 2026-01-13
-- Purpose: Support run-based versioning for tracking pipeline executions

-- Add run_id column to ofertas_esco_matching
ALTER TABLE ofertas_esco_matching ADD COLUMN run_id TEXT;

-- Create index for faster run queries
CREATE INDEX IF NOT EXISTS idx_ofertas_esco_matching_run_id ON ofertas_esco_matching(run_id);

-- Existing data gets NULL run_id (processed before run tracking was implemented)
