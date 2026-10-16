# -*- coding: utf-8 -*-
"""
[FRENTE N — N4] Construye el gold set de tareas desde las marcas de Cyn (28 casos).

gold_tareas por caso = (extraídas correctas, no objetadas) + FALTA (redacción de
Cyn) − SOBRA. Granularidad = la de Cyn (unidad funcional). Se encodean a mano
desde su validación (fuente: validacion_tareas_respuestas_2026-08-26.xlsx) porque
FALTA/SOBRA son prosa libre; los campos estructurales se leen del Excel.

Salida: metrics/gold_set_tareas.json (protegido; repo privado — patrón del gold
set existente database/gold_set_manual_v2.json).
"""
import json
import openpyxl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / 'exports/cyn_backlog/validacion_tareas_respuestas_2026-08-26.xlsx'
OUT = ROOT / 'metrics/gold_set_tareas.json'

# gold_tareas por id (redacción de Cyn, granularidad de unidad funcional).
# [] = salida vacía válida (los OK sin tareas y los que ella dejó en cero).
GOLD = {
    '1118165658': [  # C1 FALLA
        "analizar y evaluar riesgo crediticio para el otorgamiento de líneas de crédito a clientes",
        "realizar seguimiento de pedidos",
        "coordinar con el área comercial la correcta entrega y cobranza de los pedidos",
        "controlar y realizar seguimiento de cuentas corrientes comerciales",
        "gestionar integralmente la facturación",
        "realizar seguimiento de cobranzas",
        "controlar vencimientos",
        "elaborar reportes de crédito, facturación y morosidad",
        "trabajar coordinadamente con las áreas Comercial, Administración y Finanzas",
    ],
    '5790086984': [  # C2 FALLA + sobra huérfano
        "diseñar, planificar y ejecutar estrategias integrales de testing",
        "crear y mantener casos de prueba, planes de testing y documentación técnica detallada",
        "identificar, reportar y dar seguimiento a los bugs hasta su resolución",
        "asegurar que el producto cumpla con los requisitos funcionales y no funcionales (performance, seguridad y usabilidad)",
        "participar de las ceremonias ágiles",
        "articular activamente con desarrolladores, BAs y otros stakeholders",
        "aportar análisis crítico sobre los requerimientos",
        "actuar como nexo entre los equipos técnicos y los clientes",
    ],
    '1118392033': [  # C3 FALLA
        "realizar la carga, descarga y reparto de mercadería a clientes",
        "brindar una atención cordial a los clientes",
        "cuidar el vehículo y la mercadería asignada",
    ],
    '2176458': [  # C4 FALLA
        "mecanizar en máquinas CNC con programación a pie de máquina mediante sistema FAGOR",
        "usar y mantener herramientas de medición",
        "ejecutar las órdenes de trabajo",
        "controlar la entrada y salida al taller de materiales y equipos de trabajo",
        "llevar registro y control de los trabajos realizados y/o a realizar en el taller",
        "mantener en orden el equipo y el sitio de trabajo, reportando cualquier anomalía",
        "cumplir las normas y procedimientos en materia de seguridad integral",
    ],
    '1117972807': [  # C5 FALLA
        "colaborar con la liquidación de sueldos",
        "tareas de contabilidad general",
        "tareas generales de oficina",
    ],
    '1118316198': [  # C6 — re-adjudicado v12.3 (hoja 2 C6). Verificado contra el aviso:
        # las 3 extra (medición/CRM/IA) SÍ están en el bloque "Sus tareas fundamentales serán:" → entran.
        "planificar, ejecutar y optimizar la estrategia de performance digital",
        "impulsar la adquisición de usuarios",
        "monitorear y analizar indicadores clave como CPA, ROAS, conversión, retención y calidad de tráfico",
        "identificar oportunidades de mejora a partir del análisis de datos y comportamiento de usuarios",
        "implementar y validar herramientas de medición, tracking y atribución digital",
        "gestionar acciones de CRM, segmentación y automatización para potenciar la retención",
        "utilizar herramientas de IA para optimizar procesos, generar insights y mejorar el rendimiento de las campañas",
    ],
    '2176705': [  # C7 FALLA
        "diseñar, desarrollar y entregar soluciones de software confiables y de alta calidad",
        "contribuir al desarrollo de código productivo y participar activamente en revisiones de código dentro del equipo",
        "resolver problemas técnicos complejos relacionados con el diseño, el desarrollo y la estabilidad de las aplicaciones",
        "identificar y ejecutar oportunidades de automatización para reducir incidentes recurrentes y mejorar la estabilidad operativa",
        "participar en evaluaciones técnicas con proveedores externos, startups y equipos internos cuando sea requerido",
        "promover el uso de nuevas tecnologías, herramientas y buenas prácticas dentro de la comunidad de ingeniería",
        "contribuir a una cultura de diversidad, equidad e inclusión dentro del equipo y la organización",
    ],
    '6477274334': [],  # C8 FALLA (sobra 2) → cero tareas
    '1118058753': [],  # C9 FALLA (sobra 2) → cero tareas
    '6265862938': [],  # C10 FALLA (sobra 1) → cero tareas
    '6171358600': [],  # C11 FALLA (sobra 2) → cero tareas
    '2185030': [  # C12 FALLA
        "captar nuevos asociados",
        "comercializar planes de cobertura médica",
        "realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta",
        "recibir y gestionar leads provenientes de distintos canales",
        "registrar y realizar seguimiento de la gestión comercial en CRM",
        "analizar la competencia",           # C12 v12.3: separadas (autonomía funcional, hoja 1)
        "reportar acciones del mercado",
    ],
    '5273316732': [  # C13 FALLA
        "ofrecer productos bancarios",
        "comunicarse de manera clara, efectiva y persuasiva para generar ventas",
    ],
    '5917821361': [  # C14 FALLA
        "brindar atención cordial, eficiente y resolutiva a los clientes en sala y vía pública",
        "promocionar los servicios, eventos y beneficios del Bingo",
        "garantizar una experiencia satisfactoria y segura bajo los protocolos de servicio",
        "colaborar en acciones de marketing y fidelización de clientes",
    ],
    '5650193558': [],  # C15 FALLA (sobra 1) → cero tareas
    '2176546': [  # C16 OK (5 tareas, se conservan tal cual)
        "realizar extracciones de sangre para la obtención de plasma rico en plaquetas (PRP)",
        "administrar sueros vitamínicos según protocolos establecidos",
        "brindar atención y orientación a los pacientes durante los procedimientos",
        "mantener un ambiente de trabajo seguro y estéril",
        "colaborar con el equipo para asegurar la calidad del servicio",
    ],
    '2169530': [  # C17 FALLA
        "realizar el mantenimiento preventivo y correctivo de una flota vehicular, incluyendo máquinas viales, camiones y utilitarios",
        "reparar maquinarias pesadas, camiones y utilitarios",
        "diagnosticar y resolver fallas mecánicas en sistemas hidráulicos y neumáticos",
        "realizar reparaciones generales y trabajos de soldadura",
    ],
    '2168972': [  # C18 FALLA (sobra 1)
        "asistir a audiencias",
        "realizar el seguimiento de la cartera de clientes",
    ],
    '6097371222': [],  # C19 OK → cero tareas
    '2172514': [],     # C20 OK → cero tareas
    '5909299836': [],  # C21 OK → cero tareas
    '5160083235': [    # C22 OK (1 tarea)
        "reponer los productos en góndolas",
    ],
    '6483882943': [    # C23 OK (1 tarea)
        "realizar la carga y descarga de mercadería",
    ],
    '2187269': [  # C24 FALLA (gemelo de C12)
        "captar nuevos asociados",
        "comercializar planes de cobertura médica",
        "realizar prospección activa presencial y/o digital de nuevos clientes individuales y corporativos, gestionando el proceso completo de venta: presupuestación por segmento, cierre y documentación para el alta",
        "recibir y gestionar leads provenientes de distintos canales",
        "registrar y realizar seguimiento de la gestión comercial en CRM",
        "analizar la competencia",
        "reportar acciones del mercado",
    ],
    '1118076732': [],  # C25 FALLA (sobra 2) → cero tareas
    '2181056': [],     # C26 FALLA (sobra 1) → cero tareas
    '1118300373': [  # C27 FALLA
        "aplicar tratamientos de medicina regenerativa y estética ginecológica",
        "participar en la formación y capacitación en protocolos exclusivos",
        "brindar atención profesional, cálida y empática a las pacientes",
        "contribuir a un ambiente de excelencia e innovación en medicina estética",
    ],
    '2176620': [  # C28 FALLA
        "desarrollar, configurar y mantener pantallas HMI en Fast Tools (Yokogawa) para sistemas SCADA de producción y facilities",
        "programar y configurar gráficos de proceso, tendencias y alarmas en DeltaV Operate para plantas de tratamiento y baterías de producción",
        "diseñar arquitecturas de visualización SCADA integradas, asegurando consistencia entre sistemas Fast Tools y DeltaV",
        "implementar estándares de HMI según ISA-101 y guías de alto rendimiento (High Performance HMI)",
        "coordinar con Operaciones para definir requerimientos de visualización y optimizar interfaces de operador",
        "elaborar documentación técnica de pantallas SCADA (especificaciones funcionales, narrativas de operación, manuales de usuario)",
        "supervisar contratistas de servicios de automatización en desarrollos SCADA",  # C28 v12.3: verificado en el texto → entra
    ],
    # ── 4 casos de la hoja 3 (listas escuetas sin verbo) — veredicto de Cyn ──
    # v12.4 FLIP (Frente_N_preguntas_Cyn (3), hoja "3-listas sin verbo", fila chofer +
    # QWEN_TAREAS_CASOS_ENTRENAMIENTO caso 17): el chofer VUELVE A VACÍO. Sus actividades
    # ("Manejo de Chasis…", "Manejo de Remitos", "control de la mercadería") están TODAS
    # bajo "Requisitos Excluyentes: Experiencia Verificable en el manejo de:" → requisitos,
    # NO tareas (RG-TAR-005). v12.2 trabajaba BIEN dejándolo []. El oro se corrige (el
    # principio de COMO_USAR orden 6: la referencia oro puede necesitar corrección).
    '1117212619': [],  # Chofer de camiones → VACÍO (flip v12.4, RG-TAR-005)
    '2184455': [  # Electricista/Montador/Herrero — todas menos "manejo de herramientas" (RG-TAR-008)
        "instalar tendidos eléctricos en automotores",
        "laminar y pulir PRFV",
        "fabricar y reparar piezas en fibra de vidrio",
        "armar estructuras metálicas",
    ],
    '7853619060': [  # Atención de mostrador — bloque "Tareas principales" (6, incl. limpieza)
        "reponer mercadería",
        "atender al público",
        "realizar tareas de depósito",
        "embalar",
        "cargar y descargar mercadería",
        "limpiar y mantener el lugar de trabajo",  # v12.4: 6ta tarea, verificada en el bloque
    ],
    '8802322877': [  # Ejecutivo de ventas — "desarrollar y potenciar cartera" (una sola, del pitch)
        "desarrollar y potenciar la cartera de clientes",
    ],
    # ── 11 casos NUEVOS de entrenamiento (QWEN_TAREAS_CASOS_ENTRENAMIENTO) — v12.4 ──
    # Gold encodeado contra el cuerpo real de BD (verificado). Idioma fiel al aviso.
    '8839648839': [  # caso 1 — Project Manager (indeed, aviso EN → el modelo TRADUCE al español).
        # Gold en español (fiel a la salida del modelo con prompt en español). Preservar nivel (RG-TAR-014).
        "gestionar integralmente el proceso de entrega de las órdenes asignadas",
        "coordinar con recursos internos y terceros contratados para cumplir requisitos y plazos del cliente",
        "comunicarse regularmente con los clientes brindando actualizaciones claras y consistentes",
        "gestionar tareas como la orden de circuitos de internet, proyectos VoIP alojados y procesos de portabilidad numérica",
        "documentar dependencias y prioridades para la ejecución del proyecto",
        # fuera: "utilizar experiencia práctica / demostrar expertise" = experiencia/expertise;
        #        "asumir responsabilidades adicionales según sea necesario" = relleno vago.
    ],
    '7675133068': [  # caso 2 — Cheker Químico (computrabajo). Mismo proceso, tareas distintas (RG-TAR-011).
        "autorizar la puesta en marcha de la línea de producción",
        "realizar seguimiento de los lotes productivos",
        "controlar y liberar áreas de producción",
        "controlar el acondicionamiento en líneas",
        "muestrear materias primas, semielaborados, productos terminados y material de empaque",
        "realizar controles fisicoquímicos de materias primas, semielaborados y productos terminados",
    ],
    '5092480960': [  # caso 3 — Asistente Personal Ejecutiva (computrabajo). Conservar generalidad (RG-TAR-016).
        "gestionar integralmente la agenda y las prioridades",
        "coordinar reuniones, viajes y logística",
        "comunicarse directamente con socios, proveedores y equipo",
        "organizar información sensible y brindar soporte ejecutivo",
        "resolver situaciones con autonomía y criterio",
    ],
    '8493010864': [  # caso 5 — Responsable elaboración cosméticos (computrabajo). Bloque Tareas/Funciones.
        "ejecutar y supervisar la elaboración de productos cosméticos según fórmulas aprobadas y procedimientos establecidos",
        "preparar y dosificar materias primas, controlando pesos, tiempos y condiciones del proceso",
        "controlar parámetros de proceso (temperatura, agitación, tiempos, homogeneidad)",
        "registrar documentación productiva: órdenes de producción, hojas de lote y controles de proceso",
        "coordinar con las áreas de Calidad, I+D y Producción ante desvíos o ajustes de formulación",
        "mantener el orden, limpieza y correcto uso de equipos e instalaciones del laboratorio",
        "detectar desvíos, proponer mejoras y colaborar en la optimización de procesos productivos",
        # fuera (frontera RG-TAR-009, se LISTA para Cyn): "asegurar el cumplimiento de GMP y normativas internas",
        #        "cumplir con normas de seguridad e higiene industrial".
    ],
    '7916148421': [  # caso 6 — Gestor Express (computrabajo). N1 corta el chrome (RG-TAR-001).
        "brindar asesoramiento personalizado a clientes",
        "ordenar y coordinar las filas del banco",
        "atender y gestionar reclamos",
    ],
    '8046413181': [  # caso 7 — Ejecutivo Sr Operaciones Turismo (indeed). "asegurar" como unidad (RG-TAR-013).
        "coordinar documentación de viaje y asegurar que todo esté en tiempo y forma",
        "gestionar bookings para Argentina, Chile, Perú, Colombia y Ecuador",
        "mantener una comunicación fluida, enviando confirmaciones y updates",
        "revisar itinerarios, actualizar costos y coordinar facturación",
        "atender el teléfono de emergencia (rotativo)",
    ],
    '8016348095': [  # caso 8 — Ejecutivo Empresas Minería (indeed). Finalidad subordinada fuera (RG-TAR-013).
        "brindar atención personalizada a compañías de minería, ofreciendo soluciones financieras adaptadas",
        "gestionar y ampliar la cartera de clientes del segmento empresas del sector minero, realizando visitas periódicas",
        "desarrollar propuestas comerciales y financieras para empresas de minería",
        "realizar análisis de riesgos y viabilidad de proyectos comerciales del sector minero",
        "supervisar y hacer seguimiento de las operaciones y servicios brindados",
        "identificar oportunidades de negocio, participando en la promoción de productos y servicios",
        # fuera: "asegurando la satisfacción del cliente y el cumplimiento de los plazos" = finalidad.
    ],
    '5558920196': [  # caso 9 — Contador Junior (computrabajo). Función genérica, NO desglosar (RG-TAR-016).
        "realizar tareas administrativas, contables y algunas impositivas",
        # NO inventar "liquidar impuestos / conciliar cuentas / preparar balances".
    ],
    '8665011978': [],  # caso 10 — Empleado Administrativo (indeed) → VACÍO (solo requisito "facturar").
    '8889067032': [  # caso 11 — Supervisor Mantenimiento YPF (indeed). "garantizar/asegurar" como responsabilidad (RG-TAR-013).
        "supervisar y asegurar en campo la correcta ejecución del montaje, precomisionado, comisionado y puesta en marcha de equipos de electricidad, instrumentación y control en pozos del upstream",
        "planificar y participar en la programación de trabajos vinculados a la puesta en marcha de nuevos pozos y optimizaciones",
        "garantizar el cumplimiento de estándares técnicos, de calidad, seguridad, salud y medio ambiente",
        "verificar el cumplimiento de alcances, plazos, instructivos, procedimientos y especificaciones técnicas",
        "gestionar eficientemente la planificación de trabajos, recursos y materiales",
        "asegurar la correcta utilización de sistemas corporativos y la trazabilidad de la información",
        "articular con distintas áreas internas para la ejecución segura y eficiente de las tareas y gestionar permisos de trabajo",
        "elaborar y validar informes de ejecución y documentación técnica",
        "definir y asignar recursos, equipos, herramientas y materiales necesarios",
        "validar el cumplimiento de tareas en campo para su posterior certificación según pliegos técnicos",
    ],
    '8001095540': [  # caso 21 — Account Receivable Analyst (indeed). Tareas concretas MENOS HSE/compliance (RG-TAR-009).
        "analizar las cuentas corrientes de los clientes para detectar y conciliar diferencias y partidas (facturas, notas de crédito, órdenes de pago)",
        "realizar el seguimiento de los clientes deudores vía telefónica, correo electrónico y/o reuniones",
        "ingresar las cobranzas y generar los recibos correspondientes",
        "asesorar al cliente sobre su situación y brindarle soporte para agilizar el cobro de las facturas pendientes",
        "revisar diariamente los extractos bancarios para identificar acreditaciones de pagos no identificados",
        "elaborar y enviar los estados de cuenta a los clientes deudores",
        "realizar diariamente la apertura y el cierre de caja",
        "informar a los responsables de cuenta sobre cualquier riesgo de cobranza",
        "verificar que no existan diferencias cambiarias significativas y generar la corrección correspondiente",
        "brindar asistencia a los auditores externos",
        "crear y validar información financiera para el alta o reactivación de clientes",
        "validar las líneas de crédito de los clientes y gestionar autorización de sobregiros o suspensión de la línea de crédito",
        "generar reportes semanales, quincenales y mensuales de las cuentas por cobrar",
        "realizar la previsión de deudores incobrables",
        "participar como test owner de controles internos",
        "realizar la búsqueda de documentación y carga para el armado de cartas de pago a proveedores intragroup y del exterior",
        # fuera (RG-TAR-009): "conocer los aspectos e impactos ambientales…", "actuar en forma segura",
        #        "cumplir con los procedimientos del sistema de gestión ambiental/seguridad",
        #        "cumplimiento del plan de entrenamientos mandatorios".
    ],
}

