# SPEC T — Flujo estructural de propagación de correcciones humanas

**Fecha:** 2026-04-27
**Autor:** Claude + Gerardo
**Estado:** Draft — pendiente decisiones
**Audiencia primaria:** Gerardo (decide), Claude (ejecuta), Cyn/Diego/Sergio (informados)
**Pre-condición:** SPEC S aplicado (caso piloto que reveló la falta de propagación)

---

## 1. Por qué este spec

A lo largo de SPEC P y SPEC S descubrimos que **las correcciones humanas no se propagan automáticamente** a ofertas similares. Caso testigo:

> En **abril 2026** Cyn y Diego corrigieron 3 ofertas (6866505508, 7347150394, 8299423434) diciendo "el área debería ser Logística, no Producción".
>
> Los issues se cerraron documentando el fix pero **313 ofertas similares quedaron sin tocar** durante semanas, hasta que SPEC S las propagó hoy.

**Datos del problema:**
- 542 issues humanos resueltos en BD
- 469 modificaron algún config
- **468 (99.8%) NO tienen rastro de propagación a ofertas similares**

Si no resolvemos esto estructuralmente, cada corrección que Cyn/Diego haga en el futuro va a quedar como **fix puntual sin escala** — perdemos la mayoría del valor de su trabajo.

---

## 2. Diagnóstico del flujo actual

### 2.1 Cómo se hace hoy

```
1. Humano detecta error en /admin/validacion
2. Crea issue (texto libre en `descripcion`)
3. Claude/Gerardo resuelve:
   - Modifica config/*.json
   - Re-procesa la oferta puntual
4. Cierra issue con:
   - estado='resuelto'
   - solucion_aplicada (texto libre)
   - config_modificada (texto libre)
5. Issue → training_pair (ya existe)
```

### 2.2 Qué falta

| Paso faltante | Consecuencia |
|---|---|
| **Detectar el patrón corregido** (qué condición + qué cambio) | Cada fix queda implícito, sin reusar |
| **Query de propagación** (¿cuántas ofertas más están en la misma situación?) | Solo se arregla la oferta del issue |
| **Re-procesamiento masivo** | Las N ofertas similares quedan mal |
| **Auditoría post-fix** | Nadie verifica que el fix funcionó |
| **Trazabilidad cuantitativa** | No sabemos cuántas ofertas tocó cada corrección |

### 2.3 Por qué pasa

1. **Los issues son texto libre.** `campo_afectado`, `valor_actual`, `valor_esperado` casi siempre están vacíos en issues humanos. Cyn/Diego escriben todo en `descripcion`.

2. **Falta un step "propagación" en el flujo.** No hay checkbox obligatorio "¿revisaste otras ofertas similares?".

3. **Falta tooling.** No hay función helper que tome un patrón y propague la corrección.

4. **No hay auditoría.** Después de cerrar el issue, nadie verifica si las N ofertas similares quedaron bien.

---

## 3. Diseño propuesto

### 3.1 Cambio de modelo

Cada corrección humana se trata como **producción de una regla derivada**, no como un fix puntual.

```
ANTES:  oferta X mal → fix oferta X → marcar resuelto
DESPUÉS: oferta X mal → fix oferta X
                    → identificar el patrón (qué condición → qué cambio)
                    → query: ¿cuántas otras ofertas matchean este patrón?
                    → propagar fix a las N
                    → auditar (verificar N quedaron bien)
                    → marcar resuelto con metadata cuantitativa
```

### 3.2 Nuevas estructuras de datos

Agregar a tabla `issues` 3 columnas:

| Columna | Tipo | Para qué |
|---|---|---|
| `patron_corregido` | jsonb | Estructura: `{campo, condicion: {tipo, keywords}, valor_anterior, valor_nuevo}` |
| `propagacion_n` | int | Cantidad de ofertas similares afectadas por el fix |
| `propagacion_ids` | jsonb | Lista de id_oferta tocadas (para auditoría) |

