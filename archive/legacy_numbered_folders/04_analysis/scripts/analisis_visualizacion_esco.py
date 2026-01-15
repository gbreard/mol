# -*- coding: utf-8 -*-
"""
Análisis Estadístico y Visualización de Integración ZonaJobs + ESCO
Genera análisis completo, gráficos estáticos y dashboard interactivo
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
from collections import Counter

# Visualizaciones
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para guardar gráficos sin mostrar
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['figure.figsize'] = (12, 8)

# Plotly para dashboards interactivos
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Paths
OUTPUT_DIR = Path(r"D:\OEDE\Webscrapping\data\processed")
CHARTS_DIR = OUTPUT_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)


class AnalizadorESCO:
    """Analizador estadístico y generador de visualizaciones"""

    def __init__(self, csv_path=None):
        """Inicializar con path al CSV o usar el más reciente"""
        if csv_path:
            self.csv_path = Path(csv_path)
        else:
            # Buscar archivo más reciente
            archivos = list(OUTPUT_DIR.glob("zonajobs_esco_enriquecida_*.csv"))
            if not archivos:
                raise FileNotFoundError("No se encontraron archivos de integración")
            self.csv_path = max(archivos, key=lambda x: x.stat().st_mtime)

        print("=" * 80)
        print("ANÁLISIS ESTADÍSTICO Y VISUALIZACIÓN - ZONAJOBS + ESCO")
        print("=" * 80)
        print(f"\n[LOAD] Archivo: {self.csv_path.name}")

        self.df = pd.read_csv(self.csv_path)
        self.df_clasificadas = self.df[self.df['clasificada'] == True].copy()

        print(f"[OK] Cargadas {len(self.df)} ofertas")
        print(f"[OK] Clasificadas: {len(self.df_clasificadas)} ({len(self.df_clasificadas)/len(self.df)*100:.1f}%)")

        self.stats = {}
        self.figuras = []

    def analisis_general(self):
        """Análisis estadístico general"""
        print("\n[1] ANÁLISIS ESTADÍSTICO GENERAL")
        print("-" * 80)

        total = len(self.df)
        clasificadas = len(self.df_clasificadas)
        sin_clasificar = total - clasificadas

        self.stats['general'] = {
            'total_ofertas': total,
            'clasificadas': clasificadas,
            'sin_clasificar': sin_clasificar,
            'tasa_clasificacion': clasificadas / total * 100
        }

        if clasificadas > 0:
            self.stats['similitud'] = {
                'promedio': self.df_clasificadas['esco_match_1_similitud'].mean(),
                'mediana': self.df_clasificadas['esco_match_1_similitud'].median(),
                'std': self.df_clasificadas['esco_match_1_similitud'].std(),
                'min': self.df_clasificadas['esco_match_1_similitud'].min(),
                'max': self.df_clasificadas['esco_match_1_similitud'].max(),
                'q25': self.df_clasificadas['esco_match_1_similitud'].quantile(0.25),
                'q75': self.df_clasificadas['esco_match_1_similitud'].quantile(0.75)
            }

        print(f"  Total ofertas: {total}")
        print(f"  Clasificadas: {clasificadas} ({self.stats['general']['tasa_clasificacion']:.1f}%)")
        print(f"  Sin clasificar: {sin_clasificar}")

        if clasificadas > 0:
            print(f"\n  Similitud:")
            print(f"    Promedio: {self.stats['similitud']['promedio']:.3f}")
            print(f"    Mediana: {self.stats['similitud']['mediana']:.3f}")
            print(f"    Desv. Est.: {self.stats['similitud']['std']:.3f}")
            print(f"    Min-Max: {self.stats['similitud']['min']:.3f} - {self.stats['similitud']['max']:.3f}")

    def analisis_ocupaciones(self):
        """Análisis por ocupaciones ESCO"""
        print("\n[2] ANÁLISIS POR OCUPACIONES ESCO")
        print("-" * 80)

        if len(self.df_clasificadas) == 0:
            print("  [SKIP] No hay ofertas clasificadas")
            return

        # Distribución de ocupaciones
        ocupaciones = self.df_clasificadas['esco_match_1_label'].value_counts()

        self.stats['ocupaciones'] = {
            'total_unicas': len(ocupaciones),
            'top_10': ocupaciones.head(10).to_dict(),
            'promedio_ofertas_por_ocupacion': ocupaciones.mean(),
            'mediana_ofertas_por_ocupacion': ocupaciones.median()
        }

        print(f"  Ocupaciones únicas identificadas: {len(ocupaciones)}")
        print(f"  Promedio ofertas por ocupación: {ocupaciones.mean():.1f}")
        print(f"  Mediana ofertas por ocupación: {ocupaciones.median():.1f}")

        print(f"\n  Top 10 Ocupaciones:")
        for idx, (occ, count) in enumerate(ocupaciones.head(10).items(), 1):
            print(f"    {idx:2d}. {occ}: {count} ofertas")

    def analisis_isco(self):
        """Análisis por códigos ISCO"""
        print("\n[3] ANÁLISIS POR CÓDIGOS ISCO")
        print("-" * 80)

        if len(self.df_clasificadas) == 0:
            print("  [SKIP] No hay ofertas clasificadas")
            return

        # Filtrar ofertas con ISCO
        con_isco = self.df_clasificadas[self.df_clasificadas['esco_match_1_isco_4d'].notna()].copy()

        if len(con_isco) == 0:
            print("  [WARN] No hay ofertas con códigos ISCO")
            return

        # Calcular ISCO 1D si no existe
        if 'esco_match_1_isco_1d' not in con_isco.columns:
            con_isco['esco_match_1_isco_1d'] = con_isco['esco_match_1_isco_4d'].astype(str).str[0]

        # Distribución por nivel ISCO
        isco_4d = con_isco['esco_match_1_isco_4d'].value_counts()
        isco_2d = con_isco['esco_match_1_isco_2d'].value_counts().sort_index()
        isco_1d = con_isco['esco_match_1_isco_1d'].value_counts().sort_index()

        self.stats['isco'] = {
            'ofertas_con_isco': len(con_isco),
            'codigos_isco_4d_unicos': len(isco_4d),
            'codigos_isco_2d_unicos': len(isco_2d),
            'codigos_isco_1d_unicos': len(isco_1d),
            'distribucion_1d': isco_1d.to_dict(),
            'distribucion_2d': isco_2d.to_dict(),
            'top_isco_4d': isco_4d.head(10).to_dict()
        }

        print(f"  Ofertas con código ISCO: {len(con_isco)} ({len(con_isco)/len(self.df_clasificadas)*100:.1f}%)")
        print(f"  Códigos ISCO únicos:")
        print(f"    1 dígito: {len(isco_1d)} grupos principales")
        print(f"    2 dígitos: {len(isco_2d)} subgrupos")
        print(f"    4 dígitos: {len(isco_4d)} ocupaciones específicas")

        print(f"\n  Distribución por Grupo Principal (1 dígito):")
        for codigo, count in isco_1d.items():
            print(f"    Grupo {codigo}: {count} ofertas ({count/len(con_isco)*100:.1f}%)")

        print(f"\n  Top 10 Grupos ISCO (2 dígitos):")
        for idx, (codigo, count) in enumerate(isco_2d.head(10).items(), 1):
            print(f"    {idx:2d}. Grupo {codigo}: {count} ofertas")

    def analisis_skills(self):
        """Análisis de skills y competencias"""
        print("\n[4] ANÁLISIS DE SKILLS Y COMPETENCIAS")
        print("-" * 80)

        if len(self.df_clasificadas) == 0:
            print("  [SKIP] No hay ofertas clasificadas")
            return

        con_skills = self.df_clasificadas[self.df_clasificadas['skills_esenciales_count'] > 0].copy()

        self.stats['skills'] = {
            'ofertas_con_skills': len(con_skills),
            'promedio_skills_esenciales': con_skills['skills_esenciales_count'].mean(),
            'mediana_skills_esenciales': con_skills['skills_esenciales_count'].median(),
            'max_skills_esenciales': con_skills['skills_esenciales_count'].max()
        }

        print(f"  Ofertas enriquecidas con skills: {len(con_skills)} ({len(con_skills)/len(self.df_clasificadas)*100:.1f}%)")

        if len(con_skills) > 0:
            print(f"  Skills esenciales por oferta:")
            print(f"    Promedio: {self.stats['skills']['promedio_skills_esenciales']:.1f}")
            print(f"    Mediana: {self.stats['skills']['mediana_skills_esenciales']:.1f}")
            print(f"    Máximo: {int(self.stats['skills']['max_skills_esenciales'])}")

            # Extraer skills más frecuentes
            all_skills = []
            for skills_str in con_skills['skills_esenciales_top5'].dropna():
                if pd.notna(skills_str):
                    skills = skills_str.split('; ')
                    all_skills.extend(skills)

            if all_skills:
                skill_freq = Counter(all_skills)
                self.stats['skills']['top_skills'] = dict(skill_freq.most_common(15))

                print(f"\n  Top 15 Skills Más Demandadas:")
                for idx, (skill, freq) in enumerate(skill_freq.most_common(15), 1):
                    print(f"    {idx:2d}. {skill}: {freq} veces")

    def analisis_modalidad(self):
        """Análisis por modalidad de trabajo"""
        print("\n[5] ANÁLISIS POR MODALIDAD DE TRABAJO")
        print("-" * 80)

        modalidad_dist = self.df['modalidad_trabajo'].value_counts()

        self.stats['modalidad'] = {
            'distribucion': modalidad_dist.to_dict()
        }

        print(f"  Distribución por modalidad:")
        for mod, count in modalidad_dist.items():
            print(f"    {mod}: {count} ofertas ({count/len(self.df)*100:.1f}%)")

        # Clasificación por modalidad
        if len(self.df_clasificadas) > 0:
            clasificacion_por_mod = pd.crosstab(
                self.df['modalidad_trabajo'],
                self.df['clasificada']
            )

            print(f"\n  Tasa de clasificación por modalidad:")
            for mod in modalidad_dist.index:
                if mod in clasificacion_por_mod.index:
                    total_mod = clasificacion_por_mod.loc[mod].sum()
                    clasificadas_mod = clasificacion_por_mod.loc[mod, True] if True in clasificacion_por_mod.columns else 0
                    tasa = clasificadas_mod / total_mod * 100 if total_mod > 0 else 0
                    print(f"    {mod}: {tasa:.1f}%")

    def analisis_geografico(self):
        """Análisis por localización geográfica"""
        print("\n[6] ANÁLISIS POR LOCALIZACIÓN GEOGRÁFICA")
        print("-" * 80)

        if 'localizacion' not in self.df.columns:
            print("  [SKIP] No hay datos de localización")
            return

        # Limpiar y agrupar localizaciones
        loc_dist = self.df['localizacion'].value_counts()

        # Agrupar Capital Federal vs GBA vs Otras
        def categorizar_localizacion(loc):
            if pd.isna(loc):
                return 'No especificado'
            loc_lower = str(loc).lower()
            if 'capital' in loc_lower or 'caba' in loc_lower or 'buenos aires' in loc_lower:
                return 'Capital Federal / CABA'
            elif 'gba' in loc_lower or 'gran buenos aires' in loc_lower:
                return 'GBA'
            else:
                return 'Otras localidades'

        self.df['region'] = self.df['localizacion'].apply(categorizar_localizacion)
        region_dist = self.df['region'].value_counts()

        self.stats['geografico'] = {
            'localizaciones_unicas': len(loc_dist),
            'distribucion_localidades': loc_dist.head(10).to_dict(),
            'distribucion_regiones': region_dist.to_dict()
        }

        print(f"  Localizaciones únicas: {len(loc_dist)}")
        print(f"\n  Top 10 Localidades:")
        for idx, (loc, count) in enumerate(loc_dist.head(10).items(), 1):
            print(f"    {idx:2d}. {loc}: {count} ofertas ({count/len(self.df)*100:.1f}%)")

        print(f"\n  Distribución por Región:")
        for region, count in region_dist.items():
            print(f"    {region}: {count} ofertas ({count/len(self.df)*100:.1f}%)")

        # Cruce con ocupaciones (si hay clasificadas)
        if len(self.df_clasificadas) > 0:
            df_con_region = self.df_clasificadas.copy()
            df_con_region['region'] = df_con_region['localizacion'].apply(categorizar_localizacion)

            print(f"\n  Top 5 Ocupaciones por Región:")
            for region in region_dist.index:
                ofertas_region = df_con_region[df_con_region['region'] == region]
                if len(ofertas_region) > 0:
                    top_occ = ofertas_region['esco_match_1_label'].value_counts().head(3)
                    print(f"\n    {region}:")
                    for occ, count in top_occ.items():
                        print(f"      - {occ}: {count} ofertas")

    def analisis_empresas(self):
        """Análisis por empresas reclutadoras"""
        print("\n[7] ANÁLISIS POR EMPRESAS")
        print("-" * 80)

        if 'empresa' not in self.df.columns:
            print("  [SKIP] No hay datos de empresas")
            return

        empresa_dist = self.df['empresa'].value_counts()

        # Identificar confidenciales
        confidenciales = self.df['empresa'].str.contains('confidencial', case=False, na=False).sum()
        con_nombre = len(self.df) - confidenciales

        self.stats['empresas'] = {
            'empresas_unicas': len(empresa_dist),
            'ofertas_confidenciales': confidenciales,
            'ofertas_con_nombre': con_nombre,
            'top_10_empresas': empresa_dist.head(10).to_dict()
        }

        print(f"  Empresas únicas: {len(empresa_dist)}")
        print(f"  Ofertas confidenciales: {confidenciales} ({confidenciales/len(self.df)*100:.1f}%)")
        print(f"  Ofertas con nombre: {con_nombre} ({con_nombre/len(self.df)*100:.1f}%)")

        print(f"\n  Top 10 Empresas/Reclutadores:")
        for idx, (emp, count) in enumerate(empresa_dist.head(10).items(), 1):
            print(f"    {idx:2d}. {emp}: {count} ofertas")

        # Cruce con ocupaciones (si hay clasificadas)
        if len(self.df_clasificadas) > 0:
            print(f"\n  Ocupaciones más ofrecidas por Top 3 Empresas:")
            for emp in empresa_dist.head(3).index:
                ofertas_emp = self.df_clasificadas[self.df_clasificadas['empresa'] == emp]
                if len(ofertas_emp) > 0:
                    top_occ = ofertas_emp['esco_match_1_label'].value_counts().head(3)
                    print(f"\n    {emp}:")
                    for occ, count in top_occ.items():
                        print(f"      - {occ}: {count} ofertas")

    def generar_grafico_distribucion_ocupaciones(self):
        """Gráfico: Top 15 Ocupaciones ESCO"""
        print("\n[8] GENERANDO GRÁFICOS...")
        print("-" * 80)

        if len(self.df_clasificadas) == 0:
            print("  [SKIP] No hay datos para graficar")
            return

        # Gráfico 1: Top 15 Ocupaciones
        print("  [1/10] Top 15 Ocupaciones ESCO...")

        ocupaciones = self.df_clasificadas['esco_match_1_label'].value_counts().head(15)

        fig, ax = plt.subplots(figsize=(12, 8))
        ocupaciones.plot(kind='barh', ax=ax, color='steelblue')
        ax.set_xlabel('Cantidad de Ofertas')
        ax.set_ylabel('Ocupación ESCO')
        ax.set_title('Top 15 Ocupaciones ESCO Más Frecuentes', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        plt.tight_layout()

        chart_path = CHARTS_DIR / "01_top_ocupaciones.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_isco_grupos(self):
        """Gráfico: Distribución por Grupos ISCO"""
        print("  [2/10] Distribución por Grupos ISCO...")

        con_isco = self.df_clasificadas[self.df_clasificadas['esco_match_1_isco_2d'].notna()].copy()

        if len(con_isco) == 0:
            print("    [SKIP] No hay datos ISCO")
            return

        isco_2d = con_isco['esco_match_1_isco_2d'].value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(12, 8))
        isco_2d.plot(kind='bar', ax=ax, color='coral')
        ax.set_xlabel('Grupo ISCO (2 dígitos)')
        ax.set_ylabel('Cantidad de Ofertas')
        ax.set_title('Distribución de Ofertas por Grupo ISCO (2 dígitos)', fontsize=14, fontweight='bold')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        plt.tight_layout()

        chart_path = CHARTS_DIR / "02_distribucion_isco.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_similitud(self):
        """Gráfico: Distribución de similitud"""
        print("  [3/10] Distribución de Similitud...")

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Histograma
        axes[0].hist(self.df_clasificadas['esco_match_1_similitud'], bins=20,
                     color='green', alpha=0.7, edgecolor='black')
        axes[0].set_xlabel('Similitud')
        axes[0].set_ylabel('Frecuencia')
        axes[0].set_title('Distribución de Similitud de Matching')
        axes[0].axvline(self.df_clasificadas['esco_match_1_similitud'].mean(),
                        color='red', linestyle='--', label=f'Promedio: {self.df_clasificadas["esco_match_1_similitud"].mean():.3f}')
        axes[0].legend()

        # Boxplot
        axes[1].boxplot(self.df_clasificadas['esco_match_1_similitud'], vert=True)
        axes[1].set_ylabel('Similitud')
        axes[1].set_title('Boxplot de Similitud')
        axes[1].set_xticklabels(['Similitud'])

        plt.tight_layout()

        chart_path = CHARTS_DIR / "03_distribucion_similitud.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_skills(self):
        """Gráfico: Top 15 Skills"""
        print("  [4/10] Top 15 Skills Más Demandadas...")

        if 'top_skills' not in self.stats.get('skills', {}):
            print("    [SKIP] No hay datos de skills")
            return

        top_skills = self.stats['skills']['top_skills']
        skills_df = pd.Series(top_skills).head(15).sort_values()

        fig, ax = plt.subplots(figsize=(12, 8))
        skills_df.plot(kind='barh', ax=ax, color='purple')
        ax.set_xlabel('Frecuencia')
        ax.set_ylabel('Skill')
        ax.set_title('Top 15 Skills Esenciales Más Demandadas', fontsize=14, fontweight='bold')
        plt.tight_layout()

        chart_path = CHARTS_DIR / "04_top_skills.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_modalidad(self):
        """Gráfico: Distribución por modalidad"""
        print("  [5/10] Distribución por Modalidad de Trabajo...")

        modalidad_dist = self.df['modalidad_trabajo'].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        ax.pie(modalidad_dist.values, labels=modalidad_dist.index, autopct='%1.1f%%',
               startangle=90, colors=colors)
        ax.set_title('Distribución de Ofertas por Modalidad de Trabajo', fontsize=14, fontweight='bold')
        plt.tight_layout()

        chart_path = CHARTS_DIR / "05_modalidad_trabajo.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_tasa_clasificacion(self):
        """Gráfico: Tasa de clasificación"""
        print("  [6/10] Tasa de Clasificación...")

        clasificadas = len(self.df_clasificadas)
        sin_clasificar = len(self.df) - clasificadas

        fig, ax = plt.subplots(figsize=(8, 6))
        sizes = [clasificadas, sin_clasificar]
        labels = [f'Clasificadas\n({clasificadas})', f'Sin clasificar\n({sin_clasificar})']
        colors = ['#90EE90', '#FFB6C1']
        explode = (0.1, 0)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
               autopct='%1.1f%%', shadow=True, startangle=90)
        ax.set_title('Tasa de Clasificación con ESCO', fontsize=14, fontweight='bold')
        plt.tight_layout()

        chart_path = CHARTS_DIR / "06_tasa_clasificacion.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_isco_jerarquia(self):
        """Gráfico: Jerarquía ISCO (1 dígito)"""
        print("  [7/10] Jerarquía ISCO (Grupos Principales)...")

        con_isco = self.df_clasificadas[self.df_clasificadas['esco_match_1_isco_4d'].notna()].copy()

        if len(con_isco) == 0:
            print("    [SKIP] No hay datos ISCO")
            return

        # Calcular ISCO 1D si no existe
        if 'esco_match_1_isco_1d' not in con_isco.columns:
            con_isco['esco_match_1_isco_1d'] = con_isco['esco_match_1_isco_4d'].astype(str).str[0]

        isco_1d = con_isco['esco_match_1_isco_1d'].value_counts().sort_index()

        # Nombres de grupos ISCO principales
        isco_nombres = {
            '1': 'Directores y gerentes',
            '2': 'Profesionales científicos e intelectuales',
            '3': 'Técnicos y profesionales de nivel medio',
            '4': 'Personal de apoyo administrativo',
            '5': 'Trabajadores de servicios y ventas',
            '6': 'Agricultores y trabajadores agropecuarios',
            '7': 'Oficiales, operarios y artesanos',
            '8': 'Operadores de instalaciones y máquinas',
            '9': 'Ocupaciones elementales'
        }

        labels = [f"{codigo}: {isco_nombres.get(codigo, 'Otro')}" for codigo in isco_1d.index]

        fig, ax = plt.subplots(figsize=(10, 8))
        bars = ax.bar(range(len(isco_1d)), isco_1d.values, color='teal')
        ax.set_xticks(range(len(isco_1d)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_xlabel('Grupo Principal ISCO')
        ax.set_ylabel('Cantidad de Ofertas')
        ax.set_title('Distribución por Grupos Principales ISCO (1 dígito)', fontsize=14, fontweight='bold')

        # Añadir valores sobre las barras
        for i, (bar, val) in enumerate(zip(bars, isco_1d.values)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                   str(int(val)), ha='center', va='bottom')

        plt.tight_layout()

        chart_path = CHARTS_DIR / "07_isco_grupos_principales.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_skills_por_ocupacion(self):
        """Gráfico: Skills por ocupación"""
        print("  [8/10] Skills por Ocupación...")

        con_skills = self.df_clasificadas[self.df_clasificadas['skills_esenciales_count'] > 0].copy()

        if len(con_skills) == 0:
            print("    [SKIP] No hay datos de skills")
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(con_skills['skills_esenciales_count'], bins=range(0, int(con_skills['skills_esenciales_count'].max())+2),
                color='orange', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Cantidad de Skills Esenciales')
        ax.set_ylabel('Frecuencia')
        ax.set_title('Distribución de Skills Esenciales por Oferta', fontsize=14, fontweight='bold')
        ax.axvline(con_skills['skills_esenciales_count'].mean(), color='red',
                   linestyle='--', label=f'Promedio: {con_skills["skills_esenciales_count"].mean():.1f}')
        ax.legend()
        plt.tight_layout()

        chart_path = CHARTS_DIR / "08_skills_por_oferta.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_geografico(self):
        """Gráfico: Distribución geográfica"""
        print("  [9/10] Distribución Geográfica...")

        if 'region' not in self.df.columns:
            print("    [SKIP] No hay datos geográficos procesados")
            return

        region_dist = self.df['region'].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        wedges, texts, autotexts = ax.pie(region_dist.values, labels=region_dist.index,
                                           autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title('Distribución Geográfica de Ofertas', fontsize=14, fontweight='bold')

        # Mejorar legibilidad
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        plt.tight_layout()

        chart_path = CHARTS_DIR / "09_distribucion_geografica.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_grafico_empresas(self):
        """Gráfico: Top empresas reclutadoras"""
        print("  [10/10] Top Empresas Reclutadoras...")

        if 'empresa' not in self.df.columns:
            print("    [SKIP] No hay datos de empresas")
            return

        # Top 10 empresas
        empresa_dist = self.df['empresa'].value_counts().head(10)

        fig, ax = plt.subplots(figsize=(12, 8))
        empresa_dist.plot(kind='barh', ax=ax, color='#9B59B6')
        ax.set_xlabel('Cantidad de Ofertas')
        ax.set_ylabel('Empresa / Reclutador')
        ax.set_title('Top 10 Empresas/Reclutadores con Más Ofertas', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        plt.tight_layout()

        chart_path = CHARTS_DIR / "10_top_empresas.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Guardado: {chart_path.name}")

    def generar_dashboard_interactivo(self):
        """Genera dashboard interactivo con Plotly"""
        print("\n[9] GENERANDO DASHBOARD INTERACTIVO")
        print("-" * 80)

        if len(self.df_clasificadas) == 0:
            print("  [SKIP] No hay datos clasificados")
            return

        # Crear figura con subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Top 10 Ocupaciones ESCO',
                'Distribución ISCO (2 dígitos)',
                'Distribución de Similitud',
                'Modalidad de Trabajo',
                'Tasa de Clasificación',
                'Top 10 Skills'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "histogram"}, {"type": "pie"}],
                [{"type": "pie"}, {"type": "bar"}]
            ]
        )

        # 1. Top Ocupaciones
        ocupaciones = self.df_clasificadas['esco_match_1_label'].value_counts().head(10)
        fig.add_trace(
            go.Bar(x=ocupaciones.values, y=ocupaciones.index, orientation='h',
                   marker_color='steelblue', name='Ocupaciones'),
            row=1, col=1
        )

        # 2. ISCO 2D
        con_isco = self.df_clasificadas[self.df_clasificadas['esco_match_1_isco_2d'].notna()]
        if len(con_isco) > 0:
            isco_2d = con_isco['esco_match_1_isco_2d'].value_counts().head(10).sort_values()
            fig.add_trace(
                go.Bar(x=isco_2d.values, y=isco_2d.index, orientation='h',
                       marker_color='coral', name='ISCO'),
                row=1, col=2
            )

        # 3. Similitud
        fig.add_trace(
            go.Histogram(x=self.df_clasificadas['esco_match_1_similitud'],
                        nbinsx=20, marker_color='green', name='Similitud'),
            row=2, col=1
        )

        # 4. Modalidad
        modalidad_dist = self.df['modalidad_trabajo'].value_counts()
        fig.add_trace(
            go.Pie(labels=modalidad_dist.index, values=modalidad_dist.values,
                   name='Modalidad'),
            row=2, col=2
        )

        # 5. Tasa clasificación
        clasificadas = len(self.df_clasificadas)
        sin_clasificar = len(self.df) - clasificadas
        fig.add_trace(
            go.Pie(labels=['Clasificadas', 'Sin clasificar'],
                   values=[clasificadas, sin_clasificar],
                   marker_colors=['#90EE90', '#FFB6C1'],
                   name='Clasificación'),
            row=3, col=1
        )

        # 6. Top Skills
        if 'top_skills' in self.stats.get('skills', {}):
            top_skills = pd.Series(self.stats['skills']['top_skills']).head(10).sort_values()
            fig.add_trace(
                go.Bar(x=top_skills.values, y=top_skills.index, orientation='h',
                       marker_color='purple', name='Skills'),
                row=3, col=2
            )

        # Layout
        fig.update_layout(
            title_text="Dashboard Interactivo - Integración ZonaJobs + ESCO",
            title_font_size=20,
            showlegend=False,
            height=1200,
            width=1400
        )

        # Guardar
        dashboard_path = CHARTS_DIR / "dashboard_interactivo.html"
        fig.write_html(str(dashboard_path))
        print(f"  [OK] Dashboard guardado: {dashboard_path.name}")
        print(f"  [INFO] Abrir en navegador: {dashboard_path}")

    def generar_informe_html(self):
        """Genera informe HTML completo"""
        print("\n[10] GENERANDO INFORME HTML COMPLETO")
        print("-" * 80)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe de Integración ZonaJobs + ESCO</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ margin: 0; }}
        h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Informe de Integración ZonaJobs + ESCO</h1>
        <p>Análisis Estadístico y Visualización Completa</p>
        <p style="font-size: 14px;">Generado: {timestamp}</p>
    </div>

    <div class="section">
        <h2>1. Resumen Ejecutivo</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{self.stats['general']['total_ofertas']}</div>
                <div class="stat-label">Ofertas Procesadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['general']['clasificadas']}</div>
                <div class="stat-label">Clasificadas con ESCO</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['general']['tasa_clasificacion']:.1f}%</div>
                <div class="stat-label">Tasa de Clasificación</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['similitud']['promedio']:.3f}</div>
                <div class="stat-label">Similitud Promedio</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>2. Distribución de Ocupaciones ESCO</h2>
        <p>Se identificaron <strong>{self.stats['ocupaciones']['total_unicas']}</strong> ocupaciones únicas.</p>
        <img src="charts/01_top_ocupaciones.png" alt="Top Ocupaciones">
    </div>

    <div class="section">
        <h2>3. Análisis por Códigos ISCO</h2>
        <p><strong>{self.stats['isco']['ofertas_con_isco']}</strong> ofertas clasificadas con códigos ISCO.</p>
        <img src="charts/02_distribucion_isco.png" alt="Distribución ISCO">
        <img src="charts/07_isco_grupos_principales.png" alt="Grupos ISCO">
    </div>

    <div class="section">
        <h2>4. Calidad del Matching</h2>
        <img src="charts/03_distribucion_similitud.png" alt="Distribución Similitud">

        <table>
            <tr>
                <th>Métrica</th>
                <th>Valor</th>
            </tr>
            <tr>
                <td>Promedio</td>
                <td>{self.stats['similitud']['promedio']:.3f}</td>
            </tr>
            <tr>
                <td>Mediana</td>
                <td>{self.stats['similitud']['mediana']:.3f}</td>
            </tr>
            <tr>
                <td>Desviación Estándar</td>
                <td>{self.stats['similitud']['std']:.3f}</td>
            </tr>
            <tr>
                <td>Mínimo</td>
                <td>{self.stats['similitud']['min']:.3f}</td>
            </tr>
            <tr>
                <td>Máximo</td>
                <td>{self.stats['similitud']['max']:.3f}</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>5. Skills y Competencias</h2>
        <p><strong>{self.stats['skills']['ofertas_con_skills']}</strong> ofertas enriquecidas con skills esenciales.</p>
        <img src="charts/04_top_skills.png" alt="Top Skills">
        <img src="charts/08_skills_por_oferta.png" alt="Skills por Oferta">
    </div>

    <div class="section">
        <h2>6. Análisis por Modalidad</h2>
        <img src="charts/05_modalidad_trabajo.png" alt="Modalidad">
    </div>

    <div class="section">
        <h2>7. Distribución Geográfica</h2>
        <p>Análisis de ofertas por localización y región.</p>
        <img src="charts/09_distribucion_geografica.png" alt="Distribución Geográfica">
        {'<p><strong>' + str(self.stats.get('geografico', {}).get('localizaciones_unicas', 0)) + '</strong> localizaciones únicas identificadas.</p>' if 'geografico' in self.stats else ''}
    </div>

    <div class="section">
        <h2>8. Top Empresas Reclutadoras</h2>
        <img src="charts/10_top_empresas.png" alt="Top Empresas">
        {'<p><strong>' + str(self.stats.get('empresas', {}).get('ofertas_confidenciales', 0)) + '</strong> ofertas confidenciales de <strong>' + str(self.stats.get('empresas', {}).get('empresas_unicas', 0)) + '</strong> empresas únicas.</p>' if 'empresas' in self.stats else ''}
    </div>

    <div class="section">
        <h2>9. Dashboard Interactivo</h2>
        <p>Acceda al dashboard interactivo para explorar los datos en detalle:</p>
        <a href="charts/dashboard_interactivo.html" target="_blank" style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Abrir Dashboard Interactivo
        </a>
    </div>

    <div class="footer">
        <p>Proyecto ZonaJobs + ESCO Integration</p>
        <p>Desarrollado para OEDE - {datetime.now().year}</p>
    </div>
</body>
</html>
"""

        informe_path = OUTPUT_DIR / "informe_completo.html"
        with open(informe_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  [OK] Informe guardado: {informe_path.name}")
        print(f"  [INFO] Abrir en navegador: {informe_path}")

    def guardar_estadisticas_json(self):
        """Guarda estadísticas en JSON"""
        print("\n[11] GUARDANDO ESTADÍSTICAS EN JSON")
        print("-" * 80)

        # Convertir tipos pandas a tipos Python nativos
        def convert_to_native(obj):
            if isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            else:
                return obj

        stats_native = convert_to_native(self.stats)

        stats_path = OUTPUT_DIR / "estadisticas_completas.json"

        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_native, f, indent=2, ensure_ascii=False)

        print(f"  [OK] Estadísticas guardadas: {stats_path.name}")

    def ejecutar_analisis_completo(self):
        """Ejecuta el análisis completo"""
        # Análisis estadísticos
        self.analisis_general()
        self.analisis_ocupaciones()
        self.analisis_isco()
        self.analisis_skills()
        self.analisis_modalidad()
        self.analisis_geografico()
        self.analisis_empresas()

        # Gráficos estáticos
        self.generar_grafico_distribucion_ocupaciones()
        self.generar_grafico_isco_grupos()
        self.generar_grafico_similitud()
        self.generar_grafico_skills()
        self.generar_grafico_modalidad()
        self.generar_grafico_tasa_clasificacion()
        self.generar_grafico_isco_jerarquia()
        self.generar_grafico_skills_por_ocupacion()
        self.generar_grafico_geografico()
        self.generar_grafico_empresas()

        # Dashboard interactivo
        self.generar_dashboard_interactivo()

        # Informe HTML
        self.generar_informe_html()

        # Guardar estadísticas
        self.guardar_estadisticas_json()

        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETADO")
        print("=" * 80)
        print(f"\n📁 Archivos generados en: {OUTPUT_DIR}")
        print(f"📊 Gráficos guardados en: {CHARTS_DIR}")
        print(f"\n🌐 Abrir informe: {OUTPUT_DIR / 'informe_completo.html'}")
        print(f"📈 Dashboard interactivo: {CHARTS_DIR / 'dashboard_interactivo.html'}")


def main():
    """Función principal"""
    try:
        analizador = AnalizadorESCO()
        analizador.ejecutar_analisis_completo()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
