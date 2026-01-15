# Estrategia de Matching v2.0

> **Versión:** 2.0.0
> **Fecha:** 2025-12-10
> **Estado:** Diseño
> **Dependencia:** NLP Schema v5 (153 columnas)

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo

Alcanzar **98%+ de precisión** en el matching de ofertas laborales a ocupaciones ESCO, aprovechando todas las variables extraídas por NLP v10.

### 1.2 Problema Actual

El matching v8.4 solo utiliza 3 variables:
- `titulo` (texto crudo)
- `skills` (lista básica)
- `descripcion` (texto completo)

NLP v10 extrae **153 columnas** con información estructurada que no se está aprovechando.

### 1.3 Principios de Diseño

| Principio | Descripción |
|-----------|-------------|
| **Separación NLP/Matching** | NLP extrae, Matching consume. Sin lógica de extracción en matching. |
| **Sin hardcodeado** | Toda la configuración en JSON externos, no en código. |
| **Cascada de filtros** | Reducir candidatos progresivamente antes de scoring costoso. |
| **Trazabilidad** | Registrar qué nivel y método produjo cada match. |
| **Configurabilidad** | Pesos, umbrales y mapeos ajustables sin cambiar código. |

---

## 2. Variables Disponibles (NLP v10)

### 2.1 Para Filtrar Candidatos (Pre-scoring)

Estas variables reducen el espacio de búsqueda de 3000 ocupaciones ESCO a ~50-100 candidatos.

| Variable | Tipo | Uso en Filtrado |
|----------|------|-----------------|
| `tipo_oferta` | enum | Descartar "motivacional", "titulo_only", "bolsa_trabajo" |
| `area_funcional` | enum | Filtrar por sector ESCO (ej: IT → ISCO 25xx) |
| `nivel_seniority` | enum | Filtrar por jerarquía (junior → no ISCO 1xxx) |
| `tiene_gente_cargo` | bool | Filtrar por supervisión |
| `sector_empresa` | string | Contexto sectorial |
| `calidad_texto` | enum | Descartar "muy_baja" |

### 2.2 Para Scoring (Similitud)

Estas variables se usan para calcular scores de similitud con candidatos ESCO.

| Variable | Tipo | Peso Base | Notas |
|----------|------|-----------|-------|
| `titulo_limpio` | string | 0.40 | Sin ubicación ni empresa |
| `tareas_explicitas` | list | 0.30 | Tareas mencionadas literalmente |
| `tareas_inferidas` | list | 0.10 | Tareas deducidas del contexto |
| `skills_tecnicas_list` | list | 0.15 | Skills técnicas específicas |
| `tecnologias_list` | list | 0.15 | Herramientas y tecnologías |
| `conocimientos_especificos_list` | list | 0.10 | Conocimientos de dominio |
| `mision_rol` | string | 0.10 | Descripción resumida del rol |

### 2.3 Para Ajustes Finales (Penalizaciones/Boosts)

Estas variables ajustan el score final después del cálculo base.

| Variable | Ajuste | Condición |
|----------|--------|-----------|
| `nivel_seniority` | -0.15 a -0.20 | Mismatch fuerte con nivel ESCO |
| `sector_empresa` | +0.10 | Match exacto con sector ESCO |
| `tiene_gente_cargo` | -0.10 | Mismatch supervisión |
| `licencia_conducir` | +0.05 | Requerida para roles específicos (chofer) |
| `es_tercerizado` | info | Para tracking, no penaliza |

### 2.4 Variables No Usadas en Matching (Solo Analíticas)

| Variable | Razón |
|----------|-------|
| `provincia`, `localidad` | Geográficas, no afectan ocupación |
| `experiencia_min_anios` | Correlaciona con seniority ya capturado |
| `salario_*` | Condicional, no define ocupación |
| `beneficios_*` | Atributos de la oferta, no del rol |
| `idioma_*` | Requisito adicional, no ocupación |

---

