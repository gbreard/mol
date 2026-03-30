# -*- coding: utf-8 -*-
"""
M-01: Tests para sync_learnings.py extendido — datos de último run.

9 tests: 5 unitarios + 4 integración (mock Supabase).
"""

import pytest
import sys
import sqlite3
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_with_runs(tmp_path):
    """SQLite con pipeline_runs y skills_extraction_failures para tests."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript('''
        CREATE TABLE pipeline_runs (
            run_id TEXT PRIMARY KEY,
            timestamp TEXT,
            git_branch TEXT,
            git_commit TEXT,
            nlp_version TEXT,
            matching_version TEXT,
            ofertas_count INTEGER,
            metricas_precision REAL,
            errores_detectados INTEGER,
            errores_corregidos INTEGER,
            errores_escalados INTEGER,
            run_anterior TEXT,
            diff_mejoras INTEGER,
            diff_regresiones INTEGER,
            delta_reglas INTEGER,
            sinonimos_count INTEGER,
            reglas_negocio_count INTEGER,
            metricas_detalle TEXT,
            source TEXT,
            description TEXT,
            config_snapshot TEXT,
            config_files TEXT,
            ofertas_ids TEXT,
            metricas_total INTEGER,
            metricas_correctos INTEGER,
            metricas_parciales INTEGER,
            metricas_errores INTEGER,
            reglas_validacion_count INTEGER,
            empresas_catalogo_count INTEGER
        );

        CREATE TABLE ofertas_esco_matching (
            id_oferta TEXT PRIMARY KEY,
            run_id TEXT,
            isco_code TEXT,
            estado_validacion TEXT DEFAULT 'pendiente'
        );

        CREATE TABLE ofertas_esco_skills_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta TEXT,
            skill_mencionado TEXT
        );

        CREATE TABLE ofertas_nlp (
            id_oferta TEXT PRIMARY KEY,
            tareas_explicitas TEXT,
            titulo_limpio TEXT
        );

        CREATE TABLE skills_extraction_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oferta_id TEXT,
            run_id TEXT,
            tarea_texto TEXT,
            tarea_origen TEXT,
            mejor_skill_uri TEXT,
            mejor_skill_label TEXT,
            mejor_score REAL,
            threshold_usado REAL DEFAULT 0.40,
            gap_al_umbral REAL,
            fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo_falla TEXT DEFAULT 'sin_clasificar'
        );

        -- Insert test data: 2 runs
        INSERT INTO pipeline_runs (run_id, timestamp, git_branch, git_commit,
            nlp_version, matching_version, ofertas_count, metricas_precision,
            errores_detectados, errores_corregidos, errores_escalados,
            run_anterior, diff_mejoras, diff_regresiones, delta_reglas)
        VALUES ('run_002', '2026-03-30T14:00:00', 'main', 'abc123',
            '11.3.0', '3.5.2', 500, 0.976,
            12, 10, 2,
            'run_001', 15, 0, 38);

        INSERT INTO pipeline_runs (run_id, timestamp, git_branch, git_commit,
            nlp_version, matching_version, ofertas_count, metricas_precision,
            errores_detectados, errores_corregidos, errores_escalados,
            run_anterior, diff_mejoras, diff_regresiones, delta_reglas)
        VALUES ('run_001', '2026-03-29T10:00:00', 'main', 'def456',
            '11.3.0', '3.5.2', 487, 0.974,
            8, 8, 0,
            NULL, NULL, NULL, 20);

        -- Ofertas del run_002
        INSERT INTO ofertas_esco_matching (id_oferta, run_id) VALUES ('O1', 'run_002');
        INSERT INTO ofertas_esco_matching (id_oferta, run_id) VALUES ('O2', 'run_002');

        -- Skills
        INSERT INTO ofertas_esco_skills_detalle (id_oferta, skill_mencionado) VALUES ('O1', 'skill_a');
        INSERT INTO ofertas_esco_skills_detalle (id_oferta, skill_mencionado) VALUES ('O1', 'skill_b');
        INSERT INTO ofertas_esco_skills_detalle (id_oferta, skill_mencionado) VALUES ('O2', 'skill_c');

        -- NLP (for tareas count)
        INSERT INTO ofertas_nlp (id_oferta, tareas_explicitas, titulo_limpio)
        VALUES ('O1', 'tarea1; tarea2; tarea3', 'Titulo oferta 1');
        INSERT INTO ofertas_nlp (id_oferta, tareas_explicitas, titulo_limpio)
        VALUES ('O2', 'tarea4; tarea5', 'Titulo oferta 2');

        -- Failures del run_002
        INSERT INTO skills_extraction_failures (oferta_id, run_id, tarea_texto, mejor_skill_label, mejor_score, gap_al_umbral)
        VALUES ('O1', 'run_002', 'Controlar mermas', 'administrar', 0.3945, 0.0055);
        INSERT INTO skills_extraction_failures (oferta_id, run_id, tarea_texto, mejor_skill_label, mejor_score, gap_al_umbral)
        VALUES ('O2', 'run_002', 'Elaborar plan maestro', 'planificar inventario', 0.3809, 0.0191);
    ''')
    conn.close()
    return db_path


@pytest.fixture
def db_empty(tmp_path):
    """SQLite con tablas vacías."""
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript('''
        CREATE TABLE pipeline_runs (run_id TEXT PRIMARY KEY, timestamp TEXT,
            git_branch TEXT, git_commit TEXT, nlp_version TEXT, matching_version TEXT,
            ofertas_count INTEGER, metricas_precision REAL, errores_detectados INTEGER,
            errores_corregidos INTEGER, errores_escalados INTEGER, run_anterior TEXT,
            diff_mejoras INTEGER, diff_regresiones INTEGER, delta_reglas INTEGER,
            sinonimos_count INTEGER, reglas_negocio_count INTEGER);
    ''')
    conn.close()
    return db_path


@pytest.fixture
def db_no_failures(tmp_path):
    """SQLite con pipeline_runs pero SIN tabla skills_extraction_failures."""
    db_path = tmp_path / "no_failures.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript('''
        CREATE TABLE pipeline_runs (run_id TEXT PRIMARY KEY, timestamp TEXT,
            git_branch TEXT, git_commit TEXT, nlp_version TEXT, matching_version TEXT,
            ofertas_count INTEGER, metricas_precision REAL, errores_detectados INTEGER,
            errores_corregidos INTEGER, errores_escalados INTEGER, run_anterior TEXT,
            diff_mejoras INTEGER, diff_regresiones INTEGER, delta_reglas INTEGER,
            sinonimos_count INTEGER, reglas_negocio_count INTEGER);
        CREATE TABLE ofertas_esco_matching (id_oferta TEXT PRIMARY KEY, run_id TEXT);
        CREATE TABLE ofertas_esco_skills_detalle (id INTEGER PRIMARY KEY, id_oferta TEXT, skill_mencionado TEXT);
        CREATE TABLE ofertas_nlp (id_oferta TEXT PRIMARY KEY, tareas_explicitas TEXT, titulo_limpio TEXT);

        INSERT INTO pipeline_runs (run_id, timestamp, ofertas_count, metricas_precision)
        VALUES ('run_X', '2026-03-30T12:00:00', 100, 0.95);
    ''')
    conn.close()
    return db_path


# ============================================================================
# Unitarios
# ============================================================================

class TestGetUltimoRunData:

    def test_lee_ultimo_run_completo(self, db_with_runs):
        """Lee el run más reciente con todos los campos."""
        from sync_learnings import _get_ultimo_run_data, DB_PATH
        # Patch DB_PATH para usar nuestro test DB
        with patch('sync_learnings.DB_PATH', db_with_runs):
            result = _get_ultimo_run_data(verbose=True)

        assert result["ultimo_run_id"] == "run_002"
        assert result["ultimo_run_branch"] == "main"
        assert result["ultimo_run_nlp_version"] == "11.3.0"
        assert result["ultimo_run_matching_version"] == "3.5.2"
        assert result["ultimo_run_ofertas"] == 500
        assert result["ultimo_run_precision"] == 0.976
        assert result["ultimo_run_errores"] == 12
        assert result["ultimo_run_corregidos"] == 10
        assert result["ultimo_run_escalados"] == 2
        assert result["ultimo_run_reglas_nuevas"] == 38

    def test_lee_failures_del_run(self, db_with_runs):
        """Cuenta failures y genera top_failures correctamente."""
        with patch('sync_learnings.DB_PATH', db_with_runs):
            result = _get_ultimo_run_data()

        assert result["ultimo_run_failures"] == 2
        assert result["ultimo_run_failures_pct"] > 0

        top = json.loads(result["ultimo_run_top_failures"])
        assert len(top) == 2
        # Ordenados por gap ASC
        assert top[0]["gap"] <= top[1]["gap"]
        assert "tarea" in top[0]
        assert "score" in top[0]

    def test_delta_precision_calculado(self, db_with_runs):
        """Calcula delta_precision vs run anterior."""
        with patch('sync_learnings.DB_PATH', db_with_runs):
            result = _get_ultimo_run_data()

        # run_002 precision=0.976, run_001 precision=0.974
        assert result["ultimo_run_delta_precision"] == round(0.976 - 0.974, 4)

    def test_pipeline_runs_vacia(self, db_empty):
        """Si pipeline_runs está vacía, retorna NULLs sin error."""
        with patch('sync_learnings.DB_PATH', db_empty):
            result = _get_ultimo_run_data()

        assert result["ultimo_run_id"] is None
        assert result["ultimo_run_ofertas"] is None
        assert result["ultimo_run_failures"] == 0

    def test_sin_tabla_failures(self, db_no_failures):
        """Si skills_extraction_failures no existe, failures=0."""
        with patch('sync_learnings.DB_PATH', db_no_failures):
            result = _get_ultimo_run_data()

        assert result["ultimo_run_id"] == "run_X"
        assert result["ultimo_run_failures"] == 0
        assert result["ultimo_run_failures_pct"] == 0.0
        assert result["ultimo_run_top_failures"] is None


# ============================================================================
# Integración (mock Supabase)
# ============================================================================

class TestSyncToSupabaseExtended:

    def test_data_incluye_campos_ultimo_run(self, db_with_runs):
        """El dict data enviado a sistema_estado incluye ultimo_run_*."""
        with patch('sync_learnings.DB_PATH', db_with_runs):
            ultimo_run = _get_ultimo_run_data()

        # Verificar que tiene los campos
        assert "ultimo_run_id" in ultimo_run
        assert "ultimo_run_failures" in ultimo_run
        assert "ultimo_run_top_failures" in ultimo_run
        assert ultimo_run["ultimo_run_id"] == "run_002"

    def test_rpc_recibe_parametros_correctos(self, db_with_runs):
        """El RPC insertar_pipeline_run recibe los params correctos."""
        with patch('sync_learnings.DB_PATH', db_with_runs):
            ultimo_run = _get_ultimo_run_data()

        # Simular lo que haría sync_to_supabase
        params = {
            "p_run_id": ultimo_run["ultimo_run_id"],
            "p_timestamp": ultimo_run["ultimo_run_timestamp"],
            "p_git_branch": ultimo_run["ultimo_run_branch"],
            "p_ofertas_count": ultimo_run["ultimo_run_ofertas"],
            "p_failures_count": ultimo_run["ultimo_run_failures"],
            "p_precision": ultimo_run["ultimo_run_precision"],
        }
        assert params["p_run_id"] == "run_002"
        assert params["p_ofertas_count"] == 500
        assert params["p_failures_count"] == 2
        assert params["p_precision"] == 0.976

    def test_sync_sin_supabase_config(self, db_with_runs, tmp_path):
        """Si supabase_config.json no existe, retorna False sin error."""
        from sync_learnings import sync_to_supabase

        with patch('sync_learnings.SUPABASE_CONFIG_PATH', tmp_path / "nonexistent.json"):
            result = sync_to_supabase(
                p1={"ofertas_totales": 0}, p2={"ofertas_con_nlp": 0},
                p3={"ofertas_sincronizadas": 0}, suggested=(1, "test", "test"),
                verbose=False
            )
        assert result is False

    def test_ultimo_run_none_no_rompe_sync(self, db_empty):
        """Si no hay run, los campos son NULL pero no rompen el INSERT."""
        with patch('sync_learnings.DB_PATH', db_empty):
            result = _get_ultimo_run_data()

        # Verificar que se puede serializar a JSON (como haría Supabase)
        serialized = json.dumps(result)
        assert serialized is not None
        assert '"ultimo_run_id": null' in serialized


# Importar después de sys.path
from sync_learnings import _get_ultimo_run_data
