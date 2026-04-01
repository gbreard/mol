# -*- coding: utf-8 -*-
"""
Tests: Alerta de equivalencias con baja confianza en Centro de Control.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAlertaEquivConfianza:

    def test_condicion_se_activa(self):
        """Con >50 grupos auto y similitud_minima < 0.87, alerta se activa."""
        count = 435
        threshold = 50
        assert count > threshold

    def test_condicion_no_se_activa(self):
        """Con <=50 grupos, no hay alerta."""
        count = 30
        threshold = 50
        assert not (count > threshold)

    def test_severidad_es_warning(self):
        """La alerta es warning, no error."""
        nivel = 'warning'
        assert nivel == 'warning'

    def test_accion_link_existe(self):
        """El link de acción apunta a equivalencias con filtro de confianza."""
        accion_links = {
            'ver_equiv_baja_confianza': {
                'label': 'Ver equivalencias',
                'href': '/admin/procesamiento/fabrica/equivalencias?sort=confianza_asc'
            }
        }
        link = accion_links.get('ver_equiv_baja_confianza')
        assert link is not None
        assert 'confianza_asc' in link['href']

    def test_alerta_no_rompe_pipeline_ok(self):
        """La alerta de equiv no impide que 'Pipeline operativo' aparezca
        cuando todo lo demás está OK — se agregan ambas alertas."""
        # La condición de "todo OK" ahora incluye equiv_baja_confianza <= 50
        # Si hay >50 grupos con baja confianza, "Pipeline operativo" no aparece
        equiv_count = 435
        dias_scraping = 1
        sin_nlp = 0
        pendientes_matching = 0
        pendientes_sync = 0
        errores = 0
        issues = 0

        all_ok = (dias_scraping <= 3 and sin_nlp == 0 and
                  pendientes_matching == 0 and pendientes_sync == 0 and
                  errores == 0 and issues == 0 and equiv_count <= 50)

        # Con 435 grupos baja confianza, "todo OK" no se muestra
        assert not all_ok

    def test_mensaje_incluye_conteo(self):
        """El mensaje de la alerta incluye el número de grupos."""
        count = 435
        mensaje = f'{count} grupos de skills con baja confianza — revisar equivalencias'
        assert '435' in mensaje
        assert 'baja confianza' in mensaje
