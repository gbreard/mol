"""Tests del verificador de bajas (Fase 4). searchV2 mockeado; sin red."""
import sqlite3, sys
from datetime import datetime, timedelta
from pathlib import Path
import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import database.verificador_bajas as vb  # noqa: E402


def build(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE ofertas (id_oferta INTEGER PRIMARY KEY, portal TEXT, titulo TEXT,
            url_oferta TEXT, estado_oferta TEXT, estado_ciclo TEXT, fecha_ultimo_visto TEXT,
            verificaciones_caida_count INTEGER DEFAULT 0, fecha_primera_verificacion_caida TEXT,
            fecha_ultima_verificacion TEXT, fecha_baja_estimada TEXT, fecha_baja_intervalo_desde TEXT,
            fecha_baja_intervalo_hasta TEXT, fecha_baja_incertidumbre_dias INTEGER);
        CREATE TABLE verificaciones_baja (id INTEGER PRIMARY KEY AUTOINCREMENT, id_oferta INTEGER,
            portal TEXT, fecha TEXT, via TEXT, resultado TEXT, senal_cruda TEXT);
        CREATE TABLE transiciones_ciclo_vida (id INTEGER PRIMARY KEY AUTOINCREMENT, id_oferta INTEGER,
            portal TEXT, estado_desde TEXT, estado_hacia TEXT, motivo TEXT, fecha TEXT);
    """)
    c.commit(); c.close()


def hoy_menos_h(h):
    return (datetime.now() - timedelta(hours=h)).isoformat()


@pytest.fixture
def v(tmp_path, monkeypatch):
    db = str(tmp_path / "t.db"); build(db)
    monkeypatch.setattr(vb, "LOCK_LOCAL", tmp_path / "nolock")  # sin lock
    ver = vb.VerificadorBajas(db); ver.connect()
    yield ver, db
    ver.close()


def ins(db, **k):
    cols = ",".join(k); ph = ",".join("?" * len(k))
    c = sqlite3.connect(db); c.execute(f"INSERT INTO ofertas ({cols}) VALUES ({ph})", tuple(k.values())); c.commit(); c.close()


def get(db, ido):
    c = sqlite3.connect(db)
    r = c.execute("SELECT estado_ciclo, estado_oferta, verificaciones_caida_count FROM ofertas WHERE id_oferta=?", (ido,)).fetchone()
    c.close(); return r


# ---- clasificación searchV2 ----
def test_navent_viva_caida_ambigua(v, monkeypatch):
    ver, _ = v
    def fake(portal, q):  # (data, status)
        if q == "presente":  return {"content": [{"id": 99}], "total": 1}, 200
        if q == "cero":      return {"content": [], "total": 0}, 200
        if q == "menos":     return {"content": [{"id": 1}, {"id": 2}], "total": 2}, 200
        return {"content": [{"id": k} for k in range(1000, 1100)], "total": 500}, 200  # tope, sin el id 99
    monkeypatch.setattr(ver, "_searchv2", fake)
    assert ver.clasificar_navent("bumeran", "presente", 99)[0] == "viva"
    assert ver.clasificar_navent("bumeran", "cero", 99)[0] == "caida"
    assert ver.clasificar_navent("bumeran", "menos", 99)[0] == "caida"
    assert ver.clasificar_navent("bumeran", "tope", 99)[0] == "ambigua"  # tope y sin id, reintento igual tope


# ---- cola: gap 72h respetado ----
def test_cola_respeta_gap(v):
    ver, db = v
    ins(db, id_oferta=1, portal="bumeran", estado_ciclo="presunta_baja", verificaciones_caida_count=0, fecha_ultimo_visto="2026-07-01")
    ins(db, id_oferta=2, portal="bumeran", estado_ciclo="presunta_baja", verificaciones_caida_count=1,
        fecha_ultima_verificacion=hoy_menos_h(80), fecha_ultimo_visto="2026-07-02")   # gap cumplido
    ins(db, id_oferta=3, portal="bumeran", estado_ciclo="presunta_baja", verificaciones_caida_count=1,
        fecha_ultima_verificacion=hoy_menos_h(10), fecha_ultimo_visto="2026-07-03")   # gap NO cumplido
    ids = {r[0] for r in ver.cola("bumeran", 100)}
    assert ids == {1, 2}   # 3 excluida por gap


# ---- 2 caídas → confirmada; 1 caída no ----
def test_dos_caidas_confirma(v):
    ver, db = v
    ins(db, id_oferta=1, portal="bumeran", estado_oferta="baja", estado_ciclo="presunta_baja",
        fecha_ultimo_visto="2026-07-01", verificaciones_caida_count=0)
    ts = datetime.now().isoformat()
    ver._aplicar(1, "bumeran", "2026-07-01", 0, None, "caida", {"caso": "cero"}, ts, dry=False)
    ver.conn.commit()
    assert get(db, 1)[0] == "presunta_baja" and get(db, 1)[2] == 1   # 1ª caída: cuenta, no confirma
    ver._aplicar(1, "bumeran", "2026-07-01", 1, "2026-08-01", "caida", {"caso": "cero"}, ts, dry=False)
    ver.conn.commit()
    ec, eo, cnt = get(db, 1)
    assert ec == "baja_confirmada" and cnt == 2
    assert eo == "baja"   # legacy intacto
    c = sqlite3.connect(db)
    assert c.execute("SELECT fecha_baja_intervalo_desde,fecha_baja_intervalo_hasta FROM ofertas WHERE id_oferta=1").fetchone() == ("2026-07-01", "2026-08-01")
    c.close()


# ---- resurrección: confirmada verificada viva → activa + transición ----
def test_viva_revive_y_loguea(v):
    ver, db = v
    ins(db, id_oferta=1, portal="zonajobs", estado_oferta="baja", estado_ciclo="presunta_baja",
        verificaciones_caida_count=1, fecha_ultimo_visto="2026-07-01")
    ver._aplicar(1, "zonajobs", "2026-07-01", 1, None, "viva", {"n_resultados": 1}, datetime.now().isoformat(), dry=False)
    ver.conn.commit()
    ec, eo, cnt = get(db, 1)
    assert ec == "activa" and cnt == 0 and eo == "baja"
    c = sqlite3.connect(db)
    t = c.execute("SELECT estado_desde,estado_hacia,motivo FROM transiciones_ciclo_vida WHERE id_oferta=1").fetchone()
    v_ = c.execute("SELECT resultado FROM verificaciones_baja WHERE id_oferta=1").fetchone()[0]
    c.close()
    assert t == ("presunta_baja", "activa", "verificacion_viva") and v_ == "viva"


# ---- ambigua no cambia contadores ----
def test_ambigua_no_cuenta(v):
    ver, db = v
    ins(db, id_oferta=1, portal="bumeran", estado_oferta="baja", estado_ciclo="presunta_baja",
        verificaciones_caida_count=0, fecha_ultimo_visto="2026-07-01")
    ver._aplicar(1, "bumeran", "2026-07-01", 0, None, "ambigua", {"caso": "tope"}, datetime.now().isoformat(), dry=False)
    assert get(db, 1)[0] == "presunta_baja" and get(db, 1)[2] == 0
