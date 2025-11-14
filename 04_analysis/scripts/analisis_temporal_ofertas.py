"""
Análisis Temporal de Ofertas Laborales
========================================

Genera análisis temporal de ofertas por día y semana,
con descomposición por grupos ocupacionales ISCO.

Fecha: 2025-10-17
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import json
from pathlib import Path

# Configuración
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 11

# Colores para grupos ISCO
ISCO_COLORS = {
    '1': '#FF6B6B',  # Rojo - Directores y gerentes
    '2': '#4ECDC4',  # Turquesa - Profesionales científicos
    '3': '#45B7D1',  # Azul - Técnicos profesionales
    '4': '#FFA07A',  # Naranja - Personal apoyo administrativo
    '5': '#98D8C8',  # Verde - Servicios y ventas
    '6': '#F7DC6F',  # Amarillo - Agricultores
    '7': '#BB8FCE',  # Púrpura - Oficiales y artesanos
    '8': '#EC7063',  # Coral - Operadores
    '9': '#85C1E2',  # Azul claro - Ocupaciones elementales
}

ISCO_LABELS = {
    '1': 'Directores y gerentes',
    '2': 'Profesionales científicos',
    '3': 'Técnicos profesionales',
    '4': 'Personal administrativo',
    '5': 'Servicios y ventas',
    '6': 'Agricultores',
    '7': 'Oficiales y artesanos',
    '8': 'Operadores de máquinas',
    '9': 'Ocupaciones elementales',
}


def cargar_datos(archivo_csv):
    """Carga y prepara los datos con fechas procesadas."""
    print(f"\n>> Cargando datos desde: {archivo_csv}")

    df = pd.read_csv(archivo_csv)

    # Convertir fecha de publicación
    df['fecha_pub_dt'] = pd.to_datetime(df['fecha_publicacion'], format='%d-%m-%Y')
    df['fecha_pub_date'] = df['fecha_pub_dt'].dt.date

    # Extraer componentes temporales
    df['año'] = df['fecha_pub_dt'].dt.year
    df['mes'] = df['fecha_pub_dt'].dt.month
    df['mes_nombre'] = df['fecha_pub_dt'].dt.month_name()
    df['semana_del_año'] = df['fecha_pub_dt'].dt.isocalendar().week
    df['dia_semana'] = df['fecha_pub_dt'].dt.dayofweek
    df['dia_semana_nombre'] = df['fecha_pub_dt'].dt.day_name()

    # Crear semana del mes (1-5)
    df['dia_del_mes'] = df['fecha_pub_dt'].dt.day
    df['semana_del_mes'] = ((df['dia_del_mes'] - 1) // 7) + 1

    # Extraer grupo ISCO 1 dígito
    df['isco_1d'] = df['esco_match_1_isco_4d'].astype(str).str[0]

    print(f"[OK] Datos cargados: {len(df)} ofertas")
    print(f"   Rango: {df['fecha_pub_dt'].min().date()} a {df['fecha_pub_dt'].max().date()}")
    print(f"   Dias totales: {(df['fecha_pub_dt'].max() - df['fecha_pub_dt'].min()).days + 1}")

    return df


def analisis_diario(df):
    """Genera análisis por día."""
    print("\n>> Analisis diario...")

    # Total por día
    ofertas_dia = df.groupby('fecha_pub_date').size().reset_index(name='total_ofertas')
    ofertas_dia['fecha'] = pd.to_datetime(ofertas_dia['fecha_pub_date'])

    # Por grupo ISCO
    ofertas_dia_isco = df[df['clasificada'] == True].groupby(['fecha_pub_date', 'isco_1d']).size().reset_index(name='ofertas')

    stats = {
        'total_dias': len(ofertas_dia),
        'promedio_dia': ofertas_dia['total_ofertas'].mean(),
        'max_dia': ofertas_dia['total_ofertas'].max(),
        'min_dia': ofertas_dia['total_ofertas'].min(),
        'mediana_dia': ofertas_dia['total_ofertas'].median(),
    }

    print(f"   Total días con ofertas: {stats['total_dias']}")
    print(f"   Promedio por día: {stats['promedio_dia']:.2f}")
    print(f"   Máximo: {stats['max_dia']} | Mínimo: {stats['min_dia']}")

    return ofertas_dia, ofertas_dia_isco, stats


def analisis_semanal(df):
    """Genera análisis por semana."""
    print("\n>> Analisis semanal...")

    # Crear identificador de semana (año-semana)
    df['año_semana'] = df['fecha_pub_dt'].dt.strftime('%Y-W%U')

    # Total por semana
    ofertas_semana = df.groupby('año_semana').agg({
        'id_oferta': 'count',
        'fecha_pub_dt': ['min', 'max']
    }).reset_index()
    ofertas_semana.columns = ['año_semana', 'total_ofertas', 'fecha_inicio', 'fecha_fin']

    # Por grupo ISCO
    ofertas_semana_isco = df[df['clasificada'] == True].groupby(['año_semana', 'isco_1d']).size().reset_index(name='ofertas')

    stats = {
        'total_semanas': len(ofertas_semana),
        'promedio_semana': ofertas_semana['total_ofertas'].mean(),
        'max_semana': ofertas_semana['total_ofertas'].max(),
        'min_semana': ofertas_semana['total_ofertas'].min(),
    }

    print(f"   Total semanas: {stats['total_semanas']}")
    print(f"   Promedio por semana: {stats['promedio_semana']:.2f}")
    print(f"   Máximo: {stats['max_semana']} | Mínimo: {stats['min_semana']}")

    return ofertas_semana, ofertas_semana_isco, stats


def visualizar_serie_diaria(ofertas_dia, output_dir):
    """Crea gráfico de serie temporal diaria."""
    print("\n>> Generando serie temporal diaria...")

    fig, ax = plt.subplots(figsize=(16, 6))

    ax.plot(ofertas_dia['fecha'], ofertas_dia['total_ofertas'],
            marker='o', linewidth=2, markersize=6, color='#2E86AB')

    # Línea de tendencia
    z = np.polyfit(mdates.date2num(ofertas_dia['fecha']), ofertas_dia['total_ofertas'], 1)
    p = np.poly1d(z)
    ax.plot(ofertas_dia['fecha'], p(mdates.date2num(ofertas_dia['fecha'])),
            "--", alpha=0.5, color='red', linewidth=2, label='Tendencia')

    ax.set_xlabel('Fecha de Publicación', fontweight='bold')
    ax.set_ylabel('Número de Ofertas', fontweight='bold')
    ax.set_title('Serie Temporal Diaria de Ofertas Laborales\nZonaJobs (Agosto - Octubre 2025)',
                 fontweight='bold', fontsize=14, pad=20)

    # Formato de fechas
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=45, ha='right')

    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend()

    plt.tight_layout()
    output_file = output_dir / '09_serie_temporal_diaria.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   [OK] Guardado: {output_file.name}")
    return str(output_file)


def visualizar_serie_semanal(ofertas_semana, output_dir):
    """Crea gráfico de serie temporal semanal."""
    print("\n>> Generando serie temporal semanal...")

    fig, ax = plt.subplots(figsize=(14, 6))

    x_pos = np.arange(len(ofertas_semana))
    bars = ax.bar(x_pos, ofertas_semana['total_ofertas'], color='#45B7D1', alpha=0.8)

    # Línea de tendencia
    z = np.polyfit(x_pos, ofertas_semana['total_ofertas'], 1)
    p = np.poly1d(z)
    ax.plot(x_pos, p(x_pos), "--", alpha=0.6, color='red', linewidth=2, label='Tendencia')

    # Etiquetas
    labels = [f"Sem {sem.split('-W')[1]}\n{inicio.strftime('%d/%m')}"
              for sem, inicio in zip(ofertas_semana['año_semana'], ofertas_semana['fecha_inicio'])]
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=45, ha='right')

    ax.set_xlabel('Semana del Año', fontweight='bold')
    ax.set_ylabel('Número de Ofertas', fontweight='bold')
    ax.set_title('Serie Temporal Semanal de Ofertas Laborales\nZonaJobs (Agosto - Octubre 2025)',
                 fontweight='bold', fontsize=14, pad=20)

    # Valores sobre barras
    for i, (bar, val) in enumerate(zip(bars, ofertas_semana['total_ofertas'])):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                str(int(val)), ha='center', va='bottom', fontsize=9)

    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend()

    plt.tight_layout()
    output_file = output_dir / '10_serie_temporal_semanal.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   [OK] Guardado: {output_file.name}")
    return str(output_file)


def visualizar_stacked_diario_isco(ofertas_dia, ofertas_dia_isco, output_dir):
    """Crea gráfico apilado diario por grupo ISCO."""
    print("\n>> Generando serie diaria descompuesta por ISCO...")

    # Preparar datos para gráfico apilado
    pivot_data = ofertas_dia_isco.pivot_table(
        index='fecha_pub_date',
        columns='isco_1d',
        values='ofertas',
        fill_value=0
    )

    # Convertir índice a datetime
    pivot_data.index = pd.to_datetime(pivot_data.index)
    pivot_data = pivot_data.sort_index()

    # Asegurar que todas las columnas ISCO existen
    for isco in sorted(pivot_data.columns):
        if isco not in pivot_data.columns:
            pivot_data[isco] = 0

    fig, ax = plt.subplots(figsize=(16, 7))

    # Gráfico apilado
    bottom = np.zeros(len(pivot_data))

    for isco in sorted(pivot_data.columns):
        values = pivot_data[isco].values
        color = ISCO_COLORS.get(str(isco), '#95A5A6')
        label = f"{isco}: {ISCO_LABELS.get(str(isco), 'Otro')}"

        ax.bar(pivot_data.index, values, bottom=bottom,
               label=label, color=color, alpha=0.85, width=0.8)
        bottom += values

    ax.set_xlabel('Fecha de Publicación', fontweight='bold')
    ax.set_ylabel('Número de Ofertas', fontweight='bold')
    ax.set_title('Serie Temporal Diaria por Grupo Ocupacional ISCO\nZonaJobs (Agosto - Octubre 2025)',
                 fontweight='bold', fontsize=14, pad=20)

    # Formato de fechas
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=45, ha='right')

    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=9)

    plt.tight_layout()
    output_file = output_dir / '11_serie_diaria_isco_stacked.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   [OK] Guardado: {output_file.name}")
    return str(output_file)


def visualizar_stacked_semanal_isco(ofertas_semana, ofertas_semana_isco, output_dir):
    """Crea gráfico apilado semanal por grupo ISCO."""
    print("\n>> Generando serie semanal descompuesta por ISCO...")

    # Preparar datos para gráfico apilado
    pivot_data = ofertas_semana_isco.pivot_table(
        index='año_semana',
        columns='isco_1d',
        values='ofertas',
        fill_value=0
    )

    # Ordenar por semana
    pivot_data = pivot_data.sort_index()

    fig, ax = plt.subplots(figsize=(14, 7))

    x_pos = np.arange(len(pivot_data))
    bottom = np.zeros(len(pivot_data))

    for isco in sorted(pivot_data.columns):
        values = pivot_data[isco].values
        color = ISCO_COLORS.get(str(isco), '#95A5A6')
        label = f"{isco}: {ISCO_LABELS.get(str(isco), 'Otro')}"

        ax.bar(x_pos, values, bottom=bottom,
               label=label, color=color, alpha=0.85)
        bottom += values

    # Etiquetas del eje X
    semana_labels = [f"S{sem.split('-W')[1]}" for sem in pivot_data.index]
    ax.set_xticks(x_pos)
    ax.set_xticklabels(semana_labels, rotation=45, ha='right')

    ax.set_xlabel('Semana del Año', fontweight='bold')
    ax.set_ylabel('Número de Ofertas', fontweight='bold')
    ax.set_title('Serie Temporal Semanal por Grupo Ocupacional ISCO\nZonaJobs (Agosto - Octubre 2025)',
                 fontweight='bold', fontsize=14, pad=20)

    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=9)

    plt.tight_layout()
    output_file = output_dir / '12_serie_semanal_isco_stacked.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   [OK] Guardado: {output_file.name}")
    return str(output_file)


def visualizar_heatmap_semanal(df, output_dir):
    """Crea heatmap de ofertas por día de la semana y semana del mes."""
    print("\n>> Generando heatmap dia/semana...")

    # Solo ofertas clasificadas
    df_clasificadas = df[df['clasificada'] == True].copy()

    # Agregar por día de semana y semana del mes
    heatmap_data = df_clasificadas.groupby(['dia_semana', 'mes_nombre']).size().unstack(fill_value=0)

    # Ordenar días de semana (0=Lunes, 6=Domingo)
    dias_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    fig, ax = plt.subplots(figsize=(10, 6))

    im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')

    # Etiquetas
    ax.set_xticks(np.arange(len(heatmap_data.columns)))
    ax.set_yticks(np.arange(len(heatmap_data.index)))
    ax.set_xticklabels(heatmap_data.columns, rotation=45, ha='right')
    ax.set_yticklabels([dias_nombres[i] if i < 7 else f'Día {i}' for i in heatmap_data.index])

    # Valores en celdas
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            value = heatmap_data.values[i, j]
            if value > 0:
                ax.text(j, i, int(value), ha="center", va="center",
                       color="white" if value > heatmap_data.values.max()/2 else "black",
                       fontweight='bold')

    ax.set_title('Distribución de Ofertas por Día de la Semana y Mes\nZonaJobs (Agosto - Octubre 2025)',
                 fontweight='bold', fontsize=13, pad=20)
    ax.set_xlabel('Mes', fontweight='bold')
    ax.set_ylabel('Día de la Semana', fontweight='bold')

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Número de Ofertas', rotation=270, labelpad=20, fontweight='bold')

    plt.tight_layout()
    output_file = output_dir / '13_heatmap_dia_mes.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"   [OK] Guardado: {output_file.name}")
    return str(output_file)


def convertir_a_tipos_nativos(obj):
    """Convierte tipos numpy/pandas a tipos nativos de Python para JSON."""
    if isinstance(obj, dict):
        return {k: convertir_a_tipos_nativos(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convertir_a_tipos_nativos(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    else:
        return obj


def generar_estadisticas_temporales(df, ofertas_dia_stats, ofertas_semana_stats):
    """Genera diccionario con todas las estadísticas temporales."""
    print("\n>> Generando estadisticas temporales...")

    stats = {
        'rango_temporal': {
            'fecha_inicio': df['fecha_pub_dt'].min().strftime('%Y-%m-%d'),
            'fecha_fin': df['fecha_pub_dt'].max().strftime('%Y-%m-%d'),
            'dias_totales': int((df['fecha_pub_dt'].max() - df['fecha_pub_dt'].min()).days + 1),
        },
        'analisis_diario': ofertas_dia_stats,
        'analisis_semanal': ofertas_semana_stats,
        'por_mes': df.groupby('mes_nombre').size().to_dict(),
        'por_dia_semana': df.groupby('dia_semana_nombre').size().to_dict(),
        'tendencia': {
            'descripcion': 'Analisis de tendencia temporal',
            'ofertas_primera_semana': int(df[df['semana_del_año'] == df['semana_del_año'].min()].shape[0]),
            'ofertas_ultima_semana': int(df[df['semana_del_año'] == df['semana_del_año'].max()].shape[0]),
        }
    }

    # Convertir todos los tipos numpy a tipos nativos
    stats = convertir_a_tipos_nativos(stats)

    return stats


def main():
    """Función principal."""
    print("="*70)
    print("ANALISIS TEMPORAL DE OFERTAS LABORALES")
    print("ZonaJobs + ESCO")
    print("="*70)

    # Rutas
    base_dir = Path(r"D:\OEDE\Webscrapping")
    data_dir = base_dir / "data" / "processed"
    output_dir = data_dir / "charts"
    output_dir.mkdir(exist_ok=True)

    # Archivo más reciente
    archivo_csv = data_dir / "zonajobs_esco_enriquecida_20251016_204914.csv"

    # 1. Cargar datos
    df = cargar_datos(archivo_csv)

    # 2. Análisis diario
    ofertas_dia, ofertas_dia_isco, ofertas_dia_stats = analisis_diario(df)

    # 3. Análisis semanal
    ofertas_semana, ofertas_semana_isco, ofertas_semana_stats = analisis_semanal(df)

    # 4. Visualizaciones
    graficos_generados = []

    graficos_generados.append(visualizar_serie_diaria(ofertas_dia, output_dir))
    graficos_generados.append(visualizar_serie_semanal(ofertas_semana, output_dir))
    graficos_generados.append(visualizar_stacked_diario_isco(ofertas_dia, ofertas_dia_isco, output_dir))
    graficos_generados.append(visualizar_stacked_semanal_isco(ofertas_semana, ofertas_semana_isco, output_dir))
    graficos_generados.append(visualizar_heatmap_semanal(df, output_dir))

    # 5. Generar estadísticas
    stats_temporales = generar_estadisticas_temporales(df, ofertas_dia_stats, ofertas_semana_stats)

    # Guardar estadísticas
    stats_file = data_dir / 'estadisticas_temporales.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_temporales, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Estadisticas guardadas: {stats_file.name}")

    # 6. Guardar tablas CSV
    ofertas_dia.to_csv(data_dir / 'ofertas_por_dia.csv', index=False)
    ofertas_semana.to_csv(data_dir / 'ofertas_por_semana.csv', index=False)
    ofertas_dia_isco.to_csv(data_dir / 'ofertas_por_dia_isco.csv', index=False)
    ofertas_semana_isco.to_csv(data_dir / 'ofertas_por_semana_isco.csv', index=False)

    print(f"[OK] Tablas temporales guardadas en: {data_dir}")

    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN DEL ANALISIS TEMPORAL")
    print("="*70)
    print(f"\n>> Visualizaciones generadas: {len(graficos_generados)}")
    for grafico in graficos_generados:
        print(f"   - {Path(grafico).name}")

    print(f"\n>> Archivos de datos:")
    print(f"   - ofertas_por_dia.csv ({len(ofertas_dia)} dias)")
    print(f"   - ofertas_por_semana.csv ({len(ofertas_semana)} semanas)")
    print(f"   - ofertas_por_dia_isco.csv")
    print(f"   - ofertas_por_semana_isco.csv")
    print(f"   - estadisticas_temporales.json")

    print("\n" + "="*70)
    print("[OK] ANALISIS TEMPORAL COMPLETADO")
    print("="*70)

    return stats_temporales


if __name__ == "__main__":
    main()
