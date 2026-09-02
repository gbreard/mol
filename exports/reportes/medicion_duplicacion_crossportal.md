# Duplicación de ofertas entre portales — medición

**Fecha:** 2026-09-01 · **Rama:** `medicion/duplicacion-crossportal` · **Alcance:** solo lectura sobre BD local, sin fetches a portales
**Datos y scripts:** `exports/reportes/dedup/`

MOL no deduplica entre portales (S-02): una vacante publicada en N portales cuenta N veces.
Para indicadores la unidad correcta es la **vacante**, no la publicación. Esto mide la
magnitud antes de diseñar la deduplicación.

---

## 0. Hallazgo previo: el espacio de ids está mal dimensionado

Antes de lo pedido, algo que apareció al leer cómo se forman los ids y que cambia la
lectura del resto.

`id_oferta` es **INTEGER PRIMARY KEY**, un espacio único para todos los portales. Cada
scraper genera su id así:

| portal | fórmula | rango efectivo |
|---|---|---|
| Bumeran | id crudo de Navent | 1.113.634.135 – 1.118.423.439 |
| ZonaJobs | id crudo de Navent | 1.914.954 – 1.118.421.294 |
| ComputRabajo | `5e9 + crc32(slug)` | 5.000.183.979 – **9.294.914.818** |
| Portal Empleo | `7e9 + crc32(uuid)` | 7.001.055.034 – **11.293.115.413** |
| Indeed | `8e9 + hash % 1e9` | 8.000.186.808 – 8.999.981.012 |
| CABA | `6e9 + id` | 6.000.022.071 – 6.000.023.171 |

Los prefijos suponen que cada portal ocupa una banda de 1e9, pero **crc32 llega a 4.29e9**,
así que ComputRabajo se derrama sobre las bandas de Portal Empleo e Indeed:

```
ofertas de computrabajo con id en la banda 7e9-8e9 (Portal Empleo): 10.963
ofertas de computrabajo con id en la banda 8e9-9e9 (Indeed)       : 10.928
ofertas de portalempleo con id > 8e9 (banda Indeed)               :  1.035
```

**Consecuencia:** si dos portales generan el mismo id, el `INSERT OR IGNORE` descarta la
segunda oferta en silencio. No es duplicación: es **pérdida de datos y mala atribución de
portal**. Con ~20K ofertas por banda solapada la probabilidad de al menos una colisión no
es despreciable, y no queda rastro en la BD para contarlas a posteriori.

Lo mismo, pero por diseño, entre **Bumeran y ZonaJobs**: comparten backend Navent y usan el
id crudo, así que una vacante publicada en los dos colapsa en **una sola fila**. Se ve
directamente en los datos:

```
ZonaJobs, ids en la banda Navent/Bumeran (1.113-1.119e9): 3.187 de 17.939 (17,8 %)
```

Esas 3.187 son avisos que existen en ambos portales y quedaron atribuidos al que los
insertó primero. **Para el par Bumeran↔ZonaJobs el problema no es sobreconteo sino
subconteo.** Por eso toda la medición que sigue se hace **por contenido**, no por id.

---

## 1. Duplicación exacta por contenido — corpus completo

Criterio: título y empresa normalizados idénticos (minúsculas, sin tildes, sin puntuación,
sin sufijos societarios SA/SRL/SAS/Ltda/Grupo/Argentina), entre portales distintos.
Corpus: 116.682 ofertas.

| par de portales | pares |
|---|---|
| **bumeran ↔ zonajobs** | **12.408** |
| indeed ↔ portalempleo | 2.554 |
| bumeran ↔ computrabajo | 1.321 |
| computrabajo ↔ zonajobs | 579 |
| bumeran ↔ indeed | 552 |
| indeed ↔ zonajobs | 368 |
| computrabajo ↔ indeed | 204 |
| caba ↔ indeed | 33 |
| otros (caba↔bumeran, caba↔ct, ct↔pe) | 3 |

Ofertas involucradas en al menos un duplicado cross-portal:

| portal | involucradas | corpus | % |
|---|---|---|---|
| portalempleo | 705 | 1.347 | **52,3 %** |
| caba | 31 | 66 | **47,0 %** |
| zonajobs | 4.980 | 17.939 | **27,8 %** |
| bumeran | 5.984 | 30.970 | **19,3 %** |
| indeed | 1.105 | 19.482 | 5,7 % |
| computrabajo | 1.236 | 46.878 | 2,6 % |

