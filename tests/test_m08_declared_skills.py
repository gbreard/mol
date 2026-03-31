# -*- coding: utf-8 -*-
"""
M-08: Tests — Conectar fuentes declaradas con ESCO.

8 parser + 7 extractor + 4 integración + 4 regresión + 5 casos borde = 28 tests
"""

import pytest
import sys
import sqlite3
import numpy as np
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def extractor():
    """Extractor mock con embeddings controlados (mismo patrón M-06)."""
    from skills_implicit_extractor import SkillsImplicitExtractor

    ext = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    ext.verbose = False
    ext.top_k = 3
    ext.threshold = 0.40

    ext.metadata = [
        {"label": "instalar cableado eléctrico", "uri": "http://esco/skill/001"},
        {"label": "trabajar en equipo", "uri": "http://esco/skill/002"},
        {"label": "gestionar inventario", "uri": "http://esco/skill/003"},
        {"label": "programar en Python", "uri": "http://esco/skill/004"},
        {"label": "liderazgo", "uri": "http://esco/skill/005"},
    ]

    dim = 32
    ext.embeddings = np.zeros((5, dim), dtype=np.float32)
    ext.embeddings[0, 0:6] = 1.0
    ext.embeddings[1, 6:12] = 1.0
    ext.embeddings[2, 12:18] = 1.0
    ext.embeddings[3, 18:24] = 1.0
    ext.embeddings[4, 24:30] = 1.0
    norms = np.linalg.norm(ext.embeddings, axis=1, keepdims=True)
    ext.embeddings = ext.embeddings / norms

    ext.sinonimos_skills = {"tareas_a_skills": {}, "soft_skills_argentinas": {}}
    # Equivalencia: skill 001 → grupo EQ-001
    ext.equiv_lookup = {"http://esco/skill/001": "EQ-001"}
    ext.equiv_groups = {"EQ-001": {"label": "instalar cableado (canónico)"}}
    ext.weights_config = {"skills_genericas": {"lista": [], "peso": 0.5}}
    ext.terminology_config = {"terminos": {}}

    def _encode(text, normalize_embeddings=True):
        vec = np.zeros(dim, dtype=np.float32)
        text_lower = text.lower()
        if "cableado" in text_lower or "instalar" in text_lower:
            vec[0:6] = 1.0
        elif "equipo" in text_lower or "trabajo en equipo" in text_lower:
            vec[6:12] = 1.0
        elif "inventario" in text_lower or "gestionar" in text_lower:
            vec[12:18] = 1.0
        elif "python" in text_lower or "programar" in text_lower:
            vec[18:24] = 1.0
        elif "liderazgo" in text_lower or "liderar" in text_lower:
            vec[24:30] = 1.0
        else:
            vec[30:32] = 1.0  # No matchea nada
        norm = np.linalg.norm(vec)
        if norm > 0 and normalize_embeddings:
            vec = vec / norm
        return vec

    ext.model = MagicMock()
    ext.model.encode = _encode
    return ext


# ============================================================================
# Nivel 1 — Unitarios: Parser
# ============================================================================

