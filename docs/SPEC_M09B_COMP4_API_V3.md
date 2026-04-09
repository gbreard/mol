# M-09b Componente 4 — Análisis Automático con API de Anthropic (V3)

> **Estado:** ⬜ No iniciado  
> **Prioridad:** ALTO  
> **Prerequisito de:** M-09b Componentes 1-3 ✅  
> **Contexto:** Cynthia genera análisis experto en sus correcciones.
> Este componente usa la API de Anthropic para leer esas correcciones
> automáticamente y proponer candidatos estructurados que aparecen
> en la UI para aprobación humana.

---

## El flujo completo

```
Cynthia corrige en el dashboard
    ↓
Alerta en /admin/metricas
    ↓
Operador clickea "Analizar con Claude"
    ↓
API de Anthropic lee todas las correcciones pendientes
    → propone candidatos estructurados por tipo
    ↓
Candidatos aparecen en la UI por destino:
    /admin/procesamiento/reglas    → reglas nuevas y fixes
    /admin/procesamiento/diccionarios → sinónimos
    /admin/gold-set (futuro M-10) → skills faltantes
    ↓
Cynthia o el operador revisa y aprueba
    ↓
Al aprobar → se crea con linaje completo
             → issue se cierra automáticamente
```

---

## Lo que Claude analiza

Por cada corrección pendiente, Claude recibe:

### Input mínimo (siempre)
```
titulo_limpio + titulo (original)
isco_code + isco_label actual
sector_empresa + area_funcional + nivel_seniority
regla_aplicada + decision_metodo + occupation_match_score
reglas_candidatas: top 3 reglas que matchean el título
    [{id, prioridad, condicion_resumida}]
    → evita que Claude proponga reglas que ya existen
validacion_correcciones.nota (análisis de Cynthia)
validacion_correcciones.ocupacion_corregida (si existe)
validacion_correcciones.skills_editadas (si existen)
```

### Input por tipo de problema esperado

**Para candidatos de NLP (sector/área/seniority mal):**
```
tareas_explicitas   → qué hace el puesto realmente
skills_tecnicas     → confirma el perfil
nivel_educativo     → para detectar errores de educación
mision_rol          → contexto adicional
```

**Para candidatos de skills_gold_set:**
```
tareas_explicitas   → skills implícitas no extraídas
skills_tecnicas     → skills actuales (para detectar faltantes)
```

**Para candidatos de regla_nueva/fix_regla:**
```
reglas_candidatas   → reglas que ya matchean el título
                      (evita duplicados)
```

### Input opcional (solo si nota es ambigua)
```
descripcion completa del aviso (campo descripcion)
```

Solo se incluye cuando la nota dice "ver aviso completo"
o cuando no hay nota y solo hay `skills_editadas`.
Con ~1.500 chars por aviso, incluirla siempre duplicaría
tokens innecesariamente.

---

## El prompt de Claude

```
Sos un experto en clasificación ocupacional del mercado
laboral argentino. Analizás correcciones de validadores
humanos sobre ofertas de trabajo clasificadas con ESCO/ISCO.

Para cada corrección, proponé una acción concreta del
siguiente tipo:

TIPOS DE ACCIÓN:
- regla_nueva: crear regla en matching_rules_business.json
- fix_regla: modificar condición o label de regla existente
- fix_bug: corregir bug (tilde, prioridad, override_semantico)
- sinonimo: agregar a sinonimos_argentinos_esco.json
- skills_gold_set: skills faltantes para enriquecer Gold Set
- nlp_correccion_sector: agregar/modificar regla en
  correccion_sector de nlp_inference_rules.json
  "Si título contiene X y sector es Y → corregir a Z"
- nlp_area_funcional: agregar keyword a categoría de
  area_funcional en nlp_inference_rules.json
- nlp_limpieza_tareas: agregar patrón de ruido a
  limpieza_tareas en nlp_inference_rules.json
- nlp_fix_puntual: corrección directa en una oferta en BD
  (cuando el patrón no es generalizable)
- excepcion_aceptable: el sistema está bien, caso edge
- requiere_revision: no hay suficiente info para decidir

IMPORTANTE sobre NLP:
Cuando Cynthia reporta sector mal o área mal, proponé SIEMPRE
dos acciones si el patrón es generalizable:
1. nlp_fix_puntual → corrige la oferta actual
2. nlp_correccion_sector → corrige todas las futuras

Si el error es de una sola oferta y no es generalizable,
solo proponé nlp_fix_puntual.

Para cada acción incluí:
- tipo: (uno de los anteriores)
- propuesta: (detalle concreto de la acción)
- justificacion: (por qué esta acción resuelve el problema)
- confianza: alta | media | baja
- afecta_otras_ofertas: true | false
- issue_ids: (lista de IDs de issues relacionados)

CONTEXTO DEL SISTEMA:
- El matcher tiene 323 reglas de negocio en
  matching_rules_business.json
- Las reglas usan titulo_contiene_alguno,
  titulo_contiene_todos, area_funcional_es, sector_es
- El semántico usa BGE-M3 con peso 60% skills + 40% título
- El override_semantico: true hace que la regla gane
  incluso con score >= 0.95 del semántico

FORMATO DE RESPUESTA:
Respondé SOLO con un JSON array. Sin texto adicional.
Sin markdown. Sin explicaciones fuera del JSON.

[
  {
    "oferta_id": "...",
    "titulo": "...",
    "tipo": "...",
    "propuesta": { ... },
    "justificacion": "...",
    "confianza": "...",
    "afecta_otras_ofertas": true/false,
    "issue_ids": ["..."]
  }
]
```

