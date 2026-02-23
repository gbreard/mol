# MOL - Monitor de Ofertas Laborales

## LEER PRIMERO: Estado Actual

**ANTES DE HACER CUALQUIER COSA, leer `.ai/learnings.yaml` para el estado actual del trabajo.**

El archivo `learnings.yaml` contiene:
- `current_state`: Qué estamos haciendo AHORA (ofertas, versiones, próximo paso)
- `ultimo_trabajo`: Qué se hizo en la última sesión
- `problemas_conocidos`: Issues actuales
- **`conteos`**: SINGLE SOURCE OF TRUTH para cantidades (reglas, skills, etc.)

**Comando del usuario: "Guardá estado"** → Ejecutar `python scripts/sync_learnings.py` + agregar notas en ultimo_trabajo si es necesario.

**AUTO-SYNC + REPORTE DE FASES (v2.0):** Al iniciar sesión, Claude recibe automáticamente:
- **Reporte de las 3 fases** con métricas actuales (ofertas, NLP, matching, validación)
- **Sugerencia de fase** basada en qué necesita atención (errores, pendientes, etc.)
- **Conteos actualizados** desde configs y BD

Triggers:
- **Al iniciar sesión** → Hook SessionStart (`.claude/settings.json`)
- Al ejecutar pipeline → `sync_learnings_yaml()` al final
- Manual: `python scripts/sync_learnings.py` (con `--human` para formato detallado)

---

## PENDIENTE CRITICO: Rotar Supabase service_role_key (S-01)

**La `service_role_key` actual está comprometida** (existe en el historial de git). El código ya fue limpiado (commit `9f904093`) pero la key vieja sigue siendo válida.

**Pasos a realizar (manual):**
1. Ir a **Supabase Dashboard → Settings → API** → regenerar `service_role_key`
2. Actualizar `config/supabase_config.json` local con la nueva key
3. Actualizar `SUPABASE_SERVICE_ROLE_KEY` en **Vercel** (si se usa)
4. Verificar que `sync_to_supabase.py` y `generate_mol_skills_profile.py` sigan funcionando
5. **Borrar esta sección de CLAUDE.md** una vez completado

---

## Descripcion
Sistema de monitoreo del mercado laboral argentino para OEDE. Scrapea ofertas de empleo, extrae informacion con NLP, clasifica segun taxonomia ESCO, y provee dashboards para analistas.

## Estado Actual

> **CONTEOS OFICIALES:** Ver `.ai/learnings.yaml` sección `conteos` (single source of truth)

- NLP v11.3 (20 campos + postprocessor + qwen2.5:7b)
- **Matching v3.4.2 ESCO-FIRST** - ESCO es target, ISCO se deriva
- **Conteos dinámicos** (ver `learnings.yaml`): reglas_negocio, reglas_validacion, sinonimos_argentinos
- **Auto-sync** de learnings.yaml activado (v1.0)

### Matching v3.4.2 ESCO-First (2026-01-21)
```
PRINCIPIO: ESCO es el TARGET, ISCO es CONSECUENCIA

FLUJO DE PRIORIDAD:
1. REGLAS DE NEGOCIO (si aplican) → GANAN SIEMPRE
   - Buscan ocupación ESCO por label exacto
   - ISCO se deriva de la ocupación encontrada

2. DICCIONARIO ARGENTINO (si no hay regla)
   - Mapea términos argentinos a ISCO

3. SEMÁNTICO (fallback)
   - Skills + título embeddings

METADATA GUARDADA:
- isco_semantico, score_semantico (siempre calculado)
- isco_regla, regla_aplicada (si aplica regla)
- dual_coinciden: 1=mismo, 0=difieren, NULL=solo semántico
- decision_metodo: "regla_prioridad" | "semantico_default"
```

### Trabajo en Curso
- Validando 110 ofertas para dashboard (próximo paso: revisión en Google Sheets)
- Gold Set de referencia: 49 casos (archivo histórico)

### Sistema de Priorización v1.0 (2026-01-20)

El pipeline procesa ofertas **por prioridad**, no por orden de scraping.

**Criterios de scoring:**
| Criterio | Peso | Lógica |
|----------|------|--------|
| Fecha publicación | 40% | Más reciente = mayor score |
| Cantidad vacantes | 30% | Más vacantes = mayor impacto |
| Permanencia | 30% | Baja permanencia = alta demanda |

**Tabla:** `ofertas_prioridad` (estados: pendiente → en_proceso → procesado)

**Comandos:**
```bash
# Ver estado de la cola
python scripts/get_priority_batch.py --queue-status

# Procesar lote de 100 por prioridad
python scripts/run_validated_pipeline.py --limit 100

# Ver próximo lote sin procesar
python scripts/get_priority_batch.py --size 100
```

**Bloqueo por errores:** El sistema **NO avanza** al siguiente lote si hay errores pendientes.
```
Lote 1 → 5 errores → [BLOQUEADO] → Resolver errores → [DESBLOQUEADO] → Lote 2
```

Para forzar (NO recomendado): `--force-new-batch`

---

## Modelo de 3 Fases

El proyecto se organiza en 3 macro-fases independientes:

