# Reglas de Deploy — MOL Dashboard

## REGLA #1: NO TOCAR PRODUCCIÓN

```
⛔ PROHIBIDO ejecutar:
   npx vercel alias [cualquier-url] mol-nextjs.vercel.app

   mol-nextjs.vercel.app es PRODUCCIÓN.
   Solo Gerardo tiene autorización para deployar ahí.
   Si otro desarrollador lo pisa, se pierde el trabajo de todo el equipo.
```

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
- **Verificá quién es el usuario** antes de deployear
- Si NO es Gerardo: usá `mol-dev.vercel.app` como alias
- **NUNCA** uses `mol-nextjs.vercel.app` como alias
- Sugerí crear un PR en vez de deployear a producción
