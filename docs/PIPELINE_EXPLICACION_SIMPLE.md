# Pipeline MOL - Explicación Simple

## Resumen en una oración

**Scrapeamos ofertas de empleo → Limpiamos el texto → Extraemos información estructurada con IA → Clasificamos la ocupación según estándar internacional ESCO**

---

## Las 4 Etapas del Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  SCRAPING   │ → │  LIMPIEZA   │ → │     NLP     │ → │  MATCHING   │
│             │    │   TITULO    │    │             │    │    ESCO     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
   Portal web       Quitar ruido      Extraer datos      Clasificar
   → Base datos     geográfico        estructurados      ocupación
```

---

## Etapa 1: SCRAPING

**¿Qué hace?** Descarga ofertas de portales de empleo (Bumeran, ZonaJobs, etc.)

**Ejemplo real:**
```
Del portal Bumeran descargamos:

ID: 1118028201
Título: "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10 de 10 a 1130 NUEVA Suc. SAN ISIDRO"
Empresa: "CONA CONSULTORES EN RRHH"
Ubicación: "Tortuguitas, Buenos Aires"
Descripción: "Buscamos OPERARIOS DE PRODUCCIÓN ALIMENTICIA con experiencia..."
```

**Problema:** El título tiene mucho "ruido" (códigos internos, fechas, sucursales)

---

## Etapa 2: LIMPIEZA DE TÍTULO

**¿Qué hace?** Elimina el ruido del título para dejar solo la ocupación

**Reglas de limpieza (ejemplos):**

| Patrón | Ejemplo | Se elimina |
|--------|---------|------------|
| Códigos al inicio | `671SI Operarios...` | `671SI` |
| Fechas/horarios | `- pres 31/10 de 10 a 1130` | todo |
| Sucursales | `NUEVA Suc. SAN ISIDRO` | todo |
| Abreviaturas | `ind.` → `industria` | se expande |
| Prefijos genéricos | `Búsqueda Laboral:` | se elimina |
| Ubicaciones al final | `– Vicente López` | se elimina |

**Ejemplo real:**

```
ANTES:  "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10 de 10 a 1130 NUEVA Suc. SAN ISIDRO"

DESPUÉS: "Operarios industria ALIMENTICIA"
```

**Otro ejemplo:**
```
ANTES:  "Búsqueda Laboral: Modelista – Vicente López (Florida Oeste)"

DESPUÉS: "Modelista"
```

---

## Etapa 3: EXTRACCIÓN NLP (Procesamiento de Lenguaje Natural)

**¿Qué hace?** Lee la descripción completa y extrae ~50 campos estructurados usando IA (modelo Qwen2.5)

**Campos que extrae:**

| Categoría | Campos |
|-----------|--------|
| **Ubicación** | provincia, localidad, modalidad (remoto/presencial/híbrido) |
| **Requisitos** | experiencia_min/max, nivel_educativo, idiomas, licencia_conducir |
| **Persona** | requisito_sexo, requisito_edad, carrera_especifica |
| **Trabajo** | jornada_laboral, turnos_rotativos, tiene_gente_cargo |
| **Salario** | salario_min/max, moneda, beneficios |
| **Skills** | skills_tecnicas, soft_skills, certificaciones |
| **Tareas** | tareas_explicitas (lista de responsabilidades) |

**Ejemplo real - Oferta Farmacéutico:**

```
ENTRADA (descripción):
"Somos Farmacity... Estamos en búsqueda de farmacéuticos/as en Rio Cuarto...
dispensa de medicamentos, control y orden de stock, participación en
campañas de vacunación..."

SALIDA NLP:
- provincia: "Córdoba"
- localidad: "Río Cuarto"
- sector_empresa: "Salud/Farmaceutica"
- nivel_educativo: "universitario"
- modalidad: "presencial"
- tareas_explicitas: "dispensa de medicamentos; control y orden de stock;
                      participación en campañas de vacunación"
- skills_tecnicas: "stock"
- area_funcional: "Salud"
```

---

## Etapa 4: MATCHING ESCO

**¿Qué hace?** Clasifica cada oferta según la taxonomía europea de ocupaciones (ESCO/ISCO)

**¿Qué es ESCO?** Es un estándar internacional con ~3,000 ocupaciones codificadas. Ejemplo:
- Código 5223 = "Vendedor de tienda"
- Código 2262 = "Farmacéutico"
- Código 7511 = "Operario de procesamiento de alimentos"

**¿Cómo funciona el matching?**

```
                    ┌─────────────────────┐
                    │   Título Limpio     │
                    │   "Modelista"       │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │  Skills    │   │  Embeddings│   │  Contexto  │
       │  40%       │   │  (BGE-M3)  │   │  (área,    │
       │            │   │  50%       │   │  seniority)│
       └────────────┘   └────────────┘   └────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  ISCO: 7531         │
                    │  "Modista"          │
                    └─────────────────────┘