| Fase | Descripcion | Ubicacion Principal | Salida |
|------|-------------|---------------------|--------|
| 1. Adquisicion | Scraping, deteccion bajas | `01_sources/`, `run_scheduler.py` | BD cruda |
| 2. Procesamiento | NLP, Skills, Matching, **Validacion** | `database/`, `config/`, `export_validation_excel.py` | Excel validacion + datos validados |
| 3. Presentacion | Dashboard (solo validados) | `fase3_dashboard/`, `Visual--/`, `sync_to_supabase.py` | Dashboard usuarios finales |

**Para trabajar en una fase especifica**, indicar en `learnings.yaml`:
```yaml
fase_actual: "procesamiento"  # adquisicion | procesamiento | presentacion
```

**REGLA:** Si modificas el pipeline de una fase, actualizar `docs/reference/ARQUITECTURA_3_FASES.md`.

> Arquitectura completa: `docs/reference/ARQUITECTURA_3_FASES.md`

---

## Deploy Dashboard (Fase 3)

**URL producción:** https://mol-nextjs.vercel.app

**Arquitectura:**
```
fase3_dashboard/mol-dashboard/  →  Vercel (mol-dashboard)  →  mol-nextjs.vercel.app
         ↓                                ↓
    Código local                    Deploy via CLI
         ↓                                ↓
   gbreard/mol (GitHub)            Supabase (datos)
```

**IMPORTANTE:** El deploy NO es automático. No está vinculado a GitHub por limitaciones del plan gratuito de Vercel.

### Flujo de trabajo

1. **Desarrollar** en localhost:
   ```bash
   cd fase3_dashboard/mol-dashboard
   npm run dev
   # Abrir http://localhost:3000
   ```

2. **Cuando está listo** → decirle a Claude: "commitear y deployar"

3. **Claude ejecuta:**
   ```bash
   # Regenerar architecture JSON (si cambiaron pantallas o pipeline)
   python scripts/generate_architecture_json.py

   # Commit a GitHub
   git add fase3_dashboard/mol-dashboard/
   git commit -m "feat(dashboard): descripción del cambio"
   git push origin main

   # Deploy a Vercel
   cd fase3_dashboard/mol-dashboard
   npx vercel --prod --yes

   # IMPORTANTE: Actualizar alias (el deploy crea URL nueva cada vez)
   npx vercel alias [url-del-deploy] mol-nextjs.vercel.app
   ```

   **Nota:** Sin el último comando, `mol-nextjs.vercel.app` queda apuntando al deploy anterior.

### Comandos útiles Vercel

```bash
# Ver proyectos
npx vercel ls

# Deploy a producción
npx vercel --prod --yes

# Ver logs de un deploy
npx vercel logs [url-del-deploy]

# Login (si expira la sesión)
npx vercel login
```

### Variables de entorno (ya configuradas)

| Variable | Valor |
|----------|-------|
| NEXT_PUBLIC_SUPABASE_URL | https://uywzoyhjjofsvvsrrnek.supabase.co |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | (configurada en Vercel) |

---

## Gestión de Issues (Supabase)

Los issues/feedback de usuarios están en la tabla `issues` de Supabase. La **anon key NO tiene permisos de UPDATE** (RLS). Usar siempre el **service role key** via Python.

### Actualizar estado de un issue

```python
python3 -c "
import json
from supabase import create_client

config = json.load(open('config/supabase_config.json'))
client = create_client(config['url'], config['service_role_key'])

client.table('issues').update({
    'estado': 'resuelto',
    'resuelto_at': '2026-02-12T00:00:00Z',
    'solucion_aplicada': 'Descripción de lo que se hizo',
    'config_modificada': 'archivos modificados'
}).eq('id', 'UUID-DEL-ISSUE').execute()
"
```

### Listar issues pendientes

```python
python3 -c "
import json
from supabase import create_client

config = json.load(open('config/supabase_config.json'))
client = create_client(config['url'], config['service_role_key'])

result = client.table('issues').select('id,titulo,estado,prioridad').in_('estado', ['pendiente','en_progreso']).order('created_at', desc=True).execute()
for i in result.data:
    print(f\"{i['id'][:8]} | {i['estado']:12} | {i['prioridad']:6} | {i['titulo']}\")
"
```

### Campos actualizables

| Campo | Tipo | Cuándo |
|-------|------|--------|
| `estado` | `pendiente` / `en_progreso` / `resuelto` / `descartado` | Siempre al cambiar estado |
| `resuelto_at` | ISO timestamp | Al marcar resuelto |
| `solucion_aplicada` | string | Al marcar resuelto |
| `config_modificada` | string | Si se modificaron archivos |
| `ofertas_afectadas` | number | Si aplica |
| `sprint` | string | Para tracking |

**Config:** `config/supabase_config.json` (contiene `url` + `service_role_key`)

---

## Documentación Extendida

### Planificación del Producto (FUENTE DE VERDAD)

**IMPORTANTE:** Toda la planificación del producto está en `docs/plan/`. Es la ÚNICA fuente válida para diseño, roadmap y features.

