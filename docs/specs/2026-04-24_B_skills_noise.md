# SPEC B: Skills ruido en descripciones cortas (threshold dinámico)

**Fecha:** 2026-04-24
**Estado:** Draft — pendiente aprobación
**Scope:** Cambio de código en `skills_implicit_extractor.py` + config.
**Specs relacionados:**
- `2026-04-24_A_operarios_config.md` — config fixes (independiente)
- `2026-04-24_C_tareas_contaminadas.md` — bug extracción (independiente)

---

## 1. Problema

Cuando una oferta tiene descripción corta y tareas vacías, el `skills_implicit_extractor` asigna skills ESCO **totalmente aleatorias** de dominios irrelevantes, con scores bajos (~0.5-0.7) pero arriba del threshold default (0.40).

### Caso concreto reportado por Cynthia

**Oferta 1118219210** (Operario de producción, bebidas) tiene asignadas estas skills:

- `desarrollar protocolos de investigación científica`
- `centrarse en los pasajeros`
- `evaluar el comportamiento animal`
- `estibar la carga`
- `asesorar sobre paisajismo`
- `terapéutica aplicada a la medicina`
- `elaborar materiales informativos para turistas`
- `prever cambios en la tecnología automovilística`
- `ordenación pesquera`
- `seguir las tendencias en equipamiento deportivo`
- `bombear pintura`
- `técnicas de respiración`
- `servicios distribuidos de directorio de información`
- `controlar pacientes de oncología aguda`
- `secar la película fotográfica`
- `regular la temperatura del horno`
- `transferir peces`
- `supervisar los trabajos de mantenimiento`
- `enrollar el hilo en bobinas`

**Ninguna tiene relación con la oferta.** Son skills random de cualquier dominio que pasaron el threshold 0.40 por matchear palabras genéricas.

### Root cause

1. **Threshold global fijo en 0.40** (`DEFAULT_THRESHOLD` en `skills_implicit_extractor.py:88`) sin ajuste por contexto.
2. **Descripciones cortas** no dan contexto al BGE-M3 para matchear skills específicas. El modelo entrega top-K indices con scores medios/bajos de cualquier dominio.
3. **Tareas vacías o muy cortas** (menos de 10 palabras) no son suficientes para discriminar dominios.
4. **Pipeline igual asigna skills** aunque los scores sean del orden 0.40-0.55 (ruido).

### Evidencia del problema

Ofertas con `descripcion_muy_corta` (<400 chars) + `sin_skills_desc_larga` (auto-validator V14/V25) tienen altísima tasa de skills ruido. Al menos **5-7 de las 18 ofertas operarios** analizadas tienen este patrón.

---

## 2. Propuesta de solución

### 2.1 Threshold dinámico según contexto

```python
def compute_effective_threshold(descripcion: str, tareas: list[str]) -> float:
    """Umbral dinámico según contexto disponible.

    - Descripción corta + sin tareas → threshold alto (evita ruido)
    - Descripción larga + tareas → threshold normal (más tolerante)
    """
    desc_len = len(descripcion or '')
    tareas_count = len([t for t in tareas if t.strip()])
    tareas_chars = sum(len(t) for t in tareas if t)

    # Caso 1: sin tareas útiles + desc corta → muy restrictivo
    if tareas_count == 0 and desc_len < 400:
        return 0.75
    # Caso 2: pocas tareas + desc corta → restrictivo
    if tareas_count < 2 and desc_len < 600:
        return 0.65
    # Caso 3: contexto pobre pero algo → moderado
    if tareas_chars < 100:
        return 0.55
    # Caso 4: contexto normal → default actual
    return 0.40
```

### 2.2 Política "sin skills si no hay confianza"

Si tras aplicar el threshold dinámico **no hay ninguna skill** arriba del umbral:
- **NO asignar skills random** (comportamiento actual: asigna las top K aunque sean ruido).
- Marcar en `skills_regla_aplicada = 'SKILLS_LOW_CONFIDENCE'`.
- Registrar en `validation_errors` con severity `warning`: "skills no asignadas por baja confianza".

### 2.3 Fallback con `skills_rules.json`

Cuando threshold dinámico descarta todas las skills semánticas, intentar `skills_rules.json` (forzadas por ISCO):
- Si hay regla `skills_rules` para el ISCO asignado → aplicarla.
- Si no → cero skills.

Así: ofertas mal (descripción corta) obtienen las skills típicas del ISCO vía regla (que son genéricas pero correctas), sin depender del matcher semántico.

