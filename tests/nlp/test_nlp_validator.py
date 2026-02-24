#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para NLPValidator (database/nlp_validator.py v1.1.0)
==========================================================

Tests unitarios sin BD: validar_oferta, validar_lote, extraction report,
campos calculados, gate blocking.
"""

import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.nlp_validator import NLPValidator


@pytest.fixture(scope="module")
def validator():
    return NLPValidator(verbose=False)


def oferta_limpia() -> dict:
    """Oferta completa que pasa TODAS las reglas."""
    return {
        "id_oferta": 1000,
        "titulo_limpio": "Analista de Sistemas",
        "provincia": "Buenos Aires",
        "localidad": "CABA",
        "sector_empresa": "Tecnologia",
        "area_funcional": "IT",
        "nivel_seniority": "semisenior",
        "modalidad": "remoto",
        "tipo_oferta": "demanda_real",
        "tareas_explicitas": "Desarrollar sistemas; Mantener bases de datos; Documentar APIs",
        "skills_count": 8,
        "skills_origen_tarea_count": 5,
        "descripcion_length": 500,
        "clae_code": "6201",
        "clae_seccion": "J",
        "es_intermediario": 0,
        "sector_confianza": "alta",
        "sector_fuente": "scraping",
        "experiencia_min_anios": 3,
        "experiencia_max_anios": 5,
        "jornada_laboral": "full-time",
        "tipo_contrato": "efectivo",
        "tiene_gente_cargo": 0,
        "nivel_educativo": "universitario",
        "empresa": "TechCorp SA",
    }


def oferta_con_gate_block() -> dict:
    """Oferta que debe ser BLOQUEADA (titulo vacio = critico)."""
    o = oferta_limpia()
    o["id_oferta"] = 2000
    o["titulo_limpio"] = ""
    return o


def oferta_con_warnings() -> dict:
    """Oferta que pasa gate pero tiene warnings/medio."""
    o = oferta_limpia()
    o["id_oferta"] = 3000
    o["skills_count"] = 2  # V03: medio
    o["provincia"] = ""  # V12: medio
    return o


def oferta_incompleta() -> dict:
    """Oferta con muchos campos vacíos — para extraction report."""
    return {
        "id_oferta": 4000,
        "titulo_limpio": "Vendedor",
        "provincia": None,
        "localidad": None,
        "sector_empresa": None,
        "area_funcional": None,
        "nivel_seniority": None,
        "modalidad": "presencial",
        "tipo_oferta": "demanda_real",
        "tareas_explicitas": "",
        "skills_count": 0,
        "descripcion_length": 80,
        "clae_code": None,
        "clae_seccion": None,
        "es_intermediario": 0,
        "experiencia_min_anios": None,
        "experiencia_max_anios": None,
        "jornada_laboral": None,
        "tipo_contrato": None,
        "tiene_gente_cargo": 0,
        "nivel_educativo": None,
        "empresa": "Empresa Desconocida",
    }


# ============================================================================
# Tests: validar_oferta
# ============================================================================

class TestValidarOferta:
    """Tests para NLPValidator.validar_oferta()."""

    def test_oferta_limpia_pasa_gate(self, validator):
        result = validator.validar_oferta(oferta_limpia())
        assert result["gate_pass"] is True
        assert result["gate_blocked_by"] == []

    def test_oferta_limpia_sin_errores(self, validator):
        result = validator.validar_oferta(oferta_limpia())
        assert len(result["errores"]) == 0

    def test_titulo_vacio_bloquea_gate(self, validator):
        result = validator.validar_oferta(oferta_con_gate_block())
        assert result["gate_pass"] is False
        assert "V01_titulo_limpio_vacio" in result["gate_blocked_by"]

    def test_tareas_vacias_no_bloquea_gate(self, validator):
        """NV08 bajó a medio en Sprint 7 — ya no bloquea gate."""
        o = oferta_limpia()
        o["tareas_explicitas"] = ""
        o["skills_count"] = 0
        result = validator.validar_oferta(o)
        assert result["gate_pass"] is True
        errores_ids = [e["id_regla"] for e in result["errores"]]
        assert "NV08_sin_tareas_ni_skills" in errores_ids

    def test_sector_null_like_bloquea(self, validator):
        o = oferta_limpia()
        o["sector_empresa"] = "null"
        result = validator.validar_oferta(o)
        assert result["gate_pass"] is False
        assert "NV11_sector_null_like" in result["gate_blocked_by"]

    def test_seniority_invalido_bloquea(self, validator):
        o = oferta_limpia()
        o["nivel_seniority"] = "semi_senior"
        result = validator.validar_oferta(o)
        assert result["gate_pass"] is False
        assert "NV04_seniority_invalido" in result["gate_blocked_by"]

    def test_warnings_no_bloquean_gate(self, validator):
        result = validator.validar_oferta(oferta_con_warnings())
        assert result["gate_pass"] is True
        assert len(result["errores"]) >= 2  # al menos V03 + V12

    def test_errores_tienen_estructura(self, validator):
        result = validator.validar_oferta(oferta_con_gate_block())
        assert len(result["errores"]) > 0
        error = result["errores"][0]
        assert "id_regla" in error
        assert "diagnostico" in error
        assert "severidad" in error
        assert "mensaje" in error

    def test_multiple_gate_blocks(self, validator):
        """Oferta con multiples errores critico/alto."""
        o = oferta_limpia()
        o["titulo_limpio"] = ""  # V01 critico
        o["nivel_seniority"] = "semi_senior"  # NV04 alto
        result = validator.validar_oferta(o)
        assert result["gate_pass"] is False
        assert len(result["gate_blocked_by"]) >= 2


# ============================================================================
# Tests: computed fields
# ============================================================================

class TestComputedFields:
    """Tests para _enrich_computed_fields."""

    def test_sector_coincide_area(self, validator):
        o = {"sector_empresa": "IT", "area_funcional": "IT"}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["sector_coincide_area"] is True

    def test_sector_no_coincide_area(self, validator):
        o = {"sector_empresa": "Tecnologia", "area_funcional": "RRHH"}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["sector_coincide_area"] is False

    def test_tareas_explicitas_length(self, validator):
        o = {"tareas_explicitas": "Tarea uno; Tarea dos"}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["tareas_explicitas_length"] == 20

    def test_tareas_explicitas_length_vacia(self, validator):
        o = {"tareas_explicitas": ""}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["tareas_explicitas_length"] == 0

    def test_experiencia_rango_invertido(self, validator):
        o = {"experiencia_min_anios": 5, "experiencia_max_anios": 3}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["experiencia_rango_invertido"] is True

    def test_experiencia_rango_normal(self, validator):
        o = {"experiencia_min_anios": 2, "experiencia_max_anios": 5}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["experiencia_rango_invertido"] is False

    def test_experiencia_rango_sin_max(self, validator):
        o = {"experiencia_min_anios": 3, "experiencia_max_anios": None}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["experiencia_rango_invertido"] is False

    def test_skills_count_from_list(self, validator):
        o = {"skills_tecnicas_list": "Python;React;SQL"}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["skills_count"] == 3

    def test_skills_count_from_empty_list(self, validator):
        o = {"skills_tecnicas_list": ""}
        enriched = validator._enrich_computed_fields(o)
        assert enriched["skills_count"] == 0


# ============================================================================
# Tests: validar_lote
# ============================================================================

class TestValidarLote:
    """Tests para NLPValidator.validar_lote()."""

    def test_lote_estructura(self, validator):
        result = validator.validar_lote([oferta_limpia()])
        assert "total" in result
        assert "gate_pass_count" in result
        assert "gate_block_count" in result
        assert "ids_aprobados" in result
        assert "ids_bloqueados" in result
        assert "errores_detalle" in result
        assert "extraction_report" in result

    def test_lote_una_limpia(self, validator):
        result = validator.validar_lote([oferta_limpia()])
        assert result["total"] == 1
        assert result["gate_pass_count"] == 1
        assert result["gate_block_count"] == 0
        assert 1000 in result["ids_aprobados"]

    def test_lote_una_bloqueada(self, validator):
        result = validator.validar_lote([oferta_con_gate_block()])
        assert result["total"] == 1
        assert result["gate_pass_count"] == 0
        assert result["gate_block_count"] == 1
        assert 2000 in result["ids_bloqueados"]

    def test_lote_mixto(self, validator):
        ofertas = [oferta_limpia(), oferta_con_gate_block(), oferta_con_warnings()]
        result = validator.validar_lote(ofertas)
        assert result["total"] == 3
        assert result["gate_pass_count"] == 2  # limpia + warnings
        assert result["gate_block_count"] == 1  # titulo vacio
        assert 1000 in result["ids_aprobados"]
        assert 2000 in result["ids_bloqueados"]
        assert 3000 in result["ids_aprobados"]

    def test_errores_por_severidad(self, validator):
        result = validator.validar_lote([oferta_con_gate_block()])
        assert "critico" in result["errores_por_severidad"]

    def test_lote_vacio(self, validator):
        result = validator.validar_lote([])
        assert result["total"] == 0
        assert result["gate_pass_count"] == 0
        assert result["gate_block_count"] == 0


# ============================================================================
# Tests: extraction report
# ============================================================================

class TestExtractionReport:
    """Tests para NLPValidator.get_extraction_report()."""

    def test_report_estructura(self, validator):
        report = validator.get_extraction_report([oferta_limpia()])
        assert "field_completeness" in report
        assert "value_distributions" in report
        assert "summary" in report

    def test_report_completeness_full(self, validator):
        report = validator.get_extraction_report([oferta_limpia()])
        fc = report["field_completeness"]
        # titulo_limpio debería tener 100%
        assert fc["titulo_limpio"]["pct_filled"] == 100.0

    def test_report_completeness_partial(self, validator):
        report = validator.get_extraction_report([oferta_limpia(), oferta_incompleta()])
        fc = report["field_completeness"]
        # provincia: 1 de 2 = 50%
        assert fc["provincia"]["pct_filled"] == 50.0

    def test_report_distributions(self, validator):
        report = validator.get_extraction_report([oferta_limpia(), oferta_limpia()])
        dist = report["value_distributions"]
        # sector_empresa debería tener Tecnologia: 2
        assert dist.get("sector_empresa", {}).get("Tecnologia") == 2

    def test_report_summary_below_50(self, validator):
        report = validator.get_extraction_report([oferta_incompleta()])
        # Muchos campos vacíos → below_50pct debería tener items
        assert len(report["summary"]["below_50pct"]) > 0

    def test_report_empty_input(self, validator):
        report = validator.get_extraction_report([])
        assert report["field_completeness"] == {}


# ============================================================================
# Tests: version y config
# ============================================================================

class TestVersionConfig:

    def test_version(self, validator):
        assert validator.VERSION == "1.1.0"

    def test_gate_severities(self, validator):
        assert validator.GATE_SEVERITIES == {"critico", "alto"}

    def test_rules_loaded(self, validator):
        assert len(validator.rules_config.get("reglas", [])) == 35
