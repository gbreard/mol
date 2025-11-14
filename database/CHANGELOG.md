# Changelog - Base de Datos Bumeran Scraping

Registro cronológico de cambios significativos en la base de datos SQLite.

---

## [v2.0.1] - 2025-11-03

### Mejoras de Calidad de Datos

**Problema identificado:** 5,181 ofertas del 3/11 tenian campos criticos vacios (100% descripcion, modalidad_trabajo, tipo_trabajo, id_empresa).

**Causa raiz:** Bug en `run_scheduler.py` - guardaba ofertas en BD sin llamar a `procesar_ofertas()`.

#### Corregido

- **`run_scheduler.py`** (lineas 105-116): **BUG FIX CRITICO**
  - Agregado paso de procesamiento antes de insercion en BD
  - Ahora llama a `scraper.scraper.procesar_ofertas()` para normalizar fechas y campos
  - Evita guardado de ofertas con datos incompletos

  ```python
  # 4. Procesar ofertas (agregar fechas normalizadas y campos adicionales)
  logger.info("Procesando fechas y campos adicionales...")
  ofertas_list = df_ofertas.to_dict('records')
  df_ofertas_procesadas = scraper.scraper.procesar_ofertas(ofertas_list)

  # 5. Guardar en SQLite
  with DatabaseManager(**DB_CONFIG) as db:
      ofertas_insertadas = db.insert_ofertas(df_ofertas_procesadas)  # FIXED
  ```

#### Añadido

- **`01_sources/bumeran/scrapers/bumeran_scraper.py`** (lineas 805-850):
  - **Validacion de calidad en procesar_ofertas()**
  - Verifica 6 campos criticos: titulo, descripcion, empresa, modalidad_trabajo, tipo_trabajo, id_empresa
  - Rechaza ofertas con campos criticos vacios
  - Logging de advertencias con estadisticas de rechazo
  - Primera capa de defensa contra datos incompletos

- **`database/db_manager.py`** (lineas 195-263):
  - **Validacion de calidad en insert_ofertas()**
  - Segunda capa de validacion antes de insercion en BD
  - Mismos 6 campos criticos validados
  - Rechaza ofertas defectuosas antes de commit
  - Proteccion adicional contra inconsistencias

- **`database/verify_data_quality.py`**: Script de verificacion
  - Analisis exhaustivo de campos criticos
  - Distribucion de ofertas incompletas por fecha
  - Modo detallado con flag `--detailed`
  - Uso: `python database/verify_data_quality.py [--detailed]`

- **`database/delete_incomplete_ofertas_nov3.py`**: Script de limpieza
  - Eliminacion segura con confirmacion interactiva
  - Modo dry-run para simulacion: `--dry-run`
  - Elimina de v1 y v2 simultaneamente
  - Logging detallado de operaciones

#### Eliminado

- **5,181 ofertas defectuosas del 3/11**
  - Fecha de eliminacion: 2025-11-03 22:28
  - Razon: Datos incompletos (100% campos criticos vacios)
  - Herramienta: `database/delete_incomplete_ofertas_nov3.py`
  - **Estado BD antes**: 10,660 ofertas (42.6% completas)
  - **Estado BD despues**: 5,479 ofertas (82.8% completas)

#### Impacto en Calidad

**Antes (2025-11-03 pre-limpieza):**
```
Total ofertas:          10,660
Ofertas completas:      4,536 (42.6%)
Ofertas incompletas:    6,124 (57.4%)

Campos criticos vacios:
- descripcion:          5,181 (48.6%)
- modalidad_trabajo:    5,181 (48.6%)
- tipo_trabajo:         5,181 (48.6%)
- id_empresa:           6,124 (57.4%)
```

**Despues (2025-11-03 post-limpieza + validaciones):**
```
Total ofertas:          5,479
Ofertas completas:      4,536 (82.8%)
Ofertas incompletas:    943 (17.2%)

Campos criticos vacios:
- descripcion:          0 (0.0%)   ✓ PERFECTO
- modalidad_trabajo:    0 (0.0%)   ✓ PERFECTO
- tipo_trabajo:         0 (0.0%)   ✓ PERFECTO
- id_empresa:           943 (17.2%) (ofertas del 31/10, menos critico)
```

**Mejora neta:** +40.2% en ofertas completas (de 42.6% a 82.8%)

#### Archivos Afectados

**Modificados:**
- `run_scheduler.py`: Bug fix critico
- `01_sources/bumeran/scrapers/bumeran_scraper.py`: Validacion layer 1
- `database/db_manager.py`: Validacion layer 2

**Creados:**
- `database/verify_data_quality.py`: Herramienta de verificacion
- `database/delete_incomplete_ofertas_nov3.py`: Herramienta de limpieza

#### Validacion

```bash
# Verificar calidad actual
python database/verify_data_quality.py

# Verificar con detalles
python database/verify_data_quality.py --detailed
```

#### Lecciones Aprendidas

1. **Validacion multinivel es esencial**: Dos capas (processing + insertion) previenen corrupciones
2. **Testing de integracion necesario**: Bug no detectado hasta produccion
3. **Herramientas de verificacion criticas**: `verify_data_quality.py` permite deteccion temprana
4. **Limpieza controlada**: Scripts con dry-run y confirmacion evitan errores

---

## [v2.0.0] - 2025-11-03

### Migración v1 → v2

**Estado:** EN CURSO (Dual-write habilitado)

**Objetivo:** Migración gradual de esquema denormalizado (v1) a esquema inmutable basado en JSON (v2).

#### Añadido

