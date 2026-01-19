"""
Dashboard de Monitoreo - Bumeran Scraping
==========================================

Dashboard interactivo para monitorear el sistema de scraping automático
de ofertas laborales de Bumeran.

Uso:
    python dashboard_scraping.py

Acceder en: http://localhost:8050
"""

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import json
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

DB_PATH = Path(__file__).parent / "database" / "bumeran_scraping.db"
TRACKING_FILE = Path(__file__).parent / "data" / "tracking" / "bumeran_scraped_ids.json"

# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

def cargar_ofertas():
    """Carga ofertas desde SQLite"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        id_oferta,
        titulo,
        empresa,
        localizacion,
        modalidad_trabajo,
        tipo_trabajo,
        fecha_publicacion_iso,
        scrapeado_en,
        url_oferta
    FROM ofertas
    ORDER BY scrapeado_en DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Convertir a datetime
    df['scrapeado_en'] = pd.to_datetime(df['scrapeado_en'])
    df['fecha_scraping'] = df['scrapeado_en'].dt.date

    return df

def cargar_estadisticas():
    """Carga estadísticas generales"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total ofertas
    cursor.execute('SELECT COUNT(*) FROM ofertas')
    total_ofertas = cursor.fetchone()[0]

    # Ofertas únicas
    cursor.execute('SELECT COUNT(DISTINCT id_oferta) FROM ofertas')
    ofertas_unicas = cursor.fetchone()[0]

    # Empresas únicas
    cursor.execute('SELECT COUNT(DISTINCT empresa) FROM ofertas WHERE empresa IS NOT NULL')
    empresas_unicas = cursor.fetchone()[0]

    # Fecha última actualización
    cursor.execute('SELECT MAX(scrapeado_en) FROM ofertas')
    ultima_actualizacion = cursor.fetchone()[0]

    conn.close()

    # Tracking
    with open(TRACKING_FILE, 'r') as f:
        tracking = json.load(f)

    return {
        'total_ofertas': total_ofertas,
        'ofertas_unicas': ofertas_unicas,
        'empresas_unicas': empresas_unicas,
        'ultima_actualizacion': ultima_actualizacion,
        'ids_tracking': len(tracking.get('scraped_ids', []))
    }

# ============================================================================
# CREAR APP DASH
# ============================================================================

app = dash.Dash(__name__)

# Estilo CSS personalizado
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard Scraping Bumeran</title>
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
                min-width: 200px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                text-align: center;
            }
            .stat-value {
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }
            .stat-label {
                font-size: 14px;
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
# LAYOUT
# ============================================================================

def crear_layout():
    """Crea el layout del dashboard"""

    # Cargar datos
    df = cargar_ofertas()
    stats = cargar_estadisticas()

    return html.Div([
        # Header
        html.Div([
            html.H1("Dashboard de Monitoreo - Bumeran Scraping",
                   style={'margin': '0', 'fontSize': '32px'}),
            html.P(f"Última actualización: {stats['ultima_actualizacion']}",
                  style={'margin': '5px 0 0 0', 'opacity': '0.9'})
        ], className='header'),

        # Estadísticas
        html.Div([
            html.Div([
                html.Div('Total Ofertas', className='stat-label'),
                html.Div(f"{stats['total_ofertas']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('Ofertas Únicas', className='stat-label'),
                html.Div(f"{stats['ofertas_unicas']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('Empresas', className='stat-label'),
                html.Div(f"{stats['empresas_unicas']:,}", className='stat-value')
            ], className='stat-card'),

            html.Div([
                html.Div('IDs Rastreados', className='stat-label'),
                html.Div(f"{stats['ids_tracking']:,}", className='stat-value')
            ], className='stat-card'),
        ], className='stats-container'),

        # Gráfico: Ofertas por fecha
        html.Div([
            html.H3("Evolución de Ofertas Scrapeadas",
                   style={'marginBottom': '20px', 'color': '#333'}),
            dcc.Graph(id='grafico-temporal', figure=crear_grafico_temporal(df))
        ], className='chart-container'),

        # Gráfico: Top empresas
        html.Div([
            html.H3("Top 15 Empresas con Más Ofertas",
                   style={'marginBottom': '20px', 'color': '#333'}),
            dcc.Graph(id='grafico-empresas', figure=crear_grafico_empresas(df))
        ], className='chart-container'),

        # Gráfico: Modalidad de trabajo
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Modalidad de Trabajo",
                           style={'marginBottom': '20px', 'color': '#333'}),
                    dcc.Graph(id='grafico-modalidad', figure=crear_grafico_modalidad(df))
                ], style={'width': '48%', 'display': 'inline-block'}),

                html.Div([
                    html.H3("Tipo de Trabajo",
                           style={'marginBottom': '20px', 'color': '#333'}),
                    dcc.Graph(id='grafico-tipo', figure=crear_grafico_tipo(df))
                ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
            ])
        ], className='chart-container'),

        # Gráfico: Top ubicaciones
        html.Div([
            html.H3("Top 10 Ubicaciones",
                   style={'marginBottom': '20px', 'color': '#333'}),
            dcc.Graph(id='grafico-ubicaciones', figure=crear_grafico_ubicaciones(df))
        ], className='chart-container'),

        # Intervalo para auto-refresh (cada 5 minutos)
        dcc.Interval(
            id='interval-component',
            interval=5*60*1000,  # 5 minutos en millisegundos
            n_intervals=0
        )
    ])

