# SPEC E — Análisis de factibilidad

**Fecha:** 2026-04-24
**Spec:** `2026-04-24_E_embeddings_enriquecidos.md`
**Estado:** Análisis previo a implementación

Decisiones ya tomadas:
- Modelo: BGE-M3 base (LoRA no disponible en disco).
- Retropropagación: **gradual** (no big-bang).
- Filtro `filtrar_por_trust`: se mantiene en `False` (cambio independiente).
- `texto_indexado`: se persiste en metadata.

---

## 1. Factibilidad técnica

### 1.1 Datos fuente (auditados)

| Archivo | Tamaño | Contenido | Estado |
|---|---:|---|---|
| `esco_skills_full.json` | 11.4 MB | 14,257 skills con label + description + L1/L2 + broader | ✅ 100% completitud |
| `esco_skill_to_occupations.json` | 31.2 MB | 13,492 skills con esco_codes de ocupaciones | ✅ 95% cobertura |
| `esco_occupations_full.json` | 1.0 MB | 3,046 ocupaciones con jerarquía | ✅ |
| `esco_occupation_skills.json` | 29.0 MB | Mapeo inverso ocupación → skills | ✅ |

**No hace falta tocar el RDF.** Todo ya extraído.

**Discrepancia detectada:** `esco_skills_full.json` tiene 14,257 skills pero los embeddings actuales tienen 14,247. 10 skills quedaron sin vector. A revisar durante Fase 1.

### 1.2 Modelo

- **BGE-M3 base** confirmado disponible (se descarga de HF la primera vez, después cacheado).
- LoRA fine-tuned: `data/finetuning/matching/model_lora` **NO existe**. Confirma decisión 1.
- CPU: OK (prototipo corrió en 8.8s para 575 skills).
- RAM: ~2 GB modelo + ~500 MB embeddings = 2.5 GB pico. Sin problemas.

### 1.3 Embeddings actuales (para backup)

| Archivo | Tamaño | Shape |
|---|---:|---|
| `esco_skills_embeddings_full.npy` | 55.7 MB | 14,247 × 1024 |
| `esco_occupations_embeddings.npy` | 11.9 MB | 3,045 × 1024 |

**Baselines existentes en `baselines/`:** `esco_skills_embeddings_full_baseline.npy` + `esco_occupations_embeddings_baseline.npy`. Rollback viable sin trabajo adicional.

### 1.4 Código downstream a tocar

| Archivo | Líneas | Impacto |
|---|---:|---|
| `database/skills_implicit_extractor.py` | 1,773 | Medio — agregar soporte al nuevo metadata (campo `esco_codes_aplicable`) |
| `database/match_by_skills.py` | 377 | Bajo — usar `esco_code` del metadata nuevo de ocupaciones |
| `database/match_ofertas_v3.py` | 2,075 | Nulo (usa skills_implicit_extractor, no toca embeddings directo) |
| `database/skill_categorizer.py` | 362 | Nulo (ya usa L1/L2 que seguirán disponibles) |
| `config/embedding_config.py` | 20 | Bajo — actualizar paths si cambian |

**Conclusión:** el cambio es contenido. Los embeddings son una dependencia de 1-2 archivos.

### 1.5 Tiempos reales medidos (sobre BD)

Corrida sobre 20 ofertas validadas aleatorias:
- Carga de extractor (modelo + embeddings): 6.4 s una vez.
- Por oferta: **0.47 s promedio** (mín 0.17 / máx 1.01).
- 49,117 ofertas:
  - Secuencial: **~6.4 h**
  - 4 workers paralelos: **~1.6 h**

Esto es con el modelo y embeddings actuales. Con embeddings nuevos (mismo tamaño) el tiempo es igual.

---

## 2. Factibilidad operativa

### 2.1 Desglose de tiempos por fase

