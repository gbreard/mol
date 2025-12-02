#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sync_nlp_from_history.py
========================
Sincroniza ofertas_nlp_history -> ofertas_nlp
Extrae datos del JSON extracted_data y los inserta en ofertas_nlp

PROBLEMA: 1,042 ofertas tienen datos NLP en history pero NO en la tabla activa.
Esto causa que el matching multicriteria no tenga skills -> score_skills = 0 -> RECHAZADOS.

SOLUCION: Extraer los datos del JSON `extracted_data` e insertarlos en `ofertas_nlp`.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "bumeran_scraping.db"

def main():
    print("=" * 70)
    print("SINCRONIZAR ofertas_nlp_history -> ofertas_nlp")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Verificar estado inicial
    c.execute('SELECT COUNT(*) FROM ofertas_nlp')
    count_antes = c.fetchone()[0]
    print(f"\n[1] Estado inicial ofertas_nlp: {count_antes:,}")

    # Obtener ofertas faltantes (las mas recientes por id_oferta)
    print("\n[2] Buscando ofertas faltantes en ofertas_nlp...")
    c.execute('''
        SELECT h.id_oferta, h.extracted_data, h.processed_at, h.nlp_version, h.quality_score
        FROM ofertas_nlp_history h
        INNER JOIN (
            SELECT id_oferta, MAX(processed_at) as max_date
            FROM ofertas_nlp_history
            WHERE extracted_data IS NOT NULL AND extracted_data != ''
            GROUP BY id_oferta
        ) latest ON h.id_oferta = latest.id_oferta AND h.processed_at = latest.max_date
        WHERE NOT EXISTS (SELECT 1 FROM ofertas_nlp n WHERE n.id_oferta = h.id_oferta)
    ''')

    faltantes = c.fetchall()
    print(f"    Ofertas a sincronizar: {len(faltantes):,}")

    if len(faltantes) == 0:
        print("\n[!] No hay ofertas para sincronizar. Todo esta al dia.")
        conn.close()
        return

    # Procesar e insertar
    print("\n[3] Sincronizando...")
    insertados = 0
    errores = []

    for row in faltantes:
        try:
            data = json.loads(row['extracted_data'])

            # Preparar valores (pueden ser listas que se deben serializar)
            def safe_json(value):
                if value is None:
                    return None
                if isinstance(value, (list, dict)):
                    return json.dumps(value, ensure_ascii=False)
                return value

            c.execute('''
                INSERT OR REPLACE INTO ofertas_nlp (
                    id_oferta, skills_tecnicas_list, soft_skills_list,
                    experiencia_min_anios, experiencia_max_anios, experiencia_area,
                    nivel_educativo, estado_educativo, carrera_especifica,
                    idioma_principal, nivel_idioma_principal,
                    jornada_laboral, beneficios_list, certificaciones_list,
                    nlp_version, nlp_confidence_score, nlp_extraction_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['id_oferta'],
                safe_json(data.get('skills_tecnicas_list')),
                safe_json(data.get('soft_skills_list')),
                data.get('experiencia_min_anios'),
                data.get('experiencia_max_anios'),
                data.get('experiencia_area'),
                data.get('nivel_educativo'),
                data.get('estado_educativo'),
                data.get('carrera_especifica'),
                data.get('idioma_principal'),
                data.get('nivel_idioma_principal'),
                data.get('jornada_laboral'),
                safe_json(data.get('beneficios_list')),
                safe_json(data.get('certificaciones_list')),
                row['nlp_version'],
                row['quality_score'],
                row['processed_at']
            ))
            insertados += 1

            if insertados <= 5:
                print(f"    [+] {row['id_oferta']}")
            elif insertados == 6:
                print(f"    ... (procesando restantes)")

        except json.JSONDecodeError as e:
            errores.append(f"{row['id_oferta']}: JSON invalido - {e}")
        except Exception as e:
            errores.append(f"{row['id_oferta']}: {e}")

    conn.commit()

    # Verificar resultado
    c.execute('SELECT COUNT(*) FROM ofertas_nlp')
    count_despues = c.fetchone()[0]

    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"  Insertados correctamente: {insertados:,}")
    print(f"  Errores: {len(errores)}")
    print(f"\n  ofertas_nlp ANTES:   {count_antes:,}")
    print(f"  ofertas_nlp DESPUES: {count_despues:,}")
    print(f"  Diferencia:          +{count_despues - count_antes:,}")

    if errores:
        print(f"\n  ERRORES ({len(errores)}):")
        for e in errores[:10]:
            print(f"    - {e}")
        if len(errores) > 10:
            print(f"    ... y {len(errores) - 10} mas")

    # Verificar objetivo
    c.execute('SELECT COUNT(DISTINCT id_oferta) FROM ofertas')
    total_ofertas = c.fetchone()[0]
    cobertura = count_despues / total_ofertas * 100 if total_ofertas else 0

    print(f"\n  COBERTURA NLP:")
    print(f"    Total ofertas: {total_ofertas:,}")
    print(f"    Con NLP:       {count_despues:,} ({cobertura:.1f}%)")

    if cobertura >= 99.9:
        print("\n  [OK] Cobertura completa!")
    else:
        faltantes_final = total_ofertas - count_despues
        print(f"\n  [!] Faltan {faltantes_final:,} ofertas por procesar NLP")

    print("=" * 70)
    conn.close()


if __name__ == '__main__':
    main()
