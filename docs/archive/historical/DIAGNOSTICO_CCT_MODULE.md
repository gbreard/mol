# Diagnostico Modulo CCT
**Fecha:** 2025-12-08
**Carpeta analizada:** D:\Trabajos en PY\Scrap CCT\

---

## 1. RESUMEN EJECUTIVO

| Metrica | Valor |
|---------|-------|
| **PDFs descargados** | 106,704 |
| **JSONs generados** | 1,718 |
| **Scripts Python** | ~350 (sin .venv) |
| **Carpetas principales** | 6 |
| **PDFs duplicados** | 129 nombres repetidos |

**Estado general:** Scraping COMPLETADO (106K PDFs), Parsing EN DESARROLLO con fragmentacion.

---

## 2. ESTRUCTURA DE CARPETAS

```
D:\Trabajos en PY\Scrap CCT\
├── .claude/                    (config Claude Code)
├── convenios-scraper/          [PROYECTO PRINCIPAL - SCRAPING]
│   ├── src/                    (22 archivos - codigo fuente)
│   ├── scripts/                (1,817 archivos - lotes de descarga)
│   ├── output/
│   │   └── TODOS_LOS_PDFS_CCT/ (106,255 PDFs)
│   ├── docs/
│   └── _ARCHIVO/               (34 archivos historicos)
│
├── Parseo/                     [OBSOLETO - Primeros experimentos]
│   └── parseo_cct/             (78 scripts, 10 PDFs test)
│
├── Parseo N1/                  [OBSOLETO - Incluye .venv corrupto]
│   └── 22,218 archivos (mayoria de .venv)
│
├── Parseo N2/                  [PROYECTO ACTIVO - PARSING + RAG]
│   ├── FASE_0_SCRAPING/        (OCR, DeepSeek, PDFs de prueba)
│   ├── FASE_1_PARSEO/          (Parser Python v2)
│   ├── FASE_2_3_REVISION/      (Muestra validacion)
│   ├── FASE_4_EDITOR_WEB/      (51,605 archivos - App Next.js)
│   ├── scripts/                (45 scripts utiles)
│   └── _OBSOLETO_NO_USAR/      (7,420 archivos)
│
└── Parseo_N/                   [EXPERIMENTO - Sistema extraccion]
    └── 67 archivos (25 scripts)
```

---

## 3. ESTADO POR COMPONENTE

### 3.1 SCRAPING (convenios-scraper)
| Item | Estado | Detalle |
|------|--------|---------|
| PDFs descargados | COMPLETADO | 106,236 en TODOS_LOS_PDFS_CCT/ |
| Metadata | PARCIAL | estado_descarga.json desactualizado |
| Tracking | BASICO | Solo 2 docs en JSON, 97 reportes |
| Documentacion | BUENA | ESTADO_PROYECTO.md actualizado |

**Problemas identificados:**
- [ ] 129 PDFs con nombres duplicados (mismo archivo en varias carpetas)
- [ ] Scripts de descarga dispersos (1,817 en scripts/)
- [ ] Sin DB unificada de estado de descarga

### 3.2 PARSING (Parseo N2)
| Item | Estado | Detalle |
|------|--------|---------|
| Parser v2 | FUNCIONAL | parser_v2_mejorado.py |
| Tesauro | COMPLETO | 4,608 conceptos |
| DeepSeek OCR | CONFIGURADO | Integrado |
| JSONs parseados | ~1,512 | En FASE_2_3_REVISION y FASE_4 |
| Editor Web | DESPLEGADO | https://cct-json.vercel.app |

**Problemas identificados:**
- [ ] Solo 315 PDFs procesados vs 106K disponibles
- [ ] 7,420 archivos obsoletos en _OBSOLETO_NO_USAR/
- [ ] Sin tracking centralizado PDF -> JSON

### 3.3 RAG (Parseo N2)
| Item | Estado | Detalle |
|------|--------|---------|
| Qdrant Cloud | CONFIGURADO | Collection cct_chunks |
| Vectorizacion | PENDIENTE | Script por crear (CCT-87) |
| API Consulta | PENDIENTE | Endpoint por crear (CCT-89) |
| Validacion humana | EN PROGRESO | UI funcional, 18 docs muestra |

---

## 4. PROBLEMAS CRITICOS

### 4.1 Fragmentacion de trabajo
```
4 carpetas de Parseo diferentes:
- Parseo/       (abandonado)
- Parseo N1/    (corrupto, .venv mezclado)
- Parseo N2/    (activo)
- Parseo_N/     (experimento)
```
**Impacto:** Codigo duplicado, confusion, dificil mantenimiento.
**Solucion:** Consolidar todo en Parseo N2, archivar el resto.

### 4.2 PDFs duplicados
```
129 nombres de archivo repetidos:
- CCT-130-75-Principal-1.pdf: 8 copias
- CCT-130-75-Principal-2.pdf: 8 copias
- CON-CCT-130-1975-A.pdf: 8 copias
...etc
```
**Impacto:** Desperdicio de espacio, confusion en procesamiento.
**Solucion:** Deduplicar manteniendo solo en TODOS_LOS_PDFS_CCT/.

