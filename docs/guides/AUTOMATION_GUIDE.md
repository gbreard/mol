# GUIA DE AUTOMATIZACION - Sistema de Scraping
**Proyecto:** Monitor de Ofertas Laborales (MOL)
**Version:** 2.0
**Fecha:** 2025-10-31

---

## INTRODUCCION

Este documento describe todo lo necesario para configurar, monitorear y solucionar problemas del sistema de scraping automatizado.

**Objetivo:** Sistema completamente autonomo que ejecuta scraping de ofertas laborales sin intervencion manual.

---

## ARQUITECTURA DE AUTOMATIZACION

### Componentes

```
Windows Scheduled Task
    |
    v
run_scheduler.py (Orquestador)
    |
    +--> Verifica dia/hora
    +--> Ejecuta scraping
    +--> Guarda en SQLite
    +--> Registra metricas
    +--> Genera alertas
    +--> Escribe logs
```

### Flujo de Ejecucion

1. **Windows arranca** o **Usuario inicia sesion**
2. Task Scheduler activa tarea `BumeranScrapingAutomatico`
3. `pythonw.exe` ejecuta `run_scheduler.py` en background
4. Scheduler verifica:
   - Dia de la semana (Lunes=0, Jueves=3)
   - Hora actual (8:00 AM)
5. Si coincide:
   - Importa `BumeranMultiSearch`
   - Ejecuta scraping con `ultra_exhaustiva_v3_2`
   - Guarda ofertas en `database/bumeran_scraping.db`
   - Registra metricas en tabla `metricas_scraping`
   - Genera alertas si detecta problemas
6. Escribe log en `logs/scheduler_YYYYMMDD.log`
7. Proceso termina y espera proxima ejecucion

---

## CONFIGURACION INICIAL

### Pre-requisitos

**Software necesario:**
- Python 3.x
- Google Chrome (ultima version)
- ChromeDriver (compatible con Chrome)
- Windows 10/11

**Paquetes Python:**
```bash
pip install selenium beautifulsoup4 pandas schedule sqlite3
```

**Verificar instalacion:**
```bash
# Verificar Python
python --version

# Verificar Chrome
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version

# Verificar ChromeDriver
chromedriver --version

# Verificar paquetes
python -c "import selenium; import bs4; import pandas; import schedule; print('OK')"
```

### Configurar Windows Scheduled Task

**Metodo 1: Usando script automatico (RECOMENDADO)**

```powershell
# Ejecutar en PowerShell como Administrador
cd D:\OEDE\Webscrapping
.\setup_task.ps1
```

El script hace:
1. Detecta Python y pythonw.exe automaticamente
2. Crea tarea con nombre `BumeranScrapingAutomatico`
3. Configura triggers (logon + daily)
4. Asigna usuario actual
5. Inicia tarea inmediatamente
6. Muestra estado

**Metodo 2: Configuracion manual**

```powershell
# Crear accion
$action = New-ScheduledTaskAction `
    -Execute "C:\Path\To\pythonw.exe" `
    -Argument "D:\OEDE\Webscrapping\run_scheduler.py" `
    -WorkingDirectory "D:\OEDE\Webscrapping"

# Crear trigger - Al iniciar sesion
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn

# Crear trigger - Diario con repeticion
$triggerDaily = New-ScheduledTaskTrigger -Daily -At 7:00AM
$triggerDaily.Repetition = $(
    New-ScheduledTaskTrigger -Once -At 7:00AM `
        -RepetitionInterval (New-TimeSpan -Hours 1) `
        -RepetitionDuration (New-TimeSpan -Days 1)
).Repetition

# Configuracion
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

# Principal (usuario)
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# Registrar tarea
Register-ScheduledTask `
    -TaskName "BumeranScrapingAutomatico" `
    -Action $action `
    -Trigger $triggerLogon, $triggerDaily `
    -Settings $settings `
    -Principal $principal `
    -Description "Scraping automatizado de Bumeran - Lunes y Jueves 8AM" `
    -Force
```

### Verificar Configuracion

```powershell
# Ver estado de tarea
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico"

# Ver proxima ejecucion
Get-ScheduledTaskInfo -TaskName "BumeranScrapingAutomatico"

# Ver historial
Get-ScheduledTaskInfo -TaskName "BumeranScrapingAutomatico" | Select-Object *
```

