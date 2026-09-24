# Rediseño del sync de skills a Supabase

**Detectado:** 2026-09-07, preparando el sync de la Fase 5 (B.0).
**Estado:** abierto, **planificado para después de la Fase 5**.
**Severidad:** alta como deuda de diseño — hoy hace imposible un sync completo.

## El problema

`sync_to_supabase.py` sincroniza `ofertas_esco_skills_detalle` → `ofertas_skills` con
**delete + insert por oferta**, vía requests individuales del cliente Supabase.

Medido el 2026-09-07:

```
Encontradas: 96.872 ofertas
Encontradas: 2.819.992 skills      <- 2,8 MILLONES
Encontradas: 2.373 ocupaciones
```

El free tier de Supabase sostiene ~15 req/s. Aun contando dos operaciones por oferta
(un DELETE + un INSERT en lote), son ~194.000 requests; si el patrón fuera por fila, la
escala es de días. **El sync completo es hoy inejecutable en la práctica**, y esa es la
razón de que se agregara `--skip-skills` para poder descongelar el panel.

## La documentación decía 300K

`CLAUDE.md` afirmaba *"~300K HTTP requests individuales (~60-90 min)"* y *"Full: ~2.5h"*.
La cifra real es **casi 10× mayor**. Esa desactualización casi motiva lanzar una corrida
que habría tardado días y probablemente disparado el rate limit (Cloudflare 1018, que
pausa el proyecto). Corregido en el mismo commit que abre este issue.

## Qué evaluar

Tres preguntas, en orden de impacto:

1. **¿Supabase necesita las 2,8M filas crudas?** Es la pregunta de fondo. Si los paneles
   consumen agregados (skills por ocupación, top-N por período, conteos), una **tabla
   agregada** de miles de filas sirve igual y elimina el problema de raíz. Hay que mirar
   qué consultan realmente las RPCs y el frontend antes de optimizar el transporte de algo
   que quizá no haga falta transportar.
2. **Si hacen falta crudas: bulk en vez de requests individuales.** `COPY` vía conexión
   Postgres directa, o `insert` con lotes grandes en una sola llamada, en vez de
   delete+insert por oferta. Cambia el orden de magnitud del tiempo.
3. **Si el volumen es correcto pero el refresco no**: hoy se re-suben todas las skills de
   una oferta cada vez que la oferta entra al sync. Un criterio incremental real
   (`skills_actualizadas_en`, con el mismo patrón que `descripcion_actualizada_en` del
   VPS) evitaría re-subir lo que no cambió.

## Mientras tanto

- `--skip-skills` permite el sync de ofertas sin arrastrar esto.
- `ofertas_skills` en Supabase queda con los datos del último sync completo que sí corrió.
  **Conviene verificar qué tan viejos son antes de confiar en cualquier panel de skills.**

## Referencias

- `scripts/exports/sync_to_supabase.py` — `upsert_skills()` (~línea 884), `main()` (~2600)
- `CLAUDE.md` § "Sync a Supabase — Cómo funciona internamente"
- Contexto: Fase 5 del ciclo de vida, etapa B.0
