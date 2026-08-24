# M — P0b: fuente real del `01` + anatomía del clasificador de escenarios

**Fecha:** 2026-08-23 · **Branch:** `feat/export-colegas-postL`
**Dos entregas:** (1) de qué fuente lee el `01` — **caso 2, ya lee local**; (2) la descripción del
`02` para laudar si se re-corre tal cual.

---

## 1. La fuente del `01` — **ya leía local. No había bloqueo por ahí.**

Verificado en código (`scripts/01_descargar_snapshot.py`, listas `TABLAS_SQLITE` y
`TABLAS_SUPABASE_FULL`). Las tres tablas que la cadena del export necesita salen **todas de la
SQLite local**:

| Tabla en el sandbox | Origen real | Cómo |
|---|---|---|
| `ofertas_dashboard` | **SQLite local** | JOIN `ofertas` + `ofertas_nlp` + `ofertas_esco_matching` (D-007) |
| `ofertas_skills` | **SQLite local** | ← `ofertas_esco_skills_detalle` |
| `ofertas_skills_clasificadas` | — | la produce el `02`, no el `01` |

Supabase aporta **solo 5 tablas que no participan del export**: `esco_argentino`,
`emergentes_pendientes`, `tension_ocupaciones`, `issues`, `sistema_estado` (+ columnas de
`skills_embeddings`). Confirma lo que decís: es consumidor paralelo, no eslabón de la cadena.

Dos apuntes operativos, no bloqueos: el script **exige** `SUPABASE_URL` y
`SUPABASE_SERVICE_ROLE_KEY` en `.env` aunque la parte que importa sea local (están pobladas); y el
`.env` trae rutas Windows (`D:/OEDE/...`), así que la cadena corre con el intérprete del venv de
Windows (`venv/Scripts/python.exe`), invocable desde WSL sin fricción.

### Cambio hecho antes de correr

`SQL_OFERTAS_DASHBOARD` reproducía las 60 columnas de Supabase y **no traía la trazabilidad del
traductor**. Como el export la necesita (P1.a) y el `01` es una descarga completa, lo extendí antes
de correr para no pagar dos veces: **+4 columnas** (`arbol_hub_id`, `arbol_regla_id`,
`arbol_camino`, `arbol_traza_json` — la traza pesa 5,2 MB en total, entra entera). Total: 64.

### Resultado de la corrida

| Tabla | Junio | Ahora |
|---|---:|---:|
| `ofertas_dashboard` | 68.241 | **97.185** |
| `ofertas_skills` | 1.569.227 | **2.827.507** |
| `ofertas_local` | — | 112.857 |
| `esco_skills` / `esco_associations` | — | 14.257 / 129.004 |

Verificado en el parquet: 64 columnas, 3.710 filas con `arbol_hub_id` poblado (ej. hub 51 /
regla `D11` / camino `D_directa`, que es `decision_metodo='arbol_contexto'`).

---

## 2. El clasificador de escenarios (`02`) — descripción para el laudo

**Rol:** observacional. Etiqueta cada fila de `ofertas_skills` con un escenario y flags. No rutea,
no modifica producción. Re-ejecutable (DROP/CREATE de sus propias tablas).

### Qué campos usa

- De `ofertas_skills`: `skill_tipo_fuente`, `esco_skill_uri`, `id_oferta`.
- De `ofertas_dashboard`: **`esco_occupation_uri`** (el destino ocupacional que decidió el matcher)
  y `empresa`.
- De `esco_skills`: pertenencia al catálogo (`uri_en_catalogo`) y nivel taxonómico L1
  (`T%` = transversal).
- De `esco_associations`: **`en_canon`**, es decir si el par (skill, ocupación) está en el canon ESCO.

`skill_tipo_fuente` define el **modo**: DERIVED (`tarea`, `titulo`, `semantico`), DECLARED (las seis
`*_declarada` + `skills_nlp` + `soft_skills_nlp`) y LEGACY (`terminologia`, `regla`).

### Qué estadísticas calcula — **todas agrupadas por ocupación**

- Masa por ocupación: n° de ofertas y de empresas de cada `esco_occupation_uri`.
- Par (ocupación × skill × modo): n° de ofertas y empresas que lo demandan.
- **Penetración** = empresas del par / empresas de la ocupación (con fallback a ofertas si el campo
  empresa no sirve).
