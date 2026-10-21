"""
Tests del cooldown anti-regiro de ambiguas (2026-10-21).

Problema medido: cola() no filtraba las count=0 por timestamp, así que una oferta
clasificada 'ambigua' se re-elegía cada día y gastaba la cuota girando sobre ofertas
indecidibles por búsqueda (CT: ambigua 88-99%, solo ~653 distintas/sem avanzaban).

Fix: _aplicar setea fecha_ultima_verificacion en ambigua; cola() no re-toma una count=0
hasta pasar cooldown_ambigua (30d por config). Las frescas (timestamp NULL) y las count=1
(gap 72h) no se tocan. Estos tests usan una BD temporal; no tocan red.
"""
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import database.verificador_bajas as vb  # noqa: E402

SCHEMA = """
CREATE TABLE ofertas (
  id_oferta INTEGER PRIMARY KEY, portal TEXT, titulo TEXT, url_oferta TEXT,
  estado_ciclo TEXT, verificaciones_caida_count INTEGER,
  fecha_ultimo_visto TEXT, fecha_ultima_verificacion TEXT,
  fecha_primera_verificacion_caida TEXT,
  fecha_baja_intervalo_desde TEXT, fecha_baja_intervalo_hasta TEXT,
  fecha_baja_estimada TEXT, fecha_baja_incertidumbre_dias INTEGER
);
CREATE TABLE verificaciones_baja (
  id INTEGER PRIMARY KEY AUTOINCREMENT, id_oferta INTEGER, portal TEXT,
  fecha TEXT, via TEXT, resultado TEXT, senal_cruda TEXT
);
CREATE TABLE transiciones_ciclo_vida (
  id INTEGER PRIMARY KEY AUTOINCREMENT, id_oferta INTEGER, portal TEXT,
  estado_desde TEXT, estado_hacia TEXT, motivo TEXT, fecha TEXT
);
"""

NOW = datetime.now()


def _ins(conn, ido, count=0, ult_verif=None, ultimo_visto="2026-08-01T00:00:00"):
    conn.execute(
        """INSERT INTO ofertas (id_oferta, portal, titulo, url_oferta, estado_ciclo,
           verificaciones_caida_count, fecha_ultimo_visto, fecha_ultima_verificacion)
           VALUES (?,?,?,?,?,?,?,?)""",
        (ido, "computrabajo", f"Puesto {ido}", f"http://x/{ido}", "presunta_baja",
         count, ultimo_visto, ult_verif))


@pytest.fixture
def v(tmp_path):
    db = tmp_path / "t.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    ver = vb.VerificadorBajas(db_path=str(db))
    ver.connect()
    yield ver
    ver.close()


def _ids(rows):
    return {r[0] for r in rows}


def test_cooldown_cargado_de_config(v):
    # default 30d (o lo que diga el config)
    assert v.cooldown_ambigua >= timedelta(days=1)


def test_cola_incluye_fresca_null(v):
    # count=0 nunca verificada (timestamp NULL) → siempre elegible
    _ins(v.conn, 1, count=0, ult_verif=None)
    v.conn.commit()
    assert 1 in _ids(v.cola("computrabajo", 100))


def test_cola_excluye_ambigua_en_cooldown(v):
    # count=0 verificada hace 5d (dentro del cooldown 30d) → NO se re-elige
    reciente = (NOW - timedelta(days=5)).isoformat()
    _ins(v.conn, 2, count=0, ult_verif=reciente)
    v.conn.commit()
    assert 2 not in _ids(v.cola("computrabajo", 100))


def test_cola_incluye_ambigua_pasado_cooldown(v):
    # count=0 verificada hace 40d (> cooldown 30d) → vuelve a ser elegible
    viejo = (NOW - timedelta(days=40)).isoformat()
    _ins(v.conn, 3, count=0, ult_verif=viejo)
    v.conn.commit()
    assert 3 in _ids(v.cola("computrabajo", 100))


def test_cola_count1_respeta_gap_no_cooldown(v):
    # count=1 verificada hace 1h (< gap 72h) → NO; hace 100h (> gap) → SÍ.
    # El cooldown de 30d NO aplica a count=1 (mantiene su gap corto para confirmar).
    _ins(v.conn, 4, count=1, ult_verif=(NOW - timedelta(hours=1)).isoformat())
    _ins(v.conn, 5, count=1, ult_verif=(NOW - timedelta(hours=100)).isoformat())
    v.conn.commit()
    got = _ids(v.cola("computrabajo", 100))
    assert 4 not in got and 5 in got


def test_aplicar_ambigua_setea_timestamp_sin_cambiar_contador(v):
    _ins(v.conn, 6, count=0, ult_verif=None)
    v.conn.commit()
    ts = NOW.isoformat()
    v._aplicar(6, "computrabajo", "2026-08-01", 0, None, "ambigua", {"caso": "x"}, ts, dry=False)
    row = v.conn.execute(
        "SELECT verificaciones_caida_count, fecha_ultima_verificacion FROM ofertas WHERE id_oferta=6"
    ).fetchone()
    assert row[0] == 0                      # contador intacto
    assert row[1] == ts                     # timestamp seteado → activa cooldown
    # y quedó registrada en verificaciones_baja (histórico para medir flips)
    n = v.conn.execute(
        "SELECT COUNT(*) FROM verificaciones_baja WHERE id_oferta=6 AND resultado='ambigua'"
    ).fetchone()[0]
    assert n == 1


def test_aplicar_ambigua_dry_no_escribe(v):
    _ins(v.conn, 7, count=0, ult_verif=None)
    v.conn.commit()
    v._aplicar(7, "computrabajo", "2026-08-01", 0, None, "ambigua", {}, NOW.isoformat(), dry=True)
    row = v.conn.execute(
        "SELECT fecha_ultima_verificacion FROM ofertas WHERE id_oferta=7").fetchone()
    assert row[0] is None                   # dry-run no escribe
    n = v.conn.execute(
        "SELECT COUNT(*) FROM verificaciones_baja WHERE id_oferta=7").fetchone()[0]
    assert n == 0


def test_ambigua_en_cooldown_desaparece_de_la_cola_tras_aplicar(v):
    # integración: fresca entra a la cola → _aplicar ambigua → ya no vuelve a la cola
    _ins(v.conn, 8, count=0, ult_verif=None)
    v.conn.commit()
    assert 8 in _ids(v.cola("computrabajo", 100))
    v._aplicar(8, "computrabajo", "2026-08-01", 0, None, "ambigua", {}, NOW.isoformat(), dry=False)
    v.conn.commit()
    assert 8 not in _ids(v.cola("computrabajo", 100))
