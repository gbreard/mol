# -*- coding: utf-8 -*-
"""
Tests de coherencia SPEC J — verifica que TODAS las reglas activas con
esco_code apuntan a una ocupación válida en metadata.
"""
import json
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope='module')
def reglas_activas():
    """Devuelve dict {rule_id: regla} para todas las reglas activas."""
    with open(ROOT / 'config/matching_rules_business.json', encoding='utf-8') as f:
        data = json.load(f)
    out = {}
    def walk(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict) and 'accion' in v and 'condicion' in v:
                    if v.get('activa', True):
                        out[k] = v
                elif isinstance(v, dict):
                    walk(v)
    walk(data)
    return out


@pytest.fixture(scope='module')
def code_to_occupation():
    """Mapa esco_code → {uri, label, isco_4dig} desde metadata."""
    meta_path = ROOT / 'database/embeddings/esco_occupations_metadata.json'
    with open(meta_path, encoding='utf-8') as f:
        meta = json.load(f)
    out = {}
    for o in meta:
        code = o.get('esco_code')
        if code:
            out[code] = o
    return out


def test_344_reglas_activas_tienen_esco_code(reglas_activas):
    """Tras SPEC J, las 344 reglas activas con esco_label deben tener esco_code."""
    con_label = [rid for rid, r in reglas_activas.items()
                 if r['accion'].get('esco_label')]
    sin_code = [rid for rid in con_label
                if not reglas_activas[rid]['accion'].get('esco_code')]
    assert not sin_code, f'Reglas sin esco_code: {sin_code}'


def test_todo_esco_code_existe_en_metadata(reglas_activas, code_to_occupation):
    """Cada esco_code declarado en una regla debe existir en metadata."""
    huerfanas = []
    for rid, r in reglas_activas.items():
        code = r['accion'].get('esco_code')
        if code and code not in code_to_occupation:
            huerfanas.append((rid, code))
    assert not huerfanas, f'Reglas con esco_code huérfano: {huerfanas[:10]}'


def test_forzar_isco_coherente_con_esco_code(reglas_activas):
    """forzar_isco debe coincidir con primer chunk del esco_code."""
    incoherentes = []
    for rid, r in reglas_activas.items():
        accion = r['accion']
        code = accion.get('esco_code')
        forzar = accion.get('forzar_isco')
        if code and forzar:
            isco_derivado = code.split('.')[0]
            if isco_derivado != forzar:
                incoherentes.append((rid, code, forzar, isco_derivado))
    assert not incoherentes, (
        f'Reglas con forzar_isco != prefijo de esco_code: {incoherentes[:10]}'
    )


def test_esco_label_sigue_siendo_correcto(reglas_activas, code_to_occupation):
    """El esco_label de la regla debe coincidir con el de metadata para su esco_code."""
    discrepancias = []
    for rid, r in reglas_activas.items():
        accion = r['accion']
        code = accion.get('esco_code')
        label_regla = (accion.get('esco_label') or '').strip().lower()
        if not code or not label_regla:
            continue
        occ = code_to_occupation.get(code, {})
        label_meta = (occ.get('label') or '').strip().lower()
        if label_meta and label_regla != label_meta:
            # Aceptar si label_regla es solo la parte masc del compuesto
            label_short = label_regla.split('/')[0].strip()
            if label_short != label_meta.split('/')[0].strip():
                discrepancias.append((rid, code, label_regla[:40], label_meta[:40]))
    assert not discrepancias, (
        f'Reglas con esco_label inconsistente con metadata: {discrepancias[:10]}'
    )


def test_no_hay_codes_duplicados_inesperados(reglas_activas):
    """Reportar (no fallar) si múltiples reglas apuntan al mismo esco_code.
    Esto es válido (varias reglas pueden mapear al mismo target) pero útil saberlo."""
    code_to_rules = defaultdict(list)
    for rid, r in reglas_activas.items():
        code = r['accion'].get('esco_code')
        if code:
            code_to_rules[code].append(rid)
    duplicados = {c: rs for c, rs in code_to_rules.items() if len(rs) > 1}
    if duplicados:
        # No fallar — solo informar
        print(f'\n[INFO] {len(duplicados)} esco_codes con múltiples reglas:')
        for code, rules in list(duplicados.items())[:5]:
            print(f'  {code}: {len(rules)} reglas ({rules[:3]}...)')


def test_resolver_funciona_para_canonicas():
    """Test funcional: importar matcher + verificar resolución."""
    import sys, sqlite3, warnings
    warnings.filterwarnings('ignore')
    sys.path.insert(0, str(ROOT / 'database'))
    sys.path.insert(0, str(ROOT / 'config'))
    from match_ofertas_v3 import MatcherV3
    conn = sqlite3.connect(str(ROOT / 'database/bumeran_scraping.db'))
    m = MatcherV3(db_conn=conn, verbose=False)
    canonicas = [
        ('7214.3.1', 'remachador'),
        ('8142.1', 'plástico moldeo soplado'),
        ('2221.2', 'enfermero responsable'),
        ('3123.1', 'supervisor general construcción'),
        ('9333.8', 'mozo de almacén'),
    ]
    for code, hint in canonicas:
        occ = m._find_occupation_by_esco_code(code)
        assert occ is not None, f'No resolvió {code} ({hint})'
        assert occ.get('uri'), f'{code} sin URI'
    conn.close()
