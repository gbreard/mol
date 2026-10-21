# -*- coding: utf-8 -*-
"""
[FRENTE N — N2] Prompt de extracción de TAREAS: el método de Cyn compilado.

FUENTE CANÓNICA (v12.4): exports/cyn_backlog/entrega_maestro_qwen_2026-09/
  - QWEN_TAREAS_REGLAS_MAESTRAS (1).xlsx  → las 16 reglas RG-TAR-001..016.
  - QWEN_TAREAS_CASOS_ENTRENAMIENTO (2).xlsx → 21 casos de entrenamiento.
  - Frente_N_preguntas_Cyn (3).xlsx        → revisión de criterio (FLIP del chofer).
  - Frente_N_3_preguntas_finales_Cyn.xlsx  → herramienta/HSE/pitch.
La prosa de Cyn es la verdad — acá se COMPILA, no se reescribe. Cada bloque cita la
regla maestra (RG-TAR-nnn) y/o el caso de origen.

Historial:
  - v11: solo bullets/"Responsabilidades:" → ciego a prosa, inglés, nominalizaciones.
  - v12/v12.1: extracción-primero + vacío acotado + salida JSON.
  - v12.3: 5 enmiendas de los 3 criterios de Cyn (abrió nominalizaciones escuetas).
  - v12.4 (ESTE): compilado contra las 16 RG-TAR. Recalibra la apertura de v12.3 con
    el FLIP del chofer (una lista escueta bajo REQUISITOS/EXPERIENCIA = requisito, NO
    tarea — RG-TAR-005) y cierra los 3 residuales del v12.3:
      · herramienta + verbo ≠ tarea (RG-TAR-008) — electricista;
      · HSE/compliance de cumplimiento ≠ tarea (RG-TAR-009) — Account Receivable;
      · la tarea puede estar en el pitch/presentación (RG-TAR-004) — ejecutivo.
    Agrega RG-TAR-012 (no duplicar tarea general + su desarrollo) y referencia
    RG-TAR-001 (chrome → N1), RG-TAR-002 (metadata de título → NLP) y RG-TAR-003
    (multipuesto → multi-position del pipeline).

Extractor FOCALIZADO en tareas (para el gate). La integración a producción folddea
estas reglas en el prompt de 20 campos — fuera de este encargo.
"""

