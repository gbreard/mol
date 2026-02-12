#!/usr/bin/env python3
"""
Migración one-time: Poblar clae_seccion y clae_descripcion_seccion en ofertas_dashboard de Supabase.

Lee clae_seccion de la BD local (ofertas_nlp) y actualiza Supabase.

Uso:
    python3 scripts/db/populate_clae_seccion.py [--dry-run]
"""

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.exports.sync_to_supabase import _get_clae_descripcion_seccion

DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "supabase_config.json"

NOMBRES_CORTOS = {
    'A': 'Agricultura y Pesca',
    'B': 'Minería',
    'C': 'Industria Manufacturera',
    'D': 'Electricidad y Gas',
    'E': 'Agua y Saneamiento',
    'F': 'Construcción',
    'G': 'Comercio',
    'H': 'Transporte y Almacenamiento',
    'I': 'Alojamiento y Gastronomía',
    'J': 'Tecnología y Comunicaciones',
    'K': 'Finanzas y Seguros',
    'L': 'Servicios Inmobiliarios',
    'M': 'Servicios Profesionales',
    'N': 'Servicios Administrativos',
    'O': 'Administración Pública',
    'P': 'Enseñanza',
    'Q': 'Salud',
    'R': 'Arte y Esparcimiento',
    'S': 'Otros Servicios',
    'Z': 'Otros Sectores',
}


def main():
    dry_run = '--dry-run' in sys.argv

    # 1. Leer clae_seccion de BD local
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT n.id_oferta, n.clae_seccion
        FROM ofertas_nlp n
        INNER JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado', 'validado_auto', 'validado_claude')
    """)
    rows = cur.fetchall()
    conn.close()

    print(f"Ofertas en BD local con matching validado: {len(rows)}")

    # Contar cobertura
    with_clae = [r for r in rows if r['clae_seccion']]
    without_clae = [r for r in rows if not r['clae_seccion']]
    print(f"  Con CLAE sección: {len(with_clae)}")
    print(f"  Sin CLAE sección: {len(without_clae)}")

    if not with_clae:
        print("No hay datos CLAE para poblar.")
        return

    # 2. Conectar a Supabase
    config = json.load(open(CONFIG_PATH))
    from supabase import create_client
    client = create_client(config['url'], config['service_role_key'])

    # 3. Leer todas las ofertas de Supabase (paginado)
    print("\nLeyendo ofertas de Supabase...")
    all_supabase = []
    offset = 0
    PAGE_SIZE = 1000
    while True:
        result = client.table('ofertas_dashboard').select('id_oferta').range(offset, offset + PAGE_SIZE - 1).execute()
        if not result.data:
            break
        all_supabase.extend(r['id_oferta'] for r in result.data)
        if len(result.data) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    supabase_ids = set(all_supabase)
    print(f"Ofertas en Supabase: {len(supabase_ids)}")

    # 4. Preparar updates
    updates = []
    for row in with_clae:
        id_oferta = str(row['id_oferta'])
        if id_oferta not in supabase_ids:
            continue
        seccion = row['clae_seccion']
        descripcion = NOMBRES_CORTOS.get(seccion.upper().strip()) if seccion else None
        updates.append({
            'id_oferta': id_oferta,
            'clae_seccion': seccion,
            'clae_descripcion_seccion': descripcion,
        })

    print(f"Ofertas a actualizar: {len(updates)}")

    if dry_run:
        print("\n[DRY-RUN] No se ejecutan cambios.")
        # Mostrar distribución
        from collections import Counter
        dist = Counter(u['clae_descripcion_seccion'] for u in updates)
        print("\nDistribución por sector:")
        for sec, cnt in dist.most_common():
            print(f"  {cnt:4d}  {sec}")
        return

    # 5. Ejecutar updates uno por uno (UPDATE, no upsert)
    updated = 0
    errors = 0
    for i, u in enumerate(updates):
        try:
            client.table('ofertas_dashboard').update({
                'clae_seccion': u['clae_seccion'],
                'clae_descripcion_seccion': u['clae_descripcion_seccion'],
            }).eq('id_oferta', u['id_oferta']).execute()
            updated += 1
            if (i + 1) % 200 == 0:
                print(f"  Progreso: {updated}/{len(updates)} actualizadas")
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  ERROR en {u['id_oferta']}: {e}")

    print(f"\nTotal actualizado: {updated}/{len(updates)}")


if __name__ == '__main__':
    main()
