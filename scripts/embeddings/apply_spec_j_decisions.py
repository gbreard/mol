#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC J Fase 2 — Aplicar decisiones manuales para las 18 reglas pendientes.

Decisiones aprobadas por el usuario el 2026-04-25.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

DECISIONES = {
    # AMBIGUAS — todas a la opción más genérica
    'R32_operario_picking':           ('9333.8', 'mozo de almacén/moza de almacén'),
    'R36_operario_almacen':           ('9333.8', 'mozo de almacén/moza de almacén'),
    'R136_personal_deposito':         ('9333.8', 'mozo de almacén/moza de almacén'),
    'R137_tareas_picking_crossdocking':('9333.8', 'mozo de almacén/moza de almacén'),
    'R141_peon_deposito':             ('9333.8', 'mozo de almacén/moza de almacén'),
    'R142_bodeguero':                 ('9333.8', 'mozo de almacén/moza de almacén'),
    'R350_operario_deposito_logistica':('9333.8', 'mozo de almacén/moza de almacén'),
    'R221_analista_calidad_general':  ('7543.10', 'inspector de control de calidad/inspectora de control de calidad'),
    'R287_herrero':                   ('7221.1',  'herrero/herrera'),

    # SIN MATCH — etiqueta nueva basada en metadata
    'R193_supervisor_operaciones':    ('3123.1',  'supervisor general de construcción/supervisora general de construcción'),
    'R207_peon_cocina':               ('9412.1',  'ayudante de cocina'),
    'R209_personal_maestranza':       ('9112.2',  'operario de limpieza de edificios/operaria de limpieza de edificios'),
    'R210_telefonista_ventas':        ('4222.1',  'agente de centro de atención al cliente'),
    'R212_personal_limpieza':         ('9112.2',  'operario de limpieza de edificios/operaria de limpieza de edificios'),
    'R213_asistente_comercial':       ('4222.1',  'agente de centro de atención al cliente'),
    'R214_analista_comercial':        ('2431.3',  'especialista en publicidad'),
    'R302_supervisor_obra':           ('3123.1',  'supervisor general de construcción/supervisora general de construcción'),
    'R332_talentos_discapacidad':     ('2635.3',  'trabajador social/trabajadora social'),
}


def collect_rules(rules_obj):
    out = []
    def walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict) and 'accion' in v and 'condicion' in v:
                    out.append((k, v))
                elif isinstance(v, dict):
                    walk(v)
    walk(rules_obj)
    return out


def main():
    rules_path = ROOT / 'config/matching_rules_business.json'
    backup = f'{rules_path}.pre_spec_j_decisions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak'
    shutil.copy(rules_path, backup)
    print(f'[apply] Backup: {backup}')

    with open(rules_path, encoding='utf-8') as f:
        rules_obj = json.load(f)

    aplicadas = 0
    no_encontradas = []
    for rid, regla in collect_rules(rules_obj):
        if rid not in DECISIONES:
            continue
        code, label = DECISIONES[rid]
        accion = regla['accion']
        accion['esco_code'] = code
        accion['esco_label'] = label
        # Actualizar forzar_isco a partir del esco_code (primeros 4 chars antes del primer .)
        accion['forzar_isco'] = code.split('.')[0]
        aplicadas += 1
        print(f'  ✓ {rid} → ESCO {code}  "{label[:60]}"')

    no_aplicadas = set(DECISIONES.keys()) - {rid for rid, _ in collect_rules(rules_obj) if rid in DECISIONES}
    if no_aplicadas:
        print(f'\n  ⚠ Reglas no encontradas en JSON: {no_aplicadas}')

    with open(rules_path, 'w', encoding='utf-8') as f:
        json.dump(rules_obj, f, ensure_ascii=False, indent=2)
    print(f'\n[apply] {aplicadas}/18 decisiones aplicadas')

    # Verificación
    print('\n[apply] Verificación post-update:')
    cobertura = {'con_esco_code': 0, 'sin_esco_code': 0, 'sin_esco_label': 0}
    for rid, r in collect_rules(rules_obj):
        if not r.get('activa', True):
            continue
        a = r['accion']
        if 'esco_code' in a:
            cobertura['con_esco_code'] += 1
        elif 'esco_label' in a:
            cobertura['sin_esco_code'] += 1
        else:
            cobertura['sin_esco_label'] += 1
    for k, v in cobertura.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
