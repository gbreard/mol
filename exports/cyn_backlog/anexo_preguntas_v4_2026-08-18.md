# Anexo para Cyn — las 4 preguntas del gate v4, con evidencia trazable (2026-08-18)

> La deuda visible del gate que activó el piloto (matriz v4: neta 6,7%, mejoras 57%). Cada pregunta con sus casos reales: id_oferta | título | tareas | qué decidió el traductor | qué decidía antes. Tu prosa manda; nada de esto se compila sin tu respuesta.

## Pregunta 1 — ¿«representante comercial» va como denominación (titulos_aviso) de la regla 16?

Hoy la regla 16 lista «representante de ventas» pero NO «representante comercial». Un aviso titulado así no activa el hub 16 — cayó al hub vendedor y decidió genérico donde tu regla habría afinado.

| id_oferta | título | tareas | traductor decidió | antes decidía |
|---|---|---|---|---|
| 1118202891 | Representante comercial vendedor | Desarrollar estrategias de ventas; planificar visitas semanales a toda empresa del segmento para ofrecer los servicios | 5223.4 vendedor (inclusión hub 51 — el hub 16 nunca se activó) | R40_asesor_comercial → 3322.1 |

**Si tu respuesta es sí**, la denominación entra al JSON 2.0 (fuente) — no la agregamos nosotros.

## Pregunta 2 — La rama de jerarquía del vecindario contable

Hermana de la rama de responsabilidad (análisis/cierres vs registración) que quedó para tu prosa: cuando el título trae CONDUCCIÓN («gerente», «jefe») y las tareas mezclan registración, ¿manda la conducción (1211.x) aunque la evidencia de tareas sea operativa?

| id_oferta | título | tareas | traductor decidió | antes decidía |
|---|---|---|---|---|
| 2179257 | Gerente administrativo contable (cía. de seguros) | Liderar la gestión integral de contabilidad; supervisar cierres mensuales y anuales; coordinar pagos y cobranzas; supervisar la registración | 2411.1.1 analista contable (inclusión hub 1) | R303_gerente_admin → 1211.1 director financiero |
| 6159089636 | Contador/a especializado/a en gestión financiera estratégica | Gestionar cierres mensuales; asientos; preparar estados financieros; calcular provisión de impuesto a las ganancias | 3313.2 administrativo contable (D02) | R14 → 2411.1 contable |
| 1118232497 | Contador/a | Conciliaciones; registraciones; gestionar y presentar declaraciones impositivas | 3313.2 (D02) | R14 → 2411.1 |

**Lo que necesitamos de vos:** los marcadores de la rama («responsabilidad profesional integral», conducción) en prosa operativa — con eso se compila prosa-directa, sin interpretación nuestra.

## Pregunta 3 — Venta-telefónica-CON-cartera: ¿3322.1 o 5244.1?

Tu término-set de venta externa (regla 16) hace que teleoperadores con cartera/prospección REAL vayan a 3322.1 vía la rama B2B. ¿Corresponde — o la venta telefónica manda (5244.1, tu laudo de R210) aunque haya cartera?

| id_oferta | título | tareas | traductor decidió | antes decidía |
|---|---|---|---|---|
| 9054916844 | Vendedor telefónico / call center | Contactar y gestionar potenciales clientes por teléfono y redes; prospección comercial; desarrollar y fidelizar cartera propia | 3322.1 representante (D11: prospección+cartera) | R15_customer_care → 4222.1 |

## Pregunta 4 — La frontera R15 (customer care) vs venta

R15 fuerza 4222.1 (atención al cliente) por «call center» en el título; tu prosa K2 dice 5244.1 cuando el eje es VENDER. Hoy R15 tiene precedencia (es especializada del vecindario) y le gana al traductor incluso donde el aviso es venta pura. ¿Cuál manda: el título «call center» o la tarea de venta?

| id_oferta | título | tareas | traductor decidió | antes decidía (y sigue: precedencia) |
|---|---|---|---|---|
| 1118017320 | Vendedor/a telefónico/a con experiencia en call center | Vender planes de asistencia a través de llamadas telefónicas | 5244.1 teleoperador (D10) | R15_customer_care → 4222.1 |

---
*Contexto: el piloto quedó activo (7 hubs, decide-cuando-decide + subordinación). Estas 4 fronteras están monitoreadas por telemetría (tags en la traza persistida); tus respuestas se aplican por el circuito de siempre (verificación → tandas → TEST).*
