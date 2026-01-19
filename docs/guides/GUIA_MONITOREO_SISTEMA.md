# GUÍA DE MONITOREO DEL SISTEMA AUTOMATIZADO

**Fecha de creación:** 2025-10-31
**Sistema:** Bumeran Scraping + Dashboard Automatizado
**Estado:** Operativo y Completamente Automatizado

---

## RESUMEN EJECUTIVO

Todo está configurado para funcionar **automáticamente**. Solo necesitas monitorear que el sistema esté funcionando correctamente.

**Lo que se automatizó:**
- Scraping ejecuta automáticamente Lunes y Jueves a las 8:00 AM
- Dashboard se actualiza solo con nuevos datos
- URL pública disponible para compartir con colegas
- Logs se guardan automáticamente

**Lo único que necesitas hacer:** Revisar ocasionalmente que todo funcione.

---

## ACCESOS RÁPIDOS

### Dashboard (Local)
```
http://localhost:8051
```

### Dashboard (Público - para compartir)
```
https://24f5f11dd7c9.ngrok-free.app
```
⚠️ **IMPORTANTE:** Esta URL pública cambia cada vez que reinicies ngrok. Si detenés ngrok y lo volves a iniciar, la URL será diferente.

### Logs del Sistema
```
D:\OEDE\Webscrapping\logs\
```

---

## VERIFICAR QUE TODO FUNCIONE

### 1. Verificar Dashboard

**Abrir:** http://localhost:8051

**¿Qué ver?**
- ✅ Dashboard carga correctamente
- ✅ Muestra datos actualizados
- ✅ Las 4 tabs funcionan: Overview, Keywords, Calidad, Alertas

**Si no carga:**
```bash
# Verificar si el dashboard está corriendo
netstat -ano | findstr :8051

# Si no está corriendo, iniciarlo:
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py
```

### 2. Verificar Tarea Programada

**PowerShell:**
```powershell
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Output esperado:**
```
TaskName : BumeranScrapingAutomatico
State    : Ready  (o Running si está ejecutando)
```

**Estados posibles:**
- `Ready` = Esperando próxima ejecución (NORMAL)
- `Running` = Ejecutándose ahora (NORMAL en Lunes/Jueves 8 AM)
- `Disabled` = Deshabilitado (PROBLEMA - ver sección Troubleshooting)

### 3. Verificar Última Ejecución

**PowerShell:**
```powershell
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico" | Get-ScheduledTaskInfo
```

**¿Qué ver?**
- `LastRunTime`: Última vez que corrió (debería ser Lunes o Jueves pasado)
- `NextRunTime`: Próxima ejecución programada
- `LastTaskResult`: 0 = Éxito, otro número = Error

### 4. Verificar Logs del Scraping

**Ubicación:**
```
D:\OEDE\Webscrapping\logs\
```

**Buscar archivo más reciente:**
```
scheduler_YYYY-MM-DD.log
```

**Abrir y buscar:**
- `[INFO] Iniciando scraping...`
- `[INFO] Scraping completado: X ofertas nuevas`
- `[SUCCESS]` = Todo bien
- `[ERROR]` = Hubo problemas (ver detalles)

**PowerShell - Ver últimas 50 líneas:**
```powershell
Get-Content D:\OEDE\Webscrapping\logs\scheduler_*.log -Tail 50
```

### 5. Verificar Base de Datos

**Contar ofertas actuales:**

```bash
cd D:\OEDE\Webscrapping
python -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM ofertas')
print(f'Total ofertas en DB: {cursor.fetchone()[0]:,}')
conn.close()
"
```

**Última oferta scrapeada:**

```bash
python -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute('SELECT MAX(scrapeado_en) FROM ofertas')
print(f'Última oferta scrapeada: {cursor.fetchone()[0]}')
conn.close()
"
```

### 6. Verificar Ngrok (URL Pública)

**¿Ngrok está corriendo?**
```bash
# Windows PowerShell
Get-Process ngrok -ErrorAction SilentlyContinue
```

**Si está corriendo:**
- Abrir: http://localhost:4040 (panel de control de ngrok)
- Ver URL pública actual
- Ver tráfico en tiempo real

**Si NO está corriendo:**
```bash
# Iniciar ngrok
ngrok http 8051
```

Copiar la URL que aparece en `Forwarding` (ej: https://abc123.ngrok-free.app)

---

## CALENDARIO DE EJECUCIÓN AUTOMÁTICA

### Scraping Programado

**Días:** Lunes y Jueves
**Hora:** 8:00 AM
**Duración estimada:** ~38 minutos
**Keywords procesados:** 1,148
**Modo:** Incremental (solo ofertas nuevas)

### ¿Qué pasa en cada ejecución?

1. **8:00 AM** - Windows inicia la tarea programada
2. **8:00-8:38 AM** - Scraping ejecutándose en segundo plano (pythonw)
3. **8:38 AM** - Datos guardados automáticamente en SQLite
4. **8:38 AM+** - Dashboard muestra nuevos datos (auto-refresh cada 5 min)

### Próximas Ejecuciones (Ejemplo)

Si hoy es viernes 1 de noviembre:
- **Próximo scraping:** Lunes 4 de noviembre a las 8:00 AM
- **Siguiente:** Jueves 7 de noviembre a las 8:00 AM

---

## COMANDOS ÚTILES

### Control de la Tarea Programada

**Ver estado:**
```powershell
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Iniciar manualmente:**
```powershell
Start-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Detener (si está corriendo):**
```powershell
Stop-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Habilitar (si está deshabilitada):**
```powershell
Enable-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Deshabilitar (pausar automatización):**
```powershell
Disable-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Ver historial de ejecuciones:**
```powershell
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=102} | Where-Object {$_.Message -like "*BumeranScrapingAutomatico*"} | Select-Object TimeCreated, Message -First 10
```

