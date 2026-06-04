# SPEC S1.B.1 — Relevamiento de Bases de Datos

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo) · 2026-06-04
> Primer spec de la fase S1.B — Relevamiento del sistema. Releva el estado actual de las bases de datos del proyecto MOL, la deuda detectada y el diseño objetivo. Sigue la plantilla común definida en `docs/specs/MOL_master_relevamiento.md`.

---

## 5.1 Memoria operativa de Gerardo

Lo que Gerardo aporta sobre las bases de datos antes de la verificación contra el código. **Información que ningún archivo del repo registra**, capturada en la conversación del 2026-06-04. Es input crítico para la capa 5.2 (relevamiento por Claude Code), no comentario complementario.

### Mapa de las tres BDs

El sistema tiene **tres bases de datos diferenciadas, con estructuras distintas, cada una con un rol específico**. No es replicación; es especialización.

| BD | Ubicación física | Rol funcional |
|---|---|---|
| **VPS** | Hostinger (VPS KVM2) | Scraping |
| **Local** | PC de Gerardo (SQLite) | NLP y matching |
| **Supabase** | Nube (Supabase managed Postgres) | UI / dashboard |

### Flujo de datos

Los datos viajan unidireccionalmente entre las tres BDs:

```
VPS (scraping)  →  Local (NLP + matching)  →  Supabase (UI)
```

- **VPS → Local**: sincronización disparada al final de cada corrida del scraper. No es por intervalo de tiempo fijo, es por evento ("cuando termina el scraper, sincroniza").
- **Local → Supabase**: push como paso final del pipeline local. Cuando Gerardo ejecuta el pipeline completo (un comando único), la sincronización a Supabase es la última etapa.

**Sospecha activa de Gerardo (a verificar)**: hay escrituras cruzadas entre BDs que no siguen el flujo unidireccional. No está confirmado, pero su intuición es que más de un proceso escribe en Supabase, y esa es la pista que sospecha está relacionada con el costo elevado de procesamiento.

### Estado conocido de cada BD

**VPS**:
- Solo guarda lo scrapeado desde el momento del scraping en adelante. No tiene historial scrapeado anterior.
- Cantidad de tablas: desconocida por Gerardo.
- **Implicación operativa**: si se pierde la BD del VPS, se pierde todo lo que no se haya sincronizado al local.

**Local**:
- Motor: SQLite.
- Guarda histórico (estados anteriores de procesamiento, versiones del NLP, runs viejos del matching).
- No hay política de limpieza definida — el histórico se acumula.
- **El NLP es lo más lento** del pipeline local (esperable: corre Qwen2.5:7b localmente, procesamiento pesado por oferta).

**Supabase**:
- El costo a fin de mes proviene de **procesamiento** (CPU usado en queries, RPCs, funciones), **no de storage**. Este es un dato crítico.
- Tabla más grande: desconocida por Gerardo, pero sospecha que sea la intermedia ofertas × skills.
- La tabla ofertas × skills crece sin límite, posiblemente más de 1 millón de filas. Riesgo de escalamiento.

### Operación

- **Acceso al sistema**: solo Gerardo. Sergio aún no entra al sistema. Cuando entre, va a hacer falta definir coordinación, permisos y qué toca cada uno.
- **Pipeline local**: se dispara con un comando único que orquesta todo (NLP + matching + sync a Supabase).
- **Cron del VPS**: se dispara al finalizar cada scraper, no en intervalos fijos.
- **Scripts de sincronización**: existen, pero Gerardo no recuerda nombres específicos. Hay que identificarlos en el código.

### Síntomas y problemas operativos

Lo que Gerardo experimenta hoy:

**1. "Hoy no me entero" cuando algo falla.**
La sincronización no tiene observabilidad. Si falla la sincronización VPS→Local o Local→Supabase, no hay alerta, log accesible, ni señal visible. El sistema puede estar en **estado de inconsistencia silenciosa**: data procesada localmente que no llega al dashboard, sin que nadie lo note.

**2. Problemas para enchufar ofertas con skills.**
Síntoma reportado por Gerardo. No está claro si es problema de extracción de skills, de matching, de la tabla intermedia, o de la sincronización. Es síntoma a investigar, no causa identificada.

**3. Costo elevado de Supabase a fin de mes.**
La factura mensual es relevante. El consumo proviene de procesamiento (no storage). Posibles fuentes hipotéticas, a verificar:
- Operaciones RPC complejas sobre la tabla ofertas × skills.
- Reintentos silenciosos de sincronización cuando algo falla.
- Queries ineficientes en el dashboard que consultan más de lo necesario.

**4. El sistema "siempre anduvo para el orto".**
Esta frase textual de Gerardo es información estructural importante: el sistema no se degradó desde un estado mejor. Nació con problemas y nunca funcionó del todo bien. La deuda es constitucional, no producto de un cambio reciente que rompió algo.

**Implicación para el método**: el relevamiento no es arqueología (qué cambió, cuándo, por qué). Es diagnóstico estructural (cómo está armado y por qué nunca funcionó bien). El diseño objetivo (capa C) no es "volver al sistema que andaba bien" — ese sistema no existió. Es diseñar lo que debería ser.

### Hipótesis tentativa de la causa central

Articulada en la conversación del 2026-06-04, **es hipótesis, no conclusión**. La capa 5.2 (verificación de Claude Code) tiene que confirmarla, refutarla o refinarla:

> El sistema sincroniza local → Supabase como push pesado al final del pipeline. La sincronización carece de observabilidad. Supabase recibe escrituras pesadas (posiblemente RPC complejos, posiblemente desde varios lados si la sospecha de "escrituras cruzadas" se confirma) que generan consumo de procesamiento. Si la sincronización falla parcialmente o se dispara más veces de las necesarias, el costo se infla sin que nadie lo note. La tabla intermedia ofertas × skills, con más de 1 millón de filas, probablemente es protagonista de las operaciones pesadas.

### Notas para fases posteriores

Cosas que aparecieron en la conversación pero que **están fuera del alcance del spec S1.B.1** y se registran para que no se pierdan:

- **Coordinación con Sergio cuando entre al sistema**: definir permisos, qué toca cada uno, cómo se comparten credenciales. Trabajo de un spec dedicado en algún momento del paraguas S1.C o posterior.
- **Riesgo operativo de capacidad concentrada**: el conocimiento técnico y operativo está hoy en una sola persona. No es trabajo del spec de BD, pero conviene marcarlo en la planificación general como deuda de organización.

---

> *Versión 0.1 — Capa 5.1 cerrada. Capa 5.2 (estado actual relevado por Claude Code) pendiente, próximo paso.*
