# Guía de Validación de Calidad de Datos

**Sistema:** Monitor de Ofertas Laborales (MOL)
**Versión:** 1.0
**Fecha:** 2025-11-07

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema de Validación](#arquitectura-del-sistema-de-validación)
3. [Uso del Validador](#uso-del-validador)
4. [Niveles de Validación](#niveles-de-validación)
5. [Interpretación de Resultados](#interpretación-de-resultados)
6. [Acciones Recomendadas](#acciones-recomendadas)
7. [Integración en Workflow](#integración-en-workflow)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Introducción

### ¿Por Qué Validar Datos?

El dashboard Shiny depende de datos de alta calidad para funcionar correctamente. Datos incompletos o mal formateados pueden causar:

- ❌ Secciones del dashboard vacías
- ❌ Gráficos que no se renderizan
- ❌ Métricas incorrectas o engañosas
- ❌ Errores en tiempo de ejecución

El sistema de validación detecta estos problemas **ANTES** de generar el CSV, permitiendo:

- ✅ Identificación temprana de problemas
- ✅ Reportes detallados con porcentajes de completitud
- ✅ Sugerencias de remediación automáticas
- ✅ Prevención de dashboards rotos

### Componentes del Sistema

```
┌────────────────────────────────────────────────────┐
│  SISTEMA DE VALIDACIÓN DE DATOS                   │
├────────────────────────────────────────────────────┤
│                                                    │
│  1. validate_shiny_data_quality.py                 │
│     └─ Validador core (3 niveles)                 │
│                                                    │
│  2. generar_csv_shiny_validado.py                  │
│     └─ Wrapper de generación segura               │
│                                                    │
│  3. validate_csv_before_load.R (opcional)          │
│     └─ Validación R-side antes de cargar          │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Arquitectura del Sistema de Validación

### Flujo de Validación

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE VALIDACIÓN                       │
└─────────────────────────────────────────────────────────────┘

Acción del Usuario:
  "Necesito actualizar el dashboard"
           │
           ▼
  ┌─────────────────────────┐
  │ generar_csv_shiny_      │
  │ validado.py             │
  └─────────────────────────┘
           │
           │ (Paso 1) Ejecuta validación
           ▼
  ┌─────────────────────────┐
  │ validate_shiny_data_    │
  │ quality.py              │
  └─────────────────────────┘
           │
           │ Conecta a DB
           ▼
  ┌─────────────────────────┐
  │ bumeran_scraping.db     │
  │ - ofertas               │
  │ - ofertas_nlp_history   │
  │ - ofertas_esco_matching │
  └─────────────────────────┘
           │
           │ Ejecuta queries de validación
           ▼
  ┌─────────────────────────┐
  │ Análisis de Completitud │
  │ - Crítico (≥95%)        │
  │ - Importante (≥50%)     │
  │ - Advertencia (≥40%)    │
  └─────────────────────────┘
           │
           ├─────── Exit Code 0 (OK) ──────────────────┐
           ├─────── Exit Code 1 (Warnings) ────────┐   │
           ├─────── Exit Code 2 (Critical) ────┐   │   │
           └─────── Exit Code 3 (Exception) ┐  │   │   │
                                            │  │   │   │
           ┌────────────────────────────────┘  │   │   │
           │ (Paso 2) Evaluar si continuar     │   │   │
           ▼                                    │   │   │
  ┌─────────────────────────┐                  │   │   │
  │ ABORTAR generación      │                  │   │   │
  │ (o --force para omitir) │                  │   │   │
  └─────────────────────────┘                  │   │   │
                                               │   │   │
           ┌───────────────────────────────────┴───┴───┘
           │ (Paso 3) Generar CSV
           ▼
  ┌─────────────────────────┐
  │ generar_csv_shiny_      │
  │ desde_db.py             │
  └─────────────────────────┘
           │
           ▼
  ┌─────────────────────────┐
  │ Visual--/               │
  │ ofertas_esco_shiny.csv  │
  └─────────────────────────┘
           │
           ▼
  ┌─────────────────────────┐
  │ Shiny Dashboard         │
  │ (reiniciar para cargar) │
  └─────────────────────────┘
```

---

## Uso del Validador

### Modo Standalone (Solo Validación)

#### Validación Completa (Todos los Niveles)

```bash
cd D:\OEDE\Webscrapping\database
python validate_shiny_data_quality.py
```

**Output Esperado:**

```
======================================================================
VALIDACIÓN DE CALIDAD DE DATOS PARA DASHBOARD SHINY
======================================================================

Conectando a base de datos...
Base de datos: D:\OEDE\Webscrapping\database\bumeran_scraping.db

Ejecutando validaciones...

📊 VALIDACIONES CRÍTICAS
====================================================

✅ PASS: ESCO Occupation Match
   Umbral requerido: 95.00%
   Completitud actual: 95.20%
   Filas completas: 5,607 / 5,890

✅ PASS: ISCO Nivel 1
   Umbral requerido: 95.00%
   Completitud actual: 95.20%
   Filas completas: 5,607 / 5,890

✅ PASS: Título de Oferta
   Umbral requerido: 100.00%
   Completitud actual: 100.00%
   Filas completas: 5,890 / 5,890

✅ PASS: Fecha de Publicación
   Umbral requerido: 100.00%
   Completitud actual: 100.00%
   Filas completas: 5,890 / 5,890

📊 VALIDACIONES IMPORTANTES
====================================================

❌ FALLO: ESCO Skills Esenciales (JSON)
   Umbral requerido: 50.00%
   Completitud actual: 0.00%
   Filas completas: 0 / 5,890

   💡 REMEDIACIÓN:
   Las skills ESCO no están siendo populadas.
   • Ejecutar populate_esco_skills_in_db.py (cuando esté disponible)
   • O verificar que match_ofertas_to_esco.py incluya skills

❌ FALLO: ESCO Skills Opcionales (JSON)
   Umbral requerido: 50.00%
   Completitud actual: 0.00%
   Filas completas: 0 / 5,890

   💡 REMEDIACIÓN: (igual que arriba)

✅ PASS: Soft Skills (NLP)
   Umbral requerido: 80.00%
   Completitud actual: 85.20%
   Filas completas: 5,018 / 5,890

✅ PASS: Skills Técnicas (NLP)
   Umbral requerido: 60.00%
   Completitud actual: 72.30%
   Filas completas: 4,258 / 5,890

⚠️ VALIDACIONES DE ADVERTENCIA
====================================================

✅ PASS: Empresa
   Umbral requerido: 90.00%
   Completitud actual: 92.10%
   Filas completas: 5,424 / 5,890

✅ PASS: Localización
   Umbral requerido: 80.00%
   Completitud actual: 85.40%
   Filas completas: 5,030 / 5,890

✅ PASS: Nivel Educativo (NLP)
   Umbral requerido: 40.00%
   Completitud actual: 40.20%
   Filas completas: 2,368 / 5,890

======================================================================
RESULTADO FINAL
======================================================================

🔴 VALIDACIÓN FALLIDA

Resumen:
  • Validaciones Críticas: 4 passed, 0 failed
  • Validaciones Importantes: 2 passed, 2 failed
  • Validaciones de Advertencia: 3 passed, 0 failed

Exit code: 1 (ADVERTENCIAS - no crítico)

📌 RECOMENDACIÓN:
El CSV puede generarse pero algunas secciones del dashboard estarán vacías.
Específicamente: la pestaña "Análisis de Skills ESCO" no tendrá datos.
```

#### Validación Por Nivel

**Solo Crítico:**

```bash
python validate_shiny_data_quality.py --nivel critico
```

Valida únicamente checks que bloquearían la generación del CSV.

**Solo Importante:**

```bash
python validate_shiny_data_quality.py --nivel importante
```

Valida checks que afectan funcionalidad del dashboard pero no bloquean.

**Solo Advertencia:**

```bash
python validate_shiny_data_quality.py --nivel advertencia
```

Valida checks de monitoreo (calidad no esencial).

#### Salida en JSON

```bash
python validate_shiny_data_quality.py --json
```

Output en formato JSON para integración con otros sistemas:

```json
{
  "timestamp": "2025-11-07 14:32:15",
  "total_ofertas": 5890,
  "validations": {
    "critico": [
      {
        "check": "ESCO Occupation Match",
        "passed": true,
        "threshold": 95.0,
        "actual": 95.2,
        "count": 5607,
        "total": 5890
      },
      ...
    ],
    "importante": [
      {
        "check": "ESCO Skills Esenciales",
        "passed": false,
        "threshold": 50.0,
        "actual": 0.0,
        "count": 0,
        "total": 5890,
        "remediation": "Ejecutar populate_esco_skills_in_db.py"
      },
      ...
    ],
    "advertencia": [...]
  },
  "summary": {
    "critico_passed": 4,
    "critico_failed": 0,
    "importante_passed": 2,
    "importante_failed": 2,
    "advertencia_passed": 3,
    "advertencia_failed": 0
  },
  "exit_code": 1,
  "result": "FAILED_NON_CRITICAL"
}
```

### Modo Integrado (Con Generación de CSV)

#### Generación Validada Estándar

```bash
cd D:\OEDE\Webscrapping\database
python generar_csv_shiny_validado.py
```

**Comportamiento:**
1. Ejecuta validación completa
2. Si exit code = 0: genera CSV
3. Si exit code = 1 (warnings): advierte pero genera CSV
4. Si exit code = 2 (crítico): **ABORTA**, no genera CSV
5. Si exit code = 3 (excepción): **ABORTA**

**Output Esperado (con warnings):**

```
======================================================================
GENERACIÓN VALIDADA DE CSV PARA DASHBOARD SHINY
======================================================================

Fecha: 2025-11-07 14:45:22

[PASO 1/3] VALIDACIÓN DE CALIDAD DE DATOS
----------------------------------------------------------------------

Ejecutando: python validate_shiny_data_quality.py

[... salida de validación ...]

----------------------------------------------------------------------
Validación completada con código de salida: 1

[PASO 2/3] ANÁLISIS DE RESULTADOS
----------------------------------------------------------------------

⚠️  ADVERTENCIAS DETECTADAS
   Nivel de fallo: IMPORTANTE
   Algunos datos no cumplen umbrales IMPORTANTES
   Ejemplo: Skills ESCO pueden estar vacíos

   DECISIÓN: Generar CSV de todos modos
   (El dashboard funcionará parcialmente)

[PASO 3/3] GENERACIÓN DE CSV
----------------------------------------------------------------------

Ejecutando: python generar_csv_shiny_desde_db.py

[... salida de generación ...]

----------------------------------------------------------------------
Generación completada con código de salida: 0

✅ CSV generado exitosamente
   Ubicación: D:\OEDE\Webscrapping\Visual--\ofertas_esco_shiny.csv
   Tamaño: 12.45 MB

======================================================================
RESUMEN DE EJECUCIÓN
======================================================================

1. Validación: Exit code 1
2. Generación CSV: Exit code 0
3. Archivo CSV: ✅ Existe

⚠️  PROCESO COMPLETADO CON ADVERTENCIAS

El CSV fue generado pero pueden existir problemas de calidad.
```

#### Generación Forzada (Ignorar Errores)

```bash
python generar_csv_shiny_validado.py --force
```

Genera el CSV **incluso si hay errores críticos**. Usar con precaución.

**Cuándo Usar --force:**
- Solo para testing/debugging
- Cuando sabes que el problema no afecta tu análisis específico
- Cuando necesitas ver qué datos SÍ están disponibles
- NUNCA para producción sin supervisión

---

## Niveles de Validación

### NIVEL CRÍTICO

**Propósito:** Garantizar datos mínimos esenciales para que el dashboard cargue.

**Umbral:** ≥95% para joins, 100% para campos obligatorios

**Checks:**

| Check | Umbral | ¿Qué Valida? |
|-------|--------|--------------|
| **ESCO Occupation Match** | 95% | Ofertas tienen ocupación ESCO asignada (tabla ofertas_esco_matching) |
| **ISCO Nivel 1** | 95% | Ofertas tienen clasificación ISCO nivel 1 |
| **Título** | 100% | Todas las ofertas tienen título |
| **Fecha Publicación** | 100% | Todas las ofertas tienen fecha válida |

**Impacto si Falla:**
- ❌ CSV no se genera (exit code 2)
- ❌ Dashboard no puede cargar datos correctamente
- ❌ Pestañas de ESCO/ISCO completamente rotas

**Remediación si Falla:**
1. **ESCO/ISCO < 95%:**
   - Ejecutar `match_ofertas_to_esco.py` sobre ofertas sin matching
   - Verificar que Claude API esté funcionando
   - Revisar logs de matching

2. **Título vacío:**
   - Problema en scraping
   - Revisar `ofertas.titulo` en DB
   - Re-scrapear si es necesario

3. **Fecha inválida:**
   - Problema en scraping
   - Revisar formato de fechas en `ofertas.fecha_publicacion_original`

### NIVEL IMPORTANTE

**Propósito:** Garantizar que funcionalidades principales del dashboard tengan datos.

**Umbral:** ≥50% para features ESCO, ≥60-80% para features NLP

**Checks:**

| Check | Umbral | ¿Qué Valida? |
|-------|--------|--------------|
| **ESCO Skills Esenciales** | 50% | JSON en ofertas_esco_matching.esco_skills_esenciales_json no es NULL |
| **ESCO Skills Opcionales** | 50% | JSON en ofertas_esco_matching.esco_skills_opcionales_json no es NULL |
| **Soft Skills (NLP)** | 80% | JSON en ofertas_nlp_history.extracted_data contiene soft_skills_list |
| **Skills Técnicas (NLP)** | 60% | JSON en ofertas_nlp_history.extracted_data contiene skills_tecnicas_list |

**Impacto si Falla:**
- ⚠️ CSV se genera con warnings (exit code 1)
- ⚠️ Algunas pestañas del dashboard estarán vacías
- ⚠️ Pérdida de funcionalidad analítica

**Remediación si Falla:**
1. **ESCO Skills < 50%:**
   - **Causa:** `populate_esco_skills_in_db.py` no ejecutado o no existe
   - **Solución:** Crear/ejecutar script de enrichment de skills
   - Ver sección [Crear Script de Skills Enrichment](#crear-script-de-skills-enrichment)

2. **NLP Skills < umbral:**
   - **Causa:** Procesamiento NLP incompleto
   - **Solución:**
     ```bash
     cd D:\OEDE\Webscrapping\database
     python process_nlp_from_db_v5.py --mode production --only-empty
     ```

### NIVEL ADVERTENCIA

**Propósito:** Monitoreo de calidad general (no bloquea generación).

**Umbral:** ≥40-90% según campo

**Checks:**

| Check | Umbral | ¿Qué Valida? |
|-------|--------|--------------|
| **Empresa** | 90% | ofertas.empresa no es NULL ni vacío |
| **Localización** | 80% | ofertas.localizacion no es NULL ni vacío |
| **Nivel Educativo (NLP)** | 40% | extracted_data.nivel_educativo no es NULL |

**Impacto si Falla:**
- 📊 Solo informativo
- 📊 No afecta generación del CSV
- 📊 Puede reducir utilidad de ciertos análisis

**Remediación si Falla:**
1. **Empresa/Localización < umbral:**
   - Problema en calidad de scraping
   - Verificar fuente (Bumeran.com)
   - Algunos anuncios pueden no incluir estos datos

2. **Nivel Educativo < 40%:**
   - Normal: muchas ofertas no especifican educación
   - Solo actuar si cae significativamente

---

## Interpretación de Resultados

### Exit Codes

| Exit Code | Significado | Acción |
|-----------|-------------|--------|
| `0` | ✅ Todo OK | Generar CSV con confianza |
| `1` | ⚠️ Warnings (Importante falló) | Revisar y decidir |
| `2` | ❌ Error Crítico | NO generar CSV (o --force) |
| `3` | 💥 Excepción | Revisar logs, debugging |

### Ejemplos de Salidas y Acciones

#### Ejemplo 1: Todo OK

```
Exit code: 0

🎉 VALIDACIÓN EXITOSA

Todas las validaciones pasaron.
```

**Acción:** Proceder con generación de CSV sin preocupaciones.

#### Ejemplo 2: Skills ESCO Vacíos (Actual)

```
Exit code: 1

🔴 VALIDACIÓN FALLIDA

Resumen:
  • Validaciones Críticas: 4 passed, 0 failed
  • Validaciones Importantes: 2 passed, 2 failed  ← PROBLEMA AQUÍ
  • Validaciones de Advertencia: 3 passed, 0 failed

Fallos Detectados:
  ❌ ESCO Skills Esenciales: 0.00% (esperado: ≥50%)
  ❌ ESCO Skills Opcionales: 0.00% (esperado: ≥50%)
```

**Interpretación:**
- Datos base están OK (crítico passed)
- Skills ESCO están vacíos (importante failed)
- Empresa/localización están OK (advertencia passed)

**Impacto:**
- Dashboard cargará y funcionará
- Pestaña "Análisis de Skills ESCO" estará vacía
- Otras pestañas (NLP, ocupaciones, ISCO) funcionarán

**Acción:**
1. **Corto plazo:** Generar CSV de todos modos (automático con wrapper)
2. **Mediano plazo:** Implementar script de populate skills (ver sección siguiente)

#### Ejemplo 3: Pocas Ocupaciones ESCO

```
Exit code: 2

❌ VALIDACIÓN CRÍTICA FALLIDA

  ❌ ESCO Occupation Match: 89.50% (esperado: ≥95%)
```

**Interpretación:**
- Menos del 95% de ofertas tienen ocupación ESCO
- Dashboard de ocupaciones/ISCO será inconsistente

**Impacto:**
- Pestaña "Análisis de Ocupaciones ESCO" tendrá datos parciales
- Jerarquía ISCO incompleta

**Acción:**
```bash
cd D:\OEDE\Webscrapping\database
python match_ofertas_to_esco.py  # Re-ejecutar matching
```

---

## Acciones Recomendadas

### Crear Script de Skills Enrichment

**Problema:** ESCO Skills están vacíos (0% completitud).

**Solución:** Crear `database/populate_esco_skills_in_db.py`

**Pseudo-código:**

```python
#!/usr/bin/env python3
"""
Script para popular skills ESCO basándose en ocupaciones ya mapeadas
"""
import sqlite3
import json
from pathlib import Path

def cargar_taxonomia_esco():
    """Carga la taxonomía ESCO (ocupaciones → skills)"""
    # Leer archivo esco_occupations_es.csv
    # Retornar diccionario: {esco_code: {"essential": [...], "optional": [...]}}
    pass

def obtener_ofertas_sin_skills(conn):
    """Obtiene ofertas con ocupación ESCO pero sin skills"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_oferta, claude_esco_code
        FROM ofertas_esco_matching
        WHERE claude_esco_code IS NOT NULL
          AND (esco_skills_esenciales_json IS NULL
               OR esco_skills_opcionales_json IS NULL)
    """)
    return cursor.fetchall()

def popular_skills(conn, id_oferta, esco_code, taxonomia):
    """Actualiza DB con skills para una oferta"""
    skills = taxonomia.get(esco_code, {})

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ofertas_esco_matching
        SET esco_skills_esenciales_json = ?,
            esco_skills_opcionales_json = ?,
            skills_updated_at = CURRENT_TIMESTAMP
        WHERE id_oferta = ?
    """, (
        json.dumps(skills.get("essential", []), ensure_ascii=False),
        json.dumps(skills.get("optional", []), ensure_ascii=False),
        id_oferta
    ))

def main():
    conn = sqlite3.connect("bumeran_scraping.db")
    taxonomia = cargar_taxonomia_esco()
    ofertas = obtener_ofertas_sin_skills(conn)

    print(f"Enriqueciendo {len(ofertas)} ofertas con skills ESCO...")

    for id_oferta, esco_code in ofertas:
        popular_skills(conn, id_oferta, esco_code, taxonomia)

    conn.commit()
    conn.close()

    print("✅ Skills ESCO populados exitosamente")

if __name__ == '__main__':
    main()
```

**Uso:**

```bash
cd D:\OEDE\Webscrapping\database
python populate_esco_skills_in_db.py
python validate_shiny_data_quality.py  # Verificar que ahora pase
python generar_csv_shiny_validado.py   # Regenerar CSV
```

### Re-ejecutar NLP Para Ofertas Sin Procesar

**Problema:** Skills NLP por debajo del umbral.

```bash
cd D:\OEDE\Webscrapping\database
python process_nlp_from_db_v5.py --mode production --only-empty
```

Esto procesa solo las ofertas que aún no tienen datos NLP (v5.1.0).

### Re-ejecutar ESCO Matching

**Problema:** Ocupaciones ESCO por debajo del 95%.

```bash
cd D:\OEDE\Webscrapping\database
python match_ofertas_to_esco.py
```

**Nota:** Este script ya tiene lógica para procesar solo ofertas sin matching previo.

---

## Integración en Workflow

### Workflow Manual (Recomendado Actualmente)

```bash
# 1. Scraping (si hay nuevas ofertas)
cd D:\OEDE\Webscrapping\01_sources\bumeran\scrapers
python run_scraping_completo.py

# 2. NLP Processing (incremental)
cd D:\OEDE\Webscrapping\database
python process_nlp_from_db_v5.py --mode production --only-empty

# 3. ESCO Matching (incremental)
python match_ofertas_to_esco.py

# 4. ESCO Skills Enrichment (si existe)
python populate_esco_skills_in_db.py  # TBD

# 5. Validación + Generación de CSV
python generar_csv_shiny_validado.py

# 6. Reiniciar Dashboard
cd D:\OEDE\Webscrapping\Visual--
powershell -File restart_dashboard.ps1
```

### Workflow Automatizado (Futuro)

**Crear:** `database/run_full_pipeline_validated.bat`

```batch
@echo off
echo ====================================================
echo PIPELINE COMPLETO CON VALIDACIÓN
echo ====================================================

cd /d D:\OEDE\Webscrapping\database

echo.
echo [1/5] Procesando NLP (solo ofertas nuevas)...
python process_nlp_from_db_v5.py --mode production --only-empty
if errorlevel 1 goto error

echo.
echo [2/5] Matching ESCO Occupations...
python match_ofertas_to_esco.py
if errorlevel 1 goto error

echo.
echo [3/5] Enriqueciendo ESCO Skills...
python populate_esco_skills_in_db.py
if errorlevel 1 goto error

echo.
echo [4/5] Validando y generando CSV...
python generar_csv_shiny_validado.py
if errorlevel 1 goto error

echo.
echo [5/5] Reiniciando Dashboard...
cd /d D:\OEDE\Webscrapping\Visual--
powershell -File restart_dashboard.ps1

echo.
echo ====================================================
echo PIPELINE COMPLETADO EXITOSAMENTE
echo ====================================================
goto end

:error
echo.
echo ERROR EN EL PIPELINE
echo Revisa los logs para más detalles
exit /b 1

:end
```

**Uso:**

```batch
D:\OEDE\Webscrapping\database\run_full_pipeline_validated.bat
```

### Scheduled Task (Windows)

**Crear tarea programada para ejecutar diariamente:**

```powershell
# Crear scheduled task
$action = New-ScheduledTaskAction -Execute "D:\OEDE\Webscrapping\database\run_full_pipeline_validated.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$principal = New-ScheduledTaskPrincipal -UserId "SISTEMA_USER" -LogonType ServiceAccount

Register-ScheduledTask -Action $action -Trigger $trigger -Principal $principal `
    -TaskName "MOL_UpdateDashboard" `
    -Description "Actualiza el dashboard MOL con validación de datos"
```

---

## Troubleshooting

### Problema 1: Validación Nunca Termina

**Síntomas:**
- Script cuelga sin output
- Proceso no responde

**Causas Posibles:**
1. Base de datos bloqueada por otro proceso
2. Query muy lento en tabla grande
3. Conexión a DB corrupta

**Solución:**

```bash
# 1. Verificar procesos que usan la DB
tasklist | findstr python
tasklist | findstr Rscript

# 2. Cerrar procesos si es seguro
taskkill /IM python.exe /F
taskkill /IM Rscript.exe /F

# 3. Re-ejecutar validación
python validate_shiny_data_quality.py
```

### Problema 2: Exit Code 3 (Excepción)

**Síntomas:**
```
💥 EXCEPCIÓN EN VALIDACIÓN
El script de validación encontró un error inesperado
```

**Causas Posibles:**
1. Base de datos no existe o ruta incorrecta
2. Tabla o columna no existe (schema desactualizado)
3. Error de permisos de lectura

**Solución:**

```bash
# 1. Verificar que la DB existe
ls D:\OEDE\Webscrapping\database\bumeran_scraping.db

# 2. Verificar schema de tablas
sqlite3 D:\OEDE\Webscrapping\database\bumeran_scraping.db ".schema ofertas"
sqlite3 D:\OEDE\Webscrapping\database\bumeran_scraping.db ".schema ofertas_esco_matching"

# 3. Ejecutar validación con debug
python validate_shiny_data_quality.py --debug  # (si tienes flag debug)
```

### Problema 3: CSV No Se Genera Después de Validación OK

**Síntomas:**
- Validación pasa (exit code 0)
- Wrapper inicia generación de CSV
- CSV no aparece en Visual--/

**Causas Posibles:**
1. Error en `generar_csv_shiny_desde_db.py`
2. Permisos de escritura en carpeta Visual--
3. Espacio en disco insuficiente

**Solución:**

```bash
# 1. Verificar permisos
cd D:\OEDE\Webscrapping\Visual--
# Intentar crear archivo de prueba
echo "test" > test.txt
del test.txt

# 2. Verificar espacio en disco
df -h D:

# 3. Ejecutar generación manualmente para ver error
cd D:\OEDE\Webscrapping\database
python generar_csv_shiny_desde_db.py
```

### Problema 4: Dashboard Muestra Datos Viejos

**Síntomas:**
- CSV nuevo generado correctamente
- Dashboard sigue mostrando datos antiguos
- Fecha de última actualización no cambia

**Causa:**
- Dashboard Shiny no recargó los datos

**Solución:**

```bash
# 1. Reiniciar dashboard manualmente
cd D:\OEDE\Webscrapping\Visual--
powershell -File restart_dashboard.ps1

# 2. O reiniciar proceso Rscript
taskkill /IM Rscript.exe /F
# Esperar 3 segundos
# Volver a iniciar dashboard
```

---

## FAQ

### ¿Con Qué Frecuencia Debo Validar?

**Respuesta:** Cada vez que vayas a actualizar el dashboard.

**Escenarios:**

1. **Actualización Manual Diaria:**
   - Ejecuta `generar_csv_shiny_validado.py` (incluye validación automática)

2. **Después de Re-procesar Datos:**
   - Si ejecutaste NLP o ESCO matching, valida antes de regenerar CSV

3. **Después de Cambios en Schema:**
   - Si modificaste tablas o columnas, ejecuta validación standalone para verificar

### ¿Puedo Modificar los Umbrales de Validación?

**Respuesta:** Sí, pero con cuidado.

**Ubicación:** `database/validate_shiny_data_quality.py`, líneas ~150-250

**Ejemplo:**

```python
# Cambiar umbral de ESCO Skills de 50% a 30%
ValidationRule(
    column="esco_skills_esenciales_json",
    description="ESCO Skills Esenciales (JSON)",
    threshold=0.30,  # Era 0.50
    level="importante",
    check_type="json_not_null"
)
```

**Recomendación:** Solo reduce umbrales si entiendes el impacto en el dashboard.

### ¿Qué Hago Si Siempre Falla ESCO Skills?

**Respuesta:** Implementa el script de enrichment (ver sección correspondiente).

**Alternativa temporal:** Oculta la pestaña de Skills ESCO del dashboard:

```r
# En app.R, comentar el menuItem:
# menuItem("Análisis de Skills ESCO", tabName = "skills_esco", icon = icon("cogs"))
```

### ¿Cómo Integro Validación en CI/CD?

**Respuesta:**

```yaml
# Ejemplo para GitHub Actions
name: Update Dashboard
on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM diario

jobs:
  update:
    runs-on: windows-latest
    steps:
      - name: Validate Data
        run: python database/validate_shiny_data_quality.py --json

      - name: Check Exit Code
        run: |
          if [ $? -eq 2 ]; then
            echo "Critical validation failed!"
            exit 1
          fi

      - name: Generate CSV
        run: python database/generar_csv_shiny_desde_db.py

      - name: Deploy Dashboard
        run: # tu comando de deploy
```

### ¿Puedo Ejecutar Validación Desde R?

**Respuesta:** Sí, usando `system()`:

```r
# Ejecutar validación desde R
exit_code <- system("python database/validate_shiny_data_quality.py", intern = FALSE)

if (exit_code == 2) {
  stop("Critical data validation failed. Aborting.")
} else if (exit_code == 1) {
  warning("Data validation warnings detected. Proceeding with caution.")
}

# Cargar datos
datos <- read.csv("Visual--/ofertas_esco_shiny.csv")
```

---

**Documento generado automáticamente**
**Última actualización:** 2025-11-07
**Versión:** 1.0
