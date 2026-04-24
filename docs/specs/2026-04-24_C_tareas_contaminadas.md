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

## 4.bis Tests

### 4.bis.1 Extender `tests/test_limpieza_tareas_ruido.py` (existente)

**Ya existe** y tiene 35 casos cubriendo filtros de "Hace N días", "Experiencia requerida: No", etc. Agregamos casos nuevos para los patrones detectados en operarios:

```python
# tests/test_limpieza_tareas_ruido.py — SUMAR al archivo existente

class TestFiltrarRuidoOperariosComputrabajo:
    """Ruido específico de ofertas ComputRabajo de operarios (2026-04-24).

    Casos reales: 7985222956, 7938726540, 7942527874.
    """

    def test_nombres_empresas_eventuales(self, postprocessor):
        """Nombres de agencias eventuales como 'EXTRAMEN', 'PULLMEN' se filtran."""
        entradas = [
            "Realizar picking; EXTRAMEN Empresa de Servicios Eventuales SRL",
            "Limpieza general; PULLMEN búsqueda y selección",
            "Controlar stock; ARCH Resources Group",
        ]
        for entrada in entradas:
            result = limpiar(postprocessor, entrada)
            assert not any("EXTRAMEN" in t or "PULLMEN" in t or "ARCH Resources" in t for t in result)

    def test_grupo_empresa_aislado(self, postprocessor):
        """'Grupo Gestión' aislado (sin otro contexto) se filtra."""
        result = limpiar(postprocessor, "Carga y descarga; Grupo Gestión; Empaquetado")
        assert "Grupo Gestión" not in "; ".join(result)
        assert any("descarga" in t.lower() for t in result)  # tarea real preservada

    def test_ubicaciones_buenos_aires_gba(self, postprocessor):
        """Ubicaciones formato '<Localidad>, Buenos Aires-GBA' se filtran."""
        entradas = [
            "Picking; San Martín, Buenos Aires-GBA",
            "Control calidad; Santos Lugares, Buenos Aires-GBA",
            "Soldadura; Villa Maipú, Buenos Aires-GBA",
        ]
        for entrada in entradas:
            result = limpiar(postprocessor, entrada)
            assert not any("Buenos Aires-GBA" in t for t in result)

    def test_descripciones_otras_empresas(self, postprocessor):
        """'Importante empresa X dedicada a Y...' (descripción de OTRO aviso) se filtra."""
        entradas = [
            "Realizar picking; Importante empresa metalúrgica dedicada a la fabricación de electrodomésticos",
            "Embalaje; Importante empresa del rubro alimenticio incorpora Operarios/as",
            "Limpieza; Importante fábrica alimenticia busca Operarios/as",
        ]
        for entrada in entradas:
            result = limpiar(postprocessor, entrada)
            assert not any("Importante empresa" in t or "Importante fábrica" in t for t in result)

    def test_ui_noise_computrabajo(self, postprocessor):
        """Texto de UI del portal ComputRabajo se filtra."""
        entradas = [
            "Picking mercadería; Ocultaste esta oferta, pulsaRecuperar oferta",
            "Control stock; para verla de nuevo en los listados",
        ]
        for entrada in entradas:
            result = limpiar(postprocessor, entrada)
            txt = "; ".join(result)
            assert "Ocultaste" not in txt
            assert "pulsaRecuperar" not in txt
            assert "nuevo en los listados" not in txt

    def test_frases_cortadas(self, postprocessor):
        """'Operar y controlar...' (frase terminada en puntos suspensivos) se filtra."""
        result = limpiar(postprocessor, "Picking; Operar y controlar...; Empaquetar")
        # Tarea cortada termina en "..." o queda muy corta — postprocessor debería descartar
        assert not any(t.endswith("...") for t in result)

    # ========================================================================
    # PRESERVAR tareas reales aun con ruido alrededor
    # ========================================================================

    def test_preservar_tareas_reales_caso_7985222956(self, postprocessor):
        """Caso real: oferta Operario Pickeador.

        Entrada tiene 5 tareas válidas + 5 ruido. Output debe tener las 5 válidas.
        """
        entrada = (
            "Picking de mercadería; "
            "uso de handheld; "
            "cumplimiento de procedimientos de recepción; "
            "carga y descarga; "
            "empaquetado y embalaje; "
            "Operar y controlar...; "
            "Hace 2 días; "
            "Grupo Gestión; "
            "San Martín, Buenos Aires-GBA; "
            "Importante empresa metalúrgica dedicada a la fabricación de electrodomésticos"
        )
        result = limpiar(postprocessor, entrada)

        # Las 5 reales deben estar
        assert any("picking" in t.lower() for t in result)
        assert any("handheld" in t.lower() or "recepción" in t.lower() for t in result)
        assert any("carga" in t.lower() and "descarga" in t.lower() for t in result)
        assert any("empaquetado" in t.lower() or "embalaje" in t.lower() for t in result)

        # Los 5 ruido NO deben estar
        txt = "; ".join(result)
        for noise in ["Hace 2 días", "Grupo Gestión", "Buenos Aires-GBA",
                      "Importante empresa metalúrgica", "Operar y controlar..."]:
            assert noise not in txt, f"Ruido '{noise}' no fue filtrado"
```

### 4.bis.2 Test nuevo del scraper — `tests/scraping/test_computrabajo_description.py`

Archivo nuevo para validar que el scraper bajo la nueva lógica devuelve descripciones limpias (sin UI noise ni texto de otras ofertas).

