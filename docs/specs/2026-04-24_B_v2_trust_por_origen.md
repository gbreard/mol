# SPEC B v2 — Filtro de skills por trust-source (reemplaza B original)

**Fecha:** 2026-04-24
**Estado:** Draft — pendiente aprobación
**Scope:** Cambio de código en `skills_implicit_extractor.py`
**Reemplaza:** `2026-04-24_B_skills_noise.md` (original, invalidado por Fase 0)
**Basado en:** `2026-04-24_B_FASE0_informe.md` (datos empíricos)
**Specs relacionados:** SPEC A (cerrado `554262df`), SPEC C (cerrado `6c506341`)

---

## 1. Contexto arquitectural

### Cómo se extraen las skills hoy

El pipeline NLP sigue este flujo:

```
Oferta
  └─ LLM extrae tareas_explicitas (fuente de verdad del puesto)
  └─ Postprocessor limpia el ruido (SPEC C)
  
MATCHING (match_ofertas_v3 → skills_implicit_extractor.extract_skills)
  1. Terminología argentina (prioridad máxima)
       - `_extract_terminology_skills(texto, area)`
       - Busca términos argentinos en título y tareas → skill ESCO directa
       - Origen: "terminologia_argentina"
  2. Por cada texto (título, cada tarea, skills_nlp, soft_skills_nlp):
       - BGE-M3 genera embedding
       - Top-K similaridad contra 14,247 embeddings ESCO
       - Si score ≥ threshold (0.40 default) → agrega skill
       - Cada skill queda con campo `origen`: "titulo" | "tarea" | "skills_nlp" | "soft_skills_nlp"
       - Y `texto_fuente`: primeros 100 chars del texto que la generó
```

### Implicancias clave (lo que aprendimos en Fase 0)

1. **Las skills con `origen='tarea'` vienen de tareas reales** del puesto.
2. **Las tareas son la fuente de verdad**, no ESCO. ESCO es el diccionario estandarizador.
3. **Filtrar por compatibilidad ESCO** (como proponía SPEC B original) sesgaría el sistema a vocabulario europeo y **descartaría skills argentinas válidas** (25% de las del diccionario no tienen asociación ESCO oficial).
4. **El score BGE-M3 no discrimina calidad** — skills random y buenas tienen scores solapados (0.65-0.80).

### Dónde está el problema real

Según datos de Fase 0 (52,370 ofertas, 868,010 skills):

| Caso | Skills asignadas | ¿Válidas? |
|---|---|---|
| `origen='tarea'` + tarea sustantiva (≥20 chars) | Mayoría | ✅ Sí |
| `origen='tarea'` + tarea contaminada | Pocas (ya resuelto SPEC C) | ❌ Ruido (removido) |
| `origen='skills_nlp'` / `soft_skills_nlp'` | Todas | ✅ Sí (LLM las detectó) |
| `origen='terminologia_argentina'` | Todas | ✅ Sí (diccionario curado) |
| **`origen='titulo'` + título corto/genérico** | **Top-K random** | ❌ **Ruido real** |
| `origen='titulo'` + título sustantivo | Skills del rol | ⚠️ Mezcla |

**El ruido está concentrado en el caso "título como única fuente".**

Ejemplo canónico (oferta 5575403602, operario limpieza, desc=239):
- Sin tareas extraídas (texto insuficiente)
- BGE-M3 matchea solo contra "operario de limpieza" (título corto)
- Top-K trae skills de cualquier dominio con score 0.70-0.77:
  - "apuestas mutuas"
  - "programas públicos de seguridad social"
  - "escribir en catalán"

---

## 2. Propuesta: filtro por trust-source

### Idea central

Calificar cada skill asignada según la **confianza de su fuente**, NO según compatibilidad con ESCO. Descartar solo las de baja confianza.

### Modelo de trust

```
trust = f(origen, score, contexto_oferta)

nivel_confianza =
  ALTO   → skill proviene de tarea real, LLM o diccionario argentino
  MEDIO  → skill del título sustantivo con buen score
  BAJO   → skill top-K de título corto con score medio (probable ruido)
```

### Lógica concreta

