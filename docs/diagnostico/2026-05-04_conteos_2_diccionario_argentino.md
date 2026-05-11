# Conteos 2 — Diccionario argentino + plan F1

**Fecha ejecución:** 2026-05-04
**Pipeline activo durante el diagnóstico:** no
**Modo:** read-only estricto (SQLite con `?mode=ro`, sin ejecutar scripts del pipeline)
**Tiempo total:** ~25 min
**Queries no completadas:** ninguna

---

## A — Arquitectura del path "diccionario argentino"

### A1. ¿Cuántos paths `diccionario_argentino_*` hay en el código?

**Hay 1 sola función que genera todos los valores `diccionario_argentino_*`.**

Los 8 valores observados en BD (`administrativo`, `vendedor`, `analista`, `gerente`, `operario`, `operador`, `tecnico`, etc.) NO son funciones distintas — son sufijos generados dinámicamente por un único f-string.

**Ubicación única:**
- `database/match_ofertas_v3.py:312` —
  ```python
  "metodo": f"diccionario_argentino_{termino.replace(' ', '_')}",
  ```
- Función contenedora: `_match_by_argentino_dict()` definida en línea **241**.
- El sufijo viene de la clave del JSON `sinonimos_argentinos_esco.json` (ej. `"administrativo"`, `"gerente de operaciones gastronómicas"` → `"gerente_de_operaciones_gastronómicas"`).

**Llamadas a `_match_by_argentino_dict()`:** 1 sola, en línea **577** (dentro de `_full_semantic_match`).

> No hay 8 paths separados; hay 1 path con 24 entradas distintas en el JSON, y el `match_method` se sufija con la clave matcheada.

### A2. ¿Cuáles son las ocupaciones del diccionario argentino?

`config/sinonimos_argentinos_esco.json` v1.1.0, fecha_creacion 2026-01-14.

**Total entradas reales (excluyendo `_descripcion`): 24** (no 25).

**Distribución de campos:**
| Campo | Entradas con el campo |
|---|---|
| `esco_uri` | **0 / 24** |
| `esco_label` | 19 / 24 |
| `isco_primario` (4 dig) | 19 / 24 |
| `isco_familia` (1-2 dig, sin primario) | 5 / 24 |
| `contextos` (mapeo subcategoría→ISCO) | 9 / 24 |

**Listado completo:**

| Clave | isco | esco_label | tiene_contextos |
|---|---|---|---|
| recepcionista | 4226 | recepcionista | sí |
| jefe de mantenimiento | 1321 | jefe de mantenimiento/jefa de mantenimiento | no |
| gerente | familia 1 | (sin label) | sí |
| analista de tesoreria | 4312 | empleado de gestión financiera/empleada... | no |
| analista | familia 2 | (sin label) | sí |
| operador de atencion | 4222 | empleado de centro de contacto/empleada... | no |
| operario | familia 8 | (sin label) | sí |
| operador | familia 8 | (sin label) | sí |
| vendedor | 5223 | vendedor/vendedora | sí |
| administrativo | 4110 | empleado de oficina/empleada de oficina | sí |
| tecnico | familia 3 | (sin label) | sí |
| personal para obra | 7112 | albañil | no |
| capataz | 3123 | capataz de construcción | sí |
| albañil | 7112 | albañil | no |
| plomero | 7126 | fontanero/fontanera | no |
| martillero | 3334 | agente inmobiliario/agente inmobiliaria | no |
| repositor | 9334 | reponedor/reponedora | no |
| ejecutivo comercial | 3322 | representante comercial | no |
| administrativo contable | 4311 | empleado de contabilidad/empleada... | no |
| cajero de mostrador | 5230 | cajero/cajera | no |
| operario de deposito | 9333 | mozo de almacén/moza de almacén | no |
| bachero | 9412 | ayudante de cocina | no |
| vendedor mayorista | 5223 | vendedor especializado/vendedora especializada | no |
| gerente de operaciones gastronómicas | 1412 | director de restaurante/directora... | no |

**Schema observado (3 formas distintas):**

```jsonc
// Forma 1: ISCO primario directo
"recepcionista": {
  "isco_primario": "4226",
  "esco_label": "recepcionista",
  "variantes": ["recepcionista","receptionist"],
  "contextos": {"consultorio|medico|salud": "4226", "hotel|alojamiento": "4224", ...}
}

// Forma 2: Familia ISCO con contextos obligatorios
"gerente": {
  "isco_familia": "1",
  "variantes": ["gerente","manager","director"],
  "contextos": {"ventas|comercial": "1221", "finanzas": "1211", ...}
  // NO trae esco_label en la entrada padre
}

// Forma 3: ISCO primario sin variantes ni contextos
"plomero": {
  "isco_primario": "7126",
  "esco_label": "fontanero/fontanera",
  "variantes": ["plomero","plomera","plomeria"]
}
```

