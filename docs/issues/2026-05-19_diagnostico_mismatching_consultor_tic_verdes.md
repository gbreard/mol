# Diagnóstico — Mismatching sistémico vía reglas de negocio (caso "consultor de TIC verdes")

**Fecha:** 2026-05-19
**Tipo:** investigación read-only (sin cambios en datos/código)
**Disparador:** hallazgo en medición SPEC AR-Cat — "consultor de TIC verdes" aparece como la 4ª ocupación más frecuente (506 ofertas en universo, 526 actualmente en BD)
**Severidad estimada:** alto (~2,400 ofertas con `esco_label` críticamente incorrecto, ~3.5% del universo)

---

## 1. Resumen ejecutivo

El alto volumen de "consultor de TIC verdes/consultora de TIC verdes" **no es un fenómeno semántico catch-all**, sino un **bug puntual en una regla de negocio** (`R238_analista_it`) que asigna ese label europeo hyper-específico (consultoría en sustentabilidad TIC) a cualquier oferta cuyo título contenga "analista" + `area_funcional = IT`.

**Hallazgo más amplio:** este patrón se repite en otras reglas de `reglas_forzar_isco`. **259 de 358 reglas (72%)** están marcadas con `_linaje.requiere_revision = true`. Al menos **3 reglas críticas afectan ~1,715 ofertas** con labels completamente desalineados del título real (analistas IT/RRHH/Comercial mapeados a labels que describen otras ocupaciones). Otras ~7 reglas con keyword genérica (ej. "operario" a secas) afectan ~225 ofertas con labels muy específicos no justificados.

**Total impacto estimado del problema:** ~**2,400 ofertas** (3.5% del universo de 68,152) con `esco_label` críticamente incorrecto.

**Implicación para SPEC AR-Cat:** la medición original del universo a curar (4,087 combinaciones únicas) **está inflada por bugs de labels europeos mal asignados**, no por la diversidad real del mercado argentino. El primer trabajo antes (o en paralelo a) AR-Cat es **auditar y corregir las 259 reglas con `requiere_revision: true`**, que pueden colapsar el universo a curar antes de cualquier curación humana.

---

## 2. Diagnóstico del caso "consultor de TIC verdes" (526 ofertas)

### 2.1 Origen confirmado

| Dimensión | Valor | Lectura |
|---|---|---|
| `regla_aplicada = R238_analista_it` | **521 de 526 (99%)** | Origen único, NO es catch-all |
| `occupation_match_score` | 0.980 (constante) | Score artificial, fijado por la regla |
| `occupation_match_method = regla_negocio_R238_analista_it` | 521 (99%) | Reconfirma origen |
| `decision_metodo = regla_prioridad` | 404 (77%) | Regla ganó sobre semántico |
| `decision_metodo = dual_coinciden` | 109 (21%) | Casualmente el semántico también devolvía 2511, pero con otro label |
| `validacion_humana` | **0 de 526** | Ningún humano ha validado todavía estas ofertas |

### 2.2 Definición de la regla R238

```json
{
  "id": "R238_analista_it",
  "nombre": "Analista IT/Sistemas",
  "prioridad": 0,
  "condicion": {
    "titulo_contiene_alguno": ["analista"],
    "area_funcional_es": "IT",
    "titulo_no_contiene_alguno": ["seguridad", "datos", "data"]
  },
  "accion": {
    "forzar_isco": "2511",
    "esco_label": "consultor de TIC verdes/consultora de TIC verdes",
    "esco_code": "2511.7"
  },
  "_linaje": { "requiere_revision": true }
}
```

**ISCO 2511 (Analistas de sistemas) es correcto.** El bug está en el `esco_label`: "consultor de TIC verdes" es una ocupación ESCO hyper-específica de sustentabilidad ambiental aplicada a TIC, no genérica.

### 2.3 Evidencia — títulos reales matcheados (top 15 de 526)

```
27  Analista funcional
11  Analista funcional semi senior
 7  Analista funcional IT
 7  Analista de aplicaciones SAP SSR. (rosario)
 7  Analista de desarrollo analítico
 7  Analista de sistemas
 7  Analista funcional SR
 7  Analista SR. de soporte IT (o365)
 7  Analista funcional implementador odoo
 6  Analista de infraestructura
 6  Analista funcional SSR
 5  Analista IT
 5  Analista soporte técnico
 5  Analista funcional ERP
 5  Analista / focal point de telecomunicaciones
```

