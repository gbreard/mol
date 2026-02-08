import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const TABLE_OFERTAS = 'ofertas_dashboard';
const TABLE_SKILLS = 'ofertas_skills';
const TABLE_OCUPACIONES = 'ocupaciones_esco';
const TABLE_ISSUES = 'issues';

export async function GET() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !supabaseServiceKey) {
    return NextResponse.json(
      { error: 'Missing Supabase configuration' },
      { status: 500 }
    );
  }

  try {
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const { data: ofertasData, error: ofertasError } = await supabase
      .from(TABLE_OFERTAS)
      .select('id_oferta, portal, fecha_publicacion, isco_code, estado');

    if (ofertasError) {
      return NextResponse.json(
        { error: 'Error fetching ofertas', details: ofertasError.message },
        { status: 502 }
      );
    }

    const ofertas = ofertasData ?? [];
    const ofertasTotales = ofertas.length;
    const ofertasActivas = ofertas.filter(o => o.estado === 'activa').length;

    // Count by source (portal)
    const fuentesCounts: Record<string, number> = {};
    ofertas.forEach(o => {
      const fuente = o.portal || 'unknown';
      fuentesCounts[fuente] = (fuentesCounts[fuente] || 0) + 1;
    });

    // Get last sync date
    let ultimoScraping: string | null = null;
    let diasDesdeScraping: number | null = null;
    if (ofertas.length > 0) {
      const fechas = ofertas
        .map(o => o.fecha_publicacion)
        .filter(f => f)
        .sort()
        .reverse();
      if (fechas.length > 0) {
        ultimoScraping = fechas[0];
        const lastDate = new Date(fechas[0]);
        const today = new Date();
        diasDesdeScraping = Math.floor((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
      }
    }

    // Get NLP and matching stats
    // In Supabase, all synced offers have NLP and matching (only validated ones are synced)
    const conNlp = ofertas.length;
    const sinNlp = 0; // Local SQLite has pending, but Supabase only has processed
    const conMatching = ofertas.filter(o => o.isco_code).length;
    const validadas = ofertas.length; // All in Supabase are validated

    // Get issues count (pending errors)
    const { count: erroresCount, error: erroresError } = await supabase
      .from(TABLE_ISSUES)
      .select('id', { count: 'exact', head: true })
      .eq('estado', 'abierto');

    const erroresSinResolver = erroresError ? 0 : (erroresCount ?? 0);

    let reglasNegocio = 0;
    const { data: estadoData } = await supabase
      .from('sistema_estado')
      .select('reglas_negocio')
      .single();
    if (estadoData?.reglas_negocio) {
      reglasNegocio = estadoData.reglas_negocio;
    }

    // Get skills count for additional info
    const { count: skillsCount } = await supabase
      .from(TABLE_SKILLS)
      .select('id', { count: 'exact', head: true });

    // Get ocupaciones count
    const { count: ocupacionesCount } = await supabase
      .from(TABLE_OCUPACIONES)
      .select('esco_uri', { count: 'exact', head: true });

    // Supabase stats
    const ofertasSupabase = ofertasTotales;
    const pendientesSync = 0; // Can't know from Supabase alone

    // Determine suggested phase
    let suggested = {
      fase: 3,
      nombre: 'Presentacion',
      razon: `${ofertasSupabase} ofertas en dashboard, ${skillsCount || 0} skills, ${ocupacionesCount || 0} ocupaciones`
    };

    if (erroresSinResolver > 0) {
      suggested = {
        fase: 2,
        nombre: 'Procesamiento',
        razon: `${erroresSinResolver} issues abiertos para resolver`
      };
    } else if (diasDesdeScraping && diasDesdeScraping > 7) {
      suggested = {
        fase: 1,
        nombre: 'Adquisicion',
        razon: `${diasDesdeScraping} dias desde ultima publicacion`
      };
    }

    const metrics = {
      phase1: {
        ofertas_totales: ofertasTotales,
        ofertas_activas: ofertasActivas,
        ultimo_scraping: ultimoScraping,
        dias_desde_scraping: diasDesdeScraping,
        fuentes: fuentesCounts
      },
      phase2: {
        con_nlp: conNlp,
        sin_nlp: sinNlp,
        con_matching: conMatching,
        pendientes_matching: sinNlp,
        validadas: validadas,
        errores_sin_resolver: erroresSinResolver,
        reglas_negocio: reglasNegocio
      },
      phase3: {
        ofertas_supabase: ofertasSupabase,
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
