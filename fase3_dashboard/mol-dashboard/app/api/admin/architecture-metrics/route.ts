import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

// Table names (same as sync_to_supabase.py)
const TABLE_OFERTAS = 'ofertas_dashboard';
const TABLE_SKILLS = 'ofertas_skills';
const TABLE_OCUPACIONES = 'ocupaciones_esco';
const TABLE_ISSUES = 'issues';

export async function GET() {
  try {
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Use count queries to avoid pagination limits (Supabase default is 1000)

    // Total offers count
    const { count: ofertasTotales, error: totalError } = await supabase
      .from(TABLE_OFERTAS)
      .select('*', { count: 'exact', head: true });

    if (totalError) {
      console.error('Error counting ofertas:', totalError);
    }

    // Active offers count
    const { count: ofertasActivas } = await supabase
      .from(TABLE_OFERTAS)
      .select('*', { count: 'exact', head: true })
      .eq('estado', 'activa');

    // Count by portal using multiple queries
    // Since Supabase doesn't have GROUP BY in REST API, we query each portal
    const portales = ['bumeran', 'zonajobs', 'computrabajo', 'indeed', 'linkedin'];
    const fuentesCounts: Record<string, number> = {};

    await Promise.all(portales.map(async (portal) => {
      const { count } = await supabase
        .from(TABLE_OFERTAS)
        .select('*', { count: 'exact', head: true })
        .eq('portal', portal);
      if (count && count > 0) {
        fuentesCounts[portal] = count;
      }
    }));

    // Get last publication date (order by fecha_publicacion desc, limit 1)
    let ultimoScraping: string | null = null;
    let diasDesdeScraping: number | null = null;

    const { data: lastOffer } = await supabase
      .from(TABLE_OFERTAS)
      .select('fecha_publicacion')
      .not('fecha_publicacion', 'is', null)
      .order('fecha_publicacion', { ascending: false })
      .limit(1)
      .single();

    if (lastOffer?.fecha_publicacion) {
      ultimoScraping = lastOffer.fecha_publicacion;
      const lastDate = new Date(lastOffer.fecha_publicacion);
      const today = new Date();
      diasDesdeScraping = Math.floor((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));
    }

    // Get offers with matching (isco_code not null)
    const { count: conMatching } = await supabase
      .from(TABLE_OFERTAS)
      .select('*', { count: 'exact', head: true })
      .not('isco_code', 'is', null);

    // All synced offers have NLP and are validated
    const conNlp = ofertasTotales || 0;
    const sinNlp = 0; // Local SQLite has pending, but Supabase only has processed
    const validadas = ofertasTotales || 0; // All in Supabase are validated

    // Get issues count (pending errors)
    const { count: erroresCount, error: erroresError } = await supabase
      .from(TABLE_ISSUES)
      .select('id', { count: 'exact', head: true })
      .eq('estado', 'abierto');

    if (erroresError) {
      console.error('Error fetching issues:', erroresError);
    }

    const erroresSinResolver = erroresCount || 0;

    // Get rules count from sistema_estado if exists, otherwise default
    let reglasNegocio = 140;
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
