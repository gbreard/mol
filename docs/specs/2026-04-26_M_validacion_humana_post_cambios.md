# SPEC M — Validación humana de la reclasificación post SPEC E+G+H+J+K

**Fecha:** 2026-04-26
**Autor:** Claude + Gerardo
**Estado:** Draft — listo para ejecutar
**Audiencia primaria:** Cynthia, Diego (analistas)
**Pre-condición:** SPEC E+G+H+J+K aplicados en BD local. **Sync grande Supabase NO ejecutado todavía** — la BD local tiene los cambios pendientes de subir.
**Output esperado:** lista de issues / decisiones documentadas que guíen ajustes finos antes del sync.

---

## 1. Por qué este spec

Tras una cadena de cambios sistémicos (embeddings enriquecidos, rematch ESCO, migración de reglas a esco_code, filtros de skills, etc.), **3,315 ofertas (9.7%) cambiaron de ocupación ESCO** y **5,272 ofertas tuvieron rematch directo**. Antes de syncar a producción Supabase, queremos confirmar empíricamente que los cambios son **mejoras reales** y no introducen regresiones.

La validación humana es **muestral, dirigida y con criterios claros**, no exhaustiva.

---

## 2. Scope de revisión

### Universo
- 52,548 ofertas validadas
- 3,315 con cambio de ISCO 4-dig
- 5,272 ofertas con rematch SPEC H

### Muestra propuesta: **80-100 ofertas**
Cubrir 4 tiers de prioridad:

| Tier | Tipo | ISCOs afectados | Ofertas a revisar |
|---|---|---|---:|
| **1** | ISCOs que más se vaciaron (potenciales "fallbacks" antes) | 1349, 1431, 3435, 3123, 5223 | 10 c/u = **50** |
| **2** | Cambios % dramáticos (muestra chica → variabilidad alta) | 5246, 7127, 3251, 5165, 2633 | 5 c/u = **25** |
| **3** | ISCOs que más crecieron (validar que ganaron lo correcto) | 1221, 1420, 3512 | 5 c/u = **15** |
| **4** | (Opcional) Estables, control negativo | 7231, 5120, 8322 | 3 c/u = 9 |

**Total: 90 ofertas (sin tier 4) o 99 (con).**

---

## 3. Proceso de revisión — paso a paso

### Paso 1: el spec genera la lista de IDs

Claude ejecuta `scripts/embeddings/generate_validation_sample.py` (a crear). Output: `/tmp/spec_m_sample.csv` con columnas:

```
id_oferta | titulo | tier | isco_antes | esco_label_antes | isco_despues |
esco_label_despues | esco_code_nuevo | regla_aplicada | url_admin
```

### Paso 2: el validador abre el archivo

Cyn / Diego abren el CSV en LibreOffice o Google Sheets. Lo más práctico: importarlo a una hoja con columnas adicionales editables:

```
| ... datos del paso 1 ... | resultado | comentario | issue_creado |
```

### Paso 3: para cada oferta, la persona...

1. Va al admin del dashboard (`/admin/validacion?id=XXXX`) — el sistema muestra título, descripción, tareas.
2. Lee el aviso real.
3. Compara con la asignación nueva (esco_label nuevo).
4. Compara con la asignación vieja (esco_label antes) si tiene contexto.
5. Marca en la columna `resultado` uno de:
   - **`OK`**: el nuevo está bien
   - **`MEJORA`**: el nuevo es claramente mejor que el viejo
   - **`PEOR`**: el nuevo es peor que el viejo (regresión)
   - **`AMBOS_MAL`**: ni el nuevo ni el viejo son correctos (caso difícil para el sistema)
   - **`DUDOSA`**: no estoy seguro
6. (Opcional) Comentario: explicar el problema.
7. Si es `PEOR` o `AMBOS_MAL`, crear issue en Supabase tabla `issues` con prioridad alta.

### Paso 4: tiempo estimado por persona

- 90 ofertas × 90 segundos cada una = **~135 minutos**
- Distribuible entre Cyn (50) + Diego (40) o como prefieran

---

## 4. Datos que el reporte muestra por oferta

```
[1118098190]  "Líder de arquitectura y gobierno de datos"
  Tier:           1 (vaciado)
  Antes:          ISCO 2511 — ingeniero de datos (score 0.85)
  Después:        ISCO 2521 — administrador de bases de datos (score 0.63)
  esco_code:      2521.1
  Regla aplicada: (ninguna, fue semántico)
  Fuente cambio:  SPEC H
  URL admin:      https://mol-nextjs.vercel.app/admin/validacion?id=1118098190

  Tareas (resumen):
   - Diseñar arquitectura cloud del data warehouse
   - Liderar equipo de data engineering
   - Definir gobierno de datos
```

---

## 5. Cómo se interpretan los resultados

### Métricas a calcular tras la validación

```
Total revisadas: N
Aceptadas (OK + MEJORA): A (%)
Regresiones (PEOR): P (%)
Casos difíciles (AMBOS_MAL): D (%)
Dudosas: U (%)
```

