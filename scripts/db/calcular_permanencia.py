#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
calcular_permanencia.py
=======================
Calcula y analiza la permanencia de ofertas laborales.

Permanencia = días que una oferta estuvo publicada
Categorías:
  - baja: <7 días (ofertas que se llenan rápido o temporales)
  - media: 7-30 días (normal)
  - alta: >30 días (difíciles de cubrir o estructurales)

Métricas adicionales:
  - Permanencia por sector/área
  - Permanencia por empresa
  - Permanencia por modalidad de trabajo
  - Tendencias temporales

Uso:
    python calcular_permanencia.py
    python calcular_permanencia.py --exportar
    python calcular_permanencia.py --detalle empresa
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import argparse
import json

DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'


class AnalizadorPermanencia:
    """Analiza la permanencia de ofertas laborales"""

    # Categorías de permanencia (en días)
    CATEGORIAS = {
        'baja': (0, 7),        # <7 días
        'media': (7, 30),      # 7-30 días
        'alta': (30, 365),     # >30 días
    }

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def calcular_permanencia_ofertas_baja(self) -> int:
        """
        Calcula días de permanencia para ofertas dadas de baja.

        Returns:
            Número de ofertas procesadas
        """
        cursor = self.conn.cursor()

        # Actualizar dias_publicada para ofertas con baja
        cursor.execute("""
            UPDATE ofertas
            SET dias_publicada = CAST(
                julianday(COALESCE(fecha_baja, 'now')) -
                julianday(fecha_publicacion_iso) AS INTEGER
            )
            WHERE fecha_publicacion_iso IS NOT NULL
              AND estado_oferta = 'baja'
              AND (dias_publicada IS NULL OR dias_publicada < 0)
        """)

        actualizadas = cursor.rowcount
        self.conn.commit()

        return actualizadas

    def calcular_permanencia_ofertas_activas(self) -> int:
        """
        Calcula días de permanencia actual para ofertas todavía activas.

        Returns:
            Número de ofertas procesadas
        """
        cursor = self.conn.cursor()

        # Para ofertas activas, calcular días desde publicación hasta hoy
        cursor.execute("""
            UPDATE ofertas
            SET dias_publicada = CAST(
                julianday('now') - julianday(fecha_publicacion_iso) AS INTEGER
            )
            WHERE fecha_publicacion_iso IS NOT NULL
              AND estado_oferta = 'activa'
        """)

        actualizadas = cursor.rowcount
        self.conn.commit()

        return actualizadas

    def categorizar_permanencia(self) -> int:
        """
        Asigna categoría de permanencia basada en días.

        Returns:
            Número de ofertas categorizadas
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE ofertas
            SET categoria_permanencia = CASE
                WHEN dias_publicada < 7 THEN 'baja'
                WHEN dias_publicada < 30 THEN 'media'
                WHEN dias_publicada >= 30 THEN 'alta'
                ELSE NULL
            END
            WHERE dias_publicada IS NOT NULL
        """)

        actualizadas = cursor.rowcount
        self.conn.commit()

        return actualizadas

    def obtener_estadisticas_generales(self) -> Dict:
        """
        Obtiene estadísticas generales de permanencia.

        Returns:
            Dict con estadísticas
        """
        cursor = self.conn.cursor()

        stats = {}

        # Total de ofertas
        cursor.execute("SELECT COUNT(*) FROM ofertas")
        stats['total_ofertas'] = cursor.fetchone()[0]

        # Por estado
        cursor.execute("""
            SELECT estado_oferta, COUNT(*)
            FROM ofertas
            GROUP BY estado_oferta
        """)
        stats['por_estado'] = {row[0] or 'NULL': row[1] for row in cursor.fetchall()}

        # Por categoría de permanencia
        cursor.execute("""
            SELECT categoria_permanencia, COUNT(*), AVG(dias_publicada),
                   MIN(dias_publicada), MAX(dias_publicada)
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
            GROUP BY categoria_permanencia
            ORDER BY categoria_permanencia
        """)
        stats['por_categoria'] = {}
        for row in cursor.fetchall():
            cat = row[0] or 'sin_categoria'
            stats['por_categoria'][cat] = {
                'cantidad': row[1],
                'promedio_dias': round(row[2], 1) if row[2] else None,
                'min_dias': row[3],
                'max_dias': row[4]
            }

        # Estadísticas globales de permanencia
        cursor.execute("""
            SELECT
                AVG(dias_publicada) as promedio,
                MIN(dias_publicada) as minimo,
                MAX(dias_publicada) as maximo,
                COUNT(*) as con_datos
            FROM ofertas
            WHERE dias_publicada IS NOT NULL AND dias_publicada > 0
        """)
        row = cursor.fetchone()
        stats['permanencia_global'] = {
            'promedio_dias': round(row[0], 1) if row[0] else None,
            'minimo_dias': row[1],
            'maximo_dias': row[2],
            'ofertas_con_datos': row[3]
        }

        # Distribución por semana
        cursor.execute("""
            SELECT
                CASE
                    WHEN dias_publicada < 7 THEN '1. <1 semana'
                    WHEN dias_publicada < 14 THEN '2. 1-2 semanas'
                    WHEN dias_publicada < 21 THEN '3. 2-3 semanas'
                    WHEN dias_publicada < 28 THEN '4. 3-4 semanas'
                    WHEN dias_publicada < 60 THEN '5. 1-2 meses'
                    ELSE '6. >2 meses'
                END as rango,
                COUNT(*) as cantidad
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
            GROUP BY rango
            ORDER BY rango
        """)
        stats['distribucion_rangos'] = {row[0]: row[1] for row in cursor.fetchall()}

        return stats

    def obtener_permanencia_por_area(self) -> pd.DataFrame:
        """
        Obtiene permanencia promedio por área/subárea.

        Returns:
            DataFrame con permanencia por área
        """
        query = """
            SELECT
                id_area,
                id_subarea,
                COUNT(*) as cantidad,
                AVG(dias_publicada) as promedio_dias,
                SUM(CASE WHEN categoria_permanencia = 'baja' THEN 1 ELSE 0 END) as perm_baja,
                SUM(CASE WHEN categoria_permanencia = 'media' THEN 1 ELSE 0 END) as perm_media,
                SUM(CASE WHEN categoria_permanencia = 'alta' THEN 1 ELSE 0 END) as perm_alta
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
            GROUP BY id_area, id_subarea
            HAVING COUNT(*) >= 10
            ORDER BY promedio_dias DESC
        """

        return pd.read_sql_query(query, self.conn)

    def obtener_permanencia_por_empresa(self, min_ofertas: int = 5) -> pd.DataFrame:
        """
        Obtiene permanencia promedio por empresa.

        Args:
            min_ofertas: Mínimo de ofertas para incluir empresa

        Returns:
            DataFrame con permanencia por empresa
        """
        query = """
            SELECT
                empresa,
                COUNT(*) as cantidad,
                AVG(dias_publicada) as promedio_dias,
                SUM(CASE WHEN estado_oferta = 'activa' THEN 1 ELSE 0 END) as activas,
                SUM(CASE WHEN estado_oferta = 'baja' THEN 1 ELSE 0 END) as bajas
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
              AND empresa IS NOT NULL
            GROUP BY empresa
            HAVING COUNT(*) >= ?
            ORDER BY promedio_dias DESC
        """

        return pd.read_sql_query(query, self.conn, params=(min_ofertas,))

    def obtener_permanencia_por_modalidad(self) -> pd.DataFrame:
        """
        Obtiene permanencia por modalidad de trabajo.

        Returns:
            DataFrame con permanencia por modalidad
        """
        query = """
            SELECT
                modalidad_trabajo,
                tipo_trabajo,
                COUNT(*) as cantidad,
                AVG(dias_publicada) as promedio_dias,
                SUM(CASE WHEN categoria_permanencia = 'baja' THEN 1 ELSE 0 END) as perm_baja,
                SUM(CASE WHEN categoria_permanencia = 'media' THEN 1 ELSE 0 END) as perm_media,
                SUM(CASE WHEN categoria_permanencia = 'alta' THEN 1 ELSE 0 END) as perm_alta
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
            GROUP BY modalidad_trabajo, tipo_trabajo
            ORDER BY cantidad DESC
        """

        return pd.read_sql_query(query, self.conn)

    def obtener_permanencia_por_provincia(self) -> pd.DataFrame:
        """
        Obtiene permanencia por provincia.

        Returns:
            DataFrame con permanencia por provincia
        """
        query = """
            SELECT
                provincia_normalizada,
                COUNT(*) as cantidad,
                AVG(dias_publicada) as promedio_dias,
                SUM(CASE WHEN estado_oferta = 'activa' THEN 1 ELSE 0 END) as activas,
                SUM(CASE WHEN estado_oferta = 'baja' THEN 1 ELSE 0 END) as bajas
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
              AND provincia_normalizada IS NOT NULL
            GROUP BY provincia_normalizada
            ORDER BY cantidad DESC
        """

        return pd.read_sql_query(query, self.conn)

    def obtener_ofertas_extremas(self, tipo: str = 'alta', limite: int = 20) -> pd.DataFrame:
        """
        Obtiene ofertas con permanencia extrema (muy alta o muy baja).

        Args:
            tipo: 'alta' para ofertas más duraderas, 'baja' para las más cortas
            limite: Cantidad de ofertas a retornar

        Returns:
            DataFrame con ofertas extremas
        """
        orden = "DESC" if tipo == 'alta' else "ASC"

        query = f"""
            SELECT
                id_oferta,
                titulo,
                empresa,
                modalidad_trabajo,
                provincia_normalizada,
                fecha_publicacion_iso,
                fecha_baja,
                dias_publicada,
                estado_oferta
            FROM ofertas
            WHERE dias_publicada IS NOT NULL
              AND dias_publicada > 0
            ORDER BY dias_publicada {orden}
            LIMIT ?
        """

        return pd.read_sql_query(query, self.conn, params=(limite,))

    def exportar_reporte_completo(self, output_dir: Path = None) -> Dict[str, str]:
        """
        Exporta reporte completo de permanencia.

        Args:
            output_dir: Directorio de salida

        Returns:
            Dict con rutas de archivos generados
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / 'data' / 'reports'

        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivos = {}

        # Estadísticas generales (JSON)
        stats = self.obtener_estadisticas_generales()
        stats_file = output_dir / f'permanencia_stats_{timestamp}.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        archivos['estadisticas'] = str(stats_file)

        # Por área (CSV)
        df_area = self.obtener_permanencia_por_area()
        area_file = output_dir / f'permanencia_por_area_{timestamp}.csv'
        df_area.to_csv(area_file, index=False, encoding='utf-8-sig')
        archivos['por_area'] = str(area_file)

        # Por empresa (CSV)
        df_empresa = self.obtener_permanencia_por_empresa()
        empresa_file = output_dir / f'permanencia_por_empresa_{timestamp}.csv'
        df_empresa.to_csv(empresa_file, index=False, encoding='utf-8-sig')
        archivos['por_empresa'] = str(empresa_file)

        # Por modalidad (CSV)
        df_modalidad = self.obtener_permanencia_por_modalidad()
        modalidad_file = output_dir / f'permanencia_por_modalidad_{timestamp}.csv'
        df_modalidad.to_csv(modalidad_file, index=False, encoding='utf-8-sig')
        archivos['por_modalidad'] = str(modalidad_file)

        # Por provincia (CSV)
        df_provincia = self.obtener_permanencia_por_provincia()
        provincia_file = output_dir / f'permanencia_por_provincia_{timestamp}.csv'
        df_provincia.to_csv(provincia_file, index=False, encoding='utf-8-sig')
        archivos['por_provincia'] = str(provincia_file)

        # Ofertas extremas (CSV)
        df_alta = self.obtener_ofertas_extremas('alta', 50)
        alta_file = output_dir / f'ofertas_permanencia_alta_{timestamp}.csv'
        df_alta.to_csv(alta_file, index=False, encoding='utf-8-sig')
        archivos['permanencia_alta'] = str(alta_file)

        df_baja = self.obtener_ofertas_extremas('baja', 50)
        baja_file = output_dir / f'ofertas_permanencia_baja_{timestamp}.csv'
        df_baja.to_csv(baja_file, index=False, encoding='utf-8-sig')
        archivos['permanencia_baja'] = str(baja_file)

        return archivos


def imprimir_estadisticas(stats: Dict):
    """Imprime estadísticas formateadas"""
    print("="*70)
    print("ESTADÍSTICAS DE PERMANENCIA")
    print("="*70)
    print()

    print(f"Total ofertas: {stats['total_ofertas']:,}")
    print()

    print("Por estado:")
    for estado, cantidad in stats['por_estado'].items():
        pct = cantidad / stats['total_ofertas'] * 100
        print(f"  {estado:15}: {cantidad:,} ({pct:.1f}%)")
    print()

    if stats['permanencia_global']['promedio_dias']:
        print("Permanencia global:")
        print(f"  Promedio: {stats['permanencia_global']['promedio_dias']} días")
        print(f"  Mínimo: {stats['permanencia_global']['minimo_dias']} días")
        print(f"  Máximo: {stats['permanencia_global']['maximo_dias']} días")
        print()

    print("Por categoría de permanencia:")
    for cat, datos in stats['por_categoria'].items():
        print(f"  {cat:15}: {datos['cantidad']:,} ofertas (promedio: {datos['promedio_dias']} días)")
    print()

    print("Distribución por rangos:")
    for rango, cantidad in stats['distribucion_rangos'].items():
        print(f"  {rango}: {cantidad:,}")

    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Calcula y analiza permanencia de ofertas'
    )
    parser.add_argument(
        '--calcular',
        action='store_true',
        help='Calcular permanencia (actualizar BD)'
    )
    parser.add_argument(
        '--exportar',
        action='store_true',
        help='Exportar reporte completo'
    )
    parser.add_argument(
        '--detalle',
        choices=['area', 'empresa', 'modalidad', 'provincia', 'extremas'],
        help='Mostrar detalle específico'
    )

    args = parser.parse_args()

    with AnalizadorPermanencia() as analizador:
        # Calcular permanencia si se solicita
        if args.calcular:
            print("Calculando permanencia...")
            n_baja = analizador.calcular_permanencia_ofertas_baja()
            n_activa = analizador.calcular_permanencia_ofertas_activas()
            n_cat = analizador.categorizar_permanencia()
            print(f"  Ofertas baja procesadas: {n_baja:,}")
            print(f"  Ofertas activas procesadas: {n_activa:,}")
            print(f"  Ofertas categorizadas: {n_cat:,}")
            print()

        # Mostrar estadísticas generales
        stats = analizador.obtener_estadisticas_generales()
        imprimir_estadisticas(stats)

        # Mostrar detalle si se solicita
        if args.detalle == 'area':
            print("\nPERMANENCIA POR ÁREA:")
            print(analizador.obtener_permanencia_por_area().to_string())

        elif args.detalle == 'empresa':
            print("\nPERMANENCIA POR EMPRESA (top 30):")
            print(analizador.obtener_permanencia_por_empresa().head(30).to_string())

        elif args.detalle == 'modalidad':
            print("\nPERMANENCIA POR MODALIDAD:")
            print(analizador.obtener_permanencia_por_modalidad().to_string())

        elif args.detalle == 'provincia':
            print("\nPERMANENCIA POR PROVINCIA:")
            print(analizador.obtener_permanencia_por_provincia().to_string())

        elif args.detalle == 'extremas':
            print("\nOFERTAS CON PERMANENCIA MÁS ALTA:")
            print(analizador.obtener_ofertas_extremas('alta', 10).to_string())
            print("\nOFERTAS CON PERMANENCIA MÁS BAJA:")
            print(analizador.obtener_ofertas_extremas('baja', 10).to_string())

        # Exportar si se solicita
        if args.exportar:
            print("\nExportando reporte...")
            archivos = analizador.exportar_reporte_completo()
            print("Archivos generados:")
            for tipo, ruta in archivos.items():
                print(f"  {tipo}: {ruta}")


if __name__ == '__main__':
    main()
