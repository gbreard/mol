#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditor de Efectividad de Reglas de Negocio

v1.0 - 2026-01-22

Genera un reporte detallado de cómo funcionan las reglas de negocio
comparando sus resultados con el matching semántico.

Casos identificados:
1. REGLAS EFECTIVAS: Coinciden con semántico > 70%
2. REGLAS NECESARIAS: Semántico falla sistemáticamente (score bajo)
3. REGLAS PROBLEMÁTICAS: Override semántico alto (posible error en regla)
4. REGLAS SIN USO: Nunca aplicadas en el lote actual

Uso:
    python scripts/audit_rules_effectiveness.py
    python scripts/audit_rules_effectiveness.py --verbose
    python scripts/audit_rules_effectiveness.py --export reporte.md
"""

import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "bumeran_scraping.db"
RULES_PATH = BASE_DIR / "config" / "matching_rules_business.json"


def load_all_rules() -> Dict[str, Any]:
    """Carga todas las reglas de negocio del JSON."""
    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("reglas_forzar_isco", {})


def get_rules_from_db() -> List[Dict]:
    """Obtiene estadísticas de reglas desde la vista v_reglas_efectividad."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    cur = conn.execute("""
        SELECT
            regla_aplicada,
            usos_total,
            coinciden_semantico,
            pct_coincidencia,
            score_semantico_promedio,
            score_min,
            score_max,
            tipos_decision
        FROM v_reglas_efectividad
        ORDER BY pct_coincidencia ASC
    """)

    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return results


def get_decision_summary() -> Dict[str, int]:
    """Obtiene resumen de tipos de decisión."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    cur = conn.execute("""
        SELECT decision_metodo, COUNT(*) as total
        FROM ofertas_esco_matching
        WHERE decision_metodo IS NOT NULL
        GROUP BY decision_metodo
    """)

    result = {row["decision_metodo"]: row["total"] for row in cur.fetchall()}
    conn.close()
    return result


def get_problematic_cases(limit: int = 10) -> List[Dict]:
    """Obtiene casos donde la regla override semántico con score alto."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    cur = conn.execute("""
        SELECT
            m.id_oferta,
            n.titulo_limpio,
            m.regla_aplicada,
            m.isco_regla,
            m.isco_semantico,
            m.score_semantico,
            m.decision_metodo,
            m.decision_razon
        FROM ofertas_esco_matching m
        LEFT JOIN ofertas_nlp n ON m.id_oferta = n.id_oferta
        WHERE m.decision_metodo = 'regla_override_semantico_alto'
           OR (m.dual_coinciden = 0 AND m.score_semantico > 0.75)
        ORDER BY m.score_semantico DESC
        LIMIT ?
    """, (limit,))

    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return results


def classify_rules(rules_stats: List[Dict], all_rules: Dict) -> Dict[str, List]:
    """Clasifica reglas en categorías."""
    classification = {
        "efectivas": [],       # Coinciden > 70%
        "necesarias": [],      # Semántico falla (score < 0.6)
        "problematicas": [],   # Override alto (coinc < 30%, score > 0.7)
        "sin_uso": [],         # Nunca aplicadas
        "normales": []         # Resto
    }

    # Reglas usadas (del DB)
    used_rules = {r["regla_aplicada"] for r in rules_stats}

    # Clasificar reglas usadas
    for rule in rules_stats:
        regla_id = rule["regla_aplicada"]
        pct = rule["pct_coincidencia"] or 0
        score = rule["score_semantico_promedio"] or 0

        if pct > 70:
            classification["efectivas"].append(rule)
        elif pct < 30 and score > 0.7:
            classification["problematicas"].append(rule)
        elif score < 0.6:
            classification["necesarias"].append(rule)
        else:
            classification["normales"].append(rule)

    # Reglas no usadas
    for rule_id, rule_data in all_rules.items():
        if not isinstance(rule_data, dict):
            continue
        if not rule_data.get("activa", True):
            continue
        if rule_id not in used_rules:
            classification["sin_uso"].append({
                "regla_aplicada": rule_id,
                "nombre": rule_data.get("nombre", ""),
                "condicion": str(rule_data.get("condicion", {}))[:100]
            })

    return classification


def generate_report(verbose: bool = False) -> str:
    """Genera el reporte de efectividad."""
    lines = []
    lines.append("=" * 70)
    lines.append("AUDITORIA DE EFECTIVIDAD DE REGLAS DE NEGOCIO")
    lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70)

    # Cargar datos
    all_rules = load_all_rules()
    rules_stats = get_rules_from_db()
    decision_summary = get_decision_summary()
    problematic_cases = get_problematic_cases()

    # Clasificar
    classification = classify_rules(rules_stats, all_rules)

    # Resumen general
    lines.append("\n## RESUMEN GENERAL")
    lines.append(f"Total reglas en config: {len([r for r in all_rules.values() if isinstance(r, dict) and r.get('activa', True)])}")
    lines.append(f"Reglas usadas: {len(rules_stats)}")
    lines.append(f"Reglas sin uso: {len(classification['sin_uso'])}")

    # Decisiones
    lines.append("\n## DECISIONES (v3.5.1)")
    for metodo, total in sorted(decision_summary.items(), key=lambda x: -x[1]):
        lines.append(f"  {metodo}: {total}")

    # Reglas problemáticas (alta prioridad)
    lines.append("\n## REGLAS PROBLEMATICAS (REVISAR)")
    lines.append("Reglas donde semántico da score > 0.7 pero coincidencia < 30%")
    lines.append("Esto indica que la regla puede estar forzando un ISCO incorrecto.")
    lines.append("-" * 50)
    if classification["problematicas"]:
        for rule in classification["problematicas"]:
            lines.append(f"  {rule['regla_aplicada']}")
            lines.append(f"    Usos: {rule['usos_total']}, Coincidencia: {rule['pct_coincidencia']}%")
            lines.append(f"    Score semántico: {rule['score_semantico_promedio']:.3f} (min: {rule['score_min']:.2f}, max: {rule['score_max']:.2f})")
    else:
        lines.append("  (ninguna)")

    # Reglas necesarias (semántico falla)
    lines.append("\n## REGLAS NECESARIAS")
    lines.append("Reglas donde semántico tiene score bajo (<0.6) - la regla corrige un error.")
    lines.append("-" * 50)
    if classification["necesarias"]:
        for rule in classification["necesarias"][:10]:
            lines.append(f"  {rule['regla_aplicada']}: {rule['usos_total']} usos, score_sem={rule['score_semantico_promedio']:.3f}")
    else:
        lines.append("  (ninguna)")

    # Reglas efectivas
    lines.append("\n## REGLAS EFECTIVAS")
    lines.append("Reglas con > 70% coincidencia con semántico - validadas automáticamente.")
    lines.append("-" * 50)
    if classification["efectivas"]:
        for rule in classification["efectivas"][:10]:
            lines.append(f"  {rule['regla_aplicada']}: {rule['usos_total']} usos, coincidencia={rule['pct_coincidencia']}%")
    else:
        lines.append("  (ninguna)")

    # Reglas sin uso
    lines.append("\n## REGLAS SIN USO")
    lines.append(f"Reglas activas que no aplicaron a ninguna oferta ({len(classification['sin_uso'])} total)")
    lines.append("-" * 50)
    if classification["sin_uso"]:
        for rule in classification["sin_uso"][:15]:
            lines.append(f"  {rule['regla_aplicada']}: {rule['nombre']}")
            if verbose:
                lines.append(f"    Condición: {rule['condicion']}...")
    else:
        lines.append("  (ninguna)")

    # Casos problemáticos específicos
    if problematic_cases:
        lines.append("\n## CASOS A REVISAR (override semántico alto)")
        lines.append("-" * 50)
        for case in problematic_cases[:5]:
            lines.append(f"  ID: {case['id_oferta']}")
            lines.append(f"  Título: {case['titulo_limpio'][:60]}...")
            lines.append(f"  Regla: {case['regla_aplicada']} -> ISCO {case['isco_regla']}")
            lines.append(f"  Semántico: ISCO {case['isco_semantico']} (score: {case['score_semantico']:.2f})")
            lines.append(f"  Decisión: {case['decision_metodo']}")
            lines.append("")

    # Recomendaciones
    lines.append("\n## RECOMENDACIONES")
    lines.append("-" * 50)

    n_problematicas = len(classification["problematicas"])
    n_sin_uso = len(classification["sin_uso"])

    if n_problematicas > 0:
        lines.append(f"1. REVISAR {n_problematicas} reglas problemáticas - pueden tener ISCO incorrecto")

    if n_sin_uso > 10:
        lines.append(f"2. Considerar desactivar {n_sin_uso} reglas sin uso para limpiar config")

    if not decision_summary:
        lines.append("3. Reprocesar ofertas con v3.5.1 para poblar decision_metodo")

    if len(classification["efectivas"]) > 0:
        lines.append(f"4. {len(classification['efectivas'])} reglas son efectivas y están validadas por semántico")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Auditar efectividad de reglas de negocio")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar más detalles")
    parser.add_argument("--export", type=str, help="Exportar reporte a archivo")
    args = parser.parse_args()

    report = generate_report(verbose=args.verbose)

    if args.export:
        export_path = Path(args.export)
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Reporte exportado a: {export_path}")
    else:
        print(report)


if __name__ == "__main__":
    main()
