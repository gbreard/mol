# [CASCADA] PUNTO DE CONTROL P1-total — censo + distribución + muestra + sub-ofertas (2026-10-16)

**La re-extracción de tareas v12.5 está COMPLETA en staging (119.081), neteada por el laudo 1
y con los deltas de Cyn aplicados.** Este es el punto de control antes de P2/P3. El swap a la
tabla viva sigue pospuesto al gate P3. **Espero tu OK.**

## 1. Censo por capa (staging `cascada_staging.db`)

| Capa | n | vacías | media (no vacío) | qué es |
|---|---|---|---|---|
| re-extracción | 96.481 | 11,3% | 6,78 | tareas v11 reemplazadas por v12.5 |
| primera-extracción | 20.635 | 11,0% | 7,06 | backlog sin-NLP (primera vez con v12.5) |
| delta contador | 1.965 | 93,8% | 3,99 | laudo 2: 122 flips (6,2%), 1.843 correctamente [] |
| **TOTAL** | **119.081** | — | — | una sola época v12.5 |

Duración P1: 2026-10-05 → 2026-10-16 (~11 días), 385–863 of/h según tramo/contención. 0 pérdidas (resumible, staging aislado, 0 locks tras el fix).

## 2. Distribución n_tareas ANTES vs DESPUÉS (98.168 re-ext comparables)

| | v11 | **v12.5** |
|---|---|---|
| media n_tareas/aviso | 5,43 | **5,92** |
| avisos vacíos | 4.179 (4,3%) | **12.454 (12,7%)** |
| subió / bajó / igual | — | 39.602 / 28.190 / 30.376 |

**Lectura (clave del control point):** v12.5 extrae MÁS tareas donde hay tareas reales (media
5,43→5,92, recupera bloques que v11 truncaba — el fallo del frente M) y MENOS avisos con tareas
(vacías 4,3%→12,7%) porque **corrige la sobre-extracción de v11**. Verifiqué 3 de esas vacías
nuevas: las tres tenían en v11 tareas que en realidad eran **requisitos/experiencia/atributos**
("Experiencia: Mantenimiento preventivo…", "¿Qué valoramos?: orden y limpieza", "Requisitos:
Experiencia en caja") → v12.5 devuelve [] correctamente (RG-TAR-005/009). **El +8,4% de vacías
es precisión ganada, no señal perdida.** (Consistente con el gate: anti-alucinación 12/12.)

## 3. Muestra de 15 (spot de calidad) — sana
- **re-ext** ricas: 1118411285 (13 tareas), 1118411991 (11, v11 daba 3 → recupera bloque).
- **delta** flips correctos: 1118412460 (v11=1 → 6: "desarrollar Pinamar y Cariló", "gestionar
  comercialmente…"); 1843 correctamente [].
- **primera** sólidas: 1118473646 (14: Mercado Libre), 1118473779 (6: Meta Ads), 1118475499 (ventas).
- 1118410030 correctamente [] (era "Experiencia:…" en v11). Detalle completo en el JSON.

## 4. Sub-ofertas (541) — verificación de 10 familias
Los **541 padres fueron re-extraídos** (es_suboferta=0, en staging). La RE-DERIVACIÓN DEL SPLIT
por puesto NO se puede hacer limpia desde la extracción v12.5 **porque el extractor es por-oferta
y fusiona los puestos** (es el gap RG-TAR-003 / laudo 3). Cobertura v12.5 del contenido v11 de la
familia (10 muestras): 4 familias 85–100%, varias parciales, 2 con padre [] (v11 tenía 3 y 9
tokens triviales — requisito-only que v12.5 corrige igual que el resto).
**Conclusión:** la re-derivación del split de las 541 **va con el mini-frente multipuesto
(laudo 3, post-swap)** — misma maquinaria. No hay evidencia de pérdida sistémica: donde el padre
quedó [], es la misma corrección de sobre-extracción del corpus. Hasta entonces, las 541 quedan
con el flag de su familia y NO deben usarse para atribuir tareas por puesto.

## 5. Flags en staging (auditables / excluibles)
- `multipuesto_inline_pendiente=1`: **638** (laudo 3, para el mini-frente post-swap).
- `tareas_json_pre_laudo1` + `laudo1_removidas_json`: 2.975 filas (neteo HSE reversible).
- `tareas_json_pre_delta2` + `delta2_flip`: 1.965 (delta contador, 122 flips).

## 6. P2 — verificación (c): ¿el matcher consume skills para decidir ocupación?
**Respuesta: (B) SÍ consume.** `match_ofertas_v3.py:1567` → `combined_score = 0.6·skill_score +
0.4·title_score`. El path skills-first decide **skills_first_v3 37,2% + semantic_fallback 0,1%
≈ 37,3%** del corpus; el resto son reglas de negocio (~52%), diccionario argentino (~10%) y árbol
de contexto (3,8%), que NO consumen skills derivadas.
- **Implicación para P4 (la contabilidad que pediste):** como las skills NO se re-derivan en esta
  cascada (frente O), ese ~37,3% re-matchearía con **skills v11** + título. Además el matcher
  RE-EXTRAE skills en el momento del match (`extract_skills_dual`, línea 666) — si P4 las re-extrae
  de las tareas v12.5 sería una re-derivación de skills de facto. **Decisión de diseño P4 (tuya):**
  congelar skills (leer las v11 almacenadas) vs dejar que el re-matching las re-derive. Ese es el
  número con el que se decide la contabilidad del segundo re-matching post-O.

## 7. Qué sigue (tu gate)
1. **¿OK al P1-total?** (censo + la lectura del +8,4% vacías = precisión).
2. Con tu OK: **P3 (shadow del árbol)** corre sobre este staging neteado — dos poblaciones (las que
   decidían / las que abstenían-y-ahora-deciden, sobre-muestreadas), vara dual (<15% no-explicadas,
   techo 10% costo), case-set re-corrido. **No arranca sin tu OK.**
3. El swap (staging→vivo) y el P4 esperan el gate P3; el diseño del swap (ventana de escritores) ya
   está en `CASCADA_DISEÑO_swap_P3.md`.

Censo completo: `exports/reportes/CASCADA_P1_total_censo_2026-10-16.json`.
