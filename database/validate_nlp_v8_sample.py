#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MOL-54: Validar Pipeline NLP v8.0 Antes de Escalar
===================================================

Revisa una muestra aleatoria de ofertas procesadas con NLP v8.0
para detectar problemas antes de escalar a 9,443 ofertas.
"""

import sqlite3
import json
import random
from pathlib import Path
from collections import Counter

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

def get_sample_offers(cursor, n=10):
    """Obtiene N ofertas aleatorias procesadas con v8.0.0"""
    cursor.execute("""
        SELECT v.id_oferta, v.titulo, v.empresa,
               v.resultado_capa0, v.resultado_capa1_verificado,
               v.items_verificados, v.items_descartados,
               v.confidence_score, v.coverage_score,
               o.descripcion
        FROM validacion_v7 v
        JOIN ofertas o ON CAST(v.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
        WHERE v.nlp_version = '8.0.0'
        ORDER BY RANDOM()
        LIMIT ?
    """, (n,))
    return cursor.fetchall()

def parse_json_safe(text):
    """Parse JSON de forma segura"""
    if not text:
        return {}
    try:
        return json.loads(text)
    except:
        return {}

def parse_nested_json(value):
    """Parse JSON que puede estar doblemente codificado"""
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed] if parsed else []
        except:
            return [value] if value else []
    return []

def analyze_offer(row):
    """Analiza una oferta individual"""
    id_oferta, titulo, empresa, capa0, capa1, items_v, items_d, conf, cov, desc = row

    capa0_data = parse_json_safe(capa0)
    capa1_data = parse_json_safe(capa1)

    # Extraer campos clave - nombres correctos del schema NLP v8
    skills_tec = parse_nested_json(capa1_data.get('skills_tecnicas_list'))
    skills_soft = parse_nested_json(capa1_data.get('soft_skills_list'))
    skills = skills_tec + skills_soft

    # Ubicacion desde capa0 (regex)
    ubicacion = capa0_data.get('ubicacion', '')

    # Otros campos
    responsabilidades = parse_nested_json(capa1_data.get('responsabilidades_list'))
    requisitos = parse_nested_json(capa1_data.get('requisitos_excluyentes_list'))
    beneficios = parse_nested_json(capa1_data.get('beneficios_list'))
    tecnologias = parse_nested_json(capa1_data.get('tecnologias_stack_list'))

    salario = capa0_data.get('salario', {})
    experiencia = capa0_data.get('experiencia', {})
    educacion = capa0_data.get('educacion', {})

    return {
        'id': id_oferta,
        'titulo': titulo,
        'empresa': empresa,
        'skills': skills,
        'skills_tec': skills_tec,
        'skills_soft': skills_soft,
        'skills_count': len(skills),
        'ubicacion': ubicacion,
        'salario': salario,
        'experiencia': experiencia,
        'educacion': educacion,
        'responsabilidades': responsabilidades,
        'requisitos': requisitos,
        'beneficios': beneficios,
        'tecnologias': tecnologias,
        'items_verificados': items_v,
        'items_descartados': items_d,
        'confidence': conf,
        'coverage': cov,
        'desc_len': len(desc) if desc else 0
    }

def detect_anomalies(analysis):
    """Detecta anomalias en el analisis"""
    anomalies = []

    # Sin ninguna extraccion en oferta con descripcion larga
    total_extracted = (len(analysis['skills_tec']) + len(analysis['skills_soft']) +
                      len(analysis['requisitos']) + len(analysis['responsabilidades']))
    if total_extracted == 0 and analysis['desc_len'] > 500:
        anomalies.append("Sin extraccion pero descripcion > 500 chars")

    # Confidence muy bajo
    if analysis['confidence'] and analysis['confidence'] < 0.5:
        anomalies.append(f"Confidence bajo: {analysis['confidence']:.2f}")

    # Items descartados > verificados (posible alucinacion)
    if analysis['items_descartados'] > analysis['items_verificados']:
        anomalies.append(f"Mas descartados ({analysis['items_descartados']}) que verificados ({analysis['items_verificados']})")

    # Coverage anomalo (solo si es muy extremo)
    if analysis['coverage'] and analysis['coverage'] > 500:
        anomalies.append(f"Coverage anomalo: {analysis['coverage']}")

    return anomalies

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print("MOL-54: VALIDACION NLP v8.0 - MUESTRA ALEATORIA")
    print("=" * 70)

    # Obtener muestra
    sample = get_sample_offers(cursor, n=10)
    print(f"\nMuestra: {len(sample)} ofertas aleatorias\n")

    all_analyses = []
    total_anomalies = []

    for i, row in enumerate(sample, 1):
        analysis = analyze_offer(row)
        anomalies = detect_anomalies(analysis)
        all_analyses.append(analysis)
        total_anomalies.extend(anomalies)

        print("-" * 70)
        print(f"[{i}/10] ID: {analysis['id']}")
        print(f"Titulo: {analysis['titulo'][:60]}...")
        print(f"Empresa: {analysis['empresa']}")
        print(f"Skills Tec ({len(analysis['skills_tec'])}): {', '.join(str(s) for s in analysis['skills_tec'][:3])}{'...' if len(analysis['skills_tec']) > 3 else ''}")
        print(f"Skills Soft ({len(analysis['skills_soft'])}): {', '.join(str(s) for s in analysis['skills_soft'][:3])}{'...' if len(analysis['skills_soft']) > 3 else ''}")
        print(f"Requisitos ({len(analysis['requisitos'])}): {', '.join(str(r)[:30] for r in analysis['requisitos'][:2])}{'...' if len(analysis['requisitos']) > 2 else ''}")
        print(f"Responsab ({len(analysis['responsabilidades'])}): {', '.join(str(r)[:30] for r in analysis['responsabilidades'][:2])}{'...' if len(analysis['responsabilidades']) > 2 else ''}")
        print(f"Tecnologias ({len(analysis['tecnologias'])}): {', '.join(str(t) for t in analysis['tecnologias'][:5])}")
        print(f"Confidence: {analysis['confidence']:.2f} | Coverage: {analysis['coverage']:.2f}")
        print(f"Items: {analysis['items_verificados']} verificados, {analysis['items_descartados']} descartados")

        if anomalies:
            print(f"[!] ANOMALIAS: {'; '.join(anomalies)}")
        else:
            print("[OK] Sin anomalias")

    # Resumen estadístico
    print("\n" + "=" * 70)
    print("RESUMEN ESTADÍSTICO")
    print("=" * 70)

    skills_counts = [a['skills_count'] for a in all_analyses]
    with_skills = sum(1 for c in skills_counts if c > 0)
    with_skills_tec = sum(1 for a in all_analyses if len(a['skills_tec']) > 0)
    with_skills_soft = sum(1 for a in all_analyses if len(a['skills_soft']) > 0)
    with_requisitos = sum(1 for a in all_analyses if len(a['requisitos']) > 0)
    with_responsab = sum(1 for a in all_analyses if len(a['responsabilidades']) > 0)
    with_tecnologias = sum(1 for a in all_analyses if len(a['tecnologias']) > 0)

    print(f"\nCobertura de campos (Capa 1 - LLM):")
    print(f"  - Con skills tecnicos: {with_skills_tec}/10 ({with_skills_tec*10}%)")
    print(f"  - Con skills blandos: {with_skills_soft}/10 ({with_skills_soft*10}%)")
    print(f"  - Con requisitos: {with_requisitos}/10 ({with_requisitos*10}%)")
    print(f"  - Con responsabilidades: {with_responsab}/10 ({with_responsab*10}%)")
    print(f"  - Con tecnologias: {with_tecnologias}/10 ({with_tecnologias*10}%)")

    print(f"\nSkills por oferta:")
    print(f"  - Promedio: {sum(skills_counts)/len(skills_counts):.1f}")
    print(f"  - Mínimo: {min(skills_counts)}")
    print(f"  - Máximo: {max(skills_counts)}")

    avg_conf = sum(a['confidence'] for a in all_analyses) / len(all_analyses)
    print(f"\nConfidence promedio: {avg_conf:.2f}")

    print(f"\nAnomalías detectadas: {len(total_anomalies)}")
    if total_anomalies:
        for anom in set(total_anomalies):
            count = total_anomalies.count(anom)
            print(f"  - {anom}: {count}x")

    # Veredicto
    print("\n" + "=" * 70)
    print("VEREDICTO PRELIMINAR")
    print("=" * 70)

    issues = []
    # Criterio: al menos 60% deben tener requisitos O responsabilidades (datos utiles)
    with_useful_data = sum(1 for a in all_analyses if len(a['requisitos']) > 0 or len(a['responsabilidades']) > 0)
    if with_useful_data < 6:
        issues.append(f"Cobertura datos utiles baja: {with_useful_data*10}% < 60%")
    if len(total_anomalies) > 5:
        issues.append(f"Demasiadas anomalias: {len(total_anomalies)}")
    if avg_conf < 0.7:
        issues.append(f"Confidence promedio bajo: {avg_conf:.2f} < 0.70")

    if issues:
        print("[!] REQUIERE REVISION:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[OK] MUESTRA APROBADA - Pipeline funcionando correctamente")

    conn.close()

    return {
        'with_skills_pct': with_skills * 10,
        'avg_confidence': avg_conf,
        'anomalies_count': len(total_anomalies),
        'issues': issues
    }

if __name__ == "__main__":
    main()
