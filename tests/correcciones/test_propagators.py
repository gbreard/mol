"""
Tests para SPEC T Fase 1 — propagators.

Estos tests usan datos reales de la BD local y verifican:
  1. Schema validation (patrones inválidos son rechazados).
  2. Identify funciona (encuentra ofertas con el patrón).
  3. Dry-run NO modifica BD.
  4. Casos conocidos: SPEC P (R236 marketing) y SPEC S (operario depósito)
     que ya están aplicados deben dar 0 cambios efectivos en dry-run/apply
     (porque ya se propagaron).

Run:
    pytest tests/correcciones/test_propagators.py -v
"""
import sqlite3

import pytest

from scripts.correcciones import propagate_correction
from scripts.correcciones.propagators import (
    MatchingESCOPropagator,
    NLPAreaPropagator,
    PatronInvalido,
    PropagationResult,
    SkillsFiltroPropagator,
    get_propagator,
    validar_patron,
)


DB_PATH = "database/bumeran_scraping.db"


# ─────────────────────────────────────────────────────────────────────
# Schema validation
# ─────────────────────────────────────────────────────────────────────

class TestValidarPatron:
    def test_tipo_invalido(self):
        with pytest.raises(PatronInvalido):
            validar_patron({"tipo": "no_existe", "campo": "x", "condicion": {"tipo": "y"},
                            "valor_nuevo": "z"})

    def test_campo_obligatorio(self):
        with pytest.raises(PatronInvalido):
            validar_patron({"tipo": "nlp_area_funcional",
                            "condicion": {"tipo": "titulo_contiene_alguno"},
                            "valor_nuevo": "X"})

    def test_condicion_tipo_obligatorio(self):
        with pytest.raises(PatronInvalido):
            validar_patron({"tipo": "nlp_area_funcional", "campo": "area_funcional",
                            "condicion": {}, "valor_nuevo": "X"})

    def test_valor_nuevo_obligatorio_excepto_skills(self):
        with pytest.raises(PatronInvalido):
            validar_patron({"tipo": "nlp_area_funcional", "campo": "area_funcional",
                            "condicion": {"tipo": "titulo_contiene_alguno",
                                          "keywords": ["x"]}})

    def test_skills_filtro_no_requiere_valor_nuevo(self):
        # No debe lanzar
        validar_patron({"tipo": "skills_filtro", "campo": "skills_oferta",
                        "condicion": {"tipo": "regla_aplicada", "valor_unico": "R1"}})

    def test_patron_valido_pasa(self):
        validar_patron({"tipo": "nlp_area_funcional", "campo": "area_funcional",
                        "condicion": {"tipo": "titulo_contiene_alguno",
                                      "keywords": ["x"]},
                        "valor_anterior": "A", "valor_nuevo": "B"})


# ─────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────

class TestFactory:
    def test_get_propagator_devuelve_instancia_correcta(self):
        p = get_propagator("nlp_area_funcional")
        assert isinstance(p, NLPAreaPropagator)

        p = get_propagator("matching_esco")
        assert isinstance(p, MatchingESCOPropagator)

        p = get_propagator("skills_filtro")
        assert isinstance(p, SkillsFiltroPropagator)

    def test_get_propagator_tipo_invalido(self):
        with pytest.raises(PatronInvalido):
            get_propagator("inexistente")


# ─────────────────────────────────────────────────────────────────────
# NLP Area — caso SPEC S
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def patron_spec_s():
    """Patrón usado en SPEC S — operario depósito → Logistica."""
    return {
        "tipo": "nlp_area_funcional",
        "campo": "area_funcional",
        "condicion": {
            "tipo": "titulo_contiene_alguno",
            "keywords": [
                "operario de deposito",
                "operario de depósito",
                "operario de almacen",
                "operario de almacén",
                "operario de despacho",
                "operarios/as de depósito",
                "operarios/as de almacen",
                "despacho metalúrgico",
            ],
        },
        "valor_anterior": "Produccion",
        "valor_nuevo": "Logistica",
    }


