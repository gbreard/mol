# SPEC — Mejoras UI de Equivalencias de Skills

> **Estado:** ⬜ No iniciado  
> **Prioridad:** ALTO  
> **Prerequisito de:** M-08b (generación de candidatos nuevos)  
> **Contexto:** Antes de agregar más candidatos automáticos con M-08b,
> hay que cerrar tres gaps que hacen que la aprobación humana no tenga
> efecto real en el matching.

---

## Problema que resuelve

El sistema de equivalencias tiene tres gaps que lo hacen inefectivo:

**Gap 1 — Aprobación sin efecto real**
```
Analista aprueba grupo
    → estado = 'aprobado' en Supabase
    → skill_equivalence_lookup NO cambia
    → extractor sigue usando cache anterior
    → el matching NO cambia hasta proceso manual
```
Los 201 grupos "aprobados" pueden no estar activos en el matching.

**Gap 2 — Sin score de confianza**
```
799 grupos automáticos sin revisar
    → analista no sabe cuáles son más confiables
    → no puede priorizar qué revisar primero
    → revisa por frecuencia pero no por calidad
```

**Gap 3 — Sin impacto visible**
```
Analista aprueba un grupo
    → no sabe qué ocupaciones afecta
    → no sabe cuántas ofertas impacta
    → no puede evaluar si la decisión es correcta
```

---

## Decisiones de diseño

### Alcance

Este spec cierra los tres gaps en este orden de prioridad:

1. **Regeneración automática del lookup** — el más crítico porque
   sin esto ninguna aprobación tiene efecto
2. **Score de confianza** — habilita priorización inteligente
3. **Impacto en Perfil Argentino** — habilita decisión informada

### Regeneración: cuándo y cómo

La regeneración del lookup ocurre en dos momentos:

```
Momento A — Post-aprobación individual
    Analista aprueba/rechaza un grupo
    → API actualiza estado en Supabase
    → API exporta lookup actualizado a config/skill_equivalences_lookup.json
    → Extractor lo lee en próximo run (singleton se recarga al iniciar)
    → Inmediato para el operador, sin intervención manual

Momento B — Post-regeneración de clustering
    Cuando se corre generate_skill_equivalences.py
    → reconstruye toda la tabla desde cero
    → exporta lookup completo
    → este flujo ya existe, no cambia
```

El Momento A es el gap crítico que hay que cerrar.

---

## Componente 1 — Regeneración automática post-aprobación

### Backend: endpoint de exportación

**Archivo:** `app/api/skill-equivalences/export-lookup/route.ts` (nuevo)

Cuando el analista aprueba o modifica un grupo, el frontend llama a
este endpoint que:

1. Lee `skill_equivalences` + `skill_equivalence_lookup` de Supabase
2. Construye el dict `{uri: {group_id, canonical_label, label_argentino}}`
3. Escribe `config/skill_equivalences_lookup.json` en el servidor local

**Problema:** El dashboard está en Vercel (cloud) pero el JSON debe
escribirse en el servidor local donde corre el extractor.

**Solución:** El endpoint no escribe el archivo — expone el JSON via
GET. El extractor ya tiene lógica de fallback a Supabase si no
encuentra el JSON local. Agregar un paso en el pipeline que descargue
el lookup actualizado de Supabase al iniciar cada run.

```
Al iniciar match_and_persist():
    → consultar Supabase: ¿hay cambios en skill_equivalences
      desde la última carga del singleton?
    → si sí: recargar equiv_lookup desde Supabase
    → si no: usar cache existente
```

**Campo nuevo en `skill_equivalences`:**
```sql
ALTER TABLE skill_equivalences 
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();

-- Trigger para actualizar updated_at en cada cambio
CREATE OR REPLACE FUNCTION update_equivalences_timestamp()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER equivalences_updated
BEFORE UPDATE ON skill_equivalences
FOR EACH ROW EXECUTE FUNCTION update_equivalences_timestamp();
```

