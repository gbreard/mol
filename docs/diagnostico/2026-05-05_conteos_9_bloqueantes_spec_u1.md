# Conteos 9 — Resolución de 4 bloqueantes pre-SPEC U-1 v3

**Fecha:** 2026-05-05
**Pipeline activo:** no (no hay procesos `run_validated_pipeline` / `process_nlp` / `match_ofertas` corriendo)
**Modo:** READ-ONLY estricto (`?mode=ro`); no se ejecutó el matcher; no se ejecutó el UPDATE real de C4 (sólo `EXPLAIN QUERY PLAN`).
**Tiempo total:** ~50 min
**Output destino solicitado:** `docs/diagnostico/2026-05-05_conteos_9_bloqueantes_spec_u1.md` (este archivo). Mirror a `/mnt/user-data/outputs/` no posible (filesystem inaccesible — mismo blocker que reportes anteriores).

---

## Resumen ejecutivo

| Bloqueante | Estado tras este reporte | Contenido a llevar al SPEC v3 |
|---|---|---|
| **A. Heurística URI por contexto** | Resuelto con asterisco | 8/11 contextos elegibles automáticamente por frecuencia + keyword. **3/11 requieren decisión humana**. |
| **B. SQL de C4** | SQL ejecutable (validado vía `EXPLAIN QUERY PLAN`). Estimación realista. | SQL listo para correr; ETA 5-30 min con índices existentes. |
| **C. Label drift en 3 entradas isco_primario** | Resuelto, decisión por entrada propuesta. | 3 cambios en JSON: 1 cambio de ISCO + 2 sustituciones de label canónico. |
| **D. Criterio zombie Supabase** | Re-definido. **El conteo "28.395 zombies" del SPEC es probablemente artefacto de backlog de sync, no zombies reales**. | Cambio crítico de orden: PRIMERO sync, LUEGO recontar, LUEGO DELETE. |

**Hallazgo colateral más importante:** local tiene **56.397 ofertas validadas** pero Supabase tiene "16K+" según CLAUDE.md. **Drift de ~40K ofertas no sincronizadas**. El último sync exitoso en `config/supabase_sync_log.json` fue **2026-04-28** y desde entonces hubo nuevas validaciones (última `validado_timestamp` = 2026-04-30). El backlog histórico del log muestra que ofertas se subieron en lotes irregulares; el conteo total acumulado en Supabase no llega ni cerca a 56K.

---

## A — Heurística de selección de URI para contextos

### A1. Listado de los 11 contextos pendientes (Opción 3 SPEC v2 §5.3)

| # | Entrada | Contexto (regex) | ISCO declarado | Notas del JSON |
|---|---|---|---|---|
| 1 | gerente | `ventas\|comercial` | 1221 | sin esco_label declarado |
| 2 | gerente | `finanzas\|financiero` | 1211 | — |
| 3 | gerente | `operaciones\|planta\|produccion` | 1321 | — |
| 4 | gerente | `rrhh\|recursos humanos` | 1212 | — |
| 5 | gerente | `it\|sistemas\|tecnologia` | 1330 | — |
| 6 | gerente | `marketing` | 1221 | **ISCO duplicado con #1** |
| 7 | gerente | `logistica\|supply chain` | 1324 | — |
| 8 | operador | `atencion\|atención\|cliente\|call center\|telefonico\|telefónico` | 4222 | — |
| 9 | operador | `almacen\|almacén\|deposito\|depósito\|logistica\|logística` | 9333 | — |
| 10 | operador | `produccion\|producción\|planta\|fabrica\|fábrica` | 8160 | — |
| 11 | operador | `maquinas\|máquinas\|cnc\|torno` | 8211 | **ver A4 — ISCO problemático** |

### A2. Candidatos por contexto en `esco_occupations` (top hist por ISCO)

Lookup con prefijo `'C'` sobre `isco_code`. Conteos `n_hist` desde `ofertas_esco_matching`.

#### #1 gerente.ventas|comercial (C1221, 16 candidatos)
| URI (último segmento) | Label | n_hist |
|---|---|---:|
| dc97adbe-… | responsable de marketing digital | 252 |
| a7594892-… | director de ventas/directora de ventas | **251** |
| d954fd71-… | director de promoción/directora de promoción | 174 |
| 6fcf4638-… | responsable de marketing | 171 |
| 2d3d7188-… | director comercial/directora comercial | 95 |
| (otros 11 candidatos con hist ≤11) | — | — |

