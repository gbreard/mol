# docs(specs): adendas de transferencia harness en S1.B.3 y S1.B.4

## Qué registra

Evidencia transferida desde la conversación paralela del harness (sandbox MOL_escenarios, índice de investigaciones, FACTIBILIDAD_S0), registrada como adendas con fuente en los dos specs ya cerrados que toca. Según protocolo del master v0.2: sin priorización — todo converge en S1.C.

- **S1.B.3 / A-1**: el Gold Set ampliado UBICADO (tabla `gold_set` de Supabase, commit 9890779e, 112-113 casos, composición exacta). Resuelve la acción pendiente de D-03. Dato crítico: la precisión sobre el ampliado nunca se midió.
- **S1.B.4 / A-2**: 8.381 URIs huérfanas — posible divergencia entre el corpus de embeddings (enriched) y el catálogo de runtime (esco_skills).
- **S1.B.4 / A-3**: segunda fosa anónima — `_filter_llm_skills` descarta sin escribir al cementerio (~25% de lo extraído).
- **S1.B.4 / A-4**: cuantificación poblacional de la divergencia AR↔EU (90%+ fuera del canon; 3.292 pares multi-empresa; 972 URIs comodín; curaduría cubre ~1,3%).
- **S1.B.4 / A-5**: tercera columna zombi (`match_method` hardcodeado).
- **S1.B.4 / A-6**: genealogía del cementerio — M-06 tiene spec, M-13 "completado" sin estarlo (variante nueva de D-15), y el veredicto de los tests en rojo.

## Verificación incluida

T6.3 verificada por lectura de los dos archivos de tests de M-06. **Veredicto distinto al esperado**: ninguno de los dos archivos invoca `filtrar_por_trust` (ni método ni parámetro). El `AttributeError` no viene de una API inexistente sino de **drift de fixture** — las fixtures usan `__new__` (saltan `__init__`) y omiten `self.filtrar_por_trust`, atributo que el path de extracción lee (`:936`/`:941`) y que es un parámetro real del constructor (`:107`, default False) agregado después de escritas las fixtures. El texto de A-6 quedó ajustado a este hallazgo.

## DEPLOY_RULES

Documentos de relevamiento. Sin impacto en producción.
