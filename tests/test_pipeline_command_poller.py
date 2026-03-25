"""
Tests for pipeline_command_poller.py
Tests: command mapping, argument building, validation
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline_command_poller import COMMAND_MAP, PROJECT_DIR


class TestCommandMap:
    """Test that all commands have valid mappings."""

    EXPECTED_COMMANDS = [
        'run_pipeline', 'run_nlp', 'run_matching', 'reprocess_errors',
        'revalidate_nlp', 'revalidate_matching', 'reapply_rules',
        'export_excel', 'sync_supabase', 'sync_supabase_full', 'generate_training',
    ]

    def test_all_commands_mapped(self):
        """Every expected command has a mapping."""
        for cmd in self.EXPECTED_COMMANDS:
            assert cmd in COMMAND_MAP, f"Command '{cmd}' not in COMMAND_MAP"

    def test_no_extra_commands(self):
        """No unexpected commands in the map."""
        for cmd in COMMAND_MAP:
            assert cmd in self.EXPECTED_COMMANDS, f"Unexpected command '{cmd}' in COMMAND_MAP"

    def test_all_mappings_have_script(self):
        """Every mapping has a 'script' key."""
        for cmd, mapping in COMMAND_MAP.items():
            assert 'script' in mapping, f"Command '{cmd}' missing 'script' key"
            assert isinstance(mapping['script'], str), f"Command '{cmd}' script is not string"

    def test_all_mappings_have_build_args(self):
        """Every mapping has a callable 'build_args'."""
        for cmd, mapping in COMMAND_MAP.items():
            assert 'build_args' in mapping, f"Command '{cmd}' missing 'build_args' key"
            assert callable(mapping['build_args']), f"Command '{cmd}' build_args is not callable"

    def test_all_scripts_exist(self):
        """Every referenced script file exists."""
        for cmd, mapping in COMMAND_MAP.items():
            script_path = PROJECT_DIR / mapping['script']
            assert script_path.exists(), f"Script for '{cmd}' not found: {script_path}"


class TestArgumentBuilding:
    """Test argument building for each command."""

    def test_run_pipeline_with_limit(self):
        args = COMMAND_MAP['run_pipeline']['build_args']({'limit': 500})
        assert '--limit' in args
        assert '500' in args

    def test_run_pipeline_with_ids(self):
        args = COMMAND_MAP['run_pipeline']['build_args']({'ids': '1,2,3'})
        assert '--ids' in args
        assert '1,2,3' in args

    def test_run_nlp_with_limit(self):
        args = COMMAND_MAP['run_nlp']['build_args']({'limit': 100})
        assert '--limit' in args
        assert '100' in args

    def test_run_matching_skips_nlp(self):
        args = COMMAND_MAP['run_matching']['build_args']({'limit': 50})
        assert '--skip-nlp' in args

    def test_reprocess_errors_has_only_pending(self):
        args = COMMAND_MAP['reprocess_errors']['build_args']({})
        assert '--only-pending' in args

    def test_sync_supabase_no_args(self):
        args = COMMAND_MAP['sync_supabase']['build_args']({})
        assert args == []

    def test_sync_supabase_full_has_flag(self):
        args = COMMAND_MAP['sync_supabase_full']['build_args']({})
        assert '--full' in args

    def test_reapply_rules_no_args(self):
        args = COMMAND_MAP['reapply_rules']['build_args']({})
        assert args == []

    def test_generate_training_no_args(self):
        args = COMMAND_MAP['generate_training']['build_args']({})
        assert args == []

    def test_export_excel_has_etapa(self):
        args = COMMAND_MAP['export_excel']['build_args']({})
        assert '--etapa' in args
        assert 'completo' in args

    def test_export_excel_with_ids(self):
        args = COMMAND_MAP['export_excel']['build_args']({'ids': '10,20'})
        assert '--ids' in args
        assert '10,20' in args


class TestProjectStructure:
    """Test that the poller's assumptions about the project are correct."""

    def test_project_dir_exists(self):
        assert PROJECT_DIR.exists()

    def test_config_dir_exists(self):
        assert (PROJECT_DIR / "config").exists()

    def test_database_dir_exists(self):
        assert (PROJECT_DIR / "database").exists()

    def test_scripts_dir_exists(self):
        assert (PROJECT_DIR / "scripts").exists()

    def test_supabase_config_exists(self):
        config_path = PROJECT_DIR / "config" / "supabase_config.json"
        assert config_path.exists(), "supabase_config.json required for poller"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
