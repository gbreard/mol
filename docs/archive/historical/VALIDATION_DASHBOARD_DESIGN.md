# MOL - Sistema de Validación Colaborativa

> **Fecha:** 2025-12-05
> **Arquitectura:** Local (Windows) → S3 → Vercel Dashboard

---

## 1. Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LOCAL (Windows)                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐  │
│  │   SQLite    │───▶│  Exporter   │───▶│  JSONs para validación      │  │
│  │   (BD)      │    │  (Python)   │    │  (ofertas, matches, etc)    │  │
│  └─────────────┘    └─────────────┘    └──────────────┬──────────────┘  │
└────────────────────────────────────────────────────────┼────────────────┘
                                                         │ Upload
                                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              AWS S3                                      │
│  bucket: mol-validation-data                                             │
│  ├── snapshots/                                                          │
│  │   └── 2025-12-05/                                                     │
│  │       ├── ofertas.json          (datos de ofertas)                    │
│  │       ├── matches.json          (resultados matching)                 │
│  │       ├── metrics.json          (métricas agregadas)                  │
│  │       └── candidates.json       (top-k candidatos por oferta)         │
│  ├── gold_set/                                                           │
│  │   └── validations.json          (validaciones colaborativas)          │
│  └── config/                                                             │
│      └── esco_occupations.json     (catálogo ESCO reducido)              │
└────────────────────────────────────────────────────────┬────────────────┘
                                                         │ Fetch
                                                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Vercel Dashboard                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐  │
│  │   Métricas  │    │   Lista     │    │      Detalle Caso           │  │
│  │   Generales │    │   Casos     │    │   + Validación              │  │
│  └─────────────┘    └─────────────┘    └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Schema de Datos JSON

### 2.1 ofertas.json

Datos mínimos de ofertas necesarios para el dashboard.

```json
{
  "version": "1.0",
  "snapshot_date": "2025-12-05",
  "total_ofertas": 6521,
  "ofertas": [
    {
      "id": "1118027276",
      "titulo": "Ejecutivo de Cuentas SSR/SR - Presencial",
      "empresa": "StaffRock IT",
      "ubicacion": "Capital Federal",
      "fecha_publicacion": "2025-11-28",
      "descripcion_preview": "En StaffRock IT, empresa especializada en servicios de Staff Augmentation...",
      "descripcion_full": "...(texto completo para detalle)...",
      "url_original": "https://www.bumeran.com.ar/empleos/...",
      "fuente": "bumeran"
    }
  ]
}
```

**Campos:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | string | ID único de la oferta |
| titulo | string | Título del puesto |
| empresa | string | Nombre de la empresa (puede ser "Confidencial") |
| ubicacion | string | Localización normalizada |
| fecha_publicacion | string | Fecha ISO (YYYY-MM-DD) |
| descripcion_preview | string | Primeros 200 chars para lista |
| descripcion_full | string | Texto completo para detalle |
| url_original | string | Link a la oferta original |
| fuente | string | Portal de origen (bumeran, zonajobs, etc) |

---

### 2.2 matches.json

Resultados del matching ESCO para cada oferta.

```json
{
  "version": "1.0",
  "snapshot_date": "2025-12-05",
  "matching_version": "v8.4_topk",
  "total_matches": 6521,
  "matches": [
    {
      "id_oferta": "1118027276",
      "esco": {
        "uri": "http://data.europa.eu/esco/occupation/...",
        "label": "representante técnico de ventas",
        "isco_code": "C3322"
      },
      "scores": {
        "final": 0.514,
        "titulo": 0.542,
        "skills": 0.35,
        "descripcion": 0.48
      },
      "status": "revision",
      "never_confirm": false,
      "ajustes_aplicados": {
        "comercial_match": 0.05
      },
      "skills_matched": ["ventas", "negociación", "CRM"],
      "skills_oferta": ["ventas B2B", "negociación", "CRM", "prospección"]
    }
  ]
}
```

**Campos status:**
- `confirmado`: Score >= 0.60 y coverage >= 0.40
- `revision`: Score 0.50-0.60 o never_confirm=true
- `rechazado`: Score < 0.50

