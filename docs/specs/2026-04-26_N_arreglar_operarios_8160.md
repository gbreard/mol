# SPEC N — Arreglar codificación de operarios genéricos (R240 → 8160.35)

**Fecha:** 2026-04-26
**Autor:** Claude + Gerardo
**Estado:** Draft — listo para implementar
**Disparador:** Issues pendientes de Diego (24 abril) sobre operarios mal codificados a ISCO 8160. Tras SPEC E+G+H+J+K, los cambios NO resolvieron el problema. Causa raíz: regla `R240_operario_produccion`.
**Bloquea:** Sync grande Supabase (preferimos que el dashboard no muestre 1,335 "operarios de prensado de fruta" cuando son operarios diversos).

---

## 1. Diagnóstico

### 1.1 Hallazgo

`R240_operario_produccion` tiene **target absurdo: `ESCO 8160.35 "operario de prensado de fruta"`**.

```json
"R240_operario_produccion": {
  "condicion": {
    "titulo_contiene_alguno": ["operario","operaria"],
    "area_funcional_es": "Produccion",
    "titulo_no_contiene_alguno": ["limpieza","logistic","soldador","soldadora","soldadura"]
  },
  "accion": {
    "forzar_isco": "8160",
    "esco_label": "operario de prensado de fruta/operaria de prensado de fruta",
    "esco_code": "8160.35"
  },
  "_linaje": {
    "requiere_revision": true   ← el equipo ya sabía que era problemática
  }
}
```

### 1.2 Impacto medido

- **1,336 ofertas** validadas tienen `regla_aplicada = R240` y `esco_code = 8160.35`
- **1,335 / 1,567 (85%)** de ofertas en ISCO 8160 son por R240 (resto son R37 alimentos)
- Diego reportó 3 issues en abril sobre ofertas mal codificadas — los 3 caen en este patrón

### 1.3 Sample real de ofertas atrapadas

Las 12 ofertas random con R240 muestran diversidad MASIVA:

| Título real | Codificado como (R240 mal) | Lo correcto sería |
|---|---|---|
| Operario carpinterías de aluminio y PVC | prensado de fruta | 7223 (operario máquinas metal) |
| Operarios/as de Logística Tandil | prensado de fruta | 9333 (mozo almacén) |
| Operarios/as metalúrgicos/as | prensado de fruta | 7214 (chapista/metalúrgico) |
| Operario/a de Maestranza | prensado de fruta | 9112 (limpieza edificios) |
| Operario/a de Lavadero de Autos | prensado de fruta | 9122 (lavador vehículos) |
| Operarios con experiencia en Pickeado | prensado de fruta | 9333 (mozo almacén) |
| Operario soldadores Metalurgica | prensado de fruta (??) | 7212 (soldador) |
| Operario Maquinista/Mantenimiento | prensado de fruta | 7233 (mecánico maquinaria) |

**R240 funciona como un GIANT FALLBACK** que aplasta operarios de cualquier sector industrial a un único target sin sentido.

---

## 2. Causa raíz

### 2.1 Por qué R240 está así

Histórico del linaje:
- v512 (sprint 7, feb 2026): se creó la regla "Operario de producción"
- Se le puso target 8160 con label "operario de prensado de fruta" porque era el único ESCO específico bajo 8160 que matcheaba con "operario producción" en label
- En SPEC J (hoy) se migró el `esco_label` → `esco_code` → quedó `8160.35` formalizado

### 2.2 Por qué el matcher no se autocorrige

- La regla R240 tiene **prioridad 0** (default) y se dispara por keywords title amplias.
- Las reglas más recientes SPEC A (R345-R352) tienen prioridad -1/-2/-3 → **ganan a R240**.
- Pero R240 sigue capturando todo lo que NO matchea las específicas — y son MUCHAS ofertas.

### 2.3 Por qué SPEC H/J no lo arregló

- SPEC H solo tocó ofertas con `decision_metodo = 'semantico_unico'`. Las ofertas con R240 ya tenían `decision_metodo = 'regla_prioridad'` → **fuera del scope SPEC H**.
- SPEC J migró el target de R240 de label a esco_code, pero conservó el target malo.

---

## 3. Propuesta — 3 alternativas

### Opción A — Desactivar R240 y dejar al semántico decidir

- **Pro**: con embeddings enriquecidos (SPEC E), el semántico debería clasificar bien cada operario según contexto.
- **Contra**: las 1,336 ofertas vuelven a depender 100% de BGE-M3. Riesgo de re-introducir el ruido que SPEC H corrigió en otras ofertas.

### Opción B — Cambiar target de R240 a ESCO neutral

- **Pro**: simple y rápido. Cambiar `esco_code: "8160"` (sin sub) o `esco_code: "9329.1"` (peón industria).
- **Contra**: ¿existe esco_code "8160" sin sub-ocupación en metadata? Verificar. Si no, hay que elegir un sub-código menos absurdo (`9329.1` "peón industria manufacturera no clasificado" sería más honesto).