class TestNLPAreaPropagator:
    def test_identify_no_lanza(self, patron_spec_s):
        propagator = NLPAreaPropagator(db_path=DB_PATH)
        ids = propagator.identify(patron_spec_s)
        assert isinstance(ids, list)

    def test_identify_post_spec_s_devuelve_pocos_o_ninguno(self, patron_spec_s):
        """SPEC S ya aplicado → identify(area=Produccion) debe encontrar ~0
        porque la mayoría se cambió a Logistica."""
        propagator = NLPAreaPropagator(db_path=DB_PATH)
        ids = propagator.identify(patron_spec_s)
        # Pueden quedar algunas ofertas que el LLM siga asignando Producción
        # (las que tienen título genérico "Operario de Producción" + despacho en desc)
        # Esperamos << 50 (vs los 316 originales pre-SPEC-S).
        assert len(ids) < 50, f"Esperaba <50 residuales, hay {len(ids)}"

    def test_dry_run_no_toca_bd(self, patron_spec_s):
        # Snapshot pre
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE area_funcional='Logistica'")
        antes = cur.fetchone()[0]
        conn.close()

        # Run dry
        result = propagate_correction(patron_spec_s, dry_run=True, update_issue=False)
        assert result.dry_run is True
        # Verificar que el conteo no cambió
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ofertas_nlp WHERE area_funcional='Logistica'")
        despues = cur.fetchone()[0]
        conn.close()
        assert antes == despues, "Dry-run no debe modificar BD"

    def test_apply_con_patron_inventado_no_afecta_nada(self):
        """Patrón con keyword inexistente → 0 ofertas tocadas."""
        patron = {
            "tipo": "nlp_area_funcional",
            "campo": "area_funcional",
            "condicion": {
                "tipo": "titulo_contiene_alguno",
                "keywords": ["xyzzyplugh_inexistente_keyword_zzz"],
            },
            "valor_anterior": "Produccion",
            "valor_nuevo": "Logistica",
        }
        result = propagate_correction(patron, dry_run=False, update_issue=False)
        assert result.ofertas_actualizadas == 0
        assert result.errores == []


# ─────────────────────────────────────────────────────────────────────
# Matching ESCO — caso SPEC P R236
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def patron_r236():
    """SPEC P: R236_analista_marketing → 2431.10."""
    return {
        "tipo": "matching_esco",
        "campo": "esco_label",
        "condicion": {"tipo": "regla_aplicada", "valor_unico": "R236_analista_marketing"},
        "valor_anterior": "2431.6",
        "valor_nuevo": "2431.10",
    }


class TestMatchingESCOPropagator:
    def test_identify_r236_devuelve_ofertas(self, patron_r236):
        propagator = MatchingESCOPropagator(db_path=DB_PATH)
        ids = propagator.identify(patron_r236)
        # SPEC P aplicado: las 169 ofertas R236 siguen con regla_aplicada=R236
        # solo cambiaron de target.
        assert len(ids) > 100, f"Esperaba >100 ofertas R236, hay {len(ids)}"

    def test_dry_run_estima_correcto(self, patron_r236):
        result = propagate_correction(patron_r236, dry_run=True, update_issue=False)
        assert result.dry_run is True
        assert result.ofertas_identificadas > 100
        assert result.ofertas_actualizadas == result.ofertas_identificadas
        assert len(result.errores) == 0


# ─────────────────────────────────────────────────────────────────────
# Skills Filtro
# ─────────────────────────────────────────────────────────────────────

class TestSkillsFiltroPropagator:
    def test_identify_por_lista(self):
        patron = {
            "tipo": "skills_filtro",
            "campo": "skills_oferta",
            "condicion": {
                "tipo": "id_oferta_lista",
                "valores": [8299423434, 6786905097],
            },
        }
        propagator = SkillsFiltroPropagator(db_path=DB_PATH)
        ids = propagator.identify(patron)
        # Las 2 deberían existir en BD
        assert len(ids) == 2

    def test_dry_run_no_dispara_re_extract(self):
        """Dry-run NO debe ejecutar el script de re-extracción."""
        patron = {
            "tipo": "skills_filtro",
            "campo": "skills_oferta",
            "condicion": {
                "tipo": "id_oferta_lista",
                "valores": [8299423434],
            },
        }
        result = propagate_correction(patron, dry_run=True, update_issue=False)
        assert result.dry_run is True
        # ofertas_actualizadas en dry-run es == identificadas (pretende)
        assert result.ofertas_identificadas == 1


# ─────────────────────────────────────────────────────────────────────
# Result schema
# ─────────────────────────────────────────────────────────────────────

class TestPropagationResult:
    def test_to_dict_serializable(self):
        result = PropagationResult(
            tipo="nlp_area_funcional",
            ofertas_identificadas=5,
            ofertas_actualizadas=5,
            ids_tocados=[1, 2, 3, 4, 5],
            dry_run=True,
        )
        d = result.to_dict()
        import json as _json
        # Debe poder serializarse a JSON sin errores
        s = _json.dumps(d)
        assert "nlp_area_funcional" in s

    def test_summary_dry_run_indicado(self):
        result = PropagationResult(
            tipo="x", ofertas_identificadas=10, ofertas_actualizadas=10, dry_run=True
        )
        assert "[DRY-RUN]" in result.summary()