> **Discrepancia con CLAUDE.md:** `CLAUDE.md:1180` declara "17 ocupaciones" en el diccionario; el archivo real tiene 24.

### A3. ¿Dónde se invoca el diccionario dentro del flujo?

Trazado en `match_ofertas_v3.py:_full_semantic_match()` (alrededor de línea 540-808):

```
PASO 1: skills_dual_result (extracción de skills)
                 │
PASO 2: 2a: dict_match = _match_by_argentino_dict(oferta_nlp)        ← línea 577
        2b: si NO hay dict_match → semántico (skills_first / title_only)  ← líneas 596+
PASO 3: rule_info = _evaluate_rule_only(oferta_nlp)                  ← línea 657
PASO 4: dual_coinciden = (regla_isco[:4] == semantic_isco[:4])
PASO 5: _decide_dual_match(regla_isco, semantic_isco, score, ...)    ← línea 697
PASO 6: persistir según decisión
```

**Hallazgo crítico:** el resultado del diccionario **se carga en las variables `semantic_*` del flujo** (líneas 587-594), no en variables propias. Es decir, el diccionario "pretende ser" el semántico para el resto del pipeline.

```python
if dict_match:
    semantic_isco   = dict_match["isco_code"]   # ← líneas 587-594
    semantic_label  = dict_match["esco_label"]
    semantic_score  = dict_match["score"]       # = 0.90
    semantic_metodo = dict_match["metodo"]
    # NO se setea semantic_uri  ← bug raíz
else:
    # ... bloque 2b: skills_first / title_only / no_match
    semantic_uri = best.get("occupation_uri", "")   # sí se setea acá
```

**¿Entra al duelo dual?** Sí. Cuando hay dict_match Y hay regla_isco, `_decide_dual_match` los compara con la misma lógica que regla-vs-semántico. Si la regla gana (dual_coinciden, regla_critica, regla_prioridad, etc.), se invoca `_resolve_rule_target()` que **sí resuelve URI** (línea 748: `esco_uri=rule_occupation['uri']`). Si "el semántico" gana (que en realidad es el diccionario), `esco_uri=semantic_uri=""` (línea 784). Por eso el bug solo se manifiesta cuando el diccionario gana o cuando no hay regla.

**¿Bypassea el semántico?** Sí — si dict_match matchea, **el bloque 2b no corre** (líneas 587 if/else 595). No hay fallback semántico. Esto es relevante para el fix: cualquier reemplazo del diccionario debe decidir explícitamente "qué hago si la URI no se puede derivar".

### A4. Línea exacta donde se omite la asignación de URI

| Paso | Archivo:línea | Qué pasa con `esco_uri` |
|---|---|---|
| Init en `_full_semantic_match` | `match_ofertas_v3.py:584` | `semantic_uri = ""` |
| Path `dict_match` | `match_ofertas_v3.py:587-594` | NO toca `semantic_uri` (solo isco/label/score/metodo) |
| Return `MatchResult` | `match_ofertas_v3.py:782-784` | `esco_uri=semantic_uri` → `""` cuando viene del diccionario |
| Persistir en BD | `match_ofertas_v3.py:1437-1454` | `result.esco_uri` se inserta en columna `esco_occupation_uri` |
| `_match_by_argentino_dict` retorna | `match_ofertas_v3.py:308-314` | Retorna dict con `isco_code, esco_label, score, metodo, termino_matched`. **No retorna URI.** |

El JSON `sinonimos_argentinos_esco.json` no tiene `esco_uri` en ninguna entrada (A2: 0/24).

**Hipótesis confirmada:** el JSON nunca tuvo URI y el código **nunca tuvo lógica para derivarla** desde `isco_code`. La URI se asume que se resolverá downstream — pero downstream no la resuelve (los pasos 4-5 reciben `semantic_isco` sin URI y la persistencia toma el string vacío tal cual).

### A5. ¿Hay un lookup `esco_code → esco_uri` que el diccionario podría usar?

**Sí, parcialmente. Pero no por `isco_code` 4-dígitos.**

`match_ofertas_v3.py:166-177` construye `self.code_to_occupation`, un diccionario `esco_code → {uri, label, esco_code, isco_code}`, indexado por **`esco_code`** (formato `4110.1`, `5223.7`, etc.) — NO por `isco_code` (formato `4110`).

