# SPEC O — Detección sistémica de problemas de codificación post-SPEC N

**Fecha:** 2026-04-26
**Autor:** Claude + Gerardo
**Estado:** Draft — para alinear antes de ejecutar
**Pre-condición:** SPEC E+G+H+J+K+L+N aplicados. Bug `persist_matching_result` corregido. 6,628 ofertas re-matcheadas con todos los campos coherentes.
**Bloquea:** Sync grande Supabase.

---

## 1. Por qué este spec

En SPEC N nos enfocamos en operarios mal codificados a `8160.35 prensado de fruta` (target absurdo). Al investigar, descubrimos efectos secundarios:

| Hallazgo | Origen del problema |
|---|---|
| R240 → `8160.35 prensado fruta` | Target absurdo: regla genérica → ESCO ultra-específico |
| R301 captura "autoelevador" | `"elevador"` como substring sin exclusiones |
| R351 → `4321.1 coordinador inventario` | Target administrativo para rol manual |
| R351 vs R353 vs R275 | Reglas redundantes/superpuestas con targets distintos |
| Bug `persist_matching_result` | Solo persistía 9 columnas, dejando 7 huérfanas |

Hipótesis fuerte: **estos no son casos aislados, son patrones**. Si los buscamos sistemáticamente vamos a encontrar más reglas con los mismos defectos. Antes de syncear queremos cerrar los más visibles.

Pero **no podemos revisar las 348 reglas a mano** ni las 52,548 ofertas. Necesitamos un proceso dirigido por señales cuantitativas.

---

## 2. Scope

### Universo
- 348 reglas activas en `matching_rules_business.json`
- 52,548 ofertas validadas en `ofertas_esco_matching`
- ~3,045 ocupaciones ESCO con `esco_code`

### Lo que SÍ hace este spec
- Detectar reglas con defectos estructurales (target absurdo, substring trampa, redundancia)
- Detectar ofertas mal codificadas detectables sin lectura humana caso por caso
- Producir reporte priorizado de hallazgos
- Aplicar fixes triviales automáticamente
- Escalar fixes complejos a Gerardo (no a Cyn/Diego — ese es SPEC M)

### Lo que NO hace
- NO revisar todas las reglas una por una
- NO hacer validación humana caso por caso (eso es SPEC M)
- NO fine-tuning de modelos
- NO modificar el matcher

---

## 3. Métodos de detección

Cada método produce una lista priorizada de candidatos. Aplicamos el método, juntamos hallazgos, deduplicamos, priorizamos por severidad.

### M1 — ESCO codes ultra-específicos con alta cobertura

**Hipótesis:** una regla genérica que manda 100+ ofertas a un esco_code de 3+ niveles (`X.Y.Z` o `X.Y.Z.W`) probablemente está usando ese código como fallback.

**Query:**
```sql
SELECT titulo_esco_code, esco_label, regla_aplicada, COUNT(*) as n
FROM ofertas_esco_matching
WHERE titulo_esco_code LIKE '%.%.%'  -- 3+ niveles
  AND regla_aplicada IS NOT NULL
GROUP BY titulo_esco_code
HAVING n >= 50
ORDER BY n DESC
```

**Severidad:** **Alta**. Ejemplo conocido: `8160.35 prensado de fruta` con 1,336 ofertas — eso ya lo arreglamos pero pueden haber otros como `8131.20`, `7223.4.4.1`, `9333.8.1`, `3115.1.6`.

**Criterio de problema:** mirar el label vs los títulos típicos de la regla. Si la regla se llama "operario X" y el target es "responsable de pedidos de almacén/responsable de", probablemente está mal.

**Acción:** revisar regla, posiblemente cambiar target a un nivel más genérico (X.Y.W estándar de la familia).

---

### M2 — Substrings trampa en `titulo_contiene_alguno`

**Hipótesis:** términos cortos genéricos sin exclusiones matchean palabras compuestas problemáticas.

**Query:** parsear `matching_rules_business.json`, para cada regla con `titulo_contiene_alguno`, identificar términos cortos (≤9 chars):
- `"elevador"` → atrapa "autoelevador" (R301 ya arreglado)
- `"control"` → atrapa "controlador", "control de stock"
- `"chofer"` → atrapa "chofer" en cualquier contexto
- `"asistente"` → atrapa muchos roles
- `"operador"` → atrapa "operador IT" vs "operador maquinaria"
- `"técnico"` → atrapa miles de variantes