| Documento | Contenido | Cuándo leer |
|-----------|-----------|-------------|
| **`docs/plan/INDEX.md`** | Mapa completo + estado actual | **SIEMPRE al planificar** |
| `docs/plan/01_MODELO_NEGOCIO.md` | Usuarios, niveles, pricing | Definir accesos y planes |
| `docs/plan/02_ARQUITECTURA_PANTALLAS.md` | 30 pantallas (P-01 a P-30) | Agregar/modificar rutas |
| `docs/plan/03_WIREFRAMES/` | Wireframes por área | Diseñar UI |
| `docs/plan/04_MODELO_DATOS.md` | Tablas SQL, schema | Crear/modificar tablas |
| `docs/plan/05_USER_FLOWS.md` | Flujos F-01 a F-05 | Implementar journeys |
| `docs/plan/06_SEGURIDAD.md` | Issues S-01 a S-17 (4 CRITICOS) | **Fase 0 BLOQUEANTE** |
| `docs/plan/07_ESCALABILIDAD.md` | Issues E-01 a E-15 | Performance, cache, índices |
| `docs/plan/08_PROPUESTA_VALOR.md` | Features V-01 a V-15 | Qué falta vs competidores |
| `docs/plan/09_ROADMAP.md` | Fases 0-4 + dependencias | Priorizar trabajo |
| `docs/plan/10_OBSERVABILIDAD.md` | Monitoreo, métricas, pipeline | Admin dashboard |
| `docs/plan/11_CONFIGURACION_ADMIN.md` | /admin/configuracion | Panel admin |
| `docs/plan/12_INSIGHTS_SISTEMA.md` | Performance + ubicación | Insights SQL |
| `docs/plan/ANALISIS_ISSUES_USUARIO.md` | Feedback usuario, sprints | Issues reportados |

### Documentación Técnica (Pipeline)

| Tema | Documento | Cuándo leer |
|------|-----------|-------------|
| **Arquitectura 3 Fases** | `docs/reference/ARQUITECTURA_3_FASES.md` | Entender macro-estructura |
| **Colaboracion (multi-dev)** | `docs/guides/COLABORACION.md` | Trabajo en equipo, sync git |
| Pipeline completo (5 etapas) | `docs/reference/PIPELINE.md` | Entender flujo de datos |
| Run Tracking y Versionado | `docs/guides/RUN_TRACKING.md` | Comparar corridas |
| Sistema de Validación | `docs/guides/VALIDACION.md` | Estados, protección datos |
| Flujos de Optimización | `docs/guides/OPTIMIZACION.md` | Corregir errores NLP/Matching |
| Sincronización Supabase | `docs/guides/SUPABASE_SYNC.md` | Subir datos al dashboard |

**IMPORTANTE:** Antes de optimizar el pipeline, LEER `docs/guides/OPTIMIZACION.md`.

---

## Flujo de Optimización → Validación Humana (v2.2)

El sistema tiene dos fases separadas:

```
FASE 1: OPTIMIZACIÓN (Claude)     FASE 2: VALIDACIÓN (Humano)
─────────────────────────────     ──────────────────────────
Claude itera:                     Solo cuando converge:
- Procesa lote                    - Recibe Excel
- Detecta errores                 - Revisa en Google Sheets
- Crea reglas en JSONs            - Marca OK/ERROR
- Reprocesa                       - Devuelve feedback
- Repite hasta tasa < 5%          - Aprueba o rechaza
```

### Estados de un Lote

| Estado | Descripción | Siguiente acción |
|--------|-------------|------------------|
| `optimizacion` | Claude iterando | Procesar, detectar errores, crear reglas |
| `listo_validacion` | Tasa < 5% (convergido) | Enviar a humano |
| `en_validacion` | Humano revisando | Esperar feedback |
| `validado` | Humano aprobó | Listo para producción |
| `rechazado` | Humano pidió más trabajo | Reabrir y continuar |

### Comandos del Flujo

```python
from scripts.run_tracking import RunTracker
tracker = RunTracker()

# 1. Crear lote
lote_id = tracker.create_batch("Lote 100 ofertas", offer_ids=[...])

# 2. Iterar (Claude optimiza)
while True:
    stats = run_matching_pipeline(offer_ids, source="optimizacion")
    tracker.add_run_to_batch(lote_id, stats['run_id'])

    result = tracker.check_convergence(lote_id)
    if result['convergido']:
        print(f"CONVERGIDO: Tasa {result['tasa']}% < 5%")
        break
    # ... detectar errores, crear reglas, reprocesar ...

# 3. Enviar a humano
tracker.send_to_human_validation(lote_id)  # Genera Excel

# 4. Después del feedback humano
tracker.complete_human_validation(lote_id, aprobado=True)  # o False

# Si rechazado, reabrir
tracker.reopen_batch_for_optimization(lote_id)
```

### Visualizar Estado

```bash
python scripts/show_learning_evolution.py --batches
```

---

## ⛔ PROHIBIDO IMPROVISAR - FLUJO OBLIGATORIO

**Claude: ANTES de ejecutar CUALQUIER comando, verificar este checklist:**

```
□ 1. ¿Existe un script para esto? → USAR ESE SCRIPT
□ 2. ¿El script maneja dependencias (NLP antes de Matching)? → CONFIAR EN ÉL
□ 3. ¿Necesito verificar algo? → EL SCRIPT YA LO HACE
□ 4. ¿Quiero hacer una query manual? → NO, USAR EL SCRIPT
```

### Flujo ÚNICO para Optimización (NO hay alternativa)

