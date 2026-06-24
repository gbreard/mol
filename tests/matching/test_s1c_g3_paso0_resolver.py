# -*- coding: utf-8 -*-
"""
SPEC S1C-G3 — Test 0 (Paso 0: limpieza del resolver).

Verifica la higiene estructural del Paso 0, que NO toca el camino de decisión:
  0.a  _find_occupation_uri (código muerto) fue borrada.
  0.b  _get_esco_label_for_isco ya NO inventa un label arbitrario para un
       ISCO no mapeado: falla de forma ruidosa (loguea WARNING) y devuelve "".

Estos tests son de mecanismo, no de Gold Set: el Paso 0 no debe mover métricas.
"""
import sys
import sqlite3
import logging
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


def test_find_occupation_uri_borrada(matcher):
    """0.a — el método muerto _find_occupation_uri ya no existe."""
    assert not hasattr(matcher, '_find_occupation_uri'), \
        '_find_occupation_uri debería haberse borrado (código muerto, 0 callers)'


def test_isco_mapeado_devuelve_label_explicito(matcher):
    """0.b — un ISCO con mapeo explícito sigue devolviendo su label autoritativo."""
    # Tomar cualquier ISCO presente en el mapeo explícito.
    if not matcher.isco_preferred_labels:
        pytest.skip('isco_preferred_labels vacío en este entorno')
    isco, label = next(iter(matcher.isco_preferred_labels.items()))
    assert matcher._get_esco_label_for_isco(isco) == label


def test_isco_no_mapeado_falla_ruidoso_sin_label_arbitrario(matcher, caplog):
    """0.b — un ISCO SIN mapeo explícito devuelve "" (no un label arbitrario)
    y deja un WARNING visible. Antes devolvía un label arbitrario vía LIMIT 1."""
    isco_inexistente = '0000'  # no es un ISCO real → no está en el mapeo
    assert isco_inexistente not in matcher.isco_preferred_labels
    with caplog.at_level(logging.WARNING):
        resultado = matcher._get_esco_label_for_isco(isco_inexistente)
    assert resultado == '', \
        f'Esperaba "" (sin label), obtuvo un label arbitrario: {resultado!r}'
    assert any('S1C-G3' in r.message or '_get_esco_label_for_isco' in r.message
               for r in caplog.records), \
        'El fallo del resolver debería loguear un WARNING visible'
