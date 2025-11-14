# -*- coding: utf-8 -*-
"""
Fix and Re-clean - Corrige problemas del pipeline híbrido y re-limpia
======================================================================

PROBLEMAS A CORREGIR:
1. Combinación híbrida REEMPLAZA en lugar de UNIR (Regex + LLM)
2. Skills agrupadas con " y " no se separan
3. Falta columna de localización/ubicación
"""

import pandas as pd
import ast
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_and_split_skills(value):
    """
    Parsea skills y separa las conectadas con " y "

    Ejemplos:
    "['skill1', 'skill2']" -> ["skill1", "skill2"]
    "skill1, skill2 y skill3" -> ["skill1", "skill2", "skill3"]
    "organizacion y gestion del tiempo" -> ["organizacion", "gestion del tiempo"]
    """
    if pd.isna(value):
        return []

    value_str = str(value).strip()

    # Si es lista Python
    if value_str.startswith('[') and value_str.endswith(']'):
        try:
            parsed = ast.literal_eval(value_str)
            if isinstance(parsed, list):
                skills = [str(item).strip() for item in parsed if item and str(item).strip()]
                # Expandir skills con " y "
                expanded = []
                for skill in skills:
                    if ' y ' in skill:
                        expanded.extend([s.strip() for s in skill.split(' y ') if s.strip()])
                    else:
                        expanded.append(skill)
                return expanded
        except:
            pass

    # Si es string normal
    skills = [s.strip() for s in value_str.split(',') if s.strip()]

    # Expandir skills con " y "
    expanded = []
    for skill in skills:
        if ' y ' in skill:
            # Separar por " y "
            parts = [s.strip() for s in skill.split(' y ') if s.strip()]
            expanded.extend(parts)
        else:
            expanded.append(skill)

    return expanded


def recombine_hybrid_skills(row):
    """
    Re-combina soft skills correctamente: UNION(Regex, LLM) en lugar de reemplazar
    """
    # Obtener skills de Regex (lista Python)
    regex_skills = parse_and_split_skills(row.get('soft_skills_list'))

    # Obtener skills de LLM (string)
    llm_skills = parse_and_split_skills(row.get('hybrid_soft_skills_list'))

    # UNIR (no reemplazar)
    all_skills = set()
    all_skills.update(regex_skills)
    all_skills.update(llm_skills)

    # Remover duplicados y vacíos
    all_skills = {s for s in all_skills if s and len(s) > 2}

    if all_skills:
        return ', '.join(sorted(all_skills))
    return None