```python
# -*- coding: utf-8 -*-
"""
Tests: ComputRabajo scraper — extracción limpia de descripción.

Verifica que el scraper NO incluye:
  - UI noise ("Ocultaste esta oferta...", "pulsaRecuperar oferta...")
  - Ofertas similares ("Importante empresa X dedicada a...")
  - Metadata del portal ("Hace 2 días", ubicaciones sueltas)
  - Nombres de empresas de otras ofertas

Requiere HTML fixtures en tests/fixtures/computrabajo/
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "01_sources/computrabajo/scrapers"))

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures/computrabajo"


@pytest.fixture
def scraper():
    from computrabajo_scraper import ComputrabajoScraper
    return ComputrabajoScraper()


class TestDescripcionLimpia:

    def test_oferta_normal_descripcion_completa(self, scraper):
        """Oferta con HTML estándar — descripción debe estar completa."""
        html_path = FIXTURES_DIR / "oferta_normal.html"
        if not html_path.exists():
            pytest.skip(f"Fixture faltante: {html_path}")
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
        result = scraper._parse_detail_html(html)  # método helper hipotético
        desc = result.get('descripcion', '')
        assert len(desc) > 100
        assert len(desc) < 5000  # sanity: no captura la página entera

    def test_no_ui_noise_ocultar_oferta(self, scraper):
        """'Ocultaste esta oferta, pulsaRecuperar oferta...' NO debe aparecer en descripción."""
        html_path = FIXTURES_DIR / "oferta_con_ocultar.html"
        if not html_path.exists():
            pytest.skip(f"Fixture faltante: {html_path}")
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
        result = scraper._parse_detail_html(html)
        desc = result.get('descripcion', '')
        assert "Ocultaste esta oferta" not in desc
        assert "pulsaRecuperar" not in desc
        assert "nuevo en los listados" not in desc

    def test_no_incluye_ofertas_similares(self, scraper):
        """Sección 'Ofertas similares' al final NO debe incluirse."""
        html_path = FIXTURES_DIR / "oferta_con_similares.html"
        if not html_path.exists():
            pytest.skip(f"Fixture faltante: {html_path}")
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
        result = scraper._parse_detail_html(html)
        desc = result.get('descripcion', '')
        # Patrones típicos de "ofertas similares"
        assert "Importante empresa metalúrgica dedicada a" not in desc
        assert "EXTRAMEN" not in desc
        assert "PULLMEN" not in desc
        assert "Grupo Gestión" not in desc

    def test_oferta_real_contaminada_reproducida(self, scraper):
        """Reproduce caso real 7985222956.

        El HTML capturado en producción contenía 'Ocultaste esta oferta' +
        descripción real + 'Importante empresa metalúrgica...' al final.

        Tras el fix, solo debe quedar la descripción real del puesto Pickeador.
        """
        html_path = FIXTURES_DIR / "oferta_7985222956.html"
        if not html_path.exists():
            pytest.skip(f"Fixture faltante: {html_path}")
        with open(html_path, encoding='utf-8') as f:
            html = f.read()
        result = scraper._parse_detail_html(html)
        desc = result.get('descripcion', '')
        # Debe tener el contenido real
        assert "neumáticos" in desc.lower() or "pickeador" in desc.lower()
        # Y NO el ruido
        assert "metalúrgica dedicada" not in desc
        assert "ARCH Resources" not in desc or desc.count("ARCH") <= 1  # 1 OK si es intro de esta oferta
```

**Setup de fixtures HTML:**

Para que estos tests corran, hay que capturar HTML de producción:

```bash
mkdir -p tests/fixtures/computrabajo
# Guardar HTML de las 3 ofertas contaminadas conocidas:
for oid in 7985222956 7938726540 7942527874; do
    python3 -c "
import requests
r = requests.get(f'https://ar.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-operario-en-buenos-aires-{oid}')
open(f'tests/fixtures/computrabajo/oferta_{oid}.html','w').write(r.text)
"
done
```

### 4.bis.3 Tests de regresión

```bash
# Debe seguir pasando tras el fix
pytest tests/scraping/test_pipeline_fixes.py -v
pytest tests/test_limpieza_tareas_ruido.py -v
pytest tests/matching/test_gold_set_v2_verified.py -v  # v2 — casos verificados
```

**Nota:** no usar `test_gold_set_manual.py` (v1). Ver Specs A/B para detalles.

### 4.bis.4 Smoke test sobre BD actual

Script para validar que el fix limpió las tareas contaminadas ya en BD (tras re-correr postprocessor):

```python
import sqlite3

conn = sqlite3.connect('database/bumeran_scraping.db')
c = conn.cursor()

# Ofertas target del análisis
OFERTAS_TEST = ['7985222956', '7938726540', '7942527874']

NOISE_PATTERNS = [
    'Hace 2 días', 'Hace 3 días', 'Grupo Gestión',
    'EXTRAMEN', 'PULLMEN', 'ARCH Resources',
    'Buenos Aires-GBA', 'Importante empresa metalúrgica',
    'Ocultaste esta oferta',
]

for oid in OFERTAS_TEST:
    c.execute("SELECT tareas_explicitas FROM ofertas_nlp WHERE id_oferta=?", (oid,))
    row = c.fetchone()
    if not row: continue
    tareas = row[0] or ''
    encontrados = [p for p in NOISE_PATTERNS if p in tareas]
    status = "OK" if not encontrados else f"RUIDO: {encontrados}"
    print(f"{oid}: {status}")
```

**Criterio:** las 3 ofertas post-fix deben reportar "OK" (sin ruido).

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
