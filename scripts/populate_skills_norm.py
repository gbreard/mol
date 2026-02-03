#!/usr/bin/env python3
"""
Poblar tabla ofertas_skills_norm desde JSON existentes.

Este script extrae skills de:
1. ofertas_esco_matching.skills_oferta_json
2. ofertas_esco_skills_detalle (si tiene datos)

Y los normaliza en ofertas_skills_norm.

Uso:
    python scripts/populate_skills_norm.py
    python scripts/populate_skills_norm.py --limit 100
    python scripts/populate_skills_norm.py --dry-run
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"


def get_connection() -> sqlite3.Connection:
    """Obtener conexión a la BD."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def check_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Verificar si una tabla existe."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def create_table_if_not_exists(conn: sqlite3.Connection) -> None:
    """Crear tabla si no existe (ejecutar migración)."""
    migration_path = PROJECT_ROOT / "database" / "migrations" / "021_skills_normalized.sql"

    if migration_path.exists():
        print(f"Ejecutando migración: {migration_path.name}")
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Ejecutar cada statement por separado
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError as e:
                    if 'already exists' not in str(e):
                        print(f"  Warning: {e}")

        conn.commit()
        print("  Migración completada")
    else:
        print(f"ERROR: No se encontró la migración en {migration_path}")


def get_ofertas_with_skills(
    conn: sqlite3.Connection,
    limit: Optional[int] = None
) -> List[Tuple[int, str, str]]:
    """
    Obtener ofertas con skills JSON.

    Returns:
        Lista de (id_oferta, skills_json, run_id)
    """
    query = """
        SELECT
            id_oferta,
            skills_oferta_json,
            run_id
        FROM ofertas_esco_matching
        WHERE skills_oferta_json IS NOT NULL
          AND skills_oferta_json != '[]'
          AND skills_oferta_json != ''
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor = conn.execute(query)
    return [(row['id_oferta'], row['skills_oferta_json'], row['run_id'])
            for row in cursor.fetchall()]


def parse_skills_json(skills_json: str) -> List[Dict]:
    """
    Parsear JSON de skills.

    Maneja diferentes formatos:
    - Lista de strings: ["Python", "SQL"]
    - Lista de dicts: [{"uri": "...", "label": "Python", "score": 0.9}]
    """
    if not skills_json:
        return []

    try:
        skills = json.loads(skills_json)
    except json.JSONDecodeError:
        return []

    if not isinstance(skills, list):
        return []

    result = []
    for skill in skills:
        if isinstance(skill, str):
            # Formato simple: string
            result.append({
                'skill_uri': skill.lower().replace(' ', '_'),
                'preferred_label': skill,
                'origen': 'merged',
                'score': None,
            })
        elif isinstance(skill, dict):
            # Formato completo: dict
            result.append({
                'skill_uri': skill.get('uri') or skill.get('skill_uri') or skill.get('label', '').lower().replace(' ', '_'),
                'preferred_label': skill.get('label') or skill.get('preferred_label') or skill.get('preferred_label_es'),
                'L1': skill.get('L1'),
                'L1_nombre': skill.get('L1_nombre'),
                'L2': skill.get('L2'),
                'L2_nombre': skill.get('L2_nombre'),
                'es_digital': 1 if skill.get('es_digital') else 0,
                'origen': skill.get('origen', 'merged'),
                'score': skill.get('score'),
                'es_esencial': 1 if skill.get('es_esencial') else 0,
            })

    return result


def insert_skills(
    conn: sqlite3.Connection,
    id_oferta: int,
    skills: List[Dict],
    run_id: Optional[str],
    dry_run: bool = False
) -> int:
    """
    Insertar skills en la tabla normalizada.

    Returns:
        Número de skills insertados
    """
    if dry_run:
        return len(skills)

    inserted = 0
    for skill in skills:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO ofertas_skills_norm (
                    id_oferta, skill_uri, preferred_label,
                    L1, L1_nombre, L2, L2_nombre,
                    es_digital, origen, score, es_esencial, run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_oferta,
                skill.get('skill_uri'),
                skill.get('preferred_label'),
                skill.get('L1'),
                skill.get('L1_nombre'),
                skill.get('L2'),
                skill.get('L2_nombre'),
                skill.get('es_digital', 0),
                skill.get('origen', 'merged'),
                skill.get('score'),
                skill.get('es_esencial', 0),
                run_id,
            ))
            inserted += 1
        except sqlite3.IntegrityError as e:
            # Duplicate key - ignorar
            pass
        except Exception as e:
            print(f"  Error insertando skill para oferta {id_oferta}: {e}")

    return inserted


def get_skills_from_detalle(conn: sqlite3.Connection, limit: Optional[int] = None) -> List[Dict]:
    """
    Obtener skills desde ofertas_esco_skills_detalle si tiene datos.
    """
    # Verificar si la tabla tiene datos
    cursor = conn.execute("SELECT COUNT(*) FROM ofertas_esco_skills_detalle")
    count = cursor.fetchone()[0]

    if count == 0:
        return []

    print(f"  Encontrados {count} registros en ofertas_esco_skills_detalle")

    query = """
        SELECT
            id_oferta,
            esco_skill_uri as skill_uri,
            esco_skill_label as preferred_label,
            L1, L1_nombre, L2, L2_nombre,
            es_digital,
            origen_tipo as origen,
            score
        FROM ofertas_esco_skills_detalle
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor = conn.execute(query)
    return [dict(row) for row in cursor.fetchall()]


