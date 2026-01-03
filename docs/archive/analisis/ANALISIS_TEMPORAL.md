# Análisis Temporal de Ofertas Laborales

**Fecha**: 2025-10-17
**Versión**: 1.0
**Estado**: ✅ COMPLETADO

---

## 🎯 Resumen Ejecutivo

Se completó el **análisis temporal** de las 61 ofertas laborales scrapeadas de ZonaJobs, abarcando el período del **18 de agosto al 15 de octubre de 2025** (59 días).

El análisis incluye:

1. ✅ **Serie temporal diaria** con total de ofertas
2. ✅ **Serie temporal semanal** agrupada
3. ✅ **Descomposición por grupos ocupacionales ISCO** en ambas series
4. ✅ **Heatmap** de distribución por día de la semana y mes
5. ✅ **5 visualizaciones** de alta calidad (300 DPI)

---

## 📊 Resultados Clave

### Rango Temporal

- **Fecha inicio**: 18 de agosto de 2025
- **Fecha fin**: 15 de octubre de 2025
- **Días totales**: 59 días
- **Días con ofertas**: 32 días (54.2%)

### Análisis Diario

| Métrica | Valor |
|---------|-------|
| **Días con ofertas** | 32 |
| **Promedio diario** | 1.91 ofertas/día |
| **Máximo diario** | 4 ofertas |
| **Mínimo diario** | 1 oferta |
| **Mediana** | 2.0 ofertas |

### Análisis Semanal

| Métrica | Valor |
|---------|-------|
| **Semanas con ofertas** | 9 semanas |
| **Promedio semanal** | 6.78 ofertas/semana |
| **Máximo semanal** | 12 ofertas (Semana 34) |
| **Mínimo semanal** | 2 ofertas (Semana 40) |

---

## 📅 Distribución por Período

### Por Mes

| Mes | Ofertas | % del Total |
|-----|---------|-------------|
| **Septiembre** | 29 | 47.5% |
| **Agosto** | 19 | 31.1% |
| **Octubre** | 13 | 21.3% |

**Insights:**
- Septiembre fue el mes más activo con casi la mitad de las ofertas
- Octubre muestra una disminución (solo se capturaron primeras 2 semanas)
- Tendencia: pico en septiembre

### Por Semana del Año

| Semana | Período | Ofertas |
|--------|---------|---------|
| **W34** | 25-29 ago | 12 |
| **W37** | 15-18 sep | 10 |
| **W35** | 1-5 sep | 8 |
| **W33** | 18-22 ago | 7 |
| **W41** | 12-15 oct | 7 |
| **W39** | 30 sep - 3 oct | 6 |
| **W36** | 8-10 sep | 5 |
| **W38** | 22-26 sep | 4 |
| **W40** | 6-8 oct | 2 |

**Insights:**
- Mayor actividad en semanas 34 y 37
- Mínimo en semana 40 (principios de octubre)
- Variabilidad alta (CV ≈ 45%)

### Por Día de la Semana

| Día | Ofertas | % del Total |
|-----|---------|-------------|
| **Miércoles** | 20 | 32.8% |
| **Lunes** | 15 | 24.6% |
| **Martes** | 12 | 19.7% |
| **Viernes** | 7 | 11.5% |
| **Jueves** | 6 | 9.8% |
| **Domingo** | 1 | 1.6% |
| **Sábado** | 0 | 0% |

**Insights:**
- **Miércoles** es el día más activo (casi 1/3 de ofertas)
- Concentración en primera mitad de semana (Lun-Mie: 77%)
- Fin de semana prácticamente inactivo
- Patrón típico de publicación laboral

---

## 📈 Análisis por Grupo Ocupacional ISCO

### Distribución Temporal por Grupos

El análisis descompuesto muestra cómo se distribuyen los diferentes grupos ocupacionales a lo largo del tiempo:

#### Top 5 Grupos más Frecuentes

| Grupo ISCO | Descripción | Ofertas | % |
|------------|-------------|---------|---|
| **2** | Profesionales científicos e intelectuales | 12 | 26.7% |
| **3** | Técnicos y profesionales de nivel medio | 10 | 22.2% |
| **1** | Directores y gerentes | 7 | 15.6% |
| **4** | Personal de apoyo administrativo | 7 | 15.6% |
| **5** | Trabajadores de servicios y ventas | 5 | 11.1% |

