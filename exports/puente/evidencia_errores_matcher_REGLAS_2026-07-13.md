# Evidencia de errores del matcher — lote REGLAS de Cyn (2026-07-13)

> Pares (esco extraído por el sistema → esco correcto de Cyn) de la Hoja 1 de
> `docs/REGLAS-v2.xlsx`, donde ambos códigos existen. **Mismo molde que los 104
> override-duro: insumo del diseño del traductor (Eje 4).** La columna `id_oferta_ref`
> vino vacía en todo el lote → se conserva el `titulo_ejemplo` como ancla del aviso.
> Los árboles de desambiguación de cada raíz están en
> `exports/cyn_backlog/taxonomia_contexto_cyn.md` (v2).

| # | raíz ambigua | denominación argentina | título ejemplo | matcher dijo | Cyn corrigió |
|---|---|---|---|---|---|
| 1 | administrativo | Administrativo de obras | Administrativo de obras | `4110` | `4110.1` |
| 2 | analista | Analista de oficina técnica | Analista de oficina técnica | `2142` | `2142.1.2` |
| 3 | supervisor | Supervisor de instalación | Supervisor de instalacion | `3123` | `3123.1` |
| 4 | jefe | Jefe operativo | Jefe operativo ingeniero industrial | `1323` | `1323.1` |
| 5 | electricista | Electricista industrial | Electricista industrial | `8212` | `7411.1.1.2` |
| 6 | operario | Operario de depósito | Operario especializado para depósito | `9329` | `9333.8.1` |
| 7 | técnico | Técnico/a en instalaciones electromecánicas | Técnico/a en instalaciones electromecánicas | `7412` | `7412.7` |
| 8 | ingeniero | Ingeniero/a civil | Ingeniero/a civil | `3112` | `1323.1` |
| 9 | técnico | Técnico instalador / electricista | Tecnico instalador / electricista para la indust | `7411` | `3435.23` |
| 10 | técnico | Técnico en instalación y mantenimiento de equipos de seguridad | Técnico en instalación y mantenimiento de equipo | `3512` | `7422.5` |
| 11 | ingeniero | Ingeniero civil | Ingeniero civil para obra importante constructor | `1323` | `1323.1` |
| 12 | electricista | Electricista matriculado | Electricista matriculado para mantenimiento resi | `7411` | `7411.1.1.1` |
| 13 | responsable | Responsable de mantenimiento edilicio | Responsable de mantenimiento edilicio | `3115` | `1219.1.1` |
| 14 | ingeniero | Ingeniero/a en integración electrónica y electromecánica | Ingeniero/a en integración electrónica y electro | `7412` | `2141.3.2.1` |
| 15 | ingeniero | Ingeniero/a mecánico/electromecánico | Ingeniero/a mecánico, electromecánico | `7412` | `3115.1.6` |
| 16 | técnico | Técnico en instalación de equipos de seguridad | Técnico en instalación de equipos de seguridad | `7422` | `7422.5` |
| 17 | técnico | Técnico en instalación de equipos de seguridad | Técnico en instalación de equipos de seguridad | `3512` | `7422.5` |
| 18 | colocador | Colocador de porcelanato | Colocador de porcelanato | `7131` | `7122.4` |
| 19 | electricista | Oficial electricista | Oficial Electricista | `7131` | `7411.1.1` |
| 20 | pintor | Oficial pintor | Oficial Pintor | `7131` | `7131.1` |
| 21 | herrero / soldador | Oficial herrero / soldador | Oficial Herrero/ Soldador | `7212` | `7212.3` |
| 22 | mampostero | Mampostero | Mampostero | `7131` | `7112.1` |
| 23 | albañil | Oficial albañil | Oficial Albañil | `7112` | `7112.1` |
| 24 | encargado | Encargado de edificio | Encargado de edificio I | `1219` | `5153.1` |
| 25 | ingeniero / arquitecto | Ingeniero civil o arquitecto jefe de obra | Ingeniero civil o arquitecto para jefe de obra | `1323` | `1323.1` |
| 26 | aprendiz | Aprendiz de instalador | Aprendiz de Instalador | `3114` | `7119.4` |
| 27 | operario | Operario de carga y descarga | Operarios de carga y descarga-eventuales | `9333` | `9333.3` |
| 28 | ingeniero | Ingeniero/a civil | Ingeniero/a civil | `2149` | `2142.1` |
| 29 | ingeniero | Ingeniero/a eléctrico | Ingeniero/a eléctrico | `2151` | `2151.1` |
| 30 | administrativo | Administrativo de infraestructura | Administrativo de infraestructura | `4110` | `3343.1` |
| 31 | técnico | Técnico oficial | Técnico Oficial | `8159` | `7119.4` |
| 32 | técnico / ingeniero | Técnico / ingeniero eléctrico-electrónico | Tecnico/ ingeniero. electrico- electronico | `3512` | `2152.1.3` |
| 33 | técnico | Técnico electromecánico de mantenimiento | Técnico electromecánico para mantenimiento | `7412` | `3113.1.2` |
| 34 | técnico electricista / electromecánico | Técnico electricista / electromecánico de taller | Tecnico electricista / electromecánico - taller | `7411` | `7412.3` |
| 35 | técnico eléctrico / electromecánico | Técnico eléctrico / electromecánico | Técnico electrico, electromecanico o afines | `7412` | `7412.3` |
| 36 | técnico | Técnico de mantenimiento eléctrico industrial | Técnico de mantenimiento eléctrico industrial | `7412` | `7411.1.1.2` |
| 37 | ingeniero | Ingeniero civil | Ing. civil | `2142` | `1323.1` |
| 38 | técnico electricista / electromecánico | Técnico electricista / electromecánico de taller | Técnico electricista / electromecánico - taller | `7411` | `7412.3` |
| 39 | técnico | Técnico en ascensores | Técnico en ascensores | `7412` | `7412` ⚠label=técnico de ascensores→resuelve `7412.7` |
| 40 | técnico electricista / electromecánico | Técnico electricista / electromecánico | TÉCNICO ELECTRICISTA / ELECTROMECÁNICO | `7411` | `7411.1.1.2` |
| 41 | técnico electromecánico | Técnico electromecánico de mantenimiento | Técnico electromecánico para mantenimiento | `7412` | `7412.3` |
| 42 | supervisor | Supervisor/a de montaje / ascensores | Supervisor/a de montaje / ascensores | `7412` | `3123.1.14` |
| 43 | técnico | Técnico de puesta en marcha de ascensores | Técnico de puesta en marcha de ascensores | `7412` | `7412` ⚠label=técnico de ascensores→resuelve `7412.7` |
| 44 | técnico | Technical monitoring operations | Technical monitoring operations | `2132` | `3511.1` |
| 45 | sobrestante | Sobrestante de obra - arq. o ing. civil | Sobrestante de obra - arq. o ing. civil | `2142` | `3123.1` |
| 46 | técnico | Técnicos eléctricos/electrónicos | Técnicos eléctricos/electrónicos | `3114` | `7411.1.1.2` |
| 47 | jefe | Jefe de obra - ingeniero civil o arquitecto | Jefe de obra - ingeniero civil o arquitecto | `1323` | `1323.1` |
| 48 | técnico | Técnico instalador de alarmas | Técnico instalador de alarmas | `7421` | `7422.5` |
| 49 | técnico | Ref.21177: técnico mecánico de elevadores | Ref.21177: técnico mecánico de elevadores | `7412` | `7412` ⚠label=técnico de ascensores→resuelve `7412.7` |
| 50 | arquitecto | Arquitecto/a junior - dibujo y modelado técnico | Arquitecto/a junior - dibujo y modelado técnico | `3512` | `2161.1` |
| 51 | técnico | Técnico electromecánico - electrónico | mantenimiento | Técnico electromecánico - electrónico | mantenim | `7412` | `7412.3` |
| 52 | jefe | Jefe de obra - ingeniero civil o arquitecto | Jefe de obra - ingeniero civil o arquitecto | `1323` | `1323.1` |
| 53 | instalador | Instaladores de medidores de agua | Instaladores de medidores de agua | `7126` | `7126.8` |
| 54 | técnico | Técnico en electrónica/ingeniero junior | Técnico en electrónica/ingeniero junior | `3114` | `3114.1` |
| 55 | ayudante | Ayudante de terminación (industria gráfica) | Ayudante de terminación (industria gráfica) | `5223` | `7323.1` |
| 56 | técnico | Técnico electrónico, movilidad propia, empresa de seguridad | Técnico electrónico, movilidad propia, empresa d | `7421` | `7422.5` |
| 57 | técnico | Técnicos en electrónica, o en telecomunicaciones | Técnicos en electrónica, o en telecomunicaciones | `2153` | `2153` ⚠inconsistencia interna (árbol dice técnico 3522.1) — en devoluciones |

**Total pares: 57.** Distribución del error: el matcher erra mayormente DENTRO de la
familia técnica (7412↔7411↔3114) pero también cruza grupos ISCO-1 completos
(5223 vendedor→7323 encuadernador; 2132 agrónomo→3511 operador de centro de datos;
3512 TIC→2161 arquitecto; 7131 pintor naval→7112 albañil) — consistente con el patrón
F0.6 (75% de errores gruesos con ISCO-1 mal en familias técnicas).
