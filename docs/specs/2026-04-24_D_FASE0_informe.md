# SPEC D — Fase 0 Exploratoria: Informe de findings

**Fecha:** 2026-04-24
**Autor:** Claude (análisis empírico sobre BD local, snapshot 2026-04-24 14:56)
**Estado:** Investigación completada — **invalida el approach de filtro automático**
**Conclusión principal:** La idea original ("comparar skills semánticas contra skills oficiales ESCO del ISCO aplicado") **NO discrimina ruido** con los datos actuales. Se propone un approach alternativo basado en curación.

---

## 1. Contexto

Spec disparado por 2 issues pendientes de Cynthia (2026-04-24):
- `#0cf1bf8d` oferta 9255109063 (operario plástico flex blow) — ~50 skills random asignadas
- `#41571c84` oferta 7907119232 (operario metalúrgico) — skills ruidosas ("producir diseños textiles", "equipos de acuicultura")

Ambas ofertas tienen ISCO correcto por SPEC A pero **skills semánticas de dominio ajeno**. El filtro trust v2 no las detecta porque son `origen=tarea` (confiadas por construcción).

Cynthia aporta, además de la queja, **las skills correctas sugeridas** por puesto — valioso como gold set.

---

## 2. Las 4 dimensiones investigadas

### 2.1 Magnitud del problema

| Métrica | Valor |
|---|---|
| Ofertas validadas totales | 52,548 |
| Con regla matching aplicada (`decision_metodo=regla_prioridad`) | 20,574 (39.2%) |
| Skills totales en ofertas con regla | 348,794 |

**Dispersión de skills por ISCO (top 15):**

| ISCO | Ofertas | Skills distintas | Cobertura prom (oferta vs top-20 ISCO) | % ofertas ruidosas (<30% cobertura) |
|---|---:|---:|---:|---:|
| 3322 asesor comercial | 2,215 | 3,892 | 18.1% | **84%** |
| 2512 desarrollador SW | 970 | 3,179 | 19.8% | 81% |
| 1219 jefe genérico | 854 | 4,205 | 10.2% | **94%** |
| 8160 operario producción | 796 | 3,042 | 19.3% | 74% |
| 7231 mecánico | 738 | 2,820 | 19.8% | 81% |
| 2411 contador | 631 | 2,650 | 10.9% | **93%** |
| 2511 analista IT | 438 | 2,310 | 14.1% | **93%** |
| 9112 op. limpieza | 428 | 1,277 | 35.6% | 54% |

**Dispersión = alta en todos los ISCOs**. Cada oferta trae 10-20 skills, pero solo el 10-35% coincide con las skills más frecuentes del mismo ISCO. El resto son skills distintas entre ofertas → consistencia muy baja.

**Proyección:** ~7,856 ofertas ruidosas en top 15 ISCOs; **~16,000 ofertas afectadas en total** (estimado). No es un caso borde, es sistémico.

### 2.2 Cobertura de `skills_rules.json`

| Métrica | Valor |
|---|---|
| Reglas RS activas | 27 |
| Skills forzadas totales | 41 |
| Promedio skills/regla | 1.5 |
| Reglas matching con ofertas aplicadas | 309 |
| Ofertas con regla matching pero SIN RS rule | 10,697 (**52%**) |

`skills_rules.json` está subdimensionado: 27 reglas cubren solo el 48% de ofertas con regla matching. Y cada RS tiene en promedio **1.5 skills** — muy pocas para describir un rol.

**ESCO oficial como seed:** `esco_skill_to_occupations.json` contiene 13,492 skills vinculadas a 426 ISCOs. Para los 17 ISCOs relevantes hay entre 47 y 1,965 relaciones oficiales disponibles. **Sirve como seed** para curación.

### 2.3 Tres enfoques de coherencia (probados sobre caso Cyn)

