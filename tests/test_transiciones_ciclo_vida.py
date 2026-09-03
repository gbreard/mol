"""
Tests del motor de transiciones (Fase 3, modo sombra).
Valida: umbral por portal, reset al reaparecer, PE 2-ausencias-completas,
Indeed no-inferido, y que el legacy estado_oferta NUNCA se toca.
"""
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import database.transiciones_ciclo_vida as tcv  # noqa: E402


def hoy_menos(d):
    return (datetime.now() - timedelta(days=d)).isoformat()


def build_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE ofertas (
            id_oferta INTEGER PRIMARY KEY, portal TEXT, estado_oferta TEXT,
            estado_ciclo TEXT, fecha_ultimo_visto TEXT,
            verificaciones_caida_count INTEGER DEFAULT 0,
            fecha_primera_verificacion_caida TEXT,
            fecha_baja_estimada TEXT, fecha_baja_intervalo_desde TEXT,
            fecha_baja_intervalo_hasta TEXT, fecha_baja_incertidumbre_dias INTEGER);
        CREATE TABLE transiciones_ciclo_vida (
            id INTEGER PRIMARY KEY AUTOINCREMENT, id_oferta INTEGER, portal TEXT,
            estado_desde TEXT, estado_hacia TEXT, motivo TEXT, fecha TEXT);
        CREATE TABLE corridas_scraping (
            id INTEGER PRIMARY KEY AUTOINCREMENT, portal TEXT, fecha TEXT,
            completa INTEGER, n_vistas INTEGER, n_esperadas INTEGER, nota TEXT);
        CREATE TABLE divergencia_ciclo_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT,
            n_legacy_baja_ciclo_activa INTEGER, n_legacy_baja_total INTEGER, detalle_json TEXT);
    """)
    c.commit()
    return c


@pytest.fixture
def motor(tmp_path, monkeypatch):
    db = str(tmp_path / "t.db")
    build_db(db).close()
    monkeypatch.setattr(tcv, "STATE", tmp_path / "state.json")  # aislar estado
    m = tcv.TransicionesCicloVida(db)
    m.connect()
    yield m, db
    m.close()


def ins(db, **k):
    cols = ",".join(k); ph = ",".join("?" * len(k))
    c = sqlite3.connect(db); c.execute(f"INSERT INTO ofertas ({cols}) VALUES ({ph})", tuple(k.values()))
    c.commit(); c.close()


def estado(db, ido):
    c = sqlite3.connect(db)
    r = c.execute("SELECT estado_ciclo, estado_oferta, verificaciones_caida_count FROM ofertas WHERE id_oferta=?", (ido,)).fetchone()
    c.close(); return r


def test_activa_a_presunta_por_umbral(motor):
    m, db = motor
    # bumeran umbral 42d: 50d sin ver → presunta; 10d → sigue activa
    ins(db, id_oferta=1, portal="bumeran", estado_oferta="activa", estado_ciclo="activa", fecha_ultimo_visto=hoy_menos(50))
    ins(db, id_oferta=2, portal="bumeran", estado_oferta="activa", estado_ciclo="activa", fecha_ultimo_visto=hoy_menos(10))
    m.ejecutar(dry_run=False)
    assert estado(db, 1)[0] == "presunta_baja"
    assert estado(db, 2)[0] == "activa"


def test_reset_al_reaparecer(motor):
    m, db = motor
    # presunta_baja con verificaciones y visto HOY → vuelve a activa + reset
    ins(db, id_oferta=3, portal="zonajobs", estado_oferta="baja", estado_ciclo="presunta_baja",
        fecha_ultimo_visto=hoy_menos(0), verificaciones_caida_count=1, fecha_primera_verificacion_caida=hoy_menos(1))
    m.ejecutar(dry_run=False)
    ec, eo, vc = estado(db, 3)
    assert ec == "activa" and vc == 0
    assert eo == "baja"  # legacy NO se toca
    # transición registrada (alimenta métrica de resurrección)
    c = sqlite3.connect(db)
    t = c.execute("SELECT estado_desde,estado_hacia,motivo FROM transiciones_ciclo_vida WHERE id_oferta=3").fetchone()
    c.close()
    assert t == ("presunta_baja", "activa", "scraping_reaparece")


def test_pe_dos_ausencias_completas(motor):
    m, db = motor
    # oferta PE vista hace 10d; luego 2 corridas COMPLETAS posteriores (ausente en ambas) → confirmada
    ins(db, id_oferta=4, portal="portalempleo", estado_oferta="baja", estado_ciclo="presunta_baja",
        fecha_ultimo_visto=hoy_menos(10))
    c = sqlite3.connect(db)
    for d, comp in [(5, 1), (2, 1)]:  # 2 corridas completas después del último visto (10d)
        c.execute("INSERT INTO corridas_scraping (portal,fecha,completa) VALUES ('portalempleo',?,?)", (hoy_menos(d), comp))
    c.commit(); c.close()
    m.ejecutar(dry_run=False)
    assert estado(db, 4)[0] == "baja_confirmada"


def test_pe_no_confirma_sin_dos_completas(motor):
    m, db = motor
    ins(db, id_oferta=5, portal="portalempleo", estado_oferta="baja", estado_ciclo="presunta_baja",
        fecha_ultimo_visto=hoy_menos(10))
    c = sqlite3.connect(db)
    c.execute("INSERT INTO corridas_scraping (portal,fecha,completa) VALUES ('portalempleo',?,1)", (hoy_menos(2),))
    # una completa + una INCOMPLETA no alcanzan
    c.execute("INSERT INTO corridas_scraping (portal,fecha,completa) VALUES ('portalempleo',?,0)", (hoy_menos(5),))
    c.commit(); c.close()
    m.ejecutar(dry_run=False)
    assert estado(db, 5)[0] == "presunta_baja"  # NO confirmada


def test_indeed_no_se_infiere(motor):
    m, db = motor
    # indeed no entra a Navent+CT ni a PE: su estado_ciclo no cambia por umbral
    ins(db, id_oferta=6, portal="indeed", estado_oferta="activa", estado_ciclo="activa", fecha_ultimo_visto=hoy_menos(90))
    m.ejecutar(dry_run=False)
    assert estado(db, 6)[0] == "activa"  # sin inferencia (§11.8)


def test_legacy_nunca_se_toca(motor):
    m, db = motor
    ins(db, id_oferta=7, portal="bumeran", estado_oferta="baja", estado_ciclo="activa", fecha_ultimo_visto=hoy_menos(50))
    m.ejecutar(dry_run=False)
    ec, eo, _ = estado(db, 7)
    assert ec == "presunta_baja"  # ciclo transiciona
    assert eo == "baja"           # legacy intacto
    # divergencia registrada
    c = sqlite3.connect(db)
    n = c.execute("SELECT COUNT(*) FROM divergencia_ciclo_log").fetchone()[0]
    c.close()
    assert n == 1