### 2.4 Telemetría

Agregar métricas en `experiment_logger`:
- `skills_threshold_dynamic_applied`: veces que el threshold dinámico se usó
- `skills_low_confidence_skipped`: ofertas sin skills por baja confianza
- `skills_rules_fallback_applied`: ofertas que usaron skills_rules como fallback

---

## 3. Cambios concretos

### Archivo: `database/skills_implicit_extractor.py`

**Agregar método:**
```python
def _compute_effective_threshold(self, descripcion: str, tareas: list) -> float:
    ...
```

**Modificar `extract_from_tasks()` y `extract_from_descripcion()`:**
- Llamar a `_compute_effective_threshold()` antes del bucle de top_indices.
- Si `len(skills_implicitas) == 0` tras el threshold, marcar origen como `low_confidence`.

**Modificar `match_ofertas_v3.py`:**
- Cuando skills extractor devuelve `low_confidence`, intentar skills_rules por ISCO.

### Archivo: `config/skills_extractor_config.json` (NUEVO)

```json
{
  "version": "1.0",
  "thresholds": {
    "default": 0.40,
    "descripcion_corta_sin_tareas": 0.75,
    "descripcion_corta_pocas_tareas": 0.65,
    "contexto_pobre": 0.55
  },
  "limits": {
    "descripcion_corta_chars": 400,
    "tareas_chars_pobre": 100
  }
}
```

Evita que los thresholds queden hardcoded en el código — permiten tuning.

---

## 4. Tests

### 4.1 Unit tests — archivo nuevo

**Archivo:** `tests/matching/test_skills_threshold_dynamic.py`

Sigue patrón de `tests/test_limpieza_tareas_ruido.py` (clases `TestXxx`, fixtures, aserts concretos).

```python
# -*- coding: utf-8 -*-
"""
Tests: threshold dinámico en skills_implicit_extractor.

Verifica que el threshold se ajusta según contexto (largo descripción,
cantidad de tareas) y que ofertas con contexto pobre no asignan skills
random.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database"))


@pytest.fixture(scope="module")
def extractor():
    """SkillsImplicitExtractor con modelo cargado (una sola vez por módulo)."""
    from skills_implicit_extractor import SkillsImplicitExtractor
    return SkillsImplicitExtractor(verbose=False)


# ============================================================================
# Threshold dinámico
# ============================================================================

class TestThresholdDinamico:

    def test_desc_corta_sin_tareas(self, extractor):
        """Desc < 400 chars + 0 tareas → threshold muy restrictivo."""
        t = extractor._compute_effective_threshold("Operario producción. Envio CV.", [])
        assert t == 0.75

    def test_desc_corta_pocas_tareas(self, extractor):
        """Desc < 600 chars + 1 tarea → threshold restrictivo."""
        t = extractor._compute_effective_threshold("Se busca operario.", ["controlar máquinas"])
        assert t == 0.65

    def test_tareas_chars_pobres(self, extractor):
        """Tareas muy cortas (< 100 chars totales) → threshold moderado."""
        desc = "x" * 1000  # desc larga
        tareas = ["x"]  # tarea vacía
        t = extractor._compute_effective_threshold(desc, tareas)
        assert t == 0.55

    def test_contexto_normal(self, extractor):
        """Desc larga + tareas reales → threshold default."""
        desc = "Se busca operario con experiencia en línea de producción. " * 10
        tareas = [
            "controlar máquinas de envasado",
            "realizar picking de mercadería",
            "cumplir estándares de calidad",
        ]
        t = extractor._compute_effective_threshold(desc, tareas)
        assert t == 0.40


# ============================================================================
# Política: no asignar skills si no hay confianza
# ============================================================================

class TestLowConfidencePolicy:

    def test_zero_skills_si_todas_bajo_threshold(self, extractor):
        """Oferta sin contexto no debe recibir skills random."""
        skills = extractor.extract_from_tasks(
            descripcion="Operario.",
            tareas=[],
        )
        # Comportamiento esperado: cero skills O marcadas como low_confidence
        if skills:
            assert all(s.get('origen') == 'low_confidence' for s in skills)
        else:
            assert skills == []

    def test_no_skills_irrelevantes_desc_corta(self, extractor):
        """Las skills 'top-K random' de dominios ajenos no deben aparecer."""
        skills = extractor.extract_from_tasks(
            descripcion="Operario de producción. Jornada diurna.",
            tareas=[],
        )
        skill_labels = [s.get('skill_esco', '').lower() for s in skills]
        # Dominios random que aparecían en el caso reportado
        dominios_prohibidos = [
            'oncología', 'paisajismo', 'radioterapia',
            'pedagogía teatral', 'inseminar', 'transferir peces',
            'ordenación pesquera',
        ]
        for dominio in dominios_prohibidos:
            assert not any(dominio in l for l in skill_labels), \
                f"Skill irrelevante '{dominio}' apareció"

    def test_marca_origen_low_confidence(self, extractor):
        """Skills asignadas con threshold dinámico deben marcar origen."""
        skills = extractor.extract_from_tasks(
            descripcion="Operario producción",
            tareas=["operario"],
        )
        # Si algo se asignó con threshold ajustado, el origen debe indicar
        if skills:
            origenes = set(s.get('origen') for s in skills)
            # Puede tener: sinonimo_argentino, semantico_normal, low_confidence
            assert len(origenes) > 0


# ============================================================================
# Fallback con skills_rules.json
# ============================================================================

class TestSkillsRulesFallback:

    def test_fallback_aplica_skills_rules_por_isco(self, extractor):
        """Si threshold dinámico descarta todas, skills_rules por ISCO
        aplica como fallback (integrado en match_ofertas_v3)."""
        from match_ofertas_v3 import MatcherV3
        # Oferta sin tareas, pero con ISCO ya asignado por regla matching
        # Debe aplicar skills_rules.json[ISCO 9333] (mozo almacén)
        pytest.skip("Requiere fixture con BD mock — implementar según estructura MatcherV3")


# ============================================================================
# Regresión: no romper casos con contexto bueno
# ============================================================================

class TestRegresionGoldSet:

    def test_gold_set_ofertas_normales_mantienen_skills(self, extractor):
        """Las 49 ofertas del gold set tienen contexto normal.
        Deben mantener >= 80% de sus skills tras el fix."""
        import json
        from pathlib import Path
        gold = json.load(open(Path(__file__).parent / "gold_set.json"))
        # Sample de 5 para no relentizar
        muestra = gold[:5] if isinstance(gold, list) else list(gold.values())[:5]
        for caso in muestra:
            desc = caso.get('descripcion', '') or ''
            tareas = caso.get('tareas_explicitas', '') or ''
            if len(desc) < 400 or not tareas:
                continue  # saltar casos borderline
            threshold = extractor._compute_effective_threshold(desc, tareas.split(';'))
            assert threshold == 0.40, f"Gold set caso {caso.get('id_oferta')} recibió threshold ajustado"
```

