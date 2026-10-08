# -*- coding: utf-8 -*-
"""
[FRENTE N — N2] Prompt v12 de extracción de TAREAS: el método de Cyn compilado.

FUENTE: exports/cyn_backlog/validacion_tareas_respuestas_2026-08-26.xlsx
        (columnas "Lógica de razonamiento" + "Claves metodológicas", 28 casos).
La prosa de Cyn es la verdad — acá se COMPILA, no se reescribe. Cada regla lleva
la cita del/los caso(s) de origen (clave→caso N).

Cambios vs v11 (regla 3 del prompt lite):
  - v11 solo pedía "buscar bullets/numeración/'Responsabilidades:'" → ciego a
    prosa, encabezados no canónicos e inglés (frente M).
  - v11 no tenía definición negativa (atribución al puesto) → requisitos-como-tarea.
  - v11 no permitía vacío → alucinación.
  - v11 usaba separador ';' → colisión con contenido. v12 devuelve lista JSON.

Este es un extractor FOCALIZADO en tareas (para el gate). La integración a
producción folddea estas reglas en el prompt de 20 campos — fuera de este encargo.
"""

# El prompt. {cuerpo} se reemplaza con el cuerpo YA limpiado por N1.
# v12.1: reordenado extracción-primero + salida vacía acotada (post gate-1).
# v12.3 (post criterios de Cyn, Excel N_criterios_respuestas_2026-08-26.xlsx): 5 enmiendas —
#   (1) granularidad = autonomía funcional, no sintaxis (hoja 1);
#   (2) nominalizaciones escuetas SÍ extraen si hay acción normalizable (hoja 3 D8);
#   (3) finalidades/resultados no son tareas (hoja 2 C12);
#   (4) fidelidad de nivel de abstracción (hoja 2 C6);
#   (5) variantes del mismo tipo = una unidad preservando alcances (hoja 3 D3).
PROMPT_TAREAS_V12 = """Sos un analista experto en extraer las TAREAS de un aviso de empleo argentino. Tu trabajo es listar TODAS las acciones que el aviso atribuye al puesto, con la granularidad correcta y sin inventar.

## QUÉ ES UNA TAREA
Una acción productiva que la persona realiza EN el puesto: verbo + objeto + (dónde/con qué, cuando el aviso lo dice). Ej: "registrar asientos contables en SAP", "visitar clientes de la zona oeste".

## PASO 1 — ENCONTRÁ EL BLOQUE FUNCIONAL Y RECORRELO COMPLETO
Buscá dónde el aviso dice qué hace la persona. Puede ser: un bloque titulado (Responsabilidades / Funciones / Tareas / Tareas a desarrollar / Descripción de tareas / Principales funciones), la MISIÓN o presentación del rol ("Tu misión será…", "Serás responsable de…", "Como X serás responsable de:"), encabezados interrogativos ("¿Qué vas a hacer?", "¿Qué harás?", "¿Cuál es el desafío?", "Lo que harás") o en inglés ("Responsibilities", "Key Responsibilities", "What you will be doing"), o prosa corrida. Recorré ese bloque COMPLETO y extraé CADA acción: si hay 7 responsabilidades, tienen que salir las 7. No te detengas en la primera. [casos 1,2,5,14,17,24,28]
- La frase de MISIÓN casi siempre contiene tareas: "tu misión será captar nuevos asociados, comercializando planes" → extraé "captar nuevos asociados" Y "comercializar planes". No la trates como mero contexto. [casos 12,13,17,24]

## PASO 2 — RECONOCÉ LAS FORMAS DE LA ACCIÓN (no exijas verbo explícito)
- Regla de nominalización (criterio de Cyn, hoja 3 D8, textual): «reconocer una nominalización como tarea cuando expresa una acción efectivamente realizada en el puesto y puede normalizarse a verbo sin agregar información. No exigir verbo explícito. Si la expresión describe principalmente una herramienta, conocimiento, condición de trabajo, competencia o resultado esperado, no corresponde clasificarla como tarea. En expresiones ambiguas como 'manejo de…', decidir por la función y el contexto del puesto, no por la palabra aislada.»
- Aplicá esto también a LISTAS ESCUETAS de sustantivos-de-acción sin verbo ni encabezado: SÍ se extraen. Calibradores: "manejo de chasis" en un chofer = conducir chasis (TAREA); "reposición de mercadería" = reponer mercadería (TAREA); "instalación de tendidos eléctricos" = instalar tendidos (TAREA). En cambio "manejo de herramientas eléctricas" = instrumento del oficio (NO tarea); "manejo de Excel/AutoCAD" = skill (NO). [hoja 3; casos 1,3,12,17,23,24]
- Gerundios que expresan una acción real → tarea: "comercializando planes" → "comercializar planes"; "reportando anomalías" → "reportar anomalías". Pero un gerundio de MODO o FINALIDAD NO es tarea (ver PASO 5). [casos 4,6,12,24]

## PASO 3 — GRANULARIDAD = AUTONOMÍA FUNCIONAL (no sintaxis)
Criterio de Cyn (hoja 1, textual): «La misma oración no obliga a unir y la presencia de dos verbos no obliga a separar. No decidir por puntuación, oración ni cantidad de verbos.» Decidí por la FUNCIÓN:
- SEPARÁ cuando cada acción representa una función propia y autónoma. Calibradores (hoja 1): "seguir pedidos" ≠ "coordinar con el área comercial la entrega/cobranza" → DOS; "seguir cobranzas" ≠ "controlar vencimientos" → DOS; "participar de ceremonias ágiles" ≠ "articular con desarrolladores/BAs" → DOS; "aportar análisis crítico" ≠ "actuar como nexo" → DOS; "analizar la competencia" ≠ "reportar acciones del mercado" → DOS.
- UNÍ cuando las acciones forman una única unidad funcional y separarlas rompe o altera el sentido: "diseñar, planificar y ejecutar estrategias de testing" (una función de testing); "desarrollar, configurar y mantener pantallas HMI en Fast Tools" (una función sobre el mismo objeto).
- Variantes del MISMO tipo = una unidad preservando los alcances (hoja 3 D3): "manejo de chasis de 8 pallets" + "de 12 pallets" → "conducir chasis (de 8 y 12 pallets)".
- El MISMO verbo sobre OTRO objeto = OTRA tarea: "configurar pantallas HMI en Fast Tools" ≠ "configurar gráficos en DeltaV". [caso 28]
- Una enumeración de OBJETOS o DIMENSIONES no genera una tarea por cada uno: "reportes de crédito, facturación y morosidad" → UNA; "performance, seguridad y usabilidad" son dimensiones de UNA responsabilidad. [casos 1,2,6,14]

## PASO 4 — FIDELIDAD (no eleves de nivel, no concretes de más, no inventes)
- Preservá EXACTAMENTE el nivel de intervención: colaborar ≠ realizar ≠ liderar; participar ≠ coordinar ≠ dirigir; cuidar ≠ mantener ≠ reparar; reportar ≠ reparar. "Colaborar con la liquidación de sueldos" NO es "liquidar sueldos". [casos 1,2,3,5,7,14,16,27]
- Fidelidad de nivel de abstracción (Cyn, hoja 2 C6): no reemplaces la expresión del aviso por concreciones que no surgen de la evidencia; no agregues ítems por conocimiento del área ni por inferencia desde el título — solo lo efectivamente atribuido. Si el aviso dice "estrategia de performance digital", no lo cambies por "campañas en Google Ads y Meta Ads" salvo que el aviso lo diga.
- Conservá la finalidad/condición cuando DELIMITA la tarea ("realizar extracciones para obtención de PRP", "administrar sueros según protocolos"). [casos 2,16]
- No inventes verbos ni completes funciones que el aviso no dice. Un límite temporal ("hasta su resolución") NO autoriza "resolver". [casos 2,3,11]
- Una responsabilidad general/vaga atribuida al puesto SÍ se conserva ("tareas generales de oficina", "contribuir a un ambiente de excelencia"); pero un verbo suelto sin objeto funcional ("trabajar en conjunto con un equipo") NO es tarea. [casos 5,7,18,27]

## PASO 5 — EL TEST DE ATRIBUCIÓN (qué NO es tarea)
Leé la ORACIÓN COMPLETA y preguntá: ¿el aviso asigna esta acción al PUESTO, o describe lo que el candidato debe TENER/SER? NO son tareas: "experiencia en X" / "participación en X" (experiencia previa), "conocimiento de X", "manejo de [herramienta/software]" cuando es requisito, disponibilidad/horario/residencia/movilidad, beneficios, atributos personales, formación/idiomas, y el TÍTULO o RUBRO (no completes funciones típicas de la ocupación que el aviso no enuncia: "Dibujante" no habilita "hacer planos"). Tampoco son tareas los rasgos bajo "Características / Perfil / Autonomía / Iniciativa" ("iniciativa para investigar causas raíz"): son atributos del candidato aunque contengan un verbo. [casos 2,7,8,9,10,11,15,18,19,20,21,25,26]
- FINALIDADES y RESULTADOS ESPERADOS NO son tareas (Cyn, hoja 2 C12): "asegurar una experiencia de asesoramiento…", "garantizar trazabilidad y eficiencia…", "aportar información clave para mejorar estrategias…", "asegurar una respuesta oportuna…" solo se registran si describen una acción laboral real y AUTÓNOMA atribuida al puesto; si son el para-qué o el resultado de otra tarea, NO se extraen. [hoja 2 C12]

## PASO 6 — CUÁNDO DEVOLVER VACÍO (condición ESTRICTA)
Devolvé {{"tareas": []}} SÓLO SI, tras recorrer todo el aviso, NO existe ningún bloque de responsabilidades/funciones/tareas NI la misión atribuye acciones — es decir, el aviso solo trae título, requisitos, perfil y/o beneficios. En ese caso no inventes nada. PERO: si existe un bloque funcional (aunque sus tareas sean breves, como "Asistir a audiencias", "Aplicar tratamientos" o "Reponer productos en góndolas"), NUNCA devuelvas vacío: extraé esas acciones. [casos 8,9,10,11,15,19,20,21,25,26 vacío correcto · 16,18,22,23,27 con tareas]

## PASO 7 — CONTROL FINAL (obligatorio)
Segundo recorrido: (a) COBERTURA — ¿quedó afuera alguna acción del bloque funcional? (b) NO-INVENCIÓN — ¿alguna tarea tuya está inventada, elevada de nivel, o es un fragmento cortado por puntuación/paréntesis (ej. "seguridad y usabilidad")? Corregí antes de responder. [casos 1,2,3,4,28]

## FORMATO
Devolvé SOLO un JSON: {{"tareas": ["...", "..."]}} — texto fiel al aviso, nominalización→verbo. Vacío solo según PASO 6.

## AVISO
{cuerpo}
"""


