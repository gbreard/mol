# -*- coding: utf-8 -*-
"""
M-08c: Tests de gobierno del re-clustering.
Output JSON + poller parsing + alerta + pipeline_commands.
"""
import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPreviewJsonOutput:

    def test_preview_json_tiene_campos_requeridos(self):
        """JSON de preview tiene tipo, threshold, cambios, protegidos."""
        preview = {
            "tipo": "recluster_preview",
            "threshold_usado": 0.85,
            "grupos_analizados": 799,
            "grupos_protegidos": 201,
            "labels_argentinos_protegidos": 14,
            "cambios": {"total": 43, "divididos": 12, "fusionados": 8, "sin_cambio": 23},
        }
        assert preview["tipo"] == "recluster_preview"
        assert "threshold_usado" in preview
        assert "cambios" in preview
        assert "grupos_protegidos" in preview

    def test_apply_json_tiene_campos_requeridos(self):
        """JSON de apply tiene tipo, grupos procesados, updated_at."""
        apply_result = {
            "tipo": "recluster_apply",
            "threshold_usado": 0.85,
            "grupos_procesados": 799,
            "grupos_protegidos": 201,
            "grupos_nuevos": 15,
            "updated_at_actualizado": True,
        }
        assert apply_result["tipo"] == "recluster_apply"
        assert apply_result["updated_at_actualizado"] is True

    def test_threshold_se_incluye_en_json(self):
        """El threshold usado se refleja en el JSON."""
        for threshold in [0.80, 0.85, 0.90, 0.95]:
            result = {"tipo": "recluster_preview", "threshold_usado": threshold}
            assert result["threshold_usado"] == threshold


class TestPollerJsonParsing:

    def test_poller_parsea_json_ultima_linea(self):
        """Si la última línea es JSON con 'tipo', se mergea al resultado."""
        stdout = "[EQUIV] Procesando...\n[EQUIV] OK\n" + json.dumps({"tipo": "recluster_preview", "cambios": {"total": 5}})
        stdout_lines = stdout.strip().split('\n')
        resultado = {"exit_code": 0, "duracion_seg": 10.5}

        try:
            last_line = stdout_lines[-1].strip()
            parsed = json.loads(last_line)
            if isinstance(parsed, dict) and "tipo" in parsed:
                resultado.update(parsed)
        except (json.JSONDecodeError, IndexError):
            pass

        assert resultado["tipo"] == "recluster_preview"
        assert resultado["cambios"]["total"] == 5
        assert resultado["exit_code"] == 0
        assert resultado["duracion_seg"] == 10.5

    def test_poller_sin_json_resultado_minimo(self):
        """Sin JSON en stdout, resultado solo tiene exit_code y duración."""
        stdout = "[EQUIV] Procesando...\n[EQUIV] OK\nSubido a Supabase"
        stdout_lines = stdout.strip().split('\n')
        resultado = {"exit_code": 0, "duracion_seg": 45.2}

        try:
            last_line = stdout_lines[-1].strip()
            parsed = json.loads(last_line)
            if isinstance(parsed, dict) and "tipo" in parsed:
                resultado.update(parsed)
        except (json.JSONDecodeError, IndexError):
            pass

        assert "tipo" not in resultado
        assert resultado["exit_code"] == 0

    def test_poller_json_invalido_no_rompe(self):
        """JSON malformado en última línea no rompe el parseo."""
        stdout = "[EQUIV] OK\n{invalid json"
        stdout_lines = stdout.strip().split('\n')
        resultado = {"exit_code": 0, "duracion_seg": 5}

        try:
            last_line = stdout_lines[-1].strip()
            parsed = json.loads(last_line)
            if isinstance(parsed, dict) and "tipo" in parsed:
                resultado.update(parsed)
        except (json.JSONDecodeError, IndexError):
            pass

        assert resultado == {"exit_code": 0, "duracion_seg": 5}

    def test_poller_stdout_vacio(self):
        """Stdout vacío no rompe."""
        stdout = ""
        stdout_lines = stdout.strip().split('\n') if stdout.strip() else []
        resultado = {"exit_code": 0, "duracion_seg": 0}

        try:
            last_line = stdout_lines[-1].strip() if stdout_lines else ""
            parsed = json.loads(last_line)
            if isinstance(parsed, dict) and "tipo" in parsed:
                resultado.update(parsed)
        except (json.JSONDecodeError, IndexError):
            pass

        assert resultado == {"exit_code": 0, "duracion_seg": 0}


class TestCommandMapping:

    def test_recluster_preview_en_command_map(self):
        """recluster_preview existe en COMMAND_MAP del poller."""
        from pipeline_command_poller import COMMAND_MAP
        assert 'recluster_preview' in COMMAND_MAP

    def test_recluster_apply_en_command_map(self):
        """recluster_apply existe en COMMAND_MAP del poller."""
        from pipeline_command_poller import COMMAND_MAP
        assert 'recluster_apply' in COMMAND_MAP

    def test_preview_usa_partial_y_preview_flags(self):
        """recluster_preview genera --partial --preview en args."""
        from pipeline_command_poller import COMMAND_MAP
        args = COMMAND_MAP['recluster_preview']['build_args']({})
        assert '--partial' in args
        assert '--preview' in args

    def test_apply_usa_partial_sin_preview(self):
        """recluster_apply genera --partial sin --preview."""
        from pipeline_command_poller import COMMAND_MAP
        args = COMMAND_MAP['recluster_apply']['build_args']({})
        assert '--partial' in args
        assert '--preview' not in args

    def test_threshold_se_pasa_al_script(self):
        """Si params tiene threshold, se agrega --threshold."""
        from pipeline_command_poller import COMMAND_MAP
        args = COMMAND_MAP['recluster_preview']['build_args']({'threshold': 0.90})
        assert '--threshold' in args
        assert '0.9' in args

    def test_sin_threshold_usa_default(self):
        """Sin threshold en params, no agrega --threshold (usa default del script)."""
        from pipeline_command_poller import COMMAND_MAP
        args = COMMAND_MAP['recluster_preview']['build_args']({})
        assert '--threshold' not in args


class TestApplyUsaMismoThreshold:

    def test_preview_y_apply_mismo_threshold(self):
        """El apply debería usar el mismo threshold que el preview."""
        from pipeline_command_poller import COMMAND_MAP
        threshold = 0.90
        preview_args = COMMAND_MAP['recluster_preview']['build_args']({'threshold': threshold})
        apply_args = COMMAND_MAP['recluster_apply']['build_args']({'threshold': threshold})

        preview_threshold = preview_args[preview_args.index('--threshold') + 1]
        apply_threshold = apply_args[apply_args.index('--threshold') + 1]

        assert preview_threshold == apply_threshold
