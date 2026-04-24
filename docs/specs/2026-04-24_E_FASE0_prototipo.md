# SPEC E — Fase 0: Prototipo embeddings enriquecidos

**Fecha:** 2026-04-24
**Objetivo:** Validar si reconstruir los embeddings ESCO con texto enriquecido (no solo `label`) resuelve el problema de matching ruidoso.
**Resultado:** ✅ **Validado con evidencia rotunda**. Los embeddings enriquecidos discriminan semánticamente por dominio donde los actuales fallan.

---

## 1. Diagnóstico previo

Los embeddings actuales (`esco_skills_embeddings_full.npy`, 14,247 × 1024) se generaron usando **solo el campo `label`** de cada skill ESCO. Esto dejó fuera:
- `description` (14,257 skills ya tienen descripción extraída del RDF)
- `broader_label` (jerarquía padre)
- `category_label`, `L1`, `L2` (taxonomía 28 categorías / 112 subcategorías)
- `esco_codes` de ocupaciones donde aplica (conexión con las 3,045 ocupaciones ESCO)

Resultado: BGE-M3 matcheaba tareas cortas ("Tareas de montaje") contra skills basándose solo en parecido superficial de strings. Skills de dominios ajenos aparecían en top-K constantemente.

---

## 2. Prototipo

**Script:** `scripts/embeddings/prototipo_embeddings_enriquecidos.py`

**Subset:** 575 skills del corpus ESCO, incluyendo:
- 163 skills metalúrgicas (ESCO 7214.*)
- 195 skills plástico (ESCO 8142.*)
- 88 skills textiles (ESCO 7318.*) — dominio ajeno de control
- 150 skills enfermería (ESCO 2221.*) — dominio ajeno de control
- 13 skills de "ruido conocido" que Cyn marcó como malas

**Texto enriquecido generado por skill:**
```
{label}
Categoría: {L1}.{L2} {category_label}
Tipo general: {broader_label}
Típica en: {top 3 ocupaciones essential_for con esco_code}
{description}
```

**Ejemplo real:**
```
controlar baños galvánicos
Categoría: S2.S2.8 controlar la calidad de los productos
Tipo general: controlar la calidad de los productos
Típica en: operador de máquinas de galvanización (8122.7)
Controlar la temperatura y la composición cambiante de la solución 
compuesta de diferentes componentes químicos...
```

**Proceso:**
1. Generar embeddings BGE-M3 sobre texto enriquecido (575 skills en 8.8 s)
2. Subsetear embeddings viejos al mismo conjunto de 575 skills (misma base de comparación)
3. Correr matching sobre tareas de las 2 ofertas Cyn con ambos sets
4. Comparar top-K

---

## 3. Resultados comparativos

### 3.1 Operario metalúrgico — "Conocimiento de soldadura"

| Rank | Viejo (solo label) | Score | Nuevo (enriquecido) | Score |
|---|---|---:|---|---:|
| 1 | aplicar los principios de enfermería | 0.75 | **manejar equipos de soldadura** | 0.60 |
| 2 | animación de partículas | 0.73 | **operar herramientas para soldadura** | 0.56 |
| 3 | mecánica de los buques | 0.67 | **tecnologías de corte** | 0.56 |
| 4 | evaluar el tratamiento de radioterapia | 0.54 | **emplear técnicas de soldadura** | 0.55 |
| 5 | utilizar el razonamiento clínico | 0.51 | **conductividad térmica de los metales** | 0.54 |

### 3.2 Operario plástico — "Manejo u operación de máquinas de estiro-soplado"

| Rank | Viejo | Score | Nuevo | Score |
|---|---|---:|---|---:|
| 1 | evaluar el tratamiento de radioterapia | 0.68 | **ocuparse de máquinas de moldeo por soplado** ← Cyn | 0.65 |
| 2 | mantener la administración personal | 0.67 | **operar maquinaria para fabricar plástico** ← Cyn | 0.61 |
| 3 | cultivar plancton | 0.64 | manejar rodillos | 0.61 |
| 4 | preparar piezas de trabajo para el grabado | 0.62 | ocuparse de sierras para metales | 0.60 |
| 5 | participar en formación del personal sanitario | 0.62 | operar bobinadoras de cable aislante | 0.59 |

### 3.3 Otros casos

- "Tareas de montaje" (metal): viejo → textiles/enfermería/plásticos. Nuevo → `construir plataformas de trabajo`, `montar unidades mecatrónicas`, `instalar matrices de prensado`, `montar sensores`.
- "Manejo de herramientas manuales" (metal): viejo → `modificar diseños textiles`, `estudiar fotografías aéreas`. Nuevo → `utilizar herramientas de construcción o reparación`, `utilizar herramientas eléctricas`, `herramientas mecánicas`.
- "Procesamiento de plásticos: control de calidad" (plástico): viejo → `pesar los materiales`, `ordenación pesquera`, `tratar las enfermedades`. Nuevo → `controlar condiciones ambientales de procesamiento`, `inspeccionar la calidad de los productos`, `manipular el plástico`.

---

## 4. Observaciones clave

### 4.1 Discriminación semántica por dominio
Los embeddings enriquecidos **expulsan** skills de dominios ajenos aunque el label superficial sea similar. El contexto (categoría + jerarquía + descripción + ocupaciones) da a BGE-M3 la señal que le faltaba.

### 4.2 Las skills que Cyn sugirió aparecen
- `ocuparse de máquinas de moldeo por soplado` — rank 1 nuevo, ausente viejo
- `operar maquinaria para fabricar plástico` — rank 2 nuevo, ausente viejo
- `manejar equipos de soldadura`, `emplear técnicas de soldadura` — rank 1 y 4 nuevos, ausentes viejo

El conocimiento que Cyn "sabía" estaba **en ESCO desde siempre**, solo que los embeddings no lo exponían.

### 4.3 Scores absolutos bajan
Rango viejo: 0.51-0.92 (casi todos muy altos porque BGE-M3 confundía dominios parecidos).
Rango nuevo: 0.54-0.65 (más bajo pero más correcto). El threshold actual (0.40) seguirá sirviendo pero probablemente convenga ajustar umbrales o usar solo ranking por top-K.

### 4.4 Costo
- Regeneración completa: 14,247 skills × 1024-dim en BGE-M3 ≈ **3-4 min CPU**
- Ocupaciones (3,045) otros **~1 min**
- No requiere GPU ni fine-tuning

---

## 5. Conclusión

El enriquecimiento del texto antes de embedder **resuelve el root cause** detectado en todas las fases exploratorias anteriores (Spec B, Spec D). Las skills ruidosas desaparecen del top-K, las skills correctas emergen naturalmente.

**Próximo paso:** escribir SPEC E formal con plan de 4 fases (regenerar embeddings completos + actualizar metadatos con `esco_code` + ajustar pipeline + retropropagar 49K ofertas).

---

## Anexos

- Script prototipo: `scripts/embeddings/prototipo_embeddings_enriquecidos.py`
- Fuentes RDF ya extraídas (sin acción necesaria):
  - `database/embeddings/esco_skills_full.json` (14,257 skills con description + L1/L2 + broader)
  - `database/embeddings/esco_skill_to_occupations.json` (skill → esco_codes)
- Embeddings actuales a reemplazar:
  - `database/embeddings/esco_skills_embeddings_full.npy`
  - `database/embeddings/esco_skills_metadata_full.json`
  - `database/embeddings/esco_occupations_embeddings.npy`
  - `database/embeddings/esco_occupations_metadata.json`
- Baselines disponibles para rollback: `database/embeddings/baselines/`
