# docs(spec-s1b4): cierre SPEC S1.B.4 — Relevamiento de Skills

## Qué cierra

Cuarto spec de la fase S1.B. Primero en usar un **marco teórico propio del componente** (el "Modelo conceptual del MOL" v1.0, 2026-05-30) cuyo mapeo de capacidades la capa 5.2 verificó contra el código.

- **5.1** Memoria operativa triple: Gerardo + Cyn + modelo conceptual (5 escenarios, vocabulario vivo, tareas como ancla).
- **5.2** Estado relevado: el embudo de 3 capas, el cementerio estructurado, la vectorización con manifest, el perfil argentino como boost post-match, la cadena de emergentes cableada a buffers muertos.
- **5.3** Deuda observada (12 ítems en 8 categorías, sin priorizar).
- **5.4** Principios de diseño objetivo (7 principios).

## Hallazgo central

**El sistema está más construido y menos conectado de lo que el propio modelo conceptual suponía.** La señal de origen que el modelo pedía crear ya existe limpia (`skill_tipo_fuente`, 11 valores, 0 nulos) — pero la documentación apunta a la columna muerta (`origen_tipo`). El cementerio es una tabla rica de 7.564 filas que nadie reutiliza. La cadena de emergentes no está cortada: está cableada a buffers que nadie consume (mismos dead-ends que el loop de Matching).

## Refutaciones a la memoria

- `filtrar_por_trust` NO fue eliminado: vive con default False desde SPEC B v2, nunca activado — variante nueva de D-15: "construido y nunca encendido".
- Los embeddings SÍ tienen trazabilidad (corpus_manifest.json, regenerados 2026-04-24) — pero sin la release de ESCO de origen.
- El gold set de skills no existe como tal: son las mismas 49 ofertas del de matching, congeladas en era v10.

## Patrón D-15: cuarta aparición consecutiva

7 instancias en Skills. Con 4 de 4 componentes confirmados, el patrón es la regla del proyecto, no la excepción.

## Próximo paso

Quinto spec: S1.B.5 — NLP. El material de Cyn (campo Sector roto, tareas bien extraídas, listas sin verbo) ya está capturado.

## DEPLOY_RULES

Documento de relevamiento. Sin impacto en producción.