```bash
# PASO 1: Procesar ofertas (NLP + Matching + Validación automática)
python scripts/run_validated_pipeline.py --limit 10

# PASO 2: Ver errores detectados
python scripts/review_offer_chain.py --errores --limit 5

# PASO 3: Si hay errores, crear regla en config/*.json correspondiente

# PASO 4: Reprocesar SOLO los IDs con error
python scripts/run_validated_pipeline.py --ids X,Y,Z

# PASO 5: Comparar
python scripts/compare_runs.py --latest

# PASO 6: Cuando converge, exportar Excel
python scripts/exports/export_validation_excel.py --etapa completo --ids X,Y,Z
```

### ❌ PROHIBIDO (durante ejecución del pipeline)

| Acción | Por qué está mal |
|--------|------------------|
| Queries manuales a BD para verificar estado | El script ya verifica |
| Ejecutar matching sin verificar NLP | `run_validated_pipeline` ya lo maneja |
| Crear scripts "demo" o "test" ad-hoc | Ya existen los scripts |
| Inventar pasos no documentados | Todo está en CLAUDE.md |
| Hacer verificaciones "por las dudas" | Confiá en el pipeline |

### ✅ PERMITIDO SIEMPRE

| Acción | Cuándo |
|--------|--------|
| Editar `config/*.json` | Para crear reglas nuevas |
| Leer archivos para entender código | Antes de modificar |
| Ejecutar scripts documentados | Siempre |

### ✅ PERMITIDO INTERVENIR MANUALMENTE cuando:

| Situación | Qué hacer |
|-----------|-----------|
| **Usuario pide ver datos específicos** | Queries a BD para mostrar lo que pide |
| **Diagnosticar error que el script no resuelve** | Investigar cadena completa (NLP → Skills → Matching) |
| **Crear regla nueva** | Consultar BD para ver ejemplos similares, entender el patrón |
| **Entender por qué falló algo** | Leer logs, ver datos de la oferta específica |
| **Usuario pregunta "¿qué pasó con X?"** | Investigar libremente |
| **Depurar un bug en el pipeline** | Queries diagnósticas, leer código |
| **Explorar para planificar** | Antes de ejecutar, entender el estado actual |

### 🔑 REGLA CLAVE

```
EJECUCIÓN DE PIPELINE → Usar scripts, no improvisar
DIAGNÓSTICO/INVESTIGACIÓN → Intervenir manualmente está OK
CREAR REGLAS → Necesito ver datos para entender el patrón
```

**Preguntarse:** ¿Estoy EJECUTANDO el pipeline o estoy INVESTIGANDO/DIAGNOSTICANDO?
- Ejecutando → Scripts únicamente
- Investigando → Queries manuales OK

---

## REGLAS CRÍTICAS - LEER PRIMERO

**ANTES de escribir código o crear archivos:**

1. **LEER este CLAUDE.md COMPLETO** - todo está documentado aquí
2. **NUNCA crear scripts nuevos** - buscar si ya existe uno para la tarea
3. **Cambios van en `config/*.json`** - no en código Python
4. **Si hay que modificar un `.py`**:
   - Versionar (ej: `v3.py` → `v4.py`)
   - Archivar versión anterior en `archive_old_versions/`
   - Actualizar CLAUDE.md

### Entry Points del Sistema (NO crear alternativas)

**⚠️ WSL + Ollama:** Si Ollama corre en Windows y el proyecto en WSL, usar:
```bash
OLLAMA_HOST=172.17.0.1 python scripts/run_validated_pipeline.py --limit 500
```

**⚠️ Lotes grandes (>100):** Correr en BACKGROUND, no esperar:
```bash
OLLAMA_HOST=172.17.0.1 python scripts/run_validated_pipeline.py --limit 500 > /tmp/pipeline.log 2>&1 &
# Verificar progreso:
tail -f /tmp/pipeline.log
```

| Tarea | Comando | NO hacer |
|-------|---------|----------|
| **⭐ Pipeline Completo** | `python scripts/run_validated_pipeline.py --limit 500` | Scripts separados |
| **NLP lote** | `python database/process_nlp_from_db_v11.py --ids X` | Crear script nuevo |
| **Scraping** | `python run_scheduler.py` | Llamar scrapers directo |
| **Comparar runs** | `python scripts/compare_runs.py --latest` | Crear comparador custom |
| **Validar ofertas** | `python scripts/validar_ofertas.py --ids X --estado validado` | UPDATE manual en BD |
| **Export Excel** | `python scripts/exports/export_validation_excel.py --etapa completo --ids X` | - |
| **Sync Supabase** | `python scripts/exports/sync_to_supabase.py` (incremental) | Queries directas a Supabase |
| **Sync Full** | `python scripts/exports/sync_to_supabase.py --full` | - |
| **Reapply Rules** | `python scripts/reapply_rules_to_validated.py` | Reprocesar validadas manualmente |
| **Generar Architecture JSON** | `python scripts/generate_architecture_json.py` | Editar dashboard_architecture.json a mano |

**⭐ REGLA CRÍTICA - Pipeline Integrado:**
- **SIEMPRE** usar `run_validated_pipeline.py` para procesar ofertas
- Ejecuta TODO automáticamente: Matching → Validación → Corrección → Reporte
- Errores se persisten en tabla `validation_errors` (no se pierden)
- Si hay errores que requieren reglas nuevas → genera `metrics/cola_claude_*.json`

### Flujo Completo de Trabajo (v3.4.3)