```python
self.code_to_occupation = {}
for o in (self.occ_metadata or []):
    code = o.get('esco_code')                # ← formato '4110.1', no '4110'
    if code and code not in self.code_to_occupation:
        isco = o.get('isco_4dig') or (code.split('.')[0] if '.' in code else code[:4])
        self.code_to_occupation[code] = {
            'uri': o.get('uri', ''), 'label': o.get('label') or o.get('esco_label') or '',
            'esco_code': code, 'isco_code': isco,
        }
```

Función `_find_occupation_by_esco_code(esco_code)` (línea 1183) usa este lookup. Es invocada **solo** desde `_resolve_rule_target()` (línea 1205) — el path de las reglas, no del diccionario.

**Por qué no se usa en el diccionario argentino:** el JSON `sinonimos_argentinos_esco.json` declara `isco_primario` 4-dígitos, no `esco_code`. El lookup espera `esco_code`. Para que funcionara directamente, las entradas tendrían que declarar `esco_code` (ej. "4110.1") en lugar de — o además de — `isco_primario` ("4110").

**Ratio ESCO/ISCO en el catálogo (cuántas opciones hay para los ISCOs de Diego):**

| ISCO | Total ocupaciones ESCO bajo ese ISCO |
|---|---|
| 3322 (Repr. comercial) | 3 |
| 4110 (Empleado oficina) | 2 |
| 2512 (Desarrollador SW) | 10 |
| 5223 (Vendedor) | **44** |

> Para 4110 hay 2 ESCOs y para 3322 hay 3, así que un default razonable existe. Para 5223 con 44 opciones, el default no es trivial — el contexto del título (mayorista, especializado, audio/video, etc.) determina cuál.

**Conclusión A5:** existe la infraestructura (lookup `esco_code → uri`), pero el JSON del diccionario no tiene `esco_code`. El gap es de schema, no de código.

---

## B — Precondiciones del fix F1 (backfill de flags `is_essential` / `is_optional`)

### B1. Tabla `esco_associations` — schema y cobertura

**Schema:**
```
association_uri          TEXT PRIMARY KEY (nullable, autoindex único)
occupation_uri           TEXT NOT NULL
skill_uri                TEXT NOT NULL
relation_type            TEXT NOT NULL    ('essential' | 'optional')
skill_type_in_relation   TEXT (nullable)
```

**Índices existentes:**
- `idx_esco_assoc_type` sobre `(relation_type)`
- `idx_esco_assoc_skill` sobre `(skill_uri)`
- `idx_esco_assoc_occ` sobre `(occupation_uri)`
- `sqlite_autoindex_esco_associations_1` (único) sobre `(association_uri)`

> **No existe índice compuesto `(occupation_uri, skill_uri)`**. SQLite tendría que elegir uno de los dos índices simples y filtrar el resto en memoria. Para el backfill F1 conviene crear ese índice antes de correr (lectura — no modifica datos, solo acelera el SELECT).

**Total filas:** 129.004
- `relation_type='essential'`: 67.622
- `relation_type='optional'`: 61.382

**No existe valor `none`** en `relation_type`. Skills no presentes en `esco_associations` simplemente NO matchean — quedan con flags=0 (que es lo que tendría sentido como "no listada en ESCO para esta ocupación").

**Cobertura de URIs (occupation_uri):**

| Métrica | Valor |
|---|---|
| URIs distintos en `ofertas_esco_matching` (no vacíos) | 2.232 |
| URIs distintos en `esco_associations` | 3.039 |
| URIs presentes en ambas (∩) | **2.231** (99,96%) |
| URIs en matching SIN cobertura en assoc | **1** (afecta 1 oferta) |

> El URI sin cobertura es `46d0568d-7415-4643-94aa-89d2470fbe3c` — afecta 1 sola oferta.

### B2. Lógica del backfill como SQL — viable como single UPDATE

**Forma del JOIN (descripción, NO ejecutar):**

```
Por cada fila de ofertas_esco_skills_detalle d:
  obtener m.esco_occupation_uri (oferta padre) via INNER JOIN m.id_oferta = d.id_oferta
  obtener a.relation_type via LEFT JOIN
    a.occupation_uri = m.esco_occupation_uri AND a.skill_uri = d.esco_skill_uri
  setear:
    is_essential_for_occupation = (a.relation_type = 'essential' ? 1 : 0)
    is_optional_for_occupation  = (a.relation_type = 'optional'  ? 1 : 0)
```

**Viabilidad:** sí, viable como **UPDATE con WHERE/EXISTS** o como `UPDATE FROM` (SQLite 3.33+) con subquery. Lo recomendable es un `UPDATE...FROM` con scope a las filas backfilleables.