#### #2 gerente.finanzas|financiero (C1211, 5 candidatos)
| URI | Label | n_hist |
|---|---|---:|
| 30f3ea93-… | **director financiero/directora financiera** | **177** |
| 04f39bfa-… | director de contabilidad/… | 10 |
| b680251e-… | tesorero de banco/… | 7 |
| 3e1a2f3c-… | tesorero de empresa/… | 3 |
| 44e0c015-… | director de presupuesto/… | 2 |

#### #3 gerente.operaciones|planta|produccion (C1321, 21 candidatos)
| URI | Label | n_hist |
|---|---|---:|
| eb9479c6-… | **director de producción industrial/…** | **227** |
| fdb16700-… | director de control de calidad en industrias/… | 96 |
| 6426ada1-… | director de fabricación/… | 26 |
| (otros con hist ≤5) | — | — |

#### #4 gerente.rrhh|recursos humanos (C1212, 6 candidatos)
| URI | Label | n_hist |
|---|---|---:|
| f605bcd2-… | **director de recursos humanos/…** | **131** |
| a14e96a7-… | director de formación en empresas/… | 48 |
| 949ab84f-… | responsable de igualdad e inclusión | 18 |
| (otros con hist ≤10) | — | — |

#### #5 gerente.it|sistemas|tecnologia (C1330, 13 candidatos)
| URI | Label | n_hist |
|---|---|---:|
| 8b6388a4-… | **gestor de proyectos de TIC/gestora de proyectos de TIC** | **104** |
| 719f101d-… | gestor de la transformación digital/… | 29 |
| f0ca39a8-… | gestor de operaciones de TIC/… | 16 |
| 7b1b5da8-… | director de tecnología/directora de tecnología | 14 |
| (otros con hist ≤8) | — | — |

#### #6 gerente.marketing (C1221, **mismos 16 candidatos** que #1)
| URI | Label | n_hist |
|---|---|---:|
| dc97adbe-… | **responsable de marketing digital** | **252** |
| 6fcf4638-… | responsable de marketing | 171 |
| 0ddbf393-… | director de marketing/directora de marketing | 11 |

#### #7 gerente.logistica|supply chain (C1324, 90 candidatos — **ISCO genérico amplio**)
| URI | Label | n_hist |
|---|---|---:|
| 632e61c8-… | director de distribución/… | 71 |
| 2f5de1ab-… | jefe de almacén/… | 50 |
| aacc3918-… | **director de la cadena de suministro/…** | **40** |
| 377865f0-… | director de compras/… | 35 |
| a2ff6cc3-… | director de logística intermodal/… | 11 |
| 823db06f-… | director de distribución y logística/… | 8 |
| (otros 84 candidatos con hist ≤5) | — | — |

#### #8 operador.atencion|cliente|call center (C4222, 2 candidatos)
| URI | Label | n_hist |
|---|---|---:|
| b7b75eb6-… | **agente de centro de atención al cliente** | **841** |
| fde97584-… | agente de atención al cliente por chat | 6 |

#### #9 operador.almacen|deposito|logistica (C9333, 9 candidatos)
| URI | Label | n_hist |
|---|---|---:|
| bea705fe-… | **mozo de almacén/moza de almacén** | **962** |
| 808becc8-… | operario de logística de almacén/… | 325 |
| cd94def5-… | responsable de pedidos de almacén | 12 |
| (otros con hist ≤8) | — | — |

#### #10 operador.produccion|planta|fabrica (C8160, 55 candidatos — **ISCO específico de alimentos**)
| URI | Label | n_hist |
|---|---|---:|
| 7235d075-… | operario de prensado de fruta/… | 171 |
| e3dc66de-… | **operario de producción de alimentos/operaria de producción de alimentos** | **21** |
| 2a2da883-… | operador de refrigeración de alimentos/… | 17 |
| (otros 52 con hist ≤10) | — | — |

