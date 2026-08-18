"""
Tests del clasificador de candidatas del puente (FRENTE B).

Contrato: el clasificador (config congelada config/clasificador_candidatas.json)
sobre la fixture de las 34 reproduce la matriz v2 EXACTA (senal + clasificacion),
con 0 falsos vocabulario. Cambiar la config exige actualizar este test (regresion
del ajuste).
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from puente.clasificador import Clasificador  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "clasificador_candidatas_fixture_2026-07-03.json"


@pytest.fixture(scope="module")
def clf():
    return Clasificador()


@pytest.fixture(scope="module")
def fixture_data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_reproduce_matriz_v2_exacta(clf, fixture_data):
    """Cada caso: senal y clasificacion esperadas se reproducen exactas."""
    fallos = []
    for c in fixture_data["casos"]:
        res = clf.clasificar(c["denominacion"], c["esco_code"])
        if res["clase"] != c["clasificacion_esperada"] or res["senal"] != c["senal_esperada"]:
            fallos.append((c["id_oferta"], c["denominacion"],
                           f"esperado {c['clasificacion_esperada']}/{c['senal_esperada']}",
                           f"got {res['clase']}/{res['senal']}"))
    assert not fallos, f"divergencias con la fixture v2: {fallos}"


def test_cero_falsos_vocabulario(clf, fixture_data):
    """La barra: ninguna candidata que el humano juzgo NO-vocabulario puede salir VOCABULARIO."""
    falsos = []
    for c in fixture_data["casos"]:
        res = clf.clasificar(c["denominacion"], c["esco_code"])
        hj = c["juicio_humano"]["clase"]
        if res["clase"] == "VOCABULARIO" and hj != "VOCABULARIO":
            falsos.append((c["id_oferta"], c["denominacion"], hj))
    assert not falsos, f"FALSOS VOCABULARIO (error caro): {falsos}"


def test_resumen_esperado_coincide(clf, fixture_data):
    """El split del clasificador coincide con el resumen declarado en la fixture."""
    from collections import Counter
    got = Counter(clf.clasificar(c["denominacion"], c["esco_code"])["clase"]
                  for c in fixture_data["casos"])
    esperado = fixture_data["resumen_esperado"]["clasificador"]
    assert dict(got) == esperado, f"split {dict(got)} != esperado {esperado}"


def test_head_anclado_no_substring(clf):
    """El falso disparo v1 'oficina tecnica' NO debe activar S1-azul:tecnico:
    el head es 'analista', no 'tecnica' en posicion interna."""
    assert clf.head("Analista de Oficina Tecnica") == "analista"
    res = clf.clasificar("Analista de Oficina Tecnica", "2142.1")
    assert res["senal"] == "S1-blanca:analista", res


def test_familias_blancas_recuperan_falsos_vocab_v1(clf):
    """Los 3 falsos-vocab de la v1 que se recuperan por familia blanca / dict / guard."""
    assert clf.clasificar("Advisor", "2519.7")["clase"] == "CONDICIONAL"
    assert clf.clasificar("Asesor comercial", "1221.3.2")["senal"] == "S1-blanca:asesor"
    assert clf.clasificar("Gerente Administracion", "1211.1")["senal"] == "S1b-dict:gerente"
    # guard de profundidad recupera Ingeniero Electronico (sub-codigo fino)
    assert clf.clasificar("Ingeniero Electronico", "2152.1.12")["senal"] == "guard-prof:2pts"


def test_guard_profundidad_no_toca_nivel_base(clf):
    """esco_code de 1 punto (ocupacion base) NO dispara el guard."""
    assert not clf.guard_profundidad("5414.1")
    assert clf.guard_profundidad("2152.1.12")
    # vigilador/a (base, sin otra senal) sale VOCABULARIO
    assert clf.clasificar("vigilador/a", "5414.1")["clase"] == "VOCABULARIO"


def test_s1b_es_dinamico_desde_diccionario(clf):
    """S1b lee las entradas con bloque contextos del diccionario en runtime."""
    # al 2026-07-03 eran gerente/vendedor/tecnico/operador; 'vendedor' se retiro
    # con la activacion del piloto Eje 4 ([FRENTE H P4] 2026-08-18, _migra_en_piloto)
    for raiz in ["gerente", "tecnico", "operador"]:
        assert raiz in clf.dict_contextos, f"{raiz} deberia estar en dict_contextos"
    assert "vendedor" not in clf.dict_contextos, "vendedor fue retirada en el piloto"


def test_conflicto_retroactivo_sintetico(clf):
    """Denominacion que ya existe en el diccionario con OTRO esco_code -> conflicto.
    'vigilador/a' esta en el dic con 5414.1; una correccion a otro codigo dispara S3."""
    lookup = {"vigilador/a": "5414.1", "vigilador": "5414.1"}
    res = clf.clasificar("vigilador/a", "9999.9", dict_lookup=lookup)
    assert res["clase"] == "CONDICIONAL"
    assert res["senal"] == "S3-conflicto"
    assert res["conflicto_retroactivo"]["esco_code_dic"] == "5414.1"
    assert res["conflicto_retroactivo"]["esco_code_correccion"] == "9999.9"


def test_ruido_ref_y_localidad(clf):
    """Titulo que es solo prefijo-Ref sin denominacion util, o solo localidad -> RUIDO."""
    assert clf.es_ruido("Ref 20826") is not None
    assert clf.es_ruido("BU667") is not None
    # con denominacion real detras del prefijo NO es ruido
    assert clf.es_ruido("BU667 Operario de Produccion Metalurgico") is None
    assert clf.es_ruido("Operario/a soldador") is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
