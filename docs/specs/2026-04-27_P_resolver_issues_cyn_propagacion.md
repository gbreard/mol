# SPEC P — Resolver issues Cynthia 2026-04-27 + propagación a casos similares

**Fecha:** 2026-04-27
**Autor:** Claude + Gerardo
**Estado:** Draft — listo para ejecutar
**Pre-condición:** SPEC N + O aplicados, sync grande Supabase completo
**Bloquea:** SPEC M (validación humana muestral)

---

## 1. Por qué este spec

Cynthia abrió 12 issues entre 24-04 y 27-04 con análisis detallado y propuestas concretas de target ESCO + skills correctas. Resolverlos uno por uno sin propagación implica:
- Cyn reportó 6 ofertas, pero hay decenas/cientos similares en BD que sufren los mismos errores.
- Resolver solo las reportadas deja el 99% del problema sin tocar.

Este spec resuelve **simultáneamente** los issues directos + propaga los fixes a todas las ofertas afectadas por las mismas reglas/patrones.

---

## 2. Categorías de problema detectados

Los 12 issues de Cyn se agrupan en 3 categorías:

### Categoría A — Reglas de matching con target incorrecto (3 reglas, ~150 ofertas afectadas)

| Regla | Target actual | Target Cyn | Justificación | Cobertura actual |
|---|---|---|---|---:|
| **R352_operario_ensamble_armas** | `7223.7 tornero` | **`7222.2 armero/armera`** | Aviso pide "Técnico armero" + ensamble pistolas. ESCO 7222.2 dice "armeros modifican y reparan armas de fuego". NO menciona torno/viruta. | 1 oferta (R352 cobertura baja) |
| **R349_operario_envasado** | `8183.1 línea envasado/embotellado` | **derivar a 9329.1 cuando es "habilidad manual" sin línea automatizada** | Aviso 6786905097 no tiene línea automatizada, solo tareas manuales. R240 (target 9329.1 trabajador fábrica) es mejor. | 119 ofertas |
| **R351_operario_despacho** | `9333.3 operario logística almacén` | **agregar caso especial → `8343.4 operador grúa producción` cuando aviso menciona puente grúa** | El despacho metalúrgico con grúa es operación de equipo pesado, no logística general. | 7 ofertas R351 + más en R353/R275 |

### Categoría B — Skills alucinadas por LLM no filtradas (6 ofertas Cyn + N propagación)

Ofertas matcheadas correctamente pero con skills absurdas (peces, javanés, sánscrito, psiquiatría, etc.) porque NO se re-procesaron con SPEC G+K.

**Ofertas Cyn directas:**
- 8299423434 (despacho metalúrgico)
- 6786905097 (habilidad manual papelera)
- 7879857202 (ensamble armas)
- 6866505508 (operarios depósito)
- 9255109063 (flex blow plásticos)
- 7907119232 (operario metalúrgico)

**Propagación esperada:** todas las ofertas validadas que NO pasaron por SPEC E retropro reciente Y tienen skills problemáticas. Estimación: identificar vía query (skills con L2 incompatible al ESCO específico).

### Categoría C — NLP mal en area_funcional (1 oferta Cyn + propagación)

`6866505508` tiene `area_funcional='Producción'` cuando debería ser `'Logística'` (Operarios de depósito).

**Causa probable:** regla NLP que asigna "Producción" como default para operarios. Necesita revisar `nlp_inference_rules.json`.

---

## 3. Plan por fases

### Fase 1 — Fixes de reglas (Categoría A)

#### 1.1 R352_operario_ensamble_armas (CAMBIO DE TARGET)
```json
"accion": {
  "forzar_isco": "7222",
  "esco_label": "armero/armera",
  "esco_code": "7222.2"
}
```

**Propagación:** identificar ofertas con título "ensamble de armas/pistolas" matcheadas a `7223.7 tornero` o cualquier otra regla. Re-rematch.

#### 1.2 R349_operario_envasado (REFINAR EXCLUSIÓN)
Agregar exclusión `titulo_no_contiene_alguno`: `["habilidad manual", "manualmente"]` cuando el aviso describe trabajo manual sin línea automatizada. O bajar prioridad para que R240 (9329.1 trabajador fábrica) gane.

**Investigación previa:** ver cuántas ofertas en R349 mencionan "habilidad manual" para evaluar si rompe casos buenos. Si <5%, aplicar exclusión.

#### 1.3 R351_operario_despacho — caso "metalúrgico + grúa"