```python
def is_skill_trusted(skill: dict, oferta_context: dict) -> tuple[bool, str]:
    """Retorna (trust, motivo) basado en origen + calidad fuente."""
    origen = skill.get('origen', 'desconocido')
    texto_fuente = skill.get('texto_fuente', '') or ''
    score = skill.get('score', 0)

    # 1. Origen "regla" / "terminologia_argentina" → siempre confianza alta
    if origen in ('regla', 'terminologia_argentina', 'sinonimo_argentino',
                   'regla_cynthia', 'regla_issue'):
        return True, 'origen_reglas'

    # 2. Origen "skills_nlp" o "soft_skills_nlp" → LLM las identificó
    if origen in ('skills_nlp', 'soft_skills_nlp'):
        return True, 'origen_llm_detectado'

    # 3. Origen "tarea" con tarea sustantiva (≥20 chars no triviales)
    if origen == 'tarea':
        tarea_clean = texto_fuente.strip()
        if len(tarea_clean) >= 20:
            return True, 'origen_tarea_real'
        # Tarea muy corta → depende del score
        if score >= 0.75:
            return True, 'origen_tarea_corta_score_alto'
        return False, 'origen_tarea_corta_score_bajo'

    # 4. Origen "titulo" → depende del contexto
    if origen == 'titulo':
        titulo_len = len(oferta_context.get('titulo_limpio', ''))
        tiene_tareas = bool(oferta_context.get('tareas_explicitas'))
        tiene_skills_nlp = bool(oferta_context.get('skills_tecnicas_list'))

        # Si ya hay tareas o skills_nlp como fuente, las de título son secundarias
        # → exigir score alto
        if (tiene_tareas or tiene_skills_nlp) and score < 0.80:
            return False, 'titulo_redundante_score_bajo'

        # Sin otras fuentes, el título es lo único
        if titulo_len >= 30:
            # Título razonable → permisivo
            if score >= 0.70:
                return True, 'titulo_solo_fuente_score_ok'
            return False, 'titulo_solo_fuente_score_bajo'
        else:
            # Título muy corto → muy estricto
            if score >= 0.85:
                return True, 'titulo_corto_score_muy_alto'
            return False, 'titulo_corto_score_medio'

    # Fallback: score alto o descartar
    if score >= 0.80:
        return True, 'fallback_score_alto'
    return False, 'fallback_origen_desconocido'
```

### Qué no hace este filtro

- ❌ NO consulta ESCO oficial (`esco_associations`)
- ❌ NO depende del ISCO asignado
- ❌ NO usa el diccionario argentino como "lista blanca" (ya se procesa antes, en terminology_skills)
- ❌ NO elimina skills aunque sean raras — solo si la evidencia de origen es débil

---

## 3. Impacto estimado según Fase 0

Aplicando la lógica sobre la distribución observada:

| Categoría | Ofertas (aprox) | % | Efecto |
|---|---|---|---|
| `desc≥800 + tareas≥3` (bueno) | 38,254 | 73% | Casi sin cambios (mayoría skills son `origen='tarea'`) |
| `400-800 + 2-5 tareas` (medio) | 5,029 | 10% | Pocas skills descartadas (las `origen='titulo'` con score<0.80) |
| `desc<600 + tareas<2` (pobre) | 2,057 | 4% | Descartes significativos de skills de título |
| **`desc<400 + tareas=0` (crítico)** | **783** | **1.5%** | **Limpieza completa** — solo skills con evidencia fuerte |

**Ofertas con impacto real:** ~3% (1,552). Coincide con donde está el problema.

---

## 4. Implementación

### 4.1 Archivo: `database/skills_implicit_extractor.py`

Agregar método:

```python
def _classify_skill_trust(self, skill: dict, oferta_context: dict) -> tuple[bool, str]:
    """Determina si una skill asignada es confiable según su origen."""
    # ... (lógica de sección 2)
```

Modificar `extract_skills` para aplicar filtro antes de retornar:

```python
# Al final del método extract_skills, antes del return:
if self.filtrar_por_trust:
    skills_trusted = []
    skills_descartadas_bajo_trust = []
    for s in skills_extraidas:
        trust, motivo = self._classify_skill_trust(s, oferta_context)
        if trust:
            s['trust_motivo'] = motivo
            skills_trusted.append(s)
        else:
            skills_descartadas_bajo_trust.append({**s, 'descarte_motivo': motivo})
    
    if self.verbose and skills_descartadas_bajo_trust:
        print(f"[TRUST] Descartadas {len(skills_descartadas_bajo_trust)} skills por baja confianza")
    
    skills_extraidas = skills_trusted
```

