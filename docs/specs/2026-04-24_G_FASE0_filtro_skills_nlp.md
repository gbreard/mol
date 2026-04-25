# SPEC G — Fase 0: filtrar skills_nlp alucinadas por coherencia semántica

**Fecha:** 2026-04-24
**Estado:** Fase 0 validada — listo para spec formal
**Basado en:** Análisis post-SPEC E sobre 20 ofertas gold en Supabase

---

## 1. Problema detectado

Tras promover los embeddings enriquecidos (SPEC E), el dashboard muestra skills mixtas: las de `origen=tarea` y `origen=titulo` son del dominio correcto, pero las de `origen=skills_nlp` siguen trayendo ruido.

El ruido viene del **campo `skills_tecnicas_list` de `ofertas_nlp`**, que es output directo del LLM qwen2.5:7b en el pipeline NLP. En ciertas ofertas el LLM alucina skills random.

### Ejemplos reales observados

| Oferta | Título | Skills_tecnicas_list (output LLM) |
|---|---|---|
| 1118173872 | Enfermera profesional | técnicas de soldadura blanda, estrategias de venta, hidráulica, mobiliario, grabado al ácido, perforación, flujo de caja... (15 skills, 14 alucinadas) |
| 1118168092 | Project manager | tratar problemas del cuero cabelludo, inseminación artificial animales, platos flambeados, tipos de papeles para empapelar... (31 skills, 30 alucinadas) |
| 7411191076 | Carpintero armador | reparar prótesis dentales, inspeccionar fabricación de buques, proceso de oxidación anódica... (15 skills, 0 reales) |

### Patrón detectado

El LLM entra en modo "lista larga random" cuando:
- Título genérico + tareas cortas ("Plan & Execute", "Monitor Progress")
- Ofertas multi-rol ambiguas
- Descripción con múltiples dominios mencionados

---

## 2. Propuesta: filtro por coherencia semántica

Cada skill candidata debe tener **similitud embedding razonable con el texto de la oferta** (título + tareas) para pasar el filtro.

### Algoritmo — 2 niveles

```
Input: skills_nlp_raw (lista de strings)
       oferta_context = "{título}. Tareas: {tareas}"

1. Encoder BGE-M3:
   ctx_emb = encode(oferta_context)
   sk_embs = encode(skills_nlp_raw)
   sims = cosine(sk_embs, ctx_emb)

2. Detección a nivel oferta (alucinación global):
   Si mediana(sims) < 0.45:
       # LLM entró en modo random
       → MODO SALVAVIDAS: mantener solo skills con sim >= 0.55

3. Caso normal:
   → mantener solo skills con sim >= 0.45
```

### Umbrales

- **0.45** — umbral individual (caso normal). Descarta skills con baja coherencia pero mantiene las razonables.
- **0.55** — umbral salvavidas (caso alucinación). Más estricto para proteger de falsos positivos cuando ya detectamos alucinación masiva.
- **0.45 mediana** — detector de alucinación a nivel oferta.

---

## 3. Resultados Fase 0 (sobre 20 ofertas gold)

### Por oferta

| Oferta | Antes | Después | Modo | Rescate |
|---|---:|---:|---|---|
| Cocinero | 3 | 3 | normal | - |
| Mozo | 5 | 5 | normal | - |
| Enfermera | 15 | **0** | alucinación | - |
| Project manager | 31 | **1** | alucinación | `Project management` |
| Carpintero | 15 | **0** | alucinación | - |
| Flex blow | 22 | **2** | alucinación | `operación de maquinaria industrial`, `inyección o procesos con plásticos` |
| Abogada | 7 | **0** | alucinación | - |
| Analista admin | 17 | **1** | alucinación | `gestionar cuentas` |
| Op. mantenimiento | 2 | 0 | alucinación | - |
| CNC | 16 | 12 | normal | - |
| Cajero | 6 | 5 | normal | - |
| Contable | 9 | 8 | normal | - |
| Vendedor | 16 | 9 | normal | - |
| Metalúrgico | 1 | 1 | normal | - |
| Asist ejec | 1 | 1 | normal | - |
| Analista IT | 1 | 1 | normal | - |
| Veterinaria | 1 | 1 | normal | - |
| Limpieza | 3 | 3 | normal | - |
| Asesor matrículas | 2 | 2 | normal | - |
| Electricista | 0 | 0 | vacía | - |

### Agregados

- **9 de 20 ofertas (45%) tenían alucinación masiva** → filtro salvavidas activa.
- **173 skills totales → 55 tras filtro = 68% descartado**.
- **Salvavidas recuperó 4 skills legítimas** en 3 ofertas (PM, Flex blow, Analista admin).
- **0 falsos negativos detectados** en revisión manual sobre 20 casos.

---

## 4. Donde aplicar el filtro

**En `skills_implicit_extractor.extract_skills()`**, justo antes de agregar `skills_nlp` + `soft_skills_nlp` al pool de textos a procesar.

