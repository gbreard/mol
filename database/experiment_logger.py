#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Experiment Logger - Sistema de Metricas para MOL
=================================================

VERSION: 1.0.0
FECHA: 2025-12-07
ISSUE: MOL-48

Sistema centralizado para persistir y comparar resultados de experimentos.
Permite trackear precision, timing y comparar versiones del pipeline.

Uso:
    from experiment_logger import ExperimentLogger

    logger = ExperimentLogger()

    # Loguear experimento
    logger.log_experiment(
        name="matching_v83_baseline",
        metrics={"precision": 0.789, "recall": 0.75},
        config={"use_reranker": True, "weights": [0.5, 0.4, 0.1]}
    )

    # Timer para medir componentes
    with logger.timer("reranker"):
        # codigo del reranker
        pass

    # Comparar experimentos
    logger.compare_experiments("matching_v83_baseline", "matching_v84_sin_reranker")
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import hashlib


# Paths
BASE_DIR = Path(__file__).parent.parent
METRICS_DIR = BASE_DIR / "metrics"
EXPERIMENTS_FILE = METRICS_DIR / "experiments.json"
GOLD_SET_HISTORY_FILE = METRICS_DIR / "gold_set_history.json"
TIMING_LOGS_FILE = METRICS_DIR / "timing_logs.jsonl"