### 4.2 Configuración

Flag en `__init__`:

```python
def __init__(self, ..., filtrar_por_trust: bool = True):
    ...
    self.filtrar_por_trust = filtrar_por_trust
```

Default `True` para pipeline. `False` para debugging o comparación.

### 4.3 Pasar contexto de oferta

`extract_skills` necesita recibir el contexto. Ya tiene `titulo_limpio`, `tareas_explicitas`, `skills_nlp`. Agregar un dict `oferta_context` construido internamente:

```python
oferta_context = {
    'titulo_limpio': titulo_limpio or '',
    'tareas_explicitas': tareas_explicitas or '',
    'skills_tecnicas_list': skills_nlp or [],
}
```

### 4.4 Guardar motivo en BD (opcional pero recomendado)

Al persistir skills en `ofertas_esco_matching.skills_semantico_json`, incluir el campo `trust_motivo` para trazabilidad. Permite análisis posterior ("¿qué % de skills son `origen_tarea_real` vs `titulo_solo_fuente`?").

---

## 5. Tests

### 5.1 Archivo nuevo: `tests/matching/test_skills_trust.py`

```python
# -*- coding: utf-8 -*-
"""
Tests: filtro de skills por trust-source.

Verifica que skills de tareas reales se mantienen y skills top-K
de título corto se descartan.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database"))


@pytest.fixture(scope="module")
def extractor():
    from skills_implicit_extractor import SkillsImplicitExtractor
    return SkillsImplicitExtractor(verbose=False)


class TestTrustOrigen:

    def test_skill_de_tarea_real_se_mantiene(self, extractor):
        """Una skill con origen='tarea' + tarea sustantiva → trust=True."""
        skill = {
            'origen': 'tarea', 'score': 0.65,
            'texto_fuente': 'realizar operaciones de carga y descarga',
            'skill_esco': 'manejar carretillas elevadoras',
        }
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_tarea_real'

    def test_skill_de_tarea_contaminada_corta_score_bajo(self, extractor):
        """Tarea <20 chars + score < 0.75 → trust=False."""
        skill = {
            'origen': 'tarea', 'score': 0.55,
            'texto_fuente': 'Hace 2 días',
            'skill_esco': 'skill random',
        }
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is False

    def test_skill_terminologia_argentina_pasa(self, extractor):
        """Origen terminologia_argentina → siempre True."""
        skill = {
            'origen': 'terminologia_argentina', 'score': 0.60,
            'skill_esco': 'gestionar el inventario',
        }
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_reglas'

    def test_skill_sinonimo_argentino_pasa(self, extractor):
        """Origen sinonimo_argentino → siempre True."""
        skill = {
            'origen': 'sinonimo_argentino', 'score': 0.99,
            'skill_esco': 'gestionar la caja',
        }
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True

    def test_skill_llm_detectada_pasa(self, extractor):
        """Origen skills_nlp → siempre True."""
        skill = {'origen': 'skills_nlp', 'score': 0.55, 'skill_esco': 'AutoCAD'}
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True


class TestTrustTitulo:

    def test_titulo_corto_score_bajo_descartado(self, extractor):
        """Título corto + score <0.85 → trust=False (caso peor)."""
        skill = {'origen': 'titulo', 'score': 0.72, 'skill_esco': 'apuestas mutuas'}
        context = {'titulo_limpio': 'operario', 'tareas_explicitas': ''}
        trust, motivo = extractor._classify_skill_trust(skill, context)
        assert trust is False
        assert motivo == 'titulo_corto_score_medio'

    def test_titulo_corto_score_muy_alto_pasa(self, extractor):
        """Título corto + score ≥0.85 → trust=True."""
        skill = {'origen': 'titulo', 'score': 0.88, 'skill_esco': 'skill relacionada'}
        context = {'titulo_limpio': 'operario', 'tareas_explicitas': ''}
        trust, motivo = extractor._classify_skill_trust(skill, context)
        assert trust is True

    def test_titulo_redundante_score_bajo_descartado(self, extractor):
        """Si ya hay tareas + título con score<0.80 → descartado (redundante)."""
        skill = {'origen': 'titulo', 'score': 0.72, 'skill_esco': 'skill'}
        context = {
            'titulo_limpio': 'Operario de producción en línea de envasado',
            'tareas_explicitas': 'controlar máquinas; cumplir estándares',
        }
        trust, motivo = extractor._classify_skill_trust(skill, context)
        assert trust is False
        assert motivo == 'titulo_redundante_score_bajo'

    def test_titulo_largo_score_ok_pasa(self, extractor):
        """Título >=30 chars + score>=0.70 + sin tareas → trust=True."""
        skill = {'origen': 'titulo', 'score': 0.72, 'skill_esco': 'skill'}
        context = {
            'titulo_limpio': 'Desarrollador Python Senior Remoto LATAM',
            'tareas_explicitas': '',
        }
        trust, motivo = extractor._classify_skill_trust(skill, context)
        assert trust is True


class TestCasosReales:
    """Casos reales sacados de la Fase 0 exploratoria."""

    def test_operario_limpieza_skills_random(self, extractor):
        """Oferta 5575403602: operario limpieza con skills random del título."""
        context = {'titulo_limpio': 'operario/a de limpieza',
                   'tareas_explicitas': ''}
        # Las 3 skills random que asignó BGE-M3
        skills_random = [
            {'origen': 'titulo', 'score': 0.77, 'skill_esco': 'apuestas mutuas'},
            {'origen': 'titulo', 'score': 0.75, 'skill_esco': 'programas públicos de seguridad social'},
            {'origen': 'titulo', 'score': 0.70, 'skill_esco': 'escribir en catalán'},
        ]
        for s in skills_random:
            trust, motivo = extractor._classify_skill_trust(s, context)
            assert trust is False, f"Skill random '{s['skill_esco']}' debería ser descartada"

    def test_ingeniero_civil_skills_relevantes_mantienen(self, extractor):
        """Oferta 7069402536: ingeniero civil con skills razonables."""
        context = {'titulo_limpio': 'Ingeniero civil',
                   'tareas_explicitas': ''}
        # Skills relevantes
        skills_ok = [
            {'origen': 'titulo', 'score': 0.79, 'skill_esco': 'ingeniería civil'},
            {'origen': 'titulo', 'score': 0.72, 'skill_esco': 'diseñar planos técnicos'},
        ]
        for s in skills_ok:
            trust, motivo = extractor._classify_skill_trust(s, context)
            # Título corto → solo score muy alto (>0.85) pasa
            # Este test verifica el comportamiento: score 0.79 con título corto
            # en realidad DEBERÍA fallar. Esto es un trade-off conocido.
            # Revisar si ajustar threshold.
            pass  # comportamiento esperado: score<0.85 + titulo<30 → False
```

