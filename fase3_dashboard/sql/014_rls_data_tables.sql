-- =============================================================================
-- 014_rls_data_tables.sql  —  S-03 Fix: RLS policies for data tables
-- =============================================================================
-- Fixes:
--   1. esco_argentino: overly permissive policy (any authenticated user can write)
--   2. sistema_estado: missing RLS
--   3. tension_ocupaciones: missing RLS (conditional — table may not exist)
--   4. perfiles_trabajadores: overly permissive policy (conditional)
--   5. audit_log: missing/broken policies (conditional)
-- =============================================================================

-- Helper: check if current user is platform admin via user_metadata
-- (idempotent — only creates if not exists)
CREATE OR REPLACE FUNCTION public.is_platform_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT coalesce(
    (auth.jwt() -> 'user_metadata' ->> 'role') IN ('admin', 'super_admin'),
    false
  );
$$;


-- =============================================================================
-- 1. FIX esco_argentino  — DROP permissive policy, add restrictive ones
-- =============================================================================

-- Drop existing overly permissive policy
DROP POLICY IF EXISTS "Usuarios autenticados pueden gestionar esco_argentino" ON public.esco_argentino;
DROP POLICY IF EXISTS "esco_argentino_select_public" ON public.esco_argentino;
DROP POLICY IF EXISTS "esco_argentino_write_admin" ON public.esco_argentino;

-- RLS should already be enabled from 007_esco_argentino.sql, but ensure it
ALTER TABLE public.esco_argentino ENABLE ROW LEVEL SECURITY;

-- SELECT: anyone can read (public reference data)
CREATE POLICY "esco_argentino_select_public"
  ON public.esco_argentino
  FOR SELECT
  USING (true);

-- INSERT/UPDATE/DELETE: only service_role (bypasses RLS) or platform admins
CREATE POLICY "esco_argentino_write_admin"
  ON public.esco_argentino
  FOR ALL
  USING (public.is_platform_admin())
  WITH CHECK (public.is_platform_admin());


-- =============================================================================
-- 2. sistema_estado  — Enable RLS, public read, service_role write
-- =============================================================================

ALTER TABLE public.sistema_estado ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "sistema_estado_select_public" ON public.sistema_estado;
DROP POLICY IF EXISTS "sistema_estado_write_service" ON public.sistema_estado;

-- Anyone can read system state (dashboard metrics)
CREATE POLICY "sistema_estado_select_public"
  ON public.sistema_estado
  FOR SELECT
  USING (true);

-- Writes only via service_role (which bypasses RLS) — no explicit write policy
-- needed since service_role is exempt. But we add admin as fallback.
CREATE POLICY "sistema_estado_write_service"
  ON public.sistema_estado
  FOR ALL
  USING (public.is_platform_admin())
  WITH CHECK (public.is_platform_admin());


-- =============================================================================
-- 3. tension_ocupaciones  — Conditional (table may not exist yet)
-- =============================================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'tension_ocupaciones'
  ) THEN
    EXECUTE 'ALTER TABLE public.tension_ocupaciones ENABLE ROW LEVEL SECURITY';

    -- Drop if exists to make idempotent
    EXECUTE 'DROP POLICY IF EXISTS "tension_ocupaciones_select_public" ON public.tension_ocupaciones';
    EXECUTE 'DROP POLICY IF EXISTS "tension_ocupaciones_write_admin" ON public.tension_ocupaciones';

    EXECUTE '
      CREATE POLICY "tension_ocupaciones_select_public"
        ON public.tension_ocupaciones
        FOR SELECT
        USING (true)
    ';

    EXECUTE '
      CREATE POLICY "tension_ocupaciones_write_admin"
        ON public.tension_ocupaciones
        FOR ALL
        USING (public.is_platform_admin())
        WITH CHECK (public.is_platform_admin())
    ';

    RAISE NOTICE 'RLS configured for tension_ocupaciones';
  ELSE
    RAISE NOTICE 'tension_ocupaciones does not exist — skipping';
  END IF;
END $$;


-- =============================================================================
-- 4. perfiles_trabajadores  — Fix permissive policy, scope to created_by
-- =============================================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'perfiles_trabajadores'
  ) THEN
    EXECUTE 'ALTER TABLE public.perfiles_trabajadores ENABLE ROW LEVEL SECURITY';

    -- Drop existing permissive policies
    EXECUTE 'DROP POLICY IF EXISTS "perfiles_trabajadores_select" ON public.perfiles_trabajadores';
    EXECUTE 'DROP POLICY IF EXISTS "perfiles_trabajadores_insert" ON public.perfiles_trabajadores';
    EXECUTE 'DROP POLICY IF EXISTS "perfiles_trabajadores_update" ON public.perfiles_trabajadores';
    EXECUTE 'DROP POLICY IF EXISTS "perfiles_trabajadores_delete" ON public.perfiles_trabajadores';
    EXECUTE 'DROP POLICY IF EXISTS "Usuarios autenticados pueden gestionar perfiles" ON public.perfiles_trabajadores';

    -- SELECT: users see their own profiles, admins see all
    EXECUTE '
      CREATE POLICY "perfiles_trabajadores_select"
        ON public.perfiles_trabajadores
        FOR SELECT
        USING (
          auth.uid() = created_by
          OR public.is_platform_admin()
        )
    ';

    -- INSERT: authenticated users can create (created_by set by app)
    EXECUTE '
      CREATE POLICY "perfiles_trabajadores_insert"
        ON public.perfiles_trabajadores
        FOR INSERT
        WITH CHECK (auth.role() = ''authenticated'')
    ';

    -- UPDATE: only own profiles or admin
    EXECUTE '
      CREATE POLICY "perfiles_trabajadores_update"
        ON public.perfiles_trabajadores
        FOR UPDATE
        USING (
          auth.uid() = created_by
          OR public.is_platform_admin()
        )
    ';

    -- DELETE: only admin
    EXECUTE '
      CREATE POLICY "perfiles_trabajadores_delete"
        ON public.perfiles_trabajadores
        FOR DELETE
        USING (public.is_platform_admin())
    ';

    RAISE NOTICE 'RLS configured for perfiles_trabajadores';
  ELSE
    RAISE NOTICE 'perfiles_trabajadores does not exist — skipping';
  END IF;
END $$;


-- =============================================================================
-- 5. audit_log  — Conditional: admin read, authenticated insert
-- =============================================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'audit_log'
  ) THEN
    EXECUTE 'ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY';

    EXECUTE 'DROP POLICY IF EXISTS "audit_log_select_admin" ON public.audit_log';
    EXECUTE 'DROP POLICY IF EXISTS "audit_log_insert_auth" ON public.audit_log';

    -- Only admins can read audit logs
    EXECUTE '
      CREATE POLICY "audit_log_select_admin"
        ON public.audit_log
        FOR SELECT
        USING (public.is_platform_admin())
    ';

    -- Any authenticated user can insert (log their actions)
    EXECUTE '
      CREATE POLICY "audit_log_insert_auth"
        ON public.audit_log
        FOR INSERT
        WITH CHECK (auth.role() = ''authenticated'')
    ';

    RAISE NOTICE 'RLS configured for audit_log';
  ELSE
    RAISE NOTICE 'audit_log does not exist — skipping';
  END IF;
END $$;


-- =============================================================================
-- Verification query (run after execution)
-- =============================================================================
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY tablename;
