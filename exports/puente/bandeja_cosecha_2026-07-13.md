# Bandeja de COSECHA — material de Cyn (sesión Word 2026-07 + REGLAS-v2.xlsx) · 2026-07-13

> **Dry-run EXACTO**: réplica del resolver real del diccionario (`_match_by_argentino_dict`
> v3.5.8: normalización lowercase + longest-match + contextos + resolución por esco_code)
> con la entrada agregada en memoria, sobre las **69,794 ofertas** con
> `titulo_limpio` (ofertas_nlp). *blast* = ofertas cuyo RESULTADO de resolución cambia
> (NO substring). Motor validado contra el número histórico: `vendedor viajante` = **141**,
> el mismo blast del HOLD de P5.
>
> Códigos: todos validados contra el catálogo (`esco_occupations_full.json`). Los grupos
> G4/G13 del Excel decían `7412` con label «técnico de ascensores» → resuelto por label a
> **7412.7** (el código que Cyn cita en el resto del material). G23 ídem `2153`→**2153.1**.
> Ninguna entrada se inventó; lo que no resuelve está en EXCLUIDAS con motivo.

**Resumen:** LISTAS-PARA-CARGAR=130 (incluye la HOLD-destrabada) · HOLD-≥50=9 · NO-OP=0 · EXCLUIDAS=9 + 15 genéricas/artefactos

---

## 1 · LISTAS-PARA-CARGAR (blast <50, sin colisión — o HOLD destrabado por Cyn)

