# SPEC R — Validación de casos RAROS/borderline (no polivalentes)

**Fecha:** 2026-04-27
**Autor:** Claude + Gerardo
**Estado:** Draft — listo para entregar a Cyn
**Audiencia primaria:** Cynthia
**Pre-condición:** SPEC P aplicado, sync grande Supabase OK
**Complementa:** SPEC M (validación cambios) + SPEC Q (sospechas con hipótesis)

---

## 1. Por qué este spec

SPEC M valida los cambios YA aplicados. SPEC Q valida sospechas con HIPÓTESIS clara. **Este SPEC R cubre casos donde NO tenemos hipótesis específica** — son rarezas detectadas por queries que pueden ser:
- Errores de NLP (tareas vacías, skills count 0) que el matching "tapó"
- Casos donde el matcher "adivinó" sin información suficiente
- Reglas viejas no auditadas que arrastran problemas
- Decisiones automáticas en zona gris

Hasta ahora no los inspeccionamos porque eran difíciles de categorizar. Este spec entrega 90 ofertas para que Cyn ayude a clasificarlas.

---

## 2. Scope

**90 ofertas en 5 grupos:**

| Grupo | Tipo de rareza | N | Universo afectado |
|---|---|---:|---:|
| **D** | NLP defectuoso (tareas <30 chars o skills <3) | 15 | 4,781 ofertas con skills <3 + 3,148 con tareas vacías |
| **E** | Sin regla + score < 0.45 | 15 | 134 |
| **F** | ISCO FFAA (0xxx) | 20 | 21 (TODAS las que existen) |
| **G** | decision_metodo = "regla_zona_gris" | 15 | 1,500 |
| **H** | Reglas legacy de alta cobertura no auditadas | 25 | 5 reglas, 2,294 ofertas |

---

## 3. Detalle por grupo

### Grupo D — NLP defectuoso (15 ofertas)

**Sospecha:** el scraper no obtuvo descripción suficiente, o el LLM falló al extraer tareas/skills. El matching pudo "adivinar" basado en datos pobres.

**Universo:**
- 3,148 ofertas con `tareas_explicitas` < 30 caracteres
- 4,781 ofertas con `skills_demandados_total` < 3

**Lo que queremos saber:**
- ¿La oferta original tenía descripción suficiente o el problema es de scraping?
- Si scraping OK → ¿el LLM perdió la información que estaba ahí?
- ¿La clasificación actual es razonable o es producto del bias del modelo?

**Acción si Cyn confirma:**
- Si scraping OK + LLM falla → fix prompt NLP
- Si scraping incompleto → re-scrapear esas ofertas
- Si la clasificación es razonable a pesar del NLP pobre → marcar como "descripción incompleta pero rol claro por título"

### Grupo E — Sin regla + score bajo (15 ofertas)

**Sospecha:** el matcher no encontró ninguna regla aplicable Y el embedding semántico no encontró ocupación cercana (score < 0.45). El sistema asignó algo "adivinando".

**Universo:** 134 ofertas validadas con esta condición.

**Lo que queremos saber:**
- ¿El rol existe en ESCO pero el matcher no lo encontró?
- ¿El rol NO existe en ESCO (caso Catálogo MOL Argentino)?
- ¿La oferta tiene mala calidad (poca info para matchear)?

**Acción si Cyn confirma:**
- Si el rol está en ESCO y debería matchear: investigar por qué falla.
- Si el rol no está en ESCO: candidato a Catálogo MOL.

### Grupo F — ISCO FFAA / 0xxx (20 ofertas, TODAS las del universo)

**Sospecha:** Argentina mercado civil, no debería haber ofertas codificadas como Oficial FFAA, Suboficial, Tropa de las fuerzas armadas. Si tenemos 21 ofertas en ISCO 010/021/031, **probablemente todas son falsos positivos**.