---

### 2.3 candidates.json

Top-K candidatos ESCO para cada oferta (para mostrar alternativas).

**Optimización:** Solo exportar candidatos de casos que requieren validación:
- `status = "revision"`
- `never_confirm = true`
- Cola de validación (high/medium priority)

Esto reduce de ~65,000 registros (6,521 × 10) a ~3,000-4,000 registros.

```json
{
  "version": "1.0",
  "snapshot_date": "2025-12-05",
  "total_ofertas_con_candidatos": 2156,
  "candidates": {
    "1118027276": [
      {
        "rank": 1,
        "uri": "http://data.europa.eu/esco/occupation/...",
        "label": "técnico de contadores eléctricos",
        "score": 0.579,
        "rejected_reason": "comercial_mismatch"
      },
      {
        "rank": 2,
        "uri": "http://data.europa.eu/esco/occupation/...",
        "label": "representante técnico de ventas",
        "score": 0.542,
        "selected": true
      },
      {
        "rank": 3,
        "uri": "http://data.europa.eu/esco/occupation/...",
        "label": "responsable de recursos humanos",
        "score": 0.541,
        "rejected_reason": "comercial_mismatch"
      }
    ]
  }
}
```

**Nota:** Para casos `confirmado` (score >= 0.60), no se exportan candidatos alternativos ya que no requieren revisión.

---

### 2.4 metrics.json

Métricas agregadas del snapshot.

```json
{
  "version": "1.0",
  "snapshot_date": "2025-12-05",
  "pipeline": {
    "ofertas_total": 6521,
    "ofertas_con_nlp": 5479,
    "ofertas_con_matching": 6521,
    "cobertura_nlp": 0.84
  },
  "matching": {
    "confirmados": 2934,
    "revision": 2156,
    "rechazados": 1431,
    "score_promedio": 0.58,
    "score_mediana": 0.61
  },
  "gold_set": {
    "total_casos": 19,
    "validados": 15,
    "pendientes": 4,
    "precision": 0.789
  },
  "by_error_type": {
    "sector_funcion": 0,
    "nivel_jerarquico": 2,
    "programa_general": 1,
    "tipo_ocupacion": 1
  },
  "distribucion_isco": {
    "1": 245,
    "2": 1823,
    "3": 987,
    "4": 1456,
    "5": 1234,
    "7": 456,
    "8": 234,
    "9": 86
  },
  "top_ocupaciones": [
    {"label": "empleado administrativo", "count": 456},
    {"label": "vendedor especializado", "count": 234},
    {"label": "operario de producción", "count": 198}
  ],
  "history": [
    {"date": "2025-12-01", "precision": 0.579, "version": "v8.3", "gold_set_size": 19},
    {"date": "2025-12-05", "precision": 0.789, "version": "v8.4", "gold_set_size": 19}
  ]
}
```

**Nuevos campos:**
| Campo | Descripción |
|-------|-------------|
| by_error_type | Distribución de errores por categoría (para diagnóstico) |
| history | Evolución temporal de precisión (para gráficos de tendencia) |

---

### 2.5 validations.json (Gold Set Colaborativo)

Estructura para validaciones de múltiples usuarios.

```json
{
  "version": "2.0",
  "last_updated": "2025-12-05T14:30:00Z",
  "validators": [
    {"id": "fzazworka", "name": "Federico", "role": "admin"},
    {"id": "jperez", "name": "Juan", "role": "validator"}
  ],
  "cases": [
    {
      "id_oferta": "1118027276",
      "titulo_oferta": "Ejecutivo de Cuentas SSR/SR",
      "esco_match": {
        "uri": "http://data.europa.eu/esco/...",
        "label": "representante técnico de ventas"
      },
      "priority": "high",
      "status": "validated",
      "validations": [
        {
          "validator_id": "fzazworka",
          "timestamp": "2025-12-05T14:30:00Z",
          "verdict": "correct",
          "confidence": "high",
          "comment": "Match aceptable, familia ventas correcta",
          "suggested_esco": null
        }
      ],
      "consensus": {
        "verdict": "correct",
        "agreement": 1.0,
        "validators_count": 1
      }
    },
    {
      "id_oferta": "1118027662",
      "titulo_oferta": "Farmacéutico/a para farmacias",
      "esco_match": {
        "uri": "http://data.europa.eu/esco/...",
        "label": "ingeniero farmacéutico"
      },
      "priority": "high",
      "status": "pending",
      "validations": [],
      "consensus": null
    }
  ],
  "queue": {
    "high_priority": ["1118027662", "1118027834"],
    "medium_priority": ["1118028038"],
    "random_sample": ["1118029001", "1118029045"]
  }
}
```

