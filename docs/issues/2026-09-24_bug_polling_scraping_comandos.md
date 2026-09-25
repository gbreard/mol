# Bug latente: polling de scraping/comandos nunca dispara (stale closure)

**Fecha:** 2026-09-24 · **Estado:** abierto · **Prioridad:** baja

## Ubicación
`fase3_dashboard/mol-dashboard/app/admin/scraping/comandos/page.tsx:152-165`

## Síntoma
El auto-refresh que debería refrescar la lista de comandos mientras hay uno
`pendiente`/`ejecutando` **nunca corre el fetch**.

## Causa
```tsx
useEffect(() => {
  loadSchedule();
  loadCommands();
  const interval = setInterval(() => {
    if (commands.some(c => c.estado === 'pendiente' || c.estado === 'ejecutando')) {
      loadCommands();
    }
  }, 30000);
  return () => clearInterval(interval);
}, []);   // <-- deps vacías
```
El `useEffect` tiene deps `[]`, así que el closure captura `commands` del primer
render (arreglo **vacío**). El `.some(...)` evalúa siempre sobre `[]` → siempre
`false` → `loadCommands()` dentro del intervalo nunca se llama. Solo corre el
`loadCommands()` inicial (una vez, al montar).

## Fix sugerido (no aplicar ahora)
Incluir `commands` en las deps (recreando el intervalo al cambiar), o usar un `ref`
que espeje el último `commands`, o poll incondicional con backoff. Cualquiera saca
el stale closure. No urge: la pantalla igual carga al montar y con el botón.

## Nota
Detectado durante la auditoría de polling del admin (issue
`2026-09-24_timeout_rpcs_admin_metricas.md`, punto #2). Los otros 4 sitios de
polling quedaron sin tocar; los dos incondicionales (metricas, arquitectura) se
removieron en ese mismo trabajo.
