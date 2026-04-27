# SPEC Q — Validación humana de casos sospechosos identificados por Claude

**Fecha:** 2026-04-27
**Autor:** Claude + Gerardo
**Estado:** Draft — listo para entregar a Cyn
**Audiencia primaria:** Cynthia (analista)
**Pre-condición:** SPEC N + O + P aplicados, sync grande Supabase completo
**Complementa:** SPEC M (validación muestra ISCO antes/después)

---

## 1. Por qué este spec

A lo largo de SPEC O y SPEC P, identificamos casos sospechosos donde:
- **A) Perfiles polivalentes** que ESCO no representa bien (debate de equipo pendiente)
- **B) Targets ultra-específicos** asignados a roles genéricos (probable miscoding)
- **C) Reglas que pisan al semántico** masivamente (regla vs ESCO embedding discrepan ≥95%)

Hasta ahora **NO los validamos humanamente** — se documentaron pero quedaron pendientes. Este spec entrega muestras dirigidas a Cynthia para confirmar/descartar nuestras sospechas y guiar fixes futuros.

A diferencia de SPEC M (que valida cambios YA aplicados), este spec valida **casos donde sospechamos que el sistema sigue mal**.

---

## 2. Scope

**101 ofertas estratificadas en 3 grupos:**

| Grupo | Tipo de sospecha | Ofertas | Ofertas afectadas en BD |
|---|---|---:|---:|
| **A** | Perfiles polivalentes (ESCO no apto) | 50 | ~5,800 |
| **B** | Targets ultra-específicos absurdos | 27 | ~1,800 |
| **C** | Reglas con divergencia 95%+ vs semántico | 24 | ~3,500 |

Si Cyn confirma las sospechas: cada caso valida un fix de regla o un código MOL Argentino nuevo (impacto miles de ofertas).

---

## 3. Detalle por grupo

### Grupo A — Perfiles polivalentes (50 ofertas)

10 reglas × 5 ofertas c/u. Cada regla representa un rol argentino que ESCO clasifica fragmentado:

| Regla | Rol argentino | Cobertura | Sospecha |
|---|---|---:|---|
| R162_tecnico_mantenimiento_edilicio | Técnico polivalente edilicio | 140 | electricidad+plomería+climatización combinadas |
| R110_tecnico_mantenimiento | Técnico mantenimiento industrial | 353 | mismo perfil polivalente |
| R49_jefe_generico | Jefe genérico PyME | 1,042 | "jefe" sin especialidad pisa varios ESCOs |
| R170_asesor_comercial | Asesor comercial PyME | 1,199 | ventas + ATC + admin combinadas |
| R34_cajero | Cajero argentino | 556 | atender + cobrar + reponer |
| R166_cocinero_planchero | Cocinero planchero | 426 | cocina completa en PyME |
| R31_mozo_camarero | Mozo argentino | 418 | atender + cobrar + barra |
| R109_ejecutivo_ventas | Ejecutivo de ventas | 757 | ventas B2B + cuentas + admin |
| R15_customer_care | Customer care | 505 | ATC + ventas + soporte |
| R226_analista_rrhh | Analista RRHH | 408 | label ESCO raro pero ISCO 2423 OK |

**Si Cyn confirma:** alimentan decisión del equipo sobre Catálogo MOL Argentino (ver `docs/plan/15_PERFILES_POLIVALENTES_AR.md`).

### Grupo B — Targets ultra-específicos (27 ofertas)

9 ESCO codes × 3 ofertas c/u. Detectados por SPEC O M1 (regla genérica → ESCO ultra-específico):

| ESCO | Label | Cobertura | Por qué sospechoso |
|---|---|---:|---|
| 3331.2.1 | especialista importación/exportación | 261 | reglas múltiples lo apuntan |
| 3323.2.2 | comprador de TIC | 386 | "compras" genérico → comprador IT |
| 1221.3.3 | director de promoción | 174 | "gerente ventas" → director promoción |
| 3321.3.1 | asesor de seguros | 225 | OK pero verificar variantes |
| 3323.2.1 | comprador café verde | 96 | absurdo (Argentina no produce café) |
| 2131.4.2 | bioquímico | 80 | confirmar |
| 1221.3.2 | responsable marketing | 148 | confirmar |
| 5132.1.1 | barista | 131 | OK probablemente |
| 1431.2.1 | jefe de sala | 97 | confirmar |

**Si Cyn confirma 3+ casos absurdos en un código:** fix rule (cambio target).

### Grupo C — Reglas con divergencia masiva (24 ofertas)

8 reglas × 3 ofertas c/u. Detectadas por SPEC O M3 (dual_coinciden=0 ≥95% en n≥100):

| Regla | Cobertura | Tasa diff | Sospecha |
|---|---:|---:|---|
| R240_operario_produccion | 1,101 | 99% | semántico discrepa — fallback genérico |
| R229_analista_comercial | 497 | 98% | "analista" vs "ejecutivo" mezclados |
| R48_secretaria_admin | 321 | 98% | rol polivalente probable |
| R241_tecnico_it | 297 | 99% | técnico IT tiene muchas variantes |
| R323_atencion_publico | 287 | 100% | ATC genérico |
| R305_electromecanico | 266 | 98% | electromecánico polivalente |
| R91_jefe_mantenimiento | 241 | 98% | jefe + mantenimiento |
| R30_community_manager | 175 | 100% | role nuevo, ESCO desactualizado |

**Si Cyn confirma:** estas reglas pasan al pipeline de propagación (estilo SPEC O R228/R236/R237).

---

## 4. Entregable a Cyn

Carpeta: **`exports/spec_q/`**

```
exports/spec_q/
├── INSTRUCCIONES_CYN.md      (instructivo corto)
└── ids_validar_cyn.txt       (101 IDs agrupados por grupo + caso)
```

Cyn trabaja con el flujo habitual de `/admin/validacion` (mismo que SPEC M).

---

## 5. Cronograma

| Fase | Duración | Quién |
|---|---:|---|
| Entrega paquete a Cyn | inmediato | Gerardo |
| Validación humana | ~2-3 hs | Cyn (puede repartir con Diego) |
| Análisis de issues nuevos | 30 min | Claude |
| Decisiones según hallazgos | 1 hr | Equipo |
| Aplicación de fixes confirmados | 1-3 hs | Claude |

**Total wall-clock estimado:** 1-2 días.

---

## 6. Decisiones según resultado

### Grupo A (polivalentes)
- **Si Cyn confirma 5+ casos en una regla:** entra al Catálogo MOL Argentino (escala a debate de equipo).
- **Si discrepa con la sospecha (ej: dice que el ESCO es OK):** desactivar warning, mantener sin tocar.

### Grupo B (targets absurdos)
- **Si 2+ casos del mismo código son absurdos:** crear SPEC R con fix de target (estilo R236 SPEC O).
- **Si solo 1 caso:** dejar pendiente para revisión más amplia.

### Grupo C (regla pisa semántico)
- **Si la regla es claramente peor que el semántico:** desactivar regla.
- **Si la regla está bien (corrige al semántico):** documentar y mantener.

---

## 7. Lo que este spec NO hace

- NO aplica fixes — solo recolecta evidencia humana.
- NO sustituye SPEC M (validación de cambios YA aplicados).
- NO toca pipeline ni reglas hasta tener feedback Cyn.

---

## 8. Próximo paso

Una vez Cyn termine la revisión:
- Claude consume issues nuevos creados.
- Genera reporte por grupo con conteos y recomendaciones.
- Equipo decide qué fixes aplicar y cuáles archivar.
