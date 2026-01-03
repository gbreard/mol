# Sistema de Validación MOL v2 - Documento de Planificación

**Fecha:** 2025-12-06
**Estado:** En diseño
**Versión:** 2.0

---

## 1. Visión General

### 1.1 Objetivo del Sistema

Construir un pipeline de procesamiento de ofertas laborales con validación colaborativa que permita:
- Extraer información estructurada de ofertas (NLP)
- Clasificar ofertas según taxonomía ESCO (Matching)
- Validar calidad con colaboradores remotos
- Liberar datos limpios a producción para usuarios finales

### 1.2 Usuarios del Sistema

| Usuario | Dashboard | Función |
|---------|-----------|---------|
| Administrador (Gerardo) | Local | Control total del pipeline |
| 3 Admins validadores | Vercel Optimización | Validar NLP y Matching |
| Analistas OEDE | Vercel Producción | Consumir datos limpios |

### 1.3 Métricas de Éxito

- Precisión NLP >= 90%
- Precisión Matching >= 95%
- Precisión por familia >= 80%
- Tiempo de iteración de optimización < 1 día (con gold set)

---

## 2. Arquitectura General

### 2.1 Principio Fundamental

**LOCAL es el centro de control. CLOUD es para colaboración.**

- Toda la ejecución ocurre en LOCAL
- S3 es el puente de datos entre local y cloud
- Vercel solo lee datos y escribe validaciones
- Colegas NO pueden disparar acciones, solo validar

### 2.2 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LOCAL (tu máquina) - CENTRO DE CONTROL                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DASHBOARD ADMIN LOCAL (Streamlit)                                  │   │
│  │  • Configurar modelos (Ollama, embeddings)                          │   │
│  │  • Ejecutar scraping                                                │   │
│  │  • Ejecutar pipeline (NLP, Matching)                                │   │
│  │  • Tests contra gold set                                            │   │
│  │  • Exportar a S3                                                    │   │
│  │  • Sincronizar validaciones                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Scraper  │─►│   NLP    │─►│ Matching │─►│ Embeddings│                   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
│                      │                                                      │
│                      ▼                                                      │
│                ┌──────────┐                                                │
│                │  SQLite  │                                                │
│                └──────────┘                                                │
│                      │                                                      │
│                      ▼                                                      │
│            export_*.py scripts                                             │
│                      │                                                      │
└──────────────────────┼──────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │       S3        │
              │                 │
              │  /experiment/   │◄────────────┐
              │  /production/   │             │
              └─────────────────┘             │
                  │         │                 │
        ┌─────────┘         └─────────┐       │
        ▼                             ▼       │
┌──────────────────────┐    ┌──────────────────────┐
│ DASH OPTIMIZACIÓN    │    │ DASH USUARIO FINAL   │
│ Vercel (gratis)      │    │ Vercel (pago)        │
│ 3 admins             │    │ Multiusuario         │
│                      │    │                      │
│ • Validar NLP        │    │ • Métricas mercado   │
│ • Validar Matching   │    │ • Visualizaciones    │
│ • Feedback           │    │ • Exportar datos     │
│                      │    │                      │
│ Lee: /experiment/    │    │ Lee: /production/    │
│ Escribe: validations │    │ Escribe: nada        │
└──────────────────────┘    └──────────────────────┘
           │
           │ validaciones
           └────────────────────► sync al local