---

## CONFIGURACION DE NGROK (Dashboard Publico)

Ngrok permite compartir el dashboard localmente corriendo con colegas externos.

### Instalar y Configurar Ngrok

**Metodo Automatico:**

```powershell
# Ejecutar en PowerShell como Administrador
cd D:\OEDE\Webscrapping
.\setup_ngrok_task.ps1
```

Esto:
1. Detecta ngrok instalado
2. Crea tarea `NgrokDashboardAutomatico`
3. Configura para iniciar ngrok en puerto 8051
4. Inicia ngrok automaticamente
5. Muestra URL publica

**Metodo Manual:**

1. Descargar ngrok: https://ngrok.com/download
2. Descomprimir en `C:\Users\[Usuario]\ngrok\`
3. Ejecutar:
```bash
ngrok http 8051
```

### Obtener URL Publica Actual

```powershell
# Ejecutar script helper
.\obtener_url_ngrok.ps1

# O manualmente
curl http://localhost:4040/api/tunnels
```

La URL cambia cada vez que reinicias ngrok (version gratuita).

### Hacer Ngrok Persistente

La tarea programada `NgrokDashboardAutomatico` inicia ngrok automaticamente al arrancar Windows.

**Verificar estado:**
```powershell
Get-ScheduledTask -TaskName "NgrokDashboardAutomatico"
```

**Reiniciar manualmente:**
```powershell
Restart-ScheduledTask -TaskName "NgrokDashboardAutomatico"
```

---

## MONITOREO DEL SISTEMA

### Comandos Esenciales

**1. Verificar si scraping esta corriendo:**

```powershell
Get-Process python* | Where-Object {$_.Path -like "*run_scheduler*"}
```

**2. Ver ultimos logs:**

```powershell
Get-Content D:\OEDE\Webscrapping\logs\scheduler_*.log -Tail 50
```

**3. Ver proxima ejecucion programada:**

```powershell
$task = Get-ScheduledTask -TaskName "BumeranScrapingAutomatico"
$info = Get-ScheduledTaskInfo -TaskName "BumeranScrapingAutomatico"

Write-Host "Estado: $($task.State)"
Write-Host "Ultima ejecucion: $($info.LastRunTime)"
Write-Host "Proxima ejecucion: $($info.NextRunTime)"
Write-Host "Ultimo resultado: $($info.LastTaskResult)"
```

**4. Contar ofertas en base de datos:**

```python
import sqlite3
conn = sqlite3.connect('D:/OEDE/Webscrapping/database/bumeran_scraping.db')
cursor = conn.cursor()

# Total ofertas
cursor.execute("SELECT COUNT(*) FROM ofertas")
print(f"Total ofertas: {cursor.fetchone()[0]:,}")

# Ofertas ultimos 7 dias
cursor.execute("""
    SELECT COUNT(*)
    FROM ofertas
    WHERE fecha_publicacion_iso >= date('now', '-7 days')
""")
print(f"Ultimos 7 dias: {cursor.fetchone()[0]:,}")

conn.close()
```

**5. Ver keywords mas productivos:**

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('D:/OEDE/Webscrapping/database/bumeran_scraping.db')

df = pd.read_sql_query("""
    SELECT keyword, ofertas_encontradas, ofertas_nuevas, veces_ejecutado
    FROM keywords_performance
    WHERE ofertas_encontradas > 0
    ORDER BY ofertas_encontradas DESC
    LIMIT 20
""", conn)

print(df.to_string())
conn.close()
```

### Dashboard de Monitoreo

**Iniciar dashboard:**
```bash
cd D:\OEDE\Webscrapping
python dashboard_scraping_v2.py
```

**Acceder:**
- Local: http://localhost:8051
- Publico: [URL ngrok actual]

**Tabs disponibles:**
- **Overview:** Metricas generales
- **Keywords:** Performance de keywords
- **Calidad:** Completitud de datos
- **Alertas:** Problemas detectados
- **Datos:** Tablas completas y descargas

---

## SOLUC ION DE PROBLEMAS

### Problema 1: Tarea no se ejecuta

**Sintoma:** Logs no se actualizan, DB no crece

**Diagnostico:**
```powershell
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico" | Select-Object State, LastRunTime
```

