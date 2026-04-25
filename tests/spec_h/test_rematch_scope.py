# -*- coding: utf-8 -*-
"""
Tests SPEC H — Selección de scope y estructura de BD.

Usa BD temporal con fixtures. No requiere cargar MatcherV3 (tests puros de
selección SQL).
"""
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'scripts' / 'embeddings'))

# Import funciones del script como módulo
import importlib.util
spec = importlib.util.spec_from_file_location(
    "rematch_spec_h",
    ROOT / "scripts" / "embeddings" / "rematch_isco_spec_h.py"
)
rematch_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rematch_mod)


@pytest.fixture
def db_tmp(tmp_path):
    """BD temporal con schema mínimo + fixtures."""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    # Schema mínimo de ofertas_esco_matching
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
        run_id TEXT,
        skills_semantico_json TEXT
    )''')
    c.execute('''CREATE TABLE ofertas_nlp (
        id_oferta TEXT PRIMARY KEY,
        titulo_limpio TEXT,
        tareas_explicitas TEXT,
        skills_tecnicas_list TEXT,
        soft_skills_list TEXT,
        sector_empresa TEXT,
        nivel_seniority TEXT,
        area_funcional TEXT
    )''')
    c.execute('''CREATE TABLE ofertas (
        id_oferta TEXT PRIMARY KEY,
        titulo TEXT,
        descripcion TEXT
    )''')

    # Fixtures: 10 ofertas con variedad de decision_metodo y estado_validacion
    rows = [
        # Scope SPEC H (debe incluir)
        ('S1', '5120', 'cocinero', '5120.1', 0.62, 0.62, 'semantico_unico', 'validado_claude',  None, None, None, '[]'),
        ('S2', '7214', 'remachador', '7214.3.1', 0.58, 0.58, 'semantico_unico', 'validado_claude', None, None, None, '[]'),
        ('S3', '8142', 'plástico', '8142.1', 0.70, 0.70, 'semantico_unico', 'validado',  None, None, None, '[]'),  # protegida por trigger

        # Fuera de scope
        ('R1', '7214', 'metalúrgico', None, 1.00, 1.00, 'regla_prioridad', 'validado_claude', None, None, None, '[]'),
        ('R2', '8142', 'plástico', None, 1.00, 1.00, 'regla_prioridad', 'validado', None, None, None, '[]'),
        ('D1', '2221', 'enfermera', None, 0.75, 0.75, 'dual_coinciden', 'validado_claude', None, None, None, '[]'),
        ('P1', '3322', 'asesor', None, 0.55, 0.55, 'regla_por_score_bajo', 'validado_claude', None, None, None, '[]'),
        ('Z1', '4120', 'admin', None, 0.60, 0.60, 'regla_zona_gris', 'validado_claude', None, None, None, '[]'),

        # Pendientes o sin skills
        ('PE1', None, None, None, None, None, None, 'pendiente', None, None, None, None),
        ('S4_nosk', '5120', 'cocinero', None, 0.55, 0.55, 'semantico_unico', 'validado_claude', None, None, None, None),  # sin skills
    ]
    c.executemany('''INSERT INTO ofertas_esco_matching VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', rows)
    conn.commit()
    yield conn, str(db)
    conn.close()


