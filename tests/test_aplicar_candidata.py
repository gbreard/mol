"""
Tests de aplicar_candidata (FRENTE B, P4) — escritura git-first del puente.

Corren sobre una COPIA temporal del diccionario (nunca el real), con commit=False.
Cubren: rechazo ruidoso sin esco_code, colision longest-match, esquema post-G3,
editor viejo inalcanzable, squash por sesion, idempotencia.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from puente import aplicar_candidata as ac  # noqa: E402

DICT_REAL = ROOT / "config" / "sinonimos_argentinos_esco.json"


@pytest.fixture(scope="module")
def code2occ():
    return ac.cargar_catalogo()


@pytest.fixture
def dict_tmp(tmp_path):
    """Copia temporal del diccionario real."""
    p = tmp_path / "sinonimos.json"
    shutil.copy(DICT_REAL, p)
    return p


def _cand(denom, esco, **kw):
    base = {"denominacion": denom, "esco_code": esco,
            "linaje": {"confirmado_por": "test", "fecha": "2026-07-03",
                       "id_oferta": "999", "correccion_fuente": "sintetica"}}
    base.update(kw)
    return base


def _count(dict_path):
    return len([k for k in json.loads(dict_path.read_text(encoding="utf-8"))["ocupaciones_titulo"]
                if not k.startswith("_")])


# 6 — rechazo ruidoso: sin esco_code resoluble, diccionario intacto
def test_rechazo_ruidoso_sin_esco_code(dict_tmp, code2occ):
    n0 = _count(dict_tmp)
    rep = ac.aplicar([_cand("puesto inventado xyz", "9999.99")], "s-test",
                     commit=False, dict_path=dict_tmp, mirror_path=None,
                     code2occ=code2occ, verbose=False)
    assert not rep["aplicadas"]
    assert rep["rechazadas"] and "NO resuelve" in rep["rechazadas"][0]["motivo"]
    assert _count(dict_tmp) == n0  # intacto


def test_rechazo_sin_esco_code_vacio(dict_tmp, code2occ):
    rep = ac.aplicar([_cand("algo", "")], "s", commit=False, dict_path=dict_tmp,
                     mirror_path=None, code2occ=code2occ, verbose=False)
    assert not rep["aplicadas"]
    assert "sin esco_code" in rep["rechazadas"][0]["motivo"]


# 7 — colision longest-match: no pisa en silencio
# (fixture actualizado [FRENTE H P4]: 'ejecutivo comercial' se retiro del dict con el
#  piloto — la base pasa a 'intendente de obra' -> 3123.1.1, entrada estable de G3)
def test_colision_longest_match(dict_tmp, code2occ):
    # 'intendente de obra' existe -> 3123.1.1. Una candidata superstring con OTRO
    # codigo debe ser rechazada (sombrearia la existente).
    rep = ac.aplicar([_cand("intendente de obra vial", "1323.1")], "s",
                     commit=False, dict_path=dict_tmp, mirror_path=None,
                     code2occ=code2occ, verbose=False)
    assert not rep["aplicadas"]
    assert "colision" in rep["rechazadas"][0]["motivo"].lower()


def test_colision_mismo_codigo_no_bloquea(dict_tmp, code2occ):
    # substring con MISMO codigo no es colision (no hay sombreado peligroso)
    rep = ac.aplicar([_cand("intendente de obra civil", "3123.1.1")], "s",
                     commit=False, dict_path=dict_tmp, mirror_path=None,
                     code2occ=code2occ, verbose=False)
    assert rep["aplicadas"], rep


# 8 — esquema post-G3 completo
def test_esquema_post_g3(dict_tmp, code2occ):
    rep = ac.aplicar([_cand("denominacion nueva de prueba", "5414.1",
                            variantes=["denom alt"], notas="nota de prueba")],
                     "s", commit=False, dict_path=dict_tmp, mirror_path=None,
                     code2occ=code2occ, verbose=False)
    assert rep["aplicadas"]
    dic = json.loads(dict_tmp.read_text(encoding="utf-8"))["ocupaciones_titulo"]
    e = dic["denominacion nueva de prueba"]
    assert e["esco_code"] == "5414.1"
    assert e["isco_primario"] == "5414"
    assert e["esco_label"] and e["esco_uri"]
    assert "denominacion nueva de prueba" in e["variantes"] and "denom alt" in e["variantes"]
    assert e["_linaje"]["confirmado_por"] == "test"
    assert e["_linaje"]["id_oferta"] == "999"
    assert e["nota"] == "nota de prueba"


# 9 — el editor viejo (que stripea esco_code) NO es alcanzable desde este camino
def test_editor_viejo_inalcanzable():
    """El camino de escritura es filesystem+git; NO pasa por el endpoint config-editor
    (que stripea esco_code) ni por Supabase config_overrides. Se verifica a nivel de
    CODIGO (no de la prosa del docstring que explica que estan fuera del circuito)."""
    src = (ROOT / "scripts" / "puente" / "aplicar_candidata.py").read_text(encoding="utf-8")
    # separar codigo de docstrings/comentarios
    import ast
    tree = ast.parse(src)
    # no importa clientes HTTP ni supabase (el write es local)
    imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
    imports += [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
    for prohibido in ("requests", "supabase", "httpx"):
        assert not any(prohibido in (i or "") for i in imports), f"no debe importar {prohibido}"
    # no hay llamada al endpoint del editor ni a create_client
    assert "config-editor" not in src
    assert "create_client" not in src
    # el write es via write_text al diccionario local
    assert "write_text" in src


def test_esco_code_nunca_stripeado(dict_tmp, code2occ):
    """El editor viejo stripea esco_code; aplicar_candidata SIEMPRE lo escribe."""
    ac.aplicar([_cand("otra denom prueba", "5414.1")], "s", commit=False,
               dict_path=dict_tmp, mirror_path=None, code2occ=code2occ, verbose=False)
    e = json.loads(dict_tmp.read_text(encoding="utf-8"))["ocupaciones_titulo"]["otra denom prueba"]
    assert "esco_code" in e and e["esco_code"] == "5414.1"


# 10 — squash: N candidatas en una sesion -> UN commit; linaje sobrevive
def test_squash_un_commit(dict_tmp, code2occ, monkeypatch):
    commits = []

    def fake_run(cmd, **kw):
        if cmd[:2] == ["git", "commit"] or (len(cmd) > 1 and cmd[1] == "commit"):
            commits.append(cmd)
        class R:  # noqa
            returncode = 0
        return R()
    monkeypatch.setattr(ac.subprocess, "run", fake_run)

    cands = [_cand("denom sesion uno", "5414.1"), _cand("denom sesion dos", "4226.1")]
    rep = ac.aplicar(cands, "sesion-squash", commit=True, dict_path=dict_tmp,
                     mirror_path=None, code2occ=code2occ, verbose=False)
    assert len(rep["aplicadas"]) == 2
    assert len(commits) == 1, f"esperaba 1 commit (squash), hubo {len(commits)}"
    # linaje por entrada sobrevive en el JSON
    dic = json.loads(dict_tmp.read_text(encoding="utf-8"))["ocupaciones_titulo"]
    assert dic["denom sesion uno"]["_linaje"]["id_oferta"] == "999"
    assert dic["denom sesion dos"]["_linaje"]["id_oferta"] == "999"


# 11 — idempotencia: re-aplicar la misma candidata ya cargada -> no duplica
def test_idempotencia(dict_tmp, code2occ):
    c = _cand("denom idempotente", "5414.1")
    ac.aplicar([c], "s1", commit=False, dict_path=dict_tmp, mirror_path=None,
               code2occ=code2occ, verbose=False)
    n1 = _count(dict_tmp)
    rep = ac.aplicar([c], "s2", commit=False, dict_path=dict_tmp, mirror_path=None,
                     code2occ=code2occ, verbose=False)
    assert not rep["aplicadas"]
    assert rep["noop"] and "ya existe" in rep["noop"][0]["motivo"]
    assert _count(dict_tmp) == n1  # no duplica


def test_idempotencia_conflicto_otro_codigo(dict_tmp, code2occ):
    ac.aplicar([_cand("denom conflictiva", "5414.1")], "s1", commit=False,
               dict_path=dict_tmp, mirror_path=None, code2occ=code2occ, verbose=False)
    rep = ac.aplicar([_cand("denom conflictiva", "4226.1")], "s2", commit=False,
                     dict_path=dict_tmp, mirror_path=None, code2occ=code2occ, verbose=False)
    assert not rep["aplicadas"]
    assert "conflicto" in rep["rechazadas"][0]["motivo"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
