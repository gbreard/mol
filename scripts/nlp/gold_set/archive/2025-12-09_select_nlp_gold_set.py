# -*- coding: utf-8 -*-
"""
Seleccionar 20 ofertas variadas para Gold Set NLP
=================================================

Categorias:
- 5 Ventas/Comercial
- 5 IT/Sistemas
- 5 Admin/RRHH/Contable
- 5 Produccion/Operaciones

Criterios:
- descripcion >= 200 caracteres
- titulo variado
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"

# Keywords por categoria
CATEGORIAS = {
    "ventas": ["vendedor", "ventas", "comercial", "asesor comercial", "ejecutivo de ventas", "promotor"],
    "it": ["desarrollador", "programador", "analista sistemas", "it", "software", "devops", "frontend", "backend"],
    "admin": ["administrativo", "asistente", "recepcionista", "recursos humanos", "rrhh", "contador", "contable", "tesorero"],
    "produccion": ["operario", "produccion", "logistica", "deposito", "almacen", "chofer", "tecnico", "mantenimiento", "electromecanico"]
}

def select_offers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    selected = {}

    for categoria, keywords in CATEGORIAS.items():
        # Build LIKE conditions for keywords
        like_conditions = " OR ".join([f"LOWER(titulo) LIKE '%{kw}%'" for kw in keywords])

        query = f"""
            SELECT id_oferta, titulo, LENGTH(descripcion) as desc_len
            FROM ofertas
            WHERE descripcion IS NOT NULL
              AND LENGTH(descripcion) > 200
              AND ({like_conditions})
            ORDER BY RANDOM()
            LIMIT 5
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        selected[categoria] = []
        for row in rows:
            selected[categoria].append({
                "id_oferta": str(row[0]),
                "titulo": row[1],
                "desc_len": row[2]
            })

    conn.close()
    return selected

def main():
    print("=" * 70)
    print("SELECCION DE OFERTAS PARA GOLD SET NLP")
    print("=" * 70)

    offers = select_offers()

    all_ids = []

    for categoria, lista in offers.items():
        print(f"\n## {categoria.upper()} ({len(lista)} ofertas)")
        print("-" * 50)
        for o in lista:
            print(f"  {o['id_oferta']}: {o['titulo'][:50]}... ({o['desc_len']} chars)")
            all_ids.append(o['id_oferta'])

    print("\n" + "=" * 70)
    print(f"TOTAL: {len(all_ids)} ofertas seleccionadas")
    print("=" * 70)

    # Output IDs for NLP processing
    print("\n## IDs para procesar con NLP v8:")
    print(" ".join(all_ids))

    # Save to JSON for reference
    output_path = Path(__file__).parent / "nlp_gold_set_candidates.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total": len(all_ids),
            "ids": all_ids,
            "by_category": offers
        }, f, indent=2, ensure_ascii=False)

    print(f"\nGuardado en: {output_path}")

    return all_ids

if __name__ == "__main__":
    main()
