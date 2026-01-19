# -*- coding: utf-8 -*-
"""
Integración Semántica ZonaJobs + ESCO
Conecta ofertas de ZonaJobs con ocupaciones ESCO usando matching semántico
y enriquece con skills y conocimientos

RECURSOS UTILIZADOS:
- ESCO consolidado: D:/Trabajos en PY/EPH-ESCO/07_esco_data/esco_consolidado_con_isco.json
- Skills ESCO: D:/Trabajos en PY/EPH-ESCO/07_esco_data/esco_skills_info.json
- Relaciones Ocupación-Skills: D:/Trabajos en PY/EPH-ESCO/07_esco_data/esco_ocupaciones_skills_relaciones.json
- ZonaJobs: D:/OEDE/Webscrapping/data/raw/
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
from collections import Counter, defaultdict
import unicodedata

# CONFIGURACIÓN DE PATHS
ZONAJOBS_DATA_DIR = Path(r"D:\OEDE\Webscrapping\data\raw")
ESCO_DATA_DIR = Path(r"D:\Trabajos en PY\EPH-ESCO\07_esco_data")
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\data\processed")

# Crear directorio de salida
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class NormalizadorTextoES:
    """Normalizador de texto en español para matching semántico"""

    # Términos comunes a remover
    STOPWORDS_ES = {
        'el', 'la', 'los', 'las', 'de', 'del', 'y', 'e', 'o', 'u',
        'un', 'una', 'unos', 'unas', 'para', 'por', 'con', 'sin',
        'en', 'a', 'al', 'sobre', 'entre', 'desde', 'hasta'
    }

    # Sinónimos ocupacionales Argentina-España
    SINONIMOS = {
        'programador': ['desarrollador', 'developer'],
        'desarrollador': ['programador', 'developer'],
        'contador': ['contable', 'accountant'],
        'vendedor': ['comercial', 'sales'],
        'administrativo': ['oficinista', 'clerk'],
        'gerente': ['director', 'manager', 'jefe'],
        'analista': ['analyst', 'especialista'],
        'técnico': ['technician', 'tech'],
        'ingeniero': ['engineer', 'ing'],
        'asistente': ['assistant', 'ayudante'],
        'encargado': ['responsable', 'supervisor'],
    }

    @staticmethod
    def normalizar(texto):
        """Normaliza texto para matching"""
        if pd.isna(texto) or not texto:
            return ""

        # Convertir a minúsculas
        texto = texto.lower().strip()

        # Remover acentos
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join([c for c in texto if not unicodedata.combining(c)])

        # Remover caracteres especiales, mantener espacios
        texto = re.sub(r'[^a-z0-9\s]', ' ', texto)

        # Remover múltiples espacios
        texto = re.sub(r'\s+', ' ', texto).strip()

        return texto

    @staticmethod
    def tokenizar_y_limpiar(texto):
        """Tokeniza y remueve stopwords"""
        tokens = NormalizadorTextoES.normalizar(texto).split()
        tokens_limpios = [t for t in tokens if t not in NormalizadorTextoES.STOPWORDS_ES]
        return tokens_limpios

    @staticmethod
    def expandir_sinonimos(texto):
        """Expande texto con sinónimos"""
        tokens = NormalizadorTextoES.tokenizar_y_limpiar(texto)
        tokens_expandidos = set(tokens)

        for token in tokens:
            if token in NormalizadorTextoES.SINONIMOS:
                tokens_expandidos.update(NormalizadorTextoES.SINONIMOS[token])

        return ' '.join(sorted(tokens_expandidos))


class IntegradorESCOSemantico:
    """Integrador semántico de ZonaJobs con ESCO"""

    def __init__(self):
        self.zonajobs_df = None
        self.esco_ocupaciones = {}
        self.esco_skills = {}
        self.ocupacion_skills = {}
        self.resultados = []

        print("=" * 80)
        print("INTEGRACIÓN SEMÁNTICA ZONAJOBS + ESCO")
        print("=" * 80)

    def cargar_zonajobs(self):
        """Carga datos de ZonaJobs"""
        print("\n[PASO 1] CARGANDO DATOS DE ZONAJOBS")
        print("-" * 80)

        archivos_csv = list(ZONAJOBS_DATA_DIR.glob("zonajobs_todas_*.csv"))

        if not archivos_csv:
            print("[ERROR] No se encontraron archivos de ZonaJobs")
            return False

        ultimo_csv = max(archivos_csv, key=lambda x: x.stat().st_mtime)
        print(f"[LOAD] Archivo: {ultimo_csv.name}")

        self.zonajobs_df = pd.read_csv(ultimo_csv)
        print(f"[OK] Cargadas {len(self.zonajobs_df)} ofertas")
        print(f"[OK] Campos: {len(self.zonajobs_df.columns)}")

        # Mostrar algunas ofertas de muestra
        print("\n[MUESTRA] Primeros 5 títulos:")
        for idx, titulo in enumerate(self.zonajobs_df['titulo'].head(5), 1):
            print(f"  {idx}. {titulo}")

        return True

    def cargar_esco_consolidado(self):
        """Carga ocupaciones ESCO con códigos ISCO"""
        print("\n[PASO 2] CARGANDO OCUPACIONES ESCO CONSOLIDADAS")
        print("-" * 80)

        # Intentar cargar el archivo con ISCO completo primero
        esco_path_completo = ESCO_DATA_DIR / "esco_ocupaciones_con_isco_completo.json"
        esco_path_consolidado = ESCO_DATA_DIR / "esco_consolidado_con_isco.json"

        if esco_path_completo.exists():
            esco_path = esco_path_completo
            print(f"[INFO] Usando archivo con ISCO completo extraído del RDF")
        elif esco_path_consolidado.exists():
            esco_path = esco_path_consolidado
            print(f"[WARN] Usando archivo consolidado (códigos ISCO limitados)")
        else:
            print(f"[ERROR] No se encontraron archivos de ESCO")
            return False

        print(f"[LOAD] {esco_path.name}")

        with open(esco_path, 'r', encoding='utf-8') as f:
            self.esco_ocupaciones = json.load(f)

        print(f"[OK] Cargadas {len(self.esco_ocupaciones)} ocupaciones ESCO")

        # Estadísticas de ISCO
        con_isco_4d = sum(1 for occ in self.esco_ocupaciones.values()
                          if occ.get('codigo_isco_4d'))

        print(f"[INFO] Ocupaciones con ISCO 4 dígitos: {con_isco_4d}")

        # Mostrar muestra
        print("\n[MUESTRA] Primeras 3 ocupaciones:")
        for idx, (esco_id, occ) in enumerate(list(self.esco_ocupaciones.items())[:3], 1):
            print(f"  {idx}. {occ.get('label_es', 'N/A')} (ISCO: {occ.get('codigo_isco_4d', 'N/A')})")

        return True

    def cargar_esco_skills(self):
        """Carga skills de ESCO"""
        print("\n[PASO 3] CARGANDO SKILLS ESCO")
        print("-" * 80)

        # Cargar información de skills
        skills_info_path = ESCO_DATA_DIR / "esco_skills_info.json"

        if skills_info_path.exists():
            print(f"[LOAD] {skills_info_path.name}")
            with open(skills_info_path, 'r', encoding='utf-8') as f:
                self.esco_skills = json.load(f)
            print(f"[OK] Cargados {len(self.esco_skills)} skills")
        else:
            print("[WARN] No se encontró archivo de skills")

        # Cargar relaciones ocupación-skills
        relaciones_path = ESCO_DATA_DIR / "esco_ocupaciones_skills_relaciones.json"

        if relaciones_path.exists():
            print(f"[LOAD] {relaciones_path.name}")
            with open(relaciones_path, 'r', encoding='utf-8') as f:
                self.ocupacion_skills = json.load(f)
            print(f"[OK] Cargadas relaciones para {len(self.ocupacion_skills)} ocupaciones")

            # Estadísticas
            total_skills = sum(len(occ.get('skills_esenciales', [])) +
                              len(occ.get('skills_opcionales', []))
                              for occ in self.ocupacion_skills.values())
            print(f"[INFO] Total relaciones ocupación-skill: {total_skills}")
        else:
            print("[WARN] No se encontró archivo de relaciones")

        return True

    def calcular_similitud_semantica(self, texto1, texto2):
        """
        Calcula similitud semántica entre dos textos en español

        Combina:
        - Similitud de texto normalizado
        - Similitud con expansión de sinónimos
        - Coincidencia de tokens clave
        """
        # Normalizar textos
        norm1 = NormalizadorTextoES.normalizar(texto1)
        norm2 = NormalizadorTextoES.normalizar(texto2)

        # Similitud básica
        sim_basica = SequenceMatcher(None, norm1, norm2).ratio()

        # Similitud con tokens
        tokens1 = set(NormalizadorTextoES.tokenizar_y_limpiar(texto1))
        tokens2 = set(NormalizadorTextoES.tokenizar_y_limpiar(texto2))

        if not tokens1 or not tokens2:
            return sim_basica

        # Jaccard similarity de tokens
        interseccion = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        sim_tokens = interseccion / union if union > 0 else 0

        # Similitud con sinónimos expandidos
        exp1 = NormalizadorTextoES.expandir_sinonimos(texto1)
        exp2 = NormalizadorTextoES.expandir_sinonimos(texto2)
        sim_sinonimos = SequenceMatcher(None, exp1, exp2).ratio()

        # Score combinado (ponderado)
        score_final = (
            sim_basica * 0.3 +
            sim_tokens * 0.4 +
            sim_sinonimos * 0.3
        )

        return score_final

    def encontrar_mejor_match(self, titulo_zonajobs, threshold=0.5, top_n=5):
        """
        Encuentra las mejores ocupaciones ESCO para un título de ZonaJobs

        Args:
            titulo_zonajobs: Título de la oferta
            threshold: Umbral mínimo de similitud
            top_n: Cantidad de mejores matches a retornar

        Returns:
            Lista de matches ordenados por similitud
        """
        if not titulo_zonajobs or pd.isna(titulo_zonajobs):
            return []

        matches = []

        for esco_id, occ_data in self.esco_ocupaciones.items():
            label_es = occ_data.get('label_es', '')

            if not label_es:
                continue

            # Calcular similitud
            similitud = self.calcular_similitud_semantica(titulo_zonajobs, label_es)

            # También comparar con labels alternativos
            alt_labels = occ_data.get('alt_labels_es', [])
            similitudes_alt = [
                self.calcular_similitud_semantica(titulo_zonajobs, alt_label)
                for alt_label in alt_labels
                if alt_label
            ]

            # Usar la mejor similitud
            if similitudes_alt:
                similitud = max(similitud, max(similitudes_alt))

            if similitud >= threshold:
                matches.append({
                    'esco_id': esco_id,
                    'esco_uri': occ_data.get('uri', ''),
                    'esco_label_es': label_es,
                    'esco_label_en': occ_data.get('label_en', ''),
                    'codigo_isco_4d': occ_data.get('codigo_isco_4d'),
                    'codigo_isco_2d': occ_data.get('codigo_isco_2d'),
                    'codigo_isco_1d': occ_data.get('codigo_isco_1d'),
                    'similitud': round(similitud, 4)
                })

        # Ordenar por similitud descendente
        matches_ordenados = sorted(matches, key=lambda x: x['similitud'], reverse=True)

        return matches_ordenados[:top_n]

    def obtener_skills_para_ocupacion(self, esco_id):
        """Obtiene skills asociadas a una ocupación ESCO"""
        if esco_id not in self.ocupacion_skills:
            return {'esenciales': [], 'opcionales': []}

        occ_data = self.ocupacion_skills[esco_id]

        # Obtener IDs de skills
        skill_ids_esenciales = occ_data.get('skills_esenciales', [])
        skill_ids_opcionales = occ_data.get('skills_opcionales', [])

        # Resolver labels de skills
        skills_esenciales = []
        for skill_id in skill_ids_esenciales[:10]:  # Limitar a 10 por tipo
            if skill_id in self.esco_skills:
                skill_info = self.esco_skills[skill_id]
                labels = skill_info.get('labels', {})
                label_es = labels.get('es', labels.get('en', skill_id))
                skills_esenciales.append({
                    'id': skill_id,
                    'label': label_es
                })

        skills_opcionales = []
        for skill_id in skill_ids_opcionales[:10]:  # Limitar a 10 por tipo
            if skill_id in self.esco_skills:
                skill_info = self.esco_skills[skill_id]
                labels = skill_info.get('labels', {})
                label_es = labels.get('es', labels.get('en', skill_id))
                skills_opcionales.append({
                    'id': skill_id,
                    'label': label_es
                })

        return {
            'esenciales': skills_esenciales,
            'opcionales': skills_opcionales
        }

    def clasificar_ofertas(self, threshold=0.5):
        """Clasifica todas las ofertas de ZonaJobs con ESCO"""
        print("\n[PASO 4] CLASIFICANDO OFERTAS CON ESCO")
        print("-" * 80)

        if self.zonajobs_df is None or len(self.zonajobs_df) == 0:
            print("[ERROR] No hay datos de ZonaJobs")
            return False

        if not self.esco_ocupaciones:
            print("[ERROR] No hay datos de ESCO")
            return False

        print(f"[PROCESS] Clasificando {len(self.zonajobs_df)} ofertas...")
        print(f"[CONFIG] Threshold de similitud: {threshold}")
        print(f"[CONFIG] Retornando top 3 matches por oferta")

        resultados = []
        clasificadas = 0

        for idx, oferta in self.zonajobs_df.iterrows():
            titulo = oferta['titulo']

            # Encontrar mejores matches
            matches = self.encontrar_mejor_match(titulo, threshold=threshold, top_n=3)

            if matches:
                # Usar el mejor match
                mejor_match = matches[0]

                # Obtener skills para este match
                skills = self.obtener_skills_para_ocupacion(mejor_match['esco_id'])

                resultado = {
                    # Datos de la oferta original
                    'id_oferta': oferta.get('id_oferta'),
                    'titulo_original': titulo,
                    'empresa': oferta.get('empresa'),
                    'localizacion': oferta.get('localizacion'),
                    'modalidad_trabajo': oferta.get('modalidad_trabajo'),
                    'tipo_trabajo': oferta.get('tipo_trabajo'),
                    'fecha_publicacion': oferta.get('fecha_publicacion'),
                    'url_oferta': oferta.get('url_oferta'),

                    # Mejor match ESCO
                    'esco_match_1_id': mejor_match['esco_id'],
                    'esco_match_1_label': mejor_match['esco_label_es'],
                    'esco_match_1_isco_4d': mejor_match['codigo_isco_4d'],
                    'esco_match_1_isco_2d': mejor_match['codigo_isco_2d'],
                    'esco_match_1_similitud': mejor_match['similitud'],

                    # Skills esenciales (top 5)
                    'skills_esenciales_top5': '; '.join([s['label'] for s in skills['esenciales'][:5]]),
                    'skills_esenciales_count': len(skills['esenciales']),

                    # Skills opcionales (top 5)
                    'skills_opcionales_top5': '; '.join([s['label'] for s in skills['opcionales'][:5]]),
                    'skills_opcionales_count': len(skills['opcionales']),

                    # Matches alternativos
                    'esco_match_2_label': matches[1]['esco_label_es'] if len(matches) > 1 else None,
                    'esco_match_2_similitud': matches[1]['similitud'] if len(matches) > 1 else None,
                    'esco_match_3_label': matches[2]['esco_label_es'] if len(matches) > 2 else None,
                    'esco_match_3_similitud': matches[2]['similitud'] if len(matches) > 2 else None,

                    # Metadata
                    'fecha_clasificacion': datetime.now().isoformat(),
                    'clasificada': True
                }

                clasificadas += 1
            else:
                # Sin match
                resultado = {
                    'id_oferta': oferta.get('id_oferta'),
                    'titulo_original': titulo,
                    'empresa': oferta.get('empresa'),
                    'localizacion': oferta.get('localizacion'),
                    'modalidad_trabajo': oferta.get('modalidad_trabajo'),
                    'tipo_trabajo': oferta.get('tipo_trabajo'),
                    'fecha_publicacion': oferta.get('fecha_publicacion'),
                    'url_oferta': oferta.get('url_oferta'),
                    'esco_match_1_id': None,
                    'esco_match_1_label': None,
                    'esco_match_1_isco_4d': None,
                    'esco_match_1_isco_2d': None,
                    'esco_match_1_similitud': 0.0,
                    'skills_esenciales_top5': None,
                    'skills_esenciales_count': 0,
                    'skills_opcionales_top5': None,
                    'skills_opcionales_count': 0,
                    'esco_match_2_label': None,
                    'esco_match_2_similitud': None,
                    'esco_match_3_label': None,
                    'esco_match_3_similitud': None,
                    'fecha_clasificacion': datetime.now().isoformat(),
                    'clasificada': False
                }

            resultados.append(resultado)

            # Mostrar progreso
            if (idx + 1) % 10 == 0:
                print(f"  Progreso: {idx + 1}/{len(self.zonajobs_df)} ({clasificadas} clasificadas)")

        self.resultados = pd.DataFrame(resultados)

        print(f"\n[OK] Clasificación completada")
        print(f"  Total ofertas: {len(self.resultados)}")
        print(f"  Clasificadas: {clasificadas} ({clasificadas/len(self.resultados)*100:.1f}%)")
        print(f"  Sin clasificar: {len(self.resultados) - clasificadas}")

        return True

    def guardar_resultados(self):
        """Guarda resultados en múltiples formatos"""
        print("\n[PASO 5] GUARDANDO RESULTADOS")
        print("-" * 80)

        if self.resultados is None or len(self.resultados) == 0:
            print("[ERROR] No hay resultados para guardar")
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. CSV principal
        csv_path = OUTPUT_DIR / f"zonajobs_esco_enriquecida_{timestamp}.csv"
        self.resultados.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"[SAVE] CSV: {csv_path.name}")

        # 2. JSON completo
        json_path = OUTPUT_DIR / f"zonajobs_esco_enriquecida_{timestamp}.json"
        self.resultados.to_json(json_path, orient='records', force_ascii=False, indent=2)
        print(f"[SAVE] JSON: {json_path.name}")

        # 3. Excel con análisis
        excel_path = OUTPUT_DIR / f"zonajobs_esco_analisis_{timestamp}.xlsx"

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Hoja 1: Ofertas enriquecidas
            self.resultados.to_excel(writer, sheet_name='Ofertas Enriquecidas', index=False)

            # Hoja 2: Estadísticas de clasificación
            clasificadas = self.resultados[self.resultados['clasificada'] == True]

            if len(clasificadas) > 0:
                # Top ocupaciones ESCO
                top_ocupaciones = clasificadas['esco_match_1_label'].value_counts().head(20)
                top_ocupaciones.to_excel(writer, sheet_name='Top Ocupaciones ESCO')

                # Distribución por ISCO
                if 'esco_match_1_isco_2d' in clasificadas.columns:
                    dist_isco = clasificadas['esco_match_1_isco_2d'].value_counts().sort_index()
                    dist_isco.to_excel(writer, sheet_name='Distribución ISCO')

                # Distribución de similitudes
                stats_similitud = clasificadas['esco_match_1_similitud'].describe()
                stats_similitud.to_excel(writer, sheet_name='Stats Similitud')

        print(f"[SAVE] Excel: {excel_path.name}")

        # 4. Reporte de estadísticas
        self.generar_reporte_estadisticas()

        print(f"\n[OK] Todos los archivos guardados en:")
        print(f"  {OUTPUT_DIR}")

        return True

    def generar_reporte_estadisticas(self):
        """Genera reporte detallado de estadísticas"""
        print("\n" + "=" * 80)
        print("ESTADÍSTICAS DE INTEGRACIÓN")
        print("=" * 80)

        total = len(self.resultados)
        clasificadas = self.resultados['clasificada'].sum()
        sin_clasificar = total - clasificadas

        print(f"\n📊 RESUMEN GENERAL:")
        print(f"  Total ofertas procesadas: {total}")
        print(f"  Clasificadas con ESCO: {clasificadas} ({clasificadas/total*100:.1f}%)")
        print(f"  Sin clasificar: {sin_clasificar} ({sin_clasificar/total*100:.1f}%)")

        if clasificadas > 0:
            df_clasificadas = self.resultados[self.resultados['clasificada'] == True]

            print(f"\n🎯 CALIDAD DE MATCHING:")
            print(f"  Similitud promedio: {df_clasificadas['esco_match_1_similitud'].mean():.3f}")
            print(f"  Similitud mediana: {df_clasificadas['esco_match_1_similitud'].median():.3f}")
            print(f"  Similitud mínima: {df_clasificadas['esco_match_1_similitud'].min():.3f}")
            print(f"  Similitud máxima: {df_clasificadas['esco_match_1_similitud'].max():.3f}")

            print(f"\n👔 TOP 10 OCUPACIONES ESCO:")
            top_ocupaciones = df_clasificadas['esco_match_1_label'].value_counts().head(10)
            for idx, (ocupacion, count) in enumerate(top_ocupaciones.items(), 1):
                print(f"  {idx:2d}. {ocupacion}: {count} ofertas")

            print(f"\n🏢 TOP 10 CÓDIGOS ISCO (2 dígitos):")
            if 'esco_match_1_isco_2d' in df_clasificadas.columns:
                top_isco = df_clasificadas['esco_match_1_isco_2d'].value_counts().head(10)
                for codigo, count in top_isco.items():
                    print(f"  Grupo {codigo}: {count} ofertas")

            print(f"\n🎓 SKILLS ENRIQUECIDAS:")
            total_con_skills = (df_clasificadas['skills_esenciales_count'] > 0).sum()
            print(f"  Ofertas con skills esenciales: {total_con_skills}")
            if total_con_skills > 0:
                promedio_skills = df_clasificadas[df_clasificadas['skills_esenciales_count'] > 0]['skills_esenciales_count'].mean()
                print(f"  Promedio skills esenciales por oferta: {promedio_skills:.1f}")

        print("\n" + "=" * 80)

    def ejecutar_pipeline_completo(self, threshold=0.5):
        """Ejecuta el pipeline completo de integración"""
        print("\n" + "🚀 " * 20)
        print("PIPELINE DE INTEGRACIÓN ZONAJOBS + ESCO")
        print("🚀 " * 20)

        # Paso 1: Cargar ZonaJobs
        if not self.cargar_zonajobs():
            return False

        # Paso 2: Cargar ESCO ocupaciones
        if not self.cargar_esco_consolidado():
            return False

        # Paso 3: Cargar ESCO skills
        if not self.cargar_esco_skills():
            return False

        # Paso 4: Clasificar
        if not self.clasificar_ofertas(threshold=threshold):
            return False

        # Paso 5: Guardar
        if not self.guardar_resultados():
            return False

        print("\n" + "✅ " * 20)
        print("INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("✅ " * 20)

        return True


def main():
    """Función principal"""
    integrador = IntegradorESCOSemantico()

    # Ejecutar con threshold de 0.4 (más permisivo para POC)
    integrador.ejecutar_pipeline_completo(threshold=0.4)


if __name__ == "__main__":
    main()
