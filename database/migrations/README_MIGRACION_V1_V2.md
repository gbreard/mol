# Migración de Base de Datos v1 → v2

**Fecha de migración:** 2025-11-03
**Estado:** COMPLETADA
**Resultado:** 10,660 ofertas sincronizadas entre v1 y v2

---

## Contexto

El proyecto de scraping de Bumeran.com.ar está migrando gradualmente desde un esquema de base de datos v1 (22 tablas) hacia un esquema v2 más robusto (31 tablas). La migración se realiza mediante una estrategia de **dual-write** para evitar interrupciones en producción.

### Esquema v1 (Producción actual)
- **Tabla principal:** `ofertas`
- **Estructura:** Denormalizada, 39 campos por oferta
- **Estado:** En producción, utilizada por dashboard operativo

### Esquema v2 (Objetivo)
- **Tabla principal:** `ofertas_raw`
- **Estructura:** JSON inmutable + SHA256 hash
- **Campos:**
  - `id` (INTEGER PRIMARY KEY)
  - `id_oferta` (TEXT UNIQUE)
  - `scraping_session_id` (INTEGER FK)
  - `raw_json` (TEXT)
  - `content_hash` (TEXT)
  - `scrapeado_en` (TIMESTAMP)
  - `source` (TEXT)
  - `url_oferta` (TEXT)
- **Ventajas:** Inmutabilidad, auditoría completa, detección de cambios

---

## Estrategia de Migración: Dual-Write

La migración se implementó mediante **dual-write strategy**:

1. Todas las escrituras van simultáneamente a v1 (CRITICAL) y v2 (WARNING)
2. Si v2 falla, solo se registra WARNING y se continúa con v1
3. v1 permanece como source of truth durante la transición
4. Una vez validada v2, se puede hacer el switch

### Implementación

**Archivo:** `database/db_manager.py`

```python
def insert_ofertas(self, ofertas: pd.DataFrame) -> int:
    # Escribir en v1 (CRITICAL)
    ofertas.to_sql('ofertas', self.conn, if_exists='append', index=False)

    # DUAL-WRITE: Escribir también en v2 (WARNING)
    if self.enable_dual_write and self.db_v2:
        try:
            logger.info(f"[DUAL-WRITE] Escribiendo {len(ofertas)} ofertas en schema v2...")
            self.db_v2.insert_ofertas_raw(ofertas)
            logger.info(f"[DUAL-WRITE] OK - {len(ofertas)} ofertas escritas en v2")
        except Exception as e:
            logger.warning(f"[DUAL-WRITE] ERROR escribiendo en v2: {e}")
            logger.warning("[DUAL-WRITE] v1 OK, v2 falló (continuando...)")
```

---

## Proceso de Migración Ejecutado

### FASE 1: Migración Histórica (5,479 ofertas)

**Script:** `migrate_historical_data.py`
**Fecha:** 2025-11-03 10:15:54
**Duración:** 0.36 segundos
**Resultado:** 5,479 ofertas migradas exitosamente

#### Pasos ejecutados:
1. Creación de sesión de scraping (ID=1)
2. Extracción de todas las ofertas de v1
3. Conversión a JSON + cálculo de SHA256
4. Inserción en `ofertas_raw` con `INSERT OR IGNORE`
5. Procesamiento en batches de 500 registros
6. Validación de integridad

#### Resultados:
```
Total ofertas en v1: 5,479
Total ofertas en v2 (antes): 0
Total ofertas en v2 (después): 5,479
Velocidad: 16,265 ofertas/segundo
```

**Log:** `database/migrations/migration_historical.log`

---

### FASE 2: Habilitación de Dual-Write

**Archivo modificado:** `database/config.py`
**Fecha:** 2025-11-03
**Cambio:**

```python
DB_CONFIG = {
    'db_path': os.getenv('DB_PATH', 'database/bumeran_scraping.db'),
    'enable_dual_write': True,  # ← AGREGADO
}
```

---

### FASE 3: Problema Identificado

**Fecha:** 2025-11-03
**Issue:** El scraping del 3 de noviembre capturó 5,181 nuevas ofertas pero solo las escribió en v1, **no en v2**.

**Causa raíz:** El scheduler (`run_scheduler.py`) no tenía habilitado el dual-write al momento del scraping porque se ejecutó **antes** de la actualización de `DB_CONFIG`.

**Evidencia:**
```sql
SELECT COUNT(*) FROM ofertas WHERE DATE(scrapeado_en) = '2025-11-03';
-- Resultado: 5,181 ofertas

SELECT COUNT(*) FROM ofertas_raw WHERE DATE(scrapeado_en) = '2025-11-03';
-- Resultado: 0 ofertas (problema detectado)
```

---

### FASE 4: Migración de Ofertas Faltantes (5,181 ofertas)

**Script:** `migrate_missing_ofertas.py`
**Fecha:** 2025-11-03
**Objetivo:** Migrar las 5,181 ofertas del 3/11 que no se escribieron en v2