## 3. Arquitectura en Cascada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MATCHING v2.0 PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 0: FILTRO DE VALIDEZ                                                  │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Entrada:  Oferta con NLP v10                                                │
│ Proceso:  tipo_oferta ∈ ["demanda_real"]?                                   │
│           calidad_texto != "muy_baja"?                                      │
│ Salida:   Oferta válida → continuar                                         │
│           Oferta inválida → DESCARTADA (status: "filtrada")                 │
│ Config:   config/matching_config.json → filtros.tipo_oferta_validos         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 1: BYPASS DICCIONARIO ARGENTINO                                       │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Entrada:  titulo_limpio                                                     │
│ Proceso:  Buscar match exacto/fuzzy en diccionario_arg_esco (267 términos)  │
│ Salida:   Match encontrado → ESCO directo (score: 0.99, nivel: 1)           │
│           No encontrado → continuar a Nivel 2                               │
│ Config:   Tabla BD: diccionario_arg_esco                                    │
│           config/matching_config.json → bypass_diccionario                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 2: FILTRADO POR CONTEXTO                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Entrada:  area_funcional, nivel_seniority, tiene_gente_cargo                │
│ Proceso:                                                                    │
│   1. Cargar todas las ocupaciones ESCO (3000)                               │
│   2. Si area_funcional != null:                                             │
│      → Filtrar por ISCO válidos para esa área                               │
│      → Ej: "Ventas" → solo ISCO 12xx, 33xx, 52xx                            │
│   3. Si nivel_seniority != null:                                            │
│      → Filtrar por ISCO válidos para ese nivel                              │
│      → Ej: "junior" → excluir ISCO 1xxx                                     │
│   4. Si tiene_gente_cargo == true:                                          │
│      → Preferir ISCO 1xxx, penalizar roles individuales                     │
│   5. Si tiene_gente_cargo == false:                                         │
│      → Excluir ISCO 11xx, 12xx (alta dirección)                             │
│ Salida:   Lista filtrada de ~50-200 candidatos ESCO                         │
│ Config:   config/area_funcional_esco_map.json                               │
│           config/nivel_seniority_esco_map.json                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 3: SCORING MULTICRITERIO                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Entrada:  Candidatos filtrados + datos NLP completos                        │
│ Proceso:                                                                    │
│   1. Determinar pesos dinámicos según riqueza de datos:                     │
│      - Si len(tareas_explicitas) >= 3 → peso_tareas = 0.40                  │
│      - Si len(tecnologias_list) >= 5 → peso_skills = 0.30                   │
│      - Si solo titulo disponible → peso_titulo = 0.85                       │
│   2. Para cada candidato ESCO calcular:                                     │
│      score = (                                                              │
│        peso_titulo * similitud(titulo_limpio, esco_label) +                 │
│        peso_tareas * overlap(tareas_explicitas, esco_tasks) +               │
│        peso_skills * overlap(tecnologias_list + skills_tecnicas, skills) +  │
│        peso_descripcion * similitud_semantica(mision_rol, esco_desc)        │
│      )                                                                      │
│ Salida:   Top 5 candidatos con scores                                       │
│ Config:   config/matching_config.json → pesos_base, pesos_dinamicos         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 4: AJUSTES FINALES                                                    │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Entrada:  Top 5 candidatos con scores base                                  │
│ Proceso:                                                                    │
│   Para cada candidato:                                                      │
│   1. PENALIZACIONES:                                                        │
│      - nivel_seniority mismatch fuerte (junior→gerente): -0.20              │
│      - nivel_seniority mismatch leve (junior→senior): -0.10                 │
│      - sector cruzado (mozo→agricultura): -0.25                             │
│      - tiene_gente_cargo mismatch: -0.10                                    │
│   2. BOOSTS:                                                                │
│      - sector_empresa coincide exacto: +0.10                                │
│      - ISCO en diccionario argentino: +0.05                                 │
│      - licencia_conducir requerida y rol es chofer: +0.05                   │
│ Salida:   Candidato final con score ajustado                                │
│ Config:   config/matching_config.json → penalizaciones, boosts              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ NIVEL 5: DECISIÓN FINAL                                                     │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Entrada:  Mejor candidato con score ajustado                                │
│ Proceso:                                                                    │
│   Si score >= score_minimo_final (0.45):                                    │
│     → MATCH EXITOSO                                                         │
│   Si score < score_minimo_final:                                            │
│     → SIN MATCH (status: "sin_match", mejor_score: X)                       │
│ Salida:   Resultado final con metadata completa                             │
│ Config:   config/matching_config.json → filtros.score_minimo_final          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Mapeos de Contexto

### 4.1 area_funcional → ISCO Válidos

Este mapeo reduce el espacio de búsqueda basándose en el área funcional detectada.

| area_funcional | ISCO Primarios | ISCO Secundarios | Excluir | Notas |
|----------------|----------------|------------------|---------|-------|
| **IT/Sistemas** | 251, 252, 351, 352 | 133, 216 | - | Desarrolladores, analistas, técnicos |
| **Ventas/Comercial** | 122, 332, 524 | 243, 333, 521 | 2, 7, 8, 9 | Vendedores, agentes, directores ventas |
| **Administracion/Finanzas** | 241, 331, 411, 412 | 121, 431 | 5, 7, 8, 9 | Contadores, administrativos, cajeros |
| **RRHH** | 242, 333 | 121 | 5, 7, 8, 9 | Especialistas RRHH, selectores |
| **Operaciones/Logistica** | 132, 432, 933 | 314, 833, 834 | - | Jefes almacén, operarios, choferes |
| **Produccion/Manufactura** | 312, 313, 721-754, 811-818 | 132 | 1, 2, 4 | Técnicos, operarios, supervisores |
| **Marketing** | 122, 243, 264 | 216, 343 | 7, 8, 9 | Marketing, diseño, publicidad |
| **Salud** | 221, 222, 226, 321, 322 | 532 | 7, 8, 9 | Médicos, enfermeros, técnicos |
| **Educacion** | 231, 232, 233, 234, 235 | 263, 341 | 7, 8, 9 | Profesores, capacitadores |
| **Legal** | 261, 335 | 334 | 7, 8, 9 | Abogados, asistentes legales |
| **Atencion al Cliente** | 422, 523, 524 | 333, 962 | 1, 2, 7, 8 | Call center, recepcionistas |
| **Consultoria** | 241, 242, 243, 251, 252 | 121, 122 | 7, 8, 9 | Consultores diversos |
| **Otros** | - | - | - | Sin filtro, usar todos |

### 4.2 nivel_seniority → ISCO Válidos

| nivel_seniority | ISCO Permitidos | ISCO Excluidos | Lógica |
|-----------------|-----------------|----------------|--------|
| **trainee** | 2, 3, 4, 5, 6, 7, 8, 9 | 1 | Sin roles directivos |
| **junior** | 2, 3, 4, 5, 6, 7, 8, 9 | 1 | Sin roles directivos |
| **semisenior** | 1, 2, 3, 4, 5, 6, 7, 8, 9 | - | Cualquier nivel |
| **senior** | 1, 2, 3, 4, 5, 6, 7, 8, 9 | - | Cualquier nivel |
| **lead/manager** | 1, 2, 3 | 4, 5, 6, 7, 8, 9 | Preferir supervisión/dirección |

### 4.3 tiene_gente_cargo → Filtro

| tiene_gente_cargo | Efecto en Filtrado | Efecto en Scoring |
|-------------------|--------------------|--------------------|
| `true` | Boost ISCO 1xxx | +0.10 si candidato es supervisión |
| `false` | Penalizar ISCO 11xx, 12xx | -0.10 si candidato es alta dirección |
| `null` | Sin filtro | Sin ajuste |

### 4.4 Mapeo Cruzado sector_empresa ↔ ISCO

Para detectar "sector cruzado" (penalización -0.25):

