# -*- coding: utf-8 -*-
"""
Tests E2.4: Downstream triggers al aprobar emergentes
======================================================

Tests de integración contra Supabase real.
Aprueba una emergente, verifica los 4 triggers, revierte al final.
"""

import pytest
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


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


@pytest.fixture(scope="module")
def esco_argentino_iscos(supabase):
    """Set of isco_codes that have esco_argentino profiles."""
    r = supabase.table('esco_argentino').select('isco_code').execute()
    return set(row['isco_code'] for row in (r.data or []))


@pytest.fixture(scope="module")
def test_emergente_with_profile(supabase, esco_argentino_iscos):
    """Find a pendiente emergente whose isco IS in esco_argentino."""
    r = supabase.table('emergentes_pendientes').select(
        'id,skill_label,isco_code,ocupacion_label,skill_uri'
    ).eq('estado', 'pendiente').limit(100).execute()

    for e in (r.data or []):
        if e['isco_code'] in esco_argentino_iscos:
            return e
    pytest.skip("No pendiente emergente with isco in esco_argentino")


@pytest.fixture(scope="module")
def approval_result(supabase, test_emergente_with_profile):
    """Approve the emergente and return the RPC result. Revert after all tests."""
    eid = test_emergente_with_profile['id']
    isco = test_emergente_with_profile['isco_code']

    # Save esco_argentino state before
    ea_before = supabase.table('esco_argentino').select(
        'esco_occupation_uri,skills_consolidadas,total_skills,skills_from_argentina'
    ).eq('isco_code', isco).limit(1).execute()

    # Approve
    result = supabase.rpc('aprobar_emergente_con_triggers', {
        'p_emergente_id': eid,
        'p_admin_email': 'pytest@test.local',
        'p_notas': 'E2.4 automated test',
    }).execute()

    yield {
        'rpc_data': result.data,
        'emergente': test_emergente_with_profile,
        'ea_before': ea_before.data[0] if ea_before.data else None,
    }

    # === CLEANUP: Revert everything ===
    # Revert emergente
    supabase.table('emergentes_pendientes').update({
        'estado': 'pendiente',
        'fecha_resolucion': None,
        'resuelto_por': None,
        'notas': None,
    }).eq('id', eid).execute()

    # Remove training pair
    supabase.table('approved_training_pairs').delete().eq('emergente_id', eid).execute()

    # Remove pipeline command
    supabase.table('pipeline_commands').delete().eq('comando', 'invalidar_cache_argentino').eq('creado_por', 'pytest@test.local').execute()

    # Revert esco_argentino
    if ea_before.data:
        occ_uri = ea_before.data[0]['esco_occupation_uri']
        supabase.table('esco_argentino').update({
            'skills_consolidadas': ea_before.data[0]['skills_consolidadas'],
            'total_skills': ea_before.data[0]['total_skills'],
            'skills_from_argentina': ea_before.data[0]['skills_from_argentina'],
        }).eq('esco_occupation_uri', occ_uri).execute()


# ============================================================
# Tests
# ============================================================

class TestE24DownstreamTriggers:

    def test_aprobar_emergente_inserta_en_esco_argentino(self, supabase, approval_result):
        """T1: Después de aprobar, skill aparece en skills_consolidadas."""
        isco = approval_result['emergente']['isco_code']
        skill_label = approval_result['emergente']['skill_label'].lower()

        ea = supabase.table('esco_argentino').select(
            'skills_consolidadas,total_skills'
        ).eq('isco_code', isco).limit(1).execute()

        assert ea.data, f"No esco_argentino for ISCO {isco}"

        skills = ea.data[0]['skills_consolidadas']
        labels = [s.get('label_normalized', '').lower() for s in skills]
        assert skill_label in labels, \
            f"Skill '{skill_label}' not found in esco_argentino skills"

        # total_skills should have increased
        before = approval_result['ea_before']
        assert ea.data[0]['total_skills'] == before['total_skills'] + 1

    def test_aprobar_genera_training_pair(self, supabase, approval_result):
        """T2: approved_training_pairs tiene el par nuevo en formato correcto."""
        eid = approval_result['emergente']['id']

        tp = supabase.table('approved_training_pairs').select('*').eq(
            'emergente_id', eid
        ).execute()

        assert len(tp.data) == 1, f"Expected 1 training pair, got {len(tp.data)}"

        pair = tp.data[0]
        assert pair['query'] == approval_result['emergente']['skill_label']
        assert pair['source'] == 'emergente_aprobada'
        assert pair['confianza'] == 'alta'
        assert pair['split'] == 'train'
        assert isinstance(pair['negatives'], list)
        assert pair['positive'].startswith('http')

    def test_conteo_emergentes_muestra_real(self, supabase):
        """La query de conteo devuelve el total real de pendientes."""
        r = supabase.table('emergentes_pendientes').select(
            'id', count='exact', head=True
        ).eq('estado', 'pendiente').execute()

        # Should be close to 459 (minus the one we approved in the fixture)
        assert r.count >= 400, \
            f"Expected ~458 pendientes, got {r.count}"

    def test_rollback_action_matches(self):
        """Frontend sends action: 'activar' matching API expectation."""
        admin_component = PROJECT_ROOT / "fase3_dashboard" / "mol-dashboard" / "components" / "PerfilArgentinoAdmin.tsx"
        if not admin_component.exists():
            admin_component = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard/components/PerfilArgentinoAdmin.tsx")
        if not admin_component.exists():
            pytest.skip("PerfilArgentinoAdmin.tsx not found")

        content = admin_component.read_text()
        assert 'action: "activar"' in content, \
            "Frontend should send action: 'activar' not 'rollback'"
        assert 'action: "rollback"' not in content, \
            "Found stale action: 'rollback' in frontend"

    def test_alerta_corte_version_a_10_aprobaciones(self, supabase, approval_result):
        """Trigger 4: alerta es null cuando < 10 aprobaciones."""
        rpc = approval_result['rpc_data']

        # With only 1-2 approvals, no alert expected
        count = rpc.get('aprobadas_desde_corte', 0)
        if count < 10:
            assert rpc.get('trigger_4_alerta') is None, \
                f"Expected no alert with {count} approvals"
        else:
            assert rpc.get('trigger_4_alerta') is not None, \
                f"Expected alert with {count} >= 10 approvals"
