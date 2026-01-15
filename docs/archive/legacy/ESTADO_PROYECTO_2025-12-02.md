# Estado del Proyecto MOL - 2 de Diciembre 2025

## Resumen de la Sesión

### 1. Subida a GitHub ✅ COMPLETADO

**Repositorio:** https://github.com/gbreard/mol.git
**Branch:** `feature/fase1-fundamentos-datos`

#### Acciones realizadas:
1. **Actualización de `.gitignore`** para excluir datos sensibles:
   ```
   # Datos de ofertas (no versionar)
   01_sources/*/data/raw/*.json
   01_sources/*/data/raw/*.csv
   01_sources/*/data/raw/*.xlsx
   01_sources/*/data/metrics/*.json
   02_consolidation/data/*.json
   02_consolidation/data/consolidated/*.csv
   02_consolidation/data/consolidated/*.json
   03_esco_matching/data/*.csv

   # ChromaDB vectors (grandes)
   database/esco_vectors/

   # Archivos de tracking y backups
   data/tracking/*.bak*
   *.bak_*
   database/*.csv
   database/*.txt
   database/embeddings/
   ```

2. **Limpieza del historial de Git** con `git filter-branch`:
   - Eliminados archivos grandes (2GB+) del historial
   - Archivos eliminados: `ofertas_consolidadas_*.csv/json`, archivos de matching
   - Ejecutado `git gc --prune=now --aggressive` para limpiar

3. **Push exitoso** al repositorio remoto

#### Lo que NO se subió (excluido):
- Bases de datos SQLite (`*.db`)
- Datos de ofertas en JSON/CSV
- Vectores de ChromaDB
- Credenciales y archivos sensibles

---

### 2. Configuración de MCP de Linear ✅ COMPLETADO

**Comando ejecutado:**
```bash
claude mcp add --transport sse linear-server https://mcp.linear.app/sse
```

**Configuración guardada en:** `C:\Users\Gerardo\.claude.json`

**Workspace objetivo:** molar

#### Próximos pasos para Linear:
1. Reiniciar la sesión de Claude Code
2. Ejecutar `/mcp` para autenticarse
3. Autorizar acceso al workspace "molar" en el navegador

#### Funcionalidades disponibles con Linear MCP:
- Buscar, crear y actualizar issues
- Ver proyectos y ciclos
- Agregar comentarios
- Gestionar backlog

---

## Estado Actual del Proyecto

### Estructura del Repositorio
```
D:\OEDE\Webscrapping\
├── 01_sources/          # Scrapers (Bumeran, ZonaJobs, etc.)
├── 02_consolidation/    # Consolidación de ofertas
├── 02.5_nlp_extraction/ # Pipeline NLP v6.0 (Hermes 3:8b)
├── 03_esco_matching/    # Matching con taxonomía ESCO
├── 04_territorial/      # Normalización territorial INDEC
├── database/            # Scripts de BD y ChromaDB
├── Visual--/            # Dashboards Shiny
└── .gitignore           # Configuración de exclusiones
```

### Branch Actual
- **Branch:** `feature/fase1-fundamentos-datos`
- **Commits recientes:**
  - `6a6f341` - Migrar NLP v6.0 de Qwen 2.5:14b a Hermes 3:8b
  - `4d6a0cf` - feat(territorial): Normalización territorial con INDEC + FASE 1 COMPLETADA
  - `12737f3` - wip(territorial): Investigación inicial Tarea 4
  - `582f254` - feat(nlp): Completar testing y documentación NLP v6.0
  - `d221116` - wip(nlp): Crear script de testing para NLP v6.0

### FASE 1 - Fundamentos de Datos: COMPLETADA ✅
1. ✅ Scraping de portales de empleo
2. ✅ Consolidación de ofertas
3. ✅ Pipeline NLP v6.0 (extracción estructurada)
4. ✅ Normalización territorial con INDEC

### Pendiente (Contexto de sesiones anteriores)
- **FASE 3:** Matching híbrido (ChromaDB semántico + SQL ocupacional)
- Dashboards de validación tenían problemas de reinicio

---

## Archivos de Configuración Importantes

### `.claude/settings.local.json`
Contiene permisos para comandos de Bash frecuentes (Python, R, SQLite, Git)

### `.gitignore`
Excluye todos los datos sensibles y archivos grandes

---

## Notas Técnicas

### Para clonar el proyecto:
```bash
git clone https://github.com/gbreard/mol.git
cd mol
git checkout feature/fase1-fundamentos-datos
```

### Para restaurar datos (no versionados):
Los datos de ofertas deben obtenerse por separado ya que no están en el repositorio.

---

*Documento generado: 2025-12-02*