#### #11 operador.maquinas|cnc|torno (C8211, 11 candidatos — **TODOS son montadores, ninguno es operador de torno**)
| URI | Label | n_hist |
|---|---|---:|
| be0e6189-… | montador de motores náuticos/… | 19 |
| 1a6d1acf-… | montador en mecatrónica/… | 2 |
| ad7c76e8-… | montador de aeronaves/… | 1 |
| (otros 8 montadores con hist ≤1) | — | — |

→ **El ISCO 8211 declarado en JSON parece estar mal**: 8211 ESCO es "montadores de maquinaria mecánica" no "operadores de máquinas-herramienta". Operador de CNC/torno encajaría en 7223 ("operadores de máquinas-herramienta") o 8121 ("operadores de instalaciones de procesamiento de metales"). **Decisión humana requerida**: cambiar ISCO o quitar este contexto.

### A3. Heurística aplicada — selección final

Reglas (en orden):

1. **Por keyword en label**: si una URI contiene una palabra del contexto en su label.
2. **Por frecuencia histórica**: dentro de los matches por keyword, la de mayor `n_hist`.
3. **Default `.1` ESCO**: no aplicable porque BD no tiene esa convención (todas las URIs son UUID y los `esco_code` no siempre tienen `.1`).
4. **Decisión humana**: si la heurística no decide, o si el ISCO declarado parece erróneo.

| # | Entrada | Contexto | URI seleccionada (segmento) | Label | Heurística | Confianza |
|---|---|---|---|---|---|---|
| 1 | gerente | ventas\|comercial | a7594892-… | director de ventas | keyword "ventas" + freq | **alta** |
| 2 | gerente | finanzas\|financiero | 30f3ea93-… | director financiero | keyword "financiera" + freq | **alta** |
| 3 | gerente | operaciones\|planta\|produccion | eb9479c6-… | director de producción industrial | keyword "producción" + freq | **alta** |
| 4 | gerente | rrhh\|recursos humanos | f605bcd2-… | director de recursos humanos | keyword "recursos humanos" + freq | **alta** |
| 5 | gerente | it\|sistemas\|tecnologia | 8b6388a4-… | gestor de proyectos de TIC | freq dominante (104 vs 29) | **media** (alternativa: "director de tecnología" 14 hist) |
| 6 | gerente | marketing | dc97adbe-… | responsable de marketing digital | keyword "marketing" + freq | **media-alta** (alternativa: "director de marketing" 11 hist; ver E1) |
| 7 | gerente | logistica\|supply chain | aacc3918-… | director de la cadena de suministro | keyword "supply chain" / "cadena suministro" | **media** (compite con "director de distribución" hist=71) |
| 8 | operador | atencion\|cliente\|call center | b7b75eb6-… | agente de centro de atención al cliente | freq dominante (841 vs 6) | **alta** |
| 9 | operador | almacen\|deposito\|logistica | bea705fe-… | mozo de almacén | freq dominante (962 vs 325) | **alta** |
| 10 | operador | produccion\|planta\|fabrica | e3dc66de-… | operario de producción de alimentos | keyword "producción" + label genérico | **baja** (top por hist es "prensado de fruta", no genérico) |
| 11 | operador | maquinas\|cnc\|torno | — | — | **DECISIÓN HUMANA: ISCO 8211 mal declarado** | — |

### A4. Casos que requieren decisión humana

| # | Caso | Por qué |
|---|---|---|
| **6** | gerente.marketing | La heurística devuelve "responsable de marketing digital" pero "director de marketing" es semánticamente más natural para "gerente de marketing" (sólo 11 hist). Ambos son C1221. **Pregunta:** ¿priorizar frecuencia o naturalidad del label? |
| **7** | gerente.logistica\|supply chain | Compiten "director de la cadena de suministro" (40, matchea "supply chain") vs "director de distribución" (71, sin matchear keyword). **Pregunta:** ¿usar matching keyword o frecuencia bruta? |
| **10** | operador.produccion | C8160 es ISCO específico de alimentos; "operario de producción de alimentos" cubre el caso genérico mejor que "operario de prensado de fruta" (top por hist) que es muy específico. **Pregunta:** ¿confirmar el genérico o aceptar el específico top? |
| **11** | operador.maquinas\|cnc\|torno | C8211 ESCO no tiene operadores de máquinas-herramienta; sólo montadores. **Pregunta crítica:** ¿es el ISCO correcto? Probable correcto: 7223 (machinists/operadores) o 8121 (operadores de instalaciones de metales). |

