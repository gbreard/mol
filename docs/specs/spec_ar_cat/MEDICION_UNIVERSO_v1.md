# SPEC AR-Cat — Medición del Universo a Curar (v1)

**Fecha:** 2026-05-20
**Autor:** Claude (read-only investigation)
**Estado:** medición concluida, pendiente decisiones de scope
**Refs:**
- `docs/issues/2026-05-19_investigacion_denominaciones_argentinas.md` (investigación previa SPEC W D.3)
- `config/sinonimos_argentinos_esco.json` (22 KEYs, 32 URIs)
- Tabla `esco_argentino` Supabase (44 filas)
- `ofertas_dashboard` Supabase (68,152 filas, 100% con isco+esco)

---

## Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Total ofertas con isco+esco poblado | **68,152 (100%)** |
| **Combinaciones únicas ISCO+ESCO en el universo** | **4,087** |
| Combinaciones que cubren 50% del volumen | **38** |
| Combinaciones que cubren 80% del volumen | **259** |
| Combinaciones que cubren 95% del volumen | **1,878** |
| Cubiertas por al menos una fuente argentina existente | **50.1% del volumen** (249 combinaciones) |
| A curar desde cero | **49.9% del volumen** (3,838 combinaciones) |
| **Tiempo Cyn para cubrir 80% volumen (curado priorizado)** | **~43 días** (259 combos × 10 min, 6/día) |
| Tiempo Cyn para cubrir 95% volumen | **~313 días** (1,878 combos) |

**Hallazgo clave:** la distribución es muy long-tail. **38 combinaciones cubren la mitad de las ofertas**, pero llegar al 95% requiere curar **~1,878** (45 veces más). El esfuerzo se concentra en los primeros 250–300 ítems si Gerardo acepta priorización por frecuencia.

---

## 1. Distribución de frecuencias

### 1.1 Curva acumulada (volumen ofertas)

```
Cobertura  |  Combinaciones necesarias
─────────────────────────────────────
   50%     |        38   (0.93% del catálogo)
   80%     |       259   (6.34%)
   95%     |     1,878   (45.95%)
  100%     |     4,087   (100%)
```

### 1.2 Top 30 combinaciones más frecuentes (45.5% del volumen)

| # | ISCO | count | % | % acum | ESCO label |
|---|------|-------|---|--------|------------|
| 1 | 3322 | 4435 | 6.51% | 6.51% | representante comercial |
| 2 | 5223 | 3469 | 5.09% | 11.60% | vendedor especializado/vendedora especializada |
| 3 | 2512 | 1931 | 2.83% | 14.43% | desarrollador de software/desarrolladora de software |
| 4 | 4110 | 1869 | 2.74% | 17.17% | empleado de oficina/empleada de oficina |
| 5 | 2411 | 1611 | 2.36% | 19.54% | contable |
| 6 | 9329 | 1511 | 2.22% | 21.75% | trabajador de fábrica/trabajadora de fábrica |
| 7 | 1219 | 1287 | 1.89% | 23.64% | jefe de departamento/jefa de departamento |
| 8 | 9333 | 1122 | 1.65% | 25.29% | mozo de almacén/moza de almacén |
| 9 | 4311 | 1018 | 1.49% | 26.78% | empleado de contabilidad/empleada de contabilidad |
| 10 | 4222 | 1017 | 1.49% | 28.28% | agente de centro de atención al cliente |
| 11 | 7233 | 735 | 1.08% | 29.35% | mecánico de maquinaria industrial |
| 12 | 5230 | 717 | 1.05% | 30.41% | cajero/cajera |
| 13 | 2411 | 699 | 1.03% | 31.43% | analista contable |
| 14 | 8322 | 694 | 1.02% | 32.45% | conductor de vehículo de reparto |
| 15 | 9112 | 678 | 0.99% | 33.44% | operario de limpieza de edificios |
| 16 | 7231 | 675 | 0.99% | 34.43% | mecánico de vehículos/mecánica de vehículos |
| 17 | 5223 | 630 | 0.92% | 35.36% | vendedor/vendedora |
| 18 | 3512 | 627 | 0.92% | 36.28% | técnico de TIC/técnica de TIC |
| 19 | 5131 | 601 | 0.88% | 37.16% | camarero/camarera |
| 20 | 4226 | 572 | 0.84% | 38.00% | recepcionista |
| 21 | 7231 | 545 | 0.80% | 38.80% | supervisor de mantenimiento de vehículos |
| 22 | 5120 | 542 | 0.80% | 39.60% | cocinero/cocinera |
| 23 | 2423 | 535 | 0.79% | 40.38% | asesor de orientación profesional |
| 24 | 9412 | 527 | 0.77% | 41.15% | ayudante de cocina |
| 25 | 7412 | 522 | 0.77% | 41.92% | mecánico electricista/mecánica electricista |
| 26 | 2212 | 517 | 0.76% | 42.68% | médico especialista/médica especialista |
| 27 | 2611 | 507 | 0.74% | 43.42% | abogado/abogada |
| 28 | 2511 | 506 | 0.74% | 44.16% | consultor de TIC verdes/consultora de TIC verdes |
| 29 | 9333 | 452 | 0.66% | 44.83% | operario de logística de almacén |
| 30 | 2221 | 448 | 0.66% | 45.49% | enfermero responsable de cuidados generales |

