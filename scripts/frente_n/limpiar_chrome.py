# -*- coding: utf-8 -*-
"""
[FRENTE N — N1] Pre-limpiador de chrome de plataforma (determinístico, sin LLM).

Separa el CUERPO REAL del aviso del contenido agregado por el portal (blurbs de
empresa, ratings, "Ofertas similares" con avisos AJENOS, footer legal, alertas,
menús de navegación, metadata estructurada). Cyn lo valida en su caso 21:
"separo el cuerpo real de la oferta del contenido agregado por la plataforma".

REGLA: la descripción cruda en BD NO se toca. Esta limpieza es SOLO en el camino
de entrada al extractor (y reutilizable por cualquier otro consumidor).

Motivación (frente M): en ComputRabajo el 59% del texto scrapeado es chrome, lo
que (a) diluye la atención del LLM sobre las tareas reales y (b) arriesga
contaminación cruzada (importar tareas de avisos ajenos del bloque "Ofertas
similares").
"""
import re
import unicodedata

# ── ComputRabajo ──────────────────────────────────────────────────────────
# El cuerpo real del aviso termina en el PRIMERO de estos marcadores. Todo lo
# que sigue es chrome del portal (censado en el frente M).
_CT_CORTE = [
    r'\nRequerimientos\b',
    r'\bAcerca de\s',
    r'\bOfertas similares\b',
    r'\bEvaluaci[oó]n general\b',
    r'¡No te pierdas',
    r'\bPalabras clave\s*:',
    r'\bVer detalles legales\b',
    r'Nos tomamos muy en serio',
    r'\bAptitudes asociadas a esta oferta\b',
    r'\bHay\s*\d+\s*aptitudes',
]
_CT_CORTE_RE = re.compile('|'.join(_CT_CORTE), re.IGNORECASE)
# Header que CT antepone al aviso oculto.
_CT_HEADER_RE = re.compile(r'^\s*Ocultaste esta oferta[^\n]*\n', re.IGNORECASE | re.MULTILINE)

# ── Portal Empleo / CABA ──────────────────────────────────────────────────
# Metadata estructurada embebida que el NLP levanta como si fueran tareas
# (frente M P2: "Estudios requeridos:", "Modalidad:", etc.). El separador que
# los scrapers de estos portales insertan es '---'. Cortamos el bloque de
# metadata cuando aparece DESPUÉS del cuerpo. Conservador: solo si hay un '---'.
_META_LABELS = (r'Estudios? (requeridos?|m[ií]nimos?)', r'Modalidad\s*:', r'D[ií]as? laborables?',
                r'Idiomas?\s*:', r'Salario\s*:', r'Horario\s*:', r'Experiencia requerida',
                r'Postularme\b', r'Volver\b', r'versi[oó]n\s*:\s*\d')
_META_RE = re.compile('|'.join(_META_LABELS), re.IGNORECASE)

# ── Indeed ────────────────────────────────────────────────────────────────
# Caso extremo del frente M: descripción == menú de navegación del portal.
# Si el texto es predominantemente menú/nav, se considera SIN cuerpo → ''.
_NAV_MARKERS = ('Registrate', 'Armá tu CV', 'Buscá empleo', 'Iniciar sesión', 'Crear alerta',
                'Portal Empleo', 'Ciudadano', 'Empresas', 'Mi cuenta')


def _es_solo_navegacion(texto):
    """True si el texto parece ser solo chrome de navegación (sin aviso real)."""
    if not texto:
        return True
    hits = sum(1 for m in _NAV_MARKERS if m.lower() in texto.lower())
    # muchos marcadores de nav Y texto corto → es el menú, no un aviso
    return hits >= 3 and len(texto) < 400


def limpiar_chrome(descripcion, portal):
    """Devuelve el cuerpo real del aviso, sin chrome de plataforma.

    NUNCA elide el cuerpo por error: si no reconoce chrome, devuelve el texto
    (normalizado en espacios). Determinístico e idempotente.
    """
    if not descripcion:
        return ''
    d = descripcion
    portal = (portal or '').lower()

    if _es_solo_navegacion(d):
        return ''

    if portal == 'computrabajo':
        d = _CT_HEADER_RE.sub('', d)
        m = _CT_CORTE_RE.search(d)
        if m:
            d = d[:m.start()]
    elif portal in ('portalempleo', 'caba'):
        # cortar el bloque de metadata estructurada si va precedido de '---'
        sep = d.find('---')
        if sep != -1 and _META_RE.search(d[sep:]):
            d = d[:sep]
        else:
            # sin '---': quitar líneas sueltas que sean puramente metadata
            d = '\n'.join(l for l in d.split('\n')
                          if not (l.strip() and _META_RE.match(l.strip())))

    # normalización mínima de espacios (no altera contenido)
    d = re.sub(r'[ \t]+', ' ', d)
    d = re.sub(r'\n{3,}', '\n\n', d)
    return d.strip()


_INF = re.compile(r'\b\w{3,}(ar|er|ir|ando|iendo)\b', re.IGNORECASE)
_NOM = ('carga', 'descarga', 'gestion', 'gestión', 'recepcion', 'recepción', 'seguimiento',
        'control', 'analisis', 'análisis', 'reporte', 'registro', 'diseño', 'desarrollo',
        'mantenimiento', 'instalacion', 'instalación', 'reparacion', 'reparación', 'atencion',
        'atención', 'elaboracion', 'elaboración', 'administracion', 'administración',
        'liquidacion', 'liquidación', 'confeccion', 'confección', 'supervision', 'supervisión',
        'medicion', 'medición', 'limpieza', 'venta', 'ventas', 'asesoramiento')


def parece_solo_titulo(texto):
    """True si el cuerpo (ya limpio) es apenas un título de puesto: corto y SIN
    ningún verbo de acción ni nominalización → el título NO genera tareas (Cyn
    casos 9,10,11,19,20,21,26). Evita alucinación en avisos título-only cuyo
    bloque de metadata N1 ya recortó. Reconoce nominalizaciones para NO marcar
    como título a avisos cortos con tareas reales ('Instalación y mantenimiento…')."""
    if not texto:
        return False  # vacío se maneja aparte (limpiar_chrome ya devolvió '')
    t = texto.strip()
    if len(t) > 120:
        return False
    low = unicodedata.normalize('NFKD', t.lower()).encode('ascii', 'ignore').decode()
    if _INF.search(t):
        return False
    if any(n in low for n in _NOM):
        return False
    return True


def ratio_removido(descripcion, portal):
    """% de texto removido por la limpieza (para medición N1)."""
    if not descripcion:
        return 0.0
    limpio = limpiar_chrome(descripcion, portal)
    return 1 - (len(limpio) / len(descripcion)) if len(descripcion) else 0.0
