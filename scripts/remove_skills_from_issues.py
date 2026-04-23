#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove Skills From Issues v1.0
==============================

Procesa issues de Supabase donde un validador (ej: Cynthia) lista skills
que el LLM asignó mal. Las remueve de ofertas_esco_matching.skills_regla_json
y skills_semantico_json.

Detecta skills a remover por patrón:
  - "skill → ❌ Incorrecta"
  - "skill : Validación: ❌"
  - Bloques tras marcador "SKILLS INCORRECTAS" / "Skills que no tienen..."

Uso:
    python scripts/remove_skills_from_issues.py --author cyn --dry-run
    python scripts/remove_skills_from_issues.py --author cyn
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

SKILL_VERBS_PAT = re.compile(
    r'^(asesorar|actualizar|aplicar|analizar|asistir|buscar|brindar|cargar|capacitar|'
    r'coordinar|controlar|cocinar|comunicar|comprar|conducir|consultar|crear|'
    r'desarrollar|diagnosticar|dirigir|diseñar|distribuir|ejecutar|elaborar|enseñar|'
    r'entregar|establecer|evaluar|facilitar|fabricar|garantizar|generar|gestionar|'
    r'guiar|identificar|implementar|informar|instalar|interactuar|interpretar|'
    r'investigar|leer|liderar|limpiar|manejar|mantener|monitorear|motivar|negociar|'
    r'observar|ocuparse|ofrecer|operar|organizar|planificar|preparar|presentar|'
    r'producir|promover|proporcionar|proveer|recibir|recolectar|registrar|realizar|'
    r'reparar|representar|resolver|responder|revisar|seguir|seleccionar|servir|'
    r'supervisar|sustituir|tomar|transportar|tratar|trabajar|usar|utilizar|'
    r'vender|verificar|visitar|vincular)\s',
    re.IGNORECASE,
)

EXCLUDE_STARTS = re.compile(
    r'^(área|area|sector|seniority|experiencia|ocupación|ocupacion|clasificación|'
    r'clasificacion|atributos|observaci|tareas|oferta|isco|denominaci|código|'
    r'codigo|criterio|nota|programa|título|titulo)',
    re.IGNORECASE,
)


