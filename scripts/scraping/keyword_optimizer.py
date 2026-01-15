"""
KeywordOptimizer - Sistema de Optimizacion de Keywords
=======================================================

Analiza, propone, versiona y mide mejoras en keywords de scraping.

Uso CLI:
    python -m database.keyword_optimizer analyze
    python -m database.keyword_optimizer propose --output v3.3
    python -m database.keyword_optimizer apply v3.3 --author "gerardo"
    python -m database.keyword_optimizer compare v3.1 v3.2
"""

import json
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class KeywordOptimizer:
    """Optimizador de keywords para scraping"""

    def __init__(self, db_path: Optional[Path] = None, config_path: Optional[Path] = None):
        """
        Args:
            db_path: Path a bumeran_scraping.db
            config_path: Path a data/config/
        """
        self.base_dir = Path(__file__).parent.parent
        self.db_path = db_path or self.base_dir / "database" / "bumeran_scraping.db"
        self.config_path = config_path or self.base_dir / "data" / "config"

        self.master_keywords_path = self.config_path / "master_keywords.json"
        self.history_path = self.config_path / "keywords_history"
        self.proposals_path = self.config_path / "keywords_proposals"
        self.changelog_path = self.history_path / "changelog.json"

        # Crear directorios si no existen
        self.history_path.mkdir(parents=True, exist_ok=True)
        self.proposals_path.mkdir(parents=True, exist_ok=True)

    def _get_db_connection(self):
        """Conexion a SQLite"""
        return sqlite3.connect(str(self.db_path))

    def _load_master_keywords(self) -> dict:
        """Carga el diccionario maestro actual"""
        if not self.master_keywords_path.exists():
            raise FileNotFoundError(f"No se encontro master_keywords.json en {self.master_keywords_path}")

        with open(self.master_keywords_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_changelog(self) -> dict:
        """Carga el changelog de versiones"""
        if not self.changelog_path.exists():
            return {"versions": [], "current_version": None, "last_updated": None}

        with open(self.changelog_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_changelog(self, changelog: dict):
        """Guarda el changelog"""
        changelog["last_updated"] = datetime.now().isoformat()[:10]
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, indent=2, ensure_ascii=False)

    def analyze(self) -> dict:
        """
        Analiza keywords_performance y retorna metricas detalladas

        Returns:
            Dict con metricas de rendimiento de keywords
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "problematic": {
                "sin_resultados": [],
                "muy_genericos": [],
                "baja_novedad": []
            },
            "efficient": [],
            "by_category": {},
            "recommendations": []
        }

        # 1. Resumen general
        cursor.execute("SELECT COUNT(DISTINCT keyword) FROM keywords_performance")
        total_keywords = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT keyword) FROM keywords_performance
            WHERE ofertas_encontradas = 0
        """)
        sin_resultados = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT keyword) FROM keywords_performance
            WHERE ofertas_encontradas > 5000
        """)
        muy_genericos = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                SUM(ofertas_encontradas) as total_encontradas,
                SUM(ofertas_nuevas) as total_nuevas
            FROM keywords_performance
        """)
        row = cursor.fetchone()
        total_encontradas = row[0] or 0
        total_nuevas = row[1] or 0
        tasa_novedad_global = (total_nuevas / total_encontradas * 100) if total_encontradas > 0 else 0

        cursor.execute("""
            SELECT AVG(ofertas_encontradas) FROM keywords_performance
            WHERE ofertas_encontradas > 0
        """)
        promedio_ofertas = cursor.fetchone()[0] or 0

        analysis["summary"] = {
            "total_keywords": total_keywords,
            "sin_resultados": sin_resultados,
            "sin_resultados_pct": round(sin_resultados / total_keywords * 100, 1) if total_keywords > 0 else 0,
            "muy_genericos": muy_genericos,
            "tasa_novedad_global": round(tasa_novedad_global, 1),
            "promedio_ofertas_por_keyword": round(promedio_ofertas, 1),
            "total_ofertas_encontradas": total_encontradas,
            "total_ofertas_nuevas": total_nuevas
        }

        # 2. Keywords sin resultados
        cursor.execute("""
            SELECT keyword FROM keywords_performance
            WHERE ofertas_encontradas = 0
            ORDER BY keyword
            LIMIT 50
        """)
        analysis["problematic"]["sin_resultados"] = [row[0] for row in cursor.fetchall()]

        # 3. Keywords muy genericos (>5000 ofertas)
        cursor.execute("""
            SELECT keyword, SUM(ofertas_encontradas) as total
            FROM keywords_performance
            GROUP BY keyword
            HAVING SUM(ofertas_encontradas) > 5000
            ORDER BY total DESC
        """)
        analysis["problematic"]["muy_genericos"] = [
            {"keyword": row[0], "ofertas": row[1]}
            for row in cursor.fetchall()
        ]

        # 4. Keywords con baja tasa de novedad (<10%)
        cursor.execute("""
            SELECT
                keyword,
                SUM(ofertas_encontradas) as encontradas,
                SUM(ofertas_nuevas) as nuevas,
                ROUND(SUM(ofertas_nuevas) * 100.0 / NULLIF(SUM(ofertas_encontradas), 0), 1) as tasa
            FROM keywords_performance
            GROUP BY keyword
            HAVING SUM(ofertas_encontradas) > 100
                AND ROUND(SUM(ofertas_nuevas) * 100.0 / NULLIF(SUM(ofertas_encontradas), 0), 1) < 10
            ORDER BY tasa ASC
            LIMIT 20
        """)
        analysis["problematic"]["baja_novedad"] = [
            {"keyword": row[0], "encontradas": row[1], "nuevas": row[2], "tasa_pct": row[3]}
            for row in cursor.fetchall()
        ]

        # 5. Keywords mas eficientes (alta novedad, buen volumen)
        cursor.execute("""
            SELECT
                keyword,
                SUM(ofertas_encontradas) as encontradas,
                SUM(ofertas_nuevas) as nuevas,
                ROUND(SUM(ofertas_nuevas) * 100.0 / NULLIF(SUM(ofertas_encontradas), 0), 1) as tasa
            FROM keywords_performance
            GROUP BY keyword
            HAVING SUM(ofertas_encontradas) BETWEEN 50 AND 2000
                AND ROUND(SUM(ofertas_nuevas) * 100.0 / NULLIF(SUM(ofertas_encontradas), 0), 1) > 50
            ORDER BY nuevas DESC
            LIMIT 20
        """)
        analysis["efficient"] = [
            {"keyword": row[0], "encontradas": row[1], "nuevas": row[2], "tasa_pct": row[3]}
            for row in cursor.fetchall()
        ]

        # 6. Distribucion por rango de ofertas
        cursor.execute("""
            SELECT
                CASE
                    WHEN ofertas_encontradas = 0 THEN 'sin_resultados'
                    WHEN ofertas_encontradas < 50 THEN 'muy_especifico'
                    WHEN ofertas_encontradas < 500 THEN 'especifico'
                    WHEN ofertas_encontradas < 2000 THEN 'moderado'
                    WHEN ofertas_encontradas < 5000 THEN 'amplio'
                    ELSE 'muy_generico'
                END as rango,
                COUNT(DISTINCT keyword) as cantidad
            FROM keywords_performance
            GROUP BY rango
            ORDER BY cantidad DESC
        """)
        analysis["distribution"] = {row[0]: row[1] for row in cursor.fetchall()}

        # 7. Generar recomendaciones
        recommendations = []

        if sin_resultados > total_keywords * 0.3:
            recommendations.append({
                "tipo": "critico",
                "mensaje": f"El {analysis['summary']['sin_resultados_pct']}% de keywords no trae resultados. Considerar eliminarlos.",
                "accion": "eliminar_sin_resultados"
            })

        if muy_genericos > 5:
            recommendations.append({
                "tipo": "alerta",
                "mensaje": f"Hay {muy_genericos} keywords muy genericos (>5000 ofertas). Considerar eliminar o reemplazar.",
                "accion": "revisar_genericos"
            })

        genericos_especificos = analysis["problematic"]["muy_genericos"]
        for g in genericos_especificos:
            if g["keyword"] == "" or len(g["keyword"]) <= 2:
                recommendations.append({
                    "tipo": "critico",
                    "mensaje": f"Keyword '{g['keyword']}' es demasiado generico ({g['ofertas']:,} ofertas). Eliminar.",
                    "accion": "eliminar_keyword",
                    "keyword": g["keyword"]
                })

        analysis["recommendations"] = recommendations

        conn.close()
        return analysis

    def propose_changes(self, analysis: Optional[dict] = None, version: str = None) -> dict:
        """
        Genera propuesta de cambios basada en analisis

        Args:
            analysis: Resultado de analyze() (si None, ejecuta analyze())
            version: Version propuesta (ej: "3.3")

        Returns:
            Dict con propuesta de cambios
        """
        if analysis is None:
            analysis = self.analyze()

        master = self._load_master_keywords()
        current_version = master.get("version", "3.2")

        if version is None:
            # Incrementar version automaticamente
            parts = current_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            version = ".".join(parts)

        proposal = {
            "version": version,
            "base_version": current_version,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "changes": {
                "remove": [],
                "add": [],
                "modify": []
            },
            "justification": [],
            "expected_impact": {}
        }

        # 1. Proponer eliminar keywords sin resultados
        sin_resultados = analysis["problematic"]["sin_resultados"]
        if sin_resultados:
            proposal["changes"]["remove"].extend([
                {"keyword": kw, "reason": "sin_resultados"}
                for kw in sin_resultados[:100]  # Limitar a 100
            ])
            proposal["justification"].append(
                f"Eliminar {len(sin_resultados)} keywords sin resultados para reducir tiempo de scraping"
            )

        # 2. Proponer eliminar keywords muy genericos problematicos
        for g in analysis["problematic"]["muy_genericos"]:
            if g["keyword"] == "" or len(g["keyword"]) <= 2:
                proposal["changes"]["remove"].append({
                    "keyword": g["keyword"],
                    "reason": f"muy_generico ({g['ofertas']:,} ofertas)"
                })
                proposal["justification"].append(
                    f"Eliminar '{g['keyword']}' por ser demasiado generico"
                )

        # 3. Calcular impacto esperado
        keywords_to_remove = len(proposal["changes"]["remove"])
        current_total = analysis["summary"]["total_keywords"]

        proposal["expected_impact"] = {
            "keywords_eliminados": keywords_to_remove,
            "keywords_final": current_total - keywords_to_remove,
            "reduccion_pct": round(keywords_to_remove / current_total * 100, 1) if current_total > 0 else 0,
            "tiempo_estimado_ahorro_min": round(keywords_to_remove * 0.5, 1)  # ~30 seg por keyword
        }

        # 4. Guardar propuesta
        proposal_path = self.proposals_path / f"v{version}_proposal.json"
        with open(proposal_path, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)

        return proposal

    def apply_version(self, version: str, author: str, description: str = None) -> bool:
        """
        Aplica propuesta: backup + cambios + changelog

        Args:
            version: Version a aplicar (ej: "3.3")
            author: Autor del cambio
            description: Descripcion opcional

        Returns:
            True si exitoso
        """
        # 1. Cargar propuesta
        proposal_path = self.proposals_path / f"v{version}_proposal.json"
        if not proposal_path.exists():
            raise FileNotFoundError(f"No se encontro propuesta para version {version}")

        with open(proposal_path, 'r', encoding='utf-8') as f:
            proposal = json.load(f)

        # 2. Cargar master actual
        master = self._load_master_keywords()
        current_version = master.get("version", "unknown")

        # 3. Backup de version actual
        backup_path = self.history_path / f"v{current_version}_{datetime.now().strftime('%Y-%m-%d')}.json"
        shutil.copy(self.master_keywords_path, backup_path)
        print(f"Backup creado: {backup_path.name}")

        # 4. Aplicar cambios
        keywords_removed = set()
        keywords_added = set()

        # Eliminar keywords de todas las estrategias
        for change in proposal["changes"]["remove"]:
            kw = change["keyword"]
            keywords_removed.add(kw)
            for strategy_name, strategy_data in master["estrategias"].items():
                if kw in strategy_data["keywords"]:
                    strategy_data["keywords"].remove(kw)

            # Eliminar de categorias tambien
            if "categorias" in master:
                for cat_name, cat_keywords in master["categorias"].items():
                    if kw in cat_keywords:
                        cat_keywords.remove(kw)

        # Agregar nuevos keywords (si hay)
        for change in proposal["changes"].get("add", []):
            kw = change["keyword"]
            strategy = change.get("strategy", "general")
            keywords_added.add(kw)
            if strategy in master["estrategias"]:
                if kw not in master["estrategias"][strategy]["keywords"]:
                    master["estrategias"][strategy]["keywords"].append(kw)

        # 5. Actualizar metadata
        master["version"] = version
        master["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
        master["nota_version"] = description or f"Optimizacion automatica: -{len(keywords_removed)} keywords"

        # 6. Guardar master actualizado
        with open(self.master_keywords_path, 'w', encoding='utf-8') as f:
            json.dump(master, f, indent=2, ensure_ascii=False)

        # 7. Actualizar changelog
        changelog = self._load_changelog()
        changelog["versions"].append({
            "version": version,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "author": author,
            "description": description or f"Optimizacion: -{len(keywords_removed)} +{len(keywords_added)} keywords",
            "changes": {
                "added": len(keywords_added),
                "removed": len(keywords_removed),
                "modified": 0
            },
            "keywords_removed": list(keywords_removed)[:50],  # Guardar primeros 50
            "keywords_added": list(keywords_added),
            "metrics_post": None  # Se actualiza despues del proximo scraping
        })
        changelog["current_version"] = version
        self._save_changelog(changelog)

        # 8. Marcar propuesta como aplicada
        proposal["status"] = "applied"
        proposal["applied_at"] = datetime.now().isoformat()
        proposal["applied_by"] = author
        with open(proposal_path, 'w', encoding='utf-8') as f:
            json.dump(proposal, f, indent=2, ensure_ascii=False)

        print(f"Version {version} aplicada exitosamente")
        print(f"  - Keywords eliminados: {len(keywords_removed)}")
        print(f"  - Keywords agregados: {len(keywords_added)}")

        return True

    def compare_versions(self, v1: str, v2: str) -> dict:
        """
        Compara metricas entre dos versiones

        Args:
            v1: Version base (ej: "3.1")
            v2: Version comparar (ej: "3.2")

        Returns:
            Dict con comparacion
        """
        changelog = self._load_changelog()

        v1_data = None
        v2_data = None

        for v in changelog["versions"]:
            if v["version"] == v1:
                v1_data = v
            if v["version"] == v2:
                v2_data = v

        if not v1_data:
            raise ValueError(f"Version {v1} no encontrada en changelog")
        if not v2_data:
            raise ValueError(f"Version {v2} no encontrada en changelog")

        comparison = {
            "v1": v1,
            "v2": v2,
            "v1_date": v1_data.get("date"),
            "v2_date": v2_data.get("date"),
            "changes": {
                "keywords_added": v2_data["changes"]["added"] - v1_data["changes"]["added"],
                "keywords_removed": v2_data["changes"]["removed"] - v1_data["changes"]["removed"]
            },
            "metrics_comparison": {}
        }

        # Comparar metricas si estan disponibles
        m1 = v1_data.get("metrics_post") or {}
        m2 = v2_data.get("metrics_post") or {}

        if m1 and m2:
            for key in m1:
                if key in m2 and m1[key] is not None and m2[key] is not None:
                    comparison["metrics_comparison"][key] = {
                        "v1": m1[key],
                        "v2": m2[key],
                        "diff": m2[key] - m1[key]
                    }

        return comparison

    def get_version_history(self) -> List[dict]:
        """Obtiene historial de versiones"""
        changelog = self._load_changelog()
        return changelog.get("versions", [])

    def update_metrics_for_version(self, version: str, metrics: dict):
        """
        Actualiza metricas post-scraping para una version

        Args:
            version: Version a actualizar
            metrics: Dict con metricas (total_keywords, sin_resultados, etc.)
        """
        changelog = self._load_changelog()

        for v in changelog["versions"]:
            if v["version"] == version:
                v["metrics_post"] = metrics
                break

        self._save_changelog(changelog)


def main():
    """CLI del KeywordOptimizer"""
    parser = argparse.ArgumentParser(
        description="Sistema de Optimizacion de Keywords",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m database.keyword_optimizer analyze
  python -m database.keyword_optimizer propose --version 3.3
  python -m database.keyword_optimizer apply 3.3 --author gerardo
  python -m database.keyword_optimizer compare 3.1 3.2
  python -m database.keyword_optimizer history
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # analyze
    parser_analyze = subparsers.add_parser("analyze", help="Analiza keywords actuales")
    parser_analyze.add_argument("--json", action="store_true", help="Output en JSON")

    # propose
    parser_propose = subparsers.add_parser("propose", help="Genera propuesta de cambios")
    parser_propose.add_argument("--version", "-v", help="Version propuesta (ej: 3.3)")

    # apply
    parser_apply = subparsers.add_parser("apply", help="Aplica propuesta de cambios")
    parser_apply.add_argument("version", help="Version a aplicar")
    parser_apply.add_argument("--author", "-a", required=True, help="Autor del cambio")
    parser_apply.add_argument("--description", "-d", help="Descripcion del cambio")

    # compare
    parser_compare = subparsers.add_parser("compare", help="Compara dos versiones")
    parser_compare.add_argument("v1", help="Version base")
    parser_compare.add_argument("v2", help="Version a comparar")

    # history
    parser_history = subparsers.add_parser("history", help="Muestra historial de versiones")

    args = parser.parse_args()

    optimizer = KeywordOptimizer()

    if args.command == "analyze":
        analysis = optimizer.analyze()

        if args.json:
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        else:
            print("=" * 70)
            print("ANALISIS DE KEYWORDS")
            print("=" * 70)
            print()

            s = analysis["summary"]
            print(f"Total keywords:        {s['total_keywords']:,}")
            print(f"Sin resultados:        {s['sin_resultados']:,} ({s['sin_resultados_pct']}%)")
            print(f"Muy genericos:         {s['muy_genericos']}")
            print(f"Tasa novedad global:   {s['tasa_novedad_global']}%")
            print(f"Promedio ofertas/kw:   {s['promedio_ofertas_por_keyword']:.0f}")
            print()

            print("DISTRIBUCION:")
            for rango, cantidad in analysis.get("distribution", {}).items():
                print(f"  {rango:20} {cantidad:4}")
            print()

            if analysis["problematic"]["muy_genericos"]:
                print("KEYWORDS MUY GENERICOS:")
                for g in analysis["problematic"]["muy_genericos"][:10]:
                    print(f"  '{g['keyword']}': {g['ofertas']:,} ofertas")
                print()

            if analysis["recommendations"]:
                print("RECOMENDACIONES:")
                for r in analysis["recommendations"]:
                    print(f"  [{r['tipo'].upper()}] {r['mensaje']}")

    elif args.command == "propose":
        proposal = optimizer.propose_changes(version=args.version)
        print("=" * 70)
        print(f"PROPUESTA v{proposal['version']}")
        print("=" * 70)
        print()
        print(f"Base: v{proposal['base_version']}")
        print(f"Keywords a eliminar: {len(proposal['changes']['remove'])}")
        print(f"Keywords a agregar:  {len(proposal['changes']['add'])}")
        print()
        print("IMPACTO ESPERADO:")
        for k, v in proposal["expected_impact"].items():
            print(f"  {k}: {v}")
        print()
        print("JUSTIFICACION:")
        for j in proposal["justification"]:
            print(f"  - {j}")
        print()
        print(f"Propuesta guardada en: keywords_proposals/v{proposal['version']}_proposal.json")

    elif args.command == "apply":
        optimizer.apply_version(args.version, args.author, args.description)

    elif args.command == "compare":
        comparison = optimizer.compare_versions(args.v1, args.v2)
        print(json.dumps(comparison, indent=2, ensure_ascii=False))

    elif args.command == "history":
        history = optimizer.get_version_history()
        print("=" * 70)
        print("HISTORIAL DE VERSIONES")
        print("=" * 70)
        for v in history:
            print(f"\nv{v['version']} ({v['date']}) - {v.get('author', 'N/A')}")
            print(f"  {v.get('description', 'Sin descripcion')}")
            print(f"  Cambios: +{v['changes']['added']} -{v['changes']['removed']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
