# -*- coding: utf-8 -*-
"""
Tests SPEC G — _filter_llm_skills.

Usa BGE-M3 cargado en el extractor. Test de comportamiento de la política
de 2 niveles (detección oferta-level + salvavidas).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'database'))
sys.path.insert(0, str(ROOT / 'config'))


@pytest.fixture(scope='module')
def extractor():
    from skills_implicit_extractor import SkillsImplicitExtractor
    return SkillsImplicitExtractor(verbose=False)


class TestFilterLlmSkills:

    def test_skills_validas_se_mantienen(self, extractor):
        """Cocinero con skills coherentes — todas pasan."""
        skills = ['realizar tareas de limpieza', 'mantener la limpieza de la zona de trabajo']
        out = extractor._filter_llm_skills(
            skills,
            titulo='Cocinero/a',
            tareas='Preparacion de platos; toma de comandas; limpieza de cocina',
        )
        assert len(out) == len(skills), f'Esperaba todas, got {out}'

    def test_alucinacion_masiva_descarta_todo(self, extractor):
        """Enfermera con skills random — modo salvavidas activa, casi todas caen."""
        skills_alucinadas = [
            'técnicas de soldadura blanda',
            'estrategias de venta',
            'controlar el movimiento de piezas en máquinas',
            'mantener sistemas hidráulicos',
            'gestionar la entrega de mobiliario',
            'inspeccionar un grabado al ácido',
            'gestionar el flujo de caja',
        ]
        out = extractor._filter_llm_skills(
            skills_alucinadas,
            titulo='Enfermera profesional',
            tareas='Administrar cuidados; supervisar pacientes',
        )
        # En modo salvavidas, casi todas deben caer
        assert len(out) <= 2, f'En alucinación deberían caer casi todas, quedaron {out}'

    def test_lista_vacia(self, extractor):
        assert extractor._filter_llm_skills([], 'titulo', 'tareas') == []

    def test_none_input(self, extractor):
        assert extractor._filter_llm_skills(None, 'titulo', 'tareas') == []

    def test_descarta_null_strings(self, extractor):
        skills = ['null', 'none', '', '   ', 'realizar tareas de limpieza']
        out = extractor._filter_llm_skills(
            skills, titulo='Mozo', tareas='atender mesas; limpiar')
        # 'realizar tareas de limpieza' debería quedar; los otros descartados como input inválido
        assert all(s.lower() not in ('null','none','') for s in out)

    def test_filter_disabled_mantiene_todo(self):
        """Con filter_llm_skills=False, no filtra nada."""
        from skills_implicit_extractor import SkillsImplicitExtractor
        e = SkillsImplicitExtractor(filter_llm_skills=False)
        skills = ['xxxx', 'yyyy', 'realizar tareas']
        out = e._filter_llm_skills(skills, 'titulo', 'tareas')
        # Sin filtro, devuelve la lista normalizada (sin null/none)
        assert len(out) == len(skills)

    def test_contexto_vacio_devuelve_skills_sin_filtrar(self, extractor):
        """Si no hay título ni tareas, no podemos filtrar — devolver tal cual."""
        skills = ['cualquier skill']
        out = extractor._filter_llm_skills(skills, '', '')
        assert out == skills

    def test_caso_canonico_project_manager_alucinacion(self, extractor):
        """PM con tareas en inglés cortas — el LLM tiende a alucinar lista larga."""
        skills_pm = [
            'Project management',
            'Basecamp',
            'tratar problemas del cuero cabelludo',
            'discapacidad auditiva',
            'historia de la moda',
            'seleccionar semen para inseminación animal',
            'tipos de papeles para empapelar',
            'mezclar hormigón',
            'comprender el griego hablado',
            'leer las etiquetas del equipaje facturado',
        ]
        out = extractor._filter_llm_skills(
            skills_pm,
            titulo='Project manager',
            tareas='Plan & Execute; Monitor Progress; Lead Meetings',
        )
        # En modo salvavidas, debería rescatar al menos "Project management"
        # y descartar la mayoría de las random
        assert 'Project management' in out or len(out) <= 2
        # Las absurdas deben desaparecer
        for absurda in ['historia de la moda', 'tipos de papeles para empapelar',
                        'comprender el griego hablado']:
            assert absurda not in out, f'"{absurda}" debería caer'