class TestEnsureTables:

    def test_crea_tablas_si_no_existen(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        names = {r[0] for r in c.fetchall()}
        assert 'ofertas_matching_backup_spec_h' in names
        assert 'spec_h_rematch_progress' in names


class TestSeleccionarIds:

    def test_piloto_solo_semantico_unico(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        ids = rematch_mod.seleccionar_ids(conn, 'piloto', limit=100)
        # Debe contener S1, S2, S3 pero no R1, R2, D1, P1, Z1, PE1
        assert 'S1' in ids
        assert 'S2' in ids
        assert 'S3' in ids
        assert 'R1' not in ids
        assert 'R2' not in ids
        assert 'D1' not in ids
        assert 'P1' not in ids
        assert 'Z1' not in ids
        assert 'PE1' not in ids

    def test_excluye_sin_skills(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        ids = rematch_mod.seleccionar_ids(conn, 'piloto', limit=100)
        # S4_nosk no tiene skills_semantico_json
        assert 'S4_nosk' not in ids

    def test_excluye_ya_procesadas(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        c = conn.cursor()
        # Marcar S2 como procesada
        c.execute('''INSERT INTO spec_h_rematch_progress
                     (id_oferta, tanda, procesada_at, resultado)
                     VALUES ('S2', 'piloto', '2026-01-01', 'actualizada')''')
        conn.commit()
        ids = rematch_mod.seleccionar_ids(conn, 'piloto', limit=100)
        assert 'S1' in ids
        assert 'S2' not in ids  # excluida
        assert 'S3' in ids

    def test_extra_ids_tambien_excluye_procesadas(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        c = conn.cursor()
        c.execute('''INSERT INTO spec_h_rematch_progress
                     (id_oferta, tanda, procesada_at, resultado)
                     VALUES ('S1', 'ids', '2026-01-01', 'actualizada')''')
        conn.commit()
        ids = rematch_mod.seleccionar_ids(conn, 'ids', extra_ids=['S1', 'S2'])
        assert 'S1' not in ids
        assert 'S2' in ids

    def test_resto_incluye_todas_pendientes(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        ids = rematch_mod.seleccionar_ids(conn, 'resto')
        # Debe incluir S1, S2, S3 (todas pendientes del scope)
        assert set(ids) >= {'S1', 'S2', 'S3'}
        # Y no las fuera de scope
        assert not any(i in ids for i in ('R1','R2','D1','P1','Z1','PE1','S4_nosk'))

    def test_limit_se_respeta(self, db_tmp):
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        ids = rematch_mod.seleccionar_ids(conn, 'piloto', limit=2)
        assert len(ids) <= 2


class TestGetEstadoActual:

    def test_retorna_estado_completo(self, db_tmp):
        conn, _ = db_tmp
        estado = rematch_mod.get_estado_actual(conn, 'S1')
        assert estado is not None
        assert estado['isco_code'] == '5120'
        assert estado['esco_occupation_label'] == 'cocinero'
        assert estado['score_semantico'] == 0.62
        assert estado['decision_metodo'] == 'semantico_unico'
        assert estado['estado_validacion'] == 'validado_claude'

    def test_retorna_none_si_no_existe(self, db_tmp):
        conn, _ = db_tmp
        assert rematch_mod.get_estado_actual(conn, 'NOEXISTE') is None


class TestGetOfertaNlp:

    def test_retorna_dict_con_campos(self, db_tmp):
        conn, _ = db_tmp
        c = conn.cursor()
        c.execute('''INSERT INTO ofertas_nlp VALUES
                     ('S1', 'Cocinero/a', 'preparar platos; cocinar',
                      'cocinar', 'trabajar en equipo', 'Gastronomia', 'junior', 'Cocina')''')
        c.execute('''INSERT INTO ofertas VALUES ('S1', 'Cocinero para restaurante', 'buena descripcion')''')
        conn.commit()
        nlp = rematch_mod.get_oferta_nlp(conn, 'S1')
        assert nlp['titulo_limpio'] == 'Cocinero/a'
        assert nlp['tareas_explicitas'] == 'preparar platos; cocinar'
        assert nlp['sector_empresa'] == 'Gastronomia'
        assert nlp['nivel_seniority'] == 'junior'

    def test_retorna_none_si_no_existe_nlp(self, db_tmp):
        conn, _ = db_tmp
        assert rematch_mod.get_oferta_nlp(conn, 'NOEXISTE') is None


class TestSnapshotBackup:

    def test_backup_guarda_estado_original(self, db_tmp):
        """Simular escritura al backup y verificar campos."""
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        c = conn.cursor()
        c.execute('''INSERT INTO ofertas_matching_backup_spec_h (
                     id_oferta, isco_code_antes, esco_occupation_label_antes,
                     titulo_esco_code_antes, score_semantico_antes,
                     decision_metodo_antes, estado_validacion_antes,
                     matching_timestamp_antes, backup_at)
                     VALUES ('S1', '5120', 'cocinero', '5120.1', 0.62,
                             'semantico_unico', 'validado_claude',
                             NULL, '2026-04-25T03:00:00Z')''')
        conn.commit()
        c.execute('SELECT * FROM ofertas_matching_backup_spec_h WHERE id_oferta=?', ('S1',))
        row = c.fetchone()
        assert row is not None
        assert row[1] == '5120'
        assert row[2] == 'cocinero'

    def test_insert_or_ignore_no_pisa_backup_existente(self, db_tmp):
        """Si backup ya existe para una oferta, segundo INSERT OR IGNORE no sobreescribe."""
        conn, _ = db_tmp
        rematch_mod.ensure_tables(conn)
        c = conn.cursor()
        # Primer insert
        c.execute('''INSERT OR IGNORE INTO ofertas_matching_backup_spec_h
                     (id_oferta, isco_code_antes, backup_at)
                     VALUES ('S1', '5120', '2026-04-25')''')
        # Segundo intento con ISCO distinto → debe ser ignorado
        c.execute('''INSERT OR IGNORE INTO ofertas_matching_backup_spec_h
                     (id_oferta, isco_code_antes, backup_at)
                     VALUES ('S1', '9999', '2026-04-26')''')
        conn.commit()
        c.execute('SELECT isco_code_antes FROM ofertas_matching_backup_spec_h WHERE id_oferta=?', ('S1',))
        assert c.fetchone()[0] == '5120'  # preservado el original
