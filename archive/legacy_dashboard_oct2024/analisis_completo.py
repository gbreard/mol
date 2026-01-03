import pandas as pd
import numpy as np

df = pd.read_excel('ofertas_consolidadas.xlsx', sheet_name='BASE')

print("=" * 80)
print("ANÁLISIS COMPLETO DE DATOS DISPONIBLES PARA EL DASHBOARD")
print("=" * 80)

# 1. CLASIFICACIÓN OCUPACIONAL
print("\n1. CLASIFICACIÓN OCUPACIONAL (ESCO/ISCO)")
print("-" * 80)
print(f"Ofertas con código ESCO: {df['clasificacion_esco.ocupacion_esco_code'].notna().sum()}")
print(f"Ofertas con código ISCO: {df['clasificacion_esco.isco_code'].notna().sum()}")
print(f"Ofertas con habilidades ESCO: {df['clasificacion_esco.skills'].notna().sum()}")

if df['clasificacion_esco.isco_code'].notna().sum() > 0:
    print("\nTop 10 códigos ISCO:")
    print(df['clasificacion_esco.isco_code'].value_counts().head(10))

    print("\nTop 10 labels ISCO:")
    print(df['clasificacion_esco.isco_label'].value_counts().head(10))

# 2. SALARIOS Y COMPENSACIÓN
print("\n2. SALARIOS Y COMPENSACIÓN")
print("-" * 80)
print(f"Ofertas con salario mínimo: {df['compensacion.salario_minimo'].notna().sum()}")
print(f"Ofertas con salario máximo: {df['compensacion.salario_maximo'].notna().sum()}")
print(f"Ofertas con beneficios: {df['compensacion.beneficios'].notna().sum()}")

if df['compensacion.salario_minimo'].notna().sum() > 0:
    salarios = df['compensacion.salario_minimo'].dropna()
    print(f"\nEstadísticas salariales:")
    print(f"  Promedio: ${salarios.mean():,.0f}")
    print(f"  Mediana: ${salarios.median():,.0f}")
    print(f"  Mínimo: ${salarios.min():,.0f}")
    print(f"  Máximo: ${salarios.max():,.0f}")

# 3. REQUISITOS
print("\n3. REQUISITOS")
print("-" * 80)
print(f"Ofertas con experiencia mínima: {df['requisitos.experiencia_minima'].notna().sum()}")
print(f"Ofertas con nivel educativo: {df['requisitos.nivel_educativo'].notna().sum()}")
print(f"Ofertas con idiomas: {df['requisitos.idiomas'].notna().sum()}")
print(f"Ofertas con habilidades: {df['requisitos.habilidades'].notna().sum()}")

if df['requisitos.nivel_educativo'].notna().sum() > 0:
    print("\nNiveles educativos:")
    print(df['requisitos.nivel_educativo'].value_counts())

# 4. ÁREA DE TRABAJO
print("\n4. ÁREA Y NIVEL DE PUESTO")
print("-" * 80)
print(f"Ofertas con área de trabajo: {df['detalles.area_trabajo'].notna().sum()}")
print(f"Ofertas con nivel de puesto: {df['detalles.nivel_puesto'].notna().sum()}")
print(f"Ofertas con cantidad de vacantes: {df['detalles.cantidad_vacantes'].notna().sum()}")

if df['detalles.area_trabajo'].notna().sum() > 0:
    print("\nTop áreas de trabajo:")
    print(df['detalles.area_trabajo'].value_counts().head(10))

# 5. UBICACIÓN GEOGRÁFICA
print("\n5. UBICACIÓN GEOGRÁFICA")
print("-" * 80)
print(f"Ofertas con provincia: {df['ubicacion.provincia'].notna().sum()}")
print(f"Ofertas con ciudad: {df['ubicacion.ciudad'].notna().sum()}")
print(f"Ofertas con zona: {df['ubicacion.zona'].notna().sum()}")
print(f"Ofertas con código postal: {df['ubicacion.codigo_postal'].notna().sum()}")

print("\nDistribución por provincia (todas):")
print(df['ubicacion.provincia'].value_counts())

