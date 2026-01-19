"""
VALIDACIÓN PRE-PROCESO - Ejecutar ANTES de cualquier pipeline

Evita el error de reprocesar ofertas ya validadas.
Muestra claramente qué ofertas son NUEVAS vs ya procesadas.

Uso:
    python scripts/check_before_process.py --ids 123,456,789
    python scripts/check_before_process.py --file exports/ids_nuevos.txt
    python scripts/check_before_process.py --pendientes  # Ver todas las pendientes

Fecha: 2026-01-19
"""

import sqlite3
import argparse
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"


def check_ids_status(ids: list[str]) -> dict:
    """
    Verifica el estado de una lista de IDs.

    Returns:
        Dict con categorías: nuevas, ya_matching, validadas, sin_nlp
    """
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    result = {
        "nuevas": [],           # Tienen NLP, no tienen matching -> OK para procesar
        "ya_matching": [],      # Ya tienen matching pero no validadas -> CUIDADO
        "validadas": [],        # Ya validadas -> NO PROCESAR
        "sin_nlp": [],          # No tienen NLP -> necesitan NLP primero
    }

    for id_oferta in ids:
        id_str = str(id_oferta).strip()

        # Verificar si tiene NLP
        cur.execute("SELECT 1 FROM ofertas_nlp WHERE id_oferta = ?", (id_str,))
        tiene_nlp = cur.fetchone() is not None

        if not tiene_nlp:
            result["sin_nlp"].append(id_str)
            continue

        # Verificar si tiene matching
        cur.execute("""
            SELECT estado_validacion FROM ofertas_esco_matching
            WHERE id_oferta = ?
        """, (id_str,))
        row = cur.fetchone()

        if row is None:
            result["nuevas"].append(id_str)
        elif row[0] == "validado":
            result["validadas"].append(id_str)
        else:
            result["ya_matching"].append(id_str)

    conn.close()
    return result


def get_pendientes_matching() -> list[str]:
    """
    Obtiene IDs que tienen NLP pero NO tienen matching.
    Estas son las ofertas que realmente necesitan procesarse.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("""
        SELECT n.id_oferta
        FROM ofertas_nlp n
        LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
        WHERE m.id_oferta IS NULL
        ORDER BY n.id_oferta
    """)

    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids


def print_report(result: dict, ids_input: list[str]):
    """Imprime reporte claro del estado."""

    total = len(ids_input)

    print("=" * 60)
    print("  VALIDACIÓN PRE-PROCESO")
    print("=" * 60)
    print(f"\nIDs recibidos: {total}")
    print()

    # NUEVAS - OK para procesar
    n_nuevas = len(result["nuevas"])
    print(f"✅ NUEVAS (OK para procesar): {n_nuevas}")
    if n_nuevas > 0 and n_nuevas <= 10:
        print(f"   IDs: {', '.join(result['nuevas'])}")

    # YA MATCHING - Cuidado
    n_matching = len(result["ya_matching"])
    if n_matching > 0:
        print(f"\n⚠️  YA TIENEN MATCHING (reprocesar?): {n_matching}")
        if n_matching <= 10:
            print(f"   IDs: {', '.join(result['ya_matching'])}")

    # VALIDADAS - NO PROCESAR
    n_validadas = len(result["validadas"])
    if n_validadas > 0:
        print(f"\n🚫 YA VALIDADAS (NO PROCESAR): {n_validadas}")
        if n_validadas <= 10:
            print(f"   IDs: {', '.join(result['validadas'])}")
        print("   ⛔ Estas ofertas ya pasaron validación humana!")
        print("   ⛔ Reprocesarlas perdería el trabajo de validación!")

    # SIN NLP
    n_sin_nlp = len(result["sin_nlp"])
    if n_sin_nlp > 0:
        print(f"\n❌ SIN NLP (necesitan NLP primero): {n_sin_nlp}")
        if n_sin_nlp <= 10:
            print(f"   IDs: {', '.join(result['sin_nlp'])}")

    print()
    print("=" * 60)

    # Decisión final
    if n_validadas > 0:
        print("🚨 ATENCIÓN: Hay ofertas YA VALIDADAS en la lista!")
        print("   NO ejecutar el pipeline con estos IDs.")
        print(f"   Usar solo las {n_nuevas} ofertas NUEVAS.")
        return False
    elif n_nuevas == 0:
        print("⚠️  No hay ofertas nuevas para procesar.")
        return False
    else:
        print(f"✅ Seguro procesar {n_nuevas} ofertas nuevas.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validar IDs antes de procesar")
    parser.add_argument("--ids", help="IDs separados por coma")
    parser.add_argument("--file", help="Archivo con IDs (uno por línea)")
    parser.add_argument("--pendientes", action="store_true",
                       help="Mostrar todas las ofertas pendientes de matching")
    parser.add_argument("--export", help="Exportar IDs pendientes a archivo")

    args = parser.parse_args()

    if args.pendientes:
        pendientes = get_pendientes_matching()
        print(f"\n📋 OFERTAS PENDIENTES DE MATCHING: {len(pendientes)}")
        print("   (Tienen NLP pero NO tienen matching)")
        print()

        if len(pendientes) == 0:
            print("   ✅ No hay ofertas pendientes!")
        elif len(pendientes) <= 20:
            print(f"   IDs: {', '.join(pendientes)}")
        else:
            print(f"   Primeros 20: {', '.join(pendientes[:20])}")
            print(f"   ... y {len(pendientes) - 20} más")

        if args.export and len(pendientes) > 0:
            with open(args.export, 'w') as f:
                f.write('\n'.join(pendientes))
            print(f"\n   Exportados a: {args.export}")

        return

    # Obtener IDs de argumento o archivo
    ids = []
    if args.ids:
        ids = [x.strip() for x in args.ids.split(",")]
    elif args.file:
        with open(args.file) as f:
            ids = [line.strip() for line in f if line.strip()]
    else:
        parser.print_help()
        return

    # Verificar estado
    result = check_ids_status(ids)
    ok = print_report(result, ids)

    # Código de salida
    exit(0 if ok else 1)


if __name__ == "__main__":
    main()
