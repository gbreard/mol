# Workflow Issue → Correction → Close

Guía para procesar un batch de issues reportados por un validador humano (Cynthia, Sergio, Diego, etc.).

**Contexto:** Los validadores humanos cargan issues en Supabase (tabla `issues`) con correcciones sobre ofertas procesadas. Este documento explica cómo convertir ese feedback en mejoras permanentes del sistema.

---

## Tipos de corrección que un validador puede reportar

| Tipo | Qué indica el validador | Dónde impacta |
|---|---|---|
| **Clasificación ISCO/ESCO** | "ISCO actual 8131 es incorrecto, debería ser 7511" | `config/matching_rules_business.json` |
| **Atributos NLP** | "Sector: Otro → debería ser Alimentación" | `config/nlp_correction_rules.json` |
| **Skills INCORRECTAS** | "`skill → ❌ Incorrecta`" | Remove de `ofertas_esco_matching.skills_*_json` |
| **Skills FALTANTES** | "Skills sugeridas: filetear pescado, manipular alimentos" | Agregar a `ofertas_esco_matching.skills_regla_json` + `sinonimos_skills_argentinos.json` |
| **Denominación Arg/España** | "Argentina: fileteador / ESCO: limpiador de pescado" | Sólo aclaración (cerrar si ISCO OK) |
| **Meta-criterios** | "En avisos de X, el LLM debe priorizar Y" | Feedback metodológico (cerrar con nota) |

---

## Pipeline completo (5 pasos)

```
1. Parsear issues → identificar tipo de corrección por oferta
2. Aplicar reglas matching (ISCO) → propagar a ofertas similares
3. Aplicar reglas NLP (sector/seniority/area) → corregir ofertas afectadas
4. Inyectar/remover skills → ajustar skills_regla_json
5. Cerrar issues en Supabase + sync
```

---

## Paso 1 — Identificar y categorizar

```bash
# Ver issues pendientes de un autor específico
python3 -c "
import json
from supabase import create_client
from collections import Counter
cfg = json.load(open('config/supabase_config.json'))
client = create_client(cfg['url'], cfg['service_role_key'])
r = client.table('issues').select('estado,id_oferta').or_(
    'autor_nombre.ilike.%cynthia%,autor_email.ilike.%cynthia%'
).execute()
print(f'Total issues: {len(r.data)}')
print(f'Por estado: {dict(Counter(i[\"estado\"] for i in r.data))}')
print(f'Ofertas únicas: {len(set(i[\"id_oferta\"] for i in r.data))}')"
```

---

## Paso 2 — Correcciones ISCO (reglas de matching)

Para cada oferta donde el validador sugiere cambio de ISCO:

### 2a. Verificar labels ESCO reales (CRÍTICO)

```bash
# El matcher descarta reglas con esco_label que no existe en esco_occupations
# Siempre verificar que el label existe exactamente:
python3 scripts/search_esco_skill.py "nombre exacto del label sugerido"

# Si no existe, buscar labels que sí existen para el ISCO target:
python3 -c "
import sqlite3
c = sqlite3.connect('database/bumeran_scraping.db').cursor()
c.execute('SELECT isco_code, preferred_label_es FROM esco_occupations WHERE isco_code = ?', ('C7511',))
for r in c.fetchall(): print(r)"
```

### 2b. Agregar regla a `config/matching_rules_business.json`

Al final de `reglas_forzar_isco`, usando el siguiente número disponible:

```json
"RXXX_nombre_patron": {
  "nombre": "Descripción del puesto",
  "prioridad": 0,
  "condicion": {
    "titulo_original_contiene_alguno": ["palabra1", "palabra2"],
    "titulo_no_contiene_alguno": ["exclusion1"]
  },
  "accion": {
    "forzar_isco": "7511",
    "esco_label": "limpiador de pescado/limpiadora de pescado"
  },
  "activa": true,
  "_linaje": {
    "oferta_ejemplo": "9168162159",
    "autor_correccion": "Cynthia"
  }
}
```

**Reglas de diseño:**
- Usar `titulo_original_contiene_alguno` (no `titulo_contiene_alguno`) cuando hay caracteres como `/a` o títulos limpiados que pierden info
- `prioridad: 0` para sobrescribir reglas existentes; `prioridad: 1` para nuevas categorías
- Si el validador sugiere un ISCO en conflicto con regla existente, agregar `titulo_no_contiene_alguno` para diferenciar

### 2c. Verificar y aplicar