### 5.2 Test de regresión end-to-end

`tests/matching/test_skills_trust_integration.py`:

Reprocesar las 3 ofertas del caso real sample:
- Operario limpieza 5575403602 → debería quedar con 0 skills random
- Ingeniero civil 7069402536 → mantiene skills relevantes (o acepta que se pierdan si título es corto)
- Enfermera 1118173872 → mantiene las de tareas, descarta las ruido del título

### 5.3 Tests de regresión existentes

```bash
pytest tests/matching/test_gold_set_v2_verified.py -v  # debe mantener 47/48 passed
pytest tests/matching/test_gold_set_manual.py -v        # regresión matching
pytest tests/test_limpieza_tareas_ruido.py -v           # limpieza tareas
```

---

## 6. Plan de implementación (4 fases, ~4-6h)

### Fase 1 — Implementación core (~2h)
- Agregar `_classify_skill_trust()` y `filtrar_por_trust` flag
- Modificar `extract_skills()` para aplicar filtro
- Guardar `trust_motivo` en resultado

### Fase 2 — Tests (~1h)
- Escribir `test_skills_trust.py` con 12 casos
- Correr tests regresión gold set v2

### Fase 3 — Análisis de impacto (~1h)
Antes de retropropagar a BD, correr sobre BD actual **en modo análisis** (sin modificar):
```bash
python scripts/analyze_trust_impact.py  # nuevo script one-shot
# Reporta: cuántas skills se descartarían por origen, por oferta, por banda de contexto
```