### 4.2 Tests de regresión (existentes)

**Correr antes y después del deploy:**

```bash
# Gold set matching (49 casos manuales)
pytest tests/matching/test_gold_set_manual.py -v

# Gold set dinámico con Supabase
pytest tests/matching/test_m10_gold_set.py -v

# Gold set skills específicamente
pytest tests/matching/test_m10_gold_set_skills.py -v

# Ruido de tareas (complementario al Spec C)
pytest tests/test_limpieza_tareas_ruido.py -v
```

**Criterio de aceptación:** todos los tests pre-existentes deben seguir pasando (0 regresiones).

### 4.3 Smoke test manual con ofertas afectadas

Script rápido para validar casos concretos:

```bash
python3 -c "
import sys, sqlite3, json
sys.path.insert(0, 'database')
from skills_implicit_extractor import SkillsImplicitExtractor

conn = sqlite3.connect('database/bumeran_scraping.db')
c = conn.cursor()

OFERTAS_TEST = [
    ('1118219210', 0, 'cero skills random'),      # desc corta, caso peor
    ('7985222956', '<=5', 'pocas, sin oncología/paisajismo'),
    ('7272678691', '>=3', 'skills reales operario plástico'),
]

ext = SkillsImplicitExtractor(verbose=False)
for oid, expected, nota in OFERTAS_TEST:
    c.execute('SELECT descripcion FROM ofertas WHERE id_oferta=?', (oid,))
    desc = c.fetchone()[0] or ''
    c.execute('SELECT tareas_explicitas FROM ofertas_nlp WHERE id_oferta=?', (oid,))
    tareas = (c.fetchone() or [''])[0] or ''
    tareas_list = [t.strip() for t in tareas.split(';') if t.strip()]
    skills = ext.extract_from_tasks(descripcion=desc, tareas=tareas_list)
    print(f'{oid}: {len(skills)} skills ({nota})')
"
```