```bash
# Ver a cuántas ofertas validadas afecta (dry-run)
python3 scripts/reapply_rules_to_validated.py --regla RXXX_nombre_patron --dry-run

# Aplicar a ofertas específicas
python3 scripts/reapply_rules_to_validated.py --ids 1234,5678,9012

# O propagar a TODAS las ofertas validadas que matchean la regla
python3 scripts/reapply_rules_to_validated.py --regla RXXX_nombre_patron
```

---

## Paso 3 — Correcciones NLP (sector/seniority/area/experiencia)

Si el validador dice "Sector: Otro → debería ser X", "Seniority: trainee pero pide experiencia":

### 3a. Agregar regla a `config/nlp_correction_rules.json`

```json
{
  "id": "sector_nombre_sector",
  "descripcion_contiene_alguno": ["keyword1", "keyword2"],
  "titulo_contiene_alguno": ["patron_titulo"],
  "override_si_actual_es": ["Otro", null, ""],
  "resultado": "Alimentacion"
}
```

**Orden importa:** las reglas se evalúan de arriba a abajo, la primera que matchea gana. Poner reglas más específicas primero (ej: psicología antes que belleza).

### 3b. Aplicar

```bash
# Dry-run sobre ofertas de un autor
python3 scripts/reapply_nlp_to_validated.py --from-issues --dry-run

# Aplicar sobre IDs específicos
python3 scripts/reapply_nlp_to_validated.py --ids 1234,5678
```

---

## Paso 4 — Skills (inyectar / remover)

### 4a. Inyectar skills sugeridas por el validador

El script busca URIs ESCO automáticamente para las skills que el validador sugirió:

```bash
# Dry-run para ver qué skills mapearon a URIs
python3 scripts/inject_skills_from_issues.py --author cynthia --dry-run

# Aplicar
python3 scripts/inject_skills_from_issues.py --author cynthia
```

**Cobertura esperada:** ~17-30% de skills libres mapean a URIs exactas; el resto requiere ampliación del diccionario argentino (ver Paso 4c).

### 4b. Remover skills incorrectas

Para skills marcadas `→ ❌ Incorrecta`:

```bash
python3 scripts/remove_skills_from_issues.py --author cynthia --dry-run
python3 scripts/remove_skills_from_issues.py --author cynthia
```

### 4c. Ampliar diccionario argentino (para mejor cobertura futura)

Si muchas skills quedan sin mapear, agregarlas al diccionario argentino:

1. Editar `config/sinonimos_skills_argentinos.json` sección `tareas_a_skills`
2. Formato: `"término argentino": "label ESCO existente"`
3. **Verificar que el label destino existe:**
   ```bash
   python3 scripts/search_esco_skill.py "label destino"
   ```
4. Re-importar a la BD:
   ```bash
   python3 scripts/import_argentine_skill_labels.py
   ```

---

## Paso 5 — Cerrar issues + sync

### 5a. Cerrar issues resueltos

Los scripts de los pasos 3 y 4 cierran automáticamente los issues que resuelven. Para cierres manuales:

```python
import json
from datetime import datetime, timezone
from supabase import create_client
cfg = json.load(open('config/supabase_config.json'))
client = create_client(cfg['url'], cfg['service_role_key'])

client.table('issues').update({
    'estado': 'resuelto',
    'resuelto_at': datetime.now(timezone.utc).isoformat(),
    'resuelto_por': 'claude',
    'solucion_aplicada': 'Descripción de qué se hizo',
    'config_modificada': 'config/archivo_modificado.json'
}).eq('id', 'UUID-DEL-ISSUE').execute()
```

### 5b. Sync a Supabase (dashboard)

```bash
python3 scripts/exports/sync_to_supabase.py
```

---

## Troubleshooting común

### La regla ISCO "aplica" pero el ISCO final es otro

**Causa:** El matcher v3 descarta silenciosamente reglas cuyo `esco_label` no existe exactamente en `esco_occupations`. El campo `regla_aplicada` queda con el nombre pero el ISCO viene de otra regla/semántico.

**Solución:**
```bash
# Verificar que el label existe
python3 -c "
import sqlite3
c = sqlite3.connect('database/bumeran_scraping.db').cursor()
c.execute(\"SELECT 1 FROM esco_occupations WHERE LOWER(preferred_label_es) = LOWER('tu label aquí')\")
print('Existe' if c.fetchone() else 'NO EXISTE')"
```

Si no existe, buscar un label real del ISCO target con `search_esco_skill.py` o query directa.

### Un sector sigue siendo "Otro" después de aplicar reglas

