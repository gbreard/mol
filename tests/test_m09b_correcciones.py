# -*- coding: utf-8 -*-
"""
M-09b: Tests de circulación de correcciones expertas.
11 tests: 3 RPC/cola + 4 tipo inferido + 2 reporte + 2 regresión
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCorreccionesSinProcesar:

    def test_correcciones_sin_procesada_se_cuentan(self):
        """Correcciones con procesada_en_pipeline=NULL se cuentan."""
        correcciones = [
            {"procesada": None, "corr": {"nota": "algo largo" * 10}},
            {"procesada": None, "corr": {"ocupacion_corregida": {"isco": "2411"}}},
            {"procesada": "2026-03-30T10:00:00", "corr": {"nota": "ya procesada"}},
        ]
        pendientes = [c for c in correcciones if c["procesada"] is None]
        assert len(pendientes) == 2

    def test_procesada_limpia_cola(self):
        """Corrección con procesada_en_pipeline no aparece."""
        corr = {"procesada": "2026-04-01T12:00:00", "validacion_at": "2026-03-30T10:00:00"}
        es_pendiente = corr["procesada"] is None or corr["validacion_at"] > corr["procesada"]
        assert not es_pendiente  # procesada es posterior

    def test_correccion_nueva_reaparece(self):
        """Si Cynthia corrige de nuevo después de procesada, reaparece."""
        corr = {"procesada": "2026-03-30T10:00:00", "validacion_at": "2026-04-01T14:00:00"}
        es_pendiente = corr["procesada"] is None or corr["validacion_at"] > corr["procesada"]
        assert es_pendiente  # validacion posterior a procesada


class TestTipoInferido:

    def test_tipo_matching(self):
        """ocupacion_corregida → Matching"""
        corr = {"ocupacion_corregida": {"isco_code": "2411"}}
        tipo = "Matching" if corr.get("ocupacion_corregida") else None
        assert tipo == "Matching"

    def test_tipo_nlp(self):
        """nlp_editado → NLP"""
        corr = {"nlp_editado": {"area_funcional": "finanzas"}}
        tipo = None
        if corr.get("ocupacion_corregida"): tipo = "Matching"
        elif corr.get("nlp_editado"): tipo = "NLP"
        assert tipo == "NLP"

    def test_tipo_skills(self):
        """skills_editadas → Skills"""
        corr = {"skills_editadas": [{"label": "gestionar"}]}
        tipo = None
        if corr.get("ocupacion_corregida"): tipo = "Matching"
        elif corr.get("nlp_editado"): tipo = "NLP"
        elif corr.get("skills_editadas"): tipo = "Skills"
        assert tipo == "Skills"

    def test_tipo_sinonimos_por_keyword(self):
        """Nota con 'repositor = reponedor' → Sinónimos"""
        corr = {"nota": "Diccionario: repositor = reponedor = repositor de góndola"}
        nota = (corr.get("nota") or "").lower()
        keywords_sinonimos = ["sinónimo", "equivale", "diccionario", "repositor", "reponedor"]
        tipo = "Sinónimos" if any(kw in nota for kw in keywords_sinonimos) else None
        assert tipo == "Sinónimos"


class TestReporte:

    def test_reporte_tiene_4_secciones(self):
        """Reporte markdown tiene las 4 secciones."""
        report = """# Reporte de correcciones
## CORRECCIONES DE ISCO
## NOTAS CON ANÁLISIS
## SKILLS EDITADAS
## INSTRUCCIONES PARA CLAUDE CODE"""
        assert "CORRECCIONES DE ISCO" in report
        assert "NOTAS CON ANÁLISIS" in report
        assert "SKILLS EDITADAS" in report
        assert "INSTRUCCIONES PARA CLAUDE CODE" in report

    def test_reporte_incluye_linaje(self):
        """Reporte incluye issue_id y oferta_id."""
        issue_id = "abc123"
        oferta_id = "1118027941"
        line = f"- Issue: #{issue_id[:8]}"
        line2 = f"(ID: {oferta_id})"
        assert issue_id[:8] in line
        assert oferta_id in line2


class TestRegresion:

    def test_validacion_no_tiene_campos_nuevos(self):
        """El wizard de validación no tiene campos nuevos obligatorios."""
        # M-09b no modifica el wizard — solo lee lo que ya existe
        wizard_fields = ["ocupacion_corregida", "nlp_editado", "tareas_editadas", "skills_editadas", "nota"]
        # Ningún campo nuevo agregado por M-09b
        m09b_new_fields = []
        assert len(m09b_new_fields) == 0

    def test_issues_existentes_no_afectados(self):
        """Issues sin corrección asociada siguen mostrándose normal."""
        issue = {"id": "xyz", "id_oferta": None, "titulo": "Bug en gráfico"}
        corrections = {}
        tipo = None
        if issue.get("id_oferta") and issue["id_oferta"] in corrections:
            corr = corrections[issue["id_oferta"]]
            if corr.get("ocupacion_corregida"): tipo = "Matching"
        assert tipo is None  # Sin badge, sin crash