def fix_hybrid_csv():
    """Corrige el CSV híbrido y genera uno limpio corregido"""

    logger.info("=" * 70)
    logger.info("CORRECCION Y RE-LIMPIEZA DEL PIPELINE")
    logger.info("=" * 70)
    logger.info("")

    # 1. Cargar CSV híbrido
    logger.info("1. Cargando CSV híbrido...")
    df = pd.read_csv('../data/processed/all_sources_hybrid_20251027_141056.csv', low_memory=False)
    logger.info(f"   Filas: {len(df):,}")
    logger.info(f"   Columnas: {len(df.columns)}")

    # 2. Re-combinar soft skills correctamente
    logger.info("")
    logger.info("2. Re-combinando soft skills (UNION de Regex + LLM)...")

    df['soft_skills_fixed'] = df.apply(recombine_hybrid_skills, axis=1)

    # Comparar con versión incorrecta
    before = df['final_soft_skills_list'].notna().sum()
    after = df['soft_skills_fixed'].notna().sum()

    logger.info(f"   Antes (incorrecto): {before:,} ofertas con soft skills")
    logger.info(f"   Despues (corregido): {after:,} ofertas con soft skills")
    logger.info(f"   Mejora: +{after - before} ofertas")

    # Ejemplo de corrección
    logger.info("")
    logger.info("   Ejemplo de correccion (fila 0):")
    row0 = df.iloc[0]
    logger.info(f"     Regex: {row0.get('soft_skills_list', 'N/A')}")
    logger.info(f"     LLM: {row0.get('hybrid_soft_skills_list', 'N/A')}")
    logger.info(f"     Antes (incorrecto): {row0.get('final_soft_skills_list', 'N/A')}")
    logger.info(f"     Despues (corregido): {row0.get('soft_skills_fixed', 'N/A')}")

    # 3. Skills técnicas también con split
    logger.info("")
    logger.info("3. Procesando skills técnicas...")

    def parse_tech_skills(row):
        skills = parse_and_split_skills(row.get('skills_tecnicas_list'))
        if skills:
            return ', '.join(skills)
        return None

    df['skills_tecnicas_fixed'] = df.apply(parse_tech_skills, axis=1)

    # 4. Normalizar educación
    logger.info("")
    logger.info("4. Normalizando educación...")

    education_mapping = {
        'secundario': 'secundario', 'secundaria': 'secundario',
        'terciario': 'terciario', 'terciaria': 'terciario',
        'universitario': 'universitario', 'universitaria': 'universitario',
        'grado': 'universitario', 'licenciatura': 'universitario',
        'posgrado': 'posgrado', 'postgrado': 'posgrado',
        'maestría': 'posgrado', 'maestria': 'posgrado', 'doctorado': 'posgrado'
    }

    df['educacion_fixed'] = df['final_nivel_educativo'].astype(str).str.lower().map(education_mapping)

    # 5. Seleccionar columnas finales (incluyendo localización)
    logger.info("")
    logger.info("5. Seleccionando columnas finales...")

    final_cols = [
        # Identificación
        'id_aviso', 'fecha_publicacion', 'fuente',

        # Contenido
        'titulo', 'descripcion', 'empresa',

        # Ubicación (agregado)
        'localizacion',

        # Contrato
        'tipo_contrato', 'modalidad', 'salario',

        # Requisitos (corregidos)
        'soft_skills_fixed',
        'skills_tecnicas_fixed',
        'educacion_fixed',
        'experiencia_min_anios',
        'experiencia_max_anios',

        # Otros
        'idioma_principal',
        'area_experiencia',
        'certificaciones_list',

        # Metadata
        'hybrid_method',
        'hybrid_llm_called'
    ]

    existing_cols = [col for col in final_cols if col in df.columns]
    df_clean = df[existing_cols].copy()

    # Renombrar columnas fixed
    df_clean.rename(columns={
        'soft_skills_fixed': 'soft_skills',
        'skills_tecnicas_fixed': 'skills_tecnicas',
        'educacion_fixed': 'nivel_educativo'
    }, inplace=True)

    # 6. Agregar estadísticas
    logger.info("")
    logger.info("6. Calculando estadísticas...")

    df_clean['soft_skills_count'] = df_clean['soft_skills'].apply(
        lambda x: len([s.strip() for s in str(x).split(',') if s.strip()]) if pd.notna(x) else 0
    )

    df_clean['skills_tecnicas_count'] = df_clean['skills_tecnicas'].apply(
        lambda x: len([s.strip() for s in str(x).split(',') if s.strip()]) if pd.notna(x) else 0
    )

    df_clean['is_complete'] = (
        df_clean['nivel_educativo'].notna() &
        df_clean['soft_skills'].notna() &
        df_clean['experiencia_min_anios'].notna()
    )

    # 7. Guardar
    logger.info("")
    logger.info("=" * 70)
    logger.info("GUARDANDO DATOS CORREGIDOS")
    logger.info("=" * 70)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'../data/processed/all_sources_fixed_{timestamp}.csv'

    df_clean.to_csv(output_path, index=False)

    logger.info(f"")
    logger.info(f"Guardado: {output_path}")
    logger.info(f"Tamaño: {Path(output_path).stat().st_size / 1024 / 1024:.1f} MB")

    # 8. Resumen
    logger.info("")
    logger.info("=" * 70)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 70)
    logger.info(f"Ofertas: {len(df_clean):,}")
    logger.info(f"Columnas: {len(df_clean.columns)}")
    logger.info("")

    logger.info("COBERTURA:")
    key_fields = {
        'soft_skills': 'Soft Skills',
        'skills_tecnicas': 'Skills Técnicas',
        'nivel_educativo': 'Educación',
        'experiencia_min_anios': 'Experiencia',
        'localizacion': 'Localización',
        'idioma_principal': 'Idioma'
    }

    for field, label in key_fields.items():
        if field in df_clean.columns:
            coverage = df_clean[field].notna().sum()
            pct = 100 * coverage / len(df_clean)
            logger.info(f"  {label}: {coverage:,} ({pct:.1f}%)")

    logger.info("")
    logger.info(f"Ofertas completas: {df_clean['is_complete'].sum():,} ({100*df_clean['is_complete'].sum()/len(df_clean):.1f}%)")

    logger.info("")
    logger.info("MEJORAS vs VERSION ANTERIOR:")

    # Cargar versión anterior para comparar
    df_old = pd.read_csv('../data/processed/all_sources_clean_20251027_155530.csv', low_memory=False)

    old_soft = df_old['soft_skills_clean'].notna().sum()
    new_soft = df_clean['soft_skills'].notna().sum()

    logger.info(f"  Soft skills: {old_soft:,} -> {new_soft:,} (+{new_soft - old_soft})")

    if 'localizacion' not in df_old.columns:
        logger.info(f"  Localizacion: 0 -> {df_clean['localizacion'].notna().sum():,} (NUEVA!)")

    logger.info("=" * 70)

    return df_clean


if __name__ == "__main__":
    try:
        df_fixed = fix_hybrid_csv()
        logger.info("")
        logger.info("Correccion completada!")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