**Criterio de problema:** la regla NO tiene `titulo_no_contiene_alguno` con las palabras compuestas problemáticas obvias.

**Severidad:** **Alta** si la regla apunta a un ESCO muy distinto al rol genérico (ej: técnico ascensores capturando técnico mecánico).

**Acción:** agregar exclusiones específicas.

---

### M3 — Reglas con `dual_coinciden=0` masivo

**Hipótesis:** si una regla aplica pero el semántico (ESCO embedding) está siempre en otra dirección, la regla está pisando ocupaciones más pertinentes.

**Query:**
```sql
SELECT regla_aplicada,
       SUM(dual_coinciden) as concuerdan,
       SUM(CASE WHEN dual_coinciden=0 THEN 1 ELSE 0 END) as difieren,
       COUNT(*) as total,
       CAST(SUM(CASE WHEN dual_coinciden=0 THEN 1 ELSE 0 END) AS REAL)/COUNT(*) as tasa_diferencia
FROM ofertas_esco_matching
WHERE regla_aplicada IS NOT NULL
  AND dual_coinciden IS NOT NULL
GROUP BY regla_aplicada
HAVING total >= 20 AND tasa_diferencia >= 0.5
ORDER BY tasa_diferencia DESC, total DESC
```

**Criterio de problema:** tasa_diferencia ≥ 50% indica que la regla y el semántico discrepan en mayoría. Inspeccionar manualmente top 10.

**Severidad:** **Media**. Puede ser que la regla está corrigiendo bien (ej: matching argentino vs ESCO genérico). O puede estar pisando.

**Acción:** caso por caso. Si la regla es pertinente, dejar. Si no, ajustar target.

---

### M4 — Reglas con cobertura alta + target inconsistente

**Hipótesis:** reglas que aplican a 500+ ofertas pero su `esco_label` es ultra-específico o suena distinto al `nombre` de la regla.

**Query:**
```sql
SELECT regla_aplicada, esco_label, COUNT(*) as n
FROM ofertas_esco_matching
WHERE regla_aplicada IS NOT NULL
GROUP BY regla_aplicada
HAVING n >= 500
ORDER BY n DESC
```

**Cruzar con JSON:** comparar `nombre` de la regla vs `esco_label` del target. Si difieren mucho, sospechoso.

**Severidad:** **Media-Alta** según la diferencia.

**Acción:** revisar manual top 10.

---

### M5 — Targets duplicados entre reglas (redundancia)

**Hipótesis:** múltiples reglas que apuntan al mismo `esco_code` con condiciones superpuestas — probablemente algunas son obsoletas o pisan otras.

**Query:** parsear JSON, agrupar reglas por `esco_code` target. Si dos+ apuntan al mismo y sus condiciones se superponen (compartiendo términos), candidatas a consolidación.

**Severidad:** **Baja**. No causa miscoding, solo desorden.

**Acción:** consolidar reglas o documentar diferencias intencionales.

---

### M6 — Issues abiertos en Supabase tabla `issues`

**Query:**
```python
client.table('issues').select('*').in_('estado', ['pendiente', 'en_progreso']).execute()
```

**Filtrar:** issues de Cyn/Diego con `tipo` relacionado a matching/ESCO.

**Severidad:** **Variable** (la define el issue).

**Acción:** atender uno por uno (el flujo issue → fix → training_pair ya existe).

---

### M7 — Score semántico bajo con regla aplicada

**Hipótesis:** cuando `regla_aplicada` no es NULL pero `score_semantico < 0.4`, la regla está tapando un match débil. La regla puede estar bien (corrigiendo) o mal (forzando algo equivocado).

**Query:**
```sql
SELECT regla_aplicada, COUNT(*) as n,
       AVG(score_semantico) as score_prom
FROM ofertas_esco_matching
WHERE regla_aplicada IS NOT NULL
  AND score_semantico < 0.4
GROUP BY regla_aplicada
HAVING n >= 30
ORDER BY n DESC
```

**Severidad:** **Baja-Media**. Casos sospechosos para revisión manual de muestra.

---

## 4. Criterios de severidad y triage

| Nivel | Criterio | Acción |
|---|---|---|
| **🔴 Crítica** | Target absurdo (8160.35) afectando >100 ofertas, o substring trampa con falso positivo claro | Fix inmediato + re-rematch |
| **🟠 Alta** | Tasa de incoherencia ≥50% en regla con cobertura ≥50 | Investigar, fix si confirmado |
| **🟡 Media** | Reglas duplicadas o con cobertura alta y target ambiguo | Revisar, decidir consolidación |
| **🟢 Baja** | Casos individuales o de bajo volumen | Documentar, atender en batches |

