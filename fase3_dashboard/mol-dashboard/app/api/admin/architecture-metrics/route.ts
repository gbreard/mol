import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

export async function GET() {
  try {
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get total and active offers
    const { data: ofertasData, error: ofertasError } = await supabase
      .from('ofertas')
      .select('id, fuente, fecha_publicacion, activa', { count: 'exact' });

    if (ofertasError) {
      console.error('Error fetching ofertas:', ofertasError);
    }

    const ofertas = ofertasData || [];
    const ofertasTotales = ofertas.length;
    const ofertasActivas = ofertas.filter(o => o.activa).length;

    // Count by source
    const fuentesCounts: Record<string, number> = {};
    ofertas.forEach(o => {
      const fuente = o.fuente || 'unknown';
      fuentesCounts[fuente] = (fuentesCounts[fuente] || 0) + 1;
    });

    // Get last scraping date
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

    // Get NLP and matching stats from ofertas_esco_matching view or table
    const { data: matchingData, error: matchingError } = await supabase
      .from('ofertas')
      .select('id, isco, estado_validacion');

    if (matchingError) {
      console.error('Error fetching matching data:', matchingError);
    }

    const matching = matchingData || [];
    const conNlp = matching.filter(m => m.isco).length;
    const sinNlp = matching.filter(m => !m.isco).length;
    const conMatching = matching.filter(m => m.isco).length;
    const validadas = matching.filter(m => m.estado_validacion === 'validado_claude' || m.estado_validacion === 'validado_humano').length;

    // Get validation errors count
    const { count: erroresCount, error: erroresError } = await supabase
      .from('validation_errors')
      .select('id', { count: 'exact', head: true })
      .eq('resuelto', false);

    if (erroresError) {
      console.error('Error fetching validation errors:', erroresError);
    }

    const erroresSinResolver = erroresCount || 0;

    // Get rules count (approximation - we'll use a fixed value or config)
    const reglasNegocio = 140; // From CLAUDE.md - this could be fetched from sistema_estado

    // Get Supabase stats (ofertas in dashboard)
    const { count: supabaseCount, error: supabaseError } = await supabase
      .from('ofertas')
      .select('id', { count: 'exact', head: true });

    if (supabaseError) {
      console.error('Error counting supabase ofertas:', supabaseError);
    }

    const ofertasSupabase = supabaseCount || 0;

    // Calculate pending sync (difference between validadas and supabase)
    const pendientesSync = Math.max(0, validadas - ofertasSupabase);

    // Determine suggested phase
    let suggested = {
      fase: 3,
      nombre: 'Presentacion',
      razon: 'Sistema funcionando normalmente'
    };

    if (erroresSinResolver > 0) {
      suggested = {
        fase: 2,
        nombre: 'Procesamiento',
        razon: `${erroresSinResolver} errores pendientes de resolver`
      };
    } else if (sinNlp > conNlp * 0.1) {
      suggested = {
        fase: 2,
        nombre: 'Procesamiento',
        razon: `${sinNlp} ofertas pendientes de NLP`
      };
    } else if (diasDesdeScraping && diasDesdeScraping > 7) {
      suggested = {
        fase: 1,
        nombre: 'Adquisicion',
        razon: `${diasDesdeScraping} dias sin scraping`
      };
    } else if (pendientesSync > 0) {
      suggested = {
        fase: 3,
        nombre: 'Presentacion',
        razon: `${pendientesSync} ofertas pendientes de sincronizar`
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
        pendientes_sync: pendientesSync
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