| Fase | Desarrollo | Ejecución | Humano |
|---|---:|---:|---:|
| 1 — Regeneración | 3 h | 5 min (BGE-M3 × 17K textos) | — |
| 2 — A/B test + sampling | 2 h | 10 min | **1-2 h review manual** |
| 3 — Promoción a prod | 1 h | 5 min | — |
| 4 — Retropropagación gradual | 1 h | 2-6 h (ver 3.1) | **30 min revisión** |
| **TOTAL** | **7 h** | **3-7 h** | **2-3 h** |

### 2.2 Recursos

- **Disco:** +150 MB durante Fase 1 (embeddings nuevos coexisten con viejos), vuelve a normal tras Fase 3.
- **RAM:** pico 4 GB durante A/B test (carga ambos sets en memoria para comparar).
- **CPU:** 1 core saturado durante regeneración; 4 cores si paralelizamos retropropagación.
- **Red:** nada (todo local, ya teníamos BGE-M3 cacheado).
- **Ollama:** no necesario.

### 2.3 Ventana operativa

- Fases 1 y 2 no bloquean nada. Pueden correr en paralelo al uso normal del sistema.
- Fase 3 es atómica (mover archivos, <5 min). **Necesita ventana de "no matching nuevo"** o aceptar que los matches ejecutándose en ese instante usen viejo/nuevo mezclado (consecuencia menor: la próxima oferta usa nuevo).
- Fase 4 (retropropagación) puede correr en background durante días sin problema.

---

## 3. Retropropagación gradual — diseño

### 3.1 Estrategia escalonada

En vez de reprocesar las 49K ofertas de una:

```
Tanda 1 — PILOTO       : 100 ofertas     → revisar → GO/NO-GO
Tanda 2 — VERIFICACION :   1,000 ofertas → revisar → GO/NO-GO  
Tanda 3 — SCALE-UP     :  10,000 ofertas → revisar → GO/NO-GO
Tanda 4 — RESTO        : ~38,000 ofertas → background
```

Tiempo real esperado:
- Tanda 1: ~1 min (100 × 0.47 s)
- Tanda 2: ~10 min
- Tanda 3: ~80 min (~1.3 h) — correr en background
- Tanda 4: ~5 h — correr en background

### 3.2 Seleccion de cada tanda

**Tanda 1 (piloto — 100 ofertas):**
- 20 "gold" (casos Cyn + enfermera + casos canónicos conocidos) — comparación directa con spec 0.
- 30 aleatorias de top 5 reglas (metal, plástico, asesor comercial, desarrollador, cocinero) — diversidad de dominios curados.
- 30 aleatorias de reglas menos comunes — cobertura de casos borde.
- 20 sin regla matching (`decision_metodo=semantico_default`) — verifica que el cambio no rompe ese flujo.

**Criterio GO para tanda 2:** sobre esas 100, ≥80% tienen skills del dominio correcto según revisión manual. Caso crítico: las 20 gold deben mostrar skills esperadas.

**Tanda 2 (verificación — 1,000 ofertas):**
- Muestra estratificada por ISCO (10-20 ofertas por top 50 ISCOs).
- Gold set v2 pasa (47/48).

**Criterio GO para tanda 3:** gold set v2 pasa + métrica agregada "skills en `esco_codes_aplicable`" ≥70% (vs ~5% hoy).

**Tanda 3 (scale-up — 10,000 ofertas):**
- Toda oferta con regla aplicada (las 20K se hacen aquí + resto en tanda 4).
- Corre en background.

**Tanda 4 (resto — ~38K):**
- Todo lo que queda, principalmente ofertas sin regla.
- Corre en background.

### 3.3 Reversibilidad por tanda

**Clave:** antes de cada tanda, snapshot de `skills_semantico_json` de las ofertas a procesar en tabla auxiliar `skills_semantico_json_backup_spec_e`. Si en la revisión post-tanda algo es peor, revertimos solo esas ofertas.

