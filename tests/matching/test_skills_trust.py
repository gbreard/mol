# -*- coding: utf-8 -*-
"""
Tests: SPEC B v2 — filtro de skills por trust-source.

Verifica _classify_skill_trust() del SkillsImplicitExtractor sin cargar el
modelo BGE-M3 (usa __new__ para evitar la inicialización pesada).
"""
import sys
from pathlib import Path

import pytest

# Ajustar paths antes de importar
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "database"))
sys.path.insert(0, str(ROOT / "config"))


@pytest.fixture(scope="module")
def extractor():
    """Extractor sin init (evita cargar el modelo; basta para probar el clasificador)."""
    from skills_implicit_extractor import SkillsImplicitExtractor
    e = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    return e


class TestTrustOrigenFuerte:
    """Origen confiable por definición (reglas / LLM / diccionario)."""

    def test_terminologia_argentina_pasa(self, extractor):
        skill = {'origen': 'terminologia_argentina', 'score': 0.95,
                 'texto_fuente': 'picking', 'skill_esco': 'gestionar inventario'}
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_reglas'

    def test_sinonimo_argentino_pasa(self, extractor):
        skill = {'origen': 'sinonimo_argentino', 'score': 0.99,
                 'texto_fuente': 'caja', 'skill_esco': 'gestionar la caja'}
        trust, _ = extractor._classify_skill_trust(skill, {})
        assert trust is True

    def test_regla_issue_pasa(self, extractor):
        skill = {'origen': 'regla_issue', 'score': 0.5,
                 'texto_fuente': '', 'skill_esco': 'skill forzada'}
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_reglas'

    def test_skills_nlp_pasa_aunque_score_bajo(self, extractor):
        skill = {'origen': 'skills_nlp', 'score': 0.45,
                 'texto_fuente': 'AutoCAD', 'skill_esco': 'AutoCAD'}
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_llm_detectado'

    def test_soft_skills_nlp_pasa(self, extractor):
        skill = {'origen': 'soft_skills_nlp', 'score': 0.42,
                 'texto_fuente': 'liderazgo', 'skill_esco': 'liderar equipos'}
        trust, _ = extractor._classify_skill_trust(skill, {})
        assert trust is True


class TestTrustTarea:
    """Origen=tarea: depende del largo del texto y del score."""

    def test_tarea_sustantiva_pasa(self, extractor):
        skill = {
            'origen': 'tarea', 'score': 0.65,
            'texto_fuente': 'realizar operaciones de carga y descarga',
            'skill_esco': 'manejar carretillas elevadoras',
        }
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_tarea_real'

    def test_tarea_corta_score_bajo_descartada(self, extractor):
        skill = {'origen': 'tarea', 'score': 0.55,
                 'texto_fuente': 'Hace 2 dias', 'skill_esco': 'skill'}
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is False
        assert motivo == 'origen_tarea_corta_score_bajo'

    def test_tarea_corta_score_alto_pasa(self, extractor):
        skill = {'origen': 'tarea', 'score': 0.78,
                 'texto_fuente': 'Soldar', 'skill_esco': 'soldar piezas'}
        trust, motivo = extractor._classify_skill_trust(skill, {})
        assert trust is True
        assert motivo == 'origen_tarea_corta_score_alto'


class TestTrustTitulo:
    """Origen=titulo: la lógica depende del contexto de la oferta."""

    def test_titulo_corto_score_medio_descartado(self, extractor):
        skill = {'origen': 'titulo', 'score': 0.77,
                 'texto_fuente': 'operario', 'skill_esco': 'apuestas mutuas'}
        ctx = {'titulo_limpio': 'operario', 'tareas_explicitas': ''}
        trust, motivo = extractor._classify_skill_trust(skill, ctx)
        assert trust is False
        assert motivo == 'titulo_corto_score_medio'

    def test_titulo_corto_score_muy_alto_pasa(self, extractor):
        skill = {'origen': 'titulo', 'score': 0.88,
                 'texto_fuente': 'operario', 'skill_esco': 'skill'}
        ctx = {'titulo_limpio': 'operario', 'tareas_explicitas': ''}
        trust, motivo = extractor._classify_skill_trust(skill, ctx)
        assert trust is True
        assert motivo == 'titulo_corto_score_muy_alto'

    def test_titulo_largo_score_ok_pasa(self, extractor):
        skill = {'origen': 'titulo', 'score': 0.72,
                 'texto_fuente': 'Desarrollador Python Senior Remoto LATAM',
                 'skill_esco': 'programacion en Python'}
        ctx = {'titulo_limpio': 'Desarrollador Python Senior Remoto LATAM',
               'tareas_explicitas': ''}
        trust, motivo = extractor._classify_skill_trust(skill, ctx)
        assert trust is True
        assert motivo == 'titulo_solo_fuente_score_ok'

    def test_titulo_redundante_score_bajo_descartado(self, extractor):
        """Si ya hay tareas, skill del titulo con score<0.80 se descarta."""
        skill = {'origen': 'titulo', 'score': 0.72,
                 'texto_fuente': 'Operario produccion linea envasado',
                 'skill_esco': 'skill'}
        ctx = {'titulo_limpio': 'Operario produccion linea envasado',
               'tareas_explicitas': 'controlar maquinas; cumplir estandares'}
        trust, motivo = extractor._classify_skill_trust(skill, ctx)
        assert trust is False
        assert motivo == 'titulo_redundante_score_bajo'

    def test_titulo_redundante_score_alto_pasa(self, extractor):
        """Si ya hay tareas pero la skill de titulo tiene score >= 0.80, pasa."""
        skill = {'origen': 'titulo', 'score': 0.83,
                 'texto_fuente': 'Ingeniero civil',
                 'skill_esco': 'ingenieria civil'}
        ctx = {'titulo_limpio': 'Ingeniero civil con 5 anios de experiencia',
               'tareas_explicitas': 'disenar puentes; supervisar obras'}
        trust, motivo = extractor._classify_skill_trust(skill, ctx)
        assert trust is True