| sector_empresa | ISCO Compatibles | Incompatibles (penalizar) |
|----------------|------------------|---------------------------|
| Tecnología | 25x, 35x, 13x | 6xx, 92x |
| Retail | 52x, 42x, 33x | 22x, 23x |
| Salud | 22x, 32x, 53x | 7xx, 8xx |
| Industria | 7xx, 8xx, 31x | 22x, 23x, 26x |
| Agro | 6xx, 92x | 25x, 26x |
| Gastronomía | 512, 513, 941 | 25x, 22x |
| Finanzas | 24x, 33x, 41x | 6xx, 7xx, 8xx |

---

## 5. Configuración JSON

### 5.1 config/matching_config.json (Expandido)

```json
{
  "version": "2.0.0",
  "descripcion": "Configuración del pipeline de matching ESCO v2",

  "filtros": {
    "tipo_oferta_validos": ["demanda_real"],
    "calidad_texto_minima": ["alta", "media", "baja"],
    "score_minimo_final": 0.45,
    "usar_filtro_area": true,
    "usar_filtro_seniority": true,
    "usar_filtro_supervision": true
  },

  "bypass_diccionario": {
    "habilitado": true,
    "score_asignado": 0.99,
    "tabla": "diccionario_arg_esco",
    "usar_fuzzy": true,
    "umbral_fuzzy": 0.85
  },

  "pesos_base": {
    "titulo": 0.40,
    "tareas": 0.30,
    "skills": 0.20,
    "descripcion": 0.10
  },

  "pesos_dinamicos": {
    "tareas_ricas": {
      "condicion": "len(tareas_explicitas) >= 3",
      "pesos": {
        "titulo": 0.30,
        "tareas": 0.40,
        "skills": 0.20,
        "descripcion": 0.10
      }
    },
    "skills_ricas": {
      "condicion": "len(tecnologias_list) >= 5",
      "pesos": {
        "titulo": 0.35,
        "tareas": 0.25,
        "skills": 0.30,
        "descripcion": 0.10
      }
    },
    "solo_titulo": {
      "condicion": "len(tareas_explicitas) == 0 and len(skills_tecnicas_list) == 0",
      "pesos": {
        "titulo": 0.85,
        "tareas": 0.00,
        "skills": 0.00,
        "descripcion": 0.15
      }
    },
    "datos_completos": {
      "condicion": "len(tareas_explicitas) >= 3 and len(tecnologias_list) >= 3",
      "pesos": {
        "titulo": 0.25,
        "tareas": 0.35,
        "skills": 0.30,
        "descripcion": 0.10
      }
    }
  },

  "penalizaciones": {
    "seniority_mismatch_fuerte": {
      "valor": -0.20,
      "descripcion": "junior/trainee matched a gerente/director",
      "pares": [
        ["trainee", "1"],
        ["junior", "11"],
        ["junior", "12"]
      ]
    },
    "seniority_mismatch_leve": {
      "valor": -0.10,
      "descripcion": "junior matched a senior sin supervisión",
      "pares": [
        ["trainee", "2"],
        ["junior", "13"]
      ]
    },
    "sector_cruzado": {
      "valor": -0.25,
      "descripcion": "Sector empresa incompatible con ocupación",
      "usar_mapeo": "config/sector_isco_compatibilidad.json"
    },
    "gente_cargo_mismatch": {
      "valor": -0.10,
      "descripcion": "tiene_gente_cargo=false pero matched a rol de supervisión"
    }
  },

  "boosts": {
    "sector_exacto": {
      "valor": 0.10,
      "descripcion": "sector_empresa coincide exactamente con sector ESCO"
    },
    "diccionario_isco_match": {
      "valor": 0.05,
      "descripcion": "ISCO del candidato está en diccionario argentino"
    },
    "licencia_conducir_match": {
      "valor": 0.05,
      "descripcion": "licencia_conducir=true y rol es chofer/conductor"
    }
  },

  "similitud": {
    "algoritmo_titulo": "fuzzy_ratio",
    "algoritmo_tareas": "jaccard_overlap",
    "algoritmo_skills": "jaccard_overlap",
    "algoritmo_descripcion": "tfidf_cosine",
    "usar_embeddings": false,
    "modelo_embeddings": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
  },

  "output": {
    "incluir_alternativas": true,
    "max_alternativas": 3,
    "incluir_scores_componentes": true,
    "incluir_metadata_debug": false
  }
}
```

### 5.2 config/area_funcional_esco_map.json