**Observaciones:**
- Notar que el mismo ISCO aparece con múltiples labels ESCO (ej. 5223 en filas 2 y 17, 7231 en 16 y 21, 2411 en 5 y 13, 9333 en 8 y 29). Esto valida la decisión de granularidad ISCO+ESCO.
- Fila 28 "consultor de TIC verdes" (506 ofertas) parece un mismatching sistémico — vale flag aparte (probable mala clasificación, no terminología local).

### 1.3 Top 10 ISCOs con MÁS ocupaciones ESCO distintas (heterogeneidad)

| ISCO | # ESCOs distintos | Total ofertas |
|------|-------------------|---------------|
| 5223 | 104 | 4,646 |
| 1420 | 95 | 624 |
| 1221 | 87 | 1,477 |
| 2431 | 70 | 938 |
| 2511 | 62 | 1,311 |
| 8160 | 51 | 288 |
| 2149 | 48 | 216 |
| 2310 | 47 | 140 |
| 2513 | 46 | 188 |
| 1324 | 46 | 409 |

**Interpretación:** ISCO 5223 (vendedores) tiene 104 sub-ocupaciones ESCO distintas en el universo. Confirma que **NO se puede curar a nivel ISCO solo** — la granularidad ESCO captura matices reales que el ISCO de 4 dígitos pierde.

---

## 2. Cobertura por fuentes argentinas existentes

### 2.1 esco_argentino (tabla Supabase, 44 filas)

```sql
-- Schema confirma: NO tiene columnas de denominación AR.
-- Solo esco_occupation_label (ES europeo) + skills_consolidadas + métricas.
```

| Métrica | Valor |
|---|---|
| URIs únicos en `esco_argentino` | 44 |
| URIs del universo (4,087 combos → 2,115 URIs únicos) | 2,115 |
| URIs en intersección (universo ∩ esco_argentino) | **44** (100% de esco_argentino está en universo) |
| Combinaciones del universo cubiertas | **181** (mismas URIs aparecen con distintos ISCO) |
| **Ofertas cubiertas** | **28,524 / 68,152 (41.9%)** |

### 2.2 sinonimos_argentinos_esco.json (22 KEYs → 32 URIs únicos)

| Métrica | Valor |
|---|---|
| KEYs de ocupaciones argentinas | 22 |
| URIs únicos extraídos (incluyendo contextos) | 32 |
| ISCOs únicos extraídos | 40 |
| **Cobertura por URI exacta** | 20,111 ofertas (29.5%) |
| Cobertura por ISCO (más permisiva) | 29,641 ofertas (43.5%) |

### 2.3 Resumen consolidado

```
Total ofertas universo:                       68,152
─────────────────────────────────────────────────────
Cubiertas por esco_argentino (tabla):         28,524 (41.9%)
Cubiertas por sinonimos JSON (URI exacta):    20,111 (29.5%)
Cubiertas por al menos una fuente (unión):    34,120 (50.1%)
NO cubiertas por nada:                        34,032 (49.9%)
─────────────────────────────────────────────────────
Combinaciones universo:                        4,087
Combinaciones cubiertas por unión:               249
Combinaciones a curar desde cero:              3,838
```

