# -*- coding: utf-8 -*-
"""
Corrige nivel_seniority segun reglas de nlp_inference_rules.json

Reglas principales (correccion_por_experiencia):
- junior/trainee con 5+ años exp -> senior
- junior/trainee con 2+ años exp -> semisenior
- trainee con 1+ año exp -> junior
"""
import sqlite3
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"
CONFIG_PATH = BASE / "config" / "nlp_inference_rules.json"
GOLD_SET_PATH = BASE / "database" / "gold_set_nlp_100_ids.json"


def cargar_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def corregir_seniority(seniority_actual, exp_min, config):
    """
    Aplica reglas de correccion a seniority.
    Retorna (seniority_correcto, cambio_realizado)
    """
    if not seniority_actual or exp_min is None:
        return seniority_actual, False

    try:
        exp_min = float(exp_min)
    except (ValueError, TypeError):
        return seniority_actual, False

    correccion_config = config.get("nivel_seniority", {}).get("correccion_por_experiencia", {})
    reglas = correccion_config.get("reglas", [])

    if not reglas:
        return seniority_actual, False

    seniority_lower = seniority_actual.lower().strip()

    for regla in reglas:
        seniorities_aplicables = [s.lower() for s in regla.get("seniority_actual", [])]
        exp_requerida = regla.get("exp_min_mayor_igual", 0)
        seniority_correcto = regla.get("seniority_correcto")

        if seniority_lower in seniorities_aplicables and exp_min >= exp_requerida:
            if seniority_lower != seniority_correcto.lower():
                return seniority_correcto, True
            break

    return seniority_actual, False


def corregir_gold_set(dry_run=True):
    """Corrige seniority en ofertas del Gold Set."""
    config = cargar_config()

    # Cargar IDs
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        ids = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT id_oferta, nivel_seniority, experiencia_min_anios, titulo_limpio
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, ids)

    correcciones = []
    stats = {
        "total": 0,
        "con_seniority": 0,
        "con_experiencia": 0,
        "inconsistentes": 0
    }

    for row in c.fetchall():
        id_oferta, seniority, exp_min, titulo = row
        stats["total"] += 1

        if seniority:
            stats["con_seniority"] += 1
        if exp_min:
            stats["con_experiencia"] += 1

        seniority_nuevo, cambio = corregir_seniority(seniority, exp_min, config)

        if cambio:
            stats["inconsistentes"] += 1
            correcciones.append({
                'id': id_oferta,
                'titulo': titulo[:50] if titulo else "",
                'seniority_orig': seniority,
                'exp_min': exp_min,
                'seniority_nuevo': seniority_nuevo
            })

    print("=" * 70)
    print("DIAGNOSTICO SENIORITY - Gold Set 100")
    print("=" * 70)
    print(f"\nTotal ofertas:     {stats['total']}")
    print(f"Con seniority:     {stats['con_seniority']}")
    print(f"Con exp_min:       {stats['con_experiencia']}")
    print(f"Inconsistentes:    {stats['inconsistentes']}")
    print()

    if correcciones:
        print(f"Correcciones a aplicar: {len(correcciones)}")
        print("-" * 70)

        for corr in correcciones:
            print(f"\n{corr['id']}:")
            print(f"  Titulo: {corr['titulo']}")
            print(f"  ANTES:  nivel_seniority={corr['seniority_orig']}, exp_min={corr['exp_min']}")
            print(f"  DESPUES: nivel_seniority={corr['seniority_nuevo']}")

    else:
        print("\n[OK] No hay inconsistencias en seniority")

    if dry_run:
        print(f"\n[DRY RUN] No se modifico la BD. Usar --apply para aplicar.")
        conn.close()
        return correcciones

    # Aplicar cambios
    print("\nAplicando cambios...")
    for corr in correcciones:
        c.execute("""
            UPDATE ofertas_nlp
            SET nivel_seniority = ?
            WHERE id_oferta = ?
        """, (corr['seniority_nuevo'], corr['id']))

    conn.commit()
    print(f"[OK] {len(correcciones)} registros corregidos")
    conn.close()

    return correcciones


def mostrar_todos():
    """Muestra todos los seniority del Gold Set para revision."""
    config = cargar_config()

    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        ids = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT id_oferta, nivel_seniority, experiencia_min_anios, titulo_limpio
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
        ORDER BY experiencia_min_anios DESC NULLS LAST
    """, ids)

    print("=" * 90)
    print("TODOS LOS SENIORITY - Gold Set 100 (ordenado por exp_min DESC)")
    print("=" * 90)
    print(f"{'ID':<12} {'Seniority':<12} {'Exp':<5} {'Titulo':<50}")
    print("-" * 90)

    for row in c.fetchall():
        id_oferta, seniority, exp_min, titulo = row
        titulo_corto = (titulo[:47] + "...") if titulo and len(titulo) > 50 else (titulo or "")
        exp_str = str(int(exp_min)) if exp_min else "-"
        seniority_str = seniority or "-"

        # Marcar inconsistencias
        flag = ""
        if seniority and exp_min:
            _, cambio = corregir_seniority(seniority, exp_min, config)
            if cambio:
                flag = " ⚠️"

        print(f"{id_oferta:<12} {seniority_str:<12} {exp_str:<5} {titulo_corto}{flag}")

    conn.close()


if __name__ == "__main__":
    import sys

    if "--all" in sys.argv:
        mostrar_todos()
    else:
        dry_run = "--apply" not in sys.argv
        corregir_gold_set(dry_run=dry_run)
