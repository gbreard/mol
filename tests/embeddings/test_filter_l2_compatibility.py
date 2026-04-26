# -*- coding: utf-8 -*-
"""SPEC K — tests para filter_skills_by_l2_compatibility."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'database'))
sys.path.insert(0, str(ROOT / 'config'))


@pytest.fixture(scope='module')
def extractor():
    from skills_implicit_extractor import SkillsImplicitExtractor
    e = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    return e


class TestL2Compatible:

    def test_T_pasa_siempre(self, extractor):
        """L1 transversal pasa para cualquier ocupación."""
        # 5120.1 cocinero — T* siempre compatible
        assert extractor._l2_compatible('T', 'T', '5120.1') is True
        assert extractor._l2_compatible('T1', 'T1.1', '5120.1') is True
        assert extractor._l2_compatible('T6', 'T6.2', '7214.3.1') is True

    def test_l1_vacio_pasa(self, extractor):
        assert extractor._l2_compatible('', '', '5120.1') is True
        assert extractor._l2_compatible(None, None, '5120.1') is True

    def test_skill_S_compatible_con_cocinero(self, extractor):
        """Cocinero tiene S3.3 en su set → debe pasar."""
        assert extractor._l2_compatible('S3', 'S3.3', '5120.1') is True

    def test_skill_S_incompatible_con_cocinero(self, extractor):
        """Cocinero/grupo 5120 NO tiene S8.4 (coquización) → False."""
        # Set grupo 5120 tiene S8.0, S8.5 pero NO S8.4
        assert extractor._l2_compatible('S8', 'S8.4', '5120.1') is False

    def test_target_invalido_es_permisivo(self, extractor):
        """Si esco_code no existe en metadata, no filtra."""
        assert extractor._l2_compatible('S8', 'S8.4', 'XXXX.99') is True

    def test_target_vacio_pasa(self, extractor):
        assert extractor._l2_compatible('S8', 'S8.4', '') is True
        assert extractor._l2_compatible('S8', 'S8.4', None) is True


class TestFilterSkillsByL2:

    def test_skills_compatibles_pasan(self, extractor):
        """Cocinero con S3.3 (set propio) y T deben pasar."""
        skills = [
            {'skill_esco': 'cocinar', 'L1': 'S3', 'L2': 'S3.3'},
            {'skill_esco': 'trabajo equipo', 'L1': 'T', 'L2': 'T.1'},
        ]
        out = extractor.filter_skills_by_l2_compatibility(skills, '5120.1')
        assert len(out) == 2

    def test_skills_incompatibles_descartadas(self, extractor):
        """Cocinero con S8.4 (no está en grupo 5120) debe caer."""
        skills = [
            {'skill_esco': 'cocinar', 'L1': 'S3', 'L2': 'S3.3'},
            {'skill_esco': 'controlar coquización', 'L1': 'S8', 'L2': 'S8.4'},
        ]
        out = extractor.filter_skills_by_l2_compatibility(skills, '5120.1')
        labels = [s['skill_esco'] for s in out]
        assert 'cocinar' in labels
        assert 'controlar coquización' not in labels

    def test_target_vacio_pasa_todas(self, extractor):
        skills = [{'skill_esco': 'x', 'L1': 'S8', 'L2': 'S8.4'}]
        assert extractor.filter_skills_by_l2_compatibility(skills, '') == skills
        assert extractor.filter_skills_by_l2_compatibility(skills, None) == skills

    def test_target_inexistente_pasa_todas(self, extractor):
        skills = [{'skill_esco': 'x', 'L1': 'S8', 'L2': 'S8.4'}]
        out = extractor.filter_skills_by_l2_compatibility(skills, 'XXXX.99')
        assert out == skills

    def test_caso_canonico_enfermera(self, extractor):
        """Enfermera 2221.2: skills de alcantarillado deben caer.
        El set propio + grupo 2221 NO incluye S6.2 ni S7.2."""
        skills = [
            {'skill_esco': 'planificar asistencia', 'L1': 'S4', 'L2': 'S4.2'},  # S4.2 está en set
            {'skill_esco': 'inspeccionar desagües', 'L1': 'S6', 'L2': 'S6.2'},  # NO en set
            {'skill_esco': 'colocar tuberías', 'L1': 'S7', 'L2': 'S7.2'},  # NO en set
            {'skill_esco': 'instalar sistemas sépticos', 'L1': 'S7', 'L2': 'S7.2'},  # NO en set
        ]
        out = extractor.filter_skills_by_l2_compatibility(skills, '2221.2')
        labels = [s['skill_esco'] for s in out]
        assert 'planificar asistencia' in labels
        assert 'inspeccionar desagües' not in labels
        assert 'colocar tuberías' not in labels
        assert 'instalar sistemas sépticos' not in labels

    def test_caso_canonico_carpintero_sin_falsos_positivos(self, extractor):
        """Carpintero 7522.2 grupo: S2.8 está → válida pasa."""
        skills = [
            # S2.8 está en grupo 7522
            {'skill_esco': 'controlar normas calidad fabricación', 'L1': 'S2', 'L2': 'S2.8'},
        ]
        out = extractor.filter_skills_by_l2_compatibility(skills, '7522.2')
        assert len(out) == 1, f'Skill S2.8 (en grupo 7522) debería pasar, got {out}'
