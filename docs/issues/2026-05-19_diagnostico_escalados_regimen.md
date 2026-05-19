# Diagnóstico: 40% de escalados del régimen es mayormente ruido

**Fecha:** 2026-05-19
**Origen:** Análisis post-régimen 15-17 mayo
**Estado:** Diagnóstico completo. Implementación PAUSADA hasta input de Cyn.

## TL;DR

El "40% de escalados" del régimen NO es un problema de matching.
De los 104.372 errores escalados acumulados:
- 87.8% (91.606) es ruido que no debería escalar
- 12.2% (12.766) son errores reales de matching

## Composición del ruido

### Categoría A — Errores upstream (69.6%, 72.686 escalados)
V14 descripción corta, V12/NQ12 provincia vacía, V16 CLAE missing,
V11/V29 tareas vacías. Son fallos del scraper o LLM, no del matcher.
No deberían pasar al auto-corrector.

### Categoría B — V28 sobre-disparando (9.4%, 9.775 escalados)
"Sin skills esenciales matcheadas" se dispara cuando ESCO target tiene
skills muy específicas (académicas) y la oferta tiene skills prácticas.
Cruzando con gold set: humano valida estas como OK o "revisar", no error.

### Categoría C — Bug V27 (0.4%, 454 escalados)
454 casos reportan "regla difiere de semántico" cuando
ISCO_regla == ISCO_semantico (mismo ISCO). Lógica V27 escala por
divergencia de skills aunque ISCO coincida. Falso positivo claro.

### Categoría D — Warnings informativos (8.3%, 8.691 escalados)
V18, V20-V22, V24, V26, V30. No son errores, son flags informativos
(ej: "sector igual a área"). Escalan sin necesidad.

## Lo que SÍ funciona

V31_ocupacion_esco_incorrecta (severidad alto): 499 casos auto-corregidos
con fix_v31_excluir_reglas (42% tasa de corrección). Demuestra que el
modelo del corrector está bien diseñado, solo necesita más reglas
específicas tipo fix_v31_*.

## Hallazgos puntuales para revisar con Cyn

- R111_vendedor_generico: 2.575 V28. La regla está bien, las ofertas son
  vendedores reales, pero las "skills esenciales" del ESCO target
  (vendedor especializado, 5223) son muy específicas y no las extrae el
  LLM en ofertas comunes.
- R30_community_manager: el semántico dice 1330 (gerente TIC) cuando la
  regla dice 2432 (community manager) — el semántico está descalibrado
  para este caso.
- R275_operario_deposito_almacen: tiene 114 V27 falsas — ISCO 9333 = 9333
  pero igual escala.

## Recomendaciones (NO implementar todavía)

| # | Acción | Impacto | Esfuerzo |
|---|--------|---------|----------|
| R1 | Reclasificar Categoría A a severidad info + no escalar | -69.6% ruido | 30 min |
| R2 | V28: bajar severidad warning → info, criterio adicional "revisar humano" | -9.4% | 15 min |
| R3 | Fix bug V27: verificar igualdad ISCO antes de escalar | -0.4% | 20 min |
| R4 | Categoría D: warnings informativos → info, no escalar | -8.3% | 15 min |
| R5 | Atacar los 12K reales: crear más reglas fix_v31_* | régimen 40% → 5-10% | 2-3h |

Total R1-R4: ~1.5h. Después: régimen debería escalar ~5%, no 40%.

## Por qué PAUSADO

Reclasificar severidades afecta cómo Cyn percibe el sistema cuando audita.
Implementar sin su input puede generar confusión (counts del dashboard
cambian drásticamente sin explicación). Espero respuestas del cuestionario
para incorporar su criterio sobre qué considera "ruido" vs "error real".

R3 (fix bug V27) es bug técnico puro sin componente político. Podría
fixearse independientemente, pero se incluye en el lote para mantener
trazabilidad conjunta.

## Próximos pasos

1. Recibir respuestas del cuestionario de Cyn
2. Procesar bloques relevantes (especialmente Bloque 1 sobre cómo trabaja
   y Bloque 3 sobre Gold Set)
3. Decidir con su input cuáles R1-R5 implementar y cómo
4. Implementación + tests + commit
