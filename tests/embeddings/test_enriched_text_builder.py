# -*- coding: utf-8 -*-
"""
Tests unit para build_enriched_embeddings.build_enriched_text y build_metadata_record.

No requieren cargar BGE-M3 (son tests puros de construcción de strings/dicts).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "embeddings"))

from build_enriched_embeddings import build_enriched_text, build_metadata_record


class TestBuildEnrichedText:

    def test_skill_completa(self):
        skill = {
            'uri': 'http://example.com/skill/x',
            'label': 'ocuparse de remachadoras',
            'description': 'Manejar máquinas diseñadas para unir piezas metálicas mediante remaches.',
            'L1': 'S8',
            'L2': 'S8.5',
            'category_label': 'manejar equipos de producción',
            'broader_label': 'manejar herramientas mecánicas',
        }
        occ = [
            ('7214.3.1', 'remachador/remachadora', 'essential_for'),
            ('7214.3', 'ferrallista', 'essential_for'),
        ]
        texto = build_enriched_text(skill, occ)
        assert 'ocuparse de remachadoras' in texto
        assert 'S8.5' in texto
        assert 'manejar equipos de producción' in texto
        assert 'manejar herramientas mecánicas' in texto
        assert '7214.3.1' in texto
        assert 'remachador/remachadora' in texto
        assert 'Manejar máquinas' in texto

    def test_skill_sin_broader(self):
        skill = {
            'label': 'skill sin padre',
            'L1': 'S1', 'L2': 'S1.2', 'category_label': 'cat',
            'broader_label': '',
        }
        texto = build_enriched_text(skill, [])
        assert 'skill sin padre' in texto
        assert 'Tipo general' not in texto

    def test_skill_sin_ocupaciones(self):
        skill = {
            'label': 'skill huérfana',
            'description': 'desc',
        }
        texto = build_enriched_text(skill, [])
        assert 'skill huérfana' in texto
        assert 'Típica en' not in texto
        assert 'desc' in texto

    def test_skill_sin_label_retorna_vacio(self):
        skill = {'label': '', 'description': 'algo'}
        assert build_enriched_text(skill, []) == ''

    def test_description_truncada_a_500_chars(self):
        skill = {'label': 'test', 'description': 'a' * 800}
        texto = build_enriched_text(skill, [])
        # Debe haber truncado a 500 chars
        assert 'a' * 500 in texto
        assert 'a' * 501 not in texto

    def test_broader_igual_a_label_se_omite(self):
        """Cuando broader_label es igual al label, no lo duplicamos."""
        skill = {'label': 'programar', 'broader_label': 'programar'}
        texto = build_enriched_text(skill, [])
        assert 'Tipo general: programar' not in texto

    def test_fallback_optional_si_no_hay_essential(self):
        skill = {'label': 'test'}
        occ = [
            ('1234.5', 'ocupación optativa', 'optional_for'),
        ]
        texto = build_enriched_text(skill, occ)
        assert 'ocupación optativa (1234.5)' in texto

    def test_top_3_ocupaciones_limite(self):
        """Más de 3 essential_for → solo las primeras 3."""
        skill = {'label': 'test'}
        occ = [
            (f'100{i}.1', f'ocup{i}', 'essential_for') for i in range(10)
        ]
        texto = build_enriched_text(skill, occ)
        assert 'ocup0' in texto
        assert 'ocup1' in texto
        assert 'ocup2' in texto
        assert 'ocup3' not in texto

    def test_unicode_preservado(self):
        skill = {
            'label': 'análisis técnico de emisiones',
            'description': 'Evaluar niveles en españá'
        }
        texto = build_enriched_text(skill, [])
        assert 'análisis' in texto
        assert 'españá' in texto


class TestBuildMetadataRecord:

    def test_record_completo(self):
        skill = {
            'uri': 'http://example/skill/x',
            'label': 'test',
            'description': 'desc',
            'type': 'skill',
            'L1': 'S8',
            'L2': 'S8.5',
            'category_code': 'S8.5',
            'category_label': 'cat',
            'broader_uri': 'http://example/b',
            'broader_label': 'b',
        }
        occ = [
            ('7214.3.1', 'remachador', 'essential_for'),
            ('7214.3', 'ferrallista', 'optional_for'),
            ('7214.3.1', 'remachador', 'optional_for'),  # duplicado de esco_code
        ]
        texto = 'cualquier texto'
        rec = build_metadata_record(skill, occ, texto)

        # Campos básicos
        assert rec['uri'] == 'http://example/skill/x'
        assert rec['label'] == 'test'
        assert rec['description'] == 'desc'
        assert rec['type'] == 'skill'
        assert rec['L1'] == 'S8'
        assert rec['L2'] == 'S8.5'

        # esco_codes_aplicable es único y ordenado
        assert rec['esco_codes_aplicable'] == ['7214.3', '7214.3.1']
        assert rec['n_occupations'] == 2
        assert rec['texto_indexado'] == texto

    def test_record_sin_ocupaciones(self):
        skill = {'uri': 'x', 'label': 'y'}
        rec = build_metadata_record(skill, [], 'texto')
        assert rec['esco_codes_aplicable'] == []
        assert rec['n_occupations'] == 0

    def test_record_preserva_texto_indexado(self):
        skill = {'uri': 'x', 'label': 'y'}
        texto = 'texto con\nsalto de línea\ny más'
        rec = build_metadata_record(skill, [], texto)
        assert rec['texto_indexado'] == texto