**Enfoque A — Similaridad con centroide embedding del ISCO**
- Promediar embeddings de las 163 skills oficiales del ISCO 7214 → centroide
- Medir similitud de cada skill candidata vs centroide
- **Resultado:** las 12 skills asignadas caen en rango estrecho (0.61-0.75). No discrimina.
- "producir diseños textiles" (obvio ruido) tiene sim=0.708, más alta que "herramientas metalúrgicas" (sim=0.660).

**Enfoque B — Jaccard por URI (pertenencia al ESCO oficial del ISCO)**
- Skill pertenece al ESCO oficial del ISCO exacto → mantener
- Sobre caso metalúrgico: **0 de 12 skills pertenecen**.
- Rechaza el ruido correctamente PERO también todas las skills argentinas legítimas que no estén en ESCO oficial.
- Global: **94.3% descarte** sobre 348K skills. Inaceptable.

**Enfoque C — Híbrido (pertenencia O similitud ≥ 0.80 con cualquier skill oficial)**
- Sobre caso Cyn: confunde igual. "animación de partículas" sim=0.884 con "mecánica de los buques" pasa como SIMIL (falso positivo). "evaluar tratamiento de radioterapia" sim=0.847 con "ocuparse de máquinas de moldeo" pasa (falso positivo).
- BGE-M3 captura parecido sintáctico más que semántico profundo — coincide con Fase 0 de SPEC B.

**Enfoque B' — Jaccard jerárquico (grupo ISCO 1/2/3 dígitos)**
- Ampliar pertenencia al grupo: ISCO 7214 → grupo 72 → grupo 7
- Distribución global:
  - 5.7% skills en ISCO 4-dig
  - 10.5% en grupo 3-dig
  - 18.6% en grupo 2-dig
  - 41.4% en grupo 1-dig
  - **58.6% fuera de todo grupo ESCO relacionado**
- Caso metalúrgico: deja pasar "producir diseños textiles" (está en grupo 7 artesanos) — sigue siendo falso positivo.

### 2.4 Riesgo de falsos positivos

Ejemplos reales del Enfoque B' (grupo 2-dig) aplicado al caso plástico (8142):
- **Mantenidas erróneamente**: "aplicar normas de mantenimiento a artículos de marroquinería", "completar registro del traslado del paciente", "mantener instrumentos musicales"
- **Descartadas erróneamente**: "fabricar piezas de metal" (score 0.63, tiene sentido como equivalente de "producir piezas")
- **Correctas**: "preparar moldes ensamblados" (única skill que legítimamente pasa)

**El filtro ni rechaza bien el ruido ni preserva bien lo bueno**. El problema es que **BGE-M3 asignó skills random en primera instancia** — filtrar después no recupera información que no se capturó.

---

## 3. Invalidación del approach original

El SPEC D original proponía:
> "Filtrar skills semánticas por compatibilidad con skills oficiales ESCO del ISCO aplicado"

**Los datos invalidan esto:**

1. **BGE-M3 no discrimina** entre dominios cercanos y lejanos con consistencia.
2. **ESCO oficial es incompleto** para vocabulario argentino — descartar lo que no pertenece tira 94% de skills.
3. **Grupo ISCO (1-dig)** agrupa dominios muy distintos — deja pasar ruido.
4. **El ruido nació en extracción**, no se puede filtrar después con las señales disponibles.

---

## 4. Diagnóstico del root cause real

El problema no es el filtrado. Es que **BGE-M3 mapea tareas cortas/genéricas a skills random**:

- Tarea: "Tareas de montaje" (3 palabras) → BGE-M3 top-K: "producir diseños textiles", "equipos de acuicultura", "animación de partículas"
- Tarea: "Operación de maquinaria automática" (4 palabras) → BGE-M3 top-K: "quitar tejados", "radioterapia", "cultivar plancton"

El modelo genera embeddings a nivel palabra/texto corto y el top-K contra 14K skills ESCO cae en skills de dominios diversos que comparten tokens superficiales.

---

## 5. Propuesta alternativa: curación expandida + fuente explícita por regla

### 5.1 Idea