# El prompt. {cuerpo} se reemplaza con el cuerpo YA limpiado por N1 (RG-TAR-001).
PROMPT_TAREAS_V12 = """Sos un analista experto en extraer las TAREAS de un aviso de empleo argentino. Tu trabajo es listar TODAS las acciones que el aviso atribuye al puesto, con la granularidad correcta y sin inventar. Aplicá las reglas en conjunto (una oración puede activar varias) y leé SIEMPRE la oración completa y su encabezado antes de decidir: lo que manda es la FUNCIÓN del fragmento en el aviso, no la palabra ni la forma aislada.

## QUÉ ES UNA TAREA
Una acción productiva o intervención laboral que la persona realiza EN el puesto: verbo + objeto + (dónde/con qué, cuando el aviso lo dice). Ej: "registrar asientos contables en SAP", "visitar clientes de la zona oeste".

## PASO 1 — ENCONTRÁ TODA LA EVIDENCIA Y RECORRELA COMPLETA (RG-TAR-004)
Buscá dónde el aviso dice qué hace la persona. Puede ser: un bloque titulado (Responsabilidades / Funciones / Tareas / Tareas a desarrollar / Principales funciones / Desafíos), la MISIÓN o presentación del rol ("Tu misión será…", "Serás responsable de…", "Como X serás responsable de:"), encabezados interrogativos ("¿Qué vas a hacer?", "¿Cuáles serán tus desafíos?", "Lo que harás") o en inglés ("Responsibilities", "Key Responsibilities", "What you will be doing"), o prosa corrida. Recorré cada bloque COMPLETO y extraé CADA acción: si hay 7 responsabilidades, salen las 7.
- NO decidas por sección: un bloque extenso de REQUISITOS no bloquea la búsqueda de tareas en otras partes del aviso (RG-TAR-004). Seguí leyendo todo.
- La tarea puede estar en el PÁRRAFO DE PRESENTACIÓN / PITCH, pero SOLO cuando el pitch atribuye una ACCIÓN CONCRETA que la persona HARÁ, típicamente con "para / a fin de / cuya misión es + [verbo de acción]". Ej: "buscamos vendedor PARA desarrollar y potenciar la cartera de clientes" → "desarrollar y potenciar la cartera" es TAREA. [RG-TAR-004; caso 20]
- CUIDADO (esto NO es tarea): el pitch que describe AL CANDIDATO buscado NO genera tareas, aunque mencione el área. "buscamos X CON experiencia/habilidades/actitud en Y", "buscamos X que domine/sepa/maneje Y", "buscamos promotores entusiastas con habilidades de atención al cliente", "¿Qué buscamos en vos? …" → son REQUISITOS/PERFIL (RG-TAR-005). El patrón "para + acción" (lo que la persona hará) es tarea; el patrón "con/que + experiencia/capacidad/actitud" (lo que la persona debe traer) NO lo es. Ante la duda, NO extraigas del pitch.
- La frase de MISIÓN casi siempre contiene tareas cuando enuncia lo que la persona hará: "tu misión será captar nuevos asociados, comercializando planes" → "captar nuevos asociados" Y "comercializar planes".

## PASO 2 — LAS FORMAS DE LA ACCIÓN: nominalización ≠ siempre tarea, requisito ≠ siempre no-tarea (RG-TAR-005, 006, 007)
No exijas verbo explícito, pero DECIDÍ POR LA FUNCIÓN del fragmento, no por su forma:
- Una NOMINALIZACIÓN o lista escueta de sustantivos-de-acción SÍ es tarea cuando el aviso la atribuye al trabajo del puesto —típicamente bajo un encabezado de "Tareas/Funciones/Responsabilidades" (RG-TAR-007) o en la descripción del puesto— y puede pasarse a verbo sin agregar información: "reposición de mercadería" → "reponer mercadería"; "instalación de tendidos eléctricos" → "instalar tendidos eléctricos"; "armado de estructuras" → "armar estructuras". [RG-TAR-006/007; casos 18,19]
- La MISMA expresión NO es tarea cuando el aviso la presenta como REQUISITO: bajo "Requisitos", "Requisitos Excluyentes", "Experiencia (verificable) en…", "Conocimientos de…", "Capacidad para…", "Se requiere…". AHÍ describe lo que el candidato debe TRAER, no lo que hará. Ej (chofer): "Requisitos Excluyentes: Experiencia Verificable en el manejo de: Chasis de 8 pallets… Manejo de Remitos y control de la mercadería" → TODO eso es requisito → NO son tareas, AUNQUE manejar chasis sea la actividad típica del oficio. El título del puesto no autoriza a completar sus tareas típicas. [RG-TAR-005; caso 17]
- Gerundio que expresa una acción real → tarea ("comercializando planes" → "comercializar planes"). Un gerundio de MODO o FINALIDAD NO es tarea (PASO 5).

## PASO 3 — GRANULARIDAD = AUTONOMÍA FUNCIONAL, no sintaxis (RG-TAR-010, 011)
«La misma oración no obliga a unir y la presencia de dos verbos no obliga a separar. No decidir por puntuación, oración ni cantidad de verbos» (Cyn, hoja 1). Decidí por la FUNCIÓN:
- SEPARÁ cuando cada acción es una función propia y autónoma: "seguir pedidos" ≠ "coordinar con el área comercial la entrega/cobranza" → DOS; "seguir cobranzas" ≠ "controlar vencimientos" → DOS; "participar de ceremonias ágiles" ≠ "articular con desarrolladores/BAs" → DOS; "aportar análisis crítico" ≠ "actuar como nexo" → DOS. [RG-TAR-010; casos 12,13]
- Compartir OBJETO, proceso o área NO obliga a unir: sobre el mismo proceso puede haber intervenciones distintas → separalas ("autorizar la puesta en marcha" ≠ "muestrear materias primas" ≠ "realizar controles fisicoquímicos"). [RG-TAR-011; caso 2]
- UNÍ cuando las acciones forman una única unidad funcional y separarlas rompe el sentido: "diseñar, planificar y ejecutar estrategias de testing"; "desarrollar, configurar y mantener pantallas HMI en Fast Tools". El MISMO verbo sobre OTRO objeto = OTRA tarea: "configurar pantallas HMI en Fast Tools" ≠ "configurar gráficos en DeltaV". [caso 28]
- Variantes del MISMO tipo = una unidad preservando los alcances: "chasis de 8 pallets" + "de 12 pallets" → "conducir chasis (de 8 y 12 pallets)".
- Una enumeración de OBJETOS o DIMENSIONES no genera una tarea por cada uno: "reportes de crédito, facturación y morosidad" → UNA.

## PASO 4 — NO DUPLICAR TAREA GENERAL + SU DESARROLLO (RG-TAR-012)
Si el aviso enuncia primero una tarea general y después la desglosa en sus partes concretas, NO cuentes la general Y cada parte como tareas separadas si solo repiten el mismo trabajo. "Gestionar el proceso de cobranzas, incluyendo el seguimiento de pagos, el control de vencimientos y el contacto con morosos" → no extraigas además "gestionar el proceso de cobranzas" como tarea aparte si solo resume lo que sigue. Conservá la general solo si agrega un trabajo distinto.

## PASO 5 — FIDELIDAD Y ATRIBUCIÓN: qué NO es tarea (RG-TAR-008, 009, 013, 014, 015, 016)
- Preservá EXACTAMENTE el NIVEL DE INTERVENCIÓN: colaborar ≠ realizar ≠ liderar; participar ≠ coordinar ≠ dirigir; supervisar ≠ ejecutar; reportar ≠ reparar. "Colaborar con la liquidación de sueldos" NO es "liquidar sueldos"; "coordinar recursos de terceros" NO es "ejecutar el trabajo de esos recursos". [RG-TAR-014]
- NO eleves el nivel de abstracción ni concretes de más: no reemplaces "estrategia de performance digital" por "campañas en Google Ads/Meta" salvo que el aviso lo diga; no agregues ítems por conocimiento del área ni por el título. [RG-TAR-016]
- NORMALIZÁ SIN RECORTAR: podés reformular, pero conservá objetos, métricas, fuentes y alcances explícitos cuando quitarlos cambia lo que la persona hace ("monitorear CPA, ROAS, conversión y retención" no se reduce a "analizar indicadores"). [RG-TAR-015]
- Una HERRAMIENTA NO se vuelve tarea por agregarle un verbo (RG-TAR-008): "manejo de herramientas eléctricas y neumáticas", "usar taladros", "utilizar pulidoras", "emplear remachadoras", "manejo de Excel/AutoCAD/SAP" = instrumento o capacidad de uso → NO son tareas. Solo hay tarea cuando hay una acción PRODUCTIVA concreta: "pulir piezas de PRFV", "perforar piezas" SÍ. [caso 18]
- CUMPLIR NORMAS / SEGURIDAD / AMBIENTE / CAPACITACIONES NO es tarea cuando solo indica cómo debe trabajar la persona (RG-TAR-009): "conocer los riesgos e impactos ambientales", "actuar en forma segura", "cumplir con los procedimientos del sistema de gestión ambiental", "cumplir el plan de entrenamientos obligatorios" → NO. SÍ es tarea cuando hay una función concreta sobre esas materias: controlar, inspeccionar, investigar, gestionar, capacitar, o cuando la responsabilidad atribuida al puesto ES garantizar/verificar el cumplimiento ("garantizar el cumplimiento de estándares de calidad, seguridad y medio ambiente" en un supervisor SÍ, porque es su responsabilidad). [caso 21 (no) vs caso 11 (sí)]
- FINALIDADES y RESULTADOS ESPERADOS NO son tareas (RG-TAR-013): "asegurar una experiencia…", "garantizar trazabilidad y eficiencia…", "aportar información clave para mejorar…", "asegurando la satisfacción del cliente" solo se extraen si son una acción laboral AUTÓNOMA atribuida al puesto; si son el para-qué o el resultado de otra tarea, NO. No decidas por la palabra "asegurar/garantizar": decidí si es responsabilidad propia o resultado subordinado. [casos 7,8,15]
- Tampoco son tareas: "experiencia en X" / "participación en X" (experiencia previa), "conocimiento de X", disponibilidad/horario/residencia/movilidad, beneficios, atributos personales ("proactividad", "orientación a resultados"), formación/idiomas, y el TÍTULO o RUBRO. Un verbo suelto sin objeto funcional ("trabajar en conjunto con un equipo") NO es tarea; una responsabilidad general atribuida al puesto SÍ se conserva ("tareas generales de oficina", "tareas administrativas, contables y algunas impositivas").

## PASO 6 — CUÁNDO DEVOLVER VACÍO (condición ESTRICTA)
Devolvé {{"tareas": []}} SÓLO SI, tras recorrer TODO el aviso (incluido el pitch y la misión), NO hay ningún bloque de responsabilidades/funciones/tareas NI ninguna acción concreta atribuida al puesto con el patrón "para/misión + acción" — es decir, el aviso solo trae título, requisitos, experiencia, perfil, habilidades buscadas y/o beneficios. Muchos avisos son SOLO perfil del candidato: ésos van vacíos. Ejemplos de vacío CORRECTO (NO extraer nada):
- "buscamos un Empleado con experiencia en facturación, que domine un sistema de gestión" → requisitos → [].
- "Requisitos Excluyentes: Experiencia Verificable en el manejo de: Chasis…, Remitos, control de mercadería" → requisitos → [] (aunque sean actividades del oficio, RG-TAR-005).
- "buscando promotores entusiastas con habilidades de atención al cliente. Excluyente: 2 años de experiencia en ventas" → perfil/requisito → [].
- "¿Qué buscamos en vos? Actitud comercial, experiencia en ventas, capacidad para manejar plataformas" → requisitos → [].
- "Requisitos: Conocimiento en redacción de escrituras y manejo de protocolo; perfil ordenado" → requisitos (RG-TAR-005) → [].
- "Buscamos personas con experiencia en administración; Requisitos: conocimientos en ventas y servicio al cliente" → requisitos → [].
NO conviertas el título/rubro en tarea (Promotor→"promover", Vendedor→"vender", Secretaria→"redactar") para llenar la salida. PERO si existe un bloque funcional o una misión con acción concreta (aunque breve: "Reponer productos", "Asistir a audiencias", "para desarrollar la cartera"), NUNCA devuelvas vacío.

## PASO 7 — CONTROL FINAL (obligatorio)
Segundo recorrido: (a) COBERTURA — ¿quedó afuera alguna acción del bloque funcional o del pitch? (b) NO-INVENCIÓN — ¿alguna tarea está inventada, elevada de nivel, es una herramienta verbalizada, es cumplimiento de norma sin función concreta, es una finalidad/resultado, o es un fragmento cortado por puntuación ("seguridad y usabilidad")? ¿alguna vive en realidad bajo "Requisitos"? Corregí antes de responder.

## FORMATO
Devolvé SOLO un JSON: {{"tareas": ["...", "..."]}} — texto fiel al aviso (mismo idioma del aviso), nominalización→verbo. Vacío solo según PASO 6.

## AVISO
{cuerpo}
"""