**Campos de validación:**
| Campo | Valores | Descripción |
|-------|---------|-------------|
| verdict | correct, incorrect, uncertain | Evaluación del validador |
| confidence | high, medium, low | Confianza en la evaluación |
| suggested_esco | URI o null | ESCO alternativo sugerido |

**Lógica de consenso:**
- 2+ validadores con mismo verdict → consenso
- Desacuerdo → escalado a admin
- Agreement = % de validadores con mismo verdict

---

### 2.6 esco_occupations.json (Catálogo reducido)

Para el selector de ESCO alternativo en el dashboard.

```json
{
  "version": "1.1.2",
  "total": 3045,
  "occupations": [
    {
      "uri": "http://data.europa.eu/esco/occupation/...",
      "label": "abogado/abogada",
      "isco_code": "C2611",
      "isco_group": "Profesionales del derecho",
      "keywords": ["derecho", "legal", "jurídico", "litigio"]
    }
  ],
  "isco_groups": {
    "1": "Directores y gerentes",
    "2": "Profesionales científicos e intelectuales",
    "3": "Técnicos y profesionales de nivel medio",
    "4": "Personal de apoyo administrativo",
    "5": "Trabajadores de servicios y vendedores",
    "6": "Agricultores y trabajadores calificados",
    "7": "Oficiales, operarios y artesanos",
    "8": "Operadores de instalaciones y máquinas",
    "9": "Ocupaciones elementales"
  }
}
```

---

## 3. Estructura de Archivos en S3

```
s3://mol-validation-data/
├── snapshots/
│   ├── 2025-12-05/
│   │   ├── ofertas.json         (~2 MB comprimido)
│   │   ├── matches.json         (~1 MB comprimido)
│   │   ├── candidates.json      (~5 MB comprimido)
│   │   └── metrics.json         (~10 KB)
│   ├── 2025-12-04/
│   │   └── ...
│   └── latest.json              (puntero al snapshot actual)
├── gold_set/
│   ├── validations.json         (gold set colaborativo)
│   └── history/
│       └── validations_2025-12-04.json
└── config/
    ├── esco_occupations.json    (~500 KB comprimido)
    └── validators.json          (lista de validadores)
```

**latest.json:**
```json
{
  "current_snapshot": "2025-12-05",
  "previous_snapshot": "2025-12-04"
}
```

---

## 4. Flujo de Datos

### 4.1 Export Local → S3

```bash
# Ejecutar después de cada pipeline
python scripts/export_to_s3.py --snapshot 2025-12-05
```

El script:
1. Extrae datos de SQLite
2. Genera JSONs optimizados
3. Comprime con gzip
4. Sube a S3 con aws cli

### 4.2 Dashboard → S3

```typescript
// Fetch desde Vercel
const snapshot = await fetch('https://mol-validation-data.s3.amazonaws.com/snapshots/latest.json')
const { current_snapshot } = await snapshot.json()
const ofertas = await fetch(`https://mol-validation-data.s3.amazonaws.com/snapshots/${current_snapshot}/ofertas.json`)
```

### 4.3 Validación → S3

```typescript
// POST validación desde dashboard
async function submitValidation(idOferta: string, validation: Validation) {
  // Fetch current validations
  const validations = await fetch('.../gold_set/validations.json')

  // Add new validation
  validations.cases.find(c => c.id_oferta === idOferta).validations.push(validation)

  // Re-calculate consensus
  calculateConsensus(validations)

  // Upload updated file
  await uploadToS3(validations)
}
```

---

## 5. Consideraciones de Seguridad

### Recomendación: Bucket Privado + IAM (MVP)

**No usar bucket público.** En su lugar:

1. Bucket privado (Block Public Access = ON)
2. Usuario IAM con credenciales limitadas
3. Credenciales en variables de entorno de Vercel

```bash
# Variables de entorno en Vercel
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET=mol-validation-data
```

### IAM Policy (lectura + escritura limitada)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSnapshots",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::mol-validation-data",
        "arn:aws:s3:::mol-validation-data/snapshots/*",
        "arn:aws:s3:::mol-validation-data/config/*"
      ]
    },
    {
      "Sid": "ReadWriteGoldSet",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::mol-validation-data/gold_set/*"
    }
  ]
}
```

