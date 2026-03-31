# -*- coding: utf-8 -*-
"""
M-08b Parte 0: Tests de texto_original en ofertas_esco_skills_detalle.
"""
import pytest
import sys
import sqlite3
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def db_with_texto_original():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE ofertas_esco_skills_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta TEXT,
            skill_mencionado TEXT,
            skill_tipo_fuente TEXT,
            esco_skill_uri TEXT,
            esco_skill_label TEXT,
            match_score REAL,
            match_method TEXT,
            esco_skill_type TEXT,
            source_classification TEXT,
            texto_original TEXT
        );
    ''')
    yield conn
    conn.close()


class TestTextoOriginal:

    def test_save_guarda_texto_fuente_como_texto_original(self, db_with_texto_original):
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_with_texto_original
        matcher.verbose = False

        skills = [{
            "skill_esco": "gestionar relaciones con clientes",
            "skill_uri": "http://esco/skill/001",
            "score": 0.45,
            "origen": "tecnologia_declarada",
            "texto_fuente": "CRM",
            "L1": "S", "L1_nombre": "Skills", "L2": "S1", "L2_nombre": "Sub",
            "es_digital": False
        }]

        matcher.save_skills_detalle("OF_001", skills)

        row = db_with_texto_original.execute(
            "SELECT texto_original, skill_mencionado FROM ofertas_esco_skills_detalle"
        ).fetchone()
        assert row["texto_original"] == "CRM"
        assert row["skill_mencionado"] == "gestionar relaciones con clientes"

    def test_save_tarea_como_texto_original(self, db_with_texto_original):
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_with_texto_original
        matcher.verbose = False

        skills = [{
            "skill_esco": "instalar cableado",
            "skill_uri": "http://esco/skill/002",
            "score": 0.82,
            "origen": "tarea",
            "tarea": "instalar cableado industrial",
            "L1": "T", "L1_nombre": "Técnica", "L2": "T1", "L2_nombre": "Sub",
            "es_digital": False
        }]

        matcher.save_skills_detalle("OF_002", skills)

        row = db_with_texto_original.execute(
            "SELECT texto_original FROM ofertas_esco_skills_detalle"
        ).fetchone()
        assert row["texto_original"] == "instalar cableado industrial"

    def test_regla_sin_texto_original(self, db_with_texto_original):
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_with_texto_original
        matcher.verbose = False

        skills = [{
            "skill_esco": "operar autoelevador",
            "skill_uri": "http://esco/skill/003",
            "score": 0.99,
            "origen": "regla",
            "L1": "T", "L1_nombre": "Técnica", "L2": "T1", "L2_nombre": "Sub",
            "es_digital": False
        }]

        matcher.save_skills_detalle("OF_003", skills)

        row = db_with_texto_original.execute(
            "SELECT texto_original FROM ofertas_esco_skills_detalle"
        ).fetchone()
        assert row["texto_original"] is None

    def test_texto_original_truncado_200(self, db_with_texto_original):
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_with_texto_original
        matcher.verbose = False

        skills = [{
            "skill_esco": "algo",
            "skill_uri": "http://esco/skill/004",
            "score": 0.50,
            "origen": "tarea",
            "texto_fuente": "x" * 500,
            "L1": "T", "L1_nombre": "", "L2": "", "L2_nombre": "",
            "es_digital": False
        }]

        matcher.save_skills_detalle("OF_004", skills)

        row = db_with_texto_original.execute(
            "SELECT texto_original FROM ofertas_esco_skills_detalle"
        ).fetchone()
        assert len(row["texto_original"]) <= 200
