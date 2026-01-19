#!/usr/bin/env python3
"""
Script para normalizar ubicaciones con códigos INDEC
=====================================================

Parsea el campo 'localizacion' de ofertas y normaliza contra
códigos INDEC oficiales de provincias argentinas.

Proceso:
1. Agregar columnas normalizadas a tabla ofertas
2. Parsear campo localizacion ("Localidad, Provincia")
3. Matching de provincias (exacto + variantes + fuzzy)
4. Actualizar ofertas con datos normalizados

Uso:
    python normalizar_ubicaciones.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict
import unicodedata
import re


def normalize_string(s: str) -> str:
    """
    Normaliza un string para matching:
    - Lowercase
    - Sin acentos
    - Sin espacios extra
    - Sin puntuación
    """
    if not s:
        return ""

    # Lowercase
    s = s.lower()

    # Quitar acentos
    s = unicodedata.normalize('NFKD', s)
    s = ''.join([c for c in s if not unicodedata.combining(c)])

    # Quitar puntuación y espacios múltiples
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)

    return s.strip()


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcula la distancia de Levenshtein entre dos strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 en lugar de j ya que previous_row y current_row son 1 más largos
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity_score(s1: str, s2: str) -> float:
    """
    Calcula score de similitud (0-100%) entre dos strings
    Usa distancia de Levenshtein normalizada
    """
    if not s1 or not s2:
        return 0.0

    s1_norm = normalize_string(s1)
    s2_norm = normalize_string(s2)

    if s1_norm == s2_norm:
        return 100.0

    distance = levenshtein_distance(s1_norm, s2_norm)
    max_len = max(len(s1_norm), len(s2_norm))

    if max_len == 0:
        return 0.0

    similarity = (1 - distance / max_len) * 100
    return similarity


class UbicacionNormalizer:
    """Normalizador de ubicaciones con códigos INDEC"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.provincias_cache: Dict[str, Dict] = {}
        self._load_provincias()

    def _load_provincias(self):
        """Carga provincias INDEC en memoria para matching rápido"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo_provincia, nombre_oficial, nombre_comun, variantes
            FROM indec_provincias
        """)

        for codigo, nombre_oficial, nombre_comun, variantes_json in cursor.fetchall():
            variantes = json.loads(variantes_json) if variantes_json else []

            self.provincias_cache[codigo] = {
                "codigo": codigo,
                "nombre_oficial": nombre_oficial,
                "nombre_comun": nombre_comun,
                "variantes": variantes,
                "nombres_normalizados": [
                    normalize_string(nombre_oficial),
                    normalize_string(nombre_comun)
                ] + [normalize_string(v) for v in variantes]
            }

        conn.close()
        print(f"[OK] Cargadas {len(self.provincias_cache)} provincias INDEC en memoria")

    def match_provincia(self, provincia_raw: str, fuzzy_threshold: float = 85.0) -> Optional[Dict]:
        """
        Intenta matchear una provincia raw contra INDEC

        Estrategia:
        1. Matching exacto contra nombre_comun
        2. Matching exacto contra variantes
        3. Fuzzy matching (threshold 85%)

        Returns:
            Dict con codigo, nombre_comun o None si no match
        """
        if not provincia_raw:
            return None

        provincia_norm = normalize_string(provincia_raw)

        # 1. Matching exacto
        for codigo, data in self.provincias_cache.items():
            if provincia_norm in data["nombres_normalizados"]:
                return {
                    "codigo": codigo,
                    "nombre_comun": data["nombre_comun"],
                    "match_type": "exact"
                }

        # 2. Fuzzy matching
        best_match = None
        best_score = 0.0

        for codigo, data in self.provincias_cache.items():
            for nombre_normalizado in data["nombres_normalizados"]:
                score = similarity_score(provincia_norm, nombre_normalizado)
                if score > best_score:
                    best_score = score
                    best_match = {
                        "codigo": codigo,
                        "nombre_comun": data["nombre_comun"],
                        "match_type": "fuzzy",
                        "similarity": score
                    }

        if best_score >= fuzzy_threshold:
            return best_match

        return None

    def parse_localizacion(self, localizacion: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parsea campo localizacion en formato "Localidad, Provincia"

        Returns:
            (localidad_raw, provincia_raw)
        """
        if not localizacion:
            return None, None

        # Split por coma
        parts = localizacion.split(',')

        if len(parts) >= 2:
            localidad_raw = parts[0].strip()
            provincia_raw = parts[1].strip()
            return localidad_raw, provincia_raw
        elif len(parts) == 1:
            # Solo provincia (caso raro)
            return None, parts[0].strip()
        else:
            return None, None


def add_normalized_columns(cursor):
    """Agrega columnas normalizadas a tabla ofertas si no existen"""

    # Verificar si ya existen
    cursor.execute("PRAGMA table_info(ofertas)")
    columns = [row[1] for row in cursor.fetchall()]

    columns_to_add = [
        ("provincia_normalizada", "TEXT"),
        ("codigo_provincia_indec", "TEXT"),
        ("localidad_normalizada", "TEXT"),
        ("codigo_localidad_indec", "TEXT")
    ]

    added = 0
    for col_name, col_type in columns_to_add:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE ofertas ADD COLUMN {col_name} {col_type}")
            added += 1
            print(f"  [+] Columna agregada: {col_name}")

    if added == 0:
        print(f"  [OK] Columnas ya existían")
    else:
        print(f"  [OK] {added} columnas agregadas")


def normalize_all_ofertas(db_path: str):
    """Normaliza todas las ofertas en la BD"""

    print("=" * 70)
    print("NORMALIZACION DE UBICACIONES")
    print("=" * 70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Paso 1: Agregar columnas
        print("PASO 1: Agregar columnas normalizadas")
        add_normalized_columns(cursor)
        conn.commit()

        # Paso 2: Inicializar normalizador
        print("\nPASO 2: Cargar provincias INDEC")
        normalizer = UbicacionNormalizer(db_path)

        # Paso 3: Obtener ofertas a normalizar
        print("\nPASO 3: Normalizar ofertas")
        cursor.execute("""
            SELECT id_oferta, localizacion
            FROM ofertas
            WHERE localizacion IS NOT NULL
        """)

        ofertas = cursor.fetchall()
        total_ofertas = len(ofertas)
        print(f"  Total ofertas a procesar: {total_ofertas}")

        # Estadísticas
        stats = {
            "total": total_ofertas,
            "provincia_normalizada": 0,
            "provincia_no_match": 0,
            "localidad_parseada": 0,
            "match_exacto": 0,
            "match_fuzzy": 0
        }

        no_match_provincias = set()

        # Procesar cada oferta
        for i, (id_oferta, localizacion) in enumerate(ofertas, 1):
            if i % 1000 == 0:
                print(f"  Procesadas: {i}/{total_ofertas} ({(i/total_ofertas)*100:.1f}%)")

            # Parsear
            localidad_raw, provincia_raw = normalizer.parse_localizacion(localizacion)

            if localidad_raw:
                stats["localidad_parseada"] += 1

            # Matchear provincia
            if provincia_raw:
                match = normalizer.match_provincia(provincia_raw)

                if match:
                    stats["provincia_normalizada"] += 1

                    if match["match_type"] == "exact":
                        stats["match_exacto"] += 1
                    else:
                        stats["match_fuzzy"] += 1

                    # Actualizar BD
                    cursor.execute("""
                        UPDATE ofertas
                        SET provincia_normalizada = ?,
                            codigo_provincia_indec = ?,
                            localidad_normalizada = ?
                        WHERE id_oferta = ?
                    """, (
                        match["nombre_comun"],
                        match["codigo"],
                        localidad_raw,  # Por ahora guardamos raw, sin normalizar localidades
                        id_oferta
                    ))
                else:
                    stats["provincia_no_match"] += 1
                    no_match_provincias.add(provincia_raw)

        # Commit final
        conn.commit()

        # Reporte
        print("\n" + "=" * 70)
        print("REPORTE FINAL")
        print("=" * 70)

        print(f"\n1. ESTADISTICAS GENERALES:")
        print(f"   Total ofertas procesadas: {stats['total']}")
        print(f"   Localidades parseadas: {stats['localidad_parseada']} ({(stats['localidad_parseada']/stats['total'])*100:.1f}%)")

        print(f"\n2. NORMALIZACION DE PROVINCIAS:")
        print(f"   Provincias normalizadas: {stats['provincia_normalizada']} ({(stats['provincia_normalizada']/stats['total'])*100:.1f}%)")
        print(f"   - Matching exacto: {stats['match_exacto']}")
        print(f"   - Matching fuzzy: {stats['match_fuzzy']}")
        print(f"   No match: {stats['provincia_no_match']} ({(stats['provincia_no_match']/stats['total'])*100:.1f}%)")

        if no_match_provincias:
            print(f"\n3. PROVINCIAS SIN MATCH ({len(no_match_provincias)} únicas):")
            for provincia in sorted(no_match_provincias):
                print(f"   - {provincia}")

        # Validación
        print(f"\n4. VALIDACION:")
        cursor.execute("""
            SELECT COUNT(DISTINCT codigo_provincia_indec)
            FROM ofertas
            WHERE codigo_provincia_indec IS NOT NULL
        """)
        provincias_distintas = cursor.fetchone()[0]
        print(f"   Provincias distintas encontradas: {provincias_distintas}/24")

        cursor.execute("""
            SELECT codigo_provincia_indec, COUNT(*) as total
            FROM ofertas
            WHERE codigo_provincia_indec IS NOT NULL
            GROUP BY codigo_provincia_indec
            ORDER BY total DESC
            LIMIT 10
        """)

        print(f"\n   Top 10 provincias normalizadas:")
        for codigo, total in cursor.fetchall():
            # Obtener nombre
            cursor.execute("""
                SELECT nombre_comun
                FROM indec_provincias
                WHERE codigo_provincia = ?
            """, (codigo,))
            nombre = cursor.fetchone()[0]
            print(f"     {codigo} - {nombre:30} {total:5} ofertas")

        print("\n" + "=" * 70)
        print("NORMALIZACION COMPLETADA")
        print("=" * 70)

        # Objetivo: >80% provincias normalizadas
        cobertura_pct = (stats['provincia_normalizada']/stats['total'])*100
        objetivo_cumplido = cobertura_pct >= 80.0

        print(f"\nOBJETIVO: >80% provincias normalizadas")
        print(f"Resultado: {cobertura_pct:.1f}% - {'[OK] CUMPLIDO' if objetivo_cumplido else '[X] NO CUMPLIDO'}")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {str(e)}")
        raise

    finally:
        conn.close()


def main():
    """Ejecuta la normalización"""
    db_path = Path(__file__).parent / "bumeran_scraping.db"

    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return

    normalize_all_ofertas(str(db_path))


if __name__ == "__main__":
    main()
