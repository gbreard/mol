# ✅ CHECKLIST FASE 0: PREPARACIÓN Y CONFIGURACIÓN
**Duración:** 2 semanas
**Objetivo:** Preparar entorno y herramientas sin afectar producción

---

## 📅 SEMANA 1: INFRAESTRUCTURA

### 1. Setup de Entorno de Desarrollo

#### 1.1 Base de datos de desarrollo
- [ ] **Copiar BD actual a BD de desarrollo**
  ```bash
  # Ubicación actual
  cp D:/OEDE/Webscrapping/ofertas_laborales.db D:/OEDE/Webscrapping/ofertas_laborales_DEV.db

  # Verificar copia
  ls -lh D:/OEDE/Webscrapping/*.db
  ```
  - ✅ Criterio: Archivo `ofertas_laborales_DEV.db` existe (~50 MB)
  - ✅ Criterio: Tiene las mismas tablas que producción

- [ ] **Verificar integridad de BD dev**
  ```bash
  sqlite3 D:/OEDE/Webscrapping/ofertas_laborales_DEV.db "PRAGMA integrity_check;"
  ```
  - ✅ Criterio: Retorna "ok"

#### 1.2 Configurar servidores de testing
- [ ] **Dashboard Shiny en puerto 3841**
  - Modificar `app.R` o `app_minimal_working.R`
  - Cambiar puerto de 3840 a 3841
  - Probar: `http://localhost:3841`
  - ✅ Criterio: Dashboard dev carga sin errores

- [ ] **Dashboard Plotly en puerto 8053** (si existe)
  - Modificar `dashboard_scraping_v4.py`
  - Cambiar puerto de 8052 a 8053
  - Probar: `http://localhost:8053`
  - ✅ Criterio: Dashboard técnico dev carga

#### 1.3 Instalar/actualizar dependencias
- [ ] **Dependencias R**
  ```r
  # Ejecutar en RStudio
  install.packages(c("shiny", "shinydashboard", "DT", "ggplot2",
                     "dplyr", "tidyr", "plotly", "shinyWidgets",
                     "shinyTree"))
  ```
  - ✅ Criterio: Todos los paquetes instalan sin error

- [ ] **Dependencias Python**
  ```bash
  pip install --upgrade pandas sqlite3 plotly dash requests beautifulsoup4 ollama
  ```
  - ✅ Criterio: Todos instalan sin conflictos

---

### 2. Control de Versiones (Git)

#### 2.1 Inicializar repositorio Git
- [ ] **Verificar si Git ya existe**
  ```bash
  cd D:/OEDE/Webscrapping
  git status
  ```
  - Si existe: ✅ Saltar a 2.2
  - Si NO existe: Continuar abajo

- [ ] **Inicializar Git** (solo si no existe)
  ```bash
  cd D:/OEDE/Webscrapping
  git init
  ```
  - ✅ Criterio: Mensaje "Initialized empty Git repository"

- [ ] **Crear .gitignore**
  ```bash
  # Crear archivo .gitignore
  cat > .gitignore << 'EOF'
  # Bases de datos
  *.db
  *.db-journal
  *.sqlite

  # Python
  __pycache__/
  *.pyc
  *.pyo
  venv/
  .env

  # R
  .Rproj.user/
  .Rhistory
  .RData
  .Ruserdata
  *.Rproj

  # Logs
  *.log
  logs/

  # Archivos temporales
  *.tmp
  *.bak
  *~

  # Datos grandes
  *.csv
  *.parquet
  *.rds

  # Credenciales
  credentials.json
  .secrets/
  EOF
  ```
  - ✅ Criterio: Archivo `.gitignore` creado

#### 2.2 Crear estructura de ramas
- [ ] **Commit inicial**
  ```bash
  git add .
  git commit -m "Initial commit: Sistema MOL v1.0 actual

  Estado actual antes de comenzar rediseño v2.0.
  Incluye dashboards, scripts de scraping y BD.
  "
  ```
  - ✅ Criterio: Commit exitoso con ~50-100 archivos

- [ ] **Crear rama development**
  ```bash
  git branch development
  git checkout development
  ```
  - ✅ Criterio: Ahora estás en rama `development`

- [ ] **Crear rama para fase 1**
  ```bash
  git checkout -b feature/fase1-fundamentos-datos
  ```
  - ✅ Criterio: Rama `feature/fase1-fundamentos-datos` creada

#### 2.3 Configurar Git
- [ ] **Configurar usuario**
  ```bash
  git config user.name "Equipo OEDE"
  git config user.email "oede@trabajo.gob.ar"
  ```

- [ ] **Verificar configuración**
  ```bash
  git config --list | grep user
  ```
  - ✅ Criterio: Muestra nombre y email correctos

---

### 3. Backup Completo

#### 3.1 Backup de Base de Datos
- [ ] **Crear carpeta de backups**
  ```bash
  mkdir -p D:/OEDE/Webscrapping/backups/fase0_$(date +%Y%m%d)
  ```