```
PASO 1: PROCESAR OFERTAS NUEVAS
───────────────────────────────
python scripts/run_validated_pipeline.py --limit 100
  → NLP → Matching → Validación Automática → Reporte Errores

PASO 2: RESOLVER ERRORES (si hay)
─────────────────────────────────
# Ver errores
python scripts/review_offer_chain.py --errores --limit 5

# Crear reglas según tipo de error:
│ Error NLP        │ → config/nlp_inference_rules.json
│ Error Matching   │ → config/matching_rules_business.json
│ Error Limpieza   │ → config/nlp_titulo_limpieza.json

# Reprocesar IDs con error
python scripts/run_validated_pipeline.py --ids X,Y,Z

PASO 3: APLICAR REGLAS A VALIDADAS (si se crearon reglas nuevas)
────────────────────────────────────────────────────────────────
# Las reglas nuevas pueden afectar ofertas YA validadas
# Este script las reprocesa SIN perder el estado de validación
python scripts/reapply_rules_to_validated.py

PASO 4: SINCRONIZAR A SUPABASE
──────────────────────────────
python scripts/exports/sync_to_supabase.py
```

**¿Cuándo usar `reapply_rules_to_validated.py`?**
- Después de crear reglas nuevas en `matching_rules_business.json`
- Cuando hay ofertas validadas que podrían beneficiarse de las nuevas reglas
- El script detecta automáticamente qué ofertas reprocesar (las que tuvieron errores resueltos)

---

## Pipeline de Validación con Aprendizaje (v2.0)

**Principio:** Claude REVISA casos individuales para APRENDER y crear REGLAS en JSONs.
El sistema luego aplica las reglas automáticamente. Claude NO reemplaza al LLM.

### Cadena de Dependencias

```
SCRAPING → NLP → SKILLS → MATCHING
              ↓       ↓         ↓
           tareas  extraídas  ESCO code
           ubicación  de tareas+título
           seniority
           área

Si NLP extrae mal las tareas → Skills quedan mal → Matching falla
```

### Flujo de Trabajo (UN COMANDO)

```
COMANDO ÚNICO (hace TODO automáticamente):
──────────────────────────────────────────
python scripts/run_validated_pipeline.py --limit 100

EJECUTA AUTOMÁTICAMENTE:
  1. MATCHING     → match_ofertas_v3.py
  2. VALIDACIÓN   → auto_validator.py (detecta errores → BD)
  3. CORRECCIÓN   → auto_corrector.py (arregla lo que puede → BD)
  4. REPORTE      → genera cola_claude.json si hay errores escalados

OPCIONES:
  --limit N          Procesar N ofertas
  --ids X,Y,Z        Procesar IDs específicos
  --export-markdown  Generar validation/feedback_*.md para GitHub

RESULTADO:
  - Errores detectados → tabla validation_errors (persistidos)
  - Errores corregidos → marcados corregido=1 en BD
  - Errores escalados → metrics/cola_claude_*.json + escalado_claude=1 en BD
```

### Si Hay Errores Escalados

```
CLAUDE REVISA cola_claude_*.json:
─────────────────────────────────
python scripts/review_offer_chain.py --errores --limit 5

Claude ve TODA la cadena:
1. SCRAPING: ¿Datos completos?
2. NLP: ¿Tareas, ubicación, seniority, área correctos?
3. SKILLS: ¿Coherentes con título y tareas?
4. MATCHING: ¿ISCO correcto?

CREAR REGLA según dónde falló:
| Falla en | Config a modificar |
|----------|-------------------|
| NLP - tareas | prompt o nlp_extraction_patterns.json |
| NLP - ubicación | config/nlp_preprocessing.json |
| NLP - seniority | config/nlp_inference_rules.json |
| NLP - área | config/nlp_inference_rules.json |
| Skills - faltan | config/skills_database.json |
| Matching | config/matching_rules_business.json |

REPROCESAR IDs afectados:
python scripts/run_validated_pipeline.py --ids X,Y,Z
```

### Archivos del Sistema de Validación

| Archivo | Función |
|---------|---------|
| `scripts/run_validated_pipeline.py` | **⭐ ENTRY POINT PRINCIPAL** - orquesta todo |
| `config/validation_rules.json` | Reglas de auto-detección (ver conteos en learnings.yaml) |
| `config/diagnostic_patterns.json` | Patrones para identificar punto de falla |
| `config/auto_correction_map.json` | Mapeo diagnóstico → config a modificar |
| `database/auto_validator.py` | Validador automático (persiste en BD) |
| `database/auto_corrector.py` | Corrector automático (actualiza BD) |
| `scripts/review_offer_chain.py` | **Revisión UNO POR UNO** (cadena completa) |

### Tablas de Validación en BD

| Tabla | Función |
|-------|---------|
| `validation_errors` | Errores detectados por auto_validator (persistidos) |
| `ofertas_esco_matching` | Estado de matching y validación |
| `pipeline_runs` | Historial de corridas |

**Consultas útiles:**
```sql
-- Errores pendientes (no resueltos)
SELECT * FROM v_errores_pendientes;

-- Resumen por tipo de error
SELECT * FROM v_errores_por_tipo;

-- Errores escalados a Claude
SELECT * FROM validation_errors WHERE escalado_claude = 1 AND resuelto = 0;
```

### Ejemplo de Revisión Claude

