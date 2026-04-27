# SPEC M — Validación de muestra (90 ofertas)

**Para:** Cynthia
**Tiempo estimado:** ~2-2.5 hs
**Archivo a completar:** `spec_m_muestra_validacion_cyn.csv`

---

## Contexto

Tras los SPECs E+G+H+J+K+N+O+P, **6,781 ofertas cambiaron de ocupación ISCO 4-dig**. Antes de dar el trabajo por estable, te pedimos validar 90 ofertas dirigidas para confirmar que los cambios son mejoras reales.

**No es revisión exhaustiva** — es muestra estratificada con criterios claros.

---

## Cómo usar el CSV

Abrí el archivo en Google Sheets o LibreOffice. Tiene 90 filas y 14 columnas.

**Columnas que ya vienen llenas (solo lectura):**
| Columna | Qué muestra |
|---|---|
| `tier` | 1, 2 o 3 (ver criterio abajo) |
| `isco_focus` | ISCO bajo análisis |
| `id_oferta` | ID único |
| `titulo` | Título original del aviso |
| `isco_antes` / `esco_antes` | Cómo estaba codificada ANTES |
| `isco_despues` / `esco_despues` | Cómo está codificada AHORA |
| `esco_code_granular` | Código ESCO granular (vacío si no aplica/aún sin actualizar) |
| `regla_aplicada` | Qué regla disparó (si hubo) |
| `url_admin` | Link directo al admin del dashboard |

**Columnas que vos completás:**
| Columna | Qué poner |
|---|---|
| `resultado` | Una de: **OK** / **MEJORA** / **PEOR** / **AMBOS_MAL** / **DUDOSA** |
| `comentario` | (opcional) explicación breve si es PEOR / AMBOS_MAL |
| `isco_correcto` | (opcional) si conocés el ISCO que debería ser |

---

## Criterios de evaluación

Para cada oferta:

1. **Hacé clic en `url_admin`** → te abre el aviso original con título, descripción, tareas.
2. **Leé el aviso real.**
3. **Compará** con `esco_despues` (la nueva clasificación) y `esco_antes` (la vieja).
4. **Marcá en `resultado`:**

| Marca | Cuándo |
|---|---|
| **OK** | El nuevo está bien (ya estaba bien o cambió a algo igual de bueno) |
| **MEJORA** | El nuevo es claramente mejor que el viejo |
| **PEOR** | El nuevo es peor que el viejo (regresión) |
| **AMBOS_MAL** | Ni el nuevo ni el viejo son correctos |
| **DUDOSA** | No estoy segura |

**Si marcás PEOR o AMBOS_MAL:** poné en `isco_correcto` qué ISCO sería correcto, y en `comentario` por qué (1 línea alcanza).

---

## Distribución de la muestra

Total: **90 ofertas** estratificadas por tipo de cambio.

| Tier | Tipo | ISCOs cubiertos | N |
|---|---|---|---:|
| **1** | ISCOs que más se vaciaron — potenciales fallbacks pre-fix | 8160 (prensado fruta), 5223, 4311, 1349, 2431 | 50 |
| **2** | Cambios puntuales — muestra chica con alta variabilidad | 3435, 3123, 7412, 8322, 2269 | 25 |
| **3** | ISCOs que más crecieron — validar ganancia | 9329 (trabajador fábrica), 9333 (mozo almacén), 2411 (analista contable) | 15 |

---

## Ejemplo de lo que vas a ver

```
tier: 1
isco_focus: 8160
id_oferta: 1118098190
titulo: Operario de producción zona Pilar
isco_antes: 8160 (prensado de fruta)
isco_despues: 9329 (trabajador de fábrica)
url_admin: https://mol-nextjs.vercel.app/admin/validacion?id=1118098190
```

→ Abrís el link, leés el aviso, ves que es operario genérico de planta industrial, no de fruta. Marcás `MEJORA`. Listo.

---

## Cuando termines

Mandanos el CSV completo (Google Sheets exportado, o el archivo modificado).

Calculamos:
- % MEJORA + OK
- % PEOR (regresiones)
- % AMBOS_MAL (límites del sistema)

Y decidimos:
- **>80% MEJORA+OK:** sistema validado, seguimos.
- **60-80%:** documentar caveats, seguimos con cuidado.
- **<60%:** investigar regresiones antes de avanzar.

---

## Si encontrás patrones (extra)

Si ves que MUCHAS ofertas de un mismo `regla_aplicada` están **PEOR**, marcalo en `comentario` con "REGLA-X" para que detectemos rápido. No es obligatorio.

---

## Tiempo estimado

- 90 ofertas × ~90 segundos cada una = **~135 minutos**
- Distribuible en 2-3 sesiones

Si querés repartir con Diego, agarrá Tier 1 (50) y dale Tier 2+3 (40), o como prefieran.

---

**Cualquier duda escribinos.** Lo más importante es que NO te frenes en casos dudosos — marcá `DUDOSA` y seguí.