**Universo:**
- 10 ofertas en ISCO 0110 (Oficial FFAA)
- 7 en ISCO 0210 (Suboficial)
- 4 en ISCO 0310 (Tropa)

**Lo que queremos saber:**
- ¿Son ofertas militares reales (raro en Argentina civil)?
- O ¿son ofertas de seguridad privada / vigilancia mal codificadas?

**Acción si Cyn confirma falsos positivos:**
- Crear regla de exclusión: ISCO 0xxx solo si la empresa es oficial FFAA.
- Re-rematch las afectadas.

### Grupo G — Zona gris (15 ofertas)

**Sospecha:** la regla aplicó pero el sistema marcó la decisión como "regla_zona_gris" — significa que el score estaba en borderline (entre 0.55 y 0.65) y la regla "salvó" la clasificación.

**Universo:** 1,500 ofertas con `decision_metodo='regla_zona_gris'`.

**Lo que queremos saber:**
- ¿La regla acertó al pisar el semántico borderline?
- ¿O el semántico tenía razón y la regla forzó algo equivocado?

### Grupo H — Reglas LEGACY de alta cobertura (25 ofertas)

**Sospecha:** reglas creadas antes de febrero 2026 y no auditadas desde entonces. Pueden tener targets desactualizados o condiciones obsoletas.

| Regla | Fecha | Cobertura | Sospecha |
|---|---|---:|---|
| R14_contador_auditor | 2026-01-22 | **1,199** | huge cobertura, no auditada hace 3 meses |
| R13_enfermero | 2026-01-23 | 337 | enfermería tiene muchos sub-roles |
| R139_repositor | 2026-01-23 | 311 | rol comercial PyME polivalente probable |
| R207_peon_cocina | 2026-01-22 | 267 | peón cocina vs ayudante cocina |
| R137_tareas_picking_crossdocking | 2026-01-22 | 180 | revisar si solapa con R353 nueva |

**Acción si Cyn detecta problemas en una regla:** SPEC siguiente con fix de target o exclusiones.

---

## 4. Entregable a Cyn

```
exports/spec_r/
├── INSTRUCCIONES_CYN.md      (instructivo corto)
└── ids_validar_cyn.txt       (90 IDs agrupados por grupo)
```

---

## 5. Flujo

Idéntico a SPEC M y Q:
1. Cyn abre `/admin/validacion`
2. Toma un ID del archivo
3. Procesa con OK / Issue / Revisar habitual
4. Si crea issue, incluye su análisis (como hizo el 27-04)

---

## 6. Cronograma

| Fase | Duración |
|---|---:|
| Validación humana | ~2-2.5 hs |
| Análisis post-validación | 30 min |
| Decisiones de fix | 1 hr |
| Aplicación de fixes | 2-4 hs (variable según hallazgos) |

---

## 7. Decisiones según hallazgos

### Si Grupo D revela problema masivo NLP
→ SPEC dedicado a fix de prompt LLM o regex de extracción de tareas.

### Si Grupo E confirma rol no representado en ESCO
→ Aporta candidatos al Catálogo MOL Argentino.

### Si Grupo F confirma falsos positivos FFAA
→ Fix sistémico simple: exclusión de palabras clave (ej: "fuerzas armadas", "ejército") en reglas de seguridad/vigilancia.

### Si Grupo G muestra que zona gris generalmente acierta
→ Validar política E del SPEC H (umbral fallback 0.59-0.61).

### Si Grupo H detecta reglas obsoletas
→ Plan de auditoría de reglas legacy (similar a SPEC O M3).

---

## 8. Lo que este spec NO hace

- NO incluye casos polivalentes (eso está en SPEC Q grupo A).
- NO toca pipeline ni reglas hasta tener feedback Cyn.
- NO sustituye SPEC M ni Q.

---

## 9. Próximo paso

Una vez Cyn termine:
- Claude consume issues nuevos.
- Por grupo, identifica patrones (¿X% de Grupo F son falsos positivos?).
- Propone batch de fixes priorizado.
