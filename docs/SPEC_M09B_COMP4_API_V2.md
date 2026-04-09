# M-09b Componente 4 — Análisis Automático con API de Anthropic

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
titulo_limpio
isco_code + isco_label actual
sector_empresa + area_funcional
regla_aplicada + decision_metodo + occupation_match_score
validacion_correcciones.nota (análisis de Cynthia)
validacion_correcciones.ocupacion_corregida (si existe)
validacion_correcciones.skills_editadas (si existen)
```

### Input opcional (solo si nota es ambigua)
```
descripcion completa del aviso (campo descripcion)
tareas_explicitas
skills_tecnicas
```

**Por qué no siempre la descripción completa:**
La descripción del aviso puede tener 1.500+ caracteres. Si la nota
de Cynthia es clara, incluir la descripción duplica tokens sin valor.
Solo se incluye cuando la nota dice cosas como "ver aviso completo"
o cuando no hay nota y solo hay `skills_editadas`.

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
- nlp_fix: corrección de campo NLP (sector, área, educación)
- excepcion_aceptable: el sistema está bien, caso edge
- requiere_revision: no hay suficiente info para decidir

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

### nlp_fix
```json
{
  "tipo": "nlp_fix",
  "propuesta": {
    "campo": "sector_empresa",
    "valor_actual": "Otro",
    "valor_correcto": "Construcción",
    "aplica_a_oferta": "7215160363"
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
Tab NLP         → tipo: nlp_fix
Tab Excepciones → tipo: excepcion_aceptable
```

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
  oferta_ids?: string[]  // opcional, si vacío analiza todas las pendientes
  incluir_descripcion?: boolean  // default false
}

Response: {
  candidatos: CandidatosPropuestos[],
  tokens_usados: { input: number, output: number },
  costo_estimado: number,
  ofertas_analizadas: number
}
```

El endpoint:
1. Lee las correcciones pendientes de Supabase
2. Construye el prompt con los datos de cada oferta
3. Llama a la API de Anthropic
4. Parsea el JSON de respuesta
5. Guarda los candidatos en tabla `rule_candidates`
6. Actualiza `api_anthropic_usage` en sistema_estado
7. Retorna los candidatos al frontend

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

Next.js (API):
    app/api/admin/analizar-correcciones/route.ts (nuevo)
        → llama a API Anthropic
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

test_api_usage_se_actualiza()
    → después de cada llamada
    → api_anthropic_usage tiene tokens y costo actualizados

test_respuesta_invalida_no_rompe()
    → dado respuesta de Claude que no es JSON válido
    → endpoint retorna error manejable sin romper

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
□ Llamada a API Anthropic con prompt correcto
□ Candidatos se guardan en rule_candidates
□ api_anthropic_usage se actualiza después de cada llamada
□ Página /admin/procesamiento/correcciones creada
□ Tabs por tipo (Reglas/Sinónimos/Skills/NLP/Excepciones)
□ Cards con confianza, tipo, issue, botones en cada tab
□ Botón "Analizar con Claude" en /admin/issues navega correctamente
□ Aprobar regla_nueva → config_overrides con _linaje
□ Aprobar fix_regla → modifica regla existente con _linaje
□ Rechazar → motivo registrado, issue queda abierto
□ KPI card de costo API en /admin/metricas
□ Alerta si costo_hoy > $1.00
□ 9 tests pasando
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

- No procesa skills_gold_set — esas van a M-10
- No automatiza la aprobación — siempre requiere humano
- No expone la API key en el frontend (va en variables
  de entorno del servidor Next.js)
- No limita el acceso a Cynthia — solo platform_admin
  puede aprobar, pero Cynthia puede ver los candidatos
  que nacieron de sus correcciones (read-only)

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
