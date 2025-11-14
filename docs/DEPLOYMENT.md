# 🚀 DEPLOYMENT - Sistema de Scraping Bumeran en Producción

**Versión:** 4.0 - Sistema Completo con Automatización
**Fecha:** 30 Octubre 2025
**Estado:** ✅ Listo para Producción

---

## 📋 Tabla de Contenidos

1. [Resumen del Sistema](#resumen-del-sistema)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación Inicial](#instalación-inicial)
4. [Configuración de PostgreSQL](#configuración-de-postgresql)
5. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
6. [Ejecución Manual (Testing)](#ejecución-manual-testing)
7. [Automatización Semanal](#automatización-semanal)
8. [Dashboard de Métricas](#dashboard-de-métricas)
9. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Resumen del Sistema

### Componentes Implementados

**Fase 1-3: Scraper Robusto** ✅
- ✅ Tracking incremental seguro (operaciones atómicas)
- ✅ Retry automático con exponential backoff (tenacity)
- ✅ Validación de schemas (Pydantic)
- ✅ Fechas ISO 8601 con timezone Argentina
- ✅ Limpieza de HTML entities
- ✅ Sistema de métricas de performance
- ✅ Rate limiting adaptativo (0.5s-10s)
- ✅ Circuit breaker (fail-fast tras 5 fallos)
- ✅ Sistema de alertas automáticas

**Fase 4: Infraestructura de Producción** ✅
- ✅ Base de datos PostgreSQL (5 tablas, 3 vistas)
- ✅ DatabaseManager (db_manager.py)
- ✅ Scheduler automatizado (lunes y jueves 8:00 AM)
- ✅ Scripts de deployment (batch files)
- ⏳ Dashboard Plotly Dash (pendiente)

### Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE SCRAPING                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌───────────────┐    ┌─────────────┐│
│  │   Bumeran    │──────│    Scraper    │────│  PostgreSQL ││
│  │     API      │      │   (Fases 1-3) │    │             ││
│  └──────────────┘      └───────────────┘    └─────────────┘│
│                               │                      │       │
│                               │                      │       │
│                      ┌────────▼──────────┐           │       │
│                      │   Optimizaciones  │           │       │
│                      ├───────────────────┤           │       │
│                      │ • Rate Limiter    │           │       │
│                      │ • Circuit Breaker │           │       │
│                      │ • Alertas         │           │       │
│                      └───────────────────┘           │       │
│                               │                      │       │
│                      ┌────────▼──────────┐           │       │
│                      │   CSV + Tracking  │           │       │
│                      └───────────────────┘           │       │
│                                                       │       │
│  ┌──────────────────────────────────────────────────▼──────┐│
│  │              Scheduler (Lunes y Jueves 8:00 AM)         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │         Dashboard Plotly Dash (localhost:8050)          ││
│  │  • Métricas históricas  • Circuit breaker stats         ││
│  │  • Rate limiter         • Alertas                       ││
│  └─────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
```

---

## 💻 Requisitos del Sistema

### Software Necesario

1. **Python 3.9+**
   - Descargar: https://www.python.org/downloads/
   - Asegurarse de agregar Python a PATH durante instalación

2. **PostgreSQL 14+**
   - Descargar: https://www.postgresql.org/download/
   - Durante instalación, recordar password de usuario `postgres`

3. **Git** (opcional, para control de versiones)
   - Descargar: https://git-scm.com/downloads

### Hardware Recomendado

- **CPU:** 2+ cores
- **RAM:** 4+ GB
- **Disco:** 10+ GB libres
- **Internet:** Conexión estable

---

## 🔧 Instalación Inicial

### Paso 1: Clonar/Descargar Proyecto

```bash
cd D:\OEDE\Webscrapping
```

### Paso 2: Instalar Dependencias de Python

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r config\requirements.txt
```

**Dependencias incluidas:**
- `requests` - HTTP requests
- `pandas` - Procesamiento de datos
- `tenacity` - Retry logic
- `pydantic` - Validación de schemas
- `psycopg2-binary` - PostgreSQL driver
- `schedule` - Scheduler
- `plotly`, `dash` - Dashboard (pendiente)

### Paso 3: Verificar Instalación

```bash
python --version  # Debe mostrar Python 3.9+
pip list | findstr postgres  # Debe mostrar psycopg2
pip list | findstr schedule  # Debe mostrar schedule
```

---

## 🗄️ Configuración de PostgreSQL

### Paso 1: Iniciar PostgreSQL

**Windows:**
- Buscar "pgAdmin 4" en el menú inicio
- O verificar que el servicio `postgresql-x64-14` esté corriendo en Services

**Verificar conexión:**
```bash
psql -U postgres -c "SELECT version();"
```

### Paso 2: Crear Base de Datos

**Opción A: Usando pgAdmin (GUI)**
1. Abrir pgAdmin 4
2. Conectar a servidor local (usuario: postgres, password: tu_password)
3. Click derecho en "Databases" → Create → Database
4. Nombre: `bumeran_scraping`
5. Encoding: UTF8
6. OK

**Opción B: Usando psql (Command Line)**
```bash
cd D:\OEDE\Webscrapping\database

# Ejecutar script de creación
psql -U postgres -f create_database.sql

# Debería mostrar:
# ✅ Base de datos creada exitosamente!
```

### Paso 3: Verificar Tablas Creadas

```sql
-- Conectar a la base de datos
psql -U postgres -d bumeran_scraping

-- Listar tablas
\dt

-- Debería mostrar:
-- ofertas
-- metricas_scraping
-- alertas
-- circuit_breaker_stats
-- rate_limiter_stats
```

---

## 🔐 Configuración de Variables de Entorno

### Paso 1: Crear archivo .env

```bash
cd D:\OEDE\Webscrapping

# Copiar plantilla
copy .env.example .env

# Editar con tu editor favorito
notepad .env
```

### Paso 2: Configurar Credenciales

Editar `.env` con tus valores:

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bumeran_scraping
DB_USER=postgres
DB_PASSWORD=TU_PASSWORD_AQUI  # ← CAMBIAR!

# Alertas (Opcional - Futuro)
ALERT_EMAIL=tu_email@example.com
```

### Paso 3: Verificar Configuración

```bash
cd D:\OEDE\Webscrapping

python database\config.py
```

Debería mostrar:
```
======================================================================
CONFIGURACIÓN ACTUAL
======================================================================

BASE DE DATOS:
  Host:     localhost
  Port:     5432
  Database: bumeran_scraping
  User:     postgres
  Password: ******* (configurado)

SCHEDULER:
  Días:     Lun, Jue
  Hora:     08:00
  Timezone: America/Argentina/Buenos_Aires

✓ Configuración válida
```

---

## 🧪 Ejecución Manual (Testing)

### Test 1: Scraping Pequeño (Recomendado Primero)

```bash
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers

# Test de Fase 1 (tracking, retry, validación)
python test_fase1_mejoras.py

# Test de Fase 2 (fechas ISO, HTML, métricas)
python test_fase2_mejoras.py

# Test de Fase 3 (rate limiter, circuit breaker, alertas)
python test_fase3_mejoras.py
```

**Resultado esperado:** `[PASS] TEST X COMPLETADO` para cada test

### Test 2: Scraping Completo (12k ofertas)

```bash
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers

python run_scraping_completo.py
```

**Duración estimada:** 15-25 minutos (dependiendo de rate limiter adaptativo)

**Resultado esperado:**
```
======================================================================
SCRAPING COMPLETADO EXITOSAMENTE - 12,142 OFERTAS
======================================================================

Archivos generados:
  CSV     : D:\OEDE\Webscrapping\01_sources\bumeran\data\raw\bumeran_completo_20251030_123456.csv
  JSON    : D:\OEDE\Webscrapping\01_sources\bumeran\data\raw\bumeran_completo_20251030_123456.json
  EXCEL   : D:\OEDE\Webscrapping\01_sources\bumeran\data\raw\bumeran_completo_20251030_123456.xlsx
```

### Test 3: Integración con PostgreSQL

```bash
cd D:\OEDE\Webscrapping

# Test de scheduler (ejecuta scraping inmediatamente)
python run_scheduler.py --test
```

**Resultado esperado:**
```
TEST MODE - Ejecutando scraping inmediatamente
======================================================================
INICIANDO SCRAPING PROGRAMADO
======================================================================
...
Insertando 12,142 ofertas...
✓ 12,142 ofertas insertadas/actualizadas
Métricas guardadas con ID: 1
Total ofertas en DB: 12,142
======================================================================
SCRAPING COMPLETADO EXITOSAMENTE - 15.35 minutos
======================================================================
```

---

## ⏰ Automatización Semanal

### Opción A: Scheduler Python (Recomendado)

**Ventaja:** Simple, portable, logs detallados

#### Paso 1: Iniciar Scheduler

**Modo Visible (para testing):**
```bash
cd D:\OEDE\Webscrapping
start_scheduler.bat
```

**Modo Oculto (producción):**
```bash
cd D:\OEDE\Webscrapping
start_scheduler.bat --hidden
```

#### Paso 2: Verificar Scheduler Está Corriendo

**Task Manager:**
- Presionar `Ctrl + Shift + Esc`
- Buscar proceso `python.exe` o `pythonw.exe`
- Debería estar corriendo `run_scheduler.py`

**Logs:**
```bash
# Ver logs en tiempo real
cd D:\OEDE\Webscrapping\logs
type scheduler_202510.log
```

#### Paso 3: Detener Scheduler

**Si modo visible:** Presionar `Ctrl + C` en la consola

**Si modo oculto:**
- Task Manager → buscar `pythonw.exe` → End Task

---

### Opción B: Windows Task Scheduler (Más Robusto)

**Ventaja:** Sobrevive a reinicios, ejecución garantizada

#### Paso 1: Abrir Task Scheduler

1. Presionar `Win + R`
2. Escribir `taskschd.msc`
3. Enter

#### Paso 2: Crear Nueva Tarea

1. Click derecho en "Task Scheduler Library" → Create Task...
2. **General Tab:**
   - Name: `Bumeran Scraping - Lunes`
   - Description: `Scraping automatizado de Bumeran (Lunes 8:00 AM)`
   - Run whether user is logged on or not: ✓
   - Run with highest privileges: ✓

3. **Triggers Tab:**
   - New...
   - Begin the task: `On a schedule`
   - Weekly
   - Start: `08:00:00`
   - Recur every: `1 weeks on`
   - Monday: ✓
   - OK

4. **Actions Tab:**
   - New...
   - Action: `Start a program`
   - Program/script: `C:\Path\To\Python\python.exe`
     (Encontrar con: `where python`)
   - Add arguments: `D:\OEDE\Webscrapping\run_scheduler.py --test`
   - Start in: `D:\OEDE\Webscrapping`
   - OK

5. **Conditions Tab:**
   - Uncheck: `Start the task only if the computer is on AC power`

6. **Settings Tab:**
   - Allow task to be run on demand: ✓
   - Run task as soon as possible after a scheduled start is missed: ✓

#### Paso 3: Repetir para Jueves

Crear otra tarea idéntica pero con trigger en **Thursday**

#### Paso 4: Probar Tarea

Click derecho en tarea → Run

Verificar logs en `D:\OEDE\Webscrapping\logs\`

---

## 📊 Dashboard de Métricas

**Estado:** ⏳ Pendiente de implementación

**Próximos pasos:**
1. Crear `dashboard_app.py` con Plotly Dash
2. Gráficos:
   - Evolución delay adaptativo
   - Circuit breaker opens timeline
   - Tasas de validación
   - Ofertas scrapeadas por ejecución
3. Ejecución: `python dashboard_app.py`
4. Acceso: http://localhost:8050

---

## 🔍 Monitoreo y Mantenimiento

### Logs

**Ubicación:** `D:\OEDE\Webscrapping\logs\`

**Archivos:**
- `scheduler_YYYYMM.log` - Log del scheduler (rotación mensual)
- `scraping_YYYYMMDD_HHMMSS.log` - Log de cada ejecución manual

**Ver logs recientes:**
```bash
cd D:\OEDE\Webscrapping\logs

# Últimas 50 líneas
powershell Get-Content scheduler_202510.log -Tail 50

# En tiempo real
powershell Get-Content scheduler_202510.log -Wait
```

### Verificar Métricas en PostgreSQL

```sql
-- Conectar
psql -U postgres -d bumeran_scraping

-- Últimas 10 ejecuciones
SELECT * FROM v_ultimas_ejecuciones;

-- Alertas críticas recientes
SELECT * FROM v_alertas_criticas LIMIT 10;

-- Total ofertas
SELECT COUNT(*) FROM ofertas;
```

### Backups

**Base de Datos (Semanal Recomendado):**
```bash
cd D:\OEDE\Webscrapping\backups

# Crear backup
pg_dump -U postgres -d bumeran_scraping -F c -f bumeran_scraping_20251030.backup

# Restaurar (si es necesario)
pg_restore -U postgres -d bumeran_scraping -c bumeran_scraping_20251030.backup
```

**CSV (Automático):**
Los archivos CSV se guardan automáticamente en:
`D:\OEDE\Webscrapping\01_sources\bumeran\data\raw\`

### Limpieza de Logs Antiguos

```bash
# Eliminar logs >3 meses
cd D:\OEDE\Webscrapping\logs
del /Q scheduler_202407.log
del /Q scheduler_202408.log
```

---

## 🐛 Troubleshooting

### Error: "No module named 'psycopg2'"

**Causa:** PostgreSQL driver no instalado

**Solución:**
```bash
pip install psycopg2-binary
```

### Error: "password authentication failed for user postgres"

**Causa:** Password incorrecta en `.env`

**Solución:**
1. Verificar password en pgAdmin
2. Actualizar `DB_PASSWORD` en `.env`
3. Reintentar

### Error: "CRITICAL: >50% de ofertas inválidas. ¿Cambió el schema de la API?"

**Causa:** Bumeran cambió el formato de su API

**Solución:**
1. Verificar respuesta de API manualmente:
   ```bash
   curl -X POST https://www.bumeran.com.ar/api/avisos/searchV2 \
     -H "x-site-id: BMAR" -H "Content-Type: application/json" \
     -d '{"page": 0, "pageSize": 1}'
   ```
2. Actualizar `bumeran_schemas.py` con nuevo formato
3. Reintentar

### Scraping Muy Lento

**Causa:** Rate limiter demasiado conservador

**Solución:**
Editar `database/config.py`:
```python
'rate_limiter': {
    'min_delay': 0.3,  # Reducir de 0.5s
    'max_delay': 10.0,
    'success_threshold': 3,  # Reducir de 5
}
```

### Circuit Breaker Se Abre Frecuentemente

**Causa:** API inestable o max_failures muy bajo

**Solución:**
Editar `database/config.py`:
```python
'circuit_breaker': {
    'max_failures': 10,  # Aumentar de 5
    'timeout': 60,  # Aumentar de 30s
}
```

### Scheduler No Ejecuta a Horario Programado

**Causa:** Múltiples posibles

**Solución:**
1. Verificar zona horaria:
   ```python
   from datetime import datetime
   import pytz

   tz = pytz.timezone('America/Argentina/Buenos_Aires')
   print(datetime.now(tz))
   ```
2. Verificar scheduler está corriendo:
   ```bash
   tasklist | findstr python
   ```
3. Revisar logs para errores

---

## 📞 Soporte

**Documentación Adicional:**
- `MEJORAS_FASE1_COMPLETADAS.md` - Tracking + Retry + Validación
- `MEJORAS_FASE2_COMPLETADAS.md` - Fechas + HTML + Métricas
- `MEJORAS_FASE3_COMPLETADAS.md` - Rate Limiter + Circuit Breaker + Alertas

**Archivos de Configuración:**
- `database/config.py` - Configuración centralizada
- `.env` - Variables de entorno (NO subir a Git)

**Scripts Útiles:**
- `run_scraping_completo.py` - Scraping manual completo
- `run_scheduler.py` - Scheduler automatizado
- `start_scheduler.bat` - Inicio rápido del scheduler
- `database/db_manager.py` - Gestor de base de datos

---

## ✅ Checklist de Deployment

Antes de poner en producción, verificar:

- [ ] PostgreSQL instalado y corriendo
- [ ] Base de datos `bumeran_scraping` creada
- [ ] Tablas creadas (5 tablas, 3 vistas)
- [ ] Python 3.9+ instalado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` configurado con password correcto
- [ ] Tests de Fase 1+2+3 pasando
- [ ] Test de scraping completo exitoso
- [ ] Test de integración PostgreSQL exitoso
- [ ] Scheduler funcionando (al menos 1 ejecución exitosa)
- [ ] Logs configurados y monitoreados
- [ ] Backups de base de datos configurados
- [ ] Documentación leída y comprendida

---

**FIN DOCUMENTO - SISTEMA LISTO PARA PRODUCCIÓN** ✅

**Próximos Pasos Recomendados:**
1. Ejecutar scraping completo de validación
2. Configurar scheduler semanal (lunes y jueves)
3. Monitorear primeras 2-3 ejecuciones automáticas
4. Implementar dashboard de métricas (opcional)
5. Proceder con parseo ESCO y vinculación semántica
