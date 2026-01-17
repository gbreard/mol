#!/usr/bin/env python3
"""Demo del proceso de optimización para mostrar al usuario."""
import sqlite3

DB_PATH = 'D:/OEDE/Webscrapping/database/bumeran_scraping.db'

def demo_paso1_buscar():
    """PASO 1: Buscar ofertas no validadas, ordenadas por score."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT o.id_oferta, o.titulo, o.empresa, m.isco_code, m.isco_label,
               m.score_final_ponderado, m.occupation_match_method
        FROM ofertas o
        JOIN ofertas_esco_matching m ON CAST(o.id_oferta AS TEXT) = m.id_oferta
        WHERE m.estado_validacion != 'validado'
        ORDER BY m.score_final_ponderado ASC
        LIMIT 10
    """)

    print('='*100)
    print('PASO 1: BUSCAR OFERTAS NO VALIDADAS (ordenadas por score ASC)')
    print('='*100)
    print()
    print('Las ofertas con score bajo son las primeras candidatas a revisar.')
    print()

    ofertas = []
    for row in cur.fetchall():
        id, titulo, empresa, isco, label, score, method = row
        ofertas.append(id)
        titulo_short = (titulo[:50] + '...') if titulo and len(str(titulo)) > 50 else titulo
        print(f'ID: {id}')
        print(f'  Titulo: {titulo_short}')
        print(f'  Empresa: {empresa}')
        print(f'  ISCO: {isco} - {label}')
        score_str = f'{score:.3f}' if score else 'NULL'
        print(f'  Score: {score_str} | Metodo: {method}')
        print()

    conn.close()
    return ofertas

def demo_paso2_diagnosticar(oferta_id):
    """PASO 2: Diagnosticar una oferta específica (NLP, Skills, Sector)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print('='*100)
    print(f'PASO 2: DIAGNOSTICAR OFERTA {oferta_id}')
    print('='*100)

    # 2.1 Datos básicos
    cur.execute("SELECT * FROM ofertas WHERE id_oferta = ?", (oferta_id,))
    oferta = dict(cur.fetchone() or {})
    print(f'\n--- SCRAPING (datos originales) ---')
    print(f'Titulo: {oferta.get("titulo")}')
    print(f'Empresa: {oferta.get("empresa")}')
    print(f'Descripcion: {(oferta.get("descripcion") or "")[:200]}...')

    # 2.2 NLP
    cur.execute("SELECT * FROM ofertas_nlp WHERE id_oferta = ?", (oferta_id,))
    row = cur.fetchone()
    nlp = dict(row) if row else {}
    print(f'\n--- NLP (campos extraidos) ---')
    print(f'nivel_seniority: {nlp.get("nivel_seniority")}')
    print(f'area_funcional: {nlp.get("area_funcional")}')
    print(f'sector: {nlp.get("sector")}')
    print(f'sector_confianza: {nlp.get("sector_confianza")}')
    print(f'es_intermediario: {nlp.get("es_intermediario")}')
    print(f'modalidad: {nlp.get("modalidad")}')
    print(f'tareas_principales: {(nlp.get("tareas_principales") or "")[:150]}...')

    # 2.3 Skills
    cur.execute("""
        SELECT skill_name, skill_type, source
        FROM ofertas_skills WHERE id_oferta = ?
        LIMIT 10
    """, (oferta_id,))
    skills = cur.fetchall()
    print(f'\n--- SKILLS (extraidas) ---')
    for s in skills:
        print(f'  - {s["skill_name"]} ({s["skill_type"]}) [source: {s["source"]}]')
    if not skills:
        print('  (sin skills)')

    # 2.4 Matching
    cur.execute("SELECT * FROM ofertas_esco_matching WHERE id_oferta = ?", (str(oferta_id),))
    row = cur.fetchone()
    matching = dict(row) if row else {}
    print(f'\n--- MATCHING (resultado) ---')
    print(f'ISCO: {matching.get("isco_code")} - {matching.get("isco_label")}')
    print(f'Score final: {matching.get("score_final_ponderado")}')
    print(f'Score titulo: {matching.get("score_titulo")}')
    print(f'Score skills: {matching.get("score_skills")}')
    print(f'Metodo: {matching.get("occupation_match_method")}')
    print(f'Cobertura skills: {matching.get("skills_cobertura")}')

    conn.close()
    return {'oferta': oferta, 'nlp': nlp, 'skills': skills, 'matching': matching}

if __name__ == '__main__':
    ofertas = demo_paso1_buscar()
    if ofertas:
        print('\n' + '='*100)
        print('Selecciono la primera oferta para diagnosticar:')
        print('='*100)
        demo_paso2_diagnosticar(ofertas[0])
