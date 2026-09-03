import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin, isAuthError } from '@/lib/api-auth';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import Anthropic from '@anthropic-ai/sdk';

// skills_tecnicas puede venir como JSON array serializado o como texto plano
// (dato heredado mal formateado). Parsear sin try/catch revienta el batch.
function parseSkillsTecnicas(raw: unknown): unknown[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    const trimmed = raw.trim();
    if (!trimmed.startsWith('[')) return [];
    try {
      const parsed = JSON.parse(trimmed);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

// ============================================================
// Supabase admin client
// ============================================================

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

// ============================================================
// Rule matching (TypeScript port of titulo_contiene_alguno)
// ============================================================

interface RuleCondition {
  titulo_contiene_alguno?: string[];
  titulo_contiene_todos?: string[];
}

interface MatchingRule {
  nombre: string;
  condicion: RuleCondition;
  accion: { forzar_isco: string; esco_label?: string };
  prioridad?: number;
  activa?: boolean;
}

function loadMatchingRules(): Record<string, MatchingRule> {
  // Load from Supabase is not practical here — use a simplified approach
  // The rules are already in the prompt context; we match titles client-side
  return {};
}

function findCandidateRules(
  titulo: string,
  rules: Record<string, MatchingRule>
): Array<{ id: string; prioridad: number; condicion_resumida: string }> {
  const tituloLower = titulo.toLowerCase();
  const matches: Array<{ id: string; prioridad: number; condicion_resumida: string }> = [];

  for (const [rid, rule] of Object.entries(rules)) {
    if (rule.activa === false) continue;
    const keywords = rule.condicion?.titulo_contiene_alguno || [];
    const matchedKeyword = keywords.find(k => tituloLower.includes(k.toLowerCase()));
    if (matchedKeyword) {
      matches.push({
        id: rid,
        prioridad: rule.prioridad ?? 0,
        condicion_resumida: `titulo_contiene "${matchedKeyword}" → ISCO ${rule.accion?.forzar_isco}`,
      });
    }
  }

  return matches.sort((a, b) => b.prioridad - a.prioridad).slice(0, 3);
}

// ============================================================
// Prompt construction
// ============================================================

const SYSTEM_PROMPT = `Sos un experto en clasificación ocupacional del mercado laboral argentino. Analizás correcciones de validadores humanos sobre ofertas de trabajo clasificadas con ESCO/ISCO.

Para cada corrección, proponé una acción concreta del siguiente tipo:

TIPOS DE ACCIÓN:
- regla_nueva: crear regla en matching_rules_business.json
- fix_regla: modificar condición o label de regla existente
- fix_bug: corregir bug (tilde, prioridad, override_semantico)
- sinonimo: agregar a sinonimos_argentinos_esco.json
- skills_gold_set: skills faltantes para enriquecer Gold Set
- nlp_correccion_sector: agregar/modificar regla en correccion_sector de nlp_inference_rules.json
- nlp_area_funcional: agregar keyword a categoría de area_funcional en nlp_inference_rules.json
- nlp_limpieza_tareas: agregar patrón de ruido a limpieza_tareas en nlp_inference_rules.json
- nlp_fix_puntual: corrección directa en una oferta en BD (cuando el patrón no es generalizable)
- excepcion_aceptable: el sistema está bien, caso edge
- requiere_revision: no hay suficiente info para decidir

IMPORTANTE sobre NLP:
Cuando el validador reporta sector mal o área mal, proponé SIEMPRE dos acciones si el patrón es generalizable:
1. nlp_fix_puntual → corrige la oferta actual
2. nlp_correccion_sector → corrige todas las futuras

Para cada acción incluí:
- tipo: (uno de los anteriores)
- propuesta: (detalle concreto de la acción — JSON object con los campos que correspondan al tipo)
- justificacion: (por qué esta acción resuelve el problema)
- confianza: alta | media | baja
- afecta_otras_ofertas: true | false
- issue_ids: (lista de IDs de issues relacionados, puede ser vacía)

CONTEXTO DEL SISTEMA:
- El matcher tiene 323 reglas de negocio en matching_rules_business.json
- Las reglas usan titulo_contiene_alguno, titulo_contiene_todos, area_funcional_es, sector_es
- El semántico usa BGE-M3 con peso 60% skills + 40% título
- override_semantico: true hace que la regla gane incluso con score >= 0.95

FORMATO DE RESPUESTA:
Respondé SOLO con un JSON array. Sin texto adicional. Sin markdown. Sin explicaciones fuera del JSON.`;

interface CorrectionData {
  id_oferta: string;
  titulo: string;
  titulo_limpio: string;
  isco_code: string;
  isco_label: string;
  sector_empresa: string;
  area_funcional: string;
  nivel_seniority: string;
  regla_aplicada: string | null;
  decision_metodo: string | null;
  occupation_match_score: number | null;
  validacion_correcciones: Record<string, unknown>;
  // NLP fields (optional, included when relevant)
  tareas_explicitas?: string;
  skills_tecnicas?: string[];
  nivel_educativo?: string;
  mision_rol?: string;
  // Rule candidates
  reglas_candidatas?: Array<{ id: string; prioridad: number; condicion_resumida: string }>;
}

function buildBatchPrompt(corrections: CorrectionData[]): string {
  const items = corrections.map(c => {
    const corr = c.validacion_correcciones || {};
    const nota = (corr.nota as string) || '';
    const ocupCorr = corr.ocupacion_corregida as Record<string, string> | undefined;
    const skillsEdit = corr.skills_editadas as string[] | undefined;

    // Determine if NLP fields are needed
    const needsNlp = nota.toLowerCase().includes('sector') ||
      nota.toLowerCase().includes('área') ||
      nota.toLowerCase().includes('area') ||
      nota.toLowerCase().includes('seniority');

    const needsSkills = skillsEdit && skillsEdit.length > 0;

    let entry = `--- Oferta ${c.id_oferta} ---
titulo: ${c.titulo_limpio || c.titulo}
titulo_original: ${c.titulo}
isco_actual: ${c.isco_code} (${c.isco_label})
sector: ${c.sector_empresa || 'N/A'}
area: ${c.area_funcional || 'N/A'}
seniority: ${c.nivel_seniority || 'N/A'}
regla_aplicada: ${c.regla_aplicada || 'ninguna'}
decision: ${c.decision_metodo || 'N/A'}
score: ${c.occupation_match_score ?? 'N/A'}`;

    if (c.reglas_candidatas && c.reglas_candidatas.length > 0) {
      entry += `\nreglas_candidatas: ${JSON.stringify(c.reglas_candidatas)}`;
    }

    if (ocupCorr) {
      entry += `\nocupacion_corregida: ISCO ${ocupCorr.isco_code} (${ocupCorr.esco_label})`;
    }

    if (nota) {
      entry += `\nnota_validador: ${nota.slice(0, 500)}`;
    }

    if (skillsEdit) {
      entry += `\nskills_editadas: ${JSON.stringify(skillsEdit).slice(0, 300)}`;
    }

    // NLP fields when relevant
    if (needsNlp && c.tareas_explicitas) {
      entry += `\ntareas: ${c.tareas_explicitas.slice(0, 300)}`;
    }
    if ((needsNlp || needsSkills) && c.skills_tecnicas) {
      entry += `\nskills_tecnicas: ${JSON.stringify(c.skills_tecnicas).slice(0, 200)}`;
    }
    if (needsNlp && c.nivel_educativo) {
      entry += `\nnivel_educativo: ${c.nivel_educativo}`;
    }
    if (needsNlp && c.mision_rol) {
      entry += `\nmision: ${c.mision_rol.slice(0, 200)}`;
    }

    return entry;
  });

  return items.join('\n\n');
}

// ============================================================
// Parse Claude response with retry
// ============================================================

function parseJsonResponse(text: string): unknown[] | null {
  // Try direct parse
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed;
  } catch { /* continue */ }

  // Try extracting JSON array from markdown
  const match = text.match(/\[[\s\S]*\]/);
  if (match) {
    try {
      return JSON.parse(match[0]);
    } catch { /* continue */ }
  }

  return null;
}

// ============================================================
// POST handler
// ============================================================

export async function POST(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) return NextResponse.json({ error: 'ANTHROPIC_API_KEY no configurada' }, { status: 500 });

  // Parse body
  const body = await request.json().catch(() => ({}));
  const batchSize = Math.min(body.batch_size || 15, 20);
  const incluirDescripcion = body.incluir_descripcion || false;

  // Check rate limit
  const { data: rateLimit } = await client.rpc('check_api_rate_limit', { p_max_daily: 5 });
  if (!rateLimit?.allowed) {
    return NextResponse.json({
      error: `Rate limit alcanzado: ${rateLimit?.llamadas_hoy}/${rateLimit?.max_daily} llamadas hoy. Costo: $${rateLimit?.costo_hoy}`,
    }, { status: 429 });
  }

  // Fetch pending corrections
  const selectFields = 'id_oferta,titulo,titulo_limpio,isco_code,isco_label,sector_empresa,area_funcional,nivel_seniority,regla_aplicada,decision_metodo,occupation_match_score,validacion_correcciones,tareas_explicitas,skills_tecnicas,nivel_educativo,mision_rol';

  let query = client.from('ofertas_dashboard')
    .select(selectFields)
    .not('validacion_correcciones', 'is', null);

  if (body.oferta_ids && Array.isArray(body.oferta_ids) && body.oferta_ids.length > 0) {
    query = query.in('id_oferta', body.oferta_ids);
  }

  const { data: corrections, error: fetchErr } = await query.limit(100);
  if (fetchErr) return NextResponse.json({ error: fetchErr.message }, { status: 500 });
  if (!corrections || corrections.length === 0) {
    return NextResponse.json({ error: 'No hay correcciones pendientes' }, { status: 404 });
  }

  // Load matching rules for candidate detection
  let matchingRules: Record<string, MatchingRule> = {};
  try {
    const { data: rulesJson } = await client.storage.from('config').download('matching_rules_business.json');
    // Fallback: load from a simple RPC or just skip if not available
  } catch { /* skip rule matching if not available */ }

  // Process in batches
  const anthropic = new Anthropic({ apiKey });
  const allCandidates: unknown[] = [];
  let totalInput = 0;
  let totalOutput = 0;
  const batchId = `batch_${Date.now()}`;

  for (let i = 0; i < corrections.length; i += batchSize) {
    const batch = corrections.slice(i, i + batchSize);

    // Enrich with reglas_candidatas
    const enriched: CorrectionData[] = batch.map(c => ({
      ...c,
      reglas_candidatas: findCandidateRules(c.titulo_limpio || c.titulo || '', matchingRules),
      skills_tecnicas: parseSkillsTecnicas(c.skills_tecnicas) as string[],
    }));

    const userPrompt = buildBatchPrompt(enriched);

    // Call Claude with retry
    let candidates: unknown[] | null = null;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const msg = await anthropic.messages.create({
          model: 'claude-sonnet-4-6',
          max_tokens: 4096,
          system: SYSTEM_PROMPT,
          messages: [{ role: 'user', content: userPrompt }],
        });

        totalInput += msg.usage.input_tokens;
        totalOutput += msg.usage.output_tokens;

        const text = msg.content[0].type === 'text' ? msg.content[0].text : '';
        candidates = parseJsonResponse(text);

        if (candidates) break;

        // Retry with explicit instruction
        if (attempt === 0) {
          const retryMsg = await anthropic.messages.create({
            model: 'claude-sonnet-4-6',
            max_tokens: 4096,
            system: SYSTEM_PROMPT,
            messages: [
              { role: 'user', content: userPrompt },
              { role: 'assistant', content: text },
              { role: 'user', content: 'Tu respuesta no es JSON válido. Respondé SOLO con un JSON array []. Sin markdown ni explicaciones.' },
            ],
          });
          totalInput += retryMsg.usage.input_tokens;
          totalOutput += retryMsg.usage.output_tokens;
          const retryText = retryMsg.content[0].type === 'text' ? retryMsg.content[0].text : '';
          candidates = parseJsonResponse(retryText);
        }
      } catch (err) {
        console.error(`Batch ${i / batchSize + 1} attempt ${attempt + 1} error:`, err);
        if (attempt === 1) break;
      }
    }

    if (candidates) {
      allCandidates.push(...candidates);
    }
  }

  // Save candidates to rule_candidates
  let savedCount = 0;
  for (const c of allCandidates) {
    const candidate = c as Record<string, unknown>;
    try {
      await client.from('rule_candidates').insert({
        oferta_id: candidate.oferta_id || null,
        issue_ids: Array.isArray(candidate.issue_ids) ? candidate.issue_ids : [],
        tipo: candidate.tipo || 'requiere_revision',
        propuesta: candidate.propuesta || {},
        justificacion: candidate.justificacion || null,
        confianza: candidate.confianza || 'baja',
        afecta_otras: candidate.afecta_otras_ofertas || false,
        generado_por: 'claude-api',
        batch_id: batchId,
      });
      savedCount++;
    } catch (err) {
      console.error('Error saving candidate:', err);
    }
  }

  // Update API usage
  await client.rpc('update_api_anthropic_usage', {
    p_tokens_input: totalInput,
    p_tokens_output: totalOutput,
  });

  // Calculate cost
  const costoEstimado = (totalInput / 1_000_000) * 3.0 + (totalOutput / 1_000_000) * 15.0;

  return NextResponse.json({
    candidatos: allCandidates,
    tokens_usados: { input: totalInput, output: totalOutput },
    costo_estimado: Math.round(costoEstimado * 10000) / 10000,
    ofertas_analizadas: corrections.length,
    batches_procesados: Math.ceil(corrections.length / batchSize),
    candidatos_guardados: savedCount,
    batch_id: batchId,
  });
}