**Posibles causas y soluciones:**

**Causa: Tarea deshabilitada**
```powershell
Enable-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

**Causa: Ruta de Python incorrecta**
```powershell
# Verificar ruta
(Get-ScheduledTask -TaskName "BumeranScrapingAutomatico").Actions[0].Execute

# Debe apuntar a pythonw.exe valido
# Si no, reconfigurar con setup_task.ps1
```

**Causa: Falta conexion de red**
```powershell
# La tarea requiere red
# Verificar:
(Get-ScheduledTask -TaskName "BumeranScrapingAutomatico").Settings.RunOnlyIfNetworkAvailable
# Debe ser True
```

**Causa: Usuario sin permisos**
```powershell
# Ejecutar PowerShell como Administrador y reconfigurar
.\setup_task.ps1
```

### Problema 2: Scraping falla con errores

**Sintoma:** Logs muestran excepciones, ofertas = 0

**Diagnostico:**
```powershell
Select-String -Path D:\OEDE\Webscrapping\logs\*.log -Pattern "ERROR|Exception"
```

**Posibles causas:**

**Causa: ChromeDriver desactualizado**
```bash
# Descargar ultima version compatible con Chrome
# https://chromedriver.chromium.org/downloads

# Reemplazar en ruta del sistema
# Verificar version
chromedriver --version
chrome --version
# Deben ser compatibles
```

**Causa: Selenium no encuentra Chrome**
```python
# En scrapear_con_diccionario.py
# Verificar ruta de Chrome en options.binary_location
```

**Causa: Portal cambio estructura HTML**
```bash
# Revisar selectores CSS/XPath
# Actualizar scrapers afectados
# Ver SCRAPING_PHASE_SUMMARY.md para detalles
```

**Causa: Bloqueo por anti-scraping**
```python
# Aumentar delays en scrapear_con_diccionario.py:
delay_between_requests=2.5  # Antes: 1.5
delay_between_keywords=3.0  # Antes: 2.0
```

### Problema 3: Base de datos bloqueada

**Sintoma:** `database is locked` en logs

**Causa:** Dashboard y scraper accediendo simultaneamente

**Solucion:**
```bash
# Detener dashboard antes de scraping manual
# O agregar timeout en SQLite:
conn = sqlite3.connect('database/bumeran_scraping.db', timeout=30)
```

### Problema 4: Logs muy grandes

**Sintoma:** Carpeta `logs/` > 500 MB

**Solucion:**
```powershell
# Eliminar logs mayores a 30 dias
Get-ChildItem D:\OEDE\Webscrapping\logs\*.log |
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} |
    Remove-Item
```

### Problema 5: Ngrok no inicia

**Sintoma:** `obtener_url_ngrok.ps1` muestra error

**Diagnostico:**
```powershell
Get-Process ngrok -ErrorAction SilentlyContinue
```

**Solucion si no esta corriendo:**
```powershell
Start-ScheduledTask -TaskName "NgrokDashboardAutomatico"

# Esperar 5 segundos
Start-Sleep -Seconds 5