### Opción C — Mantener R240 pero estrechar condición + agregar reglas específicas (RECOMENDADA)

Combinación de:
1. **Refinar R240**: agregar más exclusiones a `titulo_no_contiene_alguno`:
   - aluminio, pvc, carpintería
   - lavadero, autos, vehículos
   - maestranza, mantenimiento
   - pickeo, picking, descarga, carga, despacho
   - metalúrgico (R347 ya lo cubre pero se le escapa con "operarios metalúrgicos plural")
2. **Cambiar target de R240** a `ESCO 9329.1` (peón industria manufacturera no clasificado) — es honesto: si la oferta es realmente operario genérico sin más detalle, esto refleja eso.
3. **Crear reglas específicas faltantes**:
   - R_operario_carga_descarga → `ESCO 9333.x` (mozo almacén)
   - R_operario_lavadero → `ESCO 9122.1` (lavador vehículos)
   - R_operario_maestranza → `ESCO 9112.2` (limpieza edificios)
   - R_operario_aluminio_pvc → `ESCO 7223.x` (operario máquinas metal)

---

## 4. Diseño técnico (Opción C — recomendada)

### 4.1 Nuevas reglas

```json
"R_NEW_OPERARIO_CARGA_DESCARGA": {
  "nombre": "Operario carga/descarga",
  "prioridad": -1,
  "condicion": {
    "titulo_contiene_alguno": ["operario","operaria","operarios","operarias"],
    "titulo_o_tareas_contiene_alguno": ["carga","descarga","despacho","picking","pickeo"]
  },
  "accion": { "esco_code": "9333.8", "esco_label": "mozo de almacén/moza de almacén" }
}

"R_NEW_OPERARIO_LAVADERO": {
  "nombre": "Operario de lavadero de vehículos",
  "prioridad": -1,
  "condicion": {
    "titulo_contiene_alguno": ["operario","operaria"],
    "titulo_o_tareas_contiene_alguno": ["lavadero","lavado de auto","lavado de vehíc","lavar autos"]
  },
  "accion": { "esco_code": "9122.1", "esco_label": "operario de limpieza de vehículos/operaria de limpieza de vehículos" }
}

"R_NEW_OPERARIO_MAESTRANZA": {
  "nombre": "Operario de maestranza",
  "prioridad": -1,
  "condicion": {
    "titulo_contiene_alguno": ["maestranza"]
  },
  "accion": { "esco_code": "9112.2", "esco_label": "operario de limpieza de edificios/operaria de limpieza de edificios" }
}

"R_NEW_OPERARIO_ALUMINIO_PVC": {
  "nombre": "Operario carpintería aluminio/PVC",
  "prioridad": -1,
  "condicion": {
    "titulo_contiene_alguno": ["operario","operaria"],
    "titulo_o_tareas_contiene_alguno": ["aluminio","pvc","carpintería de aluminio"]
  },
  "accion": { "esco_code": "7223.x", "esco_label": "operario de máquinas para trabajar metales/operaria..." }
}
```

(El esco_code exacto se confirma en Fase 1 buscando en metadata.)

### 4.2 Refinar R240

```json
"R240_operario_produccion": {
  ...
  "condicion": {
    "titulo_contiene_alguno": ["operario","operaria"],
    "area_funcional_es": "Produccion",
    "titulo_no_contiene_alguno": [
      "limpieza","logistic","soldador","soldadora","soldadura",
      "carga","descarga","despacho","picking","pickeo",
      "lavadero","lavado","autos","vehíc",
      "maestranza","mantenimiento",
      "aluminio","pvc","carpintería",
      "metalúrgico","metalurgico"
    ]
  },
  "accion": {
    "esco_code": "9329.1",     ← target HONESTO: peón industria sin clasificar
    "esco_label": "peón de la industria manufacturera no clasificado/peona..."
  }
}
```

(Verificar en Fase 1 que `9329.1` existe en metadata. Si no, buscar el código equivalente.)

### 4.3 Re-correr matching sobre las 1,336 ofertas afectadas

Después de actualizar reglas:
1. DELETE `spec_h_rematch_progress` para los IDs con R240 actual
2. Re-correr `rematch_isco_spec_h.py --ids X,Y,Z` (script ya existente, solo lista de IDs)
3. Esperado:
   - Ofertas con keywords específicas → ganan reglas nuevas (R_NEW_*)
   - Ofertas sin keywords específicas → caen en R240 modificada → 9329.1
4. Tiempo: ~10 min ejecución + 10 min reactivar/relockear

---

## 5. Plan por fases

