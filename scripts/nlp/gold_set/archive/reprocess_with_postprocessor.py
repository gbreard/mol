# -*- coding: utf-8 -*-
"""
Reprocesar NLP v10.0.0 con postprocessor actualizado
=====================================================

Aplica fixes:
- Skills: normaliza dicts a texto plano
- Jornada: unifica full_time -> full-time
- Modalidad: unifica mixta -> hibrido
- Experiencia: rechaza valores > 15 (probable edad)

Fecha: 2026-01-03
"""
import sqlite3
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from database.nlp_postprocessor import NLPPostprocessor

DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bumeran_scraping.db"

def reprocess_nlp_records(dry_run: bool = True, verbose: bool = False):
    """Reprocesa registros NLP v10.0.0 con postprocessor actualizado."""

    pp = NLPPostprocessor(verbose=verbose)
    print(f"NLP Postprocessor v{pp.VERSION}")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Obtener registros NLP v10
    c.execute("""
        SELECT n.*, o.descripcion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.nlp_version = '10.0.0'
    """)
    rows = c.fetchall()

    print(f"Registros a reprocesar: {len(rows)}")

    stats = {
        "skills_limpiadas": 0,
        "jornada_normalizada": 0,
        "modalidad_normalizada": 0,
        "experiencia_corregida": 0,
        "tareas_limpiadas": 0,
        "total_actualizados": 0
    }

    campos_actualizar = [
        'skills_tecnicas_list', 'soft_skills_list',
        'jornada_laboral', 'modalidad',
        'experiencia_min_anios', 'experiencia_max_anios',
        'tareas_explicitas'
    ]

    for row in rows:
        id_oferta = row['id_oferta']
        descripcion = row['descripcion'] or ''

        # Construir dict con datos actuales
        data = {key: row[key] for key in row.keys() if key != 'descripcion'}

        # Valores originales para comparar
        orig_skills = data.get('skills_tecnicas_list')
        orig_soft = data.get('soft_skills_list')
        orig_jornada = data.get('jornada_laboral')
        orig_modalidad = data.get('modalidad')
        orig_exp_min = data.get('experiencia_min_anios')
        orig_tareas = data.get('tareas_explicitas')

        # Aplicar postprocessor (sin skills_regex, solo limpieza)
        processed = pp.postprocess(data.copy(), descripcion)

        # Detectar cambios
        cambios = {}

        # Skills
        if processed.get('skills_tecnicas_list') != orig_skills:
            cambios['skills_tecnicas_list'] = processed.get('skills_tecnicas_list')
            stats['skills_limpiadas'] += 1

        if processed.get('soft_skills_list') != orig_soft:
            cambios['soft_skills_list'] = processed.get('soft_skills_list')

        # Jornada
        if processed.get('jornada_laboral') != orig_jornada:
            cambios['jornada_laboral'] = processed.get('jornada_laboral')
            stats['jornada_normalizada'] += 1

        # Modalidad
        if processed.get('modalidad') != orig_modalidad:
            cambios['modalidad'] = processed.get('modalidad')
            stats['modalidad_normalizada'] += 1

        # Experiencia
        if processed.get('experiencia_min_anios') != orig_exp_min:
            cambios['experiencia_min_anios'] = processed.get('experiencia_min_anios')
            stats['experiencia_corregida'] += 1
            if verbose:
                print(f"  ID {id_oferta}: exp {orig_exp_min} -> {processed.get('experiencia_min_anios')}")

        # Tareas
        if processed.get('tareas_explicitas') != orig_tareas:
            cambios['tareas_explicitas'] = processed.get('tareas_explicitas')
            stats['tareas_limpiadas'] += 1

        # Aplicar cambios si hay
        if cambios:
            stats['total_actualizados'] += 1

            if not dry_run:
                set_clause = ", ".join([f"{k} = ?" for k in cambios.keys()])
                values = list(cambios.values()) + [id_oferta]

                c.execute(f"""
                    UPDATE ofertas_nlp
                    SET {set_clause}
                    WHERE id_oferta = ?
                """, values)

    if not dry_run:
        conn.commit()

    conn.close()

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  Skills limpiadas: {stats['skills_limpiadas']}")
    print(f"  Tareas limpiadas: {stats['tareas_limpiadas']}")
    print(f"  Jornada normalizada: {stats['jornada_normalizada']}")
    print(f"  Modalidad normalizada: {stats['modalidad_normalizada']}")
    print(f"  Experiencia corregida: {stats['experiencia_corregida']}")
    print(f"  Total actualizados: {stats['total_actualizados']}")

    if dry_run:
        print("\n[DRY RUN] No se aplicaron cambios.")
        print("Ejecutar con --execute para aplicar.")
    else:
        print("\nCambios aplicados exitosamente.")

    return stats

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Reprocesar NLP con postprocessor actualizado")
    parser.add_argument('--execute', action='store_true', help='Aplicar cambios')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar detalles')

    args = parser.parse_args()

    reprocess_nlp_records(dry_run=not args.execute, verbose=args.verbose)

if __name__ == "__main__":
    main()
