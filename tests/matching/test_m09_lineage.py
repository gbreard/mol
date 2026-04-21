# -*- coding: utf-8 -*-
"""
Tests M-09: Linaje de reglas de negocio
========================================

5 tests for save modal, diff detection, changelog, lineage tab, backfill.
"""

import pytest
import json
from pathlib import Path

DASHBOARD_ROOT = Path("/mnt/d/OEDE/Webscrapping/fase3_dashboard/mol-dashboard")
RULES_PATH = Path("/mnt/d/OEDE/Webscrapping/config/matching_rules_business.json")


class TestM09Lineage:

    def test_modal_guardado_con_linaje(self):
        """Modal appears when saving, description is required."""
        page = DASHBOARD_ROOT / "app/admin/procesamiento/reglas/page.tsx"
        if not page.exists():
            pytest.skip("Rules page not found")
        content = page.read_text()

        assert 'showSaveModal' in content, "Save modal state not found"
        assert 'saveDescription' in content, "Description field not found"
        assert 'saveIssueId' in content, "Issue ID field not found"
        assert 'saveTipoCambio' in content, "Tipo cambio not found"
        assert 'openSaveModal' in content, "openSaveModal function not found"
        # Description required: button disabled when empty
        assert "!saveDescription.trim()" in content, "Description required check not found"

    def test_reglas_modificadas_detectadas(self):
        """Changed rules are detected automatically by comparing with original."""
        page = DASHBOARD_ROOT / "app/admin/procesamiento/reglas/page.tsx"
        content = page.read_text()

        assert 'detectChangedRules' in content, "detectChangedRules function not found"
        assert 'detectedChanges' in content, "detectedChanges state not found"
        assert 'originalReglas' in content, "originalReglas state not found"
        assert 'Reglas modificadas' in content, "Modified rules display not found"

    def test_changelog_guarda_campos_nuevos(self):
        """PUT handler includes lineage fields in changelog."""
        route = DASHBOARD_ROOT / "app/api/config-editor/route.ts"
        if not route.exists():
            pytest.skip("Config editor route not found")
        content = route.read_text()

        assert 'lineage' in content, "lineage param not found in PUT handler"
        assert 'issue_id' in content, "issue_id not in changelog"
        assert 'reglas_modificadas' in content, "reglas_modificadas not in changelog"
        assert 'tipo_cambio' in content, "tipo_cambio not in changelog"

    def test_tab_linaje_visible(self):
        """Expanded rule shows lineage tab with fields."""
        page = DASHBOARD_ROOT / "app/admin/procesamiento/reglas/page.tsx"
        content = page.read_text()

        assert 'showLinaje' in content, "showLinaje toggle not found"
        assert '_linaje' in content, "Linaje data reference not found"
        assert 'training_pair_ids' in content, "training_pair_ids display not found"
        assert 'requiere_revision' in content, "requiere_revision display not found"
        assert 'Linaje' in content, "Linaje label not found"

    def test_backfill_extrae_datos(self):
        """Backfill extracts data from _cambios and training pairs."""
        if not RULES_PATH.exists():
            pytest.skip("matching_rules_business.json not found")

        rules = json.loads(RULES_PATH.read_text(encoding='utf-8'))
        reglas = rules.get('reglas_forzar_isco', {})

        total = sum(1 for k, v in reglas.items() if isinstance(v, dict))
        with_linaje = sum(1 for k, v in reglas.items() if isinstance(v, dict) and v.get('_linaje'))
        with_tp = sum(1 for k, v in reglas.items() if isinstance(v, dict) and v.get('_linaje', {}).get('training_pair_ids'))
        with_version = sum(1 for k, v in reglas.items() if isinstance(v, dict) and v.get('_linaje', {}).get('version_origen'))

        # All rules should have _linaje after backfill
        assert with_linaje == total, \
            f"Expected all {total} rules to have _linaje, got {with_linaje}"

        # Some should have training pair IDs
        assert with_tp >= 30, \
            f"Expected >= 30 rules with training_pair_ids, got {with_tp}"

        # Some should have version_origen from _cambios
        assert with_version >= 50, \
            f"Expected >= 50 rules with version_origen, got {with_version}"
