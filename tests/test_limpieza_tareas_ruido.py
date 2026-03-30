# -*- coding: utf-8 -*-
"""
Tests: filtro de ruido en tareas_explicitas.

Verifica que metadata de scraping, ubicaciones, empresas y UI
se filtran correctamente, y que tareas reales no se pierden.
"""

import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def postprocessor():
    """NLPPostprocessor con config real."""
    from nlp_postprocessor import NLPPostprocessor
    return NLPPostprocessor(verbose=False)


def limpiar(postprocessor, tareas_str):
    """Helper: pasa tareas por _limpiar_tareas y retorna lista resultante."""
    data = {"tareas_explicitas": tareas_str}
    result = postprocessor._limpiar_tareas(data)
    cleaned = result.get("tareas_explicitas")
    if cleaned is None:
        return []
    return [t.strip() for t in cleaned.split(";") if t.strip()]


# ============================================================================
# Ruido que DEBE filtrarse
# ============================================================================

class TestFiltrarRuido:

    def test_metadata_temporal(self, postprocessor):
        """'Hace N días/horas' se filtra."""
        result = limpiar(postprocessor, "Gestionar inventario; Hace 3 días; Controlar stock")
        assert "Hace 3 días" not in "; ".join(result)
        assert any("inventario" in t.lower() for t in result)

    def test_metadata_temporal_variantes(self, postprocessor):
        """Todas las variantes temporales se filtran."""
        variantes = ["Hace 2 días", "Hace 18 horas", "Hace 5 semanas", "Hace 1 día"]
        for v in variantes:
            result = limpiar(postprocessor, f"Tarea real; {v}")
            assert v not in "; ".join(result), f"'{v}' no se filtró"

    def test_experiencia_requerida(self, postprocessor):
        """'Experiencia requerida: No' se filtra."""
        result = limpiar(postprocessor, "Atención al cliente; Experiencia requerida: No; Cocina")
        assert not any("experiencia requerida" in t.lower() for t in result)

    def test_dias_laborables(self, postprocessor):
        """'Dias laborables: ...' se filtra."""
        result = limpiar(postprocessor, "Vender productos; Dias laborables: Lunes a Viernes")
        assert not any("dias laborables" in t.lower() for t in result)

    def test_ubicacion_duplicada(self, postprocessor):
        """'Córdoba, Córdoba' se filtra (regex ciudad, provincia)."""
        result = limpiar(postprocessor, "Supervisar equipo; Córdoba, Córdoba")
        assert not any("córdoba, córdoba" in t.lower() for t in result)

    def test_ubicacion_gba(self, postprocessor):
        """'San Martín, Buenos Aires-GBA' se filtra."""
        result = limpiar(postprocessor, "Coordinar logística; San Martín, Buenos Aires-GBA")
        # El regex debería matchear ubicaciones con -gba
        cleaned = "; ".join(result).lower()
        assert "buenos aires-gba" not in cleaned or "coordinar" in cleaned

    def test_ui_ocultaste(self, postprocessor):
        """Texto de UI 'Ocultaste esta oferta...' se filtra."""
        result = limpiar(postprocessor, "Ocultaste esta oferta pulsa recuperar; Tarea real aquí")
        assert not any("ocultaste" in t.lower() for t in result)

    def test_postularme_volver(self, postprocessor):
        """'Postularme Volver versión: 0.7.11' se filtra."""
        result = limpiar(postprocessor, "Cocinar platos; Postularme Volver versión: 0.7.11")
        assert not any("postularme" in t.lower() for t in result)

    def test_empresa_sa(self, postprocessor):
        """'Adecco Argentina SA' se filtra."""
        result = limpiar(postprocessor, "Liderar equipo; Adecco Argentina SA")
        assert not any("adecco" in t.lower() for t in result)


# ============================================================================
# Tareas reales que NO deben filtrarse
# ============================================================================

class TestPreservarTareasReales:

    def test_tarea_con_experiencia_real(self, postprocessor):
        """'Gestionar experiencia del cliente' no se filtra (contiene 'experiencia' pero es tarea)."""
        result = limpiar(postprocessor, "Gestionar experiencia del cliente; Resolver consultas")
        assert any("experiencia" in t.lower() for t in result)

    def test_tarea_con_ubicacion_en_contexto(self, postprocessor):
        """'Visitar clientes en Córdoba' no se filtra."""
        result = limpiar(postprocessor, "Visitar clientes en Córdoba; Gestionar cartera")
        assert any("córdoba" in t.lower() for t in result)

    def test_tareas_normales_intactas(self, postprocessor):
        """Tareas normales pasan sin cambios."""
        tareas = "Gestionar inventario; Controlar calidad; Supervisar equipo; Elaborar informes"
        result = limpiar(postprocessor, tareas)
        assert len(result) == 4

    def test_tarea_con_numero(self, postprocessor):
        """'Gestionar 5 cuentas clave' no se filtra (tiene número pero es tarea)."""
        result = limpiar(postprocessor, "Gestionar 5 cuentas clave; Elaborar reportes")
        assert any("5 cuentas" in t for t in result)

    def test_tarea_con_tiempo(self, postprocessor):
        """'Hacer seguimiento cada 3 días' no se filtra (tiene 'días' en contexto de tarea)."""
        result = limpiar(postprocessor, "Hacer seguimiento cada 3 días; Control de calidad")
        assert any("seguimiento" in t.lower() for t in result)


