# Insumos FASE 2 del traductor — precompilación desde la segunda ronda de Cyn (2026-08-14)

> Fuente: `segunda_ronda_respuestas_2026-08-14.xlsx` (prosa textual de Cyn — jamás reescrita, acá se CITA). Todo lo de este archivo es material CONDICIONAL: ramas de desambiguación por tareas que NO se crean como reglas planas. Linaje: `segunda_ronda_cyn_2026-08-14`.

## 1. Mini-hub RRHH (reemplazo condicional de R226, retirada)

Denominación de entrada: «analista de RRHH» (+ «analista rrhh», «analista de recursos humanos», «analista generalista de rrhh»). **TRES ramas** (la prosa manda — el encargo citaba 2, Cyn dio 3):

> «Sí, agregar "analista de RRHH" como variante de título, pero no como asignación automática a una única ocupación ESCO. Los avisos revisados muestran que esta denominación es ambigua y requiere desambiguación por tareas: cuando el puesto es generalista e integra procesos de administración de personal, selección, capacitación, desempeño y relaciones laborales, corresponde ESCO 2423.3 — responsable de recursos humanos; cuando el eje es reclutamiento y selección, corresponde ESCO 2423.6 — consultor de selección de personal/consultora de selección de personal; y cuando predominan nómina, novedades y liquidación de haberes, corresponde ESCO 4313.1 — administrativo de nóminas/administrativa de nóminas. Por lo tanto, agregar "analista de RRHH" como forma de entrada, sujeta a desambiguación funcional, y no asociarla automáticamente al destino histórico 2423 — asesor de orientación profesional/asesora de orientación profesional.»

| Rama | Evidencia (tareas) | Destino |
|---|---|---|
| generalista | administración de personal + selección + capacitación + desempeño + relaciones laborales | 2423.3 |
| selección | reclutamiento y selección | 2423.6 |
| nómina | nómina, novedades, liquidación de haberes | 4313.1 |

Cohort de referencia: las 770 que decidía R226 (bandera r14r226 del shadow queda saldada del lado R226).

## 2. Territorio de las 3 auxiliares retiradas (R1/R2/R137 — cohort 548 en `exports/cohorts/cohort_K2_pre_retiro_auxiliares_2026-08-14.json`)

**CAD (ex R1, 238):**
> «3118.3 debe asignarse únicamente cuando las tareas reales tienen como eje elaborar dibujos, planos, modelos 2D/3D y documentación técnica.»

**Diseño (ex R2, 89):**
> «mantener 2166 cuando el núcleo real del puesto sea crear y desarrollar piezas gráficas, identidad visual, materiales publicitarios o contenidos visuales. En los avisos revisados, los perfiles UX/UI/Product Designer correspondieron a 2513.3, Fotógrafo de moda a 3431.1 y Responsable de marketing a 1221.3.2.»

**Picking (ex R137, 221) — tres ramas:**
> «Cuando el eje sea recepción, control y almacenamiento de mercadería, corresponde 9333.8 — mozo de almacén/moza de almacén. Cuando predominen picking, armado, preparación y despacho de pedidos, corresponde 9333.8.1 — responsable de pedidos de almacén. Y cuando el puesto combine carga, descarga, movimiento y tareas generales de depósito/logística, corresponde 9333.3 — operario de logística de almacén/operaria de logística de almacén.»

## 3. Contable: confirmatorio del hub del piloto (respuesta 3) + R14 subordinada

Cyn NO quiere división plana nueva para analista/asistente/auxiliar/administrativo contable — su respuesta ES el modelo de desambiguación del hub contable:

> «"Analista contable" y variantes corresponden a 2411.1.1 cuando predominan análisis de cuentas, cierres, balances, provisiones, desvíos y reportes. "Asistente contable", "Auxiliar contable" y "Administrativo/a contable" corresponden en general a 3313.2 [...] cuando predominan registraciones, facturación, cobranzas, pagos, conciliaciones y soporte operativo contable. Si las tareas son meramente administrativas y lo contable es accesorio, corresponde 3343.1 [...]. Los casos específicamente impositivos pueden corresponder a 2411.1.12 [...] y "Responsable contable" puede corresponder a 2411.1 — contable cuando existe responsabilidad profesional integral. Por lo tanto, no incorporar todos estos títulos dentro de 2411.1.1 ni crear una división única por denominación: mantenerlos sujetos a desambiguación funcional entre reglas ya existentes.»

**Verificación de coherencia con las D del hub contable (confirmatorio):** los 5 destinos de Cyn (2411.1.1 / 3313.2 / 3343.1 / 2411.1.12 / 2411.1) son exactamente inclusiones y D del vecindario contable del piloto (hub 1 inclusión; D01→3313.2; D03/D05→3343.1; D06→asesor fiscal; hub 2 inclusión). **Único matiz:** el hub separa la facturación pura hacia 4311.1 (D02) mientras la prosa de Cyn la agrupa "en general" bajo 3313.2 — no es contradicción (su "en general" lo admite), pero es pregunta fina para la sesión de árboles si el shadow fase 2 muestra volumen en esa frontera.

**Laudo L4 — `subordinadas_al_traductor` (P4 del H):**
- `R14_contador_auditor` — NO se toca ahora; su territorio lo cubre el hub contable. Si el gate del traductor diera NO-GO definitivo, se re-evalúa.

## 4. Seguros patrimoniales (exclusión en R229a — laudo L3)

> «Excluir los casos con ocupación ESCO específica por el objeto de la venta, como seguros patrimoniales, que corresponde a ESCO 3321.3.1 — asesor de seguros/asesora de seguros.»

Aplicado como exclusión simple (`titulo_no_contiene_alguno: ["seguros"]` en R229a): ninguna plana de seguros K-validada (R268b, R132) captura «ejecutivo de venta seguros patrimoniales» → el caso queda al semántico hasta que el hub fase 2 tome el vecindario. Rama precompilada: ejecutivo/vendedor comercial + objeto=seguros → 3321.3.1.

## 5. Venta telefónica (aplicado como planas — acá solo el registro)

R210 → 5244.1 (corrección) + R210b «líder de equipo comercial» → 1221.3.2.1 (excepción distinguible por título). La frontera fina que queda para fase 2: «reservar 4222.1 para puestos cuyo núcleo real sea atención al cliente» — es una D del vecindario ventas (ya existe como D05/D10 en los hubs 16/51).