Los portales chicos son los más afectados en proporción: **más de la mitad de Portal Empleo
y casi la mitad de CABA son republicaciones** que ya están en otro portal. Cualquier
indicador que los sume tal cual está inflando.

---

## 2. Duplicación fuerte — heurística multi-campo, últimos 60 días

Criterio: título normalizado + empresa normalizada + `|fecha_publicación| ≤ 7 días`, entre
portales distintos. Corpus de la ventana: **24.670** ofertas.

**La provincia quedó fuera del match**, por falta de dato:

| portal | n | empresa vacía | **provincia vacía** | fecha_pub vacía |
|---|---|---|---|---|
| computrabajo | 46.878 | 5.743 (12 %) | **46.878 (100 %)** | 549 (1 %) |
| bumeran | 30.970 | 0 (0 %) | **26.049 (84 %)** | 8 (0 %) |
| indeed | 19.482 | 0 (0 %) | **19.482 (100 %)** | 3.262 (17 %) |
| zonajobs | 17.939 | 0 (0 %) | **16.766 (93 %)** | 0 (0 %) |
| portalempleo | 1.347 | 0 (0 %) | **1.347 (100 %)** | 1 (0 %) |
| caba | 66 | 0 (0 %) | **66 (100 %)** | 0 (0 %) |

`provincia_normalizada` está vacía entre el 84 % y el 100 % según portal: **incluirla en el
match habría descartado casi todos los pares verdaderos.** Es el campo que más falta para
esta tarea.

### Matriz de pares candidatos (60 días)

| par | pares |
|---|---|
| bumeran × zonajobs | 777 |
| bumeran × computrabajo | 101 |
| computrabajo × zonajobs | 88 |
| bumeran × indeed | 81 |
| indeed × zonajobs | 72 |
| computrabajo × indeed | 14 |
| indeed × portalempleo | 9 |
| caba × indeed | 6 |
| **total** | **1.148** |

| portal | involucradas | corpus 60d | % |
|---|---|---|---|
| caba | 6 | 23 | 26,1 % |
| zonajobs | 781 | 4.300 | 18,2 % |
| bumeran | 796 | 4.709 | 16,9 % |
| portalempleo | 9 | 140 | 6,4 % |
| indeed | 142 | 5.253 | 2,7 % |
| computrabajo | 170 | 10.245 | 1,7 % |
| **total** | **1.904** | **24.670** | **7,7 % del corpus reciente** |

---

## 3. Precisión y recall de la heurística

### Precisión: 50/50 (muestra aleatoria validada a mano)

**Cero falsos positivos.** Los 50 pares son duplicados verdaderos. Ejemplos:

```
[zonajobs 2186272] / [bumeran 1118375255]  "Gerente de Sistemas - Córdoba"
   idearhumano | idearhumano — misma fecha, descripción idéntica

[computrabajo 5126351984] / [zonajobs 2188076]
   "Mecánico eventual 2 a 3 meses Loma Verde Escobar" / "…Loma Verde | Escobar"
   Adecco Argentina S.A. | Adecco Argentina — 1 día de diferencia
```

**La similitud de descripción no sirve como criterio de descarte.** Seis de los 50 pares
tienen descripciones muy distintas (similitud 0,03–0,59) y aun así son la misma vacante:

```
[bumeran 1118410860] / [indeed …]  "Secretaria Atención al Paciente" — Sanatorio Allende
   A: "En Sanatorio Allende combinamos trayectoria, excelencia médica…"
   B: "Desde Sanatorio Allende nos encontramos en búsqueda de personal…"
```

Indeed antepone `Fecha:/Ubicación:/Empresa:` a todas sus descripciones, y varias empresas
redactan una versión por portal. Un filtro por similitud de texto habría descartado el 12 %
de los duplicados verdaderos.

Con n=50 y 0 errores, la precisión real está en torno al 93-100 % (IC 95 %).

### Recall: la heurística pierde más de la mitad

Prueba de falsos negativos: 30 ofertas de ComputRabajo cuya empresa también publica en
Bumeran (universo: 1.418 ofertas en 60 días).

| resultado | n |
|---|---|
| título exacto — **capturado por la heurística** | 2 |
| título parcial (sim 0,60–0,99) — **falso negativo potencial** | 5 |
| sin candidato en ventana | 23 |

De esos 5, revisados uno a uno, **~2-3 son duplicados reales**:

```
sim=0.87  Startia Consultores
  CT : "Supervisor de Producción y Operaciones. Turno Tarde. Productos Cacique"
  BUM: "Supervisor de Producción y Operaciones para Productos Cacique (Turno Tarde)"   -> MISMO

sim=0.71  360 Marketing
  CT : "supervisor/a"          BUM: "Supervisor/a de Ventas"                            -> probable

sim=0.61  Grupo Gestión
  CT : "Técnico/a de Mantenimiento para reconocido hipermercado en CABA"
  BUM: "Técnico/a de mantenimiento de autoelevadores zona Olivos"                       -> DISTINTOS
```

Recall estimado: **~45 %** (2 capturados sobre ~4,5 duplicados reales). La heurística de
título exacto encuentra menos de la mitad de la duplicación cross-portal cuando el
anunciante reescribe el título.

---

## 4. Recomendación

**Exacta + fuerte no alcanzan; pero la capa semántica no es lo primero que falta.**

Orden sugerido, por relación costo/beneficio:

1. **Arreglar el espacio de ids** (bloqueante, y es un bug, no una mejora). Reasignar
   prefijos que no se pisen — p. ej. multiplicar el prefijo por 1e10, o mejor, usar una PK
   sintética propia y guardar `(portal, id_nativo)` como clave natural con índice único.
   Mientras esto no se arregle, hay pérdida silenciosa de ofertas por colisión y el par
   Bumeran↔ZonaJobs es inmedible en su magnitud real.
2. **Poblar `provincia_normalizada`** (84-100 % vacía). Es el campo que más aportaría al
   match: hoy dos puestos distintos de la misma consultora en provincias distintas son
   indistinguibles para la heurística, que es justo el falso positivo que más riesgo tiene.
3. **Implementar la heurística fuerte tal cual está**: precisión ~100 % sobre 50 casos,
   captura 1.148 pares en 60 días y 7,7 % del corpus reciente. Es ganancia inmediata y de
   bajo riesgo. Marcar el par, **sin borrar**: agregar `vacante_id` compartido y contar por
   vacante en los indicadores.
4. **Capa semántica: sí, pero después y acotada.** El recall de ~45 % dice que hace falta;
   el detalle de los falsos negativos dice dónde es peligrosa. Los casos que se escapan se
   concentran en **consultoras de RRHH** (Grupo Gestión, Randstad, Startia, B&B) que
   publican decenas de puestos distintos con títulos parecidos para clientes distintos.
   Aplicar embeddings sobre título ahí produciría falsos positivos con facilidad.
   Recomendación: usarla **solo con umbral alto y exigiendo coincidencia adicional**
   (provincia una vez poblada, o similitud de descripción cuando ambas existen), y validarla
   contra el gold set antes de activarla.

### Campos que faltan o vienen sucios

| campo | estado | impacto en dedup |
|---|---|---|
| `provincia_normalizada` | 84-100 % vacía | **alto** — impide desambiguar puestos de la misma consultora |
| `empresa` | 12 % vacía en CT, 0 % en el resto | medio — esas 5.743 de CT quedan fuera de todo match |
| `fecha_publicacion_iso` | 17 % vacía en Indeed | bajo — se cae al `scrapeado_en` |
| `confidencial` | sin poblar en ningún portal | los avisos confidenciales no tienen empresa y son indeduplicables |

---

## 5. Gold set semilla

`exports/reportes/dedup/gold_set_dedup_semilla.json` — 50 pares validados a mano el
2026-09-01, con veredicto, evidencia y similitud de descripción.

Distribución: bumeran↔zonajobs 29 · computrabajo↔zonajobs 6 · bumeran↔computrabajo 6 ·
caba↔indeed 3 · indeed↔zonajobs 3 · bumeran↔indeed 2 · computrabajo↔indeed 1.

Los 50 son positivos. **Para que sirva como gold set de evaluación hay que agregarle
negativos** — sobre todo los casos difíciles: puestos distintos de la misma consultora,
misma empresa y fecha, títulos parecidos. Sin negativos solo permite medir recall, no
precisión.

---

## 6. Reproducibilidad

- `dup_exacta.py` — duplicación exacta sobre el corpus completo + cobertura de campos
- `dup_fuerte.py` — heurística de 60 días, genera `pares_fuertes.json` y la muestra de 50
- `falsos_neg.py` — estimación de falsos negativos CT↔Bumeran
- `gold_set_dedup_semilla.json`, `falsos_negativos.json` — salidas

Semillas fijas (`random.seed`), sin escrituras en BD, sin requests a portales.