### 4.3 Sin tracking centralizado
- No hay BD que relacione: PDF -> OCR -> JSON -> Validacion
- estado_descarga.json tiene solo 2 registros
- Imposible saber que porcentaje esta procesado

---

## 5. ARCHIVOS CLAVE

### Scripts importantes
| Archivo | Ubicacion | Funcion |
|---------|-----------|---------|
| `parser_v2_mejorado.py` | Parseo N2/FASE_1_PARSEO/ | Parser principal |
| `config_elementos.yaml` | Parseo N2/FASE_1_PARSEO/ | Patrones deteccion |
| `tesauro_convenios.json` | Parseo N2/FASE_1_PARSEO/ | 4,608 conceptos |
| `descarga_masiva_final_completa.py` | convenios-scraper/scripts/ | Scraping principal |

### Archivos tracking
| Archivo | Contenido |
|---------|-----------|
| `convenios-scraper/output/estado_descarga.json` | 2 docs (desactualizado) |
| `Parseo N2/FASE_2_3_REVISION/estado_revision.json` | 18 docs muestra |
| `convenios-scraper/output/REPORTES/` | 97 JSONs de progreso |

---

## 6. PROPUESTA DE ESTRUCTURA LIMPIA

```
D:\Trabajos en PY\Scrap CCT\
├── ARCHIVADO/                  [Mover aqui carpetas obsoletas]
│   ├── Parseo/
│   ├── Parseo N1/
│   └── Parseo_N/
│
├── convenios-scraper/          [SCRAPING - Sin cambios]
│   └── output/TODOS_LOS_PDFS_CCT/  (PDFs unicos)
│
├── parseo/                     [RENOMBRAR Parseo N2]
│   ├── FASE_0_SCRAPING/
│   ├── FASE_1_PARSEO/
│   ├── FASE_2_3_REVISION/
│   ├── FASE_4_EDITOR_WEB/
│   └── scripts/
│
└── tracking/                   [NUEVO - Sistema centralizado]
    ├── db/
    │   └── cct_tracking.db     (SQLite)
    └── scripts/
        ├── sync_pdfs.py
        └── check_status.py
```

---

## 7. SISTEMA DE TRACKING PROPUESTO

### Base de datos SQLite
```sql
-- Tabla principal: estado de cada PDF
CREATE TABLE documentos (
    id INTEGER PRIMARY KEY,
    codigo TEXT UNIQUE,          -- "CCT-130-75"
    pdf_path TEXT,               -- ruta al PDF
    pdf_hash TEXT,               -- SHA256 para deduplicar
    ocr_done BOOLEAN DEFAULT 0,
    ocr_path TEXT,
    json_done BOOLEAN DEFAULT 0,
    json_path TEXT,
    validated BOOLEAN DEFAULT 0,
    vectorized BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Tabla de metricas
CREATE TABLE metricas (
    fecha DATE PRIMARY KEY,
    total_pdfs INTEGER,
    total_ocr INTEGER,
    total_json INTEGER,
    total_validados INTEGER,
    total_vectorizados INTEGER
);
```

### Dashboard propuesto (Tab CCT en admin)
```
+------------------------------------------+
| CCT - CONVENIOS COLECTIVOS               |
+------------------------------------------+
| Total PDFs: 106,236    |  Procesados: 2% |
| Con OCR: 315          |  Validados: 18  |
| Vectorizados: 0       |                  |
+------------------------------------------+
| [Sync PDFs]  [Check Status]  [Dedup]    |
+------------------------------------------+
| Ultimos procesados:                      |
| - CCT-130-75 (OK) 2025-12-01            |
| - CON-ACU-1916-2023 (pendiente)         |
+------------------------------------------+
```

---

## 8. ACCIONES RECOMENDADAS

### Inmediatas (prioridad alta)
1. [ ] Crear script de deduplicacion de PDFs
2. [ ] Implementar BD de tracking SQLite
3. [ ] Mover carpetas obsoletas a ARCHIVADO/

### Corto plazo
4. [ ] Agregar tab CCT al dashboard admin
5. [ ] Crear script sync_pdfs.py para popular tracking
6. [ ] Documentar pipeline completo PDF -> RAG

### Mediano plazo
7. [ ] Integrar tracking con Linear (issues CCT-*)
8. [ ] Dashboard de progreso de validacion
9. [ ] Alertas de PDFs huerfanos o corruptos

---

## 9. ESTIMACIONES

| Tarea | Complejidad | Archivos |
|-------|-------------|----------|
| Deduplicacion PDFs | Media | 1 script |
| BD Tracking SQLite | Baja | 2 scripts |
| Tab CCT dashboard | Media | 1 archivo (app.py) |
| Script sync_pdfs | Media | 1 script |
| Mover obsoletos | Baja | Manual |

**Total:** ~5 scripts nuevos + modificacion dashboard

---

*Generado por analisis automatico - 2025-12-08*
