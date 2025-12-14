# -*- coding: utf-8 -*-
"""Mostrar casos NLP con texto original y valores extraídos."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bumeran_scraping.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener 5 casos con texto original y NLP
    cursor.execute('''
        SELECT
            o.id_oferta,
            o.titulo,
            o.descripcion,
            n.area_funcional,
            n.nivel_seniority,
            n.modalidad,
            n.experiencia_min_anios,
            n.jornada_laboral,
            n.mision_rol,
            n.skills_tecnicas_list,
            n.provincia,
            n.localidad,
            n.tipo_oferta,
            n.tiene_gente_cargo
        FROM ofertas o
        JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        WHERE n.nlp_version = '10.0.0'
        LIMIT 5
    ''')

    for i, row in enumerate(cursor.fetchall(), 1):
        print("=" * 80)
        print(f"CASO {i} - ID: {row['id_oferta']}")
        print("=" * 80)
        print(f"\nTITULO: {row['titulo']}")
        print(f"\nDESCRIPCION (primeros 600 chars):")
        desc = row['descripcion'] or ''
        print(desc[:600] + "..." if len(desc) > 600 else desc)
        print(f"\n--- VALORES EXTRAIDOS (NLP v10) ---")
        print(f"  Area Funcional:    {row['area_funcional']}")
        print(f"  Seniority:         {row['nivel_seniority']}")
        print(f"  Modalidad:         {row['modalidad']}")
        print(f"  Exp Min (anios):   {row['experiencia_min_anios']}")
        print(f"  Jornada:           {row['jornada_laboral']}")
        print(f"  Provincia:         {row['provincia']}")
        print(f"  Localidad:         {row['localidad']}")
        print(f"  Tipo Oferta:       {row['tipo_oferta']}")
        print(f"  Tiene gente cargo: {row['tiene_gente_cargo']}")

        # Skills
        skills = row['skills_tecnicas_list']
        if skills:
            try:
                skills_list = json.loads(skills) if isinstance(skills, str) else skills
                if isinstance(skills_list, list):
                    print(f"  Skills tecnicas:   {', '.join(skills_list[:5])}")
                else:
                    print(f"  Skills tecnicas:   {skills[:80]}")
            except:
                print(f"  Skills tecnicas:   {str(skills)[:80]}")
        else:
            print(f"  Skills tecnicas:   N/A")

        # Mision
        mision = row['mision_rol']
        if mision:
            mision_trunc = mision[:120] + "..." if len(mision) > 120 else mision
            print(f"  Mision del rol:    {mision_trunc}")
        else:
            print(f"  Mision del rol:    N/A")
        print()

    conn.close()


if __name__ == "__main__":
    main()
