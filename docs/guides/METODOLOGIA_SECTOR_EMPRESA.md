# Metodología de Clasificación sector_empresa

## Problema Fundamental

El campo `sector_empresa` debe indicar el **sector económico del EMPLEADOR**, no el área funcional del puesto.

### Ejemplo del problema

| Oferta | Empresa | Sector correcto | Sector incorrecto |
|--------|---------|-----------------|-------------------|
| Vigilante | Banco Galicia | Finanzas (K) | Seguridad (N) |
| Desarrollador Python | Hospital Alemán | Salud (Q) | Tecnología (J) |
| Contador | Google | Tecnología (J) | Finanzas (K) |

## Fuentes de Datos

### 1. Datos del Portal (NO disponibles actualmente)
- `id_area`, `id_subarea`: Son categorías del **PUESTO**, no del empleador
- No existe campo de sector de empresa en el scraping

### 2. Datos de la Oferta
| Campo | Confiabilidad para sector | Ejemplo |
|-------|---------------------------|---------|
| `empresa` | ALTA (si identificable) | "Banco Galicia" → Finanzas |
| Frase "somos empresa de..." | ALTA | "somos una empresa de tecnología" |
| Keywords en descripción | BAJA | "software" podría ser el puesto, no la empresa |
| Título del puesto | MUY BAJA | "Vigilante" no indica sector del empleador |

## Metodología Actual (v1.0 - con limitaciones)

### Flujo de Clasificación

```
1. LLM extrae sector_empresa del texto
        ↓
2. Si vacío → Postprocessor busca patrones "somos empresa de..."
        ↓
3. Si vacío → Postprocessor busca keywords en descripción (PROBLEMÁTICO)
        ↓
4. sector_empresa → CLAE mapping
```

### Problema en Paso 3

El paso 3 busca keywords como "software", "salud", "finanzas" en **toda la descripción**, incluyendo:
- Requisitos del puesto ("conocimientos en software")
- Área funcional ("para el área de finanzas")
- Skills requeridas ("experiencia en sistemas de salud")

Esto causa **contaminación** entre sector del empleador y área del puesto.

## Propuesta: Niveles de Confianza

### Nivel de Confianza

| Nivel | Fuente | Ejemplo | Acción |
|-------|--------|---------|--------|
| **ALTA** | Empresa identificable | "Wall Security SRL" → Seguridad | Usar directo |
| **ALTA** | Frase explícita | "somos empresa líder en logística" | Usar directo |
| **MEDIA** | Keyword después de patrón empresa | "empresa de [software]" | Usar con precaución |
| **BAJA** | Keyword en descripción general | "experiencia en software" | Marcar para revisión |
| **SIN DATO** | Sin información disponible | Empresa "Confidencial" sin frases | Dejar NULL |

### Implementación Propuesta

1. Agregar columna `sector_confianza` en `ofertas_nlp`:
   - 'alta': Empresa identificable o frase explícita
   - 'media': Keyword en contexto de empresa
   - 'baja': Keyword en descripción general
   - null: Sin clasificar

2. Modificar `_extract_sector()` para:
   - Solo buscar keywords DESPUÉS de patrones "somos empresa de..."
   - NO buscar keywords sueltos en la descripción
   - Marcar confianza según la fuente

3. Agregar regla de validación para marcar `sector_confianza = 'baja'`

## Validación Manual Requerida

### Casos a revisar SIEMPRE

1. **sector_empresa ≠ area_funcional** cuando:
   - sector = Seguridad pero area = IT
   - sector = Salud pero area = Administración en cementerio
   - sector = Tecnología pero empresa es de alarmas

2. **Empresa "Confidencial"** con sector asignado:
   - Si no hay frase "somos empresa de...", el sector es inferido (baja confianza)

3. **sector_confianza = 'baja'**:
   - Revisar si el sector viene del puesto o de la empresa

## Limitaciones Conocidas

1. **No tenemos catálogo de empresas argentinas** con su sector CLAE
   - Solución futura: Construir lookup de empresas conocidas

2. **El 68% de ofertas no tiene frase explícita de sector**
   - Estas clasificaciones son de baja confianza

3. **Empresas confidenciales** (~40% del dataset)
   - Sin nombre de empresa, solo podemos inferir de frases explícitas

## Recomendaciones para Análisis

### Para análisis de demanda de skills por sector:

1. **Filtrar por confianza**: Solo usar `sector_confianza IN ('alta', 'media')`
2. **Excluir inferidos**: No usar ofertas donde sector fue inferido de keywords del puesto
3. **Validar muestra**: Revisar manualmente una muestra por sector antes de publicar
4. **Documentar limitación**: Aclarar que el sector es una aproximación

### Cobertura esperada con metodología estricta:

| Criterio | % ofertas |
|----------|-----------|
| Empresa identificable conocida | ~5% (requiere catálogo) |
| Frase explícita "somos empresa de..." | ~32% |
| Empresa identificable + frase | ~35% |
| **Cobertura confiable total** | **~35%** |

---

*Documento creado: 2026-01-15*
*Versión: 1.0*
*Autor: Claude (análisis metodológico)*
