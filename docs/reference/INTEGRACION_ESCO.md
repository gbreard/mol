# Integración con ESCO y Análisis Semántico

Esta guía muestra cómo integrar los datos scrapeados de ZonaJobs con la taxonomía ESCO para clasificación de ocupaciones y extracción de skills.

---

## Estructura de Directorios

```
D:\OEDE\
├── Webscrapping\
│   ├── data\
│   │   ├── raw\              <- Datos scrapeados de ZonaJobs
│   │   └── processed\        <- Resultados de clasificación ESCO
│   └── scripts\
│       └── cargar_datos_para_procesamiento.py
│
└── ESCO\                     <- (Ajustar según tu estructura)
    ├── occupations_es.csv
    ├── skills_es.csv
    └── ...
```

---

## Paso 1: Cargar Datos de ZonaJobs

### Opción A: Usando el script de carga

```python
from cargar_datos_para_procesamiento import cargar_ultimos_datos, preparar_para_esco

# Cargar y preparar automaticamente
df_ofertas = preparar_para_esco()

# El DataFrame tiene estas columnas optimizadas:
# - id_oferta
# - titulo, titulo_normalizado
# - descripcion, descripcion_limpia
# - texto_completo (titulo + descripcion)
# - empresa, localizacion, modalidad_trabajo
```

### Opción B: Carga manual

```python
import pandas as pd
from pathlib import Path

# Directorio de datos
data_dir = Path("D:/OEDE/Webscrapping/data/raw")

# Cargar ultimo CSV
archivos = list(data_dir.glob("zonajobs_todas_*.csv"))
ultimo = max(archivos, key=lambda x: x.stat().st_mtime)
df_ofertas = pd.read_csv(ultimo)

print(f"Cargadas {len(df_ofertas)} ofertas")
```

---

## Paso 2: Cargar Taxonomía ESCO

```python
# Cargar ocupaciones ESCO
esco_occupations = pd.read_csv(
    "D:/OEDE/ESCO/occupations_es.csv",
    encoding='utf-8'
)

# Cargar skills ESCO
esco_skills = pd.read_csv(
    "D:/OEDE/ESCO/skills_es.csv",
    encoding='utf-8'
)

print(f"ESCO Ocupaciones: {len(esco_occupations)}")
print(f"ESCO Skills: {len(esco_skills)}")
```

---

## Paso 3: Matching de Ocupaciones

### Método 1: Matching Simple por Similitud de Texto

```python
from difflib import SequenceMatcher
import numpy as np

def similitud_texto(a, b):
    """Calcula similitud entre dos textos"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def encontrar_ocupacion_esco(titulo_oferta, esco_df, threshold=0.6):
    """
    Encuentra la ocupacion ESCO mas similar

    Args:
        titulo_oferta: Titulo de la oferta de ZonaJobs
        esco_df: DataFrame con ocupaciones ESCO
        threshold: Umbral minimo de similitud (0-1)

    Returns:
        dict con mejor match o None
    """
    mejor_match = None
    mejor_score = 0

    for idx, row in esco_df.iterrows():
        score = similitud_texto(titulo_oferta, row['preferredLabel'])

        if score > mejor_score and score >= threshold:
            mejor_score = score
            mejor_match = {
                'esco_code': row['conceptUri'],
                'esco_titulo': row['preferredLabel'],
                'similitud': score
            }

    return mejor_match

# Aplicar a todas las ofertas
resultados = []

for idx, oferta in df_ofertas.iterrows():
    match = encontrar_ocupacion_esco(
        oferta['titulo'],
        esco_occupations,
        threshold=0.6
    )

    resultado = {
        'id_oferta': oferta['id_oferta'],
        'titulo_original': oferta['titulo'],
        'esco_code': match['esco_code'] if match else None,
        'esco_titulo': match['esco_titulo'] if match else None,
        'similitud': match['similitud'] if match else 0
    }

    resultados.append(resultado)

    if (idx + 1) % 10 == 0:
        print(f"Procesadas {idx + 1}/{len(df_ofertas)} ofertas...")

df_clasificado = pd.DataFrame(resultados)

# Estadisticas
clasificadas = df_clasificado['esco_code'].notna().sum()
print(f"\nOfertas clasificadas: {clasificadas}/{len(df_clasificado)} ({clasificadas/len(df_clasificado)*100:.1f}%)")
```

