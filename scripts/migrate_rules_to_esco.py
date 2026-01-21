#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
migrate_rules_to_esco.py - Migrar reglas de negocio a labels ESCO válidos

Este script:
1. Lee las reglas actuales de matching_rules_business.json
2. Para cada regla con esco_label, busca el match exacto o más cercano en ESCO
3. Genera un archivo JSON con las correcciones sugeridas
4. Con --apply, actualiza el archivo de reglas

Uso:
    python scripts/migrate_rules_to_esco.py              # Solo ver diagnóstico
    python scripts/migrate_rules_to_esco.py --apply     # Aplicar correcciones automáticas
    python scripts/migrate_rules_to_esco.py --export    # Exportar correcciones a JSON
"""

import json
import sqlite3
import re
import argparse
from pathlib import Path
from difflib import SequenceMatcher

# Paths
BASE_DIR = Path(__file__).parent.parent
RULES_FILE = BASE_DIR / "config" / "matching_rules_business.json"
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
OUTPUT_FILE = BASE_DIR / "config" / "esco_label_corrections.json"


def load_esco_occupations(conn) -> dict:
    """Carga todas las ocupaciones ESCO con sus labels."""
    cur = conn.execute('''
        SELECT occupation_uri, preferred_label_es, isco_code
        FROM esco_occupations
    ''')

    occupations = {}
    for uri, label, isco in cur.fetchall():
        # Indexar por label normalizado
        label_lower = label.lower()
        occupations[label_lower] = {
            'uri': uri,
            'label': label,
            'isco_code': isco
        }

        # También indexar por primera parte (sin género)
        if '/' in label:
            first_part = label.split('/')[0].strip().lower()
            if first_part not in occupations:
                occupations[first_part] = {
                    'uri': uri,
                    'label': label,
                    'isco_code': isco
                }

    return occupations


def find_best_match(label: str, occupations: dict, isco_hint: str = None) -> dict:
    """
    Busca el mejor match para un label en las ocupaciones ESCO.

    Returns:
        dict con {match_type, suggested_label, confidence, candidates}
    """
    if not label:
        return {'match_type': 'empty', 'suggested_label': None, 'confidence': 0, 'candidates': []}

    label_lower = label.lower()
    label_base = label_lower.split('/')[0].strip()

    # 1. Match exacto
    if label_lower in occupations:
        return {
            'match_type': 'exact',
            'suggested_label': occupations[label_lower]['label'],
            'confidence': 1.0,
            'isco_code': occupations[label_lower]['isco_code'],
            'candidates': []
        }

    # 2. Match por primera parte
    if label_base in occupations:
        return {
            'match_type': 'partial',
            'suggested_label': occupations[label_base]['label'],
            'confidence': 0.9,
            'isco_code': occupations[label_base]['isco_code'],
            'candidates': []
        }

    # 3. Buscar candidatos por similitud
    candidates = []

    for esco_label_lower, occ in occupations.items():
        # Calcular similitud
        similarity = SequenceMatcher(None, label_base, esco_label_lower).ratio()

        # Bonus si el ISCO coincide
        if isco_hint and occ['isco_code'].endswith(isco_hint):
            similarity += 0.2

        # Bonus si contiene palabras clave del label original
        words = set(label_base.split())
        esco_words = set(esco_label_lower.split())
        common_words = words.intersection(esco_words)
        if common_words:
            similarity += 0.1 * len(common_words)

        if similarity > 0.4:
            candidates.append({
                'label': occ['label'],
                'isco_code': occ['isco_code'],
                'similarity': min(similarity, 1.0)
            })

    # Ordenar por similitud
    candidates.sort(key=lambda x: x['similarity'], reverse=True)
    candidates = candidates[:5]  # Top 5

    if candidates and candidates[0]['similarity'] > 0.7:
        return {
            'match_type': 'fuzzy',
            'suggested_label': candidates[0]['label'],
            'confidence': candidates[0]['similarity'],
            'isco_code': candidates[0]['isco_code'],
            'candidates': candidates
        }

    return {
        'match_type': 'no_match',
        'suggested_label': None,
        'confidence': 0,
        'candidates': candidates
    }


def analyze_rules(rules: dict, occupations: dict) -> dict:
    """Analiza todas las reglas y sugiere correcciones."""
    results = {
        'exact': [],
        'partial': [],
        'fuzzy': [],
        'no_match': [],
        'empty': [],
        'corrections': {}
    }

    reglas = rules.get('reglas_forzar_isco', {})

    for rule_id, rule in reglas.items():
        if not isinstance(rule, dict):
            continue

        accion = rule.get('accion', {})
        esco_label = accion.get('esco_label', '')
        isco_code = accion.get('forzar_isco', '')

        match = find_best_match(esco_label, occupations, isco_code)
        match['rule_id'] = rule_id
        match['original_label'] = esco_label
        match['original_isco'] = isco_code

        results[match['match_type']].append(match)

        # Si hay corrección sugerida, guardarla
        if match['suggested_label'] and match['original_label'] != match['suggested_label']:
            results['corrections'][rule_id] = {
                'original': esco_label,
                'suggested': match['suggested_label'],
                'confidence': match['confidence'],
                'isco_from_esco': match.get('isco_code', '')
            }

    return results


def is_safe_correction(original: str, suggested: str) -> bool:
    """
    Determina si una corrección es segura (solo cambios menores).

    Correcciones seguras:
    - Solo diferencias de mayúsculas/minúsculas
    - Solo diferencias de acentos
    - Agregar género faltante (ej: "camarero" -> "camarero/camarera")
    """
    import unicodedata

    def normalize(s):
        # Normalizar: quitar acentos, lowercase
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        return s.lower().strip()

    orig_norm = normalize(original)
    sugg_norm = normalize(suggested)

    # Caso 1: Solo diferencias de acentos/mayúsculas
    if orig_norm == sugg_norm:
        return True

    # Caso 2: El sugerido agrega género (ej: "camarero" -> "camarero/camarera")
    if '/' in suggested and '/' not in original:
        # Verificar que la primera parte coincida
        sugg_first = suggested.split('/')[0].strip()
        if normalize(sugg_first) == orig_norm:
            return True
        # O que el original esté contenido
        if orig_norm in normalize(suggested.replace('/', ' ')):
            return True

    # Caso 3: El sugerido quita género redundante
    if '/' in original and '/' not in suggested:
        orig_first = original.split('/')[0].strip()
        if normalize(orig_first) == sugg_norm:
            return True

    return False


def apply_corrections(rules: dict, corrections: dict, safe_only: bool = True) -> dict:
    """Aplica las correcciones al archivo de reglas."""
    reglas = rules.get('reglas_forzar_isco', {})
    applied = []
    skipped = []

    for rule_id, correction in corrections.items():
        if rule_id not in reglas:
            continue

        if correction['confidence'] < 0.7:
            skipped.append((rule_id, 'low_confidence'))
            continue

        if safe_only and not is_safe_correction(correction['original'], correction['suggested']):
            skipped.append((rule_id, 'unsafe'))
            continue

        reglas[rule_id]['accion']['esco_label'] = correction['suggested']
        applied.append(rule_id)

    return rules, applied, skipped


def main():
    parser = argparse.ArgumentParser(description='Migrar reglas a labels ESCO válidos')
    parser.add_argument('--apply', action='store_true', help='Aplicar correcciones automáticas')
    parser.add_argument('--export', action='store_true', help='Exportar correcciones a JSON')
    parser.add_argument('--min-confidence', type=float, default=0.7, help='Confianza mínima para auto-aplicar')
    args = parser.parse_args()

    # Conectar a BD
    conn = sqlite3.connect(DB_PATH)

    # Cargar ocupaciones ESCO
    print("Cargando ocupaciones ESCO...")
    occupations = load_esco_occupations(conn)
    print(f"  {len(occupations)} labels indexados")

    # Cargar reglas
    print("\nCargando reglas de negocio...")
    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        rules = json.load(f)

    total_rules = len([r for r in rules.get('reglas_forzar_isco', {}).values() if isinstance(r, dict)])
    print(f"  {total_rules} reglas encontradas")

    # Analizar
    print("\nAnalizando reglas...")
    results = analyze_rules(rules, occupations)

    # Mostrar resultados
    print("\n" + "="*60)
    print("RESULTADOS DEL ANÁLISIS")
    print("="*60)

    print(f"\n[OK] Match exacto: {len(results['exact'])} reglas")
    print(f"[OK] Match parcial: {len(results['partial'])} reglas")
    print(f"[!!] Match fuzzy: {len(results['fuzzy'])} reglas")
    print(f"[XX] Sin match: {len(results['no_match'])} reglas")
    print(f"[--] Sin label: {len(results['empty'])} reglas")

    # Mostrar reglas sin match
    if results['no_match']:
        print("\n" + "-"*60)
        print("REGLAS SIN MATCH (requieren revisión manual):")
        print("-"*60)
        for match in results['no_match'][:15]:
            print(f"\n  {match['rule_id']}:")
            print(f"    Original: '{match['original_label']}' (ISCO: {match['original_isco']})")
            if match['candidates']:
                print(f"    Candidatos:")
                for c in match['candidates'][:3]:
                    print(f"      - {c['label']} (ISCO: {c['isco_code']}, sim: {c['similarity']:.2f})")

    # Mostrar correcciones sugeridas
    if results['corrections']:
        print("\n" + "-"*60)
        print(f"CORRECCIONES SUGERIDAS ({len(results['corrections'])} reglas):")
        print("-"*60)

        high_conf = [(k, v) for k, v in results['corrections'].items() if v['confidence'] >= 0.8]
        low_conf = [(k, v) for k, v in results['corrections'].items() if v['confidence'] < 0.8]

        if high_conf:
            print(f"\n  Alta confianza (>= 0.8): {len(high_conf)} reglas")
            for rule_id, corr in high_conf[:10]:
                print(f"    {rule_id}:")
                print(f"      '{corr['original']}' -> '{corr['suggested']}'")

        if low_conf:
            print(f"\n  Baja confianza (< 0.8): {len(low_conf)} reglas")
            for rule_id, corr in low_conf[:10]:
                print(f"    {rule_id}:")
                print(f"      '{corr['original']}' -> '{corr['suggested']}' ({corr['confidence']:.2f})")

    # Exportar correcciones
    if args.export:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results['corrections'], f, ensure_ascii=False, indent=2)
        print(f"\nCorrecciones exportadas a: {OUTPUT_FILE}")

    # Aplicar correcciones
    if args.apply:
        print("\n" + "="*60)
        print("APLICANDO CORRECCIONES SEGURAS...")
        print("="*60)

        rules_updated, applied, skipped = apply_corrections(rules, results['corrections'], safe_only=True)

        # Backup del archivo original
        backup_path = RULES_FILE.with_suffix('.json.bak')
        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            with open(backup_path, 'w', encoding='utf-8') as fb:
                fb.write(f.read())
        print(f"  Backup creado: {backup_path}")

        # Guardar reglas actualizadas
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules_updated, f, ensure_ascii=False, indent=2)

        print(f"  [OK] {len(applied)} reglas actualizadas (correcciones seguras)")
        if skipped:
            unsafe_count = len([s for s in skipped if s[1] == 'unsafe'])
            print(f"  [!!] {unsafe_count} reglas omitidas (requieren revision manual)")
        print(f"  Archivo guardado: {RULES_FILE}")

    conn.close()

    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    ok_rules = len(results['exact']) + len(results['partial'])
    need_fix = len(results['fuzzy']) + len(results['no_match'])
    print(f"  Reglas OK (match exacto/parcial): {ok_rules}")
    print(f"  Reglas que necesitan corrección: {need_fix}")

    if not args.apply and results['corrections']:
        print(f"\n  Para aplicar correcciones automáticas:")
        print(f"    python scripts/migrate_rules_to_esco.py --apply")


if __name__ == '__main__':
    main()