# ============================================================================
# FUNCIONES DE GRÁFICOS
# ============================================================================

def crear_grafico_temporal(df):
    """Gráfico de evolución temporal de ofertas"""
    ofertas_por_fecha = df.groupby('fecha_scraping').size().reset_index(name='cantidad')

    fig = px.line(ofertas_por_fecha,
                  x='fecha_scraping',
                  y='cantidad',
                  markers=True)

    fig.update_traces(line_color='#667eea', line_width=3, marker_size=8)
    fig.update_layout(
        xaxis_title="Fecha de Scraping",
        yaxis_title="Cantidad de Ofertas",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'size': 12}
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')

    return fig

def crear_grafico_empresas(df):
    """Gráfico de top empresas"""
    top_empresas = df[df['empresa'].notna()].groupby('empresa').size().sort_values(ascending=False).head(15)

    fig = px.bar(
        x=top_empresas.values,
        y=top_empresas.index,
        orientation='h',
        color=top_empresas.values,
        color_continuous_scale='Purples'
    )

    fig.update_layout(
        xaxis_title="Cantidad de Ofertas",
        yaxis_title="",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'size': 11}
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=False)

    return fig

def crear_grafico_modalidad(df):
    """Gráfico de modalidad de trabajo"""
    modalidad_counts = df[df['modalidad_trabajo'].notna()].groupby('modalidad_trabajo').size()

    fig = px.pie(
        values=modalidad_counts.values,
        names=modalidad_counts.index,
        color_discrete_sequence=px.colors.sequential.Purples_r
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        showlegend=True,
        font={'size': 11}
    )

    return fig

def crear_grafico_tipo(df):
    """Gráfico de tipo de trabajo"""
    tipo_counts = df[df['tipo_trabajo'].notna()].groupby('tipo_trabajo').size()

    fig = px.pie(
        values=tipo_counts.values,
        names=tipo_counts.index,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        showlegend=True,
        font={'size': 11}
    )

    return fig

def crear_grafico_ubicaciones(df):
    """Gráfico de top ubicaciones"""
    top_ubicaciones = df[df['localizacion'].notna()].groupby('localizacion').size().sort_values(ascending=False).head(10)

    fig = px.bar(
        x=top_ubicaciones.values,
        y=top_ubicaciones.index,
        orientation='h',
        color=top_ubicaciones.values,
        color_continuous_scale='Blues'
    )

    fig.update_layout(
        xaxis_title="Cantidad de Ofertas",
        yaxis_title="",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'size': 11}
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=False)

    return fig

# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    [Output('grafico-temporal', 'figure'),
     Output('grafico-empresas', 'figure'),
     Output('grafico-modalidad', 'figure'),
     Output('grafico-tipo', 'figure'),
     Output('grafico-ubicaciones', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def actualizar_graficos(n):
    """Actualiza todos los gráficos cada intervalo"""
    df = cargar_ofertas()

    return (
        crear_grafico_temporal(df),
        crear_grafico_empresas(df),
        crear_grafico_modalidad(df),
        crear_grafico_tipo(df),
        crear_grafico_ubicaciones(df)
    )

# ============================================================================
# MAIN
# ============================================================================

app.layout = crear_layout()

if __name__ == '__main__':
    print("="*70)
    print("DASHBOARD DE MONITOREO - BUMERAN SCRAPING")
    print("="*70)
    print()
    print(f"Conectando a base de datos: {DB_PATH}")
    print()

    # Verificar que existe la base de datos
    if not DB_PATH.exists():
        print(f"ERROR: No se encontró la base de datos en {DB_PATH}")
        print("Ejecute primero el scraping para generar datos.")
        exit(1)

    print("Dashboard iniciado exitosamente")
    print()
    print("Acceder en: http://localhost:8050")
    print()
    print("Presiona Ctrl+C para detener")
    print("="*70)
    print()

    app.run(debug=True, host='0.0.0.0', port=8050)