### Método 2: Usando NLP y Embeddings (Más Avanzado)

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Cargar modelo de embeddings (requiere: pip install sentence-transformers)
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Generar embeddings de ocupaciones ESCO (una vez)
print("Generando embeddings ESCO...")
esco_embeddings = model.encode(
    esco_occupations['preferredLabel'].tolist(),
    show_progress_bar=True
)

# Generar embeddings de ofertas
print("Generando embeddings de ofertas...")
ofertas_embeddings = model.encode(
    df_ofertas['titulo'].tolist(),
    show_progress_bar=True
)

# Calcular similitudes
similitudes = cosine_similarity(ofertas_embeddings, esco_embeddings)

# Obtener mejor match para cada oferta
resultados_nlp = []

for idx, oferta in df_ofertas.iterrows():
    # Indice de mejor match
    mejor_idx = np.argmax(similitudes[idx])
    mejor_score = similitudes[idx][mejor_idx]

    if mejor_score >= 0.7:  # Threshold
        resultado = {
            'id_oferta': oferta['id_oferta'],
            'titulo_original': oferta['titulo'],
            'esco_code': esco_occupations.iloc[mejor_idx]['conceptUri'],
            'esco_titulo': esco_occupations.iloc[mejor_idx]['preferredLabel'],
            'similitud_cosine': float(mejor_score)
        }
    else:
        resultado = {
            'id_oferta': oferta['id_oferta'],
            'titulo_original': oferta['titulo'],
            'esco_code': None,
            'esco_titulo': None,
            'similitud_cosine': 0
        }

    resultados_nlp.append(resultado)

df_clasificado_nlp = pd.DataFrame(resultados_nlp)
```

---

## Paso 4: Extracción de Skills

```python
def extraer_skills_descripcion(descripcion, esco_skills_df):
    """
    Extrae skills mencionadas en la descripcion

    Args:
        descripcion: Texto de la descripcion
        esco_skills_df: DataFrame con skills ESCO

    Returns:
        Lista de skills encontradas
    """
    if pd.isna(descripcion) or descripcion == '':
        return []

    descripcion_lower = descripcion.lower()
    skills_encontradas = []

    for idx, skill in esco_skills_df.iterrows():
        skill_label = skill['preferredLabel'].lower()

        # Busqueda simple (mejorar con NLP)
        if skill_label in descripcion_lower:
            skills_encontradas.append({
                'skill_code': skill['conceptUri'],
                'skill_label': skill['preferredLabel']
            })

    return skills_encontradas

# Aplicar extraccion
print("Extrayendo skills...")

df_ofertas['skills_extraidas'] = df_ofertas['descripcion'].apply(
    lambda x: extraer_skills_descripcion(x, esco_skills)
)

df_ofertas['num_skills'] = df_ofertas['skills_extraidas'].apply(len)

print(f"Skills extraidas: {df_ofertas['num_skills'].sum()}")
print(f"Promedio por oferta: {df_ofertas['num_skills'].mean():.1f}")
```

---

## Paso 5: Análisis Semántico Avanzado

### Extracción de Entidades (NER)

```python
import spacy

# Cargar modelo de español (requiere: python -m spacy download es_core_news_md)
nlp = spacy.load("es_core_news_md")

def analizar_oferta(texto):
    """
    Analiza oferta con NER

    Returns:
        dict con entidades extraidas
    """
    doc = nlp(texto)

    entidades = {
        'tecnologias': [],
        'certificaciones': [],
        'experiencia_anos': [],
        'ubicaciones': []
    }

    for ent in doc.ents:
        if ent.label_ == 'MISC':  # Tecnologias
            entidades['tecnologias'].append(ent.text)
        elif ent.label_ == 'LOC':  # Ubicaciones
            entidades['ubicaciones'].append(ent.text)

    return entidades

# Aplicar NER
df_ofertas['entidades'] = df_ofertas['texto_completo'].apply(analizar_oferta)
```

### Análisis de Sentimiento (Opcional)

```python
from textblob import TextBlob

def analizar_sentimiento(texto):
    """Analiza sentimiento del texto"""
    blob = TextBlob(texto)
    return blob.sentiment.polarity

df_ofertas['sentimiento'] = df_ofertas['descripcion'].apply(analizar_sentimiento)
```

---

## Paso 6: Guardar Resultados

```python
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Directorio de salida
output_dir = Path("D:/OEDE/Webscrapping/data/processed")

# Combinar ofertas con clasificacion ESCO
df_final = df_ofertas.merge(
    df_clasificado_nlp,
    on='id_oferta',
    how='left'
)