```json
{
  "version": "1.0.0",
  "descripcion": "Mapeo de area_funcional NLP a códigos ISCO válidos",
  "fecha_actualizacion": "2025-12-10",

  "mappings": {
    "IT/Sistemas": {
      "descripcion": "Tecnología de la información y sistemas",
      "isco_primarios": ["251", "252", "351", "352"],
      "isco_secundarios": ["133", "216", "243"],
      "excluir": [],
      "notas": "Incluye desarrollo, análisis, soporte técnico, dirección IT"
    },

    "Ventas/Comercial": {
      "descripcion": "Ventas, comercial y desarrollo de negocios",
      "isco_primarios": ["122", "332", "524", "521"],
      "isco_secundarios": ["243", "333", "523"],
      "excluir": ["2", "7", "8", "9"],
      "notas": "Excluye profesionales técnicos y operarios"
    },

    "Administracion/Finanzas": {
      "descripcion": "Administración, contabilidad y finanzas",
      "isco_primarios": ["241", "331", "411", "412", "431"],
      "isco_secundarios": ["121", "334"],
      "excluir": ["5", "6", "7", "8", "9"],
      "notas": "Contadores, administrativos, cajeros, auxiliares"
    },

    "RRHH": {
      "descripcion": "Recursos humanos y gestión de personas",
      "isco_primarios": ["242", "333"],
      "isco_secundarios": ["121", "441"],
      "excluir": ["5", "6", "7", "8", "9"],
      "notas": "Analistas RRHH, selectores, capacitadores"
    },

    "Operaciones/Logistica": {
      "descripcion": "Operaciones, logística y supply chain",
      "isco_primarios": ["132", "432", "933", "834", "833"],
      "isco_secundarios": ["314", "832", "931"],
      "excluir": [],
      "notas": "Jefes de almacén, operarios, choferes, despachantes"
    },

    "Produccion/Manufactura": {
      "descripcion": "Producción industrial y manufactura",
      "isco_primarios": ["312", "313", "721", "722", "723", "741", "751", "811", "812", "813"],
      "isco_secundarios": ["132", "314"],
      "excluir": ["1", "2", "4"],
      "notas": "Técnicos, operarios calificados, maquinistas"
    },

    "Marketing": {
      "descripcion": "Marketing, publicidad y comunicación",
      "isco_primarios": ["122", "243", "264"],
      "isco_secundarios": ["216", "343", "265"],
      "excluir": ["7", "8", "9"],
      "notas": "Marketing digital, diseñadores, community managers"
    },

    "Salud": {
      "descripcion": "Salud y servicios médicos",
      "isco_primarios": ["221", "222", "226", "321", "322", "325"],
      "isco_secundarios": ["532", "134"],
      "excluir": ["7", "8", "9"],
      "notas": "Médicos, enfermeros, técnicos de salud"
    },

    "Educacion": {
      "descripcion": "Educación y capacitación",
      "isco_primarios": ["231", "232", "233", "234", "235"],
      "isco_secundarios": ["263", "341", "531"],
      "excluir": ["7", "8", "9"],
      "notas": "Profesores, instructores, capacitadores"
    },

    "Legal": {
      "descripcion": "Servicios legales y jurídicos",
      "isco_primarios": ["261", "335"],
      "isco_secundarios": ["334", "411"],
      "excluir": ["5", "6", "7", "8", "9"],
      "notas": "Abogados, escribanos, asistentes legales"
    },

    "Atencion al Cliente": {
      "descripcion": "Atención al cliente y call center",
      "isco_primarios": ["422", "523", "524"],
      "isco_secundarios": ["333", "962", "521"],
      "excluir": ["1", "2", "7", "8"],
      "notas": "Operadores call center, recepcionistas, vendedores"
    },

    "Consultoria": {
      "descripcion": "Consultoría y servicios profesionales",
      "isco_primarios": ["241", "242", "243", "251", "252"],
      "isco_secundarios": ["121", "122", "263"],
      "excluir": ["6", "7", "8", "9"],
      "notas": "Consultores de negocio, IT, RRHH, finanzas"
    },

    "Otros": {
      "descripcion": "Sin área específica o no clasificable",
      "isco_primarios": [],
      "isco_secundarios": [],
      "excluir": [],
      "notas": "Sin filtro - usar todas las ocupaciones"
    }
  }
}
```

### 5.3 config/nivel_seniority_esco_map.json

```json
{
  "version": "1.0.0",
  "descripcion": "Mapeo de nivel_seniority NLP a códigos ISCO válidos",
  "fecha_actualizacion": "2025-12-10",

  "mappings": {
    "trainee": {
      "descripcion": "Pasante, practicante, sin experiencia",
      "permitir": ["2", "3", "4", "5", "6", "7", "8", "9"],
      "excluir": ["1"],
      "notas": "No puede ser directivo ni gerente"
    },

    "junior": {
      "descripcion": "0-2 años de experiencia",
      "permitir": ["2", "3", "4", "5", "6", "7", "8", "9"],
      "excluir": ["1"],
      "notas": "No puede ser directivo ni gerente"
    },

    "semisenior": {
      "descripcion": "2-5 años de experiencia",
      "permitir": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
      "excluir": [],
      "notas": "Puede ser cualquier nivel, incluso supervisor"
    },

    "senior": {
      "descripcion": "5+ años de experiencia",
      "permitir": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
      "excluir": [],
      "notas": "Puede ser cualquier nivel"
    },

    "lead/manager": {
      "descripcion": "Líder técnico, supervisor, gerente",
      "permitir": ["1", "2", "3"],
      "excluir": ["4", "5", "6", "7", "8", "9"],
      "boost_isco": ["1"],
      "notas": "Preferir roles de supervisión y dirección"
    }
  },

  "matriz_penalizacion": {
    "descripcion": "Penalizaciones por mismatch seniority → ISCO",
    "pares": {
      "trainee_a_director": {
        "seniority": ["trainee"],
        "isco": ["11", "12"],
        "penalizacion": -0.25
      },
      "junior_a_gerente": {
        "seniority": ["junior"],
        "isco": ["11", "12", "13"],
        "penalizacion": -0.20
      },
      "manager_a_operario": {
        "seniority": ["lead/manager"],
        "isco": ["7", "8", "9"],
        "penalizacion": -0.15
      }
    }
  }
}
```

### 5.4 config/sector_isco_compatibilidad.json

```json
{
  "version": "1.0.0",
  "descripcion": "Compatibilidad entre sector_empresa e ISCO para detectar sector cruzado",

  "sectores": {
    "Tecnologia": {
      "isco_compatibles": ["13", "21", "25", "35"],
      "isco_incompatibles": ["6", "92", "93"],
      "penalizacion_cruzado": -0.25
    },

    "Retail": {
      "isco_compatibles": ["14", "33", "42", "52"],
      "isco_incompatibles": ["22", "23", "25"],
      "penalizacion_cruzado": -0.20
    },

    "Salud": {
      "isco_compatibles": ["13", "22", "32", "53"],
      "isco_incompatibles": ["7", "8", "6"],
      "penalizacion_cruzado": -0.25
    },

    "Industria": {
      "isco_compatibles": ["13", "31", "7", "8"],
      "isco_incompatibles": ["22", "23", "26"],
      "penalizacion_cruzado": -0.20
    },

    "Agro": {
      "isco_compatibles": ["13", "6", "83", "92"],
      "isco_incompatibles": ["25", "26", "24"],
      "penalizacion_cruzado": -0.25
    },

    "Gastronomia": {
      "isco_compatibles": ["14", "34", "51", "94"],
      "isco_incompatibles": ["25", "22", "26"],
      "penalizacion_cruzado": -0.20
    },

    "Finanzas": {
      "isco_compatibles": ["12", "24", "33", "41"],
      "isco_incompatibles": ["6", "7", "8", "9"],
      "penalizacion_cruzado": -0.25
    },

    "Construccion": {
      "isco_compatibles": ["13", "31", "71", "72", "93"],
      "isco_incompatibles": ["22", "25", "26"],
      "penalizacion_cruzado": -0.20
    }
  }
}
```

