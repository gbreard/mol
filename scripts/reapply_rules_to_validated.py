#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reapply Rules to Validated Offers v1.1
======================================

Reaplicar reglas de matching a ofertas ya validadas SIN cambiar su estado.
Útil cuando se crean reglas nuevas que corrigen errores detectados.

Flujo:
1. Lee ofertas validadas candidatas (por errores resueltos o por regla específica)
2. Reaplicar SOLO matching (no NLP)
3. Actualiza campos de matching en BD
4. NO cambia estado_validacion

Uso:
    # Ver ofertas con errores resueltos (dry-run)
    python scripts/reapply_rules_to_validated.py --dry-run

    # Reprocesar todas las que tuvieron errores resueltos
    python scripts/reapply_rules_to_validated.py

    # Reprocesar IDs específicos
    python scripts/reapply_rules_to_validated.py --ids 123,456,789

    # ⭐ NUEVO: buscar todas las validadas que matchean una regla específica
    # (propaga regla nueva a ofertas similares que nadie reportó como error)
    python scripts/reapply_rules_to_validated.py --regla R_FILETEADOR --dry-run
    python scripts/reapply_rules_to_validated.py --regla R_FILETEADOR

    # Luego sincronizar a Supabase
    python scripts/exports/sync_to_supabase.py
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "database"))

DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
RULES_PATH = BASE_DIR / "config" / "matching_rules_business.json"


def get_offers_with_resolved_errors(conn) -> list:
    """Obtiene IDs de ofertas validadas que tuvieron errores resueltos."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ve.id_oferta
        FROM validation_errors ve
        JOIN ofertas_esco_matching m ON ve.id_oferta = m.id_oferta
        WHERE ve.resuelto = 1
          AND m.estado_validacion IN ('validado_claude', 'validado_humano')
        ORDER BY ve.id_oferta
    """)
    return [row[0] for row in cursor.fetchall()]


def load_rule(rule_name: str) -> dict:
    """Carga una regla de negocio del JSON por su nombre."""
    data = json.load(open(RULES_PATH, encoding='utf-8'))
    rules = data.get('reglas_forzar_isco', {})
    if rule_name not in rules:
        # Dar feedback con nombres similares
        similares = [k for k in rules.keys() if rule_name.lower() in k.lower() or k.lower() in rule_name.lower()]
        msg = f"Regla '{rule_name}' no existe en matching_rules_business.json"
        if similares:
            msg += f"\nSimilares: {similares[:5]}"
        raise ValueError(msg)
    return rules[rule_name]


