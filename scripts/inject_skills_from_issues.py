#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inject Skills Suggestions from Supabase Issues v1.0
===================================================

Parsea skills sugeridas en issues pendientes de Supabase y las inyecta en
ofertas_esco_matching.skills_regla_json buscando URIs ESCO automáticamente.

Útil cuando un validador humano (Cynthia, Sergio, etc.) reporta skills a
agregar en issues: convierte su texto libre en URIs ESCO y marca los issues
como resueltos si al menos una skill se pudo mapear.

Uso:
    # Dry-run - solo ver qué se encontraría
    python scripts/inject_skills_from_issues.py --author cyn --dry-run

    # Aplicar sobre issues de un autor
    python scripts/inject_skills_from_issues.py --author cyn

    # Aplicar sobre todos los issues pendientes
    python scripts/inject_skills_from_issues.py --all-pending
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
SUPABASE_CONFIG = BASE_DIR / "config" / "supabase_config.json"

# Verbos iniciales típicos de skills ESCO en español
VERBOS_SKILL = [
    'asesorar', 'asistir', 'analizar', 'administrar', 'actualizar', 'aplicar',
    'buscar', 'brindar',
    'calcular', 'controlar', 'comunicar', 'conducir', 'coordinar', 'capacitar',
    'comprar', 'comercializar', 'cargar', 'conectar', 'cocinar',
    'construir', 'consultar',
    'desarrollar', 'diseñar', 'dirigir', 'diagnosticar', 'distribuir',
    'ejecutar', 'elaborar', 'entregar', 'evaluar', 'establecer', 'enseñar', 'escuchar',
    'facilitar', 'fabricar',
    'gestionar', 'guiar', 'garantizar', 'generar',
    'identificar', 'implementar', 'informar', 'instalar', 'interpretar',
    'interactuar', 'investigar', 'integrar',
    'liderar', 'limpiar', 'leer',
    'manejar', 'mantener', 'monitorear', 'motivar',
    'negociar',
    'observar', 'operar', 'organizar', 'ofrecer',
    'planificar', 'preparar', 'presentar', 'promover', 'proporcionar', 'producir', 'proveer',
    'realizar', 'registrar', 'representar', 'responder', 'resolver',
    'reparar', 'revisar', 'recibir', 'recolectar',
    'seguir', 'supervisar', 'seleccionar', 'servir',
    'transportar', 'tratar', 'trabajar',
    'usar', 'utilizar',
    'vender', 'verificar', 'visitar',
]
VERBO_PATTERN = re.compile(r'^(?:' + '|'.join(VERBOS_SKILL) + r')\s', re.IGNORECASE)


def find_skill_uri(label, cursor, cache):
    """Busca URI ESCO para un label. Orden: exacto > prefix > contains > alt_labels."""
    label = label.strip().lower()
    if label in cache:
        return cache[label]
    if len(label) < 3:
        cache[label] = None
        return None

    queries = [
        ("SELECT skill_uri, preferred_label_es FROM esco_skills WHERE LOWER(preferred_label_es) = ?", (label,), 'exact'),
        ("""SELECT al.skill_uri, s.preferred_label_es FROM esco_skill_alternative_labels al
            JOIN esco_skills s ON s.skill_uri = al.skill_uri WHERE LOWER(al.label) = ? LIMIT 1""", (label,), 'exact_alt'),
        ("SELECT skill_uri, preferred_label_es FROM esco_skills WHERE LOWER(preferred_label_es) LIKE ? LIMIT 1", (label + '%',), 'prefix'),
        ("SELECT skill_uri, preferred_label_es FROM esco_skills WHERE LOWER(preferred_label_es) LIKE ? LIMIT 1", ('%' + label + '%',), 'contains'),
        ("""SELECT al.skill_uri, s.preferred_label_es FROM esco_skill_alternative_labels al
            JOIN esco_skills s ON s.skill_uri = al.skill_uri WHERE LOWER(al.label) LIKE ? LIMIT 1""", ('%' + label + '%',), 'alt_contains'),
    ]

    for sql, params, method in queries:
        cursor.execute(sql, params)
        r = cursor.fetchone()
        if r:
            cache[label] = (r[0], r[1], method)
            return cache[label]

    cache[label] = None
    return None


def parse_skills_from_description(desc):
    """Detecta skills sugeridas por bloques o por líneas que empiezan con verbo en infinitivo."""
    if not desc:
        return []
    skills = []
    in_add_block = False

    for line in desc.split('\n'):
        s = line.strip().lstrip('-').lstrip('•').lstrip('·').lstrip(':').strip().rstrip(',').rstrip(';').strip()
        s = re.sub(r'^\d+\.\s*', '', s)
        s = re.sub(r'^Skill:\s*', '', s, flags=re.IGNORECASE)
        s = re.sub(r'^Tarea\s+de\s+origen:.*$', '', s, flags=re.IGNORECASE)
        if not s:
            continue

        low = s.lower()
        if any(kw in low for kw in ['skills sugerid', 'skills nuevas', 'skills faltant',
                                     'skills pertinentes', 'skill nuevas', 'skill sugerid',
                                     'más pertinentes al aviso', 'alineadas a esco', 'faltant']):
            in_add_block = True
            continue
        if any(kw in low for kw in ['skills incorrect', 'skill incorrect', 'skills ruido',
                                     'no correspond', 'skills que no tienen']):
            in_add_block = False
            continue
        if any(kw in low for kw in ['oferta:', 'isco actual', 'criterio de', 'nota:',
                                     'justificaci', 'denominaci esco', 'validaci']):
            in_add_block = False
            continue

        if (in_add_block or VERBO_PATTERN.match(s)) and 5 <= len(s) <= 120:
            s = re.sub(r'\s+\(.*\)\s*$', '', s).rstrip('.').strip()
            if s and VERBO_PATTERN.match(s):
                skills.append(s)

    seen = set()
    out = []
    for sk in skills:
        if sk.lower() not in seen:
            seen.add(sk.lower())
            out.append(sk)
    return out