### Control del Dashboard

**Iniciar dashboard v2:**
```bash
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py
```

**Ver qué está usando el puerto 8051:**
```bash
netstat -ano | findstr :8051
```

**Matar proceso en puerto 8051:**
```bash
# 1. Encontrar PID
netstat -ano | findstr :8051
# 2. Matar proceso (reemplazar <PID>)
taskkill /PID <PID> /F
```

### Control de Ngrok

**Iniciar ngrok:**
```bash
ngrok http 8051
```

**Ver URL actual:**
- Abrir: http://localhost:4040

**Detener ngrok:**
- Presionar `Ctrl+C` en la ventana de ngrok

**Ver sesiones activas:**
```bash
ngrok tunnels list
```

### Análisis de Datos

**Ver keywords más productivos:**
```bash
cd D:\OEDE\Webscrapping
python -c "
import sqlite3
import pandas as pd
conn = sqlite3.connect('database/bumeran_scraping.db')
df = pd.read_sql_query('''
    SELECT keyword, SUM(ofertas_encontradas) as total
    FROM keywords_performance
    WHERE ofertas_encontradas > 0
    GROUP BY keyword
    ORDER BY total DESC
    LIMIT 10
''', conn)
print(df.to_string(index=False))
conn.close()
"
```

**Ver alertas recientes:**
```bash
python -c "
import sqlite3
import pandas as pd
conn = sqlite3.connect('database/bumeran_scraping.db')
df = pd.read_sql_query('''
    SELECT timestamp, level, type, message
    FROM alertas
    ORDER BY timestamp DESC
    LIMIT 10
''', conn)
print(df.to_string(index=False))
conn.close()
"
```

---

## COMPARTIR DASHBOARD CON COLEGAS

### Opción 1: URL Pública (Ngrok)

**Paso 1:** Asegurarte que ngrok esté corriendo
```bash
ngrok http 8051
```

**Paso 2:** Copiar URL de la línea `Forwarding`
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8051
```

**Paso 3:** Enviar URL a colegas por email/chat

**⚠️ IMPORTANTE:**
- La URL cambia cada vez que reinicies ngrok
- Versión gratuita: sesión expira después de 8 horas
- Solo funciona mientras tu PC y ngrok estén activos

### Opción 2: Red Local (Solo si están en la misma red)

**Paso 1:** Encontrar tu IP local
```powershell
ipconfig | findstr /i "IPv4"
```

**Paso 2:** Compartir con colegas:
```
http://TU_IP_LOCAL:8051
```

Ejemplo: `http://192.168.1.100:8051`

**Limitación:** Solo funciona si están en la misma red (oficina/WiFi)

---

## INTERPRETACIÓN DEL DASHBOARD

### Tab "Overview"

**¿Qué muestra?**
- Evolución temporal de ofertas scrapeadas
- Top 15 empresas con más ofertas
- Distribución por modalidad de trabajo (presencial/remoto/híbrido)
- Top 10 ubicaciones geográficas

**¿Qué vigilar?**
- Si la cantidad de ofertas nuevas disminuye drásticamente = posible problema con scraping

