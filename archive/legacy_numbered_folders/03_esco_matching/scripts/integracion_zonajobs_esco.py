# -*- coding: utf-8 -*-
"""
Integración ZonaJobs + ESCO
Conecta datos scrapeados de ZonaJobs con la ontología ESCO

PATHS CONFIGURADOS PARA TU PROYECTO:
- ZonaJobs data: D:\OEDE\Webscrapping\data\raw\
- ESCO RDF: D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf
- Output: D:\OEDE\Webscrapping\data\processed\
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import re
from difflib import SequenceMatcher

# CONFIGURACIÓN DE PATHS
ZONAJOBS_DATA_DIR = Path(r"D:\OEDE\Webscrapping\data\raw")
ESCO_BASE_DIR = Path(r"D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco")
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\data\processed")

# Crear directorio de salida si no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class IntegradorZonaJobsESCO:
    """Integrador principal de ZonaJobs con ESCO"""

    def __init__(self):
        self.zonajobs_df = None
        self.esco_ocupaciones = None
        self.esco_skills = None
        self.resultados = []

    def cargar_zonajobs(self):
        """Carga los últimos datos scrapeados de ZonaJobs"""
        print("\n" + "=" * 80)
        print("PASO 1: CARGANDO DATOS DE ZONAJOBS")
        print("=" * 80)

        # Buscar último archivo CSV
        archivos_csv = list(ZONAJOBS_DATA_DIR.glob("zonajobs_todas_*.csv"))

        if not archivos_csv:
            print("[ERROR] No se encontraron archivos de ZonaJobs")
            print(f"  Buscar en: {ZONAJOBS_DATA_DIR}")
            return False

        ultimo_csv = max(archivos_csv, key=lambda x: x.stat().st_mtime)
        print(f"[LOAD] Archivo: {ultimo_csv.name}")

        self.zonajobs_df = pd.read_csv(ultimo_csv)
        print(f"[OK] Cargadas {len(self.zonajobs_df)} ofertas")
        print(f"[OK] Campos: {len(self.zonajobs_df.columns)}")

        return True

    def cargar_esco_desde_procesado(self):
        """
        Carga datos ESCO ya procesados desde output/

        NOTA: Si necesitas procesar el RDF completo, usa los scripts
        existentes en EPH-ESCO para generar las tablas procesadas.
        """
        print("\n" + "=" * 80)
        print("PASO 2: CARGANDO ONTOLOGÍA ESCO")
        print("=" * 80)

        output_dir = ESCO_BASE_DIR / "output"

        # Verificar si existen datos procesados
        resultado_csv = output_dir / "resultado_agrupado.csv"

        if resultado_csv.exists():
            print(f"[LOAD] Archivo ESCO procesado: {resultado_csv.name}")
            esco_data = pd.read_csv(resultado_csv)
            print(f"[OK] Cargados {len(esco_data)} registros ESCO")

            # Extraer ocupaciones únicas
            # NOTA: Ajustar según estructura real de resultado_agrupado.csv
            print("[INFO] Estructura de datos ESCO:")
            print(f"  Columnas: {', '.join(esco_data.columns)}")

            return esco_data
        else:
            print("[WARN] No se encontraron datos ESCO procesados")
            print(f"  Esperado en: {resultado_csv}")
            print("\n[INFO] Para procesar ESCO desde RDF:")
            print("  1. Ve a: D:\\Trabajos en PY\\EPH-ESCO\\01_datos_originales\\Tablas_esco")
            print("  2. Ejecuta el notebook: extraccion_esco.ipynb")
            print("  3. O usa los scripts de procesamiento existentes")

            return None

    def cargar_esco_simple(self):
        """
        Carga simplificada de ESCO creando lista de ocupaciones desde
        el informe o datos disponibles
        """
        print("\n[MODO] Carga simplificada de ESCO")

        # Como no tenemos las tablas procesadas aún, creamos una estructura básica
        # que puede ser poblada luego con tus scripts de ESCO

        print("[INFO] Usando modo de placeholder")
        print("[TODO] Ejecutar pipeline de extracción ESCO para obtener:")
        print("  - Lista completa de 3,008 ocupaciones")
        print("  - 13,890 skills y competencias")
        print("  - Relaciones occupation-skill")

        # Placeholder
        self.esco_ocupaciones = pd.DataFrame({
            'esco_uri': [],
            'esco_label_es': [],
            'isco_code': []
        })

        return True

    def similitud_texto(self, texto1, texto2):
        """Calcula similitud entre dos textos"""
        return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()

    def matching_simple(self, titulo_zonajobs, ocupaciones_esco, threshold=0.6):
        """
        Encuentra la ocupación ESCO más similar a un título de ZonaJobs

        Args:
            titulo_zonajobs: Título de la oferta
            ocupaciones_esco: DataFrame con ocupaciones ESCO
            threshold: Umbral mínimo de similitud

        Returns:
            dict con match o None
        """
        if ocupaciones_esco is None or len(ocupaciones_esco) == 0:
            return None

        mejor_match = None
        mejor_score = 0

        for idx, occ in ocupaciones_esco.iterrows():
            score = self.similitud_texto(titulo_zonajobs, occ['esco_label_es'])

            if score > mejor_score and score >= threshold:
                mejor_score = score
                mejor_match = {
                    'esco_uri': occ['esco_uri'],
                    'esco_label': occ['esco_label_es'],
                    'isco_code': occ.get('isco_code'),
                    'similitud': score
                }

        return mejor_match

    def clasificar_ofertas(self, threshold=0.6):
        """
        Clasifica todas las ofertas de ZonaJobs con ocupaciones ESCO

        Args:
            threshold: Umbral de similitud mínimo
        """
        print("\n" + "=" * 80)
        print("PASO 3: CLASIFICANDO OFERTAS CON ESCO")
        print("=" * 80)

        if self.zonajobs_df is None:
            print("[ERROR] Datos de ZonaJobs no cargados")
            return False

        if self.esco_ocupaciones is None or len(self.esco_ocupaciones) == 0:
            print("[WARN] Datos ESCO no disponibles - usando modo placeholder")
            print("[INFO] Las ofertas se guardarán sin clasificación ESCO")
            print("[TODO] Ejecuta primero el pipeline de extracción ESCO\n")

            # Guardar ofertas sin clasificación
            resultados = []
            for idx, oferta in self.zonajobs_df.iterrows():
                resultado = {
                    'id_oferta': oferta['id_oferta'],
                    'titulo': oferta['titulo'],
                    'empresa': oferta['empresa'],
                    'localizacion': oferta['localizacion'],
                    'modalidad_trabajo': oferta['modalidad_trabajo'],
                    'esco_uri': None,
                    'esco_label': None,
                    'isco_code': None,
                    'similitud': 0.0,
                    'fecha_clasificacion': datetime.now().isoformat()
                }
                resultados.append(resultado)

            self.resultados = pd.DataFrame(resultados)
            return True

        # Clasificación con ESCO
        print(f"[PROCESS] Clasificando {len(self.zonajobs_df)} ofertas...")
        print(f"[CONFIG] Threshold de similitud: {threshold}")

        resultados = []
        clasificadas = 0

        for idx, oferta in self.zonajobs_df.iterrows():
            match = self.matching_simple(
                oferta['titulo'],
                self.esco_ocupaciones,
                threshold
            )

            resultado = {
                'id_oferta': oferta['id_oferta'],
                'titulo': oferta['titulo'],
                'empresa': oferta['empresa'],
                'localizacion': oferta['localizacion'],
                'modalidad_trabajo': oferta['modalidad_trabajo'],
                'descripcion': oferta.get('descripcion', ''),
                'esco_uri': match['esco_uri'] if match else None,
                'esco_label': match['esco_label'] if match else None,
                'isco_code': match['isco_code'] if match else None,
                'similitud': match['similitud'] if match else 0.0,
                'fecha_clasificacion': datetime.now().isoformat()
            }

            resultados.append(resultado)

            if match:
                clasificadas += 1

            if (idx + 1) % 10 == 0:
                print(f"  Progreso: {idx + 1}/{len(self.zonajobs_df)}")

        self.resultados = pd.DataFrame(resultados)

        print(f"\n[OK] Clasificación completada")
        print(f"  Clasificadas: {clasificadas}/{len(self.zonajobs_df)} ({clasificadas/len(self.zonajobs_df)*100:.1f}%)")

        return True

    def guardar_resultados(self):
        """Guarda los resultados en múltiples formatos"""
        print("\n" + "=" * 80)
        print("PASO 4: GUARDANDO RESULTADOS")
        print("=" * 80)

        if self.resultados is None or len(self.resultados) == 0:
            print("[ERROR] No hay resultados para guardar")
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV
        csv_path = OUTPUT_DIR / f"zonajobs_esco_clasificadas_{timestamp}.csv"
        self.resultados.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"[SAVE] CSV: {csv_path}")

        # JSON
        json_path = OUTPUT_DIR / f"zonajobs_esco_clasificadas_{timestamp}.json"
        self.resultados.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"[SAVE] JSON: {json_path}")

        # Excel con múltiples hojas
        excel_path = OUTPUT_DIR / f"zonajobs_esco_analisis_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Hoja 1: Todas las ofertas clasificadas
            self.resultados.to_excel(writer, sheet_name='Ofertas Clasificadas', index=False)

            # Hoja 2: Resumen de clasificación
            clasificadas = self.resultados[self.resultados['esco_uri'].notna()]

            if len(clasificadas) > 0:
                resumen_ocupaciones = clasificadas.groupby('esco_label').size().sort_values(ascending=False)
                resumen_ocupaciones.to_excel(writer, sheet_name='Resumen Ocupaciones ESCO')

                # Hoja 3: Por modalidad
                resumen_modalidad = clasificadas.groupby(['modalidad_trabajo', 'esco_label']).size().unstack(fill_value=0)
                resumen_modalidad.to_excel(writer, sheet_name='Por Modalidad')

        print(f"[SAVE] Excel: {excel_path}")

        # Estadísticas
        self.mostrar_estadisticas()

        return True

    def mostrar_estadisticas(self):
        """Muestra estadísticas de la clasificación"""
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS DE CLASIFICACIÓN")
        print("=" * 80)

        total = len(self.resultados)
        clasificadas = self.resultados['esco_uri'].notna().sum()
        sin_clasificar = total - clasificadas

        print(f"\nTotal de ofertas: {total}")
        print(f"Clasificadas con ESCO: {clasificadas} ({clasificadas/total*100:.1f}%)")
        print(f"Sin clasificar: {sin_clasificar} ({sin_clasificar/total*100:.1f}%)")

        if clasificadas > 0:
            print(f"\nSimilitud promedio: {self.resultados[self.resultados['esco_uri'].notna()]['similitud'].mean():.2f}")
            print(f"Similitud mediana: {self.resultados[self.resultados['esco_uri'].notna()]['similitud'].median():.2f}")

            print("\nTop 10 Ocupaciones ESCO:")
            top_ocupaciones = self.resultados[self.resultados['esco_uri'].notna()]['esco_label'].value_counts().head(10)
            for ocupacion, count in top_ocupaciones.items():
                print(f"  {count:3d} - {ocupacion}")

        print("=" * 80)

    def ejecutar_pipeline_completo(self):
        """Ejecuta el pipeline completo de integración"""
        print("\n" + "=" * 80)
        print("INTEGRACIÓN ZONAJOBS + ESCO")
        print("Conectando ofertas laborales con ontología ESCO")
        print("=" * 80)

        # Paso 1: Cargar ZonaJobs
        if not self.cargar_zonajobs():
            print("\n[ERROR] No se pudieron cargar datos de ZonaJobs")
            return False

        # Paso 2: Intentar cargar ESCO procesado
        esco_data = self.cargar_esco_desde_procesado()

        if esco_data is None:
            # Si no hay datos procesados, usar modo simple
            self.cargar_esco_simple()

        # Paso 3: Clasificar
        if not self.clasificar_ofertas(threshold=0.6):
            print("\n[ERROR] Error en clasificación")
            return False

        # Paso 4: Guardar
        if not self.guardar_resultados():
            print("\n[ERROR] Error guardando resultados")
            return False

        print("\n" + "=" * 80)
        print("INTEGRACIÓN COMPLETADA")
        print("=" * 80)
        print(f"\nResultados guardados en: {OUTPUT_DIR}")
        print("\nPRÓXIMOS PASOS:")
        print("1. Si no se clasificaron ofertas, ejecutar pipeline ESCO:")
        print("   - Ir a: D:\\Trabajos en PY\\EPH-ESCO\\01_datos_originales\\Tablas_esco")
        print("   - Ejecutar: extraccion_esco.ipynb")
        print("2. Re-ejecutar este script con datos ESCO completos")
        print("3. Analizar resultados en archivos generados")

        return True


def main():
    """Función principal"""
    integrador = IntegradorZonaJobsESCO()
    integrador.ejecutar_pipeline_completo()


if __name__ == "__main__":
    main()