→ **Sub-fase B de C2 en SPEC v3**: 7 selecciones automáticas + **4 decisiones humanas** (no 11 lookups automáticos como decía SPEC v2). Esfuerzo realista: 3-4h (no 2h).

---

## B — SQL de C4 reescrito

### B1. SQL ejecutable validado

```sql
UPDATE ofertas_esco_skills_detalle AS sd
SET
  is_essential_for_occupation = COALESCE((
    SELECT 1 FROM esco_associations ea
    JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
    WHERE ea.occupation_uri = om.esco_occupation_uri
      AND ea.skill_uri = sd.esco_skill_uri
      AND ea.relation_type = 'essential'
    LIMIT 1
  ), 0),
  is_optional_for_occupation = COALESCE((
    SELECT 1 FROM esco_associations ea
    JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
    WHERE ea.occupation_uri = om.esco_occupation_uri
      AND ea.skill_uri = sd.esco_skill_uri
      AND ea.relation_type = 'optional'
    LIMIT 1
  ), 0)
WHERE EXISTS (
  SELECT 1 FROM ofertas_esco_matching om
  WHERE om.id_oferta = sd.id_oferta
    AND om.esco_occupation_uri != ''
);
```

**Validación con `EXPLAIN QUERY PLAN` (ejecutado, sin UPDATE real):**

```
[4/0]   SCAN sd
[7/0]   CORRELATED SCALAR SUBQUERY 3   (filtro WHERE EXISTS)
  [12/7]   SEARCH om USING INDEX sqlite_autoindex_ofertas_esco_matching_1 (id_oferta=?)
[38/0]  CORRELATED SCALAR SUBQUERY 1   (essential)
  [49/38]  SEARCH om USING INDEX sqlite_autoindex_ofertas_esco_matching_1 (id_oferta=?)
  [54/38]  SEARCH ea USING INDEX idx_esco_assoc_occ (occupation_uri=?)
[74/0]  CORRELATED SCALAR SUBQUERY 2   (optional)
  [85/74]  SEARCH om USING INDEX sqlite_autoindex_ofertas_esco_matching_1 (id_oferta=?)
  [90/74]  SEARCH ea USING INDEX idx_esco_assoc_occ (occupation_uri=?)
```

✅ **SQL parsea, plan razonable: SCAN sobre 1.116M filas + 3 SEARCH por fila usando autoindex de id_oferta y `idx_esco_assoc_occ`**.

Columnas verificadas existentes en `ofertas_esco_skills_detalle`:
- `is_essential_for_occupation` INTEGER
- `is_optional_for_occupation` INTEGER

### B2. Estimación de tiempo

**Volumen real:**
- `ofertas_esco_skills_detalle`: **1.116.011 filas** total
- Backfilleable (con URI no vacía): **1.023.911 filas** (matchea SPEC v2)
- `esco_associations`: 129.004 filas (~43 skills/ocupación promedio)
- `ofertas_esco_matching`: 56.433 filas

**Índices disponibles:**
| Tabla | Índice | Columnas |
|---|---|---|
| esco_associations | idx_esco_assoc_occ | occupation_uri |
| esco_associations | idx_esco_assoc_skill | skill_uri |
| esco_associations | idx_esco_assoc_type | relation_type |
| ofertas_esco_matching | sqlite_autoindex | id_oferta (PK) |

**Lo que falta (no bloqueante, pero relevante):**
- ❌ NO hay índice compuesto `(occupation_uri, skill_uri, relation_type)` en `esco_associations`. Cada subquery hace SEARCH por `occupation_uri` (lookup ~O(log N)), pero luego filtra `skill_uri` y `relation_type` linealmente sobre las ~43 filas promedio por occupation. No es problema crítico pero podría acelerarse 3-5x agregando ese índice antes del UPDATE.

**Estimación realista:**
- Por fila backfilleable: 1 SEARCH autoindex + 2 subqueries con SEARCH+filter lineal sobre ~43 filas + 2 escrituras a disco
- Throughput esperado: 500-2000 filas/seg sobre 1M+ filas
- **Total: 8-35 minutos** (más realista que las "30-90 min" del SPEC v2 §7.3)

