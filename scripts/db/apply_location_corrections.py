#!/usr/bin/env python3
"""
Script para aplicar correcciones manuales de ubicaciones
=========================================================

Lee el CSV con correcciones manuales y aplica los cambios
a la base de datos de forma masiva.

Proceso:
1. Leer CSV con correcciones
2. Identificar ubicaciones corregidas
3. Aplicar UPDATE masivo para todas las ofertas con la misma ubicación
4. Reportar resultados

Uso:
    python apply_location_corrections.py
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class LocationCorrector:
    """Aplicador de correcciones de ubicaciones"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.corrections: List[Dict] = []
        self.stats = {
            "total_rows_csv": 0,
            "corrections_found": 0,
            "ubicaciones_corregidas": 0,
            "ofertas_afectadas": 0,
            "errors": 0
        }

    def load_corrections_from_csv(self, csv_path: str):
        """
        Carga correcciones desde CSV

        Solo considera filas donde al menos uno de los campos CORRECTA
        tiene valor diferente al actual.
        """
        print("PASO 1: Cargar correcciones desde CSV")
        print(f"  Archivo: {csv_path}")

        if not Path(csv_path).exists():
            raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.stats["total_rows_csv"] += 1

                # Verificar si hay correcciones
                has_correction = False

                provincia_correcta = row.get("provincia_normalizada_CORRECTA", "").strip()
                codigo_correcto = row.get("codigo_provincia_CORRECTO", "").strip()
                localidad_correcta = row.get("localidad_normalizada_CORRECTA", "").strip()

                # Comparar con valores actuales
                if provincia_correcta and provincia_correcta != row.get("provincia_normalizada_actual", "").strip():
                    has_correction = True
                if codigo_correcto and codigo_correcto != row.get("codigo_provincia_actual", "").strip():
                    has_correction = True
                if localidad_correcta and localidad_correcta != row.get("localidad_normalizada_actual", "").strip():
                    has_correction = True

                if has_correction:
                    self.corrections.append({
                        "ubicacion_original": row.get("ubicacion_original", "").strip(),
                        "provincia_normalizada_actual": row.get("provincia_normalizada_actual", "").strip(),
                        "codigo_provincia_actual": row.get("codigo_provincia_actual", "").strip(),
                        "localidad_normalizada_actual": row.get("localidad_normalizada_actual", "").strip(),
                        "provincia_normalizada_CORRECTA": provincia_correcta or None,
                        "codigo_provincia_CORRECTO": codigo_correcto or None,
                        "localidad_normalizada_CORRECTA": localidad_correcta or None,
                        "comentarios": row.get("comentarios", "").strip(),
                        "cantidad_ofertas": int(row.get("cantidad_ofertas", 0))
                    })
                    self.stats["corrections_found"] += 1

        print(f"  [OK] {self.stats['total_rows_csv']} filas leídas del CSV")
        print(f"  [OK] {self.stats['corrections_found']} ubicaciones con correcciones\n")

        if self.stats["corrections_found"] == 0:
            print("  [INFO] No se encontraron correcciones para aplicar")
            print("  [INFO] Verifica que completaste las columnas *_CORRECTA en el CSV\n")

    def apply_corrections_to_db(self):
        """
        Aplica correcciones a la base de datos

        Para cada ubicación corregida, actualiza TODAS las ofertas
        con esa ubicación original.
        """
        if not self.corrections:
            print("PASO 2: No hay correcciones para aplicar\n")
            return

        print("PASO 2: Aplicar correcciones a la base de datos")
        print(f"  Total correcciones: {len(self.corrections)}\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for i, correction in enumerate(self.corrections, 1):
                ubicacion_original = correction["ubicacion_original"]

                # Preparar valores a actualizar (solo los que tienen corrección)
                updates = []
                params = []

                if correction["provincia_normalizada_CORRECTA"]:
                    updates.append("provincia_normalizada = ?")
                    params.append(correction["provincia_normalizada_CORRECTA"])

                if correction["codigo_provincia_CORRECTO"]:
                    updates.append("codigo_provincia_indec = ?")
                    params.append(correction["codigo_provincia_CORRECTO"])

                if correction["localidad_normalizada_CORRECTA"]:
                    updates.append("localidad_normalizada = ?")
                    params.append(correction["localidad_normalizada_CORRECTA"])

                if not updates:
                    continue

                # Construir query UPDATE
                update_sql = f"""
                    UPDATE ofertas
                    SET {", ".join(updates)}
                    WHERE localizacion = ?
                """
                params.append(ubicacion_original)

                # Contar ofertas que se van a actualizar
                cursor.execute("""
                    SELECT COUNT(*) FROM ofertas
                    WHERE localizacion = ?
                """, (ubicacion_original,))

                ofertas_count = cursor.fetchone()[0]

                if ofertas_count == 0:
                    print(f"  [{i}/{len(self.corrections)}] ADVERTENCIA: '{ubicacion_original}' - 0 ofertas encontradas")
                    self.stats["errors"] += 1
                    continue

                # Aplicar UPDATE
                cursor.execute(update_sql, params)

                self.stats["ubicaciones_corregidas"] += 1
                self.stats["ofertas_afectadas"] += ofertas_count

                # Mostrar progreso
                cambios = []
                if correction["provincia_normalizada_CORRECTA"]:
                    cambios.append(f"prov={correction['provincia_normalizada_CORRECTA']}")
                if correction["codigo_provincia_CORRECTO"]:
                    cambios.append(f"cod={correction['codigo_provincia_CORRECTO']}")
                if correction["localidad_normalizada_CORRECTA"]:
                    cambios.append(f"loc={correction['localidad_normalizada_CORRECTA']}")

                print(f"  [{i}/{len(self.corrections)}] '{ubicacion_original}' -> {', '.join(cambios)} ({ofertas_count} ofertas)")

            # Commit
            conn.commit()
            print(f"\n  [OK] Correcciones aplicadas y guardadas en BD\n")

        except Exception as e:
            conn.rollback()
            print(f"\n  [ERROR] Rollback ejecutado: {str(e)}\n")
            raise

        finally:
            conn.close()

    def validate_results(self):
        """
        Valida que las correcciones se aplicaron correctamente
        """
        print("PASO 3: Validar resultados")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verificar algunas correcciones aplicadas
            print("  Verificando muestra de correcciones aplicadas:\n")

            for i, correction in enumerate(self.corrections[:5], 1):  # Mostrar solo primeras 5
                ubicacion_original = correction["ubicacion_original"]

                cursor.execute("""
                    SELECT provincia_normalizada, codigo_provincia_indec, localidad_normalizada
                    FROM ofertas
                    WHERE localizacion = ?
                    LIMIT 1
                """, (ubicacion_original,))

                result = cursor.fetchone()

                if result:
                    prov_actual, cod_actual, loc_actual = result
                    print(f"  [{i}] '{ubicacion_original}':")
                    print(f"      Provincia: {prov_actual}")
                    print(f"      Código: {cod_actual}")
                    print(f"      Localidad: {loc_actual}\n")
                else:
                    print(f"  [{i}] '{ubicacion_original}': NO ENCONTRADA\n")

            # Estadísticas globales post-corrección
            cursor.execute("""
                SELECT COUNT(*) FROM ofertas
                WHERE provincia_normalizada IS NOT NULL
            """)
            ofertas_normalizadas = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ofertas")
            ofertas_totales = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(DISTINCT codigo_provincia_indec)
                FROM ofertas
                WHERE codigo_provincia_indec IS NOT NULL
            """)
            provincias_distintas = cursor.fetchone()[0]

            print("  [OK] Estadísticas globales post-corrección:")
            print(f"      Ofertas normalizadas: {ofertas_normalizadas}/{ofertas_totales} ({(ofertas_normalizadas/ofertas_totales)*100:.1f}%)")
            print(f"      Provincias distintas: {provincias_distintas}/24\n")

        finally:
            conn.close()

    def print_report(self):
        """Imprime reporte final"""
        print("=" * 70)
        print("REPORTE FINAL - CORRECCIONES APLICADAS")
        print("=" * 70)
        print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        print("RESUMEN:")
        print(f"  Filas leídas del CSV: {self.stats['total_rows_csv']}")
        print(f"  Correcciones encontradas: {self.stats['corrections_found']}")
        print(f"  Ubicaciones corregidas: {self.stats['ubicaciones_corregidas']}")
        print(f"  Ofertas afectadas: {self.stats['ofertas_afectadas']}")
        print(f"  Errores: {self.stats['errors']}\n")

        if self.stats['corrections_found'] > 0:
            print("IMPACTO:")
            print(f"  Promedio ofertas por ubicación corregida: {self.stats['ofertas_afectadas'] / self.stats['ubicaciones_corregidas']:.1f}\n")

        print("=" * 70)
        print("PROCESO COMPLETADO")
        print("=" * 70)


def main():
    """Ejecuta el proceso de aplicación de correcciones"""

    print("=" * 70)
    print("APLICACION DE CORRECCIONES DE UBICACIONES")
    print("=" * 70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Rutas
    db_path = Path(__file__).parent / "bumeran_scraping.db"
    csv_path = Path(__file__).parent / "ubicaciones_ambiguas_validacion.csv"

    # Validar archivos
    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return

    if not csv_path.exists():
        print(f"ERROR: CSV de correcciones no encontrado en {csv_path}")
        print("\nPRIMERO debes:")
        print("1. Ejecutar: python export_ambiguous_locations.py")
        print("2. Abrir el CSV en Excel")
        print("3. Completar columnas *_CORRECTA para ubicaciones incorrectas")
        print("4. Guardar el CSV")
        print("5. Ejecutar este script\n")
        return

    # Inicializar corrector
    corrector = LocationCorrector(str(db_path))

    try:
        # Paso 1: Cargar correcciones
        corrector.load_corrections_from_csv(str(csv_path))

        # Paso 2: Aplicar correcciones
        corrector.apply_corrections_to_db()

        # Paso 3: Validar
        corrector.validate_results()

        # Reporte final
        corrector.print_report()

        # Próximos pasos
        if corrector.stats['corrections_found'] > 0:
            print("\nPROXIMOS PASOS:")
            print("1. Revisar el reporte de correcciones aplicadas")
            print("2. Validar que las correcciones son correctas (queries SQL)")
            print("3. Hacer commit de los cambios a git")
            print("4. Continuar con TAREA 2: Testing extendido NLP v6.0\n")
        else:
            print("\nNOTA:")
            print("No se aplicaron correcciones porque el CSV no tiene valores")
            print("en las columnas *_CORRECTA.")
            print("\nSi NO necesitas hacer correcciones:")
            print("  -> TAREA 3 está completa, continuar con TAREA 2\n")

    except Exception as e:
        print(f"\nERROR FATAL: {str(e)}")
        raise


if __name__ == "__main__":
    main()
