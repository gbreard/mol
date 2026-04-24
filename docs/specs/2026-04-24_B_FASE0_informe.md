# SPEC B — Fase 0 Exploratoria: Informe de findings

**Fecha:** 2026-04-24
**Autor:** Claude (análisis empírico sobre BD local, snapshot 2026-04-24 14:56)
**Estado:** Investigación completada — **reformula la propuesta original del Spec B**
**Conclusión principal:** La hipótesis de "threshold dinámico por contexto" del Spec B original **NO se sostiene con los datos**. Propuesta alternativa al final.

---

## 1. Objetivo de la exploración

Validar empíricamente las 4 preguntas clave antes de implementar Spec B:

1. ¿Qué porcentaje de ofertas cae en bandas de contexto "pobre"?
2. ¿Cómo se distribuyen los scores BGE-M3 en skills ya asignadas?
3. ¿Las skills ruidosas tienen scores más bajos que las buenas? (hipótesis central del spec)
4. ¿Qué cobertura tiene `skills_rules.json` para actuar como fallback?

---

## 2. Datos crudos

### 2.1 Distribución de contexto (52,370 ofertas validadas)

| Banda | Ofertas | % |
|---|---|---|
| Crítico (desc<400 + tareas=0) | 783 | 1.5% |
| Pobre (desc<400 + 1-2 tareas) | 769 | 1.5% |
| Corto-pobre (desc<600 + tareas<2) | 2,057 | 3.9% |
| Medio (400-800 + 2-5 tareas) | 5,029 | 9.6% |
| **Bueno (desc≥800 + ≥3 tareas)** | **38,254** | **73.0%** |

**Percentiles:**
- DESC: p10=523, p50=1337, p90=3636 (bien distribuida)
- TAREAS count: p10=2, p50=5, p90=10
- TAREAS chars: p10=65, p50=271, p90=615

**Conclusión 2.1:** solo **3% (1,552 ofertas)** caen en las bandas "crítica/pobre". El 73% tiene contexto bueno. **El problema inicial (oferta 1118219210 con 20 skills random) es más excepcional que representativo**.

### 2.2 Distribución de scores BGE-M3 (868,010 skills asignadas)

```
0.40:  13188 ( 1.5%) #
0.45:  29996 ( 3.5%) ###
0.50:  25630 ( 3.0%) ##
0.55:  27235 ( 3.1%) ###
0.60:  69819 ( 8.0%) ########
0.65: 141736 (16.3%) ################
0.70: 185662 (21.4%) #####################   <- pico
0.75: 163122 (18.8%) ##################
0.80:  98601 (11.4%) ###########
0.85:  44551 ( 5.1%) #####
0.90:  16512 ( 1.9%) #
0.95:  32671 ( 3.8%) ###
1.00:  19287 ( 2.2%) ##
```

**Percentiles:** p10=0.56, p25=0.65, p50=0.71, p75=0.77, p90=0.85, p95=0.95

**Conclusión 2.2:** distribución **unimodal con pico en 0.70**. NO hay bimodalidad que separe "buenas vs random". Esto ya invalida la premisa de que un threshold discrimina calidad.

### 2.3 Sample manual — skills ruidosas vs buenas

#### Caso crítico: Operario de limpieza (ISCO 9112, desc=239)

| Score | Skill asignada | ¿Válida? |
|---|---|---|
| 0.77 | apuestas mutuas | **❌ Random** |
| 0.75 | programas públicos de seguridad social | **❌ Random** |
| 0.70 | escribir en catalán | **❌ Random** |

#### Caso crítico: Acompañante terapéutico (ISCO 3412, desc=157)

| Score | Skill | ¿Válida? |
|---|---|---|
| 0.69 | recoger muestras de animales | **❌ Random** |
| 0.68 | calcular dimensiones de un grabado | **❌ Random** |
| 0.65 | radioterapia | ⚠️ Parcial |

