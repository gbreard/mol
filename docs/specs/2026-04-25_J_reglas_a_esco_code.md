# SPEC J — Migrar reglas de matching de `esco_label` a `esco_code`

**Fecha:** 2026-04-25
**Autor:** Claude + Gerardo
**Estado:** Draft — pendiente factibilidad confirmada en Fase 0
**Scope:** 344 reglas activas en `config/matching_rules_business.json` con campo `esco_label`. Migrar a usar `esco_code` específico (granular: 7214.3.1) en vez de `esco_label` (texto) como pivote.
**Dependencia:** SPEC E (embeddings enriquecidos), SPEC H (rematch ESCO), backfill `titulo_esco_code` (todos hechos).
**Bloquea:** SPEC G + retropropagación final de skills (es preferible aplicar sobre reglas ya migradas).

---

## 1. Motivación

Hoy las reglas matchean por `esco_label` (string libre):

```json
"R347_operario_metalurgico": {
  "accion": {
    "forzar_isco": "7214",
    "esco_label": "remachador/remachadora"
  }
}
```

El matcher resuelve `esco_label` → `esco_uri` consultando `esco_occupations_metadata.json`. Eso es **frágil** porque:

- **Texto libre**: typos o variantes de orden ("ayudante/ayudanta" vs "ayudanta/ayudante") rompen el match silenciosamente.
- **Granularidad insuficiente**: `forzar_isco: "7214"` es ISCO 4-dig que agrupa 4 ocupaciones distintas en ESCO. Perdemos información.
- **Ambigüedad**: si el label existe en >1 esco_code (ej. "mozo de almacén" en 9333.4 y 9333.8), el matcher elige uno arbitrariamente.
- **No verificable**: sin esco_code explícito, no podemos validar gold sets contra códigos específicos.

Tras SPEC E + SPEC H + backfill, ya tenemos `titulo_esco_code` poblado en 48,960 ofertas (93%). El sistema **debería usar ese mismo nivel de granularidad** en sus reglas.

## 2. Objetivo

Las reglas pasan a tener `esco_code` como identificador autoritativo:

```json
"R347_operario_metalurgico": {
  "accion": {
    "esco_code": "7214.3.1",
    "esco_label": "remachador/remachadora"
  }
}
```

Donde:
- **`esco_code`** es la fuente de verdad — el matcher lo usa para identificar la ocupación.
- **`esco_label`** queda como redundancia legible para humanos (lectura de configs).
- **`forzar_isco`** se elimina (es derivable: primeros 4 chars del esco_code).

## 3. Hallazgos de Fase 0

Sobre 348 reglas activas:

| Categoría | N | % | Acción |
|---|---:|---:|---|
| `esco_label` mapea unívocamente a 1 esco_code | **326** | **94%** | Migración automática |
| `esco_label` mapea a múltiples esco_codes (ambigüedad) | 9 | 2.6% | Decisión humana |
| `esco_label` no existe en metadata (typo) | 9 | 2.6% | Búsqueda manual |
| Reglas de priorizar/penalizar (sin esco_label) | 4 | 1.1% | Sin migración |

### 9 ambiguas (todas comparten un label idéntico)

Todas las reglas con `esco_label="mozo de almacén/moza de almacén"`:
- R32_operario_picking
- R36_operario_almacen
- R136_personal_deposito
- R137_tareas_picking_crossdocking
- R141_peon_deposito
- (otras 4)

Mapean a **9333.4** o **9333.8**. Hay que decidir cuál corresponde para cada uso. Probablemente todas a 9333.8 (mozo de almacén genérico) — verificar con catálogo.

### 9 sin match en metadata

Probablemente typos o variantes de orden:
- `supervisor de construcción/supervisora de construcción` (R193_supervisor_operaciones, R302_supervisor_obra)
- `ayudante/ayudanta de cocina` (R207_peon_cocina) — orden invertido vs metadata
- `limpiador de oficinas/limpiadora de oficinas` (R209_personal_maestranza, R212_personal_limpieza)
- `vendedor en centro de contacto/vendedora en centro de contacto` (R210_telefonista_ventas)
- `empleado del centro de contacto de información/empleada...` (R213_asistente_comercial)
- `profesional de la publicidad y la comercialización` (R214_analista_comercial)

Se resuelven buscando manualmente la variante correcta en `esco_occupations_metadata.json`.

## 4. Diseño técnico

### 4.1 Migración del JSON de reglas

Script `scripts/embeddings/migrate_rules_to_esco_code.py`:

```python
for regla_id, regla in reglas_activas:
    label = regla['accion'].get('esco_label')
    if not label: continue
    candidatos = label_to_codes[label.lower()]
    if len(set(c[0] for c in candidatos)) == 1:
        # Automática
        regla['accion']['esco_code'] = candidatos[0][0]
    else:
        # Manual: registrar en lista pendientes
        registrar_pendiente(regla_id, candidatos)
```

Output:
- `config/matching_rules_business.json` actualizado con campo `esco_code` agregado a las 326 automáticas
- `docs/specs/2026-04-25_J_PENDIENTES.md` con las 18 que requieren decisión humana

### 4.2 Modificación de `match_ofertas_v3`

En `_load_business_rules()` y en el evaluator de reglas:

**Antes**:
```python
esco_label = regla['accion']['esco_label']
uri = label_to_uri.get(esco_label.lower().strip())  # frágil
```