**Test empírico de SELECT (no UPDATE) sobre 1.000 filas:**
- Tiempo: **570 ms** para 1.000 filas (con índices simples actuales)
- 324/1.000 (32,4%) matcharon contra `esco_associations` → flag se asignaría
- 676/1.000 (67,6%) **no matcharon** → flags quedarían 0 (skill no listada en ESCO bajo esa ocupación; legítimo)

**Filas a backfilear:**

| Categoría | Filas |
|---|---|
| Total `ofertas_esco_skills_detalle` | 1.116.011 |
| **Backfilleables** (padre con URI ∧ skill con URI) | **1.023.911** |
| Excluidas (padre sin URI: viene del bug del diccionario o de no_match) | 92.100 |

**Las 92.100 excluidas:** quedarían con flags=0. No se pueden derivar hasta que se resuelva la URI del padre (fix del diccionario argentino, o re-matching). No tiene sentido un campo `pending_uri` en la tabla — el campo natural ya existe (`esco_occupation_uri = ''` en `ofertas_esco_matching`).

### B3. Estimación de tiempo de ejecución

Extrapolación lineal del SELECT test:

| Magnitud | Estimación |
|---|---|
| 1.000 filas SELECT | 570 ms (medido) |
| 1.023.911 filas SELECT | ~**10 minutos** (lineal sobre el medido) |
| Lo mismo, pero UPDATE | ~**30-60 minutos** (escritura es 2-5× más lenta que SELECT en SQLite + WAL) |

> La estimación es gruesa; el factor de escritura WAL depende del tamaño de la página y del checkpoint. Si se quiere acelerar: crear el índice compuesto `(occupation_uri, skill_uri)` sobre `esco_associations` antes (~30 segundos para esa creación, aprox.).

**Bloqueo del pipeline en producción:**
- `journal_mode = wal` (verificado).
- WAL permite lectores concurrentes durante el UPDATE; el pipeline (que escribe a `ofertas_esco_matching` y `ofertas_esco_skills_detalle`) **sí podría chocar** porque escribe sobre la misma tabla que se está actualizando.
- Recomendación operativa: ejecutar con pipeline detenido o con un lock declarado.

### B4. Verificación post-backfill (sin escribir las queries)

Lista de comprobaciones que se correrían:

1. **Distribución de flags poblados:**
   - `COUNT(*) WHERE is_essential_for_occupation=1` ≈ esperado proporcional a la fracción "essential" de `esco_associations` que matchee (67.622 / 129.004 = 52,4% del subconjunto matched).
   - `COUNT(*) WHERE is_optional_for_occupation=1` ≈ similar 47,6% del matched.
   - `COUNT(*) WHERE is_essential=0 AND is_optional=0` debería ser ≈ 67-68% (filas no listadas en ESCO bajo esa ocupación, observado 67,6% en muestra).
2. **Filas no backfilleadas:** `COUNT(*) WHERE esco_occupation_uri IS NULL OR ''` (vía join con padre) ≈ 92.100. Estas mantienen flags=0.
3. **Coherencia con catálogo:** sample de 50 filas con `is_essential=1` y verificar manualmente que esa skill está en `esco_associations` con `relation_type='essential'` para esa ocupación.
4. **Sin cambios espurios:** `COUNT(*)` total de la tabla antes y después — debe ser idéntico (solo UPDATE, no INSERT/DELETE).
5. **Distribución por ocupación:** para las top 20 ocupaciones, ratio esencial/opcional/no-listada debería seguir el patrón ESCO (cada ocupación tiene típicamente 6-15 essential y 6-50 optional según ESCO RDF).

---

## C — Fix del diccionario argentino

### C1. Alcance del fix

**Cambios mínimos para que el diccionario emita URI:**

| Archivo | Cambios estimados |
|---|---|
| `database/match_ofertas_v3.py` | ~10-15 líneas: setear `semantic_uri` cuando entra por `dict_match` (línea 587+) **o** modificar `_match_by_argentino_dict` para retornar también `esco_uri` y persistirlo. |
| `config/sinonimos_argentinos_esco.json` | ~24 entradas tocadas si se agrega `esco_uri` por entrada. **O** ~10 si solo agrego `esco_code` y dejo que el código resuelva URI vía `code_to_occupation`. |

**Dos enfoques posibles (sin recomendar uno):**

- **Enfoque A — Resolución en runtime:** agregar `esco_code` a cada entrada del JSON; el código usa `_find_occupation_by_esco_code()` (que ya existe, línea 1183) para obtener URI+label. Lados: schema estable, una sola fuente de verdad. Contra: hay que decidir cuál `esco_code` usar para los ISCOs con muchos hijos (ej. 5223 tiene 44 ESCOs).
- **Enfoque B — URI hardcodeada en el JSON:** agregar `esco_uri` a cada entrada. Lados: más simple. Contra: drift cuando cambie ESCO; redundancia con label.