def parse_skills_to_remove(desc):
    skills = []
    in_remove_block = False
    for line in desc.split('\n'):
        s = line.strip().lstrip('-').lstrip('•').lstrip('·').lstrip(':').strip()
        s = re.sub(r'^\d+\.\s*', '', s)
        s = re.sub(r'^Skill:\s*', '', s, flags=re.IGNORECASE)
        if not s:
            continue
        # Descartar cualquier línea con marcador de validación positiva
        if '✔' in s or '✓' in s or re.search(r'(?<!in)correct[ao]\b', s, re.IGNORECASE):
            continue

        low = s.lower()

        if re.search(r'skills?\s+(incorrect|asignad.*incorrect|clasificad.+llm|que\s+no\s+correspond|que\s+no\s+tienen|ruido)', low):
            in_remove_block = True
            # Si hay contenido después del marcador en la misma línea, procesarlo
            m_tail = re.search(r':\s*(.+)$', s)
            if m_tail:
                tail = m_tail.group(1).strip()
                parts = re.split(r'\s+[–—\-|]\s+', tail)
                for p in parts:
                    p = p.strip().rstrip('.').rstrip(',').rstrip(':').strip()
                    p = re.sub(r'\s*:\s*(incorrect|correct|validaci).*$', '', p, flags=re.IGNORECASE)
                    if SKILL_VERBS_PAT.match(p) and 5 <= len(p) <= 120:
                        skills.append(p)
            continue
        if re.search(r'skills?\s+(sugerid|nuev|falt|pertinent|alineadas)', low):
            in_remove_block = False
            continue
        if any(kw in low for kw in ['oferta:', 'isco actual', 'criterio de corrección',
                                     'criterio de correcion', 'atributos del aviso',
                                     'observacion de error', 'justificaci', 'denominaci',
                                     'código esco', 'codigo esco', 'ocupación:']):
            in_remove_block = False
            continue

        if EXCLUDE_STARTS.match(s):
            continue

        # Patrón: "skill → ❌"
        m = re.match(r'^(.+?)\s*(?:→|:)\s*(?:Validaci[oó]n:)?\s*❌', s)
        if m:
            candidate = m.group(1).strip().rstrip(':').rstrip('.').strip()
            if SKILL_VERBS_PAT.match(candidate) and 5 <= len(candidate) <= 120:
                skills.append(candidate)
            continue

        if in_remove_block:
            # Split por cualquier dash/separador (- – — |) con espacios
            parts = re.split(r'\s+[–—\-|]\s+', s)
            for p in parts:
                p = p.strip().rstrip('.').rstrip(',').rstrip(':').strip()
                p = re.sub(r'\s*:\s*(incorrect|correct|validaci).*$', '', p, flags=re.IGNORECASE)
                if SKILL_VERBS_PAT.match(p) and 5 <= len(p) <= 120:
                    skills.append(p)

    seen = set()
    out = []
    for s in skills:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def remove_skills_from_offer(conn, id_oferta, skills_lowercase, dry_run=False):
    """Remueve skills de skills_regla_json y skills_semantico_json.
    Match se hace comparando skill_esco en el JSON con los labels dados (case-insensitive, contains)."""
    c = conn.cursor()
    c.execute("""SELECT skills_regla_json, skills_semantico_json FROM ofertas_esco_matching
                 WHERE id_oferta = ?""", (id_oferta,))
    row = c.fetchone()
    if not row:
        return None

    changes = {'regla_removed': [], 'semantico_removed': []}
    for col_idx, col_name in enumerate(['regla', 'semantico']):
        json_str = row[col_idx]
        if not json_str or json_str == 'null':
            continue
        try:
            items = json.loads(json_str)
        except Exception:
            continue
        if not isinstance(items, list):
            continue

        kept = []
        for item in items:
            esco_label = (item.get('skill_esco') or '').lower()
            input_label = (item.get('input_original') or item.get('input_cynthia') or '').lower()
            matched = False
            for target in skills_lowercase:
                if target in esco_label or esco_label in target or target == input_label:
                    matched = True
                    break
            if matched:
                changes[f'{col_name}_removed'].append(item.get('skill_esco', ''))
            else:
                kept.append(item)

        if changes[f'{col_name}_removed'] and not dry_run:
            new_json = json.dumps(kept, ensure_ascii=False)
            sql_col = f"skills_{col_name}_json"
            c.execute(f"UPDATE ofertas_esco_matching SET {sql_col} = ? WHERE id_oferta = ?",
                      (new_json, id_oferta))

    if not dry_run:
        conn.commit()
    return changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--author', help="Substring de autor_nombre/autor_email")
    ap.add_argument('--all-pending', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    if not args.author and not args.all_pending:
        ap.error("Pasá --author o --all-pending")

    from supabase import create_client
    cfg = json.load(open(BASE_DIR / 'config' / 'supabase_config.json'))
    client = create_client(cfg['url'], cfg['service_role_key'])

    q = client.table('issues').select('id,id_oferta,descripcion').eq('estado', 'pendiente')
    if args.author:
        q = q.or_(f'autor_nombre.ilike.%{args.author}%,autor_email.ilike.%{args.author}%')
    issues = q.execute().data

    por_oferta = defaultdict(lambda: {'issue_ids': set(), 'skills': set()})
    for i in issues:
        desc = i.get('descripcion') or ''
        if 'Error detectado' in desc:
            continue
        sk = parse_skills_to_remove(desc)
        if sk:
            por_oferta[i['id_oferta']]['issue_ids'].add(i['id'])
            for s in sk:
                por_oferta[i['id_oferta']]['skills'].add(s.lower())

    print(f"Ofertas con skills-to-remove: {len(por_oferta)}")
    total_skills = sum(len(d['skills']) for d in por_oferta.values())
    print(f"Total skills (dedup por oferta): {total_skills}")

    conn = sqlite3.connect(str(DB_PATH))

    offers_changed = 0
    total_removed = 0
    issues_to_close = []

    for oid, d in sorted(por_oferta.items()):
        skills = list(d['skills'])
        changes = remove_skills_from_offer(conn, oid, skills, dry_run=args.dry_run)
        if changes is None:
            continue
        removed = changes['regla_removed'] + changes['semantico_removed']
        if removed:
            offers_changed += 1
            total_removed += len(removed)
            print(f"\n{oid}: removidas {len(removed)} skills")
            for r in removed[:5]:
                print(f"  - {r[:80]}")
            issues_to_close.extend(d['issue_ids'])

    print(f"\n{'='*60}")
    print(f"Ofertas actualizadas: {offers_changed}")
    print(f"Skills totales removidas: {total_removed}")
    print(f"Issues a cerrar: {len(issues_to_close)}")

    if args.dry_run:
        print("\n[DRY-RUN] Sin cambios guardados.")
        return

    # Cerrar issues
    from datetime import datetime, timezone
    closed = 0
    for iid in issues_to_close:
        client.table('issues').update({
            'estado': 'resuelto',
            'resuelto_at': datetime.now(timezone.utc).isoformat(),
            'resuelto_por': 'claude',
            'solucion_aplicada': f'Skills marcadas como INCORRECTAS por Cynthia fueron removidas de ofertas_esco_matching.skills_regla_json / skills_semantico_json. Proceso vía remove_skills_from_issues.py.',
            'config_modificada': 'database/ofertas_esco_matching (remove skills)'
        }).eq('id', iid).execute()
        closed += 1
    print(f"Issues cerrados en Supabase: {closed}")

    conn.close()


if __name__ == "__main__":
    main()
