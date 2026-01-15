# Guía de Anotación NER para Ofertas Laborales

## Tipos de Entidades

### 1. YEARS - Años de Experiencia
Marca los años de experiencia requeridos en la oferta.

**Ejemplos:**
- "Requerimos **3 años** de experiencia"
- "Mínimo **5 años** en el puesto"
- "Entre **2 a 4 años** trabajando con..."

### 2. EDUCATION - Educación
Marca el nivel educativo o título requerido.

**Ejemplos:**
- "**Universitario completo**"
- "**Licenciatura en Sistemas**"
- "Título **terciario** o universitario"

### 3. SKILL - Habilidad Técnica
Marca tecnologías, herramientas, lenguajes de programación, frameworks.

**Ejemplos:**
- "Experiencia con **Python** y **Django**"
- "Conocimientos de **SQL** y **PostgreSQL**"
- "Manejo de **Docker** y **Kubernetes**"

### 4. SOFT_SKILL - Habilidad Blanda
Marca competencias interpersonales y soft skills.

**Ejemplos:**
- "**Trabajo en equipo**"
- "Excelente **comunicación verbal**"
- "Capacidad de **liderazgo**"

### 5. LANGUAGE - Idioma
Marca idiomas requeridos y su nivel.

**Ejemplos:**
- "**Inglés avanzado**"
- "**Portugués intermedio**"
- "**Bilingüe inglés-español**"

### 6. AREA - Área de Experiencia
Marca áreas o dominios de experiencia laboral.

**Ejemplos:**
- "Experiencia en **desarrollo backend**"
- "Conocimiento de **administración de redes**"
- "Background en **machine learning**"

## Formato IOB

Cada palabra (token) debe etiquetarse con:
- **B-ENTITY**: Comienzo de entidad
- **I-ENTITY**: Continuación de entidad
- **O**: Fuera de entidad (Other)

### Ejemplo Completo

**Texto:**
```
Buscamos desarrollador Python con 3 años de experiencia en Django
```

**Anotación:**
```
Buscamos       O
desarrollador  O
Python         B-SKILL
con            O
3              B-YEARS
años           I-YEARS
de             O
experiencia    O
en             O
Django         B-SKILL
```

## Reglas de Anotación

1. **Multi-palabra**: Si una entidad tiene múltiples palabras, usa B- para la primera e I- para las siguientes
   - "inglés avanzado" → inglés/B-LANGUAGE avanzado/I-LANGUAGE

2. **Contexto**: Incluye modificadores relevantes en la entidad
   - "mínimo 3 años" → mínimo/B-YEARS 3/I-YEARS años/I-YEARS

3. **Listas**: Cada item de una lista es una entidad separada
   - "Python, Java y C++" → Python/B-SKILL ,/O Java/B-SKILL y/O C++/B-SKILL

4. **Ambigüedad**: Si no estás seguro, marca como O

5. **Consistencia**: Mantén el mismo criterio para casos similares

## Herramientas Recomendadas

- **Doccano**: https://github.com/doccano/doccano
- **Label Studio**: https://labelstud.io/
- **Prodigy**: https://prodi.gy/ (pago)

## Proceso de Trabajo

1. Cargar archivo JSONL en herramienta de anotación
2. Anotar entidades según las reglas
3. Revisar consistencia
4. Exportar en formato IOB
5. Validar con script de validación (próximo)