```
Caso: "Gerente de Ventas" → ISCO 2433 (incorrecto, debería ser 1221)

Claude revisa cadena:
1. SCRAPING: OK
2. NLP: nivel_seniority = NULL ❌ (debería ser "manager")
3. SKILLS: OK
4. MATCHING: Sin seniority, no priorizó nivel directivo

Diagnóstico: Falla RAÍZ en NLP (seniority no inferido de "Gerente")

Claude crea reglas:
1. nlp_inference_rules.json: {"keyword": "gerente", "nivel_seniority": "manager"}
2. matching_rules_business.json: R_GERENTE_VENTAS → forzar_isco 1221

Reprocesar → ISCO correcto
Próxima vez: Sistema aplica regla automáticamente
```

→ **Plan completo:** `/home/gerardo/.claude/plans/elegant-crunching-hippo.md`
→ **Guía optimización:** `docs/guides/OPTIMIZACION.md`

---

### Flujo de Optimización LEGACY (sin revisión Claude)

```
1. PROCESAR    → run_matching_pipeline(ids, source="gold_set")
2. EXPORTAR   → export_validation_excel.py --ids X
3. CORREGIR   → Modificar config/*.json (NO código Python)
4. COMPARAR   → compare_runs.py --latest
5. REPETIR    → Pasos 2-4 hasta que esté OK
6. VALIDAR    → validar_ofertas.py --ids X --estado validado
```

→ **Detalles:** `docs/guides/VALIDACION.md`

### Feedback Loop via Google Sheets

```
FLUJO:
1. Exportar   → python scripts/exports/export_validation_excel.py --etapa completo --ids X
2. Subir      → Excel a Google Sheets (manual)
3. Humano     → Edita en Google Sheets (columnas resultado, isco_correcto, comentario)
4. Claude     → Usuario comparte link/CSV, Claude lee y crea reglas
```

**Columnas editables por humano:**
- `resultado`: `OK` | `ERROR` | `REVISAR`
- `isco_correcto`: ISCO esperado (si es ERROR)
- `comentario`: Descripción del problema

### Protección de Datos Validados (v2.0 - 2026-01-20)

**REGLA ABSOLUTA:** Una oferta con `estado_validacion = 'validado'` NUNCA debe:
- Ser reprocesada por NLP
- Ser reprocesada por Matching
- Aparecer en Excel de validación nuevo

**Capas de protección:**

| Capa | Ubicación | Qué hace |
|------|-----------|----------|
| Query filtrada | `export_validation_excel.py:476` | Excluye validadas de selección |
| Query filtrada | `auto_validator.py:590` | Excluye validadas de validación |
| Error explícito | `match_ofertas_v3.py:1368` | Lanza ValueError si hay validadas |
| Trigger BD | `migrations/016_*.sql` | Bloquea UPDATE en ofertas validadas |

**Verificar protección:**
```bash
python scripts/check_validated_protection.py
```

**Si NECESITO reprocesar una oferta validada (caso excepcional):**
```bash
# 1. Desbloquear con justificación obligatoria
python scripts/admin_unlock_validated.py --ids 123,456 --motivo "Razón del desbloqueo"

# 2. Reprocesar normalmente
python scripts/run_validated_pipeline.py --ids 123,456
```

**NO hacer:**
- Usar `force=True` en el pipeline (bypasea controles)
- UPDATE directo a BD sin usar script admin
- Cambiar estado manualmente a 'pendiente'

---

## VERSIONES ACTUALES - USAR SIEMPRE ESTAS

### NLP Pipeline

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline NLP | `database/process_nlp_from_db_v11.py` | v7, v8, v9, v10 |
| Prompt | `database/prompts/extraction_prompt_lite_v1.py` | v8, v9, v10 |
| Regex Patterns | `database/patterns/regex_patterns_v4.py` | v1, v2, v3 |
| Normalizador | `database/normalize_nlp_values.py` | - |

**Arquitectura v11.3:**
```
CAPA 0: Regex (salarios, jornada) + Scraping directo (modalidad)
CAPA 1: LLM Qwen2.5:7b (20 campos)
CAPA 2: Postprocessor (config/nlp_*.json)
CAPA 3: Skills implícitas (BGE-M3 + ESCO embeddings)
```

### Matching Pipeline v3.4.2 ESCO-First

| Componente | Archivo ACTUAL | NO USAR |
|------------|----------------|---------|
| Pipeline Matching | `database/match_ofertas_v3.py` v3.4.2 | v2.py, v8.x |
| Matcher por Skills | `database/match_by_skills.py` v1.2.0 | - |
| Skills Extractor | `database/skills_implicit_extractor.py` v2.3 | - |
| Skills Rules Config | `config/skills_rules.json` (25 reglas) | - |
| Skills Rules Matcher | `database/skills_rules_matcher.py` | - |
| Diccionario Argentino | `config/sinonimos_argentinos_esco.json` (13 ocup) | - |
| Config reglas negocio | `config/matching_rules_business.json` (124 reglas con ESCO válido) | hardcodeados |
| Config principal | `config/matching_config.json` | - |

**Arquitectura v3.4.2 (orden de prioridad):**
```
PRINCIPIO: ESCO es TARGET, ISCO es CONSECUENCIA

1. REGLAS DE NEGOCIO (GANAN SIEMPRE si aplican)
   └── Buscan ESCO label exacto → derivan ISCO
        ↓ (si no hay regla)
2. DICCIONARIO ARGENTINO ← Vocabulario local → ISCO
        ↓ (si no matchea)
3. SEMÁNTICO (BGE-M3) ← Skills 60% + Titulo 40%
        ↓
4. PENALIZACIONES (sector, seniority)
        ↓
5. PERSISTIR EN BD (con metadata dual: isco_semantico, isco_regla)
```