#### Pasos ejecutados:
1. Identificación de ofertas con `scrapeado_en = '2025-11-03'`
2. Búsqueda/creación de sesión de scraping del 3/11
3. Conversión a JSON + SHA256
4. Inserción en `ofertas_raw` con `INSERT OR IGNORE`
5. Actualización de sesión con contadores
6. Validación final de sincronización

#### Resultados:
```
Ofertas faltantes detectadas: 5,181
Ofertas migradas: 5,181
Total en v1 (final): 10,660
Total en v2 (final): 10,660
Estado: SINCRONIZACIÓN COMPLETA
```

---

## Validación de Integridad

### Tests ejecutados:

```bash
# 1. Conteo total
SELECT COUNT(*) FROM ofertas;        -- 10,660
SELECT COUNT(*) FROM ofertas_raw;    -- 10,660

# 2. IDs únicos
SELECT COUNT(DISTINCT id_oferta) FROM ofertas;      -- 10,660
SELECT COUNT(DISTINCT id_oferta) FROM ofertas_raw;  -- 10,660

# 3. Ofertas en v1 pero no en v2
SELECT COUNT(*) FROM ofertas
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas_raw);
-- Resultado: 0

# 4. Ofertas en v2 pero no en v1
SELECT COUNT(*) FROM ofertas_raw
WHERE id_oferta NOT IN (SELECT id_oferta FROM ofertas);
-- Resultado: 0
```

### Resultado: ✅ SINCRONIZACIÓN 100% COMPLETA

---

## Scripts de Migración

### 1. `migrate_historical_data.py`

**Propósito:** Migrar datos históricos existentes en v1 a v2

**Uso:**
```bash
# Dry-run (simulación)
python migrate_historical_data.py --dry-run

# Migración real
python migrate_historical_data.py

# Con batch personalizado
python migrate_historical_data.py --batch-size 100
```

**Características:**
- Sesión de scraping para tracking
- Barra de progreso con tqdm
- Procesamiento en batches
- Rollback automático en errores
- Log detallado

---

### 2. `migrate_missing_ofertas.py`

**Propósito:** Migrar ofertas específicas que faltaban en v2

**Uso:**
```bash
python migrate_missing_ofertas.py
```

**Características:**
- Identifica ofertas por fecha
- Reutiliza/crea sesión de scraping
- Inserción con `INSERT OR IGNORE`
- Validación de sincronización

---

### 3. `test_dual_write.py`

**Propósito:** Verificar que dual-write funciona correctamente

**Uso:**
```bash
cd database
python test_dual_write.py
```

**Test realizado:**
1. Crea oferta de prueba
2. Inserta con dual-write habilitado
3. Verifica inserción en v1 y v2
4. Valida contenido JSON y hash
5. Limpia datos de prueba

---

## Estado Actual del Sistema

### Base de Datos

| Tabla | Registros | Estado |
|-------|-----------|--------|
| `ofertas` (v1) | 10,660 | Producción |
| `ofertas_raw` (v2) | 10,660 | Sincronizada |
| `scraping_sessions` | 1 | Activa |

### Configuración

- **Dual-write:** ✅ Habilitado en `DB_CONFIG`
- **Scheduler:** ⚠️ Debe reiniciarse para tomar nuevo config
- **Dashboard operativo:** ✅ Consulta v1, muestra 10,660 ofertas
- **Dashboard Shiny:** ⚠️ Usa CSV estático (268 ofertas)

---

## Próximos Pasos

### Corto Plazo

1. **Validar dual-write en próximo scraping**
   - Esperar ejecución programada (lunes/jueves 8am)
   - Verificar que nuevas ofertas se escriban en v1 y v2
   - Monitorear logs de dual-write

2. **Actualizar CSV del Dashboard Shiny**
   - Regenerar `ofertas_esco_shiny.csv` con 10,660 ofertas
   - Re-deployment en shinyapps.io

### Mediano Plazo

3. **Migrar consultas del dashboard a v2**
   - Actualizar `dashboard_scraping_v4.py` para consultar v2
   - Testing exhaustivo
   - Switch gradual

4. **Deprecar v1 gradualmente**
   - Una vez validado v2 en producción
   - Mantener v1 como backup temporal
   - Documentar plan de deprecación

---

## Logs y Archivos Relacionados

- **Log migración histórica:** `database/migrations/migration_historical.log`
- **Scripts:** `database/migrations/migrate_*.py`
- **Config:** `database/config.py`
- **Database manager:** `database/db_manager.py`
- **Test:** `database/test_dual_write.py`

---

## Contacto y Soporte

Para consultas sobre esta migración:
- **Fecha de ejecución:** 2025-11-03
- **Ejecutado por:** Claude Code AI
- **Validado por:** Usuario OEDE

---

**Última actualización:** 2025-11-03