def build_sql_from_condition(condicion: dict) -> tuple:
    """Traduce el dict de condición de una regla a un WHERE SQL.

    Devuelve (where_clause, params_list).
    Las columnas asumen el JOIN: ofertas o + ofertas_nlp n + ofertas_esco_matching m.

    Condiciones soportadas (cubren ~95% de las reglas):
      - titulo_contiene_alguno / titulo_contiene_alguno_2: OR de LIKE en titulo_limpio
      - titulo_contiene_todos: AND de LIKE en titulo_limpio
      - titulo_no_contiene_alguno / titulo_no_contiene: AND de NOT LIKE
      - titulo_contiene: LIKE en titulo_limpio
      - titulo_original_contiene_alguno: OR de LIKE en ofertas.titulo (raw)
      - titulo_o_tareas_contiene_alguno: LIKE en titulo_limpio OR tareas_explicitas
      - tareas_contiene_alguno: OR de LIKE en tareas_explicitas
      - skills_contiene_alguno: OR de LIKE en skills_tecnicas_list
      - area_funcional_es / nlp_area_es: igualdad
      - area_funcional_es_alguno: IN
      - area_funcional_no_es: desigualdad
      - sector_empresa_es_alguno: IN en sector_empresa
      - sector_es / nlp_sector_es: igualdad
      - sector_no_es: desigualdad
      - nlp_seniority_es: igualdad en nivel_seniority
      - nlp_tiene_gente_cargo: boolean en tiene_gente_a_cargo
    """
    clauses = []
    params = []

    def like_any(col, values, negate=False):
        """Genera (col LIKE ? OR col LIKE ? ...) o AND de NOT LIKE."""
        if isinstance(values, str):
            values = [values]
        op = "NOT LIKE" if negate else "LIKE"
        joiner = " AND " if negate else " OR "
        parts = []
        for v in values:
            parts.append(f"LOWER({col}) {op} ?")
            params.append(f"%{v.lower()}%")
        return "(" + joiner.join(parts) + ")"

    for key, val in condicion.items():
        if key in ('titulo_contiene_alguno', 'titulo_contiene_alguno_2'):
            clauses.append(like_any("COALESCE(n.titulo_limpio, o.titulo)", val))
        elif key == 'titulo_contiene':
            clauses.append(like_any("COALESCE(n.titulo_limpio, o.titulo)", val))
        elif key == 'titulo_contiene_todos':
            vals = val if isinstance(val, list) else [val]
            parts = []
            for v in vals:
                parts.append("LOWER(COALESCE(n.titulo_limpio, o.titulo)) LIKE ?")
                params.append(f"%{v.lower()}%")
            clauses.append("(" + " AND ".join(parts) + ")")
        elif key in ('titulo_no_contiene_alguno', 'titulo_no_contiene'):
            clauses.append(like_any("COALESCE(n.titulo_limpio, o.titulo)", val, negate=True))
        elif key == 'titulo_original_contiene_alguno':
            clauses.append(like_any("o.titulo", val))
        elif key == 'titulo_o_tareas_contiene_alguno':
            vals = val if isinstance(val, list) else [val]
            parts = []
            for v in vals:
                parts.append("(LOWER(COALESCE(n.titulo_limpio, o.titulo)) LIKE ? OR LOWER(n.tareas_explicitas) LIKE ?)")
                params.extend([f"%{v.lower()}%", f"%{v.lower()}%"])
            clauses.append("(" + " OR ".join(parts) + ")")
        elif key == 'tareas_contiene_alguno':
            clauses.append(like_any("n.tareas_explicitas", val))
        elif key == 'skills_contiene_alguno':
            clauses.append(like_any("n.skills_tecnicas_list", val))
        elif key in ('area_funcional_es', 'nlp_area_es'):
            clauses.append("LOWER(n.area_funcional) = ?")
            params.append(str(val).lower())
        elif key == 'area_funcional_es_alguno':
            vals = val if isinstance(val, list) else [val]
            placeholders = ",".join(["?"] * len(vals))
            clauses.append(f"LOWER(n.area_funcional) IN ({placeholders})")
            params.extend([str(v).lower() for v in vals])
        elif key == 'area_funcional_no_es':
            clauses.append("LOWER(COALESCE(n.area_funcional, '')) != ?")
            params.append(str(val).lower())
        elif key == 'sector_empresa_es_alguno':
            vals = val if isinstance(val, list) else [val]
            placeholders = ",".join(["?"] * len(vals))
            clauses.append(f"LOWER(n.sector_empresa) IN ({placeholders})")
            params.extend([str(v).lower() for v in vals])
        elif key in ('sector_es', 'nlp_sector_es'):
            if isinstance(val, list):
                placeholders = ",".join(["?"] * len(val))
                clauses.append(f"LOWER(n.sector_empresa) IN ({placeholders})")
                params.extend([str(v).lower() for v in val])
            else:
                clauses.append("LOWER(n.sector_empresa) = ?")
                params.append(str(val).lower())
        elif key == 'sector_no_es':
            clauses.append("LOWER(COALESCE(n.sector_empresa, '')) != ?")
            params.append(str(val).lower())
        elif key == 'nlp_seniority_es':
            if isinstance(val, list):
                placeholders = ",".join(["?"] * len(val))
                clauses.append(f"LOWER(n.nivel_seniority) IN ({placeholders})")
                params.extend([str(v).lower() for v in val])
            else:
                clauses.append("LOWER(n.nivel_seniority) = ?")
                params.append(str(val).lower())
        elif key == 'nlp_tiene_gente_cargo':
            clauses.append("n.tiene_gente_a_cargo = ?")
            params.append(1 if val else 0)
        elif key == 'titulo_tiene_patron':
            raise NotImplementedError(
                f"Condición '{key}' usa regex, no soportada en SQL. "
                "Usá --ids con IDs manuales o extendé el script."
            )
        else:
            raise NotImplementedError(f"Condición desconocida: '{key}'. Agregala a build_sql_from_condition().")

    if not clauses:
        raise ValueError("Regla sin condiciones — no se puede construir query")

    return " AND ".join(clauses), params


