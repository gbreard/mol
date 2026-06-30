# -*- coding: utf-8 -*-
"""
SPEC S1C-G3 — Test de la Parte 3 (re-routeo del diccionario por esco_code).

Verifica:
  3.a  _match_by_argentino_dict resuelve por esco_code (via_resolucion='esco_code')
       cuando la entrada del diccionario trae un esco_code de Cyn — igual que las
       reglas, en vez de adivinar label sobre ISCO-4.
  3.b  Las 6 denominaciones SEM_LIBRE TRAIN cargadas resuelven a URI real por código.

Mecanismo, no Gold Set: estas entradas son TRAIN (alimentan el loop). La medición
de generalización se hace sobre el TEST reservado (ver reporte del punto de control).
"""
import sys
import sqlite3
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent

# Las 6 denominaciones cargadas en la Parte 3 (SEM_LIBRE TRAIN).
ENTRADAS_G3 = [
    'project control manager',
    'editor de videos',
    'intendente de obra',
    'asistente de ingeniería jr',
    'líder de mantenimiento de flota',
    'oficial armador',
]


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


def test_entradas_g3_presentes_en_config():
    """Las 6 entradas G3 están en el diccionario con esco_code."""
    import json
    oc = json.load(open(ROOT / 'config/sinonimos_argentinos_esco.json',
                        encoding='utf-8'))['ocupaciones_titulo']
    for k in ENTRADAS_G3:
        assert k in oc, f'falta entrada G3: {k}'
        assert oc[k].get('esco_code'), f'entrada G3 sin esco_code: {k}'


def test_entrada_g3_resuelve_por_codigo(matcher):
    """3.a — cada entrada G3 resuelve vía esco_code con URI real (no por label)."""
    for termino in ENTRADAS_G3:
        r = matcher._match_by_argentino_dict(
            {'titulo_limpio': termino, 'sector_empresa': ''})
        assert r is not None, f'{termino}: no matcheó el diccionario'
        assert r.get('via_resolucion') == 'esco_code', \
            f'{termino}: esperaba via esco_code, fue {r.get("via_resolucion")}'
        assert r.get('esco_uri'), f'{termino}: sin URI real'
        assert r.get('isco_code'), f'{termino}: sin ISCO'


def test_codigo_inexistente_no_rompe_resolver(matcher):
    """Un esco_code que no existe en metadata NO debe romper: cae al camino
    isco/label heredado, no a un label arbitrario."""
    # 'recepcionista' es entrada legacy SIN esco_code -> usa el camino heredado
    # (esco_uri explícito). Debe seguir resolviendo.
    r = matcher._match_by_argentino_dict(
        {'titulo_limpio': 'recepcionista', 'sector_empresa': 'hotel'})
    assert r is not None and r.get('esco_uri'), \
        'entrada legacy sin esco_code debe seguir resolviendo por su camino heredado'