### Tab "Keywords"

**¿Qué muestra?**
- Top 20 keywords más productivos
- Tabla completa con todos los 1,340 keywords analizados
- Ranking de eficiencia (cuáles encuentran más ofertas)

**¿Qué vigilar?**
- Keywords con 0 ofertas consistentemente = considerar removerlos
- Nuevos keywords que aparecen en títulos pero no están en diccionario = agregarlos

### Tab "Calidad de Datos"

**¿Qué muestra?**
- Porcentaje de completitud de todas las 38 variables
- Gráfico de barras coloreado (verde=bueno, amarillo=regular, rojo=malo)

**¿Qué vigilar?**
- Completitud por debajo de 80% en campos críticos (titulo, empresa, descripcion)
- Caída brusca de completitud = posible cambio en estructura de Bumeran

### Tab "Alertas"

**¿Qué muestra?**
- Últimas 50 alertas del sistema
- Niveles: INFO (informativo), WARNING (atención), ERROR (problema)

**¿Qué vigilar?**
- Múltiples ERRORs recientes = revisar logs
- WARNING persistentes = considerar ajustes

### Tab "Datos"

**¿Qué muestra?**
- Tabla completa de todas las ofertas (paginada)
- Botones de descarga Excel/CSV

**¿Qué usar?**
- Descargar ofertas para análisis externo (Excel, Power BI, etc.)
- Filtrar y buscar ofertas específicas

---

## DESCARGA DE DATOS

### Desde Dashboard

**Ubicación:** Tab "Datos" o Tab "Keywords"

**Botones disponibles:**
1. **Descargar Ofertas Excel** - Todas las ofertas con 38 variables
2. **Descargar Ofertas CSV** - Mismo contenido en formato CSV
3. **Descargar Keywords Excel** - Ranking completo de keywords
4. **Descargar Keywords CSV** - Mismo contenido en formato CSV

**Nombres de archivo automáticos:**
- `ofertas_bumeran_YYYYMMDD_HHMMSS.xlsx`
- `ofertas_bumeran_YYYYMMDD_HHMMSS.csv`
- `keywords_performance_YYYYMMDD_HHMMSS.xlsx`
- `keywords_performance_YYYYMMDD_HHMMSS.csv`

### Desde Base de Datos (Comando Directo)

**Exportar ofertas a CSV:**
```bash
cd D:\OEDE\Webscrapping
python -c "
import sqlite3
import pandas as pd
conn = sqlite3.connect('database/bumeran_scraping.db')
df = pd.read_sql_query('SELECT * FROM ofertas', conn)
df.to_csv('ofertas_export.csv', index=False, encoding='utf-8-sig')
print(f'Exportadas {len(df):,} ofertas a ofertas_export.csv')
conn.close()
"
```

---

## TROUBLESHOOTING

### Problema: Dashboard no carga (localhost:8051 no responde)

**Causa probable:** Dashboard no está corriendo

**Solución:**
```bash
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py
```

Dejar la ventana abierta. Abrir navegador en http://localhost:8051

---

### Problema: Tarea programada no ejecuta scraping