def get_offers_matching_rule(conn, rule_name: str) -> tuple:
    """Busca ofertas validadas que cumplen la condición de una regla PERO
    tienen un ISCO distinto al que la regla fuerza.

    Devuelve (offer_ids, target_isco, rule_dict).
    """
    rule = load_rule(rule_name)
    condicion = rule.get('condicion', {})
    accion = rule.get('accion', {})
    target_isco = accion.get('forzar_isco')

    if not target_isco:
        raise ValueError(f"Regla '{rule_name}' no tiene accion.forzar_isco")

    if not rule.get('activa', True):
        print(f"[WARN] Regla '{rule_name}' está marcada como inactiva (activa=false)")

    where, params = build_sql_from_condition(condicion)

    # ISCO actual distinto al target → ofertas que NO se están beneficiando de la regla
    query = f"""
        SELECT DISTINCT m.id_oferta, m.isco_code, COALESCE(n.titulo_limpio, o.titulo) AS titulo_efectivo
        FROM ofertas_esco_matching m
        JOIN ofertas o ON o.id_oferta = m.id_oferta
        LEFT JOIN ofertas_nlp n ON n.id_oferta = m.id_oferta
        WHERE m.estado_validacion IN ('validado_claude', 'validado_humano', 'validado')
          AND (m.isco_code IS NULL OR m.isco_code != ?)
          AND {where}
        ORDER BY m.id_oferta
    """
    cursor = conn.cursor()
    cursor.execute(query, [target_isco] + params)
    rows = cursor.fetchall()
    return rows, target_isco, rule


def get_oferta_nlp_data(conn, id_oferta: str) -> dict:
    """Obtiene datos NLP de una oferta para matching."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            o.id_oferta, o.titulo, o.descripcion,
            n.titulo_limpio, n.tareas_explicitas, n.nivel_seniority,
            n.area_funcional, n.sector_empresa, n.skills_tecnicas_list,
            n.soft_skills_list, n.modalidad, n.tipo_contrato,
            m.isco_code, m.esco_occupation_label, m.regla_aplicada
        FROM ofertas o
        LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
        LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
        WHERE o.id_oferta = ?
    """, (id_oferta,))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        'id_oferta': row[0],
        'titulo': row[1] or '',
        'descripcion': row[2] or '',
        'titulo_limpio': row[3] or row[1] or '',
        'tareas_explicitas': row[4] or '',
        'nivel_seniority': row[5],
        'area_funcional': row[6],
        'sector_empresa': row[7],
        'skills_tecnicas_list': row[8],
        'soft_skills_list': row[9],
        'modalidad': row[10],
        'tipo_contrato': row[11],
        'isco_anterior': row[12],
        'esco_anterior': row[13],
        'regla_anterior': row[14]
    }