---

## Estructura de candidatos por tipo

### regla_nueva
```json
{
  "tipo": "regla_nueva",
  "propuesta": {
    "id": "R324_farmaceutico",
    "nombre": "Farmacéutico/a",
    "condicion": {
      "titulo_contiene_alguno": ["farmacéutico", "farmaceutico", "farmacéutica"]
    },
    "accion": {
      "forzar_isco": "2262",
      "esco_label": "farmacéutico/farmacéutica"
    },
    "excluir_si": []
  }
}
```

### fix_regla
```json
{
  "tipo": "fix_regla",
  "propuesta": {
    "regla_id": "R75_vigilador",
    "campo": "esco_label",
    "valor_actual": "guardia de furgón blindado",
    "valor_nuevo": "vigilante de seguridad",
    "razon": "Label ESCO incorrecto para la mayoría de vigiladores"
  }
}
```

### sinonimo
```json
{
  "tipo": "sinonimo",
  "propuesta": {
    "isco": "9334",
    "label_esco": "reponedor",
    "terminos_argentinos": ["repositor", "repositora", "repositor de góndola"]
  }
}
```

### skills_gold_set
```json
{
  "tipo": "skills_gold_set",
  "propuesta": {
    "ocupacion_isco": "2262",
    "skills_sugeridas": [
      "dispensar medicamentos",
      "dirección técnica de farmacia",
      "normativa farmacéutica"
    ],
    "fuente": "Cynthia Vázquez - corrección directa"
  }
}
```

### nlp_fix_puntual
```json
{
  "tipo": "nlp_fix_puntual",
  "propuesta": {
    "campo": "sector_empresa",
    "valor_actual": "Otro",
    "valor_correcto": "Construcción",
    "aplica_a_oferta": "7215160363"
  }
}
```

### nlp_correccion_sector
```json
{
  "tipo": "nlp_correccion_sector",
  "propuesta": {
    "keywords": ["herrero", "herrería", "forja"],
    "sector_incorrecto": ["Otro"],
    "sector_correcto": "Metalúrgica",
    "justificacion": "Herreros siempre son sector metalúrgico"
  }
}
```

### nlp_area_funcional
```json
{
  "tipo": "nlp_area_funcional",
  "propuesta": {
    "categoria": "Telecomunicaciones",
    "keywords_nuevos": ["torrista", "antenas", "radiobases"],
    "seccion": "area_funcional"
  }
}
```

### nlp_limpieza_tareas
```json
{
  "tipo": "nlp_limpieza_tareas",
  "propuesta": {
    "patron": "Competencias requeridas",
    "tipo_patron": "prefijo",
    "justificacion": "Es un encabezado de sección, no una tarea"
  }
}
```

---

## Componente UI — Página nueva /admin/procesamiento/correcciones

**Ubicación:** Nueva página dentro de /admin/procesamiento

**Por qué aquí y no en /admin/issues:**
Los candidatos propuestos son reglas, sinónimos y fixes — pertenecen
a procesamiento donde viven esos artefactos. /admin/issues es para
gestión de bugs reportados, no para candidatos de configuración.

### Layout de la página