Caveat: si la base tiene WAL checkpoint pendiente o auto-vacuum activo, puede sumar 30-50% más.

### B3. Queries de verificación post-UPDATE

```sql
-- Q1: Conteo por flag
SELECT
  SUM(CASE WHEN is_essential_for_occupation = 1 THEN 1 ELSE 0 END) AS n_essential,
  SUM(CASE WHEN is_optional_for_occupation = 1 THEN 1 ELSE 0 END) AS n_optional,
  SUM(CASE WHEN is_essential_for_occupation = 0 AND is_optional_for_occupation = 0 THEN 1 ELSE 0 END) AS n_zero,
  COUNT(*) AS total
FROM ofertas_esco_skills_detalle sd
WHERE EXISTS (
  SELECT 1 FROM ofertas_esco_matching om
  WHERE om.id_oferta = sd.id_oferta AND om.esco_occupation_uri != ''
);
-- Esperado: total = 1.023.911. n_essential ≈ 0.324 × total = ~332K (R2 §B2).
```

```sql
-- Q2: Sample 50 ofertas para inspección manual
SELECT sd.id_oferta, sd.esco_skill_label,
       om.esco_occupation_label,
       sd.is_essential_for_occupation, sd.is_optional_for_occupation
FROM ofertas_esco_skills_detalle sd
JOIN ofertas_esco_matching om ON om.id_oferta = sd.id_oferta
WHERE om.esco_occupation_uri != ''
ORDER BY RANDOM()
LIMIT 50;
-- Verificar manualmente: ¿skill marcada essential coincide con catálogo ESCO oficial?
```

```sql
-- Q3: Validación cruzada — para 5 ocupaciones aleatorias, contar essential vs catálogo
SELECT om.esco_occupation_uri, om.esco_occupation_label,
       COUNT(*) AS skills_total,
       SUM(sd.is_essential_for_occupation) AS skills_essential_post_update,
       (SELECT COUNT(*) FROM esco_associations ea
        WHERE ea.occupation_uri = om.esco_occupation_uri
          AND ea.relation_type = 'essential') AS skills_essential_catalogo
FROM ofertas_esco_matching om
JOIN ofertas_esco_skills_detalle sd ON sd.id_oferta = om.id_oferta
WHERE om.esco_occupation_uri != ''
GROUP BY om.esco_occupation_uri
LIMIT 5;
-- Verificar: skills_essential_post_update <= skills_essential_catalogo (no puede haber más).
```

### B4. Plan de pausa de pipeline

**Pipeline actualmente NO activo** (verificación con `ps aux`).

**Para C4 (UPDATE de ~1M filas):**
1. **Pausar:** matar/no-iniciar `run_validated_pipeline.py`, `process_nlp_from_db_v11.py`, `match_ofertas_v3.py`, `auto_validator.py`. No hay "modo mantenimiento"; se pausa por convención (no ejecutar entry-points).
2. **Pausar:** `sync_to_supabase.py` (lee `ofertas_esco_skills_detalle`, podría leer estado intermedio).
3. **Dejar correr:** Scraping VPS (Lun/Jue 08:00). El scraping inserta en tabla `ofertas` y no toca `ofertas_esco_*` (verificado en R5). Si C4 corre fuera del horario de scraping, no hay riesgo.
4. **Si scraping coincide con C4:** opción de tolerar (no afecta filas ya escritas) o reagendar manualmente el scraping.

**Comando concreto pre-C4:**
```bash
# Verificar nada activo
ps aux | grep -E "(run_validated_pipeline|process_nlp|match_ofertas|sync_to_supabase|auto_validator)" | grep -v grep
# Si vacío → seguro ejecutar C4
```

**Recomendación:** ejecutar C4 fuera de Lun/Jue 08:00 ART. Tiempo estimado total con margen: 1h en ventana sin pipeline.

---

## C — Label drift en 3 entradas isco_primario

### C1. Drift confirmado

**3 de 19 entradas isco_primario tienen label JSON que NO existe en `esco_occupations` con ese ISCO ni en ningún otro:**

