#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revision Manual Gold Set v3 - Reporte detallado para validacion humana
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Imports locales
import sys
sys.path.insert(0, str(Path(__file__).parent))
from match_ofertas_v3 import MatcherV3

def load_gold_set():
    gold_path = Path(__file__).parent / "gold_set_manual_v2.json"
    with open(gold_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_oferta_completa(conn, id_oferta):
    """Obtiene todos los datos de una oferta."""
    cur = conn.execute('''
        SELECT titulo_limpio, tareas_explicitas, area_funcional,
               nivel_seniority, sector_empresa, skills_tecnicas_list,
               soft_skills_list
        FROM ofertas_nlp
        WHERE id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        "titulo_limpio": row[0],
        "tareas_explicitas": row[1],
        "area_funcional": row[2],
        "nivel_seniority": row[3],
        "sector_empresa": row[4],
        "skills_tecnicas": row[5],
        "soft_skills": row[6]
    }

def get_esco_label(conn, isco_code):
    """Busca el label ESCO para un codigo ISCO."""
    if not isco_code:
        return ""
    cur = conn.execute('''
        SELECT preferred_label_es FROM esco_occupations
        WHERE isco_code LIKE ?
        LIMIT 1
    ''', (f"%{isco_code}%",))
    row = cur.fetchone()
    return row[0] if row else ""

def main():
    print("Generando reporte de revision manual...")

    conn = sqlite3.connect('bumeran_scraping.db')
    matcher = MatcherV3(db_conn=conn, verbose=False)
    gold_set = load_gold_set()

    # Crear reporte
    reporte = []
    reporte.append("=" * 100)
    reporte.append("REVISION MANUAL - GOLD SET v3.0 MATCHING")
    reporte.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    reporte.append(f"Total casos: {len(gold_set)}")
    reporte.append("=" * 100)

    for i, caso in enumerate(gold_set, 1):
        id_oferta = caso["id_oferta"]
        gold_ok = caso.get("esco_ok", True)
        gold_isco = caso.get("isco_esperado", "")
        gold_comment = caso.get("comentario", "")

        oferta = get_oferta_completa(conn, id_oferta)
        if not oferta:
            continue

        # Ejecutar matching v3
        result = matcher.match(oferta)

        reporte.append("")
        reporte.append("-" * 100)
        reporte.append(f"CASO {i}/49 | ID: {id_oferta}")
        reporte.append("-" * 100)
        reporte.append("")
        reporte.append(f"TITULO: {oferta['titulo_limpio']}")
        reporte.append("")

        tareas = oferta['tareas_explicitas'] or "(sin tareas)"
        if len(tareas) > 200:
            tareas = tareas[:200] + "..."
        reporte.append(f"TAREAS: {tareas}")
        reporte.append("")

        reporte.append(f"CONTEXTO NLP:")
        reporte.append(f"  - Area funcional: {oferta['area_funcional'] or 'N/A'}")
        reporte.append(f"  - Seniority: {oferta['nivel_seniority'] or 'N/A'}")
        reporte.append(f"  - Sector: {oferta['sector_empresa'] or 'N/A'}")
        reporte.append("")

        reporte.append(f"RESULTADO MATCHING v3:")
        reporte.append(f"  - ISCO: {result.isco_code}")
        reporte.append(f"  - Label ESCO: {result.esco_label}")
        reporte.append(f"  - Score: {result.score:.2f}")
        reporte.append(f"  - Metodo: {result.metodo}")
        reporte.append("")

        if result.skills_matched:
            skills_show = result.skills_matched[:5]
            reporte.append(f"  - Skills matched ({len(result.skills_matched)}): {skills_show}")

        if result.alternativas:
            reporte.append(f"  - Alternativas:")
            for alt in result.alternativas[:3]:
                reporte.append(f"      {alt['isco_code']}: {alt['esco_label'][:40]} (score={alt['score']:.2f})")

        reporte.append("")
        reporte.append(f"VALIDACION GOLD SET ANTERIOR:")
        if gold_ok:
            reporte.append(f"  - Estado: OK (era correcto en v2.1)")
        else:
            reporte.append(f"  - Estado: ERROR en v2.1")
            reporte.append(f"  - ISCO esperado: {gold_isco}")
            esperado_label = get_esco_label(conn, gold_isco)
            reporte.append(f"  - Label esperado: {esperado_label}")
        reporte.append(f"  - Comentario: {gold_comment}")

        reporte.append("")
        reporte.append("VERIFICACION MANUAL:")
        reporte.append("  [ ] Correcto")
        reporte.append("  [ ] Incorrecto - ISCO esperado: ____")
        reporte.append("  [ ] Revision pendiente")
        reporte.append("  Comentario: _________________________________")

    matcher.close()
    conn.close()

    # Guardar reporte
    reporte.append("")
    reporte.append("=" * 100)
    reporte.append("FIN DEL REPORTE")
    reporte.append("=" * 100)

    output_path = Path(__file__).parent.parent / "exports" / f"revision_gold_set_v3_{datetime.now().strftime('%Y%m%d')}.txt"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(reporte))

    print(f"Reporte guardado en: {output_path}")

    # Tambien generar version Excel
    try:
        import pandas as pd

        data = []
        conn = sqlite3.connect('bumeran_scraping.db')
        matcher = MatcherV3(db_conn=conn, verbose=False)

        for caso in gold_set:
            id_oferta = caso["id_oferta"]
            oferta = get_oferta_completa(conn, id_oferta)
            if not oferta:
                continue

            result = matcher.match(oferta)

            data.append({
                'ID': id_oferta,
                'Titulo': oferta['titulo_limpio'],
                'Tareas': (oferta['tareas_explicitas'] or "")[:150],
                'Area': oferta['area_funcional'],
                'Seniority': oferta['nivel_seniority'],
                'ISCO_v3': result.isco_code,
                'Label_ESCO': result.esco_label,
                'Score': round(result.score, 2),
                'Metodo': result.metodo,
                'Skills_count': len(result.skills_matched),
                'Gold_OK_v21': caso.get("esco_ok", True),
                'Gold_ISCO': caso.get("isco_esperado", ""),
                'Gold_Comment': caso.get("comentario", ""),
                'Verificacion': '',
                'Comentario_revision': ''
            })

        matcher.close()
        conn.close()

        df = pd.DataFrame(data)
        excel_path = Path(__file__).parent.parent / "exports" / f"revision_gold_set_v3_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(excel_path, index=False, sheet_name='Gold Set v3')
        print(f"Excel guardado en: {excel_path}")

    except ImportError:
        print("pandas no disponible, solo se genero TXT")

if __name__ == "__main__":
    main()
