# Bug NLP — limpieza de título no remueve ruido de referencia/ID/código

**Fecha:** 2026-06-30 · **Detectado por:** validación de denominaciones de Cyn (SPEC S1C-G3, GRUPO A) · **Estado:** registrado, no resuelto · **Severidad:** media

## Qué pasa

El pre-procesamiento de título del NLP (`titulo_limpio`) **no remueve ruido** del tipo
número de referencia / ID / código de búsqueda interno del aviso. El título llega con basura
y el matcher **clasifica sobre la basura**, no sobre la ocupación.

Es independiente del diccionario (SPEC S1C-G3 lo bordeó cargando la *denominación limpia*),
pero la raíz está en el paso de limpieza del NLP — afecta a cualquier oferta con ese ruido,
no solo las de Cyn.

## Casos testigo (de la validación de Cyn, hoja "Sin target")

| id_oferta_ref | título con ruido (titulo_limpio) | qué clasificó el sistema | denominación real |
|---|---|---|---|
| 7677139622 | `(id: 6834) at para integración escolar en billingh` | trabajador de apoyo (sobre el ruido) | asistente en educación especial (5312.4) |
| 6592545470 | `Ing. eléctrica o electromecánica` (ruido leve / disyunción) | mecánico electricista | ingeniero eléctrico (2151.1) |
| 5786782663 | `Ref 20975analista de prevención para incorporar al` | — (ruido "Ref 20975" pegado a "analista") | responsable de salud y seguridad (2263.3) |
| 8197398818 | `SCRUM master ms044ka` | comandante del Ejército | gestor de proyectos de TIC (1330.7) |
| 6297813821 | `Sobrestante de obra / capataz` (formato con barra) | (orientación ok, marcado por ruido de formato) | capataz de construcción (3123.1.1) |
| (descarte) 8?  | `Ref. 20826: project manager` | — | (descarte: el ruido es todo el target útil) |

Patrón del ruido: `(id: NNNN)`, `Ref NNNN` / `Ref. NNNN:`, códigos alfanuméricos pegados
(`ms044ka`), separadores de formato (`/`). El LLM/regex de título no los limpia y a veces
toma el ruido como la denominación (ej. "Ref 20826" → leyó "general/comandante").

## Dónde mirar

- Limpieza de título: `database/limpiar_titulos.py` (v2.8.1) y/o el pre-procesamiento NLP
  (`config/nlp_titulo_limpieza.json`, `config/nlp_preprocessing.json`).
- El fix natural es una pasada de limpieza que elimine prefijos/sufijos de referencia-ID
  antes de NLP y matching.

## Workaround actual

SPEC S1C-G3 cargó la **denominación limpia** de estos 5 casos al diccionario (marcadas
`_flag: NLP` en `config/sinonimos_argentinos_esco.json`). Eso corrige las ofertas-fuente
pero NO la raíz: cualquier oferta nueva con el mismo ruido seguirá mal clasificada hasta que
se arregle la limpieza del título.

## Relación

- SPEC S1C-G3 (`exports/cyn_backlog/PR_body_g3_carga47.md`, `taxonomia_contexto_cyn.md`).
- Investigación previa: `docs/issues/2026-05-19_investigacion_denominaciones_argentinas.md`.