```
┌─────────────────────────────────────────────────────────────┐
│ CORRECCIONES DE VALIDADORES                                 │
│ 11 pendientes de Cynthia                                    │
│                                                             │
│ [⚡ Analizar con Claude]    API: $0.07 hoy · $0.27 total   │
│                                                             │
│ Tabs: [Reglas (3)] [Sinónimos (2)] [Skills (4)] [NLP (1)]  │
│       [Excepciones (1)]                                     │
├─────────────────────────────────────────────────────────────┤
│ TAB: REGLAS                                                 │
│                                                             │
│ R324 — Farmacéutico/a → 2262        ●●●● Alta confianza   │
│ "farmacéutico" → ISCO 2262          Issue #5846800678      │
│ Afecta otras ofertas: Sí            Cynthia · hace 3 días │
│ [Aprobar ✓]  [Editar ✏]  [Rechazar ✗]  [Ver oferta →]    │
│                                                             │
│ Fix R23 — encargado depósito        ●●●○ Media confianza  │
│ Cambiar ISCO 4321 → 1324            Issue #5891652793      │
│ [Aprobar ✓]  [Editar ✏]  [Rechazar ✗]                    │
└─────────────────────────────────────────────────────────────┘
```

### Tabs por tipo de candidato

```
Tab Reglas      → tipo: regla_nueva, fix_regla, fix_bug
Tab Sinónimos   → tipo: sinonimo
Tab Skills      → tipo: skills_gold_set (input para M-10)
Tab NLP         → tipo: nlp_correccion_sector,
                       nlp_area_funcional,
                       nlp_limpieza_tareas,
                       nlp_fix_puntual
Tab Excepciones → tipo: excepcion_aceptable, requiere_revision
```

**Al aprobar en Tab NLP:**
Los candidatos NLP se marcan como aprobados en rule_candidates.
`sync_rules_from_candidates.py` los aplica a nlp_inference_rules.json
local. Mismo flujo que las reglas de matching.

### Acceso desde /admin/issues

El botón "Generar reporte para Claude Code" existente en /admin/issues
se complementa con un botón nuevo "Analizar con Claude" que:
- Navega a /admin/procesamiento/correcciones
- Dispara el análisis automáticamente si hay pendientes
- Sin duplicar la lógica en dos lugares

### Al aprobar

```
1. Se crea/modifica la regla en config_overrides
   con _linaje completo:
   {
     created_at, created_by: "claude-api",
     issue_id, oferta_ejemplo,
     justificacion (la de Claude)
   }
2. Issue asociado se marca como resuelto
3. procesada_en_pipeline se actualiza en la oferta
4. El candidato desaparece de la cola
5. updated_at en sistema_estado se actualiza
   → staleness check lo detecta en próximo run
```

### Al rechazar

```
1. El candidato se descarta con motivo (campo libre)
2. El issue queda abierto para revisión manual
3. Se registra en api_usage que fue rechazado
   (para mejorar el prompt con el tiempo)
```

---

## Contador de costos de API

### Campo nuevo en sistema_estado

```sql
ALTER TABLE sistema_estado
ADD COLUMN api_anthropic_usage JSONB DEFAULT '{
  "total_llamadas": 0,
  "total_tokens_input": 0,
  "total_tokens_output": 0,
  "costo_usd_estimado": 0.0,
  "ultimo_uso": null,
  "llamadas_hoy": 0,
  "costo_hoy": 0.0
}'::jsonb;
```

### Visible en /admin/metricas

En la sección de KPIs existente, agregar card:

```
┌─────────────────────────────┐
│ API Anthropic               │
│ $0.27 total · $0.07 hoy    │
│ 12 llamadas · 54K tokens   │
│ Último uso: hace 2 horas   │
└─────────────────────────────┘
```

Con alerta si `costo_hoy > $1.00`:
```
⚠️ Uso de API Anthropic elevado hoy ($X.XX)
   Revisá si hay llamadas duplicadas o innecesarias.
```

### Cálculo de costo estimado

```
Modelo: claude-sonnet-4-6
Input:  $3.00 / 1M tokens
Output: $15.00 / 1M tokens

Por análisis típico (~10 correcciones):
    Input estimado:  ~8.000 tokens → $0.024
    Output estimado: ~3.000 tokens → $0.045
    Total: ~$0.07 por análisis
```

---

## Endpoint de análisis

**Archivo:** `app/api/admin/analizar-correcciones/route.ts` (nuevo)

```
POST /api/admin/analizar-correcciones

Body: {
  oferta_ids?: string[]     // opcional, si vacío analiza todas las pendientes
  incluir_descripcion?: boolean  // default false
  batch_size?: number       // default 15, máximo 20
}

Response: {
  candidatos: CandidatosPropuestos[],
  tokens_usados: { input: number, output: number },
  costo_estimado: number,
  ofertas_analizadas: number,
  batches_procesados: number
}
```

**Batching obligatorio:**
Con 89 correcciones × ~800 tokens = ~71K tokens. El endpoint
procesa en chunks de `batch_size` (default 15) para:
- Evitar timeouts de Vercel (max 60s por request)
- Controlar el costo por llamada (~$0.10 por batch de 15)
- Permitir progreso visible en la UI

