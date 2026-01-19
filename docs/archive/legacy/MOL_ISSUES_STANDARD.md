# MOL - Issues en Formato Estándar

> **Proyecto:** https://linear.app/molar/project/mol-monitor-ofertas-laborales-2a9662bfa15f
> **Última actualización:** 2025-12-03
> **Formato:** Basado en plantilla CCT-RAG

---

## Índice por Prioridad

### 🔴 Alta Prioridad
- [MOL-5](#mol-5-v84-resolver-errores-sector_funcion) - Resolver sector_funcion
- [MOL-6](#mol-6-expandir-gold-set-a-50-casos) - Expandir Gold Set
- [MOL-18](#mol-18-automatizar-scrapers-faltantes) - Automatizar scrapers
- [MOL-26](#mol-26-backup-automático-de-sqlite) - Backup automático (NUEVO)
- [MOL-23](#mol-23-versionado-de-datos) - Versionado de datos (NUEVO)

### 🟡 Media Prioridad
- [MOL-7](#mol-7-métricas-recall-y-f1) - Métricas Recall/F1
- [MOL-8](#mol-8-resolver-casos-bilingües) - Casos bilingües
- [MOL-19](#mol-19-pipeline-automático-post-scraping) - Pipeline automático
- [MOL-14](#mol-14-alertas-emailslack) - Alertas
- [MOL-16](#mol-16-fix-shinytree) - Fix shinyTree
- [MOL-24](#mol-24-entity-resolution-cross-source) - Entity resolution (NUEVO)
- [MOL-25](#mol-25-drift-detection) - Drift detection (NUEVO)

### ⚪ Baja Prioridad
- [MOL-9](#mol-9-cicd-github-actions) - CI/CD
- [MOL-10](#mol-10-regex-abreviaciones-argentinas) - Regex abreviaciones
- [MOL-11](#mol-11-niveles-jerárquicos) - Niveles jerárquicos
- [MOL-12](#mol-12-consolidar-nlp-v6v7) - Consolidar NLP
- [MOL-13](#mol-13-panel-administración) - Panel admin
- [MOL-15](#mol-15-limpieza-jsons) - Limpieza JSONs
- [MOL-17](#mol-17-auth-shinymanager) - Auth shinymanager
- [MOL-20](#mol-20-centralizar-logs) - Centralizar logs
- [MOL-21](#mol-21-deprecar-dashboards) - Deprecar dashboards
- [MOL-22](#mol-22-documentar-apis) - Documentar APIs

---

# 🔴 ALTA PRIORIDAD

---

## MOL-5: [v8.4] Resolver errores sector_funcion

### Contexto
El 50% de los errores del gold set (4 de 8) son del tipo `sector_funcion`, donde el sistema mapea ofertas a ocupaciones ESCO de sectores completamente diferentes. Este es el error más crítico porque produce clasificaciones absurdas (ej: "Ejecutivo de cuentas" → "Agente de empleo").

**Historia de intentos:**
- v8.1: Ajustes por nivel jerárquico → No resolvió sector_funcion
- v8.2: 6 familias funcionales → Mejoró categorización, no precisión
- v8.3: +4 familias específicas → Mejora parcial (57.9% → 63.2%)

Referencia: `docs/CHANGELOG.md#v83`, `docs/TICKETS_CONTEXT.md#mol-5`

### Objetivo
Reducir errores de tipo `sector_funcion` de 4 casos a ≤1, alcanzando precisión ≥85% en gold set.

### Archivos involucrados
- `database/matching_rules_v84.py` - NUEVO (copiar de v83)
- `database/matching_rules_v83.py` - Referencia (NO modificar)
- `database/match_ofertas_multicriteria.py` - Referencia (NO modificar)
- `database/gold_set_manual_v1.json` - Referencia (casos de prueba)
- `database/test_gold_set_manual.py` - Modificar (apuntar a v84)
- `docs/CHANGELOG.md` - Agregar entrada v8.4

### Criterios de Aceptación
- [ ] Precisión gold set ≥85% (actual: ~80%)
- [ ] Casos sector_funcion ≤1 (actual: 4)
- [ ] Caso "Ejecutivo de cuentas" (1118027276) matchea a ventas, no contadores
- [ ] Caso "Account Executive Hunter" (1118028887) matchea a comercial, no RRHH
- [ ] Caso "Analista administrativo" (1118028376) matchea a admin, no negocios
- [ ] Caso "Asesor comercial plan ahorro" (1118028833) matchea a ventas
- [ ] NO hay regresiones en casos que antes funcionaban
- [ ] Test pasa: `python database/test_gold_set_manual.py`
- [ ] Entrada agregada en `docs/CHANGELOG.md`

### Subtareas
- [ ] Analizar los 4 casos específicos de sector_funcion (~1h)
  - Revisar embeddings actuales
  - Identificar por qué matchean incorrectamente
- [ ] Diseñar reglas para v8.4 (~2h)
  - Keywords VENTAS_B2B: "account executive", "hunter", "sales"
  - Keywords RRHH_ESCO: "agente de empleo", "reclutador"
  - Mapeo directo de títulos problemáticos
- [ ] Implementar `matching_rules_v84.py` (~2h)
  - Copiar v83 como base
  - Agregar nuevas familias/detectores
  - Agregar reglas never_confirm
- [ ] Validar con gold set (~30min)
  - Ejecutar test_gold_set_manual.py
  - Verificar métricas antes/después
- [ ] Validar sin regresiones (~1h)
  - Batch piloto de 100 ofertas
  - Revisar manualmente 10 casos aleatorios
- [ ] Documentar en CHANGELOG.md (~30min)
- [ ] Actualizar Linear con resultados (~15min)

### Notas técnicas
- El problema raíz es que embeddings de títulos en inglés ("Account Executive") están más cerca de ocupaciones de RRHH que de ventas en el espacio vectorial
- Posible approach: mapeo directo de títulos problemáticos antes del matching semántico
- Alternativa: boosting de score cuando oferta tiene keywords comerciales y ESCO tiene keywords ventas
- Priorizar precisión sobre recall: mejor no confirmar que confirmar mal
- Usar `never_confirm=True` para casos dudosos

### Referencias
- `docs/ARCHITECTURE.md#34-matching-esco`
- `docs/CHANGELOG.md#v83`
- Gold set casos: 1118027276, 1118028376, 1118028833, 1118028887

### Verificación final
```bash
# Antes de cerrar el issue:
python database/test_gold_set_manual.py

# Output esperado:
# PRECISION: >= 85.0%
# ERRORES sector_funcion: <= 1
```

---

## MOL-6: Expandir Gold Set a 50+ casos

### Contexto
Con solo 19 casos, el gold set actual no es estadísticamente representativo. Un cambio de 1 caso = 5.3pp de precisión, generando ruido en las métricas. Además, hay sectores sin cobertura (IT: 0 casos) que impiden detectar problemas en esas áreas.

Referencia: `docs/TICKETS_CONTEXT.md#mol-6`

### Objetivo
Expandir el gold set de 19 a 50+ casos con estratificación por sector, nivel jerárquico y tipo de contrato.

### Archivos involucrados
- `database/gold_set_manual_v2.json` - NUEVO archivo
- `database/gold_set_manual_v1.json` - Referencia (mantener como backup)
- `database/test_gold_set_manual.py` - Modificar (cargar v2)
- `database/extract_stratified_sample.py` - Usar para muestreo
- `docs/CHANGELOG.md` - Agregar entrada

### Criterios de Aceptación
- [ ] Gold set v2 tiene ≥50 casos
- [ ] Cobertura de sectores:
  - [ ] IT/Tech: ≥8 casos
  - [ ] Comercial/Ventas: ≥8 casos
  - [ ] Administrativo: ≥6 casos
  - [ ] Operarios/Producción: ≥6 casos
  - [ ] Salud: ≥5 casos
  - [ ] Servicios/Atención: ≥5 casos
  - [ ] Legal: ≥4 casos
  - [ ] Marketing: ≥4 casos
- [ ] Cobertura de niveles:
  - [ ] Junior/Trainee: ≥10 casos
  - [ ] Semi-senior: ≥15 casos
  - [ ] Senior/Gerencial: ≥10 casos
- [ ] Cada caso tiene:
  - [ ] `id_oferta`
  - [ ] `esco_ok` (boolean)
  - [ ] `tipo_error` (si esco_ok=false)
  - [ ] `esco_esperado_uri` (para calcular recall)
  - [ ] `esco_esperado_label`
  - [ ] `sector` (para estratificación)
  - [ ] `nivel` (para estratificación)
  - [ ] `comentario`
- [ ] Test funciona con v2: `python database/test_gold_set_manual.py`
- [ ] Documentado en CHANGELOG.md

### Subtareas
- [ ] Generar muestra estratificada (~1h)
  ```bash
  python database/extract_stratified_sample.py --output muestreo_v2.csv --n 80
  ```
- [ ] Configurar dashboard de validación (~30min)
  ```bash
  Rscript -e "shiny::runApp('Visual--/validacion_pipeline_app_v3.R', port=3853)"
  ```
- [ ] Validar casos IT/Tech: 10 casos (~1.5h)
- [ ] Validar casos Comercial/Ventas: 10 casos (~1.5h)
- [ ] Validar casos Administrativo: 8 casos (~1h)
- [ ] Validar casos Operarios: 8 casos (~1h)
- [ ] Validar casos Salud: 6 casos (~45min)
- [ ] Validar casos Servicios: 6 casos (~45min)
- [ ] Validar casos Legal: 5 casos (~30min)
- [ ] Validar casos Marketing: 5 casos (~30min)
- [ ] Compilar gold_set_manual_v2.json (~1h)
- [ ] Actualizar test_gold_set_manual.py (~30min)
- [ ] Documentar en CHANGELOG.md (~30min)

### Notas técnicas
- Priorizar casos "difíciles" (scores entre 0.50-0.70) sobre casos obvios
- Incluir casos bilingües (títulos en inglés)
- Incluir casos de pasantías/trainee (programa vs ocupación)
- Para `esco_esperado_uri`: buscar en https://esco.ec.europa.eu/
- Formato JSON:
```json
{
  "id_oferta": "1118027276",
  "esco_ok": false,
  "tipo_error": "sector_funcion",
  "esco_actual_uri": "http://data.europa.eu/esco/occupation/abc",
  "esco_esperado_uri": "http://data.europa.eu/esco/occupation/xyz",
  "esco_esperado_label": "Representante comercial",
  "sector": "comercial",
  "nivel": "semi-senior",
  "comentario": "Título en inglés confunde al modelo"
}
```

### Referencias
- `docs/ARCHITECTURE.md#7-testing-y-validación`
- `Visual--/validacion_pipeline_app_v3.R`
- ESCO Portal: https://esco.ec.europa.eu/

### Verificación final
```bash
# Verificar estructura del gold set:
python -c "
import json
with open('database/gold_set_manual_v2.json') as f:
    gs = json.load(f)
print(f'Total casos: {len(gs)}')
print(f'Campos requeridos: {list(gs[0].keys())}')
sectores = {}
for c in gs:
    s = c.get('sector', 'unknown')
    sectores[s] = sectores.get(s, 0) + 1
print(f'Por sector: {sectores}')
"
# Output esperado: Total casos: >= 50
```

---

## MOL-18: Automatizar scrapers faltantes

### Contexto
Solo Bumeran tiene scheduler automatizado (L/J 8am). Las otras 4 fuentes (ZonaJobs, Indeed, Computrabajo, LinkedIn) requieren ejecución manual, lo que significa que el sistema solo captura ~20% del mercado de forma consistente.

Referencia: `docs/ARCHITECTURE.md#21-scraping`

### Objetivo
Automatizar la ejecución de los 5 scrapers con manejo de errores, rate limiting y logging.

### Archivos involucrados
- `run_scheduler.py` - Modificar (agregar 4 fuentes)
- `01_sources/zonajobs/scrapers/zonajobs_scraper_final.py` - Verificar funcionamiento
- `01_sources/indeed/scrapers/indeed_scraper.py` - Verificar funcionamiento
- `01_sources/computrabajo/scrapers/computrabajo_scraper.py` - Verificar funcionamiento
- `01_sources/linkedin/scrapers/linkedin_scraper.py` - Verificar funcionamiento
- `config/scraper_config.yaml` - NUEVO (configuración centralizada)
- `logs/scraper_*.log` - Output

### Criterios de Aceptación
- [ ] Los 5 scrapers ejecutan automáticamente
- [ ] Cada scraper tiene:
  - [ ] Rate limiting configurado
  - [ ] Reintentos con backoff exponencial
  - [ ] Timeout máximo (30 min por fuente)
  - [ ] Logging a archivo dedicado
- [ ] Configuración en archivo YAML (no hardcodeada)
- [ ] Scheduler funciona en Windows (Task Scheduler) o cron
- [ ] Manejo de errores no detiene otros scrapers
- [ ] Resumen al final con ofertas capturadas por fuente
- [ ] Test: ejecución completa sin errores

### Subtareas
- [ ] Auditar estado de cada scraper (~2h)
  - [ ] ZonaJobs: verificar bypass Cloudflare funciona
  - [ ] Indeed: verificar rate limiting actual
  - [ ] Computrabajo: verificar HTML parsing
  - [ ] LinkedIn: verificar restricciones
- [ ] Crear config/scraper_config.yaml (~1h)
  ```yaml
  scrapers:
    bumeran:
      enabled: true
      rate_limit_seconds: 1.5
      timeout_minutes: 30
      retry_max: 3
    zonajobs:
      enabled: true
      rate_limit_seconds: 2.0
      # ...
  ```
- [ ] Modificar run_scheduler.py (~3h)
  - Cargar configuración desde YAML
  - Loop por scrapers habilitados
  - Try/except por scraper (no detener si uno falla)
  - Logging estructurado
- [ ] Implementar logging por fuente (~1h)
  - `logs/scraper_bumeran_2025-12-03.log`
  - `logs/scraper_zonajobs_2025-12-03.log`
- [ ] Crear resumen de ejecución (~1h)
  ```
  === RESUMEN SCRAPING 2025-12-03 ===
  Bumeran:     234 ofertas (OK)
  ZonaJobs:    156 ofertas (OK)
  Indeed:      ERROR - timeout
  Computrabajo: 89 ofertas (OK)
  LinkedIn:    SKIPPED - disabled
  Total:       479 ofertas
  ```
- [ ] Configurar Task Scheduler / cron (~1h)
- [ ] Test completo (~1h)
- [ ] Documentar en CHANGELOG.md (~30min)

### Notas técnicas
- ZonaJobs requiere Playwright para bypass Cloudflare
- Indeed tiene rate limiting agresivo: usar delays de 3-5s
- LinkedIn tiene restricciones legales: considerar deshabilitar o usar solo API oficial
- Usar `tenacity` para reintentos con backoff
- Logs deben rotar (máximo 30 días)

### Referencias
- `docs/ARCHITECTURE.md#21-scraping`
- `01_sources/bumeran/scrapers/bumeran_scraper.py` (ejemplo funcional)

### Verificación final
```bash
# Test de ejecución completa:
python run_scheduler.py --test-mode --limit 10

# Verificar logs generados:
ls -la logs/scraper_*.log

# Verificar ofertas capturadas:
sqlite3 database/bumeran_scraping.db "SELECT source, COUNT(*) FROM ofertas WHERE fecha_scraping = date('now') GROUP BY source"
```

---

## MOL-26: Backup automático de SQLite

### Contexto
Toda la data del proyecto está en un único archivo (`bumeran_scraping.db` de ~14MB). Un `rm` accidental, corrupción de disco o error de script podría eliminar meses de trabajo. Actualmente no hay backups automatizados.

### Objetivo
Implementar backup automático diario de la base de datos con retención de 30 días.

### Archivos involucrados
- `scripts/backup_database.py` - NUEVO archivo
- `backups/` - NUEVO directorio
- `run_scheduler.py` - Modificar (agregar paso de backup)
- `.gitignore` - Agregar exclusión de backups

### Criterios de Aceptación
- [ ] Backup diario automático después del scraping
- [ ] Formato: `backups/bumeran_scraping_YYYY-MM-DD.db.gz`
- [ ] Compresión gzip (~3MB comprimido)
- [ ] Retención: últimos 30 backups
- [ ] Limpieza automática de backups antiguos
- [ ] Verificación de integridad post-backup
- [ ] Log de backups realizados
- [ ] Script de restore documentado

### Subtareas
- [ ] Crear directorio `backups/` (~5min)
- [ ] Implementar `scripts/backup_database.py` (~2h)
  ```python
  # Funcionalidades:
  # - Copiar DB a backups/ con timestamp
  # - Comprimir con gzip
  # - Verificar integridad (PRAGMA integrity_check)
  # - Limpiar backups > 30 días
  ```
- [ ] Integrar en run_scheduler.py (~30min)
- [ ] Agregar a .gitignore (~5min)
  ```
  backups/*.db
  backups/*.gz
  ```
- [ ] Documentar proceso de restore (~30min)
- [ ] Test de backup y restore (~1h)
- [ ] Documentar en CHANGELOG.md (~15min)

### Notas técnicas
- SQLite permite copiar archivo mientras está en uso (WAL mode)
- Verificar integridad antes de comprimir: `PRAGMA integrity_check`
- Restore: `gunzip backup.db.gz && cp backup.db bumeran_scraping.db`
- Considerar backup a ubicación externa (Google Drive, S3) como mejora futura

### Referencias
- SQLite backup: https://www.sqlite.org/backup.html

### Verificación final
```bash
# Ejecutar backup manual:
python scripts/backup_database.py

# Verificar backup creado:
ls -lh backups/

# Verificar integridad del backup:
gunzip -k backups/bumeran_scraping_2025-12-03.db.gz
sqlite3 backups/bumeran_scraping_2025-12-03.db "PRAGMA integrity_check"
# Output esperado: ok
```

---

## MOL-23: Versionado de datos

### Contexto
Actualmente solo se versiona código (git), pero no datasets. Esto causa:
- No se puede reproducir métricas históricas
- Si ESCO se actualiza, no hay baseline de comparación
- Gold sets cambian sin tracking

Referencia: Principios FAIR, mejores prácticas MLOps

### Objetivo
Implementar versionado de datasets críticos (gold sets, snapshots de BD, configuraciones).

### Archivos involucrados
- `data/gold_sets/` - NUEVO directorio
- `data/snapshots/` - NUEVO directorio
- `data/LATEST.json` - NUEVO (punteros a versiones activas)
- `scripts/version_data.py` - NUEVO script

### Criterios de Aceptación
- [ ] Estructura de directorios creada
- [ ] Gold sets versionados: `data/gold_sets/gold_set_v1_2025-11-28.json`
- [ ] Snapshots de BD: `data/snapshots/ofertas_2025-12-03.csv.gz`
- [ ] Archivo LATEST.json apunta a versiones activas
- [ ] Script para crear nueva versión de gold set
- [ ] Script para crear snapshot
- [ ] Documentación de uso

### Subtareas
- [ ] Crear estructura de directorios (~15min)
  ```
  data/
  ├── gold_sets/
  │   ├── gold_set_v1_2025-11-28.json
  │   └── LATEST -> gold_set_v1_2025-11-28.json
  ├── snapshots/
  │   └── ofertas_2025-12-03.csv.gz
  └── LATEST.json
  ```
- [ ] Migrar gold set actual (~30min)
- [ ] Implementar version_data.py (~2h)
  - `--new-gold-set`: crea nueva versión de gold set
  - `--snapshot`: crea snapshot de ofertas
  - `--list`: lista versiones disponibles
- [ ] Actualizar test_gold_set_manual.py para usar LATEST (~30min)
- [ ] Documentar en README (~30min)
- [ ] Documentar en CHANGELOG.md (~15min)

### Notas técnicas
- No usar DVC por complejidad, solución simple con archivos
- LATEST.json estructura:
  ```json
  {
    "gold_set": "gold_sets/gold_set_v2_2025-12-15.json",
    "ofertas_snapshot": "snapshots/ofertas_2025-12-03.csv.gz",
    "esco_version": "1.1.2"
  }
  ```
- Snapshots solo de ofertas (la BD completa es muy grande)

### Referencias
- FAIR Principles: https://www.go-fair.org/fair-principles/
- `docs/ARCHITECTURE.md`

### Verificación final
```bash
# Crear snapshot:
python scripts/version_data.py --snapshot

# Listar versiones:
python scripts/version_data.py --list

# Verificar LATEST:
cat data/LATEST.json
```

---

# 🟡 MEDIA PRIORIDAD

---

## MOL-7: Métricas Recall y F1

### Contexto
Actualmente solo medimos precisión (% de matches correctos). Un sistema podría tener 100% precisión si solo confirma 10 ofertas obvias. Necesitamos recall para saber qué % del universo estamos clasificando correctamente.

Referencia: `docs/TICKETS_CONTEXT.md#mol-7`

### Objetivo
Agregar métricas de Recall, F1-Score y Top-3 Accuracy al benchmark.

### Archivos involucrados
- `database/test_gold_set_manual.py` - Modificar
- `database/gold_set_manual_v2.json` - Requiere campo `esco_esperado_uri`

### Criterios de Aceptación
- [ ] Benchmark reporta Precision, Recall, F1-Score
- [ ] Benchmark reporta Top-3 Accuracy
- [ ] Gold set tiene `esco_esperado_uri` para cada caso
- [ ] Output formateado:
  ```
  === MÉTRICAS COMPLETAS ===
  Precision:   80.0%
  Recall:      75.0%
  F1-Score:    77.4%
  Top-3 Acc:   92.0%
  ```
- [ ] Documentado en CHANGELOG.md

### Subtareas
- [ ] Agregar `esco_esperado_uri` a gold set (~requiere MOL-6)
- [ ] Implementar cálculo de Recall (~1h)
- [ ] Implementar cálculo de F1 (~30min)
- [ ] Implementar Top-3 Accuracy (~1h)
- [ ] Formatear output (~30min)
- [ ] Documentar (~30min)

### Notas técnicas
- Recall = matches_correctos / total_con_esco_esperado
- Precision = matches_correctos / total_confirmados
- F1 = 2 * (P * R) / (P + R)
- Top-3: verificar si `esco_esperado` está en los top 3 candidatos

### Dependencias
- Requiere: MOL-6 (gold set expandido con esco_esperado_uri)

### Verificación final
```bash
python database/test_gold_set_manual.py
# Output debe incluir: Precision, Recall, F1, Top-3
```

---

## MOL-8: Resolver casos bilingües

### Contexto
Títulos en inglés no matchean bien con ocupaciones ESCO en español. Los embeddings de BGE-M3 son multilingües pero la distancia semántica inglés↔español a veces es mayor que la distancia a ocupaciones incorrectas.

### Objetivo
Mejorar matching de títulos en inglés mediante traducción o diccionario de equivalencias.

### Archivos involucrados
- `database/title_translations.json` - NUEVO diccionario
- `database/match_ofertas_multicriteria.py` - Modificar preproceso

### Criterios de Aceptación
- [ ] Diccionario con ≥50 traducciones comunes
- [ ] Preproceso traduce título antes de embedding
- [ ] "Account Executive" matchea a ventas
- [ ] "Software Developer" matchea a desarrollador
- [ ] "Data Analyst" matchea a analista de datos
- [ ] Sin regresiones en títulos en español
- [ ] Documentado en CHANGELOG.md

### Subtareas
- [ ] Crear title_translations.json (~2h)
- [ ] Implementar preproceso de traducción (~1h)
- [ ] Validar con casos bilingües del gold set (~1h)
- [ ] Documentar (~30min)

### Notas técnicas
- Alternativa a diccionario: usar API de traducción (pero agrega latencia)
- Priorizar términos de IT, ventas, marketing (más comunes en inglés)
- Formato diccionario:
  ```json
  {
    "account executive": "ejecutivo de cuentas",
    "software developer": "desarrollador de software",
    "data analyst": "analista de datos"
  }
  ```

### Verificación final
```bash
# Test manual:
python -c "
from database.match_ofertas_multicriteria import preprocesar_titulo
print(preprocesar_titulo('Account Executive'))
# Output esperado: 'ejecutivo de cuentas'
"
```

---

## MOL-19: Pipeline automático post-scraping

### Contexto
Después del scraping hay que ejecutar manualmente: consolidación → NLP → matching. Esto genera retrasos y posibles olvidos.

### Objetivo
Automatizar el pipeline completo post-scraping con un solo comando.

### Archivos involucrados
- `scripts/run_full_pipeline.py` - NUEVO script
- `run_scheduler.py` - Modificar (invocar pipeline)

### Criterios de Aceptación
- [ ] Un comando ejecuta todo: `python scripts/run_full_pipeline.py`
- [ ] Orden correcto: consolidar → NLP → matching
- [ ] Si un paso falla, no ejecuta los siguientes
- [ ] Log de cada paso con tiempo de ejecución
- [ ] Notificación al terminar (ver MOL-14)
- [ ] Documentado

### Subtareas
- [ ] Crear run_full_pipeline.py (~2h)
- [ ] Integrar con run_scheduler.py (~1h)
- [ ] Implementar logging por paso (~1h)
- [ ] Test completo (~1h)
- [ ] Documentar (~30min)

### Dependencias
- Requiere: MOL-18 (scrapers automatizados)

### Verificación final
```bash
python scripts/run_full_pipeline.py --dry-run
# Output: muestra pasos que ejecutaría sin ejecutarlos
```

---

## MOL-14: Alertas email/Slack

### Contexto
`alert_manager.py` existe pero tiene `email_enabled=False`. No hay notificaciones cuando algo falla o cuando el pipeline termina.

### Objetivo
Habilitar alertas por email o Slack para eventos críticos.

### Archivos involucrados
- `database/alert_manager.py` - Modificar
- `config/alerts_config.yaml` - NUEVO

### Criterios de Aceptación
- [ ] Alerta cuando scraping falla
- [ ] Alerta cuando ofertas_nuevas < threshold
- [ ] Alerta cuando pipeline completo termina
- [ ] Resumen diario con métricas
- [ ] Configuración en YAML (no hardcodeada)
- [ ] Al menos un canal funcional (email o Slack)

### Subtareas
- [ ] Definir eventos que disparan alertas (~30min)
- [ ] Crear alerts_config.yaml (~30min)
- [ ] Implementar envío de email (~2h)
- [ ] Implementar webhook de Slack (alternativo) (~2h)
- [ ] Integrar con run_scheduler.py (~1h)
- [ ] Test de alertas (~30min)
- [ ] Documentar (~30min)

### Notas técnicas
- Email: usar smtplib con Gmail o SendGrid
- Slack: webhook simple, no requiere bot
- Considerar rate limiting de alertas (máximo 3/hora)

### Verificación final
```bash
# Test de alerta:
python -c "from database.alert_manager import send_alert; send_alert('Test', 'Mensaje de prueba')"
```

---

## MOL-16: Fix shinyTree

### Contexto
El componente shinyTree para navegar la jerarquía ESCO está deshabilitado por un bug de input/output binding.

### Objetivo
Rehabilitar el árbol ESCO navegable en el dashboard.

### Archivos involucrados
- `Visual--/app.R` - Modificar
- `Visual--/www/custom.js` - Posible fix de bindings

### Criterios de Aceptación
- [ ] Árbol ESCO visible y navegable
- [ ] Al seleccionar ocupación, filtran ofertas
- [ ] Sin errores en consola R
- [ ] Sin errores en consola browser

### Subtareas
- [ ] Debuggear error actual (~1h)
- [ ] Implementar fix (~2h)
- [ ] Test en diferentes browsers (~30min)
- [ ] Documentar (~15min)

### Notas técnicas
- Error conocido: "Error in shinyTree: input binding not found"
- Posible causa: versión de shinyTree incompatible
- Alternativa: usar otro widget de árbol (jsTree, collapsibleTree)

### Verificación final
```r
# En R:
shiny::runApp('Visual--/app.R', port=3853)
# Verificar que el árbol carga y es interactivo
```

---

## MOL-24: Entity Resolution cross-source

### Contexto
Cuando se automaticen los 5 scrapers, la misma oferta puede aparecer en múltiples portales. Actualmente no hay deduplicación cross-source.

### Objetivo
Implementar detección de duplicados entre diferentes fuentes.

### Archivos involucrados
- `02_consolidation/scripts/deduplicacion_cross_source.py` - NUEVO
- `database/bumeran_scraping.db` - Agregar tabla `ofertas_canonical`

### Criterios de Aceptación
- [ ] Detección de duplicados basada en (titulo + empresa + ubicacion)
- [ ] Hash de deduplicación: `canonical_id`
- [ ] Tabla `ofertas_canonical` con oferta representativa
- [ ] Métricas: % de duplicados detectados
- [ ] Sin falsos positivos (ofertas diferentes marcadas como iguales)

### Subtareas
- [ ] Diseñar algoritmo de hash (~1h)
- [ ] Crear tabla ofertas_canonical (~30min)
- [ ] Implementar script (~3h)
- [ ] Validar con muestra manual (~1h)
- [ ] Documentar (~30min)

### Notas técnicas
- Hash: normalizar título (lowercase, sin puntuación) + normalizar empresa + código provincia
- Usar Levenshtein para fuzzy matching de títulos
- Threshold de similaridad: >0.85

### Dependencias
- Requiere: MOL-18 (tener datos de múltiples fuentes)

### Verificación final
```sql
-- Verificar duplicados detectados:
SELECT canonical_id, COUNT(*) as fuentes
FROM ofertas
WHERE canonical_id IS NOT NULL
GROUP BY canonical_id
HAVING COUNT(*) > 1
```

---

## MOL-25: Drift Detection

### Contexto
Si un portal cambia su API/HTML, el scraper puede fallar silenciosamente (capturar 0 ofertas o datos corruptos). Actualmente no hay monitoreo de esto.

### Objetivo
Implementar detección de anomalías en el proceso de scraping.

### Archivos involucrados
- `scripts/drift_detector.py` - NUEVO
- `config/drift_thresholds.yaml` - NUEVO

### Criterios de Aceptación
- [ ] Alerta si ofertas_nuevas < threshold diario
- [ ] Alerta si campos obligatorios vienen vacíos (>10%)
- [ ] Alerta si estructura de respuesta cambia
- [ ] Health check validable manualmente
- [ ] Integrado con sistema de alertas (MOL-14)

### Subtareas
- [ ] Definir métricas de drift (~1h)
- [ ] Implementar drift_detector.py (~2h)
- [ ] Definir thresholds por fuente (~1h)
- [ ] Integrar con alertas (~1h)
- [ ] Documentar (~30min)

### Notas técnicas
- Threshold ofertas: Bumeran >50/día, ZonaJobs >30/día
- Campos obligatorios: titulo, empresa, descripcion
- Guardar historial de métricas para detectar tendencias

### Verificación final
```bash
python scripts/drift_detector.py --check-all
# Output: OK/WARNING/CRITICAL por fuente
```

---

# ⚪ BAJA PRIORIDAD

---

## MOL-9: CI/CD GitHub Actions

### Contexto
No hay validación automática de código. Un push puede romper el matching sin que nadie se entere hasta ejecutar manualmente.

### Objetivo
Configurar GitHub Actions para validar automáticamente en cada push.

### Archivos involucrados
- `.github/workflows/test.yml` - NUEVO

### Criterios de Aceptación
- [ ] Workflow ejecuta en cada push a main
- [ ] Corre test_gold_set_manual.py
- [ ] Falla si precision < 75%
- [ ] Badge de estado en README

### Subtareas
- [ ] Crear workflow YAML (~1h)
- [ ] Configurar secrets si necesario (~30min)
- [ ] Agregar badge a README (~15min)
- [ ] Test del workflow (~30min)

### Dependencias
- Requiere: MOL-5 estable (precisión consistente)

### Verificación final
```bash
# Push a main y verificar que Action corre
git push origin main
# Verificar en GitHub Actions tab
```

---

## MOL-10: Regex abreviaciones argentinas

### Contexto
El regex v4 no detecta abreviaciones comunes argentinas: Adm., Gte., Coord., Jfe., Aux.

### Objetivo
Agregar patrones para abreviaciones argentinas en regex v4.1.

### Archivos involucrados
- `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py` - Modificar (crear v4.1)

### Criterios de Aceptación
- [ ] Detecta: Adm., Gte., Coord., Jfe., Aux., Ing., Lic., Dr.
- [ ] Expande a forma completa
- [ ] Sin falsos positivos
- [ ] Cobertura regex aumenta (60-70% → 70-75%)

### Subtareas
- [ ] Listar abreviaciones comunes (~30min)
- [ ] Implementar patrones (~1h)
- [ ] Test con muestra (~1h)
- [ ] Documentar (~30min)

### Verificación final
```python
from regex_patterns_v4 import extraer_nivel
assert extraer_nivel("Gte. Comercial") == "gerente"
```

---

## MOL-11: Niveles jerárquicos

### Contexto
La detección de niveles (Junior/Senior/Manager) tiene baja cobertura. Muchas ofertas no explicitan el nivel.

### Objetivo
Mejorar inferencia de nivel jerárquico desde contexto.

### Archivos involucrados
- `02.5_nlp_extraction/scripts/patterns/regex_patterns_v4.py` - Modificar
- `database/matching_rules_v84.py` - Ajustar penalizaciones

### Criterios de Aceptación
- [ ] Detecta nivel desde años de experiencia requeridos
- [ ] Detecta nivel desde salario (si disponible)
- [ ] Cobertura de nivel aumenta

### Subtareas
- [ ] Mapear experiencia → nivel (~1h)
- [ ] Implementar inferencia (~2h)
- [ ] Validar (~1h)
- [ ] Documentar (~30min)

---

## MOL-12: Consolidar NLP v6+v7

### Contexto
Existen múltiples versiones de scripts NLP. Dificulta mantenimiento.

### Objetivo
Unificar en un solo archivo con flags de configuración.

### Archivos involucrados
- `database/process_nlp_unified.py` - NUEVO
- `database/process_nlp_from_db_v6.py` - Deprecar
- `database/process_nlp_from_db_v7.py` - Deprecar

### Criterios de Aceptación
- [ ] Un solo script: process_nlp_unified.py
- [ ] Flag --version para seleccionar comportamiento
- [ ] Versiones antiguas movidas a archive/
- [ ] Sin regresiones

### Subtareas
- [ ] Analizar diferencias v6 vs v7 (~1h)
- [ ] Implementar script unificado (~3h)
- [ ] Test de equivalencia (~1h)
- [ ] Deprecar versiones antiguas (~30min)

---

## MOL-13: Panel administración

### Contexto
No existe panel de administración. Todo es CLI.

### Objetivo
Crear panel web para monitorear y operar el sistema.

### Archivos involucrados
- `admin/admin_panel.py` - NUEVO (Dash app, puerto 8053)

### Criterios de Aceptación
- [ ] Ver estado de scrapers
- [ ] Ver estado de pipeline NLP/Matching
- [ ] Ejecutar tareas manualmente
- [ ] Ver logs recientes
- [ ] Ver métricas gold set

### Dependencias
- Requiere: MOL-20 (logs centralizados)

---

## MOL-15: Limpieza JSONs

### Contexto
10,800 archivos JSON en 01_sources/*/data/raw/, muchos duplicados.

### Objetivo
Limpiar JSONs antiguos y consolidar.

### Criterios de Aceptación
- [ ] Eliminar JSONs > 30 días ya procesados
- [ ] Liberar >1GB de espacio
- [ ] Script de limpieza automatizable

---

## MOL-17: Auth shinymanager

### Contexto
Autenticación deshabilitada para debug. Dashboard públicamente accesible.

### Objetivo
Rehabilitar autenticación con shinymanager.

### Dependencias
- Requiere: MOL-16 (estabilidad del dashboard)

---

## MOL-20: Centralizar logs

### Contexto
Logs distribuidos en múltiples carpetas.

### Objetivo
Todos los logs en `logs/` con formato unificado.

### Criterios de Aceptación
- [ ] Directorio único: logs/
- [ ] Rotación automática (7 días)
- [ ] Formato: `[timestamp] [nivel] [módulo] mensaje`

---

## MOL-21: Deprecar dashboards

### Contexto
Múltiples versiones de dashboards obsoletos.

### Objetivo
Mantener solo 2 dashboards activos, mover resto a archive/.

---

## MOL-22: Documentar APIs

### Contexto
APIs de scrapers descubiertas por reverse engineering, sin documentación.

### Objetivo
Documentar endpoints, headers, payloads, rate limits.

### Archivos involucrados
- `docs/SCRAPER_APIS.md` - NUEVO

---

# Apéndice: Grafo de Dependencias

```
                         ┌─────────┐
                         │  MOL-6  │ Gold Set 50+
                         └────┬────┘
                              │ mejora
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      ┌─────────┐       ┌─────────┐       ┌─────────┐
      │  MOL-5  │       │  MOL-7  │       │  MOL-8  │
      │sector_fn│       │ Recall  │       │bilingüe │
      └────┬────┘       └─────────┘       └─────────┘
           │ estabiliza
           ▼
      ┌─────────┐
      │  MOL-9  │ CI/CD
      └─────────┘

      ┌─────────┐       ┌─────────┐
      │ MOL-18  │ ────► │ MOL-19  │
      │scrapers │       │pipeline │
      └────┬────┘       └────┬────┘
           │                 │
           ▼                 ▼
      ┌─────────┐       ┌─────────┐
      │ MOL-24  │       │ MOL-14  │
      │ dedup   │       │alertas  │
      └─────────┘       └─────────┘

      ┌─────────┐       ┌─────────┐
      │ MOL-20  │ ────► │ MOL-13  │
      │  logs   │       │  admin  │
      └─────────┘       └─────────┘

      ┌─────────┐       ┌─────────┐
      │ MOL-16  │ ────► │ MOL-17  │
      │shinyTree│       │  auth   │
      └─────────┘       └─────────┘
```

---

> **Generado:** 2025-12-03
> **Formato:** Basado en CCT-RAG issue template
