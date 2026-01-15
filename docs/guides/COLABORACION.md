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

### Division por Fases

| Persona | Fase | Foco |
|---------|------|------|
| Dev 1 | Procesamiento (Fase 2) | NLP, Skills, Matching, Validacion |
| Dev 2 | Presentacion (Fase 3) | Dashboard, Supabase, Visualizaciones |

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

## Notas para Claude

**Si hay dudas sobre colaboracion o configuracion compartida:**
1. Consultar la documentacion oficial en https://code.claude.com/docs/en/memory
2. Respetar la division de fases en `learnings.yaml`
3. No modificar archivos de otra fase sin coordinacion explicita
4. Siempre hacer `git pull` conceptual: preguntar si hay cambios recientes antes de editar archivos criticos

---

*Ultima actualizacion: 2026-01-15*