**Rate limit de seguridad:**
Máximo 5 llamadas a la API de Anthropic por día.
Si se supera, el endpoint retorna error 429 con mensaje claro.

El endpoint:
1. Verifica rate limit diario (max 5 llamadas)
2. Lee las correcciones pendientes de Supabase
3. Obtiene reglas_candidatas para cada título
   (top 3 reglas que matchean via matching_rules_business.json)
4. Construye prompt por batch incluyendo campos NLP relevantes
5. Llama a la API de Anthropic (claude-sonnet-4-6)
6. Parsea el JSON de respuesta (con retry si es inválido)
7. Guarda los candidatos en tabla `rule_candidates`
8. Actualiza `api_anthropic_usage` en sistema_estado
9. Retorna los candidatos al frontend

**Script de sincronización (Python):**
`scripts/sync_rules_from_candidates.py`

Cuando el operador aprueba un candidato desde la UI, el candidato
queda en `rule_candidates` con estado 'aprobado'. Este script
lee los candidatos aprobados y los aplica a los JSONs locales:

```
Candidato tipo regla_nueva    → agrega a matching_rules_business.json
Candidato tipo fix_regla      → modifica regla existente
Candidato tipo sinonimo       → agrega a sinonimos_argentinos_esco.json
Candidato tipo nlp_correccion → agrega a nlp_inference_rules.json
Candidato tipo nlp_area       → agrega keyword a area_funcional
Candidato tipo nlp_limpieza   → agrega patrón a limpieza_tareas
```

El script se corre localmente después de aprobar candidatos en la UI.
Es el mismo patrón que los otros scripts de sync del pipeline.

---

## Tabla nueva: `rule_candidates`

```sql
CREATE TABLE rule_candidates (
    id              BIGSERIAL PRIMARY KEY,
    oferta_id       TEXT,
    issue_ids       TEXT[],
    tipo            TEXT NOT NULL,
    propuesta       JSONB NOT NULL,
    justificacion   TEXT,
    confianza       TEXT,
    afecta_otras    BOOLEAN DEFAULT FALSE,
    estado          TEXT DEFAULT 'pendiente',
    -- pendiente | aprobado | rechazado
    revisado_por    TEXT,
    revisado_at     TIMESTAMPTZ,
    motivo_rechazo  TEXT,
    generado_por    TEXT DEFAULT 'claude-api',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_candidates_estado  ON rule_candidates(estado);
CREATE INDEX idx_candidates_tipo    ON rule_candidates(tipo);
CREATE INDEX idx_candidates_oferta  ON rule_candidates(oferta_id);

ALTER TABLE rule_candidates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "platform_admin_only" ON rule_candidates
    FOR ALL TO authenticated
    USING (auth.jwt() ->> 'role' = 'platform_admin');
```

---

## Cambios por archivo

```
Supabase (migrations):
    → ADD COLUMN api_anthropic_usage en sistema_estado
    → CREATE TABLE rule_candidates + índices + RLS

Python (script nuevo):
    scripts/sync_rules_from_candidates.py
        → lee rule_candidates con estado 'aprobado'
        → aplica a matching_rules_business.json
        → aplica a sinonimos_argentinos_esco.json
        → aplica a nlp_inference_rules.json
        → marca candidatos como 'sincronizado'

Next.js (API):
    app/api/admin/analizar-correcciones/route.ts (nuevo)
        → batching con batch_size=15
        → rate limit 5 llamadas/día
        → llama a API Anthropic con prompt enriquecido
        → incluye reglas_candidatas y campos NLP por tipo
        → guarda candidatos en rule_candidates
        → actualiza api_anthropic_usage

Next.js (UI):
    app/admin/procesamiento/correcciones/page.tsx (NUEVA)
        → página principal del Componente 4
        → botón "Analizar con Claude" con contador de costo
        → tabs: Reglas / Sinónimos / Skills / NLP / Excepciones
        → cards con confianza, aprobar/rechazar/editar por tab

    app/admin/metricas/page.tsx
        → KPI card de uso API Anthropic
        → alerta si costo_hoy > $1.00

    app/admin/issues/page.tsx
        → botón "Analizar con Claude" que navega a
          /admin/procesamiento/correcciones y dispara análisis
```

---

## Tests requeridos

