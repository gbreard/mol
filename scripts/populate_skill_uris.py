"""
Poblar URIs faltantes en ofertas_esco_skills_detalle.

El extractor de skills guarda el label pero no el URI.
Este script hace lookup por label normalizado y agrega el URI.

Uso:
    python scripts/populate_skill_uris.py [--dry-run]
"""

import argparse
import json
import sqlite3
from pathlib import Path


def normalize(label: str) -> str:
    """Normaliza label para comparación."""
    if not label:
        return ""
    return label.strip().lower()


def load_esco_skills(json_path: Path) -> dict:
    """Carga skills ESCO y crea índice por label normalizado."""
    print(f"Cargando {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    skills = data.get('skills', {})
    print(f"  {len(skills)} skills ESCO cargadas")

    # Crear índice por label normalizado
    label_to_uri = {}
    for uri, skill_data in skills.items():
        label = skill_data.get('label', '')
        label_norm = normalize(label)
        if label_norm:
            label_to_uri[label_norm] = {
                'uri': uri,
                'label': label,
                'description': skill_data.get('description', ''),
                'L1': skill_data.get('L1', ''),
                'L2': skill_data.get('L2', '')
            }

    print(f"  {len(label_to_uri)} labels únicos indexados")
    return label_to_uri


def get_skills_without_uri(conn: sqlite3.Connection) -> list:
    """Obtiene skills sin URI de la BD."""
    cursor = conn.execute("""
        SELECT id, esco_skill_label
        FROM ofertas_esco_skills_detalle
        WHERE (esco_skill_uri IS NULL OR esco_skill_uri = '')
          AND esco_skill_label IS NOT NULL
          AND esco_skill_label != ''
    """)

    return cursor.fetchall()


def update_skill_uri(conn: sqlite3.Connection, skill_id: int, uri: str) -> None:
    """Actualiza el URI de una skill."""
    conn.execute("""
        UPDATE ofertas_esco_skills_detalle
        SET esco_skill_uri = ?
        WHERE id = ?
    """, (uri, skill_id))


def main():
    parser = argparse.ArgumentParser(description='Poblar URIs faltantes en skills')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se haría')
    args = parser.parse_args()

    # Paths
    base_path = Path(__file__).parent.parent
    db_path = base_path / 'database' / 'bumeran_scraping.db'
    json_path = base_path / 'database' / 'embeddings' / 'esco_skills_full.json'

    print("=== Poblar URIs en ofertas_esco_skills_detalle ===\n")

    # 1. Cargar índice ESCO
    label_to_uri = load_esco_skills(json_path)

    # 2. Conectar a BD
    print(f"\nConectando a {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 3. Obtener skills sin URI
    print("Buscando skills sin URI...")
    skills_sin_uri = get_skills_without_uri(conn)
    print(f"  {len(skills_sin_uri)} skills sin URI")

    if not skills_sin_uri:
        print("\n✓ Todas las skills ya tienen URI")
        conn.close()
        return

    # 4. Procesar
    matched = 0
    not_matched = 0
    not_matched_labels = set()

    print(f"\nProcesando{' (dry-run)' if args.dry_run else ''}...")

    for row in skills_sin_uri:
        skill_id = row['id']
        label = row['esco_skill_label']
        label_norm = normalize(label)

        if label_norm in label_to_uri:
            uri = label_to_uri[label_norm]['uri']
            matched += 1

            if not args.dry_run:
                update_skill_uri(conn, skill_id, uri)
        else:
            not_matched += 1
            if len(not_matched_labels) < 50:  # Limitar para no llenar la consola
                not_matched_labels.add(label)

    if not args.dry_run:
        conn.commit()

    conn.close()

    # 5. Resumen
    print(f"\n=== RESUMEN ===")
    print(f"Total procesadas: {len(skills_sin_uri)}")
    print(f"Con match ESCO:   {matched} ({matched/len(skills_sin_uri)*100:.1f}%)")
    print(f"Sin match ESCO:   {not_matched} ({not_matched/len(skills_sin_uri)*100:.1f}%)")

    if not_matched_labels:
        print(f"\nLabels sin match en ESCO (primeros {len(not_matched_labels)}):")
        for label in sorted(not_matched_labels)[:20]:
            print(f"  - {label}")

    if args.dry_run:
        print("\n[DRY-RUN] No se realizaron cambios. Ejecutar sin --dry-run para aplicar.")
    else:
        print(f"\n✓ {matched} URIs actualizados en la BD")


if __name__ == '__main__':
    main()