- [ ] **Backup de BD principal**
  ```bash
  cp D:/OEDE/Webscrapping/ofertas_laborales.db \
     D:/OEDE/Webscrapping/backups/fase0_$(date +%Y%m%d)/ofertas_laborales_backup.db
  ```
  - ✅ Criterio: Archivo copiado exitosamente

- [ ] **Validar backup**
  ```bash
  sqlite3 D:/OEDE/Webscrapping/backups/fase0_*/ofertas_laborales_backup.db "SELECT COUNT(*) FROM ofertas_raw;"
  ```
  - ✅ Criterio: Retorna número de ofertas (ej: 6521)

#### 3.2 Backup de código
- [ ] **Comprimir código actual**
  ```bash
  cd D:/OEDE/Webscrapping
  tar -czf backups/fase0_$(date +%Y%m%d)/codigo_v1.0.tar.gz \
    --exclude='*.db' \
    --exclude='*.csv' \
    --exclude='backups' \
    .
  ```
  - ✅ Criterio: Archivo `.tar.gz` creado (~10-20 MB)

#### 3.3 Backup de dashboards
- [ ] **Capturar screenshots de dashboards actuales**
  - Abrir dashboard Shiny (localhost:3840)
  - Tomar screenshots de cada tab (6 tabs)
  - Guardar en: `D:/OEDE/Webscrapping/docs/screenshots_v1.0/`
  - ✅ Criterio: 6 imágenes guardadas

- [ ] **Exportar dashboard actual**
  - Si está en shinyapps.io: Descargar versión actual
  - Guardar en backups
  - ✅ Criterio: Código del dashboard publicado respaldado

---

## 📅 SEMANA 2: DOCUMENTACIÓN TÉCNICA

### 4. Mapeo de Arquitectura Actual

#### 4.1 Inventario de scripts
- [ ] **Listar todos los scripts Python**
  ```bash
  cd D:/OEDE/Webscrapping
  find . -name "*.py" -type f > docs/inventario_scripts_python.txt
  ```

- [ ] **Listar todos los scripts R**
  ```bash
  find . -name "*.R" -type f > docs/inventario_scripts_R.txt
  ```

- [ ] **Documentar propósito de cada script**
  - Crear archivo: `docs/INVENTARIO_SCRIPTS.md`
  - Para cada script principal, documentar:
    - Nombre del archivo
    - Qué hace (1 frase)
    - Inputs (archivos, BD, APIs)
    - Outputs (archivos, BD, dashboards)
    - Frecuencia de ejecución
  - ✅ Criterio: Al menos 10 scripts documentados

#### 4.2 Diagrama de flujo del sistema
- [ ] **Crear diagrama de arquitectura actual**
  - Herramienta: draw.io, Mermaid, o papel+foto
  - Incluir:
    - 5 portales de scraping
    - Scripts de recolección
    - Base de datos SQLite
    - Scripts de NLP
    - Scripts de ESCO
    - 2 dashboards (Shiny + Plotly)
  - Guardar en: `docs/arquitectura_v1.0.png`
  - ✅ Criterio: Diagrama muestra flujo completo

#### 4.3 Inventario de tablas de BD
- [ ] **Listar todas las tablas**
  ```bash
  sqlite3 D:/OEDE/Webscrapping/ofertas_laborales.db ".tables" > docs/tablas_bd.txt
  ```

- [ ] **Documentar schema de tablas principales**
  ```bash
  sqlite3 D:/OEDE/Webscrapping/ofertas_laborales.db ".schema ofertas_raw" > docs/schema_bd.sql
  sqlite3 D:/OEDE/Webscrapping/ofertas_laborales.db ".schema ofertas_nlp_v5" >> docs/schema_bd.sql
  sqlite3 D:/OEDE/Webscrapping/ofertas_laborales.db ".schema esco_occupations" >> docs/schema_bd.sql
  sqlite3 D:/OEDE/Webscrapping/ofertas_laborales.db ".schema esco_skills" >> docs/schema_bd.sql
  ```
  - ✅ Criterio: Archivo `schema_bd.sql` contiene schema de 4+ tablas

---

### 5. Plan de Testing

#### 5.1 Definir casos de prueba críticos
- [ ] **Crear documento de test cases**
  - Archivo: `docs/PLAN_DE_TESTING.md`
  - Incluir:
    - **Test Case 1:** Scraping de Bumeran (ejecutar y validar >100 ofertas)
    - **Test Case 2:** NLP procesa oferta completa (validar 17 campos)
    - **Test Case 3:** ESCO clasifica oferta (validar ocupación asignada)
    - **Test Case 4:** Dashboard carga sin errores (validar 6 tabs)
    - **Test Case 5:** Filtros de dashboard funcionan (cambiar filtro, ver resultado)
  - ✅ Criterio: 5 test cases documentados con pasos claros