### Patrones Temporales por Grupo

**Semana 34 (Pico: 12 ofertas)**:
- Mayoría de Grupo 2 (Profesionales)
- Alto componente de Grupo 3 (Técnicos)

**Semana 40 (Mínimo: 2 ofertas)**:
- Solo 2 grupos representados
- Baja diversidad ocupacional

---

## 📊 Visualizaciones Generadas

### 1. Serie Temporal Diaria (09_serie_temporal_diaria.png)

Gráfico de línea con:
- Número de ofertas por día
- Línea de tendencia
- Formato de fechas legible

**Observaciones:**
- Tendencia general ligeramente decreciente
- Varios picos de 3-4 ofertas
- Algunos días sin ofertas (gaps)

### 2. Serie Temporal Semanal (10_serie_temporal_semanal.png)

Gráfico de barras con:
- Total de ofertas por semana
- Línea de tendencia
- Valores sobre barras

**Observaciones:**
- Pico claro en semana 34 (12 ofertas)
- Caída pronunciada en semana 40 (2 ofertas)
- Recuperación en semana 41

### 3. Serie Diaria por Grupo ISCO - Apilado (11_serie_diaria_isco_stacked.png)

Gráfico de barras apiladas diario mostrando:
- Descomposición por grupo ocupacional
- Código de colores por grupo ISCO
- Evolución de composición ocupacional

**Observaciones:**
- Predominio de Grupos 2 y 3 (azules)
- Días con alta diversidad ocupacional
- Días monográficos (un solo grupo)

### 4. Serie Semanal por Grupo ISCO - Apilado (12_serie_semanal_isco_stacked.png)

Similar al anterior pero agregado semanalmente:
- Composición ocupacional por semana
- Mejor visualización de patrones

**Observaciones:**
- Semanas 34 y 37 muy diversas
- Semana 40 con mínima diversidad
- Balance relativo entre grupos principales

### 5. Heatmap Día de Semana × Mes (13_heatmap_dia_mes.png)

Mapa de calor mostrando:
- Filas: días de la semana
- Columnas: meses
- Intensidad: número de ofertas

**Observaciones:**
- Miércoles de septiembre: máxima intensidad
- Lunes consistentemente activo
- Fin de semana sin actividad
- Patrón claro de concentración mid-week

---

## 🔍 Insights y Hallazgos

### 1. Estacionalidad

- **No hay suficiente datos** para análisis estacional robusto (solo 2 meses)
- Septiembre muestra mayor actividad
- Posible tendencia decreciente hacia octubre

### 2. Patrón Semanal

- **Concentración en primera mitad de semana**
- Miércoles es el día preferido (33%)
- Fin de semana prácticamente sin ofertas
- Consistente con prácticas de RRHH (publicar lunes-miércoles)

### 3. Composición Ocupacional

- **Estable a lo largo del tiempo**: predominio de Grupos 2 y 3
- No hay concentraciones temporales de grupos específicos
- Diversidad ocupacional correlaciona con volumen total

### 4. Tendencias

- **Tendencia ligeramente decreciente** en período analizado
- Pico en última semana de agosto (W34)
- Caída en primera semana de octubre (W40)

---

## 📁 Archivos Generados

### Ubicación

```
D:\OEDE\Webscrapping\data\processed\
```

### Visualizaciones

```
charts/
├── 09_serie_temporal_diaria.png          # Serie diaria total
├── 10_serie_temporal_semanal.png         # Serie semanal total
├── 11_serie_diaria_isco_stacked.png      # Descomposición diaria ISCO
├── 12_serie_semanal_isco_stacked.png     # Descomposición semanal ISCO
└── 13_heatmap_dia_mes.png                # Heatmap día × mes
```

### Datos

```
processed/
├── ofertas_por_dia.csv                    # 32 días con datos
├── ofertas_por_semana.csv                 # 9 semanas con datos
├── ofertas_por_dia_isco.csv               # Descomposición diaria
├── ofertas_por_semana_isco.csv            # Descomposición semanal
└── estadisticas_temporales.json           # Todas las métricas
```

---