### Autenticación del Dashboard

Opciones:
1. **Simple:** Password compartido (para MVP) - rápido pero sin trazabilidad
2. **OAuth:** Google/GitHub login (recomendado) - NextAuth.js + whitelist de emails
3. **AWS Cognito:** Integración nativa con S3 - más complejo

**Recomendación:** Empezar con (1) para MVP, migrar a (2) cuando haya más validadores.

---

## 6. Estimación de Tamaño

| Archivo | Registros | Tamaño Raw | Comprimido |
|---------|-----------|------------|------------|
| ofertas.json | 6,521 | ~8 MB | ~2 MB |
| matches.json | 6,521 | ~4 MB | ~1 MB |
| candidates.json | ~2,200 x 5 (optimizado) | ~5 MB | ~1.5 MB |
| metrics.json | 1 | ~15 KB | ~5 KB |
| esco_occupations.json | 3,045 | ~2 MB | ~500 KB |
| validations.json | ~100 | ~50 KB | ~15 KB |

**Nota:** candidates.json solo incluye casos en `revision` o `never_confirm`, reduciendo ~65% del tamaño.

**Total por snapshot:** ~5 MB comprimido
**Costo S3 mensual estimado:** < $1 USD

---

## 7. Wireframes del Dashboard

### 7.1 Vista: Métricas Generales (Home)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MOL - Dashboard de Validación                           [fzazworka] [Logout]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   OFERTAS       │  │   MATCHING      │  │   GOLD SET      │                  │
│  │                 │  │                 │  │                 │                  │
│  │    6,521        │  │    78.9%        │  │    19/50        │                  │
│  │   total         │  │   precisión     │  │   validados     │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│                                                                                 │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │  Distribución por Status          │  │  Distribución por ISCO            │ │
│  │  ┌──────────────────────────────┐ │  │  ┌──────────────────────────────┐ │ │
│  │  │ ████████████      Confirmado │ │  │  │ ███         1-Directores     │ │ │
│  │  │ ████████  45%     Revisión   │ │  │  │ ██████████  2-Profesionales  │ │ │
│  │  │ ████      22%     Rechazado  │ │  │  │ █████       3-Técnicos       │ │ │
│  │  │           33%                │ │  │  │ ███████     4-Administrativo │ │ │
│  │  └──────────────────────────────┘ │  │  │ ██████      5-Servicios      │ │ │
│  └────────────────────────────────────┘  │  │ ██          7-Operarios     │ │ │
│                                          │  └──────────────────────────────┘ │ │
│  ┌────────────────────────────────────┐  └────────────────────────────────────┘ │
│  │  Top 5 Ocupaciones ESCO           │                                         │
│  │  1. Empleado administrativo (456) │  ┌────────────────────────────────────┐ │
│  │  2. Vendedor especializado  (234) │  │  Cola de Validación               │ │
│  │  3. Operario de producción  (198) │  │                                    │ │
│  │  4. Recepcionista           (145) │  │  Alta prioridad:    4 casos       │ │
│  │  5. Técnico de soporte      (132) │  │  Media prioridad:   12 casos      │ │
│  └────────────────────────────────────┘  │  Muestra random:    8 casos       │ │
│                                          │                                    │ │
│                                          │  [Ir a Validación →]              │ │
│                                          └────────────────────────────────────┘ │
│                                                                                 │
│  Snapshot: 2025-12-05  |  Última actualización: hace 2 horas                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:**
| Componente | Datos | Interacción |
|------------|-------|-------------|
| KPI Cards | metrics.json | Click → filtrar lista |
| Gráfico Status | metrics.matching | Hover → tooltip |
| Gráfico ISCO | metrics.distribucion_isco | Click → filtrar por ISCO |
| Top Ocupaciones | metrics.top_ocupaciones | Click → ver casos |
| Cola Validación | validations.queue | Click → ir a lista |

