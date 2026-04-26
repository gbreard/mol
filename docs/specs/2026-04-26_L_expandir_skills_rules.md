# SPEC L — Expansión automática de `skills_rules.json` desde ESCO oficial

**Fecha:** 2026-04-26
**Autor:** Claude + Gerardo
**Estado:** Draft — listo para implementar
**Scope:** Las 27 reglas activas en `config/skills_rules.json` (reglas RS_*)
**Dependencia:** SPEC J (reglas matching ya tienen `esco_code` válido)
**Bloquea:** Sync grande Supabase (preferimos correrlo después)

---

## 1. Motivación

Tras SPEC E + G + H + J + K, el matching de ofertas a ocupaciones ESCO funciona mucho mejor. Pero el catálogo de **reglas de skills** (`skills_rules.json`) está **subdimensionado**:

- 27 reglas activas, **41 skills forzadas totales**
- **Promedio 1.5 skills por regla**
- 18 reglas (67%) fuerzan solo **1 skill**
- Cobertura: aplican a **26,274 ofertas validadas** (50% del total) — pero cada una solo recibe 1-2 skills forzadas

Ejemplo concreto:
- `RS06_vendedor_comercial` fuerza solo `"realizar ventas activas"` y aplica a 5,100 ofertas. Cada vendedor en BD tiene UNA skill forzada — el resto viene del semántico.
- `RS01_desarrollador_python` fuerza solo `"Python"` cuando un desarrollador real usa Django, Git, SQL, frameworks, etc.

### Problema secundario: inconsistencias menores

- `RS26_peon_cocina` tiene **3 URIs inválidas** (UUIDs con ceros padding — generados durante tests probablemente).
- `RS27_gmp_sop_procedimientos`: regla activa pero **sin uso** en ninguna oferta validada.

---

## 2. Hallazgo Fase 0

Analizando dónde aplican las RS, la mayoría tiene un esco_code dominante claro:

| Regla RS | esco_code dominante | Skills forzadas hoy | Skills oficiales disponibles |
|---|---|---:|---:|
| RS01_desarrollador_python | 2512.4 (desarrollador SW) | 1 | 30+ esenciales |
| RS02_contador_contable | 2411.1 (contable) | 3 | 30+ esenciales |
| RS03_vigilador_seguridad | 5414.1 (vigilante) | 2 | 20+ esenciales |
| RS04_chofer_conductor | 8322.2 (conductor grúa) | 1 | 25+ esenciales |
| RS06_vendedor_comercial | 3322.1 (representante comercial) | 1 | 32 esenciales |
| ... | | | |

ESCO oficial tiene skills `essential_for` autoritativas por ocupación. **Podemos expandir las RS automáticamente** sin curación humana.

---

## 3. Propuesta — Opción C (expansión automática)

### 3.1 Algoritmo

Para cada regla RS activa:

1. **Identificar esco_code dominante**: la ocupación ESCO más frecuente entre las ofertas donde la RS aplicó (consultar `ofertas_esco_matching.titulo_esco_code` filtrando por `skills_regla_aplicada = rid`).
2. **Tomar top 5 skills `essential_for`** de ese esco_code (desde `esco_occupation_skills.json`).
3. **Mergear con skills existentes** de la regla:
   - Skills ya presentes (con URI válida) se preservan.
   - Skills nuevas se agregan con `fuente: "esco_oficial_auto"`.
   - Si una skill ya existe (por URI) no se duplica.
4. **Eliminar URIs inválidas** detectadas en Fase 0.

### 3.2 Limpieza adicional

- **RS26_peon_cocina**: eliminar las 3 URIs falsas. Reemplazar por top 5 essential de su esco_code dominante (probablemente 9412.1).
- **RS27_gmp_sop_procedimientos**: marcar `activa: false` (sin uso documentado).

### 3.3 Resultado esperado

| Métrica | Antes | Después |
|---|---:|---:|
| Reglas activas | 27 | 26 (sin RS27) |
| Skills forzadas totales | 41 | ~150 |
| Promedio skills/regla | 1.5 | ~5.7 |
| URIs inválidas | 3 | 0 |
| Reglas con 1 skill | 18 | 0 |

---

## 4. Diseño técnico

### 4.1 Script `scripts/embeddings/expand_skills_rules.py`

Pseudocódigo:

