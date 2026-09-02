#!/usr/bin/env python3
"""Guarda de colisiones de id_oferta entre portales.

POR QUE EXISTE
`id_oferta` es PRIMARY KEY unica para TODOS los portales, y los prefijos que
usa cada scraper suponen bandas de 1e9 — pero crc32 llega a 4.29e9, asi que
ComputRabajo (5e9+crc32) se derrama sobre las bandas de Portal Empleo (7e9) e
Indeed (8e9). Medido el 2026-09-01: 10.963 ofertas de CT en la banda 7e9-8e9,
10.928 en 8e9-9e9, 1.035 de PE en la banda de Indeed. Ademas Bumeran y ZonaJobs
comparten backend Navent y usan el id crudo, asi que una vacante publicada en
ambos colisiona por diseno (3.187 ofertas de ZJ tienen id de la banda Bumeran).

Cuando dos portales generan el mismo id, hasta ahora pasaba una de dos cosas, y
ninguna dejaba rastro:

  INSERT OR IGNORE  (zonajobs, computrabajo, caba, portalempleo, indeed)
      -> se descarta la oferta ENTRANTE. Perdida silenciosa.
  INSERT OR REPLACE (bumeran, via db_manager)
      -> se DESTRUYE la fila existente de otro portal, campo `portal` incluido,
         y con ella lo que solo vive en local (estado_validacion, fecha_baja,
         banderas de validacion humana). Sustitucion silenciosa, a diario.

Este modulo NO arregla el espacio de ids (eso es una migracion con spec propia).
Hace la perdida VISIBLE y CONTABLE, y en el unico caso destructivo la BLOQUEA.

ALCANCE
Cubre los puntos de insercion de los scrapers. El sync VPS->local
(sync_from_vps.py ejecutando el SQL de export_nuevas.py) queda FUERA a
proposito: su `ON CONFLICT DO UPDATE` solo toca `descripcion` y con guarda de
longitud, asi que no destruye nada, e instrumentarlo obligaria a reescribir el
generador de SQL del VPS. Costo alto, dano nulo.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Acciones registrables:
#   'rechazada'          -> INSERT OR IGNORE descarto la entrante (perdida)
#   'reemplazo_evitado'  -> se detuvo un REPLACE que iba a destruir la existente
#   'reemplazo'          -> un REPLACE llego a destruir la existente. NO deberia
#                           aparecer nunca: si aparece, hay un camino de
#                           insercion sin cubrir y hay que buscarlo.
ACCIONES = ('rechazada', 'reemplazo_evitado', 'reemplazo')

DDL = """
CREATE TABLE IF NOT EXISTS colisiones_id (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    id_oferta         INTEGER NOT NULL,
    portal_existente  TEXT,
    portal_entrante   TEXT NOT NULL,
    accion            TEXT NOT NULL,
    titulo_entrante   TEXT,
    empresa_entrante  TEXT,
    url_entrante      TEXT,
    titulo_existente  TEXT,
    url_existente     TEXT,
    detectada_en      TEXT NOT NULL,
    nodo              TEXT NOT NULL
)
"""
IDX = ("CREATE INDEX IF NOT EXISTS idx_colisiones_portales "
       "ON colisiones_id(portal_entrante, portal_existente)")


def asegurar_tabla(cur):
    """Crea la tabla si falta. Idempotente, barato: llamar al inicio del insert."""
    cur.execute(DDL)
    cur.execute(IDX)


def _registrar(cur, id_oferta, portal_existente, portal_entrante, accion,
               entrante=None, existente=None, nodo='vps'):
    entrante = entrante or {}
    existente = existente or {}
    cur.execute(
        "INSERT INTO colisiones_id (id_oferta, portal_existente, portal_entrante,"
        " accion, titulo_entrante, empresa_entrante, url_entrante,"
        " titulo_existente, url_existente, detectada_en, nodo)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (id_oferta, portal_existente, portal_entrante, accion,
         entrante.get('titulo'), entrante.get('empresa'), entrante.get('url_oferta'),
         existente.get('titulo'), existente.get('url_oferta'),
         datetime.now().isoformat(), nodo))


def registrar_si_cross_portal(cur, id_oferta, portal_entrante, oferta, nodo='vps'):
    """Para los puntos con INSERT OR IGNORE. Llamar SOLO si rowcount == 0.

    Un rowcount de 0 casi siempre es un duplicado legitimo del mismo portal (el
    caso normal del scraping incremental), asi que primero se lee el portal de
    la fila existente — un SELECT por PK, sobre indice — y recien se escribe si
    difiere. Sin este filtro la tabla se llenaria de ruido.

    Devuelve True si registro una colision cross-portal.
    """
    fila = cur.execute(
        "SELECT portal FROM ofertas WHERE id_oferta = ?", (id_oferta,)).fetchone()
    if not fila:
        return False                      # rechazo por otra causa (constraint, etc.)
    portal_existente = fila[0]
    if portal_existente == portal_entrante:
        return False                      # duplicado legitimo: no es colision
    _registrar(cur, id_oferta, portal_existente, portal_entrante, 'rechazada',
               entrante=oferta, nodo=nodo)
    logger.warning(
        f"  COLISION DE ID: {id_oferta} ya existe como '{portal_existente}', "
        f"se descarta la de '{portal_entrante}' — registrada en colisiones_id")
    return True


def filtrar_reemplazos_cross_portal(cur, values, idx_id, idx_portal, nodo='vps'):
    """Para el punto con INSERT OR REPLACE (Bumeran).

    REPLACE destruiria la fila existente de otro portal. Esta funcion:
      1. lee de una sola consulta el portal de todos los ids del lote,
      2. saca del lote las filas que pisarian a otro portal,
      3. les refresca `fecha_ultimo_visto`: el avistamiento es REAL (ids Navent
         compartidos = mismo aviso vivo publicado en los dos portales), y sin
         esto el aviso caeria como falsa presunta_baja en el ciclo de vida,
      4. registra cada caso como 'reemplazo_evitado'.

    Devuelve (values_a_insertar, n_evitados).
    """
    if not values:
        return values, 0

    ids = [v[idx_id] for v in values]
    existentes = {}
    for i in range(0, len(ids), 900):          # limite de variables de SQLite
        trozo = ids[i:i + 900]
        marcas = ','.join('?' * len(trozo))
        for r in cur.execute(
                f"SELECT id_oferta, portal, titulo, url_oferta FROM ofertas "
                f"WHERE id_oferta IN ({marcas})", trozo):
            existentes[r[0]] = {'portal': r[1], 'titulo': r[2], 'url_oferta': r[3]}

    # `fecha_ultimo_visto` es del ciclo de vida y SOLO existe en la BD local
    # (VPS: 45 columnas, local: 62). En el VPS el UPDATE tiraria "no such column"
    # y —al estar el llamador dentro de un try/except— la guarda quedaria
    # desactivada en silencio, que es justo lo que se quiere evitar.
    tiene_ultimo_visto = any(
        r[1] == 'fecha_ultimo_visto' for r in cur.execute("PRAGMA table_info(ofertas)"))

    a_insertar, evitados, ahora = [], 0, datetime.now().isoformat()
    for v in values:
        oid = v[idx_id]
        portal_entrante = v[idx_portal] if idx_portal is not None else 'bumeran'
        prev = existentes.get(oid)
        if prev and prev['portal'] and prev['portal'] != portal_entrante:
            # el avistamiento es real aunque no insertemos
            if tiene_ultimo_visto:
                cur.execute("UPDATE ofertas SET fecha_ultimo_visto = ? WHERE id_oferta = ?",
                            (ahora, oid))
            _registrar(cur, oid, prev['portal'], portal_entrante, 'reemplazo_evitado',
                       entrante={'titulo': None, 'empresa': None, 'url_oferta': None},
                       existente=prev, nodo=nodo)
            evitados += 1
            continue
        a_insertar.append(v)

    if evitados:
        logger.warning(
            f"  {evitados} REEMPLAZOS CROSS-PORTAL EVITADOS: filas de otro portal que "
            f"habrian sido destruidas. Registradas en colisiones_id; se refresco su "
            f"fecha_ultimo_visto porque el avistamiento es real.")
    return a_insertar, evitados


def resumen(cur):
    """Conteo por (accion, par de portales). Para la query de seguimiento."""
    try:
        return list(cur.execute(
            "SELECT accion, portal_entrante, portal_existente, COUNT(*) "
            "FROM colisiones_id GROUP BY 1,2,3 ORDER BY 4 DESC"))
    except Exception:
        return []
