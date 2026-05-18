"""
Tests de disciplina de versionado:
- Los archivos *_VERSION existen
- VERSION constants en código leen del archivo (no hardcoded)
- check_version_bumped.py funciona como pre-commit guard
"""

import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "database"))
sys.path.insert(0, str(REPO / "scripts"))


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


class TestVersionFiles:
    def test_matcher_version_existe_y_es_semver(self):
        path = REPO / "database" / "MATCHER_VERSION"
        assert path.exists(), f"Falta {path}"
        content = path.read_text().strip()
        assert SEMVER_RE.match(content), f"Formato inválido: {content!r}"

    def test_nlp_version_existe_y_es_semver(self):
        path = REPO / "database" / "NLP_VERSION"
        assert path.exists(), f"Falta {path}"
        content = path.read_text().strip()
        assert SEMVER_RE.match(content), f"Formato inválido: {content!r}"


class TestVersionConstantsLeenArchivo:
    def test_matcher_v3_lee_de_archivo(self):
        from match_ofertas_v3 import MatcherV3

        expected = (REPO / "database" / "MATCHER_VERSION").read_text().strip()
        assert MatcherV3.VERSION == expected

    def test_nlp_v11_lee_de_archivo(self):
        from process_nlp_from_db_v11 import NLPExtractorV11

        expected = (REPO / "database" / "NLP_VERSION").read_text().strip()
        assert NLPExtractorV11.VERSION == expected
        assert NLPExtractorV11.NLP_VERSION_TAG == expected

    def test_run_tracking_lee_de_archivos(self):
        from run_tracking import RunTracker

        tracker = RunTracker()
        versions = tracker._get_pipeline_versions()
        assert versions["matching"] == (REPO / "database" / "MATCHER_VERSION").read_text().strip()
        assert versions["nlp"] == (REPO / "database" / "NLP_VERSION").read_text().strip()


class TestCheckVersionBumped:
    def _run_check(self, staged_files: list[str], extra_args: list[str] = None) -> int:
        from check_version_bumped import main

        with patch("check_version_bumped.staged_files", return_value=set(staged_files)):
            with patch("sys.argv", ["check_version_bumped.py"] + (extra_args or [])):
                return main()

    def test_sin_cambios_pasa(self):
        assert self._run_check([]) == 0

    def test_cambio_no_relacionado_pasa(self):
        assert self._run_check(["docs/README.md"]) == 0

    def test_cambio_matcher_sin_bump_falla(self, capsys):
        rc = self._run_check(["database/match_ofertas_v3.py"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "MATCHER_VERSION" in captured.out

    def test_cambio_matcher_con_bump_pasa(self):
        rc = self._run_check([
            "database/match_ofertas_v3.py",
            "database/MATCHER_VERSION",
        ])
        assert rc == 0

    def test_cambio_nlp_sin_bump_falla(self, capsys):
        rc = self._run_check(["database/process_nlp_from_db_v11.py"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "NLP_VERSION" in captured.out

    def test_cambio_nlp_con_bump_pasa(self):
        rc = self._run_check([
            "database/process_nlp_from_db_v11.py",
            "database/NLP_VERSION",
        ])
        assert rc == 0

    def test_allow_no_bump_bypasa(self):
        rc = self._run_check(
            ["database/match_ofertas_v3.py"],
            extra_args=["--allow-no-bump"],
        )
        assert rc == 0

    def test_cambio_doble_uno_bumpeado_otro_no_falla(self, capsys):
        rc = self._run_check([
            "database/match_ofertas_v3.py",
            "database/MATCHER_VERSION",
            "database/process_nlp_from_db_v11.py",  # sin NLP_VERSION
        ])
        assert rc == 1
        captured = capsys.readouterr()
        # Solo se reporta el archivo sin bump
        assert "process_nlp_from_db_v11.py" in captured.out
        assert "match_ofertas_v3.py" not in captured.out


class TestHookFiles:
    def test_pre_commit_hook_existe_y_es_ejecutable(self):
        hook = REPO / "scripts" / "hooks" / "pre-commit"
        assert hook.exists()
        assert hook.stat().st_mode & 0o111, "Hook no es ejecutable"

    def test_validator_es_ejecutable(self):
        validator = REPO / "scripts" / "check_version_bumped.py"
        assert validator.exists()
        assert validator.stat().st_mode & 0o111, "Validator no es ejecutable"