**Migración SQL:**
```sql
ALTER TABLE issues
  ADD COLUMN patron_corregido jsonb,
  ADD COLUMN propagacion_n int DEFAULT 0,
  ADD COLUMN propagacion_ids jsonb;
```

### 3.3 Tipos de propagación según el campo

| Campo corregido | Mecanismo |
|---|---|
| `area_funcional` (NLP) | Regla en `nlp_inference_rules.json` `prioridad_por_titulo` + UPDATE BD |
| `sector_empresa` (NLP) | Regla en `nlp_correction_rules.json` + UPDATE BD |
| `nivel_seniority` (NLP) | Regla en `nlp_inference_rules.json` |
| `tareas_explicitas` (NLP) | Más complejo — requiere análisis caso a caso |
| `esco_occupation_label` (Matching) | Regla en `matching_rules_business.json` + re-rematch |
| `skills` (Skills) | Filtros en `skills_rules.json` (ya existe) |

### 3.4 Función helper de propagación

```python
# scripts/correcciones/propagate_correction.py

def propagate_correction(
    patron: dict,           # {campo, condicion, valor_anterior, valor_nuevo}
    dry_run: bool = True
) -> dict:
    """
    Toma un patrón de corrección y lo propaga a todas las ofertas similares.

    Returns:
        {
          'ofertas_identificadas': N,
          'ofertas_actualizadas': M,
          'ids': [...],
          'reglas_creadas': [...],
        }
    """
    # 1. Identificar ofertas que matchean el patrón
    # 2. Si dry_run=False, aplicar UPDATE/re-rematch según campo
    # 3. Generar regla derivada en config correspondiente
    # 4. Retornar reporte
```

---

## 4. Workflow nuevo

```
PASO 1: Recibir issue humano
  └─ Si campo_afectado vacío → pedir a humano que lo complete (futuro)
  └─ Si valor_esperado vacío → pedir que lo complete

PASO 2: Claude analiza descripción del issue
  └─ Identifica: campo, condición típica, valor anterior, valor nuevo
  └─ Estructura el patrón en `patron_corregido` JSON

PASO 3: Aplicar fix puntual (oferta del issue)

PASO 4: Query de propagación
  └─ ¿Cuántas ofertas matchean el patrón?
  └─ Si N > 1: continuar
  └─ Si N == 1: marcar como excepción (campo `solo_excepcion=true`)

PASO 5: Crear regla derivada en config correspondiente
  └─ Según tipo de campo (NLP, matching, skills)
  └─ Linaje: link al issue origen

PASO 6: Aplicar UPDATE/re-procesamiento masivo
  └─ Re-rematch / re-NLP / re-skills según corresponda
  └─ Verificar que N ofertas quedaron coherentes

PASO 7: Cerrar issue con metadata completa
  └─ estado='resuelto'
  └─ patron_corregido (JSON estructurado)
  └─ propagacion_n (cantidad)
  └─ propagacion_ids (lista de IDs tocados)
  └─ solucion_aplicada (texto libre)
  └─ config_modificada (texto libre)
```

---

## 5. Plan de implementación por fases

### Fase 0 — Preparación
- Crear migration SQL para 3 columnas nuevas en `issues`
- Aplicar en Supabase (dev y prod)
- Backup tabla issues antes

### Fase 1 — Helper de propagación
- Implementar `scripts/correcciones/propagate_correction.py`
- Cubre 3 tipos básicos: NLP area_funcional, NLP sector_empresa, Matching ESCO
- Tests sobre casos conocidos (3 ofertas SPEC S)

### Fase 2 — Migración del flujo Claude
- Documentar workflow nuevo en `CLAUDE.md` (sección "Resolver issues humanos")
- Convertir flujo en checklist obligatorio
- Que cada issue humano que resuelva Claude pase por los 7 pasos

