# -*- coding: utf-8 -*-
"""
Script de utilidad para cargar datos de ZonaJobs
y prepararlos para análisis con ESCO y procesamiento semántico

Uso:
    from cargar_datos_para_procesamiento import cargar_ultimos_datos

    df = cargar_ultimos_datos()
    print(f"Cargadas {len(df)} ofertas")
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path
from datetime import datetime
import json


class CargadorDatosZonaJobs:
    """Cargador de datos de ZonaJobs para procesamiento posterior"""

    DATA_DIR = Path(r"D:\OEDE\Webscrapping\data\raw")
    OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\data\processed")

    def __init__(self):
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def listar_archivos_disponibles(self):
        """Lista todos los archivos de datos disponibles"""
        archivos = {
            'csv': list(self.DATA_DIR.glob("zonajobs_*.csv")),
            'json': list(self.DATA_DIR.glob("zonajobs_*.json")),
            'excel': list(self.DATA_DIR.glob("zonajobs_*.xlsx"))
        }

        print("=" * 80)
        print("ARCHIVOS DE DATOS DISPONIBLES")
        print("=" * 80)

        for formato, lista in archivos.items():
            print(f"\n{formato.upper()} ({len(lista)} archivos):")
            for archivo in sorted(lista, key=lambda x: x.stat().st_mtime, reverse=True):
                size = archivo.stat().st_size / 1024  # KB
                fecha = datetime.fromtimestamp(archivo.stat().st_mtime)
                print(f"  - {archivo.name}")
                print(f"    Tamano: {size:.1f} KB | Fecha: {fecha.strftime('%Y-%m-%d %H:%M')}")

        return archivos

    def cargar_ultimo_csv(self):
        """Carga el archivo CSV mas reciente"""
        archivos = list(self.DATA_DIR.glob("zonajobs_todas_*.csv"))

        if not archivos:
            print("[ERROR] No se encontraron archivos CSV")
            return None

        ultimo = max(archivos, key=lambda x: x.stat().st_mtime)

        print(f"\n[LOAD] Cargando: {ultimo.name}")
        df = pd.read_csv(ultimo)
        print(f"[OK] Cargadas {len(df)} ofertas con {len(df.columns)} columnas")

        return df

    def cargar_ultimo_json(self):
        """Carga el archivo JSON mas reciente"""
        archivos = list(self.DATA_DIR.glob("zonajobs_todas_*.json"))

        if not archivos:
            print("[ERROR] No se encontraron archivos JSON")
            return None

        ultimo = max(archivos, key=lambda x: x.stat().st_mtime)

        print(f"\n[LOAD] Cargando: {ultimo.name}")
        with open(ultimo, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        print(f"[OK] Cargadas {len(df)} ofertas con {len(df.columns)} columnas")

        return df

    def preparar_para_esco(self, df):
        """
        Prepara los datos para matching con ESCO

        Retorna DataFrame con columnas optimizadas para matching:
        - titulo_normalizado: Titulo limpio
        - descripcion_limpia: Descripcion sin HTML
        - texto_completo: Titulo + Descripcion para analisis
        """

        print("\n[PREP] Preparando datos para matching ESCO...")

        df_prep = df.copy()

        # Normalizar titulo
        df_prep['titulo_normalizado'] = df_prep['titulo'].str.lower().str.strip()

        # Usar descripcion limpia (ya sin HTML)
        df_prep['descripcion_limpia'] = df_prep['descripcion'].fillna('')

        # Crear texto completo para analisis
        df_prep['texto_completo'] = (
            df_prep['titulo'] + '. ' +
            df_prep['descripcion_limpia']
        )

        # Remover valores nulos
        df_prep = df_prep.dropna(subset=['titulo'])

        # Remover duplicados por ID
        df_prep = df_prep.drop_duplicates(subset=['id_oferta'])

        print(f"[OK] {len(df_prep)} ofertas preparadas")
        print(f"[OK] Columnas: {', '.join(df_prep.columns)}")

        return df_prep

    def extraer_campos_clave(self, df):
        """
        Extrae solo campos clave para procesamiento

        Retorna:
            DataFrame con campos minimos para analisis
        """
        campos_clave = [
            'id_oferta',
            'titulo',
            'descripcion',
            'empresa',
            'localizacion',
            'modalidad_trabajo',
            'tipo_trabajo',
            'fecha_publicacion',
            'url_oferta'
        ]

        # Filtrar solo campos que existen
        campos_disponibles = [c for c in campos_clave if c in df.columns]

        df_mini = df[campos_disponibles].copy()

        print(f"\n[EXTRACT] Extraidos {len(campos_disponibles)} campos clave")

        return df_mini

    def guardar_para_procesamiento(self, df, nombre="ofertas_para_procesar"):
        """Guarda datos preparados para el siguiente paso"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Guardar en CSV (mejor para pandas)
        csv_path = self.OUTPUT_DIR / f"{nombre}_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n[SAVE] CSV: {csv_path}")

        # Guardar en JSON (mejor para integraciones)
        json_path = self.OUTPUT_DIR / f"{nombre}_{timestamp}.json"
        df.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"[SAVE] JSON: {json_path}")

        return csv_path, json_path

    def estadisticas_rapidas(self, df):
        """Muestra estadisticas rapidas del dataset"""

        print("\n" + "=" * 80)
        print("ESTADISTICAS DEL DATASET")
        print("=" * 80)

        print(f"\nTotal de ofertas: {len(df)}")
        print(f"Empresas unicas: {df['empresa'].nunique()}")
        print(f"Ubicaciones unicas: {df['localizacion'].nunique()}")

        print("\nModalidades:")
        if 'modalidad_trabajo' in df.columns:
            print(df['modalidad_trabajo'].value_counts().to_string())

        print("\nTipos de trabajo:")
        if 'tipo_trabajo' in df.columns:
            print(df['tipo_trabajo'].value_counts().to_string())

        print("\nTop 10 empresas:")
        print(df['empresa'].value_counts().head(10).to_string())

        print("\nLongitud promedio de descripcion:")
        if 'descripcion' in df.columns:
            df['desc_len'] = df['descripcion'].fillna('').str.len()
            print(f"  Media: {df['desc_len'].mean():.0f} caracteres")
            print(f"  Mediana: {df['desc_len'].median():.0f} caracteres")

        print("\n" + "=" * 80)


