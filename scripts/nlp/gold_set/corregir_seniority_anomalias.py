# -*- coding: utf-8 -*-
"""
Corrige anomalias de seniority detectadas en Gold Set 100:
1. "junior o semi-senior" -> "semisenior"
2. Casos sin seniority: intentar inferir
3. exp=0 cuando deberia ser NULL
"""
import sqlite3
import json
import re
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"
CONFIG_PATH = BASE / "config" / "nlp_inference_rules.json"
GOLD_SET_PATH = BASE / "database" / "gold_set_nlp_100_ids.json"


def cargar_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def inferir_seniority_de_texto(descripcion, config):
    """Infiere seniority buscando keywords en descripcion."""
    if not descripcion:
        return None

    texto = descripcion.lower()
    reglas = config.get("nivel_seniority", {}).get("reglas", [])

    for regla in sorted(reglas, key=lambda x: x.get("prioridad", 99)):
        keywords = regla.get("contiene_cualquiera", [])
        for kw in keywords:
            if kw.lower() in texto:
                return regla.get("resultado")

    return None


def extraer_experiencia_de_texto(descripcion):
    """Extrae años de experiencia del texto."""
    if not descripcion:
        return None

    texto = descripcion.lower()

    # Patrones de experiencia
    patrones = [
        r'(\d+)\s*(?:años?|anos?)\s*(?:de\s*)?experiencia',
        r'experiencia\s*(?:de\s*)?(\d+)\s*(?:años?|anos?)',
        r'experiencia\s*minima?\s*(?:de\s*)?(\d+)',
        r'minimo?\s*(\d+)\s*(?:años?|anos?)\s*(?:de\s*)?experiencia',
    ]

    # Patrones a excluir (edad)
    patrones_excluir = [
        r'edad\s*(?:de\s*)?(\d+)',
        r'(\d+)\s*(?:años?|anos?)\s*(?:de\s*)?edad',
        r'entre\s*(\d+)\s*y\s*(\d+)\s*años?',  # rango de edad
    ]

    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            valor = int(match.group(1))
            # Verificar que no sea edad (valores tipicos de edad: 18-65)
            contexto = texto[max(0, match.start()-30):match.end()+30]
            es_edad = any(re.search(p, contexto) for p in patrones_excluir)
            if not es_edad and valor < 15:  # experiencia razonable
                return valor

    return None