**Para los `isco_familia` (5 entradas: gerente, analista, operario, operador, tecnico):** estas requieren contexto para resolverse a un ISCO 4-dígitos. Cuando el contexto matchea, hoy se elige un ISCO en el bloque `contextos`. Para que estas también tengan URI, los `contextos` tendrían que mapear a `esco_code`/`esco_uri` además de a ISCO.

### C2. Backward compatibility

**Consumidores actuales del JSON `sinonimos_argentinos_esco.json`:**

| Archivo | Cómo lo lee |
|---|---|
| `database/match_ofertas_v3.py:217` | `load_config('sinonimos_argentinos_esco')` — lee `ocupaciones_titulo`, espera `variantes`, `isco_primario`/`isco_familia`, `esco_label`, `contextos`. **Es el único consumidor que usa los datos para matching.** |
| `scripts/run_tracking.py:107` | Cuenta entradas (solo lee, para métrica). Robusto a campos extra. |
| `scripts/sync_learnings.py:138` | Cuenta entradas. Robusto a campos extra. |
| `scripts/sync_rules_from_candidates.py:104` | **Escribe** entradas nuevas al JSON. Usa key `"isco"` (NO `"isco_primario"`) y `"label"` (NO `"esco_label"`) — ver E.5 (drift de schema). |

**Conclusión:** agregar campos nuevos al schema es seguro para los lectores. El único punto frágil es `sync_rules_from_candidates.py` que ya tiene un drift propio.

### C3. Estrategia para las 3.762 ofertas ya afectadas

(El reporte 1 contó 3.762 ofertas con `esco_occupation_uri = ''`; D1 confirma que el grueso son ISCO 4110 administrativo=1.904 y ISCO 5223 vendedor=465.)

| Estrategia | Qué requiere | Costo | Riesgo |
|---|---|---|---|
| **A — Backfill batch** sobre las 3.762 | script Python que para cada oferta tome `isco_code`, busque la entrada ESCO default (típicamente la `.1` del ISCO en `esco_occupations_full.json`) y haga UPDATE. | Bajo (~minutos). | Para ISCOs como 5223 con 44 ESCOs hijos, el "default" puede ser equivocado en los casos especializados (vendedor de joyería, de automóviles, etc.). |
| **B — Reprocesar en pipeline normal** | Volver a marcar las 3.762 como pendientes y dejar que `run_validated_pipeline.py` las re-matchee con el código fixeado. | Más alto (NLP+matching+skills-detalle ~horas). | Bajo. Es el camino "limpio". Pero genera nuevas filas en `validation_errors` y mueve las ofertas a estado `pendiente`. |
| **C — Marcar `needs_uri_resolution`** | Agregar columna nueva. | Medio (migración + cambios en queries del dashboard). | Alto: cambia el contrato de tabla y otras lecturas tendrían que filtrar por la columna. |

**Datos relevantes para evaluar:**
- 1.904 / 3.762 son ISCO 4110 con 2 hijos ESCO (la default `.1` cubre ~99% de los casos genéricos).
- 465 / 3.762 son ISCO 5223 (44 hijos): default razonable es `5223.7` ("vendedor especializado") pero podría ser incorrecto para casos no especializados.
- 354 / 3.762 son ISCO 2 (analista, familia): no hay default — necesitan recontextualización completa.

> Estrategia B es la única que mantiene la integridad semántica para los casos `isco_familia`. A es viable solo para `isco_primario` con pocos hijos. C es overkill.

---

## D — Granularidad ESCO en lugar de ISCO

### D1. Mapeo URIs ESCO de las 4 ocupaciones de Diego

(Datos de `ofertas_esco_matching` agrupados por `esco_occupation_uri` cuando `isco_code` coincide.)

#### ISCO 3322 — Representante comercial (3.716 ofertas, 18 URIs distintos)

| URI (último segmento) | n | vía dict | vía regla | vía otro | label |
|---|---|---|---|---|---|
| `14031d4a-...18262b6432b2` | **3.670** | 0 | 3.602 | 68 | representante comercial |
| `<URI_VACIA>` | **28** | 27 | 0 | 1 | (sin label) |
| `73357956-...03beb9b39da2` | 2 | 0 | 0 | 2 | representante comercial |
| `ff3a164d-...49093dabf9fc` | 2 | 0 | 0 | 2 | comercial de cías. eléctricas de energías renovables |
| `4c6b3657-...ea763411190d` | 1 | 0 | 0 | 1 | comercial de cías. eléctricas |
| (otros 13 URIs con n=1) | 13 | 0 | 0 | 13 | (varios labels) |

