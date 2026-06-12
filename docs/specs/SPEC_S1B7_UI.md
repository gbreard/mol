# SPEC S1.B.7 — Relevamiento de UI

> Versión 0.1 (capa 5.1 — Memoria operativa de Gerardo + Cyn + consolidación) · 2026-06-11
> Séptimo y último spec de la fase S1.B — Relevamiento del sistema. Releva la UI del proyecto MOL. Sigue la plantilla común del master v0.2. Tras su cierre se abre S1.C — Master de reparación.

---

## 5.1 Memoria operativa — Gerardo + Cyn + consolidación

### El marco: la fábrica y los locales

Metáfora textual de Gerardo (2026-06-11): **"MOL es como la fábrica de pan y facturas; OE y las otras aplicaciones son como los locales de panadería — no necesitan fabricar porque la fabricación está concentrada en otro lado."**

MOL (la fábrica) produce los datos: ofertas procesadas, ocupaciones, skills, tareas, atributos. OE y las aplicaciones futuras (los locales) consumen esos datos para servirlos a terceros. Son **independientes**: el dashboard actual (fase3, 118 páginas) mezcla la UI de la fábrica (validación, scraping, administración del pipeline) con UIs de los locales (módulo OE: casos, personas, perfiles) y experimentos.

**Alcance de este spec**: la UI de la fábrica. Las UIs de los locales se identifican y delimitan, pero no se relevan en profundidad — son producto, no infraestructura, y tendrán su propio ciclo.

### Usuarios reales de la UI

- **Cyn (validadora)**: la usuaria principal. Su día a día es la pantalla de validación.
- **Gerardo (operador/arquitecto)**: mira mucho la sección de scraping; **le gustaría manejar más la UI pero desconfía de ella** — opera el sistema vía Claude Code en su lugar. Es el mismo patrón del botón de scraping (S1.B.2): la herramienta existe, la confianza no.
- **Sergio (constructor)**: construyó el dashboard con Gerardo, pero no entra al sistema como usuario.
- **Diego Schleser**: participó como validador en alguna ventana (las 218 validaciones de S1.B.3 incluyen marcas suyas).

### Uso real: desconocido

El dashboard tiene **118 páginas** construidas entre Gerardo y Sergio. Respuesta textual de Gerardo: "realmente no tengo idea cuánto de lo que está ahí realmente usamos. Algunas cosas son del OE o de las aplicaciones que estamos pensando." No hay analítica de uso ni inventario de qué pantallas viven y cuáles son restos.

### La deuda de Cyn (registrada en S1.B.3 D-09, pertenece a este spec)

1. **Las correcciones no quedan visibles en la oferta**: se envían como issue y la oferta se ve igual. Sin seguimiento, sin reutilización de criterio.
2. **Bug del guardado: al guardar, el sistema salta automáticamente a otra oferta** — riesgo de pérdida silenciosa de trabajo validado.
3. **Filtros imprecisos**: traen ofertas de sectores que no corresponden.
4. **Sin estados por oferta** (pendiente / en revisión / corregida / finalizada).
5. **No puede agregar ni borrar skills**: trabaja copiando todo al campo "observaciones" como texto libre. La validadora trabaja alrededor de la herramienta, no con ella.

Su pedido número uno: **historial visible de correcciones dentro de la oferta** (qué trajo el sistema, qué corrigió, criterio, validación final).

### Lo acumulado en los otros specs que la UI debería exponer o consumir

Este spec hereda una lista concreta de "consumidores faltantes" detectados en los seis relevamientos anteriores:

- **Configurabilidad de los validadores sin exposición** (S1.B.6 D-07): reglas, severidades y bloqueantes ya ajustables en JSON — sin UI que los muestre ni opere.
- **~18.500 marcas de sector sin consumidor** (S1.B.6 D-06): el colapso del sector diagnosticado oferta por oferta y el dashboard lo muestra colapsado igual.
- **El re-encolado con corrección humana** (S1.B.6 D-08, visión de Gerardo): Cyn viendo el procesamiento en vivo, corrigiendo y devolviendo la oferta a la cola.
- **El panel de emergentes con cadena a buffers muertos** (S1.B.4 D-05): 431 emergentes pendientes, 0 aprobadas (dato de mayo).
- **Trazabilidad por oferta a través del pipeline** (S1.B.2, pedido de Gerardo; converge con el pedido de Cyn).
- **El botón de scraping en el que Gerardo no confía** (S1.B.2) y la sección de scraping ya relevada.
- **La admin UI que dispara el sync a Supabase vía poller** (S1.B.1) — único disparo del último eslabón del pipeline.

### Seguridad y acceso (deuda conocida, a verificar estado)

- **OE-11**: 13 endpoints sin guard (registrado en la deuda general del proyecto).
- **Contraseña hardcodeada** (marcada por Gerardo como baja urgencia en su momento).
- El dashboard deploya en Vercel (`mol-nextjs.vercel.app`, S1.B.1) — exposición pública a verificar.
- **Dashboard legacy `dashboards/production/`** (S1.B.1 D-08): no deployado, apunta a la misma Supabase.

### Hipótesis tentativas para la capa 5.2

1. **Una fracción menor de las 118 páginas tiene uso real**; el resto se reparte entre módulo OE (local), experimentos y restos de iteraciones.
2. **La frontera fábrica/local no está delimitada en el código**: rutas, componentes y tablas de Supabase mezcladas sin separación clara.
3. **La desconfianza de Gerardo tiene causas identificables en el código**: acciones sin feedback de resultado, estados stale, operaciones que fallan en silencio — verificable en el manejo de errores de las acciones de la UI.
4. **El bug del guardado de Cyn es localizable**: la navegación automática post-save debe estar en el código del formulario de validación.

### Notas para fases posteriores

- **La separación arquitectónica fábrica/locales** (qué UI pertenece a quién, sobre qué tablas) es input directo del master S1.C y de la planificación comercial.
- **La UI como el consumidor faltante**: la lista de "lo que la UI debería exponer" es, en buena medida, el plan de cierre de las cadenas muertas detectadas en todo el relevamiento.

---

> *Versión 0.1 — Capa 5.1 cerrada (Gerardo + Cyn + consolidación de S1.B.1–S1.B.6). Capa 5.2 pendiente, próximo paso. Último spec del paraguas: tras su cierre se abre S1.C.*