| # | denominación (candidata) | esco_code | ocupación | blast | linaje | notas |
|---|---|---|---|---|---|---|
| 1 | vendedor viajante | `3322.1` | representante comercial | **141** | Word sesión 2026-07 — HOLD 141 DESTRABADO por decisión escrita de Cyn (Confirmar) | **HOLD 141 DESTRABADO por decisión escrita de Cyn (Confirmar)** — criterio textual en taxonomía «vendedor» · ej: vendedor viajante de autos okm, usados; vendedor viajante de repuestos automotores fu… |
| 2 | supervisor de obra | `3123.1` | supervisor general de construcción | **46** | REGLAS.xlsx Cyn Hoja 2 G16 | ej: técnico/supervisor de obras; técnico/supervisor de obras |
| 3 | coordinador de obra | `1323.1` | director de obra | **28** | REGLAS.xlsx Cyn Hoja 2 G1 | ej: coordinador de obra; coordinador de obra civil |
| 4 | ingeniero eléctrico | `2151.1` | ingeniero eléctrico | **26** | REGLAS.xlsx Cyn Hoja 2 G8 | ej: ingeniero electrico ssr; ingeniero eléctrico de proyectos |
| 5 | técnico electricista industrial | `7411.1.1.2` | electricista industrial | **18** | REGLAS.xlsx Cyn Hoja 2 G3 | ej: tecnico electricista industrial- permanente; técnico electricista industrial |
| 6 | director de obra | `1323.1` | director de obra | **14** | REGLAS.xlsx Cyn Hoja 2 G1 | ej: director de obra; arquitecto/a director de obra |
| 7 | instalador de sistemas de seguridad | `7422.5` | técnico en alarmas de seguridad | **14** | REGLAS.xlsx Cyn Hoja 2 G17 | ej: técnico instalador de sistemas de seguridad; técnico instalador de sistemas de seguridad e… |
| 8 | encargado de edificio | `5153.1` | conserje de edificio | **13** | REGLAS.xlsx Cyn Hoja 2 G11 | ej: encargado de edificio modalidad media jornada…; encargado de edificio modalidad media jornada… |
| 9 | técnico instalador de alarmas | `7422.5` | técnico en alarmas de seguridad | **13** | REGLAS.xlsx Cyn Hoja 2 G17 | ej: técnico instalador de alarmas; tecnico instalador de alarmas |
| 10 | analista de monitoreo | `3511.1` | operador de centro de datos | **12** | REGLAS.xlsx Cyn Hoja 2 G14 | ej: analista de monitoreo de infraestructura ssr.…; analista de monitoreo senior- empresa de ener… |
| 11 | ingeniero electricista | `2151.1` | ingeniero eléctrico | **12** | REGLAS.xlsx Cyn Hoja 2 G8 | ej: ingeniero electricista; ingeniero electricista |
| 12 | gerente de obra | `1323.1` | director de obra | **8** | REGLAS.xlsx Cyn Hoja 2 G1 | ej: gerente de obra; gerente de obra |
| 13 | técnico en electrónica | `3114.1` | ingeniero técnico en electrónica | **8** | REGLAS.xlsx Cyn Hoja 2 G20 | ej: técnico en electrónica; técnico en electrónica digital - caba villa u… |
| 14 | responsable de obra | `1323.1` | director de obra | **7** | REGLAS.xlsx Cyn Hoja 2 G1 | ej: responsable de obra y logística; responsable de obra para fabrica de aberturas |
| 15 | técnico electromecánico de mantenimiento | `7412.3` | mecánico electricista | **7** | REGLAS.xlsx Cyn Hoja 2 G2 | ej: técnico electromecánico de mantenimiento indu…; técnico electromecánico de mantenimiento |
| 16 | encargado de obra | `3123.1` | supervisor general de construcción | **6** | REGLAS.xlsx Cyn Hoja 2 G16 | ej: encargado de obras y mantenimiento industrial; encargado de obra eléctrica |
| 17 | operador noc | `3511.1` | operador de centro de datos | **6** | REGLAS.xlsx Cyn Hoja 2 G14 | ej: operador noc; operador noc con conocimientos en gpon |
| 18 | técnico de mantenimiento de equipos industriales | `7412.3` | mecánico electricista | **6** | REGLAS.xlsx Cyn Hoja 2 G2 | ej: técnico de mantenimiento de equipos industria…; técnico de mantenimiento de equipos industria… |
| 19 | administrativo de mantenimiento | `3343.1` | empleado administrativo | **5** | REGLAS.xlsx Cyn Hoja 2 G10 | ej: administrativo de mantenimiento; administrativo de mantenimiento |
| 20 | desarrollador python sr | `2512.9` | desarrollador de IdC | **5** | Word sesión 2026-07 (estable image7) | ⚠ DISCREPANCIA: `2512.9` = **desarrollador de IdC** (IoT) en el catálogo, pero el criterio de Cyn («desarrollo de software con Python, backend, APIs») describe **desarrollador de software = `2512.4`**. ¿Typo de sub-código? Decidir antes de cargar. · ej: desarrollador python sr para proyectos bancar…; desarrollador python sr para proyectos bancar… |
| 21 | ingeniero en telecomunicaciones | `2153.1` | ingeniero de telecomunicaciones | **5** | REGLAS.xlsx Cyn Hoja 2 G23 | ej: ssr ingeniero en telecomunicaciones orientaci…; ingeniero en telecomunicaciones (trainee / jr… |
| 22 | mecánico electricista | `7412.3` | mecánico electricista | **5** | REGLAS.xlsx Cyn Hoja 2 G2 | ej: técnico mecánico electricista; técnico mecánico electricista / electromecáni… |
| 23 | técnico de ascensores | `7412.7` | técnico de ascensores | **4** | REGLAS.xlsx Cyn Hoja 2 G13 | COMPLEMENTO de entrada existente «tecnico de ascensores» (mismo código; suma la variante acentuada) · ej: representante técnico de ascensores; vendedor técnico de ascensores |
| 24 | técnico de mantenimiento eléctrico industrial | `7411.1.1.2` | electricista industrial | **4** | REGLAS.xlsx Cyn Hoja 2 G3 | ej: técnico de mantenimiento eléctrico industrial; técnico de mantenimiento eléctrico industrial |
| 25 | técnico en ascensores | `7412.7` | técnico de ascensores | **4** | REGLAS.xlsx Cyn Hoja 2 G4 | COMPLEMENTO de entrada existente «tecnico de ascensores» (mismo código; suma la variante acentuada) · ej: supervisor técnico / técnico en ascensores; técnico en ascensores |
| 26 | técnico oficial | `7119.4` | especialista en trabajos verticales | **4** | REGLAS.xlsx Cyn Hoja 2 G5 | ej: técnico oficial; tecnico oficial de mantenimiento |
| 27 | arquitecto dibujante | `2161.1` | arquitecto | **2** | REGLAS.xlsx Cyn Hoja 2 G18 | ej: arquitecto dibujante proyectista semi senior; arquitecto dibujante |
| 28 | arquitecto junior | `2161.1` | arquitecto | **2** | REGLAS.xlsx Cyn Hoja 2 G18 | ej: arquitecto junior; arquitecto junior |
| 29 | electricista de planta | `7411.1.1.2` | electricista industrial | **2** | REGLAS.xlsx Cyn Hoja 2 G3 | ej: técnico electricista de planta; electricista de planta |
| 30 | ingeniero civil estructural | `2142.1` | ingeniero civil | **2** | REGLAS.xlsx Cyn Hoja 2 G7 | ej: jefe de obra- ingeniero civil estructural - a…; jefe de obra- ingeniero civil estructural - a… |
| 31 | técnico de monitoreo | `3511.1` | operador de centro de datos | **2** | REGLAS.xlsx Cyn Hoja 2 G14 | ej: técnico de monitoreo para centro de operacion…; tecnico de monitoreos ambientales |
| 32 | técnico de seguridad electrónica | `7422.5` | técnico en alarmas de seguridad | **2** | REGLAS.xlsx Cyn Hoja 2 G22 | ej: técnico de seguridad electrónica; tecnico de seguridad electronica |
| 33 | técnico electrónico de mantenimiento industrial | `7412.3` | mecánico electricista | **2** | REGLAS.xlsx Cyn Hoja 2 G2 | ej: técnico electrónico de mantenimiento industri…; técnico electrónico de mantenimiento industri… |
| 34 | técnico mecánico de elevadores | `7412.7` | técnico de ascensores | **2** | REGLAS.xlsx Cyn Hoja 2 G13 | ej: ref.21177:técnico mecánico de elevadores; técnico mecánico de elevadores |
| 35 | administrativo de infraestructura | `3343.1` | empleado administrativo | **1** | REGLAS.xlsx Cyn Hoja 2 G10 | ej: administrativo de infraestructura |
| 36 | arquitecto de obra | `3123.1` | supervisor general de construcción | **1** | REGLAS.xlsx Cyn Hoja 2 G16 | ej: arquitecto de obra |
| 37 | ingeniero eléctrico de proyectos | `2151.1` | ingeniero eléctrico | **1** | REGLAS.xlsx Cyn Hoja 2 G8 | ej: ingeniero eléctrico de proyectos |
| 38 | instalador de ascensores | `7412.7` | técnico de ascensores | **1** | REGLAS.xlsx Cyn Hoja 2 G4 | ej: tecnico instalador de ascensores |
| 39 | líder de obra | `1323.1` | director de obra | **1** | REGLAS.xlsx Cyn Hoja 2 G1 | ej: líder de obra |
| 40 | peón de carga | `9333.3` | operario de logística de almacén | **1** | REGLAS.xlsx Cyn Hoja 2 G6 | ej: peón de carga, descarga, orden y limpieza |
| 41 | proyectista de instrumentación | `2152.1.3` | ingeniero de instrumentación | **1** | REGLAS.xlsx Cyn Hoja 2 G9 | ej: proyectista de instrumentación y control - co… |
| 42 | technical monitoring operations | `3511.1` | operador de centro de datos | **1** | REGLAS.xlsx Cyn Hoja 2 G14 | ej: technical monitoring operations |
| 43 | técnico de cctv | `7422.5` | técnico en alarmas de seguridad | **1** | REGLAS.xlsx Cyn Hoja 2 G22 | ej: técnico de cctv |
| 44 | técnico de puesta en marcha de ascensores | `7412.7` | técnico de ascensores | **1** | REGLAS.xlsx Cyn Hoja 2 G13 | ej: técnico de puesta en marcha de ascensores |
| 45 | técnico de sistemas de seguridad | `7422.5` | técnico en alarmas de seguridad | **1** | REGLAS.xlsx Cyn Hoja 2 G17 | ej: técnico de sistemas de seguridad electrónica |
| 46 | arquitecto de documentación técnica | `2161.1` | arquitecto | **0** | REGLAS.xlsx Cyn Hoja 2 G18 | blast 0 hoy → cobertura futura (scraping continuo) |
| 47 | arquitecto modelador técnico | `2161.1` | arquitecto | **0** | REGLAS.xlsx Cyn Hoja 2 G18 | blast 0 hoy → cobertura futura (scraping continuo) |
| 48 | arquitecto proyectista junior | `2161.1` | arquitecto | **0** | REGLAS.xlsx Cyn Hoja 2 G18 | blast 0 hoy → cobertura futura (scraping continuo) |
| 49 | arquitecto recién recibido | `2161.1` | arquitecto | **0** | REGLAS.xlsx Cyn Hoja 2 G18 | blast 0 hoy → cobertura futura (scraping continuo) |
| 50 | arquitecto responsable de obra | `1323.1` | director de obra | **0** | REGLAS.xlsx Cyn Hoja 2 G1 | blast 0 hoy → cobertura futura (scraping continuo) |
| 51 | asistente administrativo de infraestructura | `3343.1` | empleado administrativo | **0** | REGLAS.xlsx Cyn Hoja 2 G10 | blast 0 hoy → cobertura futura (scraping continuo) |
| 52 | auxiliar administrativo de mantenimiento | `3343.1` | empleado administrativo | **0** | REGLAS.xlsx Cyn Hoja 2 G10 | blast 0 hoy → cobertura futura (scraping continuo) |
| 53 | auxiliar de terminación | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 54 | ayudante de encuadernación | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 55 | ayudante de imprenta | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 56 | ayudante de plomería para instalación de medidores | `7126.8` | fontanero | **0** | REGLAS.xlsx Cyn Hoja 2 G19 | blast 0 hoy → cobertura futura (scraping continuo) |
| 57 | ayudante de postimpresión | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 58 | ayudante de taller (lonas y toldos) | `7533.4` | fabricante de artículos textiles confeccionados | **0** | Word sesión 2026-07 (estable image7) | blast 0 hoy → cobertura futura (scraping continuo) |
| 59 | ayudante de terminación gráfica | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 60 | chofer de recolección de residuos | `8332.2` | conductor de vehículo de carga | **0** | Word sesión 2026-07 (estable image7) | ⚠ DISCREPANCIA: `8332.2` = **conductor de vehículo de carga** (genérico), pero existe `8332.8` **conductor de vehículo de recogida de basura**, que calza exacto con el criterio de Cyn («maneja camión o vehículo de recolección de residuos»). Decidir antes de cargar. · blast 0 hoy → cobertura futura (scraping continuo) |
| 61 | colocador de medidores de agua | `7126.8` | fontanero | **0** | REGLAS.xlsx Cyn Hoja 2 G19 | blast 0 hoy → cobertura futura (scraping continuo) |
| 62 | conserje de edificio | `5153.1` | conserje de edificio | **0** | REGLAS.xlsx Cyn Hoja 2 G11 | blast 0 hoy → cobertura futura (scraping continuo) |
| 63 | diseñador de telecomunicaciones | `2153.1` | ingeniero de telecomunicaciones | **0** | REGLAS.xlsx Cyn Hoja 2 G23 | blast 0 hoy → cobertura futura (scraping continuo) |
| 64 | electromecánico de ascensores | `7412.7` | técnico de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G4 | blast 0 hoy → cobertura futura (scraping continuo) |
| 65 | encargado de consorcio | `5153.1` | conserje de edificio | **0** | REGLAS.xlsx Cyn Hoja 2 G11 | blast 0 hoy → cobertura futura (scraping continuo) |
| 66 | encargado de montaje de ascensores | `3123.1.14` | supervisor de instalaciones de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G12 | blast 0 hoy → cobertura futura (scraping continuo) |
| 67 | ingeniero civil de proyectos | `2142.1` | ingeniero civil | **0** | REGLAS.xlsx Cyn Hoja 2 G7 | blast 0 hoy → cobertura futura (scraping continuo) |
| 68 | ingeniero civil en obra | `3123.1` | supervisor general de construcción | **0** | REGLAS.xlsx Cyn Hoja 2 G16 | blast 0 hoy → cobertura futura (scraping continuo) |
| 69 | ingeniero de electricidad industrial | `2151.1` | ingeniero eléctrico | **0** | REGLAS.xlsx Cyn Hoja 2 G8 | blast 0 hoy → cobertura futura (scraping continuo) |
| 70 | ingeniero de instrumentación y control | `2152.1.3` | ingeniero de instrumentación | **0** | REGLAS.xlsx Cyn Hoja 2 G9 | blast 0 hoy → cobertura futura (scraping continuo) |
| 71 | ingeniero de obra civil | `2142.1` | ingeniero civil | **0** | REGLAS.xlsx Cyn Hoja 2 G7 | blast 0 hoy → cobertura futura (scraping continuo) |
| 72 | ingeniero de telecomunicaciones | `2153.1` | ingeniero de telecomunicaciones | **0** | REGLAS.xlsx Cyn Hoja 2 G23 | blast 0 hoy → cobertura futura (scraping continuo) |
| 73 | ingeniero de telecos | `2153.1` | ingeniero de telecomunicaciones | **0** | REGLAS.xlsx Cyn Hoja 2 G23 | blast 0 hoy → cobertura futura (scraping continuo) |
| 74 | ingeniero electrónico orientado a telecomunicaciones | `2153.1` | ingeniero de telecomunicaciones | **0** | REGLAS.xlsx Cyn Hoja 2 G23 | blast 0 hoy → cobertura futura (scraping continuo) |
| 75 | ingeniero eléctrico y de automatización | `2151.1` | ingeniero eléctrico | **0** | REGLAS.xlsx Cyn Hoja 2 G8 | blast 0 hoy → cobertura futura (scraping continuo) |
| 76 | ingeniero en construcciones | `1323.1` | director de obra | **0** | REGLAS.xlsx Cyn Hoja 2 G1 | blast 0 hoy → cobertura futura (scraping continuo) |
| 77 | ingeniero junior en electrónica | `3114.1` | ingeniero técnico en electrónica | **0** | REGLAS.xlsx Cyn Hoja 2 G20 | blast 0 hoy → cobertura futura (scraping continuo) |
| 78 | ingeniero técnico en electrónica | `3114.1` | ingeniero técnico en electrónica | **0** | REGLAS.xlsx Cyn Hoja 2 G20 | blast 0 hoy → cobertura futura (scraping continuo) |
| 79 | instalador de alarmas comerciales | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G17 | blast 0 hoy → cobertura futura (scraping continuo) |
| 80 | instalador de alarmas domiciliarias | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G17 | blast 0 hoy → cobertura futura (scraping continuo) |
| 81 | instalador de medidores de agua | `7126.8` | fontanero | **0** | REGLAS.xlsx Cyn Hoja 2 G19 | blast 0 hoy → cobertura futura (scraping continuo) |
| 82 | instalador de redes de seguridad | `7119.4` | especialista en trabajos verticales | **0** | REGLAS.xlsx Cyn Hoja 2 G5 | blast 0 hoy → cobertura futura (scraping continuo) |
| 83 | instalador de sensores | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G17 | blast 0 hoy → cobertura futura (scraping continuo) |
| 84 | instalador domiciliario de agua | `7126.8` | fontanero | **0** | REGLAS.xlsx Cyn Hoja 2 G19 | blast 0 hoy → cobertura futura (scraping continuo) |
| 85 | jefe de montaje de ascensores | `3123.1.14` | supervisor de instalaciones de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G12 | blast 0 hoy → cobertura futura (scraping continuo) |
| 86 | jefe de obra operativo | `3123.1` | supervisor general de construcción | **0** | REGLAS.xlsx Cyn Hoja 2 G16 | blast 0 hoy → cobertura futura (scraping continuo) |
| 87 | jefe operativo en obra | `1323.1` | director de obra | **0** | REGLAS.xlsx Cyn Hoja 2 G1 | blast 0 hoy → cobertura futura (scraping continuo) |
| 88 | oficial en trabajos verticales | `7119.4` | especialista en trabajos verticales | **0** | REGLAS.xlsx Cyn Hoja 2 G5 | blast 0 hoy → cobertura futura (scraping continuo) |
| 89 | operador de plataforma | `3511.1` | operador de centro de datos | **0** | REGLAS.xlsx Cyn Hoja 2 G14 | blast 0 hoy → cobertura futura (scraping continuo) |
| 90 | operario de encuadernación | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 91 | operario de postimpresión | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 92 | operario de terminación gráfica | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 93 | operario eventual de depósito | `9333.3` | operario de logística de almacén | **0** | REGLAS.xlsx Cyn Hoja 2 G6 | blast 0 hoy → cobertura futura (scraping continuo) |
| 94 | operario gráfico de terminación | `7323.1` | encuadernador | **0** | REGLAS.xlsx Cyn Hoja 2 G21 | blast 0 hoy → cobertura futura (scraping continuo) |
| 95 | operario vertical | `7119.4` | especialista en trabajos verticales | **0** | REGLAS.xlsx Cyn Hoja 2 G5 | blast 0 hoy → cobertura futura (scraping continuo) |
| 96 | plomero instalador | `7126.8` | fontanero | **0** | REGLAS.xlsx Cyn Hoja 2 G19 | blast 0 hoy → cobertura futura (scraping continuo) |
| 97 | portero de edificio | `5153.1` | conserje de edificio | **0** | REGLAS.xlsx Cyn Hoja 2 G11 | blast 0 hoy → cobertura futura (scraping continuo) |
| 98 | proyectista de control | `2152.1.3` | ingeniero de instrumentación | **0** | REGLAS.xlsx Cyn Hoja 2 G9 | blast 0 hoy → cobertura futura (scraping continuo) |
| 99 | representante de ventas industrial | `2433.6.1` | representante técnico de ventas de maquinaria y equipo agrícolas | **0** | Word sesión 2026-07 (estable image7) | blast 0 hoy → cobertura futura (scraping continuo) |
| 100 | responsable de ingeniería de telecomunicaciones | `2153.1` | ingeniero de telecomunicaciones | **0** | REGLAS.xlsx Cyn Hoja 2 G23 | blast 0 hoy → cobertura futura (scraping continuo) |
| 101 | responsable de montaje de ascensores | `3123.1.14` | supervisor de instalaciones de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G12 | blast 0 hoy → cobertura futura (scraping continuo) |
| 102 | supervisor de instalación de ascensores | `3123.1.14` | supervisor de instalaciones de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G12 | blast 0 hoy → cobertura futura (scraping continuo) |
| 103 | supervisor de montaje de ascensores | `3123.1.14` | supervisor de instalaciones de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G12 | blast 0 hoy → cobertura futura (scraping continuo) |
| 104 | supervisor de montaje de medios de elevación | `3123.1.14` | supervisor de instalaciones de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G12 | blast 0 hoy → cobertura futura (scraping continuo) |
| 105 | trabajador de almacén | `9333.3` | operario de logística de almacén | **0** | REGLAS.xlsx Cyn Hoja 2 G6 | blast 0 hoy → cobertura futura (scraping continuo) |
| 106 | trabajador en altura | `7119.4` | especialista en trabajos verticales | **0** | REGLAS.xlsx Cyn Hoja 2 G5 | blast 0 hoy → cobertura futura (scraping continuo) |
| 107 | técnico de barreras y molinetes | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G22 | blast 0 hoy → cobertura futura (scraping continuo) |
| 108 | técnico de colocación de medidores | `7126.8` | fontanero | **0** | REGLAS.xlsx Cyn Hoja 2 G19 | blast 0 hoy → cobertura futura (scraping continuo) |
| 109 | técnico de control de acceso | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G22 | blast 0 hoy → cobertura futura (scraping continuo) |
| 110 | técnico de documentación técnica i&c | `2152.1.3` | ingeniero de instrumentación | **0** | REGLAS.xlsx Cyn Hoja 2 G9 | blast 0 hoy → cobertura futura (scraping continuo) |
| 111 | técnico de ensamble electrónico | `3114.1` | ingeniero técnico en electrónica | **0** | REGLAS.xlsx Cyn Hoja 2 G20 | blast 0 hoy → cobertura futura (scraping continuo) |
| 112 | técnico de equipos de elevación | `7412.7` | técnico de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G4 | blast 0 hoy → cobertura futura (scraping continuo) |
| 113 | técnico de mantenimiento de alarmas | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G17 | blast 0 hoy → cobertura futura (scraping continuo) |
| 114 | técnico de mantenimiento de ascensores | `7412.7` | técnico de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G4 | blast 0 hoy → cobertura futura (scraping continuo) |
| 115 | técnico de mantenimiento eléctrico de planta | `7411.1.1.2` | electricista industrial | **0** | REGLAS.xlsx Cyn Hoja 2 G3 | blast 0 hoy → cobertura futura (scraping continuo) |
| 116 | técnico de operaciones tic | `3511.1` | operador de centro de datos | **0** | REGLAS.xlsx Cyn Hoja 2 G14 | blast 0 hoy → cobertura futura (scraping continuo) |
| 117 | técnico de producción electrónica | `3114.1` | ingeniero técnico en electrónica | **0** | REGLAS.xlsx Cyn Hoja 2 G20 | blast 0 hoy → cobertura futura (scraping continuo) |
| 118 | técnico de puesta en marcha electrónica | `3114.1` | ingeniero técnico en electrónica | **0** | REGLAS.xlsx Cyn Hoja 2 G20 | blast 0 hoy → cobertura futura (scraping continuo) |
| 119 | técnico de servicio electrónico | `3114.1` | ingeniero técnico en electrónica | **0** | REGLAS.xlsx Cyn Hoja 2 G20 | blast 0 hoy → cobertura futura (scraping continuo) |
| 120 | técnico de servicio técnico de calle en seguridad electrónica | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G22 | blast 0 hoy → cobertura futura (scraping continuo) |
| 121 | técnico de servicio técnico industrial | `7412.3` | mecánico electricista | **0** | REGLAS.xlsx Cyn Hoja 2 G2 | blast 0 hoy → cobertura futura (scraping continuo) |
| 122 | técnico de soporte operativo | `3511.1` | operador de centro de datos | **0** | REGLAS.xlsx Cyn Hoja 2 G14 | blast 0 hoy → cobertura futura (scraping continuo) |
| 123 | técnico de verisure | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G17 | blast 0 hoy → cobertura futura (scraping continuo) |
| 124 | técnico electricista/electromecánico de flota | `7412.3` | mecánico electricista | **0** | REGLAS.xlsx Cyn Hoja 2 G2 | blast 0 hoy → cobertura futura (scraping continuo) |
| 125 | técnico electromecánico de ascensores | `7412.7` | técnico de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G13 | blast 0 hoy → cobertura futura (scraping continuo) |
| 126 | técnico electrónico de ascensores | `7412.7` | técnico de ascensores | **0** | REGLAS.xlsx Cyn Hoja 2 G13 | blast 0 hoy → cobertura futura (scraping continuo) |
| 127 | técnico electrónico de seguridad | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G22 | blast 0 hoy → cobertura futura (scraping continuo) |
| 128 | técnico en alarmas de seguridad | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G17 | blast 0 hoy → cobertura futura (scraping continuo) |
| 129 | técnico en trabajos verticales | `7119.4` | especialista en trabajos verticales | **0** | REGLAS.xlsx Cyn Hoja 2 G5 | blast 0 hoy → cobertura futura (scraping continuo) |
| 130 | técnico instalador de equipamiento de seguridad | `7422.5` | técnico en alarmas de seguridad | **0** | REGLAS.xlsx Cyn Hoja 2 G22 | blast 0 hoy → cobertura futura (scraping continuo) |

Variantes que carga cada candidata (género + sin-acentos, convención G3): ver JSON adjunto
`exports/puente/candidatas_cosecha_2026-07-13.json` — el payload de `aplicar_candidata` sale de ahí.

### Secuencia recomendada de carga (por el guard anti-colisión del comando)
Las específicas-largas primero es indiferente; lo que importa: si más adelante se confirma
alguna HOLD corta (ej. «técnico electromecánico»), el comando la rechazará por colisión con
las específicas ya cargadas («técnico electromecánico de ascensores») — es el guard
funcionando: la corta requerirá decisión estructural (traductor), no carga plana.

---

## 2 · HOLD ≥50 (9 — NO se cargan sin decisión explícita de Gerardo/Cyn)

| denominación | esco_code | ocupación | **blast** | linaje | agravantes |
|---|---|---|---|---|---|
| técnico electromecánico | `7412.3` | mecánico electricista | **334** | REGLAS.xlsx Cyn Hoja 2 G2 | colisión intra-tanda con «técnico electromecánico de ascensores» (7412.7) |
| jefe de obra | `1323.1` | director de obra | **181** | REGLAS.xlsx Cyn Hoja 2 G1 | colisión intra-tanda con «jefe de obra operativo» (3123.1) |
| técnico electrónico | `3114.1` | ingeniero técnico en electrónica | **162** | REGLAS.xlsx Cyn Hoja 2 G20 | colisión intra-tanda con «técnico electrónico de ascensores» (7412.7), «técnico electrónico de mantenimiento industrial» (7412.3), «técnico electrónico de seguridad» (7422.5) |
| operario de logística | `9333.3` | operario de logística de almacén | **65** | REGLAS.xlsx Cyn Hoja 2 G6 | — |
| electricista industrial | `7411.1.1.2` | electricista industrial | **63** | REGLAS.xlsx Cyn Hoja 2 G3 | — |
| empleado administrativo | `3343.1` | empleado administrativo | **61** | REGLAS.xlsx Cyn Hoja 2 G10 | — |
| operario de carga y descarga | `9333.3` | operario de logística de almacén | **60** | REGLAS.xlsx Cyn Hoja 2 G6 | — |
| operador de monitoreo | `3511.1` | operador de centro de datos | **55** | REGLAS.xlsx Cyn Hoja 2 G14 | — |
| auxiliar de depósito | `9333.3` | operario de logística de almacén | **53** | REGLAS.xlsx Cyn Hoja 2 G6 | — |

> Las HOLD cortas-genéricas («electromecánico» 746, «técnico electromecánico» 334, «técnico
> electrónico» 162, «técnico instalador» 128→ya excluida, «jefe de obra» 181) son raíces de
> familia con árbol en la taxonomía v2: la recomendación del harness es NO cargarlas planas
> — son el caso de uso del traductor (Eje 4). Las medianas («electricista industrial» 63,
> «operario de carga y descarga» 60, «operario de logística» 65, «auxiliar de depósito» 53,
> «empleado administrativo» 61, «operador de monitoreo» 55) son denominaciones completas con
> calificador: análogas a «vendedor viajante» — cargables si Cyn/Gerardo confirman con muestra.

---

## 3 · NO-OP (0 — ya en el diccionario con el mismo código)

Ninguna candidata resultó NO-OP exacto. (Las cuasi-duplicadas de «tecnico de ascensores»
ya cargada aparecen en LISTAS como COMPLEMENTO: la versión acentuada suma cobertura real —
blast 4 en títulos con tilde — porque el matcher compara strings con acentos.)

---

## 4 · EXCLUIDAS con motivo (9 curadas + 15 genéricas/artefactos del parseo)

| denominación | esco_code | blast | motivo |
|---|---|---|---|
| electromecánico | `7412.3` | 746 | COLISIÓN vs diccionario: colision longest-match: 'electromecánica' <-> 'ing. eléctrica o electromecánica' de 'ing. eléctrica o electromecánica' (2151.1 != 7412.3) — sombreado silencioso, rechazo ruidoso |
| técnico instalador | `7119.4` | 128 | CONDICIONAL: contradice el árbol v1 de la familia «técnico» («Técnico/a instalador» → 7422.5 alarmas por defecto); G5 lo lleva a 7119.4 (redes de seguridad/altura). Depende del aviso → traductor. Además blast 128 (≥50) y colisiona con «técnico instalador de alarmas/equipamiento de seguridad» (7422.5). |
| ingeniero civil | `1323.1` | 76 | CONDICIONAL por construcción: el propio Excel la lleva a DOS códigos (G1→1323.1 si gestiona obra, G7→2142.1 si diseña). El árbol de Cyn la bifurca por tareas → traductor (taxonomía, familia «ingeniero»), no diccionario plano. |
| ingeniero civil | `2142.1` | 76 | CONDICIONAL por construcción: ídem — misma denominación con dos códigos en el propio Excel (G1 vs G7). |
| sobrestante | `3123.1` | 18 | COLISIÓN con «sobrestante de obra / capataz» (3123.1.1 ≠ 3123.1) → rechazo ruidoso. Condicional (GRUPO B v1). |
| sobrestante de obra | `3123.1` | 13 | COLISIÓN con entrada existente «sobrestante de obra / capataz» (3123.1.1 ≠ 3123.1) → rechazo ruidoso del comando. Además es la bifurcación GRUPO B de v1 (capataz/conductor por tareas) → condicional, traductor. |
| ingeniero eléctrico-electrónico | `2152.1.3` | 0 | COLISIÓN intra-tanda con «ingeniero eléctrico» (2151.1, blast 26): substring con código distinto → el comando rechazaría el par. Blast 0 hoy; es denominación compuesta condicional (árbol I&C por tareas) → taxonomía. |
| supervisor técnico de ascensores | `3123.1.14` | 0 | COLISIÓN longest-match con entrada existente «tecnico de ascensores» (7412.7 ≠ 3123.1.14) → rechazo ruidoso del comando. Blast 0 hoy; queda en taxonomía (familia «supervisor», rama ascensores). |
| coordinador de obra en terreno | `3123.1` | 0 | COLISIÓN intra-tanda con «coordinador de obra» (1323.1, blast 28): substring con código distinto. Blast 0 hoy → queda en taxonomía (familia conducción/rama obra vs sobrestante). |

**Genéricas / artefactos del parseo de la prosa de Hoja 2** (la prosa dice «…o personal
técnico que instala…»: descriptor gramatical, no denominación — se listan por transparencia):

| término | grupo | motivo |
|---|---|---|
| personal técnico | G2+G17 | descriptor generico de la prosa ("...o personal tecnico que...") y ademas COLISIONA entre grupos: G2->7412.3 vs G17->7422.5 |
| personal de operaciones | G14 | descriptor generico de la prosa, no denominacion |
| personal de acabado gráfico | G21 | descriptor generico de la prosa, no denominacion |
| personal de mantenimiento edilicio residencial | G11 | descriptor generico de la prosa, no denominacion |
| personal de instalación de medidores | G19 | descriptor generico de la prosa, no denominacion |
| profesional civil | G7 | descriptor generico de la prosa, no denominacion |
| profesional de ingeniería para Oil & Gas | G9 | descriptor generico de la prosa, no denominacion |
| técnico/a (solo) | G9 | artefacto del parser: "Técnico/a o ingeniero/a eléctrico/a-electrónico/a" es una denominación compuesta |
| arquitecto/a (solo) | G18 | la raíz sola no es denominación cargable: es la familia («arquitecto», taxonomía v1) |
| técnico/a de equipos de elevación (G13 dup) | G13 | duplicada de G4 (mismo código): se carga una vez por G4 |
| instalador/a de ascensores (G13 dup) | G13 | duplicada de G4 (mismo código) |
| técnico/a de mantenimiento de ascensores (G13 dup) | G13 | duplicada de G4 (mismo código) |
| técnico/a instalador/a de alarmas (G22 dup) | G22 | duplicada de G17 (mismo código) |
| técnico/a de sistemas de seguridad (G22 dup) | G22 | duplicada de G17 (mismo código) |
| supervisor/a de obra... ingeniero/a civil... (G1/G7/G16 solapes) | G1/G7/G16 | ver colisiones intra-tanda en la bandeja |

---

## 5 · Colisiones intra-tanda detectadas (anticipo del rechazo ruidoso del comando)

| candidata A | código A | candidata B | código B |
|---|---|---|---|
| jefe de obra | `1323.1` | jefe de obra operativo | `3123.1` |
| coordinador de obra | `1323.1` | coordinador de obra en terreno | `3123.1` |
| ingeniero civil | `1323.1` | ingeniero civil | `2142.1` |
| ingeniero civil | `1323.1` | ingeniero civil de proyectos | `2142.1` |
| ingeniero civil | `1323.1` | ingeniero civil estructural | `2142.1` |
| ingeniero civil | `1323.1` | ingeniero civil en obra | `3123.1` |
| técnico electromecánico | `7412.3` | técnico electromecánico de ascensores | `7412.7` |
| técnico electrónico de mantenimiento industrial | `7412.3` | técnico electrónico | `3114.1` |
| electromecánico | `7412.3` | electromecánico de ascensores | `7412.7` |
| electromecánico | `7412.3` | técnico electromecánico de ascensores | `7412.7` |
| técnico instalador | `7119.4` | técnico instalador de alarmas | `7422.5` |
| técnico instalador | `7119.4` | técnico instalador de equipamiento de seguridad | `7422.5` |
| ingeniero civil | `2142.1` | ingeniero civil en obra | `3123.1` |
| ingeniero eléctrico | `2151.1` | ingeniero eléctrico-electrónico | `2152.1.3` |
| supervisor técnico de ascensores | `3123.1.14` | técnico de ascensores | `7412.7` |
| técnico electrónico de ascensores | `7412.7` | técnico electrónico | `3114.1` |
| técnico electrónico | `3114.1` | técnico electrónico de seguridad | `7422.5` |

> El guard de `aplicar_candidata` rechaza CUALQUIER relación de substring entre términos con
> códigos distintos (aunque el longest-match la resolvería): de cada par sólo puede vivir una
> en el diccionario plano. La curación de arriba ya eligió (la específica entra, la genérica
> va a HOLD/taxonomía); los pares donde ambas quedaron en LISTAS son del MISMO código (ok).

---

**Fuentes:** Word `docs/Sesion_Cyn_familias.docx` (sesión Gerardo+Cyn julio 2026; imágenes
EMF transcriptas y verificadas) · Excel `docs/REGLAS-v2.xlsx` Hoja 2 «Reglas consolidadas»
(22 grupos válidos de 24: G15 REQUIERE-REVISION y G24 sin variantes, excluidos — van en
devoluciones). Precedencia: Word manda. La prosa de Cyn es la verdad de dominio: las
variantes se explotaron de su enumeración textual (+ expansión mecánica de género «/a» y
copia sin acentos, convención G3).

**PUNTO DE CONTROL:** Gerardo confirma sobre esta bandeja qué se carga. Ningún write al
diccionario antes de eso (P3: `aplicar_candidata`, squash por sesión, tandas ≤50 con TEST
entre tandas).