> Cobertura sólida vía reglas (97% reglas, <1% URI vacía). Casi monocultivo de un solo URI.

#### ISCO 5223 — Vendedor (3.833 ofertas, 142 URIs distintos)

| URI (último segmento) | n | dict | regla | otro | label |
|---|---|---|---|---|---|
| `547b304b-...b7046df5f64e` | **2.895** | 0 | 2.831 | 64 | vendedor especializado |
| `<URI_VACIA>` | **465** | 465 | 0 | 0 | (sin label) |
| `9ba74e8a-...eb3c7a5c11df` | 78 | 0 | 0 | 78 | vendedor/vendedora |
| `38395ab3-...430eff19ec8d` | 36 | 0 | 0 | 36 | agente de alquiler de coches con opción a compra |
| `73357956-...03beb9b39da2` | 30 | 0 | 0 | 30 | operador de ventas |
| (otros 137 URIs ≤21 cada uno) | 329 | 0 | ~17 | ~312 | (varios labels) |

> 142 URIs — granularidad enorme. El URI vacío es 12% de los 5223. Los demás vienen del semántico (442 ofertas dispersas en 137 URIs distintos).

#### ISCO 4110 — Empleado de oficina (1.974 ofertas, 8 URIs distintos)

| URI | n | dict | regla | otro | label |
|---|---|---|---|---|---|
| `<URI_VACIA>` | **1.904** | **1.904** | 0 | 0 | (sin label) |
| `6c999fc7-...af124a1783a2` | 52 | 0 | 28 | 24 | empleado de oficina |
| `0a3c2d5b-...62bf3fed3310` | 12 | 0 | 0 | 12 | administrador de cuentas de socios |
| (otros 5 con n=1-2) | 6 | 0 | 0 | 6 | empleado de oficina (varios) |

> **96,5% URI vacía** — todas vienen del diccionario argentino "administrativo". Caso angular del bug.

#### ISCO 2512 — Desarrollador de software (1.630 ofertas, 45 URIs distintos)

| URI | n | dict | regla | otro | label |
|---|---|---|---|---|---|
| `f2b15a0e-...29b9d50b77d1` | **1.508** | 0 | 1.507 | 1 | desarrollador de software |
| `349ee6f6-...48765b55280e` | 24 | 0 | 0 | 24 | ingeniero de sistemas en la nube |
| `d0aa0792-...686cf4869d2e` | 13 | 0 | 0 | 13 | arquitecto de software |
| (otros 42 URIs ≤11 cada uno) | 85 | 0 | 0 | 85 | (varios) |

> Cobertura sólida vía reglas. URI vacía 0 ofertas.

### D2. ¿Esos URIs aparecen en algún Gold Set?

**Total IDs distintos sumados de los 5 gold sets activos (con casos parseables): 136 ids.**

Casos por ISCO Diego (sumando todos los gold sets activos):

| ISCO | name | casos en gold sets |
|---|---|---|
| 3322 | Representante comercial | **13** |
| 5223 | Vendedor | **4** |
| 4110 | Empleado de oficina | **0** |
| 2512 | Desarrollador SW | **4** |

**Por gold set:**

| Gold set | n_casos | parseable | iscos_distintos | tiene_uri |
|---|---|---|---|---|
| `database/gold_set_manual_v2.json` | 49 | sí (49 dicts) | 15 | 0 |
| `database/gold_set_nlp_100_ids.json` | 106 | no (lista de IDs sueltos) | 0 | 0 |
| `exports/matching_v3_gold_set_100.json` | 100 | sí | 55 | 0 |
| `metrics/gold_set_history.json` | 24 | no (entradas de histórico, no casos) | 0 | 0 |
| `metrics/gold_set_nlp_reprocesado.json` | (sin casos detectables) | — | — | — |
| `tests/matching/gold_set.json` | 49 | sí pero sin campo isco | 0 | 0 |
| `tests/matching/gold_set_v2.json` | 36 | sí | 27 | 0 |
| `tests/nlp/gold_set.json` | 49 | sí pero sin campo isco | 0 | 0 |

> **Ningún gold set declara `esco_uri`.** Todos trabajan a nivel ISCO o sin campo de target estructurado. Confirma el problema señalado en el reporte 1: la cobertura por ISCO oculta el problema real (mismo ISCO ↔ múltiples ESCOs distintos).

### D3. Top 20 URIs ESCO en MOL — cobertura en gold sets

**4 de las top 20 URIs no aparecen en ningún gold set:**

