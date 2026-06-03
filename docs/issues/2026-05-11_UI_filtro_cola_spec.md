# Issue: UI de validación necesita filtro por cola SPEC

**Fecha:** 2026-05-11
**Origen:** Hallazgo H17 post-cierre SPEC U-1
**Prioridad:** Alta (afecta procesamiento de 5.462 ofertas en cola humana)

## Problema

SPEC U-1 generó cola humana de 5.462 ofertas (974 de sub-fase D + 4.488 de C1)
con banderas específicas:
- `bandera_spec_w = 'sub_ocupacion_bizarra_revisar'` (407 ofertas)
- `bandera_spec_w_C1` con 4 valores distintos (304 ofertas)
- Estado `pendiente_humano_subfaseD` o `pendiente_humano_C1` (resto)

Cynthia revisó solo 7 de esas 5.462 (0.13%) durante 6 días post-cierre.
El 70% de su tiempo fue sobre auto-validadas pre-SPEC porque la UI no le
muestra primero la cola SPEC.

## Causa raíz

La UI de validación no tiene filtro por:
- `bandera_spec_w` IS NOT NULL
- `bandera_spec_w_C1` IS NOT NULL
- Estado `pendiente_humano_*`

Cynthia revisa lo que "aparece" en la UI sin priorización por SPEC.

## Solución sugerida

Agregar filtros a la UI de validación:
1. Toggle "Mostrar solo cola SPEC U-1" → filtra por banderas activas.
2. Selector "Tipo de cola" → desplegable con valores de banderas SPEC W.
3. Orden por antigüedad de bandera (más viejas primero).

## Impacto si no se hace

5.462 ofertas quedan en cola sin procesar. Trabajo de SPEC U-1 desaprovechado
porque el output no llega al validador humano. La cola sigue creciendo cuando
corra C1 nuevamente o C2 sub-fase E si se hace.

## Esfuerzo estimado

2-4 horas si la UI ya tiene infraestructura de filtros existente.
Más si requiere componentes nuevos.

## Responsable

A definir — quien mantenga la UI (probablemente backend dashboard MOL).