---

## 5. Proceso por hallazgo

```
1. Detectar    → query produce candidatos
2. Inspeccionar → leer 5-10 ejemplos manualmente
3. Diagnosticar → bug en regla / target malo / falsa alarma?
4. Decidir     → fix? consolidar? dejar?
5. Aplicar fix → editar JSON / DB
6. Propagar    → re-rematch ofertas afectadas
7. Verificar   → query post-fix muestra resultado esperado
8. Documentar  → linaje en _linaje del JSON
```

---

## 6. Plan de ejecución por fases

### Fase 1 — Detección (paralela, ~30 min)
Ejecutar M1 + M2 + M3 + M4 + M7 en paralelo. Generar reportes por método en `/tmp/spec_o_*.csv`.

### Fase 2 — Triage (manual, ~30 min)
Claude lee los reportes, identifica hallazgos críticos/altos, propone plan al usuario.

### Fase 3 — Aprobación (5-10 min)
Usuario valida cuáles fixes aplicar. Decisiones binarias por hallazgo.

### Fase 4 — Aplicación (~1-2 h)
Por cada fix aprobado:
- Editar regla JSON
- Re-rematch ofertas afectadas
- Verificar resultado

### Fase 5 — Integración con SPEC M
Si quedan casos ambiguos que requieren juicio humano, pasarlos a Cyn/Diego en el batch de validación SPEC M.

### Fase 6 — Sync grande
Cuando todo lo detectable está cerrado.

**Total wall-clock:** ~3 horas (sin contar SPEC M).

---

## 7. Riesgos y mitigaciones

### 7.1 Falsos positivos
M1 puede flaggear targets ultra-específicos legítimos (ej: 7223.4.4.1 programador CNC tiene sentido).
**Mitigación:** revisar manual antes de aplicar fix. Solo fix si target NO refleja el rol.

### 7.2 Cascada de cambios
Cada fix puede afectar otras reglas (como pasó con R301 → R3 autoelevador, R275, etc.).
**Mitigación:** después de cada fix, re-correr detección sobre la región afectada.

### 7.3 Degradación
Un fix mal aplicado puede romper más casos de los que arregla.
**Mitigación:** test pre/post sobre Gold Set referencia (49 casos) + verificación de regla sobre muestra de 5-10 ofertas.

### 7.4 No converger
Cada round de fix puede revelar nuevos problemas (efecto cebolla).
**Mitigación:** fijar 2-3 rondas máximo. Si después de eso quedan casos, archivar como "límites del sistema" y avanzar.

---

## 8. Lo que este spec NO hace

- NO revisa reglas no afectadas por las queries (las que aplican a 1-20 ofertas y son específicas)
- NO sustituye la validación humana de SPEC M (eso es muestral y dirigido)
- NO toca el matcher, ESCO embeddings, ni los modelos
- NO se pelea con casos donde el dataset ESCO no tiene buena ocupación (límites estructurales)

---

## 9. Decisiones inmediatas para arrancar

Necesito que confirmes:

1. **¿Arrancamos con los 7 métodos o subset?**
   Recomendado: M1 + M2 + M3 (alto rendimiento, bajo costo). M4-M7 después si quedan ganas.

2. **Umbrales de detección.** Los del spec son default (n≥50, tasa≥50%). ¿Más estrictos? ¿Más laxos?

3. **¿Aplicar fixes triviales sin pedir aprobación caso por caso?**
   Trivial = agregar exclusión obvia (ej: `"autoelevador"` cuando ya identificamos el bug). Riesgosos = cambio de target (te consulto siempre).

4. **¿Dónde paramos?** Recomendado: después de 2 rondas de detección+fix, syncear. Sin perfeccionismo.

5. **Cobertura mínima de ofertas para considerar un fix.**
   Recomendado: ≥30. Por debajo, dejarlo para SPEC M (validación humana).

---

## 10. Output esperado

Al terminar SPEC O:
- 5-15 reglas auditadas y posiblemente refinadas
- 500-3,000 ofertas re-matcheadas
- 1 reporte de hallazgos `/tmp/spec_o_reporte.md`
- 0 problemas detectables sin lectura humana caso por caso
- Lista corta de casos ambiguos para SPEC M
- Confianza para syncear
