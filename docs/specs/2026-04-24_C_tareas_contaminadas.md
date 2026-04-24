# SPEC C: Tareas contaminadas con texto de otras ofertas (ComputRabajo)

**Fecha:** 2026-04-24
**Estado:** Draft — requiere investigación antes de implementar
**Scope:** Bug del scraper (+ posible fallback en LLM prompt).
**Specs relacionados:**
- `2026-04-24_A_operarios_config.md` — config fixes (independiente)
- `2026-04-24_B_skills_noise.md` — skills ruido (independiente)

---

## 1. Problema

En **al menos 3 de las 18 ofertas operarios analizadas**, el campo `ofertas_nlp.tareas_explicitas` contiene fragmentos que claramente pertenecen a OTRAS ofertas scrapeadas (diferentes empresas, distintos rubros), mezclados con las tareas correctas.

### Ejemplo concreto — oferta 7985222956 (Operario Pickeador)

**Tareas que extrajo el pipeline:**
```
1. Picking de mercadería                                        ← CORRECTA
2. uso de handheld                                              ← CORRECTA
3. cumplimiento de procedimientos de recepción                  ← CORRECTA
4. carga y descarga                                             ← CORRECTA
5. empaquetado y embalaje                                       ← CORRECTA
6. Operar y controlar...                                        ← ❌ frase cortada
7. Hace 2 días                                                  ← ❌ metadata del portal
8. Grupo Gestión                                                ← ❌ nombre de otra empresa
9. San Martín, Buenos Aires-GBA                                 ← ❌ ubicación de otra oferta
10. Importante empresa metalúrgica dedicada a la fabricación... ← ❌ descripción de OTRA oferta
```

**Las últimas 5 son ruido de texto de otras ofertas / UI del portal.**

### Otras ofertas con el mismo patrón

- **7938726540** (Operario producción alimenticia): tareas tienen "Hace 2 días", "Grupo Gestión", "Santos Lugares, Buenos Aires-GBA", "EXTRAMEN Empresa de Servicios Eventuales SRL", "Importante fábrica alimenticia busca Operarios/as".
- **7942527874** (Operario CNC): menor contaminación pero `desc` empieza con "DESDE GRUPO CONSULTORES DE EMPRESAS" que no es tarea.

---

## 2. Root cause (hipótesis)

### Evidencia en la BD

Las descripciones de las ofertas contaminadas empiezan con:

```
Ocultaste esta oferta, pulsaRecuperar ofertapara verla de nuevo en los listados
<contenido real de la oferta>
<ofertas relacionadas al final>
```

La primera línea (`"Ocultaste esta oferta, pulsaRecuperar oferta..."`) es **UI del portal de ComputRabajo** — aparece solo en usuarios logueados que marcaron la oferta como oculta. No debería estar en el scraping.

### Análisis del scraper

`01_sources/computrabajo/scrapers/computrabajo_scraper.py:330-409` tiene 3 métodos de extracción de descripción:

- **Método 1** (principal): `div.box_detail > p.mbB` — solo la descripción real.
- **Método 2** (fallback): buscar `p/div > 100 chars` que no sean review/oferta-similar.
- **Método 3** (fallback final): `<meta name="description">`.

**Hipótesis de por qué contamina:**

**H1** (más probable): Método 2 captura divs/párrafos de la sección de "ofertas similares" porque alguna no tiene las clases listadas en `skip_classes`. La lista actual es:
```python
skip_classes = {'fs13', 'fc_aux', 'result', 'fs50', 'list_dot', 'fc_ok', 'fw_b', 'fwB', 'box_tooltip', 'group'}
```
Las "ofertas similares" pueden tener clases distintas (ej: `jobcard`, `vacancy-item`) y no ser filtradas.

**H2**: El HTML de ComputRabajo cambió y la clase `p.mbB` ya no es exclusiva de la descripción principal. Puede haber varias.

**H3**: El LLM recibe la descripción correcta pero el prompt le pide extraer tareas de manera laxa, incluyendo texto de bullets de "empresas similares" si aparecen.

### Cómo diferenciar H1/H2 de H3

Revisar `ofertas.descripcion` (raw del scraping) para ver si ya está contaminado:
- Si el raw YA tiene el texto ajeno → bug del scraper (H1 o H2).
- Si el raw está limpio y el ruido solo aparece en `ofertas_nlp.tareas_explicitas` → bug del LLM prompt (H3).