**Hallazgo:** las 2 fuentes argentinas existentes **NO contienen denominaciones argentinas** en columna estructurada. `esco_argentino` tiene skills argentinas (D6) pero la denominación es la europea. `sinonimos JSON` tiene la denominación argentina como KEY del diccionario, pero no como dato curado canónico. **Cobertura real de "denominación argentina curada" hoy = 0%.**

Lo que las fuentes sí aportan es **prior knowledge**: 249 combinaciones (50% del volumen) tienen mapping ESCO ya validado por humano (vía catalogación en `esco_argentino` o vía matcher en `sinonimos`), pero todavía falta poblar la traducción AR del label.

---

## 3. Trabajo distribuido por Cyn

### 3.1 Si Cyn audita 30 ofertas/día (cuestionario MOL — capacidad reportada)

Simulación 1000 muestras random uniformes sobre las 68,152 ofertas:

```
Combinaciones únicas vistas en una sesión de 30 ofertas:
  Promedio: 25.8
  Mediana:  26
  Rango:    17–30
```

Significa: Cyn ve **~26 ocupaciones distintas por día** en muestreo aleatorio. La mayoría (~25 de 26) son combinaciones que aparecen 1+ veces en su pool diario; pocas son repetidas.

### 3.2 Estrategia A: Curado oportunista (Cyn cura cuando topa con error en su día de validación)

Simulación 50 corridas, muestreo random con reemplazo, 30 ofertas/día:

| Cobertura volumen | Día promedio | Notas |
|---|---|---|
| 50% | día 5 | rápido — concentrado en top frecuentes |
| 80% | día 61 | dos meses para cubrir 4 de cada 5 ofertas que ve |
| 95% | día 712 | dos años — long tail muy disperso |

**37 de 50 simulaciones alcanzaron 95% en menos de 730 días.** Las otras 13 no llegaron (long tail genera combinaciones nuevas continuamente).

### 3.3 Estrategia B: Curado priorizado (Cyn cura combos por frecuencia descendente, fuera del flujo de validación diaria)

Asumiendo **10 min/combo** (lectura ESCO label + escribir denominación AR), **6 combos curados/día** (~1 hora):

| Cobertura volumen | Combos a curar | Días-persona |
|---|---|---|
| 50% | 38 | **~6 días** (un rato puntual) |
| 80% | 259 | **~43 días** |
| 95% | 1,878 | ~313 días |
| 100% | 4,087 | ~681 días (~85 días-persona @ 8h/día) |

**Comparativa A vs B para 80%:** B es ~1.4x más rápido (43 vs 61 días). El gap real es **calidad**: en estrategia A, Cyn cura solo lo que ve; en B, cura sistemáticamente la cabeza del histograma.

### 3.4 Recomendación táctica

Hibridar:
- **Sprint dedicado de curación priorizada del top 50** (~9h de Cyn = ~2 jornadas) → cubre 55% del volumen
- **Curado oportunista en flujo de validación** (UI badge editable) para el resto, cuando Cyn detecte denominación faltante o errónea

Esto evita el bloqueo de 43 días seguidos en curación pura y mantiene a Cyn en su flujo de auditoría primario.

---

## 4. Consistencia entre fuentes

| Fuente | URIs únicos |
|---|---|
| esco_argentino (tabla) | 44 |
| sinonimos JSON | 32 |
| **Intersección** | **12** |
| Solo en esco_argentino | 32 |
| Solo en sinonimos | 20 |

**Sin conflictos de ISCO detectados en la intersección** (las 12 URIs comunes tienen mismo ISCO en ambas fuentes).

### 4.1 Las 32 ocupaciones SOLO en esco_argentino (no en sinonimos JSON)

Cubren ocupaciones más amplias (médicos, abogados, ingenieros, programadores) que el JSON de sinonimos no incluye:

| ISCO | ESCO label europeo |
|------|---|
| 8322 | conductor de vehículo de reparto |
| 5414 | vigilante de seguridad |
| 3122 | supervisor de producción |
| 3321 | asesor de seguros |
| 7231 | mecánico de vehículos |
| 2411 | analista de presupuestos |
| 4214 | cobrador de deudas |
| 2141 | ingeniero industrial |
| 4120 | secretario/secretaria |
| 2166 | diseñador gráfico |
| 3341 | supervisor de centro de llamadas |
| 1221 | responsable de marketing |
| 9112 | camarero de pisos |
| 4221 | agente de viajes |
| 2262 | farmacéutico |
| 8142 | operador de máquinas para muebles plástico |
| 5120 | cocinero/cocinera |
| 1219 | jefe de departamento |
| 2611 | abogado/abogada |
| 2212 | médico especialista |
| 3118 | dibujante técnico |
| 2511 | analista de sistemas de TIC |
| 3115 | supervisor de mantenimiento industrial |
| 5243 | vendedor a domicilio |
| 5132 | barista |
| 3334 | agente inmobiliario alquileres |
| 5131 | camarero/camarera |
| 4321 | coordinador de inventario |
| 8322 | chófer privado |
| 2411 | contable |
| 2512 | desarrollador de software |
| 1323 | director de obra |

### 4.2 Las 20 ocupaciones SOLO en sinonimos JSON (no en esco_argentino)

Cubren títulos argentinos comunes que el catálogo curado todavía no procesó:

| ISCO | key JSON | esco_label |
|------|---|---|
| 3123 | capataz | capataz de construcción |
| 7112 | albañil | albañil |
| 3257 | tecnico[seguridad\|higiene] | inspector de seguridad e higiene |
| 1211 | gerente[finanzas\|financiero] | director financiero |
| 4312 | analista de tesoreria | empleado adm. gestión financiera |
| 3512 | tecnico[it\|sistemas\|soporte] | técnico de TIC |
| 1219 | jefe de mantenimiento | director de mantenimiento de fábrica |
| 4110 | administrativo | empleado de oficina |
| 7127 | tecnico[refrigeracion\|aire\|clima] | instalador calefacción/ventilación |
| 3111 | tecnico[quimico\|laboratorio] | técnico laboratorio industrias químicas |
| 1330 | gerente[it\|sistemas\|tecnologia] | gestor proyectos TIC |
| 5223 | vendedor | vendedor/vendedora |
| 1324 | gerente[logistica\|supply chain] | director cadena de suministro |
| 9334 | repositor | reponedor/reponedora |
| 8160 | operador[produccion\|...] | operario producción alimentos |
| 1321 | gerente[operaciones\|...] | director producción industrial |
| 7126 | plomero | fontanero/fontanera |
| 1212 | gerente[rrhh\|recursos humanos] | director recursos humanos |
| 4226 | recepcionista | recepcionista |
| 7421 | tecnico[electronica\|electronico] | técnico reparador electrónica |

**Observación:** las 20 KEYs del JSON ya **son** denominaciones argentinas (ej. "plomero" vs "fontanero", "repositor" vs "reponedor", "capataz" vs "capataz de construcción"). Estas 20 entradas son **el seed natural** para arrancar SPEC AR-Cat — solo hay que migrar la KEY a un campo `denominacion_arg` en `esco_argentino` (o tabla nueva).

### 4.3 Implicación operativa

Las dos fuentes existentes son **complementarias, no redundantes**. Si SPEC AR-Cat unifica:

- 44 (esco_argentino) + 20 (solo sinonimos) = **64 ocupaciones con info parcial argentina** disponibles como base. (12 están en ambas y se mergean sin conflicto.)
- De esas 64, solo 20 tienen denominación AR explícita (las KEYs del JSON). Las 44 de esco_argentino aportan skills curadas pero **no la denominación AR**.

**Para arrancar:** SPEC AR-Cat necesitaría primero migrar las 20 denominaciones del JSON a `esco_argentino.denominacion_arg` (one-time, ~30 min). Después, Cyn cura las 24 restantes de las 44 que no tienen AR. Eso ya cubre las top ~64 ocupaciones — pero esas 64 no necesariamente coinciden con el top 50 por frecuencia, así que vale chequear el overlap antes de tomar este atajo.

---

## 5. Decisiones pendientes para Gerardo

### 5.1 Granularidad

**Confirmado en investigación previa:** ISCO + ESCO (no solo ISCO). Razón: ISCO 5223 tiene 104 sub-ocupaciones ESCO distintas — sería terrible curar "vendedor" para 4,646 ofertas sin distinguir si es de tienda, telemarketing, mostrador, etc.

