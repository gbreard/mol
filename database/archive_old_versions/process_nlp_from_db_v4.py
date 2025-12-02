#!/usr/bin/env python3
"""
Procesa NLP con MODO HÍBRIDO v4.0
==================================

Arquitectura:
1. Regex v3.7 (base rápida, 100% ofertas)
2. LLM refinement (solo campos vacíos, ~30% ofertas)

Modos disponibles:
- 'regex_only': Solo regex v3.7
- 'hybrid': Regex v3.7 + LLM para campos vacíos (recomendado)
- 'llm_refine_all': LLM para todos los campos vacíos

Tiempo estimado (hybrid, 5,479 ofertas):
- Regex: ~2 min
- LLM: ~30-45 min (solo ofertas con campos vacíos)
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Agregar paths
scripts_dir = Path(__file__).parent.parent / "02.5_nlp_extraction" / "scripts"
sys.path.insert(0, str(scripts_dir))

from extractors.bumeran_extractor import BumeranExtractor
from llm_extractor import LLMExtractor


class HybridNLPProcessor:
    """Procesa NLP con modo híbrido: Regex v3.7 + LLM refinement"""

    def __init__(
        self,
        db_path='bumeran_scraping.db',
        mode='hybrid',
        llm_model='llama3:latest'
    ):
        """
        Inicializa el procesador híbrido

        Args:
            db_path: Path a la base de datos
            mode: 'regex_only', 'hybrid', o 'llm_refine_all'
            llm_model: Modelo LLM a usar (default: llama3:latest)
        """
        self.db_path = Path(__file__).parent / db_path
        self.mode = mode
        self.regex_extractor = BumeranExtractor()
        self.llm_extractor = None
        self.conn = None

        # Inicializar LLM solo si es necesario
        if mode in ['hybrid', 'llm_refine_all']:
            try:
                self.llm_extractor = LLMExtractor(model=llm_model)
                print(f"[OK] LLM inicializado: {llm_model}")
            except Exception as e:
                print(f"[WARNING] No se pudo inicializar LLM: {e}")
                print("[WARNING] Usando solo regex")
                self.mode = 'regex_only'

    def conectar(self):
        """Conecta a la base de datos"""
        self.conn = sqlite3.connect(self.db_path)
        print(f"[OK] Conectado a: {self.db_path}")

    def obtener_ofertas(self, solo_con_campos_vacios=False):
        """
        Obtiene ofertas de la tabla ofertas

        Args:
            solo_con_campos_vacios: Si True, solo ofertas con campos vacíos en NLP
        """
        cursor = self.conn.cursor()

        if solo_con_campos_vacios:
            # Solo ofertas que ya tienen registro NLP pero con campos vacíos
            query = """
                SELECT o.id_oferta, o.titulo, o.descripcion
                FROM ofertas o
                INNER JOIN ofertas_nlp n ON o.id_oferta = CAST(n.id_oferta AS TEXT)
                WHERE o.descripcion IS NOT NULL
                AND (
                    n.experiencia_min_anios IS NULL
                    OR n.nivel_educativo IS NULL
                    OR n.skills_tecnicas_list IS NULL
                    OR n.soft_skills_list IS NULL
                )
            """
        else:
            # Todas las ofertas con descripción
            query = """
                SELECT id_oferta, titulo, descripcion
                FROM ofertas
                WHERE descripcion IS NOT NULL
            """

        cursor.execute(query)
        ofertas = cursor.fetchall()
        print(f"[OK] {len(ofertas):,} ofertas para procesar")
        return ofertas

    def procesar_oferta(self, id_oferta, titulo, descripcion):
        """
        Procesa una oferta con el modo seleccionado

        Returns:
            dict con campos NLP extraídos
        """
        import json

        # 1. FASE BASE: Regex v3.7 (siempre)
        resultado = self.regex_extractor.extract_all(
            descripcion=descripcion if descripcion else "",
            titulo=titulo if titulo else ""
        )

        # 2. FASE REFINAMIENTO: LLM (solo si hay campos vacíos y modo habilitado)
        if self.llm_extractor and self.mode in ['hybrid', 'llm_refine_all']:
            # Determinar si necesita refinamiento
            necesita_refinamiento = (
                resultado.get('experiencia_min_anios') is None or
                resultado.get('nivel_educativo') is None or
                resultado.get('skills_tecnicas_list') is None or
                resultado.get('soft_skills_list') is None
            )

            if necesita_refinamiento:
                try:
                    resultado = self.llm_extractor.refine_empty_fields(
                        titulo=titulo if titulo else "",
                        descripcion=descripcion if descripcion else "",
                        current_result=resultado
                    )
                except Exception as e:
                    # Si falla el LLM, continuar con regex
                    print(f"[WARNING] LLM falló para oferta {id_oferta}: {e}")

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
                datos_nlp.get('nlp_version', 'v4.0.0'),
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
                datos_nlp.get('nlp_version', 'v4.0.0'),
                datos_nlp.get('nlp_confidence_score', 0.0)
            ))

    def ejecutar(self, solo_con_campos_vacios=False):
        """
        Ejecuta el proceso completo

        Args:
            solo_con_campos_vacios: Si True, solo procesa ofertas con campos vacíos
        """
        print("=" * 70)
        print(f"PROCESAMIENTO NLP v4.0 - MODO: {self.mode.upper()}")
        print("=" * 70)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Arquitectura: Regex v3.7 + {'LLM refinement' if self.mode != 'regex_only' else 'Sin LLM'}")
        print()

        self.conectar()
        ofertas = self.obtener_ofertas(solo_con_campos_vacios=solo_con_campos_vacios)

        print(f"\n[PROCESANDO] Extrayendo datos NLP...")

        procesadas = 0
        con_llm = 0
        errores = 0

        for id_oferta, titulo, descripcion in tqdm(ofertas, desc="Procesando", unit="oferta"):
            try:
                # Procesar NLP
                datos_nlp = self.procesar_oferta(id_oferta, titulo, descripcion)

                # Contar si se usó LLM
                if datos_nlp.get('nlp_version') == 'v4.0.0':
                    con_llm += 1

                # Insertar en DB
                self.insertar_nlp(datos_nlp)

                procesadas += 1

                # Commit cada 50 ofertas (menos frecuente para LLM)
                if procesadas % 50 == 0:
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
        print(f"Modo:                {self.mode}")
        print(f"Ofertas procesadas:  {procesadas:,}")
        print(f"Con LLM refinement:  {con_llm:,} ({con_llm/max(procesadas,1)*100:.1f}%)")
        print(f"Errores:             {errores:,}")

        # Verificar tabla
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ofertas_nlp")
        total_nlp = cursor.fetchone()[0]

        # Contar versiones
        cursor.execute("""
            SELECT nlp_version, COUNT(*) as count
            FROM ofertas_nlp
            GROUP BY nlp_version
        """)
        versiones = cursor.fetchall()

        print(f"\nTotal en ofertas_nlp: {total_nlp:,}")
        print("\nVersiones NLP:")
        for version, count in versiones:
            print(f"  {version}: {count:,} ofertas ({count/max(total_nlp,1)*100:.1f}%)")

        self.conn.close()
        print(f"\n[OK] Proceso completado - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Procesa NLP con modo híbrido v4.0')
    parser.add_argument(
        '--mode',
        choices=['regex_only', 'hybrid', 'llm_refine_all'],
        default='hybrid',
        help='Modo de procesamiento (default: hybrid)'
    )
    parser.add_argument(
        '--only-empty',
        action='store_true',
        help='Procesar solo ofertas con campos vacíos'
    )
    parser.add_argument(
        '--model',
        default='llama3:latest',
        help='Modelo LLM a usar (default: llama3:latest)'
    )

    args = parser.parse_args()

    try:
        processor = HybridNLPProcessor(mode=args.mode, llm_model=args.model)
        processor.ejecutar(solo_con_campos_vacios=args.only_empty)
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