→ **Detalles:** `docs/reference/PIPELINE.md`

### Skills Dual System v2.3 (2026-01-22)

Sistema DUAL para extracción de skills (mismo patrón que ISCO matching):
- **Reglas de skills** (prioridad) + **Semántico BGE-M3** (fallback)
- Guarda AMBOS resultados para comparación y métricas

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| Skills Rules Config | `config/skills_rules.json` | 25 reglas que fuerzan skills específicas |
| Skills Rules Matcher | `database/skills_rules_matcher.py` | Evaluador de reglas |
| Skills Extractor | `database/skills_implicit_extractor.py` v2.3 | Método `extract_skills_dual()` |

**Arquitectura Dual:**
```
1. Evaluar REGLAS DE SKILLS (skills_rules.json)
   └── Si matchea → skills_regla (prioridad)
        ↓
2. Extraer SEMÁNTICO (BGE-M3 siempre)
   └── skills_semantico
        ↓
3. Comparar ambos
   └── dual_coinciden_skills: 1=igual, 0=difieren, NULL=solo semántico
        ↓
4. Merge final
   └── skills_final = skills_regla + skills_semantico únicos
```

**Columnas en BD (`ofertas_esco_matching`):**
- `skills_regla_json`: Skills forzadas por regla (JSON array)
- `skills_semantico_json`: Skills de BGE-M3 (JSON array)
- `skills_regla_aplicada`: ID de regla aplicada (ej: "RS02_contador")
- `dual_coinciden_skills`: 1=coinciden, 0=difieren, NULL=sin regla

**Reglas de Validación (V24-V30):**
| Regla | Detecta | Severidad |
|-------|---------|-----------|
| V24 | Skills no coherentes con ISCO (< 30%) | alto |
| V25 | Tareas vacías pero skills presentes | medio |
| V26 | Formato tareas incorrecto (`,` vs `;`) | medio |
| V27 | Divergencia regla vs semántico | warning |
| V28 | Sin skills esenciales del ISCO | alto |
| V29 | Tareas muy cortas (< 50 chars) | bajo |
| V30 | Puesto IT sin skills técnicas | alto |

**Métricas en sync_learnings.py:**
```
SKILLS DUAL (v2.3):
  Por regla: 45% | Por semantico: 55%
  Dual coinciden: 78%
  Skills promedio: 6.2/oferta
```

### Tests y Gold Sets

| Conjunto | Ubicación | Casos | Uso |
|----------|-----------|-------|-----|
| **Ofertas en validación** | BD `ofertas_esco_matching` | **100** | Validar para dashboard |
| Gold Set referencia | `database/gold_set_manual_v2.json` | 49 | Test de regresión |
| NLP Extraction | `tests/nlp/gold_set.json` | 20+ | Test NLP |

**IMPORTANTE:** El trabajo actual es sobre las **100 ofertas en validación**, no el Gold Set de 49.

```bash
# Ejecutar tests
python -m pytest tests/ -v

# Test Gold Set Matching (referencia)
pytest tests/matching/test_gold_set_manual.py -v

# Ver estado de las 100 ofertas en validación
python scripts/validar_ofertas.py --status
```

---

## Configuración

### Configs NLP (Postprocessor)

| Archivo | Propósito |
|---------|-----------|
| `config/nlp_preprocessing.json` | Parsing ubicación |
| `config/nlp_inference_rules.json` | Inferencia área/seniority/modalidad |
| `config/nlp_validation.json` | Validación tipos |
| `config/nlp_extraction_patterns.json` | Regex experiencia |
| `config/nlp_normalization.json` | CABA → Capital Federal |

### Configs Matching

| Archivo | Propósito |
|---------|-----------|
| `config/matching_config.json` | Pesos, umbrales, penalizaciones |
| `config/matching_rules_business.json` | Reglas de negocio (ver conteos en learnings.yaml) |
| `config/area_funcional_esco_map.json` | Mapeo área → ISCO |
| `config/sector_isco_compatibilidad.json` | Compatibilidad sector-ISCO |

### Diccionarios

| Archivo | Propósito |
|---------|-----------|
| `config/skills_database.json` | ~320 skills técnicas |
| `config/oficios_arg.json` | ~170 oficios argentinos |

---

## Comandos Clave

```bash
# === SCRAPING ===
python run_scheduler.py --test

# === NLP ===
python database/process_nlp_from_db_v11.py --ids 123,456

# === MATCHING ===
pytest tests/matching/test_gold_set_manual.py -v

# === VALIDACIÓN ===
python scripts/validar_ofertas.py --status
python scripts/compare_runs.py --list
python scripts/compare_runs.py --latest
python scripts/validar_ofertas.py --ids 123,456 --estado validado

# === EXPORT ===
python scripts/exports/export_validation_excel.py --etapa completo --ids X
```

---

## Guía Rápida: Mapeo Error → Config

