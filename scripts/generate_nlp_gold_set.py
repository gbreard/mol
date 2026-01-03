# -*- coding: utf-8 -*-
"""
Generar Gold Set NLP para tests
===============================

Extrae los valores NLP v10.0.0 de los 49 casos del Gold Set
y los guarda como expected values para testing.
"""

import sqlite3
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
GOLD_SET_PATH = PROJECT_ROOT / "database" / "gold_set_manual_v2.json"
OUTPUT_PATH = PROJECT_ROOT / "tests" / "nlp" / "gold_set.json"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Cargar Gold Set IDs
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    gold_ids = [str(g['id_oferta']) for g in gold_data]

    # Campos críticos a incluir en el Gold Set NLP
    campos_criticos = [
        # Ubicación
        'provincia', 'localidad', 'modalidad',
        # Rol
        'area_funcional', 'nivel_seniority', 'tiene_gente_cargo',
        # Experiencia
        'experiencia_min_anios', 'experiencia_max_anios',
        # Educación
        'nivel_educativo',
        # Condiciones
        'tipo_contrato', 'jornada_laboral',
        # Empresa
        'es_tercerizado', 'sector_empresa',
        # Metadatos
        'tipo_oferta', 'calidad_texto',
        # Skills (JSON)
        'skills_tecnicas_list', 'soft_skills_list', 'herramientas_list',
        # Otros
        'mision_rol', 'idioma_principal'
    ]

    # Obtener columnas existentes
    cursor.execute("PRAGMA table_info(ofertas_nlp)")
    columnas_existentes = {row[1] for row in cursor.fetchall()}

    # Filtrar campos que existen
    campos = [c for c in campos_criticos if c in columnas_existentes]

    print(f"Campos a extraer: {len(campos)}")
    print(f"Gold Set IDs: {len(gold_ids)}")

    # Query para obtener datos NLP + título original
    placeholders = ','.join(['?'] * len(gold_ids))
    campos_sql = ', '.join([f'n.[{c}]' for c in campos])

    query = f"""
        SELECT n.id_oferta, o.titulo, {campos_sql}
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.nlp_version = '10.0.0' AND n.id_oferta IN ({placeholders})
    """

    cursor.execute(query, gold_ids)
    rows = cursor.fetchall()

    print(f"Ofertas con NLP v10: {len(rows)}")

    # Construir Gold Set NLP
    gold_set_nlp = []
    for row in rows:
        expected = {}
        for campo in campos:
            valor = row[campo]
            # Parsear JSON si corresponde
            if campo.endswith('_list') and valor:
                try:
                    valor = json.loads(valor) if isinstance(valor, str) else valor
                except:
                    pass
            expected[campo] = valor

        gold_set_nlp.append({
            "id_oferta": str(row['id_oferta']),
            "titulo_original": row['titulo'],
            "nlp_version": "10.0.0",
            "expected": expected,
            "verified": False,  # Para marcar cuando se revise manualmente
            "notes": ""
        })

    # Crear directorio si no existe
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Guardar
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(gold_set_nlp, f, ensure_ascii=False, indent=2)

    print(f"\nGold Set NLP guardado en: {OUTPUT_PATH}")
    print(f"Total casos: {len(gold_set_nlp)}")

    # Resumen de cobertura
    print("\n" + "=" * 60)
    print("RESUMEN DE COBERTURA POR CAMPO")
    print("=" * 60)

    for campo in campos:
        con_valor = sum(1 for g in gold_set_nlp if g['expected'].get(campo) not in [None, '', [], '[]'])
        pct = (con_valor / len(gold_set_nlp) * 100) if gold_set_nlp else 0
        status = "OK" if pct >= 80 else "MEDIO" if pct >= 50 else "BAJO" if pct > 0 else "VACIO"
        print(f"  {campo:<30}: {con_valor:>3}/{len(gold_set_nlp)}  ({pct:>5.1f}%)  [{status}]")

    conn.close()
    return gold_set_nlp


if __name__ == "__main__":
    main()