# Casos nuevos (no están en la hoja "28 casos" del Excel original): id → (portal, veredicto)
# 4 de la hoja 3 + 11 de QWEN_TAREAS_CASOS_ENTRENAMIENTO (v12.4). Cuerpo desde BD.
NUEVOS_HOJA3 = {
    '1117212619': ('bumeran', 'VACIO (flip v12.4: requisitos, RG-TAR-005)'),
    '2184455': ('zonajobs', 'TAREAS (hoja 3; sin herramientas, RG-TAR-008)'),
    '7853619060': ('portalempleo', 'TAREAS (hoja 3; 6, Tareas principales)'),
    '8802322877': ('computrabajo', 'TAREAS (hoja 3; 1, del pitch, RG-TAR-004)'),
    # ── 11 casos de entrenamiento del maestro (v12.4) ──
    '8839648839': ('indeed', 'caso 1 — nivel de intervencion (RG-TAR-014)'),
    '7675133068': ('computrabajo', 'caso 2 — mismo proceso, tareas distintas (RG-TAR-011)'),
    '5092480960': ('computrabajo', 'caso 3 — generalidad (RG-TAR-016)'),
    '8493010864': ('computrabajo', 'caso 5 — bloque Tareas; HSE fuera (frontera RG-TAR-009)'),
    '7916148421': ('computrabajo', 'caso 6 — chrome del portal (RG-TAR-001/N1)'),
    '8046413181': ('indeed', 'caso 7 — asegurar como unidad (RG-TAR-013)'),
    '8016348095': ('indeed', 'caso 8 — finalidad subordinada fuera (RG-TAR-013)'),
    '5558920196': ('computrabajo', 'caso 9 — funcion generica (RG-TAR-016)'),
    '8665011978': ('indeed', 'caso 10 — VACIO (solo requisito)'),
    '8889067032': ('indeed', 'caso 11 — garantizar como responsabilidad (RG-TAR-013)'),
    '8001095540': ('indeed', 'caso 21 — AR sin HSE/compliance (RG-TAR-009)'),
}