En lugar de filtrar automáticamente las skills semánticas, **expandir masivamente `skills_rules.json`** para que las skills correctas por rol estén forzadas, y **dar prioridad a las skills de regla sobre las semánticas** cuando hay regla matching aplicada.

### 5.2 Componentes

**(a) Expansión de `skills_rules.json`:**
- Crear RS rules para cada una de las 309 reglas matching activas (hoy hay 27).
- Seed automático: por cada ISCO, extraer las top 10-20 skills oficiales ESCO como propuesta inicial.
- Curación humana (Cyn, equipo): aprobar/descartar/agregar skills argentinas específicas.
- Target: 100-150 reglas RS con 5-10 skills cada una (~1,000 skills curadas totales).

**(b) Política "fuente explícita por regla":**
- Si la oferta matchea regla matching R_xxx y existe RS_xxx correspondiente:
  - Skills forzadas por RS → entran con origen=`regla_cynthia` (o similar)
  - Skills semánticas (BGE-M3) → se mantienen **solo si son del top-3 por score** en cada texto fuente. El resto se descarta.
- Si la oferta no tiene regla matching:
  - Comportamiento actual (sin cambios).

**(c) Gold set de validación:**
- Usar las skills sugeridas por Cynthia como dataset de validación.
- Asegurar que después de la expansión, las 2 ofertas canónicas (7907119232 y 9255109063) tienen solo skills del dominio correcto.

### 5.3 Por qué esto sí podría funcionar

- **No depende de BGE-M3 para discriminar** — la curación humana es la fuente de verdad.
- **No sesga a ESCO europeo** — la curación incluye terminología argentina.
- **Reversible e iterable** — cada RS es una regla editable. Feedback de usuarios → ajuste de skills.
- **Es trabajo honesto** — reconoce que el problema no se resuelve con algoritmia, requiere curación.

### 5.4 Costo estimado

- Seed automático desde ESCO: 2h (script)
- Curación inicial para top 30 ISCOs (cubre ~80% ofertas con regla): **20-40h humanas** (Cyn + verificación)
- Implementación del cambio en `skills_implicit_extractor` para respetar jerarquía de fuente: 4h
- Retropropagación + tests: 4h
- **Total: ~30-50h humanas + ~10h técnicas**

Vs. el SPEC D automático original (~6-10h) pero con resultado real.

---

## 6. Recomendaciones

### Opción A (nueva, basada en datos): Curación expandida + fuente explícita
- Esfuerzo: **30-50h humanas + 10h técnicas**
- Riesgo: medio (depende de disponibilidad de Cyn/equipo)
- Beneficio: resultado real, no parche
- Escalable con más curación

### Opción B (SPEC D original): **DESCARTAR**
- Los datos invalidan que el filtrado automático sea confiable.

### Opción C (conservadora): Solo cubrir top 15 ISCOs con mayor ruido
- Limitar curación a top 15 ISCOs (cubren ~70% ofertas con regla).
- Esfuerzo: 15-20h humanas + 6h técnicas
- Cobertura parcial pero impacto alto en casos visibles como los de Cyn

### Opción D (no hacer): Aceptar estado actual
- Usuarios reportan casos → resolver por issue individual
- 94% de ofertas con regla siguen con skills dispersas
- Aceptable si el caso de uso del dashboard no requiere skills precisas

---

## 7. Próximo paso

Revisar este informe con el stakeholder:
- Decidir A / C / D
- Si A o C: planificar sesiones de curación con Cyn/equipo
- Si D: documentar como limitación conocida

---

## Anexos

- Seed ESCO disponible: `database/embeddings/esco_skill_to_occupations.json` (13,492 skills)
- BD fuente del análisis: `/tmp/pipeline_test/snapshot2.db` (snapshot 2026-04-24 14:56)
- Casos Cyn pendientes: issues #0cf1bf8d (9255109063) y #41571c84 (7907119232)
- Informe relacionado: `2026-04-24_B_FASE0_informe.md` (Fase 0 de SPEC B, invalidación análoga)
