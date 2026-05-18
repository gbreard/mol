import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseAdmin: SupabaseClient | null = null;
function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } });
  return supabaseAdmin;
}

interface RunRow {
  timestamp: string;
  ofertas_count: number | null;
  errores_escalados: number | null;
}

function tasaEscaladosPct(runs: RunRow[]): number {
  const validos = runs.filter((r) => (r.ofertas_count ?? 0) > 0);
  if (validos.length === 0) return 0;
  const ratios = validos.map((r) => (r.errores_escalados ?? 0) / (r.ofertas_count ?? 1));
  const mean = ratios.reduce((a, b) => a + b, 0) / ratios.length;
  return Math.round(mean * 100 * 10) / 10;
}

// GET /api/processing-metrics — metrics for learning dashboard
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  try {
    // Resolved issues for training pairs count
    const { data: issues } = await client
      .from('issues')
      .select('id, resuelto_at')
      .eq('estado', 'resuelto')
      .not('id_oferta', 'is', null)
      .order('resuelto_at', { ascending: false })
      .limit(500);

    // Últimos N runs para tasa_error_actual y primer run para baseline
    const { data: runsRecientes } = await client
      .from('pipeline_runs_history')
      .select('timestamp, ofertas_count, errores_escalados')
      .order('timestamp', { ascending: false })
      .limit(5);

    // Baseline: primer run con errores escalados > 0 (los runs muy viejos no medían escalados)
    const { data: primerRun } = await client
      .from('pipeline_runs_history')
      .select('timestamp, ofertas_count, errores_escalados')
      .gt('ofertas_count', 0)
      .gt('errores_escalados', 0)
      .order('timestamp', { ascending: true })
      .limit(1);

    const tasaErrorActual = tasaEscaladosPct((runsRecientes as RunRow[]) || []);
    const tasaErrorInicial = tasaEscaladosPct((primerRun as RunRow[]) || []);

    // Timeline desde pipeline_runs_history (agrupado por día, últimos 60 días)
    const sinceISO = new Date(Date.now() - 60 * 86400000).toISOString();
    const { data: runsTimeline } = await client
      .from('pipeline_runs_history')
      .select('timestamp, ofertas_count, errores_escalados')
      .gte('timestamp', sinceISO)
      .gt('ofertas_count', 0)
      .order('timestamp', { ascending: true });

    const byDay: Record<string, { ofertas: number; escalados: number }> = {};
    for (const run of (runsTimeline as RunRow[]) || []) {
      const day = run.timestamp.split('T')[0];
      if (!byDay[day]) byDay[day] = { ofertas: 0, escalados: 0 };
      byDay[day].ofertas += run.ofertas_count ?? 0;
      byDay[day].escalados += run.errores_escalados ?? 0;
    }
    const timeline_errores = Object.entries(byDay)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([fecha, { ofertas, escalados }]) => ({
        fecha,
        total_procesadas: ofertas,
        tasa_error: ofertas > 0 ? Math.round((escalados / ofertas) * 100 * 10) / 10 : 0,
      }));

    // Reglas activas desde config_overrides
    const { data: configOverride } = await client
      .from('config_overrides')
      .select('json_value, version')
      .eq('config_key', 'matching_rules_business')
      .maybeSingle();

    let totalReglasActivas = 0;
    if (configOverride?.json_value?.reglas_forzar_isco) {
      totalReglasActivas = Object.keys(configOverride.json_value.reglas_forzar_isco)
        .filter((k: string) => k !== 'descripcion').length;
    }

    return NextResponse.json({
      aprendizaje: {
        total_reglas_activas: totalReglasActivas,
        total_reglas_creadas: totalReglasActivas,
        tasa_error_actual: tasaErrorActual,
        tasa_error_inicial: tasaErrorInicial,
        timeline_errores,
        timeline_reglas: [],
        gold_set: [],
      },
      training_pairs: (issues || []).length,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Error desconocido';
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
