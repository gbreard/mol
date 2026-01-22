# Guia de Colaboracion - Proyecto MOL

## Contexto
Este proyecto es trabajado por multiples personas, cada una potencialmente en una fase distinta.
Claude Code debe respetar las politicas de colaboracion.

## Documentacion Oficial Claude Code (LEER SI HAY DUDAS)

| Tema | URL |
|------|-----|
| Settings y Scopes | https://code.claude.com/docs/en/settings |
| Memory y CLAUDE.md | https://code.claude.com/docs/en/memory |
| Permisos compartidos | https://code.claude.com/docs/en/iam |
| GitHub Actions | https://code.claude.com/docs/en/github-actions |

---

## Modelo de Colaboracion MOL

### Modelo de Trabajo

**Ambos desarrolladores trabajan en todas las fases.**

Para evitar conflictos:
- **Coordinar** antes de editar archivos criticos (configs, CLAUDE.md)
- **Usar branches** para trabajo no trivial
- **Commits frecuentes** para minimizar divergencia
- **Pull antes de empezar** cada sesion

### Fuente de Verdad

```
SQLite Local (cada dev)     Supabase (compartido)
       │                           │
       │   Solo datos validados    │
       └──────────────────────────►│
                                   │
                          Dashboard Next.js
```

- **Datos crudos/en proceso:** SQLite local de cada dev
- **Datos validados:** Supabase (compartido, source of truth para dashboard)

---

## Reglas de Sincronizacion

### Git (OBLIGATORIO)

1. **Antes de empezar sesion:** `git pull`
2. **Commits frecuentes:** No acumular cambios grandes
3. **Push al terminar:** No dejar cambios sin pushear
4. **Conflictos en learnings.yaml:** Resolver manualmente, combinar estados

### Archivos Compartidos (en git)

- `CLAUDE.md` - Instrucciones del proyecto
- `.ai/learnings.yaml` - Estado actual del trabajo
- `docs/` - Toda la documentacion
- `config/*.json` - Configuraciones
- `database/*.py` - Codigo de procesamiento
- `scripts/` - Utilidades

### Archivos Locales (NO en git)

- `.env` - Credenciales (compartir por canal seguro)
- `database/*.db` - Bases de datos SQLite
- `.claude/settings.local.json` - Settings personales

---

## Flujo de Branches Git

### Estructura de Branches

```
main                    <- Produccion (estable)
  |-- feature/X         <- Features nuevas
  |-- fix/Y             <- Bug fixes
  |-- experiment/Z      <- Experimentos (descartar o PR)
```

### Cuando usar Branches

