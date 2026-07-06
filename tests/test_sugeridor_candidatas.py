"""
Tests del sugeridor de candidatas del puente (FRENTE B, P2).

Cubre las funciones puras (sin tocar Supabase): filtro de entrada, resolucion
esco_uuid->esco_code con guarda, estado de bandeja, ruido. La corrida end-to-end
contra Supabase se valida en el punto de control P2 (no en test unitario).
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from puente import sugeridor_candidatas as sug  # noqa: E402
from puente.clasificador import Clasificador  # noqa: E402


@pytest.fixture(scope="module")
def uri2occ():
    return sug.load_catalog()


# ---- filtro de entrada ----
def test_filtro_entra_por_ocupacion_corregida_no_por_flag():
    # entra: tiene ocupacion_corregida, aunque el flag sea 'revisar'
    vc_ok = {"ocupacion_corregida": {"esco_uuid": "x", "isco_code": "5414"}}
    assert sug.es_correccion_ocupacion(vc_ok) is True
    # NO entra: flag 'error' pero SIN ocupacion_corregida (solo nota/skills)
    vc_no = {"validacion_humana": "error", "nota": "mal extraida", "skills_editadas": []}
    assert sug.es_correccion_ocupacion(vc_no) is False
    # NO entra: vacio / no-dict
    assert sug.es_correccion_ocupacion(None) is False
    assert sug.es_correccion_ocupacion("basura") is False


# ---- resolucion contra catalogo (patron G3, nunca inventa) ----
def test_resuelve_uuid_valido(uri2occ):
    # tomar un uuid real del catalogo
    any_uri = next(iter(uri2occ))
    occ_ref = uri2occ[any_uri]
    uuid = any_uri.rsplit("/", 1)[-1]
    occ, motivo = sug.resolver({"esco_uuid": uuid}, uri2occ)
    assert occ is not None
    assert occ["esco_code"] == occ_ref["esco_code"]


def test_uuid_irresoluble_es_pendiente(uri2occ):
    occ, motivo = sug.resolver({"esco_uuid": "00000000-dead-beef-0000-000000000000"}, uri2occ)
    assert occ is None
    assert "no resuelve" in motivo


def test_sin_uuid_es_pendiente(uri2occ):
    occ, motivo = sug.resolver({"esco_label": "algo"}, uri2occ)
    assert occ is None
    assert "sin esco_uuid" in motivo


def test_isco_picker_divergente_es_aviso(uri2occ):
    # uuid valido pero el picker declara un isco distinto -> resuelve con aviso (no descarta)
    any_uri = next(iter(uri2occ))
    uuid = any_uri.rsplit("/", 1)[-1]
    occ, motivo = sug.resolver({"esco_uuid": uuid, "isco_code": "9999"}, uri2occ)
    assert occ is not None
    assert motivo and "aviso" in motivo


# ---- estado de bandeja ----
def test_estado_bandeja():
    assert sug.estado_bandeja("VOCABULARIO", None) == "AUTO"
    assert sug.estado_bandeja("CONDICIONAL", "VOCABULARIO") == "A-CONFIRMAR"
    assert sug.estado_bandeja("CONDICIONAL", "CONDICIONAL") == "CONDICIONAL->traductor"
    assert sug.estado_bandeja("CONDICIONAL", None) == "CONDICIONAL->traductor"
    assert sug.estado_bandeja("RUIDO", None) == "RUIDO"


# ---- ruido (Ref/localidad) via clasificador compartido ----
def test_ruido_detectado():
    clf = Clasificador()
    assert clf.es_ruido("Ref 20826") is not None
    assert clf.es_ruido("Operario/a soldador") is None


# ---- conflicto retroactivo (sintetico) a nivel sugeridor ----
def test_conflicto_retroactivo_marca_condicional():
    clf = Clasificador()
    lookup = {"vigilador/a": "5414.1"}
    res = clf.clasificar("vigilador/a", "1234.5", dict_lookup=lookup)
    assert res["clase"] == "CONDICIONAL"
    assert res["conflicto_retroactivo"]["esco_code_dic"] == "5414.1"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
