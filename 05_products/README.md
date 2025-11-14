# 05_products - Productos Finales

## 🎯 Propósito

Este directorio contiene los productos finales listos para publicación, distribución o consumo externo.

## 📁 Estructura

```
05_products/
├── datasets/          # Datasets publicables
├── reports/           # Informes finales
└── apis/             # API REST (si se desarrolla)
```

## 📊 Datasets

### Estructura de `datasets/`

```
datasets/
├── ofertas_laborales_argentina_2025.csv      # Dataset completo
├── ofertas_laborales_argentina_2025.json     # Formato JSON
├── ofertas_isco_clasificadas_2025.xlsx       # Con clasificación ISCO
├── diccionario_datos.md                      # Documentación de campos
└── metadata.json                             # Metadatos del dataset
```

### Contenido

Datasets listos para:
- Publicación en portales de datos abiertos
- Compartir con investigadores
- Usar en otros proyectos
- Análisis externos

### Características

- ✅ Datos limpios y validados
- ✅ Schema documentado
- ✅ Sin información sensible
- ✅ Licencia clara
- ✅ Versionado

## 📄 Reports

### Estructura de `reports/`

```
reports/
├── informe_anual_mercado_laboral_2025.pdf
├── presentacion_ejecutiva_2025.pptx
├── reporte_tecnico_metodologia.pdf
└── dashboard_ofertas_2025.html
```

### Tipos de Reportes

1. **Reporte Ejecutivo**: Resumen para tomadores de decisión
2. **Reporte Técnico**: Metodología completa
3. **Dashboard Interactivo**: Exploración de datos
4. **Presentaciones**: Para comunicar resultados

## 🌐 APIs

### API REST (opcional)

Si se desarrolla una API:

```
apis/
├── app.py                    # Aplicación FastAPI
├── models.py                 # Modelos de datos
├── routes/
│   ├── ofertas.py
│   ├── estadisticas.py
│   └── esco.py
├── docs/
│   └── api_documentation.md
└── requirements.txt
```

### Endpoints Ejemplo

```
GET /api/v1/ofertas
GET /api/v1/ofertas/{id}
GET /api/v1/estadisticas/isco
GET /api/v1/estadisticas/temporal
GET /api/v1/skills/top
```

## 📦 Publicación

### Dataset en Datos Abiertos

```bash
# Preparar para publicación
cd 05_products/datasets
python ../../scripts/preparar_publicacion.py
```

Genera:
- Archivo de datos
- Diccionario de datos
- Metadatos en formato estándar
- Licencia

### Reporte Final

```bash
# Generar reporte final
cd 05_products/reports
python ../../04_analysis/scripts/generar_reportes.py --final
```

## ✅ Checklist de Publicación

Antes de publicar, verificar:

- [ ] Datos completos y validados
- [ ] Sin información personal sensible
- [ ] Licencia definida (ej: CC BY 4.0)
- [ ] Documentación clara
- [ ] Metadatos completos
- [ ] Versionado correcto
- [ ] README con instrucciones
- [ ] Citación recomendada

## 📜 Licencia

Definir licencia apropiada:
- **CC BY 4.0**: Atribución
- **CC BY-SA 4.0**: Atribución + CompartirIgual
- **CC0**: Dominio público
- **Otra**: Según política institucional

## 📖 Citación Sugerida

```
OEDE (2025). Ofertas Laborales Argentina - Clasificación ESCO.
Dataset extraído de múltiples fuentes, procesado y clasificado
según taxonomía ESCO. Disponible en: [URL]
```

## 🔄 Versionado

Usar versionado semántico:
- `v1.0.0`: Primera versión completa
- `v1.1.0`: Nuevas funcionalidades
- `v1.0.1`: Correcciones menores

---

**Última actualización**: 2025-10-21
