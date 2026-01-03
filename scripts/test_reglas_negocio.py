# -*- coding: utf-8 -*-
"""Test de reglas de negocio v2.2 sobre los 10 casos con errores."""
import sys
import sqlite3
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.match_ofertas_v2 import (
    nivel_1_5_reglas_negocio,
    match_oferta_v2_bge,
    load_all_configs,
    get_semantic_matcher
)

# Los 10 casos con errores identificados
CASOS_ERROR = [
    {"id": "1118027941", "titulo": "Dibujante Tecnico", "isco_esperado": "3118"},
    {"id": "1118028027", "titulo": "OPERADOR DE AUTOELEVADORES", "isco_esperado": "8344"},
    {"id": "1118018714", "titulo": "Diseñador Gráfico E-commerce", "isco_esperado": "2166"},
    {"id": "1117995368", "titulo": "ASESOR TÉCNICO NUTRICIÓN ANIMAL RUMIANTES", "isco_esperado": "3240"},
    {"id": "2162667", "titulo": "Gerente de Operaciones - Gastronomía", "isco_esperado": "1412"},
    {"id": "1118026729", "titulo": "Responsable de Deposito", "isco_esperado": "4321"},
    {"id": "1118027276", "titulo": "Ejecutivo de Cuentas SSR/SR", "isco_esperado": "3322"},
    {"id": "1117984105", "titulo": "Gerente de Ventas", "isco_esperado": "1221"},
    {"id": "1118018461", "titulo": "Asesor/a de Admisiones", "isco_esperado": "2359"},
    {"id": "1117977340", "titulo": "RECEPCIONISTA ADMINISTRATIVO", "isco_esperado": "4226"},
]

def main():
    # Conectar BD
    db_path = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=" * 80)
    print("TEST REGLAS DE NEGOCIO v2.2 - 10 CASOS CON ERRORES")
    print("=" * 80)

    corregidos = 0

    for caso in CASOS_ERROR:
        print(f"\n{'='*60}")
        print(f"ID: {caso['id']}")
        print(f"Título: {caso['titulo']}")
        print(f"ISCO Esperado: {caso['isco_esperado']}")

        # Obtener datos NLP de BD
        cursor.execute("""
            SELECT
                o.titulo,
                n.titulo_limpio,
                n.skills_tecnicas_list,
                n.tareas_explicitas,
                n.nivel_seniority,
                n.tiene_gente_cargo,
                n.sector_empresa,
                n.mision_rol
            FROM ofertas o
            LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
            WHERE o.id_oferta = ?
        """, (caso["id"],))

        row = cursor.fetchone()
        if not row:
            print(f"  ERROR: No encontrado en BD")
            continue

        oferta_nlp = {
            "titulo": row[0],
            "titulo_limpio": row[1],
            "skills_tecnicas_list": row[2],
            "tareas_explicitas": row[3],
            "nivel_seniority": row[4],
            "tiene_gente_cargo": row[5],
            "sector_empresa": row[6],
            "mision_rol": row[7]
        }

        print(f"  titulo_limpio: {oferta_nlp.get('titulo_limpio')}")
        print(f"  skills: {oferta_nlp.get('skills_tecnicas_list')[:100] if oferta_nlp.get('skills_tecnicas_list') else 'N/A'}...")

        # Probar reglas de negocio
        resultado = nivel_1_5_reglas_negocio(oferta_nlp, conn)

        if resultado:
            isco_obtenido = resultado.get("isco_code")
            metodo = resultado.get("metodo")
            esco_label = resultado.get("esco_label")

            match = "OK" if isco_obtenido == caso["isco_esperado"] else "PARCIAL"
            if match == "OK":
                corregidos += 1

            print(f"\n  REGLA APLICADA: {metodo}")
            print(f"  ISCO obtenido: {isco_obtenido}")
            print(f"  ESCO label: {esco_label}")
            print(f"  Resultado: {match}")
        else:
            print(f"\n  SIN REGLA APLICADA - continuaría a matching semántico")

    print("\n" + "=" * 80)
    print(f"RESUMEN: {corregidos}/10 casos corregidos por reglas de negocio")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    main()