def analizar_anomalias(dry_run=True):
    """Analiza y corrige anomalias en Gold Set."""
    config = cargar_config()

    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        ids = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    correcciones = []

    # 1. Corregir "junior o semi-senior" -> "semisenior"
    print("=" * 70)
    print("1. SENIORITY NO NORMALIZADO")
    print("=" * 70)

    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT id_oferta, nivel_seniority, titulo_limpio
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
        AND nivel_seniority LIKE '%o %'
    """, ids)

    for row in c.fetchall():
        id_o, seniority, titulo = row
        print(f"ID {id_o}: '{seniority}' -> 'semisenior'")
        print(f"   Titulo: {titulo}")
        correcciones.append({
            'id': id_o,
            'campo': 'nivel_seniority',
            'valor_viejo': seniority,
            'valor_nuevo': 'semisenior',
            'razon': 'normalizar valor compuesto'
        })

    # 2. Casos sin seniority
    print()
    print("=" * 70)
    print("2. CASOS SIN SENIORITY (intentar inferir)")
    print("=" * 70)

    c.execute(f"""
        SELECT n.id_oferta, n.titulo_limpio, n.experiencia_min_anios, o.descripcion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta IN ({placeholders})
        AND n.nivel_seniority IS NULL
    """, ids)

    for row in c.fetchall():
        id_o, titulo, exp_min, descripcion = row
        print(f"\nID {id_o}: {titulo}")

        # Intentar inferir de descripcion
        seniority_inferido = inferir_seniority_de_texto(descripcion, config)

        # Si no hay inferencia por keywords, usar experiencia
        if not seniority_inferido and exp_min is not None:
            rangos = config.get("nivel_seniority", {}).get("inferencia_por_experiencia", {}).get("rangos", [])
            for rango in rangos:
                if rango.get("exp_min", 0) <= exp_min <= rango.get("exp_max", 99):
                    seniority_inferido = rango.get("resultado")
                    break

        if seniority_inferido:
            print(f"   -> Inferido: {seniority_inferido}")
            correcciones.append({
                'id': id_o,
                'campo': 'nivel_seniority',
                'valor_viejo': None,
                'valor_nuevo': seniority_inferido,
                'razon': 'inferido de descripcion/experiencia'
            })
        else:
            # Buscar experiencia en texto
            exp_texto = extraer_experiencia_de_texto(descripcion)
            if exp_texto:
                print(f"   -> Experiencia detectada en texto: {exp_texto} anos")
                # Inferir seniority
                rangos = config.get("nivel_seniority", {}).get("inferencia_por_experiencia", {}).get("rangos", [])
                for rango in rangos:
                    if rango.get("exp_min", 0) <= exp_texto <= rango.get("exp_max", 99):
                        seniority_inferido = rango.get("resultado")
                        break
                if seniority_inferido:
                    print(f"   -> Seniority inferido: {seniority_inferido}")
                    correcciones.append({
                        'id': id_o,
                        'campo': 'nivel_seniority',
                        'valor_viejo': None,
                        'valor_nuevo': seniority_inferido,
                        'razon': 'inferido de experiencia en texto'
                    })
                    correcciones.append({
                        'id': id_o,
                        'campo': 'experiencia_min_anios',
                        'valor_viejo': exp_min,
                        'valor_nuevo': exp_texto,
                        'razon': 'extraido de descripcion'
                    })
            else:
                print(f"   -> No se pudo inferir (sin keywords ni experiencia)")

    # 3. Verificar exp=0 sospechosos
    print()
    print("=" * 70)
    print("3. CASOS CON EXP=0 (verificar si correcto)")
    print("=" * 70)

    c.execute(f"""
        SELECT n.id_oferta, n.titulo_limpio, n.nivel_seniority, o.descripcion
        FROM ofertas_nlp n
        JOIN ofertas o ON n.id_oferta = o.id_oferta
        WHERE n.id_oferta IN ({placeholders})
        AND n.experiencia_min_anios = 0
        AND n.nivel_seniority NOT IN ('trainee')
    """, ids)

    for row in c.fetchall():
        id_o, titulo, seniority, descripcion = row
        exp_texto = extraer_experiencia_de_texto(descripcion)

        if exp_texto and exp_texto > 0:
            print(f"\nID {id_o}: {titulo}")
            print(f"   Actual: seniority={seniority}, exp=0")
            print(f"   -> Experiencia en texto: {exp_texto} anos")
            correcciones.append({
                'id': id_o,
                'campo': 'experiencia_min_anios',
                'valor_viejo': 0,
                'valor_nuevo': exp_texto,
                'razon': 'extraido de descripcion (era 0)'
            })

    # Resumen
    print()
    print("=" * 70)
    print(f"RESUMEN: {len(correcciones)} correcciones a aplicar")
    print("=" * 70)

    for corr in correcciones:
        print(f"  {corr['id']}: {corr['campo']} = {corr['valor_viejo']} -> {corr['valor_nuevo']}")

    if dry_run:
        print(f"\n[DRY RUN] No se modifico la BD. Usar --apply para aplicar.")
        conn.close()
        return correcciones

    # Aplicar
    print("\nAplicando cambios...")
    for corr in correcciones:
        c.execute(f"""
            UPDATE ofertas_nlp
            SET {corr['campo']} = ?
            WHERE id_oferta = ?
        """, (corr['valor_nuevo'], corr['id']))

    conn.commit()
    print(f"[OK] {len(correcciones)} correcciones aplicadas")
    conn.close()

    return correcciones


if __name__ == "__main__":
    import sys
    dry_run = "--apply" not in sys.argv
    analizar_anomalias(dry_run=dry_run)
