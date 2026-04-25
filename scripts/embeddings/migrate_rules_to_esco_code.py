#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC J Fase 1 — Migración de reglas: agregar campo `esco_code` a cada regla
con `esco_label` que mapea unívocamente a un código ESCO.

Para reglas con label ambiguo o sin match, registra en archivo de pendientes
para curación manual.

Uso:
    python3 scripts/embeddings/migrate_rules_to_esco_code.py
    python3 scripts/embeddings/migrate_rules_to_esco_code.py --dry-run
"""
import argparse
import copy
import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def collect_rules(rules_obj):
    """Devuelve lista [(rule_id, regla_dict, contenedor_path)] para mutar in-place."""
    out = []
    def walk(d, path):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict) and 'accion' in v and 'condicion' in v:
                    out.append((k, v))
                elif isinstance(v, dict):
                    walk(v, path + [k])
    walk(rules_obj, [])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rules', default=str(ROOT / 'config/matching_rules_business.json'))
    p.add_argument('--meta', default=str(ROOT / 'database/embeddings/esco_occupations_metadata.json'))
    p.add_argument('--pending-out', default=str(ROOT / 'docs/specs/2026-04-25_J_PENDIENTES.md'))
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    # Cargar metadata
    print('[migrate] Cargando metadata ocupaciones...')
    meta = json.load(open(args.meta))
    label_to_codes = defaultdict(list)
    for o in meta:
        lbl = (o.get('label') or '').lower().strip()
        code = o.get('esco_code', '')
        uri = o.get('uri', '')
        if lbl and code:
            label_to_codes[lbl].append((code, uri, o['label']))
            lbl_short = lbl.split('/')[0].strip()
            if lbl_short != lbl:
                label_to_codes[lbl_short].append((code, uri, o['label']))

    # Cargar reglas
    print('[migrate] Cargando reglas...')
    with open(args.rules, encoding='utf-8') as f:
        rules_obj = json.load(f)
    reglas = collect_rules(rules_obj)
    activas = [(rid, r) for rid, r in reglas if r.get('activa', True)]
    print(f'[migrate] Reglas activas: {len(activas)}')

    # Backup
    if not args.dry_run:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = f'{args.rules}.pre_spec_j_{ts}.bak'
        shutil.copy(args.rules, backup)
        print(f'[migrate] Backup: {backup}')

    # Procesar
    automaticas = []
    ambiguas = []
    sin_match = []
    sin_esco_label = 0

    for rid, regla in activas:
        accion = regla['accion']
        label = accion.get('esco_label')
        if not label:
            sin_esco_label += 1
            continue
        label_l = label.lower().strip()
        candidatos = label_to_codes.get(label_l, [])
        if not candidatos:
            candidatos = label_to_codes.get(label_l.split('/')[0].strip(), [])
        codes_unicos = sorted(set(c[0] for c in candidatos))
        if not candidatos:
            sin_match.append((rid, label, accion.get('forzar_isco')))
        elif len(codes_unicos) == 1:
            # Migración automática
            code = codes_unicos[0]
            accion['esco_code'] = code
            automaticas.append((rid, label, code))
        else:
            ambiguas.append((rid, label, codes_unicos, accion.get('forzar_isco')))

    print(f'\n[migrate] Resultado:')
    print(f'  Migradas automáticas: {len(automaticas)}')
    print(f'  Ambiguas (manual):    {len(ambiguas)}')
    print(f'  Sin match (manual):   {len(sin_match)}')
    print(f'  Sin esco_label:       {sin_esco_label}')

    # Persistir reglas migradas
    if not args.dry_run:
        with open(args.rules, 'w', encoding='utf-8') as f:
            json.dump(rules_obj, f, ensure_ascii=False, indent=2)
        print(f'[migrate] Escrito {args.rules}')

    # Generar archivo de pendientes
    if ambiguas or sin_match:
        with open(args.pending_out, 'w', encoding='utf-8') as f:
            f.write('# SPEC J — Pendientes de curación manual\n\n')
            f.write(f'**Generado:** {datetime.now().isoformat()}\n')
            f.write(f'**Total pendientes:** {len(ambiguas) + len(sin_match)}\n\n')
            f.write('Para cada regla, agregar el campo `esco_code` correcto en `config/matching_rules_business.json`.\n\n')
            f.write('---\n\n')

            if ambiguas:
                f.write(f'## A) Reglas ambiguas ({len(ambiguas)}) — múltiples esco_codes para el mismo label\n\n')
                f.write('Hay que decidir cuál esco_code corresponde para cada regla.\n\n')
                # Agrupar por label para revisar juntas
                grupos = defaultdict(list)
                for rid, label, codes, isco in ambiguas:
                    grupos[label].append((rid, codes, isco))
                for label, items in grupos.items():
                    f.write(f'### Label: `{label}`\n\n')
                    codes_compartidos = items[0][1]
                    f.write('Opciones (mismo label aparece en varios esco_codes):\n')
                    for code in codes_compartidos:
                        # Buscar el label específico de cada candidato
                        candidatos = label_to_codes[label.lower().strip()]
                        for c, uri, orig_label in candidatos:
                            if c == code:
                                f.write(f'- **`{code}`**: {orig_label} ([{uri}])\n')
                                break
                    f.write(f'\nReglas afectadas ({len(items)}):\n')
                    for rid, _, isco in items:
                        f.write(f'- `{rid}` (forzar_isco actual: {isco})\n')
                    f.write('\n')

            if sin_match:
                f.write(f'## B) Reglas sin match ({len(sin_match)}) — label no existe en metadata\n\n')
                f.write('El `esco_label` actual no aparece en `esco_occupations_metadata.json`. Buscar variante correcta.\n\n')
                for rid, label, isco in sin_match:
                    f.write(f'### `{rid}`\n')
                    f.write(f'- esco_label actual: `"{label}"`\n')
                    f.write(f'- forzar_isco actual: `{isco}`\n')
                    # Sugerir variantes posibles buscando subcadenas en metadata
                    suggestions = []
                    for ml, candidatos in label_to_codes.items():
                        words = label.lower().split()[:3]
                        if all(w in ml for w in words[:2] if len(w) > 3):
                            for c, _, ol in candidatos[:1]:
                                suggestions.append((ml, c, ol))
                                if len(suggestions) >= 5:
                                    break
                        if len(suggestions) >= 5:
                            break
                    if suggestions:
                        f.write(f'- Sugerencias posibles:\n')
                        for sug_lbl, sug_code, sug_orig in suggestions[:5]:
                            f.write(f'  - `{sug_code}` — {sug_orig}\n')
                    f.write('\n')

        print(f'[migrate] Pendientes documentados en {args.pending_out}')


if __name__ == '__main__':
    main()
