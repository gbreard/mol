#!/usr/bin/env python3
"""
Procesa NLP directamente desde tabla ofertas a ofertas_nlp
Sin CSVs intermedios - todo en DB
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Agregar path al extractor de Bumeran
scripts_dir = Path(__file__).parent.parent / "02.5_nlp_extraction" / "scripts"
sys.path.insert(0, str(scripts_dir))

from extractors.bumeran_extractor import BumeranExtractor


class DirectNLPProcessor:
    """Procesa NLP directo de DB a DB"""

    def __init__(self, db_path='bumeran_scraping.db'):
        self.db_path = Path(__file__).parent / db_path
        self.extractor = BumeranExtractor()
        self.conn = None

    def conectar(self):
        """Conecta a la base de datos"""
        self.conn = sqlite3.connect(self.db_path)
        print(f"[OK] Conectado a: {self.db_path}")

    def obtener_ofertas(self):
        """Obtiene ofertas de la tabla ofertas"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id_oferta, titulo, descripcion
            FROM ofertas
            WHERE descripcion IS NOT NULL
        """)
        ofertas = cursor.fetchall()
        print(f"[OK] {len(ofertas):,} ofertas para procesar")
        return ofertas

    def procesar_oferta(self, id_oferta, titulo, descripcion):
        """
        Procesa una oferta con NLP

        Returns:
            dict con campos NLP extraídos
        """
        import json

        # Usar el extractor de Bumeran
        resultado = self.extractor.extract_all(
            descripcion=descripcion if descripcion else "",
            titulo=titulo if titulo else ""
        )

        # Agregar id_oferta
        resultado['id_oferta'] = id_oferta

        # Convertir listas a JSON strings
        for key, value in resultado.items():
            if isinstance(value, list):
                resultado[key] = json.dumps(value, ensure_ascii=False)

        return resultado

    def insertar_nlp(self, datos_nlp):
        """Inserta datos NLP en ofertas_nlp"""
        cursor = self.conn.cursor()

        # Verificar si ya existe
        cursor.execute("SELECT 1 FROM ofertas_nlp WHERE id_oferta = ?", (datos_nlp['id_oferta'],))
        existe = cursor.fetchone()

        if existe:
            # UPDATE
            cursor.execute("""
                UPDATE ofertas_nlp
                SET experiencia_min_anios = ?,
                    experiencia_max_anios = ?,
                    nivel_educativo = ?,
                    estado_educativo = ?,
                    carrera_especifica = ?,
                    idioma_principal = ?,
                    nivel_idioma_principal = ?,
                    skills_tecnicas_list = ?,
                    soft_skills_list = ?,
                    certificaciones_list = ?,
                    salario_min = ?,
                    salario_max = ?,
                    moneda = ?,
                    beneficios_list = ?,
                    requisitos_excluyentes_list = ?,
                    requisitos_deseables_list = ?,
                    jornada_laboral = ?,
                    horario_flexible = ?,
                    nlp_extraction_timestamp = ?,
                    nlp_version = ?,
                    nlp_confidence_score = ?
                WHERE id_oferta = ?
            """, (
                datos_nlp.get('experiencia_min_anios'),
                datos_nlp.get('experiencia_max_anios'),
                datos_nlp.get('nivel_educativo'),
                datos_nlp.get('estado_educativo'),
                datos_nlp.get('carrera_especifica'),
                datos_nlp.get('idioma_principal'),
                datos_nlp.get('nivel_idioma_principal'),
                datos_nlp.get('skills_tecnicas_list'),
                datos_nlp.get('soft_skills_list'),
                datos_nlp.get('certificaciones_list'),
                datos_nlp.get('salario_min'),
                datos_nlp.get('salario_max'),
                datos_nlp.get('moneda'),
                datos_nlp.get('beneficios_list'),
                datos_nlp.get('requisitos_excluyentes_list'),
                datos_nlp.get('requisitos_deseables_list'),
                datos_nlp.get('jornada_laboral'),
                datos_nlp.get('horario_flexible'),
                datetime.now().isoformat(),
                datos_nlp.get('nlp_version', 'v3.5.0'),
                datos_nlp.get('nlp_confidence_score', 0.0),
                datos_nlp['id_oferta']
            ))
        else:
            # INSERT
            cursor.execute("""
                INSERT INTO ofertas_nlp (
                    id_oferta, experiencia_min_anios, experiencia_max_anios,
                    nivel_educativo, estado_educativo, carrera_especifica,
                    idioma_principal, nivel_idioma_principal,
                    skills_tecnicas_list, soft_skills_list, certificaciones_list,
                    salario_min, salario_max, moneda, beneficios_list,
                    requisitos_excluyentes_list, requisitos_deseables_list,
                    jornada_laboral, horario_flexible,
                    nlp_extraction_timestamp, nlp_version, nlp_confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos_nlp['id_oferta'],
                datos_nlp.get('experiencia_min_anios'),
                datos_nlp.get('experiencia_max_anios'),
                datos_nlp.get('nivel_educativo'),
                datos_nlp.get('estado_educativo'),
                datos_nlp.get('carrera_especifica'),
                datos_nlp.get('idioma_principal'),
                datos_nlp.get('nivel_idioma_principal'),
                datos_nlp.get('skills_tecnicas_list'),
                datos_nlp.get('soft_skills_list'),
                datos_nlp.get('certificaciones_list'),
                datos_nlp.get('salario_min'),
                datos_nlp.get('salario_max'),
                datos_nlp.get('moneda'),
                datos_nlp.get('beneficios_list'),
                datos_nlp.get('requisitos_excluyentes_list'),
                datos_nlp.get('requisitos_deseables_list'),
                datos_nlp.get('jornada_laboral'),
                datos_nlp.get('horario_flexible'),
                datetime.now().isoformat(),
                datos_nlp.get('nlp_version', 'v3.5.0'),
                datos_nlp.get('nlp_confidence_score', 0.0)
            ))

    def ejecutar(self):
        """Ejecuta el proceso completo"""
        print("=" * 70)
        print("PROCESAMIENTO NLP DIRECTO: DB a DB")
        print("=" * 70)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.conectar()
        ofertas = self.obtener_ofertas()

        print(f"\n[PROCESANDO] Extrayendo datos NLP...")

        procesadas = 0
        errores = 0

        for id_oferta, titulo, descripcion in tqdm(ofertas, desc="Procesando", unit="oferta"):
            try:
                # Procesar NLP
                datos_nlp = self.procesar_oferta(id_oferta, titulo, descripcion)

                # Insertar en DB
                self.insertar_nlp(datos_nlp)

                procesadas += 1

                # Commit cada 100 ofertas
                if procesadas % 100 == 0:
                    self.conn.commit()

            except Exception as e:
                errores += 1
                if errores <= 10:
                    print(f"\n[ERROR] Oferta {id_oferta}: {e}")

        # Commit final
        self.conn.commit()

        # Reporte
        print(f"\n" + "=" * 70)
        print("REPORTE FINAL")
        print("=" * 70)
        print(f"Ofertas procesadas:  {procesadas:,}")
        print(f"Errores:             {errores:,}")

        # Verificar tabla
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
        total_nlp = cursor.fetchone()[0]
        print(f"\nTotal en ofertas_nlp: {total_nlp:,}")

        self.conn.close()
        print(f"\n[OK] Proceso completado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    try:
        processor = DirectNLPProcessor()
        processor.ejecutar()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