| Entrada (clave en JSON) | ISCO declarado | Label declarado en JSON | Existe label en C{ISCO}? | Existe label en otro ISCO? |
|---|---|---|---|---|
| jefe de mantenimiento | 1321 | "jefe de mantenimiento/jefa de mantenimiento" | ❌ No | ❌ No con ese label exacto |
| analista de tesoreria | 4312 | "empleado de gestión financiera/empleada de gestión financiera" | ❌ No | ❌ No con ese label exacto |
| operador de atencion | 4222 | "empleado de centro de contacto/empleada de centro de contacto" | ❌ No | ❌ No con ese label exacto |

**Las 16 restantes matchean exacto** (recepcionista, vendedor, administrativo, personal para obra, capataz, albañil, plomero, martillero, repositor, ejecutivo comercial, administrativo contable, cajero de mostrador, operario de deposito, bachero, vendedor mayorista, gerente de operaciones gastronómicas).

### C2. Búsqueda extendida — labels candidatos

#### `jefe de mantenimiento`
| ISCO en BD | Label canónico cercano | URI segmento |
|---|---|---|
| **C1219** | **director de mantenimiento de una fábrica/directora de mantenimiento** | 680831bb-… |
| C2141 | técnico de mantenimiento y reparación | 615920c5-… |
| C2144 | ingeniero de mantenimiento/ingeniera de mantenimiento | 1c36dd08-… |
| C3115 | supervisor de mantenimiento industrial/supervisora de mantenimiento | a9b20949-… |

→ **Hallazgo crítico**: el ISCO 1321 declarado en JSON es probablemente INCORRECTO. El label "director de mantenimiento de una fábrica" está en **ISCO 1219** (otros directores de servicios).

#### `analista de tesoreria`
| ISCO en BD | Label cercano | URI segmento |
|---|---|---|
| **C4312** | **empleado administrativo de gestión financiera/empleada administrativa de gestión financiera** | (en C4312, ya listado en query anterior) |
| C1211 | tesorero de empresa, tesorero de banco | 3e1a2f3c-…, b680251e-… |

→ El label JSON dice "empleado de gestión financiera"; el canónico es "empleado **administrativo** de gestión financiera". Diferencia mínima, mismo ISCO.

#### `operador de atencion`
| ISCO en BD | Label cercano | URI segmento |
|---|---|---|
| **C4222** | **agente de centro de atención al cliente** | b7b75eb6-… |
| C4222 | agente de atención al cliente por chat | fde97584-… |

→ ISCO correcto. El label JSON "empleado de centro de contacto" no existe; el canónico es "agente de centro de atención al cliente" (con 841 ofertas históricas — confirma que es el match correcto).

### C3. Decisión sugerida por entrada

| Entrada | Decisión | Cambio JSON propuesto | Justificación |
|---|---|---|---|
| **jefe de mantenimiento** | **(iii) Cambiar ISCO** | `isco_primario: "1321"` → `"1219"`<br>`esco_label: "director de mantenimiento de una fábrica"` | El label correcto está en otro ISCO. Histórico: 149 ofertas con "jefe…" matchearon C1321 — **probablemente clasificadas mal** todas estas. Re-matching con C1219 corrige. |
| **analista de tesoreria** | **(i) Aceptar label canónico** | `esco_label: "empleado administrativo de gestión financiera/empleada administrativa de gestión financiera"`<br>(mantener `isco_primario: "4312"`) | Mismo ISCO; sólo añadir "administrativo". Cambio cosmético en output. |
| **operador de atencion** | **(i) Aceptar label canónico** | `esco_label: "agente de centro de atención al cliente"`<br>(mantener `isco_primario: "4222"`) | Label real ESCO. 841 ofertas históricas validan. |

**Frecuencia histórica afectada por cambios:**
- jefe de mantenimiento: 149 ofertas con título "jefe…" en C1321 → todas se re-clasifican a C1219 (impacto **medio**, requiere re-rematch dirigido o entrar en C1).
- analista de tesoreria: 35 ofertas con "analista…" en C4312 → label cambia, ISCO/URI igual. **Sólo cambia campo `esco_occupation_label`**.
- operador de atencion: 213 ofertas con "operador…" en C4222 → label cambia, ISCO igual.

### C4. Conteos correctos finales (vs SPEC v2)

