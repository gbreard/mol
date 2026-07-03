"""
Tests del fix veneno terminologia (2026-07-03).

Cubren:
1. terminologia_argentina_skills.json quedó vaciado (0 términos, deprecado).
2. skills_rules.json recibió las 10 reglas migradas, todas con URI real del catálogo.
3. El fallo-ruidoso de _extract_terminology_skills rechaza URIs fuera del catálogo
   (patrón Paso 0 de G3) sin necesidad de cargar el modelo BGE-M3.
"""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "database"))


def _real_uris():
    con = sqlite3.connect(str(ROOT / "database" / "bumeran_scraping.db"))
    uris = {r[0] for r in con.execute("SELECT skill_uri FROM esco_skills").fetchall()}
    con.close()
    return uris


def test_terminologia_vaciada_y_deprecada():
    cfg = json.load(open(ROOT / "config" / "terminologia_argentina_skills.json", encoding="utf-8"))
    assert cfg.get("terminos") == {}, "terminologia debe quedar sin términos (vaciada)"
    assert "_DEPRECADO" in cfg, "debe marcar el canal como deprecado"


def test_skills_rules_migradas_con_uri_real():
    real = _real_uris()
    sr = json.load(open(ROOT / "config" / "skills_rules.json", encoding="utf-8"))
    reglas = sr["reglas_forzar_skills"]
    migradas = [rid for rid in reglas if isinstance(reglas[rid], dict)
                and reglas[rid].get("_migrado_de", "").startswith("terminologia")]
    assert len(migradas) == 10, f"esperaba 10 reglas migradas, hay {len(migradas)}"
    # ninguna URI forzada puede estar fuera del catálogo real
    fabricadas = []
    for rid in migradas:
        for s in reglas[rid]["accion"]["forzar_skills"]:
            if s["skill_uri"] not in real:
                fabricadas.append((rid, s["skill_uri"]))
    assert not fabricadas, f"URIs fabricadas en reglas migradas: {fabricadas}"


def test_skills_rules_sin_uris_fabricadas_en_total():
    """El config entero (27 previas + 10 nuevas) no debe tener ninguna URI fabricada."""
    real = _real_uris()
    sr = json.load(open(ROOT / "config" / "skills_rules.json", encoding="utf-8"))
    fabricadas = []
    for rid, rule in sr["reglas_forzar_skills"].items():
        if not isinstance(rule, dict):
            continue
        for s in rule.get("accion", {}).get("forzar_skills", []):
            if s.get("skill_uri") and s["skill_uri"] not in real:
                fabricadas.append((rid, s["skill_uri"]))
    assert not fabricadas, f"skills_rules tiene URIs fabricadas: {fabricadas}"


def test_fallo_ruidoso_rechaza_uri_no_catalogo(caplog):
    """Si alguien repuebla terminologia con una URI fuera del catálogo, no entra y se loguea."""
    from skills_implicit_extractor import SkillsImplicitExtractor
    # Instancia mínima sin cargar el modelo (evita BGE-M3).
    ext = SkillsImplicitExtractor.__new__(SkillsImplicitExtractor)
    ext.verbose = False
    ext.metadata = [
        {"uri": "http://data.europa.eu/esco/skill/REAL-0001", "label": "skill real"},
    ]
    ext._valid_skill_uris_cache = None
    ext.terminology_config = {
        "terminos": {
            "picking": {
                "skills_esco": [
                    {"skill": "skill real", "uri": "http://data.europa.eu/esco/skill/REAL-0001"},
                    {"skill": "skill fabricada", "uri": "http://data.europa.eu/esco/skill/FAKE-9999"},
                ]
            }
        }
    }
    import logging
    with caplog.at_level(logging.WARNING):
        out = ext._extract_terminology_skills("tareas de picking en almacen")
    uris = {s["skill_uri"] for s in out}
    assert "http://data.europa.eu/esco/skill/REAL-0001" in uris, "la URI real debe pasar"
    assert "http://data.europa.eu/esco/skill/FAKE-9999" not in uris, "la URI fabricada NO debe entrar"
    assert any("no-catálogo" in r.message or "RECHAZADA" in r.message for r in caplog.records), \
        "debe loguear el rechazo de la URI fabricada"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
