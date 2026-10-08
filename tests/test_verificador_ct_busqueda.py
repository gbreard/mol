"""
Tests de la vía BÚSQUEDA de CompuTrabajo en el verificador de bajas
(mini-spec SPEC_ct_verificacion_busqueda.md). Espejo de clasificar_navent:
presencia en el buscador = existencia. No tocan red ni BD (se mockea _ct_buscar).
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
import database.verificador_bajas as vb  # noqa: E402

TID = vb.CT_ID_PREFIX + 123  # id objetivo de prueba


@pytest.fixture
def v():
    # __init__ solo lee el config (no conecta BD). clasificar_* no toca BD.
    return vb.VerificadorBajas()


def test_slug():
    s = vb.VerificadorBajas._slug_ct
    assert s("Vendedor de Mostradór!! (urgente)") == "vendedor-de-mostrador-urgente"
    assert s("Operario/a de depósito", 2) == "operario-a"
    assert s("") == ""


def test_viva_id_presente(v, monkeypatch):
    monkeypatch.setattr(v, "_ct_buscar", lambda q: ({TID, vb.CT_ID_PREFIX + 9}, 5, False))
    r, s = v.clasificar_ct_busqueda("u", "Vendedor", TID)
    assert r == "viva" and s["id_presente"] is True


def test_caida_cero_resultados(v, monkeypatch):
    monkeypatch.setattr(v, "_ct_buscar", lambda q: (set(), 0, False))
    r, s = v.clasificar_ct_busqueda("u", "Puesto inexistente", TID)
    assert r == "caida" and s["caso"] == "cero_resultados"


def test_caida_menos_que_tope_sin_id(v, monkeypatch):
    # hay resultados, no se llenó el tope (vimos todo), el id no está → caída
    monkeypatch.setattr(v, "_ct_buscar",
                        lambda q: ({vb.CT_ID_PREFIX + 1, vb.CT_ID_PREFIX + 2}, 5, False))
    r, s = v.clasificar_ct_busqueda("u", "Vendedor", TID)
    assert r == "caida" and s["caso"] == "menos_que_tope_sin_id"


def test_tope_reintento_resuelve_caida(v, monkeypatch):
    # 1ª query (corta) llena el tope; reintento (query larga) ve todo sin el id → caída
    seq = [({vb.CT_ID_PREFIX + 7}, 40, True), ({vb.CT_ID_PREFIX + 8}, 4, False)]
    monkeypatch.setattr(v, "_ct_buscar", lambda q: seq.pop(0))
    titulo = "Analista funcional senior de sistemas con experiencia bancaria avanzada y liderazgo"
    r, s = v.clasificar_ct_busqueda("u", titulo, TID)
    assert r == "caida" and s.get("reintento") and s["caso"] == "reintento_menos_tope"


def test_tope_persiste_ambigua(v, monkeypatch):
    # el tope se mantiene en ambas queries → ambigua (no cuenta, no confirma baja)
    calls = []
    def fake(q):
        calls.append(q)
        return ({vb.CT_ID_PREFIX + 1}, 40, True)
    monkeypatch.setattr(v, "_ct_buscar", fake)
    titulo = "Vendedor comercial de mostrador con atencion al publico general polirubro flexible"
    r, s = v.clasificar_ct_busqueda("u", titulo, TID)
    assert r == "ambigua" and s["caso"] == "tope_alcanzado"
    assert len(calls) == 2  # query corta + reintento


def test_sin_titulo_ambigua(v):
    r, s = v.clasificar_ct_busqueda("u", None, TID)
    assert r == "ambigua"


def test_bloqueo_propaga_para_circuit_breaker(v, monkeypatch):
    # un bloqueo del buscador (non-200/challenge) NO debe leerse como "caída":
    # _ct_buscar_pagina lanza BloqueoError y debe propagarse (lo toma el circuit-breaker).
    def boom(query, pagina):
        raise vb.BloqueoError("CT busq challenge")
    monkeypatch.setattr(v, "_ct_buscar_pagina", boom)
    with pytest.raises(vb.BloqueoError):
        v.clasificar_ct_busqueda("u", "Vendedor", TID)


def test_ct_buscar_corta_en_pagina_no_llena(v, monkeypatch):
    # si la 1ª página no está llena, NO pide la 2ª y tope=False (vio todo)
    paginas = {1: ({vb.CT_ID_PREFIX + 1}, 5)}
    llamadas = []
    def fake_pag(query, pagina):
        llamadas.append(pagina)
        return paginas.get(pagina, (set(), 0))
    monkeypatch.setattr(v, "_ct_buscar_pagina", fake_pag)
    ids, n, tope = v._ct_buscar("vendedor")
    assert ids == {vb.CT_ID_PREFIX + 1} and n == 5 and tope is False
    assert llamadas == [1]  # no pidió la página 2


def test_ct_buscar_tope_dos_paginas_llenas(v, monkeypatch):
    def fake_pag(query, pagina):
        return ({vb.CT_ID_PREFIX + pagina}, 20)  # ambas llenas
    monkeypatch.setattr(v, "_ct_buscar_pagina", fake_pag)
    monkeypatch.setattr(vb.time, "sleep", lambda *_: None)
    ids, n, tope = v._ct_buscar("vendedor")
    assert tope is True and n == 40