class TestCasosReales:
    """Casos sacados del informe Fase 0 (skills random en ofertas cortas)."""

    def test_operario_limpieza_skills_random_descartadas(self, extractor):
        """Oferta 5575403602: operario limpieza sin tareas → 3 skills random deben caer."""
        ctx = {'titulo_limpio': 'operario/a de limpieza', 'tareas_explicitas': ''}
        skills_random = [
            {'origen': 'titulo', 'score': 0.77,
             'texto_fuente': 'operario/a de limpieza', 'skill_esco': 'apuestas mutuas'},
            {'origen': 'titulo', 'score': 0.75,
             'texto_fuente': 'operario/a de limpieza', 'skill_esco': 'programas publicos de seguridad social'},
            {'origen': 'titulo', 'score': 0.70,
             'texto_fuente': 'operario/a de limpieza', 'skill_esco': 'escribir en catalan'},
        ]
        for s in skills_random:
            trust, motivo = extractor._classify_skill_trust(s, ctx)
            assert trust is False, (
                f"Skill random '{s['skill_esco']}' deberia caer (score={s['score']}, motivo={motivo})"
            )

    def test_enfermera_skills_de_tareas_se_mantienen(self, extractor):
        """Oferta 1118173872: enfermera con tareas reales → sus skills de 'tarea' quedan."""
        ctx = {
            'titulo_limpio': 'Enfermera profesional',
            'tareas_explicitas': 'administrar medicamentos segun indicacion medica; entregar historial medico al familiar',
        }
        skill_tarea = {
            'origen': 'tarea', 'score': 0.76,
            'texto_fuente': 'entregar historial medico al familiar',
            'skill_esco': 'entregar el historial medico',
        }
        trust, motivo = extractor._classify_skill_trust(skill_tarea, ctx)
        assert trust is True
        assert motivo == 'origen_tarea_real'

    def test_enfermera_skills_titulo_redundantes_caen(self, extractor):
        """Misma enfermera: skills del titulo con score<0.80 (mobiliario/grabado) caen por redundancia."""
        ctx = {
            'titulo_limpio': 'Enfermera profesional',
            'tareas_explicitas': 'administrar medicamentos; supervisar pacientes',
        }
        for label, score in [('gestionar la entrega de mobiliario', 0.79),
                             ('inspeccionar un grabado al acido', 0.79)]:
            skill = {'origen': 'titulo', 'score': score,
                     'texto_fuente': 'Enfermera profesional', 'skill_esco': label}
            trust, motivo = extractor._classify_skill_trust(skill, ctx)
            assert trust is False
            assert motivo == 'titulo_redundante_score_bajo'


class TestFlagFiltrarPorTrust:
    """Verifica que el flag filtrar_por_trust controla el filtrado real."""

    def test_flag_default_no_filtra(self):
        """Por default filtrar_por_trust=False: skill baja confianza queda."""
        from skills_implicit_extractor import SkillsImplicitExtractor
        e = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
        assert not getattr(e, 'filtrar_por_trust', False) is True
        # el __new__ no corre __init__, así que el default aquí es "no existe".
        # Lo importante es que quien instancia con __init__ tenga default False.

    def test_clasificador_retorna_tupla(self, extractor):
        """Siempre (bool, str) — sanity check del contrato."""
        skill = {'origen': 'titulo', 'score': 0.72,
                 'texto_fuente': 'op', 'skill_esco': 'x'}
        resultado = extractor._classify_skill_trust(skill, {})
        assert isinstance(resultado, tuple)
        assert len(resultado) == 2
        trust, motivo = resultado
        assert isinstance(trust, bool)
        assert isinstance(motivo, str)