def build_prompt_v12(cuerpo_limpio):
    """Construye el prompt v12 con el cuerpo YA limpiado por N1."""
    return PROMPT_TAREAS_V12.replace("{cuerpo}", cuerpo_limpio or "(sin descripción)")


# ── ESPEJO DE VERIFICACIÓN — clave de Cyn → sección del prompt que la implementa ──
# (punto de control ANTES de correr nada; a Gerardo con el prompt completo).
# Formato: (clave metodológica, casos de origen, paso del prompt v12 que la cubre)
ESPEJO = [
    ("Recorrer todo el bloque; no detenerse en la primera acción", "1,2,5,14,17,24,28", "PASO 1"),
    ("Las tareas pueden estar fuera de un bloque titulado (misión/presentación)", "6,12,17", "PASO 1"),
    ("Reconocer encabezados no canónicos e interrogativos", "6,7,12,13", "PASO 1"),
    ("Reconocer encabezados en inglés (Responsibilities/What you will do)", "7", "PASO 1"),
    ("Separar requisitos/experiencia de las acciones del puesto", "4,7,8,9,25", "PASO 2"),
    ("Test de atribución: leer la oración completa antes de decidir", "8,10,15,21,25,26", "PASO 2"),
    ("'experiencia en X' / 'participación en X' ≠ tarea actual", "8,9,10,15,21,25", "PASO 2"),
    ("'conocimiento de X' ≠ tarea", "26", "PASO 2"),
    ("'manejo de [herramienta]' como requisito ≠ tarea", "11,15,26", "PASO 2"),
    ("Disponibilidad/modalidad/residencia ≠ tarea", "8,9", "PASO 2"),
    ("El título del puesto y el rubro no generan tareas típicas", "8,9,10,11,15,18,19,20,21,22,26", "PASO 2"),
    ("Reconocer nominalizaciones como acciones", "1,3,12,17,23,24", "PASO 3"),
    ("No exigir verbos en infinitivo", "3,23", "PASO 3"),
    ("Gerundio que expresa acción real → tarea", "4,6,12,24", "PASO 3"),
    ("No todo gerundio es tarea (modo/finalidad)", "24", "PASO 3"),
    ("Varios verbos sobre el mismo objeto = una unidad funcional", "1,2,6,7,28", "PASO 4"),
    ("Mismo verbo, otro objeto = otra tarea", "28", "PASO 4"),
    ("Separar verbos funcionalmente distintos", "1,2,24", "PASO 4"),
    ("Mantener juntas secuencias operativas de un proceso", "3,12,24", "PASO 4"),
    ("Enumeración de objetos/dimensiones no genera tareas por cada uno", "1,2,6,14", "PASO 4"),
    ("Preservar el nivel de intervención (colaborar≠realizar; participar≠coordinar)", "1,2,3,5,7,14,16,27", "PASO 5"),
    ("Conservar finalidad/condición cuando delimita la tarea", "2,16", "PASO 5"),
    ("Finalidad sola ≠ tarea independiente", "6,7,13,24", "PASO 5"),
    ("No inventar verbos; límite temporal no autoriza acción nueva", "2,3,8,11,15", "PASO 5"),
    ("No completar funciones típicas del oficio/título", "3,8,9,10,11,15,18,19,20,21,22,26", "PASO 5"),
    ("Una tarea general/vaga atribuida al puesto se conserva", "5,7,27", "PASO 5"),
    ("Un verbo suelto sin objeto funcional concreto no es tarea", "18", "PASO 5"),
    ("Cero tareas es salida válida", "8,9,10,11,15,19,20,21,25,26", "PASO 6"),
    ("La escasez produce menos extracción, no más", "11", "PASO 6"),
    ("Control final de cobertura", "1,2,3,4,5,14,16,17,22,24,28", "PASO 7"),
    ("Control final de no-invención", "3,10,18,23", "PASO 7"),
    ("Controlar fragmentos huérfanos por corte de puntuación/paréntesis", "2", "PASO 7"),
    ("Un adjetivo de modo (cordial/cálida) no genera tarea aparte ni la invalida", "3,13,14,27", "PASO 5"),
]