---

## 6. Pseudocódigo del Pipeline

```python
# database/match_ofertas_v2.py

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# ESTRUCTURAS DE DATOS
# ============================================================================

class MatchStatus(Enum):
    SUCCESS = "success"
    FILTERED = "filtered"
    NO_MATCH = "no_match"
    BYPASS = "bypass"

@dataclass
class MatchResult:
    status: MatchStatus
    esco_uri: Optional[str]
    esco_label: Optional[str]
    isco_code: Optional[str]
    score: float
    score_components: Dict[str, float]
    nivel_match: int
    metodo: str
    candidatos_considerados: int
    alternativas: List[Dict]
    metadata: Dict

# ============================================================================
# CARGA DE CONFIGURACIÓN
# ============================================================================

def load_configs() -> Dict:
    """Carga todos los archivos de configuración."""
    config_dir = Path("config")

    return {
        "matching": json.load(open(config_dir / "matching_config.json")),
        "area_map": json.load(open(config_dir / "area_funcional_esco_map.json")),
        "seniority_map": json.load(open(config_dir / "nivel_seniority_esco_map.json")),
        "sector_compat": json.load(open(config_dir / "sector_isco_compatibilidad.json"))
    }

# ============================================================================
# NIVEL 0: FILTRO DE VALIDEZ
# ============================================================================

def nivel_0_filtro_validez(oferta_nlp: Dict, config: Dict) -> Tuple[bool, str]:
    """
    Verifica si la oferta es válida para matching.

    Returns:
        (es_valida, razon_rechazo)
    """
    filtros = config["matching"]["filtros"]

    # Verificar tipo_oferta
    tipo_oferta = oferta_nlp.get("tipo_oferta")
    if tipo_oferta not in filtros["tipo_oferta_validos"]:
        return False, f"tipo_oferta_invalido: {tipo_oferta}"

    # Verificar calidad_texto
    calidad = oferta_nlp.get("calidad_texto")
    if calidad and calidad not in filtros["calidad_texto_minima"]:
        return False, f"calidad_texto_baja: {calidad}"

    return True, ""

# ============================================================================
# NIVEL 1: BYPASS DICCIONARIO ARGENTINO
# ============================================================================

def nivel_1_bypass_diccionario(titulo_limpio: str, config: Dict, db_conn) -> Optional[Dict]:
    """
    Busca match directo en diccionario argentino.

    Returns:
        Dict con esco_uri y score si hay match, None si no.
    """
    bypass_config = config["matching"]["bypass_diccionario"]

    if not bypass_config["habilitado"]:
        return None

    # Búsqueda exacta
    cursor = db_conn.execute("""
        SELECT esco_uri, esco_label, isco_code
        FROM diccionario_arg_esco
        WHERE LOWER(termino_arg) = LOWER(?)
    """, (titulo_limpio,))

    row = cursor.fetchone()
    if row:
        return {
            "esco_uri": row["esco_uri"],
            "esco_label": row["esco_label"],
            "isco_code": row["isco_code"],
            "score": bypass_config["score_asignado"],
            "metodo": "diccionario_exacto"
        }

    # Búsqueda fuzzy si está habilitada
    if bypass_config["usar_fuzzy"]:
        cursor = db_conn.execute("SELECT termino_arg, esco_uri, esco_label, isco_code FROM diccionario_arg_esco")

        from rapidfuzz import fuzz
        mejor_match = None
        mejor_score = 0

        for row in cursor:
            ratio = fuzz.ratio(titulo_limpio.lower(), row["termino_arg"].lower()) / 100
            if ratio > mejor_score and ratio >= bypass_config["umbral_fuzzy"]:
                mejor_score = ratio
                mejor_match = row

        if mejor_match:
            return {
                "esco_uri": mejor_match["esco_uri"],
                "esco_label": mejor_match["esco_label"],
                "isco_code": mejor_match["isco_code"],
                "score": bypass_config["score_asignado"] * mejor_score,
                "metodo": "diccionario_fuzzy"
            }

    return None

# ============================================================================
# NIVEL 2: FILTRADO POR CONTEXTO
# ============================================================================

def nivel_2_filtrar_por_contexto(
    candidatos: List[Dict],
    oferta_nlp: Dict,
    config: Dict
) -> List[Dict]:
    """
    Filtra candidatos ESCO basándose en contexto NLP.
    """
    filtros = config["matching"]["filtros"]
    area_map = config["area_map"]["mappings"]
    seniority_map = config["seniority_map"]["mappings"]

    resultado = candidatos.copy()

    # Filtrar por area_funcional
    if filtros["usar_filtro_area"]:
        area = oferta_nlp.get("area_funcional")
        if area and area in area_map:
            mapeo = area_map[area]
            isco_validos = set(mapeo["isco_primarios"] + mapeo["isco_secundarios"])
            isco_excluir = set(mapeo.get("excluir", []))

            if isco_validos:  # Si hay ISCOs definidos, filtrar
                resultado = [
                    c for c in resultado
                    if any(c["isco_code"].startswith(isco) for isco in isco_validos)
                    and not any(c["isco_code"].startswith(ex) for ex in isco_excluir)
                ]

    # Filtrar por nivel_seniority
    if filtros["usar_filtro_seniority"]:
        seniority = oferta_nlp.get("nivel_seniority")
        if seniority and seniority in seniority_map:
            mapeo = seniority_map[seniority]
            isco_permitir = set(mapeo["permitir"])
            isco_excluir = set(mapeo["excluir"])

            resultado = [
                c for c in resultado
                if any(c["isco_code"].startswith(p) for p in isco_permitir)
                and not any(c["isco_code"].startswith(ex) for ex in isco_excluir)
            ]

    # Filtrar por tiene_gente_cargo
    if filtros["usar_filtro_supervision"]:
        tiene_gente = oferta_nlp.get("tiene_gente_cargo")
        if tiene_gente is False:
            # Excluir alta dirección
            resultado = [
                c for c in resultado
                if not c["isco_code"].startswith("11") and not c["isco_code"].startswith("12")
            ]

    return resultado

# ============================================================================
# NIVEL 3: SCORING MULTICRITERIO
# ============================================================================

def calcular_pesos_dinamicos(oferta_nlp: Dict, config: Dict) -> Dict[str, float]:
    """
    Calcula pesos dinámicos según riqueza de datos.
    """
    pesos_base = config["matching"]["pesos_base"]
    pesos_dinamicos = config["matching"]["pesos_dinamicos"]

    tareas = oferta_nlp.get("tareas_explicitas") or []
    skills = oferta_nlp.get("tecnologias_list") or []
    skills_tec = oferta_nlp.get("skills_tecnicas_list") or []

    # Evaluar condiciones en orden de prioridad
    if len(tareas) >= 3 and len(skills + skills_tec) >= 3:
        return pesos_dinamicos["datos_completos"]["pesos"]

    if len(tareas) >= 3:
        return pesos_dinamicos["tareas_ricas"]["pesos"]

    if len(skills + skills_tec) >= 5:
        return pesos_dinamicos["skills_ricas"]["pesos"]

    if len(tareas) == 0 and len(skills_tec) == 0:
        return pesos_dinamicos["solo_titulo"]["pesos"]

    return pesos_base

def calcular_similitud_titulo(titulo_oferta: str, esco_label: str) -> float:
    """Calcula similitud entre título de oferta y label ESCO."""
    from rapidfuzz import fuzz
    return fuzz.ratio(titulo_oferta.lower(), esco_label.lower()) / 100

def calcular_overlap_listas(lista_a: List[str], lista_b: List[str]) -> float:
    """Calcula Jaccard overlap entre dos listas."""
    if not lista_a or not lista_b:
        return 0.0

    set_a = set(item.lower() for item in lista_a)
    set_b = set(item.lower() for item in lista_b)

    interseccion = len(set_a & set_b)
    union = len(set_a | set_b)

    return interseccion / union if union > 0 else 0.0

def nivel_3_scoring(
    candidatos: List[Dict],
    oferta_nlp: Dict,
    config: Dict
) -> List[Tuple[Dict, float, Dict]]:
    """
    Calcula scores para cada candidato.

    Returns:
        Lista de (candidato, score_total, score_components)
    """
    pesos = calcular_pesos_dinamicos(oferta_nlp, config)

    titulo = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo") or ""
    tareas = oferta_nlp.get("tareas_explicitas") or []
    skills = (oferta_nlp.get("tecnologias_list") or []) + (oferta_nlp.get("skills_tecnicas_list") or [])
    mision = oferta_nlp.get("mision_rol") or ""

    resultados = []

    for candidato in candidatos:
        # Score por título
        score_titulo = calcular_similitud_titulo(titulo, candidato["label"])

        # Score por tareas
        esco_tasks = candidato.get("tasks") or []
        score_tareas = calcular_overlap_listas(tareas, esco_tasks)

        # Score por skills
        esco_skills = candidato.get("skills") or []
        score_skills = calcular_overlap_listas(skills, esco_skills)

        # Score por descripción (similitud semántica simplificada)
        esco_desc = candidato.get("description") or ""
        score_desc = calcular_similitud_titulo(mision, esco_desc) if mision else 0.0

        # Score total ponderado
        score_total = (
            pesos["titulo"] * score_titulo +
            pesos["tareas"] * score_tareas +
            pesos["skills"] * score_skills +
            pesos["descripcion"] * score_desc
        )

        score_components = {
            "titulo": score_titulo,
            "tareas": score_tareas,
            "skills": score_skills,
            "descripcion": score_desc,
            "pesos_usados": pesos
        }

        resultados.append((candidato, score_total, score_components))

    # Ordenar por score descendente
    resultados.sort(key=lambda x: x[1], reverse=True)

    return resultados[:5]  # Top 5

# ============================================================================
# NIVEL 4: AJUSTES FINALES
# ============================================================================

def nivel_4_ajustes(
    top_candidatos: List[Tuple[Dict, float, Dict]],
    oferta_nlp: Dict,
    config: Dict
) -> List[Tuple[Dict, float, Dict]]:
    """
    Aplica penalizaciones y boosts al score.
    """
    penalizaciones = config["matching"]["penalizaciones"]
    boosts = config["matching"]["boosts"]
    seniority_map = config["seniority_map"]
    sector_compat = config["sector_compat"]

    seniority = oferta_nlp.get("nivel_seniority")
    tiene_gente = oferta_nlp.get("tiene_gente_cargo")
    sector = oferta_nlp.get("sector_empresa")

    resultados_ajustados = []

    for candidato, score, components in top_candidatos:
        ajuste = 0.0
        ajustes_aplicados = []

        isco = candidato["isco_code"]

        # Penalización por seniority mismatch
        if seniority:
            matriz = seniority_map.get("matriz_penalizacion", {}).get("pares", {})
            for nombre, regla in matriz.items():
                if seniority in regla["seniority"]:
                    if any(isco.startswith(i) for i in regla["isco"]):
                        ajuste += regla["penalizacion"]
                        ajustes_aplicados.append(f"penalizacion_{nombre}: {regla['penalizacion']}")

        # Penalización por tiene_gente_cargo mismatch
        if tiene_gente is False and isco.startswith(("11", "12")):
            ajuste += penalizaciones["gente_cargo_mismatch"]["valor"]
            ajustes_aplicados.append(f"gente_cargo_mismatch: {penalizaciones['gente_cargo_mismatch']['valor']}")

        # Penalización por sector cruzado
        if sector and sector in sector_compat.get("sectores", {}):
            sector_info = sector_compat["sectores"][sector]
            if any(isco.startswith(i) for i in sector_info.get("isco_incompatibles", [])):
                ajuste += sector_info["penalizacion_cruzado"]
                ajustes_aplicados.append(f"sector_cruzado: {sector_info['penalizacion_cruzado']}")

        # Boost por sector exacto
        if sector and sector in sector_compat.get("sectores", {}):
            sector_info = sector_compat["sectores"][sector]
            if any(isco.startswith(i) for i in sector_info.get("isco_compatibles", [])):
                ajuste += boosts["sector_exacto"]["valor"]
                ajustes_aplicados.append(f"sector_exacto: +{boosts['sector_exacto']['valor']}")

        # Boost por tiene_gente_cargo match
        if tiene_gente is True and isco.startswith("1"):
            ajuste += 0.05
            ajustes_aplicados.append("gente_cargo_match: +0.05")

        score_final = max(0.0, min(1.0, score + ajuste))

        components["ajustes"] = ajustes_aplicados
        components["score_base"] = score
        components["score_ajustado"] = score_final

        resultados_ajustados.append((candidato, score_final, components))

    # Reordenar por score ajustado
    resultados_ajustados.sort(key=lambda x: x[1], reverse=True)

    return resultados_ajustados

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def match_oferta_v2(oferta_nlp: Dict, db_conn, config: Dict = None) -> MatchResult:
    """
    Pipeline completo de matching v2.

    Args:
        oferta_nlp: Diccionario con todos los campos NLP v10
        db_conn: Conexión a la base de datos
        config: Configuración (se carga automáticamente si es None)

    Returns:
        MatchResult con todos los detalles del matching
    """
    if config is None:
        config = load_configs()

    # -------------------------------------------------------------------------
    # NIVEL 0: Filtro de validez
    # -------------------------------------------------------------------------
    es_valida, razon = nivel_0_filtro_validez(oferta_nlp, config)
    if not es_valida:
        return MatchResult(
            status=MatchStatus.FILTERED,
            esco_uri=None,
            esco_label=None,
            isco_code=None,
            score=0.0,
            score_components={},
            nivel_match=0,
            metodo="filtrado",
            candidatos_considerados=0,
            alternativas=[],
            metadata={"razon_filtrado": razon}
        )

    # -------------------------------------------------------------------------
    # NIVEL 1: Bypass diccionario
    # -------------------------------------------------------------------------
    titulo_limpio = oferta_nlp.get("titulo_limpio") or oferta_nlp.get("titulo")
    bypass = nivel_1_bypass_diccionario(titulo_limpio, config, db_conn)

    if bypass:
        return MatchResult(
            status=MatchStatus.BYPASS,
            esco_uri=bypass["esco_uri"],
            esco_label=bypass["esco_label"],
            isco_code=bypass["isco_code"],
            score=bypass["score"],
            score_components={"bypass": 1.0},
            nivel_match=1,
            metodo=bypass["metodo"],
            candidatos_considerados=1,
            alternativas=[],
            metadata={"titulo_buscado": titulo_limpio}
        )

    # -------------------------------------------------------------------------
    # NIVEL 2: Filtrar candidatos
    # -------------------------------------------------------------------------
    # Cargar todas las ocupaciones ESCO
    cursor = db_conn.execute("""
        SELECT uri as esco_uri, label, isco_code, description, tasks, skills
        FROM esco_occupations
    """)
    todos_candidatos = [dict(row) for row in cursor]

    candidatos_filtrados = nivel_2_filtrar_por_contexto(todos_candidatos, oferta_nlp, config)

    if not candidatos_filtrados:
        # Si el filtro es muy restrictivo, usar todos
        candidatos_filtrados = todos_candidatos

    # -------------------------------------------------------------------------
    # NIVEL 3: Scoring
    # -------------------------------------------------------------------------
    top_5 = nivel_3_scoring(candidatos_filtrados, oferta_nlp, config)

    if not top_5:
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            esco_uri=None,
            esco_label=None,
            isco_code=None,
            score=0.0,
            score_components={},
            nivel_match=3,
            metodo="sin_candidatos",
            candidatos_considerados=len(candidatos_filtrados),
            alternativas=[],
            metadata={}
        )

    # -------------------------------------------------------------------------
    # NIVEL 4: Ajustes finales
    # -------------------------------------------------------------------------
    top_ajustados = nivel_4_ajustes(top_5, oferta_nlp, config)

    mejor = top_ajustados[0]
    candidato, score_final, components = mejor

    # -------------------------------------------------------------------------
    # NIVEL 5: Decisión final
    # -------------------------------------------------------------------------
    score_minimo = config["matching"]["filtros"]["score_minimo_final"]

    if score_final < score_minimo:
        return MatchResult(
            status=MatchStatus.NO_MATCH,
            esco_uri=candidato["esco_uri"],
            esco_label=candidato["label"],
            isco_code=candidato["isco_code"],
            score=score_final,
            score_components=components,
            nivel_match=5,
            metodo="score_bajo",
            candidatos_considerados=len(candidatos_filtrados),
            alternativas=[
                {"esco_uri": c["esco_uri"], "label": c["label"], "score": s}
                for c, s, _ in top_ajustados[1:4]
            ],
            metadata={"score_minimo_requerido": score_minimo}
        )

    return MatchResult(
        status=MatchStatus.SUCCESS,
        esco_uri=candidato["esco_uri"],
        esco_label=candidato["label"],
        isco_code=candidato["isco_code"],
        score=score_final,
        score_components=components,
        nivel_match=5,
        metodo="cascada_v2",
        candidatos_considerados=len(candidatos_filtrados),
        alternativas=[
            {"esco_uri": c["esco_uri"], "label": c["label"], "score": s}
            for c, s, _ in top_ajustados[1:4]
        ],
        metadata={
            "filtros_aplicados": {
                "area_funcional": oferta_nlp.get("area_funcional"),
                "nivel_seniority": oferta_nlp.get("nivel_seniority"),
                "tiene_gente_cargo": oferta_nlp.get("tiene_gente_cargo")
            }
        }
    )
```