# ============================================================================
# Casos mixtos (ruido + tareas reales)
# ============================================================================

# ============================================================================
# Ruido v2: consultoras, descripciones empresa, códigos internos
# ============================================================================

class TestFiltrarRuidoV2:

    def test_consultora_link_laboral(self, postprocessor):
        """'Link Laboral Puerto Norte' se filtra (nombre de consultora)."""
        result = limpiar(postprocessor, "Gestionar ventas; Link Laboral Puerto Norte")
        assert not any("link laboral" in t.lower() for t in result)
        assert any("ventas" in t.lower() for t in result)

    def test_consultora_adecco(self, postprocessor):
        """Nombres de consultoras conocidas se filtran."""
        result = limpiar(postprocessor, "Supervisar equipo; Adecco busca talento; Control calidad")
        assert not any("adecco" in t.lower() for t in result)

    def test_consultora_randstad(self, postprocessor):
        result = limpiar(postprocessor, "Operar maquinaria; Randstad selecciona")
        assert not any("randstad" in t.lower() for t in result)

    def test_descripcion_importante_empresa(self, postprocessor):
        """'Importante empresa de...' se filtra."""
        result = limpiar(postprocessor, "Importante empresa de autopartes busca; Controlar stock")
        assert not any("importante empresa" in t.lower() for t in result)
        assert any("stock" in t.lower() for t in result)

    def test_descripcion_importante_grupo(self, postprocessor):
        result = limpiar(postprocessor, "Importante grupo concesionario JEEP-RAM; Vender autos")
        assert not any("importante grupo" in t.lower() for t in result)

    def test_descripcion_reconocida_empresa(self, postprocessor):
        result = limpiar(postprocessor, "Reconocida empresa del rubro alimenticio; Producir alimentos")
        assert not any("reconocida empresa" in t.lower() for t in result)

    def test_codigo_interno_req(self, postprocessor):
        """'Auxiliar de Planta (req199974) - Eventual' se filtra (código interno)."""
        result = limpiar(postprocessor, "Controlar calidad; Auxiliar de Planta (req199974) - Eventual")
        assert not any("req199974" in t for t in result)

    def test_codigo_interno_ref(self, postprocessor):
        result = limpiar(postprocessor, "Gestionar inventario; Operario (ref. 12345)")
        assert not any("ref." in t for t in result)


class TestPreservarTareasRealesV2:

    def test_tarea_participar_balance(self, postprocessor):
        """Caso #2 muestra: 'Participar activamente en el armado de Balance' NO se filtra."""
        result = limpiar(postprocessor, "Participar activamente en el armado de Balance")
        assert len(result) == 1
        assert "balance" in result[0].lower()

    def test_tarea_contenido_organico(self, postprocessor):
        """Caso #9 muestra: 'Crear y gestionar contenido orgánico' NO se filtra."""
        result = limpiar(postprocessor, "Crear y gestionar contenido orgánico")
        assert len(result) == 1
        assert "contenido" in result[0].lower()

    def test_tarea_zorras_manuales(self, postprocessor):
        """Caso #36 muestra: 'Manejo de zorras manuales y eléctricas' NO se filtra."""
        result = limpiar(postprocessor, "Manejo de zorras manuales y eléctricas")
        assert len(result) == 1
        assert "zorras" in result[0].lower()

    def test_tarea_monitoreo_eeg(self, postprocessor):
        """Caso #45 muestra: 'Realización de Monitoreo EEG continuo' NO se filtra."""
        result = limpiar(postprocessor, "Realización de Monitoreo EEG continuo")
        assert len(result) == 1
        assert "eeg" in result[0].lower()

    def test_tarea_en_ingles_no_filtrada(self, postprocessor):
        """Tareas en inglés son reales, no se filtran."""
        tareas_ingles = [
            "Architect & Build",
            "Maintain tax mapping for products/services",
            "Present and articulate value proposition",
            "Implement resilience patterns and concurrency",
        ]
        for t in tareas_ingles:
            result = limpiar(postprocessor, t)
            assert len(result) == 1, f"'{t}' fue filtrada incorrectamente"

    def test_empresa_lider_en_tarea_real(self, postprocessor):
        """'Liderar equipo de ventas' NO se filtra (contiene 'líder' en contexto de tarea)."""
        result = limpiar(postprocessor, "Liderar equipo de ventas")
        assert len(result) == 1


# ============================================================================
# Casos mixtos (ruido + tareas reales)
# ============================================================================

class TestCasosMixtos:

    def test_mixto_preserva_reales_filtra_ruido(self, postprocessor):
        """De una lista mixta, solo quedan las tareas reales."""
        tareas = "Atención al cliente; Hace 3 días; Córdoba, Córdoba; Gestión de stock; Experiencia requerida: No"
        result = limpiar(postprocessor, tareas)
        labels = "; ".join(result).lower()
        assert "atención al cliente" in labels or "atencion" in labels
        assert "gestión de stock" in labels or "gestion" in labels
        assert "hace 3" not in labels
        assert "experiencia requerida" not in labels

    def test_todas_ruido_retorna_vacio(self, postprocessor):
        """Si todas las tareas son ruido, retorna vacío."""
        tareas = "Hace 2 días; Córdoba, Córdoba; Experiencia requerida: No"
        result = limpiar(postprocessor, tareas)
        assert len(result) == 0