**Pregunta abierta:** ¿una sola `denominacion_arg` por combo (ISCO, ESCO_URI), o también distinguir por sector/contexto? Ejemplo: "vendedor" (5223 retail) vs "vendedor" (5223 mayorista) vs "vendedor a domicilio" (5243). Si la respuesta es "solo por ESCO URI", el universo se reduce a **2,115 combos únicos** (no 4,087). Mitad del trabajo.

→ **Recomendación:** granularidad `(esco_occupation_uri)` única (no ISCO+URI), porque el URI ya determina el ISCO unívocamente en ESCO. Las duplicaciones ISCO+URI del universo (4,087 vs 2,115) son artefactos del matching, no semántica real. **2,115 combos a curar**, no 4,087.

### 5.2 Estrategia de arranque (prioridad)

Opciones:

| Plan | Descripción | Días Cyn |
|---|---|---|
| **P0** | Migrar 20 denominaciones del JSON sinonimos a `esco_argentino.denominacion_arg` (one-time script) | 0 (automatizable) |
| **P1** | Curar top 50 ESCOs más frecuentes (55% volumen) | ~2 días-persona |
| **P2** | Curar top 250 (80% volumen) | ~10 días-persona |
| **P3** | Curar long tail (95%+) | meses |

→ **Recomendación:** **P0 + P1**. Da 55% de cobertura en 2 días, sin bloquear a Cyn meses. P2 puede ser oportunista vía UI editable.

### 5.3 Modo de curación

- **Opción A**: Cyn cura cada vez que ve la ocupación en su flujo de validación (badge editable inline en `ClasificacionPanel`)
- **Opción B**: pantalla dedicada de curación `/curacion/ocupaciones` con lista ordenada por frecuencia y botón "agregar denominación AR"
- **Opción C**: ambas — A para corrección puntual, B para sprints de curación batch

→ **Recomendación:** **C**. Es el patrón ya validado en otros módulos (admin/procesamiento dual). Pero arrancar con B (más simple), agregar A en sprint posterior.

### 5.4 UI: ¿qué se muestra al validador?

- ¿Mostrar `denominacion_arg` SIEMPRE que esté curada, fallback a `esco_occupation_label` europeo?
- ¿Etiquetar 🇦🇷 / 🇪🇸 explícito en el badge para que Cyn vea de dónde sale la denominación?
- ¿Modo edición inline o modal aparte?

→ **Recomendación:** badge dual `denominacion_arg (esco_label europeo)` cuando ambas existen, fallback a una sola si la otra es NULL. Etiqueta 🇦🇷/🇪🇸 solo en hover/tooltip para no contaminar visualmente.

### 5.5 Scope del schema

`ofertas_dashboard` tiene HOY:
- `denominacion_arg TEXT` (vacía, M024)
- `denominacion_esp TEXT` (vacía, M024)

Tabla `esco_argentino` NO tiene esas columnas.

**Pregunta:** ¿dónde vive la fuente de verdad?

| Opción | Pros | Contras |
|---|---|---|
| En `ofertas_dashboard` (por oferta) | Permite override per-oferta | Duplica info, sync costoso |
| En `esco_argentino` (por ocupación) | Single source of truth, ~2K filas vs 68K | Requiere migración M024 (drop o deprecate columnas oferta) |
| Ambas (catálogo + override) | Flexible | Complejidad |

→ **Recomendación:** **catálogo en `esco_argentino`** (agregar columnas `denominacion_arg`, `denominacion_esp`, `denominacion_arg_curada_por`, `denominacion_arg_curada_at`). Las columnas en `ofertas_dashboard` que ya existen quedan deprecated o se usan para overrides puntuales de oferta-específica (improbable que se necesite). El frontend hace join `ofertas_dashboard.esco_occupation_uri` → `esco_argentino.denominacion_arg`.

### 5.6 Definición de "denominación española"

Ambiguo en el cuestionario. Posibles interpretaciones:
- **A**: el `esco_occupation_label` actual ya ES "español" (europeo). Solo falta etiquetarlo como tal — **gratis, 0 curación**.
- **B**: traducción explícita España vs Argentina con variantes regionales (`fontanero` vs `plomero`). Solo aplica a ~30 ocupaciones donde hay diferencia real.
- **C**: español neutro vs argentino (no aplica realmente — el español neutro no es lengua oficial de nada).

