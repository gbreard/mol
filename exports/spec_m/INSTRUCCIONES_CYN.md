# SPEC M — Validación de muestra (90 ofertas)

**Para:** Cynthia
**Tiempo estimado:** ~2-2.5 hs (90 ofertas × ~90 seg)
**Archivo con IDs:** `ids_validar_cyn.txt`

---

## Contexto rápido

Después de los SPECs E+G+H+J+K+N+O+P, **6,781 ofertas cambiaron de ocupación ISCO**. Antes de dar por estable el sistema, te pedimos validar 90 ofertas dirigidas para confirmar que los cambios son mejoras reales.

**No es revisión exhaustiva** — es muestra estratificada por criterios.

---

## Cómo trabajarlas

1. Abrí el dashboard → **`/admin/validacion`**.
2. Tomá un ID del archivo `ids_validar_cyn.txt`.
3. Buscalo en la lista (filtro por id_oferta) o entrá directo con la URL:
   ```
   https://mol-nextjs.vercel.app/admin/validacion?id=XXXXXXX
   ```
4. Mirás el aviso, evaluás la clasificación actual, y marcás en la UI usando el flujo habitual:
   - **OK** si está bien
   - **Error** si hay algo mal (creás issue con el detalle como hiciste el 27-04)
   - **Revisar** si dudás

---

## Qué evaluar en cada oferta

### En cada caso, leé el aviso y compará con la clasificación actual:

- ¿El **título ESCO** representa bien el rol pedido?
- ¿La **descripción ESCO** coincide con las tareas reales?
- ¿Las **skills** asignadas son pertinentes (sin alucinaciones tipo "javanés", "peces", etc.)?
- ¿El **área funcional** y **sector** están bien?

### Para tomar la decisión:

| Resultado | Cuándo |
|---|---|
| **OK** | El nuevo está bien (ya estaba bien o cambió a algo igual de bueno) |
| **Error / Issue** | El nuevo es peor o ambos son malos → crear issue con tu propuesta de ESCO correcto (como hacés siempre) |
| **Revisar** | No estás segura |

**Si creás issue:** seguí el formato que ya venís usando — incluye **ESCO sugerido** (código + label), justificación y skills correctas/incorrectas. Ya viste el flujo con las 6 ofertas del 27-04 (ej. 8299423434, 7879857202).

---

## Distribución de la muestra

El archivo `ids_validar_cyn.txt` agrupa los 90 IDs en 3 tiers. Te conviene ir tier por tier:

### Tier 1 — ISCOs que más se vaciaron (50 ofertas)
ISCOs que perdieron muchas ofertas tras los fixes — confirmar que el cambio fue MEJORA y no regresión.

| ISCO antes | Cambio típico | N |
|---|---|---:|
| **8160** | prensado de fruta → trabajador de fábrica / mozo de almacén | 10 |
| **5223** | vendedor especializado → coordinador restaurante / otros | 10 |
| **4311** | empleado de contabilidad → analista contable | 10 |
| **1349** | (varios fallbacks pre-fix) | 10 |
| **2431** | director relaciones clientes → especialista mercadotecnia | 10 |

### Tier 2 — Cambios puntuales (25 ofertas)
ISCOs con muestra chica donde la variabilidad puede ser alta.

ISCOs: **3435, 3123, 7412, 8322, 2269** (5 c/u)

### Tier 3 — ISCOs que más crecieron (15 ofertas)
ISCOs que recibieron muchas ofertas nuevas — validar que efectivamente les corresponde estar ahí.

| ISCO ahora | Etiqueta | N |
|---|---|---:|
| **9329** | trabajador de fábrica | 5 |
| **9333** | mozo de almacén | 5 |
| **2411** | analista contable | 5 |

---

## Tiempo estimado y reparto

- **90 ofertas × ~90 seg = ~135 min**
- Si querés repartir con Diego: vos T1 (50), él T2+T3 (40). O dividís a gusto.

---

## Cuando termines

Avisanos. Vamos a calcular sobre tus revisiones:
- % de OK + MEJORA
- % de errores (issues nuevos creados)
- Patrones recurrentes (si una regla específica genera varios errores)

Y decidimos si el sistema está listo para etapa siguiente o si hay que volver a iterar.

---

## Si encontrás un patrón

Si ves que **muchos errores caen sobre la misma `regla_aplicada`** (columna en el archivo), avisanos antes de seguir — quizás hay un fix sistémico que ahorra tiempo.

---

**Lo más importante:** no te frenes en casos dudosos. Marcá "Revisar" o creá un issue con `prioridad: baja` y seguí.
