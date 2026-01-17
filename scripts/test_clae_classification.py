#!/usr/bin/env python3
"""
Test CLAE Classification - Script de prueba para clasificación de sector a CLAE.

Este script:
1. Lee ofertas de la BD (validadas u otras según filtro)
2. Aplica clasificación CLAE usando el diccionario de keywords
3. Genera reporte Excel para revisión manual
4. NO MODIFICA LA BD - solo genera output

Uso:
    python scripts/test_clae_classification.py --limit 10
    python scripts/test_clae_classification.py --ids 123,456,789
    python scripts/test_clae_classification.py --estado validado --limit 50
"""

import sys
import os
import json
import sqlite3
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bumeran_scraping.db"
CONFIG_PATH = PROJECT_ROOT / "config"
OUTPUT_PATH = PROJECT_ROOT / "exports"


class CLAEClassifier:
    """Clasificador de sector a código CLAE usando diccionario de keywords."""

    def __init__(self):
        self.nomenclador = self._load_nomenclador()
        self.keywords_map = self._load_keywords_map()
        self.stats = {
            "total": 0,
            "clasificados": 0,
            "sin_clasificar": 0,
            "por_keyword": 0,
            "por_sector_fallback": 0
        }

    def _load_nomenclador(self) -> dict:
        """Carga el nomenclador CLAE completo."""
        path = CONFIG_PATH / "clae_nomenclador.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_keywords_map(self) -> dict:
        """Carga el diccionario de keywords a CLAE."""
        path = CONFIG_PATH / "clae_keywords_map.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def classify(self, oferta: dict) -> dict:
        """
        Clasifica una oferta a código CLAE.

        PRIORIDAD:
        1. sector_empresa (más confiable)
        2. titulo_limpio (específico del puesto)
        3. descripcion (puede tener keywords genéricos - menor peso)

        Args:
            oferta: dict con campos de ofertas_nlp

        Returns:
            dict con clae_code, clae_grupo, clae_seccion, clae_nombre, match_method
        """
        self.stats["total"] += 1

        sector_texto = oferta.get("sector_empresa", "") or ""
        titulo = oferta.get("titulo_limpio", "") or oferta.get("titulo", "") or ""
        descripcion = oferta.get("descripcion", "") or ""

        # PASO 1: Buscar por sector_empresa (PRIORIDAD MÁXIMA)
        # El sector ya fue extraído/inferido por el NLP, es más confiable
        if sector_texto:
            result = self._match_by_sector_fallback(sector_texto)
            if result:
                self.stats["clasificados"] += 1
                self.stats["por_sector_fallback"] += 1
                result["match_method"] = "sector_empresa"
                return result

        # PASO 2: Buscar por titulo_limpio (SEGUNDA PRIORIDAD)
        result = self._match_by_keywords(titulo.lower())
        if result:
            self.stats["clasificados"] += 1
            self.stats["por_keyword"] += 1
            result["match_method"] = "keyword_titulo"
            return result

        # PASO 3: Buscar por sector + titulo combinados
        texto_combinado = f"{sector_texto} {titulo}".lower()
        result = self._match_by_keywords(texto_combinado)
        if result:
            self.stats["clasificados"] += 1
            self.stats["por_keyword"] += 1
            result["match_method"] = "keyword_combinado"
            return result

        # PASO 4: Fallback descripción (ÚLTIMO RECURSO - keywords genéricos)
        # Solo si no hay otra opción, y con keywords más específicos
        result = self._match_by_keywords(descripcion.lower()[:500])
        if result:
            self.stats["clasificados"] += 1
            self.stats["por_keyword"] += 1
            result["match_method"] = "keyword_descripcion"
            return result

        # No clasificado
        self.stats["sin_clasificar"] += 1
        return {
            "clae_code": None,
            "clae_grupo": None,
            "clae_seccion": None,
            "clae_nombre": None,
            "match_method": "none"
        }

    def _match_by_keywords(self, texto: str) -> Optional[dict]:
        """Busca match por keywords en el texto."""
        best_match = None
        best_score = 0

        for mapping in self.keywords_map.get("mappings", []):
            score = 0
            for kw in mapping.get("keywords", []):
                if kw.lower() in texto:
                    # Dar más peso a keywords más largos (más específicos)
                    score += len(kw)

            if score > best_score:
                best_score = score
                best_match = mapping

        if best_match:
            return {
                "clae_code": best_match["clae"],
                "clae_grupo": best_match.get("grupo", best_match["clae"][:3]),
                "clae_seccion": best_match.get("seccion"),
                "clae_nombre": best_match.get("nombre")
            }
        return None

    def _match_by_sector_fallback(self, sector_texto: str) -> Optional[dict]:
        """
        Busca el sector_empresa en mappings.

        Prioridad:
        1. sector_directo (mapeo exacto)
        2. sector_actual en mappings (substring match)
        """
        if not sector_texto:
            return None

        sector_clean = sector_texto.strip()

        # Paso 1: Buscar en sector_directo (mapeo exacto)
        sector_directo = self.keywords_map.get("sector_directo", {})
        if sector_clean in sector_directo:
            data = sector_directo[sector_clean]
            return {
                "clae_code": data["clae"],
                "clae_grupo": data.get("grupo", data["clae"][:3]),
                "clae_seccion": data.get("seccion"),
                "clae_nombre": data.get("nombre")
            }

        # Paso 2: Buscar case-insensitive
        sector_lower = sector_clean.lower()
        for key, data in sector_directo.items():
            if key.lower() == sector_lower:
                return {
                    "clae_code": data["clae"],
                    "clae_grupo": data.get("grupo", data["clae"][:3]),
                    "clae_seccion": data.get("seccion"),
                    "clae_nombre": data.get("nombre")
                }

        # Paso 3: Fallback a sector_actual en mappings (substring match)
        for mapping in self.keywords_map.get("mappings", []):
            sector_actual = mapping.get("sector_actual", "").lower()
            if sector_actual and sector_actual in sector_lower:
                return {
                    "clae_code": mapping["clae"],
                    "clae_grupo": mapping.get("grupo", mapping["clae"][:3]),
                    "clae_seccion": mapping.get("seccion"),
                    "clae_nombre": mapping.get("nombre")
                }

        return None

    def get_descripcion(self, clae_code: str) -> str:
        """Obtiene descripción de un código CLAE del nomenclador."""
        if not clae_code:
            return ""
        actividad = self.nomenclador.get("actividades", {}).get(str(clae_code), {})
        return actividad.get("nombre", "")


