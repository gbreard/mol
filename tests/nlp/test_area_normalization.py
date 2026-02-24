#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para normalización de area_funcional en NLPPostprocessor.
===============================================================

Verifica que aliases compuestos se normalizan a valores canónicos
y que valores canónicos pasan sin modificación.
"""

import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.nlp_postprocessor import NLPPostprocessor


@pytest.fixture(scope="module")
def pp():
    return NLPPostprocessor(verbose=False)


def make_data(area: str) -> dict:
    """Datos mínimos para testear _validate_categoricos."""
    return {
        "area_funcional": area,
        "nivel_seniority": "semisenior",
        "tipo_oferta": "demanda_real",
        "titulo_limpio": "Analista",
        "titulo": "Analista",
        "experiencia_min_anios": None,
        "experiencia_max_anios": None,
    }


class TestNormalizationMap:
    """Cada alias compuesto se normaliza al valor canónico."""

    EXPECTED_NORMALIZATIONS = {
        "IT/Sistemas": "IT",
        "Sistemas": "IT",
        "Ventas/Comercial": "Ventas",
        "Recursos Humanos": "RRHH",
        "Finanzas/Contabilidad": "Contabilidad",
        "Logistica/Operaciones": "Logistica",
        "Produccion/Manufactura": "Produccion",
        "Atencion al Cliente": "Atencion al cliente",
    }

    @pytest.mark.parametrize("alias,expected", EXPECTED_NORMALIZATIONS.items())
    def test_normalization(self, pp, alias, expected):
        data = make_data(alias)
        result = pp._validate_categoricos(data)
        assert result["area_funcional"] == expected, \
            f'"{alias}" debería normalizar a "{expected}", obtuvo "{result["area_funcional"]}"'


class TestCanonicalPassthrough:
    """Valores canónicos pasan sin modificación."""

    CANONICAL_VALUES = [
        "IT", "Comercial", "RRHH", "Administracion", "Ventas",
        "Finanzas", "Contabilidad", "Logistica", "Produccion",
        "Ingenieria", "Marketing", "Legal", "Salud", "Operaciones",
        "Seguridad", "Vigilancia", "Atencion al cliente", "Otro",
        "Compras", "Calidad", "Medio ambiente", "Comunicacion",
        "Investigacion", "Gastronomia", "Diseño", "Educacion",
        "Medicina", "Mantenimiento",
    ]

    @pytest.mark.parametrize("area", CANONICAL_VALUES)
    def test_canonical_passthrough(self, pp, area):
        data = make_data(area)
        result = pp._validate_categoricos(data)
        assert result["area_funcional"] == area, \
            f'Canónico "{area}" fue modificado a "{result["area_funcional"]}"'


class TestInvalidValues:
    """Valores no canónicos ni aliases → null."""

    INVALID_VALUES = [
        "Blockchain", "Crypto", "Turismo IT", "Data Science",
        "Customer Success", "DevOps",
    ]

    @pytest.mark.parametrize("area", INVALID_VALUES)
    def test_invalid_to_null(self, pp, area):
        data = make_data(area)
        result = pp._validate_categoricos(data)
        assert result["area_funcional"] is None, \
            f'"{area}" debería ser null, obtuvo "{result["area_funcional"]}"'


class TestNullAndEmpty:
    """Null y vacío no deben causar errores."""

    def test_null_stays_null(self, pp):
        data = make_data(None)
        data["area_funcional"] = None
        result = pp._validate_categoricos(data)
        assert result["area_funcional"] is None

    def test_empty_stays_none(self, pp):
        data = make_data("")
        result = pp._validate_categoricos(data)
        # empty string → no entra en validación (falsy), queda como está
        assert result["area_funcional"] == "" or result["area_funcional"] is None
