# -*- coding: utf-8 -*-
"""
[FRENTE N — N3] Post-filtro determinístico de la salida del extractor.

Red del lado de SALIDA para los tipos de "sobra" que Cyn marcó en los 28 casos:
  - requisito disfrazado de tarea: "experiencia en X", "conocimiento de X",
    "manejo de [herramienta]" (contexto requisito) → casos 8,9,11,15,25,26.
  - condición/beneficio: "disponibilidad …", modalidad, horario → casos 8,9.
  - fragmento huérfano SIN verbo: resto de una enumeración cortado por
    puntuación/paréntesis ("seguridad y usabilidad") → caso 2.
  - duplicado semántico obvio.

Filosofía (encargo): mejor filtrar de más AL LOG que dejar pasar al corpus. Todo
lo filtrado se registra con el motivo (auditable). NO reescribe tareas: solo las
deja pasar o las descarta con motivo.
"""
import re
import unicodedata

# Lead-ins de REQUISITO / experiencia / conocimiento (nominal, no acción del puesto)
_REQ_RE = re.compile(
    r'^\s*(experiencia\b|conocimientos?\b|manejo de\b|dominio de\b|nivel de\b|'
    r'disponibilidad\b|residir\b|residencia\b|movilidad propia\b|'
    r'secundario\b|primario\b|terciario\b|universitario\b|estudios?\b|'
    r't[ií]tulo\b|matr[ií]cula\b|carnet\b|licencia de conducir\b|'
    r'edad\b|sexo\b)',
    re.IGNORECASE)

# Beneficios / condiciones
_BENEF_RE = re.compile(
    r'^\s*(obra social|prepaga|sueldo|salario|comisiones|bonos?|premios?|'
    r'horario\b|jornada\b|modalidad\b|home office|vacaciones|descuentos?|'
    r'capacitaci[oó]n continua|plan de carrera|remuneraci[oó]n)\b',
    re.IGNORECASE)

# Verbos de acción típicos (para detectar fragmentos SIN verbo). Aproximación:
# un item-tarea válido tiene al menos un verbo (infinitivo -ar/-er/-ir, o
# nominalización reconocida). Si no hay ninguno → huérfano.
_INF_RE = re.compile(r'\b\w{2,}(ar|er|ir)\b', re.IGNORECASE)
_NOMINALIZ = ('carga', 'descarga', 'gestión', 'gestion', 'recepción', 'recepcion',
              'seguimiento', 'control', 'análisis', 'analisis', 'reporte', 'registro',
              'diseño', 'desarrollo', 'mantenimiento', 'uso', 'reparación', 'reparacion',
              'atención', 'atencion', 'elaboración', 'elaboracion', 'administración',
              'administracion', 'planificación', 'planificacion', 'supervisión', 'supervision')


def _norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s.lower()).strip(' .;,')


def _sin_verbo(item):
    """True si el item no tiene verbo ni nominalización → probable huérfano."""
    if _INF_RE.search(item):
        return False
    low = _norm(item)
    return not any(n in low for n in _NOMINALIZ)


def postfiltrar(tareas, log=None):
    """Filtra la lista de tareas. Devuelve (tareas_ok, descartadas).
    `log` opcional: lista donde se appendean dicts {tarea, motivo}.
    """
    ok, descartadas, vistos = [], [], set()
    for t in (tareas or []):
        if not t or not t.strip():
            continue
        item = t.strip()
        motivo = None
        if _REQ_RE.match(item):
            motivo = 'requisito/experiencia/conocimiento'
        elif _BENEF_RE.match(item):
            motivo = 'beneficio/condicion'
        elif _sin_verbo(item):
            motivo = 'fragmento_huerfano_sin_verbo'
        else:
            clave = _norm(item)
            if clave in vistos:
                motivo = 'duplicado_semantico'
            else:
                vistos.add(clave)
        if motivo:
            descartadas.append({'tarea': item, 'motivo': motivo})
            if log is not None:
                log.append({'tarea': item, 'motivo': motivo})
        else:
            ok.append(item)
    return ok, descartadas