| URI (último segmento) | n_MOL | n_gold | label |
|---|---|---|---|
| `caafca69-...a3fa07fea4e6` | 644 | **0** | analista contable |
| `4ad4024e-...2c7948111dce` | 573 | **0** | mecánico de vehículos |
| `264b00c9-...aed2cea2b904` | 565 | **0** | supervisor de mantenimiento de vehículos |
| `3e7bf729-...83111963795c` | 506 | **0** | técnico de TIC |

(El resto del top 20 tiene entre 1 y 9 casos en gold — cobertura mínima pero presente.)

### D4. Densidad del Gold Set sobre el espacio ESCO

| Métrica | Valor |
|---|---|
| URIs ESCO con ≥1 oferta MOL | **2.232** |
| URIs ESCO ALCANZADAS por algún caso de gold set (vía id_oferta) | **87** |
| **Cobertura: % del espacio ESCO MOL** | **3,90%** |
| URIs ESCO declaradas explícitamente en gold sets | 0 |

> A nivel ESCO la cobertura de los gold sets es < 4% del espacio activo. Para un diagnóstico responsable de la calidad del matching ESCO, el gold set actual es insuficiente: cubre 87 de 2.232 URIs.

> Comparando con el reporte 1 (que organizó por ISCO), la diferencia es notable: los gold sets cubren ~30% de los ISCOs distintos, pero solo ~4% de las URIs ESCO. **La granularidad ISCO oculta el gap real.**

---

## E — Hallazgos colaterales

### E1. **Drift de labels para una misma URI** (1.237 URIs afectadas)

En `ofertas_esco_matching` hay **1.237 URIs distintas que aparecen con más de 1 label**. Top 8:

| URI (último segmento) | # labels distintos | Ejemplos |
|---|---|---|
| `f4de7e28-...30e02b3aa83b` | **41** | "planificador de producción de alimentos" / "responsable de regulación del tráfico" / "director del depto. de laboratorio médico" |
| `6a6e174e-...aa39c81cdee5` | 34 | "ayudante de cocina" / "empleado de mostrador postal" / "coctelero" |
| `bea705fe-...6e8ac1208d8f` | 31 | "reponedor" / "mozo de almacén" / "vendedor de piezas de repuesto" |
| `612430b3-...0466c4953f66` | 28 | "empleado de servicio de venta de entradas" / "técnico posventa" / "analista contable" |
| `33e3a746-...301505531cb2` | 25 | "jefe de sala" / "director de ventas" / "director de salón de belleza" |
| `9ba74e8a-...eb3c7a5c11df` | 24 | "vendedor" / "gestor atención al cliente" / "técnico en posicionamiento" |
| `7235d075-...d7e79bbce152` | 23 | "operario logística almacén" / "mozo de almacén" / "operario prensado fruta" |
| `9b889f07-...b2daa650f9ac` | 23 | "médico especialista" / "técnico radiología" / "técnico imagen diagnóstico" |

> Esto afecta directamente cualquier reporte agregado por URI: si se agrupa por `(uri, label)` se generan filas duplicadas. Si se agrupa solo por `uri` y se elige un `label` representativo, los analistas verán labels sorpresivos. La URI canónica tiene un único label en el catálogo ESCO oficial; aquí hay un bug de transcripción upstream (skills_first / semántico que escriben labels distintos al canónico). Pendiente diagnóstico ulterior.

### E2. **Código zombi: `database/normalizacion_arg.py`**

Existe un segundo módulo en `database/` con funciones aparentemente equivalentes al diccionario argentino:

```
database/normalizacion_arg.py:
  46  def _cargar_diccionario(conn=None)
  82  def normalizar_termino_argentino(titulo, conn=None) -> tuple
  135 def obtener_boost_isco(titulo, candidatos, conn=None) -> list
  192 def buscar_match_diccionario_directo(titulo, conn=None) -> dict | None
  265 def get_stats()
```

**Importadores actuales:**
- `database/archive_old_versions/matching_old/match_ofertas_multicriteria.py` (archivado)
- `database/archive_old_versions/tests_historical/test_bypass.py` (archivado)
- `scripts/nlp/archive_historical/debug_mozo_boost.py` (archivado)

**Producción NO lo importa.** Es código zombi que debería estar en `archive_old_versions/`. Sin embargo está en la raíz de `database/` lo que sugiere que puede confundir a próximos desarrolladores buscando el path argentino real.

### E3. **Drift de schema en `sync_rules_from_candidates.py`**

`scripts/sync_rules_from_candidates.py:113`:
```python
ocu_titulo[key] = {"isco": isco, "label": label}
```

El JSON `sinonimos_argentinos_esco.json` declara las claves `isco_primario`/`isco_familia` y `esco_label`, NO `isco`/`label`.