class ExperimentLogger:
    """
    Logger centralizado para experimentos del pipeline MOL.

    Guarda:
    - experiments.json: Resultados de experimentos con metricas
    - gold_set_history.json: Historico de ejecuciones del gold set
    - timing_logs.jsonl: Tiempos por componente (append-only)
    """

    def __init__(self, metrics_dir: Path = None):
        """
        Args:
            metrics_dir: Directorio para guardar metricas. Default: metrics/
        """
        self.metrics_dir = metrics_dir or METRICS_DIR
        self._ensure_metrics_dir()

        # Cache de timings para la sesion actual
        self._session_timings: Dict[str, List[float]] = {}
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _ensure_metrics_dir(self):
        """Crea el directorio metrics/ si no existe"""
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Crear archivos vacios si no existen
        experiments_file = self.metrics_dir / "experiments.json"
        if not experiments_file.exists():
            experiments_file.write_text("{}", encoding="utf-8")

        gold_set_file = self.metrics_dir / "gold_set_history.json"
        if not gold_set_file.exists():
            gold_set_file.write_text("[]", encoding="utf-8")

        # .gitkeep para que el directorio se versione
        gitkeep = self.metrics_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    def _generate_experiment_id(self, name: str) -> str:
        """Genera un ID unico para el experimento"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{name}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def log_experiment(
        self,
        name: str,
        metrics: Dict[str, float],
        config: Dict[str, Any] = None,
        description: str = "",
        tags: List[str] = None
    ) -> str:
        """
        Registra un experimento con sus metricas.

        Args:
            name: Nombre descriptivo del experimento (ej: "matching_v83_baseline")
            metrics: Dict con metricas (ej: {"precision": 0.789, "recall": 0.75})
            config: Configuracion usada (ej: {"use_reranker": True})
            description: Descripcion opcional
            tags: Tags para filtrar (ej: ["matching", "baseline"])

        Returns:
            experiment_id: ID unico del experimento
        """
        experiment_id = self._generate_experiment_id(name)

        experiment = {
            "id": experiment_id,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "config": config or {},
            "description": description,
            "tags": tags or [],
            "session_timings": dict(self._session_timings)  # Incluir timings de la sesion
        }

        # Cargar experimentos existentes
        experiments_file = self.metrics_dir / "experiments.json"
        try:
            experiments = json.loads(experiments_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            experiments = {}

        # Guardar bajo el nombre (permite sobreescribir)
        experiments[name] = experiment

        # Persistir
        experiments_file.write_text(
            json.dumps(experiments, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print(f"[EXPERIMENT] Guardado: {name} (id: {experiment_id})")
        for metric_name, value in metrics.items():
            print(f"  - {metric_name}: {value:.4f}" if isinstance(value, float) else f"  - {metric_name}: {value}")

        return experiment_id

    def log_gold_set_run(
        self,
        precision: float,
        correct: int,
        incorrect: int,
        total: int,
        errors_by_type: Dict[str, int],
        version: str = "unknown",
        notes: str = ""
    ) -> None:
        """
        Registra una ejecucion del gold set.

        Args:
            precision: Precision del run (0-100)
            correct: Cantidad de casos correctos
            incorrect: Cantidad de casos incorrectos
            total: Total de casos evaluados
            errors_by_type: Errores por tipo (ej: {"sector_funcion": 4})
            version: Version del matching (ej: "v8.3")
            notes: Notas adicionales
        """
        run = {
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "precision": precision,
            "correct": correct,
            "incorrect": incorrect,
            "total": total,
            "errors_by_type": errors_by_type,
            "notes": notes
        }

        # Cargar historial
        history_file = self.metrics_dir / "gold_set_history.json"
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            history = []

        history.append(run)

        # Persistir
        history_file.write_text(
            json.dumps(history, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print(f"[GOLD SET] Run guardado: {precision:.1f}% ({correct}/{total})")

    def log_timing(self, component: str, duration_ms: float, metadata: Dict[str, Any] = None):
        """
        Registra el tiempo de ejecucion de un componente.

        Args:
            component: Nombre del componente (ej: "reranker", "bge_m3", "rules")
            duration_ms: Duracion en milisegundos
            metadata: Datos adicionales (ej: {"batch_size": 10})
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self._session_id,
            "component": component,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        }

        # Append al archivo JSONL
        timing_file = self.metrics_dir / "timing_logs.jsonl"
        with open(timing_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # Guardar en cache de sesion
        if component not in self._session_timings:
            self._session_timings[component] = []
        self._session_timings[component].append(duration_ms)

    @contextmanager
    def timer(self, component: str, metadata: Dict[str, Any] = None):
        """
        Context manager para medir tiempo de un componente.

        Uso:
            with logger.timer("reranker"):
                # codigo que queres medir
                pass

        Args:
            component: Nombre del componente
            metadata: Datos adicionales
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.log_timing(component, duration_ms, metadata)

    def get_experiment(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un experimento por nombre.

        Args:
            name: Nombre del experimento

        Returns:
            Dict con datos del experimento o None si no existe
        """
        experiments_file = self.metrics_dir / "experiments.json"
        try:
            experiments = json.loads(experiments_file.read_text(encoding="utf-8"))
            return experiments.get(name)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def list_experiments(self, tag: str = None) -> List[Dict[str, Any]]:
        """
        Lista todos los experimentos, opcionalmente filtrados por tag.

        Args:
            tag: Tag para filtrar (opcional)

        Returns:
            Lista de experimentos
        """
        experiments_file = self.metrics_dir / "experiments.json"
        try:
            experiments = json.loads(experiments_file.read_text(encoding="utf-8"))
            result = list(experiments.values())

            if tag:
                result = [e for e in result if tag in e.get("tags", [])]

            # Ordenar por timestamp descendente
            result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return result
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def compare_experiments(self, name_a: str, name_b: str) -> Dict[str, Any]:
        """
        Compara dos experimentos.

        Args:
            name_a: Nombre del primer experimento (baseline)
            name_b: Nombre del segundo experimento

        Returns:
            Dict con comparacion de metricas y decision sugerida
        """
        exp_a = self.get_experiment(name_a)
        exp_b = self.get_experiment(name_b)

        if not exp_a:
            raise ValueError(f"Experimento '{name_a}' no encontrado")
        if not exp_b:
            raise ValueError(f"Experimento '{name_b}' no encontrado")

        metrics_a = exp_a.get("metrics", {})
        metrics_b = exp_b.get("metrics", {})

        comparison = {
            "baseline": name_a,
            "candidate": name_b,
            "timestamp": datetime.now().isoformat(),
            "metrics_comparison": {},
            "timing_comparison": {},
            "summary": {}
        }

        # Comparar metricas
        all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())
        for metric in all_metrics:
            val_a = metrics_a.get(metric, 0)
            val_b = metrics_b.get(metric, 0)
            diff = val_b - val_a
            diff_pct = (diff / val_a * 100) if val_a != 0 else 0

            comparison["metrics_comparison"][metric] = {
                "baseline": val_a,
                "candidate": val_b,
                "diff": diff,
                "diff_pct": diff_pct,
                "improved": diff > 0 if metric in ["precision", "recall", "f1"] else diff < 0
            }

        # Comparar timings si existen
        timings_a = exp_a.get("session_timings", {})
        timings_b = exp_b.get("session_timings", {})

        for component in set(timings_a.keys()) | set(timings_b.keys()):
            avg_a = sum(timings_a.get(component, [0])) / max(1, len(timings_a.get(component, [1])))
            avg_b = sum(timings_b.get(component, [0])) / max(1, len(timings_b.get(component, [1])))

            comparison["timing_comparison"][component] = {
                "baseline_avg_ms": avg_a,
                "candidate_avg_ms": avg_b,
                "speedup": avg_a / avg_b if avg_b > 0 else 0
            }

        # Generar resumen
        precision_a = metrics_a.get("precision", 0)
        precision_b = metrics_b.get("precision", 0)
        precision_diff = precision_b - precision_a

        if precision_diff >= -2:
            decision = "GO" if precision_diff >= 0 else "GO (within tolerance)"
        else:
            decision = "NO-GO"

        comparison["summary"] = {
            "precision_diff": precision_diff,
            "decision": decision,
            "reasoning": f"Precision cambio {precision_diff:+.1f}% ({precision_a:.1f}% -> {precision_b:.1f}%)"
        }

        # Imprimir comparacion
        print("\n" + "=" * 60)
        print("COMPARACION DE EXPERIMENTOS")
        print("=" * 60)
        print(f"Baseline:  {name_a}")
        print(f"Candidate: {name_b}")
        print("-" * 60)
        print("METRICAS:")
        for metric, data in comparison["metrics_comparison"].items():
            symbol = "+" if data["improved"] else "-" if data["diff"] != 0 else "="
            print(f"  {metric}: {data['baseline']:.4f} -> {data['candidate']:.4f} ({symbol}{abs(data['diff']):.4f})")

        if comparison["timing_comparison"]:
            print("-" * 60)
            print("TIMING:")
            for comp, data in comparison["timing_comparison"].items():
                print(f"  {comp}: {data['baseline_avg_ms']:.1f}ms -> {data['candidate_avg_ms']:.1f}ms ({data['speedup']:.2f}x)")

        print("-" * 60)
        print(f"DECISION: {comparison['summary']['decision']}")
        print(f"RAZON: {comparison['summary']['reasoning']}")
        print("=" * 60 + "\n")

        return comparison

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas de timing de la sesion actual.

        Returns:
            Dict con avg, min, max por componente
        """
        stats = {}
        for component, times in self._session_timings.items():
            if times:
                stats[component] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "total_ms": sum(times)
                }
        return stats

    def print_session_stats(self):
        """Imprime estadisticas de timing de la sesion actual"""
        stats = self.get_session_stats()
        if not stats:
            print("[TIMING] No hay datos de timing en esta sesion")
            return

        print("\n" + "-" * 50)
        print("TIMING DE SESION")
        print("-" * 50)
        for component, data in sorted(stats.items()):
            print(f"  {component}:")
            print(f"    - Count: {data['count']}")
            print(f"    - Avg:   {data['avg_ms']:.1f}ms")
            print(f"    - Min:   {data['min_ms']:.1f}ms")
            print(f"    - Max:   {data['max_ms']:.1f}ms")
            print(f"    - Total: {data['total_ms']:.1f}ms")
        print("-" * 50 + "\n")


# Singleton para uso global
_logger_instance = None

def get_logger() -> ExperimentLogger:
    """Obtiene la instancia singleton del logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ExperimentLogger()
    return _logger_instance


if __name__ == "__main__":
    # Test basico
    print("Testing ExperimentLogger...")

    logger = ExperimentLogger()

    # Test timer
    with logger.timer("test_component"):
        time.sleep(0.1)

    # Test log_experiment
    logger.log_experiment(
        name="test_experiment",
        metrics={"precision": 0.85, "recall": 0.80},
        config={"test": True},
        tags=["test"]
    )

    # Test log_gold_set_run
    logger.log_gold_set_run(
        precision=78.9,
        correct=15,
        incorrect=4,
        total=19,
        errors_by_type={"sector_funcion": 4},
        version="v8.3_test"
    )

    # Print stats
    logger.print_session_stats()

    print("\nTest completado. Verificar metrics/")
