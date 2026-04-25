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
    esco_label: Optional[str] = None
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
            esco_label='remachador/remachadora',
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
            isco_code='7214', esco_label='x', score=0.70,
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
            isco_code='7214', esco_label='y', score=0.95,
            metadata={'decision_metodo': 'regla_prioridad', 'regla_aplicada': 'R347'}
        )
        rematch_mod.persist_matching_result(conn, 'X1', result, estado_actual, 'r')
        conn.commit()
        c = conn.cursor()
        c.execute('SELECT decision_metodo FROM ofertas_esco_matching WHERE id_oferta="X1"')
        assert c.fetchone()[0] == 'regla_prioridad'


class TestEvaluarCambio:
    """Tests de la política D (mixta) en evaluar_cambio()."""

    def _eval(self, sv, sn, dm='semantico_unico', isco_n='7214', isco_v='5120'):
        return rematch_mod.evaluar_cambio(sv, sn, dm, isco_n, isco_v, umbral_min=0.45)

    def test_score_bajo_skip(self):
        assert self._eval(0.65, 0.40) == 'skip_score_bajo'

    def test_mismo_isco_skip(self):
        assert self._eval(0.65, 0.70, isco_n='5120') == 'skip_no_cambio'

    def test_regla_gana_aunque_score_bajo(self):
        assert self._eval(0.65, 0.30, dm='regla_prioridad') == 'actualizada_dispara_regla'

    def test_score_sube_actualiza(self):
        assert self._eval(0.55, 0.70) == 'actualizada'

    def test_score_baja_dentro_tolerancia_actualiza(self):
        # tolerancia 0.05: viejo 0.70, nuevo 0.66 → diferencia 0.04 < 0.05 → acepta
        assert self._eval(0.70, 0.66) == 'actualizada'

    def test_score_baja_fuera_tolerancia_y_viejo_alto_skip(self):
        # viejo 0.85, nuevo 0.65 → diferencia 0.20, viejo NO era bajo → SKIP regresion
        assert self._eval(0.85, 0.65) == 'skip_regresion_probable'

    def test_score_baja_pero_viejo_era_bajo_actualiza(self):
        # viejo 0.40 (era ruido), nuevo 0.50 → diff 0.10 fuera tolerancia
        # PERO viejo era < 0.50 → acepta cambio
        # (este caso ya cae en skip_score_bajo si nuevo < 0.45 — usemos 0.50)
        # nuevo 0.50 ≥ 0.45 (umbral) → procesa
        # viejo 0.40 < 0.50 → POLITICA acepta
        assert self._eval(0.40, 0.50) == 'actualizada'

    def test_score_baja_viejo_borderline_skip(self):
        # viejo 0.55, nuevo 0.45, diff 0.10 fuera tolerancia, viejo NO < 0.50
        assert self._eval(0.55, 0.45) == 'skip_regresion_probable'

    def test_caso_canonico_lashista(self):
        """Lashista: viejo era ruido (0.55) → nuevo 0.65 mejor → actualizar."""
        assert self._eval(0.555, 0.649, isco_n='5142', isco_v='2421') == 'actualizada'

    def test_caso_canonico_electricista_de_obra(self):
        """Electricista 0.94 → 0.60 → preservar viejo (es regresión)."""
        assert self._eval(0.94, 0.60, isco_n='7127', isco_v='7411') == 'skip_regresion_probable'