**Opción A (preferida):** crear nueva regla `R358_despacho_metalurgico_grua` con prio -2 (gana sobre R351 prio -1):
```json
"R358_despacho_metalurgico_grua": {
  "nombre": "Despacho metalúrgico con puente grúa",
  "prioridad": -2,
  "condicion": {
    "titulo_original_contiene_alguno": [
      "despacho metalúrgico",
      "despacho metalurgico"
    ],
    "titulo_o_tareas_contiene_alguno": [
      "puente grua",
      "puente grúa",
      "manejo de grua",
      "manejo de grúa"
    ]
  },
  "accion": {
    "forzar_isco": "8343",
    "esco_label": "operador de grúa de instalaciones de producción/operadora de grúa de instalaciones de producción",
    "esco_code": "8343.4"
  }
}
```

**Opción B (más amplia):** crear regla genérica para cualquier rol con "puente grúa" en título/tareas → 8343.4. Más cobertura pero riesgo de pisar otras reglas.

**Recomendación:** Opción A (conservadora). Si después aparecen más casos de puente grúa mal codificados, ampliar a Opción B.

### Fase 2 — Identificar propagación (queries)

```sql
-- Ofertas con "ensamble de armas/pistolas" mal codificadas
SELECT id_oferta, titulo, esco_occupation_label, regla_aplicada
FROM ofertas_esco_matching JOIN ofertas USING(id_oferta)
WHERE LOWER(titulo) LIKE '%ensamble%arma%'
   OR LOWER(titulo) LIKE '%ensamble%pistola%'
   OR LOWER(titulo) LIKE '%armero%'
ORDER BY id_oferta;

-- Ofertas con "habilidad manual" mal codificadas a 8183
SELECT id_oferta, titulo, esco_occupation_label
FROM ofertas_esco_matching JOIN ofertas USING(id_oferta)
WHERE titulo_esco_code = '8183.1'
  AND (LOWER(titulo) LIKE '%habilidad manual%'
       OR LOWER(descripcion) LIKE '%habilidad manual%');

-- Ofertas con "despacho metalúrgico" + "puente grúa"
SELECT id_oferta, titulo
FROM ofertas o JOIN ofertas_esco_matching m USING(id_oferta)
WHERE LOWER(titulo) LIKE '%despacho metal%'
  AND (LOWER(o.descripcion) LIKE '%puente gr%' OR LOWER(o.descripcion) LIKE '%manejo de gr%');
```

Salida: `/tmp/spec_p_propagacion_ids.txt` con IDs únicos a re-rematch.

### Fase 3 — Re-rematch (Categoría A propagada)

Usar `scripts/embeddings/rematch_isco_spec_h.py --ids ...` con los IDs identificados en Fase 2. Tiempo: ~5 min para <500 ofertas.

### Fase 4 — Re-procesamiento de skills (Categoría B)

Las 6 ofertas Cyn + las identificadas en Fase 2 deben re-extraer skills aplicando SPEC G + K:

**Opción A (rápida):** usar el script de retropropagación SPEC E sobre los IDs específicos:
```bash
python scripts/embeddings/retropropagar_skills_spec_e.py --ids ID1,ID2,...
```

**Opción B (completa):** re-correr pipeline NLP+Skills+Matching:
```bash
python scripts/run_validated_pipeline.py --ids ID1,ID2,...
```

La A es más rápida y solo regenera skills (sin re-NLP). La B es más completa pero requiere unlock de validadas.

**Recomendación:** Opción A. La B se usa solo si Cyn reporta también problemas NLP (tareas mal, área mal).

### Fase 5 — Fix NLP area_funcional (Categoría C)

**Análisis:** revisar `config/nlp_inference_rules.json` para detectar regla que asigna "Producción" a operarios genéricos.

**Acción:** agregar override "Logística" para títulos que contengan "depósito", "almacén", "despacho" como predominante.

**Propagación:** re-procesar NLP de ofertas con `area_funcional='Produccion'` y título que dice "depósito/almacén/despacho". Estimación: 200-500 ofertas.

### Fase 6 — Cerrar issues Cyn

Para cada issue:
1. Verificar que el fix se aplicó (BD local + Supabase reflejan cambio).
2. UPDATE issue en Supabase:
```python
client.table('issues').update({
    'estado': 'resuelto',
    'resuelto_at': '2026-04-27T...',
    'solucion_aplicada': 'SPEC P fase X — descripción',
    'config_modificada': 'matching_rules_business.json (R352)'
}).eq('id', UUID).execute()
```