def main():
    parser = argparse.ArgumentParser(description='Reapply rules to validated offers')
    parser.add_argument('--ids', help='IDs específicos separados por coma')
    parser.add_argument('--regla', help='Nombre de regla de matching_rules_business.json (ej: R139_repositor). '
                                        'Busca ofertas validadas que cumplen la condición pero tienen ISCO distinto.')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar, no modificar')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar detalles')
    args = parser.parse_args()

    if sum(bool(x) for x in [args.ids, args.regla]) > 1:
        parser.error("Usá --ids O --regla, no ambos")

    print("=" * 60)
    print("REAPPLY RULES TO VALIDATED OFFERS")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))

    # Obtener IDs a procesar
    if args.ids:
        offer_ids = [id.strip() for id in args.ids.split(',')]
        print(f"IDs especificados: {len(offer_ids)}")
    elif args.regla:
        try:
            rows, target_isco, rule = get_offers_matching_rule(conn, args.regla)
        except (ValueError, NotImplementedError) as e:
            print(f"[ERROR] {e}")
            conn.close()
            sys.exit(1)
        print(f"Regla:         {args.regla}")
        print(f"Descripción:   {rule.get('nombre', '-')}")
        print(f"ISCO objetivo: {target_isco} ({rule.get('accion', {}).get('esco_label', '-')})")
        print(f"Candidatas:    {len(rows)} ofertas validadas con ISCO distinto")

        if rows and (args.dry_run or args.verbose):
            print(f"\nPrimeras {min(20, len(rows))}:")
            for oferta_id, isco_actual, titulo in rows[:20]:
                print(f"  {oferta_id} | {isco_actual or 'NULL':5} → {target_isco} | {titulo[:60]}")

        offer_ids = [row[0] for row in rows]

        if args.dry_run:
            print(f"\n[DRY-RUN] Se reprocesarían {len(offer_ids)} ofertas con regla '{args.regla}'")
            conn.close()
            return
    else:
        offer_ids = get_offers_with_resolved_errors(conn)
        print(f"Ofertas con errores resueltos: {len(offer_ids)}")

    if not offer_ids:
        print("No hay ofertas para procesar.")
        conn.close()
        return

    if args.dry_run:
        print(f"\n[DRY-RUN] Se reprocesarían {len(offer_ids)} ofertas:")
        print(f"IDs: {offer_ids[:10]}{'...' if len(offer_ids) > 10 else ''}")
        conn.close()
        return

    # Importar matcher
    try:
        from match_ofertas_v3 import MatcherV3
        matcher = MatcherV3(conn)
        print("Matcher v3 cargado OK")
    except Exception as e:
        print(f"Error cargando matcher: {e}")
        import traceback
        traceback.print_exc()
        return

    # Generar run_id para tracking
    run_id = f"reapply_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Run ID: {run_id}")

    # Procesar ofertas
    cambios = 0
    errores = 0
    sin_cambio = 0

    for i, id_oferta in enumerate(offer_ids):
        try:
            # Obtener datos NLP de la oferta
            oferta_data = get_oferta_nlp_data(conn, id_oferta)

            if not oferta_data:
                print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: No encontrada")
                errores += 1
                continue

            isco_anterior = oferta_data.pop('isco_anterior')
            esco_anterior = oferta_data.pop('esco_anterior')
            regla_anterior = oferta_data.pop('regla_anterior')

            # Ejecutar matching (esto persiste automáticamente)
            result = matcher.match_and_persist(
                id_oferta=id_oferta,
                oferta_nlp=oferta_data,
                categorize_skills=True,
                run_id=run_id,
                _allow_no_run=True
            )

            # Restaurar estado de validación (el matcher lo resetea a 'pendiente')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ofertas_esco_matching
                SET estado_validacion = 'validado_claude',
                    validado_timestamp = datetime('now')
                WHERE id_oferta = ?
            """, (id_oferta,))
            conn.commit()

            isco_nuevo = result.isco_code
            regla_nueva = result.metadata.get('regla_aplicada') if result.metadata else None

            if isco_anterior != isco_nuevo:
                cambios += 1
                if args.verbose or True:  # siempre mostrar cambios
                    print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: {isco_anterior} -> {isco_nuevo} (regla: {regla_nueva})")
            else:
                sin_cambio += 1
                if args.verbose:
                    print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: sin cambio")

        except Exception as e:
            print(f"  [{i+1}/{len(offer_ids)}] {id_oferta}: EXCEPTION - {e}")
            errores += 1

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Procesadas:  {len(offer_ids)}")
    print(f"Con cambios: {cambios}")
    print(f"Sin cambios: {sin_cambio}")
    print(f"Errores:     {errores}")
    print(f"\nPróximo paso: python scripts/exports/sync_to_supabase.py")

    conn.close()


if __name__ == "__main__":
    main()
