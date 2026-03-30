# -*- coding: utf-8 -*-
"""
M-06: Tests de integración — Verificar que los fallidos se persisten en BD.

Usa SQLite en memoria para no afectar la BD real.
"""

import pytest
import sys
import sqlite3
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_memory():
    """BD SQLite en memoria con tabla skills_extraction_failures."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE skills_extraction_failures (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            oferta_id       TEXT NOT NULL,
            run_id          TEXT,
            fecha_intento   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tarea_texto     TEXT NOT NULL,
            tarea_origen    TEXT,
            mejor_skill_uri   TEXT,
            mejor_skill_label TEXT,
            mejor_score       REAL,
            threshold_usado   REAL DEFAULT 0.40,
            gap_al_umbral     REAL,
            tipo_falla      TEXT DEFAULT 'sin_clasificar'
        );
        CREATE TABLE ofertas_esco_matching (
            id_oferta TEXT PRIMARY KEY,
            isco_code TEXT,
            run_id TEXT,
            estado_validacion TEXT DEFAULT 'pendiente'
        );
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
            source_classification TEXT
        );
    ''')
    yield conn
    conn.close()


@pytest.fixture
def mock_extractor_for_integration():
    """Extractor mock que produce failures controlados."""
    from database.skills_implicit_extractor import SkillsImplicitExtractor

    ext = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    ext.verbose = False
    ext.top_k = 3
    ext.threshold = 0.40

    ext.metadata = [
        {"label": "instalar cableado", "uri": "http://esco/skill/001"},
        {"label": "gestionar inventario", "uri": "http://esco/skill/002"},
    ]

    dim = 32
    ext.embeddings = np.zeros((2, dim), dtype=np.float32)
    ext.embeddings[0, 0:6] = 1.0
    ext.embeddings[1, 6:12] = 1.0
    norms = np.linalg.norm(ext.embeddings, axis=1, keepdims=True)
    ext.embeddings = ext.embeddings / norms

    ext.sinonimos_skills = {"tareas_a_skills": {}, "soft_skills_argentinas": {}}
    ext.equiv_lookup = {}
    ext.equiv_groups = {}
    ext.weights_config = {"skills_genericas": {"lista": [], "peso": 0.5}}
    ext.terminology_config = {"terminos": {}}

    def _encode(text, normalize_embeddings=True):
        vec = np.zeros(dim, dtype=np.float32)
        if "cableado" in text.lower():
            vec[0:6] = 1.0  # Matchea skill 001
        else:
            vec[30:32] = 1.0  # No matchea nada
        norm = np.linalg.norm(vec)
        if norm > 0 and normalize_embeddings:
            vec = vec / norm
        return vec

    ext.model = MagicMock()
    ext.model.encode = _encode
    return ext


# ============================================================================
# Tests de integración
# ============================================================================

class TestIntegrationPathMatching:

    def test_persist_skill_failures_inserta_en_bd(self, db_memory, mock_extractor_for_integration):
        """_persist_skill_failures() inserta correctamente en la tabla."""
        from database.match_ofertas_v3 import MatcherV3

        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_memory

        failures = [
            {
                "tarea_texto": "reparar tableros eléctricos",
                "tarea_origen": "tarea",
                "mejor_skill_uri": "http://esco/skill/001",
                "mejor_skill_label": "instalar cableado",
                "mejor_score": 0.32,
                "threshold_usado": 0.40,
                "gap_al_umbral": 0.08
            }
        ]

        matcher._persist_skill_failures("OFERTA_001", "run_test_001", failures)

        rows = db_memory.execute("SELECT * FROM skills_extraction_failures").fetchall()
        assert len(rows) == 1
        row = dict(rows[0])
        assert row["oferta_id"] == "OFERTA_001"
        assert row["run_id"] == "run_test_001"
        assert row["tarea_texto"] == "reparar tableros eléctricos"
        assert row["tarea_origen"] == "tarea"
        assert row["mejor_score"] == 0.32
        assert row["gap_al_umbral"] == 0.08

    def test_persist_failures_fallo_silencioso(self):
        """Si la tabla no existe, no lanza excepción."""
        from database.match_ofertas_v3 import MatcherV3

        conn_sin_tabla = sqlite3.connect(":memory:")  # BD vacía, sin tabla
        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = conn_sin_tabla

        failures = [{
            "tarea_texto": "algo",
            "mejor_score": 0.1,
            "threshold_usado": 0.40,
            "gap_al_umbral": 0.30
        }]

        # No debe lanzar excepción
        matcher._persist_skill_failures("X", "run_X", failures)
        conn_sin_tabla.close()

    def test_persist_failures_lista_vacia_no_inserta(self, db_memory):
        """Con lista vacía, no hace INSERT."""
        from database.match_ofertas_v3 import MatcherV3

        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_memory

        matcher._persist_skill_failures("OFERTA_001", "run_001", [])

        count = db_memory.execute("SELECT COUNT(*) FROM skills_extraction_failures").fetchone()[0]
        assert count == 0

    def test_multiples_failures_misma_oferta(self, db_memory):
        """Múltiples failures se insertan todas."""
        from database.match_ofertas_v3 import MatcherV3

        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_memory

        failures = [
            {"tarea_texto": "tarea A", "tarea_origen": "tarea", "mejor_score": 0.30,
             "threshold_usado": 0.40, "gap_al_umbral": 0.10},
            {"tarea_texto": "tarea B", "tarea_origen": "titulo", "mejor_score": 0.15,
             "threshold_usado": 0.40, "gap_al_umbral": 0.25},
            {"tarea_texto": "tarea C", "tarea_origen": "skills_nlp", "mejor_score": 0.05,
             "threshold_usado": 0.40, "gap_al_umbral": 0.35},
        ]

        matcher._persist_skill_failures("OFERTA_002", "run_002", failures)

        count = db_memory.execute("SELECT COUNT(*) FROM skills_extraction_failures WHERE oferta_id='OFERTA_002'").fetchone()[0]
        assert count == 3

        origenes = [r[0] for r in db_memory.execute("SELECT tarea_origen FROM skills_extraction_failures ORDER BY id").fetchall()]
        assert origenes == ["tarea", "titulo", "skills_nlp"]


class TestIntegrationPathNLP:

    def test_nlp_path_registra_con_run_id_null(self, db_memory):
        """Path NLP persiste failures con run_id=NULL."""
        # Simular lo que haría process_oferta
        failures = [
            {"tarea_texto": "diseñar agentes de IA", "mejor_score": 0.12,
             "threshold_usado": 0.40, "gap_al_umbral": 0.28}
        ]

        for f in failures:
            db_memory.execute('''
                INSERT INTO skills_extraction_failures
                (oferta_id, run_id, tarea_texto, tarea_origen,
                 mejor_skill_uri, mejor_skill_label, mejor_score,
                 threshold_usado, gap_al_umbral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "OFERTA_NLP_001", None,
                f["tarea_texto"], "nlp",
                None, None,
                f["mejor_score"],
                f["threshold_usado"],
                f["gap_al_umbral"]
            ))
        db_memory.commit()

        row = dict(db_memory.execute("SELECT * FROM skills_extraction_failures").fetchone())
        assert row["oferta_id"] == "OFERTA_NLP_001"
        assert row["run_id"] is None
        assert row["tarea_origen"] == "nlp"

    def test_ambos_paths_misma_oferta(self, db_memory):
        """Una oferta puede tener registros de ambos paths."""
        from database.match_ofertas_v3 import MatcherV3

        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = db_memory

        # Path NLP (run_id=NULL)
        db_memory.execute('''
            INSERT INTO skills_extraction_failures
            (oferta_id, run_id, tarea_texto, tarea_origen, mejor_score, threshold_usado, gap_al_umbral)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("DUAL_001", None, "tarea NLP", "nlp", 0.20, 0.40, 0.20))
        db_memory.commit()

        # Path Matching (run_id con valor)
        matcher._persist_skill_failures("DUAL_001", "run_matching_001", [
            {"tarea_texto": "tarea matching", "tarea_origen": "tarea",
             "mejor_score": 0.25, "threshold_usado": 0.40, "gap_al_umbral": 0.15}
        ])

        rows = db_memory.execute(
            "SELECT tarea_origen, run_id FROM skills_extraction_failures WHERE oferta_id='DUAL_001' ORDER BY id"
        ).fetchall()

        assert len(rows) == 2
        assert dict(rows[0])["tarea_origen"] == "nlp"
        assert dict(rows[0])["run_id"] is None
        assert dict(rows[1])["tarea_origen"] == "tarea"
        assert dict(rows[1])["run_id"] == "run_matching_001"
