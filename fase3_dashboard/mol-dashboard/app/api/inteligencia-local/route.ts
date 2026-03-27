import { NextRequest, NextResponse } from 'next/server';
import { requireRateLimit } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseAdmin: SupabaseClient | null = null;

function getSupabaseAdmin(): SupabaseClient | null {
  if (supabaseAdmin) return supabaseAdmin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;
  supabaseAdmin = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false }
  });
  return supabaseAdmin;
}

// GET /api/inteligencia-local?jurisdiccion=CABA
// Retorna: skills más demandadas vs disponibles + brechas + cursos faltantes
export async function GET(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  const jurisdiccion = request.nextUrl.searchParams.get('jurisdiccion') || 'Capital Federal';
  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  // Map jurisdiccion aliases
  const provMap: Record<string, string> = {
    'CABA': 'Capital Federal',
    'caba': 'Capital Federal',
    'GBA': 'Buenos Aires',
    'gba': 'Buenos Aires',
  };
  const provincia = provMap[jurisdiccion] || jurisdiccion;

  try {
    // Skills más demandadas en la jurisdicción (from ofertas_skills + ofertas_dashboard)
    const { data: skillsData } = await client
      .from('ofertas_skills')
      .select('preferred_label, canonical_label, l1_nombre, es_digital, id_oferta')
      .limit(1000);

    // Get ofertas de la jurisdicción
    const { data: ofertasJuris } = await client
      .from('ofertas_dashboard')
      .select('id_oferta, isco_code, isco_label')
      .eq('provincia', provincia)
      .limit(1000);

    const ofertaIds = new Set((ofertasJuris || []).map(o => o.id_oferta));

    // Filter skills to only those from this jurisdiccion
    const skillsJuris = (skillsData || []).filter(s => ofertaIds.has(s.id_oferta));

    // Count skills (use canonical_label if available for grouping)
    const skillCounts: Record<string, { count: number; digital: boolean; l1: string }> = {};
    skillsJuris.forEach(s => {
      const key = s.canonical_label || s.preferred_label;
      if (!skillCounts[key]) {
        skillCounts[key] = { count: 0, digital: s.es_digital || false, l1: s.l1_nombre || '' };
      }
      skillCounts[key].count++;
    });

    const topSkills = Object.entries(skillCounts)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 30);

    // Top ocupaciones en la jurisdicción
    const ocupCounts: Record<string, { code: string; label: string; count: number }> = {};
    (ofertasJuris || []).forEach(o => {
      if (o.isco_code) {
        const key = o.isco_code;
        if (!ocupCounts[key]) ocupCounts[key] = { code: key, label: o.isco_label || '', count: 0 };
        ocupCounts[key].count++;
      }
    });

    const topOcupaciones = Object.values(ocupCounts)
      .sort((a, b) => b.count - a.count)
      .slice(0, 20);

    // Brechas: skills digitales demandadas vs no disponibles (simplificado)
    const digitales = topSkills.filter(s => s.digital);
    const noDigitales = topSkills.filter(s => !s.digital);

    return NextResponse.json({
      jurisdiccion: provincia,
      ofertas_total: ofertaIds.size,
      skills_demandadas: topSkills,
      skills_digitales: digitales,
      ocupaciones_top: topOcupaciones,
      brechas: {
        total_skills_unicas: Object.keys(skillCounts).length,
        skills_digitales_pct: topSkills.length > 0
          ? Math.round(digitales.length / topSkills.length * 100)
          : 0,
      },
      cursos_faltantes: [], // TODO: cruzar con catálogo de cursos cuando exista
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