**Después**:
```python
esco_code = regla['accion'].get('esco_code')
if esco_code:
    uri = code_to_uri[esco_code]  # autoritativo
else:
    # Fallback al sistema viejo (durante migración)
    uri = label_to_uri.get(esco_label.lower().strip())
```

El campo `esco_label` se mantiene como legible pero `esco_code` es la fuente de verdad.

### 4.3 `forzar_isco` se deprecia

`forzar_isco: "7214"` ahora se deriva: si el esco_code es `"7214.3.1"`, el ISCO 4-dig es `"7214"` (split por `.` y tomar primer chunk).

Mantener `forzar_isco` por compatibilidad mientras todos los downstream se actualicen, pero no agregar en reglas nuevas.

### 4.4 Re-evaluar las 5,272 ofertas tocadas por SPEC H

Tras SPEC J, las reglas pueden disparar a esco_codes ligeramente distintos (más específicos en algunos casos). Re-correr SPEC H **solo sobre las 5,272 que SPEC H actualizó** para alinear con las reglas nuevas. Es muy rápido (~5 min).

## 5. Plan por fases

### Fase 1 — Script migración automática (~1 h)

- `scripts/embeddings/migrate_rules_to_esco_code.py`
- Output: JSON actualizado + lista de pendientes
- Backup: `matching_rules_business.json.pre_spec_j_{timestamp}`

### Fase 2 — Curación manual de 18 reglas (~30-45 min)

- Las 9 ambiguas (todas mozo de almacén): decidir entre 9333.4 y 9333.8
- Las 9 sin match: buscar variante correcta en metadata
- Documentar decisiones en `2026-04-25_J_DECISIONES.md`

### Fase 3 — Modificar matcher (~2-3 h)

- `database/match_ofertas_v3.py`: cambiar resolución de label → code
- Mantener fallback temporal por si quedan reglas sin migrar
- Tests existentes deben seguir pasando

### Fase 4 — Tests (~2 h)

- Actualizar `tests/matching/gold_set_v2.json` para incluir `esco_code_esperado`
- Tests nuevos: validar que cada regla resuelve a su esco_code declarado
- Regresión gold set v2 sigue 47/48

### Fase 5 — Re-correr SPEC H (~5 min)

- Sobre las 5,272 ofertas que SPEC H ya tocó, re-evaluar con reglas migradas
- La mayoría no cambiará. Solo las ambiguas (mozo de almacén) podrían moverse de 9333.4 a 9333.8 (o viceversa).

## 6. Tests específicos

### 6.1 Verificación de migración (`tests/matching/test_spec_j_rules.py`)

- Cada regla con `esco_code` resuelve a la URI correcta en metadata.
- Cada regla sin `esco_code` (las 4 priorizar/penalizar) sigue funcionando.
- 18 manuales: cada una tiene `esco_code` válido tras curación.

### 6.2 Regresión gold set v2

- Las 47 verificadas siguen pasando.
- Tests usan ahora `esco_code_esperado` en vez de `isco_esperado`.

### 6.3 Test de coherencia

- Para todas las 348 reglas: si tiene `esco_code`, el `forzar_isco` (si existe) coincide con los primeros 4 chars del esco_code.

## 7. Riesgos

### 7.1 Decisión incorrecta en ambiguas

Para "mozo de almacén" — si elegimos 9333.4 cuando algunas reglas debían ir a 9333.8, el matching se sesga. Mitigación: revisar manualmente la diferencia entre 9333.4 y 9333.8 (probablemente "mozo de almacén tradicional" vs "mozo de almacén logística moderna" o similar).

### 7.2 Las 9 sin match tienen labels obsoletos

Si el catálogo ESCO cambió de "supervisor de construcción" a otra forma, el label en la regla quedó orphan. Mitigación: buscar manualmente el label más cercano en metadata. Si no existe, decidir si usar otro esco_code aproximado o desactivar la regla.

### 7.3 Cambios de matching tras migración

Algunas ofertas que matcheaban con un esco_code podrían ahora matchear con otro (por las 9 ambiguas). Mitigación: re-correr SPEC H scope chico (5,272 ofertas) post-J.

## 8. Decisiones pendientes

1. ¿Mantener `forzar_isco` en reglas o eliminarlo? — **recomendado: mantener pero deprecado**.
2. ¿Las 9 sin match: corregir o desactivar? — **revisar caso por caso**.
3. ¿Re-correr SPEC H solo sobre 5,272 o sobre todo el scope (14K)? — **solo 5,272 (las que cambiaron)**.

## 9. Cronograma estimado

| Fase | Duración |
|---|---|
| Fase 1 (migración auto) | 1 h |
| Fase 2 (curación 18) | 30-45 min |
| Fase 3 (modificar matcher) | 2-3 h |
| Fase 4 (tests + gold actualizado) | 2 h |
| Fase 5 (re-correr SPEC H) | 5 min |
| **TOTAL** | **~1 día** |

## 10. Lo que este spec NO hace

- NO agrega skills a las reglas (SPEC G aparte).
- NO cambia las reglas en sí (mismo título, mismo target). Solo cambia cómo se identifica el target.
- NO toca ofertas con regla ya aplicada (`regla_prioridad`, `dual_coinciden`, etc.) excepto las 5,272 que SPEC H modificó.
- NO retropropaga skills (eso viene después con SPEC G).