**Hallazgo preliminar:** la descripción de 7985222956 empieza con `"Ocultaste esta oferta, pulsaRecuperar oferta..."` — eso ya es ruido en el raw. **H1 o H2 confirmado.**

---

## 3. Plan de investigación (antes de implementar)

### Paso 1: Reproducir el scraping de una oferta contaminada

```bash
# Re-scrapear 7985222956 y capturar el HTML
python3 -c "
import sys
sys.path.insert(0, '01_sources/computrabajo/scrapers')
from computrabajo_scraper import ComputrabajoScraper
s = ComputrabajoScraper()
# usar el URL de la oferta
data = s.fetch_detail(url_de_la_oferta, save_html='/tmp/contaminated.html')
print(repr(data.get('descripcion')))
"
```

### Paso 2: Inspeccionar HTML

- Abrir `/tmp/contaminated.html` en navegador.
- Buscar dónde está el texto contaminante ("Grupo Gestión", "Hace 2 días").
- Identificar si está en la sección de descripción principal o en "ofertas similares".

### Paso 3: Verificar qué método se está usando

Agregar logging en `computrabajo_scraper.py` para reportar qué método (1, 2 o 3) fue el que se ejecutó y qué clases tenía el elemento seleccionado.

### Paso 4: Confirmar hipótesis

- Si Método 2 → ampliar `skip_classes` con los nombres reales de las "ofertas similares".
- Si Método 3 → el meta description de ComputRabajo viene de una API agregada; investigar.
- Si la descripción ya tiene la UI noise (`"Ocultaste esta oferta..."`) → agregar limpieza preliminar.

---

## 4. Cambios propuestos (pendiente de confirmar root cause)

### Opción A — Fix scraper (si H1/H2 confirma)

1. **Limpiar UI noise** antes de guardar:
   ```python
   UI_NOISE_PATTERNS = [
       r'Ocultaste esta oferta.*?listados',
       r'pulsaRecuperar ofertapara.*',
       # ...
   ]
   for pat in UI_NOISE_PATTERNS:
       descripcion = re.sub(pat, '', descripcion, flags=re.IGNORECASE | re.DOTALL)
   ```

2. **Extraer solo el contenedor correcto**:
   - Identificar el selector CSS EXACTO de la descripción (puede haber cambiado).
   - Ignorar cualquier `<section>` hermano que contenga ofertas relacionadas.

3. **Agregar patrón negativo**:
   ```python
   # Si la descripción contiene nombres de OTRAS empresas separadas, es ruido
   if re.search(r'Importante\s+empresa.*?busca|ARCH\s+Resources|Grupo\s+Gestión', descripcion):
       # Log advertencia
   ```

### Opción B — Postprocessor (si H3 o si el fix al scraper es muy caro)

En `nlp_postprocessor._limpiar_tareas()`, agregar filtro post-LLM:

```python
TAREA_NOISE_PATTERNS = [
    r'^Hace \d+ (días|horas|semanas)',
    r'^[A-Z][\w\s]+,\s*Buenos Aires-GBA',  # ubicaciones
    r'^Importante empresa.*?busca',
    r'^Grupo \w+$',
    r'^EXTRAMEN|^PULLMEN|^ARCH',  # nombres de empresas eventuales
]

def is_noise_task(tarea: str) -> bool:
    for pat in TAREA_NOISE_PATTERNS:
        if re.match(pat, tarea.strip(), re.IGNORECASE):
            return True
    return False
```

Filtrar en el output de `tareas_explicitas` antes de guardar.

### Opción C — Ambas (recomendado)

- **Fix scraper** para no guardar UI noise al principio de descripción.
- **Postprocessor defensivo** para filtrar ruido que se cuele aún así.

---

## 5. Detección de ofertas ya afectadas

Query para identificar cuántas ofertas tienen tareas contaminadas:

```sql
SELECT id_oferta, tareas_explicitas
FROM ofertas_nlp
WHERE tareas_explicitas LIKE '%Hace % días%'
   OR tareas_explicitas LIKE '%Grupo Gestión%'
   OR tareas_explicitas LIKE '%EXTRAMEN%'
   OR tareas_explicitas LIKE '%PULLMEN%'
   OR tareas_explicitas LIKE '%Ocultaste esta oferta%'
   OR tareas_explicitas LIKE '%-GBA%';
```