---

### 7.2 Vista: Lista de Casos para Validar

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MOL - Dashboard de Validación                           [fzazworka] [Logout]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [< Home]  Lista de Casos para Validar                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Filtros: [Prioridad ▼] [Status ▼] [ISCO ▼] [Score ▼]     🔍 Buscar...         │
│                                                                                 │
│  Mostrando 24 casos  |  Ordenar por: [Prioridad ▼]                             │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐
│  │ 🔴 ALTA  │ 1118027662                                                       │
│  │          │ Farmacéutico/a para farmacias                                    │
│  │          │ → ingeniero farmacéutico  [Score: 0.52]                         │
│  │          │ Status: Pendiente  |  0 validaciones                             │
│  │          │                                                    [Validar →]   │
│  ├──────────┼──────────────────────────────────────────────────────────────────┤
│  │ 🔴 ALTA  │ 1118027834                                                       │
│  │          │ Vendedora digital/Atención al cliente                            │
│  │          │ → director de comercialización  [Score: 0.48] ⚠️                 │
│  │          │ Status: Pendiente  |  0 validaciones                             │
│  │          │                                                    [Validar →]   │
│  ├──────────┼──────────────────────────────────────────────────────────────────┤
│  │ 🟡 MEDIA │ 1118028038                                                       │
│  │          │ Ejecutivo/a comercial de cuentas                                 │
│  │          │ → director comercial  [Score: 0.55]                              │
│  │          │ Status: En disputa  |  2 validaciones (1 correcto, 1 incorrecto)│
│  │          │                                                    [Validar →]   │
│  ├──────────┼──────────────────────────────────────────────────────────────────┤
│  │ 🟢 RANDOM│ 1118029001                                                       │
│  │          │ Analista de sistemas                                             │
│  │          │ → analista de sistemas  [Score: 0.78]                            │
│  │          │ Status: Validado ✓  |  2 validaciones (consenso: correcto)       │
│  │          │                                                       [Ver →]   │
│  └──────────┴──────────────────────────────────────────────────────────────────┘
│                                                                                 │
│  [← Anterior]  Página 1 de 3  [Siguiente →]                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Columnas y estados:**
| Indicador | Significado |
|-----------|-------------|
| 🔴 ALTA | never_confirm=true o score < 0.50 |
| 🟡 MEDIA | score 0.50-0.60 o validaciones en disputa |
| 🟢 RANDOM | muestra aleatoria para control de calidad |
| ⚠️ | Flag especial (ej: nivel jerárquico dudoso) |

**Filtros disponibles:**
- Prioridad: Alta, Media, Random, Todas
- Status: Pendiente, En disputa, Validado, Todos
- ISCO: 1-9 (grupos principales)
- Score: <0.50, 0.50-0.60, 0.60-0.70, >0.70

---