| Situacion | Branch | Merge a |
|-----------|--------|---------|
| Feature nueva (>1 hora) | `feature/nombre-descriptivo` | main (via PR) |
| Bug fix no trivial | `fix/descripcion-bug` | main (via PR) |
| Trabajo rapido (<1 hora, bajo riesgo) | main directo | - |
| Experimento | `experiment/nombre` | descartar o PR |
| Cambios en config/*.json | main directo | - |

### Workflow Diario

```bash
# 1. Al empezar sesion
git pull origin main

# 2. Crear branch para trabajo nuevo (si aplica)
git checkout -b feature/mi-feature

# 3. Trabajar, commitear frecuente
git add .
git commit -m "feat: descripcion"

# 4. Al terminar, push y PR
git push -u origin feature/mi-feature
# Crear PR en GitHub

# 5. Despues del merge, limpiar
git checkout main
git pull
git branch -d feature/mi-feature
```

### Convencion de Branches para Colaboracion

Cuando ambos devs trabajan en todas las fases:

```
feature/tu-nombre/descripcion
feature/descripcion-iniciales
```

Ejemplos:
- `feature/nlp-fixes-fz` vs `feature/dashboard-cards-gm`
- `fix/matching-rules-fz` vs `fix/supabase-sync-gm`

### Puntos de Sincronizacion

| Punto | Funcion |
|-------|---------|
| **Git (main)** | Codigo estable |
| **Supabase** | Ofertas validadas (source of truth) |
| **learnings.yaml** | Estado del sistema |

### Conflictos Comunes

| Archivo | Como resolver |
|---------|---------------|
| `learnings.yaml` | Merge manual, combinar estados |
| `config/*.json` | Coordinar antes de editar reglas |
| `CLAUDE.md` | PR con revision |

### Ver Estado Git en Reporte

El comando `python scripts/sync_learnings.py --human` ahora muestra:

```
--- GIT ---
  Branch:           main
  Estado:           limpio | X archivos modificados
  Ultimo commit:    abc1234 - mensaje del commit
  vs Origin:        al dia | X commits adelante | X commits atras
```

---

## Comunicacion entre Fases

### Fase 2 → Fase 3

El handoff es via Supabase:

```python
# Fase 2 termina validacion
python scripts/validar_ofertas.py --ids X --estado validado

# Fase 2 sincroniza a Supabase
python scripts/exports/sync_to_supabase.py

# Fase 3 ya tiene los datos en el dashboard
```

### Evitar Conflictos

| Situacion | Que hacer |
|-----------|-----------|
| Ambos editan mismo config | Coordinar antes, o usar branches |
| Ambos editan learnings.yaml | Merge manual, combinar estados |
| Uno necesita dato del otro | Sync a Supabase primero |

---

## Setup para Nuevo Colaborador

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd Webscrapping

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Obtener credenciales (pedir al equipo)
# - .env con SUPABASE_URL, SUPABASE_KEY
# - LINEAR_API_KEY (opcional)

# 4. Solo si trabaja en Fase 2 (NLP/Matching)
ollama pull qwen2.5:7b

# 5. Leer documentacion
# - CLAUDE.md (instrucciones principales)
# - .ai/learnings.yaml (estado actual)
# - docs/reference/ARQUITECTURA_3_FASES.md (modelo de fases)
```

---

## Feedback Loop via Markdown

Sistema para que humanos validen ofertas y Claude aprenda de los errores.

### Flujo

```
1. GENERAR MARKDOWN
   python scripts/exports/export_validation_markdown.py --limit 50

   → Genera: validation/feedback_YYYYMMDD_HHMM.md

2. PUBLICAR EN GITHUB
   git add validation/feedback_*.md
   git commit -m "validation: feedback pendiente"
   git push

3. HUMANO EDITA EN GITHUB
   - Abrir validation/feedback_*.md en GitHub
   - Editar columnas: resultado | isco_correcto | comentario
   - Valores de resultado: OK | ERROR | REVISAR
   - Commit cambios

4. CLAUDE LEE Y APRENDE
   - Lee el archivo editado
   - Busca filas con ERROR o REVISAR
   - Crea reglas en config/matching_rules_business.json
   - Reprocesa ofertas afectadas
```

### Ejemplo de Edicion Humana

**Antes (generado):**
```markdown
| id | titulo | isco | isco_label | score | resultado | isco_correcto | comentario |
| 2171959 | Vigilador General | 5151 | Supervisor limpieza | 0.65 | | | |
```

**Despues (editado por humano):**
```markdown
| id | titulo | isco | isco_label | score | resultado | isco_correcto | comentario |
| 2171959 | Vigilador General | 5151 | Supervisor limpieza | 0.65 | ERROR | 5414 | Deberia ser guardia seguridad |
```

### Archivos

| Archivo | Descripcion |
|---------|-------------|
| `scripts/exports/export_validation_markdown.py` | Genera Markdown desde BD |
| `validation/` | Directorio con archivos de feedback |
| `validation/feedback_*.md` | Archivos editables por humanos |

### Ventajas

- **Versionado:** Feedback queda en historial git
- **Colaborativo:** Visible en GitHub para todo el equipo
- **Asincronico:** Humano edita cuando puede, Claude procesa despues
- **Complementario:** Excel sigue disponible para detalle

---

## Notas para Claude

**Si hay dudas sobre colaboracion o configuracion compartida:**
1. Consultar la documentacion oficial en https://code.claude.com/docs/en/memory
2. Respetar la division de fases en `learnings.yaml`
3. No modificar archivos de otra fase sin coordinacion explicita
4. Siempre hacer `git pull` conceptual: preguntar si hay cambios recientes antes de editar archivos criticos

---

*Ultima actualizacion: 2026-01-21*
