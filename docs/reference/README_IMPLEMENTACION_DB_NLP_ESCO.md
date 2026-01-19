# IMPLEMENTACIÓN BASE DE DATOS NLP + ESCO COMPLETO

**Fecha:** 2025-10-31
**Estado:** LISTO PARA EJECUTAR
**Versión:** 1.0

---

## RESUMEN

Este README documenta la implementación completa de la base de datos integrada que unifica:
- Datos de scraping (5,479+ ofertas)
- Extracción NLP (27 campos)
- Ontología ESCO completa (solo español)
- Diccionarios de normalización Argentina-ESCO
- Matching semántico con BGE-M3

**Resultado final:** Base de datos SQLite de ~28 MB con 17 tablas.

---

## SCRIPTS CREADOS

### ✅ FASE 1: Preparación (COMPLETADO)

#### 1.1. `fix_encoding_db.py`
**Propósito:** Corregir encoding UTF-8 corrupto en descripciones
**Tiempo:** 10-15 minutos
**Requisitos:** `pip install ftfy tqdm`

```bash
cd D:\OEDE\Webscrapping\database
python fix_encoding_db.py
```

**Output:**
- Nueva columna `ofertas.descripcion_utf8` con texto limpio
- Reporte con ejemplos de correcciones

---

#### 1.2. `create_tables_nlp_esco.py`
**Propósito:** Crear 17 tablas del esquema completo
**Tiempo:** <1 minuto
**Requisitos:** Ninguno adicional

```bash
python create_tables_nlp_esco.py
```

**Output:**
- 17 tablas creadas (ofertas_nlp, esco_*, diccionarios, matching)
- ~50 índices para optimización
- Reporte de tablas creadas

---

### ✅ FASE 2: Población ESCO (COMPLETADO)

#### 2. `populate_esco_from_rdf.py`
**Propósito:** Parsear RDF de ESCO y poblar tablas
**Tiempo:** 15-30 minutos
**Requisitos:** `pip install rdflib tqdm`

```bash
python populate_esco_from_rdf.py
```

**Datos procesados:**
- ~3,008 ocupaciones ESCO
- ~6,000 alternative labels en español
- ~436 códigos ISCO
- ~13,890 skills
- ~20,000 alternative labels de skills
- ~60,000 associations ocupación-skill

**Archivo fuente:** `D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf`

---

### 🔄 FASE 3: Diccionarios Argentinos (PENDIENTE CREAR)

#### 3. `populate_dictionaries.py` (A CREAR)
**Propósito:** Cargar diccionarios argentinos y CNO
**Tiempo:** 2-5 minutos

**Código esquemático:**

```python
#!/usr/bin/env python3
"""Carga diccionarios argentinos en DB"""

import sqlite3
import json
from pathlib import Path

def cargar_diccionario_arg_esco():
    """Carga diccionario_normalizacion_arg_esco.json"""
    json_path = Path("../03_esco_matching/data/diccionario_normalizacion_arg_esco.json")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = sqlite3.connect('bumeran_scraping.db')
    cursor = conn.cursor()

    for termino_arg, info in data.items():
        cursor.execute("""
            INSERT OR IGNORE INTO diccionario_arg_esco (
                termino_argentino, esco_terms_json, isco_target,
                esco_preferred_label, notes
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            termino_arg,
            json.dumps(info.get('esco_terms', [])),
            info.get('isco_target'),
            info.get('esco_label'),
            info.get('notes')
        ))

    conn.commit()
    conn.close()

def cargar_sinonimos_regionales():
    """Carga diccionario_sinonimos_ocupacionales_AR_ES.json"""
    # Similar al anterior
    pass

if __name__ == '__main__':
    cargar_diccionario_arg_esco()
    cargar_sinonimos_regionales()
```

**Para completar:**
1. Cargar `diccionario_normalizacion_arg_esco.json` → tabla `diccionario_arg_esco`
2. Cargar `diccionario_sinonimos_ocupacionales_AR_ES.json` → tabla `sinonimos_regionales`
3. Cargar CNO ocupaciones (si existe CSV)
4. Cargar matches CNO-ESCO pre-calculados (BGE-M3)

---

### 🔄 FASE 4: Migración NLP (PENDIENTE CREAR)

#### 4. `migrate_nlp_csv_to_db.py` (A CREAR)
**Propósito:** Migrar resultados NLP de CSVs a tabla ofertas_nlp
**Tiempo:** 5 minutos

