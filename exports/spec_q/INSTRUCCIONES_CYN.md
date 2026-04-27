# SPEC Q — Validación de casos sospechosos identificados por Claude

**Para:** Cynthia
**Tiempo estimado:** ~2-3 hs (101 ofertas × ~90 seg)
**Archivo con IDs:** `ids_validar_cyn.txt`
**Complementa:** SPEC M (que ya recibiste)

---

## ¿Qué tiene de distinto con SPEC M?

- **SPEC M** (90 ofertas): valida si los CAMBIOS aplicados fueron correctos.
- **SPEC Q** (101 ofertas): valida si quedan casos donde el sistema SIGUE MAL — sospechas que detectamos al revisar reglas pero no resolvimos todavía.

Si confirmás los casos de SPEC Q, eso desbloquea fixes adicionales (similar a las 6 ofertas que reportaste el 27-04 con resultado SPEC P).

---

## Cómo trabajarlas

Idéntico al SPEC M:

1. Abrí `/admin/validacion`.
2. Tomá un ID del archivo `ids_validar_cyn.txt`.
3. Buscalo o entrá directo: `https://mol-nextjs.vercel.app/admin/validacion?id=XXXXXXX`
4. Marcás OK / creás issue / Revisar como siempre.

---

## Los 3 grupos a revisar

### 🟦 Grupo A — Perfiles POLIVALENTES (50 ofertas)

Sospechamos que ESCO **no representa bien** estos roles argentinos porque concentran skills que ESCO separa en oficios distintos. Ej: técnico mantenimiento edilicio que sabe electricidad+plomería+climatización; mozo argentino que atiende+cobra+arma mesa.

**Lo que queremos saber:** ¿el ESCO actual es razonable para el rol pedido, o es genuinamente otra ocupación?

**Reglas en este grupo:**
- R162 técnico mantenimiento edilicio
- R110 técnico mantenimiento industrial
- R49 jefe genérico
- R170 asesor comercial
- R34 cajero
- R166 cocinero planchero
- R31 mozo / camarero
- R109 ejecutivo de ventas
- R15 customer care
- R226 analista RRHH

**Si confirmás "ESCO no representa bien":** alimenta el debate de equipo sobre crear códigos `MOL.AR.*` locales (Catálogo MOL Argentino).

### 🟨 Grupo B — Targets ULTRA-ESPECÍFICOS (27 ofertas)

Sospechamos que ofertas genéricas están cayendo en códigos ESCO **demasiado específicos** y absurdos. Ej: "Gerente de ventas" → "director de promoción" (1221.3.3); reglas de compras → "comprador de café verde" (3323.2.1).

**Lo que queremos saber:** ¿el código ESCO específico es coherente con el aviso, o es un fallback aleatorio?

**Códigos en este grupo:**
- 3331.2.1 especialista importación/exportación
- 3323.2.2 comprador de TIC
- 1221.3.3 director de promoción
- 3321.3.1 asesor de seguros
- 3323.2.1 comprador café verde
- 2131.4.2 bioquímico
- 1221.3.2 responsable marketing
- 5132.1.1 barista
- 1431.2.1 jefe de sala

**Si confirmás absurdo en 2+ casos del mismo código:** activamos fix de regla automatizado.

### 🟥 Grupo C — Reglas que PISAN al semántico (24 ofertas)

Hay reglas donde el matcher semántico (basado en embeddings ESCO) propone una ocupación distinta a la regla — y la regla GANA por prioridad. Eso es bueno SI la regla corrige al semántico, pero malo SI la regla está pisando una ocupación más pertinente.

**Lo que queremos saber:** ¿la regla está bien o el semántico tenía razón?

**Reglas en este grupo:**
- R240 operario producción
- R229 analista comercial
- R48 secretaria admin
- R241 técnico IT
- R323 atención al público
- R305 electromecánico
- R91 jefe mantenimiento
- R30 community manager

**Si la regla está peor que el semántico:** desactivamos la regla.

---

## Cómo evaluar cada caso

Para cada oferta:

1. Leé el aviso real (título, descripción, tareas).
2. Mirá la **clasificación actual** que muestra la UI.
3. Decidí:
   - **OK** → la clasificación es razonable
   - **Issue** → la clasificación es errónea (incluí ESCO sugerido + justificación, como hiciste el 27-04)
   - **Revisar** → no estás segura

---

## Distribución y reparto

- **101 ofertas total**
- Si querés repartir con Diego: vos Grupo A (50) + Grupo B (27) = 77 — Diego Grupo C (24). O lo dividís a gusto.

---

## Cuando termines

Avisanos. Vamos a:
- Contar issues por grupo
- Identificar patrones (¿muchos errores en una regla? ¿muchos en un código?)
- Decidir fixes a aplicar

Igual que con SPEC P, los issues que crees alimentan training_pairs para fine-tuning futuro.

---

## Importante

Lo más importante: **no te frenes en casos dudosos**. Marcá "Revisar" y seguí.

Y si encontrás un patrón claro (ej: "todas las ofertas R49 que vi son polivalentes, ninguna calza con el target"), ponelo en el primer issue del grupo y eso ya nos basta para tomar la decisión sin que revises los demás.
