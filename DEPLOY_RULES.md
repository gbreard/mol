# Reglas de Deploy — MOL Dashboard

## REGLA #1: NO TOCAR PRODUCCIÓN (regla por EFECTO, no por comando)

```
⛔ PROHIBIDO cualquier acción que PROMUEVA o CAMBIE el alias de
   producción (mol-nextjs.vercel.app), sin importar el comando:

   - npx vercel alias [url] mol-nextjs.vercel.app
   - npx vercel --prod   ← ¡también! promueve mol-nextjs AUTOMÁTICAMENTE
                            (el dominio de producción del proyecto),
                            aunque no se corra `vercel alias`.

   mol-nextjs.vercel.app es PRODUCCIÓN. Solo Gerardo la promueve.
   Si otro desarrollador la pisa, se pierde el trabajo de todo el equipo.
```

La regla es por **efecto** (mover el alias de prod), no por el nombre del comando:
el 25/09/2026 un agente corrió `vercel --prod` (sin `vercel alias`) y aun así se
promovió `mol-nextjs.vercel.app`. La letra no se violó; el efecto sí.

## Ambientes

| Ambiente | URL | Quién deployea | Cuándo |
|----------|-----|----------------|--------|
| **Producción** | `mol-nextjs.vercel.app` | Solo Gerardo | Después de revisar PR |
| **Desarrollo** | `mol-dev.vercel.app` | Sergio / otros devs | Para probar cambios |

## Cómo deployear a desarrollo (Sergio)

```bash
cd fase3_dashboard/mol-dashboard

# 1. Deploy
npx vercel --prod --yes

# 2. Asignar a URL de desarrollo (NUNCA a mol-nextjs)
npx vercel alias [url-del-deploy] mol-dev.vercel.app

# 3. Verificar en https://mol-dev.vercel.app
```

## Cómo llegar a producción

```bash
# 1. Push tu branch
git push origin feature/mi-feature

# 2. Crear PR a main
gh pr create --base main --title "feat: descripcion" --body "que hice"

# 3. Gerardo revisa, mergea y deployea a producción
# NO hacer deploy vos — esperar a que Gerardo lo haga
```

## ¿Por qué?

El 22/03/2026 se deployó a producción sin coordinación y se pisó todo el trabajo del sprint 15 (Centro de Control, Scraping admin, Procesamiento, menú reorganizado). Se tuvo que restaurar manualmente.

## Para agentes de IA (Claude Code, Cursor, etc.)

Si estás leyendo esto como agente de IA asistiendo a un desarrollador:

- **Un agente NUNCA ejecuta una acción que promueva o cambie el alias de
  producción (`mol-nextjs.vercel.app`)** — esto incluye `npx vercel --prod`, que
  lo promueve automáticamente, no solo `vercel alias`. La prohibición es por
  EFECTO, no por comando.
- **Para deploys de verificación:** usá `npx vercel` (preview, **sin `--prod`**).
  Genera una URL propia `mol-nextjs-<hash>-gbreards-projects.vercel.app` sin tocar
  producción. Pasale esa URL al desarrollador.
- **La promoción a producción la ejecuta Gerardo** (él corre el `--prod` / alias).
- Si ya se promovió prod por error, **revertir el alias también es acción sobre
  mol-nextjs → la hace Gerardo**, no el agente.
- Sugerí crear un PR / dejar la URL de preview en vez de deployear a producción.