| Conteo | SPEC v2 dice | Realidad BD/JSON |
|---|---:|---:|
| Total entradas en `ocupaciones_titulo` | (no declara) | **24** (sin `_descripcion`) |
| Con `isco_primario` | **17** | **19** (reportado en SPEC como 17 — error) |
| Con `isco_familia` | 5 | 5 ✅ |
| Contextos en `gerente` | 11 | **7** (el "11" del SPEC es probablemente gerente+operador 7+4) |
| Contextos en `operador` | 4 | 4 ✅ |
| Contextos en `analista` (a quitar) | (no declara) | 8 |
| Contextos en `operario` (a quitar) | (no declara) | 5 |
| Contextos en `tecnico` (a quitar) | (no declara) | 6 |
| **Total contextos isco_familia a procesar** | (no declara) | **30** (8+5+6 a quitar + 7+4 a conservar con URI) |

---

## D — Criterio operacional para "qué es zombie" en Supabase

### D1. Análisis del drift Local↔Supabase

**Estados de validación local:**
| Estado | Conteo |
|---|---:|
| validado_claude | 49.071 |
| validado | 7.326 |
| pendiente | 36 |
| **Total validadas (universo Supabase)** | **56.397** |

**Skills detalle local:**
- De validadas: **1.115.010** filas
- De NO-validadas: 1.001 filas
- Huérfanas (sin matching record): **0**

**Sync log (`config/supabase_sync_log.json`):**
- Último sync: **2026-04-28** (864 ofertas / 14.417 skills en esa corrida)
- Última `validado_timestamp` en local: **2026-04-30** (post-último-sync)
- Acumulado histórico de sync (2026-04-22 a 2026-04-28): ~12.400 ofertas / ~268.000 skills
- **Conclusión D1**: el sync nunca corrió a fondo; Supabase tiene **mucho menos de 56.397 ofertas**. El drift no es "8.420 hacia atrás" sino mucho mayor.

### D2. Identificación correcta de zombies

**Definición operativa:**
```
Zombie = skill en Supabase (ofertas_skills) cuyo id_oferta NO existe en
         el universo de validadas locales (ofertas con estado_validacion
         IN ('validado', 'validado_claude', 'validado_humano')).
```

Esta definición resuelve el problema del DELETE inverso: si ejecutamos `DELETE FROM ofertas_skills WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard)` en Supabase **antes** de sincronizar el backlog, no borramos zombies — borramos skills cuyos ofertas YA están validadas localmente pero aún no se subieron.

**Query en Supabase (a correr ALLÁ, no en este SQLite):**
```sql
-- Conteo de "candidatos a zombie"
SELECT COUNT(*) FROM ofertas_skills os
WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

-- Si difiere mucho (>20%) del 28.395 reportado → confirma que mayoría es backlog.
```

**Cifra esperada antes del sync:** 28.395 (reportado en SPEC).
**Cifra esperada después del sync:** mucho menor, idealmente cerca de 0 o pocos cientos (genuinos zombies por ofertas que se invalidaron localmente y nunca se borraron de Supabase).

### D3. Orden de operaciones C5 (revisado)

**Plan correcto:**

```
PASO 1: SYNC FORZADO (no DELETE)
  python scripts/exports/sync_to_supabase.py
  # Sube backlog completo: ~40K ofertas pendientes y sus ~880K skills
  # Tiempo estimado: 30-60 min (rate limit 15 req/s)

PASO 2: RE-CONTAR zombies con criterio D2
  -- En Supabase
  SELECT COUNT(*) FROM ofertas_skills os
  WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

PASO 3a: SI conteo bajó a <500 → genuinos zombies, DELETE seguro
  DELETE FROM ofertas_skills os
  WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

PASO 3b: SI conteo aún alto (>5000) → PARAR y reinvestigar
  - ¿El sync no subió todo? Verificar paginación.
  - ¿Hay drift en otros estados (ej. 'rechazado')?

PASO 4: ACTIVAR cron sync diario (si no estaba)
```

**Crítico**: NO ejecutar el DELETE antes del sync. El DELETE-then-sync invierte el problema y puede borrar skills válidas.

### D4. Verificación pre-DELETE

Antes del DELETE final:

```sql
-- En Supabase
-- Q1: Conteo
SELECT COUNT(*) AS n_zombies, COUNT(DISTINCT id_oferta) AS n_ofertas_huerfanas
FROM ofertas_skills os
WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard);

-- Q2: Top 20 ofertas con más skills huérfanas
SELECT id_oferta, COUNT(*) AS n_skills, MAX(created_at) AS last_skill
FROM ofertas_skills
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard)
GROUP BY id_oferta
ORDER BY n_skills DESC LIMIT 20;

-- Q3: Sample 20 zombies para inspección
SELECT os.id_oferta, os.skill_label, os.created_at
FROM ofertas_skills os
WHERE os.id_oferta NOT IN (SELECT id_oferta FROM ofertas_dashboard)
LIMIT 20;
```

**Decisión por umbral:**
- Q1.n_zombies < 500: confianza alta → ejecutar DELETE.
- Q1.n_zombies entre 500 y 5000: spot-check sample (Q3) manualmente. Si todas son ofertas viejas borradas localmente → ejecutar. Si alguna es válida → reinvestigar.
- Q1.n_zombies > 5000: NO ejecutar; el sync no completó.

---

## E — Hallazgos colaterales

### E1. ISCO duplicado en `gerente`
`gerente.ventas|comercial → 1221` y `gerente.marketing → 1221` apuntan al mismo ISCO. La heurística A3 elige URIs distintas (director de ventas vs responsable de marketing digital), así que no es un bloqueante de implementación, pero es una decisión de diseño implícita: a propósito de **disambiguar dos contextos al mismo ISCO en URIs distintas**. Confirmar con humano si es la intención.

### E2. Solapamiento isco_primario ↔ contextos isco_familia
- `operario de deposito` (isco_primario 9333) ↔ `operario.almacen|...` (isco_familia 8 → 9333)
- Ambas resolverían al mismo URI; redundante. Con la entrada `operario` quitada (Opción 1 SPEC v2), el solapamiento desaparece.

### E3. Drift de sync mucho mayor que lo asumido
- Local: 56.397 ofertas validadas + 1.115.010 skills.
- Supabase (CLAUDE.md): "16K+ ofertas / 300K+ skills".
- **Drift potencial: ~40K ofertas y ~800K skills no sincronizados.**
- C5 implica un sync masivo (no incremental) antes del DELETE. Tiempo: 60-90 min según CLAUDE.md.
- **Implicación crítica**: el SPEC v2 estima C5 en "4-6h"; con 40K ofertas + 800K skills + DELETE + verificaciones, **realista 6-10h**.

### E4. ISCO 8211 en `operador.maquinas|cnc|torno` parece mal declarado
ISCO 8211 ESCO contiene exclusivamente montadores (mecánicos, mecatrónica, vehículos). No tiene ningún "operador de máquinas-herramienta" o "operador de torno/CNC". Operador CNC encajaría mejor en ISCO 7223 (machinists, instaladores y operadores de máquinas-herramienta).

→ **Bug potencial pre-existente en JSON**, no creado por SPEC U-1. Si se quiere corregir en SPEC v3 sería un cambio adicional al alcance.

### E5. Falta índice compuesto óptimo en `esco_associations`
Hay índice por `occupation_uri` solo. Para C4 sería marginalmente más rápido con `(occupation_uri, skill_uri, relation_type)`. No bloqueante.

### E6. Estado pipeline al momento del diagnóstico
- 0 procesos activos del pipeline.
- 36 ofertas en estado "pendiente" (residuo, no relevante para SPEC U-1).
- Backlog NLP CLAUDE.md menciona "~4.6K ofertas pendientes NLP" — independiente del SPEC U-1, no afecta su ejecución.

---

## Anexo: queries y scripts utilizados

Archivos de scratch generados (no committeados):
- `/tmp/p9_sec_a.py` — query de candidatos por contexto (volcado a `/tmp/p9_sec_a_candidatos.json`)
- `/tmp/p9_sec_b.py` — EXPLAIN QUERY PLAN del UPDATE
- `/tmp/p9_sec_c.py` + `/tmp/p9_sec_c2.py` — drift y búsqueda extendida
- `/tmp/p9_sec_d.py` + `/tmp/p9_sec_e2.py` — análisis sync log + estados validación
