# Documentación de API de ZonaJobs

## Información General

- **Sitio**: https://www.zonajobs.com.ar
- **Tipo**: REST API
- **Formato**: JSON
- **Fecha de análisis**: 2025-10-16

---

## Endpoints Principales

### 1. Búsqueda de Ofertas Laborales (Principal)

**Endpoint**: `/api/avisos/searchHomeV2`
**Método**: `POST`
**URL Completa**: `https://www.zonajobs.com.ar/api/avisos/searchHomeV2`

#### Headers Requeridos

```json
{
  "Content-Type": "application/json",
  "Accept": "application/json",
  "x-site-id": "ZJAR",
  "x-pre-session-token": "[token-generado]",
  "Accept-Language": "es-AR",
  "Referer": "https://www.zonajobs.com.ar/",
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

#### Request Body (Estructura)

```json
{
  "filterData": {
    "filtros": [],
    "tipoDetalle": "full",
    "busquedaExtendida": false
  },
  "page": 0,
  "pageSize": 22,
  "sort": "RECIENTES"
}
```

#### Parámetros del Request

| Campo | Tipo | Descripción | Requerido | Valores Posibles |
|-------|------|-------------|-----------|------------------|
| `filterData.filtros` | Array | Filtros de búsqueda aplicados | Sí | `[]` para sin filtros |
| `filterData.tipoDetalle` | String | Nivel de detalle de respuesta | Sí | `"full"`, `"partial"` |
| `filterData.busquedaExtendida` | Boolean | Habilitar búsqueda extendida | Sí | `true`, `false` |
| `page` | Integer | Número de página (0-indexed) | Sí | `0, 1, 2, ...` |
| `pageSize` | Integer | Cantidad de resultados por página | Sí | Típicamente `22` |
| `sort` | String | Criterio de ordenamiento | Sí | `"RECIENTES"`, otros |

#### Estructura de Filtros

```json
{
  "filtros": [
    {
      "type": "provincia",
      "value": "29"  // ID de Buenos Aires
    },
    {
      "type": "keyword",
      "value": "desarrollador python"
    },
    {
      "type": "modalidadTrabajo",
      "value": "Remoto"
    }
  ]
}
```

#### Response (Estructura)

```json
{
  "filters": [
    {
      "type": "provincia",
      "facets": [
        {
          "id": "29",
          "idSemantico": "argentina|buenos-aires",
          "name": "Buenos Aires",
          "quantity": 10602
        }
      ]
    }
  ],
  "avisos": [
    {
      "id": 2165597,
      "titulo": "Título de la oferta",
      "detalle": "Descripción completa...",
      "empresa": "Nombre de la empresa",
      "localizacion": "Capital Federal, Buenos Aires",
      ...
    }
  ]
}
```

---

### 2. Obtener Filtros Disponibles

**Endpoint**: `/api/avisos/filtersV2`
**Método**: `GET`
**URL Completa**: `https://www.zonajobs.com.ar/api/avisos/filtersV2`

#### Headers

```json
{
  "Accept": "application/json, text/plain, */*",
  "x-site-id": "ZJAR",
  "Accept-Language": "es-AR"
}
```

#### Response

```json
{
  "total": 12492,
  "filters": [
    {
      "type": "provincia",
      "facets": [...]
    },
    {
      "type": "area",
      "facets": [...]
    }
  ]
}
```

---

### 3. Total de Avisos

**Endpoint**: `/api/avisos/total`
**Método**: `GET`
**URL Completa**: `https://www.zonajobs.com.ar/api/avisos/total`

Retorna el total de ofertas disponibles actualmente.

---

## Estructura de una Oferta Laboral

### Campos Completos

