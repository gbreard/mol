# Devoluciones para Cyn — lote REGLAS + sesión (2026-07-13)

Cyn: ¡gracias por el lote! Cargamos al diccionario las denominaciones consolidadas
(150 entradas nuevas) y tus árboles ya están organizados por familia en la taxonomía.
Las dos dudas de códigos que te llevamos (desarrollador Python y chofer de residuos) ya
quedaron resueltas con tu respuesta — no hay que volver sobre ellas. Esto es lo que
quedó pendiente de tu lado, ordenado para que sea fácil de retomar:

## 1 · Dos avisos que el sistema extrajo MAL (no es culpa tuya — bug de NLP)

El sistema no logró extraer las tareas reales de estos dos avisos («Sin tareas reales
disponibles»), así que no se pueden clasificar todavía. Los registramos en el issue de
NLP (`docs/issues/2026-06-30_bug_limpieza_titulo_nlp_ruido.md`) y te los volvemos a
mandar cuando el extractor los procese bien:

- **Ingeniero/a en integración electrónica y electromecánica** (el duplicado sin tareas;
  el otro aviso igual SÍ tenía tareas y lo resolviste → 2141.3.2.1 ingeniero de automatización)
- **Coordinador de mantenimiento de flota**

## 2 · El que marcaste REQUIERE REVISION

- **Montador de estructuras de hormigón** — tu nota: «Realiza el montaje de estructuras
  de hormigón en obra, con traslado fuera de la localidad, trabajo en altura y experiencia
  en tareas de montaje». Falta el código destino. Candidatos ESCO para mirar juntos:
  montador/a de estructuras prefabricadas de hormigón / ferrallista / montador/a de
  andamios — decidís vos con las tareas a la vista.

## 3 · Una inconsistencia chica para confirmar

- **Técnicos en electrónica, o en telecomunicaciones**: en la celda de código pusiste
  `2153 - ingeniero de telecomunicaciones`, pero tu árbol dice que el TÉCNICO va a
  «técnico/a en ingeniería de las telecomunicaciones» (código `3522.1`) y el ingeniero
  solo si el aviso exige título de ingeniero/a. ¿Confirmás que el default del técnico es
  3522.1? (La fila 25 de tu hoja de consolidadas — 3522.1 — quedó sin variantes; si nos
  pasás las denominaciones de ese grupo, lo cargamos igual que el resto.)

## 4 · Las filas que quedaron sin terminar (Hoja 1)

Sin código ni árbol — cuando puedas, con ver las tareas del aviso alcanza:

- Ingeniero en electrónica o en telecomunicaciones *(el sistema había dicho 2153 ingeniero de telecomunicaciones — falta tu corrección)*
- Ingeniero eléctrico o electromecánico
- Ingeniero/a civil, responsable de gestión de obras
- Coordinador de servicios eléctricos
- Ingeniero / técnico en sistemas embedded, RF e infraestructura
- Técnico electrónico de mantenimiento industrial
- Técnico instalador de sistemas de seguridad electrónica
- ASESOR COMERCIAL, TÉCNICO & LEGAL
- Supervisor de obra de mantenimiento en vía pública
- Jefe de obra ingeniero civil o arquitecto *(las otras dos filas de «jefe de obra - ingeniero civil o arquitecto» ya las resolviste → 1323.1; confirmá si esta es igual)*
- Técnico de puesta en marcha de ascensores *(ojo: la versión CON tareas de esta denominación ya la resolviste → técnico de ascensores)*
- Ingeniero civil, en construcciones o carreras afines
- Director/a de finanzas

## 5 · Ya resuelto con tu respuesta (solo para que quede registro)

- Desarrollador Python Senior → **2512.4** desarrollador de software (cargado + tu árbol en taxonomía)
- Chofer de recolección de residuos → **8332.8** conductor de vehículo de recogida de basura (cargado + tu árbol en taxonomía)