# Obtener URL
.\obtener_url_ngrok.ps1
```

**Solucion si falla autenticacion:**
```bash
# Registrarse en ngrok.com
# Obtener authtoken
# Configurar:
ngrok authtoken TU_AUTH_TOKEN
```

---

## MANTENIMIENTO RUTINARIO

### Semanal

- [ ] Verificar que tarea programada esta activa
```powershell
Get-ScheduledTask -TaskName "BumeranScrapingAutomatico" | Select-Object State
```

- [ ] Revisar logs por errores
```powershell
Select-String -Path D:\OEDE\Webscrapping\logs\scheduler_*.log -Pattern "ERROR" | Select-Object -Last 10
```

- [ ] Verificar crecimiento de DB
```python
import sqlite3
conn = sqlite3.connect('database/bumeran_scraping.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM ofertas WHERE scrapeado_en >= datetime('now', '-7 days')")
print(f"Ofertas ultimos 7 dias: {cursor.fetchone()[0]}")
conn.close()
```

### Mensual

- [ ] Revisar keywords sin resultados
```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('database/bumeran_scraping.db')
df = pd.read_sql_query("""
    SELECT keyword, veces_ejecutado
    FROM keywords_performance
    WHERE ofertas_encontradas = 0 AND veces_ejecutado >= 4
""", conn)
print(f"Keywords improductivos: {len(df)}")
print(df)
conn.close()
```

- [ ] Limpiar logs antiguos (>30 dias)
- [ ] Verificar espacio en disco
- [ ] Actualizar ChromeDriver si hay nueva version de Chrome

### Trimestral

- [ ] Revisar completitud de datos
- [ ] Analizar nuevas fuentes a agregar
- [ ] Actualizar diccionario de keywords
- [ ] Backup completo de base de datos

---

## BACKUPS

### Backup Manual

**Base de datos:**
```powershell
$fecha = Get-Date -Format "yyyyMMdd"
Copy-Item "D:\OEDE\Webscrapping\database\bumeran_scraping.db" `
          "D:\OEDE\backups\bumeran_scraping_$fecha.db"
```

**Proyecto completo:**
```bash
cd D:\OEDE
tar -czf Webscrapping_backup_$(Get-Date -Format "yyyyMMdd").tar.gz Webscrapping
```

### Backup Automatico (Opcional)

Crear tarea programada para backup semanal:

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-File D:\OEDE\Webscrapping\backup_semanal.ps1"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3:00AM

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "BackupWebscra pping" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings
```

---

## MODIFICAR FRECUENCIA DE SCRAPING

### Cambiar dias de ejecucion

**Actual:** Lunes y Jueves

**Editar:** `run_scheduler.py` lineas 20-25

```python
# Configuracion actual
SCRAPING_DAYS = [0, 3]  # 0=Lunes, 3=Jueves
SCRAPING_HOUR = 8
SCRAPING_MINUTE = 0

# Ejemplo: Todos los dias laborales
SCRAPING_DAYS = [0, 1, 2, 3, 4]  # Lunes a Viernes

# Ejemplo: Solo los lunes
SCRAPING_DAYS = [0]
```

### Cambiar hora de ejecucion

```python
SCRAPING_HOUR = 10  # Cambiar a 10:00 AM
SCRAPING_MINUTE = 30  # 10:30 AM
```

**Reiniciar tarea** para que tome los cambios:

```powershell
Restart-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

---

## AGREGAR NUEVAS FUENTES

### Pasos para agregar nuevo portal

1. **Crear estructura:**
```bash
mkdir 01_sources/nuevo_portal
mkdir 01_sources/nuevo_portal/scrapers
mkdir 01_sources/nuevo_portal/data
```

2. **Crear scraper:**
```python
# 01_sources/nuevo_portal/scrapers/scraper_nuevo.py
class NuevoPortalScraper:
    def scrape(self):
        # Implementar logica
        pass
```

3. **Agregar a scheduler:**

Editar `run_scheduler.py`:

```python
from 01_sources.nuevo_portal.scrapers.scraper_nuevo import NuevoPortalScraper

# En funcion ejecutar_scraping():
scraper_nuevo = NuevoPortalScraper()
ofertas_nuevo = scraper_nuevo.scrape()
# Guardar en DB
```

4. **Actualizar consolidacion:**

Editar `02_consolidation/consolidar_fuentes.py` para incluir nuevo portal.

---

## DESACTIVAR AUTOMATIZACION

### Desactivar temporalmente

```powershell
Disable-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

### Reactivar

```powershell
Enable-ScheduledTask -TaskName "BumeranScrapingAutomatico"
```

### Eliminar tarea completamente

```powershell
Unregister-ScheduledTask -TaskName "BumeranScrapingAutomatico" -Confirm:$false
```

---

## CONTACTO Y SOPORTE

**Documentacion relacionada:**
- `SCRAPING_PHASE_SUMMARY.md` - Detalles tecnicos de scraping
- `GUIA_MONITOREO_SISTEMA.md` - Comandos de monitoreo
- `COMPARTIR_DASHBOARD_NGROK.md` - Configuracion ngrok
- `RESUMEN_MEJORAS_IMPLEMENTADAS.md` - Historial de cambios

**Logs:**
- `D:\OEDE\Webscrapping\logs\scheduler_*.log`

**Base de datos:**
- `D:\OEDE\Webscrapping\database\bumeran_scraping.db`

---

**Documento actualizado:** 2025-10-31
**Version:** 2.0
**Estado:** Sistema completamente automatizado y operativo
