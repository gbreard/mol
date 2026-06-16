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
    """BD temporal con solo las tablas de observabilidad; redirige el helper a ella
    y el jsonl de alertas a tmp (para no contaminar logs/ reales)."""
    db = tmp_path / "obs_test.db"
    con = sqlite3.connect(str(db))
    con.executescript(MIGRATION.read_text())
    con.commit()
    con.close()
    monkeypatch.setattr(obs, "DB_PATH", db)
    monkeypatch.setattr(obs, "ALERTAS_JSONL", tmp_path / "pipeline_alertas.jsonl")
    return db


def _actas(db):
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM pipeline_run_actas")]
    con.close()
    return rows


def _alertas_tabla(db):
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM pipeline_alertas")]
    con.close()
    return rows


def _alertas_jsonl():
    import json
    p = obs.ALERTAS_JSONL
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


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


# ── Paso 3: alertas en tabla Y jsonl (criterio binario por tipo de fallo) ─────

def _aparece_en_ambos(db, tipo):
    en_tabla = any(a["tipo"] == tipo for a in _alertas_tabla(db))
    en_jsonl = any(a["tipo"] == tipo for a in _alertas_jsonl())
    return en_tabla and en_jsonl


def test_emitir_alerta_persiste_en_tabla_y_jsonl(db_tmp):
    obs.emitir_alerta("error", "ollama_down", "Conexión rechazada 172.17.0.1:11434",
                      acta_id="acta_x", contexto={"ids_count": 5})
    # Tabla
    fila = _alertas_tabla(db_tmp)[0]
    assert fila["tipo"] == "ollama_down"
    assert fila["severidad"] == "error"
    assert fila["acta_id"] == "acta_x"
    assert '"ids_count": 5' in fila["contexto"]
    # JSONL
    linea = _alertas_jsonl()[0]
    assert linea["tipo"] == "ollama_down"
    assert linea["contexto"]["ids_count"] == 5


def test_barrido_emite_alerta_corrida_incompleta(db_tmp):
    con = sqlite3.connect(str(db_tmp))
    con.execute(
        "INSERT INTO pipeline_run_actas (acta_id, started_at, pid, host) VALUES (?,?,?,?)",
        ("acta_zombie", "2026-06-16T09:00:00", 999999, obs._host()),
    )
    con.commit()
    con.close()

    obs.barrer_actas_huerfanas()

    assert _aparece_en_ambos(db_tmp, "corrida_incompleta")
    alerta = [a for a in _alertas_tabla(db_tmp) if a["tipo"] == "corrida_incompleta"][0]
    assert alerta["acta_id"] == "acta_zombie"
    assert alerta["severidad"] == "error"


def test_run_pipeline_fallida_emite_alerta_ollama_en_ambos(db_tmp, monkeypatch):
    _patch_pipeline_pesado(monkeypatch, nlp_raise=True)

    rvp.run_full_pipeline(ids=None, limit=1, skip_nlp=False, skip_matching=True,
                          only_pending=False, verbose=False)

    assert _aparece_en_ambos(db_tmp, "ollama_down")


def test_poller_lee_acta_y_alertas_para_espejo(db_tmp):
    """El lector del poller arma el espejo (última acta + alertas) desde el SQLite local."""
    import scripts.pipeline_command_poller as poller

    acta_id = obs.crear_acta(invocador="poller", args='{"limit": 3}', alcance_entrada=3)
    obs.cerrar_acta(acta_id, resultado="fallida", alcance_procesado=2,
                    fallos=[{"severidad": "error", "tipo": "ollama_down", "mensaje": "x"}])
    obs.emitir_alerta("error", "ollama_down", "Conexión rechazada", acta_id=acta_id,
                      contexto={"ids_count": 3})

    con = sqlite3.connect(str(db_tmp))
    ultima_acta, alertas = poller._leer_observabilidad_local(con)
    con.close()

    assert ultima_acta["acta_id"] == acta_id
    assert ultima_acta["resultado"] == "fallida"
    assert ultima_acta["invocador"] == "poller"
    # fallos llega deserializado (lista), listo para subir como JSONB
    assert isinstance(ultima_acta["fallos"], list)
    assert ultima_acta["fallos"][0]["tipo"] == "ollama_down"
    assert any(a["tipo"] == "ollama_down" for a in alertas)
    assert isinstance(alertas[0]["contexto"], dict)


def test_poller_lee_observabilidad_sin_tablas_no_rompe(tmp_path):
    """Si las tablas de observabilidad no existen (migración 025 no aplicada), devuelve (None, [])."""
    import scripts.pipeline_command_poller as poller

    db = tmp_path / "vacia.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE ofertas (id INTEGER)")  # BD sin tablas de observabilidad
    con.commit()
    ultima_acta, alertas = poller._leer_observabilidad_local(con)
    con.close()

    assert ultima_acta is None
    assert alertas == []


def test_emitir_alerta_nunca_rompe(monkeypatch, tmp_path):
    """Aunque tabla y jsonl fallen, emitir_alerta no lanza (no rompe el pipeline)."""
    monkeypatch.setattr(obs, "DB_PATH", tmp_path / "no_existe" / "x.db")  # _conn falla
    monkeypatch.setattr(obs, "ALERTAS_JSONL", tmp_path / "ro" / "a.jsonl")
    # crear dir read-only para forzar fallo de escritura del jsonl
    ro = tmp_path / "ro"
    ro.mkdir()
    os.chmod(ro, 0o500)
    try:
        reg = obs.emitir_alerta("error", "nlp_fallo", "x")  # no debe lanzar
        assert reg["tipo"] == "nlp_fallo"
    finally:
        os.chmod(ro, 0o700)
