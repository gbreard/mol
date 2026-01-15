"""
Analiza patrones de errores y genera reportes para Claude.

Este script es el punto de entrada para la CAPA 4 del pipeline:
- Lee errores agrupados de la cola
- Presenta PATRONES (no casos individuales) a Claude
- Claude propone reglas genéricas para config/*.json

Uso:
    python scripts/analyze_error_patterns.py
    python scripts/analyze_error_patterns.py --desde-archivo metrics/cola_claude_*.json
    python scripts/analyze_error_patterns.py --validar-primero --limit 100

Version: 1.0
Fecha: 2026-01-14
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Agregar path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.auto_validator import AutoValidator, validar_ofertas_desde_bd
from database.auto_corrector import AutoCorrector, procesar_validacion_completa


def cargar_cola_claude(archivo: Path) -> dict:
    """Carga un archivo de cola de Claude."""
    with open(archivo, 'r', encoding='utf-8') as f:
        return json.load(f)


def encontrar_ultimo_archivo_cola() -> Path | None:
    """Encuentra el archivo de cola más reciente."""
    metrics_dir = Path(__file__).parent.parent / "metrics"
    archivos = list(metrics_dir.glob("cola_claude_*.json"))
    if not archivos:
        return None
    return max(archivos, key=lambda x: x.stat().st_mtime)


def generar_sugerencia_regla(patron: dict) -> dict:
    """
    Genera una sugerencia de regla basada en el patrón.

    Args:
        patron: Patrón de error con ejemplos

    Returns:
        Sugerencia de regla para agregar a config
    """
    diagnostico = patron.get("diagnostico")
    ejemplos = patron.get("ejemplos", [])
    config_afectado = patron.get("config_afectado")

    sugerencia = {
        "diagnostico": diagnostico,
        "config": config_afectado,
        "regla_propuesta": None,
        "confianza": "baja"
    }

    if diagnostico == "error_matching" and ejemplos:
        # Intentar detectar patrón en títulos
        titulos = [e.get("titulo_limpio", "") for e in ejemplos if e.get("titulo_limpio")]
        if titulos:
            # Buscar palabras comunes
            palabras_comunes = _encontrar_palabras_comunes(titulos)
            if palabras_comunes:
                sugerencia["regla_propuesta"] = {
                    "id": f"R_AUTO_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "condicion": {
                        "titulo_contiene_alguno": list(palabras_comunes)
                    },
                    "accion": {
                        "forzar_isco": "XXXX",
                        "_nota": "COMPLETAR: Determinar ISCO correcto"
                    }
                }
                sugerencia["confianza"] = "media"

    elif diagnostico == "error_nlp_seniority" and ejemplos:
        # Buscar keywords de seniority en títulos
        titulos = [e.get("titulo_limpio", "").lower() for e in ejemplos if e.get("titulo_limpio")]
        keywords_detectadas = set()
        for titulo in titulos:
            for kw in ["jr", "sr", "senior", "junior", "trainee", "jefe", "gerente", "lead"]:
                if kw in titulo:
                    keywords_detectadas.add(kw)

        if keywords_detectadas:
            sugerencia["regla_propuesta"] = {
                "keywords_detectadas": list(keywords_detectadas),
                "agregar_a": "nivel_seniority.reglas",
                "_nota": "Mapear cada keyword al seniority correspondiente"
            }
            sugerencia["confianza"] = "media"

    elif diagnostico == "error_nlp_area" and ejemplos:
        # Analizar sectores y títulos
        sectores = [e.get("sector_empresa", "") for e in ejemplos if e.get("sector_empresa")]
        sector_mas_comun = max(set(sectores), key=sectores.count) if sectores else None

        sugerencia["regla_propuesta"] = {
            "sector_detectado": sector_mas_comun,
            "agregar_a": "area_funcional.reglas",
            "_nota": f"Inferir área desde sector '{sector_mas_comun}'"
        }
        sugerencia["confianza"] = "baja"

    return sugerencia


def _encontrar_palabras_comunes(textos: list, min_frecuencia: int = 2) -> set:
    """Encuentra palabras que aparecen en múltiples textos."""
    palabras_por_texto = []
    for texto in textos:
        palabras = set(texto.lower().split())
        # Filtrar palabras cortas y stopwords
        palabras = {p for p in palabras if len(p) > 3 and p not in {
            "para", "como", "desde", "hasta", "entre", "sobre", "bajo",
            "este", "esta", "esto", "esos", "esas", "aquí", "allí"
        }}
        palabras_por_texto.append(palabras)

    if not palabras_por_texto:
        return set()

    # Contar frecuencia
    frecuencia = defaultdict(int)
    for palabras in palabras_por_texto:
        for palabra in palabras:
            frecuencia[palabra] += 1

    return {p for p, f in frecuencia.items() if f >= min_frecuencia}


def generar_reporte_patrones(patrones: list) -> str:
    """
    Genera un reporte formateado de patrones para análisis.

    Args:
        patrones: Lista de patrones de la cola de Claude

    Returns:
        Reporte en texto formateado
    """
    if not patrones:
        return "No hay patrones que analizar."

    lineas = [
        "=" * 70,
        "REPORTE DE PATRONES DE ERROR",
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        f"Total de patrones: {len(patrones)}",
        f"Total de ofertas afectadas: {sum(p.get('cantidad', 0) for p in patrones)}",
        "",
    ]

    for i, patron in enumerate(patrones, 1):
        lineas.append("-" * 70)
        lineas.append(f"PATRÓN #{i}: {patron.get('diagnostico', 'N/A')}")
        lineas.append("-" * 70)
        lineas.append(f"  Cantidad de ofertas: {patron.get('cantidad', 0)}")
        lineas.append(f"  Config afectado: {patron.get('config_afectado', 'N/A')}")
        lineas.append("")

        # Ejemplos
        lineas.append("  EJEMPLOS:")
        for j, ej in enumerate(patron.get("ejemplos", [])[:5], 1):
            lineas.append(f"    {j}. ID: {ej.get('id_oferta', 'N/A')}")
            lineas.append(f"       Título: {ej.get('titulo_limpio', 'N/A')}")
            if ej.get("isco_code"):
                lineas.append(f"       ISCO: {ej.get('isco_code')} - {ej.get('esco_label', '')}")
            if ej.get("area_funcional"):
                lineas.append(f"       Área: {ej.get('area_funcional')}")
            if ej.get("nivel_seniority"):
                lineas.append(f"       Seniority: {ej.get('nivel_seniority')}")
            lineas.append("")

        # Sugerencia de regla
        sugerencia = generar_sugerencia_regla(patron)
        lineas.append("  SUGERENCIA DE REGLA:")
        lineas.append(f"    Confianza: {sugerencia.get('confianza', 'N/A')}")
        if sugerencia.get("regla_propuesta"):
            lineas.append(f"    Propuesta: {json.dumps(sugerencia['regla_propuesta'], indent=6, ensure_ascii=False)}")
        else:
            lineas.append("    Propuesta: Requiere análisis manual")

        lineas.append("")

    lineas.append("=" * 70)
    lineas.append("FIN DEL REPORTE")
    lineas.append("=" * 70)

    return "\n".join(lineas)


def generar_json_sugerencias(patrones: list) -> list:
    """
    Genera lista de sugerencias en formato JSON.

    Args:
        patrones: Lista de patrones

    Returns:
        Lista de sugerencias de reglas
    """
    sugerencias = []
    for patron in patrones:
        sug = generar_sugerencia_regla(patron)
        sug["patron_id"] = f"P{patrones.index(patron)+1}"
        sug["ofertas_afectadas"] = patron.get("ids", [])
        sugerencias.append(sug)
    return sugerencias


def main():
    parser = argparse.ArgumentParser(description="Analiza patrones de errores para Claude")
    parser.add_argument("--desde-archivo", type=str, help="Cargar desde archivo JSON existente")
    parser.add_argument("--validar-primero", action="store_true", help="Ejecutar validación primero")
    parser.add_argument("--limit", type=int, help="Limite de ofertas a validar")
    parser.add_argument("--ids", type=str, help="IDs específicos separados por coma")
    parser.add_argument("--output-json", type=str, help="Guardar sugerencias en JSON")
    parser.add_argument("--quiet", action="store_true", help="Solo mostrar resumen")

    args = parser.parse_args()

    patrones = []

    if args.desde_archivo:
        # Cargar desde archivo existente
        archivo = Path(args.desde_archivo)
        if not archivo.exists():
            print(f"Error: Archivo no encontrado: {archivo}")
            sys.exit(1)
        print(f"Cargando desde: {archivo}")
        data = cargar_cola_claude(archivo)
        patrones = data.get("patrones", [])

    elif args.validar_primero:
        # Ejecutar validación completa
        ids = args.ids.split(",") if args.ids else None
        print("Ejecutando validación y corrección...")
        resultados = procesar_validacion_completa(limit=args.limit, ids=ids)

        if resultados.get("correccion"):
            patrones = resultados["correccion"].get("patrones_para_claude", [])

    else:
        # Buscar último archivo de cola
        archivo = encontrar_ultimo_archivo_cola()
        if archivo:
            print(f"Cargando último archivo: {archivo}")
            data = cargar_cola_claude(archivo)
            patrones = data.get("patrones", [])
        else:
            print("No se encontró archivo de cola. Use --validar-primero para generar uno.")
            sys.exit(1)

    if not patrones:
        print("\nNo hay patrones de error que analizar.")
        print("El sistema pasó todas las validaciones automáticamente.")
        sys.exit(0)

    # Generar reporte
    if not args.quiet:
        reporte = generar_reporte_patrones(patrones)
        print("\n" + reporte)

    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"Patrones detectados: {len(patrones)}")
    print(f"Ofertas totales afectadas: {sum(p.get('cantidad', 0) for p in patrones)}")

    por_diagnostico = defaultdict(int)
    for p in patrones:
        por_diagnostico[p.get("diagnostico", "N/A")] += p.get("cantidad", 0)

    print("\nPor tipo de error:")
    for diag, count in sorted(por_diagnostico.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {diag}: {count}")

    # Guardar JSON si se pidió
    if args.output_json:
        sugerencias = generar_json_sugerencias(patrones)
        output_path = Path(args.output_json)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "sugerencias": sugerencias,
                "resumen": dict(por_diagnostico)
            }, f, indent=2, ensure_ascii=False)
        print(f"\nSugerencias guardadas en: {output_path}")

    # Instrucciones finales
    print("\n" + "=" * 50)
    print("PRÓXIMOS PASOS")
    print("=" * 50)
    print("1. Revisar cada patrón y decidir acción")
    print("2. Para errores de matching: editar config/matching_rules_business.json")
    print("3. Para errores NLP: editar config/nlp_inference_rules.json")
    print("4. Reprocesar ofertas afectadas con el pipeline")
    print("5. Verificar que los errores se corrigieron")


if __name__ == "__main__":
    main()
