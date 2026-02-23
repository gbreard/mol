import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { requireAdmin, isAuthError } from '@/lib/api-auth';

/**
 * Architecture metrics API.
 *
 * Sources of truth:
 *   - Phase 1 & 2: sistema_estado (synced from local SQLite by sync_learnings.py)
 *   - Phase 3: live counts from ofertas_dashboard / ofertas_skills / ocupaciones_esco
 *   - Issues: live count from issues table
 */

const TABLE_OFERTAS = 'ofertas_dashboard';
const TABLE_SKILLS = 'ofertas_skills';
const TABLE_OCUPACIONES = 'ocupaciones_esco';
const TABLE_ISSUES = 'issues';
const TABLE_ESTADO = 'sistema_estado';

export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.json(
      { error: 'Missing Supabase configuration (URL or key)' },
      { status: 500 }
    );
  }

  try {
    const supabase = createClient(supabaseUrl, supabaseKey);

    // --- sistema_estado: real pipeline metrics (phases 1 & 2) ---
    // Use array query + [0] instead of .single() to avoid PGRST116 with multiple rows
    const { data: estadoRows, error: estadoError } = await supabase
      .from(TABLE_ESTADO)
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(1);

    if (estadoError || !estadoRows || estadoRows.length === 0) {
      return NextResponse.json(
        { error: 'Error fetching sistema_estado', details: estadoError?.message ?? 'no rows' },
        { status: 502 }
      );
    }

    const estadoData = estadoRows[0];

    // --- Phase 3: live counts from Supabase tables ---
    const [
      { count: ofertasSupabase },
      { count: skillsCount },
      { count: ocupacionesCount },
      { count: erroresCount, error: erroresError },
    ] = await Promise.all([
      supabase.from(TABLE_OFERTAS).select('id_oferta', { count: 'exact', head: true }),
      supabase.from(TABLE_SKILLS).select('id', { count: 'exact', head: true }),
      supabase.from(TABLE_OCUPACIONES).select('esco_uri', { count: 'exact', head: true }),
      supabase.from(TABLE_ISSUES).select('id', { count: 'exact', head: true }).eq('estado', 'abierto'),
    ]);

    const erroresSinResolver = erroresError ? 0 : (erroresCount ?? 0);

    // Pendientes sync = validadas locales - sincronizadas en Supabase
    const validadasLocal = estadoData.fase2_validadas ?? 0;
    const syncedCount = ofertasSupabase ?? 0;
    const pendientesSync = Math.max(0, validadasLocal - syncedCount);

    // Determine suggested phase
    const diasScraping = estadoData.fase1_dias_desde_scraping;
    const sinNlp = estadoData.fase2_sin_nlp ?? 0;

    let suggested = {
      fase: 3,
      nombre: 'Presentacion',
      razon: `${syncedCount} ofertas en dashboard, ${skillsCount || 0} skills, ${ocupacionesCount || 0} ocupaciones`
    };

    if (erroresSinResolver > 0) {
      suggested = {
        fase: 2,
        nombre: 'Procesamiento',
        razon: `${erroresSinResolver} issues abiertos para resolver`
      };
    } else if (sinNlp > 100) {
      suggested = {
        fase: 2,
        nombre: 'Procesamiento',
        razon: `${sinNlp.toLocaleString()} ofertas sin NLP pendientes`
      };
    } else if (pendientesSync > 50) {
      suggested = {
        fase: 3,
        nombre: 'Presentacion',
        razon: `${pendientesSync} ofertas validadas pendientes de sync a Supabase`
      };
    } else if (diasScraping != null && diasScraping > 7) {
      suggested = {
        fase: 1,
        nombre: 'Adquisicion',
        razon: `${diasScraping} dias desde ultimo scraping`
      };
    }

    const metrics = {
      phase1: {
        ofertas_totales: estadoData.fase1_ofertas_totales ?? 0,
        ofertas_activas: estadoData.fase1_ofertas_activas ?? 0,
        ultimo_scraping: estadoData.fase1_ultimo_scraping,
        dias_desde_scraping: diasScraping,
        fuentes: estadoData.fase1_fuentes ?? {}
      },
      phase2: {
        con_nlp: estadoData.fase2_con_nlp ?? 0,
        sin_nlp: sinNlp,
        con_matching: estadoData.fase2_con_matching ?? 0,
        pendientes_matching: estadoData.fase2_pendientes_matching ?? 0,
        validadas: validadasLocal,
        errores_sin_resolver: erroresSinResolver,
        reglas_negocio: estadoData.fase2_reglas_negocio ?? 0
      },
      phase3: {
        ofertas_supabase: syncedCount,
        pendientes_sync: pendientesSync,
        skills_count: skillsCount || 0,
        ocupaciones_count: ocupacionesCount || 0
      },
      suggested,
      timestamp: new Date().toISOString()
    };

    return NextResponse.json(metrics);
  } catch (error) {
    console.error('Error in architecture-metrics API:', error);
    return NextResponse.json(
      { error: 'Error fetching architecture metrics' },
      { status: 500 }
    );
  }
}
