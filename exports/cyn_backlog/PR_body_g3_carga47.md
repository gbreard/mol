## SPEC S1C-G3 — cierre del loop de Cyn a escala: 47 denominaciones validadas

**Primer cierre de loop del proyecto a escala.** Por primera vez el trabajo de Cyn vuelve
al procesamiento masivamente, contra (b)=0 de P-14 (ninguna corrección de Cyn había vuelto
como regla/entrada). Branch `spec/s1c-g3-cierre-loop`. **No mergear — el merge es de Gerardo.**

Fuente: `docs/export_validacion_denominaciones_cyn_2026-06-24-v1.xlsx` (Cyn) →
`docs/DEVOLUCION_validacion_cyn_procesada.md` (harness). La validación de Cyn es la verdad de
dominio: se cargó tal cual, con dry-run de blast-radius como única red.

### Qué se cargó (GRUPO A)

- **42 denominaciones nuevas** al diccionario `sinonimos_argentinos_esco.json`, cada una por
  su **esco_code** validado por Cyn → resuelve por código vía `code_to_occupation`. **47/47
  resuelven** por código (0 sin resolver, 0 a label arbitrario).
- **UPDATE `intendente de obra`**: 5153.1 (conserje, mi carga previa errada) → **3123.1.1
  capataz de construcción**. Caso semilla cerrado por Cyn: era capataz, no conserje ni
  vigilante — coincide con el dominio de Gerardo. El error previo fue pérdida de contexto en
  la carga, no de la validación.
- **+esco_code a `ejecutivo comercial`** (entrada legacy de Cynthia 2026-04-08, mismo target
  3322.1) — cubre también `sales executive`. No se clobbeó la entrada rica existente.
- **HOLD `lobos`** (1): la nota de Cyn dice que el título es una **localidad** mal tomada
  como denominación. Cargar "lobos"→director comercial forzaría ofertas de la ciudad de
  Lobos. No hay denominación segura → no se carga.
- **dedup** `sereno` (aparecía 2 veces, mismo código).

### Dry-run de blast-radius (la red)

7 denominaciones matchean >15 ofertas: `ejecutivo comercial`(504, ya cubierta),
`telemarketer`(136), `sales executive`(56, ya cubierta), `generalista de rrhh`(45),
`vigilador/a`(35), `sommelier`(25), `sereno`(17). **Todas son denominaciones estables**
(target único validado por Cyn, NO están en HOJA 2) → es cobertura correcta, no
sobre-generalización. Cargadas con `_flag` para vigilar regresión. El único caso de
sobre-generalización real (`lobos`, localidad) fue a HOLD.

### Fix de especificidad (longest-match)

Cargar 42 variantes destapó **colisiones de substring**: una denominación genérica tapaba a
una más específica que la contiene. `_match_by_argentino_dict` ahora elige la **variante más
larga (más específica) que matchea**, no la primera en orden de inserción:

- `vigilador/a de personal` (3122 supervisor) ya no cae en `vigilador/a` (5414 seguridad).
- `sales executive` (3322) ya no cae en `sales`→vendedor (5223, colisión legacy pre-existente).

### Medición de regresión en TEST (93 ofertas reservadas)

Métrica = **regresión, no generalización** (P-26/27: las denominaciones de Cyn son
casi-únicas; el hold-out no mide generalización, mide si la carga rompe algo).

- **0 regresiones reales** (ninguna oferta no-fuente que acertaba pasó a errar).
- 2 ofertas cambiaron, **ambas ganancias** y ambas son **fuentes GRUPO A** que caen en TEST:
  `7835523819` oficial de la Armada (0110) → jefe de equipo de seguridad (5414); `7975002320`
  caucho (8141) → operador CNC (7223). Corrección de Cyn aterrizando.
- 15 de las 47 fuentes caen en TEST; solo 2 cambiaron (las groseramente mal) — el resto ya
  acertaba o lo pisa una regla. **Mecanismo probado** end-to-end sobre las fuentes.
- El longest-match es un cambio amplio (afecta todo el dict); TEST (93, estratificado) es el
  proxy y mostró 0 regresiones. El valor real se ve en producción cuando el término reaparece.

> Cifra de Cyn: de 50 denominaciones con código, el sistema erraba en ~31 (**62%**) — en
> denominaciones ausentes de ESCO el sistema falla más de la mitad de las veces. Por eso el
> vocabulario argentino corrige donde el sistema más falla.

### Taxonomía de contexto archivada (Eje 4, NO al diccionario)

`exports/cyn_backlog/taxonomia_contexto_cyn.md`: **GRUPO B** (`Sobrestante de obra`, 2 códigos
según tareas) + **HOJA 2** (6 familias — operario, técnico, arquitecto, pintor, editor,
herrero — 37 denominaciones con árboles de desambiguación). Es la **especificación experta de
las futuras reglas de contexto del Eje 4** (calificador → código). Primer cuerpo de taxonomía
ocupacional argentina documentada. Anclado al Eje 4 junto a los 104 override-duro y el
fallback label-LIKE de `_resolve_rule_target` (deuda P-01 reubicada — NO se tocó acá).

### Bug NLP registrado (aparte)

`docs/issues/2026-06-30_bug_limpieza_titulo_nlp_ruido.md`: 5 títulos llegaron con ruido sin
limpiar (`Ref 20826`, `(id: 6834)`, `ms044ka`) y el sistema clasificó sobre basura. Es del
paso de limpieza del NLP, independiente del diccionario. Workaround: se cargó la denominación
limpia (marcadas `_flag: NLP`); la raíz queda para resolver.

### Commits

- `33a37937` Paso 0 — limpieza resolver (código muerto + inversa ruidosa)
- `d098b302` Parte 3 — re-routeo dict por esco_code + 6 denominaciones (control previo)
- `13a620d4` **GRUPO A — 47 denominaciones de Cyn + longest-match**
- `50efb84d` Parte 4 — taxonomía contexto (Eje 4) + bug NLP

MATCHER 3.5.5 → **3.5.8**. Tests: 16 verdes (`test_s1c_g3_grupoA.py`, `_resolver_codigo`,
`_paso0_resolver`, `test_spec_j_coherencia`). 0 regresión en TEST.

### Lo que NO se tocó
- Canal de reglas (`_resolve_rule_target`, fallback label-LIKE vivo) — deuda Eje 4.
- `tests/harness/` previos, `config/training_pairs.json`, `metrics/gold_set_history.json`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