// GET: obtener candidatos pendientes
export async function GET(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const estado = request.nextUrl.searchParams.get('estado') || 'pendiente';

  const { data, error } = await client.from('rule_candidates')
    .select('*')
    .eq('estado', estado)
    .order('created_at', { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // Also get usage stats
  const { data: usage } = await client.rpc('check_api_rate_limit', { p_max_daily: 5 });

  return NextResponse.json({ candidatos: data || [], usage });
}

// PATCH: aprobar o rechazar candidato
export async function PATCH(request: NextRequest) {
  const auth = await requireAdmin(request);
  if (isAuthError(auth)) return auth;

  const client = getSupabaseAdmin();
  if (!client) return NextResponse.json({ error: 'Supabase no configurado' }, { status: 500 });

  const body = await request.json();
  const { id, accion, motivo } = body;

  if (!id || !['aprobar', 'rechazar'].includes(accion)) {
    return NextResponse.json({ error: 'id y accion (aprobar/rechazar) requeridos' }, { status: 400 });
  }

  const adminEmail = auth.user?.email || 'admin';
  const nuevoEstado = accion === 'aprobar' ? 'aprobado' : 'rechazado';

  const { data, error } = await client.from('rule_candidates')
    .update({
      estado: nuevoEstado,
      revisado_por: adminEmail,
      revisado_at: new Date().toISOString(),
      motivo_rechazo: accion === 'rechazar' ? (motivo || null) : null,
    })
    .eq('id', id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  // If approved and has issue_ids, close them
  if (accion === 'aprobar' && data.issue_ids && data.issue_ids.length > 0) {
    for (const issueId of data.issue_ids) {
      try {
        await client.from('issues').update({
          estado: 'resuelto',
          resuelto_at: new Date().toISOString(),
          resuelto_por: adminEmail,
          solucion_aplicada: `Aprobado via Claude API: ${data.tipo} (candidate #${data.id})`,
        }).eq('id', issueId);
      } catch { /* non-critical */ }
    }
  }

  return NextResponse.json({
    id: data.id,
    tipo: data.tipo,
    estado: nuevoEstado,
    message: `Candidato ${nuevoEstado}`,
  });
}