#### 5.2 Preparar datos de prueba
- [ ] **Crear ofertas sintéticas para testing**
  - Script: `scripts/generar_ofertas_test.py`
  - Generar 100 ofertas con variedad:
    - 30 ofertas IT (Python, Java, JavaScript, etc.)
    - 20 ofertas Admin (contador, administrativo, etc.)
    - 20 ofertas Ventas
    - 30 ofertas mixtas
  - Guardar en: `data_test/ofertas_sinteticas.csv`
  - ✅ Criterio: 100 ofertas generadas con campos completos

- [ ] **Insertar ofertas de prueba en BD dev**
  ```python
  # Script para cargar ofertas de prueba
  import pandas as pd
  import sqlite3

  df = pd.read_csv('data_test/ofertas_sinteticas.csv')
  conn = sqlite3.connect('ofertas_laborales_DEV.db')
  df.to_sql('ofertas_raw', conn, if_exists='append', index=False)
  conn.close()
  ```
  - ✅ Criterio: 100 ofertas insertadas en `ofertas_laborales_DEV.db`

#### 5.3 Establecer métricas de éxito
- [ ] **Definir KPIs por fase**
  - Crear archivo: `docs/METRICAS_EXITO.md`
  - Para cada fase (1-5), definir:
    - Métrica cuantitativa (ej: "NLP procesa 100 ofertas en <30 min")
    - Cómo se mide (ej: "Ejecutar script y cronometrar")
    - Threshold de aprobación (ej: ">90% accuracy")
  - ✅ Criterio: 15 métricas documentadas (3 por fase × 5 fases)

---

### 6. Comunicación al Equipo

#### 6.1 Reunión kickoff
- [ ] **Preparar presentación kickoff**
  - Slides (10-15 diapositivas):
    1. Situación actual del MOL
    2. Problemas identificados
    3. Objetivos del rediseño v2.0
    4. Roadmap de 5 fases (6 meses)
    5. Recursos necesarios
    6. Roles y responsabilidades
    7. Próximos pasos (Fase 1)
  - Guardar en: `docs/Kickoff_MOL_v2.0.pdf`
  - ✅ Criterio: Presentación lista para compartir

- [ ] **Agendar reunión kickoff**
  - Fecha sugerida: Fin de Semana 2 (viernes tarde)
  - Duración: 1 hora
  - Participantes:
    - Director OEDE
    - Equipo técnico (devs, analistas)
    - Stakeholders clave
  - ✅ Criterio: Invitación enviada con 1 semana anticipación

- [ ] **Realizar reunión kickoff**
  - Presentar roadmap
  - Responder preguntas
  - Confirmar aprobación para continuar
  - ✅ Criterio: Acta de reunión con aprobación firmada

#### 6.2 Asignar roles y responsabilidades
- [ ] **Crear matriz RACI**
  - Archivo: `docs/MATRIZ_RACI.md`
  - Para cada fase, definir quién es:
    - **R**esponsible (hace la tarea)
    - **A**ccountable (aprueba)
    - **C**onsulted (se consulta)
    - **I**nformed (se informa)
  - ✅ Criterio: Matriz completa para 5 fases

- [ ] **Asignar tareas de Fase 1**
  - Crear issues en Git (si aplica) o documento
  - Asignar cada tarea a una persona
  - Establecer fechas de entrega
  - ✅ Criterio: Todas las tareas de Fase 1 asignadas

---

## 📊 CRITERIOS DE APROBACIÓN DE FASE 0

Para pasar a FASE 1, verificar:

### ✅ Infraestructura
- [ ] BD de desarrollo funcional y con datos
- [ ] Servidores de testing en puertos alternativos (3841, 8053)
- [ ] Dependencias R y Python instaladas

### ✅ Control de versiones
- [ ] Git inicializado con commit inicial
- [ ] Ramas `main`, `development`, `feature/fase1-*` creadas
- [ ] `.gitignore` configurado correctamente

### ✅ Backups
- [ ] BD respaldada y validada
- [ ] Código comprimido en `.tar.gz`
- [ ] Screenshots de dashboards v1.0

### ✅ Documentación
- [ ] Inventario de scripts completo
- [ ] Diagrama de arquitectura actual
- [ ] Schema de BD documentado
- [ ] Plan de testing definido

### ✅ Equipo
- [ ] Reunión kickoff realizada
- [ ] Roadmap aprobado por stakeholders
- [ ] Roles y responsabilidades asignados
- [ ] Tareas de Fase 1 distribuidas

---

## 🚀 SIGUIENTE PASO

Una vez completados todos los checkboxes:

1. **Marcar Fase 0 como COMPLETADA**
2. **Pasar a:** `CHECKLIST_FASE_1_FUNDAMENTOS_DATOS.md`
3. **Fecha estimada de inicio Fase 1:** _____________

---

## 📝 NOTAS Y OBSERVACIONES

**Bloqueadores encontrados:**
- [Espacio para documentar problemas]

**Decisiones tomadas:**
- [Espacio para documentar cambios al plan]

**Lessons learned:**
- [Espacio para aprendizajes]

---

**Responsable Fase 0:** _____________
**Fecha inicio:** _____________
**Fecha fin:** _____________
**Status:** ⬜ No iniciada | ⏳ En progreso | ✅ Completada