```python
for rid, rule in skills_rules['reglas_forzar_skills'].items():
    if not rule.get('activa', True): continue

    # 1. Skills existentes (con URI válida)
    existing_uris = {sk['skill_uri'] for sk in rule['accion']['forzar_skills']
                     if sk.get('skill_uri') and sk['skill_uri'] in valid_uris}
    cleaned = [sk for sk in rule['accion']['forzar_skills']
               if sk.get('skill_uri') in valid_uris]

    # 2. esco_code dominante
    dom_code = query_dominant_esco(rid)  # SELECT titulo_esco_code, COUNT(*) ... LIMIT 1

    # 3. top 5 essential del code
    top5 = get_essential_skills(dom_code, k=5)
    for sk in top5:
        if sk['uri'] not in existing_uris:
            cleaned.append({
                'skill_esco': sk['label'],
                'skill_uri': sk['uri'],
                'fuente': 'esco_oficial_auto',
                'esco_code_target': dom_code,
            })

    rule['accion']['forzar_skills'] = cleaned
```

### 4.2 Backup

Backup `skills_rules.json.pre_spec_l_{timestamp}.bak` antes de escribir.

### 4.3 No re-corre matching

A diferencia de SPEC J, **NO necesitamos re-correr matching** después. Las RS se aplican durante extracción de skills, y el flag `filtrar_por_trust=False` en producción no toca skills_regla. Las skills forzadas viejas siguen presentes en BD; las nuevas RS expandidas se aplicarán a **ofertas nuevas o re-procesadas**.

**Para que las 26K ofertas validadas reciban las skills nuevas, hay que re-extraer.** Costo: ~6-7h retropropagación adicional.

### 4.4 Decisión: ¿re-extraer o no?

- **NO re-extraer**: skills antiguas en BD mantienen el set viejo (1-2 skills forzadas). Nuevas ofertas reciben set expandido.
- **SÍ re-extraer**: 6-7h retropropagación. Todas las 26K ofertas afectadas tienen skills enriquecidas.

**Recomendado: SÍ re-extraer**. Aprovechamos que el sync grande aún no corrió. Re-extraer + sync único.

---

## 5. Plan por fases

### Fase 1 — Implementación (~30 min)
- Script `expand_skills_rules.py`
- Output: `config/skills_rules.json` actualizado + reporte de cambios
- Backup automático

### Fase 2 — Tests (~30 min)
- Verificar URIs válidas post-expansión
- Verificar que `RS27` queda inactiva
- Test de regresión sobre Sprint canónicos

### Fase 3 — Re-extracción (~6-7h ejecución)
- Limpiar `spec_e_retro_progress` (las 49,295 que ya retropropagamos)
- Re-correr `retropropagar_skills_spec_e.py`
- Las RS expandidas se aplicarán durante extract_skills_dual

### Fase 4 — Sync grande (~2-3h)
- Sync incremental Supabase con todos los cambios E+G+H+J+K+L

---

## 6. Riesgos

### 6.1 Skills forzadas demasiado genéricas
Las top 5 esenciales de ESCO pueden ser MUY genéricas (ej. "trabajar en equipo" como esencial de muchas ocupaciones). Si todas las reglas terminan con las mismas skills genéricas, perdemos diferenciación.

**Mitigación**: filtrar top 5 priorizando skills NO transversales (no L1=T*). Si todas las top son transversales, tomar top 3 essential + top 2 optional sectoriales.

### 6.2 esco_code dominante no representa toda la regla
Una RS puede aplicar a 3-4 ocupaciones distintas. Tomar solo el dominante deja afuera las skills de las otras.

**Mitigación**: si la 2da ocupación tiene >25% del uso, tomar también top 2 essentials de ella.

### 6.3 Cambio masivo en BD
Las 26,274 ofertas con RS aplicada van a recibir 4-9 skills nuevas cada una. Total ~120K skills nuevas en BD.

**Mitigación**: el filtro SPEC K post-extracción debería filtrar las que no son coherentes con el ESCO específico de cada oferta. Y la métrica de "L2 incompatible" debería seguir en 0%.

---

## 7. Cronograma

| Fase | Duración |
|---|---|
| 1 — Implementación + tests | 1 h |
| 2 — Re-extracción 49K | 6-7 h |
| 3 — Sync grande | 2-3 h |
| **Total** | **~10 h** |

---

## 8. Lo que este spec NO hace

- NO toca el matcher (`match_ofertas_v3`).
- NO modifica las 348 reglas matching.
- NO hace curación humana de skills (todo es automático desde ESCO oficial).
- NO cambia umbrales ni políticas de filtros existentes.
