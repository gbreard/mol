#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para reglas NLP Validation (config/nlp_validation_rules.json v1.1.0)
==========================================================================

Verifica que cada regla:
1. DISPARA con datos que deberían activarla (positivo)
2. NO DISPARA con datos limpios (negativo)

Usa la misma lógica de evaluación de auto_validator.py para evaluar las reglas
contra ofertas sintéticas.
"""

import json
import re
import sys
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


# ============================================================================
# MINI-EVALUADOR (replica lógica de auto_validator sin depender de la clase)
# ============================================================================

_regex_cache = {}


def _get_compiled_pattern(pattern_str: str):
    """Cache de patrones regex compilados."""
    if pattern_str not in _regex_cache:
        _regex_cache[pattern_str] = re.compile(pattern_str)
    return _regex_cache[pattern_str]


def evaluar_operador(valor: Any, operador: str, valor_esperado: Any = None, valores: list = None) -> bool:
    """Evalúa un operador contra un valor. Replica auto_validator._evaluar_operador."""
    if operador == "is_null":
        return valor is None
    elif operador == "is_not_null":
        return valor is not None
    elif operador == "is_empty":
        if valor is None:
            return True
        if isinstance(valor, str):
            return valor.strip() == ""
        if isinstance(valor, (list, dict)):
            return len(valor) == 0
        return False
    elif operador == "is_not_empty":
        if valor is None:
            return False
        if isinstance(valor, str):
            return valor.strip() != ""
        if isinstance(valor, (list, dict)):
            return len(valor) > 0
        return True
    elif operador == "eq":
        return valor == valor_esperado
    elif operador == "neq":
        return valor != valor_esperado
    elif operador == "lt":
        try:
            return float(valor) < float(valor_esperado) if valor is not None else False
        except (TypeError, ValueError):
            return False
    elif operador == "gt":
        try:
            return float(valor) > float(valor_esperado) if valor is not None else False
        except (TypeError, ValueError):
            return False
    elif operador == "lte":
        try:
            return float(valor) <= float(valor_esperado) if valor is not None else False
        except (TypeError, ValueError):
            return False
    elif operador == "gte":
        try:
            return float(valor) >= float(valor_esperado) if valor is not None else False
        except (TypeError, ValueError):
            return False
    elif operador == "contains":
        if valor is None:
            return False
        return str(valor_esperado).lower() in str(valor).lower()
    elif operador == "not_contains":
        if valor is None:
            return True
        return str(valor_esperado).lower() not in str(valor).lower()
    elif operador == "contains_any":
        if valor is None or valores is None:
            return False
        valor_str = str(valor).lower()
        return any(str(v).lower() in valor_str for v in valores)
    elif operador == "contains_all":
        if valor is None or valores is None:
            return False
        valor_str = str(valor).lower()
        return all(str(v).lower() in valor_str for v in valores)
    elif operador == "matches_regex":
        if valor is None:
            return False
        try:
            pattern = _get_compiled_pattern(valor_esperado)
            return bool(pattern.search(str(valor)))
        except re.error:
            return False
    elif operador == "in_list":
        return valor in (valores or [])
    elif operador == "not_in_list":
        return valor not in (valores or [])
    return False


def evaluar_regla(oferta: dict, regla: dict) -> bool:
    """Evalúa si una regla aplica a una oferta."""
    if "condiciones" in regla:
        condiciones = regla["condiciones"]
        logica = regla.get("logica", "AND").upper()
        resultados = []
        for cond in condiciones:
            campo = cond["campo"]
            operador = cond["operador"]
            valor = oferta.get(campo)
            resultado = evaluar_operador(
                valor=valor,
                operador=operador,
                valor_esperado=cond.get("valor"),
                valores=cond.get("valores")
            )
            resultados.append(resultado)
        if logica == "AND":
            return all(resultados)
        return any(resultados)
    else:
        campo = regla["campo"]
        operador = regla["operador"]
        valor = oferta.get(campo)
        return evaluar_operador(
            valor=valor,
            operador=operador,
            valor_esperado=regla.get("valor"),
            valores=regla.get("valores")
        )


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def reglas():
    """Carga reglas desde nlp_validation_rules.json."""
    path = CONFIG_DIR / "nlp_validation_rules.json"
    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return {r["id"]: r for r in config["reglas"]}


@pytest.fixture(scope="module")
def config():
    """Carga config completa."""
    path = CONFIG_DIR / "nlp_validation_rules.json"
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def oferta_base() -> dict:
    """Oferta limpia que NO debería disparar ninguna regla."""
    return {
        "id_oferta": 999,
        "titulo_limpio": "Analista de Sistemas",
        "provincia": "Buenos Aires",
        "localidad": "CABA",
        "sector_empresa": "Tecnologia",
        "area_funcional": "IT",
        "nivel_seniority": "semisenior",
        "modalidad": "remoto",
        "tipo_oferta": "demanda_real",
        "tareas_explicitas": "Desarrollar sistemas web; Mantener bases de datos; Documentar APIs",
        "tareas_explicitas_length": 70,
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
        "experiencia_rango_invertido": False,
        "jornada_laboral": "full-time",
        "tipo_contrato": "efectivo",
        "tiene_gente_cargo": 0,
        "nivel_educativo": "universitario",
        "empresa": "TechCorp SA",
        "sector_coincide_area": False,
        "requerimiento_edad": None,
        "requerimiento_sexo": None,
    }


# ============================================================================
# META-TESTS: Integridad de la configuración
# ============================================================================

class TestConfigIntegridad:
    """Verifica integridad estructural del JSON de reglas."""

    def test_version(self, config):
        assert config["version"] == "1.1.0"

    def test_reglas_count(self, config):
        """v1.1.0 tiene 35 reglas."""
        assert len(config["reglas"]) == 35

    def test_ids_unicos(self, config):
        ids = [r["id"] for r in config["reglas"]]
        assert len(ids) == len(set(ids)), f"IDs duplicados: {[x for x in ids if ids.count(x) > 1]}"

    def test_severidades_validas(self, config):
        severidades_validas = set(config["severidades"].keys())
        for regla in config["reglas"]:
            assert regla["severidad"] in severidades_validas, \
                f'{regla["id"]}: severidad "{regla["severidad"]}" no válida'

    def test_gate_severities(self, config):
        """critico y alto deben bloquear gate."""
        assert config["severidades"]["critico"]["bloquea_gate"] is True
        assert config["severidades"]["alto"]["bloquea_gate"] is True
        assert config["severidades"]["medio"]["bloquea_gate"] is False

    def test_cada_regla_tiene_grupo(self, config):
        for regla in config["reglas"]:
            assert "grupo" in regla, f'{regla["id"]}: falta campo "grupo"'

    def test_cada_regla_tiene_diagnostico(self, config):
        for regla in config["reglas"]:
            assert "diagnostico" in regla, f'{regla["id"]}: falta campo "diagnostico"'

    def test_no_hay_reglas_exterior(self, config):
        """V04/V05/V06 fueron eliminadas en v1.1."""
        ids = [r["id"] for r in config["reglas"]]
        assert "V04_localidad_paraguay" not in ids
        assert "V05_localidad_uruguay" not in ids
        assert "V06_localidad_chile" not in ids

    def test_no_hay_tareas_inferidas(self, config):
        """tareas_inferidas fue eliminada del sistema en v1.1 (no debe usarse en campo/condiciones)."""
        for regla in config["reglas"]:
            # Verificar campo principal
            if "campo" in regla:
                assert regla["campo"] != "tareas_inferidas", \
                    f'{regla["id"]}: usa tareas_inferidas como campo'
            # Verificar condiciones
            for cond in regla.get("condiciones", []):
                assert cond.get("campo") != "tareas_inferidas", \
                    f'{regla["id"]}: usa tareas_inferidas en condiciones'

    def test_no_nv_clae_incoherente(self, config):
        """NV_CLAE_sector_incoherente eliminada en v1.1."""
        ids = [r["id"] for r in config["reglas"]]
        assert "NV_CLAE_sector_incoherente" not in ids


# ============================================================================
# TESTS: Oferta base no dispara ninguna regla
# ============================================================================

class TestOfertaBaseLimpia:
    """La oferta base (datos completos y válidos) NO debe disparar ninguna regla."""

    def test_ninguna_regla_dispara(self, reglas):
        base = oferta_base()
        for rule_id, regla in reglas.items():
            resultado = evaluar_regla(base, regla)
            assert not resultado, \
                f'Regla {rule_id} disparó con oferta limpia (severidad: {regla["severidad"]})'


# ============================================================================
# TESTS: Cada regla dispara con datos positivos
# ============================================================================

class TestReglasPositivas:
    """Cada regla DEBE disparar con datos que activan su condición."""

    # --- TITULOS ---

    def test_V01_titulo_limpio_vacio(self, reglas):
        o = oferta_base()
        o["titulo_limpio"] = ""
        assert evaluar_regla(o, reglas["V01_titulo_limpio_vacio"])

    def test_V01_titulo_limpio_none(self, reglas):
        o = oferta_base()
        o["titulo_limpio"] = None
        assert evaluar_regla(o, reglas["V01_titulo_limpio_vacio"])

    def test_V07_titulo_codigo_interno(self, reglas):
        o = oferta_base()
        o["titulo_limpio"] = "AB123 Analista de Sistemas"
        assert evaluar_regla(o, reglas["V07_titulo_codigo_interno"])

    def test_V07_no_dispara_tech_terms(self, reglas):
        """Términos técnicos como IT, SAP, AWS NO deben disparar V07."""
        o = oferta_base()
        for term in ["IT Support", "SAP Consultant", "AWS Engineer", "QA Tester", "UX Designer"]:
            o["titulo_limpio"] = term
            assert not evaluar_regla(o, reglas["V07_titulo_codigo_interno"]), \
                f'V07 disparó con término técnico: {term}'

    # --- SKILLS ---

    def test_V03_skills_insuficientes(self, reglas):
        o = oferta_base()
        o["skills_count"] = 2
        assert evaluar_regla(o, reglas["V03_skills_insuficientes"])

    def test_V03_no_dispara_con_3(self, reglas):
        o = oferta_base()
        o["skills_count"] = 3
        assert not evaluar_regla(o, reglas["V03_skills_insuficientes"])

    def test_V13_skills_sin_origen_tarea(self, reglas):
        o = oferta_base()
        o["skills_origen_tarea_count"] = 0
        assert evaluar_regla(o, reglas["V13_skills_sin_origen_tarea"])

    # --- CLASIFICACION ---

    def test_V08_area_funcional_nula(self, reglas):
        o = oferta_base()
        o["area_funcional"] = None
        assert evaluar_regla(o, reglas["V08_area_funcional_nula"])

    def test_V09_seniority_nulo(self, reglas):
        o = oferta_base()
        o["nivel_seniority"] = None
        assert evaluar_regla(o, reglas["V09_seniority_nulo"])

    def test_V15_seniority_titulo_mismatch(self, reglas):
        o = oferta_base()
        o["nivel_seniority"] = None
        o["titulo_limpio"] = "Gerente de Ventas"
        assert evaluar_regla(o, reglas["V15_seniority_titulo_mismatch"])

    def test_V15_no_dispara_si_seniority_presente(self, reglas):
        o = oferta_base()
        o["nivel_seniority"] = "manager"
        o["titulo_limpio"] = "Gerente de Ventas"
        assert not evaluar_regla(o, reglas["V15_seniority_titulo_mismatch"])

    def test_NV03_area_funcional_invalida(self, reglas):
        o = oferta_base()
        o["area_funcional"] = "Sistemas de Información"
        assert evaluar_regla(o, reglas["NV03_area_funcional_invalida"])

    def test_NV03_no_dispara_area_valida(self, reglas):
        o = oferta_base()
        for area in ["IT", "Comercial", "Administracion", "RRHH", "Ventas"]:
            o["area_funcional"] = area
            assert not evaluar_regla(o, reglas["NV03_area_funcional_invalida"]), \
                f'NV03 disparó con area válida: {area}'

    def test_NV04_seniority_invalido(self, reglas):
        o = oferta_base()
        o["nivel_seniority"] = "semi_senior"
        assert evaluar_regla(o, reglas["NV04_seniority_invalido"])

    def test_NV04_no_dispara_seniority_valido(self, reglas):
        o = oferta_base()
        for s in ["trainee", "junior", "semisenior", "senior", "lead", "manager", "director"]:
            o["nivel_seniority"] = s
            assert not evaluar_regla(o, reglas["NV04_seniority_invalido"]), \
                f'NV04 disparó con seniority válido: {s}'

    def test_NV06_tipo_oferta_invalido(self, reglas):
        o = oferta_base()
        o["tipo_oferta"] = "contrato_temporal"
        assert evaluar_regla(o, reglas["NV06_tipo_oferta_invalido"])

    def test_NV_CROSS_gente_seniority(self, reglas):
        o = oferta_base()
        o["tiene_gente_cargo"] = 1
        o["nivel_seniority"] = "junior"
        assert evaluar_regla(o, reglas["NV_CROSS_gente_seniority"])

    def test_NV_CROSS_no_dispara_con_senior(self, reglas):
        o = oferta_base()
        o["tiene_gente_cargo"] = 1
        o["nivel_seniority"] = "senior"
        assert not evaluar_regla(o, reglas["NV_CROSS_gente_seniority"])

    # --- TAREAS ---

    def test_V11_tareas_vacias(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = ""
        assert evaluar_regla(o, reglas["V11_tareas_vacias"])

    def test_V25_tareas_vacias_con_skills(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = ""
        o["skills_count"] = 5
        assert evaluar_regla(o, reglas["V25_tareas_vacias_con_skills"])

    def test_V25_no_dispara_con_tareas(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = "Desarrollar software; Testear código"
        o["skills_count"] = 5
        assert not evaluar_regla(o, reglas["V25_tareas_vacias_con_skills"])

    def test_V26_formato_tareas_comas(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = "Atender clientes, Vender productos, Hacer reportes"
        assert evaluar_regla(o, reglas["V26_formato_tareas_incorrecto"])

    def test_V26_no_dispara_con_punto_y_coma(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = "Atender clientes; Vender productos; Hacer reportes"
        assert not evaluar_regla(o, reglas["V26_formato_tareas_incorrecto"])

    def test_V29_tareas_muy_cortas(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = "Vender; Cobrar"
        o["tareas_explicitas_length"] = 15
        assert evaluar_regla(o, reglas["V29_tareas_muy_cortas"])

    def test_V14_descripcion_muy_corta(self, reglas):
        o = oferta_base()
        o["descripcion_length"] = 50
        assert evaluar_regla(o, reglas["V14_descripcion_muy_corta"])

    def test_NV08_sin_tareas_ni_skills(self, reglas):
        o = oferta_base()
        o["tareas_explicitas"] = ""
        o["skills_count"] = 0
        assert evaluar_regla(o, reglas["NV08_sin_tareas_ni_skills"])

    # --- UBICACION ---

    def test_V12_provincia_vacia(self, reglas):
        o = oferta_base()
        o["provincia"] = ""
        assert evaluar_regla(o, reglas["V12_provincia_vacia"])

    def test_NV_PROV_invalida(self, reglas):
        o = oferta_base()
        o["provincia"] = "Asuncion"
        assert evaluar_regla(o, reglas["NV_PROV_invalida"])

    def test_NV_PROV_no_dispara_provincias_argentinas(self, reglas):
        o = oferta_base()
        provincias = [
            "Buenos Aires", "Capital Federal", "CABA",
            "Córdoba", "Cordoba", "Santa Fe", "Mendoza",
            "Tucumán", "Tucuman", "Neuquén", "Neuquen",
        ]
        for prov in provincias:
            o["provincia"] = prov
            assert not evaluar_regla(o, reglas["NV_PROV_invalida"]), \
                f'NV_PROV_invalida disparó con provincia argentina: {prov}'

    def test_NV_MOD_invalida(self, reglas):
        o = oferta_base()
        o["modalidad"] = "semi-presencial"
        assert evaluar_regla(o, reglas["NV_MOD_invalida"])

    def test_NV_MOD_no_dispara_validas(self, reglas):
        o = oferta_base()
        for mod in ["presencial", "remoto", "hibrido", "híbrido"]:
            o["modalidad"] = mod
            assert not evaluar_regla(o, reglas["NV_MOD_invalida"]), \
                f'NV_MOD_invalida disparó con modalidad válida: {mod}'

    # --- EMPRESA ---

    def test_V18_sector_igual_area(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "IT"
        o["area_funcional"] = "IT"
        o["sector_coincide_area"] = True
        assert evaluar_regla(o, reglas["V18_sector_igual_area"])

    def test_V19_sector_seguridad_no_vigilancia(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Seguridad"
        o["area_funcional"] = "Administracion"
        assert evaluar_regla(o, reglas["V19_sector_seguridad_no_vigilancia"])

    def test_V19_no_dispara_vigilancia(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Seguridad"
        o["area_funcional"] = "Vigilancia"
        assert not evaluar_regla(o, reglas["V19_sector_seguridad_no_vigilancia"])

    def test_V20_sector_salud_no_sanitario(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Salud"
        o["area_funcional"] = "Administracion"
        o["sector_confianza"] = "alta"
        assert evaluar_regla(o, reglas["V20_sector_salud_no_sanitario"])

    def test_V20_no_dispara_baja_confianza(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Salud"
        o["area_funcional"] = "Administracion"
        o["sector_confianza"] = "media"
        assert not evaluar_regla(o, reglas["V20_sector_salud_no_sanitario"])

    def test_V21_sector_tecnologia_no_it(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Tecnologia"
        o["area_funcional"] = "RRHH"
        o["sector_confianza"] = "alta"
        assert evaluar_regla(o, reglas["V21_sector_tecnologia_no_it"])

    def test_V22_empresa_confidencial_con_sector(self, reglas):
        o = oferta_base()
        o["empresa"] = "Empresa Confidencial"
        o["sector_empresa"] = "Tecnologia"
        assert evaluar_regla(o, reglas["V22_empresa_confidencial_con_sector"])

    def test_V22_no_dispara_empresa_real(self, reglas):
        o = oferta_base()
        o["empresa"] = "TechCorp SA"
        o["sector_empresa"] = "Tecnologia"
        assert not evaluar_regla(o, reglas["V22_empresa_confidencial_con_sector"])

    def test_NV02_sector_no_canonico(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Blockchain y Cripto"
        assert evaluar_regla(o, reglas["NV02_sector_no_canonico"])

    def test_NV02_no_dispara_sector_canonico(self, reglas):
        o = oferta_base()
        for s in ["Tecnologia", "Salud", "Comercio", "Finanzas", "Educacion"]:
            o["sector_empresa"] = s
            assert not evaluar_regla(o, reglas["NV02_sector_no_canonico"]), \
                f'NV02 disparó con sector canónico: {s}'

    def test_NV11_sector_null_like(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "null"
        assert evaluar_regla(o, reglas["NV11_sector_null_like"])

    def test_NV11_dispara_variantes(self, reglas):
        o = oferta_base()
        for val in ["None", "N/A", "sin dato", "No especificado"]:
            o["sector_empresa"] = val
            assert evaluar_regla(o, reglas["NV11_sector_null_like"]), \
                f'NV11 no disparó con null-like: {val}'

    # --- CLAE ---

    def test_V16_clae_missing(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Tecnologia"
        o["clae_code"] = None
        o["es_intermediario"] = 0
        assert evaluar_regla(o, reglas["V16_clae_missing"])

    def test_V16_no_dispara_intermediario(self, reglas):
        o = oferta_base()
        o["sector_empresa"] = "Tecnologia"
        o["clae_code"] = None
        o["es_intermediario"] = 1
        assert not evaluar_regla(o, reglas["V16_clae_missing"])

    def test_V17_clae_seccion_invalida(self, reglas):
        o = oferta_base()
        o["clae_code"] = "9999"
        o["clae_seccion"] = "Z"
        assert evaluar_regla(o, reglas["V17_clae_seccion_invalida"])

    def test_V17_no_dispara_seccion_valida(self, reglas):
        o = oferta_base()
        o["clae_code"] = "6201"
        for sec in ["A", "C", "J", "Q", "U"]:
            o["clae_seccion"] = sec
            assert not evaluar_regla(o, reglas["V17_clae_seccion_invalida"]), \
                f'V17 disparó con sección CLAE válida: {sec}'

    # --- EDUCACION ---

    def test_NV_EDU_invalido(self, reglas):
        o = oferta_base()
        o["nivel_educativo"] = "bachillerato"
        assert evaluar_regla(o, reglas["NV_EDU_invalido"])

    def test_NV_EDU_no_dispara_validos(self, reglas):
        o = oferta_base()
        for niv in ["primario", "secundario", "terciario", "universitario", "posgrado"]:
            o["nivel_educativo"] = niv
            assert not evaluar_regla(o, reglas["NV_EDU_invalido"]), \
                f'NV_EDU disparó con nivel válido: {niv}'

    def test_NV_EDU_no_dispara_null(self, reglas):
        """NULL es aceptable (no informado), no es un valor inválido."""
        o = oferta_base()
        o["nivel_educativo"] = None
        assert not evaluar_regla(o, reglas["NV_EDU_invalido"])

    # --- EXPERIENCIA ---

    def test_NV_EXP_RANGE(self, reglas):
        o = oferta_base()
        o["experiencia_min_anios"] = 35
        assert evaluar_regla(o, reglas["NV_EXP_RANGE"])

    def test_NV_EXP_RANGE_no_dispara_normal(self, reglas):
        o = oferta_base()
        o["experiencia_min_anios"] = 10
        assert not evaluar_regla(o, reglas["NV_EXP_RANGE"])

    def test_NV_EXP_INV(self, reglas):
        o = oferta_base()
        o["experiencia_min_anios"] = 5
        o["experiencia_max_anios"] = 3
        o["experiencia_rango_invertido"] = True
        assert evaluar_regla(o, reglas["NV_EXP_INV"])

    def test_NV_EXP_INV_no_dispara_rango_ok(self, reglas):
        o = oferta_base()
        o["experiencia_min_anios"] = 3
        o["experiencia_max_anios"] = 5
        o["experiencia_rango_invertido"] = False
        assert not evaluar_regla(o, reglas["NV_EXP_INV"])

    def test_NV_EXP_SENIORITY(self, reglas):
        o = oferta_base()
        o["experiencia_min_anios"] = 1
        o["nivel_seniority"] = "director"
        assert evaluar_regla(o, reglas["NV_EXP_SENIORITY"])

    def test_NV_EXP_SENIORITY_no_dispara_coherente(self, reglas):
        o = oferta_base()
        o["experiencia_min_anios"] = 5
        o["nivel_seniority"] = "senior"
        assert not evaluar_regla(o, reglas["NV_EXP_SENIORITY"])

    # --- CONDICIONES LABORALES ---

    def test_NV_JORNADA_invalida(self, reglas):
        o = oferta_base()
        o["jornada_laboral"] = "medio tiempo"
        assert evaluar_regla(o, reglas["NV_JORNADA_invalida"])

    def test_NV_JORNADA_no_dispara_valida(self, reglas):
        o = oferta_base()
        for j in ["full-time", "part-time", "freelance"]:
            o["jornada_laboral"] = j
            assert not evaluar_regla(o, reglas["NV_JORNADA_invalida"]), \
                f'NV_JORNADA disparó con valor válido: {j}'

    def test_NV_CONTRATO_invalido(self, reglas):
        o = oferta_base()
        o["tipo_contrato"] = "temporal"
        assert evaluar_regla(o, reglas["NV_CONTRATO_invalido"])

    def test_NV_CONTRATO_no_dispara_valido(self, reglas):
        o = oferta_base()
        for c in ["monotributo", "contrato", "efectivo", "pasantia"]:
            o["tipo_contrato"] = c
            assert not evaluar_regla(o, reglas["NV_CONTRATO_invalido"]), \
                f'NV_CONTRATO disparó con valor válido: {c}'


# ============================================================================
# TESTS: Gate blocking - severidad critico/alto bloquean
# ============================================================================

class TestGateSeveridades:
    """Verificar que reglas con severidad critico/alto están correctamente marcadas."""

    GATE_RULES = {
        "V01_titulo_limpio_vacio": "critico",
        "V11_tareas_vacias": "alto",
        "V17_clae_seccion_invalida": "alto",
        "NV02_sector_no_canonico": "alto",
        "NV03_area_funcional_invalida": "alto",
        "NV04_seniority_invalido": "alto",
        "NV08_sin_tareas_ni_skills": "alto",
        "NV11_sector_null_like": "alto",
    }

    def test_gate_rules_severidad(self, reglas):
        for rule_id, expected_sev in self.GATE_RULES.items():
            assert reglas[rule_id]["severidad"] == expected_sev, \
                f'{rule_id}: esperaba severidad "{expected_sev}", tiene "{reglas[rule_id]["severidad"]}"'

    def test_gate_rules_count(self, reglas):
        """Exactamente 8 reglas bloquean el gate."""
        gate_count = sum(1 for r in reglas.values() if r["severidad"] in ("critico", "alto"))
        assert gate_count == 8, f"Esperaba 8 reglas gate, hay {gate_count}"

    def test_non_gate_rules_no_bloquean(self, reglas):
        """Reglas medio/bajo/warning/info NO bloquean."""
        non_gate = [r for r in reglas.values() if r["severidad"] not in ("critico", "alto")]
        assert len(non_gate) == 27, f"Esperaba 27 reglas no-gate, hay {len(non_gate)}"


# ============================================================================
# TESTS: Grupos completos
# ============================================================================

class TestGruposReglas:
    """Verificar que cada grupo tiene las reglas esperadas."""

    EXPECTED_GROUPS = {
        "titulos": ["V01_titulo_limpio_vacio", "V07_titulo_codigo_interno"],
        "skills": ["V03_skills_insuficientes", "V13_skills_sin_origen_tarea"],
        "clasificacion": [
            "V08_area_funcional_nula", "V09_seniority_nulo",
            "V15_seniority_titulo_mismatch",
            "NV03_area_funcional_invalida", "NV04_seniority_invalido",
            "NV06_tipo_oferta_invalido", "NV_CROSS_gente_seniority",
        ],
        "tareas": [
            "V11_tareas_vacias", "V14_descripcion_muy_corta",
            "V25_tareas_vacias_con_skills", "V26_formato_tareas_incorrecto",
            "V29_tareas_muy_cortas", "NV08_sin_tareas_ni_skills",
        ],
        "ubicacion": [
            "V12_provincia_vacia",
            "NV_PROV_invalida", "NV_MOD_invalida",
        ],
        "empresa": [
            "V18_sector_igual_area", "V19_sector_seguridad_no_vigilancia",
            "V20_sector_salud_no_sanitario", "V21_sector_tecnologia_no_it",
            "V22_empresa_confidencial_con_sector",
            "NV02_sector_no_canonico", "NV11_sector_null_like",
        ],
        "clae": ["V16_clae_missing", "V17_clae_seccion_invalida"],
        "educacion": ["NV_EDU_invalido"],
        "experiencia": ["NV_EXP_RANGE", "NV_EXP_INV", "NV_EXP_SENIORITY"],
        "condiciones_laborales": ["NV_JORNADA_invalida", "NV_CONTRATO_invalido"],
    }

    def test_grupo_membership(self, reglas):
        for grupo, expected_ids in self.EXPECTED_GROUPS.items():
            actual_ids = [r_id for r_id, r in reglas.items() if r.get("grupo") == grupo]
            for eid in expected_ids:
                assert eid in actual_ids, \
                    f'Regla {eid} debería estar en grupo "{grupo}" pero no se encontró'

    def test_total_reglas_en_grupos(self, reglas):
        total_expected = sum(len(ids) for ids in self.EXPECTED_GROUPS.values())
        assert total_expected == 35, f"Total esperado en grupos: {total_expected}, debe ser 35"