Significa que si en algún momento `sync_rules_from_candidates.py` agrega entradas nuevas (ej. desde candidatos auto-aprobados):
- El matcher las leerá vía `config.get("isco_primario")` (línea 292 de `match_ofertas_v3.py`) → **None** → la entrada nunca matcheará un ISCO 4-dígitos.
- El matcher leerá `esco_label` (línea 273) → **string vacío**.
- La entrada será efectivamente inerte.

> No verificamos cuántas entradas agregadas por este script existen actualmente. Pendiente para diagnóstico 3.

### E4. **Sin índice compuesto para JOIN del backfill F1**

`esco_associations` tiene índice sobre `occupation_uri` y sobre `skill_uri` por separado, pero no sobre el par. El UPDATE del backfill ejecutará un query del tipo `WHERE a.occupation_uri = ? AND a.skill_uri = ?`. SQLite usará uno u otro índice y filtrará el resto en memoria — para 1M+ filas, podría dominar el tiempo.

> Crear el índice compuesto `(occupation_uri, skill_uri)` antes del backfill puede reducir el tiempo significativamente. (No es destructivo; lectura.)

### E5. **Reglas ya tienen `esco_code` (98%); diccionario NO tiene ninguno**

`config/matching_rules_business.json`:
- 357 reglas con `accion`
- 350 / 357 (98%) tienen `accion.esco_code` (vía SPEC J)
- 351 / 357 (98%) tienen `accion.esco_label`

El diccionario argentino, en cambio:
- 0 / 24 entradas con `esco_code`
- 0 / 24 entradas con `esco_uri`

> Asimetría: el camino "más nuevo" (reglas) está bien instrumentado para resolver URI. El camino "más viejo" (diccionario) quedó atrás. SPEC J no se aplicó al diccionario argentino.

### E6. **CLAUDE.md desactualizado**

`CLAUDE.md:1180` declara:
```
| Diccionario Argentino | `config/sinonimos_argentinos_esco.json` (17 ocup) | - |
```

Realidad: 24 entradas reales. Drift de docs.

### E7. **No hay ofertas con isco_code de menos de 4 dígitos**

Verificado en BD: 0 ofertas con `LENGTH(isco_code) < 4`. Es decir, los `isco_familia` del diccionario (que devuelven solo "1", "2", "3", "8") no llegan a la BD — el código en `match_ofertas_v3.py:299-302` hace `continue` si el ISCO es <4 dígitos, dejando el caso al semántico. Esto significa que las 5 entradas `isco_familia` solo aportan vía sus `contextos`. Si el contexto no matchea, la entrada padre no produce nada — lo cual es correcto pero **invisible**: no hay log ni métrica de "diccionario tenía variante pero no contexto".

---

## Resumen ejecutivo (no propositivo)

**Conclusiones cuantificadas:**

1. **El path del diccionario argentino es 1 sola función con 24 entradas.** El bug de la URI vacía está en 4 líneas: `match_ofertas_v3.py:584` (init) y `587-594` (path no setea uri) → `784` (return) → `1454` (persistencia). El JSON tampoco tiene URIs (0/24 entradas).
2. **El backfill F1 es viable.** 1.023.911 filas backfilleables, infraestructura `esco_associations` cubre 99,96% de los URIs. Estimación: 30-60 min con WAL activado, o menos si se crea índice compuesto antes.
3. **Las 92.100 filas no backfilleables** salen de las 3.762 ofertas con URI vacía del diccionario (≈24 skills/oferta × 3.762 = ~90K, consistente). Son consecuencia del bug A4, no de un problema independiente.
4. **Para las 4 ocupaciones de Diego, ISCO 4110 es el caso angular:** 96,5% sin URI, 0 casos en gold sets.
5. **A nivel ESCO los gold sets cubren 3,90% del espacio activo.** A nivel ISCO la cobertura era ~30%. La granularidad ISCO ocultaba el gap real.
6. **1.237 URIs sufren label drift en BD** — una misma URI se persistió con hasta 41 labels distintos.

**Decisiones que el SPEC U no puede tomar sin más datos:**

- ¿Para los `isco_familia` del diccionario, qué se hace cuando los contextos no matchean? (5 entradas afectan ~600 ofertas según D1.)
- ¿La estrategia C3-A (default `.1` por ISCO) es aceptable para los 5223 (44 hijos)?
- ¿Se va a tocar `sync_rules_from_candidates.py` (E3) en el mismo PR del fix del diccionario? (Tienen el mismo schema drift.)
- ¿El fix del label drift (E1) es alcance del SPEC U o queda fuera?

> Estos puntos NO se proponen aquí; quedan pendientes para definir antes de implementar.
