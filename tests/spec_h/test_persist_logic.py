# -*- coding: utf-8 -*-
"""
Tests de lógica de decisión (umbral, skip, actualizar) sin cargar MatcherV3.

Usa un MockMatchResult que simula lo que retornaría MatcherV3.match().
"""
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'scripts' / 'embeddings'))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "rematch_spec_h",
    ROOT / "scripts" / "embeddings" / "rematch_isco_spec_h.py"
)
rematch_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rematch_mod)


@dataclass
class MockMatchResult:
    """Emula la estructura de MatchResult de match_ofertas_v3."""
    isco_code: Optional[str] = None
    esco_occupation_label: Optional[str] = None
    score: float = 0.0
    metadata: Optional[Dict] = None
    skills: list = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.skills is None:
            self.skills = []


@pytest.fixture
def db_tmp(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    c.execute('''CREATE TABLE ofertas_esco_matching (
        id_oferta TEXT PRIMARY KEY,
        isco_code TEXT,
        esco_occupation_label TEXT,
        titulo_esco_code TEXT,
        score_semantico REAL,
        occupation_match_score REAL,
        decision_metodo TEXT,
        estado_validacion TEXT,
        matching_timestamp TEXT,
        matching_version TEXT,
        run_id TEXT
    )''')
    c.execute('''INSERT INTO ofertas_esco_matching VALUES
                 ('X1', '5120', 'cocinero_viejo', '5120.1', 0.55, 0.55,
                  'semantico_unico', 'validado_claude', '2026-01-01', 'v3.0.0', 'run_old')''')
    conn.commit()
    rematch_mod.ensure_tables(conn)
    yield conn
    conn.close()


class TestPersistMatchingResult:

    def test_actualiza_campos_principales(self, db_tmp):
        conn = db_tmp
        estado_actual = rematch_mod.get_estado_actual(conn, 'X1')
        result = MockMatchResult(
            isco_code='7214',
            esco_occupation_label='remachador/remachadora',
            score=0.72,
            metadata={'esco_code': '7214.3.1', 'decision_metodo': 'semantico_unico'},
        )
        info = rematch_mod.persist_matching_result(conn, 'X1', result, estado_actual, 'run_new')
        conn.commit()

        c = conn.cursor()
        c.execute('SELECT isco_code, esco_occupation_label, titulo_esco_code, score_semantico, run_id, matching_version FROM ofertas_esco_matching WHERE id_oferta="X1"')
        row = c.fetchone()
        assert row[0] == '7214'
        assert row[1] == 'remachador/remachadora'
        assert row[2] == '7214.3.1'
        assert abs(row[3] - 0.72) < 1e-6
        assert row[4] == 'run_new'
        assert row[5] == 'spec_h_rematch'

    def test_mantiene_estado_validacion(self, db_tmp):
        """Crítico: el update NO debe cambiar estado_validacion."""
        conn = db_tmp
        estado_actual = rematch_mod.get_estado_actual(conn, 'X1')
        result = MockMatchResult(
            isco_code='7214', esco_occupation_label='x', score=0.70,
            metadata={'decision_metodo': 'semantico_unico'}
        )
        rematch_mod.persist_matching_result(conn, 'X1', result, estado_actual, 'r')
        conn.commit()
        c = conn.cursor()
        c.execute('SELECT estado_validacion FROM ofertas_esco_matching WHERE id_oferta="X1"')
        assert c.fetchone()[0] == 'validado_claude'  # intacto

    def test_actualiza_decision_metodo_si_dispara_regla(self, db_tmp):
        conn = db_tmp
        estado_actual = rematch_mod.get_estado_actual(conn, 'X1')
        result = MockMatchResult(
            isco_code='7214', esco_occupation_label='y', score=0.95,
            metadata={'decision_metodo': 'regla_prioridad', 'regla_aplicada': 'R347'}
        )
        rematch_mod.persist_matching_result(conn, 'X1', result, estado_actual, 'r')
        conn.commit()
        c = conn.cursor()
        c.execute('SELECT decision_metodo FROM ofertas_esco_matching WHERE id_oferta="X1"')
        assert c.fetchone()[0] == 'regla_prioridad'


class TestUmbralLogic:
    """Tests de la lógica de decisión (umbral, skip reasons)."""

    def test_score_bajo_no_persiste(self, db_tmp):
        """Si el script decide skip_score_bajo, los campos NO se tocan."""
        conn = db_tmp
        # Aquí replico la lógica inline del main() para testearla aislada.
        estado_actual = rematch_mod.get_estado_actual(conn, 'X1')
        result = MockMatchResult(
            isco_code='7214', esco_occupation_label='z', score=0.40,
            metadata={'decision_metodo': 'semantico_unico'}
        )
        umbral = 0.45

        if result.metadata.get('decision_metodo') == 'regla_prioridad':
            resultado = 'actualizada_dispara_regla'
        elif result.score < umbral:
            resultado = 'skip_score_bajo'
        elif str(result.isco_code) == estado_actual['isco_code']:
            resultado = 'skip_no_cambio'
        else:
            resultado = 'actualizada'

        assert resultado == 'skip_score_bajo'

        # Verificar que el estado en BD NO cambió
        c = conn.cursor()
        c.execute('SELECT isco_code FROM ofertas_esco_matching WHERE id_oferta="X1"')
        assert c.fetchone()[0] == '5120'  # sigue el viejo

    def test_mismo_isco_skip(self, db_tmp):
        conn = db_tmp
        estado_actual = rematch_mod.get_estado_actual(conn, 'X1')
        # Matcher retorna el mismo ISCO
        result = MockMatchResult(
            isco_code='5120', esco_occupation_label='cocinero_nuevo', score=0.70,
            metadata={'decision_metodo': 'semantico_unico'}
        )
        umbral = 0.45
        if result.metadata.get('decision_metodo') == 'regla_prioridad':
            resultado = 'actualizada_dispara_regla'
        elif result.score < umbral:
            resultado = 'skip_score_bajo'
        elif str(result.isco_code) == estado_actual['isco_code']:
            resultado = 'skip_no_cambio'
        else:
            resultado = 'actualizada'
        assert resultado == 'skip_no_cambio'

    def test_regla_tiene_prioridad_sobre_umbral(self, db_tmp):
        """Aunque score sea bajo, si dispara regla → aplicar."""
        conn = db_tmp
        estado_actual = rematch_mod.get_estado_actual(conn, 'X1')
        result = MockMatchResult(
            isco_code='7214', esco_occupation_label='x', score=0.30,
            metadata={'decision_metodo': 'regla_prioridad'}
        )
        umbral = 0.45
        if result.metadata.get('decision_metodo') == 'regla_prioridad':
            resultado = 'actualizada_dispara_regla'
        elif result.score < umbral:
            resultado = 'skip_score_bajo'
        elif str(result.isco_code) == estado_actual['isco_code']:
            resultado = 'skip_no_cambio'
        else:
            resultado = 'actualizada'
        assert resultado == 'actualizada_dispara_regla'
