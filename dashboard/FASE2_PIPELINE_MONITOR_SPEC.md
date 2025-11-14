# FASE 2: Pipeline Monitor Tab - Especificación de Implementación

**Fecha**: 2025-11-04
**Versión**: v4.5
**Prioridad**: ALTA (Prioridad #1 del usuario)

---

## 1. Resumen Ejecutivo

Implementación del **Tab Pipeline Monitor** para visualizar KPIs de eficiencia end-to-end del pipeline completo (Scraping → NLP → ESCO).

### Objetivo
Proporcionar visibilidad completa del pipeline de procesamiento de ofertas, identificando cuellos de botella y problemas en cada etapa.

### Beneficios
- ✅ Monitoreo en tiempo real de las 3 etapas del pipeline
- ✅ Identificación inmediata de ofertas con problemas
- ✅ KPIs de eficiencia y calidad por etapa
- ✅ Evolución temporal del pipeline completo
- ✅ Visibilidad de Circuit Breaker y Rate Limiter

---

## 2. Cambios Necesarios en `dashboard_scraping_v4.py`

### 2.1 CAMBIO #1: Agregar Imports (Línea ~28)

**Ubicación**: Después de `from pathlib import Path` (línea 27)

**Código a agregar**:
```python
# Importar módulos del dashboard modular
from dashboard import data_loaders as dl
from dashboard import components as comp
```

**Justificación**: Permite usar las funciones de `data_loaders.py` y componentes de `components.py` creados en FASE 1.

---

### 2.2 CAMBIO #2: Agregar Tab en la Definición (Línea 754)

**Ubicación**: Línea 754, PRIMERO en la lista de tabs (es prioridad #1)

**Código actual**:
```python
dcc.Tabs(id='tabs', value='tab-overview', children=[
    dcc.Tab(label='📊 Overview', value='tab-overview'),
    dcc.Tab(label='🔑 Keywords', value='tab-keywords'),
    # ... resto de tabs
```

**Código modificado**:
```python
dcc.Tabs(id='tabs', value='tab-pipeline', children=[  # Cambiar default a 'tab-pipeline'
    dcc.Tab(label='🔄 Pipeline Monitor', value='tab-pipeline'),  # NUEVO - Prioridad #1
    dcc.Tab(label='📊 Overview', value='tab-overview'),
    dcc.Tab(label='🔑 Keywords', value='tab-keywords'),
    # ... resto de tabs sin cambios
```

**Nota**: Cambiar el `value` default a `'tab-pipeline'` para que sea el tab que se muestre al iniciar.

---

### 2.3 CAMBIO #3: Agregar Callback para el Tab (Línea ~785)

**Ubicación**: Dentro de la función `render_tab_content()`, ANTES del caso `if tab == 'tab-overview':`

**Código a agregar**:

```python
@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs', 'value')]
)
def render_tab_content(tab):
    """Renderiza contenido según tab seleccionada"""

    # ========================================================================
    # TAB: PIPELINE MONITOR (NUEVO - PRIORIDAD #1)
    # ========================================================================
    if tab == 'tab-pipeline':
        # Cargar métricas del pipeline
        metrics = dl.cargar_pipeline_metrics()
        problemas_df = dl.cargar_ofertas_con_problemas_pipeline()
        temporal_df = dl.cargar_pipeline_temporal()

        # Circuit Breaker y Rate Limiter
        cb_stats = dl.cargar_circuit_breaker_stats()
        rl_stats = dl.cargar_rate_limiter_stats()

        return html.Div([
            # Header del tab
            comp.section_header(
                'Pipeline Monitor - Eficiencia End-to-End',
                'Monitoreo completo del pipeline: Scraping → NLP → ESCO'
            ),

            # ============================================================
            # SECCIÓN 1: KPIs PRINCIPALES (4 columnas)
            # ============================================================
            html.H4('📊 KPIs Principales', style={'margin-top': '20px', 'margin-bottom': '15px'}),

            comp.metric_row([
                {
                    'title': 'Ofertas Scrapeadas',
                    'value': f"{metrics['scraping']['total_ofertas']:,}",
                    'delta': f"Success Rate: {metrics['scraping']['success_rate']:.1f}%",
                    'delta_color': 'green' if metrics['scraping']['success_rate'] >= 90 else 'orange',
                    'color': 'primary'
                },
                {
                    'title': 'Procesadas con NLP',
                    'value': f"{metrics['nlp']['total_procesadas']:,}",
                    'delta': f"{metrics['nlp']['porcentaje_procesado']:.1f}% del total",
                    'delta_color': 'green' if metrics['nlp']['porcentaje_procesado'] >= 95 else 'orange',
                    'color': 'info'
                },
                {
                    'title': 'Matcheadas con ESCO',
                    'value': f"{metrics['esco']['total_matcheadas']:,}",
                    'delta': f"{metrics['esco']['porcentaje_matcheado']:.1f}% del total",
                    'delta_color': 'green' if metrics['esco']['porcentaje_matcheado'] >= 90 else 'orange',
                    'color': 'success'
                },
                {
                    'title': 'Pipeline Completeness',
                    'value': f"{metrics['calidad_global']['pipeline_completeness_rate']:.1f}%",
                    'delta': f"DQI: {metrics['calidad_global']['data_quality_index']:.2f}",
                    'delta_color': 'green' if metrics['calidad_global']['pipeline_completeness_rate'] >= 85 else 'red',
                    'color': 'warning'
                }
            ], columns=4),

            # ============================================================
            # SECCIÓN 2: MÉTRICAS POR ETAPA (3 columnas)
            # ============================================================
            html.H4('📈 Métricas Detalladas por Etapa', style={'margin-top': '30px', 'margin-bottom': '15px'}),

            html.Div([
                # Columna 1: SCRAPING
                html.Div([
                    comp.card_container(
                        '🌐 Etapa 1: Scraping',
                        [
                            html.P([
                                html.Strong('Total Ofertas: '),
                                f"{metrics['scraping']['total_ofertas']:,}"
                            ]),
                            html.P([
                                html.Strong('Success Rate: '),
                                f"{metrics['scraping']['success_rate']:.1f}%"
                            ]),
                            html.P([
                                html.Strong('Tiempo Promedio: '),
                                f"{metrics['scraping']['tiempo_promedio_segundos']:.1f}s"
                            ]),
                            html.P([
                                html.Strong('Ofertas/Segundo: '),
                                f"{metrics['scraping']['ofertas_por_segundo']:.2f}"
                            ]),
                            comp.progress_bar(
                                metrics['scraping']['success_rate'],
                                label=f"Success Rate: {metrics['scraping']['success_rate']:.1f}%",
                                color='success' if metrics['scraping']['success_rate'] >= 90 else 'warning'
                            )
                        ]
                    )
                ], style={'width': '33%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '0 5px'}),

                # Columna 2: NLP
                html.Div([
                    comp.card_container(
                        '🧠 Etapa 2: NLP Processing',
                        [
                            html.P([
                                html.Strong('Ofertas Procesadas: '),
                                f"{metrics['nlp']['total_procesadas']:,}"
                            ]),
                            html.P([
                                html.Strong('Score Promedio: '),
                                f"{metrics['nlp']['score_promedio']:.2f}/7"
                            ]),
                            html.P([
                                html.Strong('% Procesado: '),
                                f"{metrics['nlp']['porcentaje_procesado']:.1f}%"
                            ]),
                            html.P([
                                html.Strong('Gap (sin procesar): '),
                                f"{metrics['scraping']['total_ofertas'] - metrics['nlp']['total_procesadas']:,}"
                            ]),
                            comp.progress_bar(
                                metrics['nlp']['porcentaje_procesado'],
                                label=f"Cobertura: {metrics['nlp']['porcentaje_procesado']:.1f}%",
                                color='success' if metrics['nlp']['porcentaje_procesado'] >= 95 else 'danger'
                            )
                        ]
                    )
                ], style={'width': '33%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '0 5px'}),

                # Columna 3: ESCO
                html.Div([
                    comp.card_container(
                        '🎯 Etapa 3: ESCO Matching',
                        [
                            html.P([
                                html.Strong('Ofertas Matcheadas: '),
                                f"{metrics['esco']['total_matcheadas']:,}"
                            ]),
                            html.P([
                                html.Strong('Match Score Promedio: '),
                                f"{metrics['esco']['match_score_promedio']:.2f}"
                            ]),
                            html.P([
                                html.Strong('Skills Identificadas: '),
                                f"{metrics['esco']['total_skills']:,}"
                            ]),
                            html.P([
                                html.Strong('% Matcheado: '),
                                f"{metrics['esco']['porcentaje_matcheado']:.1f}%"
                            ]),
                            comp.progress_bar(
                                metrics['esco']['porcentaje_matcheado'],
                                label=f"Cobertura: {metrics['esco']['porcentaje_matcheado']:.1f}%",
                                color='success' if metrics['esco']['porcentaje_matcheado'] >= 90 else 'danger'
                            )
                        ]
                    )
                ], style={'width': '33%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '0 5px'})
            ], style={'display': 'flex', 'flex-wrap': 'wrap'}),

            # ============================================================
            # SECCIÓN 3: ALERTAS Y PROBLEMAS
            # ============================================================
            html.H4('⚠️ Ofertas con Problemas en el Pipeline',
                   style={'margin-top': '30px', 'margin-bottom': '15px'}),

            html.Div([
                html.P(f"Total ofertas con problemas: {len(problemas_df):,}",
                      style={'font-size': '14px', 'margin-bottom': '10px'}),

                comp.create_data_table(
                    problemas_df.head(20) if not problemas_df.empty else pd.DataFrame(),
                    table_id='table-problemas-pipeline',
                    page_size=10,
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{etapa_fallida} = "NLP NO PROCESADO"'},
                            'backgroundColor': '#fff3cd',
                            'color': '#856404'
                        },
                        {
                            'if': {'filter_query': '{etapa_fallida} = "ESCO NO MATCHEADO"'},
                            'backgroundColor': '#f8d7da',
                            'color': '#721c24'
                        }
                    ]
                ) if not problemas_df.empty else html.P('✅ No hay problemas detectados en el pipeline')
            ]),

            # ============================================================
            # SECCIÓN 4: EVOLUCIÓN TEMPORAL
            # ============================================================
            html.H4('📅 Evolución Temporal del Pipeline (Últimos 30 días)',
                   style={'margin-top': '30px', 'margin-bottom': '15px'}),

            dcc.Graph(
                figure=crear_grafico_pipeline_temporal(temporal_df)
            ) if not temporal_df.empty else html.P('Sin datos temporales'),

            # ============================================================
            # SECCIÓN 5: CIRCUIT BREAKER & RATE LIMITER
            # ============================================================
            html.H4('🔧 Sistema Operacional',
                   style={'margin-top': '30px', 'margin-bottom': '15px'}),

            html.Div([
                # Circuit Breaker
                html.Div([
                    comp.card_container(
                        'Circuit Breaker',
                        [
                            html.P('Estado actual: ') if not cb_stats.empty else html.P('⚠️ No hay datos de Circuit Breaker'),
                            comp.create_data_table(
                                cb_stats.head(10),
                                table_id='table-circuit-breaker',
                                page_size=5
                            ) if not cb_stats.empty else None
                        ]
                    )
                ], style={'width': '50%', 'display': 'inline-block', 'padding': '0 5px'}),

                # Rate Limiter
                html.Div([
                    comp.card_container(
                        'Rate Limiter',
                        [
                            html.P('Estadísticas de rate limiting:') if not rl_stats.empty else html.P('⚠️ No hay datos de Rate Limiter'),
                            comp.create_data_table(
                                rl_stats.head(10),
                                table_id='table-rate-limiter',
                                page_size=5
                            ) if not rl_stats.empty else None
                        ]
                    )
                ], style={'width': '50%', 'display': 'inline-block', 'padding': '0 5px'})
            ], style={'display': 'flex'})

        ], style={'padding': '20px'})

    # ========================================================================
    # Resto de tabs sin cambios (tab-overview, tab-keywords, etc.)
    # ========================================================================
    elif tab == 'tab-overview':
        # ... código existente sin cambios
```

---

### 2.4 CAMBIO #4: Agregar Función Auxiliar para Gráfico Temporal

**Ubicación**: Después de las funciones de carga de datos, antes de los callbacks (alrededor de línea 700)

**Código a agregar**:

```python
def crear_grafico_pipeline_temporal(df):
    """
    Crea gráfico de evolución temporal del pipeline.

    Args:
        df: DataFrame con columnas fecha, ofertas_scrapeadas, ofertas_nlp, ofertas_esco

    Returns:
        Figura de Plotly
    """
    if df.empty:
        return go.Figure()

    fig = go.Figure()

    # Línea 1: Ofertas scrapeadas
    fig.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['ofertas_scrapeadas'],
        name='Scrapeadas',
        mode='lines+markers',
        line=dict(color='#007bff', width=2),
        marker=dict(size=6)
    ))

    # Línea 2: Ofertas procesadas con NLP
    fig.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['ofertas_nlp'],
        name='Procesadas NLP',
        mode='lines+markers',
        line=dict(color='#17a2b8', width=2),
        marker=dict(size=6)
    ))

    # Línea 3: Ofertas matcheadas con ESCO
    fig.add_trace(go.Scatter(
        x=df['fecha'],
        y=df['ofertas_esco'],
        name='Matcheadas ESCO',
        mode='lines+markers',
        line=dict(color='#28a745', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title='Evolución del Pipeline por Día',
        xaxis_title='Fecha',
        yaxis_title='Número de Ofertas',
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=400
    )

    return fig
```

---

## 3. Resumen de Archivos Afectados

| Archivo | Tipo de Cambio | Líneas Afectadas | Complejidad |
|---------|---------------|------------------|-------------|
| `dashboard_scraping_v4.py` | Modificación | ~28, ~754, ~785, ~700 | Media |

**Total de líneas nuevas a agregar**: ~200 líneas

---

## 4. Testing Recomendado

### 4.1 Test de Imports
```bash
python -c "from dashboard import data_loaders, components; print('✅ Imports OK')"
```

### 4.2 Test de Funciones de Datos
```python
from dashboard import data_loaders as dl

# Test cargar_pipeline_metrics
metrics = dl.cargar_pipeline_metrics()
print(f"✅ Pipeline metrics: {metrics.keys()}")

# Test cargar_ofertas_con_problemas_pipeline
problemas = dl.cargar_ofertas_con_problemas_pipeline()
print(f"✅ Problemas detectados: {len(problemas)}")
```

### 4.3 Test de Dashboard
```bash
python dashboard_scraping_v4.py
# Abrir http://localhost:8052
# Verificar que el tab "Pipeline Monitor" aparece primero
# Verificar que muestra datos correctamente
```

---

## 5. Roadmap de Implementación

### Paso 1: Backup
```bash
cp dashboard_scraping_v4.py dashboard_scraping_v4_backup.py
```

### Paso 2: Aplicar Cambio #1 (Imports)
- Agregar líneas de import después de línea 27

### Paso 3: Aplicar Cambio #4 (Función auxiliar)
- Agregar función `crear_grafico_pipeline_temporal()` alrededor de línea 700

### Paso 4: Aplicar Cambio #2 (Definición del Tab)
- Modificar línea 754 para agregar el nuevo tab

### Paso 5: Aplicar Cambio #3 (Callback)
- Agregar el bloque `if tab == 'tab-pipeline':` en la función `render_tab_content()`

### Paso 6: Testing
- Ejecutar tests de la sección 4
- Verificar que no hay errores de sintaxis
- Verificar que el dashboard carga correctamente

---

## 6. Troubleshooting

### Error: ModuleNotFoundError: No module named 'dashboard'
**Solución**: Verificar que el directorio `dashboard/` existe y contiene `__init__.py`

### Error: KeyError en metrics
**Solución**: Verificar que la base de datos tiene datos en las tablas `ofertas`, `ofertas_nlp`, `ofertas_esco_matching`

### Dashboard no carga
**Solución**: Verificar logs de error en consola, probablemente error de sintaxis en el código agregado

---

## 7. Próximos Pasos (FASE 3)

Una vez completada FASE 2, continuar con:
- FASE 3: Tab ESCO Analytics (3 sub-tabs)
- FASE 4: Tab Query Builder
- FASE 5: Mejoras a tabs existentes
- FASE 6: Optimizaciones finales

---

**Documento generado por**: Claude Code (OEDE)
**Fecha**: 2025-11-04
**Versión del documento**: 1.0