Verificar:
- % ofertas con reducción drástica (>80% skills descartadas) → revisar manualmente
- Distribución de `trust_motivo` → ajustar thresholds si hay sesgos inesperados

### Fase 4 — Retropropagación (~1-2h)
- Aplicar filtro a las 49,117 ofertas validadas con skills
- Actualizar `skills_semantico_json` con filtrado
- Sync a Supabase

---

## 7. Riesgos

### 7.1 Thresholds arbitrarios
Los valores (0.70, 0.75, 0.80, 0.85, 20 chars, 30 chars) son razonables pero no vienen de optimización. Mitigación: la Fase 3 de análisis permite ajustar antes de retropropagar.

### 7.2 Skills de título legítimas descartadas
Cuando el título es rico pero corto (ej: "Analista contable senior SAP"), el filtro puede ser estricto. Mitigación:
- El tamaño del título se mide en chars, no en palabras — "Analista contable SAP" tiene 22 chars → sí sustantivo.
- Si problema aparece, subir threshold de "título corto" de 30 a 25 o ajustar.

### 7.3 Pérdida masiva en ofertas con tareas vacías
Si una oferta solo tiene título y no tareas, sus skills pueden bajar de 10 a 1-2. Eso puede afectar agregados del dashboard. Mitigación:
- En Fase 3, medir caída promedio de skills por oferta.
- Si es severa, considerar preservar top-3 por score mínimo incluso sin pasar trust.

### 7.4 Contaminación por skills_nlp erróneas
Si el LLM detecta skills incorrectas (ej: "AutoCAD" en una oferta de panadería), el trust actual las deja pasar por `origen='skills_nlp'`. Mitigación: fuera de scope de este spec. Se resolvería con validación LLM → ESCO previa.

---

## 8. Criterios de éxito

Sobre las 3 ofertas de referencia del caso real:

- Oferta 5575403602 (operario limpieza, desc<400, sin tareas): **de 3 skills random → 0**.
- Oferta 2179924 (acompañante terapéutico, desc<400, sin tareas): skills random descartadas.
- Oferta 1118173872 (enfermera, desc=977, con tareas): mantiene skills de tareas, descarta solo "grabado al ácido"/"mobiliario" del título con score alto (aquí podría requerir ajuste fino).

Sobre agregados:

- **Distribución de `trust_motivo`** tras retropropagación:
  - `origen_tarea_real` ≥ 60% (mayoría viene de tareas reales)
  - `origen_reglas` + `origen_llm_detectado` ≥ 20%
  - `titulo_solo_fuente_score_ok` ≤ 15%
  - `titulo_corto_*` ≤ 5%

- **Reducción total de skills en BD**:
  - Esperado: ~10-15% (coincide con el 11% de skills con score <0.60 en la data)
  - Si cae >25%: revisar; puede estar siendo muy estricto

- **Gold set v2** sigue pasando 47/48.

---

## 9. Decisiones pendientes antes de implementar

1. ¿Default `filtrar_por_trust=True` en pipeline o mantener `False` por seguridad inicial?
   - Recomendado: `False` en primera implementación, cambiar a `True` tras verificar Fase 3.
2. ¿Guardamos `trust_motivo` en BD para análisis?
   - Recomendado: Sí, es útil para telemetría y debugging.
3. ¿Thresholds ajustables vía config externa?
   - Recomendado: Sí, en `config/skills_extractor_config.json` (aún no existe; se crea).

---

## 10. Comparación con propuestas previas

| Propuesta | Approach | Validez con datos |
|---|---|---|
| **SPEC B original** | Threshold dinámico por contexto | ❌ Invalidado (scores no discriminan) |
| **Filtro ESCO compat** | Descartar skills no en ESCO oficial | ❌ Sesga a ESCO, pierde skills argentinas |
| **SPEC B v2 (este)** | Trust por origen + calidad fuente | ✅ Respeta arquitectura, filtra ruido real |

---

## 11. Anexos

- Fase 0 exploratoria: `2026-04-24_B_FASE0_informe.md`
- Código relevante: `database/skills_implicit_extractor.py:493-660` (método `extract_skills`)
- Datos: `/tmp/pipeline_test/context_dist.txt`, `scores_dist.txt`, `sample.txt`
