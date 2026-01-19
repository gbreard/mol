"""
Sincroniza ofertas validadas desde SQLite local a Supabase.

Uso:
    python scripts/exports/sync_to_supabase.py [--limit N] [--force]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Agregar paths del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: Instalar supabase-py: pip install supabase")
    sys.exit(1)


def load_config():
    """Carga configuración de Supabase"""
    config_path = Path(__file__).parent.parent.parent / "config" / "supabase_config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró {config_path}")

    with open(config_path) as f:
        return json.load(f)


def get_validated_offers(db_path: str, limit: int = None):
    """Obtiene ofertas validadas de SQLite"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            o.empresa,
            o.fecha_publicacion_iso as fecha_publicacion,
            o.url_oferta as url,
            o.portal,
            n.provincia,
            n.localidad,
            m.isco_code,
            m.esco_occupation_label as isco_label,
            m.occupation_match_score,
            m.occupation_match_method,
            n.modalidad,
            n.nivel_seniority,
            n.area_funcional,
            n.sector_empresa,
            n.salario_min,
            n.salario_max,
            n.skills_tecnicas_list,
            n.soft_skills_list
        FROM ofertas o
        JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE m.estado_validacion = 'validado'
        ORDER BY o.fecha_publicacion_iso DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    offers = []
    for row in rows:
        offer = dict(row)

        # Parsear skills JSON
        try:
            offer['skills_tecnicas'] = json.loads(offer['skills_tecnicas_list']) if offer['skills_tecnicas_list'] else []
        except:
            offer['skills_tecnicas'] = []

        try:
            offer['soft_skills'] = json.loads(offer['soft_skills_list']) if offer['soft_skills_list'] else []
        except:
            offer['soft_skills'] = []

        # Remover campos temporales
        del offer['skills_tecnicas_list']
        del offer['soft_skills_list']

        # Convertir tipos
        offer['salario_min'] = int(offer['salario_min']) if offer['salario_min'] else None
        offer['salario_max'] = int(offer['salario_max']) if offer['salario_max'] else None
        offer['occupation_match_score'] = float(offer['occupation_match_score']) if offer['occupation_match_score'] else None

        offers.append(offer)

    return offers


def sync_to_supabase(offers: list, supabase: Client, force: bool = False):
    """Sube ofertas a Supabase"""
    if force:
        # Limpiar tabla existente
        print("Limpiando tabla ofertas_dashboard...")
        supabase.table('ofertas_dashboard').delete().neq('id_oferta', '').execute()

    # Insertar en lotes de 50
    batch_size = 50
    total = len(offers)
    inserted = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = offers[i:i+batch_size]
        try:
            result = supabase.table('ofertas_dashboard').upsert(batch).execute()
            inserted += len(batch)
            print(f"  Progreso: {inserted}/{total} ofertas")
        except Exception as e:
            errors += len(batch)
            print(f"  ERROR en lote {i//batch_size + 1}: {e}")

    return inserted, errors


def main():
    parser = argparse.ArgumentParser(description='Sincroniza ofertas validadas a Supabase')
    parser.add_argument('--limit', type=int, help='Límite de ofertas a sincronizar')
    parser.add_argument('--force', action='store_true', help='Limpiar tabla antes de insertar')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué se sincronizaría')
    args = parser.parse_args()

    # Paths
    db_path = Path(__file__).parent.parent.parent / "database" / "bumeran_scraping.db"

    print("=" * 60)
    print("SYNC TO SUPABASE - Ofertas Validadas")
    print("=" * 60)

    # Cargar config
    config = load_config()
    print(f"Supabase URL: {config['url']}")

    # Obtener ofertas
    print(f"\nLeyendo ofertas validadas de: {db_path}")
    offers = get_validated_offers(str(db_path), args.limit)
    print(f"Ofertas encontradas: {len(offers)}")

    if not offers:
        print("No hay ofertas para sincronizar")
        return

    # Mostrar preview
    print(f"\nPreview (primera oferta):")
    preview = offers[0]
    for k, v in list(preview.items())[:10]:
        print(f"  {k}: {v}")

    if args.dry_run:
        print("\n[DRY RUN] No se realizaron cambios")
        return

    # Conectar a Supabase
    print("\nConectando a Supabase...")
    supabase = create_client(config['url'], config['service_role_key'])

    # Sincronizar
    print(f"\nSincronizando {len(offers)} ofertas...")
    inserted, errors = sync_to_supabase(offers, supabase, args.force)

    print("\n" + "=" * 60)
    print(f"RESULTADO:")
    print(f"  Insertadas: {inserted}")
    print(f"  Errores: {errors}")
    print("=" * 60)


if __name__ == '__main__':
    main()
