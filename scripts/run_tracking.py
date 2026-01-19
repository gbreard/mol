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

    VERSION = "2.2.0"  # v2.2: Flujo optimización → validación humana

    # Umbral de convergencia: cuando tasa < 5%, el sistema está maduro
    UMBRAL_CONVERGENCIA = 5.0

    # Estados válidos para lotes
    ESTADOS_LOTE = {
        "optimizacion": "Claude iterando, creando reglas",
        "listo_validacion": "Convergido, esperando validación humana",
        "en_validacion": "Humano revisando en Google Sheets",
        "validado": "Humano aprobó, listo para producción",
        "rechazado": "Humano pidió más trabajo"
    }

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

    def _count_learning_metrics(self) -> Dict[str, int]:
        """
        Cuenta las reglas/configs para métricas de evolución.

        Returns:
            Dict con conteos de reglas, sinónimos, empresas, etc.
        """
        counts = {
            "reglas_negocio": 0,
            "reglas_validacion": 0,
            "sinonimos": 0,
            "empresas_catalogo": 0
        }

        # Contar reglas de negocio
        rules_path = CONFIG_DIR / "matching_rules_business.json"
        if rules_path.exists():
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                counts["reglas_negocio"] = len(data.get("reglas_forzar_isco", {}))
            except:
                pass

        # Contar reglas de validación
        valid_path = CONFIG_DIR / "validation_rules.json"
        if valid_path.exists():
            try:
                with open(valid_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                counts["reglas_validacion"] = len(data.get("reglas_validacion", []))
            except:
                pass

        # Contar sinónimos argentinos
        sin_path = CONFIG_DIR / "sinonimos_argentinos_esco.json"
        if sin_path.exists():
            try:
                with open(sin_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                counts["sinonimos"] = len(data.get("ocupaciones_titulo", {}))
            except:
                pass

        # Contar empresas en catálogo
        emp_path = CONFIG_DIR / "empresas_catalogo.json"
        if emp_path.exists():
            try:
                with open(emp_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                counts["empresas_catalogo"] = len(data.get("empleadores", {})) + len(data.get("intermediarios", {}))
            except:
                pass

        return counts

    def _get_previous_run_counts(self) -> Dict[str, int]:
        """Obtiene conteos del run anterior para calcular delta."""
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute('''
            SELECT reglas_negocio_count, reglas_validacion_count,
                   sinonimos_count, empresas_catalogo_count
            FROM pipeline_runs
            WHERE reglas_negocio_count > 0
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "reglas_negocio": row[0] or 0,
                "reglas_validacion": row[1] or 0,
                "sinonimos": row[2] or 0,
                "empresas_catalogo": row[3] or 0
            }
        return {"reglas_negocio": 0, "reglas_validacion": 0, "sinonimos": 0, "empresas_catalogo": 0}

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

        # Obtener métricas de aprendizaje
        learning_counts = self._count_learning_metrics()
        prev_counts = self._get_previous_run_counts()
        delta_reglas = learning_counts["reglas_negocio"] - prev_counts["reglas_negocio"]

        # Insertar en BD
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO pipeline_runs (
                run_id, timestamp, source, description,
                git_branch, git_commit, nlp_version, matching_version,
                config_snapshot, config_files, ofertas_count, ofertas_ids,
                reglas_negocio_count, reglas_validacion_count,
                sinonimos_count, empresas_catalogo_count, delta_reglas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps([str(id) for id in offer_ids], ensure_ascii=False),
            learning_counts["reglas_negocio"],
            learning_counts["reglas_validacion"],
            learning_counts["sinonimos"],
            learning_counts["empresas_catalogo"],
            delta_reglas
        ))

        conn.commit()
        conn.close()

        print(f"[RUN] Creado: {run_id}")
        print(f"[RUN] Ofertas: {len(offer_ids)}")
        print(f"[RUN] Reglas negocio: {learning_counts['reglas_negocio']} (delta: {'+' if delta_reglas >= 0 else ''}{delta_reglas})")
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
        comparacion: Optional[Dict] = None,
        errores_detectados: int = 0,
        errores_corregidos: int = 0,
        errores_escalados: int = 0
    ) -> bool:
        """
        Guarda resultados de una corrida en BD.

        Args:
            run_id: ID del run
            metricas: Dict con total, correctos, errores, precision, etc
            errores_por_tipo: Dict con conteo por tipo de error
            comparacion: Dict con comparación vs run anterior
            errores_detectados: Cantidad de errores detectados por validación
            errores_corregidos: Cantidad auto-corregidos
            errores_escalados: Cantidad que requieren reglas nuevas

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
                diff_sin_cambio = ?,
                errores_detectados = ?,
                errores_corregidos = ?,
                errores_escalados = ?
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
            errores_detectados,
            errores_corregidos,
            errores_escalados,
            run_id
        ))

        conn.commit()
        conn.close()

        print(f"[RUN] Resultados guardados en BD: {run_id}")
        if errores_detectados > 0:
            print(f"[RUN] Errores: {errores_detectados} detectados, {errores_corregidos} corregidos, {errores_escalados} escalados")

        # Registrar evento de aprendizaje automáticamente
        try:
            learning_counts = self._count_learning_metrics()
            prev_counts = self._get_previous_run_counts()
            delta = learning_counts["reglas_negocio"] - prev_counts["reglas_negocio"]

            self.log_learning_event(
                evento_tipo="run_completado",
                config_modificado="pipeline_runs",
                descripcion=f"Run {run_id}: {metricas.get('total', 0)} ofertas procesadas",
                conteo_antes=prev_counts["reglas_negocio"],
                conteo_despues=learning_counts["reglas_negocio"],
                run_id=run_id,
                detalles={
                    "ofertas": metricas.get("total", 0),
                    "errores_detectados": errores_detectados,
                    "errores_corregidos": errores_corregidos,
                    "precision": metricas.get("precision")
                }
            )
        except Exception as e:
            print(f"[RUN] Warning: No se pudo registrar evento learning_history: {e}")

        return True

    def log_learning_event(
        self,
        evento_tipo: str,
        config_modificado: str,
        descripcion: str,
        conteo_antes: int,
        conteo_despues: int,
        run_id: Optional[str] = None,
        detalles: Optional[Dict] = None
    ) -> bool:
        """
        Registra un evento de aprendizaje en learning_history.

        Args:
            evento_tipo: 'regla_agregada', 'sinonimo_agregado', 'error_corregido', etc
            config_modificado: Nombre del archivo JSON modificado
            descripcion: Descripción del cambio
            conteo_antes: Cantidad antes del cambio
            conteo_despues: Cantidad después del cambio
            run_id: ID del run asociado (opcional)
            detalles: Info adicional en JSON

        Returns:
            True si se registró correctamente
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO learning_history (
                run_id, evento_tipo, config_modificado, descripcion,
                conteo_antes, conteo_despues, delta, detalles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            run_id,
            evento_tipo,
            config_modificado,
            descripcion,
            conteo_antes,
            conteo_despues,
            conteo_despues - conteo_antes,
            json.dumps(detalles or {}, ensure_ascii=False)
        ))

        conn.commit()
        conn.close()

        print(f"[LEARNING] {evento_tipo}: {descripcion} ({conteo_antes} -> {conteo_despues})")
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


    # =========================================
    # BATCH MANAGEMENT (v2.1)
    # =========================================

    def create_batch(
        self,
        nombre: str,
        descripcion: str = "",
        offer_ids: Optional[List[str]] = None
    ) -> str:
        """
        Crea un nuevo lote de aprendizaje.

        Args:
            nombre: Nombre descriptivo del lote
            descripcion: Descripción del objetivo del lote
            offer_ids: Lista de IDs de ofertas a procesar

        Returns:
            lote_id: Identificador único del lote
        """
        timestamp = datetime.now()
        lote_id = f"lote_{timestamp.strftime('%Y%m%d_%H%M')}"

        # Obtener reglas actuales como punto de inicio
        learning_counts = self._count_learning_metrics()

        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute('''
            INSERT INTO learning_batches (
                lote_id, nombre, descripcion, fecha_inicio,
                ofertas_total, ofertas_ids, reglas_inicio, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'en_proceso')
        ''', (
            lote_id,
            nombre,
            descripcion,
            timestamp.isoformat(),
            len(offer_ids) if offer_ids else 0,
            json.dumps([str(id) for id in offer_ids] if offer_ids else [], ensure_ascii=False),
            learning_counts["reglas_negocio"]
        ))

        conn.commit()
        conn.close()

        print(f"[BATCH] Creado: {lote_id}")
        print(f"[BATCH] Nombre: {nombre}")
        print(f"[BATCH] Ofertas: {len(offer_ids) if offer_ids else 0}")
        print(f"[BATCH] Reglas inicio: {learning_counts['reglas_negocio']}")

        return lote_id

    def add_run_to_batch(self, lote_id: str, run_id: str, es_final: bool = False) -> bool:
        """
        Asocia un run a un lote existente.

        Args:
            lote_id: ID del lote
            run_id: ID del run a asociar
            es_final: Si es el run final del lote

        Returns:
            True si se asoció correctamente
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Obtener orden
        cur.execute('SELECT MAX(orden) FROM batch_runs WHERE lote_id = ?', (lote_id,))
        max_orden = cur.fetchone()[0] or 0

        cur.execute('''
            INSERT OR REPLACE INTO batch_runs (lote_id, run_id, orden, es_final)
            VALUES (?, ?, ?, ?)
        ''', (lote_id, run_id, max_orden + 1, 1 if es_final else 0))

        conn.commit()
        conn.close()

        return True

    def finalize_batch(self, lote_id: str) -> Dict:
        """
        Finaliza un lote y calcula métricas de convergencia.

        Args:
            lote_id: ID del lote a finalizar

        Returns:
            Dict con métricas del lote
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Obtener reglas actuales
        learning_counts = self._count_learning_metrics()
        reglas_fin = learning_counts["reglas_negocio"]

        # Obtener reglas inicio del lote
        cur.execute('SELECT reglas_inicio, ofertas_total FROM learning_batches WHERE lote_id = ?', (lote_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"error": "Lote no encontrado"}

        reglas_inicio = row[0] or 0
        ofertas_total = row[1] or 0
        reglas_agregadas = reglas_fin - reglas_inicio

        # Calcular tasa de aprendizaje
        tasa = (reglas_agregadas / ofertas_total * 100) if ofertas_total > 0 else 0

        # Calcular cobertura estimada (ofertas sin error / total)
        # Por ahora asumimos que ofertas sin nuevas reglas = cubiertas
        ofertas_cubiertas = ofertas_total - reglas_agregadas  # Simplificación
        cobertura = (ofertas_cubiertas / ofertas_total * 100) if ofertas_total > 0 else 100

        # Actualizar lote
        cur.execute('''
            UPDATE learning_batches SET
                fecha_fin = ?,
                estado = 'completado',
                reglas_fin = ?,
                reglas_agregadas = ?,
                ofertas_cubiertas = ?,
                ofertas_nuevas_reglas = ?,
                tasa_aprendizaje = ?,
                cobertura_estimada = ?,
                updated_at = datetime('now')
            WHERE lote_id = ?
        ''', (
            datetime.now().isoformat(),
            reglas_fin,
            reglas_agregadas,
            ofertas_cubiertas,
            reglas_agregadas,
            round(tasa, 2),
            round(cobertura, 2),
            lote_id
        ))

        conn.commit()
        conn.close()

        metrics = {
            "lote_id": lote_id,
            "ofertas_total": ofertas_total,
            "reglas_inicio": reglas_inicio,
            "reglas_fin": reglas_fin,
            "reglas_agregadas": reglas_agregadas,
            "tasa_aprendizaje": round(tasa, 2),
            "cobertura_estimada": round(cobertura, 2)
        }

        print(f"[BATCH] Finalizado: {lote_id}")
        print(f"[BATCH] Reglas: {reglas_inicio} -> {reglas_fin} (+{reglas_agregadas})")
        print(f"[BATCH] Tasa aprendizaje: {tasa:.2f}%")
        print(f"[BATCH] Cobertura: {cobertura:.2f}%")

        return metrics

    def get_batch(self, lote_id: str) -> Optional[Dict]:
        """Obtiene información de un lote."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute('SELECT * FROM learning_batches WHERE lote_id = ?', (lote_id,))
        row = cur.fetchone()

        if row:
            result = dict(row)
            if result.get("ofertas_ids"):
                result["ofertas_ids"] = json.loads(result["ofertas_ids"])

            # Obtener runs del lote
            cur.execute('''
                SELECT run_id, orden, es_final
                FROM batch_runs WHERE lote_id = ?
                ORDER BY orden
            ''', (lote_id,))
            result["runs"] = [dict(r) for r in cur.fetchall()]

            conn.close()
            return result

        conn.close()
        return None

    def list_batches(self, limit: int = 10) -> List[Dict]:
        """Lista los últimos lotes."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute('''
            SELECT lote_id, nombre, estado, ofertas_total,
                   reglas_inicio, reglas_fin, reglas_agregadas,
                   tasa_aprendizaje, cobertura_estimada, fecha_inicio
            FROM learning_batches
            ORDER BY fecha_inicio DESC
            LIMIT ?
        ''', (limit,))

        batches = [dict(row) for row in cur.fetchall()]
        conn.close()
        return batches

    def get_convergence_metrics(self) -> Dict:
        """
        Calcula métricas globales de convergencia del sistema.

        Returns:
            Dict con métricas de convergencia
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Total de lotes y ofertas
        cur.execute('''
            SELECT
                COUNT(*) as total_lotes,
                SUM(ofertas_total) as total_ofertas,
                SUM(reglas_agregadas) as total_reglas_agregadas,
                AVG(tasa_aprendizaje) as tasa_promedio,
                MIN(tasa_aprendizaje) as tasa_minima,
                MAX(cobertura_estimada) as mejor_cobertura
            FROM learning_batches
            WHERE estado = 'completado'
        ''')
        row = cur.fetchone()

        # Tendencia de tasa de aprendizaje (últimos 5 lotes)
        cur.execute('''
            SELECT tasa_aprendizaje
            FROM learning_batches
            WHERE estado = 'completado' AND tasa_aprendizaje IS NOT NULL
            ORDER BY fecha_inicio DESC
            LIMIT 5
        ''')
        tasas_recientes = [r[0] for r in cur.fetchall()]

        # Reglas actuales
        learning_counts = self._count_learning_metrics()

        conn.close()

        # Calcular tendencia
        tendencia = "estable"
        if len(tasas_recientes) >= 2:
            if tasas_recientes[0] < tasas_recientes[-1] * 0.5:
                tendencia = "convergiendo"
            elif tasas_recientes[0] > tasas_recientes[-1] * 1.5:
                tendencia = "divergiendo"

        return {
            "total_lotes": row[0] or 0,
            "total_ofertas_procesadas": row[1] or 0,
            "total_reglas_agregadas": row[2] or 0,
            "reglas_actuales": learning_counts["reglas_negocio"],
            "tasa_promedio": round(row[3] or 0, 2),
            "tasa_minima": round(row[4] or 0, 2),
            "mejor_cobertura": round(row[5] or 0, 2),
            "tendencia": tendencia,
            "tasas_recientes": tasas_recientes
        }

    # =========================================
    # FLUJO OPTIMIZACIÓN → VALIDACIÓN HUMANA (v2.2)
    # =========================================

    def check_convergence(self, lote_id: str) -> Dict:
        """
        Verifica si el lote ha convergido y actualiza estado automáticamente.

        Si tasa < UMBRAL_CONVERGENCIA (5%):
            estado = 'listo_validacion'
        Sino:
            estado = 'optimizacion'

        Args:
            lote_id: ID del lote a verificar

        Returns:
            Dict con:
                - convergido: bool
                - tasa: float (tasa de aprendizaje actual)
                - estado: str (nuevo estado)
                - mensaje: str (descripción)
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Obtener datos actuales del lote
        cur.execute('''
            SELECT estado, ofertas_total, reglas_inicio, tasa_aprendizaje
            FROM learning_batches WHERE lote_id = ?
        ''', (lote_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return {"error": f"Lote {lote_id} no encontrado"}

        estado_actual, ofertas_total, reglas_inicio, tasa_guardada = row

        # Verificar que no está en validación o validado
        if estado_actual in ('en_validacion', 'validado'):
            conn.close()
            return {
                "convergido": True,
                "tasa": tasa_guardada or 0,
                "estado": estado_actual,
                "mensaje": f"Lote ya está en estado '{estado_actual}', no se puede modificar"
            }

        # Calcular reglas actuales y tasa
        learning_counts = self._count_learning_metrics()
        reglas_actuales = learning_counts["reglas_negocio"]
        reglas_agregadas = reglas_actuales - (reglas_inicio or 0)
        tasa = (reglas_agregadas / ofertas_total * 100) if ofertas_total > 0 else 0

        # Determinar si convergió
        convergido = tasa < self.UMBRAL_CONVERGENCIA
        nuevo_estado = 'listo_validacion' if convergido else 'optimizacion'

        # Actualizar estado y métricas
        cur.execute('''
            UPDATE learning_batches SET
                estado = ?,
                reglas_fin = ?,
                reglas_agregadas = ?,
                tasa_aprendizaje = ?,
                updated_at = datetime('now')
            WHERE lote_id = ?
        ''', (nuevo_estado, reglas_actuales, reglas_agregadas, round(tasa, 2), lote_id))

        conn.commit()
        conn.close()

        if convergido:
            mensaje = f"CONVERGIDO: Tasa {tasa:.1f}% < {self.UMBRAL_CONVERGENCIA}% - Listo para validación humana"
            print(f"[BATCH] {mensaje}")
        else:
            mensaje = f"Continuar optimizando: Tasa {tasa:.1f}% >= {self.UMBRAL_CONVERGENCIA}%"
            print(f"[BATCH] {mensaje}")

        return {
            "convergido": convergido,
            "tasa": round(tasa, 2),
            "estado": nuevo_estado,
            "reglas_agregadas": reglas_agregadas,
            "mensaje": mensaje
        }

    def send_to_human_validation(self, lote_id: str, notas: str = "") -> Dict:
        """
        Marca el lote como enviado a validación humana.

        Precondición: estado debe ser 'listo_validacion'

        Args:
            lote_id: ID del lote
            notas: Notas opcionales para el validador humano

        Returns:
            Dict con resultado de la operación
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Verificar estado actual
        cur.execute('SELECT estado, tasa_aprendizaje FROM learning_batches WHERE lote_id = ?', (lote_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return {"error": f"Lote {lote_id} no encontrado"}

        estado_actual, tasa = row

        if estado_actual == 'en_validacion':
            conn.close()
            return {"error": "El lote ya está en validación humana"}

        if estado_actual == 'validado':
            conn.close()
            return {"error": "El lote ya fue validado"}

        if estado_actual != 'listo_validacion':
            conn.close()
            return {
                "error": f"El lote está en estado '{estado_actual}'. Debe estar en 'listo_validacion' para enviar a humano.",
                "sugerencia": "Ejecutar check_convergence() primero para verificar si convergió"
            }

        # Actualizar estado
        cur.execute('''
            UPDATE learning_batches SET
                estado = 'en_validacion',
                descripcion = COALESCE(descripcion || ' | ', '') || ?,
                updated_at = datetime('now')
            WHERE lote_id = ?
        ''', (f"Enviado a validación humana: {notas}" if notas else "Enviado a validación humana", lote_id))

        conn.commit()
        conn.close()

        print(f"[BATCH] Lote {lote_id} enviado a VALIDACIÓN HUMANA")
        print(f"[BATCH] Tasa final: {tasa}%")
        print(f"[BATCH] Estado: en_validacion")

        # Registrar evento
        self.log_learning_event(
            evento_tipo="enviado_validacion",
            config_modificado="learning_batches",
            descripcion=f"Lote {lote_id} enviado a validación humana",
            conteo_antes=0,
            conteo_despues=1,
            detalles={"lote_id": lote_id, "tasa": tasa, "notas": notas}
        )

        return {
            "success": True,
            "lote_id": lote_id,
            "estado": "en_validacion",
            "mensaje": "Lote enviado a validación humana. Esperando revisión en Google Sheets."
        }

    def complete_human_validation(
        self,
        lote_id: str,
        aprobado: bool,
        errores_encontrados: int = 0,
        comentarios: str = ""
    ) -> Dict:
        """
        Registra el resultado de la validación humana.

        Args:
            lote_id: ID del lote
            aprobado: True si el humano aprobó, False si requiere más trabajo
            errores_encontrados: Cantidad de errores que encontró el humano
            comentarios: Feedback del validador humano

        Returns:
            Dict con resultado
        """
        conn = self._get_conn()
        cur = conn.cursor()

        # Verificar estado actual
        cur.execute('SELECT estado FROM learning_batches WHERE lote_id = ?', (lote_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return {"error": f"Lote {lote_id} no encontrado"}

        estado_actual = row[0]

        if estado_actual != 'en_validacion':
            conn.close()
            return {
                "error": f"El lote está en estado '{estado_actual}'. Debe estar en 'en_validacion'.",
                "sugerencia": "Solo se puede completar validación de lotes que estén siendo validados"
            }

        nuevo_estado = 'validado' if aprobado else 'rechazado'

        # Actualizar estado
        cur.execute('''
            UPDATE learning_batches SET
                estado = ?,
                fecha_fin = datetime('now'),
                errores_detectados = COALESCE(errores_detectados, 0) + ?,
                descripcion = COALESCE(descripcion || ' | ', '') || ?,
                updated_at = datetime('now')
            WHERE lote_id = ?
        ''', (
            nuevo_estado,
            errores_encontrados,
            f"Validación humana: {'APROBADO' if aprobado else 'RECHAZADO'}. {comentarios}",
            lote_id
        ))

        conn.commit()
        conn.close()

        if aprobado:
            print(f"[BATCH] Lote {lote_id} VALIDADO por humano")
            print(f"[BATCH] Estado: validado - Listo para producción")
        else:
            print(f"[BATCH] Lote {lote_id} RECHAZADO por humano")
            print(f"[BATCH] Errores encontrados: {errores_encontrados}")
            print(f"[BATCH] Estado: rechazado - Requiere más optimización")

        # Registrar evento
        self.log_learning_event(
            evento_tipo="validacion_completada",
            config_modificado="learning_batches",
            descripcion=f"Validación humana: {'aprobado' if aprobado else 'rechazado'}",
            conteo_antes=errores_encontrados if not aprobado else 0,
            conteo_despues=0 if aprobado else errores_encontrados,
            detalles={
                "lote_id": lote_id,
                "aprobado": aprobado,
                "errores_encontrados": errores_encontrados,
                "comentarios": comentarios
            }
        )

        return {
            "success": True,
            "lote_id": lote_id,
            "estado": nuevo_estado,
            "aprobado": aprobado,
            "mensaje": "Lote validado y listo para producción" if aprobado else "Lote rechazado, volver a optimizar"
        }

    def reopen_batch_for_optimization(self, lote_id: str) -> Dict:
        """
        Reabre un lote rechazado para continuar optimizando.

        Args:
            lote_id: ID del lote rechazado

        Returns:
            Dict con resultado
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute('SELECT estado FROM learning_batches WHERE lote_id = ?', (lote_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return {"error": f"Lote {lote_id} no encontrado"}

        estado_actual = row[0]

        if estado_actual != 'rechazado':
            conn.close()
            return {
                "error": f"Solo se pueden reabrir lotes rechazados. Estado actual: '{estado_actual}'"
            }

        # Actualizar reglas_inicio al valor actual (para medir nuevo delta)
        learning_counts = self._count_learning_metrics()

        cur.execute('''
            UPDATE learning_batches SET
                estado = 'optimizacion',
                reglas_inicio = ?,
                fecha_fin = NULL,
                updated_at = datetime('now')
            WHERE lote_id = ?
        ''', (learning_counts["reglas_negocio"], lote_id))

        conn.commit()
        conn.close()

        print(f"[BATCH] Lote {lote_id} REABIERTO para optimización")
        print(f"[BATCH] Reglas inicio (nuevo baseline): {learning_counts['reglas_negocio']}")

        return {
            "success": True,
            "lote_id": lote_id,
            "estado": "optimizacion",
            "mensaje": "Lote reabierto. Continuar iterando hasta convergencia."
        }

    def get_batch_state(self, lote_id: str) -> Dict:
        """
        Obtiene el estado actual de un lote con información del flujo.

        Args:
            lote_id: ID del lote

        Returns:
            Dict con estado y siguiente acción recomendada
        """
        batch = self.get_batch(lote_id)
        if not batch:
            return {"error": f"Lote {lote_id} no encontrado"}

        estado = batch.get("estado", "desconocido")
        tasa = batch.get("tasa_aprendizaje", 0)

        acciones = {
            "optimizacion": "Continuar iterando: procesar ofertas, detectar errores, crear reglas",
            "listo_validacion": "Ejecutar send_to_human_validation() para enviar a revisión",
            "en_validacion": "Esperar feedback humano, luego complete_human_validation()",
            "validado": "Lote completado. Listo para producción.",
            "rechazado": "Ejecutar reopen_batch_for_optimization() para continuar"
        }

        return {
            "lote_id": lote_id,
            "nombre": batch.get("nombre"),
            "estado": estado,
            "estado_descripcion": self.ESTADOS_LOTE.get(estado, "Desconocido"),
            "tasa_aprendizaje": tasa,
            "convergido": tasa < self.UMBRAL_CONVERGENCIA if tasa else False,
            "siguiente_accion": acciones.get(estado, "Estado desconocido"),
            "ofertas_total": batch.get("ofertas_total", 0),
            "reglas_agregadas": batch.get("reglas_agregadas", 0)
        }


def test_run_tracking():
    """Test básico del sistema de runs."""
    print("=" * 50)
    print("TEST: RunTracker v2.1 (BD-centric + Batches)")
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
