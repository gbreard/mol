#!/usr/bin/env python3
"""
Reprocesa ofertas sin código CLAE usando CLAESemanticClassifier v2.1.

Solo afecta ofertas WHERE clae_code IS NULL en ofertas_nlp.
No toca ofertas ya clasificadas.

Uso:
    python scripts/db/reprocesar_clae.py --dry-run --limit 50   # preview
    python scripts/db/reprocesar_clae.py                         # completo
    python scripts/db/reprocesar_clae.py --limit 500             # parcial
"""

import sys
import argparse
import sqlite3
import time
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "database"))
sys.path.insert(0, str(PROJECT_ROOT / "config"))

DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
BATCH_SIZE = 500


def main():
    parser = argparse.ArgumentParser(description="Reprocesar ofertas sin CLAE")
    parser.add_argument("--dry-run", action="store_true", help="No actualiza BD")
    parser.add_argument("--limit", type=int, default=0, help="Limitar cantidad (0=todas)")
    args = parser.parse_args()

    # Verificar protección: contar clasificadas ANTES
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    ya_clasificadas = conn.execute(
        "SELECT COUNT(*) FROM ofertas_nlp WHERE clae_code IS NOT NULL AND clae_code != ''"
    ).fetchone()[0]
    print(f"Ofertas ya clasificadas (protegidas): {ya_clasificadas:,}")

    # Cargar modelo y classifier
    print("Cargando modelo BGE-M3...")
    from skills_implicit_extractor import SkillsImplicitExtractor
    SkillsImplicitExtractor(verbose=False)  # fuerza carga del modelo en cache

    from clae_semantic_classifier import CLAESemanticClassifier
    classifier = CLAESemanticClassifier(verbose=False)
    print("Classifier listo.")

    # Leer ofertas sin CLAE con datos necesarios
    limit_clause = f"LIMIT {args.limit}" if args.limit else ""
    rows = conn.execute(f"""
        SELECT n.id_oferta, n.sector_empresa, n.titulo_limpio, o.id_area
        FROM ofertas_nlp n
        JOIN ofertas o ON o.id_oferta = n.id_oferta
        WHERE n.clae_code IS NULL OR n.clae_code = ''
        {limit_clause}
    """).fetchall()

    total = len(rows)
    print(f"Ofertas a procesar: {total:,}")
    if args.dry_run:
        print("[DRY-RUN] No se actualizará la BD.\n")

    # Procesar
    metodos = Counter()
    secciones = Counter()
    scores = []
    clasificadas = 0
    sin_clasificar = 0
    updated = 0
    start = time.time()

    for i, row in enumerate(rows):
        id_oferta = row["id_oferta"]
        sector = row["sector_empresa"] or ""
        titulo = row["titulo_limpio"] or ""
        id_area = row["id_area"]

        id_area_str = str(id_area) if id_area else None
        result = classifier.classify(sector, titulo, id_area_portal=id_area_str)

        if result and result.get("clae_code"):
            clasificadas += 1
            metodos[result["clae_metodo"]] += 1
            secciones[result["clae_seccion"]] += 1
            scores.append(result["clae_score"])

            if not args.dry_run:
                conn.execute("""
                    UPDATE ofertas_nlp
                    SET clae_code = ?, clae_grupo = ?, clae_seccion = ?,
                        clae_score = ?, clae_metodo = ?
                    WHERE id_oferta = ?
                      AND (clae_code IS NULL OR clae_code = '')
                """, (
                    result["clae_code"], result.get("clae_grupo"),
                    result.get("clae_seccion"), result.get("clae_score"),
                    result.get("clae_metodo"), id_oferta
                ))
                updated += 1
        else:
            sin_clasificar += 1

        if (i + 1) % BATCH_SIZE == 0:
            if not args.dry_run:
                conn.commit()
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  [{i+1:>6,}/{total:,}] clasificadas={clasificadas:,} sin_clasificar={sin_clasificar:,} ({rate:.0f}/s)")

    if not args.dry_run:
        conn.commit()

    elapsed = time.time() - start

    # Verificar protección: contar clasificadas DESPUÉS
    ya_clasificadas_despues = conn.execute(
        "SELECT COUNT(*) FROM ofertas_nlp WHERE clae_code IS NOT NULL AND clae_code != ''"
    ).fetchone()[0]
    sin_clae_despues = conn.execute(
        "SELECT COUNT(*) FROM ofertas_nlp WHERE clae_code IS NULL OR clae_code = ''"
    ).fetchone()[0]

    conn.close()

    # Resumen
    avg_score = sum(scores) / len(scores) if scores else 0
    print(f"\n{'='*60}")
    print(f"RESUMEN {'(DRY-RUN)' if args.dry_run else ''}")
    print(f"{'='*60}")
    print(f"Total procesadas:    {total:,}")
    print(f"Clasificadas:        {clasificadas:,} ({clasificadas*100/total:.1f}%)")
    print(f"Sin clasificar:      {sin_clasificar:,} ({sin_clasificar*100/total:.1f}%)")
    print(f"Score promedio:      {avg_score:.3f}")
    print(f"Tiempo:              {elapsed:.1f}s ({total/elapsed:.0f} ofertas/s)")

    print(f"\nPor método:")
    for m, c in metodos.most_common():
        print(f"  {m:25s} {c:>6,}")

    print(f"\nTop secciones:")
    for s, c in secciones.most_common(10):
        print(f"  {s} {c:>6,}")

    if not args.dry_run:
        print(f"\nUPDATEs ejecutados:  {updated:,}")
        print(f"Clasificadas antes:  {ya_clasificadas:,}")
        print(f"Clasificadas después:{ya_clasificadas_despues:,}")
        delta = ya_clasificadas_despues - ya_clasificadas
        print(f"Delta:               +{delta:,}")
        if delta > updated:
            print(f"  *** ALERTA: delta > updated — posible efecto colateral ***")
        print(f"Sin CLAE restantes:  {sin_clae_despues:,}")


if __name__ == "__main__":
    main()