def get_ofertas(conn: sqlite3.Connection, ids: List[str] = None,
                estado: str = None, limit: int = 10) -> List[dict]:
    """Obtiene ofertas de la BD según filtros."""

    query = """
        SELECT
            o.id_oferta,
            o.titulo,
            onlp.titulo_limpio,
            o.descripcion,
            onlp.sector_empresa,
            onlp.area_funcional,
            oem.isco_code,
            oem.isco_label,
            oem.estado_validacion
        FROM ofertas o
        LEFT JOIN ofertas_nlp onlp ON o.id_oferta = onlp.id_oferta
        LEFT JOIN ofertas_esco_matching oem ON o.id_oferta = oem.id_oferta
        WHERE 1=1
    """
    params = []

    if ids:
        placeholders = ','.join('?' * len(ids))
        query += f" AND o.id_oferta IN ({placeholders})"
        params.extend(ids)

    if estado:
        query += " AND oem.estado_validacion = ?"
        params.append(estado)

    query += f" LIMIT {limit}"

    cursor = conn.execute(query, params)
    columns = [desc[0] for desc in cursor.description]

    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def export_results(results: List[dict], output_file: Path):
    """Exporta resultados a CSV."""
    import csv

    if not results:
        print("No hay resultados para exportar")
        return

    fieldnames = list(results[0].keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nExportado: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Test CLAE Classification")
    parser.add_argument("--ids", type=str, help="IDs de ofertas separados por coma")
    parser.add_argument("--estado", type=str, default="validado",
                        help="Estado de validación (default: validado)")
    parser.add_argument("--limit", type=int, default=10, help="Límite de ofertas")
    parser.add_argument("--output", type=str, help="Archivo de salida (default: auto)")
    args = parser.parse_args()

    # Parsear IDs
    ids = None
    if args.ids:
        ids = [x.strip() for x in args.ids.split(",")]

    # Conectar BD
    if not DB_PATH.exists():
        print(f"Error: BD no encontrada en {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))

    # Obtener ofertas
    print(f"Obteniendo ofertas (estado={args.estado}, limit={args.limit})...")
    ofertas = get_ofertas(conn, ids=ids, estado=args.estado, limit=args.limit)
    print(f"Ofertas obtenidas: {len(ofertas)}")

    if not ofertas:
        print("No se encontraron ofertas con los filtros especificados")
        conn.close()
        sys.exit(0)

    # Clasificar
    print("\nClasificando ofertas a CLAE...")
    classifier = CLAEClassifier()

    results = []
    for oferta in ofertas:
        clae_result = classifier.classify(oferta)

        # Combinar oferta + clasificación CLAE
        result = {
            "id_oferta": oferta["id_oferta"],
            "titulo": oferta.get("titulo", "")[:50],
            "titulo_limpio": oferta.get("titulo_limpio", "")[:50],
            "sector_empresa": oferta.get("sector_empresa", ""),
            "isco_code": oferta.get("isco_code", ""),
            "isco_label": oferta.get("isco_label", ""),
            "clae_code": clae_result["clae_code"],
            "clae_grupo": clae_result["clae_grupo"],
            "clae_seccion": clae_result["clae_seccion"],
            "clae_nombre": clae_result["clae_nombre"],
            "match_method": clae_result["match_method"],
            "clae_ok": ""  # Para revisión manual
        }
        results.append(result)

    # Estadísticas
    print("\n=== ESTADÍSTICAS ===")
    print(f"Total procesadas: {classifier.stats['total']}")
    print(f"Clasificadas: {classifier.stats['clasificados']} ({100*classifier.stats['clasificados']/max(1,classifier.stats['total']):.1f}%)")
    print(f"  - Por keyword: {classifier.stats['por_keyword']}")
    print(f"  - Por sector fallback: {classifier.stats['por_sector_fallback']}")
    print(f"Sin clasificar: {classifier.stats['sin_clasificar']}")

    # Mostrar preview
    print("\n=== PREVIEW (primeras 5) ===")
    for r in results[:5]:
        print(f"\n{r['id_oferta']}: {r['titulo_limpio']}")
        print(f"  Sector actual: {r['sector_empresa']}")
        print(f"  CLAE: {r['clae_code']} ({r['clae_seccion']}) - {r['clae_nombre']}")
        print(f"  Método: {r['match_method']}")

    # Exportar
    OUTPUT_PATH.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_PATH / f"clae_test_{timestamp}.csv"
    if args.output:
        output_file = Path(args.output)

    export_results(results, output_file)

    conn.close()
    print("\nTest completado. Revisar CSV para validar clasificaciones.")


if __name__ == "__main__":
    main()