Estimación (por feedback Cynthia): 3 ofertas confirmadas de 18 analizadas = **~17%** de ofertas operarios tienen este patrón. Extrapolando a ~10K ofertas ComputRabajo: **1,500-2,000 ofertas potencialmente afectadas.**

---

## 6. Plan de implementación

### Fase 1 — Investigación (3-4 horas)
1. Re-scrapear 2-3 ofertas contaminadas con logging.
2. Inspeccionar HTML crudo.
3. Confirmar hipótesis H1/H2/H3.

### Fase 2 — Fix (estimado según root cause)

**Si H1/H2 (scraper):**
- Agregar limpieza preliminar de UI noise.
- Ampliar skip_classes o usar selector más específico.
- Tests: re-scrapear 10 ofertas y verificar descripciones limpias.

**Si H3 (LLM):**
- Ajustar prompt de extracción para que descarte texto claramente ajeno.
- O: agregar filtro post-LLM en postprocessor.

### Fase 3 — Limpieza de BD actual

Sobre las ofertas ya afectadas:

**Opción fácil (solo limpiar tareas):**
```bash
# Re-correr NLP sobre las ofertas con tareas contaminadas
python scripts/run_validated_pipeline.py --ids <lista> --skip-matching
```

**Opción completa (re-scrapear + re-procesar):**
- Marcar ofertas contaminadas como pendientes de re-scraping.
- En el próximo cron del VPS, re-bajar esas descripciones limpias.
- Re-procesar con NLP + matching.

### Fase 4 — Verificación
- Contar ofertas con patrones de ruido antes/después.
- Verificar que las 3 ofertas de Cynthia (7985222956, 7938726540, 7942527874) tienen tareas limpias.

### Fase 5 — Sync Supabase.

---

## 7. Riesgos

1. **El fix al scraper puede romper otras ofertas.** Si cambiamos el selector CSS, ofertas que antes funcionaban pueden dejar de extraer descripción. Mitigación: tests con 20+ ofertas variadas antes de desplegar.

2. **ComputRabajo puede cambiar el HTML nuevamente.** No hay control sobre eso. Mitigación: logging + alertas si >X% de ofertas scrape devuelven descripciones cortas o con patrones sospechosos.

3. **Limpieza con regex sobre descripciones ya guardadas puede perder info real.** Algunas ofertas legítimas pueden mencionar "Grupo Gestión" como cliente. Mitigación: limpieza solo en patrones muy específicos (ubicación seguida de salto de línea, "Hace X días" aislado, etc.).

4. **Re-scraping masivo costoso.** ComputRabajo limita requests. Mitigación: procesar en batches + delay entre requests.

---

## 8. Criterios de éxito

- ✅ Root cause confirmado (H1/H2/H3).
- ✅ Ofertas 7985222956, 7938726540, 7942527874 con tareas limpias (solo tareas reales del aviso).
- ✅ Query SQL de detección devuelve <5% de ofertas ComputRabajo (vs ~17% actual).
- ✅ Nuevas ofertas scrapedas no muestran UI noise ni texto de otras ofertas.
- ✅ Ofertas en el dashboard Supabase actualizadas.

---

## 9. Preguntas abiertas

1. ¿Hacemos la investigación primero (Fase 1) o ya asumimos que es el scraper y vamos directo al fix?
2. ¿Limpiamos la BD existente (Fase 3) o solo arreglamos para las nuevas?
3. ¿Opción A (scraper), B (postprocessor) o C (ambas)?
4. ¿Vale la pena re-scrapear las ~1,500 ofertas afectadas o es más costoso que beneficioso?

---

## 10. Dependencias

Este spec es **independiente** de SPEC A y SPEC B. Se puede ejecutar en paralelo o después.

**Recomendación:** ejecutar **después** de SPEC A (que arregla ISCOs). Porque:
- SPEC A es bajo riesgo y alto impacto inmediato.
- SPEC C requiere investigación primero (no es un fix directo).
- Combinar ambos en el mismo batch puede complicar el debug si algo sale mal.