```

**Ejemplo real - Modelista:**

```
ENTRADA:
- titulo_limpio: "Modelista"
- tareas: "desarrollar moldería, progresiones, fichas técnicas"
- area_funcional: "Producción"

PROCESO:
1. Busca "modelista" + "moldería" en embeddings semánticos
2. Filtra por área "Producción" → códigos ISCO 7xxx
3. Encuentra mejor match: ISCO 7531 "Modista, sastre"

SALIDA:
- ISCO: 7531
- Ocupación ESCO: "Modista"
- Score: 0.72
```

---

## Etapa 5: CATEGORIZACIÓN DE SKILLS (Bonus)

**¿Qué hace?** Clasifica las skills extraídas en categorías agregadas para dashboards

**Niveles de agregación:**

| Código | Categoría | Ejemplos |
|--------|-----------|----------|
| S5 | Digital/IT | Python, Excel, SQL, SAP |
| S6 | Técnicas | soldadura, manejo de maquinaria, electricidad |
| S4 | Gestión | contabilidad, planificación, presupuestos |
| T | Transversales | liderazgo, trabajo en equipo, comunicación |
| K | Conocimientos | normativa legal, inglés técnico |

**Ejemplo:**
```
Oferta: "Gerente de Operaciones"

Skills extraídas:
- "gestión de equipos" → T (Transversal)
- "Excel avanzado" → S5 (Digital)
- "planificación de producción" → S4 (Gestión)
- "liderazgo" → T (Transversal)

Resumen: 2 Transversales, 1 Digital, 1 Gestión
```

---

## Ejemplo Completo: De principio a fin

**Oferta original del portal:**
```
ID: 1118028201
Título: "671SI Operarios ind. ALIMENTICIA c/ Tit. secundario - pres 31/10 de 10 a 1130 NUEVA Suc. SAN ISIDRO"
Ubicación: "Tortuguitas, Buenos Aires"
Descripción: "CONA Consultores busca OPERARIOS DE PRODUCCIÓN ALIMENTICIA
con experiencia en manipulación de alimentos y producción continua.
Conocimiento de BPM. Ubicada en Tortuguitas. Turnos rotativos..."
```

**Después del pipeline:**
```
┌─────────────────────────────────────────────────────────────┐
│ RESULTADO FINAL                                              │
├─────────────────────────────────────────────────────────────┤
│ titulo_limpio:    "Operarios industria ALIMENTICIA"         │
│ provincia:        "Buenos Aires"                             │
│ localidad:        "Tortuguitas"                              │
│ sector:           "Alimentacion"                             │
│ area_funcional:   "Produccion"                               │
│ seniority:        "junior"                                   │
│ nivel_educativo:  "secundario"                               │
│ modalidad:        "presencial"                               │
│ experiencia:      1 año mínimo                               │
│ skills_tecnicas:  "BPM, manipulación de alimentos, control   │
│                    de calidad"                               │
│                                                              │
│ ISCO:             7511                                       │
│ Ocupación ESCO:   "Operario de procesamiento de alimentos"   │
└─────────────────────────────────────────────────────────────┘
```

---

## Métricas Actuales

| Métrica | Valor |
|---------|-------|
| Ofertas en BD | ~10,000 |
| Precisión NLP | ~90% |
| Precisión Matching ESCO | 100% (Gold Set 49 ofertas) |
| Campos extraídos | 155 |
| Skills por oferta | ~14 promedio |

---

## Archivos Clave

| Archivo | Función |
|---------|---------|
| `database/limpiar_titulos.py` | Limpieza de títulos |
| `config/nlp_titulo_limpieza.json` | Patrones de limpieza |
| `database/process_nlp_from_db_v10.py` | Pipeline NLP principal |
| `database/nlp_postprocessor.py` | Correcciones post-LLM |
| `database/match_ofertas_v3.py` | Matching ESCO |
| `database/skill_categorizer.py` | Categorización L1/L2 |

---

## Contacto

Para dudas técnicas sobre el pipeline, consultar `CLAUDE.md` en la raíz del proyecto.
