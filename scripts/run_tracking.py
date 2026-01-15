#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Tracking v2.0 - Sistema de versionado por corridas (BD-centric)
====================================================================

Cada ejecución del pipeline crea un "run" que vincula:
- Ofertas procesadas
- Snapshot de configs usadas
- Métricas resultantes

**v2.0**: Todo se guarda en BD (tabla pipeline_runs), no en archivos JSON.

Uso:
    from scripts.run_tracking import RunTracker

    tracker = RunTracker()
    run_id = tracker.create_run(offer_ids=[...], source="gold_set_100")
    # ... ejecutar pipeline ...
    tracker.save_results(run_id, metricas={...})
"""

import json
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Paths
BASE = Path(__file__).parent.parent
METRICS_DIR = BASE / "metrics"
RUNS_DIR = METRICS_DIR / "runs"  # Backup de configs (opcional)
CONFIG_DIR = BASE / "config"
DB_DIR = BASE / "database"
DB_PATH = DB_DIR / "bumeran_scraping.db"

# Configs a incluir en snapshot
CONFIGS_TO_SNAPSHOT = [
    "matching_config.json",
    "matching_rules_business.json",
    "sector_isco_compatibilidad.json",
    "skills_weights.json",
    "nlp_inference_rules.json",
    "nlp_titulo_limpieza.json",
    "nlp_normalization.json",
]


class RunTracker:
    """Gestiona corridas del pipeline con versionado en BD."""

    VERSION = "2.0.0"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_conn(self) -> sqlite3.Connection:
        """Obtiene conexión a la BD."""
        return sqlite3.connect(str(self.db_path))

    def create_run(
        self,
        offer_ids: List[str],
        source: str = "manual",
        description: str = ""
    ) -> str:
        """
        Crea una nueva corrida.

        Args:
            offer_ids: Lista de IDs de ofertas a procesar
            source: Origen de los IDs (gold_set_100, manual, etc)
            description: Descripción opcional del run

        Returns:
            run_id: Identificador único de la corrida
        """
        timestamp = datetime.now()
        run_id = f"run_{timestamp.strftime('%Y%m%d_%H%M')}"

        # Snapshot de configs (archivos como backup)
        run_config_dir = RUNS_DIR / f"{run_id}_config"
        run_config_dir.mkdir(exist_ok=True)
        config_versions = self._snapshot_configs(run_config_dir)
        config_files = self._get_config_contents()

        # Obtener info de git
        git_info = self._get_git_info()

        # Obtener versiones de pipelines
        pipeline_versions = self._get_pipeline_versions()

        # Insertar en BD
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO pipeline_runs (
                run_id, timestamp, source, description,
                git_branch, git_commit, nlp_version, matching_version,
                config_snapshot, config_files, ofertas_count, ofertas_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id,
            timestamp.isoformat(),
            source,
            description,
            git_info.get("branch", "unknown"),
            git_info.get("commit", "unknown"),
            pipeline_versions.get("nlp", "unknown"),
            pipeline_versions.get("matching", "unknown"),
            json.dumps(config_versions, ensure_ascii=False),
            json.dumps(config_files, ensure_ascii=False),
            len(offer_ids),
            json.dumps([str(id) for id in offer_ids], ensure_ascii=False)
        ))

        conn.commit()
        conn.close()

        print(f"[RUN] Creado: {run_id}")
        print(f"[RUN] Ofertas: {len(offer_ids)}")
        print(f"[RUN] Guardado en BD: pipeline_runs")

        return run_id

    def _snapshot_configs(self, target_dir: Path) -> Dict[str, str]:
        """Copia configs actuales y extrae versiones."""
        versions = {}

        for config_name in CONFIGS_TO_SNAPSHOT:
            config_path = CONFIG_DIR / config_name
            if config_path.exists():
                # Copiar archivo
                shutil.copy2(config_path, target_dir / config_name)

                # Extraer versión
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    version = data.get("version") or data.get("_version") or "unknown"
                    versions[config_name.replace(".json", "")] = version
                except:
                    versions[config_name.replace(".json", "")] = "error"

        return versions

    def _get_config_contents(self) -> Dict[str, dict]:
        """Obtiene contenido completo de configs para reproducibilidad."""
        contents = {}

        for config_name in CONFIGS_TO_SNAPSHOT:
            config_path = CONFIG_DIR / config_name
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        contents[config_name] = json.load(f)
                except:
                    contents[config_name] = {"error": "Could not read"}

        return contents

    def _get_git_info(self) -> Dict[str, str]:
        """Obtiene branch y commit actual."""
        try:
            branch = subprocess.check_output(
                ["git", "-C", str(BASE), "branch", "--show-current"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            commit = subprocess.check_output(
                ["git", "-C", str(BASE), "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            return {"branch": branch, "commit": commit}
        except:
            return {"branch": "unknown", "commit": "unknown"}

    def _get_pipeline_versions(self) -> Dict[str, str]:
        """Extrae versiones de los pipelines principales."""
        versions = {}

        # NLP version
        nlp_path = DB_DIR / "process_nlp_from_db_v11.py"
        if nlp_path.exists():
            versions["nlp"] = "11.3.0"

        # Matching version
        match_path = DB_DIR / "match_ofertas_v3.py"
        if match_path.exists():
            try:
                content = match_path.read_text(encoding='utf-8')
                if 'VERSION = "' in content:
                    import re
                    m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
                    if m:
                        versions["matching"] = m.group(1)
            except:
                pass
            if "matching" not in versions:
                versions["matching"] = "3.2.3"

        # Skills extractor version
        skills_path = DB_DIR / "skills_implicit_extractor.py"
        if skills_path.exists():
            versions["skills_extractor"] = "2.0"

        return versions

    def save_results(
        self,
        run_id: str,
        metricas: Dict,
        errores_por_tipo: Optional[Dict] = None,
        comparacion: Optional[Dict] = None
    ) -> bool:
        """
        Guarda resultados de una corrida en BD.

        Args:
            run_id: ID del run
            metricas: Dict con total, correctos, errores, precision, etc
            errores_por_tipo: Dict con conteo por tipo de error
            comparacion: Dict con comparación vs run anterior

        Returns:
            True si se guardó correctamente
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Preparar detalle de errores
        metricas_detalle = errores_por_tipo or {}

        # Preparar comparación
        run_anterior = None
        diff_mejoras = None
        diff_regresiones = None
        diff_sin_cambio = None

        if comparacion:
            run_anterior = comparacion.get("run_anterior")
            diff_mejoras = comparacion.get("mejoras")
            diff_regresiones = comparacion.get("regresiones")
            diff_sin_cambio = comparacion.get("sin_cambio")

        cur.execute('''
            UPDATE pipeline_runs SET
                metricas_total = ?,
                metricas_correctos = ?,
                metricas_parciales = ?,
                metricas_errores = ?,
                metricas_precision = ?,
                metricas_detalle = ?,
                run_anterior = ?,
                diff_mejoras = ?,
                diff_regresiones = ?,
                diff_sin_cambio = ?
            WHERE run_id = ?
        ''', (
            metricas.get("total"),
            metricas.get("correctos"),
            metricas.get("parciales"),
            metricas.get("errores"),
            metricas.get("precision") or metricas.get("precision_estricta"),
            json.dumps(metricas_detalle, ensure_ascii=False),
            run_anterior,
            diff_mejoras,
            diff_regresiones,
            diff_sin_cambio,
            run_id
        ))

        conn.commit()
        conn.close()

        print(f"[RUN] Resultados guardados en BD: {run_id}")
        return True

    def get_run(self, run_id: str) -> Optional[Dict]:
        """Carga metadata de un run desde BD."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute('SELECT * FROM pipeline_runs WHERE run_id = ?', (run_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            result = dict(row)
            # Parsear JSON fields
            if result.get("config_snapshot"):
                result["config_versions"] = json.loads(result["config_snapshot"])
            if result.get("ofertas_ids"):
                result["ofertas_ids"] = json.loads(result["ofertas_ids"])
            if result.get("metricas_detalle"):
                result["errores_por_tipo"] = json.loads(result["metricas_detalle"])
            return result
        return None

    def get_run_results(self, run_id: str) -> Optional[Dict]:
        """Carga resultados de un run (compatibilidad con v1)."""
        run = self.get_run(run_id)
        if run and run.get("metricas_total") is not None:
            return {
                "run_id": run_id,
                "metricas": {
                    "total": run.get("metricas_total"),
                    "correctos": run.get("metricas_correctos"),
                    "parciales": run.get("metricas_parciales"),
                    "errores": run.get("metricas_errores"),
                    "precision": run.get("metricas_precision"),
                },
                "errores_por_tipo": run.get("errores_por_tipo"),
                "comparacion_vs_anterior": {
                    "run_anterior": run.get("run_anterior"),
                    "mejoras": run.get("diff_mejoras"),
                    "regresiones": run.get("diff_regresiones"),
                    "sin_cambio": run.get("diff_sin_cambio"),
                } if run.get("run_anterior") else None
            }
        return None

    def list_runs(self, limit: int = 10) -> List[Dict]:
        """Lista los últimos runs desde BD."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute('''
            SELECT run_id, timestamp, source, description,
                   matching_version, ofertas_count, metricas_precision
            FROM pipeline_runs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        runs = [dict(row) for row in cur.fetchall()]
        conn.close()
        return runs

    def get_latest_run(self) -> Optional[str]:
        """Obtiene el run_id más reciente."""
        runs = self.list_runs(limit=1)
        return runs[0]["run_id"] if runs else None

    def get_validated_ids(self, offer_ids: List[str]) -> List[str]:
        """
        Verifica cuáles IDs están validados (no se pueden reprocesar).

        Args:
            offer_ids: Lista de IDs a verificar

        Returns:
            Lista de IDs que están validados
        """
        if not offer_ids:
            return []

        conn = self._get_conn()
        cur = conn.cursor()

        placeholders = ','.join(['?' for _ in offer_ids])
        cur.execute(f'''
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE id_oferta IN ({placeholders})
            AND estado_validacion = 'validado'
        ''', offer_ids)

        validated = [row[0] for row in cur.fetchall()]
        conn.close()

        return validated


def test_run_tracking():
    """Test básico del sistema de runs."""
    print("=" * 50)
    print("TEST: RunTracker v2.0 (BD-centric)")
    print("=" * 50)

    tracker = RunTracker()

    # Listar runs existentes
    print("\nRuns existentes en BD:")
    for run in tracker.list_runs(limit=5):
        print(f"  - {run['run_id']}: {run.get('ofertas_count', 0)} ofertas, "
              f"precision={run.get('metricas_precision', 'N/A')}")

    # Obtener run baseline
    print("\nDetalles run baseline:")
    baseline = tracker.get_run("run_baseline_20260113")
    if baseline:
        print(f"  Run ID: {baseline['run_id']}")
        print(f"  Timestamp: {baseline['timestamp']}")
        print(f"  Source: {baseline['source']}")
        print(f"  Ofertas: {baseline['ofertas_count']}")
        print(f"  Matching version: {baseline['matching_version']}")

    print("\n[OK] RunTracker v2.0 funcionando correctamente")


if __name__ == "__main__":
    test_run_tracking()
