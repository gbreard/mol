"""
Dashboard de Monitoreo v2 - Bumeran Scraping
=============================================

Dashboard interactivo EXPANDIDO con tabs para monitorear el sistema de scraping.

Nuevas features:
- Tab de Keywords (productividad)
- Tab de Calidad de Datos
- Tab de Alertas
- Tab de KPIs de Scraping

Uso:
    python dashboard_scraping_v2.py

Acceder en: http://localhost:8051
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime
import json
from pathlib import Path
import io
import base64

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

DB_PATH = Path(__file__).parent / "database" / "bumeran_scraping.db"
TRACKING_FILE = Path(__file__).parent / "data" / "tracking" / "bumeran_scraped_ids.json"

# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

def cargar_ofertas():
    """Carga ofertas desde SQLite - TODAS las columnas"""
    conn = sqlite3.connect(DB_PATH)

    # Cargar TODAS las columnas
    query = "SELECT * FROM ofertas ORDER BY scrapeado_en DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convertir fechas
    if 'scrapeado_en' in df.columns:
        df['scrapeado_en'] = pd.to_datetime(df['scrapeado_en'])
        df['fecha_scraping'] = df['scrapeado_en'].dt.date

    return df

def cargar_keywords():
    """Carga performance de keywords"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        keyword,
        SUM(ofertas_encontradas) as total_ofertas,
        SUM(ofertas_nuevas) as total_nuevas,
        COUNT(*) as veces_ejecutado,
        MAX(scraping_date) as ultima_ejecucion
    FROM keywords_performance
    WHERE ofertas_encontradas > 0
    GROUP BY keyword
    ORDER BY total_ofertas DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def cargar_alertas():
    """Carga alertas del sistema"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        timestamp, level, type, message, context
    FROM alertas
    ORDER BY timestamp DESC
    LIMIT 50
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def cargar_metricas_scraping():
    """Carga métricas de ejecuciones de scraping"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        start_time, end_time, total_time_seconds,
        offers_new, offers_duplicates, offers_total,
        success_rate, query, created_at
    FROM metricas_scraping
    ORDER BY created_at DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def calcular_completitud():
    """Calcula completitud de TODOS los campos en ofertas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener total de ofertas
    cursor.execute('SELECT COUNT(*) FROM ofertas')
    total = cursor.fetchone()[0]

    # Obtener TODAS las columnas de la tabla ofertas
    cursor.execute("PRAGMA table_info(ofertas)")
    columnas = [col[1] for col in cursor.fetchall()]

    resultados = []
    for campo in columnas:
        cursor.execute(f'''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN {campo} IS NOT NULL AND {campo} != '' THEN 1 ELSE 0 END) as completos
            FROM ofertas
        ''')
        total_campo, completos = cursor.fetchone()
        completitud = (completos / total_campo * 100) if total_campo > 0 else 0

        resultados.append({
            'campo': campo,
            'completitud': completitud,
            'completos': completos,
            'total': total_campo
        })

    conn.close()

    # Ordenar por completitud (de menor a mayor) para ver primero los campos con problemas
    df = pd.DataFrame(resultados)
    df = df.sort_values('completitud', ascending=True)

    return df

def cargar_estadisticas():
    """Carga estadísticas generales"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM ofertas')
    total_ofertas = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT id_oferta) FROM ofertas')
    ofertas_unicas = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT empresa) FROM ofertas WHERE empresa IS NOT NULL')
    empresas_unicas = cursor.fetchone()[0]

    cursor.execute('SELECT MAX(scrapeado_en) FROM ofertas')
    ultima_actualizacion = cursor.fetchone()[0]

    # Keywords productivos
    cursor.execute('''
        SELECT COUNT(DISTINCT keyword)
        FROM keywords_performance
        WHERE ofertas_encontradas > 0
    ''')
    keywords_productivos = cursor.fetchone()[0]

    # Total keywords analizados
    cursor.execute('SELECT COUNT(DISTINCT keyword) FROM keywords_performance')
    total_keywords = cursor.fetchone()[0]

    conn.close()

    with open(TRACKING_FILE, 'r') as f:
        tracking = json.load(f)

    return {
        'total_ofertas': total_ofertas,
        'ofertas_unicas': ofertas_unicas,
        'empresas_unicas': empresas_unicas,
        'ultima_actualizacion': ultima_actualizacion,
        'ids_tracking': len(tracking.get('scraped_ids', [])),
        'keywords_productivos': keywords_productivos,
        'total_keywords': total_keywords
    }