# 6. TEMPORALIDAD
print("\n6. TEMPORALIDAD")
print("-" * 80)
print(f"Ofertas con fecha de publicación: {df['fechas.fecha_publicacion'].notna().sum()}")
print(f"Ofertas con fecha de cierre: {df['fechas.fecha_cierre'].notna().sum()}")

if df['Periodo'].notna().sum() > 0:
    df['Periodo_date'] = pd.to_datetime(df['Periodo'], errors='coerce')
    print(f"\nRango de fechas:")
    print(f"  Más antigua: {df['Periodo_date'].min()}")
    print(f"  Más reciente: {df['Periodo_date'].max()}")

# 7. TIPO DE TRABAJO
print("\n7. TIPO DE TRABAJO")
print("-" * 80)
print(f"Ofertas con tipo de trabajo: {df['modalidad.tipo_trabajo'].notna().sum()}")
print(f"Ofertas con modalidad: {df['modalidad.modalidad_trabajo'].notna().sum()}")

if df['modalidad.tipo_trabajo'].notna().sum() > 0:
    print("\nTipo de trabajo:")
    print(df['modalidad.tipo_trabajo'].value_counts())

# 8. EMPRESAS
print("\n8. EMPRESAS")
print("-" * 80)
print(f"Total empresas únicas: {df['informacion_basica.empresa'].nunique()}")
print(f"Ofertas con logo: {df['informacion_basica.logo_url'].notna().sum()}")
print(f"Ofertas con URL empresa: {df['informacion_basica.empresa_url'].notna().sum()}")

# 9. DESCRIPCIONES Y TEXTO
print("\n9. CONTENIDO TEXTUAL")
print("-" * 80)
print(f"Ofertas con descripción: {df['informacion_basica.descripcion'].notna().sum()}")
print(f"Ofertas con descripción limpia: {df['informacion_basica.descripcion_limpia'].notna().sum()}")
print(f"Ofertas con descripción completa: {df['descripcion.descripcion_completa'].notna().sum()}")
print(f"Ofertas con responsabilidades: {df['descripcion.responsabilidades'].notna().sum()}")

# 10. FUENTES
print("\n10. FUENTES DE DATOS")
print("-" * 80)
print("Distribución por fuente:")
print(df['_metadata.source'].value_counts())

# 11. ANÁLISIS DE COMPLETITUD
print("\n11. ANÁLISIS DE COMPLETITUD DE DATOS")
print("-" * 80)
columnas_importantes = {
    'Empresa': 'informacion_basica.empresa',
    'Título': 'informacion_basica.titulo_normalizado',
    'Provincia': 'ubicacion.provincia',
    'Ciudad': 'ubicacion.ciudad',
    'Modalidad': 'modalidad.modalidad_trabajo',
    'Tipo trabajo': 'modalidad.tipo_trabajo',
    'Salario mín': 'compensacion.salario_minimo',
    'Clasificación ISCO': 'clasificacion_esco.isco_label',
    'Área trabajo': 'detalles.area_trabajo',
    'Nivel educativo': 'requisitos.nivel_educativo',
    'Experiencia': 'requisitos.experiencia_minima',
}

for nombre, col in columnas_importantes.items():
    pct = (df[col].notna().sum() / len(df)) * 100
    print(f"{nombre:20} : {pct:5.1f}% completo ({df[col].notna().sum()}/{len(df)})")

# 12. OPORTUNIDADES DE ANÁLISIS
print("\n" + "=" * 80)
print("COLUMNAS CON DATOS RICOS PARA NUEVOS ANÁLISIS")
print("=" * 80)

columnas_ricas = []
for col in df.columns:
    pct_completo = (df[col].notna().sum() / len(df)) * 100
    n_unicos = df[col].nunique()
    if pct_completo > 10 and n_unicos > 1:  # Más del 10% completo y más de 1 valor único
        columnas_ricas.append({
            'columna': col,
            'completitud': pct_completo,
            'valores_unicos': n_unicos,
            'registros': df[col].notna().sum()
        })

columnas_ricas_df = pd.DataFrame(columnas_ricas).sort_values('completitud', ascending=False)
print(columnas_ricas_df.to_string(index=False))

print("\n" + "=" * 80)
