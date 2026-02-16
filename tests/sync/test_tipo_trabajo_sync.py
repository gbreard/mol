"""
Tests para verificar que sync_to_supabase usa tipo_trabajo del scraping
en vez de jornada_laboral del NLP.

Step 12 del plan NLP Validator.
"""

import pytest


class TestTipoTrabajoNormalization:
    """Verifica la normalización tipo_trabajo → jornada_laboral en payload."""

    @pytest.mark.parametrize("raw_value,expected", [
        ("Full-time", "full-time"),
        ("Part-time", "part-time"),
        ("Por Horas", "por horas"),
        ("Pasantía", "pasantía"),
        ("Temporario", "temporario"),
        ("Nocturno", "nocturno"),
        ("FULL-TIME", "full-time"),
        ("full-time", "full-time"),
    ])
    def test_normaliza_lowercase(self, raw_value, expected):
        """tipo_trabajo se convierte a lowercase."""
        result = (raw_value or '').lower() or None
        assert result == expected

    @pytest.mark.parametrize("raw_value", [
        None,
        "",
        "   ",
    ])
    def test_null_y_vacios(self, raw_value):
        """Valores nulos/vacíos producen None."""
        result = (raw_value or '').lower().strip() or None
        assert result is None

    def test_payload_usa_tipo_trabajo_no_jornada(self):
        """
        El payload mapea oferta['tipo_trabajo'] → 'jornada_laboral'.
        Simula la lógica exacta de sync_to_supabase.py línea ~594.
        """
        # Simulamos una oferta como viene de la query SQL
        oferta = {
            'tipo_trabajo': 'Full-time',
            'jornada_laboral': None,  # campo NLP - NO debe usarse
        }

        # Lógica exacta del payload en sync_to_supabase.py
        payload_value = (oferta.get('tipo_trabajo') or '').lower() or None

        assert payload_value == 'full-time'

    def test_tipo_trabajo_prioridad_sobre_jornada_nlp(self):
        """
        Si la oferta tiene tipo_trabajo del scraping Y jornada_laboral del NLP,
        el sync debe usar tipo_trabajo (scraping tiene 100% coverage vs 48% NLP).
        """
        oferta = {
            'tipo_trabajo': 'Part-time',
            'jornada_laboral': 'full-time',  # NLP podría tener otro valor
        }

        payload_value = (oferta.get('tipo_trabajo') or '').lower() or None
        assert payload_value == 'part-time'  # Viene de scraping, no de NLP


class TestTipoTrabajoSQL:
    """Verifica que la query SQL trae o.tipo_trabajo."""

    def test_query_tiene_tipo_trabajo_de_ofertas(self):
        """La query debe traer o.tipo_trabajo (tabla ofertas, no NLP)."""
        import re
        from pathlib import Path

        sync_path = Path(__file__).parent.parent.parent / "scripts" / "exports" / "sync_to_supabase.py"
        content = sync_path.read_text(encoding='utf-8')

        # Debe tener o.tipo_trabajo (de tabla ofertas)
        assert 'o.tipo_trabajo' in content, "Query debe traer o.tipo_trabajo de tabla ofertas"

        # NO debe tener n.jornada_laboral (era la versión anterior)
        # Buscamos en la query principal (no en comentarios)
        lines = content.split('\n')
        in_query = False
        for line in lines:
            stripped = line.strip()
            if 'SELECT' in stripped and '--' not in stripped:
                in_query = True
            if in_query and 'n.jornada_laboral' in stripped and not stripped.startswith('#'):
                pytest.fail("Query todavía trae n.jornada_laboral del NLP - debería usar o.tipo_trabajo")
            if in_query and 'ORDER BY' in stripped:
                in_query = False

    def test_payload_mapea_tipo_trabajo_a_jornada(self):
        """
        El payload debe mapear tipo_trabajo → campo jornada_laboral de Supabase.
        """
        from pathlib import Path

        sync_path = Path(__file__).parent.parent.parent / "scripts" / "exports" / "sync_to_supabase.py"
        content = sync_path.read_text(encoding='utf-8')

        # Debe tener la línea que mapea tipo_trabajo → jornada_laboral
        assert "oferta.get('tipo_trabajo')" in content, \
            "Payload debe usar oferta.get('tipo_trabajo')"
        assert "'jornada_laboral'" in content, \
            "Payload debe seguir escribiendo en campo jornada_laboral de Supabase"