# ============================================================================
# CREAR APP DASH
# ============================================================================

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# CSS personalizado
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard Scraping Bumeran v2</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stats-container {
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                padding: 20px;
                gap: 15px;
            }
            .stat-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                min-width: 180px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }
            .stat-label {
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .chart-container {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .tab-content {
                padding: 10px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================================================================
# FUNCIONES DE GRÁFICOS
# ============================================================================

def crear_grafico_temporal(df):
    """Gráfico temporal de ofertas scrapeadas"""
    ofertas_por_fecha = df.groupby('fecha_scraping').size().reset_index(name='cantidad')

    fig = px.line(ofertas_por_fecha, x='fecha_scraping', y='cantidad', markers=True)
    fig.update_traces(line_color='#667eea', line_width=3, marker_size=8)
    fig.update_layout(
        xaxis_title="Fecha de Scraping", yaxis_title="Ofertas",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300
    )
    return fig

def crear_grafico_publicaciones_diarias(df):
    """Gráfico de evolución de publicaciones de ofertas por fecha de publicación"""
    # Convertir fecha_publicacion_iso a datetime y extraer solo la fecha
    df_copy = df.copy()
    df_copy['fecha_publicacion'] = pd.to_datetime(df_copy['fecha_publicacion_iso'], errors='coerce')
    df_copy['fecha_pub_date'] = df_copy['fecha_publicacion'].dt.date

    # Agrupar por fecha de publicación
    ofertas_por_fecha_pub = df_copy.groupby('fecha_pub_date').size().reset_index(name='cantidad')
    ofertas_por_fecha_pub = ofertas_por_fecha_pub.sort_values('fecha_pub_date')

    fig = px.line(ofertas_por_fecha_pub, x='fecha_pub_date', y='cantidad', markers=True)
    fig.update_traces(line_color='#f093fb', line_width=3, marker_size=8)
    fig.update_layout(
        xaxis_title="Fecha de Publicación de la Oferta",
        yaxis_title="Ofertas Publicadas",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300
    )
    return fig

def crear_grafico_empresas(df):
    """Top empresas"""
    top_empresas = df[df['empresa'].notna()].groupby('empresa').size().sort_values(ascending=False).head(15)

    fig = px.bar(
        x=top_empresas.values, y=top_empresas.index,
        orientation='h', color=top_empresas.values,
        color_continuous_scale='Purples'
    )
    fig.update_layout(
        xaxis_title="Ofertas", yaxis_title="",
        showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    return fig

def crear_grafico_keywords(df_keywords):
    """Top keywords productivos"""
    top_keywords = df_keywords.head(20)

    fig = px.bar(
        top_keywords, x='total_ofertas', y='keyword',
        orientation='h',
        color='total_ofertas',
        color_continuous_scale='Viridis',
        title="Top 20 Keywords Más Productivos (Datos Reales)"
    )
    fig.update_layout(
        xaxis_title="Ofertas Encontradas",
        yaxis_title="",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        height=600
    )
    return fig

def crear_grafico_evolucion_keywords(df_ofertas, df_keywords, top_n=10):
    """
    Gráfico de evolución temporal de los top N keywords más demandados
    basado en fecha de PUBLICACIÓN de ofertas (no fecha de scraping)
    """
    import re

    # Obtener top N keywords más frecuentes
    top_keywords = df_keywords.head(top_n)['keyword'].tolist()

    # Preparar dataframe de ofertas con fechas
    df_copy = df_ofertas.copy()
    df_copy['fecha_publicacion'] = pd.to_datetime(df_copy['fecha_publicacion_iso'], errors='coerce')
    df_copy['fecha_pub_date'] = df_copy['fecha_publicacion'].dt.date
    df_copy = df_copy.dropna(subset=['fecha_pub_date'])

    # Diccionario para almacenar series temporales por keyword
    datos_evolucion = []

    for keyword in top_keywords:
        # Crear patrón regex case-insensitive
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        # Filtrar ofertas que contienen este keyword
        df_keyword = df_copy[
            df_copy['titulo'].str.contains(keyword, case=False, na=False) |
            df_copy['descripcion'].str.contains(keyword, case=False, na=False)
        ]

        # Contar ofertas por fecha de publicación
        ofertas_por_fecha = df_keyword.groupby('fecha_pub_date').size().reset_index(name='cantidad')
        ofertas_por_fecha['keyword'] = keyword

        datos_evolucion.append(ofertas_por_fecha)

    if not datos_evolucion:
        # Si no hay datos, crear gráfico vacío
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos suficientes para mostrar evolución temporal",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#666")
        )
        return fig

    # Combinar todos los datos
    df_evolucion = pd.concat(datos_evolucion, ignore_index=True)

    # Crear gráfico de líneas múltiples
    fig = px.line(
        df_evolucion,
        x='fecha_pub_date',
        y='cantidad',
        color='keyword',
        markers=True,
        title=f'Evolución Temporal de los {top_n} Keywords Más Demandados'
    )

    fig.update_layout(
        xaxis_title="Fecha de Publicación de la Oferta",
        yaxis_title="Cantidad de Ofertas Publicadas",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        height=450,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            title="Keyword"
        )
    )

    fig.update_traces(line_width=2, marker_size=6)

    return fig

def crear_grafico_completitud(df_completitud):
    """Gráfico de completitud de campos"""
    df_completitud = df_completitud.sort_values('completitud', ascending=True)

    fig = px.bar(
        df_completitud, x='completitud', y='campo',
        orientation='h',
        color='completitud',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100],
        title="Completitud de Campos (%)"
    )
    fig.update_layout(
        xaxis_title="Completitud (%)",
        yaxis_title="",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    return fig

def crear_tabla_alertas(df_alertas):
    """Tabla de alertas"""
    if df_alertas.empty:
        return html.Div("No hay alertas registradas", style={'padding': '20px', 'textAlign': 'center'})

    filas = []
    for _, row in df_alertas.head(10).iterrows():
        color_map = {'ERROR': '#ff4444', 'WARNING': '#ffaa00', 'INFO': '#4444ff'}
        color = color_map.get(row['level'], '#666')

        filas.append(
            html.Tr([
                html.Td(row['timestamp'][:19], style={'fontSize': '12px'}),
                html.Td(row['level'], style={'color': color, 'fontWeight': 'bold'}),
                html.Td(row['type'], style={'fontSize': '12px'}),
                html.Td(row['message'], style={'fontSize': '12px'}),
            ])
        )

    tabla = html.Table([
        html.Thead(
            html.Tr([
                html.Th('Timestamp'),
                html.Th('Nivel'),
                html.Th('Tipo'),
                html.Th('Mensaje'),
            ])
        ),
        html.Tbody(filas)
    ], style={'width': '100%', 'borderCollapse': 'collapse'})

    return tabla

# ============================================================================
# LAYOUT CON TABS
# ============================================================================

def crear_layout():
    """Layout con tabs"""
    stats = cargar_estadisticas()

    return html.Div([
        # Header
        html.Div([
            html.H1("Dashboard de Monitoreo - Bumeran Scraping v2",
                   style={'margin': '0', 'fontSize': '28px'}),
            html.P(f"Última actualización: {stats['ultima_actualizacion']}",
                  style={'margin': '5px 0 0 0', 'opacity': '0.9'})
        ], className='header'),

        # Estadísticas principales
        html.Div([
            html.Div([
                html.Div('Total Ofertas', className='stat-label'),
                html.Div(f"{stats['total_ofertas']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('Empresas', className='stat-label'),
                html.Div(f"{stats['empresas_unicas']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('IDs Rastreados', className='stat-label'),
                html.Div(f"{stats['ids_tracking']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('Keywords Productivos', className='stat-label'),
                html.Div(f"{stats['keywords_productivos']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('Efectividad Keywords', className='stat-label'),
                html.Div(f"{stats['keywords_productivos']/stats['total_keywords']*100:.1f}%", className='stat-value')
            ], className='stat-card'),
        ], className='stats-container'),

        # Tabs
        html.Div([
            dcc.Tabs(id='tabs', value='tab-overview', children=[
                dcc.Tab(label='📊 Overview', value='tab-overview'),
                dcc.Tab(label='🔑 Keywords', value='tab-keywords'),
                dcc.Tab(label='📋 Calidad de Datos', value='tab-calidad'),
                dcc.Tab(label='⚠️ Alertas', value='tab-alertas'),
                dcc.Tab(label='💾 Datos', value='tab-datos'),
                dcc.Tab(label='📖 Diccionario', value='tab-diccionario'),
            ]),
            html.Div(id='tabs-content', className='tab-content')
        ], style={'margin': '20px'}),

        # Auto-refresh cada 5 minutos
        dcc.Interval(
            id='interval-component',
            interval=5*60*1000,
            n_intervals=0
        )
    ])

# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs', 'value')]
)
def render_tab_content(tab):
    """Renderiza contenido según tab seleccionada"""

    if tab == 'tab-overview':
        df = cargar_ofertas()
        return html.Div([
            # Gráfico de publicaciones diarias
            html.Div([
                html.H3("Evolución Diaria de Publicación de Ofertas",
                       style={'marginBottom': '15px', 'color': '#333'}),
                html.P("Muestra cuándo se publicaron originalmente las ofertas en Bumeran",
                      style={'fontSize': '13px', 'color': '#666', 'marginBottom': '10px'}),
                dcc.Graph(figure=crear_grafico_publicaciones_diarias(df))
            ], className='chart-container'),

            # Gráfico temporal de scraping
            html.Div([
                html.H3("Evolución de Ofertas Scrapeadas", style={'marginBottom': '15px', 'color': '#333'}),
                html.P("Muestra cuándo fueron capturadas las ofertas por nuestro sistema",
                      style={'fontSize': '13px', 'color': '#666', 'marginBottom': '10px'}),
                dcc.Graph(figure=crear_grafico_temporal(df))
            ], className='chart-container'),

            # Top empresas
            html.Div([
                html.H3("Top 15 Empresas", style={'marginBottom': '15px', 'color': '#333'}),
                dcc.Graph(figure=crear_grafico_empresas(df))
            ], className='chart-container'),
        ])

    elif tab == 'tab-keywords':
        df_keywords = cargar_keywords()

        if df_keywords.empty:
            return html.Div([
                html.H3("Keywords", style={'padding': '20px'}),
                html.P("No hay datos de keywords disponibles aún.",
                      style={'textAlign': 'center', 'padding': '40px', 'color': '#666'})
            ])

        # Cargar ofertas para el gráfico de evolución temporal
        df_ofertas = cargar_ofertas()

        return html.Div([
            # Gráfico de evolución temporal de keywords (por fecha de publicación)
            html.Div([
                html.H3(f"Evolución Temporal de los 10 Keywords Más Demandados",
                       style={'marginBottom': '15px', 'color': '#333'}),
                html.P("Basado en la fecha de PUBLICACIÓN de las ofertas (no la fecha de scraping)",
                      style={'fontSize': '13px', 'color': '#666', 'marginBottom': '10px'}),
                dcc.Graph(figure=crear_grafico_evolucion_keywords(df_ofertas, df_keywords, top_n=10))
            ], className='chart-container'),

            # Gráfico de Top 20 Keywords
            html.Div([
                html.H3(f"Top 20 Keywords Más Eficientes",
                       style={'marginBottom': '15px', 'color': '#333'}),
                html.P(f"Mostrando los 20 keywords más productivos de {len(df_keywords):,} totales",
                      style={'fontSize': '13px', 'color': '#666', 'marginBottom': '10px'}),
                dcc.Graph(figure=crear_grafico_keywords(df_keywords))
            ], className='chart-container'),

            # Tabla completa de TODOS los keywords
            html.Div([
                html.H3(f"TODOS los Keywords Ordenados por Eficiencia ({len(df_keywords):,} keywords productivos)",
                       style={'marginBottom': '15px', 'color': '#333'}),
                html.P("Ordenados de mayor a menor cantidad de ofertas encontradas. Use los filtros para buscar keywords específicos.",
                      style={'fontSize': '13px', 'color': '#666', 'marginBottom': '10px'}),

                # Botones de descarga
                html.Div([
                    html.Button(
                        "📊 Descargar Excel (TODOS los keywords)",
                        id="btn-download-excel-keywords-tab",
                        style={
                            'backgroundColor': '#28a745',
                            'color': 'white',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'marginRight': '10px'
                        }
                    ),
                    html.Button(
                        "📄 Descargar CSV (TODOS los keywords)",
                        id="btn-download-csv-keywords-tab",
                        style={
                            'backgroundColor': '#17a2b8',
                            'color': 'white',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px'
                        }
                    ),
                    dcc.Download(id="download-keywords-excel-tab"),
                    dcc.Download(id="download-keywords-csv-tab")
                ], style={'marginBottom': '15px'}),

                # Tabla interactiva con TODOS los keywords
                dash_table.DataTable(
                    id='table-keywords',
                    columns=[
                        {'name': 'Ranking', 'id': 'ranking'},
                        {'name': 'Keyword', 'id': 'keyword'},
                        {'name': 'Total Ofertas', 'id': 'total_ofertas'},
                        {'name': 'Ofertas Nuevas', 'id': 'total_nuevas'},
                        {'name': 'Veces Ejecutado', 'id': 'veces_ejecutado'},
                    ],
                    data=[{
                        'ranking': i + 1,
                        'keyword': row['keyword'],
                        'total_ofertas': row['total_ofertas'],
                        'total_nuevas': row['total_nuevas'],
                        'veces_ejecutado': row['veces_ejecutado']
                    } for i, (_, row) in enumerate(df_keywords.iterrows())],
                    page_size=50,
                    sort_action='native',
                    filter_action='native',
                    style_table={
                        'overflowX': 'auto',
                        'maxHeight': '600px',
                        'overflowY': 'auto'
                    },
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '13px',
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold',
                        'border': '1px solid #dee2e6'
                    },
                    style_data={
                        'border': '1px solid #dee2e6'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f8f9fa'
                        },
                        # Destacar top 10
                        {
                            'if': {'filter_query': '{ranking} <= 10'},
                            'backgroundColor': '#d4edda',
                            'fontWeight': 'bold'
                        }
                    ]
                )
            ], className='chart-container'),
        ])

    elif tab == 'tab-calidad':
        df_completitud = calcular_completitud()

        return html.Div([
            html.Div([
                html.H3(f"Análisis de Completitud de TODAS las {len(df_completitud)} Variables",
                       style={'marginBottom': '15px', 'color': '#333'}),
                html.P("Ordenadas de menor a mayor completitud (campos con problemas primero)",
                      style={'fontSize': '13px', 'color': '#666', 'marginBottom': '10px'}),
                dcc.Graph(figure=crear_grafico_completitud(df_completitud))
            ], className='chart-container'),

            html.Div([
                html.H3(f"Detalle de Completitud ({len(df_completitud)} variables)",
                       style={'marginBottom': '15px', 'color': '#333'}),
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th('Campo'),
                            html.Th('Completitud'),
                            html.Th('Completos'),
                            html.Th('Total'),
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(row['campo']),
                            html.Td(f"{row['completitud']:.1f}%",
                                   style={'color': '#00aa00' if row['completitud'] >= 90 else '#ff4444'}),
                            html.Td(f"{row['completos']:,}"),
                            html.Td(f"{row['total']:,}"),
                        ]) for _, row in df_completitud.iterrows()
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse'})
            ], className='chart-container'),
        ])

    elif tab == 'tab-alertas':
        df_alertas = cargar_alertas()

        return html.Div([
            html.Div([
                html.H3(f"Alertas del Sistema (Últimas {len(df_alertas)})",
                       style={'marginBottom': '15px', 'color': '#333'}),

                crear_tabla_alertas(df_alertas)
            ], className='chart-container'),
        ])

    elif tab == 'tab-datos':
        df = cargar_ofertas()
        df_keywords = cargar_keywords()

        # Preparar datos para tabla - TODAS LAS COLUMNAS (últimas 100 ofertas)
        df_tabla = df.head(100)

        # Reorganizar columnas para poner las más importantes primero
        columnas_principales = ['id_oferta', 'titulo', 'empresa', 'localizacion',
                               'modalidad_trabajo', 'tipo_trabajo', 'url_oferta',
                               'fecha_publicacion_iso', 'scrapeado_en']

        # Columnas restantes
        otras_columnas = [col for col in df_tabla.columns if col not in columnas_principales]

        # Reordenar: principales + otras
        columnas_ordenadas = columnas_principales + otras_columnas
        df_tabla = df_tabla[[col for col in columnas_ordenadas if col in df_tabla.columns]]

        return html.Div([
            # Tabla de Ofertas
            html.Div([
                html.H3(f"Últimas 100 Ofertas - TODAS las {len(df_tabla.columns)} columnas (Total en DB: {len(df):,})",
                       style={'marginBottom': '15px', 'color': '#333'}),

                # Botones de descarga para Ofertas
                html.Div([
                    html.Button(
                        "📊 Descargar Excel (TODAS las ofertas)",
                        id="btn-download-excel-ofertas",
                        style={
                            'backgroundColor': '#28a745',
                            'color': 'white',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'marginRight': '10px'
                        }
                    ),
                    html.Button(
                        "📄 Descargar CSV (TODAS las ofertas)",
                        id="btn-download-csv-ofertas",
                        style={
                            'backgroundColor': '#17a2b8',
                            'color': 'white',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px'
                        }
                    ),
                    dcc.Download(id="download-ofertas-excel"),
                    dcc.Download(id="download-ofertas-csv")
                ], style={'marginBottom': '15px'}),

                dash_table.DataTable(
                    data=df_tabla.to_dict('records'),
                    columns=[{'name': col, 'id': col} for col in df_tabla.columns],
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '12px',
                        'fontFamily': 'Segoe UI'
                    },
                    style_header={
                        'backgroundColor': '#667eea',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f9f9f9'
                        }
                    ],
                    filter_action='native',
                    sort_action='native',
                    sort_mode='multi'
                )
            ], className='chart-container'),

            # Tabla de Keywords
            html.Div([
                html.H3(f"Keywords Productivos (Total: {len(df_keywords):,})",
                       style={'marginBottom': '15px', 'color': '#333'}),

                # Botones de descarga para Keywords
                html.Div([
                    html.Button(
                        "📊 Descargar Excel (Keywords)",
                        id="btn-download-excel-keywords",
                        style={
                            'backgroundColor': '#28a745',
                            'color': 'white',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'marginRight': '10px'
                        }
                    ),
                    html.Button(
                        "📄 Descargar CSV (Keywords)",
                        id="btn-download-csv-keywords",
                        style={
                            'backgroundColor': '#17a2b8',
                            'color': 'white',
                            'padding': '10px 20px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px'
                        }
                    ),
                    dcc.Download(id="download-keywords-excel"),
                    dcc.Download(id="download-keywords-csv")
                ], style={'marginBottom': '15px'}),

                dash_table.DataTable(
                    data=df_keywords.to_dict('records'),
                    columns=[{'name': col, 'id': col} for col in df_keywords.columns],
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '12px',
                        'fontFamily': 'Segoe UI'
                    },
                    style_header={
                        'backgroundColor': '#667eea',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f9f9f9'
                        }
                    ],
                    filter_action='native',
                    sort_action='native',
                    sort_mode='multi'
                )
            ], className='chart-container'),
        ])

    elif tab == 'tab-diccionario':
        # Diccionario de datos con TODAS las 38 variables
        diccionario = {
            'id_oferta': 'Identificador único de la oferta laboral (clave primaria)',
            'id_empresa': 'ID de la empresa que publica la oferta',
            'titulo': 'Título del puesto de trabajo',
            'empresa': 'Nombre de la empresa que publica la oferta',
            'descripcion': 'Descripción completa del puesto y responsabilidades',
            'confidencial': 'Indica si la oferta es confidencial (1=Sí, 0=No)',
            'localizacion': 'Ubicación geográfica del puesto',
            'modalidad_trabajo': 'Modalidad (Presencial, Remoto, Híbrido)',
            'tipo_trabajo': 'Tipo de contrato (Full-time, Part-time, Freelance, etc.)',
            'fecha_publicacion_original': 'Fecha de publicación original de Bumeran',
            'fecha_hora_publicacion_original': 'Fecha y hora de publicación original',
            'fecha_modificado_original': 'Fecha de última modificación original',
            'fecha_publicacion_iso': 'Fecha de publicación en formato ISO 8601',
            'fecha_hora_publicacion_iso': 'Fecha y hora en formato ISO 8601',
            'fecha_modificado_iso': 'Fecha de modificación en formato ISO 8601',
            'fecha_publicacion_datetime': 'Fecha publicación convertida a datetime',
            'fecha_hora_publicacion_datetime': 'Fecha y hora convertida a datetime',
            'fecha_modificado_datetime': 'Fecha modificación convertida a datetime',
            'cantidad_vacantes': 'Número de vacantes disponibles para este puesto',
            'apto_discapacitado': 'Apto para personas con discapacidad (1=Sí, 0=No)',
            'id_area': 'ID del área o sector profesional',
            'id_subarea': 'ID de la subárea o especialidad',
            'id_pais': 'ID del país donde se encuentra la oferta',
            'logo_url': 'URL del logo de la empresa',
            'empresa_validada': 'Empresa verificada por Bumeran (1=Sí, 0=No)',
            'empresa_pro': 'Empresa con cuenta PRO en Bumeran (1=Sí, 0=No)',
            'promedio_empresa': 'Promedio de calificación de la empresa',
            'plan_publicacion_id': 'ID del plan de publicación contratado',
            'plan_publicacion_nombre': 'Nombre del plan de publicación',
            'portal': 'Portal desde donde se publicó (Bumeran, etc.)',
            'tipo_aviso': 'Tipo de aviso (Standard, Premium, etc.)',
            'tiene_preguntas': 'Indica si la oferta incluye preguntas (1=Sí, 0=No)',
            'salario_obligatorio': 'Requiere especificar salario (1=Sí, 0=No)',
            'alta_revision_perfiles': 'Indica alta revisión de perfiles (1=Sí, 0=No)',
            'guardado': 'Oferta guardada/marcada (1=Sí, 0=No)',
            'gptw_url': 'URL de Great Place to Work si aplica',
            'url_oferta': 'URL completa de la oferta en Bumeran',
            'scrapeado_en': 'Fecha y hora en que fue scrapeada la oferta'
        }

        # Crear DataFrame para mostrar en tabla
        df_diccionario = pd.DataFrame([
            {'Variable': k, 'Definición': v} for k, v in diccionario.items()
        ])

        return html.Div([
            html.H2("Diccionario de Datos - Variables Scrapeadas",
                   style={'color': '#667eea', 'marginBottom': '20px'}),

            html.P(f"Total de variables: {len(diccionario)}",
                  style={'fontSize': '16px', 'color': '#555', 'marginBottom': '20px'}),

            # Tabla con el diccionario
            html.Div([
                dash_table.DataTable(
                    data=df_diccionario.to_dict('records'),
                    columns=[
                        {'name': 'Variable', 'id': 'Variable'},
                        {'name': 'Definición', 'id': 'Definición'}
                    ],
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '15px',
                        'fontSize': '13px',
                        'fontFamily': 'Segoe UI',
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    },
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'Variable'},
                            'width': '30%',
                            'fontWeight': 'bold',
                            'backgroundColor': '#f0f0f0'
                        },
                        {
                            'if': {'column_id': 'Definición'},
                            'width': '70%'
                        }
                    ],
                    style_header={
                        'backgroundColor': '#667eea',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'fontSize': '14px'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f9f9f9'
                        }
                    ],
                    filter_action='native',
                    sort_action='native'
                )
            ], className='chart-container'),

            # Información adicional
            html.Div([
                html.H3("Notas Importantes:", style={'color': '#667eea', 'marginTop': '30px'}),
                html.Ul([
                    html.Li("Todas las variables provienen directamente de la API de Bumeran"),
                    html.Li("Los campos con valor 1/0 son booleanos (Sí/No)"),
                    html.Li("Algunas variables pueden tener valores NULL si no están disponibles en la fuente"),
                    html.Li("Las fechas se almacenan en múltiples formatos para facilitar análisis"),
                    html.Li("La variable 'scrapeado_en' registra cuándo se capturó cada oferta")
                ], style={'fontSize': '14px', 'lineHeight': '1.8'})
            ], className='chart-container', style={'marginTop': '20px'})
        ])

