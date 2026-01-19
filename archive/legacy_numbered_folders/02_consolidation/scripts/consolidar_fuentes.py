"""
Script principal de consolidación de datos de múltiples fuentes.
Lee datos crudos, normaliza y consolida en formato unificado.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import glob
import sys
from pathlib import Path
import argparse
import logging

# Agregar path del proyecto
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from normalizar_campos import get_normalizer


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConsolidadorMultiFuente:
    """Consolida datos de múltiples fuentes en formato unificado"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.sources_dir = self.project_root / "01_sources"
        self.output_dir = self.project_root / "02_consolidation" / "data" / "consolidated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def listar_fuentes_disponibles(self):
        """Lista fuentes con datos disponibles"""
        fuentes = []
        for source_dir in self.sources_dir.iterdir():
            if source_dir.is_dir():
                raw_dir = source_dir / "data" / "raw"
                if raw_dir.exists():
                    csv_files = list(raw_dir.glob("*.csv"))
                    if csv_files:
                        fuentes.append({
                            'nombre': source_dir.name,
                            'path': raw_dir,
                            'archivos': len(csv_files),
                            'ultimo_archivo': max(csv_files, key=lambda p: p.stat().st_mtime)
                        })
        return fuentes

    def cargar_datos_fuente(self, fuente_nombre: str, archivo: Path = None):
        """Carga datos crudos de una fuente"""
        logger.info(f"Cargando datos de {fuente_nombre}...")

        raw_dir = self.sources_dir / fuente_nombre / "data" / "raw"

        if not raw_dir.exists():
            logger.warning(f"No existe directorio de datos para {fuente_nombre}")
            return None

        # Si no se especifica archivo, tomar el más reciente
        if archivo is None:
            csv_files = list(raw_dir.glob("*.csv"))
            if not csv_files:
                logger.warning(f"No hay archivos CSV en {raw_dir}")
                return None
            archivo = max(csv_files, key=lambda p: p.stat().st_mtime)

        logger.info(f"  Archivo: {archivo.name}")

        try:
            df = pd.read_csv(archivo)
            logger.info(f"  Ofertas cargadas: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"Error cargando {archivo}: {e}")
            return None

    def normalizar_fuente(self, fuente_nombre: str, df: pd.DataFrame):
        """Normaliza datos de una fuente al schema unificado"""
        logger.info(f"Normalizando datos de {fuente_nombre}...")

        try:
            normalizer = get_normalizer(fuente_nombre)
            df_normalized = normalizer.normalize(df)
            logger.info(f"  Ofertas normalizadas: {len(df_normalized)}")
            return df_normalized
        except NotImplementedError:
            logger.warning(f"Normalizador no implementado para {fuente_nombre}")
            return None
        except Exception as e:
            logger.error(f"Error normalizando {fuente_nombre}: {e}")
            return None

    def consolidar_todas(
        self,
        fuentes: list = None,
        fecha_desde: str = None,
        fecha_hasta: str = None
    ):
        """Consolida datos de todas las fuentes"""
        logger.info("=== Iniciando Consolidación de Fuentes ===\n")

        # Si no se especifican fuentes, usar todas las disponibles
        if fuentes is None:
            fuentes_disponibles = self.listar_fuentes_disponibles()
            fuentes = [f['nombre'] for f in fuentes_disponibles]
            logger.info(f"Fuentes disponibles: {fuentes}\n")

        # Consolidar cada fuente
        dfs_consolidados = []

        for fuente in fuentes:
            logger.info(f"--- Procesando {fuente} ---")

            # Cargar datos crudos
            df_raw = self.cargar_datos_fuente(fuente)
            if df_raw is None:
                continue

            # Normalizar
            df_normalized = self.normalizar_fuente(fuente, df_raw)
            if df_normalized is None:
                continue

            dfs_consolidados.append(df_normalized)
            logger.info(f"[OK] {fuente} consolidado exitosamente\n")

        # Combinar todos los DataFrames
        if not dfs_consolidados:
            logger.error("No se pudo consolidar ninguna fuente")
            return None

        logger.info("=== Combinando todas las fuentes ===")
        df_final = pd.concat(dfs_consolidados, ignore_index=True)
        logger.info(f"Total de ofertas consolidadas: {len(df_final)}")

        # Filtrar por fechas si se especifica
        if fecha_desde or fecha_hasta:
            df_final = self._filtrar_por_fechas(df_final, fecha_desde, fecha_hasta)

        return df_final

    def _filtrar_por_fechas(self, df: pd.DataFrame, fecha_desde: str = None, fecha_hasta: str = None):
        """Filtra ofertas por rango de fechas"""
        logger.info("Filtrando por fechas...")

        # Convertir columna de fecha a datetime
        df['_temp_fecha'] = pd.to_datetime(df['fechas.fecha_publicacion'], errors='coerce')

        # Filtrar
        mask = pd.Series([True] * len(df))

        if fecha_desde:
            fecha_desde_dt = pd.to_datetime(fecha_desde)
            mask &= df['_temp_fecha'] >= fecha_desde_dt
            logger.info(f"  Desde: {fecha_desde}")

        if fecha_hasta:
            fecha_hasta_dt = pd.to_datetime(fecha_hasta)
            mask &= df['_temp_fecha'] <= fecha_hasta_dt
            logger.info(f"  Hasta: {fecha_hasta}")

        df_filtrado = df[mask].drop(columns=['_temp_fecha'])
        logger.info(f"Ofertas después de filtrar: {len(df_filtrado)}")

        return df_filtrado

    def guardar_consolidado(
        self,
        df: pd.DataFrame,
        formato: str = 'csv',
        nombre_base: str = None
    ):
        """Guarda datos consolidados"""
        if nombre_base is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_base = f"ofertas_consolidadas_{timestamp}"

        # Guardar según formato
        if formato == 'csv' or formato == 'all':
            csv_path = self.output_dir / f"{nombre_base}.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"[OK] Guardado CSV: {csv_path}")

        if formato == 'json' or formato == 'all':
            json_path = self.output_dir / f"{nombre_base}.json"
            df.to_json(json_path, orient='records', indent=2, force_ascii=False)
            logger.info(f"[OK] Guardado JSON: {json_path}")

        if formato == 'excel' or formato == 'all':
            excel_path = self.output_dir / f"{nombre_base}.xlsx"
            df.to_excel(excel_path, index=False, engine='openpyxl')
            logger.info(f"[OK] Guardado Excel: {excel_path}")

    def generar_reporte_consolidacion(self, df: pd.DataFrame):
        """Genera reporte de la consolidación"""
        logger.info("\n=== Reporte de Consolidación ===")
        logger.info(f"Total de ofertas: {len(df)}")

        # Ofertas por fuente
        logger.info("\nOfertas por fuente:")
        fuentes_count = df['_metadata.source'].value_counts()
        for fuente, count in fuentes_count.items():
            logger.info(f"  {fuente}: {count}")

        # Cobertura de campos
        logger.info("\nCobertura de campos principales:")
        campos_principales = [
            'informacion_basica.titulo',
            'informacion_basica.empresa',
            'ubicacion.provincia',
            'modalidad.modalidad_trabajo',
            'modalidad.tipo_trabajo',
            'fechas.fecha_publicacion'
        ]

        for campo in campos_principales:
            if campo in df.columns:
                no_nulos = df[campo].notna().sum()
                porcentaje = (no_nulos / len(df)) * 100
                logger.info(f"  {campo}: {porcentaje:.1f}%")

        # Rango de fechas
        if 'fechas.fecha_publicacion' in df.columns:
            fechas = pd.to_datetime(df['fechas.fecha_publicacion'], errors='coerce')
            logger.info(f"\nRango de fechas:")
            logger.info(f"  Desde: {fechas.min()}")
            logger.info(f"  Hasta: {fechas.max()}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Consolidar datos de múltiples fuentes')

    parser.add_argument(
        '--fuentes',
        nargs='+',
        help='Fuentes a consolidar (ej: zonajobs bumeran). Si no se especifica, usa todas.'
    )
    parser.add_argument(
        '--fecha-desde',
        help='Filtrar ofertas desde esta fecha (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--fecha-hasta',
        help='Filtrar ofertas hasta esta fecha (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--formato',
        choices=['csv', 'json', 'excel', 'all'],
        default='all',
        help='Formato de salida (default: all)'
    )
    parser.add_argument(
        '--nombre',
        help='Nombre base del archivo de salida'
    )
    parser.add_argument(
        '--listar',
        action='store_true',
        help='Solo listar fuentes disponibles'
    )

    args = parser.parse_args()

    # Crear consolidador
    consolidador = ConsolidadorMultiFuente()

    # Si solo se pide listar
    if args.listar:
        logger.info("=== Fuentes Disponibles ===\n")
        fuentes = consolidador.listar_fuentes_disponibles()
        for f in fuentes:
            logger.info(f"Fuente: {f['nombre']}")
            logger.info(f"  Archivos: {f['archivos']}")
            logger.info(f"  Último: {f['ultimo_archivo'].name}\n")
        return

    # Consolidar
    df_consolidado = consolidador.consolidar_todas(
        fuentes=args.fuentes,
        fecha_desde=args.fecha_desde,
        fecha_hasta=args.fecha_hasta
    )

    if df_consolidado is None:
        logger.error("Error en consolidación")
        return

    # Guardar
    consolidador.guardar_consolidado(
        df_consolidado,
        formato=args.formato,
        nombre_base=args.nombre
    )

    # Reporte
    consolidador.generar_reporte_consolidacion(df_consolidado)

    logger.info("\n✓ Consolidación completada exitosamente")


if __name__ == "__main__":
    main()
