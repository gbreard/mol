# Dashboard de Monitoreo v4 - Bumeran Scraping

## Descripción

Dashboard interactivo en Plotly Dash para monitorear y visualizar el sistema de scraping automático de ofertas laborales de Bumeran.

**Versión actual:** v4
**Base de datos:** 10,660 ofertas (actualizado 2025-11-03)
**Esquema:** Migración en curso de v1 a v2 con dual-write habilitado

## Características

### 📊 Visualizaciones Disponibles

1. **Estadísticas Principales (Tab Overview)**
   - Total de ofertas capturadas: 10,660
   - Ofertas únicas (sin duplicados)
   - Empresas únicas
   - IDs rastreados en tracking incremental

2. **Evolución Temporal**
   - Gráfico de línea mostrando ofertas scrapeadas por fecha
   - Permite identificar patrones y picos de scraping
   - Soporta formato ISO8601 con microsegundos

3. **Top Empresas**
   - Top 15 empresas con más ofertas publicadas
   - Visualización en barras horizontales

4. **Distribución por Modalidad**
   - Gráfico circular con distribución de modalidades de trabajo
   - (Presencial, Remoto, Híbrido, etc.)

5. **Distribución por Tipo**
   - Gráfico circular con tipos de trabajo
   - (Full-time, Part-time, Freelance, etc.)

6. **Top Ubicaciones**
   - Top 10 ubicaciones geográficas con más ofertas
   - Visualización en barras horizontales

7. **Tab Keywords (NUEVO en v3)**
   - Performance de keywords con datos reales
   - Análisis de efectividad de búsquedas

8. **Tab Calidad (NUEVO en v3)**
   - Análisis de completitud de datos
   - Detección de campos vacíos

9. **Tab Alertas (NUEVO en v3)**
   - Sistema de alertas automáticas
   - Monitoreo de anomalías

10. **Tab Datos (NUEVO en v3)**
    - Acceso completo a las 38 variables
    - Tabla interactiva con todos los datos

11. **Tab Diccionario (NUEVO en v3)**
    - Definiciones de todas las variables
    - Documentación de campos

12. **Tab Explorador (NUEVO en v3)**
    - Explora TODAS las 22 tablas de la base de datos
    - Navegación completa del esquema

### 🔄 Auto-Refresh

El dashboard se actualiza automáticamente cada 5 minutos para mostrar los datos más recientes de la base de datos.

## Instalación

### Dependencias

```bash
pip install dash plotly pandas
```

**Nota:** Si ya ejecutaste la instalación antes, las dependencias ya están instaladas.

## Uso

### Iniciar Dashboard

```bash
cd D:\OEDE\Webscrapping
python dashboard_scraping_v4.py
```

### Acceder

Abrir navegador en: **http://localhost:8052**

**Nota:** La versión v4 corre en puerto 8052 (versiones anteriores usaban 8050/8051)

### Detener

Presionar `Ctrl+C` en la terminal donde se ejecuta.

## Ejecución en Background (Opcional)

### Windows

```powershell
# Ejecutar en background
Start-Process python -ArgumentList "dashboard_scraping.py" -WindowStyle Hidden

# Para detener: buscar proceso y matarlo
Get-Process python | Where-Object {$_.MainWindowTitle -match "dashboard"} | Stop-Process
```

### Linux/Mac

```bash
# Ejecutar en background
nohup python dashboard_scraping.py > dashboard.log 2>&1 &

# Para detener
pkill -f dashboard_scraping.py
```

## Arquitectura

```
dashboard_scraping.py
│
├── Carga de Datos
│   ├── cargar_ofertas()        → Lee ofertas desde SQLite
│   └── cargar_estadisticas()   → Calcula métricas generales
│
├── Layout
│   ├── Header con estadísticas clave
│   ├── Gráfico temporal (línea)
│   ├── Gráfico empresas (barras)
│   ├── Gráficos modalidad/tipo (pie)
│   └── Gráfico ubicaciones (barras)
│
└── Callbacks
    └── actualizar_graficos()   → Auto-refresh cada 5min
```

## Configuración

### Cambiar Puerto

Editar `dashboard_scraping_v4.py` línea 1910:

```python
app.run(debug=True, host='0.0.0.0', port=8052)  # Cambiar 8052 por otro puerto
```

### Cambiar Intervalo de Actualización

Editar `dashboard_scraping.py` línea ~290:

```python
dcc.Interval(
    id='interval-component',
    interval=5*60*1000,  # Cambiar 5 (minutos) * 60 * 1000
    n_intervals=0
)
```

### Modo Producción (sin debug)

```python
app.run(debug=False, host='0.0.0.0', port=8050)
```

## Acceso Remoto

Para acceder desde otras máquinas en la red:

1. El dashboard ya está configurado en `host='0.0.0.0'`
2. Obtener IP de la máquina:
   ```bash
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```
3. Acceder desde otra máquina: `http://<IP_DE_LA_MAQUINA>:8050`

**Importante:** Asegurar que el firewall permita conexiones en el puerto 8050.

## Troubleshooting

### Error: "Port already in use"

```bash
# Windows
netstat -ano | findstr :8052
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8052 | xargs kill -9
```

### Error: "Database not found"

Verificar que existe `database/bumeran_scraping.db`:

```bash
ls database/bumeran_scraping.db
```

Si no existe, ejecutar primero el scraping para generar datos.

### Dashboard no carga datos

Verificar que hay datos en la base:

```python
python -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM ofertas')
print('Total ofertas:', cursor.fetchone()[0])
conn.close()
"
```

## Arquitectura de Base de Datos

### Migración v1 → v2 (En curso)

El sistema está en proceso de migración de esquema v1 a v2:

**Estado actual (2025-11-03):**
- **v1 (ofertas)**: 10,660 registros - Esquema denormalizado (39 campos)
- **v2 (ofertas_raw)**: 10,660 registros - Esquema JSON inmutable con SHA256
- **Sincronización**: 100% completa
- **Dual-write**: Habilitado en `database/config.py`

**Dashboard Operativo (v4):**
- Lee datos desde v1 (`ofertas` table)
- Soporta formato ISO8601 con microsegundos
- Muestra todas las 10,660 ofertas sincronizadas

**Documentación relacionada:**
- `database/migrations/README_MIGRACION_V1_V2.md` - Detalles completos de la migración
- `database/config.py` - Configuración de dual-write
- `database/db_manager.py` - Implementación de dual-write

## Próximas Mejoras

- [ ] Migrar consultas del dashboard a schema v2
- [ ] Filtros interactivos por fecha
- [ ] Búsqueda de ofertas en el dashboard
- [ ] Exportar visualizaciones como imágenes
- [ ] Análisis de keywords más productivos
- [ ] Comparación entre períodos
- [ ] Alertas visuales de anomalías

## Soporte

Para problemas o sugerencias, consultar:
- `README_DASHBOARD.md` - Esta documentación
- `database/migrations/README_MIGRACION_V1_V2.md` - Migración v1→v2
- `CONSOLIDACION_SCRAPING_COMPLETADA.md` - Documentación general
- `logs/scheduler_*.log` - Logs del sistema

---

**Última actualización:** 2025-11-03
**Versión:** 4.0
**Autor:** Claude Code