**Código esquemático:**

```python
#!/usr/bin/env python3
"""Migra resultados NLP de CSV a tabla ofertas_nlp"""

import sqlite3
import pandas as pd
from pathlib import Path

def migrar_nlp():
    csv_path = Path("../02.5_nlp_extraction/data/processed")

    # Buscar CSVs de NLP
    csv_files = list(csv_path.glob("*_nlp_extracted.csv"))

    if not csv_files:
        print("No se encontraron archivos NLP")
        return

    # Leer CSV más reciente
    df = pd.read_csv(csv_files[0])

    conn = sqlite3.connect('bumeran_scraping.db')

    # Insertar en ofertas_nlp
    df.to_sql('ofertas_nlp', conn, if_exists='append', index=False)

    conn.close()

if __name__ == '__main__':
    migrar_nlp()
```

---

### 🔄 FASE 5: Matching Ofertas-ESCO (PENDIENTE CREAR)

#### 5. `match_ofertas_to_esco.py` (A CREAR)
**Propósito:** Matching semántico con BGE-M3
**Tiempo:** 30-60 minutos
**Requisitos:** `pip install sentence-transformers numpy`

**Código esquemático:**

```python
#!/usr/bin/env python3
"""Matching ofertas-ESCO con BGE-M3"""

import sqlite3
from sentence_transformers import SentenceTransformer
import numpy as np

def generar_embeddings_ocupaciones():
    """Genera embeddings de ocupaciones ESCO"""
    model = SentenceTransformer('BAAI/bge-m3')
    conn = sqlite3.connect('bumeran_scraping.db')

    cursor = conn.cursor()
    cursor.execute("SELECT occupation_uri, preferred_label_es FROM esco_occupations")

    ocupaciones = cursor.fetchall()
    labels = [occ[1] for occ in ocupaciones]

    embeddings = model.encode(labels, show_progress_bar=True)

    # Guardar embeddings (pickle o numpy)
    np.save('esco_occupation_embeddings.npy', embeddings)

    conn.close()
    return embeddings

def match_ofertas():
    """Matchea ofertas con ocupaciones ESCO"""
    model = SentenceTransformer('BAAI/bge-m3')
    conn = sqlite3.connect('bumeran_scraping.db')

    # Cargar embeddings ESCO
    esco_embeddings = np.load('esco_occupation_embeddings.npy')

    # Obtener ofertas
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_oferta, titulo, descripcion_utf8
        FROM ofertas
    """)

    for id_oferta, titulo, descripcion in cursor.fetchall():
        # Generar embedding de oferta
        texto_oferta = f"{titulo}. {descripcion[:500]}"
        oferta_embedding = model.encode([texto_oferta])[0]

        # Calcular similaridad
        similarities = np.dot(esco_embeddings, oferta_embedding)
        best_match_idx = np.argmax(similarities)
        best_score = similarities[best_match_idx]

        # Guardar match en ofertas_esco_matching
        # ...

    conn.close()

if __name__ == '__main__':
    generar_embeddings_ocupaciones()
    match_ofertas()
```

---

## ORDEN DE EJECUCIÓN COMPLETO

### Paso 1: Instalar dependencias

```bash
pip install ftfy rdflib sentence-transformers tqdm numpy pandas
```

### Paso 2: Ejecutar scripts en orden

```bash
cd D:\OEDE\Webscrapping\database

# FASE 1
python fix_encoding_db.py          # 10-15 min
python create_tables_nlp_esco.py   # <1 min

# FASE 2
python populate_esco_from_rdf.py   # 15-30 min

# FASE 3 (CREAR PRIMERO)
# python populate_dictionaries.py  # 2-5 min

# FASE 4 (CREAR PRIMERO)
# python migrate_nlp_csv_to_db.py  # 5 min

# FASE 5 (CREAR PRIMERO)
# python match_ofertas_to_esco.py  # 30-60 min
```

**Tiempo total:** ~1-2 horas

---

## VERIFICACIÓN POST-IMPLEMENTACIÓN

### Verificar encoding corregido

```sql
SELECT
    id_oferta,
    SUBSTR(descripcion, 1, 50) AS original,
    SUBSTR(descripcion_utf8, 1, 50) AS limpio
FROM ofertas
WHERE descripcion LIKE '%�%'
LIMIT 5;
```

