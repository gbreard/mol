#!/usr/bin/env python3
"""
RAG Context Builder - NLP v5.0
===============================

Genera contexto automático para extracción LLM desde:
- ESCO skills dictionary (~13,890 skills)
- Mejores extracciones históricas (top confidence)
- Estadísticas salariales por nivel
- Mapeo de niveles educativos

Uso:
    from rag.context_builder import generate_rag_context

    context = generate_rag_context()
    print(context)
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class RAGContextBuilder:
    """Constructor de contexto RAG para extracción NLP"""

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: Path a la base de datos SQLite
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "database" / "bumeran_scraping.db"

        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

    def _get_connection(self):
        """Retorna conexión a la base de datos"""
        return sqlite3.connect(self.db_path)

    def get_esco_skills_dictionary(self, limit: int = None) -> List[Dict[str, str]]:
        """
        Obtiene diccionario completo de ESCO skills

        Args:
            limit: Limitar cantidad de skills (None = todas)

        Returns:
            Lista de dicts con {uri, label, description}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                skill_uri,
                preferred_label_es,
                description_es
            FROM esco_skills
            WHERE skill_type IS NOT NULL
            ORDER BY preferred_label_es
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)

        skills = []
        for row in cursor.fetchall():
            skills.append({
                "uri": row[0],
                "label": row[1],
                "description": row[2] or ""
            })

        conn.close()
        return skills

    def get_top_extractions(self, limit: int = 50, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """
        Obtiene mejores extracciones históricas como ejemplos

        Args:
            limit: Cantidad de ejemplos
            min_confidence: Confianza mínima requerida

        Returns:
            Lista de extracciones de alta calidad
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                h.id_oferta,
                h.nlp_version,
                h.extracted_data,
                h.quality_score,
                h.confidence_score,
                o.descripcion
            FROM ofertas_nlp_history h
            JOIN ofertas o ON h.id_oferta = o.id_oferta
            WHERE h.confidence_score >= ?
              AND h.is_active = 1
            ORDER BY h.quality_score DESC, h.confidence_score DESC
            LIMIT ?
        """, (min_confidence, limit))

        examples = []
        for row in cursor.fetchall():
            examples.append({
                "id_oferta": row[0],
                "version": row[1],
                "extracted_data": json.loads(row[2]) if row[2] else {},
                "quality_score": row[3],
                "confidence_score": row[4],
                "descripcion_sample": row[5][:500] if row[5] else ""  # Primeros 500 chars
            })

        conn.close()
        return examples

    def get_salary_statistics(self) -> Dict[str, Any]:
        """
        Calcula estadísticas salariales desde datos históricos

        Returns:
            Dict con MIN/MAX/AVG por moneda
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                JSON_EXTRACT(extracted_data, '$.moneda') as moneda,
                COUNT(*) as count,
                AVG(CAST(JSON_EXTRACT(extracted_data, '$.salario_min') AS REAL)) as avg_min,
                AVG(CAST(JSON_EXTRACT(extracted_data, '$.salario_max') AS REAL)) as avg_max,
                MIN(CAST(JSON_EXTRACT(extracted_data, '$.salario_min') AS REAL)) as min_min,
                MAX(CAST(JSON_EXTRACT(extracted_data, '$.salario_max') AS REAL)) as max_max
            FROM ofertas_nlp_history
            WHERE JSON_EXTRACT(extracted_data, '$.salario_min') IS NOT NULL
              AND JSON_EXTRACT(extracted_data, '$.moneda') IS NOT NULL
              AND is_active = 1
            GROUP BY moneda
        """)

        stats = {}
        for row in cursor.fetchall():
            moneda = row[0] or "desconocida"
            stats[moneda] = {
                "count": row[1],
                "avg_min": round(row[2], 2) if row[2] else None,
                "avg_max": round(row[3], 2) if row[3] else None,
                "min_min": round(row[4], 2) if row[4] else None,
                "max_max": round(row[5], 2) if row[5] else None
            }

        conn.close()
        return stats

    def get_education_mapping(self) -> Dict[str, str]:
        """
        Retorna mapeo estándar de niveles educativos para Argentina

        Returns:
            Dict con niveles educativos y sus variantes
        """
        return {
            "Secundario": [
                "secundario completo", "secundaria completa",
                "bachiller", "polimodal", "escuela secundaria"
            ],
            "Terciario": [
                "terciario completo", "terciaria completa",
                "tecnicatura", "profesor", "profesorado"
            ],
            "Universitario": [
                "universitario completo", "universidad completa",
                "licenciatura", "ingenieria", "grado universitario"
            ],
            "Posgrado": [
                "posgrado", "maestria", "master",
                "especializacion", "doctorado", "phd"
            ],
            "Primario": [
                "primario completo", "primaria completa",
                "escuela primaria", "educacion basica"
            ]
        }

    def build_context(self,
                     include_skills: bool = True,
                     include_examples: bool = True,
                     include_salaries: bool = True,
                     include_education: bool = True,
                     max_skills: int = None,
                     max_examples: int = 50) -> str:
        """
        Construye contexto RAG completo en formato texto para LLM

        Args:
            include_skills: Incluir diccionario ESCO skills
            include_examples: Incluir ejemplos de buenas extracciones
            include_salaries: Incluir estadísticas salariales
            include_education: Incluir mapeo educativo
            max_skills: Límite de skills (None = todas)
            max_examples: Cantidad de ejemplos a incluir

        Returns:
            String con contexto RAG formateado
        """
        context_parts = []

        # Header
        context_parts.append("=" * 80)
        context_parts.append("CONTEXTO RAG PARA EXTRACCIÓN NLP - v5.0")
        context_parts.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        context_parts.append("=" * 80)
        context_parts.append("")

        # 1. ESCO Skills Dictionary
        if include_skills:
            skills = self.get_esco_skills_dictionary(limit=max_skills)
            context_parts.append("## 1. DICCIONARIO DE SKILLS VÁLIDAS (ESCO)")
            context_parts.append(f"Total skills disponibles: {len(skills):,}")
            context_parts.append("")
            context_parts.append("Ejemplos de skills válidas:")
            for skill in skills[:20]:  # Mostrar primeras 20 como muestra
                context_parts.append(f"  - {skill['label']}")
                if skill['description']:
                    context_parts.append(f"    ({skill['description'][:100]}...)")
            context_parts.append("")
            if max_skills:
                context_parts.append(f"(Mostrando {min(20, len(skills))} de {len(skills)} skills)")
            else:
                context_parts.append(f"(Mostrando 20 skills de muestra)")
            context_parts.append("")

        # 2. Ejemplos de buenas extracciones
        if include_examples:
            examples = self.get_top_extractions(limit=max_examples)
            context_parts.append("## 2. EJEMPLOS DE EXTRACCIONES DE ALTA CALIDAD")
            context_parts.append(f"Total ejemplos: {len(examples)}")
            context_parts.append("")

            for i, ex in enumerate(examples[:3], 1):  # Mostrar top 3 completos
                context_parts.append(f"### Ejemplo {i} (Quality: {ex['quality_score']}, Confidence: {ex['confidence_score']:.2f})")
                context_parts.append(f"Descripción: {ex['descripcion_sample']}")
                context_parts.append("")
                context_parts.append("Datos extraídos:")
                context_parts.append(json.dumps(ex['extracted_data'], indent=2, ensure_ascii=False))
                context_parts.append("")

        # 3. Estadísticas salariales
        if include_salaries:
            salary_stats = self.get_salary_statistics()
            context_parts.append("## 3. RANGOS SALARIALES TÍPICOS")
            context_parts.append("")

            for moneda, stats in salary_stats.items():
                context_parts.append(f"### {moneda}:")
                context_parts.append(f"  Registros analizados: {stats['count']:,}")
                if stats['avg_min']:
                    context_parts.append(f"  Salario mínimo promedio: {stats['avg_min']:,.2f}")
                if stats['avg_max']:
                    context_parts.append(f"  Salario máximo promedio: {stats['avg_max']:,.2f}")
                if stats['min_min']:
                    context_parts.append(f"  Rango total: {stats['min_min']:,.2f} - {stats['max_max']:,.2f}")
                context_parts.append("")

        # 4. Mapeo educativo
        if include_education:
            education_map = self.get_education_mapping()
            context_parts.append("## 4. NIVELES EDUCATIVOS (ARGENTINA)")
            context_parts.append("")

            for nivel, variantes in education_map.items():
                context_parts.append(f"### {nivel}:")
                context_parts.append(f"  Variantes: {', '.join(variantes)}")
                context_parts.append("")

        # Footer
        context_parts.append("=" * 80)
        context_parts.append("FIN DEL CONTEXTO RAG")
        context_parts.append("=" * 80)

        return "\n".join(context_parts)

    def save_context_to_file(self, output_path: str = None, **kwargs):
        """
        Genera y guarda contexto RAG en archivo

        Args:
            output_path: Path de salida (default: ./rag_context.txt)
            **kwargs: Argumentos para build_context()
        """
        if output_path is None:
            output_path = Path(__file__).parent / "rag_context.txt"

        context = self.build_context(**kwargs)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(context)

        print(f"[OK] Contexto RAG guardado en: {output_path}")
        print(f"     Tamaño: {len(context):,} caracteres")

        return output_path