- Dispersión de la skill: en cuántas ocupaciones distintas aparece, y su penetración promedio.
- `en_canon` por par.

### Umbrales (CONFIG v1.0, decisión D-013)

| Regla | Umbral |
|---|---|
| B_FUERTE (modo empresa) | ≥5 demandantes · penetración ≥0,05 · masa ocupación ≥15 |
| B_FUERTE (fallback oferta) | ≥10 ofertas · masa ≥30 |
| B_FUERTE local (pisa comodín) | penetración ≥0,30 |
| COMODÍN | skill en ≥100 ocupaciones **y** penetración promedio ≤0,30 |
| C1_CANDIDATO | ≤2 ofertas en el par |
| Campo empresa | si >30% NULL → fallback a oferta; `"Confidencial"` cuenta como NULL |
| Emergentes (léxico) | largo 3–50 · frecuencia ≥3 |

Precedencia: LEGACY → URI_FABRICADA_* → E (declarada transversal) → A / A_DECLARADO (en canon) →
B_FUERTE local → COMODÍN → B_FUERTE por demandantes → C1 → CENTINELA. Lo que no cae en ningún
bucket aborta la corrida.

### El punto que define el laudo: **la dependencia del destino ocupacional es total**

No es que *algunos* escenarios miren la ocupación: **la unidad de análisis es el par (ocupación,
skill)**. Tres mecanismos concretos:

1. **`en_canon` —** es la bifurcación principal (separa A de todo el árbol B/C/centinela) y se
   evalúa como "¿existe este par (skill, ocupación) en el canon ESCO?". Si la oferta cambia de
   ocupación, la respuesta cambia de forma directa.
2. **`penetración` —** tiene el destino en el numerador *y* en el denominador.
3. **Dispersión (comodín) —** cuenta ocupaciones distintas por skill.

Y el efecto más importante es poblacional: **una fila puede cambiar de escenario sin que su propia
oferta se haya tocado**, sólo porque otras ofertas entraron o salieron de esa ocupación y movieron
las masas. Con 44% de destinos re-decididos, la clasificación de junio **no es reutilizable, ni
parcialmente**. Hay que re-correr el `02`.

### Dos cosas que hay que resolver antes de re-correrlo

**a) Gate duro que va a abortar en el primer intento.** `UNIVERSO_ESPERADO = 1_569_227` está
hardcodeado y se compara contra el total clasificado con `sys.exit(1)`, más un `assert` en el
reporte. El universo nuevo es **2.827.507**. Hay que actualizarlo — o mejor, hacerlo dinámico
(contar `ofertas_skills` al inicio) para que deje de ser una constante que caduca en cada snapshot.

**b) Los umbrales son absolutos y el corpus creció.** ≥5 demandantes, ≥15/≥30 de masa y ≥100
ocupaciones se calibraron sobre 68.241 ofertas y 1,57M de pares. Ahora hay 97.185 ofertas (+42%) y
2,83M de filas (+80%). Con masas mayores, más pares cruzan los mínimos: **es esperable más
B_FUERTE y menos CENTINELA/C1 por crecimiento del corpus, no porque la realidad haya cambiado.**

**Recomendación:** re-correr con los umbrales v1.0 **sin tocar**, cambiando sólo el universo
esperado. Mover umbrales y corpus a la vez haría imposible atribuir cualquier diferencia. La
distribución que salga se lee como **nueva línea de base**, no como comparable directo contra
junio; si en algún momento se quiere comparabilidad, es un ejercicio aparte de re-calibración a
masa equivalente.

Con ese laudo tomado, el `02` corre y detrás va el `05b` extendido.

---

## Estado de la cadena

- `01` — **corrido**, con las 4 columnas de trazabilidad incorporadas.
- `02` — **esperando laudo** (a + b arriba).
- `05b` — bloqueado por el `02`. **Atención:** el duckdb quedó con `ofertas_dashboard` y
  `ofertas_skills` post-L pero `ofertas_skills_clasificadas` **todavía de junio** — el `01` no la
  toca porque no es suya. Correr el `05b` ahora produciría un export que une skills nuevas con
  clasificación vieja por `id`. No correrlo hasta que el `02` regenere esa tabla.