#### Caso bueno: Enfermera profesional (ISCO 2221, desc=977)

| Score | Skill | ¿Válida? |
|---|---|---|
| 0.85 | establecer contacto con donantes potenciales | ⚠️ Ambigua |
| 0.79 | **inspeccionar un grabado al ácido** | **❌ Random** |
| 0.79 | **gestionar la entrega de mobiliario** | **❌ Random** |
| 0.78 | administrar medicamentos para facilitar reproducción | ⚠️ Parcial |
| 0.76 | entregar el historial médico | ✅ Válida |

#### Caso bueno: Ingeniero civil (ISCO 3118, desc=330)

| Score | Skill | ¿Válida? |
|---|---|---|
| 0.79 | ingeniería civil | ✅ |
| 0.72 | diseñar planos técnicos | ✅ |
| 0.66 | desarrollar proyectos arquitectónicos | ✅ |

**Conclusión 2.3:** el score **NO discrimina calidad**:
- Skills random con score 0.70-0.79 aparecen en ofertas cortas Y largas.
- Skills buenas con score 0.60-0.70 son comunes también.
- **La calidad depende de relevancia semántica al ISCO, no del score absoluto.**

### 2.4 Cobertura de `skills_rules.json` para fallback

**Estructura actual:** 27 reglas en `skills_rules.json`, todas por **título** (`titulo_contiene_alguno`), NO por ISCO.

- Top 30 ISCOs más frecuentes en ofertas validadas: **0 de 30** tienen regla explícita por ISCO.
- Top ISCO (5223, 3,685 ofertas) sin regla dedicada. Igual 3322, 2411, 4110, 8160, 1219, 9333.

**Conclusión 2.4:** el fallback propuesto en Spec B ("si threshold descarta todo, usar skills_rules por ISCO") es **inviable** con la estructura actual. Requeriría:
- Refactor de `skills_rules.json` para soportar matching por ISCO
- Llenar reglas para los ~50 ISCOs más frecuentes (~1000+ skills a mapear)
- **Esfuerzo estimado: 20-40h adicionales**

---

## 3. Invalidación de la hipótesis original del Spec B

El Spec B proponía:
> "Threshold dinámico según contexto. Desc corta + sin tareas → threshold 0.75. Normal → 0.40."

**Los datos muestran que esto NO funciona:**

1. **Las skills ruidosas tienen scores 0.70-0.80** (no bajos). Un threshold de 0.75 descartaría muchas y mantendría ruido.
2. **Las skills buenas tienen scores desde 0.60**. Threshold alto perdería skills válidas.
3. **La distribución es similar en ofertas cortas y largas** — no hay efecto contexto-dependiente claro.
4. **BGE-M3 es un modelo genérico**, no está fine-tuned en ESCO-argentino. No puede distinguir "apuestas mutuas vs limpieza" para un ISCO 9112.

---

## 4. Diagnóstico del root cause real

El problema no es el threshold. Es que **BGE-M3 genérico no tiene suficiente conocimiento de dominio**:

- Una oferta "Operario de limpieza" tiene descripción corta → pocas palabras distintivas.
- BGE-M3 entrega como top-K las skills con embeddings más cercanos a ese texto pobre.
- Como el modelo no sabe que "limpieza" y "apuestas mutuas" son dominios completamente distintos, da scores similares.

La raíz del ruido es **incompatibilidad ISCO-skill** que el modelo no detecta.

---

## 5. Propuesta alternativa: Filtro de compatibilidad ISCO-skill

### 5.1 Idea

Después de que BGE-M3 asigne skills, **filtrar por compatibilidad con el ISCO ya forzado por las reglas de matching**.

Para cada ISCO hay un conjunto de skills "típicas" (via ESCO: relación `esco_skill_to_occupations`). Si una skill asignada no está en ese conjunto (o en dominios cercanos), descartarla.

### 5.2 Implementación