**Verificar estado:**
```powershell
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Si State = Disabled:**
```powershell
Enable-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Si State = Ready pero no ejecuta:**
- Revisar que sea Lunes o Jueves
- Revisar que sea cerca de las 8:00 AM
- Ver logs en `D:\OEDE\Webscrapping\logs\`

**Si LastTaskResult != 0:**
```powershell
# Ver historial de errores
Get-ScheduledTaskInfo -TaskName "BumeranScrapingAutomatico"
```

**Solución drástica (reconfigurar):**
```powershell
cd D:\OEDE\Webscrapping
powershell -ExecutionPolicy Bypass -File setup_task.ps1
```

---

### Problema: Ngrok URL no funciona

**Verificar que ngrok esté corriendo:**
```bash
Get-Process ngrok -ErrorAction SilentlyContinue
```

**Si no está corriendo:**
```bash
ngrok http 8051
```

**Si muestra "502 Bad Gateway":**
- Causa: Dashboard no está corriendo
- Solución: Iniciar dashboard primero, luego ngrok

**Si la URL cambió:**
- Normal: ngrok genera nueva URL cada vez que se reinicia
- Solución: Copiar nueva URL de http://localhost:4040

---

### Problema: No hay ofertas nuevas en el scraping

**Verificar en logs:**
```
[INFO] Scraping completado: 0 ofertas nuevas
```

**Causas posibles:**
1. **Modo incremental funcionando correctamente** - Ya scrapeaste todas las ofertas nuevas
2. **Bumeran no publicó ofertas nuevas** - Normal en algunos días
3. **Problema de conexión** - Revisar errores en log

**Verificar última oferta:**
```bash
python -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute('SELECT MAX(scrapeado_en) FROM ofertas')
print(f'Última oferta: {cursor.fetchone()[0]}')
conn.close()
"
```

Si última oferta es de hoy = Todo normal, solo que no hay ofertas nuevas

---

### Problema: Dashboard muestra datos viejos

**Verificar auto-refresh:**
- Dashboard se actualiza automáticamente cada 5 minutos
- O refrescar manualmente (F5 en navegador)

**Verificar que haya datos nuevos en DB:**
```bash
python -c "
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM ofertas WHERE DATE(scrapeado_en) = DATE(\"now\")')
print(f'Ofertas scrapeadas HOY: {cursor.fetchone()[0]}')
conn.close()
"
```

Si devuelve 0 = No se scrapeó hoy todavía

---

### Problema: Error "PermissionError" o "database is locked"

**Causa:** Múltiples procesos accediendo a SQLite simultáneamente

**Solución:**
1. Cerrar dashboard
2. Esperar que termine scraping
3. Reiniciar dashboard

---

## MANTENIMIENTO RECOMENDADO

### Semanal

- [ ] Verificar que la tarea programada ejecutó correctamente
- [ ] Revisar logs por errores
- [ ] Verificar que dashboard muestra datos actualizados

### Mensual

- [ ] Revisar keywords sin resultados (considerar remover)
- [ ] Analizar alertas de calidad de datos
- [ ] Hacer backup de database/bumeran_scraping.db

### Trimestral

- [ ] Revisar y actualizar diccionario de keywords
- [ ] Analizar tendencias de demanda (keywords más buscados)
- [ ] Exportar datos históricos para análisis

---

## ARCHIVOS IMPORTANTES

### Scripts Principales

| Archivo | Función |
|---------|---------|
| `dashboard_scraping_v2.py` | Dashboard expandido (puerto 8051) |
| `run_scheduler.py` | Scheduler que ejecuta scraping automáticamente |
| `setup_task.ps1` | Script para configurar tarea de Windows |
| `scripts/analizar_datos_existentes.py` | Análisis de datos históricos |

### Datos

| Archivo/Carpeta | Contenido |
|-----------------|-----------|
| `database/bumeran_scraping.db` | Base de datos SQLite (13.83 MB) |
| `data/config/master_keywords.json` | Diccionario v3.2 (1,148 keywords) |
| `logs/` | Logs de ejecución |

### Documentación

| Archivo | Descripción |
|---------|-------------|
| `COMPARTIR_DASHBOARD_NGROK.md` | Guía de ngrok |
| `DASHBOARD_METRICAS_COMPLETADO.md` | Documentación de métricas |
| `GUIA_MONITOREO_SISTEMA.md` | Este archivo |

---

## CONTACTO Y SOPORTE

### ¿Dashboard no funciona?
1. Revisar esta guía (sección Troubleshooting)
2. Revisar logs en `D:\OEDE\Webscrapping\logs\`
3. Buscar error específico en logs

### ¿Queres agregar nuevos keywords?
- Editar: `data/config/master_keywords.json`
- Ubicación: Sección `ultra_exhaustiva_v3_2` → `keywords`

### ¿Queres cambiar horario de scraping?
- Editar: `database/config.py`
- Buscar: `SCHEDULER_CONFIG`
- Modificar `days_of_week` y `hour`

---

## RESUMEN DE LO QUE TENÉS AUTOMATIZADO

✅ **Scraping automático** - Lunes y Jueves 8 AM
✅ **Dashboard actualizado** - Refresh cada 5 min
✅ **Base de datos actualizada** - Automático después de cada scraping
✅ **Logs guardados** - Automático en cada ejecución
✅ **URL pública disponible** - Mientras ngrok esté activo
✅ **Descarga de datos** - Botones en dashboard
✅ **Análisis de calidad** - Automático para 38 variables
✅ **Keywords rankeados** - Automático de más a menos eficientes

**NO NECESITAS HACER NADA** - Solo monitorear ocasionalmente que funcione.

---

**Última actualización:** 2025-10-31
**Versión del sistema:** v2.0 Completamente Automatizado
**Estado:** ✅ Operativo