---

## 7. Plan de Implementación

### Fase 1: Configuración (Día 1)

| Tarea | Archivo | Prioridad |
|-------|---------|-----------|
| Crear estructura config/ | `config/` | Alta |
| Crear matching_config.json | `config/matching_config.json` | Alta |
| Crear area_funcional_esco_map.json | `config/area_funcional_esco_map.json` | Alta |
| Crear nivel_seniority_esco_map.json | `config/nivel_seniority_esco_map.json` | Alta |
| Crear sector_isco_compatibilidad.json | `config/sector_isco_compatibilidad.json` | Media |

### Fase 2: Implementación Core (Día 2-3)

| Tarea | Archivo | Prioridad |
|-------|---------|-----------|
| Implementar carga de configs | `database/match_ofertas_v2.py` | Alta |
| Implementar Nivel 0 (filtro validez) | `database/match_ofertas_v2.py` | Alta |
| Implementar Nivel 1 (bypass diccionario) | `database/match_ofertas_v2.py` | Alta |
| Implementar Nivel 2 (filtrado contexto) | `database/match_ofertas_v2.py` | Alta |
| Implementar Nivel 3 (scoring) | `database/match_ofertas_v2.py` | Alta |
| Implementar Nivel 4 (ajustes) | `database/match_ofertas_v2.py` | Alta |

