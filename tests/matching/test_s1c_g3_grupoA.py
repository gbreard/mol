# -*- coding: utf-8 -*-
"""
SPEC S1C-G3 — GRUPO A: 47 denominaciones validadas por Cyn (xlsx 2026-06-24).

Verifica:
  - Las denominaciones de Cyn resuelven por su esco_code a la ocupación correcta.
  - El fix de "variante más larga gana" desambigua substrings que antes colisionaban
    (vigilador/a de personal ≠ vigilador/a; sales executive ≠ sales→vendedor).
  - El caso semilla 'intendente de obra' quedó corregido a capataz (3123), NO conserje.

Mecanismo + no-regresión (la medición de regresión en TEST va en el reporte).
"""
import sys
import sqlite3
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope='module')
def matcher():
    warnings.filterwarnings('ignore')
    sys.path.insert(0, str(ROOT / 'database'))
    sys.path.insert(0, str(ROOT / 'config'))
    from match_ofertas_v3 import MatcherV3
    conn = sqlite3.connect(str(ROOT / 'database/bumeran_scraping.db'))
    m = MatcherV3(db_conn=conn, verbose=False)
    yield m
    conn.close()


# (denominación, ISCO-4 esperado) — muestra representativa del GRUPO A.
MUESTRA_GRUPO_A = [
    ('acomp terapeutico', '3412'),
    ('bachero / steward', '9412'),
    ('fileteador', '7511'),
    ('intendente de obra', '3123'),       # corregido de 5153 (conserje) por Cyn
    ('inyector plástico', '8142'),
    ('legal assistant', '3342'),
    ('lic. en kinesiología', '2269'),
    ('telemarketer', '5244'),
    ('sommelier', '5131'),
    ('referente de armado', '3122'),
]


def test_muestra_grupo_a_resuelve_por_codigo(matcher):
    for termino, isco_esp in MUESTRA_GRUPO_A:
        r = matcher._match_by_argentino_dict(
            {'titulo_limpio': termino, 'sector_empresa': ''})
        assert r is not None, f'{termino}: no matcheó el diccionario'
        assert str(r.get('isco_code'))[:4] == isco_esp, \
            f'{termino}: esperaba ISCO {isco_esp}, fue {r.get("isco_code")}'
        assert r.get('esco_uri'), f'{termino}: sin URI'


def test_intendente_de_obra_corregido_a_capataz(matcher):
    """Caso semilla: Cyn validó capataz (3123.1.1), NO conserje (5153)."""
    r = matcher._match_by_argentino_dict(
        {'titulo_limpio': 'intendente de obra', 'sector_empresa': ''})
    assert str(r.get('isco_code'))[:4] == '3123'
    assert 'conserje' not in (r.get('esco_label') or '').lower()


def test_variante_mas_larga_gana(matcher):
    """El fix de especificidad: la denominación más larga (más específica) gana
    sobre una genérica que la contiene como substring."""
    # 'vigilador/a de personal' (supervisor producción 3122) NO debe caer en
    # 'vigilador/a' (vigilante de seguridad 5414).
    r = matcher._match_by_argentino_dict(
        {'titulo_limpio': 'vigilador/a de personal', 'sector_empresa': ''})
    assert str(r.get('isco_code'))[:4] == '3122', \
        f'vigilador/a de personal debería ser 3122, fue {r.get("isco_code")}'
    # 'vigilador/a' a secas (sin 'de personal') sí es seguridad (5414).
    r2 = matcher._match_by_argentino_dict(
        {'titulo_limpio': 'vigilador/a nocturno', 'sector_empresa': ''})
    assert str(r2.get('isco_code'))[:4] == '5414'
    # 'sales executive' -> representante comercial (3322), no vendedor (5223 via 'sales').
    r3 = matcher._match_by_argentino_dict(
        {'titulo_limpio': 'sales executive', 'sector_empresa': ''})
    assert str(r3.get('isco_code'))[:4] == '3322', \
        f'sales executive debería ser 3322, fue {r3.get("isco_code")}'


def test_lobos_no_cargada(matcher):
    """'lobos' (localidad mal tomada como título) quedó en HOLD, no se cargó."""
    import json
    oc = json.load(open(ROOT / 'config/sinonimos_argentinos_esco.json',
                        encoding='utf-8'))['ocupaciones_titulo']
    assert 'lobos' not in oc, "'lobos' no debe cargarse (es localidad, no denominación)"
