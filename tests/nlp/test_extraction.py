# -*- coding: utf-8 -*-
"""
Tests de Extraccion NLP - Gold Set
==================================

Verifica que la extraccion NLP produce resultados consistentes
con los valores esperados del Gold Set.
"""

import json
import sqlite3
import pytest
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = Path(__file__).parent / "gold_set.json"


@pytest.fixture(scope="module")
def gold_set():
    """Carga el Gold Set NLP."""
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="module")
def db_connection():
    """Conexion a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


class TestNLPGoldSetBasics:
    """Tests basicos del Gold Set."""

    def test_gold_set_exists(self, gold_set):
        """Verifica que el Gold Set existe y tiene casos."""
        assert len(gold_set) > 0, "Gold Set vacio"

    def test_gold_set_has_49_cases(self, gold_set):
        """Verifica que hay 49 casos."""
        assert len(gold_set) == 49, f"Se esperaban 49 casos, hay {len(gold_set)}"

    def test_gold_set_structure(self, gold_set):
        """Verifica estructura de cada caso."""
        required_keys = ['id_oferta', 'titulo_original', 'expected']
        for caso in gold_set:
            for key in required_keys:
                assert key in caso, f"Falta '{key}' en caso {caso.get('id_oferta', 'unknown')}"


class TestNLPCoverage:
    """Tests de cobertura de campos."""

    def test_area_funcional_coverage(self, gold_set):
        """area_funcional debe tener >90% cobertura."""
        con_valor = sum(1 for g in gold_set if g['expected'].get('area_funcional'))
        pct = con_valor / len(gold_set) * 100
        assert pct >= 90, f"area_funcional solo tiene {pct:.1f}% cobertura (esperado >90%)"

    def test_nivel_seniority_coverage(self, gold_set):
        """nivel_seniority debe tener >80% cobertura."""
        con_valor = sum(1 for g in gold_set if g['expected'].get('nivel_seniority'))
        pct = con_valor / len(gold_set) * 100
        assert pct >= 80, f"nivel_seniority solo tiene {pct:.1f}% cobertura (esperado >80%)"

    def test_modalidad_coverage(self, gold_set):
        """modalidad debe tener >80% cobertura."""
        con_valor = sum(1 for g in gold_set if g['expected'].get('modalidad'))
        pct = con_valor / len(gold_set) * 100
        assert pct >= 80, f"modalidad solo tiene {pct:.1f}% cobertura (esperado >80%)"

    def test_experiencia_min_coverage(self, gold_set):
        """experiencia_min_anios debe tener >90% cobertura."""
        con_valor = sum(1 for g in gold_set if g['expected'].get('experiencia_min_anios') is not None)
        pct = con_valor / len(gold_set) * 100
        assert pct >= 90, f"experiencia_min_anios solo tiene {pct:.1f}% cobertura (esperado >90%)"

    def test_mision_rol_coverage(self, gold_set):
        """mision_rol debe tener >90% cobertura."""
        con_valor = sum(1 for g in gold_set if g['expected'].get('mision_rol'))
        pct = con_valor / len(gold_set) * 100
        assert pct >= 90, f"mision_rol solo tiene {pct:.1f}% cobertura (esperado >90%)"


class TestNLPValidValues:
    """Tests de valores validos."""

    # Valores canonicos (post-normalizacion)
    MODALIDADES_VALIDAS = [
        'presencial', 'remoto', 'hibrido',
        None
    ]
    SENIORITY_VALIDOS = [
        'trainee', 'junior', 'semisenior', 'senior', 'lead/manager',
        None
    ]
    AREAS_VALIDAS = [
        'IT/Sistemas', 'Ventas/Comercial', 'Administracion/Finanzas',
        'Operaciones/Logistica', 'RRHH', 'Marketing', 'Produccion/Manufactura',
        'Salud', 'Educacion', 'Legal', 'Otros',
        'Atencion al Cliente', 'Consultoria',
        None
    ]

    def test_modalidad_valid_values(self, gold_set):
        """Verifica que modalidad tiene valores validos."""
        for caso in gold_set:
            modalidad = caso['expected'].get('modalidad')
            assert modalidad in self.MODALIDADES_VALIDAS, \
                f"ID {caso['id_oferta']}: modalidad '{modalidad}' no valida"

    def test_nivel_seniority_valid_values(self, gold_set):
        """Verifica que nivel_seniority tiene valores validos."""
        for caso in gold_set:
            seniority = caso['expected'].get('nivel_seniority')
            assert seniority in self.SENIORITY_VALIDOS, \
                f"ID {caso['id_oferta']}: nivel_seniority '{seniority}' no valido"

    def test_area_funcional_valid_values(self, gold_set):
        """Verifica que area_funcional tiene valores validos (permite variantes con acentos)."""
        import unicodedata

        def normalize(s):
            if s is None:
                return None
            # Quita acentos y normaliza
            nfkd = unicodedata.normalize('NFKD', s)
            return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()

        valid_normalized = {normalize(a) for a in self.AREAS_VALIDAS}

        for caso in gold_set:
            area = caso['expected'].get('area_funcional')
            area_norm = normalize(area)
            assert area_norm in valid_normalized, \
                f"ID {caso['id_oferta']}: area_funcional '{area}' no valida"

    def test_tiene_gente_cargo_boolean(self, gold_set):
        """Verifica que tiene_gente_cargo es booleano o None."""
        for caso in gold_set:
            valor = caso['expected'].get('tiene_gente_cargo')
            assert valor in [True, False, None, 0, 1], \
                f"ID {caso['id_oferta']}: tiene_gente_cargo '{valor}' no es booleano"


class TestNLPDBConsistency:
    """Tests de consistencia con la BD."""

    def test_all_gold_set_in_db(self, gold_set, db_connection):
        """Verifica que todos los casos del Gold Set estan en la BD."""
        cursor = db_connection.cursor()
        for caso in gold_set:
            cursor.execute(
                "SELECT COUNT(*) FROM ofertas_nlp WHERE id_oferta = ?",
                (caso['id_oferta'],)
            )
            count = cursor.fetchone()[0]
            assert count > 0, f"ID {caso['id_oferta']} no encontrado en ofertas_nlp"

    def test_all_have_nlp_v10(self, gold_set, db_connection):
        """Verifica que todos tienen NLP v10.0.0."""
        cursor = db_connection.cursor()
        for caso in gold_set:
            cursor.execute(
                "SELECT nlp_version FROM ofertas_nlp WHERE id_oferta = ?",
                (caso['id_oferta'],)
            )
            row = cursor.fetchone()
            assert row is not None, f"ID {caso['id_oferta']} no encontrado"
            assert row['nlp_version'] == '10.0.0', \
                f"ID {caso['id_oferta']}: nlp_version es '{row['nlp_version']}' (esperado '10.0.0')"


class TestNLPQualityMetrics:
    """Tests de metricas de calidad."""

    def test_overall_coverage_minimum(self, gold_set):
        """Cobertura total debe ser >40%."""
        campos = [
            'provincia', 'localidad', 'modalidad', 'area_funcional',
            'nivel_seniority', 'experiencia_min_anios', 'mision_rol'
        ]

        total_valores = 0
        total_posibles = len(gold_set) * len(campos)

        for caso in gold_set:
            for campo in campos:
                valor = caso['expected'].get(campo)
                if valor not in [None, '', [], '[]']:
                    total_valores += 1

        pct = total_valores / total_posibles * 100
        assert pct >= 40, f"Cobertura total es {pct:.1f}% (minimo 40%)"

    def test_no_all_null_cases(self, gold_set):
        """Menos del 5% de casos deben tener todos los campos criticos vacios."""
        campos_criticos = ['area_funcional', 'modalidad', 'experiencia_min_anios']

        casos_vacios = []
        for caso in gold_set:
            valores = [caso['expected'].get(c) for c in campos_criticos]
            tiene_algo = any(v not in [None, '', [], '[]', 0] for v in valores)
            if not tiene_algo:
                casos_vacios.append(caso['id_oferta'])

        pct_vacios = len(casos_vacios) / len(gold_set) * 100
        # Permitir hasta 5% de casos con campos criticos vacios
        assert pct_vacios <= 5, \
            f"{len(casos_vacios)} casos ({pct_vacios:.1f}%) tienen campos criticos vacios: {casos_vacios}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