### Fase 3: Testing (Día 4)

| Tarea | Archivo | Prioridad |
|-------|---------|-----------|
| Tests unitarios por nivel | `tests/matching/test_match_v2.py` | Alta |
| Ejecutar contra Gold Set (49 casos) | Script de validación | Alta |
| Comparar v8.4 vs v2 | Reporte comparativo | Alta |
| Identificar regresiones | Análisis manual | Alta |

### Fase 4: Iteración (Día 5+)

| Tarea | Condición |
|-------|-----------|
| Ajustar pesos en config | Si precisión < 95% |
| Expandir mapeos área/seniority | Si hay áreas sin cubrir |
| Agregar términos a diccionario | Si hay títulos comunes fallando |
| Ajustar umbrales | Si hay muchos falsos positivos/negativos |

---

## 8. Métricas de Éxito

### 8.1 Métricas Primarias

| Métrica | Actual (v8.4) | Objetivo (v2) | Cómo Medir |
|---------|---------------|---------------|------------|
| **Precisión Gold Set** | 98% (48/49) | 100% (49/49) | `test_gold_set_manual.py` |
| **Recall** | ~85% | >95% | Ofertas con match / Total ofertas válidas |
| **F1-Score** | ~90% | >97% | 2 * (P * R) / (P + R) |