## 💡 Recomendaciones

### Para Análisis Futuros

1. **Ampliar período de captura**: Mínimo 6 meses para detectar estacionalidad
2. **Scraping periódico**: Automatizar captura semanal
3. **Análisis de series temporales**: ARIMA, descomposición estacional
4. **Comparación inter-anual**: Capturar mismo período en años diferentes

### Para el Mercado Laboral

1. **Publicar miércoles**: Mayor visibilidad estadística
2. **Evitar viernes-domingo**: Mínima actividad
3. **Septiembre activo**: Mayor volumen de ofertas
4. **Grupos 2-3 dominantes**: Enfocar en perfiles profesionales/técnicos

### Para el Dashboard

1. **Agregar panel temporal**: Integrar estas visualizaciones
2. **Filtros por período**: Permitir zoom en rangos específicos
3. **Alertas de tendencia**: Detectar cambios significativos
4. **Comparaciones**: Semana actual vs promedio

---

## 🚀 Próximos Pasos

### Corto Plazo

1. ✅ Integrar visualizaciones temporales en informe HTML principal
2. ✅ Actualizar documentación (INDEX.md)
3. ⬜ Agregar análisis temporal a dashboard interactivo
4. ⬜ Exportar tablas temporales a Excel consolidado

### Mediano Plazo

1. ⬜ Implementar scraping automático semanal
2. ⬜ Análisis de tendencias con más datos
3. ⬜ Predicción de volumen futuro (modelos ARIMA)
4. ⬜ Comparación con datos históricos

### Largo Plazo

1. ⬜ Sistema de alertas de anomalías temporales
2. ⬜ Análisis de ciclos y estacionalidad robusta
3. ⬜ Correlación con variables económicas (desempleo, PBI, etc.)
4. ⬜ Modelos predictivos de demanda laboral

---

## 📊 Resumen de Métricas

| Dimensión | Métrica Clave | Valor |
|-----------|---------------|-------|
| **Temporal** | Período total | 59 días |
| | Días con ofertas | 32 días (54.2%) |
| **Diaria** | Promedio | 1.91 ofertas/día |
| | Máximo | 4 ofertas |
| **Semanal** | Promedio | 6.78 ofertas/semana |
| | Máximo | 12 ofertas (W34) |
| **Mensual** | Mes más activo | Septiembre (29 ofertas) |
| **Semanal** | Día más activo | Miércoles (20 ofertas, 33%) |
| **Grupos ISCO** | Más frecuente | Grupo 2 (26.7%) |
| **Tendencia** | Dirección | Ligeramente decreciente |

---

## 📞 Recursos Relacionados

### Documentación

- [INDEX.md](../INDEX.md) - Índice principal del proyecto
- [ANALISIS_FINAL_MEJORADO.md](ANALISIS_FINAL_MEJORADO.md) - Análisis completo ESCO
- [ZONAJOBS_API_DOCUMENTATION.md](ZONAJOBS_API_DOCUMENTATION.md) - API de ZonaJobs

### Scripts

- **`analisis_temporal_ofertas.py`** - Script principal de análisis temporal
- **`zonajobs_scraper_final.py`** - Scraper de ofertas

### Ejecución

```bash
# Ejecutar análisis temporal
cd D:\OEDE\Webscrapping\scripts
python analisis_temporal_ofertas.py

# Ver resultados
cd ..\data\processed\charts
start 09_serie_temporal_diaria.png
```

---

**Desarrollado para OEDE**
**Fecha**: 2025-10-17
**Versión**: 1.0 Final
**Estado**: ✅ PRODUCCIÓN

---

## 🎉 Conclusiones

El análisis temporal revela patrones claros de publicación de ofertas laborales:

1. **Concentración mid-week**: Miércoles es el día óptimo
2. **Variabilidad semanal alta**: De 2 a 12 ofertas por semana
3. **Composición ocupacional estable**: Predominio consistente de Grupos 2-3
4. **Tendencia corto plazo**: Ligeramente decreciente

Con **más datos** (6+ meses), podremos:
- Detectar estacionalidad real
- Construir modelos predictivos
- Identificar ciclos económicos
- Optimizar estrategias de scraping

**¡Análisis temporal completado exitosamente!** 📊✅