→ **Recomendación:** Opción **A** para el 95% de casos + opción **B** solo cuando Cyn detecta diferencia. No invertir en columna `denominacion_esp` separada si va a ser idéntica a `esco_occupation_label` 95% del tiempo.

---

## 6. Resumen para Gerardo

| Pregunta | Respuesta |
|---|---|
| ¿Cuántas combinaciones únicas hay? | 4,087 (ISCO+URI) o 2,115 (URI sola) |
| ¿Cuántas cubren 80% volumen? | 259 (con granularidad ISCO+URI) |
| ¿Hay overlap entre fuentes argentinas? | Sí: 12 URIs en ambas, sin conflicto |
| ¿Cuántas denominaciones AR explícitas hay HOY? | **20** (las KEYs del JSON sinonimos) |
| ¿Tiempo para Cyn cubrir 80% volumen? | **~43 días-persona** curando por frecuencia (10 min/combo, 6/día) |
| ¿Tiempo para arrancar (top 50)? | **~2 días-persona** = 55% del volumen |
| ¿Las columnas M024 sirven? | Solo si querés override per-oferta. Sino, mover al catálogo. |
| ¿"Denominación española" = europea? | 95% sí (lo que ya hay). Etiquetar como 🇪🇸 cubre el pedido sin curar nada. |

**Recomendación táctica final:**

1. **Migrar las 20 KEYs del JSON sinonimos a un campo `denominacion_arg` en `esco_argentino`** (script one-time, ~30 min de implementación, sin curación humana).
2. **Etiquetar `esco_occupation_label` como 🇪🇸 en el frontend** (cambio UI puro, ~15 min, cubre la parte ES del pedido de Cyn).
3. **Sprint dedicado de curación priorizada top 50 ESCO con Cyn** (~2 días-persona) → 55% del volumen.
4. **UI badge editable inline** en `ClasificacionPanel` para curación oportunista del resto.
5. **Deprecate columnas `ofertas_dashboard.denominacion_arg/esp`** (creadas en M024) si se confirma que el catálogo es la fuente única.

Eso da 55% de cobertura en ~3 días de trabajo combinado humano+técnico, sin bloquear el cierre de SPEC W Sprint 1.

---

## 7. Anexos

### 7.1 Datos crudos

- Query base: `SELECT isco_code, esco_occupation_uri, esco_occupation_label, count(*) FROM ofertas_dashboard WHERE isco_code IS NOT NULL AND esco_occupation_uri IS NOT NULL GROUP BY 1,2,3 ORDER BY count DESC` (simulada vía paginación PostgREST porque PostgREST no soporta GROUP BY directo).
- Total filas procesadas: 68,152
- Combinaciones únicas: 4,087
- URIs únicos: 2,115

### 7.2 Observaciones no concluyentes

- **Fila 28 del top 30**: "consultor de TIC verdes" con 506 ofertas — probable mismatching sistémico (sospechoso). Vale flag aparte como issue de matching, no de curación AR.
- **ISCO 5223 con 104 ESCO labels distintos**: heterogeneidad muy alta. Cyn debe revisar si esto refleja realidad del mercado (vendedores muy variados) o si el matcher abrió demasiado el rango.
- **esco_argentino.esco_occupation_label = ES europeo** está pisando lo que debería ser AR. El nombre de la columna induce a error.

### 7.3 Pendientes de Gerardo antes de SPEC AR-Cat formal

- [ ] Decisión sobre granularidad: ISCO+URI vs URI única (impacta 2x el tamaño del catálogo)
- [ ] Decisión sobre scope del schema: catálogo en `esco_argentino` vs por-oferta en `ofertas_dashboard`
- [ ] Decisión sobre P0 (migración automática de 20 sinonimos) ¿ahora o después?
- [ ] Cuestionario complementario a Cyn: ¿quiere ver "denominación española" cuando ya es la que está? ¿Le sirve el etiquetado 🇪🇸 sin curar?

---

**Cierre:** medición read-only completa. Sin cambios en código ni datos. Decisión de scope pendiente de Gerardo.