### 7.3 Vista: Detalle de Caso + Validación

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MOL - Dashboard de Validación                           [fzazworka] [Logout]   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  [< Volver a Lista]  Validar Caso #1118027662                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │  OFERTA ORIGINAL                  │  │  MATCH ESCO                        │ │
│  │                                    │  │                                    │ │
│  │  Farmacéutico/a para farmacias    │  │  ingeniero farmacéutico            │ │
│  │  ─────────────────────────────    │  │  ISCO: C2145                       │ │
│  │  Empresa: Confidencial             │  │                                    │ │
│  │  Ubicación: Capital Federal        │  │  Score Final: 0.52                │ │
│  │  Fecha: 2025-11-28                 │  │  ├─ Título: 0.45                  │ │
│  │  Fuente: Bumeran                   │  │  ├─ Skills: 0.38                  │ │
│  │                                    │  │  └─ Descripción: 0.55             │ │
│  │  [Ver oferta original ↗]          │  │                                    │ │
│  └────────────────────────────────────┘  │  ⚠️ never_confirm: true           │ │
│                                          │  Razón: tipo_ocupacion            │ │
│  ┌────────────────────────────────────┐  └────────────────────────────────────┘ │
│  │  DESCRIPCIÓN COMPLETA             │                                         │
│  │                                    │  ┌────────────────────────────────────┐ │
│  │  Se busca Farmacéutico/a para     │  │  CANDIDATOS ALTERNATIVOS          │ │
│  │  cadena de farmacias. Requisitos: │  │                                    │ │
│  │  - Título de Farmacéutico         │  │  1. farmacéutico [0.58] ◀ sugerido│ │
│  │  - Matrícula habilitante          │  │  2. ingeniero farmacéutico [0.52] │ │
│  │  - Experiencia en atención al     │  │  3. técnico farmacéutico [0.48]   │ │
│  │    público                         │  │  4. auxiliar de farmacia [0.45]   │ │
│  │  - Disponibilidad horaria         │  │                                    │ │
│  │                                    │  │  [Buscar otra ocupación ESCO...]  │ │
│  │  Tareas:                           │  └────────────────────────────────────┘ │
│  │  - Dispensación de medicamentos   │                                         │ │
│  │  - Asesoramiento farmacéutico     │                                         │ │
│  │  - Control de stock               │                                         │ │
│  │  - Atención al cliente            │                                         │ │
│  └────────────────────────────────────┘                                         │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐
│  │  TU VALIDACIÓN                                                              │
│  │                                                                              │
│  │  ¿El match ESCO es correcto?                                                │
│  │                                                                              │
│  │  ( ) ✓ Correcto - El match es aceptable                                    │
│  │  (•) ✗ Incorrecto - El match es erróneo                                    │
│  │  ( ) ? Incierto - No puedo determinar                                      │
│  │                                                                              │
│  │  Confianza: [Alta ▼]                                                        │
│  │                                                                              │
│  │  ESCO sugerido: [farmacéutico                              ▼] (opcional)   │
│  │                                                                              │
│  │  Comentario:                                                                │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐
│  │  │ Es un farmacéutico de farmacia minorista, no un ingeniero que diseña   │
│  │  │ procesos farmacéuticos industriales.                                    │
│  │  └─────────────────────────────────────────────────────────────────────────┘
│  │                                                                              │
│  │                                              [Cancelar]  [Enviar Validación]│
│  └─────────────────────────────────────────────────────────────────────────────┘
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐
│  │  VALIDACIONES ANTERIORES                                                    │
│  │                                                                              │
│  │  (ninguna todavía)                                                          │
│  └─────────────────────────────────────────────────────────────────────────────┘
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Interacciones del formulario:**
| Elemento | Comportamiento |
|----------|----------------|
| Veredicto | Radio buttons, obligatorio |
| Confianza | Dropdown: Alta, Media, Baja |
| ESCO sugerido | Autocomplete con búsqueda en esco_occupations.json |
| Comentario | Textarea opcional (requerido si incorrecto) |
| Enviar | POST a S3, actualiza validations.json |

---

### 7.4 Flujo de Navegación

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │
│    HOME      │────▶│    LISTA     │────▶│   DETALLE    │
│   Métricas   │     │   Casos      │     │  + Validar   │
│              │◀────│              │◀────│              │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
  Click KPI card      Click caso          Enviar validación
  → Filtra lista      → Ver detalle       → Volver a lista
                                          → Siguiente caso