### 8.2 Métricas Secundarias

| Métrica | Objetivo | Cómo Medir |
|---------|----------|------------|
| **Uso de diccionario** | Tracking | % de matches por Nivel 1 |
| **Uso de filtros contexto** | >80% | % de ofertas con area_funcional usado |
| **Score promedio** | >0.65 | Promedio de scores finales |
| **Candidatos promedio considerados** | <200 | Promedio después de Nivel 2 |

### 8.3 Dashboard de Métricas

```sql
-- Query para métricas de matching v2
SELECT
    COUNT(*) as total_ofertas,
    SUM(CASE WHEN match_status = 'success' THEN 1 ELSE 0 END) as matches_exitosos,
    SUM(CASE WHEN match_status = 'filtered' THEN 1 ELSE 0 END) as filtradas,
    SUM(CASE WHEN match_status = 'no_match' THEN 1 ELSE 0 END) as sin_match,
    SUM(CASE WHEN match_status = 'bypass' THEN 1 ELSE 0 END) as bypass_diccionario,
    AVG(score) as score_promedio,
    AVG(candidatos_considerados) as candidatos_promedio
FROM matching_results_v2
WHERE fecha >= DATE('now', '-7 days');
```

---

## 9. Migración desde v8.4

### 9.1 Compatibilidad

- v2 puede correr en paralelo con v8.4
- Ambos guardan resultados en tablas separadas
- Comparación A/B posible

### 9.2 Pasos de Migración

1. Implementar v2 sin tocar v8.4
2. Ejecutar ambos contra mismas ofertas
3. Comparar resultados
4. Cuando v2 >= v8.4 en todas las métricas:
   - Deprecar v8.4
   - Migrar tabla de resultados
   - Actualizar pipelines dependientes

### 9.3 Rollback

Si v2 presenta problemas en producción:
1. Reactivar v8.4 (sin cambios)
2. Marcar ofertas procesadas con v2 como "pendiente_revision"
3. Analizar casos problemáticos
4. Iterar v2 y re-deployar

---

## 10. Referencias

- [ESCO Classification](https://esco.ec.europa.eu/en/classification)
- [ISCO-08 Structure](https://www.ilo.org/public/english/bureau/stat/isco/isco08/)
- [NLP Schema v5](./NLP_SCHEMA_V5.md)
- [Gold Set Manual](../database/gold_set_manual_v2.json)
- [Diccionario Argentino ESCO](../database/diccionario_arg_esco.sql)

---

> **Próximos pasos:** Crear archivos de configuración JSON y comenzar implementación.