**Lógica de invalidación en el extractor:**

```python
# Al inicializar el extractor (una vez por sesión)
self._equiv_last_loaded = datetime.now()

# Al iniciar cada run de matching
def _check_equiv_staleness(self):
    latest_change = supabase.rpc('get_latest_equiv_update').execute()
    if latest_change > self._equiv_last_loaded:
        self._reload_equiv_lookup()
        self._equiv_last_loaded = datetime.now()
```

**RPC nuevo:**
```sql
CREATE OR REPLACE FUNCTION get_latest_equiv_update()
RETURNS TIMESTAMPTZ
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT MAX(updated_at) FROM skill_equivalences;
$$;
```

---

## Componente 2 — Score de confianza del clustering

### Script generador

**Archivo:** `scripts/generate_skill_equivalences.py`

Al momento del clustering, la matriz de distancias ya está calculada.
Agregar el cálculo de dos métricas por grupo:

```python
# Para cada cluster formado:
similitud_promedio = mean(similitudes entre todos los pares del grupo)
similitud_minima   = min(similitudes entre todos los pares del grupo)
```

**Campo nuevo en `skill_equivalences`:**
```sql
ALTER TABLE skill_equivalences 
ADD COLUMN similitud_promedio REAL;
ALTER TABLE skill_equivalences 
ADD COLUMN similitud_minima REAL;
```

### UI: mostrar confianza por grupo

En cada card de grupo (colapsado), agregar junto al badge de estado:

```
analizar datos  [auto]  ●●●○  92% similitud promedio
3 equivalentes · 5.772 apariciones
```

**Código de colores:**
```
similitud >= 0.92  → ●●●●  verde   (alta confianza, aprobar con seguridad)
similitud 0.88-0.92 → ●●●○  azul   (buena confianza)
similitud 0.85-0.88 → ●●○○  amarillo (confianza media, revisar)
similitud < 0.85   → ●○○○  rojo    (baja confianza, revisar con cuidado)
```

### Priorización inteligente en filtros

Agregar opción de ordenamiento además de "por frecuencia":

```
Ordenar por:  [Frecuencia ▼]  [Confianza ▼]  [Confianza ▲ (revisar primero)]
```

"Confianza ▲" muestra primero los grupos con similitud_minima baja —
los que más necesitan revisión humana.

---

## Componente 3 — Impacto en Perfil Argentino

### RPC nuevo

```sql
CREATE OR REPLACE FUNCTION get_equivalencia_impacto(p_equivalence_id TEXT)
RETURNS TABLE (
    isco_code TEXT,
    ocupacion_label TEXT,
    ofertas_count BIGINT,
    pct_de_ocupacion REAL
)
LANGUAGE sql SECURITY DEFINER
AS $$
    SELECT 
        d.isco_code,
        d.isco_label,
        COUNT(DISTINCT os.id_oferta) as ofertas_count,
        ROUND(COUNT(DISTINCT os.id_oferta)::REAL / 
              total.total_ocupacion * 100, 1) as pct_de_ocupacion
    FROM ofertas_skills os
    JOIN ofertas_dashboard d ON os.id_oferta = d.id_oferta
    CROSS JOIN (
        SELECT COUNT(DISTINCT id_oferta) as total_ocupacion
        FROM ofertas_dashboard
        WHERE isco_code = d.isco_code
    ) total
    WHERE os.equivalence_id = p_equivalence_id
    GROUP BY d.isco_code, d.isco_label, total.total_ocupacion
    ORDER BY ofertas_count DESC
    LIMIT 5;
$$;
```

### UI: panel de impacto en modo expandido

Cuando el analista expande un grupo, agregar sección "Impacto en
ocupaciones":

