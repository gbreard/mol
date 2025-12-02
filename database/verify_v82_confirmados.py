#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verifica casos CONFIRMADOS del batch v8.2 para detectar patrones problematicos.
Genera tabla con id_oferta, titulo, esco_label, isco_code, score, coverage.
"""

import sqlite3
import struct
from pathlib import Path

from matching_rules_v82 import calcular_ajustes_v82

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Thresholds
THRESHOLD_CONFIRMADO = 0.60

# Patrones problematicos a buscar en CONFIRMADOS
PATRONES_PROBLEMATICOS = [
    # (patron_titulo, patron_esco_prohibido, descripcion)
    ("vendedor", "director", "vendedor->director"),
    ("vendedora", "director", "vendedora->director"),
    ("asistente", "director", "asistente->director"),
    ("auxiliar", "director", "auxiliar->director"),
    ("operario", "director", "operario->director"),
    ("recepcion", "director", "recepcion->director"),
    ("pasant", "cualquier", "pasantia confirmada"),
    ("trainee", "cualquier", "trainee confirmado"),
    ("medico", "enfermer", "medico->enfermero"),
    ("doctor", "enfermer", "doctor->enfermero"),
    ("farmac", "ingeniero", "farmacia->ingeniero"),
    ("administrativ", "negocios", "admin->negocios"),
    ("agente de viaje", "consultor", "viajes->consultor"),
    ("vendedor", "agente de empleo", "vendedor->agente empleo"),
]


def parse_score(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, bytes):
        if len(value) == 8:
            return struct.unpack('d', value)[0]
        elif len(value) == 4:
            return struct.unpack('f', value)[0]
    return 0.0


def check_problematic(titulo, esco_label):
    """Verifica si hay un patron problematico."""
    t = titulo.lower()
    e = esco_label.lower()

    for pat_titulo, pat_esco, desc in PATRONES_PROBLEMATICOS:
        if pat_titulo in t:
            if pat_esco == "cualquier" or pat_esco in e:
                return desc
    return None


def main():
    print("=" * 100)
    print("VERIFICACION DE CONFIRMADOS v8.2 - BATCH 200")
    print("=" * 100)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener ofertas CONFIRMADAS
    cursor.execute('''
        SELECT
            m.id_oferta,
            o.titulo,
            o.descripcion,
            m.esco_occupation_label,
            m.isco_code,
            m.score_final_ponderado,
            m.skills_cobertura,
            m.match_confirmado,
            m.requiere_revision
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE m.match_confirmado = 1
        LIMIT 200
    ''')

    rows = cursor.fetchall()
    print(f"\nOfertas CONFIRMADAS encontradas: {len(rows)}")

    # Tabla de CONFIRMADOS
    print("\n" + "=" * 100)
    print("TABLA DE 20 OFERTAS CONFIRMADAS:")
    print("-" * 100)
    print(f"{'ID':<12} | {'TITULO':<30} | {'ESCO_LABEL':<25} | {'ISCO':>6} | {'SCORE':>6} | {'COV':>5}")
    print("-" * 100)

    for i, row in enumerate(rows[:20]):
        titulo_short = (row['titulo'] or '')[:30]
        esco_short = (row['esco_occupation_label'] or '')[:25]
        score = parse_score(row['score_final_ponderado'])
        cov = parse_score(row['skills_cobertura']) if row['skills_cobertura'] else 0.0
        isco = row['isco_code'] or ''

        print(f"{row['id_oferta']:<12} | {titulo_short:<30} | {esco_short:<25} | {isco:>6} | {score:>6.3f} | {cov:>5.2f}")

    # Buscar patrones problematicos
    print("\n" + "=" * 100)
    print("CASOS PROBLEMATICOS EN CONFIRMADOS:")
    print("-" * 100)

    problematicos = []
    for row in rows:
        titulo = row['titulo'] or ''
        esco = row['esco_occupation_label'] or ''
        problema = check_problematic(titulo, esco)

        if problema:
            problematicos.append({
                'id': row['id_oferta'],
                'titulo': titulo[:40],
                'esco': esco[:40],
                'score': parse_score(row['score_final_ponderado']),
                'problema': problema
            })

    if problematicos:
        print(f"{'ID':<12} | {'PROBLEMA':<20} | {'TITULO':<35} | {'ESCO':<35}")
        print("-" * 100)
        for p in problematicos:
            print(f"{p['id']:<12} | {p['problema']:<20} | {p['titulo']:<35} | {p['esco']:<35}")
        print(f"\nTotal problematicos encontrados: {len(problematicos)}")
    else:
        print("No se encontraron patrones problematicos en CONFIRMADOS")

    # Verificar casos especificos solicitados
    print("\n" + "=" * 100)
    print("VERIFICACION DE CASOS ESPECIFICOS:")
    print("-" * 100)

    # 1. Vendedora digital -> director comercial
    cursor.execute('''
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label, m.match_confirmado
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE (LOWER(o.titulo) LIKE '%vendedor%' OR LOWER(o.titulo) LIKE '%vendedora%')
          AND LOWER(m.esco_occupation_label) LIKE '%director%'
    ''')
    vendedor_director = cursor.fetchall()
    print(f"\n1. Vendedor/a -> Director: {len(vendedor_director)} casos")
    for v in vendedor_director:
        estado = 'CONF' if v['match_confirmado'] else 'NO-CONF'
        print(f"   [{estado}] {v['id_oferta']}: {v['titulo'][:40]} -> {v['esco_occupation_label'][:40]}")

    # 2. Pasantias/trainee -> cualquier ESCO
    cursor.execute('''
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label, m.match_confirmado
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE (LOWER(o.titulo) LIKE '%pasant%' OR LOWER(o.titulo) LIKE '%trainee%')
        LIMIT 20
    ''')
    pasantias = cursor.fetchall()
    print(f"\n2. Pasantias/Trainee: {len(pasantias)} casos")
    confirmadas = sum(1 for p in pasantias if p['match_confirmado'])
    print(f"   CONFIRMADAS: {confirmadas} | NO-CONFIRMADAS: {len(pasantias) - confirmadas}")
    for p in pasantias[:5]:
        estado = 'CONF' if p['match_confirmado'] else 'NO-CONF'
        print(f"   [{estado}] {p['id_oferta']}: {p['titulo'][:40]}")

    # 3. Farmacia -> Ingeniero
    cursor.execute('''
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label, m.match_confirmado
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE (LOWER(o.titulo) LIKE '%farmac%' OR LOWER(o.titulo) LIKE '%farma%')
          AND LOWER(m.esco_occupation_label) LIKE '%ingeniero%'
    ''')
    farmacia_ing = cursor.fetchall()
    print(f"\n3. Farmacia -> Ingeniero: {len(farmacia_ing)} casos")
    for f in farmacia_ing:
        estado = 'CONF' if f['match_confirmado'] else 'NO-CONF'
        print(f"   [{estado}] {f['id_oferta']}: {f['titulo'][:40]} -> {f['esco_occupation_label'][:40]}")

    # 4. Admin -> Negocios
    cursor.execute('''
        SELECT m.id_oferta, o.titulo, m.esco_occupation_label, m.match_confirmado
        FROM ofertas_esco_matching m
        JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE LOWER(o.titulo) LIKE '%administrativ%'
          AND (LOWER(m.esco_occupation_label) LIKE '%negocios%' OR LOWER(m.esco_occupation_label) LIKE '%business%')
    ''')
    admin_negocios = cursor.fetchall()
    print(f"\n4. Administrativo -> Negocios: {len(admin_negocios)} casos")
    for a in admin_negocios:
        estado = 'CONF' if a['match_confirmado'] else 'NO-CONF'
        print(f"   [{estado}] {a['id_oferta']}: {a['titulo'][:40]} -> {a['esco_occupation_label'][:40]}")

    conn.close()
    print("\n" + "=" * 100)


if __name__ == '__main__':
    main()