# RG-TAR-003 (multipuesto): id 8126765799 (Operario textil Costureros/Tejedores/Cortadores)
# NO entra al gold. El extractor es por-oferta y NO separa tareas por puesto; scorearlo
# contra una unión de tareas penalizaría injustamente la fusión. Se LISTA para Cyn y se
# cruza con el multi-position del pipeline en el reporte (verificación RG-TAR-003).
MULTIPUESTO_FLAG = {'8126765799': 'Operario textil (Costureros/Tejedores/Cortadores) — RG-TAR-003'}

# Sobras TIPIFICADAS que Cyn marcó explícitamente (para el chequeo "cero sobras").
SOBRAS_TIPIFICADAS = {
    '5790086984': ["seguridad y usabilidad"],                 # fragmento huérfano
    '6477274334': ["atención al cliente", "disponibilidad para trabajar fines de semana"],
    '1118058753': ["realizar selección y administración de personal", "disponibilidad para trabajar presencial"],
    '6265862938': ["atención al público"],
    '6171358600': ["realizar dibujos y planos", "manejar autocad"],
    '5650193558': ["manejo de maquinas de limpieza"],
    '2168972': ["trabajar en conjunto con un equipo comprometido y en constante crecimiento"],
    '1118076732': ["asesoramiento financiero", "normativa y procesos de prevención de lavado de activos"],
    '2181056': ["manejo de protocolo"],
}