```
▼ analizar datos  [auto]  ●●●●  92%
  
  Skills equivalentes:
  • analizar datos (representante) · 3.828 ofertas
  • realizar un análisis de datos · 987 ofertas
  • análisis de datos · 957 ofertas

  Impacto en ocupaciones:              ← NUEVO
  • Analista de datos (2511)     · 1.842 ofertas (38%)
  • Científico de datos (2519)   · 923 ofertas  (19%)
  • Analista financiero (2413)   · 445 ofertas  (9%)

  [Aprobar ✓]  [Editar ✏]  [Revertir ↩]
```

El impacto se carga lazy (al expandir, no al listar) para no
impactar performance de la lista paginada.

---

## Cambios por archivo

```
Python (extractor):
    skills_implicit_extractor.py
        → _check_equiv_staleness() — verificar si lookup cambió
        → _reload_equiv_lookup() — recargar desde Supabase
        → campo _equiv_last_loaded

Python (script):
    scripts/generate_skill_equivalences.py
        → calcular similitud_promedio y similitud_minima por grupo
        → guardar en skill_equivalences

Supabase (migrations):
    → ADD COLUMN updated_at + trigger (skill_equivalences)
    → ADD COLUMN similitud_promedio, similitud_minima
    → RPC get_latest_equiv_update()
    → RPC get_equivalencia_impacto()

Next.js (UI):
    app/admin/procesamiento/fabrica/equivalencias/page.tsx
        → mostrar similitud en cards colapsadas
        → agregar opción de ordenamiento por confianza
        → agregar panel de impacto en modo expandido (lazy)
        → invalidar cache del extractor post-aprobación
          (via llamada a get_latest_equiv_update en Supabase)
```

---

## Tests requeridos

```
Python:
test_equiv_staleness_detecta_cambio()
    → dado que un grupo fue aprobado después de la última carga
    → _check_equiv_staleness() retorna True
    → el lookup se recarga

test_equiv_staleness_sin_cambio()
    → dado que no hubo cambios
    → _check_equiv_staleness() retorna False
    → no se recarga (performance)

test_similitud_promedio_calculada()
    → dado un grupo con 3 miembros y similitudes conocidas
    → similitud_promedio es correcta

test_similitud_minima_calculada()
    → similitud_minima es el mínimo entre pares

React:
test_badge_confianza_verde()
    → dado similitud_promedio >= 0.92
    → badge muestra 4 círculos verdes

test_badge_confianza_rojo()
    → dado similitud_promedio < 0.85
    → badge muestra 1 círculo rojo

test_impacto_carga_lazy()
    → al expandir grupo → llama a get_equivalencia_impacto()
    → colapsado → no llama al RPC

test_ordenamiento_por_confianza()
    → seleccionar "Confianza ▲"
    → grupos con similitud_minima baja aparecen primero

Regresión:
test_aprobacion_no_rompe_matching()
    → aprobar un grupo
    → el extractor carga el lookup actualizado en el próximo run
    → el matching produce el mismo resultado para grupos no cambiados
```

---

## Criterio de done

```
□ Migration SQL ejecutada (updated_at + trigger + similitud_*)
□ RPCs get_latest_equiv_update() y get_equivalencia_impacto() creados
□ generate_skill_equivalences.py calcula y guarda similitudes
□ Extractor verifica staleness al iniciar cada run de matching
□ Cards muestran score de confianza con código de colores
□ Ordenamiento por confianza disponible en filtros
□ Panel de impacto en ocupaciones visible al expandir (lazy)
□ 9 tests pasando
□ Aprobar un grupo → verificar que el próximo run de matching
  usa el lookup actualizado sin intervención manual
□ No regresión: 97 tests Python en verde
□ No regresión: 933 tests React en verde
```

---

## Lo que NO hace este spec

- No regenera los grupos de clustering (eso es M-08b)
- No agrega nuevos candidatos de equivalencias
- No cambia el umbral de similitud del clustering
- No migra los grupos existentes con similitud retroactiva
  (solo los nuevos runs del script tendrán el score)
- No automatiza la revisión — siempre requiere aprobación humana