```

**Atajos de teclado (opcional):**
- `j/k` - Navegar casos
- `1/2/3` - Seleccionar veredicto
- `Enter` - Enviar validación
- `Esc` - Volver a lista

---

## 8. Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE DATOS COMPLETO                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOCAL (Windows)                                                            │
│  ───────────────                                                            │
│  1. Scraping → ofertas (Bumeran, ZonaJobs, etc)                            │
│  2. NLP → ofertas_nlp (extracción skills, requisitos)                      │
│  3. Matching → matches + candidates (ESCO v8.4)                            │
│  4. Export → JSONs comprimidos                         ─────┐              │
│                                                              │ upload      │
│                                                              ▼              │
│  AWS S3 (mol-validation-data)                                              │
│  ────────────────────────────                                              │
│  5. snapshots/YYYY-MM-DD/*.json (inmutable)                                │
│  6. gold_set/validations.json (mutable)                ◄────┐              │
│  7. config/esco_occupations.json                            │ write        │
│                                                              │              │
│  VERCEL (Dashboard)                                          │              │
│  ──────────────────                                          │              │
│  8. Fetch snapshots + validations                            │              │
│  9. Renderizar métricas, lista, detalle                      │              │
│  10. Colega valida caso  ────────────────────────────────────┘              │
│                                                                             │
│  LOCAL (Sync Inverso - MOL-36)                                              │
│  ─────────────────────────────                                              │
│  11. Pull validations.json desde S3                                         │
│  12. Procesar consenso (2+ validadores acuerdan)                           │
│  13. Merge con gold_set_manual_v2.json                                     │
│  14. Re-evaluar matching (test_gold_set_manual.py)                         │
│  15. Ajustar reglas si necesario → nuevo snapshot                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Sincronización Inversa (MOL-36) - Detalle

### Flujo de merge

```
S3: validations.json
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│  sync_validations_from_s3.py                                  │
│                                                               │
│  1. Descargar validations.json                                │
│  2. Filtrar casos con consenso (agreement >= 0.67)            │
│  3. Convertir formato:                                        │
│     S3: {"verdict": "correct", "validators_count": 2}         │
│     →                                                         │
│     Local: {"esco_ok": true, "comentario": "..."}             │
│  4. Merge con gold_set existente (sin duplicados)             │
│  5. Backup antes de modificar                                 │
│  6. Guardar gold_set_manual_v2.json                           │
└───────────────────────────────────────────────────────────────┘
```

### Resolución de conflictos

| Situación | Acción |
|-----------|--------|
| 2 validadores acuerdan | Consenso automático |
| 2 validadores difieren | Escalado a admin (no se importa) |
| 1 sola validación | Pendiente (no se importa) |
| Caso ya existe en gold_set local | Skip (no sobrescribir) |

### Comando

```bash
python scripts/sync_validations_from_s3.py --dry-run  # Ver cambios sin aplicar
python scripts/sync_validations_from_s3.py            # Aplicar merge
```

### Salida esperada

```
=== Sync Validaciones S3 → Local ===
Descargando validations.json...
Total casos en S3: 45
Casos con consenso: 28
  - Correcto: 22
  - Incorrecto: 6
Casos ya en gold_set local: 19
Nuevos casos para importar: 9

Backup creado: gold_set_manual_v1_backup_20251205.json
Gold set actualizado: gold_set_manual_v2.json
  - Total casos: 28 (era 19)
  - Nuevos correctos: 7
  - Nuevos incorrectos: 2

Ejecutar validación: python database/test_gold_set_manual.py
```

---

## 10. Próximos Pasos

1. **MOL-30:** Script export_to_s3.py
2. **MOL-31:** Configurar bucket S3
3. **MOL-32:** Dashboard - Vista métricas
4. **MOL-33:** Dashboard - Lista de casos
5. **MOL-34:** Dashboard - Detalle y validación
6. **MOL-35:** Sistema de autenticación
7. **MOL-36:** Sincronización validaciones → local

### Orden de implementación

```
MOL-31 (S3) ──┬──► MOL-30 (Export) ──► MOL-32 (Métricas)
              │                              │
              │                              ▼
              │                        MOL-33 (Lista)
              │                              │
              │                              ▼
              │                        MOL-34 (Validación)
              │                              │
              └──────────────────────────────┼────► MOL-36 (Sync)
                                             │
                                             ▼
                                       MOL-35 (Auth) [opcional]
```

---

> **Documento creado:** 2025-12-05
> **Actualizado:** 2025-12-05 (observaciones incorporadas)
> **Autor:** Claude + Federico
