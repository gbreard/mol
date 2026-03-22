import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false }
  });
  return supabaseAdmin;
}

interface TrainingPair {
  id_oferta: string;
  autor: string | null;
  issue_tipo: string;
  resuelto_at: string;
  input: {
    titulo_original: string;
    titulo_limpio: string;
    sector?: string;
    area_funcional?: string;
  };
  clasificacion_incorrecta: { isco_code: string; isco_label: string };
  clasificacion_correcta: { isco_code: string; isco_label: string; metodo?: string };
  justificacion_humana: string;
}

interface TrainingPairsFile {
  version: string;
  fecha_generacion: string;
  total_pares: number;
  pares: TrainingPair[];
}

const ISCO_GROUP_NAMES: Record<string, string> = {
  '0': 'Fuerzas Armadas',
  '1': 'Directivos',
  '2': 'Profesionales',
  '3': 'Técnicos',
  '4': 'Administrativos',
  '5': 'Servicios/Ventas',
  '6': 'Agro/Pesca',
  '7': 'Oficios',
  '8': 'Operadores',
  '9': 'Elementales',
};

// Thresholds for readiness assessment
const MIN_PAIRS_READY = 500;
const MIN_ISCO_DIVERSITY = 50;
const MIN_GROUP_COVERAGE = 7; // at least 7 of 10 major groups
const MIN_PAIRS_PER_ISCO = 3;

function assessReadiness(stats: {
  totalPairs: number;
  distinctIsco: number;
  groupsCovered: number;
  iscoWithMinPairs: number;
}) {
  const checks = [
    { label: 'Pares suficientes', ok: stats.totalPairs >= MIN_PAIRS_READY, detail: `${stats.totalPairs}/${MIN_PAIRS_READY}` },
    { label: 'Diversidad ISCO', ok: stats.distinctIsco >= MIN_ISCO_DIVERSITY, detail: `${stats.distinctIsco}/${MIN_ISCO_DIVERSITY} ISCOs distintos` },
    { label: 'Cobertura de grupos', ok: stats.groupsCovered >= MIN_GROUP_COVERAGE, detail: `${stats.groupsCovered}/${MIN_GROUP_COVERAGE} grupos mayores` },
    { label: 'ISCOs con datos', ok: stats.iscoWithMinPairs >= 30, detail: `${stats.iscoWithMinPairs} ISCOs con ${MIN_PAIRS_PER_ISCO}+ pares` },
  ];

  const passed = checks.filter(c => c.ok).length;
  const ready = passed === checks.length;
  const level = ready ? 'ready' : passed >= 3 ? 'almost' : passed >= 2 ? 'partial' : 'insufficient';

  return { ready, level, checks, passed, total: checks.length };
}

// GET: training readiness stats from Supabase (issues resueltos + ofertas)
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  try {
    // Get resolved issues (source of training pairs)
    const { data: issues, error: issErr } = await client
      .from('issues')
      .select('id, titulo, estado, campo, valor_actual, valor_esperado, id_oferta, resuelto_at, created_by')
      .eq('estado', 'resuelto')
      .not('id_oferta', 'is', null)
      .order('resuelto_at', { ascending: false });

    if (issErr) throw new Error(issErr.message);

    const pairs = issues || [];
    const totalPairs = pairs.length;

    // ISCO distribution from valor_esperado
    const iscoCounts: Record<string, { count: number; label: string }> = {};
    const autores: Record<string, number> = {};

    for (const p of pairs) {
      const isco = p.valor_esperado?.toString().match(/^\d{4}/)?.[0];
      if (isco) {
        if (!iscoCounts[isco]) iscoCounts[isco] = { count: 0, label: '' };
        iscoCounts[isco].count++;
      }
      const autor = p.created_by || 'Sistema';
      autores[autor] = (autores[autor] || 0) + 1;
    }

    const distinctIsco = Object.keys(iscoCounts).length;

    // Group coverage
    const groupsCovered = new Set(
      Object.keys(iscoCounts).map(isco => isco[0])
    ).size;

    // ISCOs with minimum pairs
    const iscoWithMinPairs = Object.values(iscoCounts)
      .filter(v => v.count >= MIN_PAIRS_PER_ISCO).length;

    // Distribution by major group
    const groupDist: Record<string, number> = {};
    for (const [isco, data] of Object.entries(iscoCounts)) {
      const g = isco[0];
      groupDist[g] = (groupDist[g] || 0) + data.count;
    }

    const groups = Object.entries(groupDist)
      .map(([g, count]) => ({
        group: g,
        name: ISCO_GROUP_NAMES[g] || 'Otro',
        count,
        pct: totalPairs > 0 ? Math.round(count / totalPairs * 100) : 0,
      }))
      .sort((a, b) => b.count - a.count);

    // Top ISCOs
    const topIsco = Object.entries(iscoCounts)
      .sort(([, a], [, b]) => b.count - a.count)
      .slice(0, 15)
      .map(([code, data]) => ({ isco_code: code, count: data.count }));

    // Gaps - groups with < 5% representation
    const gaps = Object.entries(ISCO_GROUP_NAMES)
      .filter(([g]) => !groupDist[g] || groupDist[g] < totalPairs * 0.03)
      .map(([g, name]) => ({ group: g, name, count: groupDist[g] || 0 }));

    // Readiness
    const readiness = assessReadiness({
      totalPairs,
      distinctIsco,
      groupsCovered,
      iscoWithMinPairs,
    });

    // Suggestions
    const suggestions: string[] = [];
    if (totalPairs < MIN_PAIRS_READY) {
      suggestions.push(`Faltan ${MIN_PAIRS_READY - totalPairs} pares para el mínimo recomendado.`);
    }
    if (gaps.length > 0) {
      suggestions.push(`Grupos sub-representados: ${gaps.map(g => g.name).join(', ')}. Buscar ofertas de estos sectores para corregir.`);
    }
    if (distinctIsco < MIN_ISCO_DIVERSITY) {
      suggestions.push(`Solo ${distinctIsco} ISCOs distintos. Diversificar correcciones a más ocupaciones.`);
    }
    if (readiness.ready) {
      suggestions.push('Dataset listo para fine-tuning. Se recomienda entrenar con supervised + DPO.');
    }

    // Recent activity (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000).toISOString();
    const recentPairs = pairs.filter(p => p.resuelto_at && p.resuelto_at > thirtyDaysAgo).length;

    // Authors
    const autorList = Object.entries(autores)
      .sort(([, a], [, b]) => b - a)
      .map(([name, count]) => ({ name, count }));

    return NextResponse.json({
      total_pairs: totalPairs,
      distinct_isco: distinctIsco,
      groups_covered: groupsCovered,
      isco_with_min_pairs: iscoWithMinPairs,
      recent_30d: recentPairs,
      readiness,
      suggestions,
      distribution: {
        by_group: groups,
        top_isco: topIsco,
        gaps,
      },
      autores: autorList,
      fecha_datos: pairs[0]?.resuelto_at || null,
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
