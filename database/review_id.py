#!/usr/bin/env python3
"""Script para revisar un ID específico."""
import sqlite3
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def review_id(id_oferta):
    conn = sqlite3.connect('bumeran_scraping.db')
    conn.row_factory = sqlite3.Row

    # Scraping original
    print('='*70)
    print('DATOS SCRAPING ORIGINAL')
    print('='*70)
    cur = conn.execute('''
        SELECT titulo, descripcion
        FROM ofertas WHERE id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        print(f"titulo: {row['titulo']}")
        desc = row['descripcion'] or ''
        print(f"descripcion: {desc[:500]}...")

    # NLP Data
    print()
    print('='*70)
    print('DATOS NLP')
    print('='*70)
    cur = conn.execute('''
        SELECT titulo_limpio, area_funcional, nivel_seniority,
               tareas_explicitas, sector_empresa, mision_rol,
               skills_tecnicas_list, soft_skills_list
        FROM ofertas_nlp WHERE id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            val = row[key]
            if val:
                val_str = str(val)
                if len(val_str) > 300:
                    val_str = val_str[:300] + '...'
                print(f'{key}: {val_str}')

    # Matching Data
    print()
    print('='*70)
    print('RESULTADO MATCHING')
    print('='*70)
    cur = conn.execute('''
        SELECT isco_code, esco_occupation_uri, esco_occupation_label,
               occupation_match_score, occupation_match_method
        FROM ofertas_esco_matching WHERE id_oferta = ?
    ''', (id_oferta,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            print(f'{key}: {row[key]}')

    # Top Skills
    print()
    print('='*70)
    print('TOP 15 SKILLS EXTRAIDAS')
    print('='*70)
    cur = conn.execute('''
        SELECT skill_mencionado, match_score, esco_skill_type
        FROM ofertas_esco_skills_detalle
        WHERE id_oferta = ?
        ORDER BY match_score DESC
        LIMIT 15
    ''', (id_oferta,))
    for row in cur.fetchall():
        skill = row[0][:55] if row[0] else '?'
        score = row[1] or 0
        tipo = row[2] or '?'
        print(f'  {skill:<55} score={score:.3f} tipo={tipo}')

    conn.close()

if __name__ == "__main__":
    id_oferta = sys.argv[1] if len(sys.argv) > 1 else '1117941805'
    review_id(id_oferta)