### Fase 3 — Auditoría retrospectiva
- Revisar 542 issues humanos resueltos pasados
- Para cada uno con `config_modificada`: re-aplicar query de propagación
- Si encuentra N>0 ofertas mal, propagar y actualizar issue
- Resultado esperado: cientos de ofertas re-corregidas

### Fase 4 — UI mejoras (opcional, Sergio)
- Modificar `/admin/validacion` para que humanos completen `campo_afectado` y `valor_esperado` estructurados
- Botón "estimar propagación" que muestre N antes de cerrar

### Fase 5 — Auditoría continua
- Cron mensual que verifique si correcciones de los últimos 30 días están propagadas
- Alerta si encuentra issues sin propagación

---

## 6. Decisiones tomadas (2026-04-27)

| # | Decisión | Detalle |
|---|---|---|
| 6.1 | Alcance auditoría | 469 issues con `config_modificada` |
| 6.2 | Tipos de propagación | 4 tipos: NLP area_funcional, Matching ESCO target, Skills filtrado, NLP tareas_explicitas (re-extracción) |
| 6.3 | Workflow Claude | Obligatorio día 1 post Fases 0+1+2 |
| 6.4 | UI Cyn/Diego | Sugerida con autocompletado (no obligatoria, Sergio implementa cuando pueda) |
| 6.5 | Trigger propagación | Manual al cerrar issue + cron de auditoría débil (solo detecta, no propaga) |

---

## 7. Riesgos

### 7.1 Falsos positivos de propagación
Una propagación mal calibrada puede convertir 100 ofertas correctas en incorrectas.
**Mitigación:** dry_run obligatorio antes de aplicar. Query de propagación primero estima, después aplica.

### 7.2 Regresión sobre correcciones humanas previas
Una nueva corrección puede pisar otra anterior.
**Mitigación:** auditoría post-fix verifica que ofertas con corrección humana documentada NO retrocedieron.

### 7.3 Cyn/Diego no cambian su flujo
Si los humanos siguen escribiendo en texto libre y no estructurado, Claude tiene que inferir el patrón cada vez.
**Mitigación:** prompt diseñado para que Claude infiera bien + UI eventualmente sugiera estructura.

### 7.4 Cascadas indeseadas
Una propagación puede afectar ofertas que dependen de otras correcciones humanas. Cascada de cambios.
**Mitigación:** documentar dependencias entre correcciones.

---

## 8. Cronograma estimado

| Fase | Duración | Entregable |
|---|---:|---|
| 0 — Preparación | 1 hr | Migration SQL aplicada |
| 1 — Helper propagación | 4 hrs | `propagate_correction.py` + tests |
| 2 — Workflow Claude | 1 hr | CLAUDE.md actualizado |
| 3 — Auditoría retrospectiva | 8 hrs | Reporte + cientos de ofertas re-corregidas |
| 4 — UI mejoras | 1-2 días (Sergio) | UI con campos estructurados |
| 5 — Auditoría continua | 2 hrs | Cron mensual |

**Total** (sin Fase 4 que es de Sergio): **~16 hrs distribuidas en 1-2 sesiones**.

---

## 9. Lo que este spec NO hace

- NO automatiza la resolución de issues — Claude sigue interviniendo en el análisis.
- NO cambia el modelo de issues (texto libre sigue siendo válido).
- NO sustituye SPEC M, Q, R (validación humana muestral).
- NO modifica `validacion_humana` (tabla vacía actualmente, no se usa).

---

## 10. Output esperado

Al terminar SPEC T:
- Estructura de datos lista para trazabilidad de propagación
- Función helper `propagate_correction()` operativa
- CLAUDE.md con workflow nuevo documentado
- 200-500 ofertas re-corregidas como resultado de auditoría retrospectiva
- Métrica nueva en learnings.yaml: "ofertas propagadas por correcciones humanas en últimos 30 días"

A partir de entonces, **cada corrección que Cyn/Diego haga genera automáticamente la propagación a todas las ofertas similares**. Su trabajo escala N veces.