def generate_rag_context(**kwargs) -> str:
    """
    Función helper para generar contexto RAG rápidamente

    Args:
        **kwargs: Argumentos para RAGContextBuilder.build_context()

    Returns:
        String con contexto RAG
    """
    builder = RAGContextBuilder()
    return builder.build_context(**kwargs)


# Script de prueba
if __name__ == '__main__':
    print("=" * 80)
    print("TEST: Generador de Contexto RAG v5.0")
    print("=" * 80)
    print()

    builder = RAGContextBuilder()

    # Test 1: Contar ESCO skills
    print("[1/4] Cargando ESCO skills...")
    skills = builder.get_esco_skills_dictionary()
    print(f"      Total skills disponibles: {len(skills):,}")
    print(f"      Ejemplo: {skills[0]['label']}")
    print()

    # Test 2: Obtener ejemplos
    print("[2/4] Obteniendo mejores extracciones...")
    examples = builder.get_top_extractions(limit=10)
    print(f"      Ejemplos encontrados: {len(examples)}")
    if examples:
        print(f"      Top quality score: {examples[0]['quality_score']}")
        print(f"      Top confidence: {examples[0]['confidence_score']:.2f}")
    print()

    # Test 3: Estadísticas salariales
    print("[3/4] Calculando estadísticas salariales...")
    salary_stats = builder.get_salary_statistics()
    print(f"      Monedas encontradas: {list(salary_stats.keys())}")
    for moneda, stats in salary_stats.items():
        print(f"      {moneda}: {stats['count']:,} registros")
    print()

    # Test 4: Generar contexto completo
    print("[4/4] Generando contexto RAG completo...")
    output_file = builder.save_context_to_file(
        max_skills=100,  # Limitar a 100 skills por performance
        max_examples=10
    )
    print()

    print("[OK] Test completado exitosamente!")
    print(f"     Archivo generado: {output_file}")