**Veredicto:** los 526 son analistas IT reales (funcional, SAP, BI, soporte, infraestructura). El ISCO 2511 es correcto. **Únicamente el `esco_label` está mal**: debería ser "analista de sistemas de TIC" (que YA existe en BD con 479 ofertas correctamente etiquetadas con ese label desde el matching semántico).

### 2.4 Distribución de labels ESCO bajo ISCO 2511 en BD

```
414  consultor de TIC verdes/consultora de TIC verdes   ← producido por R238 (BUG)
399  analista de sistemas de TIC                        ← correcto, vía semántico
 31  analista de datos
 27  ingeniero de inteligencia artificial
 19  ingeniero de datos
 16  científico de datos
 15  consultor de TIC/consultora de TIC
 13  arquitecto de sistemas de TIC
 12  consultor de investigación en TIC
 10  ingeniero de integración
  9  analista de negocios de TIC
  8  gestor de análisis empresariales de las TIC
```

El label correcto **ya existe en el sistema** y es el segundo más usado. La regla R238 está sobre-escribiendo lo que el semántico haría bien.

---

## 3. Patrón sistémico — otras reglas con problema similar

### 3.1 Búsqueda de reglas con `_linaje.requiere_revision = true`

| Métrica | Valor |
|---|---|
| Total reglas en `reglas_forzar_isco` | 358 |
| Reglas con `requiere_revision = true` | **259 (72%)** |
| Total ofertas con regla aplicada | 44,850 |
| % universo cubierto por reglas | ~66% |

### 3.2 Reglas críticas — label totalmente desalineado del título real

| Regla | Ofertas | Keyword | ISCO | Label asignado (incorrecto) | Label correcto sugerido |
|---|---:|---|---|---|---|
| **R238_analista_it** | **495** | "analista" + area IT | 2511 | consultor de TIC verdes | analista de sistemas de TIC |
| **R226_analista_rrhh** | **559** | "analista" + area RRHH | 2423 | asesor de orientación profesional | analista/especialista en RRHH |
| **R229_analista_comercial** | **661** | "analista, ejecutivo" + area Ventas | 3322 | representante comercial | parcial: "ejecutivo X" sí matchea, "analista" no |
| **R239_analista_operaciones** | 423 | "analista" + area Operaciones | 2421 | analista de logística | analista de operaciones/procesos |
| **Subtotal críticas** | **2,138** | | | | |

**Patrón común:** la condición es "title contiene `analista`" → fuerza un label específico de ese rubro. Mezcla todos los analistas (funcional, de datos, de soporte, generalista, de selección, de comercio exterior...) en una sola ocupación europea hyper-específica.

### 3.3 Reglas con keyword genérica → label hyper-específico

| Regla | Ofertas | Keyword | Label asignado | Problema |
|---|---:|---|---|---|
| R348_operario_plastico_soplado | 11 | "operario" (a secas!) | operador máquinas moldear plástico por soplado | Keyword no específica el material |
| R318_operador_produccion | 3 | "operador de producción" | operador de prensa hidráulica | "Producción" ≠ prensa hidráulica |
| R343_inyector_plastico | 3 | "inyector plástico" | operador máquinas moldear plástico por inyección | Defensible pero estrecho |
| R128_programador_cnc | 56 | "programador cnc" | operador de máquinas CNC | Downgrade (programador → operador) |
| R315_operario_metalurgico | 8 | "operario metalúrgico" | operador de máquinas CNC | Sector ≠ máquina |
| R346_operario_corte_laser | 20 | "corte láser" | operador de cortadora láser | OK probablemente |
| R246_jefe_calidad | 80 | "jefe de calidad" | director de control de calidad **EN INDUSTRIAS** | Asume sector industrial siempre |
| R330_fiambrero | 6 | "fiambrero" | vendedor especializado en **pescado y mariscos** | Fiambrero no vende pescado |
| R53_operario_plastico | 33 | "inyección, soplado, moldeo" | operador máquinas para **muebles** de plástico | Asume muebles |
| **Subtotal específicas** | **220** | | | |

### 3.4 Reglas con label generalista (probablemente OK pero merecen revisión)

