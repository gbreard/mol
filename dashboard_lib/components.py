"""
Dashboard Components - Bumeran Scraping v4.5
=============================================

Componentes visuales reutilizables para Plotly Dash.

Funciones:
- Metric Cards (KPIs)
- Status Badges
- Tables
- Charts
- Alerts
- Filters

Autor: Claude Code (OEDE)
Fecha: 2025-11-04
Versión: 4.5.0
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from dash import html, dcc, dash_table
import plotly.graph_objects as go
import plotly.express as px


# ===============================================================================
# SECCIÓN 1: METRIC CARDS (KPI Components)
# ===============================================================================

def metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = 'green',
    icon: Optional[str] = None,
    color: str = 'primary'
) -> html.Div:
    """
    Crea una tarjeta de métrica (KPI card).

    Args:
        title: Título del KPI
        value: Valor principal
        delta: Cambio/diferencia (opcional)
        delta_color: Color del delta ('green', 'red', 'orange')
        icon: Clase de ícono (opcional)
        color: Color del borde ('primary', 'success', 'warning', 'danger')

    Returns:
        Componente Dash
    """
    delta_colors = {
        'green': '#28a745',
        'red': '#dc3545',
        'orange': '#fd7e14',
        'blue': '#007bff'
    }

    border_colors = {
        'primary': '#007bff',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'info': '#17a2b8'
    }

    card_style = {
        'border-left': f'4px solid {border_colors.get(color, "#007bff")}',
        'padding': '15px',
        'margin-bottom': '15px',
        'background': 'white',
        'border-radius': '4px',
        'box-shadow': '0 1px 3px rgba(0,0,0,0.12)'
    }

    children = [
        html.H6(title, style={'color': '#666', 'margin-bottom': '10px', 'font-size': '14px'}),
        html.H3(value, style={'margin': '0', 'font-weight': 'bold'})
    ]

    if delta:
        children.append(
            html.Span(
                delta,
                style={
                    'color': delta_colors.get(delta_color, '#666'),
                    'font-size': '12px',
                    'margin-top': '5px',
                    'display': 'block'
                }
            )
        )

    return html.Div(children, style=card_style)


def metric_row(metrics: List[Dict[str, Any]], columns: int = 4) -> html.Div:
    """
    Crea una fila de métricas.

    Args:
        metrics: Lista de dicts con parámetros para metric_card
        columns: Número de columnas (2, 3, 4, 6)

    Returns:
        Row de Dash Bootstrap
    """
    col_width = 12 // columns

    cards = []
    for metric in metrics:
        card = html.Div(
            metric_card(**metric),
            style={'width': f'{col_width/12*100}%', 'display': 'inline-block', 'padding': '0 5px'}
        )
        cards.append(card)

    return html.Div(cards, style={'display': 'flex', 'flex-wrap': 'wrap'})


# ===============================================================================
# SECCIÓN 2: STATUS BADGES
# ===============================================================================

def status_badge(text: str, status: str = 'info') -> html.Span:
    """
    Crea un badge de estado.

    Args:
        text: Texto del badge
        status: Tipo ('success', 'warning', 'danger', 'info', 'secondary')

    Returns:
        Span con estilo de badge
    """
    colors = {
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'info': '#17a2b8',
        'secondary': '#6c757d',
        'primary': '#007bff'
    }

    return html.Span(
        text,
        style={
            'background-color': colors.get(status, '#17a2b8'),
            'color': 'white',
            'padding': '4px 8px',
            'border-radius': '4px',
            'font-size': '12px',
            'font-weight': '500',
            'display': 'inline-block'
        }
    )


def progress_bar(percentage: float, label: Optional[str] = None, color: str = 'primary') -> html.Div:
    """
    Crea una barra de progreso.

    Args:
        percentage: Porcentaje (0-100)
        label: Etiqueta opcional
        color: Color ('primary', 'success', 'warning', 'danger')

    Returns:
        Componente de barra de progreso
    """
    colors = {
        'primary': '#007bff',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545'
    }

    return html.Div([
        html.Div(
            label or f'{percentage:.1f}%',
            style={'margin-bottom': '5px', 'font-size': '12px'}
        ) if label or percentage else None,
        html.Div(
            html.Div(
                style={
                    'width': f'{min(100, max(0, percentage))}%',
                    'height': '100%',
                    'background-color': colors.get(color, '#007bff'),
                    'transition': 'width 0.3s ease'
                }
            ),
            style={
                'width': '100%',
                'height': '20px',
                'background-color': '#e9ecef',
                'border-radius': '4px',
                'overflow': 'hidden'
            }
        )
    ])


# ===============================================================================
# SECCIÓN 3: TABLES
# ===============================================================================

def create_data_table(
    df: pd.DataFrame,
    table_id: str,
    page_size: int = 10,
    columns_format: Optional[Dict[str, str]] = None,
    style_data_conditional: Optional[List] = None
) -> dash_table.DataTable:
    """
    Crea una tabla interactiva de Dash.

    Args:
        df: DataFrame con los datos
        table_id: ID único de la tabla
        page_size: Filas por página
        columns_format: Dict con formato de columnas (opcional)
        style_data_conditional: Estilos condicionales

    Returns:
        DataTable de Dash
    """
    # Configuración de columnas
    columns = []
    for col in df.columns:
        col_config = {'name': col, 'id': col}

        # Aplicar formato si existe
        if columns_format and col in columns_format:
            col_config['type'] = columns_format[col]

        columns.append(col_config)

    # Estilo base
    style_cell = {
        'textAlign': 'left',
        'padding': '10px',
        'font-size': '13px',
        'border': '1px solid #ddd'
    }

    style_header = {
        'backgroundColor': '#f8f9fa',
        'fontWeight': 'bold',
        'border': '1px solid #ddd'
    }

    style_data = {
        'backgroundColor': 'white',
        'border': '1px solid #ddd'
    }

    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=df.to_dict('records'),
        page_size=page_size,
        page_action='native',
        sort_action='native',
        filter_action='native',
        style_cell=style_cell,
        style_header=style_header,
        style_data=style_data,
        style_data_conditional=style_data_conditional or [],
        style_table={'overflowX': 'auto'}
    )


# ===============================================================================
# SECCIÓN 4: CHARTS
# ===============================================================================

def create_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    color: Optional[str] = None
) -> dcc.Graph:
    """
    Crea un gráfico de líneas.

    Args:
        df: DataFrame con datos
        x_col: Columna para eje X
        y_col: Columna para eje Y
        title: Título del gráfico
        color: Color de la línea (opcional)

    Returns:
        Componente Graph
    """
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title,
        color_discrete_sequence=[color] if color else None
    )

    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return dcc.Graph(figure=fig)


def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    orientation: str = 'v',
    color_col: Optional[str] = None
) -> dcc.Graph:
    """
    Crea un gráfico de barras.

    Args:
        df: DataFrame con datos
        x_col: Columna para eje X
        y_col: Columna para eje Y
        title: Título del gráfico
        orientation: 'v' (vertical) o 'h' (horizontal)
        color_col: Columna para colorear (opcional)

    Returns:
        Componente Graph
    """
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title,
        orientation=orientation,
        color=color_col
    )

    fig.update_layout(
        template='plotly_white',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return dcc.Graph(figure=fig)


def create_pie_chart(
    df: pd.DataFrame,
    names_col: str,
    values_col: str,
    title: str
) -> dcc.Graph:
    """
    Crea un gráfico de torta.

    Args:
        df: DataFrame con datos
        names_col: Columna con nombres/categorías
        values_col: Columna con valores
        title: Título del gráfico

    Returns:
        Componente Graph
    """
    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=title
    )

    fig.update_layout(
        template='plotly_white',
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return dcc.Graph(figure=fig)


def create_indicator(
    value: float,
    title: str,
    delta: Optional[float] = None,
    format_str: str = '.2f',
    color: str = '#007bff'
) -> dcc.Graph:
    """
    Crea un indicador numérico (gauge-style).

    Args:
        value: Valor principal
        title: Título del indicador
        delta: Cambio respecto a valor anterior
        format_str: Formato del número
        color: Color del indicador

    Returns:
        Componente Graph con indicador
    """
    fig = go.Figure(go.Indicator(
        mode='number+delta' if delta is not None else 'number',
        value=value,
        delta={'reference': value - delta} if delta else None,
        title={'text': title},
        number={'valueformat': format_str}
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return dcc.Graph(figure=fig, config={'displayModeBar': False})


# ===============================================================================
# SECCIÓN 5: ALERTS
# ===============================================================================

def alert_box(
    message: str,
    alert_type: str = 'info',
    dismissible: bool = False
) -> html.Div:
    """
    Crea una caja de alerta.

    Args:
        message: Mensaje de la alerta
        alert_type: Tipo ('success', 'warning', 'danger', 'info')
        dismissible: Si se puede cerrar

    Returns:
        Componente Div con alerta
    """
    colors = {
        'success': {'bg': '#d4edda', 'border': '#c3e6cb', 'text': '#155724'},
        'warning': {'bg': '#fff3cd', 'border': '#ffeaa7', 'text': '#856404'},
        'danger': {'bg': '#f8d7da', 'border': '#f5c6cb', 'text': '#721c24'},
        'info': {'bg': '#d1ecf1', 'border': '#bee5eb', 'text': '#0c5460'}
    }

    color_scheme = colors.get(alert_type, colors['info'])

    style = {
        'padding': '12px 20px',
        'margin-bottom': '15px',
        'border': f'1px solid {color_scheme["border"]}',
        'border-radius': '4px',
        'background-color': color_scheme['bg'],
        'color': color_scheme['text']
    }

    return html.Div(message, style=style)


def create_alert_list(alerts: List[Dict[str, str]]) -> html.Div:
    """
    Crea una lista de alertas.

    Args:
        alerts: Lista de dicts con 'message' y 'type'

    Returns:
        Div con lista de alertas
    """
    return html.Div([
        alert_box(alert['message'], alert.get('type', 'info'))
        for alert in alerts
    ])


# ===============================================================================
# SECCIÓN 6: FILTERS
# ===============================================================================

def date_range_filter(filter_id: str, label: str = 'Rango de fechas') -> html.Div:
    """
    Crea un filtro de rango de fechas.

    Args:
        filter_id: ID del componente
        label: Etiqueta del filtro

    Returns:
        Componente con DatePickerRange
    """
    return html.Div([
        html.Label(label, style={'font-weight': 'bold', 'margin-bottom': '5px'}),
        dcc.DatePickerRange(
            id=filter_id,
            display_format='DD/MM/YYYY',
            style={'margin-top': '5px'}
        )
    ], style={'margin-bottom': '15px'})


def dropdown_filter(
    filter_id: str,
    options: List[Dict[str, str]],
    label: str,
    multi: bool = False,
    placeholder: str = 'Seleccionar...'
) -> html.Div:
    """
    Crea un filtro dropdown.

    Args:
        filter_id: ID del componente
        options: Lista de opciones [{'label': '...', 'value': '...'}]
        label: Etiqueta del filtro
        multi: Si permite selección múltiple
        placeholder: Texto placeholder

    Returns:
        Componente con Dropdown
    """
    return html.Div([
        html.Label(label, style={'font-weight': 'bold', 'margin-bottom': '5px'}),
        dcc.Dropdown(
            id=filter_id,
            options=options,
            multi=multi,
            placeholder=placeholder,
            style={'margin-top': '5px'}
        )
    ], style={'margin-bottom': '15px'})


def slider_filter(
    filter_id: str,
    min_val: float,
    max_val: float,
    step: float,
    label: str,
    marks: Optional[Dict] = None
) -> html.Div:
    """
    Crea un filtro slider.

    Args:
        filter_id: ID del componente
        min_val: Valor mínimo
        max_val: Valor máximo
        step: Paso del slider
        label: Etiqueta del filtro
        marks: Marcas personalizadas (opcional)

    Returns:
        Componente con Slider
    """
    return html.Div([
        html.Label(label, style={'font-weight': 'bold', 'margin-bottom': '10px'}),
        dcc.Slider(
            id=filter_id,
            min=min_val,
            max=max_val,
            step=step,
            marks=marks,
            value=min_val,
            tooltip={'placement': 'bottom', 'always_visible': True}
        )
    ], style={'margin-bottom': '20px', 'padding': '0 10px'})


# ===============================================================================
# SECCIÓN 7: LOADING STATES
# ===============================================================================

def loading_spinner(component, spinner_type: str = 'default') -> dcc.Loading:
    """
    Envuelve un componente con un spinner de carga.

    Args:
        component: Componente a envolver
        spinner_type: Tipo de spinner ('default', 'circle', 'dot')

    Returns:
        Componente Loading
    """
    return dcc.Loading(
        component,
        type=spinner_type,
        color='#007bff'
    )


# ===============================================================================
# SECCIÓN 8: CONTAINERS
# ===============================================================================

def card_container(
    title: str,
    children,
    collapsible: bool = False,
    header_color: str = '#f8f9fa'
) -> html.Div:
    """
    Crea un contenedor tipo tarjeta.

    Args:
        title: Título de la tarjeta
        children: Contenido de la tarjeta
        collapsible: Si se puede colapsar
        header_color: Color del header

    Returns:
        Componente Div con estilo de tarjeta
    """
    return html.Div([
        html.Div(
            html.H5(title, style={'margin': '0', 'font-weight': '600'}),
            style={
                'padding': '15px',
                'background-color': header_color,
                'border-bottom': '1px solid #dee2e6'
            }
        ),
        html.Div(
            children,
            style={'padding': '15px'}
        )
    ], style={
        'border': '1px solid #dee2e6',
        'border-radius': '4px',
        'margin-bottom': '20px',
        'background': 'white'
    })


def section_header(title: str, subtitle: Optional[str] = None) -> html.Div:
    """
    Crea un encabezado de sección.

    Args:
        title: Título principal
        subtitle: Subtítulo (opcional)

    Returns:
        Componente Div con header
    """
    children = [
        html.H4(title, style={'margin': '0', 'color': '#2c3e50'})
    ]

    if subtitle:
        children.append(
            html.P(subtitle, style={'margin': '5px 0 0 0', 'color': '#7f8c8d', 'font-size': '14px'})
        )

    return html.Div(
        children,
        style={
            'margin-bottom': '20px',
            'padding-bottom': '10px',
            'border-bottom': '2px solid #3498db'
        }
    )


# ===============================================================================
# FIN DEL MÓDULO components.py
# ===============================================================================
# Total funciones: 23
# - Metric Cards: 2 funciones
# - Status Badges: 2 funciones
# - Tables: 1 función
# - Charts: 5 funciones
# - Alerts: 2 funciones
# - Filters: 3 funciones
# - Loading: 1 función
# - Containers: 2 funciones
# ===============================================================================