**Ya tenemos los datos:**
- `database/embeddings/esco_skill_to_occupations.json` existe (ver listado previo)
- Es el mapeo oficial ESCO: por cada ocupación, skills obligatorias/opcionales

**Cambio en `skills_implicit_extractor`:**

```python
def filter_by_isco_compatibility(self, skills, isco_code, threshold_compat=0.6):
    """Filtra skills cuya afinidad con ISCO es baja.

    Usa esco_skill_to_occupations (mapeo oficial) o similaridad de embedding
    entre el título del ISCO y la skill.
    """
    if not isco_code:
        return skills
    occupation_skills = self._get_esco_skills_for_isco(isco_code)
    if not occupation_skills:
        return skills  # sin mapeo → no filtrar
    filtered = []
    for s in skills:
        skill_uri = s.get('skill_uri')
        if skill_uri in occupation_skills:
            filtered.append(s)  # skill oficialmente del ISCO
        else:
            # Fallback: verificar si el embedding de la skill
            # es cercano al embedding del ISCO preferred_label
            if self._skill_isco_affinity(skill_uri, isco_code) >= threshold_compat:
                filtered.append(s)
    return filtered
```

### 5.3 Por qué esto sí podría funcionar

- No depende de threshold absoluto de BGE-M3.
- Usa relaciones oficiales ESCO que son autoritativas (skills obligatorias por ocupación).
- Funciona en todas las bandas de contexto (desc corta o larga).
- No requiere llenar 50 reglas nuevas — ya existe `esco_skill_to_occupations`.

### 5.4 Riesgos

- **ESCO no cubre todos los ISCOs**: si un ISCO tiene pocas skills oficiales, el filtro es demasiado estricto. Mitigable con fallback a similaridad semántica entre title_ISCO + skill.
- **Algunas skills son genuinamente transversales** ("trabajar en equipo", "resolver problemas"). No deben filtrarse. Mantener lista whitelist.
- **Impacto masivo**: afectaría las 868K skills asignadas. Testing obligatorio.

---

## 6. Recomendación final

### Opción A (nueva, basada en datos): Filtro por compatibilidad ISCO-skill
- Esfuerzo: **6-10h**
- Riesgo: medio (requiere tests extensos)
- Beneficio: real, basado en evidencia ESCO

### Opción B (original Spec B): **DESCARTAR**
- Los datos invalidan la hipótesis de threshold dinámico.

### Opción C (conservadora): Solo resolver ofertas con contexto crítico (1.5%)
- Aplicar filtro ISCO-compat SOLO a `desc<400 + tareas=0` (783 ofertas).
- Esfuerzo: 2-3h
- Riesgo: bajo
- Beneficio: limpia el peor 1.5% sin impactar el 73% de ofertas buenas.

### Opción D (no hacer): Aceptar el status quo
- 868K skills con distribución conocida. El 11% tiene score <0.60 (potencialmente ruido).
- Dashboard funciona. Problema menor.

---

## 7. Próximo paso sugerido

1. Revisar este informe con el stakeholder.
2. Decidir entre A, C, o D.
3. Si elegir A o C: diseñar Spec B v2 con el approach de compatibilidad ISCO-skill.
4. Si D: cerrar ticket, documentar como limitación conocida.

---

## Anexos

- `/tmp/pipeline_test/context_dist.txt` — distribución de contexto
- `/tmp/pipeline_test/scores_dist.txt` — distribución de scores BGE-M3
- `/tmp/pipeline_test/sample.txt` — sample manual de 20 ofertas
- `/tmp/pipeline_test/rules_coverage.txt` — cobertura skills_rules
- `database/embeddings/esco_skill_to_occupations.json` — mapeo oficial ESCO (insumo para Opción A)

**Datos base:** snapshot de BD `/tmp/pipeline_test/snapshot2.db` (2026-04-24 14:56, 52,370 ofertas validadas).