| Fase | Acción | Duración |
|---|---|---|
| 1 | Verificar esco_codes en metadata (9329.1, 7223.x, etc.) | 10 min |
| 2 | Implementar las 4 nuevas reglas + refinar R240 en JSON | 30 min |
| 3 | Tests de coherencia (R_NEW_* tienen esco_code válido, R240 con nuevas exclusiones no rompe) | 30 min |
| 4 | Re-correr matching sobre las 1,336 afectadas | 10 min |
| 5 | Verificación canónica (los 3 casos Diego ahora correctos) | 10 min |
| 6 | Commit + sync grande | 2-3 h sync |
| **Total** | | **~4 h** |

---

## 6. Tests

### 6.1 Cobertura de reglas nuevas

```python
def test_R_NEW_operario_carga_descarga_aplica():
    nlp = mock_oferta(titulo='Operarios carga y descarga', area='Produccion')
    result = matcher.match(nlp)
    assert result.metadata['regla_aplicada'] == 'R_NEW_OPERARIO_CARGA_DESCARGA'
    assert result.metadata['esco_code'] == '9333.8'

def test_R_NEW_operario_lavadero_aplica():
    nlp = mock_oferta(titulo='Operario de lavadero de autos', area='Produccion')
    result = matcher.match(nlp)
    assert result.isco_code == '9122'
```

### 6.2 R240 ya NO atrapa los casos cubiertos por R_NEW_*

```python
def test_R240_no_atrapa_carga_descarga():
    nlp = mock_oferta(titulo='Operario de carga y descarga', area='Produccion')
    result = matcher.match(nlp)
    assert result.metadata['regla_aplicada'] != 'R240_operario_produccion'

def test_R240_aun_atrapa_genericos():
    nlp = mock_oferta(titulo='Operario de Producción', area='Produccion')
    result = matcher.match(nlp)
    assert result.metadata['regla_aplicada'] == 'R240_operario_produccion'
    assert result.metadata['esco_code'] == '9329.1'  # nuevo target neutral
```

### 6.3 Casos canónicos Diego se resuelven

```python
def test_caso_diego_carga_descarga():
    # oferta 7572054244
    result = procesar_oferta(7572054244)
    assert result.isco_code == '9333'  # Diego sugería 9333
```

### 6.4 Regresión

- Gold set v2: 47/48 pasa.
- Tests existentes SPEC E/G/H/J/K: 127+ passed.

---

## 7. Riesgos

### 7.1 Las nuevas reglas no cubren todos los casos

Después de refinar R240, ofertas que NO matcheen ninguna regla específica caerán en R240 con target 9329.1. Si 9329.1 tampoco es óptimo para muchas, seguimos con problema.

**Mitigación**: el target 9329.1 ("peón industria manufacturera no clasificado") es honesto — refleja exactamente lo que es la oferta cuando el sistema no puede ser más específico. Mejor que 8160.35 prensado de fruta.

### 7.2 Las exclusiones nuevas en R240 generan huecos

Una oferta con título "operario carga y descarga" debería matchear R_NEW_OPERARIO_CARGA_DESCARGA (prioridad -1). Si por algún error la nueva regla no aplica, R240 queda excluida → no aplica ninguna → semántico decide.

**Mitigación**: tests específicos por caso. Si una oferta cae en semántico, todavía hay embeddings enriquecidos (SPEC E) que pueden hacer un match razonable.

### 7.3 El esco_code 9329.1 puede no existir

ESCO catálogo es estricto. `9329` puede ser solo grupo, no ocupación específica.

**Mitigación**: en Fase 1 verificamos. Si no existe, alternativa: `9329` (grupo) o `9333.8` (mozo almacén) como neutral.

### 7.4 Otras reglas similares con problemas

`R37_operario_alimentos` apunta a `8160.15`. ¿También tiene mismo patrón?

**Mitigación**: revisar también R37 en Fase 1. Si es problemática, refinar.

---

## 8. Decisiones pendientes antes de implementar

1. **¿Qué target neutral para R240?** 9329.1 (peón sin clasificar) o 9333.8 (mozo almacén) o 8160 (sin sub).
2. **¿Cuántas reglas nuevas crear?** 4 propuestas + ¿operario_mantenimiento? + ¿operario_alimentos refinado?
3. **¿Auditar también R37_operario_alimentos?** Mismo patrón, target 8160.15.
4. **¿Revisar todas las reglas con `_linaje.requiere_revision: true`?** Hay otras en este estado.

---

## 9. Lo que este spec NO hace

- NO cambia código del matcher (`match_ofertas_v3`).
- NO modifica filtros de skills (G, K).
- NO toca embeddings.
- NO re-corre TODA la BD — solo las 1,336 ofertas con R240.

---

## 10. Recomendación

**Opción C** (refinar R240 + agregar reglas específicas). Es el approach más honesto:
- Reconoce que R240 era un fallback malo
- Captura los casos específicos con sus targets correctos
- Deja un fallback honesto (peón sin clasificar) para los genuinamente genéricos

Tiempo total: ~4 horas (3.5 h trabajo + 30 min sync skills posterior si afecta).

¿Procedemos con Opción C o preferís otra?
