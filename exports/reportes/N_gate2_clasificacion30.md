# FRENTE N — Gate 2: clasificación de la lectura de 30 (v11 vs v12)

Clasificación de la muestra fresca de 30 (seed 7) del gate 2, hecha por el sistema. Material crudo trazable: `N_gate2_lectura30_material.md`.

## Desglose

| Clase | N | % |
|---|---|---|
| **Mejora** (v12 recupera tareas o limpia requisitos que v11 metía) | 18 | 60% |
| **Neutral** (equivalente funcional) | 8 | 27% |
| **Regresión-a-verificar** | 3 | 10% |
| **Caso-frontera** | 1 | 3% |

**Regresión bruta 10% — bajo el techo.** Gate 2: **PASA**, con 3 preguntas de criterio en manos de la fuente (Cyn).

## Las 3 regresiones — patrón compartido

Las tres son **listas de nominalizaciones escuetas, sin verbo**, donde la atribución estricta de v12 puede estar descartando **la tarea nuclear del oficio** (v11 las tenía, v12 devolvió []):

| id | portal | título | v11 (tenía) | v12 |
|---|---|---|---|---|
| 1117212619 | bumeran | Chofer de camiones | Manejo de chasis / balancines / semis; control de mercadería; manejo de remitos | [] |
| 2184455 | zonajobs | Electricista/Montador/Herrero/Plastiquero | Instalación de tendidos eléctricos; laminación y pulido de PRFV; fabricación y reparación de piezas | [] |
| 7853619060 | portalempleo | Atención de mostrador | reposición de mercadería; atención al público; depósito; embalaje; carga y descarga | [] |

**Hipótesis del patrón:** cuando el oficio se describe con nominalizaciones terse tipo "Manejo de X", "Instalación de Y", "Reposición de Z" — sin verbo conjugado y a veces indistinguibles en forma de un requisito ("manejo de" es también marcador de requisito) — la regla de atribución las descarta y v12 se vacía. Es el reverso exacto de la precisión que ganamos (requisito-como-tarea 3,6%→0%): la misma estrictez que elimina el requisito-como-tarea puede comerse la nominalización-que-sí-es-tarea del oficio.

## El caso-frontera

| id | portal | título | v11 | v12 |
|---|---|---|---|---|
| 8802322877 | computrabajo | Ejecutivo de ventas en calle | Desarrollar cartera; trabajar bajo comisiones; trabajar autónomo/equipo; cumplir objetivos | [] |

v11 mezclaba 1 tarea plausible ("desarrollar y potenciar cartera de clientes", embebida en el pitch de intro) con 3 no-tareas (comisiones=condición, autónomo/equipo=modalidad, cumplir objetivos=vago). v12 las descartó todas. La pregunta es si "desarrollar cartera" en el párrafo de presentación cuenta como tarea atribuida o como pitch.

## A dónde va

El patrón viajó a Cyn como **pregunta 3** del paquete (`exports/cyn_backlog/N_pregunta_granularidad_y_4_revisar.md`), junto con la pregunta de granularidad y los 4 REVISAR. **El ajuste fino del prompt y el re-gate corren con su respuesta** — no se toca nada antes.