```json
{
  "id": 2165597,
  "titulo": "String - Título de la oferta",
  "detalle": "String - Descripción completa HTML/texto",
  "aptoDiscapacitado": false,
  "idEmpresa": 532382,
  "empresa": "String - Nombre de la empresa",
  "confidencial": false,
  "logoURL": "String|null - URL del logo de la empresa",
  "validada": false,
  "empresaPro": false,
  "fechaHoraPublicacion": "15-10-2025 12:41:12",
  "fechaPublicacion": "15-10-2025",
  "fechaModificado": "15-10-2025 12:49:44",
  "planPublicacion": {
    "id": 10,
    "nombre": "Avisos Platinum"
  },
  "portal": "zonajobs",
  "tipoTrabajo": "Full-time",
  "idPais": 1,
  "idArea": 14,
  "idSubarea": 30,
  "leido": null,
  "visitadoPorPostulante": null,
  "localizacion": "Capital Federal, Buenos Aires",
  "cantidadVacantes": 1,
  "guardado": null,
  "gptwUrl": null,
  "promedioEmpresa": null,
  "modalidadTrabajo": "Presencial",
  "tienePreguntas": false,
  "salarioObligatorio": true,
  "altaRevisionPerfiles": false,
  "tipoAviso": "home"
}
```

### Diccionario de Campos

| Campo | Tipo | Descripción | Nullable |
|-------|------|-------------|----------|
| `id` | Integer | ID único de la oferta | No |
| `titulo` | String | Título de la oferta laboral | No |
| `detalle` | String | Descripción completa (puede contener HTML) | No |
| `aptoDiscapacitado` | Boolean | Si acepta personas con discapacidad | No |
| `idEmpresa` | Integer | ID de la empresa | No |
| `empresa` | String | Nombre de la empresa | No |
| `confidencial` | Boolean | Si la empresa es confidencial | No |
| `logoURL` | String | URL del logo de la empresa | Sí |
| `validada` | Boolean | Si la empresa está validada | No |
| `empresaPro` | Boolean | Si la empresa tiene plan PRO | No |
| `fechaHoraPublicacion` | String | Fecha y hora de publicación (formato: DD-MM-YYYY HH:mm:ss) | No |
| `fechaPublicacion` | String | Fecha de publicación (formato: DD-MM-YYYY) | No |
| `fechaModificado` | String | Última modificación | No |
| `planPublicacion` | Object | Información del plan de publicación | No |
| `planPublicacion.id` | Integer | ID del plan | No |
| `planPublicacion.nombre` | String | Nombre del plan | No |
| `portal` | String | Portal de origen (siempre "zonajobs") | No |
| `tipoTrabajo` | String | Tipo de trabajo | No |
| `idPais` | Integer | ID del país (1 = Argentina) | No |
| `idArea` | Integer | ID del área laboral | No |
| `idSubarea` | Integer | ID de la subárea laboral | No |
| `leido` | Boolean | Si el usuario lo leyó (requiere login) | Sí |
| `visitadoPorPostulante` | Boolean | Si el usuario lo visitó (requiere login) | Sí |
| `localizacion` | String | Ubicación geográfica | No |
| `cantidadVacantes` | Integer | Número de vacantes disponibles | No |
| `guardado` | Boolean | Si el usuario lo guardó (requiere login) | Sí |
| `gptwUrl` | String | URL relacionada (raro) | Sí |
| `promedioEmpresa` | Float | Calificación promedio de la empresa | Sí |
| `modalidadTrabajo` | String | Modalidad (Presencial/Remoto/Híbrido) | No |
| `tienePreguntas` | Boolean | Si tiene preguntas de preselección | No |
| `salarioObligatorio` | Boolean | Si requiere indicar pretensión salarial | No |
| `altaRevisionPerfiles` | Boolean | Si tiene alta revisión de perfiles | No |
| `tipoAviso` | String | Tipo de aviso ("home", etc.) | No |

### Valores Posibles

#### `tipoTrabajo`
- `"Full-time"`
- `"Part-time"`
- `"Por Contrato"`
- `"Temporal"`
- `"Pasantía"`

#### `modalidadTrabajo`
- `"Presencial"`
- `"Remoto"`
- `"Híbrido"`

#### `sort` (Ordenamiento)
- `"RECIENTES"` - Más recientes primero
- `"ANTIGUOS"` - Más antiguos primero
- Posiblemente otros valores

---

## Paginación

La API usa paginación basada en índice de página:

```json
{
  "page": 0,        // Primera página = 0
  "pageSize": 22    // Resultados por página
}
```

Para obtener más resultados:
- Página 1: `"page": 0`
- Página 2: `"page": 1`
- Página 3: `"page": 2`
- etc.

