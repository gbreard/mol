# -*- coding: utf-8 -*-
"""
M-08b Parte 2: Tests de detección de candidatos a equivalencia.
"""
import pytest
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def db_candidates(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript('''
        CREATE TABLE ofertas_esco_skills_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oferta TEXT, skill_mencionado TEXT, skill_tipo_fuente TEXT,
            esco_skill_uri TEXT, esco_skill_label TEXT, match_score REAL,
            match_method TEXT, esco_skill_type TEXT, source_classification TEXT,
            texto_original TEXT
        );
    ''')
    return db_path, conn


class TestCandidateDetection:

    def test_candidato_detectado(self, db_candidates):
        db_path, conn = db_candidates
        # 6 ofertas: "CRM" y "sistema CRM" matchean misma URI
        for i in range(6):
            conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                VALUES (?, 'uri_crm', 'gestionar relaciones', 'crm', 'tecnologia_declarada', 0.42)''',
                (f'oferta_{i}',))
            conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                VALUES (?, 'uri_crm', 'gestionar relaciones', 'sistema crm', 'herramienta_declarada', 0.44)''',
                (f'oferta_{i}',))
        conn.commit()
        conn.close()

        from generate_equiv_candidates import detect_candidates
        from unittest.mock import patch
        with patch('generate_equiv_candidates.DB_PATH', db_path):
            candidates = detect_candidates(min_co=5, verbose=False)

        assert len(candidates) >= 1
        c = candidates[0]
        assert c["uri_esco"] == "uri_crm"
        assert "crm" in c["termino_a"] or "crm" in c["termino_b"]

    def test_bajo_umbral_no_detectado(self, db_candidates):
        db_path, conn = db_candidates
        # Solo 3 ofertas — bajo mínimo de 5
        for i in range(3):
            conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                VALUES (?, 'uri_x', 'skill_x', 'term_a', 'tecnologia_declarada', 0.45)''',
                (f'oferta_{i}',))
            conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                VALUES (?, 'uri_x', 'skill_x', 'term_b', 'tecnologia_declarada', 0.43)''',
                (f'oferta_{i}',))
        conn.commit()
        conn.close()

        from generate_equiv_candidates import detect_candidates
        from unittest.mock import patch
        with patch('generate_equiv_candidates.DB_PATH', db_path):
            candidates = detect_candidates(min_co=5, verbose=False)

        assert len(candidates) == 0

    def test_texto_null_ignorado(self, db_candidates):
        db_path, conn = db_candidates
        for i in range(10):
            conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                VALUES (?, 'uri_y', 'skill_y', NULL, 'tarea', 0.50)''',
                (f'oferta_{i}',))
        conn.commit()
        conn.close()

        from generate_equiv_candidates import detect_candidates
        from unittest.mock import patch
        with patch('generate_equiv_candidates.DB_PATH', db_path):
            candidates = detect_candidates(min_co=5, verbose=False)

        assert len(candidates) == 0

    def test_un_solo_texto_no_candidato(self, db_candidates):
        db_path, conn = db_candidates
        for i in range(10):
            conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                VALUES (?, 'uri_z', 'skill_z', 'siempre el mismo', 'tarea', 0.55)''',
                (f'oferta_{i}',))
        conn.commit()
        conn.close()

        from generate_equiv_candidates import detect_candidates
        from unittest.mock import patch
        with patch('generate_equiv_candidates.DB_PATH', db_path):
            candidates = detect_candidates(min_co=5, verbose=False)

        assert len(candidates) == 0

    def test_tres_textos_genera_pares(self, db_candidates):
        db_path, conn = db_candidates
        textos = ["excel", "microsoft excel", "ms excel"]
        for i in range(7):
            for t in textos:
                conn.execute('''INSERT INTO ofertas_esco_skills_detalle
                    (id_oferta, esco_skill_uri, esco_skill_label, texto_original, skill_tipo_fuente, match_score)
                    VALUES (?, 'uri_excel', 'utilizar Microsoft Office', ?, 'tecnologia_declarada', 0.48)''',
                    (f'oferta_{i}', t))
        conn.commit()
        conn.close()

        from generate_equiv_candidates import detect_candidates
        from unittest.mock import patch
        with patch('generate_equiv_candidates.DB_PATH', db_path):
            candidates = detect_candidates(min_co=5, verbose=False)

        # 3 textos → 3 pares: excel↔microsoft excel, excel↔ms excel, microsoft excel↔ms excel
        assert len(candidates) == 3
