#!/usr/bin/env python3
"""
FASE 4: Migrar resultados NLP desde CSV a base de datos

Lee los archivos CSV generados por la extracci[U+00F3]n NLP y los migra
a la tabla ofertas_nlp en la base de datos.

Maneja los 27 campos de extracci[U+00F3]n NLP incluyendo:
- Experiencia (a[U+00F1]os m[U+00ED]nimos/m[U+00E1]ximos)
- Educaci[U+00F3]n (nivel requerido/deseable)
- Skills t[U+00E9]cnicas/blandas
- Compensaci[U+00F3]n y beneficios
- Requisitos (edad, g[U+00E9]nero, etc.)

Tiempo estimado: 5 minutos
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("ERROR: La librer[U+00ED]a 'pandas' no est[U+00E1] instalada.")
    print("Instal[U+00E1] con: pip install pandas")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: La librer[U+00ED]a 'tqdm' no est[U+00E1] instalada. No se mostrar[U+00E1] barra de progreso.")
    tqdm = None


class NLPMigrator:
    """Migra resultados NLP desde CSV a base de datos"""

    def __init__(self, db_path='bumeran_scraping.db'):
        self.db_path = Path(__file__).parent / db_path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        # Buscar directorio de NLP
        self.nlp_data_dir = Path(__file__).parent.parent / "02.5_nlp_extraction" / "data" / "processed"

        self.conn = None
        self.stats = {
            'csv_files_found': 0,
            'total_records': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'records_skipped': 0,
            'errores': []
        }

    def conectar_db(self):
        """Conecta a DB"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[OK] Conectado a: {self.db_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            return False

    def buscar_archivos_nlp(self):
        """Busca archivos CSV de NLP"""
        print("\n[FILE] BUSCANDO ARCHIVOS NLP")
        print("=" * 70)

        if not self.nlp_data_dir.exists():
            print(f"  [WARNING] Directorio no encontrado: {self.nlp_data_dir}")
            print(f"  -> Creando directorio...")
            self.nlp_data_dir.mkdir(parents=True, exist_ok=True)
            return []

        # Buscar CSVs de NLP (acepta *_nlp_extracted*.csv y *_nlp_*.csv)
        csv_files = list(self.nlp_data_dir.glob("*_nlp*.csv"))

        if not csv_files:
            print(f"  [WARNING] No se encontraron archivos NLP en: {self.nlp_data_dir}")
            return []

        # Ordenar por fecha de modificaci[U+00F3]n (m[U+00E1]s reciente primero)
        csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print(f"  [OK] {len(csv_files)} archivo(s) encontrado(s):")
        for i, csv_file in enumerate(csv_files, 1):
            size_mb = csv_file.stat().st_size / 1024 / 1024
            mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
            print(f"    {i}. {csv_file.name}")
            print(f"       Tama[U+00F1]o: {size_mb:.2f} MB | Fecha: {mod_time.strftime('%Y-%m-%d %H:%M')}")

        self.stats['csv_files_found'] = len(csv_files)
        return csv_files

    def normalizar_columnas(self, df):
        """
        Normaliza nombres de columnas del CSV a los nombres de la tabla ofertas_nlp

        Args:
            df (DataFrame): DataFrame con datos NLP

        Returns:
            DataFrame: DataFrame con columnas normalizadas
        """
        # Mapeo de posibles nombres de columnas a nombres de tabla
        column_mapping = {
            'id_oferta': 'id_oferta',
            'anios_experiencia_minimo': 'anios_experiencia_minimo',
            'anios_experiencia_maximo': 'anios_experiencia_maximo',
            'experiencia_nivel_general': 'experiencia_nivel_general',
            'educacion_nivel_requerido': 'educacion_nivel_requerido',
            'educacion_nivel_deseable': 'educacion_nivel_deseable',
            'educacion_carreras_especificas': 'educacion_carreras_especificas',
            'educacion_estado_requerido': 'educacion_estado_requerido',
            'skills_tecnicas_list': 'skills_tecnicas_list',
            'skills_blandas_list': 'skills_blandas_list',
            'skills_idiomas_list': 'skills_idiomas_list',
            'compensacion_sueldo_mencionado': 'compensacion_sueldo_mencionado',
            'compensacion_tipo': 'compensacion_tipo',
            'compensacion_beneficios_list': 'compensacion_beneficios_list',
            'modalidad_trabajo': 'modalidad_trabajo',
            'tipo_contrato': 'tipo_contrato',
            'jornada_laboral': 'jornada_laboral',
            'disponibilidad_horaria': 'disponibilidad_horaria',
            'disponibilidad_viajar': 'disponibilidad_viajar',
            'disponibilidad_mudarse': 'disponibilidad_mudarse',
            'requisitos_edad_minima': 'requisitos_edad_minima',
            'requisitos_edad_maxima': 'requisitos_edad_maxima',
            'requisitos_genero': 'requisitos_genero',
            'requisitos_residencia': 'requisitos_residencia',
            'requisitos_vehiculo_propio': 'requisitos_vehiculo_propio',
            'requisitos_licencia_conducir': 'requisitos_licencia_conducir',
            'otros_certificaciones_list': 'otros_certificaciones_list',
            'otros_software_herramientas_list': 'otros_software_herramientas_list'
        }

        # Renombrar columnas que existan
        df_renamed = df.rename(columns=column_mapping)

        return df_renamed

    def procesar_csv(self, csv_file):
        """
        Procesa un archivo CSV de NLP

        Args:
            csv_file (Path): Ruta al archivo CSV
        """
        print(f"\n  [U+1F4C4] Procesando: {csv_file.name}")

        try:
            # Leer CSV
            df = pd.read_csv(csv_file, encoding='utf-8')
            print(f"    -> {len(df):,} registros en el CSV")

            if len(df) == 0:
                print("    [WARNING] Archivo vac[U+00ED]o, saltando...")
                return

            # Normalizar columnas
            df = self.normalizar_columnas(df)

            # Verificar que existe id_oferta
            if 'id_oferta' not in df.columns:
                print("    [ERROR] ERROR: No se encontr[U+00F3] columna 'id_oferta'")
                self.stats['errores'].append(f"{csv_file.name}: Falta columna id_oferta")
                return

            self.stats['total_records'] += len(df)

            # Insertar registros
            self.insertar_registros(df)

        except Exception as e:
            print(f"    [ERROR] Error procesando archivo: {e}")
            self.stats['errores'].append(f"{csv_file.name}: {e}")

    def insertar_registros(self, df):
        """
        Inserta registros en la tabla ofertas_nlp

        Args:
            df (DataFrame): DataFrame con datos NLP
        """
        cursor = self.conn.cursor()

        # Obtener columnas de la tabla ofertas_nlp
        cursor.execute("PRAGMA table_info(ofertas_nlp)")
        table_columns = {col[1] for col in cursor.fetchall()}

        # Filtrar solo las columnas que existen en la tabla
        df_columns = [col for col in df.columns if col in table_columns]

        if not df_columns:
            print("    [ERROR] ERROR: Ninguna columna coincide con la tabla ofertas_nlp")
            return

        print(f"    -> Insertando {len(df_columns)} campos por registro...")

        iterator = tqdm(df.iterrows(), total=len(df), desc="    Insertando", unit="reg") if tqdm else df.iterrows()

        for idx, row in iterator:
            try:
                # Preparar valores (solo columnas que existen en la tabla)
                values = {}
                for col in df_columns:
                    val = row[col]

                    # Manejar NaN
                    if pd.isna(val):
                        values[col] = None
                    # Manejar listas JSON (campos que terminan en _list)
                    elif col.endswith('_list') and isinstance(val, str):
                        try:
                            # Intentar parsear como JSON
                            parsed = json.loads(val)
                            values[col] = json.dumps(parsed, ensure_ascii=False)
                        except:
                            # Si falla, guardar como est[U+00E1]
                            values[col] = val
                    else:
                        values[col] = val

                # Verificar si ya existe
                id_oferta = values.get('id_oferta')
                cursor.execute("SELECT 1 FROM ofertas_nlp WHERE id_oferta = ?", (id_oferta,))
                existe = cursor.fetchone()

                if existe:
                    # UPDATE
                    set_clause = ", ".join([f"{col} = ?" for col in values.keys() if col != 'id_oferta'])
                    update_values = [values[col] for col in values.keys() if col != 'id_oferta']
                    update_values.append(id_oferta)

                    cursor.execute(f"""
                        UPDATE ofertas_nlp
                        SET {set_clause}
                        WHERE id_oferta = ?
                    """, update_values)

                    self.stats['records_updated'] += 1
                else:
                    # INSERT
                    columns = ", ".join(values.keys())
                    placeholders = ", ".join(["?" for _ in values])

                    cursor.execute(f"""
                        INSERT INTO ofertas_nlp ({columns})
                        VALUES ({placeholders})
                    """, list(values.values()))

                    self.stats['records_inserted'] += 1

            except Exception as e:
                self.stats['records_skipped'] += 1
                if len(self.stats['errores']) < 10:
                    self.stats['errores'].append(f"Registro {idx}: {e}")

        self.conn.commit()

    def generar_reporte(self):
        """Genera reporte final"""
        print("\n" + "=" * 70)
        print("REPORTE FINAL DE MIGRACI[U+00D3]N NLP")
        print("=" * 70)

        print(f"\n[STATS] ESTAD[U+00CD]STICAS:")
        print(f"  - Archivos CSV encontrados:   {self.stats['csv_files_found']}")
        print(f"  - Total registros en CSVs:    {self.stats['total_records']:,}")
        print(f"  - Registros insertados:       {self.stats['records_inserted']:,}")
        print(f"  - Registros actualizados:     {self.stats['records_updated']:,}")
        print(f"  - Registros saltados:         {self.stats['records_skipped']:,}")

        if self.stats['errores']:
            print(f"\n[WARNING] ERRORES: {len(self.stats['errores'])}")
            for error in self.stats['errores'][:10]:
                print(f"  - {error}")

        # Consultar totales en DB
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
        total_db = cursor.fetchone()[0]

        print(f"\n[CHART] ESTADO FINAL:")
        print(f"  - Total registros en ofertas_nlp: {total_db:,}")

        print("\n" + "=" * 70)
        print("[OK] PROCESO COMPLETADO")
        print("=" * 70)

    def ejecutar(self):
        """Ejecuta proceso completo"""
        print("\n" + "=" * 70)
        print("MIGRACI[U+00D3]N DE RESULTADOS NLP A BASE DE DATOS")
        print("=" * 70)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.conectar_db():
            return False

        # Buscar archivos
        csv_files = self.buscar_archivos_nlp()

        if not csv_files:
            print("\n[WARNING] No hay archivos para procesar")
            print("\nNOTA: Los archivos NLP se generar[U+00E1]n en la Fase 02.5 (NLP Extraction)")
            print("      Por ahora, esta tabla quedar[U+00E1] vac[U+00ED]a hasta que se complete esa fase.")
            return True

        # Procesar cada archivo
        print("\n[U+1F4E5] PROCESANDO ARCHIVOS NLP")
        print("=" * 70)

        for csv_file in csv_files:
            self.procesar_csv(csv_file)

        # Reporte
        self.generar_reporte()

        self.conn.close()
        return True

    def __del__(self):
        if self.conn:
            self.conn.close()


def main():
    try:
        migrator = NLPMigrator()
        exito = migrator.ejecutar()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
