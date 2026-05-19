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

interface GoldRow {
  id_oferta: string;
  esco_ok: boolean;
  isco_esperado: string | null;
  esco_esperado: string | null;
  agregado_por: string | null;
  agregado_at: string | null;
}

interface OfertaRow {
  id_oferta: string;
  isco_code: string | null;
  isco_label: string | null;
  run_id: string | null;
}

// GET /api/gold-set-metrics
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  try {
    const { data: gold } = await client
      .from('gold_set')
      .select('id_oferta, esco_ok, isco_esperado, esco_esperado, agregado_por, agregado_at')
      .eq('activo', true);

    const goldRows = (gold as GoldRow[]) || [];
    if (goldRows.length === 0) {
      return NextResponse.json({
        total: 0,
        casos: [],
        por_validador: [],
        cobertura_por_run: [],
      });
    }

    // Métricas básicas
    const total = goldRows.length;
    const ok = goldRows.filter((g) => g.esco_ok === true).length;
    const errores = goldRows.filter((g) => g.esco_ok === false).length;
    const tasaAcierto = total > 0 ? Math.round((ok / total) * 100 * 10) / 10 : 0;

    // Distribución por validador
    const porValidador = new Map<string, { total: number; ok: number; errores: number }>();
    for (const g of goldRows) {
      const v = g.agregado_por || 'unknown';
      if (!porValidador.has(v)) porValidador.set(v, { total: 0, ok: 0, errores: 0 });
      const slot = porValidador.get(v)!;
      slot.total++;
      if (g.esco_ok) slot.ok++;
      else slot.errores++;
    }
    const por_validador = Array.from(porValidador.entries())
      .map(([validador, stats]) => ({ validador, ...stats }))
      .sort((a, b) => b.total - a.total);

    // Cobertura por run: cuántas ofertas del gold están en cada run
    const goldIds = goldRows.map((g) => g.id_oferta);
    const { data: ofertas } = await client
      .from('ofertas_dashboard')
      .select('id_oferta, isco_code, isco_label, run_id')
      .in('id_oferta', goldIds);

    const ofertasMap = new Map<string, OfertaRow>();
    for (const o of (ofertas as OfertaRow[]) || []) {
      ofertasMap.set(String(o.id_oferta), o);
    }

    // Por run: cuántos del gold tiene + acierto actual
    const porRun = new Map<string, { en_gold: number; acierto: number; errores: number; sin_clasificacion: number }>();
    for (const g of goldRows) {
      const o = ofertasMap.get(g.id_oferta);
      if (!o || !o.run_id) continue;
      if (!porRun.has(o.run_id)) {
        porRun.set(o.run_id, { en_gold: 0, acierto: 0, errores: 0, sin_clasificacion: 0 });
      }
      const slot = porRun.get(o.run_id)!;
      slot.en_gold++;
      if (!o.isco_code) {
        slot.sin_clasificacion++;
      } else if (g.esco_ok === true) {
        // Humano dijo "OK" → si sigue con la misma clasificación, sigue OK
        slot.acierto++;
      } else if (g.esco_ok === false && g.isco_esperado) {
        // Humano dijo "error, debería ser X" → comparar contra X
        if (String(o.isco_code) === String(g.isco_esperado)) slot.acierto++;
        else slot.errores++;
      } else {
        // Marcado error sin isco esperado → no podemos medir
        slot.errores++;
      }
    }

    const cobertura_por_run = Array.from(porRun.entries())
      .map(([run_id, stats]) => ({
        run_id,
        ...stats,
        tasa_acierto: stats.en_gold > 0
          ? Math.round((stats.acierto / stats.en_gold) * 100 * 10) / 10
          : 0,
      }))
      .filter((r) => r.en_gold >= 3)  // solo runs con muestra >= 3
      .sort((a, b) => b.run_id.localeCompare(a.run_id))
      .slice(0, 30);

    // Casos individuales para la tabla (los primeros 100, ordenados por fecha desc)
    const casos = goldRows
      .map((g) => {
        const o = ofertasMap.get(g.id_oferta);
        return {
          id_oferta: g.id_oferta,
          esco_ok_humano: g.esco_ok,
          isco_esperado: g.isco_esperado,
          esco_esperado: g.esco_esperado,
          isco_actual: o?.isco_code || null,
          isco_label_actual: o?.isco_label || null,
          agregado_por: g.agregado_por,
          agregado_at: g.agregado_at,
        };
      })
      .sort((a, b) => (b.agregado_at || '').localeCompare(a.agregado_at || ''))
      .slice(0, 100);

    return NextResponse.json({
      total,
      ok,
      errores,
      tasa_acierto: tasaAcierto,
      por_validador,
      cobertura_por_run,
      casos,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Error desconocido';
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