def main():
    parser = argparse.ArgumentParser(description='Poblar ofertas_skills_norm')
    parser.add_argument('--limit', type=int, help='Límite de ofertas a procesar')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué haría')
    parser.add_argument('--force', action='store_true', help='Recrear tabla aunque exista')
    args = parser.parse_args()

    print("=" * 60)
    print("POBLADOR DE ofertas_skills_norm")
    print("=" * 60)
    print(f"BD: {DB_PATH}")
    print(f"Dry run: {args.dry_run}")
    print(f"Limit: {args.limit or 'Sin límite'}")
    print()

    conn = get_connection()

    # Verificar/crear tabla
    if not check_table_exists(conn, 'ofertas_skills_norm') or args.force:
        create_table_if_not_exists(conn)
    else:
        print("Tabla ofertas_skills_norm ya existe")

    # Contar existentes
    cursor = conn.execute("SELECT COUNT(*) FROM ofertas_skills_norm")
    existing = cursor.fetchone()[0]
    print(f"Skills existentes en tabla: {existing}")
    print()

    # Fuente 1: ofertas_esco_matching.skills_oferta_json
    print("FUENTE 1: ofertas_esco_matching.skills_oferta_json")
    print("-" * 50)

    ofertas = get_ofertas_with_skills(conn, args.limit)
    print(f"Ofertas con skills JSON: {len(ofertas)}")

    total_skills = 0
    total_ofertas = 0

    for id_oferta, skills_json, run_id in ofertas:
        skills = parse_skills_json(skills_json)
        if skills:
            inserted = insert_skills(conn, id_oferta, skills, run_id, args.dry_run)
            total_skills += inserted
            total_ofertas += 1

            if total_ofertas % 100 == 0:
                print(f"  Procesadas {total_ofertas} ofertas, {total_skills} skills...")

    print(f"  Total: {total_ofertas} ofertas, {total_skills} skills")
    print()

    # Fuente 2: ofertas_esco_skills_detalle (si tiene datos)
    print("FUENTE 2: ofertas_esco_skills_detalle")
    print("-" * 50)

    detalle_skills = get_skills_from_detalle(conn, args.limit)
    if detalle_skills:
        detalle_count = 0
        for skill in detalle_skills:
            id_oferta = skill.pop('id_oferta')
            inserted = insert_skills(conn, id_oferta, [skill], None, args.dry_run)
            detalle_count += inserted

        print(f"  Insertados: {detalle_count} skills desde detalle")
    else:
        print("  Sin datos en ofertas_esco_skills_detalle")

    # Commit
    if not args.dry_run:
        conn.commit()
        print()
        print("COMMIT realizado")

    # Estadísticas finales
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)

    cursor = conn.execute("SELECT COUNT(*) FROM ofertas_skills_norm")
    final_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(DISTINCT id_oferta) FROM ofertas_skills_norm")
    ofertas_count = cursor.fetchone()[0]

    cursor = conn.execute("SELECT COUNT(DISTINCT skill_uri) FROM ofertas_skills_norm")
    skills_unicos = cursor.fetchone()[0]

    print(f"Total skills en tabla: {final_count}")
    print(f"Ofertas con skills: {ofertas_count}")
    print(f"Skills únicos: {skills_unicos}")

    # Top 10 skills
    print()
    print("TOP 10 SKILLS:")
    cursor = conn.execute("""
        SELECT preferred_label, COUNT(*) as cnt
        FROM ofertas_skills_norm
        WHERE preferred_label IS NOT NULL
        GROUP BY preferred_label
        ORDER BY cnt DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"  {row['preferred_label']}: {row['cnt']}")

    conn.close()
    print()
    print("Completado.")


if __name__ == '__main__':
    main()