# ============================================================================
# CALLBACKS DE DESCARGA
# ============================================================================

@app.callback(
    Output("download-ofertas-excel", "data"),
    [Input("btn-download-excel-ofertas", "n_clicks")],
    prevent_initial_call=True
)
def download_ofertas_excel(n_clicks):
    """Descarga TODAS las ofertas en formato Excel"""
    if n_clicks:
        # Cargar TODAS las ofertas
        df = cargar_ofertas()

        # Crear buffer en memoria
        buffer = io.BytesIO()

        # Guardar a Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Ofertas')

        buffer.seek(0)

        # Retornar datos para descarga
        return dcc.send_bytes(
            buffer.getvalue(),
            filename=f"ofertas_bumeran_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

@app.callback(
    Output("download-ofertas-csv", "data"),
    [Input("btn-download-csv-ofertas", "n_clicks")],
    prevent_initial_call=True
)
def download_ofertas_csv(n_clicks):
    """Descarga TODAS las ofertas en formato CSV"""
    if n_clicks:
        # Cargar TODAS las ofertas
        df = cargar_ofertas()

        # Convertir a CSV
        csv_string = df.to_csv(index=False, encoding='utf-8-sig')

        # Retornar datos para descarga
        return dict(
            content=csv_string,
            filename=f"ofertas_bumeran_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

@app.callback(
    Output("download-keywords-excel", "data"),
    [Input("btn-download-excel-keywords", "n_clicks")],
    prevent_initial_call=True
)
def download_keywords_excel(n_clicks):
    """Descarga keywords en formato Excel"""
    if n_clicks:
        # Cargar keywords
        df = cargar_keywords()

        # Crear buffer en memoria
        buffer = io.BytesIO()

        # Guardar a Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Keywords')

        buffer.seek(0)

        # Retornar datos para descarga
        return dcc.send_bytes(
            buffer.getvalue(),
            filename=f"keywords_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

@app.callback(
    Output("download-keywords-csv", "data"),
    [Input("btn-download-csv-keywords", "n_clicks")],
    prevent_initial_call=True
)
def download_keywords_csv(n_clicks):
    """Descarga keywords en formato CSV"""
    if n_clicks:
        # Cargar keywords
        df = cargar_keywords()

        # Convertir a CSV
        csv_string = df.to_csv(index=False, encoding='utf-8-sig')

        # Retornar datos para descarga
        return dict(
            content=csv_string,
            filename=f"keywords_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

# Callbacks para descarga en Keywords Tab
@app.callback(
    Output("download-keywords-excel-tab", "data"),
    [Input("btn-download-excel-keywords-tab", "n_clicks")],
    prevent_initial_call=True
)
def download_keywords_excel_tab(n_clicks):
    """Descarga keywords desde tab Keywords en formato Excel"""
    if n_clicks:
        # Cargar keywords
        df = cargar_keywords()

        # Agregar columna de ranking
        df.insert(0, 'ranking', range(1, len(df) + 1))

        # Crear buffer en memoria
        buffer = io.BytesIO()

        # Guardar a Excel
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Keywords Performance')

        buffer.seek(0)

        # Retornar datos para descarga
        return dcc.send_bytes(
            buffer.getvalue(),
            filename=f"keywords_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

@app.callback(
    Output("download-keywords-csv-tab", "data"),
    [Input("btn-download-csv-keywords-tab", "n_clicks")],
    prevent_initial_call=True
)
def download_keywords_csv_tab(n_clicks):
    """Descarga keywords desde tab Keywords en formato CSV"""
    if n_clicks:
        # Cargar keywords
        df = cargar_keywords()

        # Agregar columna de ranking
        df.insert(0, 'ranking', range(1, len(df) + 1))

        # Convertir a CSV
        csv_string = df.to_csv(index=False, encoding='utf-8-sig')

        # Retornar datos para descarga
        return dict(
            content=csv_string,
            filename=f"keywords_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

# ============================================================================
# MAIN
# ============================================================================

app.layout = crear_layout()

if __name__ == '__main__':
    print("="*70)
    print("DASHBOARD DE MONITOREO v2 - BUMERAN SCRAPING")
    print("="*70)
    print()
    print(f"Base de datos: {DB_PATH}")
    print()

    if not DB_PATH.exists():
        print(f"ERROR: No se encontró la base de datos en {DB_PATH}")
        exit(1)

    print("Dashboard v2 iniciado exitosamente")
    print()
    print("NUEVO: Dashboard con tabs expandidas")
    print("- Tab Overview: Gráficos principales")
    print("- Tab Keywords: Performance de keywords (DATOS REALES)")
    print("- Tab Calidad: Análisis de completitud")
    print("- Tab Alertas: Sistema de alertas")
    print("- Tab Datos: Acceso completo a las 38 variables")
    print("- Tab Diccionario: Definiciones de todas las variables")
    print()
    print("Acceder en: http://localhost:8051")
    print()
    print("Presiona Ctrl+C para detener")
    print("="*70)
    print()

    app.run(debug=True, host='0.0.0.0', port=8051)
