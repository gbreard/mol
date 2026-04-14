#!/usr/bin/env python3
"""
M-09b C4: Sincronizar candidatos aprobados a JSONs locales.

Lee rule_candidates con estado='aprobado' desde Supabase y aplica:
- regla_nueva/fix_regla/fix_bug → matching_rules_business.json
- sinonimo → sinonimos_argentinos_esco.json
- nlp_correccion_sector/nlp_area_funcional/nlp_limpieza_tareas → nlp_inference_rules.json
- Genera training pairs en data/fine_tuning/train_correcciones.json

Uso:
    python scripts/sync_rules_from_candidates.py
    python scripts/sync_rules_from_candidates.py --dry-run
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
FT_DIR = PROJECT_ROOT / "data" / "fine_tuning"

RULES_PATH = CONFIG_DIR / "matching_rules_business.json"
SINONIMOS_PATH = CONFIG_DIR / "sinonimos_argentinos_esco.json"
NLP_RULES_PATH = CONFIG_DIR / "nlp_inference_rules.json"
CORRECCIONES_PATH = FT_DIR / "train_correcciones.json"


def get_supabase_client():
    config = json.loads((CONFIG_DIR / "supabase_config.json").read_text())
    from supabase import create_client
    return create_client(config['url'], config['service_role_key'])


def apply_regla_nueva(rules: dict, candidate: dict) -> bool:
    """Add new rule to matching_rules_business.json."""
    prop = candidate.get('propuesta', {})
    rule_id = prop.get('id')
    if not rule_id:
        return False

    reglas = rules.get('reglas_forzar_isco', {})
    if rule_id in reglas:
        print(f"  SKIP: {rule_id} already exists")
        return False

    reglas[rule_id] = {
        "nombre": prop.get('nombre', ''),
        "prioridad": prop.get('prioridad', 0),
        "condicion": prop.get('condicion', {}),
        "accion": prop.get('accion', {}),
        "activa": True,
        "_linaje": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "claude-api",
            "issue_ids": candidate.get('issue_ids', []),
            "oferta_ejemplo": candidate.get('oferta_id'),
            "justificacion": candidate.get('justificacion', ''),
            "candidate_id": candidate.get('id'),
        }
    }
    return True


def apply_fix_regla(rules: dict, candidate: dict) -> bool:
    """Fix existing rule."""
    prop = candidate.get('propuesta', {})
    rule_id = prop.get('regla_id')
    if not rule_id:
        return False

    reglas = rules.get('reglas_forzar_isco', {})
    if rule_id not in reglas:
        print(f"  SKIP: {rule_id} not found")
        return False

    campo = prop.get('campo')
    valor_nuevo = prop.get('valor_nuevo')
    if not campo or valor_nuevo is None:
        return False

    rule = reglas[rule_id]
    if campo in ('esco_label', 'forzar_isco'):
        rule.setdefault('accion', {})[campo] = valor_nuevo
    elif campo == 'prioridad':
        rule['prioridad'] = valor_nuevo
    elif campo == 'override_semantico':
        rule['override_semantico'] = valor_nuevo
    else:
        rule[campo] = valor_nuevo

    rule.setdefault('_linaje', {})['last_fix'] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "by": "claude-api",
        "candidate_id": candidate.get('id'),
        "razon": prop.get('razon', ''),
    }
    return True


def apply_sinonimo(sinonimos: dict, candidate: dict) -> bool:
    """Add synonym to sinonimos_argentinos_esco.json."""
    prop = candidate.get('propuesta', {})
    terminos = prop.get('terminos_argentinos', [])
    isco = prop.get('isco')
    label = prop.get('label_esco', '')

    if not terminos or not isco:
        return False

    ocu_titulo = sinonimos.get('ocupaciones_titulo', {})
    for termino in terminos:
        key = termino.lower()
        if key not in ocu_titulo:
            ocu_titulo[key] = {"isco": isco, "label": label}
    return True


def apply_nlp_correccion_sector(nlp_rules: dict, candidate: dict) -> bool:
    """Add sector correction rule."""
    prop = candidate.get('propuesta', {})
    keywords = prop.get('keywords', [])
    sector_correcto = prop.get('sector_correcto')

    if not keywords or not sector_correcto:
        return False

    cs = nlp_rules.setdefault('correccion_sector', {}).setdefault('reglas', [])
    cs.append({
        "keywords": keywords,
        "sector_incorrecto": prop.get('sector_incorrecto', ["Otro"]),
        "sector_correcto": sector_correcto,
        "_source": f"claude-api candidate #{candidate.get('id')}",
    })
    return True


def apply_nlp_area_funcional(nlp_rules: dict, candidate: dict) -> bool:
    """Add area funcional keywords."""
    prop = candidate.get('propuesta', {})
    categoria = prop.get('categoria')
    keywords = prop.get('keywords_nuevos', [])

    if not categoria or not keywords:
        return False

    af = nlp_rules.setdefault('area_funcional', {}).setdefault('categorias', {})
    existing = af.setdefault(categoria, {}).setdefault('keywords', [])
    for k in keywords:
        if k.lower() not in [e.lower() for e in existing]:
            existing.append(k)
    return True


def apply_nlp_limpieza_tareas(nlp_rules: dict, candidate: dict) -> bool:
    """Add task cleanup pattern."""
    prop = candidate.get('propuesta', {})
    patron = prop.get('patron')
    if not patron:
        return False

    lt = nlp_rules.setdefault('limpieza_tareas', {}).setdefault('patrones_ruido', [])
    if patron not in lt:
        lt.append(patron)
    return True


def generate_training_pair(candidate: dict) -> dict:
    """Generate contrastive training pair from approved candidate."""
    return {
        "query": candidate.get('oferta_id', ''),
        "tipo": candidate.get('tipo'),
        "propuesta": candidate.get('propuesta', {}),
        "justificacion": candidate.get('justificacion', ''),
        "confianza": "alta",
        "source": "claude_api_approved",
        "split": "train",
        "candidate_id": candidate.get('id'),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Sync approved candidates to local JSONs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("M-09b C4: Sincronizando candidatos aprobados")
    print("=" * 55)

    client = get_supabase_client()

    # Fetch approved candidates
    result = client.table('rule_candidates').select('*').eq('estado', 'aprobado').order('created_at').execute()
    candidates = result.data or []
    print(f"Candidatos aprobados: {len(candidates)}")

    if not candidates:
        print("Nada que sincronizar.")
        return

    # Load local configs
    rules = json.loads(RULES_PATH.read_text(encoding='utf-8'))
    sinonimos = json.loads(SINONIMOS_PATH.read_text(encoding='utf-8'))
    nlp_rules = json.loads(NLP_RULES_PATH.read_text(encoding='utf-8'))

    # Load existing training pairs
    if CORRECCIONES_PATH.exists():
        correcciones = json.loads(CORRECCIONES_PATH.read_text(encoding='utf-8'))
    else:
        correcciones = []

    applied = 0
    training_pairs_added = 0
    synced_ids = []

    for c in candidates:
        tipo = c.get('tipo', '')
        print(f"\n  [{tipo}] candidate #{c['id']}: {c.get('justificacion', '')[:60]}")

        success = False
        generates_training = False

        if tipo == 'regla_nueva':
            success = apply_regla_nueva(rules, c)
            generates_training = True
        elif tipo in ('fix_regla', 'fix_bug'):
            success = apply_fix_regla(rules, c)
            generates_training = True
        elif tipo == 'sinonimo':
            success = apply_sinonimo(sinonimos, c)
        elif tipo == 'nlp_correccion_sector':
            success = apply_nlp_correccion_sector(nlp_rules, c)
        elif tipo == 'nlp_area_funcional':
            success = apply_nlp_area_funcional(nlp_rules, c)
        elif tipo == 'nlp_limpieza_tareas':
            success = apply_nlp_limpieza_tareas(nlp_rules, c)
        elif tipo in ('nlp_fix_puntual', 'skills_gold_set', 'excepcion_aceptable', 'requiere_revision'):
            success = True  # These don't modify local files

        if success:
            applied += 1
            synced_ids.append(c['id'])
            print(f"    → Aplicado")

            if generates_training:
                pair = generate_training_pair(c)
                correcciones.append(pair)
                training_pairs_added += 1
        else:
            print(f"    → SKIP")

    print(f"\nAplicados: {applied}/{len(candidates)}")
    print(f"Training pairs generados: {training_pairs_added}")

    if args.dry_run:
        print("\n[DRY-RUN] No se guardan archivos ni se marca en BD.")
        return

    # Save configs
    with open(RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {RULES_PATH}")

    with open(SINONIMOS_PATH, 'w', encoding='utf-8') as f:
        json.dump(sinonimos, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {SINONIMOS_PATH}")

    with open(NLP_RULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(nlp_rules, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {NLP_RULES_PATH}")

    FT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORRECCIONES_PATH, 'w', encoding='utf-8') as f:
        json.dump(correcciones, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {CORRECCIONES_PATH} ({len(correcciones)} pares)")

    # Mark as synchronized in Supabase
    for cid in synced_ids:
        client.table('rule_candidates').update({
            'estado': 'sincronizado',
        }).eq('id', cid).execute()

    print(f"\n{len(synced_ids)} candidatos marcados como 'sincronizado' en Supabase")


if __name__ == "__main__":
    main()