- **Nuevo esquema v2** con 31 tablas (vs 22 en v1)
- **Tabla `ofertas_raw`**: Almacenamiento inmutable de ofertas en JSON
  - Campo `raw_json`: JSON completo de la oferta
  - Campo `content_hash`: SHA256 para detección de cambios
  - Campo `scraping_session_id`: FK a sesión de scraping
  - Índices optimizados para búsquedas
- **Tabla `scraping_sessions`**: Tracking completo de sesiones de scraping
  - Métricas de performance (ofertas/min)
  - Status de sesión (running, completed, failed)
  - Contadores de ofertas (total, nuevas, duplicadas, errores)
- **Dual-write strategy**: Escritura simultánea en v1 y v2
  - v1 (CRITICAL): Source of truth actual
  - v2 (WARNING): Nueva arquitectura en validación
  - Configuración en `database/config.py`

#### Modificado

- **`database/db_manager.py`**: Implementación de dual-write
  - Nuevo parámetro `enable_dual_write` (default: True)
  - Conexión dual a v1 y v2
  - Manejo de errores con fallback a v1
- **`database/config.py`**: Agregado flag `enable_dual_write`

#### Migración de Datos

- **FASE 1** (2025-11-03 10:15): Migración histórica
  - 5,479 ofertas migradas de v1 a v2
  - Velocidad: 16,265 ofertas/segundo
  - Duración: 0.36 segundos
  - Script: `database/migrations/migrate_historical_data.py`

- **FASE 2** (2025-11-03): Habilitación de dual-write
  - Flag activado en `DB_CONFIG`
  - Nuevas ofertas se escriben automáticamente en ambos esquemas

- **FASE 3** (2025-11-03): Detección de gap
  - 5,181 ofertas del 3/11 solo en v1
  - Causa: Scraping ejecutado antes de activar dual-write

- **FASE 4** (2025-11-03): Sincronización completa
  - 5,181 ofertas faltantes migradas a v2
  - Script: `database/migrations/migrate_missing_ofertas.py`
  - **Estado final**: 10,660 ofertas sincronizadas 100%

#### Validación

```sql
-- Verificación de sincronización
SELECT COUNT(*) FROM ofertas;        -- 10,660
SELECT COUNT(*) FROM ofertas_raw;    -- 10,660

-- Ofertas solo en v1
SELECT COUNT(*) FROM ofertas
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_raw);
-- Resultado: 0 ✓

-- Ofertas solo en v2
SELECT COUNT(*) FROM ofertas_raw
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas);
-- Resultado: 0 ✓
```

#### Archivos de Migración

- `database/migrations/README_MIGRACION_V1_V2.md`: Documentación completa
- `database/migrations/migrate_historical_data.py`: Script de migración inicial
- `database/migrations/migrate_missing_ofertas.py`: Script de sincronización
- `database/test_dual_write.py`: Test de dual-write

---

## [v1.2.0] - 2025-10-31

### Correcciones en Dashboard

#### Modificado

- **`dashboard_scraping_v4.py`** línea 53:
  - Soporte para formato ISO8601 con microsegundos
  - Cambio: `pd.to_datetime(df['scrapeado_en'])` → `pd.to_datetime(df['scrapeado_en'], format='ISO8601')`
  - Resuelve: `ValueError` al parsear timestamps con formato `2025-10-31T13:24:43.056902`

- **`dashboard_scraping_v4.py`** línea 1910:
  - Corrección de puerto: 8053 → 8052
  - Alineación con documentación

---

## [v1.1.0] - 2025-10-31

### Dashboard v4 Lanzado

#### Añadido

- **Dashboard v4** con explorador de tablas
  - Tab Overview: Estadísticas principales
  - Tab Keywords: Performance de keywords
  - Tab Calidad: Análisis de completitud
  - Tab Alertas: Sistema de alertas
  - Tab Datos: Acceso a 38 variables
  - Tab Diccionario: Documentación de campos
  - **Tab Explorador**: Navegación de las 22 tablas
- Auto-refresh cada 5 minutos
- Soporte para 10,660 ofertas

---

## [v1.0.0] - 2025-10-30

### Release Inicial

#### Esquema v1 (22 tablas)

**Tabla principal:** `ofertas`
- 39 campos denormalizados
- Estructura monolítica
- Tracking con `scrapeado_en`
- Índices básicos

**Características:**
- Scraping incremental con deduplicación
- Tracking de IDs procesados
- Métricas de scraping
- Soporte para scheduling automático

**Archivos de esquema:**
- `database/schema.sql`: Definición de tablas v1
- `database/db_manager.py`: Manager de conexión y operaciones

---

## Próximos Pasos

### v2.1.0 (Planificado)

- [ ] Migrar consultas del dashboard a v2
- [ ] Testing exhaustivo de v2 en producción
- [ ] Monitoreo de performance v2 vs v1
- [ ] Validar dual-write en próximo scraping programado

### v3.0.0 (Futuro)

- [ ] Switch completo a v2
- [ ] Deprecación de v1 (mantener como backup temporal)
- [ ] Implementación de vistas materializadas
- [ ] Optimización de índices en v2

---

## Formato del Changelog

Este changelog sigue los principios de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

**Categorías:**
- **Añadido**: Nuevas funcionalidades
- **Modificado**: Cambios en funcionalidad existente
- **Deprecado**: Funcionalidad que será removida
- **Eliminado**: Funcionalidad removida
- **Corregido**: Bugs corregidos
- **Seguridad**: Cambios relacionados con seguridad

---

**Última actualización:** 2025-11-03
**Mantenido por:** Claude Code (OEDE)
