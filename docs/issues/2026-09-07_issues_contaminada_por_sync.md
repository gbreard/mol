# La tabla `issues` (feedback humano) está contaminada con 501K registros automáticos

**Detectado:** 2026-09-07, en el dry-run del sync de la Fase 5 (B.0).
**Estado:** abierto. **Entrada frenada** con `--skip-issues`; nada limpiado.
**Severidad:** alta — el flujo de propagación de correcciones de Cyn es inusable así.

## Qué pasa

`sync_to_supabase.py` sincroniza `validation_errors` (SQLite local) a la tabla `issues` de
Supabase, creando un issue por error de validación, fila por fila.

Medido el 2026-09-07:

| | |
|---|---|
| `issues` **hoy** en Supabase | **501.356** |
| `validation_errors` sin resolver en local | 292.754 |
| `validation_errors` totales | 446.358 |
| Que el sync intentaría agregar | **257.271** |

Medio millón de registros automáticos ya adentro, y el sync quería sumar un cuarto de millón.

## Por qué importa: es la tabla de feedback humano

`issues` es donde Cyn, Diego y Gerardo reportan errores desde el dashboard, y es la entrada
del **flujo obligatorio de 7 pasos** documentado en `CLAUDE.md` (SPEC T): leer issue → fix
puntual → estructurar patrón → dry-run de propagación → aplicar → cerrar con metadata → sync.

Ese flujo asume que un issue es **una observación humana con justificación**, y que el
volumen es manejable a mano. Con 501K registros automáticos:

- Encontrar los reportes humanos reales es buscar una aguja en un pajar.
- La query de "issues pendientes" del CLAUDE.md devuelve cientos de miles de filas.
- Las métricas de issues del panel no significan nada.

## Cómo se llegó acá sin que se notara

El early-exit roto de `auto_sync.sh` (ver commit `e3a27a03`) impidió que el sync corriera
durante semanas. Los 501K vienen de corridas manuales anteriores. Al arreglar el early-exit,
el sync volvió a estar operativo y el dry-run mostró que iba a agregar 257K más — o sea que
el bug venía **tapando** este problema.

## Preguntas para el rediseño

1. **¿Los `validation_errors` deben viajar a Supabase siquiera?** Son diagnóstico interno del
   pipeline: qué regla falló en qué oferta. El dashboard puede necesitar *conteos* y
   *tendencias*, no las 446K filas. Si es así, un agregado resuelve y no hay nada que migrar.
2. **Si tienen que viajar: tabla propia.** `validation_errors_dashboard` o similar, separada
   de `issues`. Mezclar telemetría automática con feedback humano en la misma tabla es el
   error de origen; el volumen solo lo hizo visible.
3. **¿Qué se hace con los 501K existentes?** Son distinguibles: los automáticos tienen
   `autor_email='auto-validator@mol.gob.ar'` (el CLAUDE.md ya los trata aparte en el flujo de
   resolución). Habría que confirmar que **todos** los automáticos llevan esa marca antes de
   borrar nada, y contar cuántos reportes humanos reales hay debajo.

## Lo que se hizo ahora

- **`--skip-issues`**: guard sobre extracción y subida, con log explícito
  `ISSUES OMITIDOS (--skip-issues)`. La entrada queda frenada.
- **No se limpió nada.** Los 501K siguen ahí, a la espera de la decisión.

## Verificación previa a cualquier limpieza

```sql
-- ¿Cuántos son automáticos y cuántos humanos?
SELECT autor_email, COUNT(*) FROM issues GROUP BY 1 ORDER BY 2 DESC;

-- ¿Hay automáticos SIN la marca esperada? (si los hay, no se puede borrar por autor_email)
SELECT COUNT(*) FROM issues
WHERE autor_email <> 'auto-validator@mol.gob.ar'
  AND (descripcion LIKE '%validation_error%' OR titulo LIKE '%[AUTO]%');
```

## Referencias

- `scripts/exports/sync_to_supabase.py` — `sync_validation_errors_to_issues()` (~1190),
  `extraer_errores_pendientes()` (~1143)
- `CLAUDE.md` § "Gestión de Issues (Supabase)" y § "Flujo OBLIGATORIO de Resolución de Issues
  Humanos (SPEC T)"
- Hermano de `docs/issues/2026-09-07_rediseno_sync_skills.md` — mismo patrón (volumen que
  creció órdenes de magnitud sin que el diseño se revisara), problema distinto: allá es
  transporte, acá es **contaminación de una tabla de uso humano**.