| Tipo de Error | Config a Editar |
|---------------|-----------------|
| Provincia/Localidad mal | `config/nlp_preprocessing.json` |
| Seniority incorrecto | `config/nlp_inference_rules.json` |
| Modalidad incorrecta | `config/nlp_inference_rules.json` |
| Área funcional incorrecta | `config/nlp_inference_rules.json` |
| ISCO incorrecto para título X | `config/matching_rules_business.json` |

→ **Tabla completa:** `docs/guides/OPTIMIZACION.md`

---

## Regla de Versionado

**OBLIGATORIO:** Cuando se crea una nueva versión:

1. Crear nueva versión (ej: `v11.py`)
2. Archivar anterior en `database/archive_old_versions/`
3. Verificar que nada importe el archivo archivado
4. Actualizar CLAUDE.md

**NUNCA** dejar dos versiones activas en el mismo directorio.

---

## Ubicación de Scripts

| Si el script es para... | Va en... |
|-------------------------|----------|
| Gold Set NLP | `scripts/nlp/gold_set/` |
| Gold Set Matching | `scripts/matching/gold_set/` |
| Backup/migrate BD | `scripts/db/` |
| Exportar (S3, Excel) | `scripts/exports/` |
| Linear | `scripts/` (raíz) |

**NUNCA** crear `test_*.py` fuera de `tests/`.

---

## Estructura del Proyecto (Resumen)

```
MOL/
├── 01_sources/          # Scraping (bumeran/, zonajobs/, etc.)
├── database/            # BD, NLP processors, matching
│   ├── prompts/         # Prompts LLM
│   ├── patterns/        # Regex patterns
│   └── archive_old_versions/
├── config/              # JSONs de configuración
├── tests/               # Tests pytest
├── scripts/             # Utilidades
│   ├── db/              # BD
│   ├── nlp/gold_set/    # Optimización NLP
│   ├── matching/        # Optimización Matching
│   └── exports/         # Exportaciones
├── docs/                # Documentación
│   ├── guides/          # RUN_TRACKING, VALIDACION, OPTIMIZACION
│   └── reference/       # PIPELINE
├── fase3_dashboard/     # Fase 3: Dashboard y presentación
│   ├── nextjs/          # Dashboard Next.js (desarrollo)
│   └── docs/            # Docs específicos Fase 3
├── Visual--/            # Dashboard R Shiny (legacy)
└── run_scheduler.py     # Entry point scraping
```

---

## Modelos LLM/ML

| Modelo | Uso |
|--------|-----|
| **Qwen2.5:7b** | NLP: extracción semántica |
| **BGE-M3** | Matching: embeddings |
| **ChromaDB** | Skills lookup |

**Requisitos:**
- Ollama en `localhost:11434` con `qwen2.5:7b`
- ChromaDB con vectores en `database/esco_vectors/`

---

## Reglas de Desarrollo

1. **Scraping:** SIEMPRE `run_scheduler.py`, NUNCA scrapers directo
2. **Tests:** Todo cambio NLP/Matching debe pasar Gold Set
3. **Umbrales:** NLP >= 90%, Matching >= 95%
4. **Linear:** Usar cache (`scripts/linear_*.py`), NUNCA MCP directo

---

## Flujo de Branches

```
main                    ← Producción (solo via PR)
  └── develop           ← Integración (pasó Gold Set)
        ├── feature/optimization-nlp
        └── feature/optimization-matching
```

**NUNCA** push directo a `main`. **SIEMPRE** Gold Set antes de merge.

---

## Sesiones Paralelas de Claude Code

**Problema:** Dos sesiones de Claude en el mismo directorio se pisan los branches.
**Solución:** Cada sesión usa su propio **worktree** (misma BD git, distinta carpeta).

### Al iniciar una sesión nueva en paralelo

```bash
# 1. ANTES de abrir Claude, crear worktree para el branch
./scripts/worktree-session.sh create feature/nombre-del-branch

# 2. Abrir Claude Code en esa carpeta
cd /mnt/d/OEDE/Webscrapping-nombre-del-branch
claude

# 3. Si necesitás branch nuevo (se crea desde main)
./scripts/worktree-session.sh new feature/mi-nuevo-feature
```

### Al terminar la sesión

```bash
./scripts/worktree-session.sh remove feature/nombre-del-branch
```

### Reglas

- **NUNCA** hacer `git checkout` a otro branch si hay otra sesión activa
- Cada sesión trabaja en su carpeta, su branch, sin interferir
- Los commits de cualquier worktree son visibles desde todos (mismo repo)
- `./scripts/worktree-session.sh list` para ver sesiones activas

### Estructura de carpetas

```
/mnt/d/OEDE/Webscrapping/                      ← Sesión principal
/mnt/d/OEDE/Webscrapping-admin-arquitectura/    ← Sesión paralela
/mnt/d/OEDE/Webscrapping-otro-feature/          ← Otra sesión paralela
```

---

## Colaboracion Multi-Desarrollador

Este proyecto es trabajado por **multiples personas en distintas fases**.

**LEER:** `docs/guides/COLABORACION.md` para reglas de sync, division de trabajo y referencias a documentacion oficial de Claude Code.

---

## AI Platform Local

Plataforma en `D:\AI_Platform`.

```python
import httpx
GATEWAY = "http://localhost:8080"
```

| Endpoint | Descripción |
|----------|-------------|
| `POST /v1/chat/completions` | LLM |
| `POST /v1/embeddings` | Embeddings |

Docs: http://localhost:8080/docs

---

> **Última actualización:** 2026-01-16
