# [FRENTE K] Próxima ronda de auditoría — material para Cyn y Juan Domingo (2026-08-13)

La auditoría integral 2026-08-12 se verificó y aplicó (ver `exports/reportes/K_*`). Este documento junta lo que quedó FUERA de su universo o abierto, para la próxima ronda.

## 1. Las 71 reglas posteriores al export (no auditadas) — uso 5.254

El export que auditaron (299 reglas) es anterior al config vivo (357). Estas quedaron sin revisar. Top 25 por volumen:

| Regla | ofertas decididas | activa |
|---|---|---|
| R323_atencion_publico | 591 | sí |
| R353_operario_carga_descarga | 543 | sí |
| R305_electromecanico | 518 | sí |
| R274_coordinador_operaciones_logistica | 460 | sí |
| R228_analista_contabilidad | 288 | sí |
| R349_operario_envasado | 177 | sí |
| R95_tech_lead_ia_ml | 174 | sí |
| R329_tecnico_electronico_mantenimiento | 172 | sí |
| R350_operario_deposito_logistica | 164 | sí |
| R317_vendedor_viajante | 157 | sí |
| R322_mecanico_industrial | 141 | sí |
| R309_responsable_deposito | 123 | sí |
| R303_gerente_admin | 122 | sí |
| R355_operario_maestranza | 114 | sí |
| R186_kinesiologo_fisioterapeuta | 108 | sí |
| R132_vendedor_medicina_prepaga | 102 | sí |
| R306_mantenimiento_electrico | 92 | sí |
| R337_psicologo_laboral_educativo | 88 | sí |
| R66_arquitecto_software | 79 | sí |
| R80_administrativo_almacen | 76 | sí |
| R326_tecnico_refrigeracion | 74 | sí |
| R301_ascensores | 68 | sí |
| R90_supervisor_ventas | 64 | sí |
| R344_project_manager | 62 | sí |
| R347_operario_metalurgico | 62 | sí |
| … 46 más | 635 | |

**Pedido:** export fresco de estas 71 para la misma auditoría de destinos (lista completa en `exports/reportes/K_datos_p1_2026-08-13.json` → `c2_vivas_sin_contraparte`). Nota especial: varias son del mismo género que las que la auditoría retiró (R353_operario_carga_descarga, R355_operario_maestranza, R347_operario_metalurgico son primas de R240; R303_gerente_admin es prima de R49).

## 2. Las 8 auxiliares — conducta real en producción (destinos SIN validar)

La auditoría las separó como "no ocupacionales", pero tres de ellas **asignan ocupación hoy** y sus destinos nunca pasaron por la experta (codigo_esco null en el JSON):

| Regla | Conducta hoy | ofertas | destino sin validar |
|---|---|---|---|
| R1_skills_cad | fuerza ocupación si el texto menciona autocad/solidworks/revit… | 238 | 3118.3 dibujante técnico |
| R2_skills_diseno_grafico | ídem por photoshop/illustrator… | 89 | 2166.9 diseñador gráfico |
| R137_tareas_picking_crossdocking | fuerza por picking/cross-docking en título+tareas | 221 | 9333.8 mozo de almacén |
| R6/R7/R4/R9/R11 | solo priorizan/penalizan familias (no asignan); uso 0 | 0 | — |

**Pregunta para Cyn:** ¿"tiene AutoCAD en el aviso" alcanza para decidir dibujante técnico? Es el forzado-por-semejanza-de-skill operando en producción (548 ofertas). Si la respuesta es no, son 3 retiros más del mismo género que las 12.

## 3. R210_telefonista_ventas — contradicción a resolver (12 ofertas)

El JSON la marca `validado_sin_observacion_critica` con **5244.1 teleoperador**, pero la regla viva dice **4222.1 agente de centro de atención al cliente**. Las dos fuentes citadas:

- JSON auditado: `codigo_esco: 5244.1`, `ocupacion_esco_oficial: teleoperador/teleoperadora`, nota "Conservado tras auditoría: no se detectó inconsistencia crítica".
- Config vivo (`R210_telefonista_ventas.accion`): `esco_code: 4222.1`, sin linaje de cambio posterior al export.

¿Cuál es el destino correcto para "telefonista de ventas"? (Si 5244.1: es una corrección más. Si 4222.1: el export que auditaron traía un valor viejo.)

## 4. R10_electricista_industrial — regla muerta con código nuevo

Está desactivada hace meses y su condición usa claves que el matcher ya no evalúa. La auditoría le asigna 7411.1.1.2. Para revivirla haría falta redactarle condición nueva — mejor con Cyn en la próxima ronda (¿o su territorio ya lo cubre el diccionario/las 88?).

## 5. Gaps de variante detectados al aplicar (género "regla-11")

Tres listas de denominaciones del JSON pierden títulos reales del corpus por variantes ausentes — no las inventamos, las preguntamos:

| Entrada | Lista trae | Falta (con volumen real) |
|---|---|---|
| R229a_ejecutivo_comercial | "ejecutivo comercial" | **"ejecutivo/a comercial"** (70 títulos del cohort no matchean) |
| R226a_analista_rrhh | "analista rrhh", "analista de recursos humanos" | **"analista de rrhh"** (31+ títulos, el top de su cola) |
| R14a_contador / R14e_auditor | contador/auditor | la cola de R14 (993) es "analista contable/asistente contable" — ¿territorio del hub Analista contable (2411.1.1) del modelo 2.0, o falta acá? |

**Por esto R14 y R226 NO se aplicaron todavía** (las madres siguen vivas): esperan la confirmación de Cyn. 10 títulos de muestra de cada cola en `exports/reportes/K_datos_p1_2026-08-13.json` y en el reporte de aplicación.

## 6. Pedido a Juan Domingo — checksum de integridad del generador

Es el **tercer bug de generación del mismo circuito**: el `corresponde a` truncado (ronda 1), la regla 11 vacía (ronda 2), y ahora **144/306 condiciones truncadas con `...` literal** pese a que el autodeclarado del propio archivo decía `condiciones_truncadas: 0` (y los gaps de variante del §5 son probablemente el mismo mecanismo).

**Upgrade pedido:** que el generador emita, junto al JSON, un bloque de checksum de integridad:

```json
"checksum_generacion": {
  "por_regla": {
    "R229a_ejecutivo_comercial": {
      "n_condiciones": 1,
      "n_terminos_titulo": 4,
      "chars_condicion": 87,
      "n_desambiguaciones": 0
    }
  },
  "totales": {"entradas": 306, "terminos_titulo": 2841, "chars_condiciones": 41230}
}
```

Nuestro validador compara lo recibido contra el checksum del emisor: si el generador contó 12 términos y el JSON trae 3 + `...`, la pérdida se caza en la puerta — **incluso pérdidas de género nuevo** que ningún control específico anticipó. En esta ronda las 144 truncadas no nos afectaron *por construcción* (la auditoría era de destinos y las condiciones vivas no se tocan), pero la próxima ronda va a auditar condiciones y ahí el checksum es la única guarda barata.