| Regla | Ofertas | Label | Veredicto |
|---|---:|---|---|
| R111_vendedor_generico | 3,538 | vendedor especializado/vendedora especializada | OK (genérico aceptable) |
| R240_operario_produccion | 1,735 | trabajador de fábrica | OK |
| R49_jefe_generico | 1,369 | jefe de departamento | OK |
| R235_mecanico | 1,030 | mecánico de vehículos | **Discutible** — un "mecánico" sin especificar podría ser industrial, naval, aeronáutico |
| R110_tecnico_mantenimiento | 457 | mecánico de maquinaria industrial | **Discutible** — "técnico de mantenimiento" no implica industrial |
| R175_operario_limpieza | 422 | operario de limpieza de edificios | OK probablemente |
| R353_operario_carga_descarga | 429 | mozo de almacén | OK |
| R275_operario_deposito_almacen | 393 | operario de logística de almacén | OK |
| R100/R140_mucama_hotel | 142 | camarero de pisos/camarera de pisos | Es traducción europea de "mucama" — formalmente OK |

### 3.5 ISCOs con múltiples labels distintos asignados por reglas

| ISCO | Cantidad labels | Labels (sample) |
|---|---:|---|
| 2411 | 4 | analista de presupuestos, auditor de cuentas, analista contable, contable |
| 5223 | 4 | vendedor especializado, vendedor pescado/mariscos, vendedor vehículos, vendedor ferretería |
| 1324 | 4 | director distribución, jefe almacén, director cadena suministro, director compras |
| 8142 | 4 | operador soplado, operador inyección, operador prensa hidráulica, operador muebles plástico |
| **2511** | **3** | **analista de sistemas TIC, consultor de TIC verdes, arquitecto de sistemas TIC** |
| 9112 | 3 | operario limpieza edificios, camarero de pisos, operario limpieza aseos |
| 7223 | 3 | tornero, operador CNC, operador cortadora láser |
| 3512 | 3 | agente asistencia TIC, gestor asistencia TIC, técnico de TIC |

Reglas múltiples bajo el mismo ISCO pero con labels distintos **no son malo en sí** (el ISCO 5223 sí incluye distintos vendedores especializados), pero indican falta de criterio uniforme.

---

## 4. Cruzar con validación humana

| Fuente | Resultado |
|---|---|
| Validación humana sobre R238_analista_it (495 ofertas) | **0 ofertas validadas** — ningún humano ha tocado estas todavía |
| `estado_revision` en R238 | 521/521 = null |
| Issue en tabla `issues` mencionando "TIC verdes" o "R238" | **1 issue resuelto** (`0271a261`) — pero **defiende el ISCO 2511**, no menciona el problema del label |

**Lectura:** este bug **no ha sido detectado por ningún validador humano** hasta ahora. Es invisible al flujo de validación porque el ISCO es correcto y los analistas (Cyn, Diego) probablemente validan en base a ISCO, no a label ESCO específico. **Es deuda silenciosa.**

---

## 5. Severidad e impacto

### 5.1 Por nivel de gravedad

| Nivel | Reglas | Ofertas | % universo (68,152) |
|---|---:|---:|---:|
| **Crítico** (label totalmente desalineado) | 4 (R238, R226, R229, R239) | **2,138** | 3.1% |
| **Alto** (kw genérica → label específico no justificado) | 9 | **220** | 0.3% |
| Medio (label más específico que título justifica) | 3 (R235, R110, R246) | 1,567 | 2.3% |
| Total con label probablemente incorrecto | **16+ reglas** | **~3,925 ofertas** | **~5.8%** |

### 5.2 Impacto en SPEC AR-Cat (medición previa)

La medición de universo (4,087 combinaciones únicas) **está inflada por estos bugs**:
- "consultor de TIC verdes" aparece en top 30 como #28 con 506 ofertas — **artificial**, debería desaparecer del top con un fix.
- "asesor de orientación profesional" (top 23 con 535 ofertas) — buena parte viene de R226 mal aplicada.
- "representante comercial" (top 1 con 4,435 ofertas) — incluye contribución cruzada de R229.
- Combinaciones largas con count <5 inflan el conteo de 4,087 sin representar diversidad real.

**Estimación post-fix:** corregir las 16+ reglas reduciría las combinaciones únicas en ~5-10% y limpiaría 3-5 entradas del top 30, mejorando la calidad de cualquier curación humana posterior.

---

## 6. Opciones de resolución

### 6.1 Opción A — Fix puntual R238 únicamente

- Cambiar `esco_label` en R238: "consultor de TIC verdes" → "analista de sistemas de TIC"
- Re-rematch ofertas afectadas (495)
- Marca `_linaje.requiere_revision = false`
- **Costo:** 1 hora
- **Beneficio:** elimina caso emblemático del top 30
- **Limitación:** deja los otros ~3,400 mismatches en pie

### 6.2 Opción B — Sprint de auditoría de las 16+ reglas críticas/altas identificadas