def fetch_issues(author=None, all_pending=False):
    from supabase import create_client
    cfg = json.load(open(SUPABASE_CONFIG))
    client = create_client(cfg['url'], cfg['service_role_key'])

    q = client.table('issues').select('id,id_oferta,descripcion').eq('estado', 'pendiente')
    if author:
        q = q.or_(f'autor_nombre.ilike.%{author}%,autor_email.ilike.%{author}%')
    r = q.execute()
    return client, r.data


def update_offer_skills(conn, id_oferta, new_skills, dry_run=False):
    """Mergea las nuevas skills en skills_regla_json (deduplicando por URI)."""
    c = conn.cursor()
    c.execute("SELECT skills_regla_json, skills_regla_aplicada FROM ofertas_esco_matching WHERE id_oferta=?", (id_oferta,))
    row = c.fetchone()
    if not row:
        return 0
    existing_json, existing_rule = row
    try:
        existing = json.loads(existing_json) if existing_json and existing_json != 'null' else []
    except Exception:
        existing = []
    existing_uris = {e.get('skill_uri') for e in existing}

    added = 0
    for s in new_skills:
        if s['uri'] in existing_uris:
            continue
        existing.append({
            'skill_esco': s['preferred'],
            'skill_uri': s['uri'],
            'score': 0.99,
            'score_ponderado': 0.99,
            'peso': 1.0,
            'origen': 'regla_issue',
            'L1': None, 'L2': None, 'es_digital': False,
            'input_original': s['input'],
            'match_method': s['method'],
        })
        existing_uris.add(s['uri'])
        added += 1

    if added and not dry_run:
        new_rule = existing_rule or 'ISSUE_SKILLS'
        if existing_rule and 'ISSUE_SKILLS' not in existing_rule:
            new_rule = f"{existing_rule}+ISSUE_SKILLS"
        c.execute("""UPDATE ofertas_esco_matching SET skills_regla_json = ?, skills_regla_aplicada = ?
                     WHERE id_oferta = ?""", (json.dumps(existing, ensure_ascii=False), new_rule, id_oferta))
        conn.commit()
    return added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--author', help="Substring para filtrar por autor_nombre/autor_email (ej: 'cyn')")
    ap.add_argument('--all-pending', action='store_true', help='Todos los issues pendientes')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    if not args.author and not args.all_pending:
        ap.error("Pasá --author <substring> o --all-pending")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    client, issues = fetch_issues(author=args.author, all_pending=args.all_pending)
    print(f"Issues pendientes traídos: {len(issues)}")

    # Parsear skills por oferta
    por_oferta = defaultdict(lambda: {'issue_ids': [], 'skills_raw': []})
    for i in issues:
        desc = i.get('descripcion') or ''
        if 'Error detectado' in desc:
            continue
        if 'skill' not in desc.lower():
            continue
        sks = parse_skills_from_description(desc)
        if sks:
            por_oferta[i['id_oferta']]['issue_ids'].append(i['id'])
            por_oferta[i['id_oferta']]['skills_raw'].extend(sks)

    print(f"Ofertas con skills parseadas: {len(por_oferta)}")

    # Dedup skills por oferta, buscar URI, aplicar
    cache = {}
    total_found = 0
    total_missing = 0
    total_offers_updated = 0
    total_issues_to_close = []

    for oid, d in sorted(por_oferta.items()):
        seen = set()
        dedup = []
        for sk in d['skills_raw']:
            if sk.lower() not in seen:
                seen.add(sk.lower())
                dedup.append(sk)

        with_uri = []
        without_uri = []
        for sk in dedup:
            r = find_skill_uri(sk, cursor, cache)
            if r:
                uri, preferred, method = r
                with_uri.append({'input': sk, 'preferred': preferred, 'uri': uri, 'method': method})
            else:
                without_uri.append(sk)

        total_found += len(with_uri)
        total_missing += len(without_uri)

        if with_uri:
            added = update_offer_skills(conn, oid, with_uri, dry_run=args.dry_run)
            if added:
                total_offers_updated += 1
                total_issues_to_close.extend(d['issue_ids'])
                if args.verbose:
                    print(f"  {oid}: +{added} skills ({[s['preferred'] for s in with_uri[:3]]})")

    print(f"\n{'='*60}")
    print(f"Total skills con URI:     {total_found}")
    print(f"Total skills sin URI:     {total_missing} (vocabulario sin equivalente exacto en ESCO)")
    print(f"Ofertas actualizadas:     {total_offers_updated}")
    print(f"Issues a marcar resuelto: {len(total_issues_to_close)}")

    if args.dry_run:
        print("\n[DRY-RUN] Ningún cambio guardado. Issues NO cerrados.")
        return

    # Cerrar issues en Supabase
    closed = 0
    for issue_id in total_issues_to_close:
        from datetime import datetime, timezone
        client.table('issues').update({
            'estado': 'resuelto',
            'resuelto_at': datetime.now(timezone.utc).isoformat(),
            'resuelto_por': 'claude',
            'solucion_aplicada': 'Skills sugeridas mapeadas a URIs ESCO via inject_skills_from_issues.py y agregadas a ofertas_esco_matching.skills_regla_json. Skills sin match exacto quedan registradas para ampliar dic.',
            'config_modificada': 'database/ofertas_esco_matching.skills_regla_json'
        }).eq('id', issue_id).execute()
        closed += 1

    print(f"Issues cerrados en Supabase: {closed}")
    conn.close()


if __name__ == "__main__":
    main()