class TestParseDeclairedSource:

    def test_parse_json_array(self, extractor):
        result = extractor._parse_declared_source(
            "skills_tecnicas_list",
            '["Excel", "SAP", "Power BI"]'
        )
        assert result == ["excel", "sap", "power bi"]

    def test_parse_semicolon(self, extractor):
        result = extractor._parse_declared_source(
            "tecnologias_list",
            "Excel; SAP; Power BI"
        )
        assert result == ["Excel", "SAP", "Power BI"]

    def test_parse_comma_soft_skills(self, extractor):
        result = extractor._parse_declared_source(
            "soft_skills_list",
            "liderazgo, trabajo en equipo, comunicación"
        )
        assert result == ["liderazgo", "trabajo en equipo", "comunicación"]

    def test_parse_soft_skills_split_y(self, extractor):
        result = extractor._parse_declared_source(
            "soft_skills_list",
            "liderazgo y capacidad de negociación"
        )
        assert "liderazgo" in result
        assert "capacidad de negociación" in result

    def test_parse_max_items(self, extractor):
        big = "; ".join([f"skill_{i}" for i in range(25)])
        result = extractor._parse_declared_source("skills_tecnicas_list", big)
        assert len(result) <= 15

        big_soft = ", ".join([f"soft_{i}" for i in range(25)])
        result_soft = extractor._parse_declared_source("soft_skills_list", big_soft)
        assert len(result_soft) <= 20

    def test_parse_vacio(self, extractor):
        assert extractor._parse_declared_source("skills_tecnicas_list", None) == []
        assert extractor._parse_declared_source("skills_tecnicas_list", "") == []
        assert extractor._parse_declared_source("skills_tecnicas_list", "[]") == []
        assert extractor._parse_declared_source("skills_tecnicas_list", "null") == []

    def test_parse_json_con_objetos(self, extractor):
        result = extractor._parse_declared_source(
            "skills_tecnicas_list",
            '[{"valor": "Excel"}, "SAP"]'
        )
        assert "excel" in result
        assert "sap" in result

    def test_parse_tecnologias_no_lowercase(self, extractor):
        result = extractor._parse_declared_source(
            "tecnologias_list",
            "SAP; Python; AWS"
        )
        assert "SAP" in result
        assert "Python" in result
        assert "AWS" in result


# ============================================================================
# Nivel 2 — Unitarios: Extractor
# ============================================================================