- Revisar las 13 reglas listadas en secciones 3.2 y 3.3
- Para cada una: ¿el label es correcto? ¿el ISCO también? ¿hay que separar la regla en sub-reglas?
- Re-rematch las ~2,400 ofertas afectadas
- **Costo:** 1-2 días-persona
- **Beneficio:** limpia ~3.5% del universo
- **Recomendación**: **opción mínima razonable**

### 6.3 Opción C — Auditoría completa de las 259 reglas con `requiere_revision`

- Plan de revisión sistemático para las 259 reglas
- Criterios: label coherente con ISCO, condición no genérica, sin sobre-escritura del semántico cuando éste ya está bien
- **Costo:** 1-2 semanas-persona
- **Beneficio:** elimina deuda técnica completa de reglas
- **Riesgo:** sin protocolo claro de revisión, fácil meter más bugs

### 6.4 Opción D — Auditoría asistida por LLM + revisión humana

- Pasar las 259 reglas + sample de 10 ofertas matcheadas por cada una a LLM
- LLM clasifica cada regla en: OK / cambiar label / cambiar condición / archivar
- Humano valida solo las flageadas (~100-150)
- **Costo:** 2-3 días-persona + ~$5-10 LLM
- **Beneficio:** sistemático y escalable
- **Riesgo:** LLM puede equivocarse, hay que validar muestreo

---

## 7. Decisiones pendientes para Gerardo

1. **¿Prioridad relativa a SPEC AR-Cat?**
   - Hacer este fix **antes** de medir/curar denominaciones AR (recomendado: la medición SPEC AR-Cat estará viciada de lo contrario).
   - Hacerlo **en paralelo** (riesgo: conflicto de actores sobre mismas reglas).
   - Hacerlo **después** (riesgo: Cyn cura denominaciones AR sobre labels europeos incorrectos).

2. **¿Cuál opción? (A, B, C, D)**
   - Recomendación: **B (auditoría de las 16 críticas/altas)** como mínimo, y planificar **D (LLM-assisted)** para las restantes.

3. **¿Cómo manejar las ofertas YA validadas por humanos cuyo label era incorrecto?**
   - 0 ofertas R238 están validadas (no aplica aquí), pero podría aplicar a R226/R229/R235 — verificar antes.
   - Si hay validadas con label incorrecto: ¿desbloquear con `admin_unlock_validated` + re-rematch + re-validar? (proceso pesado).

4. **¿Hacer regla nueva "audit pattern" para detectar futuros R238?**
   - Validación V31: bandera reglas con `keywords ⊆ {operario, analista, técnico, gerente, jefe}` AND `esco_label contiene palabras hyper-específicas`.
   - Costo bajo, evita reincidencia.

5. **¿Re-revisar el issue resuelto `0271a261`?**
   - El issue justifica que 2511 es correcto pero no toca el label. Posiblemente la justificación humana involuntariamente cubrió un fix incompleto.

---

## 8. Anexos

### 8.1 Cómo se identificó el patrón

```sql
-- En BD (Supabase ofertas_dashboard)
SELECT regla_aplicada, COUNT(*) AS ofertas, AVG(occupation_match_score) AS score
FROM ofertas_dashboard
WHERE esco_occupation_label = 'consultor de TIC verdes/consultora de TIC verdes'
GROUP BY regla_aplicada
ORDER BY ofertas DESC;
-- → 521 ofertas vienen de R238_analista_it

-- En código (config/matching_rules_business.json)
-- Buscar reglas_forzar_isco.R238_analista_it:
--   accion.esco_label = "consultor de TIC verdes/consultora de TIC verdes"  ← BUG
```

### 8.2 Top 30 reglas por volumen — referencia

Ver bloque en sección 3 (filas con `requiere_revision = true` están marcadas).

### 8.3 Archivos de evidencia (efímeros)

- `/tmp/tic_verdes.pkl` — 526 ofertas con regla R238
- `/tmp/reglas_volumen.pkl` — Counter de reglas top en BD

### 8.4 Relación con otros docs

- `docs/issues/2026-05-19_investigacion_denominaciones_argentinas.md` — investigación previa que motivó la medición SPEC AR-Cat
- `docs/specs/spec_ar_cat/MEDICION_UNIVERSO_v1.md` — medición de universo a curar (4,087 combinaciones), **inflada por estos bugs**
- `config/matching_rules_business.json` — fuente única de reglas (358 totales, 259 con `requiere_revision`)

---

**Cierre:** investigación read-only completa. Sin cambios en código, datos ni schema. Decisión de scope y opción de resolución pendiente de Gerardo.
