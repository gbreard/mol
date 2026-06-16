"""
Tests del acta de corrida — SPEC S1C-F0.3 (Paso 2).

Verifican el punto de control: el acta se escribe correcta en una corrida real
(inicio/fin/alcance/resultado) y el barrido distingue corrida en curso de muerta.

No requiere Ollama ni toca la BD de producción: usa una BD temporal y mockea
los pasos pesados del pipeline (NLP, matching, validación, export, sync).
"""

import os
import sys
import sqlite3
from pathlib import Path

import pytest

import scripts.observabilidad as obs

# run_validated_pipeline y export_validation_excel reenvuelven sys.stdout en un
# TextIOWrapper al importarse (fix de encoding para subprocess Windows). Ese rewrap,
# si toca el stream de captura de pytest, lo cierra y rompe la sesión. Importamos
# ambos con stdout redirigido a devnull para que el rewrap envuelva devnull (no la
# captura de pytest), y restauramos después.
_orig_stdout, _orig_stderr = sys.stdout, sys.stderr
_devnull = open(os.devnull, "w")
sys.stdout = sys.stderr = _devnull
try:
    import scripts.run_validated_pipeline as rvp  # noqa: E402
    import scripts.exports.export_validation_excel  # noqa: E402,F401
finally:
    sys.stdout, sys.stderr = _orig_stdout, _orig_stderr

MIGRATION = Path(__file__).resolve().parent.parent / "database" / "migrations" / "025_pipeline_observabilidad.sql"


@pytest.fixture(autouse=True)
def _restore_streams():
    """Varios módulos del pipeline reenvuelven sys.stdout al importarse; restauramos
    los streams de pytest tras cada test para no romper su captura en el teardown."""
    so, se = sys.stdout, sys.stderr
    yield
    sys.stdout, sys.stderr = so, se


@pytest.fixture
def db_tmp(tmp_path, monkeypatch):
    """BD temporal con solo las tablas de observabilidad; redirige el helper a ella."""
    db = tmp_path / "obs_test.db"
    con = sqlite3.connect(str(db))
    con.executescript(MIGRATION.read_text())
    con.commit()
    con.close()
    monkeypatch.setattr(obs, "DB_PATH", db)
    return db


def _actas(db):
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM pipeline_run_actas")]
    con.close()
    return rows


# ── Unidad: ciclo de vida del acta ───────────────────────────────────────────

def test_crear_y_cerrar_acta_ok(db_tmp):
    acta_id = obs.crear_acta(invocador="terminal", args='{"limit": 5}', alcance_entrada=5)
    abierta = _actas(db_tmp)[0]
    assert abierta["finished_at"] is None
    assert abierta["resultado"] is None       # en curso
    assert abierta["alcance_entrada"] == 5
    assert abierta["pid"] == os.getpid()

    obs.cerrar_acta(acta_id, resultado="ok", alcance_procesado=4, matching_run_id="run_x")
    cerrada = _actas(db_tmp)[0]
    assert cerrada["finished_at"] is not None
    assert cerrada["resultado"] == "ok"
    assert cerrada["alcance_procesado"] == 4
    assert cerrada["matching_run_id"] == "run_x"


# ── Unidad: barrido distingue en curso vs muerta (mecanismo de `incompleta`) ──

def test_barrido_marca_muerta_y_respeta_viva(db_tmp):
    con = sqlite3.connect(str(db_tmp))
    host = obs._host()
    # Acta MUERTA: pid inexistente, mismo host
    con.execute(
        "INSERT INTO pipeline_run_actas (acta_id, started_at, pid, host) VALUES (?,?,?,?)",
        ("acta_muerta", "2026-06-16T10:00:00", 999999, host),
    )
    # Acta EN CURSO: pid de este proceso (vivo), started_at reciente, mismo host
    con.execute(
        "INSERT INTO pipeline_run_actas (acta_id, started_at, pid, host) VALUES (?,?,?,?)",
        ("acta_viva", obs._now(), os.getpid(), host),
    )
    con.commit()
    con.close()

    barridas = obs.barrer_actas_huerfanas()

    assert barridas == ["acta_muerta"]
    estados = {a["acta_id"]: a for a in _actas(db_tmp)}
    assert estados["acta_muerta"]["resultado"] == "incompleta"
    assert estados["acta_muerta"]["finished_at"] is not None
    assert estados["acta_viva"]["resultado"] is None        # viva → se respeta
    assert estados["acta_viva"]["finished_at"] is None


def test_barrido_timeout_respaldo(db_tmp):
    """Pid vivo pero corrida más vieja que el timeout → incompleta (respaldo)."""
    con = sqlite3.connect(str(db_tmp))
    con.execute(
        "INSERT INTO pipeline_run_actas (acta_id, started_at, pid, host) VALUES (?,?,?,?)",
        ("acta_vieja", "2020-01-01T00:00:00", os.getpid(), obs._host()),
    )
    con.commit()
    con.close()

    assert obs.barrer_actas_huerfanas() == ["acta_vieja"]
    assert _actas(db_tmp)[0]["resultado"] == "incompleta"


# ── Integración: run_full_pipeline REAL escribe el acta (T1) ──────────────────

class _FakeNLPValidator:
    def __init__(self, *a, **k):
        pass

    def validar_desde_bd(self, *a, **k):
        return {"total": 0, "gate_pass_count": 0, "gate_block_count": 0}


def _patch_pipeline_pesado(monkeypatch, nlp_raise=False):
    """Mockea los colaboradores pesados; deja intacta la lógica de acta."""
    monkeypatch.setattr(rvp, "NLPValidator", _FakeNLPValidator)
    monkeypatch.setattr(rvp, "validar_ofertas_desde_bd",
                        lambda *a, **k: {"total": 0, "sin_errores": 0, "con_errores": 0})
    monkeypatch.setattr(rvp, "sync_learnings_yaml", lambda *a, **k: None)
    monkeypatch.setattr("scripts.exports.export_validation_excel.export_validation",
                        lambda *a, **k: "/tmp/fake.xlsx")
    if nlp_raise:
        monkeypatch.setattr(rvp, "get_ids_without_nlp", lambda *a, **k: ["1"])

        def _boom(*a, **k):
            raise ConnectionError("Connection refused: 172.17.0.1:11434")

        monkeypatch.setattr(rvp, "run_nlp_for_ids", _boom)


def test_run_full_pipeline_escribe_acta_ok(db_tmp, monkeypatch):
    _patch_pipeline_pesado(monkeypatch)

    rvp.run_full_pipeline(ids=["1", "2"], skip_nlp=True, skip_matching=True, verbose=False)

    actas = _actas(db_tmp)
    assert len(actas) == 1
    acta = actas[0]
    assert acta["started_at"] is not None
    assert acta["finished_at"] is not None
    assert acta["resultado"] == "ok"
    assert acta["alcance_entrada"] == 2
    assert acta["invocador"] == "terminal"


def test_run_full_pipeline_acta_fallida_por_ollama(db_tmp, monkeypatch):
    _patch_pipeline_pesado(monkeypatch, nlp_raise=True)

    rvp.run_full_pipeline(ids=None, limit=1, skip_nlp=False, skip_matching=True,
                          only_pending=False, verbose=False)

    import json
    acta = _actas(db_tmp)[0]
    assert acta["resultado"] == "fallida"
    fallos = json.loads(acta["fallos"])
    assert any(f["tipo"] == "ollama_down" for f in fallos)