class TestExtractDeclaredSkills:

    def test_retorna_tupla(self, extractor):
        oferta = {"skills_tecnicas_list": "trabajar en equipo", "tecnologias_list": "",
                  "herramientas_list": "", "soft_skills_list": ""}
        result = extractor.extract_declared_skills(oferta, track_failures=True)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_skill_tipo_fuente_correcto(self, extractor):
        oferta = {
            "skills_tecnicas_list": "trabajar en equipo",
            "tecnologias_list": "Python",
            "herramientas_list": "",
            "soft_skills_list": "liderazgo"
        }
        skills, _ = extractor.extract_declared_skills(oferta)
        tipos = {s["origen"] for s in skills}
        assert "skills_nlp_declarada" in tipos
        assert "tecnologia_declarada" in tipos
        assert "soft_skill_declarada" in tipos

    def test_usa_equivalencia(self, extractor):
        """Skill que matchea URI con equivalencia usa label canónico."""
        oferta = {"skills_tecnicas_list": "instalar cableado",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        skills, _ = extractor.extract_declared_skills(oferta)
        cableado = [s for s in skills if "cableado" in s["skill_esco"].lower()]
        assert len(cableado) == 1
        assert cableado[0]["skill_esco"] == "instalar cableado (canónico)"

    def test_top_1(self, extractor):
        """Solo retorna 1 skill por item declarado."""
        oferta = {"skills_tecnicas_list": "gestionar inventario",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        skills, _ = extractor.extract_declared_skills(oferta)
        # Solo 1 skill para "gestionar inventario", no 3
        inv_skills = [s for s in skills if "inventario" in s["skill_esco"].lower()]
        assert len(inv_skills) == 1

    def test_failures_diferenciados(self, extractor):
        oferta = {"skills_tecnicas_list": "blockchain cuántico",
                  "tecnologias_list": "framework inexistente",
                  "herramientas_list": "", "soft_skills_list": ""}
        _, failures = extractor.extract_declared_skills(oferta, track_failures=True)
        origenes = {f["tarea_origen"] for f in failures}
        assert "skills_nlp_declarada" in origenes
        assert "tecnologia_declarada" in origenes

    def test_fuente_vacia_no_rompe(self, extractor):
        oferta = {"skills_tecnicas_list": "", "tecnologias_list": None,
                  "herramientas_list": "", "soft_skills_list": ""}
        skills, failures = extractor.extract_declared_skills(oferta)
        assert skills == []
        assert failures == []

    def test_track_failures_false(self, extractor):
        oferta = {"skills_tecnicas_list": "blockchain cuántico",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        _, failures = extractor.extract_declared_skills(oferta, track_failures=False)
        assert failures == []


# ============================================================================
# Nivel 3 — Integración
# ============================================================================

class TestIntegracion:

    def test_merge_deduplica_con_tareas(self, extractor):
        """Skill de declaradas que ya vino de tareas no se duplica."""
        # Simular skills de tareas
        skills_tareas = [
            {"skill_esco": "trabajar en equipo", "skill_uri": "http://esco/skill/002",
             "score": 0.85, "score_ponderado": 0.85, "peso": 1.0, "origen": "tarea"}
        ]
        # Declaradas con la misma skill
        oferta = {"skills_tecnicas_list": "trabajar en equipo",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        declared, _ = extractor.extract_declared_skills(oferta)

        # Merge con dedup
        existing_keys = set()
        for s in skills_tareas:
            uri = s.get("skill_uri", "")
            group = extractor.equiv_lookup.get(uri, uri)
            existing_keys.add(group)

        added = 0
        for s in declared:
            uri = s.get("skill_uri", "")
            group = extractor.equiv_lookup.get(uri, uri)
            if group not in existing_keys:
                existing_keys.add(group)
                skills_tareas.append(s)
                added += 1

        # "trabajar en equipo" ya estaba → no se agrega
        assert added == 0
        assert len(skills_tareas) == 1

    def test_merge_agrega_nuevas(self, extractor):
        """Skills nuevas de declaradas se agregan."""
        skills_tareas = [
            {"skill_esco": "trabajar en equipo", "skill_uri": "http://esco/skill/002",
             "score": 0.85, "score_ponderado": 0.85, "peso": 1.0, "origen": "tarea"}
        ]
        oferta = {"skills_tecnicas_list": "gestionar inventario",
                  "tecnologias_list": "Python", "herramientas_list": "", "soft_skills_list": "liderazgo"}
        declared, _ = extractor.extract_declared_skills(oferta)

        existing_keys = set()
        for s in skills_tareas:
            uri = s.get("skill_uri", "")
            group = extractor.equiv_lookup.get(uri, uri)
            existing_keys.add(group)

        added = 0
        for s in declared:
            uri = s.get("skill_uri", "")
            group = extractor.equiv_lookup.get(uri, uri)
            if group not in existing_keys:
                existing_keys.add(group)
                skills_tareas.append(s)
                added += 1

        # 3 nuevas (inventario, Python, liderazgo) — equipo ya estaba
        assert added == 3
        assert len(skills_tareas) == 4

    def test_failures_declaradas_en_bd(self):
        """Failures de declaradas se persisten en skills_extraction_failures."""
        from match_ofertas_v3 import MatcherV3
        conn = sqlite3.connect(":memory:")
        conn.execute('''CREATE TABLE skills_extraction_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oferta_id TEXT, run_id TEXT, tarea_texto TEXT, tarea_origen TEXT,
            mejor_skill_uri TEXT, mejor_skill_label TEXT, mejor_score REAL,
            threshold_usado REAL DEFAULT 0.40, gap_al_umbral REAL,
            fecha_intento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo_falla TEXT DEFAULT 'sin_clasificar'
        )''')

        matcher = MatcherV3.__new__(MatcherV3)
        matcher.conn = conn

        failures = [
            {"tarea_texto": "blockchain", "tarea_origen": "tecnologia_declarada",
             "mejor_score": 0.15, "threshold_usado": 0.40, "gap_al_umbral": 0.25}
        ]
        matcher._persist_skill_failures("OF_001", "run_test", failures)

        rows = conn.execute("SELECT tarea_origen FROM skills_extraction_failures").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "tecnologia_declarada"
        conn.close()

    def test_skill_tipo_fuente_en_resultado(self, extractor):
        """Las skills declaradas tienen skill_tipo_fuente diferenciado."""
        oferta = {
            "skills_tecnicas_list": "gestionar inventario",
            "tecnologias_list": "Python",
            "herramientas_list": "",
            "soft_skills_list": "liderazgo"
        }
        skills, _ = extractor.extract_declared_skills(oferta)
        tipos = [s["origen"] for s in skills]
        assert "skills_nlp_declarada" in tipos
        assert "tecnologia_declarada" in tipos
        assert "soft_skill_declarada" in tipos


# ============================================================================
# Nivel 4 — Regresión
# ============================================================================

class TestRegresion:

    def test_tareas_no_afectadas(self, extractor):
        """extract_from_tasks funciona igual que antes de M-08."""
        result = extractor.extract_from_tasks(
            "instalar cableado industrial; trabajar en equipo",
            track_failures=False
        )
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_no_duplicados(self, extractor):
        """No hay duplicados por equiv_group en el merge."""
        skills_tareas = [
            {"skill_esco": "instalar cableado (canónico)", "skill_uri": "http://esco/skill/001",
             "score": 0.90, "origen": "tarea"}
        ]
        oferta = {"skills_tecnicas_list": "instalar cableado",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        declared, _ = extractor.extract_declared_skills(oferta)

        existing_keys = set()
        for s in skills_tareas:
            uri = s.get("skill_uri", "")
            group = extractor.equiv_lookup.get(uri, uri)
            existing_keys.add(group)

        for s in declared:
            uri = s.get("skill_uri", "")
            group = extractor.equiv_lookup.get(uri, uri)
            if group not in existing_keys:
                existing_keys.add(group)
                skills_tareas.append(s)

        # Mismo grupo de equivalencia → no duplica
        assert len(skills_tareas) == 1

    def test_match_result_no_cambia(self, extractor):
        """extract_declared_skills no afecta el matching de ocupación."""
        # El matching de ocupación es independiente — extract_declared solo agrega skills
        oferta = {"skills_tecnicas_list": "gestionar inventario",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        skills, _ = extractor.extract_declared_skills(oferta)
        # No retorna MatchResult, solo skills — matching no se modifica
        assert all("isco_code" not in s for s in skills)

    def test_oferta_sin_declaradas(self, extractor):
        """Oferta con 4 listas vacías no agrega nada."""
        oferta = {"skills_tecnicas_list": "", "tecnologias_list": "",
                  "herramientas_list": "", "soft_skills_list": ""}
        skills, failures = extractor.extract_declared_skills(oferta, track_failures=True)
        assert skills == []
        assert failures == []


# ============================================================================
# Casos borde
# ============================================================================

class TestCasosBorde:

    def test_skill_tecnica_label_esco(self, extractor):
        """'trabajar en equipo' (label ESCO textual) matchea con score alto."""
        oferta = {"skills_tecnicas_list": "trabajar en equipo",
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        skills, failures = extractor.extract_declared_skills(oferta, track_failures=True)
        assert len(skills) == 1
        assert skills[0]["score"] > 0.80
        assert len(failures) == 0

    def test_nombre_corto(self, extractor):
        """'R' como tecnología no crashea."""
        oferta = {"skills_tecnicas_list": "", "tecnologias_list": "R",
                  "herramientas_list": "", "soft_skills_list": ""}
        # Debe no crashear — puede no matchear pero no rompe
        skills, failures = extractor.extract_declared_skills(oferta, track_failures=True)
        # R es 1 char, parser lo filtra (len > 1)
        assert True  # No crash

    def test_soft_skill_frase_larga(self, extractor):
        """Frase larga con múltiples soft skills se splitea."""
        oferta = {"skills_tecnicas_list": "", "tecnologias_list": "",
                  "herramientas_list": "",
                  "soft_skills_list": "liderazgo, trabajo en equipo, comunicación"}
        skills, _ = extractor.extract_declared_skills(oferta)
        # Debe producir skills para los items que matchean
        assert len(skills) >= 1

    def test_json_malformado(self, extractor):
        """JSON inválido usa fallback a split."""
        oferta = {"skills_tecnicas_list": "[Excel, SAP]",  # Sin comillas
                  "tecnologias_list": "", "herramientas_list": "", "soft_skills_list": ""}
        # No debe crashear
        skills, _ = extractor.extract_declared_skills(oferta, track_failures=True)
        assert True  # No crash

    def test_dedup_misma_fuente(self, extractor):
        """Items duplicados en la misma fuente no generan embeddings dobles."""
        oferta = {"skills_tecnicas_list": "", "tecnologias_list": "Python; SAP; Python",
                  "herramientas_list": "", "soft_skills_list": ""}
        items = extractor._parse_declared_source("tecnologias_list", "Python; SAP; Python")
        assert items.count("Python") == 1  # Dedup en parser
