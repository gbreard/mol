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

// GET /api/training-impact?profile_id=xxx
// Retorna: cursos agrupados por brecha con delta match %
export async function GET(request: NextRequest) {
  const rateLimited = requireRateLimit(request, 'public')
  if (rateLimited) return rateLimited

  const profileId = request.nextUrl.searchParams.get('profile_id');
  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  try {
    // Get worker profile skills
    let workerSkills: string[] = [];
    if (profileId) {
      const { data: profile } = await client
        .from('worker_profiles')
        .select('skills')
        .eq('id', profileId)
        .maybeSingle();
      if (profile?.skills) {
        workerSkills = Array.isArray(profile.skills)
          ? profile.skills.map((s: any) => typeof s === 'string' ? s : s.label || s.preferred_label || '')
          : [];
      }
    }

    // Get skills demandadas por ISCO (top ocupaciones)
    const { data: topOcup } = await client
      .from('ofertas_dashboard')
      .select('isco_code, isco_label')
      .not('isco_code', 'is', null)
      .limit(500);

    // Count by ISCO
    const iscoCounts: Record<string, { label: string; count: number }> = {};
    (topOcup || []).forEach(o => {
      if (!iscoCounts[o.isco_code]) iscoCounts[o.isco_code] = { label: o.isco_label || '', count: 0 };
      iscoCounts[o.isco_code].count++;
    });

    const topIsco = Object.entries(iscoCounts)
      .sort(([, a], [, b]) => b.count - a.count)
      .slice(0, 10);

    // Get skills required for top ISCOs
    const iscoIds = topIsco.map(([code]) => code);
    const { data: skillsReq } = await client
      .from('ofertas_skills')
      .select('preferred_label, canonical_label, id_oferta')
      .limit(2000);

    // Identify gaps: skills requeridas que el worker no tiene
    const skillDemand: Record<string, number> = {};
    (skillsReq || []).forEach(s => {
      const label = s.canonical_label || s.preferred_label;
      skillDemand[label] = (skillDemand[label] || 0) + 1;
    });

    const workerSkillSet = new Set(workerSkills.map(s => s.toLowerCase()));
    const gaps = Object.entries(skillDemand)
      .filter(([skill]) => !workerSkillSet.has(skill.toLowerCase()))
      .sort(([, a], [, b]) => b - a)
      .slice(0, 15)
      .map(([skill, demand]) => ({
        skill_label: skill,
        demand,
        // Simulate training impact: gaining this skill would improve match by X%
        delta_match_pct: Math.min(Math.round(demand / 50 * 10), 15),
        courses: [], // TODO: match against actual course catalog
      }));

    return NextResponse.json({
      profile_id: profileId,
      worker_skills_count: workerSkills.length,
      by_gap: gaps,
      transition_demand: topIsco.map(([code, data]) => ({
        isco_code: code,
        ocupacion_label: data.label,
        ofertas_count: data.count,
        match_score: workerSkills.length > 0 ? Math.random() * 0.4 + 0.3 : 0, // TODO: real matching
        skills_gap: [],
        estimated_months: Math.round(Math.random() * 6 + 3),
      })),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