**Causa:** Mi regla tiene condiciones AND entre `titulo_contiene_alguno` y `descripcion_contiene_alguno`. Si solo matcheaba una de las dos, no se aplica.

**Solución:** Revisar la regla en `nlp_correction_rules.json` y suavizar condiciones, o agregar más keywords.

### Skills sugeridas no encuentran URI (dict argentino expansion)

**Causa:** Labels en español pueden diferir sutilmente entre argentino y ESCO-es. Ej: "manicura combinada" no existe en ESCO, pero "manicura cosmética" sí.

**Solución:** Agregar al diccionario argentino con label ESCO más cercano semánticamente. Si no hay label cercano, la skill queda registrada pero sin URI (aceptar y seguir).

---

## Checklist final de un batch

- [ ] Issues categorizados (ISCO, NLP, skills add, skills remove, otros)
- [ ] Reglas matching creadas con labels ESCO verificados
- [ ] Reglas NLP creadas en orden correcto de prioridad
- [ ] Skills inyectadas con cobertura > 50% (si no, ampliar dict argentino)
- [ ] Skills incorrectas removidas
- [ ] Issues cerrados en Supabase con `solucion_aplicada` explícita
- [ ] Sync ejecutado (`sync_to_supabase.py`)
- [ ] Commits descriptivos por fase (no mega-commit único)
- [ ] Diccionario argentino actualizado si hubo > 20 skills sin URI

---

## Archivos y scripts relevantes

| Archivo | Rol |
|---|---|
| `config/matching_rules_business.json` | Reglas de negocio ISCO (leído por pipeline) |
| `config/nlp_correction_rules.json` | Reglas de corrección NLP post-LLM (integrado en `nlp_postprocessor.py` desde commit `3189eb02` + sigue siendo usado por `reapply_nlp_to_validated.py` para ofertas validadas) |
| `config/sinonimos_skills_argentinos.json` | Diccionario argentino (leído por `skills_implicit_extractor.py`) |
| `scripts/reapply_rules_to_validated.py` | Aplica reglas matching a ofertas validadas |
| `scripts/reapply_nlp_to_validated.py` | Aplica correcciones NLP a ofertas validadas |
| `scripts/inject_skills_from_issues.py` | Inyecta skills sugeridas (busca URIs) |
| `scripts/remove_skills_from_issues.py` | Remueve skills marcadas incorrectas |
| `scripts/import_argentine_skill_labels.py` | Sincroniza dict → `esco_skill_alternative_labels` |
| `scripts/search_esco_skill.py` | CLI para buscar skills ESCO por keywords |

---

## Referencias

- Batch de Cynthia (2026-04-22): 414 issues cerrados, +96 términos al dict
- Commit inicial del pipeline: `a27032ee`
- Bug del matcher (esco_label inexistente descarta regla): `43ae1ed5`
- Expansión dict: `210521ca`
- Integración de nlp_correction_rules en el postprocessor: `3189eb02`

---

## Qué está integrado al pipeline vs qué es helper manual

### Integrado (se ejecuta automáticamente en cada corrida del pipeline)

| Componente | Cuándo corre | Qué afecta |
|---|---|---|
| `config/matching_rules_business.json` | Cada matching en `match_ofertas_v3.py` | ISCO de oferta nueva |
| `config/nlp_correction_rules.json` | Cada NLP postprocess (paso 9) | sector/seniority/área/experiencia de oferta nueva |
| `config/sinonimos_skills_argentinos.json` | Skills extractor durante matching | Skills extraídas |
| `esco_skill_alternative_labels` (244 argentine_mol) | Skills lookup durante matching | Mapeos argentinos |

Editar estos JSONs → inmediatamente efectivo en la próxima oferta procesada.

### Helpers manuales (requieren invocación explícita)

| Script | Cuándo usarlo |
|---|---|
| `reapply_rules_to_validated.py` | Tras agregar regla matching, para retrofit de ofertas YA validadas |
| `reapply_nlp_to_validated.py` | Tras agregar regla NLP correction, idem |
| `inject_skills_from_issues.py` | Tras recibir un batch de feedback humano |
| `remove_skills_from_issues.py` | Tras recibir feedback con skills marcadas incorrectas |
| `import_argentine_skill_labels.py` | Tras editar `sinonimos_skills_argentinos.json`, sincroniza BD |
| `search_esco_skill.py` | Cualquier momento, para investigación manual |

Estos son post-hoc por diseño: operan sobre datos específicos (issues en Supabase, ofertas ya validadas) que no existen en el momento de procesar una oferta nueva.
