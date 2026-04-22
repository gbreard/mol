#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reapply NLP Correction Rules to Validated Offers v1.0
=====================================================

Aplica reglas de nlp_correction_rules.json a ofertas ya validadas SIN correr Ollama.
Corrige campos NLP erróneos (sector='Otro', seniority='trainee', exp=0, area incorrecta)
basándose en palabras clave en título/descripción.

No cambia estado_validacion. UPDATE directo a ofertas_nlp.

Uso:
    # Dry-run sobre IDs
    python scripts/reapply_nlp_to_validated.py --ids 123,456 --dry-run

    # Aplicar
    python scripts/reapply_nlp_to_validated.py --ids 123,456

    # Sobre ofertas con issues pendientes en Supabase
    python scripts/reapply_nlp_to_validated.py --from-issues
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
RULES_PATH = BASE_DIR / "config" / "nlp_correction_rules.json"


def load_rules():
    return json.load(open(RULES_PATH, encoding='utf-8'))


def contains_any(text, patterns):
    if not text or not patterns:
        return False
    t = text.lower()
    return any(p.lower() in t for p in patterns)


def should_override(actual, override_list):
    """Verifica si el valor actual cae en la lista de valores a sobrescribir."""
    for v in override_list:
        if v is None and actual is None: return True
        if v == "" and (actual == "" or actual is None): return True
        if str(actual) == str(v): return True
    return False


def apply_rules_to_field(field_name, field_rules, titulo, descripcion, current_value):
    """Evalúa las reglas de un campo específico, devuelve (nuevo_valor, regla_id) o (None, None)."""
    for rule in field_rules.get('reglas', []):
        # Check condiciones
        desc_match = True
        if 'descripcion_contiene_alguno' in rule:
            desc_match = contains_any(descripcion, rule['descripcion_contiene_alguno'])
        tit_match = True
        if 'titulo_contiene_alguno' in rule:
            tit_match = contains_any(titulo, rule['titulo_contiene_alguno'])
        if not (desc_match and tit_match):
            continue

        # Combinado (si hay ambos): OR de condiciones (ya evaluado por AND arriba — ajustar)
        # Si hay ambos: ambos deben matchear (AND)
        # Si hay solo uno: ese debe matchear

        # Check override_si_actual_es
        override = rule.get('override_si_actual_es', [])
        if override and not should_override(current_value, override):
            continue

        return rule['resultado'], rule['id']
    return None, None


def process_offer(conn, id_oferta, rules, dry_run=False, verbose=False):
    """Procesa una oferta aplicando todas las reglas de corrección."""
    c = conn.cursor()
    c.execute("""
        SELECT o.titulo, o.descripcion, n.sector_empresa, n.nivel_seniority,
               n.area_funcional, n.experiencia_min_anios
        FROM ofertas o JOIN ofertas_nlp n ON n.id_oferta = o.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))
    row = c.fetchone()
    if not row:
        return None

    titulo, descripcion, sector, seniority, area, exp_min = row

    # Evaluar reglas por campo
    field_map = {
        'sector_empresa': sector,
        'nivel_seniority': seniority,
        'area_funcional': area,
        'experiencia_min_anios': exp_min,
    }

    changes = {}
    for field, current in field_map.items():
        if field not in rules:
            continue
        new_val, rule_id = apply_rules_to_field(field, rules[field], titulo, descripcion, current)
        if new_val is not None:
            changes[field] = {'old': current, 'new': new_val, 'regla': rule_id}

    if changes and not dry_run:
        sets = []
        params = []
        for k, v in changes.items():
            sets.append(f"{k} = ?")
            params.append(v['new'])
        params.append(id_oferta)
        c.execute(f"UPDATE ofertas_nlp SET {', '.join(sets)} WHERE id_oferta = ?", params)
        conn.commit()

    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', help='IDs separados por coma')
    ap.add_argument('--from-issues', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    if not args.ids and not args.from_issues:
        ap.error("Pasá --ids o --from-issues")

    rules = load_rules()
    conn = sqlite3.connect(str(DB_PATH))

    if args.ids:
        offer_ids = [s.strip() for s in args.ids.split(',')]
    else:
        from supabase import create_client
        cfg = json.load(open(BASE_DIR / 'config' / 'supabase_config.json'))
        client = create_client(cfg['url'], cfg['service_role_key'])
        r = client.table('issues').select('id_oferta').eq('estado', 'pendiente').execute()
        offer_ids = sorted(set(i['id_oferta'] for i in r.data if i['id_oferta']))

    print(f"Ofertas a procesar: {len(offer_ids)}")
    print("=" * 60)

    total_changed = 0
    changes_by_field = {}
    for i, oid in enumerate(offer_ids, 1):
        changes = process_offer(conn, oid, rules, args.dry_run, args.verbose)
        if changes is None:
            print(f"  [{i}/{len(offer_ids)}] {oid}: NO ENCONTRADA")
            continue
        if changes:
            total_changed += 1
            summary = '; '.join(f"{k}: {v['old']!r}→{v['new']!r} ({v['regla']})"
                                for k, v in changes.items())
            print(f"  [{i}/{len(offer_ids)}] {oid}: {summary}")
            for k in changes:
                changes_by_field[k] = changes_by_field.get(k, 0) + 1
        elif args.verbose:
            print(f"  [{i}/{len(offer_ids)}] {oid}: sin cambios")

    print("\n" + "=" * 60)
    print(f"Procesadas:       {len(offer_ids)}")
    print(f"Con cambios:      {total_changed}")
    print(f"Sin cambios:      {len(offer_ids) - total_changed}")
    print("\nCambios por campo:")
    for k, n in sorted(changes_by_field.items()):
        print(f"  {k}: {n}")
    if args.dry_run:
        print("\n[DRY-RUN] Ningún cambio guardado.")

    conn.close()


if __name__ == "__main__":
    main()