```
Python — no aplica (es todo Next.js)

React — Endpoint:
test_analizar_correcciones_llama_api()
    → dado correcciones pendientes
    → endpoint llama a Anthropic API
    → retorna candidatos estructurados

test_candidatos_se_guardan_en_bd()
    → dado respuesta válida de Claude
    → candidatos aparecen en rule_candidates

test_batching_funciona()
    → dado 30 correcciones y batch_size=15
    → endpoint hace 2 llamadas a la API
    → todos los candidatos se guardan

test_rate_limit_diario()
    → dado 5 llamadas ya realizadas hoy
    → sexta llamada retorna error 429

test_reglas_candidatas_en_prompt()
    → dado oferta con regla R211 que matchea el título
    → prompt incluye R211 en reglas_candidatas
    → Claude no propone regla duplicada

test_campos_nlp_en_prompt_cuando_corresponde()
    → dado corrección tipo nlp_fix
    → prompt incluye tareas_explicitas y skills_tecnicas

test_api_usage_se_actualiza()
    → después de cada llamada
    → api_anthropic_usage tiene tokens y costo actualizados

test_respuesta_invalida_no_rompe()
    → dado respuesta de Claude que no es JSON válido
    → endpoint hace retry
    → si falla 2 veces, retorna error manejable

React — UI candidatos:
test_candidatos_se_muestran()
    → dado rule_candidates con 3 pendientes
    → sección muestra las 3 cards

test_aprobar_crea_regla_con_linaje()
    → al aprobar candidato tipo regla_nueva
    → config_overrides recibe la regla con _linaje
    → issue se cierra
    → candidato pasa a estado 'aprobado'

test_rechazar_con_motivo()
    → al rechazar con motivo
    → candidato pasa a estado 'rechazado'
    → issue queda abierto

test_kpi_costo_api_visible()
    → dado api_anthropic_usage con datos
    → card muestra costo total y costo hoy

test_alerta_costo_elevado()
    → dado costo_hoy > 1.00
    → alerta visible en /admin/metricas
```

---

## Criterio de done

```
□ Migration sistema_estado con api_anthropic_usage
□ Migration rule_candidates con RLS
□ Endpoint /api/admin/analizar-correcciones funciona
□ Batching con batch_size=15 implementado
□ Rate limit de 5 llamadas/día implementado
□ Prompt incluye reglas_candidatas (evita duplicados)
□ Prompt incluye campos NLP según tipo de problema
□ Llamada a API Anthropic con retry en JSON inválido
□ Candidatos NLP se guardan con tipo correcto
□ api_anthropic_usage se actualiza después de cada llamada
□ Script sync_rules_from_candidates.py implementado
□ Script aplica candidatos NLP a nlp_inference_rules.json
□ Página /admin/procesamiento/correcciones creada
□ Tabs por tipo (Reglas/Sinónimos/Skills/NLP con 4 sub-tipos/Excepciones)
□ Cards con confianza, tipo, issue, botones en cada tab
□ Botón "Analizar con Claude" en /admin/issues navega correctamente
□ Aprobar regla_nueva → config_overrides con _linaje
□ Aprobar fix_regla → modifica regla existente con _linaje
□ Rechazar → motivo registrado, issue queda abierto
□ KPI card de costo API en /admin/metricas
□ Alerta si costo_hoy > $1.00
□ 14 tests pasando
□ Smoke test con correcciones reales de Cynthia:
  - Clickear "Analizar con Claude"
  - Verificar que candidatos aparecen en la UI
  - Aprobar uno → verificar que regla se crea con linaje
  - Verificar que issue se cierra automáticamente
  - Verificar que costo se refleja en el KPI
□ No regresión: tests existentes en verde
```

---

## Lo que NO hace este spec

- No procesa skills_gold_set automáticamente — esas van a M-10
- No automatiza la aprobación — siempre requiere humano
- No expone la API key en el frontend (va en variables
  de entorno del servidor Next.js)
- No limita el acceso a Cynthia — solo platform_admin
  puede aprobar, pero Cynthia puede ver los candidatos
  que nacieron de sus correcciones (read-only)
- No aplica los candidatos aprobados automáticamente al JSON
  local — requiere correr sync_rules_from_candidates.py
- No cubre todas las secciones de nlp_inference_rules.json
  En esta versión solo cubre:
  correccion_sector, area_funcional, limpieza_tareas
  Las otras secciones (modalidad, seniority, etc.) se agregan
  en iteraciones futuras si aparecen casos de Cynthia

---

## Nota sobre la API key

La key de Anthropic va en variables de entorno del servidor:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Se agrega en Vercel Dashboard → Settings → Environment Variables.
Nunca se expone al cliente. El endpoint es server-side only.

El costo se acumula en la cuenta de API de Anthropic
(console.anthropic.com) — separado de la suscripción Pro/Max.
Estimado: ~$0.07 por análisis de 10 correcciones.