### Verificar tablas ESCO pobladas

```sql
SELECT
    'Ocupaciones' AS tipo, COUNT(*) AS total FROM esco_occupations
UNION ALL
SELECT 'Alt Labels ES', COUNT(*) FROM esco_occupation_alternative_labels
UNION ALL
SELECT 'Skills', COUNT(*) FROM esco_skills
UNION ALL
SELECT 'Associations', COUNT(*) FROM esco_associations;
```

**Resultado esperado:**
- Ocupaciones: ~3,008
- Alt Labels ES: ~6,000
- Skills: ~13,890
- Associations: ~60,000

### Query de ejemplo integrada

```sql
-- Top 10 ofertas con mayor match ESCO
SELECT
    o.titulo,
    o.empresa,
    m.esco_occupation_label,
    m.occupation_match_score,
    n.skills_tecnicas_list
FROM ofertas o
LEFT JOIN ofertas_nlp n ON o.id_oferta = n.id_oferta
LEFT JOIN ofertas_esco_matching m ON o.id_oferta = m.id_oferta
WHERE m.occupation_match_score > 0.8
ORDER BY m.occupation_match_score DESC
LIMIT 10;
```

---

## PRÓXIMOS PASOS (POST-IMPLEMENTACIÓN)

### 1. Completar Fase 02.5 NLP
- Anotar 500 ofertas manualmente para NER
- Entrenar modelo spaCy
- Procesar 5,479 ofertas con modelo entrenado

### 2. Generar Diccionario v4.0
```sql
-- Extraer candidatos para keywords v4.0
SELECT
    sd.skill_mencionado,
    COUNT(DISTINCT sd.id_oferta) AS ofertas_demandan
FROM ofertas_esco_skills_detalle sd
WHERE sd.esco_skill_uri IS NULL  -- Skills sin match ESCO
GROUP BY sd.skill_mencionado
HAVING ofertas_demandan >= 10
ORDER BY ofertas_demandan DESC
LIMIT 500;
```

**Objetivo:** 1,500 keywords (desde 1,148 actual) → cobertura 67-83%

### 3. Testing del bucle iterativo
- Ejecutar scraping con v4.0
- Medir incremento en ofertas capturadas
- Iterar a v5.0 si necesario

---

## TROUBLESHOOTING

### Error: "rdflib not found"
```bash
pip install rdflib
```

### Error: "Archivo RDF no encontrado"
Verificar ruta en `populate_esco_from_rdf.py`:
```python
rdf_path=r'D:\Trabajos en PY\EPH-ESCO\01_datos_originales\Tablas_esco\Data\esco-v1.2.0.rdf'
```

### Proceso muy lento
- Usar SSD si está disponible
- Cerrar otras aplicaciones
- Ejecutar en horarios de baja carga

### Error de memoria al cargar RDF
- RDF de 1.26 GB requiere ~4 GB RAM
- Cerrar aplicaciones no esenciales
- Reiniciar computadora antes de ejecutar

---

## SCRIPTS FINALES CREADOS

1. ✅ `fix_encoding_db.py` (200 líneas)
2. ✅ `create_tables_nlp_esco.py` (600 líneas)
3. ✅ `populate_esco_from_rdf.py` (400 líneas)
4. 🔄 `populate_dictionaries.py` (esqueleto - 50 líneas)
5. 🔄 `migrate_nlp_csv_to_db.py` (esqueleto - 30 líneas)
6. 🔄 `match_ofertas_to_esco.py` (esqueleto - 100 líneas)

**Total código:** ~1,380 líneas Python

---

## DOCUMENTACIÓN RELACIONADA

- `PROPUESTA_ESTRUCTURA_DB_NLP_ESCO_COMPLETA.md` - Diseño completo con queries de ejemplo
- `CONCEPTO_BUCLE_ITERATIVO_KEYWORDS.md` - Explicación del bucle v1 → v3.2 → v4.0
- `SCRAPING_PHASE_SUMMARY.md` - Documentación técnica fase scraping
- `README_LIMPIEZA_2025.md` - Estado del proyecto

---

**Fecha de creación:** 2025-10-31
**Autor:** Claude Code
**Versión:** 1.0
**Estado:** ✅ LISTO PARA EJECUTAR (Fases 1-2), 🔄 PENDIENTE (Fases 3-5)