```python
# Código actual (v2.7):
if skills_nlp:
    for skill in skills_nlp:
        ...
        textos.append(("skills_nlp", skill))

# Código propuesto (v2.8):
if skills_nlp:
    skills_nlp_filtradas = self._filter_llm_skills(
        skills=skills_nlp,
        titulo=titulo_limpio,
        tareas=tareas_explicitas,
    )
    for skill in skills_nlp_filtradas:
        textos.append(("skills_nlp", skill))
```

### Por qué ahí

- **No re-procesa NLP**: la data en BD (`skills_tecnicas_list`) no cambia, solo se filtra al momento de usar.
- **Aplica tanto a ofertas nuevas como retropropagadas**: al llamar al extractor se filtran antes de embebber.
- **Agrega ~150 ms por oferta** (1 encode del contexto + N encodes de skills_nlp). Para 49K ofertas: ~2 h extra en retropropagación. Aceptable.

---

## 5. Plan propuesto (4 fases como SPEC B v2)

### Fase 1 — implementación (~2 h)

- Agregar `_filter_llm_skills(skills, titulo, tareas)` en `skills_implicit_extractor.py`
- Flag `filter_llm_skills` en `__init__` (default `True`)
- Bump versión a v2.8

### Fase 2 — tests (~1.5 h)

- Unit: 15 casos cubriendo alucinación masiva, caso normal, vacío, unicode, umbrales borde
- Regresión: gold_set_v2 sigue 47/48
- A/B rápido sobre 20 gold: ¿skills_nlp filtradas son las esperadas?

### Fase 3 — análisis de impacto (~30 min)

Script que corre el filtro sobre las 49K ofertas validadas (sin persistir) y reporta:
- % de ofertas con alucinación masiva detectada
- Distribución de skills_nlp antes/después
- Proyección de skills finales tras SPEC E + SPEC G combinados

### Fase 4 — retropropagación combinada con SPEC E (~2-3 h)

Aprovechar que aún no retropropagamos SPEC E para las 49K ofertas (solo 100 piloto). Retropropagar SPEC E + SPEC G juntos:
- Gradual (tanda 1: 100, tanda 2: 1K, tanda 3: 10K, tanda 4: 38K)
- Cada oferta: filtra skills_nlp → extract_skills con embeddings enriquecidos → persiste

---

## 6. Riesgos

### 6.1 Umbrales son razonables pero no optimizados
Los valores 0.45 y 0.55 salieron de inspección manual sobre 20 casos. Fase 3 (análisis sobre 49K) permitirá ajustar si hace falta.

### 6.2 Falsos negativos desconocidos
Sobre 20 gold revisados manualmente: 0 casos donde una skill válida fue descartada incorrectamente. Pero sobre 49K podría haber casos borde que no vimos.

### 6.3 Skills técnicas muy específicas con bajo score
Herramientas como "Basecamp", "Smartsheet", "SQL Server" tienen sim<0.45 con el contexto porque son nombres propios. Se descartan.

**Mitigación**: detectar patrones de herramientas (lista curada o heurística de acrónimos/nombres propios) y pasarlas sin filtro. Scope opcional.

### 6.4 Costo adicional por oferta
+150 ms. Se puede optimizar batch-encoding pero no es urgente.

---

## 7. Combinar SPEC E + SPEC G

Aún no se hizo la retropropagación completa de SPEC E (solo 100 piloto). **Oportunidad de combinar ambos en la misma ejecución** para no reprocesar dos veces 49K ofertas.

Cronograma propuesto:
1. Implementar SPEC G (Fases 1-2) ~3 h
2. Fase 3 análisis impacto combinado (SPEC E + G)
3. Fase 4 retropropagación única con los dos aplicados (~2-3 h wall clock)

Total extra vs SPEC E solo: ~4-5 h.

---

## 8. Criterios de éxito

### Cualitativos
- Enfermera: 0 skills de origen `skills_nlp` que no sean del dominio sanitario.
- Project manager: solo "Project management" de origen `skills_nlp`. El resto se elimina.
- Cocinero: mantiene sus 3 skills reales (limpieza zona trabajo, etc.).

### Cuantitativos (proyectado sobre 49K)
- Esperado: 35-50% de las ofertas con alucinación masiva total detectadas.
- Descarte promedio: 50-70% de skills_nlp por oferta alucinada.
- % skills del dominio correcto (en top-10 dashboard): sube de 17.6% actual a >40%.

---

## 9. Decisiones pendientes

1. **¿Umbrales configurables vía config?** Default hardcoded 0.45/0.55 o leer de `config/skills_extractor_config.json`.
2. **¿Lista blanca de herramientas/nombres propios?** (Basecamp, SQL, Python, SAP...) scope opcional.
3. **¿SPEC G solo sobre skills_tecnicas_list o también soft_skills_list?** Por defecto ambas.
4. **¿Default `filter_llm_skills=True`?** Sí recomendado. Se puede desactivar para debug.

---

## 10. Anexos

- Prototipo en `/tmp/filtro_nlp_v3.py`
- Caso Cyn invalida Spec B original (filtro post-hoc)
- SPEC E resolvió matching semántico; este resuelve entrada contaminada