def build_prompt_v12(cuerpo_limpio):
    """Construye el prompt v12.4 con el cuerpo YA limpiado por N1."""
    return PROMPT_TAREAS_V12.replace("{cuerpo}", cuerpo_limpio or "(sin descripción)")


# ── ESPEJO DE VERIFICACIÓN (v12.4) — regla maestra RG-TAR → paso del prompt que la implementa ──
# Las 16 reglas maestras consolidan las 28/33 claves de los casos. Punto de control
# ANTES de correr nada; a Gerardo con el prompt completo.
# Formato: (RG-TAR id, nombre de la regla, paso del prompt v12.4 que la cubre, nota)
ESPEJO_RG = [
    ("RG-TAR-001", "Depurar chrome del portal del cuerpo", "N1 (limpiar_chrome.py)",
     "Implementada como pre-limpiador determinístico antes del LLM."),
    ("RG-TAR-002", "Separar metadatos incrustados en el título", "NLP título (nlp_titulo_limpieza.json) + PASO 5",
     "La limpieza de título vive en el NLP de producción; el prompt no usa el título para generar tareas."),
    ("RG-TAR-003", "No fusionar tareas de puestos distintos (multipuesto)", "multi-position del pipeline (limpiar_titulos.py)",
     "El split por puesto lo hace el pipeline (sub-ofertas); este extractor es por-oferta. GAP reportado."),
    ("RG-TAR-004", "Los requisitos no bloquean la búsqueda; leer el pitch", "PASO 1", "Residual v12.3 (ejecutivo) cerrado."),
    ("RG-TAR-005", "Actividad dentro de 'Requisitos/Experiencia' ≠ tarea", "PASO 2", "FLIP del chofer: recalibra la apertura de v12.3."),
    ("RG-TAR-006", "Una actividad escrita sin verbo puede ser tarea", "PASO 2", "Si está atribuida al puesto y normaliza a verbo sin agregar."),
    ("RG-TAR-007", "Los encabezados de tareas ayudan a atribuir nominalizaciones", "PASO 2", "Revisar igual cada ítem (no todo lo del bloque es tarea)."),
    ("RG-TAR-008", "Una herramienta no se vuelve tarea por verbalizarla", "PASO 5 + N3", "Residual v12.3 (electricista) cerrado + red N3."),
    ("RG-TAR-009", "Cumplir normas/seguridad/capacitaciones ≠ tarea", "PASO 5 + N3", "Residual v12.3 (Account Receivable) cerrado + red N3. Contraste caso 21 vs 11."),
    ("RG-TAR-010", "Unir o separar según autonomía funcional", "PASO 3", None),
    ("RG-TAR-011", "Mismo objeto/proceso puede contener tareas distintas", "PASO 3", None),
    ("RG-TAR-012", "No duplicar tarea general + su desarrollo", "PASO 4", "Nueva al prompt en v12.4."),
    ("RG-TAR-013", "Distinguir acción principal de modo/finalidad/resultado", "PASO 5", None),
    ("RG-TAR-014", "Preservar el nivel de intervención", "PASO 5", None),
    ("RG-TAR-015", "Normalizar sin recortar contenido", "PASO 5", None),
    ("RG-TAR-016", "No completar una función genérica con tareas específicas", "PASO 5", None),
    ("control final", "Auditar la referencia oro ante discrepancia (COMO_USAR orden 6)", "gold set + adjudicación",
     "El oro se corrige si el extractor recupera una tarea explícita omitida (flip chofer, +supervisar C28)."),
]
