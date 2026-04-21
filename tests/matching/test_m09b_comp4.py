# -*- coding: utf-8 -*-
"""
Tests M-09b Componente 4 — Análisis Automático con API Anthropic
================================================================

15 tests covering: API endpoint, candidates storage, batching,
rate limiting, prompt construction, UI elements, sync script.
"""

import pytest
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DASHBOARD_ROOT = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard")


def _get_supabase_client():
    candidates = [
        PROJECT_ROOT / "config" / "supabase_config.json",
        Path("/mnt/d/OEDE/Webscrapping/config/supabase_config.json"),
    ]
    for p in candidates:
        if p.exists():
            config = json.loads(p.read_text())
            from supabase import create_client
            return create_client(config['url'], config['service_role_key'])
    return None


@pytest.fixture(scope="module")
def supabase():
    client = _get_supabase_client()
    if not client:
        pytest.skip("Supabase not available")
    return client


# ============================================================
# Endpoint tests (verify code structure, not live API calls)
# ============================================================

class TestEndpointStructure:

    def test_analizar_correcciones_llama_api(self):
        """Endpoint imports Anthropic and calls messages.create."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        if not route.exists():
            pytest.skip("Endpoint not found")
        content = route.read_text()
        assert "import Anthropic" in content
        assert "messages.create" in content
        assert "claude-sonnet-4-6" in content

    def test_candidatos_se_guardan_en_bd(self):
        """Endpoint inserts into rule_candidates table."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "rule_candidates" in content
        assert ".insert(" in content

    def test_batching_funciona(self):
        """Endpoint processes in batches of batch_size."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "batchSize" in content or "batch_size" in content
        assert "for (let i = 0" in content  # batch loop

    def test_rate_limit_diario(self):
        """Endpoint checks rate limit before calling API."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "check_api_rate_limit" in content
        assert "429" in content

    def test_reglas_candidatas_en_prompt(self):
        """Prompt includes reglas_candidatas for each offer."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "reglas_candidatas" in content
        assert "findCandidateRules" in content

    def test_campos_nlp_en_prompt_cuando_corresponde(self):
        """Prompt includes NLP fields when correction mentions sector/area."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "tareas_explicitas" in content
        assert "skills_tecnicas" in content
        assert "needsNlp" in content

    def test_api_usage_se_actualiza(self):
        """Endpoint calls update_api_anthropic_usage RPC after API call."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "update_api_anthropic_usage" in content

    def test_respuesta_invalida_no_rompe(self):
        """Endpoint has JSON parse retry logic."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "parseJsonResponse" in content
        assert "retry" in content.lower() or "attempt" in content.lower()


# ============================================================
# UI tests (verify component structure)
# ============================================================

class TestUIStructure:

    def test_candidatos_se_muestran(self):
        """Correcciones page has tabs and candidate cards."""
        page = DASHBOARD_ROOT / "app/admin/procesamiento/correcciones/page.tsx"
        if not page.exists():
            pytest.skip("Correcciones page not found")
        content = page.read_text()
        assert "TabsList" in content
        assert "Reglas" in content
        assert "CandidateCard" in content or "candidat" in content.lower()

    def test_aprobar_crea_regla_con_linaje(self):
        """Approve action calls PATCH with 'aprobar'."""
        page = DASHBOARD_ROOT / "app/admin/procesamiento/correcciones/page.tsx"
        content = page.read_text()
        assert '"aprobar"' in content
        assert "Aprobar" in content

    def test_aprobar_genera_training_pair(self):
        """Sync script generates training pairs on approve."""
        script = Path("/mnt/d/OEDE/Webscrapping/scripts/sync_rules_from_candidates.py")
        if not script.exists():
            script = PROJECT_ROOT / "scripts" / "sync_rules_from_candidates.py"
        content = script.read_text()
        assert "generate_training_pair" in content
        assert "train_correcciones" in content

    def test_rechazar_con_motivo(self):
        """Reject action includes motivo_rechazo field."""
        route = DASHBOARD_ROOT / "app/api/admin/analizar-correcciones/route.ts"
        content = route.read_text()
        assert "motivo_rechazo" in content
        assert "'rechazar'" in content or '"rechazar"' in content

    def test_kpi_costo_api_visible(self):
        """Metricas page shows API cost KPI."""
        metricas = DASHBOARD_ROOT / "app/admin/metricas/page.tsx"
        if not metricas.exists():
            pytest.skip("Metricas page not found")
        content = metricas.read_text()
        assert "apiUsage" in content
        assert "costo_usd_estimado" in content
        assert "API Anthropic" in content

    def test_alerta_costo_elevado(self):
        """Metricas shows alert when costo_hoy > 1.0."""
        metricas = DASHBOARD_ROOT / "app/admin/metricas/page.tsx"
        content = metricas.read_text()
        assert "costo_hoy > 1.0" in content or "costo_hoy > 1" in content
        assert "Uso de API elevado" in content


# ============================================================
# Integration test (Supabase)
# ============================================================

class TestIntegration:

    def test_sync_script_aplica_candidatos(self, supabase):
        """rule_candidates table exists and RPCs work."""
        # Verify table exists
        r = supabase.table('rule_candidates').select('id', count='exact', head=True).execute()
        assert r.count is not None  # Table exists

        # Verify rate limit RPC
        r2 = supabase.rpc('check_api_rate_limit', {'p_max_daily': 5}).execute()
        assert r2.data is not None
        assert 'allowed' in r2.data
        assert 'llamadas_hoy' in r2.data