def main():
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb['28 casos']
    casos = []
    for r in range(2, ws.max_row + 1):
        g = lambda c: ws[f'{c}{r}'].value
        oid = str(g('B')).strip() if g('B') is not None else None
        if not oid:
            continue
        casos.append({
            'n': g('A'),
            'id_oferta': oid,
            'portal': g('C'),
            'titulo': g('D'),
            'cuerpo': g('E'),
            'sistema_v11_extrajo': g('F'),
            'veredicto_cyn': (g('I') or '').strip(),
            'gold_tareas': GOLD.get(oid, []),
            'sobras_tipificadas': SOBRAS_TIPIFICADAS.get(oid, []),
        })
    faltan = [c['id_oferta'] for c in casos if c['id_oferta'] not in GOLD]
    assert not faltan, f'IDs sin gold encodeado: {faltan}'
    # ── anexar los 4 casos nuevos de la hoja 3 (cuerpo completo desde BD) ──
    import sqlite3
    con = sqlite3.connect(f"file:{ROOT/'database/bumeran_scraping.db'}?mode=ro", uri=True)
    ints = [int(x) for x in NUEVOS_HOJA3]
    ph = ','.join('?' * len(ints))
    cuerpos = {str(r[0]): r[1] for r in con.execute(
        f"SELECT id_oferta, COALESCE(descripcion_utf8,descripcion) FROM ofertas WHERE id_oferta IN ({ph})", ints)}
    n0 = len(casos)
    for i, (oid, (portal, ver)) in enumerate(NUEVOS_HOJA3.items(), 1):
        casos.append({'n': n0 + i, 'id_oferta': oid, 'portal': portal, 'titulo': None,
                      'cuerpo': cuerpos.get(oid), 'sistema_v11_extrajo': None,
                      'veredicto_cyn': ver, 'gold_tareas': GOLD[oid], 'sobras_tipificadas': []})
    doc = {
        'version': '1.2-v12.4',
        'fuente': 'validacion_tareas_respuestas_2026-08-26.xlsx (28) + entrega_maestro_qwen_2026-09 '
                  '(16 RG-TAR + 21 casos entrenamiento + 3 finales + flip chofer)',
        'nota': 'gold re-adjudicado contra las 16 RG-TAR (v12.4). FLIP chofer 1117212619 → [] '
                '(requisitos, RG-TAR-005). mostrador +limpieza (6). 11 casos nuevos de entrenamiento. '
                'multipuesto 8126765799 fuera del gold (RG-TAR-003, se lista para Cyn). '
                'granularidad = autonomía funcional. [] = vacío válido.',
        'multipuesto_flag': MULTIPUESTO_FLAG,
        'n_casos': len(casos),
        'n_ok': sum(1 for c in casos if c['veredicto_cyn'].upper().startswith('OK')),
        'casos': casos,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    tot_gold = sum(len(c['gold_tareas']) for c in casos)
    vac = sum(1 for c in casos if not c['gold_tareas'])
    print(f'gold set -> {OUT}')
    print(f'  casos: {len(casos)}  tareas-oro totales: {tot_gold}  casos vacío-válido: {vac}')
    print(f'  OK (6 intocables esperados): {doc["n_ok"]}')


if __name__ == '__main__':
    main()