Script auxiliar:
```sql
CREATE TABLE skills_semantico_json_backup_spec_e AS
SELECT id_oferta, skills_semantico_json, datetime('now') AS backup_at
FROM ofertas_esco_matching
WHERE id_oferta IN (...);
```

Rollback por oferta: `UPDATE ... SET skills_semantico_json = (SELECT ... FROM backup)`.

### 3.4 Resumable

Si la retropropagación crashea a mitad, debe ser reanudable desde el último batch completado. Táctica:
- Procesar en batches de 500 con commit.
- Tabla de progreso: `spec_e_retropropagacion_progress (id_oferta, procesada_at)`.
- Al reiniciar, saltar las ya procesadas.

---

## 4. Puntos críticos — "dónde podemos cagarla"

### 4.1 Antes de promoción (Fases 1-2)
**Cagadas posibles:** script de generación con bug → embeddings corruptos.
**Blast radius:** 0. Los archivos van a `enriched/`, no tocan producción.
**Mitigación:** tests unit de Fase 5.1.

### 4.2 Promoción a producción (Fase 3)
**Cagadas posibles:**
- Mover archivos con script roto → pipeline no arranca.
- Metadata incompatible con código viejo → skills_implicit_extractor crashea.
**Blast radius:** **ALTO** — cualquier matching que corra durante la ventana falla.
**Mitigación:**
- Antes de mover, correr sanity check: script dummy que carga extractor con nuevos archivos y procesa 1 oferta.
- Si falla → NO mover. Revisar.
- Rollback: copiar baselines sobre producción (5 min).

### 4.3 Retropropagación
**Cagadas posibles:**
- Script corrompe `skills_semantico_json` por bug JSON.
- Timeout WSL /mnt/d deja batch en estado inconsistente.
- Skills nuevas resultan peores en casos específicos que no detectó el A/B.
**Blast radius:** por tanda (100 → 1K → 10K → resto). Cada tanda es revisable antes de la siguiente.
**Mitigación:** snapshot pre-tanda + resumable + revisión manual entre tandas.

### 4.4 Dashboard / Supabase
**Cagadas posibles:**
- Sync Supabase envía campo nuevo (`esco_codes_aplicable`) que la columna no soporta → error de sync.
**Blast radius:** sync falla, dashboard muestra datos viejos.
**Mitigación:** verificar schema Supabase antes de Fase 4 tanda 3. Si hay campo nuevo, agregar columna o filtrar al sync.

### 4.5 Efecto sobre matching de nuevas ofertas (pipeline normal)
**Cagadas posibles:**
- Ofertas scrapeadas en los días de transición usan embeddings nuevos, pero el código no esté 100% adaptado.
**Blast radius:** ofertas procesadas en ventana Fase 3→4 quedan con skills mixtas de calidad.
**Mitigación:** pausar scraping durante Fase 3 (1 día) o aceptar que esas pocas ofertas (~50-100 en un día) queden con nuevos embeddings aunque el pipeline downstream no esté optimizado aún.

---

## 5. Riesgos no mitigables

### 5.1 El A/B test puede mostrar que no es tan dramático como el prototipo
El prototipo usó 575 skills y casos Cyn cuidadosamente elegidos. Sobre corpus completo podría haber casos donde los viejos eran mejores (ofertas de roles donde el label era suficiente y la description de ESCO es confusa).

**Si eso pasa:** el análisis de Fase 2 lo detectará antes de promocionar. Decidiríamos: (a) ajustar el texto enriquecido, (b) implementación selectiva (algunos ISCOs sí, otros no), (c) abortar.

### 5.2 Umbrales de código downstream calibrados contra embeddings viejos
- `DEFAULT_THRESHOLD = 0.40` en `skills_implicit_extractor`
- Reglas `V24-V30` en `validation_rules.json`
- Score expectations en tests
- Distribución de "trust_motivo" asume ciertos score ranges

**Mitigación:** tras Fase 3, re-medir y ajustar. Incluir en checklist post-promoción.