# Guardar en CSV
csv_path = output_dir / f"ofertas_esco_clasificadas_{timestamp}.csv"
df_final.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"Guardado: {csv_path}")

# Guardar en Excel con multiples hojas
excel_path = output_dir / f"analisis_completo_{timestamp}.xlsx"

with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    df_final.to_excel(writer, sheet_name='Ofertas Clasificadas', index=False)

    # Resumen por ocupacion ESCO
    resumen = df_final.groupby('esco_titulo').size().sort_values(ascending=False)
    resumen.to_excel(writer, sheet_name='Resumen Ocupaciones')

    # Estadisticas
    stats = df_final.describe()
    stats.to_excel(writer, sheet_name='Estadisticas')

print(f"Guardado: {excel_path}")
```

---

## Paso 7: Visualización y Análisis

### Ocupaciones más demandadas

```python
import matplotlib.pyplot as plt

# Top 20 ocupaciones ESCO
top_ocupaciones = df_final['esco_titulo'].value_counts().head(20)

plt.figure(figsize=(12, 8))
top_ocupaciones.plot(kind='barh')
plt.title('Top 20 Ocupaciones ESCO en ZonaJobs')
plt.xlabel('Número de Ofertas')
plt.tight_layout()
plt.savefig(output_dir / 'top_ocupaciones_esco.png')
print("Grafico guardado: top_ocupaciones_esco.png")
```

### Mapa de calor de skills

```python
import seaborn as sns

# Matriz de co-ocurrencia de skills
# (Implementacion depende de tu estructura de datos)

# Ejemplo simple: Skills mas frecuentes
skills_todas = []
for skills_list in df_ofertas['skills_extraidas']:
    for skill in skills_list:
        skills_todas.append(skill['skill_label'])

skills_counts = pd.Series(skills_todas).value_counts().head(30)

plt.figure(figsize=(12, 8))
skills_counts.plot(kind='barh')
plt.title('Top 30 Skills Más Demandadas')
plt.xlabel('Frecuencia')
plt.tight_layout()
plt.savefig(output_dir / 'top_skills.png')
```

---

## Script Completo de Integración

```python
# integracion_esco_completa.py

import pandas as pd
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configuracion
DATA_DIR = Path("D:/OEDE/Webscrapping/data")
ESCO_DIR = Path("D:/OEDE/ESCO")
THRESHOLD_SIMILITUD = 0.7

def main():
    print("=" * 80)
    print("INTEGRACION ZONAJOBS + ESCO")
    print("=" * 80)

    # 1. Cargar datos
    print("\n[1] Cargando datos ZonaJobs...")
    ofertas = cargar_ultimos_datos_zonajobs()

    print("\n[2] Cargando taxonomia ESCO...")
    esco_occ = pd.read_csv(ESCO_DIR / "occupations_es.csv")
    esco_ski = pd.read_csv(ESCO_DIR / "skills_es.csv")

    # 2. Matching de ocupaciones
    print("\n[3] Clasificando ocupaciones con ESCO...")
    ofertas_clasificadas = clasificar_con_esco(ofertas, esco_occ)

    # 3. Extraccion de skills
    print("\n[4] Extrayendo skills...")
    ofertas_con_skills = extraer_skills(ofertas_clasificadas, esco_ski)

    # 4. Guardar resultados
    print("\n[5] Guardando resultados...")
    guardar_resultados(ofertas_con_skills)

    print("\n[OK] Proceso completado!")

if __name__ == "__main__":
    main()
```

---

## Recursos Adicionales

### Modelos de NLP Recomendados

1. **Sentence Transformers**:
   - `paraphrase-multilingual-MiniLM-L12-v2` (multilingüe, ligero)
   - `distiluse-base-multilingual-cased-v2` (mejor calidad)

2. **spaCy**:
   - `es_core_news_md` (español, tamaño medio)
   - `es_core_news_lg` (español, mejor calidad)

### Instalación

```bash
# Transformers
pip install sentence-transformers

# spaCy
pip install spacy
python -m spacy download es_core_news_md

# Visualizacion
pip install matplotlib seaborn

# Analisis de texto
pip install textblob
```

---

## Próximos Pasos

1. ✅ Ejecutar `cargar_datos_para_procesamiento.py` para preparar datos
2. ✅ Adaptar scripts de matching según tu taxonomía ESCO
3. ✅ Ajustar thresholds de similitud según resultados
4. ✅ Implementar pipeline completo de clasificación
5. ✅ Visualizar y analizar resultados
6. ✅ Iterar y mejorar el matching

---

**Última actualización**: 2025-10-16
