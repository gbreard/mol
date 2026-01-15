#!/usr/bin/env python3
"""
Wrapper de Generación Segura de CSV para Shiny
==============================================

Este script envuelve la generación del CSV agregando una capa de validación
de calidad de datos ANTES de generar el archivo.

Flujo:
1. Ejecuta validación de calidad (validate_shiny_data_quality.py)
2. Analiza resultados y decide si continuar
3. Si OK o warnings: genera CSV (generar_csv_shiny_desde_db.py)
4. Si errores críticos: aborta y alerta

Uso:
    python generar_csv_shiny_validado.py
    python generar_csv_shiny_validado.py --nivel critico
    python generar_csv_shiny_validado.py --force
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import argparse


def imprimir_header():
    """Imprime el header del script"""
    print("=" * 70)
    print("GENERACIÓN VALIDADA DE CSV PARA DASHBOARD SHINY")
    print("=" * 70)
    print()
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def ejecutar_validacion(nivel: str = None):
    """
    Ejecuta el script de validación de datos

    Args:
        nivel: Nivel de validación ('critico', 'importante', 'advertencia', o None para todos)

    Returns:
        Tupla (exit_code, nivel_fallo)
    """
    print("[PASO 1/3] VALIDACIÓN DE CALIDAD DE DATOS")
    print("-" * 70)
    print()

    cmd = [sys.executable, "validate_shiny_data_quality.py"]
    if nivel:
        cmd.extend(["--nivel", nivel])

    print(f"Ejecutando: {' '.join(cmd)}")
    print()

    # Ejecutar validación
    result = subprocess.run(cmd, capture_output=False)

    print()
    print("-" * 70)
    print(f"Validación completada con código de salida: {result.returncode}")
    print()

    # Mapear exit code a nivel de fallo
    nivel_fallo = {
        0: "NINGUNO",
        1: "IMPORTANTE",
        2: "CRÍTICO",
        3: "EXCEPCIÓN"
    }.get(result.returncode, "DESCONOCIDO")

    return result.returncode, nivel_fallo


def decidir_continuar(exit_code: int, nivel_fallo: str, force: bool = False):
    """
    Decide si continuar con la generación del CSV basándose en los resultados de validación

    Args:
        exit_code: Código de salida del validador
        nivel_fallo: Nivel de fallo detectado
        force: Si True, genera CSV incluso con errores críticos

    Returns:
        bool: True si debe continuar, False si debe abortar
    """
    print("[PASO 2/3] ANÁLISIS DE RESULTADOS")
    print("-" * 70)
    print()

    if exit_code == 0:
        print("✅ VALIDACIÓN EXITOSA")
        print("   Todos los checks pasaron. Procediendo a generar CSV.")
        print()
        return True

    elif exit_code == 1:
        print("⚠️  ADVERTENCIAS DETECTADAS")
        print(f"   Nivel de fallo: {nivel_fallo}")
        print("   Algunos datos no cumplen umbrales IMPORTANTES")
        print("   Ejemplo: Skills ESCO pueden estar vacíos")
        print()
        print("   DECISIÓN: Generar CSV de todos modos")
        print("   (El dashboard funcionará parcialmente)")
        print()
        return True

    elif exit_code == 2:
        print("❌ ERRORES CRÍTICOS DETECTADOS")
        print(f"   Nivel de fallo: {nivel_fallo}")
        print("   Datos esenciales no cumplen umbrales mínimos")
        print("   Ejemplo: Menos del 95% de ofertas tienen ocupación ESCO")
        print()

        if force:
            print("   ⚠️  FLAG --force ACTIVADO")
            print("   DECISIÓN: Generar CSV a pesar de los errores")
            print()
            return True
        else:
            print("   DECISIÓN: ABORTAR generación de CSV")
            print("   Para generar de todos modos, usa el flag --force")
            print()
            return False

    elif exit_code == 3:
        print("💥 EXCEPCIÓN EN VALIDACIÓN")
        print("   El script de validación encontró un error inesperado")
        print()

        if force:
            print("   ⚠️  FLAG --force ACTIVADO")
            print("   DECISIÓN: Generar CSV a pesar de la excepción")
            print()
            return True
        else:
            print("   DECISIÓN: ABORTAR generación de CSV")
            print("   Revisa los logs de validación para más detalles")
            print()
            return False

    else:
        print(f"⁉️  CÓDIGO DE SALIDA DESCONOCIDO: {exit_code}")
        print("   No se puede determinar el estado de los datos")
        print()

        if force:
            print("   ⚠️  FLAG --force ACTIVADO")
            print("   DECISIÓN: Generar CSV de todos modos")
            print()
            return True
        else:
            print("   DECISIÓN: ABORTAR por seguridad")
            print()
            return False


def generar_csv():
    """
    Ejecuta el script de generación de CSV

    Returns:
        int: Código de salida del generador de CSV
    """
    print("[PASO 3/3] GENERACIÓN DE CSV")
    print("-" * 70)
    print()

    cmd = [sys.executable, "generar_csv_shiny_desde_db.py"]

    print(f"Ejecutando: {' '.join(cmd)}")
    print()

    # Ejecutar generación de CSV
    result = subprocess.run(cmd, capture_output=False)

    print()
    print("-" * 70)
    print(f"Generación completada con código de salida: {result.returncode}")
    print()

    return result.returncode


def verificar_csv_generado():
    """
    Verifica que el CSV fue generado correctamente

    Returns:
        bool: True si el CSV existe, False si no
    """
    csv_path = Path(__file__).parent.parent / "Visual--" / "ofertas_esco_shiny.csv"

    if csv_path.exists():
        size_mb = csv_path.stat().st_size / (1024 * 1024)
        print(f"✅ CSV generado exitosamente")
        print(f"   Ubicación: {csv_path}")
        print(f"   Tamaño: {size_mb:.2f} MB")
        print()
        return True
    else:
        print(f"❌ CSV no encontrado en ruta esperada")
        print(f"   Ruta buscada: {csv_path}")
        print()
        return False


def imprimir_resumen(exit_code_validacion: int, exit_code_csv: int, csv_existe: bool):
    """Imprime el resumen final de la ejecución"""
    print()
    print("=" * 70)
    print("RESUMEN DE EJECUCIÓN")
    print("=" * 70)
    print()
    print(f"1. Validación: Exit code {exit_code_validacion}")

    if exit_code_csv is not None:
        print(f"2. Generación CSV: Exit code {exit_code_csv}")
        print(f"3. Archivo CSV: {'✅ Existe' if csv_existe else '❌ No encontrado'}")
    else:
        print(f"2. Generación CSV: ⏭️  Omitida (validación falló)")

    print()

    # Determinar resultado final
    if exit_code_csv == 0 and csv_existe:
        print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print()
        print("Próximos pasos:")
        print("  1. Reiniciar dashboard Shiny (si está corriendo)")
        print("  2. Verificar que todas las secciones muestran datos")
        print()
        return 0
    elif exit_code_csv is None:
        print("⚠️  PROCESO ABORTADO")
        print()
        print("El CSV NO fue generado debido a problemas de validación.")
        print()
        print("Acciones recomendadas:")
        print("  1. Revisar los errores reportados en la validación")
        print("  2. Corregir los datos en la base de datos")
        print("  3. Volver a ejecutar este script")
        print("  4. O usar --force para generar CSV de todos modos")
        print()
        return 1
    elif not csv_existe:
        print("❌ ERROR EN GENERACIÓN DE CSV")
        print()
        print("El proceso de generación falló o no produjo el archivo esperado.")
        print()
        print("Acciones recomendadas:")
        print("  1. Revisar logs del generador de CSV")
        print("  2. Verificar permisos de escritura en directorio Visual--")
        print("  3. Verificar espacio en disco")
        print()
        return 2
    else:
        print("⚠️  PROCESO COMPLETADO CON ADVERTENCIAS")
        print()
        print("El CSV fue generado pero pueden existir problemas de calidad.")
        print()
        return 0


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Genera CSV para Shiny con validación previa de calidad de datos"
    )
    parser.add_argument(
        "--nivel",
        choices=["critico", "importante", "advertencia"],
        help="Nivel de validación a ejecutar (por defecto: todos)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la generación del CSV incluso si hay errores críticos"
    )

    args = parser.parse_args()

    # Header
    imprimir_header()

    # Paso 1: Validación
    exit_code_validacion, nivel_fallo = ejecutar_validacion(args.nivel)

    # Paso 2: Decisión
    continuar = decidir_continuar(exit_code_validacion, nivel_fallo, args.force)

    exit_code_csv = None
    csv_existe = False

    if continuar:
        # Paso 3: Generación de CSV
        exit_code_csv = generar_csv()

        # Verificación
        csv_existe = verificar_csv_generado()

    # Resumen
    result = imprimir_resumen(exit_code_validacion, exit_code_csv, csv_existe)

    sys.exit(result)


if __name__ == '__main__':
    main()