### Acciones según resultados

| Métrica | Acción |
|---|---|
| `MEJORA + OK ≥ 80%` | **Sync grande adelante**. Sistema mejoró sustancialmente. |
| `MEJORA + OK 60-80%` | **Sync con caveat**. Documentar en learnings que hay X% de casos a revisar caso por caso. |
| `MEJORA + OK < 60%` | **NO syncar**. Detectar patrones en los `PEOR` y arreglar antes. |
| `AMBOS_MAL > 20%` | Hay un dominio donde ESCO no funciona bien. Documentar como límite del sistema. |
| `PEOR > 10%` | Investigar regresiones. Identificar si vienen de algún spec específico (E, H, J, K) y mitigarlo. |

### Issues como retroalimentación

Cada issue creado por Cyn/Diego se archiva en Supabase tabla `issues` siguiendo el flujo ya existente:

```
{
  "tipo": "matching_post_spec_eghjk",
  "id_oferta": "1118098190",
  "valor_actual": "ISCO 2521 — administrador de bases de datos",
  "valor_esperado": "ISCO 2511 — ingeniero de datos",
  "descripcion": "El cambio de SPEC H rebajó el rol; este es claramente arquitecto/lider, no admin BD",
  "prioridad": "alta",
  "autor": "Cynthia"
}
```

Esos issues alimentan training_pairs para fine-tuning futuro (pipeline ya existente en `scripts/sync_learnings.py`).

---

## 6. Implementación técnica

### Script `scripts/embeddings/generate_validation_sample.py`

Genera el CSV de muestra:
1. Conecta BD local
2. Para cada tier definido, selecciona N ofertas con cambio de ISCO
3. Para cada oferta, recupera del backup `ofertas_matching_backup_spec_h` los datos pre-cambio
4. Construye URL admin según convención del dashboard
5. Exporta CSV a `/tmp/spec_m_sample.csv`

Tiempo de implementación: **30 minutos**.

### Vista en dashboard (opcional, si Cyn/Diego prefieren UI sobre CSV)

Crear ruta `/admin/validacion-spec-m` que:
- Muestra una oferta a la vez
- Tiene botones OK / MEJORA / PEOR / AMBOS_MAL / DUDOSA
- Captura comentario
- Genera issue si corresponde
- Pasa a la siguiente oferta

Tiempo de implementación: **3-4 horas**.

**Recomendación**: empezar con CSV (rápido) y, si funciona el flujo, después armar la vista. La revisión es one-time, no justifica una UI dedicada de entrada.

---

## 7. Cronograma propuesto

| Día | Acción | Ejecutor |
|---|---|---|
| **D1 mañana** | Claude: implementar script de muestra. Generar `/tmp/spec_m_sample.csv` | Claude |
| **D1 tarde** | Cyn revisa Tier 1 (50 ofertas) | Cyn |
| **D1 tarde** | Diego revisa Tier 2 + 3 (40 ofertas) | Diego |
| **D2 mañana** | Claude consolida resultados, genera reporte de issues | Claude |
| **D2 mañana** | Decisión sync vs ajuste según métricas | Gerardo |
| **D2 tarde** | Sync grande (si OK) o iteración (si NO) | Claude |

**Total wall-clock: 1.5-2 días.**

---

## 8. Lo que este spec NO hace

- NO espera revisar las 52K validadas. Solo muestra de 90.
- NO bloquea sync indefinidamente. Si la métrica es buena, sync prosigue.
- NO requiere conocimiento técnico de los validadores — solo "este aviso es de tipo X o Y, ¿cuál es correcto?"
- NO sustituye fine-tuning futuro. Los issues alimentan training_pairs.

---

## 9. Riesgos

### 9.1 Cyn/Diego no tienen 2-3h
Mitigación: bajar muestra a 50 ofertas (Tier 1+2 sin Tier 3). Igualmente da señal estadística.

### 9.2 Validadores discrepan entre sí
Mitigación: si un mismo ISCO tiene >2 PEOR, escalar a Gerardo para resolución.

### 9.3 La muestra no es representativa
Mitigación: el sampling es estratificado por tier. Si igualmente hay grupos muy chicos sin cubrir, agregar 5-10 ofertas más en una segunda iteración.

### 9.4 La revisión revela problema sistémico (>30% PEOR)
Mitigación: NO syncar. Volver a SPEC H/J y endurecer (ej. política E del SPEC H más estricta, agregar más reglas a SPEC J).

---

## 10. Decisión inmediata

¿Procedemos con SPEC M? Si sí:
1. Claude genera `scripts/embeddings/generate_validation_sample.py` y CSV
2. Compartimos el CSV con Cyn/Diego
3. Esperamos su feedback (2-3h máximo)
4. Decidimos: sync o iteración

Si querés saltarlo y syncar directo (confiando en los datos cuantitativos ya medidos: +28% score, +9pp coherencia, etc.), también es válido.
