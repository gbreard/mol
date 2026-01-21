#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix_rules_esco_labels.py - Corregir labels ESCO invalidos en reglas

Para cada regla con un esco_label que no existe en ESCO:
1. Buscar la ocupacion ESCO mas corta/generica con el mismo ISCO
2. Actualizar la regla con el label correcto

Uso:
    python scripts/fix_rules_esco_labels.py              # Solo ver diagnostico
    python scripts/fix_rules_esco_labels.py --apply     # Aplicar correcciones
"""

import json
import sqlite3
import argparse
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
RULES_FILE = BASE_DIR / "config" / "matching_rules_business.json"
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"


def get_esco_for_isco(conn, isco_code: str, hint_label: str = None) -> list:
    """
    Obtiene ocupaciones ESCO para un ISCO dado.
    Si hint_label se proporciona, ordena por similitud semantica.
    """
    from difflib import SequenceMatcher
    import re

    # Mapeo de sinonimos para mejorar matching
    SYNONYMS = {
        'repartidor': ['reparto', 'delivery', 'entrega'],
        'camion': ['vehiculo', 'furgon', 'transporte'],
        'gerente': ['director', 'jefe', 'responsable'],
        'jefe': ['director', 'supervisor', 'responsable'],
        'telefonista': ['agente', 'operador', 'centro'],
        'deposito': ['almacen', 'inventario', 'bodega'],
        'almacen': ['deposito', 'inventario', 'bodega'],
        'administracion': ['oficina', 'administrativo'],
        'produccion': ['fabricacion', 'elaboracion', 'operador'],
        'tecnico': ['operario', 'especialista', 'mecanico'],
        'instalaciones': ['mantenimiento', 'tuberias', 'plomeria'],
    }

    # ISCO code puede ser "5223" o "C5223"
    isco_search = isco_code if isco_code.startswith('C') else f'C{isco_code}'

    cur = conn.execute('''
        SELECT occupation_uri, preferred_label_es, isco_code
        FROM esco_occupations
        WHERE isco_code = ?
    ''', (isco_search,))

    results = [{'uri': r[0], 'label': r[1], 'isco_code': r[2]} for r in cur.fetchall()]

    if hint_label and results:
        # Normalizar hint
        hint_lower = hint_label.lower().split('/')[0].strip()
        hint_lower = re.sub(r'[^a-z\s]', '', hint_lower)  # Solo letras
        hint_words = set(hint_lower.split())

        # Expandir hint con sinonimos
        expanded_hint = set(hint_words)
        for word in hint_words:
            if word in SYNONYMS:
                expanded_hint.update(SYNONYMS[word])

        for r in results:
            label_lower = r['label'].lower().split('/')[0].strip()
            label_lower_clean = re.sub(r'[^a-z\s]', '', label_lower)
            label_words = set(label_lower_clean.split())

            # Similitud de secuencia
            seq_sim = SequenceMatcher(None, hint_lower, label_lower_clean).ratio()

            # Bonus por palabras en comun (incluyendo sinonimos expandidos)
            common = len(expanded_hint & label_words)
            word_bonus = common * 0.2

            # Penalizacion por longitud (preferir mas cortos)
            length_penalty = len(r['label']) / 300

            r['similarity'] = seq_sim + word_bonus - length_penalty

        # Ordenar por similitud descendente
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    else:
        # Sin hint, ordenar por longitud
        results.sort(key=lambda x: len(x['label']))

    return results


def check_label_exists(conn, label: str) -> bool:
    """Verifica si un label existe exactamente en ESCO."""
    cur = conn.execute('''
        SELECT COUNT(*) FROM esco_occupations
        WHERE LOWER(preferred_label_es) = LOWER(?)
    ''', (label,))
    return cur.fetchone()[0] > 0


def analyze_rules(conn) -> dict:
    """Analiza todas las reglas y encuentra las que necesitan correccion."""
    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    reglas = rules['reglas_forzar_isco']

    valid = []
    invalid = []
    no_isco = []

    for rule_id, rule in reglas.items():
        if not isinstance(rule, dict):
            continue

        accion = rule.get('accion', {})
        esco_label = accion.get('esco_label', '')
        isco_code = accion.get('forzar_isco', '')

        if not esco_label:
            no_isco.append(rule_id)
            continue

        if check_label_exists(conn, esco_label):
            valid.append(rule_id)
            continue

        # Label no existe - buscar alternativas por ISCO con hint semantico
        if isco_code:
            alternatives = get_esco_for_isco(conn, isco_code, hint_label=esco_label)
            invalid.append({
                'rule_id': rule_id,
                'current_label': esco_label,
                'current_isco': isco_code,
                'alternatives': alternatives[:5],  # Top 5 mas cortos
                'nombre': rule.get('nombre', '')
            })
        else:
            invalid.append({
                'rule_id': rule_id,
                'current_label': esco_label,
                'current_isco': None,
                'alternatives': [],
                'nombre': rule.get('nombre', '')
            })

    return {'valid': valid, 'invalid': invalid, 'no_isco': no_isco, 'rules': rules}


def apply_fixes(rules: dict, fixes: list) -> tuple:
    """Aplica las correcciones a las reglas."""
    reglas = rules['reglas_forzar_isco']
    applied = []

    for fix in fixes:
        rule_id = fix['rule_id']
        if rule_id in reglas and fix.get('alternatives'):
            # Usar el primer alternativo (mas corto/generico)
            best = fix['alternatives'][0]
            reglas[rule_id]['accion']['esco_label'] = best['label']
            applied.append({
                'rule_id': rule_id,
                'old_label': fix['current_label'],
                'new_label': best['label']
            })

    return rules, applied


def main():
    parser = argparse.ArgumentParser(description='Corregir labels ESCO invalidos')
    parser.add_argument('--apply', action='store_true', help='Aplicar correcciones')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    print("Analizando reglas...")
    result = analyze_rules(conn)

    print("="*60)
    print("DIAGNOSTICO DE REGLAS")
    print("="*60)
    print(f"Reglas con label ESCO valido: {len(result['valid'])}")
    print(f"Reglas con label ESCO INVALIDO: {len(result['invalid'])}")
    print(f"Reglas sin label ESCO: {len(result['no_isco'])}")

    # Mostrar reglas invalidas con alternativas
    can_fix = [r for r in result['invalid'] if r['alternatives']]
    cannot_fix = [r for r in result['invalid'] if not r['alternatives']]

    print()
    print("-"*60)
    print(f"REGLAS QUE SE PUEDEN CORREGIR ({len(can_fix)}):")
    print("-"*60)

    for r in can_fix[:25]:
        best = r['alternatives'][0]
        print(f"{r['rule_id']} ({r['nombre']}):")
        print(f"  ISCO: {r['current_isco']}")
        print(f"  Actual: \"{r['current_label']}\"")
        print(f"  -> Sugerido: \"{best['label']}\"")
        print()

    if cannot_fix:
        print()
        print("-"*60)
        print(f"REGLAS SIN ALTERNATIVA ({len(cannot_fix)}):")
        print("-"*60)
        for r in cannot_fix:
            print(f"  {r['rule_id']}: \"{r['current_label']}\" (ISCO: {r['current_isco']})")

    # Aplicar correcciones
    if args.apply and can_fix:
        print()
        print("="*60)
        print("APLICANDO CORRECCIONES...")
        print("="*60)

        # Backup
        backup_path = RULES_FILE.with_suffix('.json.bak2')
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            with open(backup_path, 'w', encoding='utf-8') as fb:
                fb.write(f.read())
        print(f"Backup creado: {backup_path}")

        # Aplicar
        rules_updated, applied = apply_fixes(result['rules'], can_fix)

        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules_updated, f, ensure_ascii=False, indent=2)

        print(f"[OK] {len(applied)} reglas corregidas")
        print(f"Archivo guardado: {RULES_FILE}")

        # Mostrar cambios
        print()
        print("Cambios aplicados:")
        for a in applied[:10]:
            print(f"  {a['rule_id']}:")
            print(f"    \"{a['old_label'][:40]}...\"")
            print(f"    -> \"{a['new_label'][:40]}...\"")

    elif not args.apply and can_fix:
        print()
        print(f"Para aplicar las {len(can_fix)} correcciones:")
        print(f"  python scripts/fix_rules_esco_labels.py --apply")

    conn.close()


if __name__ == '__main__':
    main()
