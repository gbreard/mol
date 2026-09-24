"""Fase 5 / B.2 — filtro de vigencia y herencia de estado_ciclo en el sync.

Se prueba contra una SQLite en memoria con el esquema minimo que consume
extraer_ofertas_validadas(), no contra la base real: el resultado tiene que
depender del filtro, no de que ofertas esten vivas hoy.
"""
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.exports.sync_to_supabase import extraer_ofertas_validadas  # noqa: E402

HOY = datetime.now()


def _iso(dias_atras):
    return (HOY - timedelta(days=dias_atras)).isoformat()


@pytest.fixture
def conn():
    c = sqlite3.connect(':memory:')
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE ofertas (
            id_oferta INTEGER PRIMARY KEY, titulo TEXT, empresa TEXT,
            descripcion TEXT, localizacion TEXT, modalidad_trabajo TEXT,
            url_oferta TEXT, portal TEXT, fecha_publicacion_iso TEXT,
            scrapeado_en TEXT, provincia_normalizada TEXT,
            localidad_normalizada TEXT, estado_oferta TEXT,
            fecha_ultimo_visto TEXT, dias_publicada INTEGER,
            categoria_permanencia TEXT, estado_ciclo TEXT,
            fecha_baja TEXT, fecha_ultima_verificacion TEXT,
            fecha_baja_estimada TEXT, fecha_baja_intervalo_desde TEXT,
            fecha_baja_intervalo_hasta TEXT,
            fecha_baja_incertidumbre_dias INTEGER, grupo_oferta_id TEXT,
            es_republicacion INTEGER, numero_republicacion INTEGER,
            tipo_trabajo TEXT
        );
        CREATE TABLE ofertas_nlp (
            id_oferta TEXT PRIMARY KEY, parent_id_oferta TEXT,
            es_suboferta INTEGER DEFAULT 0, titulo_limpio TEXT,
            tareas_explicitas TEXT, mision_rol TEXT, area_funcional TEXT,
            nivel_seniority TEXT, sector_empresa TEXT, clae_code TEXT,
            clae_grupo TEXT, clae_seccion TEXT, clae_score REAL,
            clae_metodo TEXT, tipo_oferta TEXT, tipo_contrato TEXT,
            provincia TEXT, localidad TEXT, modalidad TEXT,
            nivel_educativo TEXT, titulo_requerido TEXT,
            experiencia_min_anios INTEGER, tiene_gente_cargo INTEGER,
            skills_tecnicas_list TEXT, soft_skills_list TEXT,
            tecnologias_list TEXT, herramientas_list TEXT,
            nlp_extraction_timestamp TEXT, nlp_version TEXT
        );
        CREATE TABLE ofertas_esco_matching (
            id_oferta TEXT PRIMARY KEY, esco_occupation_uri TEXT,
            esco_occupation_label TEXT, isco_code TEXT, isco_label TEXT,
            occupation_match_score REAL, occupation_match_method TEXT,
            skills_oferta_json TEXT, skills_matched_essential TEXT,
            skills_demandados_total INTEGER, skills_matcheados_esco INTEGER,
            matching_timestamp TEXT, matching_version TEXT, run_id TEXT,
            estado_validacion TEXT, validado_timestamp TEXT,
            validado_por TEXT, decision_metodo TEXT, regla_aplicada TEXT
        );
    """)
    yield c
    c.close()


def _oferta(c, oid, estado_ciclo, validada=True, fecha_baja=None,
            fecha_ultima_verificacion=None):
    c.execute("INSERT INTO ofertas (id_oferta, titulo, estado_ciclo, fecha_baja,"
              " fecha_ultima_verificacion) VALUES (?,?,?,?,?)",
              (oid, f'Puesto {oid}', estado_ciclo, fecha_baja, fecha_ultima_verificacion))
    c.execute("INSERT INTO ofertas_nlp (id_oferta, es_suboferta) VALUES (?,0)", (str(oid),))
    c.execute("INSERT INTO ofertas_esco_matching (id_oferta, estado_validacion,"
              " validado_timestamp) VALUES (?,?,?)",
              (str(oid), 'validado' if validada else 'pendiente', _iso(1)))
    c.commit()


def _ids(ofertas):
    return {str(o['id_oferta']) for o in ofertas}


# --- que entra y que no -----------------------------------------------------

def test_vigentes_entran_aunque_no_esten_validadas(conn):
    """El panel cuenta ofertas vivas; esperar la validacion las esconderia."""
    _oferta(conn, 1, 'activa', validada=False)
    _oferta(conn, 2, 'presunta_baja', validada=False)
    assert _ids(extraer_ofertas_validadas(conn)) == {'1', '2'}


def test_muertas_viejas_no_entran(conn):
    """76K ofertas muertas hace meses cuestan 15 min por corrida y no se ven."""
    _oferta(conn, 1, 'baja_no_verificada', fecha_baja=_iso(200))
    _oferta(conn, 2, 'baja_inferida', fecha_baja=_iso(200))
    _oferta(conn, 3, 'baja_confirmada', fecha_baja=_iso(200))
    assert extraer_ofertas_validadas(conn) == []


def test_confirmadas_recientes_entran_solo_si_validadas(conn):
    """Alimentan indicadores de duracion; sin validar el dato no es publicable."""
    _oferta(conn, 1, 'baja_confirmada', validada=True, fecha_baja=_iso(30))
    _oferta(conn, 2, 'baja_confirmada', validada=False, fecha_baja=_iso(30))
    assert _ids(extraer_ofertas_validadas(conn)) == {'1'}


def test_confirmada_en_el_borde_de_los_90_dias(conn):
    _oferta(conn, 1, 'baja_confirmada', fecha_baja=_iso(89))
    _oferta(conn, 2, 'baja_confirmada', fecha_baja=_iso(91))
    assert _ids(extraer_ofertas_validadas(conn)) == {'1'}


# --- el tapon: sin esto Supabase congela estados ----------------------------

def test_transicion_reciente_a_muerta_se_manda_una_ultima_vez(conn):
    """Sin el tapon, una oferta que muere sale del filtro y Supabase la deja
    congelada en 'activa' para siempre: el panel sobre-cuenta y no se corrige."""
    _oferta(conn, 1, 'baja_no_verificada', fecha_baja=_iso(2))
    assert _ids(extraer_ofertas_validadas(conn)) == {'1'}


def test_el_tapon_caduca_a_los_7_dias(conn):
    _oferta(conn, 1, 'baja_no_verificada', fecha_baja=_iso(9))
    assert extraer_ofertas_validadas(conn) == []


def test_el_tapon_usa_la_verificacion_si_esta(conn):
    """fecha_baja puede ser vieja y la verificacion que la mato, de ayer."""
    _oferta(conn, 1, 'baja_no_verificada', fecha_baja=_iso(200),
            fecha_ultima_verificacion=_iso(1))
    assert _ids(extraer_ofertas_validadas(conn)) == {'1'}


# --- el `since` no debe recortar a las vigentes ------------------------------

def test_since_no_recorta_las_vigentes(conn):
    """El estado_ciclo cambia cuando el scraper deja de ver la oferta, no cuando
    se la re-matchea: un incremental por validado_timestamp nunca propagaria la
    transicion."""
    _oferta(conn, 1, 'activa')
    conn.execute("UPDATE ofertas_esco_matching SET validado_timestamp=?,"
                 " matching_timestamp=? WHERE id_oferta='1'", (_iso(100), _iso(100)))
    conn.commit()
    assert _ids(extraer_ofertas_validadas(conn, since=_iso(1))) == {'1'}


# --- escape hatch y herencia -------------------------------------------------

def test_sin_filtro_vigencia_trae_las_muertas(conn):
    """Los backfills de columnas nuevas tienen que alcanzar filas ya muertas."""
    _oferta(conn, 1, 'baja_no_verificada', fecha_baja=_iso(200))
    assert _ids(extraer_ofertas_validadas(conn, sin_filtro_vigencia=True)) == {'1'}


def test_subofertas_heredan_el_estado_del_aviso_padre(conn):
    """Una sub-oferta es una posicion dentro del aviso: si el aviso vive, vive."""
    _oferta(conn, 100, 'activa')
    conn.execute("INSERT INTO ofertas_nlp (id_oferta, parent_id_oferta, es_suboferta)"
                 " VALUES ('100_2','100',1)")
    conn.execute("INSERT INTO ofertas_esco_matching (id_oferta, estado_validacion)"
                 " VALUES ('100_2','validado')")
    conn.commit()

    por_id = {str(o['id_oferta']): o for o in extraer_ofertas_validadas(conn)}
    assert set(por_id) == {'100', '100_2'}
    assert por_id['100_2']['estado_ciclo'] == 'activa'
    assert por_id['100_2']['titulo'] == por_id['100']['titulo']


def test_suboferta_de_aviso_muerto_no_entra(conn):
    """La herencia vale en los dos sentidos: no puede sobrevivir a su aviso."""
    _oferta(conn, 100, 'baja_no_verificada', fecha_baja=_iso(200))
    conn.execute("INSERT INTO ofertas_nlp (id_oferta, parent_id_oferta, es_suboferta)"
                 " VALUES ('100_2','100',1)")
    conn.execute("INSERT INTO ofertas_esco_matching (id_oferta, estado_validacion)"
                 " VALUES ('100_2','validado')")
    conn.commit()
    assert extraer_ofertas_validadas(conn) == []
