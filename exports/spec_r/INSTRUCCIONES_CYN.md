# SPEC R — Validación de casos RAROS (no polivalentes)

**Para:** Cynthia
**Tiempo estimado:** ~2-2.5 hs (90 ofertas × ~90 seg)
**Archivo con IDs:** `ids_validar_cyn.txt`

---

## ¿Qué tiene de distinto con SPEC M y SPEC Q?

| Spec | Qué valida |
|---|---|
| **M** | Cambios YA aplicados (¿el cambio fue mejora real?) |
| **Q** | Sospechas con HIPÓTESIS clara (polivalentes, targets absurdos) |
| **R** | **Rarezas SIN hipótesis específica** (necesitamos clasificar antes de proponer fix) |

---

## Cómo trabajarlas

Idéntico a SPEC M y Q:
1. Abrí `/admin/validacion`
2. Tomá ID del archivo `ids_validar_cyn.txt`
3. Buscalo o entrá directo: `https://mol-nextjs.vercel.app/admin/validacion?id=XXXXXXX`
4. Marcás OK / creás issue / Revisar como siempre

---

## Los 5 grupos

### 🟦 Grupo D — NLP DEFECTUOSO (15 ofertas)
**Sospecha:** scraping incompleto o LLM falló al extraer tareas/skills. El matching pudo ser adivinado a partir del título.

**Lo que queremos saber:**
- ¿La oferta original tenía descripción suficiente?
- ¿La clasificación es razonable a pesar del NLP pobre?

### 🟨 Grupo E — SIN REGLA + SCORE BAJO (15 ofertas)
**Sospecha:** el matcher no encontró regla aplicable Y el embedding semántico tampoco encontró ocupación cercana. El sistema "adivinó".

**Lo que queremos saber:**
- ¿El rol existe en ESCO pero el sistema falló al detectarlo?
- ¿O es un rol nuevo no representado (candidato Catálogo MOL)?

### 🟥 Grupo F — ISCO FUERZAS ARMADAS (20 ofertas — TODAS las del universo)
**Sospecha FUERTE:** Argentina mercado civil. Si tenemos 21 ofertas en ISCO 0110 (Oficial FFAA), 0210 (Suboficial), 0310 (Tropa), **probablemente todas son falsos positivos**.

**Lo que queremos saber:**
- ¿Son ofertas militares reales o seguridad privada/vigilancia mal codificadas?

**Esto es MUY rápido:** las 20 ofertas pueden revisarse en 10-15 min y probablemente todas sean PEOR/AMBOS_MAL.

### 🟪 Grupo G — ZONA GRIS (15 ofertas)
**Sospecha:** la regla aplicó en zona dudosa (score borderline 0.55-0.65). El sistema marcó la decisión como `regla_zona_gris`.

**Lo que queremos saber:**
- ¿La regla acertó al pisar el semántico borderline?
- ¿O el semántico tenía razón y la regla forzó algo equivocado?

### 🟫 Grupo H — REGLAS LEGACY ALTA COBERTURA (25 ofertas)
**Sospecha:** reglas creadas antes de febrero 2026 (>3 meses sin auditar) que clasifican muchas ofertas. Pueden tener targets desactualizados.

**Reglas en este grupo:**
- R14_contador_auditor (¡1,199 ofertas!)
- R13_enfermero (337)
- R139_repositor (311)
- R207_peon_cocina (267)
- R137_tareas_picking_crossdocking (180)

5 ofertas por regla = 25 total.

**Lo que queremos saber:**
- ¿La regla sigue siendo correcta o el target quedó obsoleto?
- ¿Hay solapamiento con reglas nuevas (ej: R137 vs R353)?

---

## Cómo evaluar

Para cada oferta:
1. Leé el aviso real (título, descripción, tareas)
2. Mirá la clasificación actual en la UI
3. Decidí:
   - **OK** → razonable
   - **Issue** → mal clasificado (proponé ESCO correcto + justificación, como siempre)
   - **Revisar** → no estás segura

---

## Distribución y reparto

- **90 ofertas total**
- Sugerencia de reparto:
  - Cyn: D + E + F = 50 ofertas (~75 min)
  - Diego: G + H = 40 ofertas (~60 min)

O lo dividís a gusto. **Grupo F (FFAA) es el más rápido** — empezá por ahí, capaz son todos errores y resolvés mucho impacto en 15 min.

---

## Cuando termines

Avisanos. Vamos a:
- Contar issues por grupo
- Identificar patrones por sub-categoría
- Priorizar fixes según impacto
  - Si Grupo F confirma falsos positivos → fix simple, alto impacto
  - Si Grupo H detecta reglas obsoletas → plan de auditoría de reglas legacy

---

## Importante

- **No te frenes en casos dudosos** — marcá "Revisar".
- **Si encontrás un patrón en un grupo** (ej: "todas las del Grupo F son seguridad privada"), ponelo en el primer issue y eso ya nos basta para el fix.