3. Generar training pair automático (`scripts/exports/generate_training_pairs.py` se dispara con sync_learnings.py).

### Fase 7 — Sync Supabase incremental

Después de Fases 1-5: `python scripts/exports/sync_to_supabase.py`. Tiempo: ~15-30 min según cuántas ofertas se tocaron.

---

## 4. Cronograma estimado

| Fase | Duración | Dependencias |
|---|---:|---|
| 1 — Fixes reglas (A) | 30 min | aprobación targets |
| 2 — Queries propagación | 10 min | Fase 1 |
| 3 — Re-rematch | 5-15 min | Fase 2 |
| 4 — Re-procesar skills | 30-60 min | Fase 3 |
| 5 — Fix NLP area | 20 min | independiente |
| 6 — Cerrar issues | 15 min | Fases 1-5 |
| 7 — Sync Supabase | 15-30 min | Fases 1-6 |
| **Total** | **~2-3 h** | secuencial |

---

## 5. Métricas de éxito

- ✅ 12 issues de Cynthia marcados como `resuelto`
- ✅ Re-rematch propaga fix a >0 ofertas similares (al menos 5-10 por regla)
- ✅ Re-extracción skills aplica SPEC G+K (skills alucinadas reducen >70% en las re-procesadas)
- ✅ Tests Gold Set v2 pasan post-fix (regresión)
- ✅ Sync Supabase sin errores

---

## 6. Riesgos

### 6.1 Cambio R352 rompe otros casos
R352 tiene baja cobertura (1 oferta), riesgo bajo. Pero "ensamble de armas" puede coincidir con otros oficios metalúrgicos no relacionados con armas reales (ej: ensamble de muebles).

**Mitigación:** verificar con query de propagación que solo ataca ofertas reales de armería.

### 6.2 Exclusión "habilidad manual" en R349 deja casos de envasado real fuera
Algunas ofertas legítimas de envasado pueden mencionar "habilidad manual" como soft skill.

**Mitigación:** condición más estricta — agregar también "papelera/papel" o "manualmente" + ausencia de "línea/maquinaria".

### 6.3 Nueva regla R358 puede pisar R351/R275
Misma prioridad → R358 prio -2 vs R351 prio -1, R358 gana. Pero si la oferta dice "operario despacho" sin metalúrgico, R351 sigue ganando.

**Mitigación:** test con ofertas reales antes de aplicar.

### 6.4 Re-procesar skills puede afectar ofertas validadas
Trigger `protect_validated_matching` puede bloquear updates.

**Mitigación:** usar script `unlock_spec_h.py` para batch específico antes de re-procesar.

### 6.5 Fix NLP area_funcional retrosurge en otras ofertas
Cambiar inferencia de área puede afectar ofertas que SÍ son Producción legítima.

**Mitigación:** test con muestra de 20 ofertas antes de aplicar masivamente.

---

## 7. Decisiones inmediatas para arrancar

1. **¿Aprobás los 3 cambios de target/regla?**
   - R352 → 7222.2 armero
   - R349 → exclusión "habilidad manual"
   - R358 (nueva) → 8343.4 grúa producción para "despacho metalúrgico + grúa"

2. **¿Re-procesar skills (Fase 4) Opción A o B?**
   - A: solo skills (script SPEC E retropro) — más rápido, no toca NLP
   - B: pipeline completo NLP+Skills+Matching — más profundo, más lento

3. **¿Aplicar fix NLP area_funcional (Fase 5) en este spec o spec separado?**
   - Si en este spec: arreglamos issue 6866505508 NLP completo
   - Spec separado: queda pendiente, pero issue Cyn no queda 100% cerrado

4. **¿Sync Supabase incremental al final, o esperar a tener más cambios?**
   - Ahora: dashboard refleja inmediatamente
   - Esperar: agrupar con futuros cambios para reducir ciclos

---

## 8. Lo que este spec NO hace

- NO crea Catálogo MOL Argentino (ese es proyecto separado, ver `docs/plan/15_PERFILES_POLIVALENTES_AR.md`).
- NO toca el matcher (`match_ofertas_v3.py`) ni el skills extractor (`skills_implicit_extractor.py`).
- NO re-genera embeddings ESCO.
- NO sustituye SPEC M (validación humana muestral) — al contrario, lo libera de los 12 casos ya conocidos.