# Funciones de conveniencia

def cargar_ultimos_datos():
    """
    Funcion rapida para cargar los ultimos datos

    Returns:
        DataFrame con las ofertas
    """
    cargador = CargadorDatosZonaJobs()
    return cargador.cargar_ultimo_csv()


def preparar_para_esco():
    """
    Funcion rapida para cargar y preparar datos para ESCO

    Returns:
        DataFrame preparado
    """
    cargador = CargadorDatosZonaJobs()
    df = cargador.cargar_ultimo_csv()

    if df is not None:
        df_prep = cargador.preparar_para_esco(df)
        csv_path, json_path = cargador.guardar_para_procesamiento(
            df_prep,
            "ofertas_para_esco"
        )
        return df_prep

    return None


def ejemplo_uso():
    """Ejemplo de uso del cargador"""

    print("=" * 80)
    print("EJEMPLO DE USO - CARGADOR DE DATOS ZONAJOBS")
    print("=" * 80)
    print()

    cargador = CargadorDatosZonaJobs()

    # 1. Listar archivos
    cargador.listar_archivos_disponibles()

    # 2. Cargar datos
    df = cargador.cargar_ultimo_csv()

    if df is not None:
        # 3. Estadisticas
        cargador.estadisticas_rapidas(df)

        # 4. Preparar para ESCO
        df_prep = cargador.preparar_para_esco(df)

        # 5. Extraer campos clave
        df_mini = cargador.extraer_campos_clave(df_prep)

        # 6. Guardar
        csv_path, json_path = cargador.guardar_para_procesamiento(
            df_mini,
            "ofertas_listas_para_esco"
        )

        print("\n" + "=" * 80)
        print("LISTO PARA PROCESAR")
        print("=" * 80)
        print(f"\nArchivos guardados en:")
        print(f"  {csv_path}")
        print(f"  {json_path}")
        print("\nProximo paso:")
        print("  1. Cargar estos datos en tu pipeline de ESCO")
        print("  2. Hacer matching de ocupaciones usando 'titulo_normalizado'")
        print("  3. Extraer skills usando 'descripcion_limpia'")
        print("  4. Guardar resultados en data/processed/")


if __name__ == "__main__":
    ejemplo_uso()
