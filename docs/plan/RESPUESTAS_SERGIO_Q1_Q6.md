# Respuestas a Q1-Q6 de Sergio

> Fecha: 2026-03-25
> Contexto: PLAN_INTEGRACION_GERARDO.md

---

### Q1: ¿`worker_profiles` reemplaza a `perfiles` o conviven?

**Respuesta: Se reemplaza.**

`worker_profiles` tiene 0 rows en producción, nadie la usa. Es una tabla plana improvisada (skills en JSONB) que creamos el 23/03. El schema de Sergio (personas + perfiles + perfil_skills) es objetivamente mejor: normalizado, con estado por skill, con vía de captura, con confianza.

- Vamos a crear las 7 tablas nuevas según el schema propuesto
- `worker_profiles` queda deprecada (no la borramos por si algún código la referencia, pero no se usa más)
- La API `/api/worker-profiles` se reemplaza por `/api/personas` + `/api/perfiles`
- La UI de `/oficina-empleo/perfil` se actualiza para usar las nuevas APIs

---

### Q2: ¿`organizaciones` ya tiene tabla en Supabase? ¿Qué campos tiene?

**Respuesta: Sí, existe. 1 row.**

```
Tabla: organizaciones
Columns: id, nombre, tipo, jurisdiccion, activa, created_at, updated_at
Rows: 1
```

Es suficiente para empezar. Si necesitamos más campos (ej: dirección, responsable, plan), se agregan con ALTER TABLE.

---

### Q3: ¿El endpoint `POST /api/compatibility-report` puede recibir `perfil_id` directo?

**Respuesta: Sí, se puede extender.**

Actualmente recibe un objeto con skills[]. Vamos a agregar `perfil_id` como parámetro opcional — si viene, la API lee las skills confirmadas del perfil desde Supabase y genera el reporte. Si no viene, sigue funcionando con skills[] como ahora.

---

### Q4: ¿La tabla `reportes_compatibilidad` tiene campo `expirado_at`?

**Respuesta: Sí, tiene `expira_at`.**

La tabla existe en `04_MODELO_DATOS.md` con campo `expira_at TIMESTAMPTZ`. El GET ya chequea expiración y devuelve `estado: "expirado"` si corresponde.

---

### Q5: ¿Sergio puede agregar Fix 4 (ranking OE) directamente en `matching-offers/route.ts`?

**Respuesta: Sí.**

Que lo haga él. Los parámetros a agregar (`org_id`, `user_provincia`) se leen de searchParams y se aplican como boost al score. Lógica:
- `+15%` si la vacante es del pool OE de esa organización
- `+10%` si misma localidad, `+5%` si misma provincia

---

### Q6: ¿El onboarding import CSV es de una sola OE o multi-OE?

**Respuesta: Una sola OE** (la del usuario logueado).

El `organizacion_id` se toma del JWT del usuario autenticado. No hay selector de OE en el frontend. Si en el futuro un admin necesita importar para otra OE, se agrega un selector con permiso admin.