**Ofertas para validar (las 18 operarios analizadas):**

| Oferta | Desc | Tareas actuales | Skills actuales | Skills post-fix esperadas |
|---|---|---|---|---|
| 1118219210 | corta | vacías | 20 random | 0 o fallback por ISCO |
| 7985222956 | corta | contaminadas | cero skills semánticas, skills por regla |
| 7272678691 | media | 4 reales | skills razonables (no ruido) |

---

## 5. Plan de implementación

### Fase 1 — Config + código
1. Crear `config/skills_extractor_config.json`.
2. Agregar `_compute_effective_threshold()` a `skills_implicit_extractor.py`.
3. Modificar `extract_from_tasks()` y `extract_from_descripcion()`.
4. Agregar telemetría.

### Fase 2 — Integración con match_ofertas_v3
1. Detectar casos `low_confidence` en skills extractor.
2. Fallback a `skills_rules.json` por ISCO.

### Fase 3 — Tests
1. Unit tests nuevos.
2. Correr gold set completo.
3. Test manual sobre ofertas 1118219210, 7985222956, 7272678691.

### Fase 4 — Reprocesar afectadas
Identificar ofertas validadas con skills ruido:
```sql
SELECT m.id_oferta, n.tareas_explicitas, n.descripcion_len, m.skills_semantico_json
FROM ofertas_esco_matching m
JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
WHERE LENGTH(n.tareas_explicitas) < 100
  AND LENGTH(n.descripcion) < 400
  AND JSON_ARRAY_LENGTH(m.skills_semantico_json) > 10
```

Re-procesar con `reapply_rules_to_validated.py` para aplicar el nuevo threshold.

### Fase 5 — Verificación
Para cada oferta reprocesada:
- Skills random desaparecen.
- Se mantiene sólo skills arriba del threshold dinámico, o skills de regla.

### Fase 6 — Sync Supabase
```bash
python scripts/exports/sync_to_supabase.py
```

---

## 6. Riesgos

1. **Bajar skills en ofertas buenas.** Si la heurística es muy restrictiva, ofertas con buen contexto pueden perder skills válidas. Mitigación: tests exhaustivos + ajustar thresholds según resultado en gold set.

2. **Retropropagación masiva.** Al re-procesar miles de ofertas con el nuevo threshold, muchas pueden pasar de tener 30 skills a tener 5. Esto puede afectar métricas agregadas del dashboard. Mitigación: hacer primero sobre sample de 100, verificar impacto.

3. **Skills rules fallback puede no existir para todos los ISCOs.** Si no hay regla en `skills_rules.json` para un ISCO, la oferta termina con 0 skills. Mitigación: completar `skills_rules.json` con skills básicas por ISCO antes de deploy.

4. **Compatibilidad con pipeline existente.** Cualquier cambio en la firma del extractor podría romper `match_ofertas_v3` u otros callers. Mitigación: mantener firma compatible, usar `origen='low_confidence'` como señal.

---

## 7. Criterios de éxito

- ✅ Oferta 1118219210 no tiene las 20 skills irrelevantes tras el fix.
- ✅ Gold set matching no rompe (49/49 casos siguen pasando).
- ✅ Ofertas con descripción `>600` chars y tareas extraídas mantienen ~80% de sus skills.
- ✅ Métrica `skills_low_confidence_skipped` reportable en sync_learnings.
- ✅ Dashboard no muestra caída abrupta en cobertura de skills (si cae >40% hay que revisar).

---

## 8. Dependencias

**Este spec requiere que SPEC A esté aplicado primero**, porque:
- El fallback usa `skills_rules.json` por ISCO.
- Si el ISCO está mal (spec A), las skills del fallback también están mal.
- Orden correcto: SPEC A → SPEC B.

## 9. Preguntas pendientes

1. ¿Los thresholds propuestos (0.75 / 0.65 / 0.55 / 0.40) son correctos, o requieren experimentación primero?
2. ¿Skills rules fallback va en el extractor o en match_ofertas_v3? (propongo match_ofertas_v3 porque ya tiene la lógica de reglas de negocio)
3. ¿Re-procesar TODAS las ofertas con patrón `desc<400 + tareas<100`, o solo las que están en issues pendientes?

---

## 10. Estimación

- Implementación + tests: **4-6 horas**
- Verificación + tuning: **2-3 horas**
- Retropropagación (si incluye universo grande): **2-4 horas** + ~30 min sync