### 5.3 Dependencias no identificadas
Puede haber scripts/dashboards que leen directamente `esco_skills_metadata_full.json` y esperan el schema viejo.

**Mitigación:** búsqueda de referencias antes de Fase 3 (`grep -r "esco_skills_metadata"` en todo el proyecto).

---

## 6. Cronograma realista

**Propuesta escalonada:**

| Día | Trabajo | Estado al final del día |
|---|---|---|
| D1 | Fase 1 (dev 3h + exec 5min) + Fase 2 parte 1 (A/B script) | Embeddings nuevos en `enriched/`, A/B corrido automáticamente |
| D2 | Fase 2 parte 2 (sampling manual 2h) + GO/NO-GO | Decisión documentada |
| D3 | Fase 3 (promoción 1h) + Fase 4 Tanda 1 piloto (1 min + revisión 1h) | 100 ofertas retropropagadas, revisadas |
| D4 | Fase 4 Tanda 2 (10 min + revisión 30 min) | 1,000 ofertas retropropagadas |
| D5+ | Fase 4 Tanda 3 + 4 (en background) | 49K completo |

**Total humano:** ~7-10 horas efectivas distribuidas en 5 días.
**Total wall-clock:** 5 días con ventanas de revisión.

---

## 7. Go/no-go checklist

### Pre-implementación (ahora)
- [x] Datos RDF auditados y completos
- [x] LoRA no disponible — confirmado BGE-M3 base
- [x] Baselines existen para rollback
- [x] Prototipo valida approach (2026-04-24_E_FASE0_prototipo.md)
- [x] Tiempos medidos sobre BD real
- [ ] Revisión del spec por el usuario ← **estamos acá**

### Pre-Fase 1
- [ ] Rama git dedicada `feature/spec-e-embeddings-enriquecidos`
- [ ] Carpeta `enriched/` creada
- [ ] Scripts de Fase 1 escritos y tests unit pasan

### Pre-Fase 3 (promoción)
- [ ] A/B test reporta GO
- [ ] Gold set v2 sigue en 47/48
- [ ] Sanity check pasa (cargar extractor + procesar 1 oferta)
- [ ] Baselines copiados a `baselines/pre_spec_e_{fecha}.*`
- [ ] `grep -r "esco_skills_metadata"` confirma no hay dependencias ocultas

### Pre-Fase 4 (retropropagación)
- [ ] Backup de `skills_semantico_json` en tabla snapshot
- [ ] Script resumable con tabla de progreso
- [ ] Sync Supabase verificado compatible con nuevo schema

---

## 8. Recomendación

**Factibilidad: ALTA.** Todos los componentes están disponibles, los tiempos son razonables, los riesgos son identificables y mitigables, el approach gradual permite abortar en cualquier tanda.

**Mi sugerencia:**
- Arrancar por Fase 1 en rama dedicada.
- Dividir la sesión en 2 bloques: (1) Fase 1+2 (desarrollo + A/B automático) en un día, (2) Fase 3+4 piloto con revisión humana en otro día.
- NO promocionar a producción sin la revisión manual de Fase 2 aprobada por vos.

---

## 9. Preguntas abiertas antes de arrancar

1. **¿Rama git separada o seguimos en `main`?** Dada la magnitud, recomiendo rama `feature/spec-e-embeddings-enriquecidos` hasta Fase 3.

2. **¿Hacemos un checkpoint de BD antes de Fase 4?** El backup por tanda ya protege, pero un dump completo de `bumeran_scraping.db` antes de arrancar retropropagación da confianza extra. Costo: 2 GB duplicados en /tmp durante el proceso.

3. **¿Quién valida Fase 2?** La revisión manual de ~100 ofertas requiere ojo humano. ¿Vos? ¿Cyn también? Si son los dos, Cyn podría confirmar los casos metalúrgico/plástico.

4. **¿Pausar scraping durante Fase 3?** Recomendado. Son ~30 min de ventana segura.