```

### 2.3 Los 3 Dashboards

| Dashboard | Ubicación | Tecnología | Usuarios | Función | Costo |
|-----------|-----------|------------|----------|---------|-------|
| **Control** | Local | Streamlit | Solo admin | Ejecuta todo | $0 |
| **Optimización** | Vercel | Next.js | 3 admins | Valida | $0 (free tier) |
| **Producción** | Vercel | Next.js | Analistas | Consume | ~$20/mes |

### 2.4 Permisos S3

| Dashboard | Lee | Escribe |
|-----------|-----|---------|
| Local | Todo | Todo |
| Optimización | `/experiment/*` | `/experiment/validations/*` |
| Producción | `/production/*` | Nada |

---

## 3. Scraping

### 3.1 Problema Detectado

Existen múltiples scripts de scraping que causan confusión:

| Script | ¿Qué hace? | Resultado |
|--------|------------|-----------|
| `bumeran_scraper.py` | API sin keywords | ❌ Solo ~20 ofertas nuevas |
| `run_scraping_completo.py` | Wrapper incompleto | ❌ No usa keywords |
| `run_scheduler.py` | **El correcto** | ✅ ~9,000-11,000 ofertas |

**Bug de la API Bumeran:**
- `page_size=100` → API devuelve solo 20
- Página 11+ → devuelve duplicados
- **Workaround:** 1 página × 1,148 keywords

### 3.2 Limitación Conocida y Aceptada

| Métrica | Valor | Nota |
|---------|-------|------|
| Ofertas en API Bumeran | ~11,450 | Total estimado |
| IDs en tracking | 10,223 | Lo capturado (89%) |
| Ofertas en BD | 9,564 | Procesadas |
| Gap | ~1,200 | Se va cerrando |

**Evolución del gap:**
- Antes: 9,385 IDs en tracking (82%)
- Ahora: 10,223 IDs en tracking (89%)
- Ofertas nuevas: +701

**Estrategia confirmada:** El gap se cierra naturalmente con cada ejecución.

### 3.3 Solución: Un Solo Punto de Entrada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DASHBOARD LOCAL - Tab Scraping                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  BUMERAN                                          [Estado: ✅ Listo]  │ │
│  │                                                                       │ │
│  │  Estrategia: [ultra_exhaustiva_v3_2 ▼]  Keywords: 1,148              │ │
│  │                                                                       │ │
│  │  Última ejecución: 2025-12-05 08:00    Ofertas: 9,385                │ │
│  │  Próxima ejecución: 2025-12-09 08:00   (Lunes)                       │ │
│  │                                                                       │ │
│  │  [▶️ Ejecutar Ahora]                                                  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ⚠️ NO usar bumeran_scraper.py directamente - siempre usar este botón     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Comando Único

El botón "Ejecutar Ahora" ejecuta internamente:

```python
# Internamente ejecuta:
from scrapers.scrapear_con_diccionario import BumeranMultiSearch

scraper = BumeranMultiSearch()
df = scraper.scrapear_multiples_keywords(
    estrategia='ultra_exhaustiva_v3_2',  # 1,148 keywords
    max_paginas_por_keyword=1,            # Evita bug paginación
    incremental=True                      # Solo IDs nuevos
)
```

### 3.5 Integración con Permanencia

```
FLUJO SEMANAL COMPLETO:
───────────────────────

run_scheduler.py
    │
    ├── 1. Scrapea con 1,148 keywords
    ├── 2. Guarda IDs en tracking JSON
    └── 3. Inserta en BD
           │
           ▼
detectar_bajas_integrado.py (automático post-scraping)
    │
    ├── 4. Lee IDs del tracking (snapshot actual)
    ├── 5. Compara con BD.estado_oferta = 'activa'
    ├── 6. Diferencia → marca como 'baja'
    └── 7. Calcula permanencia
```

**Limitación de permanencia:**
- Ofertas que nunca entraron al tracking → nunca detectamos su baja
- Ofertas nuevas (post-scraping inicial) → permanencia correcta
- El gap inicial se cierra naturalmente con el tiempo

### 3.6 Scripts a Deprecar

| Script | Acción | Razón |
|--------|--------|-------|
| `bumeran_scraper.py` | Marcar como interno | Solo usar desde scrapear_con_diccionario |
| `run_scraping_completo.py` | Eliminar | Confuso, no usa keywords |
| `bumeran_selenium_scraper.py` | Eliminar | Legacy, API funciona |

### 3.7 Estrategias de Keywords

| Estrategia | Keywords | Uso |
|------------|----------|-----|
| `ultra_exhaustiva_v3_2` | 1,148 | **Producción semanal** |
| `exhaustiva` | 1,073 | Alternativa |
| `completa` | 56 | Testing rápido |
| `minima` | 4 | Debug |

### 3.8 Otros Portales (Futuro)

| Portal | Script | Estado |
|--------|--------|--------|
| ZonaJobs | `zonajobs_scraper_final.py` | ✅ Funciona |
| Computrabajo | `computrabajo_scraper.py` | ⚠️ Revisar |
| LinkedIn | `linkedin_scraper.py` | ⚠️ Rate limited |
| Indeed | `indeed_scraper.py` | ⚠️ Rate limited |

---

## 4. Arquitectura de Dos Ciclos

### 4.1 Principio

**Son dos problemas distintos que requieren validación separada:**

| Aspecto | Ciclo 1: NLP | Ciclo 2: Matching |
|---------|--------------|-------------------|
| **Problema** | Extracción de info de texto libre | Clasificación semántica |
| **Entrada** | Texto variable (corto/largo, estructurado/narrativo) | Datos estructurados |
| **Salida** | Campos parseados | Ocupación ESCO |
| **Criterio** | ¿Extrajo correctamente? | ¿Clasificó correctamente? |
| **Umbral** | 90% precisión | 95% precisión |

### 4.2 Flujo Secuencial

```
SCRAPING
    │
    │  ofertas_raw
    ▼
CICLO 1: NLP
    │
    ├── Si score >= 3/7: pasa
    │
    ├── Si score < 3/7: descarta o reprocesa
    │
    │  ofertas_parsed (con campos NLP)
    ▼
CICLO 2: MATCHING
    │
    ├── Si precisión batch >= 95%: libera
    │
    ├── Si precisión < 95%: optimiza
    │
    │  ofertas_matched (con ESCO)
    ▼
PRODUCCIÓN
    │
    │  datos limpios
    ▼
DASHBOARD USUARIO FINAL
```

### 4.3 Interfaces de Datos

#### Scraping → NLP (ofertas_raw)

```json
{
  "id": "1118027662",
  "titulo": "Vendedor Senior B2B",
  "descripcion": "Buscamos vendedor con 3+ años...",
  "empresa": "Confidencial",
  "ubicacion": "CABA",
  "fecha_publicacion": "2025-12-05",
  "url_fuente": "https://bumeran.com/...",
  "portal": "bumeran"
}
```

#### NLP → Matching (ofertas_parsed)

```json
{
  "id": "1118027662",
  "titulo": "Vendedor Senior B2B",
  
  "// --- Campos extraídos por NLP ---",
  "experiencia_min_anios": 3,
  "nivel_educativo": "universitario",
  "soft_skills": ["negociación", "comunicación"],
  "tech_skills": ["CRM", "SAP"],
  "tareas": ["prospección", "cierre de ventas"],
  "area_funcional": "Ventas",
  "nivel_seniority": "senior",
  
  "// --- Metadatos NLP ---",
  "nlp_score": 5,
  "nlp_version": "v8.0",
  "tipo_oferta": "demanda_real",
  "pasa_a_matching": true,
  
  "// --- Fuentes (trazabilidad) ---",
  "nivel_educativo_fuente": "inferido",
  "tareas_explicitas": ["cierre de ventas"],
  "tareas_inferidas": ["prospección"]
}
```

#### Matching → Producción (ofertas_matched)

```json
{
  "id": "1118027662",
  "titulo": "Vendedor Senior B2B",
  
  "// --- Todo lo anterior + ---",
  
  "// --- Resultado Matching ---",
  "esco_uri": "http://data.europa.eu/esco/occupation/abc123",
  "esco_label": "representante técnico de ventas",
  "isco_code": "3322",
  "match_score": 0.72,
  "match_status": "confirmado",
  "familia_funcional": "comercial_ventas",
  
  "// --- Estado validación ---",
  "validacion_nlp": "correcto",
  "validacion_matching": "correcto",
  "listo_produccion": true
}
```

---

## 5. Esquema NLP v5

### 5.1 Resumen de Bloques

| # | Bloque | Campos | Crítico para Matching |
|---|--------|--------|----------------------|
| 1 | Metadata portal | 9 | - |
| 2 | Empresa | 10 | sector_empresa, es_tercerizado |
| 3 | Ubicación/Movilidad | 12 | modalidad, requiere_viajar |
| 4 | Experiencia | 9 | experiencia_nivel_previo |
| 5 | Educación | 8 | titulo_requerido, orientacion |
| 6 | Skills/Conocimientos | 10 | tech_skills, tecnologias, marcas |
| 7 | Idiomas | 4 | idioma_principal |
| 8 | Rol/Tareas | 7 | **tareas**, tiene_gente_cargo |
| 9 | Condiciones laborales | 8 | **area_funcional**, **nivel_seniority** |
| 10 | Compensación | 12 | - |
| 11 | Beneficios | 12 | - |
| 12 | Metadatos NLP | 10 | pasa_a_matching |
| 13 | Licencias/Permisos | 7 | licencia_conducir |
| 14 | Calidad/Flags | 12 | tiene_req_discriminatorios |
| 15 | Certificaciones | 4 | certificaciones_requeridas |
| 16 | Condiciones especiales | 12 | trabajo_en_altura, riesgo |

**Total: ~130 campos (muchos opcionales)**

### 5.2 Campos Críticos para Matching (Top 10)

| Prioridad | Campo | Impacto | Ejemplo |
|-----------|-------|---------|---------|
| ★★★★★ | titulo | Determina ocupación | "Vendedor Senior" |
| ★★★★★ | tareas[] | Confirma ocupación | ["picking", "inventario"] |
| ★★★★★ | area_funcional | Contexto sector | "Ventas", "Almacén" |
| ★★★★★ | nivel_seniority | Nivel jerárquico | "junior", "gerente" |
| ★★★★☆ | tiene_gente_cargo | Jefe vs IC | true/false |
| ★★★★☆ | titulo_requerido | Ocupación específica | "Lic. en SHyMA" |
| ★★★★☆ | producto_servicio | Qué vende/produce | "Plan de Ahorro" |
| ★★★☆☆ | tech_skills[] | Skills técnicas | ["SAP", "Excel"] |
| ★★★☆☆ | tecnologias[] | Stack técnico | ["4G", "5G", "CCTV"] |
| ★★★☆☆ | sector_empresa | Industria | "automotriz", "retail" |

### 5.3 Trazabilidad: Explícito vs Inferido

Para cada campo se guarda la fuente:

```python
# Campos simples
nivel_educativo: "universitario"
nivel_educativo_fuente: "inferido"  # explicito / inferido / metadata

# Campos lista
tareas_explicitas: ["liquidación impuestos"]  # del texto
tareas_inferidas: ["contabilidad general"]    # deducidas
tareas: [...]  # unión para uso

# Campos cualitativos convertidos
experiencia_texto: "amplia experiencia"  # original
experiencia_min_anios: 3                 # conversión
experiencia_min_anios_fuente: "inferido"
experiencia_min_anios_confianza: "baja"
```

### 5.4 Tabla de Conversión Cualitativo → Cuantitativo

**Experiencia:**

| Texto | Años inferidos | Confianza |
|-------|----------------|-----------|
| "sin experiencia" | 0 | alta |
| "experiencia" | 1-2 | baja |
| "amplia experiencia" | 3+ | media |
| "sólida experiencia" | 3-5 | media |
| "extensa trayectoria" | 7+ | media |

**Seniority (si no viene en metadata):**

| Señales | Seniority | Confianza |
|---------|-----------|-----------|
| "sin experiencia", "1er empleo" | trainee/junior | alta |
| "Jr", "junior" en título | junior | alta |
| "amplia experiencia" | semi-senior | media |
| "Sr", "senior" en título | senior | alta |
| "Jefe", "Coord" en título | supervisor | alta |
| "Gerente", "Director" | gerente | alta |

---

## 6. Análisis de Avisos Reales

### 6.1 Avisos Analizados

| # | Aviso | Tipo | Características |
|---|-------|------|-----------------|
| 1 | Operario de Depósito | Operativo básico | Tareas detalladas, requisitos básicos |
| 2 | Vendedor Plan de Ahorro | Comercial | Producto específico, sin tareas explícitas |
| 3 | Jefatura SHyMA | Profesional/Jefatura | Muy completo, título específico, viajes |
| 4 | Técnico Seguridad Electrónica | Técnico especializado | Marcas, discriminatorio, baja calidad texto |
| 5 | Contadora | Profesional corto | Aviso corto, inferencias necesarias |
| 6 | Team Leader Redes Móviles | Tercerizado/Riesgo | Outsourcing, certificaciones, altura |

### 6.2 Patrones Identificados

**Tipos de ofertas:**

| Tipo | % estimado | Características | NLP puede extraer |
|------|------------|-----------------|-------------------|
| Demanda real | ~60% | Requisitos concretos y medibles | ✅ Sí |
| Motivacional | ~20% | Más marketing que requisitos | ❌ Poco |
| Título-only | ~15% | Solo título, descripción vacía | ❌ Solo título |
| Híbrida | ~5% | Info útil escondida en texto largo | ✅ Si modelo es bueno |

**Patrones especiales detectados:**

- **Tercerización**: Empresa contratante ≠ cliente final (ej: Experis → Telco)
- **Discriminación**: Requisitos ilegales (sexo, edad) - flag importante
- **Género en título**: "Contadora" vs "Contador/a" - normalizar
- **Certificaciones con vigencia**: "Altura < 6 meses" - estructura especial
- **Horario específico**: "9am - 6pm L-V" - extraer
- **Marcas específicas**: "Hikvision", "Dahua" - conocimiento técnico

---

## 7. Sistema de Validación en Capas

### 7.1 Crítica del Diseño Original

**Problema:** Validación humana como gate obligatorio en cada iteración

- Cada ciclo requiere ~1 semana (esperar humanos)
- 3 iteraciones NLP + 3 iteraciones Matching = 6+ semanas
- Cuello de botella: humanos validando

### 7.2 Solución: Validación en Capas

```
CAPA 1: VALIDACIÓN AUTOMÁTICA (local, instantánea)
──────────────────────────────────────────────────
Gold Set Grande (200+ casos etiquetados)
       │
       ▼
test_nlp.py / test_matching.py
       │
       ├── Si < 85%: Claude Code sigue iterando (sin humanos)
       │
       └── Si >= 85%: Pasa a Capa 2

CAPA 2: VALIDACIÓN HUMANA MUESTRAL (cloud, semanal)
────────────────────────────────────────────────────
Solo versiones "candidatas" que pasaron Capa 1
       │
       ▼
Dashboard Vercel (90 casos nuevos)
       │
       ├── Si < 95%: Volver a Capa 1 (con errores → gold set)
       │
       └── Si >= 95%: Liberar a Producción

CAPA 3: PRODUCCIÓN
──────────────────
Datos limpios → Dashboard Usuario Final
```

### 7.3 Beneficio

| Métrica | Antes | Después |
|---------|-------|---------|
| Tiempo por iteración | ~7 días | ~30 minutos |
| Iteraciones por mes | 4 | 100+ |
| Rol de humanos | Gate obligatorio | Solo candidatas finales |

### 7.4 Inversión Requerida

- **Gold set grande**: 200+ ofertas etiquetadas manualmente (2-3 días)
- **Scripts de test**: test_nlp.py, test_matching.py (1 día)
- **Valor**: Acelera TODO el desarrollo futuro

---

## 8. Muestreo por Familias Funcionales

### 8.1 Las 10 Familias Actuales (v8.3)

| Familia | Cobertura | En Revisión | Regla |
|---------|-----------|-------------|-------|
| **SIN_FAMILIA** | 37.8% | 97.2% | Sin clasificar |
| comercial_ventas | 20.1% | 96.2% | Penaliza comercial → no comercial |
| admin_contable | 15.6% | 92.3% | Penaliza admin → negocios |
| operario_produccion | 15.2% | 96.2% | Penaliza operario → negocios |
| salud_farmacia | 3.4% | 96.0% | Penaliza farmacia → ingeniero |
| nivel_junior | 3.3% | 95.4% | Penaliza junior → directivo |
| servicios_atencion | 2.8% | 96.7% | Penaliza servicios → directivo |
| profesional_juridico | 1.2% | 97.4% | Penaliza abogado → admin |
| barista_gastronomia | 0.3% | 100% | Penaliza barista → comercio café |
| programa_pasantia | 0.3% | 100% | Siempre never_confirm |

### 8.2 Estrategia de Muestreo (90 casos/semana)

| Categoría | Casos | % | Lógica |
|-----------|-------|---|--------|
| SIN_FAMILIA | 40 | 44% | Crítico: descubrir nuevos patrones |
| Familias 100% revisión | 15 | 17% | barista, pasantia, juridico |
| Familias grandes | 25 | 28% | comercial, admin, operario (solo low score) |
| Aleatorio (control) | 10 | 11% | Validez estadística |

**Dentro de SIN_FAMILIA (40 casos):**
- 20 casos score < 0.50 (muy baja confianza)
- 10 casos score 0.50-0.60 (zona gris)
- 10 aleatorios (control)

### 8.3 Criterio de Liberación

**Híbrido (recomendado):**

1. Precisión global >= 95%
2. Ninguna familia < 80% (para familias con >= 5 casos validados)
3. Familias con < 5 casos: excluidas del criterio 2

```
Ejemplo:
- Global: 96% ✓
- SIN_FAMILIA: 85% ✓ (>= 80%)
- comercial: 100% ✓
- barista: 75% (3 casos) → excluida (< 5 casos)
→ LIBERAR ✅
```

---

## 9. Migración a Cloud (Futuro)

### 9.1 Equivalencias

| Local | Cloud |
|-------|-------|
| SQLite | PostgreSQL (Supabase, Neon) |
| Ollama | API Claude/OpenAI |
| ChromaDB | Pinecone/pgvector |
| Scripts Python | Modal/Railway/EC2 |
| Cron jobs | GitHub Actions |
| Streamlit local | Streamlit Cloud |

### 9.2 Checklist para Portabilidad

```
HACER AHORA:
□ Usar SQLAlchemy (no sqlite3 directo)
□ Abstraer LLM con config (no hardcodear Ollama)
□ Abstraer embeddings con config
□ Variables de entorno para secrets
□ Scripts sin paths absolutos
□ Requirements.txt actualizado

HACER DESPUÉS (cuando migres):
□ Crear PostgreSQL en Supabase
□ Configurar API keys (Claude/OpenAI)
□ Re-indexar embeddings en Pinecone
□ GitHub Actions para cron
□ Desplegar en Modal/Railway
```

### 9.3 Costo Estimado Cloud

| Servicio | Costo/mes |
|----------|-----------|
| Modal (compute) | ~$5-10 |
| Supabase (PostgreSQL) | $0 (free tier) |
| S3 | ~$1 |
| API Claude/OpenAI | ~$20-50 |
| Vercel Pro | $20 |
| **Total** | **~$50-80/mes** |

---

## 10. Bloque 2: Liberación a Producción

### 10.1 Flujo de Liberación

```
BATCH SEMANAL (ej: 800 ofertas)
        │
        ▼
┌─────────────────────┐
│ ¿NLP >= 90%?        │──── NO ───► Volver a optimizar
└─────────────────────┘
        │ SÍ
        ▼
┌─────────────────────┐
│ ¿Matching >= 95%?   │──── NO ───► Volver a optimizar
└─────────────────────┘
        │ SÍ
        ▼
┌─────────────────────┐
│ export_production.py│
│                     │
│ • Genera Parquet    │
│ • Particiona x sem  │
│ • Sube a S3         │
└─────────────────────┘
        │
        ▼
S3/production/
├── Ofertas W49: 18,000
├── Ofertas W50: +800 (nuevas)
└── Total: 18,800
```

### 10.2 Decisión: ¿Qué ofertas van a producción?

**TODAS las ofertas del batch van a producción** cuando la muestra pasa los umbrales.

Razonamiento:
- Si la muestra (90 casos) tiene 95% precisión
- Estadísticamente el batch completo (~800) tiene ~95% precisión
- No tiene sentido descartar el 89% de los datos

### 10.3 Duplicados Cross-Portal

**Script:** `deduplicate_cross_portal.py`

| Fase | Método | Detalle |
|------|--------|---------|
| Blocking | Provincia + semana | Reduce O(n²) a O(n×k) |
| Scoring | Título 40% + Desc 35% + Empresa 15% + Salario 10% | RapidFuzz + MinHash |
| Decisión | >= 0.85 duplicado, 0.70-0.84 revisar | Union-Find para grupos |

**Ejecución:** Después del scraping, ANTES de NLP.

**Campos agregados:**
- `grupo_duplicado`: ID del grupo (ej: "DUP-00001")
- `es_duplicado`: 1 si es duplicado, 0 si no
- `es_canonico`: 1 si es la versión principal

### 10.4 Formato de Datos: Parquet Particionado

```
S3/production/
├── current/
│   └── ofertas.parquet          ◄── Lambda lee esto
│
├── history/
│   ├── year=2025/
│   │   ├── week=49/ofertas.parquet
│   │   ├── week=50/ofertas.parquet
│   │   └── ...
│   └── ...
│
└── metadata.json
    {
      "last_update": "2025-12-06",
      "total_ofertas": 18800,
      "weeks": ["W49", "W50"],
      "precision_nlp": 0.92,
      "precision_matching": 0.96
    }
```

**¿Por qué Parquet?**
- Columnar: queries rápidos
- Comprimido: ~10x menos que JSON
- Tipado: tipos de datos preservados
- Particionado: solo lee lo necesario

### 10.5 Arquitectura Backend: Lambda + S3 (Free Tier)

```
┌─────────────────────────────────────────────────────────────────┐
│  AWS (Free Tier)                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  API Gateway ◄─── Lambda (Python + PyArrow)                    │
│       │                │                                        │
│       │                └──► Lee S3/production/ofertas.parquet  │
│       │                     Filtra con pandas                  │
│       │                     Devuelve JSON                      │
│       ▼                                                         │
│  Endpoints:                                                    │
│  GET /ofertas?familia=comercial&semana=50                      │
│  GET /metricas?year=2025                                       │
│  GET /export?format=csv                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Costo:** $0/mes (free tier)
**Escalabilidad:** Migrar a Athena (~$0.20/mes) cuando crezca

### 10.6 Permanencia de Ofertas

**Objetivo:** Calcular cuánto tiempo estuvo publicada cada oferta.

**Categorías:**

| Categoría | Días | Interpretación |
|-----------|------|----------------|
| baja | <7 | Ofertas que se cubren rápido (alta demanda) |
| media | 7-30 | Proceso de selección normal |
| alta | >30 | Difíciles de cubrir (escasez de perfil) |

**Estado actual (primera ejecución 2025-12-06):**

| Métrica | Valor |
|---------|-------|
| Bajas detectadas | 0 (normal, primera ejecución) |
| IDs en tracking | 10,223 |
| Ofertas activas en BD | 9,564 |
| Permanencia calculada | 9,556 ofertas |

**Nota:** Las bajas se detectarán a partir del próximo ciclo (Lun/Jue) cuando comparemos el nuevo snapshot con el actual.

**Implementación: Integrada con scraping semanal (0 requests extra)**

```
FLUJO SEMANAL
─────────────
run_scheduler.py
    │
    ├── Scrapea ofertas con 1,148 keywords
    ├── Guarda IDs en tracking JSON
    └── Inserta en BD
           │
           ▼
detectar_bajas_integrado.py (automático)
    │
    ├── Lee IDs del tracking (snapshot actual)
    ├── Compara con BD.estado_oferta = 'activa'
    ├── Diferencia → marca como 'baja'
    └── Calcula permanencia (baja/media/alta)
```

**Campos agregados a BD:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| estado_oferta | string | 'activa' / 'baja' / 'expirada' |
| fecha_ultimo_visto | date | Última vez en API |
| fecha_baja | date | Cuándo desapareció |
| dias_publicada | int | Permanencia calculada |
| categoria_permanencia | string | 'baja' / 'media' / 'alta' |

**Scripts:**
- `database/migrations/001_add_permanencia_fields.sql`
- `database/detectar_bajas_integrado.py`
- `database/calcular_permanencia.py`

### 10.7 ESCO Skills y Knowledge

**Estado de la ontología ESCO:**

| Métrica | Valor |
|---------|-------|
| Ocupaciones ESCO | 3,045 |
| Skills (competencias) | 11,009 (77.3%) |
| Knowledge (conocimientos) | 3,232 (22.7%) |
| Associations | 134,805 |
| skill_type poblado | 99.96% |

**Estructura de datos por oferta:**

```json
{
  "esco_uri": "http://data.europa.eu/esco/occupation/abc123",
  "esco_label": "Representante técnico de ventas",
  
  "// --- Skills ESCO (del estándar) ---",
  "esco_essential_skills": ["negociación", "técnicas de venta"],
  "esco_optional_skills": ["inglés comercial"],
  "esco_essential_knowledge": ["productos financieros", "CRM"],
  "esco_optional_knowledge": ["mercado automotriz"],
  
  "// --- Skills NLP (de la oferta real) ---",
  "nlp_tech_skills": ["SAP", "Excel", "Salesforce"],
  "nlp_soft_skills": ["negociación", "comunicación"],
  "nlp_conocimientos": ["Plan de Ahorro"],
  
  "// --- Análisis brecha (calculado) ---",
  "brecha_skills_match": ["negociación"],
  "brecha_solo_esco": ["inglés comercial"],
  "brecha_solo_local": ["SAP", "Excel", "Plan de Ahorro"]
}
```

**Valor analítico de la brecha ESCO vs Local:**

| Análisis | Pregunta que responde |
|----------|----------------------|
| Cobertura ESCO | ¿Qué % de skills ESCO se piden en Argentina? |
| Skills emergentes | ¿Qué pide el mercado local que ESCO no tiene? |
| Brecha formación | ¿Qué skills ESCO esenciales no se piden? |

**Script:** `database/esco_skills_extractor.py`

---

## 11. Dashboard Usuario Final (Producción)

### 11.1 Requisitos OEDE

Basado en documento de especificación de colegas OEDE.

**Principios de diseño:**
- Sin siglas técnicas (CIUO, ESCO) → usar "normalizadas"
- Todos los gráficos con botón [Descargar Excel/CSV]
- Subtítulo dinámico con contexto de filtros aplicados

### 11.2 Estructura General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo] Monitor de Ofertas Laborales                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│        [Panorama General] [Requerimientos] [Ofertas Laborales]             │
├──────────────┬──────────────────────────────────────────────────────────────┤
│              │                                                              │
│  FILTROS     │              CONTENIDO PRINCIPAL                            │
│  ──────────  │              (según tab seleccionado)                        │
│              │                                                              │
│  Territorio  │                                                              │
│  [Nacional▼] │                                                              │
│              │                                                              │
│  Período     │                                                              │
│  [Semana ▼]  │                                                              │
│              │                                                              │
│  Permanencia │                                                              │
│  [Todas  ▼]  │                                                              │
│              │                                                              │
│  🔍 Buscar   │                                                              │
│  ocupación   │                                                              │
│              │                                                              │
│  📂 Árbol    │                                                              │
│  ocupaciones │                                                              │
│              │                                                              │
│  ──────────  │                                                              │
│  [Metodología]                                                              │
│  [Descargar] │                                                              │
│              │                                                              │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

### 11.3 Filtros (Panel Izquierdo)

| Filtro | Opciones | Tipo |
|--------|----------|------|
| Territorio | Nacional / Provincial / Localidad | Jerárquico |
| Período | Última semana / Último mes / Último año | Temporal |
| Permanencia | Todas / Baja / Media / Alta | Categoría |
| Buscador ocupación | Texto con autocompletar | Búsqueda |
| Árbol ocupaciones | Navegación jerárquica | Navegación |

**Botones finales:**
- [Metodología y Sistema] → Documentación
- [Descargar Base Usuaria] → Export CSV completo

### 11.4 Pestaña: Panorama General

**Subtítulo dinámico:** "Datos al [Fecha] para [Territorio], [Ocupación], [Permanencia]"

**Tarjetas KPI:**

| KPI | Descripción |
|-----|-------------|
| Ofertas Analizadas | Total de ofertas con filtros aplicados |
| Ocupaciones Normalizadas | Total de categorías ISCO identificadas |
| Habilidades Identificadas | Total de skills únicas ESCO |

**Gráficos:**

| # | Gráfico | Tipo | Detalle |
|---|---------|------|---------|
| 1 | Evolución ofertas | Línea | Eje X según período (semanal/mensual/anual) |
| 2 | Top 10 ocupaciones | Barras | Ocupación seleccionada resaltada en otro color |
| 3 | Distribución por jurisdicción | Barras | Provincias + CABA, localidad agregada si aplica |

### 11.5 Pestaña: Requerimientos

**Gráficos de torta (2x2):**

| # | Gráfico | Categorías |
|---|---------|------------|
| 1 | Requerimiento de Edad | Sin req. / Solo jóvenes / Adultos y mayores |
| 2 | Requerimiento de Género | Sin req. / Mujeres / Varones |
| 3 | Requerimiento Educativo | Sin req. / Sec. completa+ / Terciaria+ / Posgrado+ |
| 4 | Otros Requerimientos | Sin req. / Idiomas / Experiencia / Ubicación / Otro |

**Gráficos de barras:**

| # | Gráfico | Detalle |
|---|---------|---------|
| 5 | Top 20 Conocimientos | skill_type = 'knowledge' de ESCO |
| 6 | Top 20 Competencias | skill_type = 'skill' de ESCO |

### 11.6 Pestaña: Ofertas Laborales

**Filtros secundarios (horizontales):**
- Edad
- Género  
- Nivel Educativo
- Otros Requerimientos (Idiomas, Experiencia, etc.)
- Buscador por título

**Tabla de ofertas:**

| Columna | Fuente |
|---------|--------|
| Ocupación normalizada | esco_label |
| Título oferta | titulo (original empresa) |
| Fecha publicación | fecha_publicacion |
| Conocimientos | esco_knowledge (tags) |
| Competencias | esco_skills (tags) |
| Link | url_fuente |

**Funcionalidades:**
- Paginación
- Ordenamiento por columna
- Descarga Excel/CSV del listado filtrado

### 11.7 Arquitectura Técnica

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  VERCEL (Next.js)                                                          │
│  https://mol-produccion.vercel.app                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Panorama   │    │Requerimientos│   │  Ofertas    │                     │
│  │  General    │    │             │    │  Laborales  │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         └──────────────────┼──────────────────┘                             │
│                            │                                                │
│                            ▼                                                │
│                    API Gateway (AWS)                                        │
│                            │                                                │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  AWS (Free Tier)                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Lambda (Python + PyArrow + Pandas)                                        │
│       │                                                                     │
│       └──► S3/production/current/ofertas.parquet                           │
│                                                                             │
│  Endpoints:                                                                │
│  ├── GET /ofertas?territorio=X&periodo=Y&permanencia=Z                     │
│  ├── GET /metricas/panorama                                                │
│  ├── GET /metricas/requerimientos                                          │
│  ├── GET /ocupaciones/arbol                                                │
│  └── GET /export?format=csv                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Costo:** $0/mes (free tier AWS + Vercel free)

---

## 12. Issues Linear

- [ ] Actualizar issues existentes con nuevo alcance
- [ ] Crear issues faltantes
- [ ] Definir orden de implementación

---

## 13. Anexos

### 13.1 Estructura S3 Completa

```
s3://mol-validation-data/
│
├── experiment/
│   ├── nlp/
│   │   ├── 2025-W50/
│   │   │   ├── parsed.json.gz
│   │   │   └── validations.json
│   │   └── latest.json
│   │
│   └── matching/
│       ├── 2025-W50/
│       │   ├── matched.json.gz
│       │   ├── candidates.json.gz
│       │   └── validations.json
│       └── latest.json
│
├── production/
│   ├── current/
│   │   └── ofertas.parquet          ◄── Lambda lee esto
│   │
│   ├── history/
│   │   └── year=2025/
│   │       ├── week=49/ofertas.parquet
│   │       ├── week=50/ofertas.parquet
│   │       └── ...
│   │
│   └── metadata.json
│
├── goldset/
│   ├── nlp_gold.json
│   └── matching_gold.json
│
└── config/
    └── esco_occupations.json.gz
```

### 13.2 Scripts a Crear/Existentes

| Script | Función | Estado |
|--------|---------|--------|
| `test_nlp.py` | Evaluar NLP contra gold set | Por crear |
| `test_matching.py` | Evaluar Matching contra gold set | Por crear |
| `generate_sample.py` | Generar muestra estratificada | Por crear |
| `export_nlp.py` | Exportar parsed a S3/experiment | Por crear |
| `export_matching.py` | Exportar matched a S3/experiment | Por crear |
| `sync_validations.py` | Descargar validaciones de S3 | Por crear |
| `analyze_errors.py` | Analizar errores para Claude Code | Por crear |
| `export_production.py` | Generar Parquet, subir a S3/production | Por crear |
| `lambda_ofertas.py` | Lambda que lee Parquet y responde queries | Por crear |
| `deduplicate_cross_portal.py` | Detectar duplicados entre portales | ✅ Existe |
| `detectar_bajas_integrado.py` | Detectar ofertas dadas de baja | ✅ Existe |
| `calcular_permanencia.py` | Calcular y analizar permanencia | ✅ Existe |
| `esco_skills_extractor.py` | Extraer skills/knowledge por ocupación | ✅ Existe |
| `update_skill_types_from_rdf.py` | Actualizar skill_type desde RDF | ✅ Existe |

---

*Documento generado: 2025-12-06*
*Actualizado: 2025-12-06 (Bloque 2 completo, Dashboard Usuario Final, ESCO skills)*
