# -*- coding: utf-8 -*-
"""Test dictionary bypass matching."""
import importlib
import normalizacion_arg
importlib.reload(normalizacion_arg)

from normalizacion_arg import normalizar_termino_argentino, buscar_match_diccionario_directo

titulos = [
    'Community manager',
    'Ejecutiva/o Comercial de Cuentas - GBA Norte',
    'Venado Tuerto -Gerente de Ventas importante Concesionario',
    'Operario Picking Zona Norte',
    'Analista de Cultivo - Roque Perez',
    'Medica Clinica o Dermatologa',
]

print('=' * 60)
print('TEST: Diccionario Bypass')
print('=' * 60)

for titulo in titulos:
    resultado = buscar_match_diccionario_directo(titulo, None)
    print(f'\nTitulo: {titulo}')
    if resultado:
        label = resultado.get('occupation_label', 'N/A')
        isco = resultado.get('isco_code', 'N/A')
        print(f'  -> BYPASS: {label} (ISCO {isco})')
    else:
        # Ver si hay match parcial
        termino, isco, esco_label, normalizado = normalizar_termino_argentino(titulo, None)
        if termino:
            print(f'  -> MATCH PARCIAL: termino={termino}, esco={esco_label}, isco={isco}')
        else:
            print(f'  -> NO MATCH')