**Nota**: Cada respuesta incluye un array `avisos` con las ofertas de esa página. Si retorna menos de `pageSize` resultados, probablemente sea la última página.

---

## Autenticación y Sesiones

### Token de Pre-Sesión

La API requiere un header `x-pre-session-token` que parece ser un UUID v4:
```
x-pre-session-token: 2b7fd94f-dc51-428d-b410-e8843e3d9c70
```

Este token se puede generar como un UUID aleatorio o extraer de la primera carga de la página.

### Token de Sesión (Response)

La API retorna un JWT en el header `x-session-jwt`:
```
x-session-jwt: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Este token tiene una duración de 30 días (aprox. 2592000 segundos) según el payload del JWT.

---

## Limitaciones y Consideraciones

### Rate Limiting

No se detectó rate limiting explícito en la respuesta, pero se recomienda:
- **Delay mínimo**: 1-2 segundos entre requests
- **Máximo recomendado**: 30 requests por minuto
- **Horarios**: Evitar horarios pico (9-18hs Argentina)

### Headers Importantes

```json
{
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "Referer": "https://www.zonajobs.com.ar/",
  "x-site-id": "ZJAR"
}
```

El `x-site-id` parece ser clave:
- `"ZJAR"` = ZonaJobs Argentina

### Cloudflare Protection

El sitio usa Cloudflare, visible en los headers de response:
```
Server: cloudflare
CF-Ray: 98fad26e4cd91eba-EZE
```

Esto significa:
- Requiere headers de navegador reales
- Puede detectar bots si no se usa correctamente
- Implementar delays entre requests

---

## Ejemplo de Uso

### Búsqueda Simple (Sin Filtros)

```python
import requests
import uuid

url = "https://www.zonajobs.com.ar/api/avisos/searchHomeV2"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-site-id": "ZJAR",
    "x-pre-session-token": str(uuid.uuid4()),
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.zonajobs.com.ar/"
}

payload = {
    "filterData": {
        "filtros": [],
        "tipoDetalle": "full",
        "busquedaExtendida": False
    },
    "page": 0,
    "pageSize": 22,
    "sort": "RECIENTES"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

# Obtener ofertas
ofertas = data.get("avisos", [])
for oferta in ofertas:
    print(f"{oferta['id']}: {oferta['titulo']} - {oferta['empresa']}")
```

### Búsqueda con Filtros

```python
payload = {
    "filterData": {
        "filtros": [
            {
                "type": "keyword",
                "value": "desarrollador python"
            },
            {
                "type": "provincia",
                "value": "29"  # Buenos Aires
            },
            {
                "type": "modalidadTrabajo",
                "value": "Remoto"
            }
        ],
        "tipoDetalle": "full",
        "busquedaExtendida": False
    },
    "page": 0,
    "pageSize": 22,
    "sort": "RECIENTES"
}
```

---

## Observaciones Adicionales

1. **Formato de Fechas**: DD-MM-YYYY o DD-MM-YYYY HH:mm:ss
2. **Encoding**: UTF-8 para todos los requests/responses
3. **IDs Semánticos**: Los filtros incluyen `idSemantico` con formato slug: `"argentina|buenos-aires"`
4. **Descripción HTML**: El campo `detalle` puede contener HTML - requiere parsing o sanitización
5. **Campos Nullable**: Varios campos pueden ser `null` - validar antes de usar
6. **Firebase**: El sitio usa Firebase para tracking (no relevante para scraping)

---

## Total de Ofertas Disponibles

Según el análisis del 2025-10-16:
- **Total de ofertas**: ~12,492
- **Buenos Aires**: ~10,602
- **Otras provincias**: ~1,890

---

## Notas Legales

Esta documentación es solo para fines educativos y de investigación. Antes de usar esta API:

1. ✅ Lee los Términos de Servicio de ZonaJobs
2. ✅ Verifica `robots.txt`
3. ✅ Implementa rate limiting apropiado
4. ✅ Usa un User-Agent identificable
5. ✅ No sobrecargues el servidor

---

**Última actualización**: 2025-10-16
**Versión**: 1.0
