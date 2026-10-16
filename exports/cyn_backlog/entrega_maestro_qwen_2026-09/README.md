# ENTREGA MAESTRO QWEN — fuente canónica (Cyn / JD, 2026-09)

Entrega maestra de Cyn+JD (`ENTREGA_MAESTRO_QWEN.zip`). Es la **especificación canónica
de los dos extractores** (tareas y skills). Se commitea COMPLETA como fuente; cada
archivo queda tal como se recibió (nombres de descarga incluidos).

## Dominio TAREAS (usado por FRENTE N — v12.4)

| Archivo | Rol |
|---|---|
| `QWEN_TAREAS_REGLAS_MAESTRAS (1).xlsx` | Las 16 reglas maestras **RG-TAR-001..016** en formato ejecutable (ID · lógica · pregunta de control · salida esperada · ejemplo) + hoja `COMO_USAR_CON_QWEN`. **Fuente canónica contra la que se compila el prompt v12.4.** |
| `QWEN_TAREAS_CASOS_ENTRENAMIENTO (2).xlsx` | 21 casos de entrenamiento (veredicto del Maestro + lógica + clave). Materia prima del gold set v12.4. |
| `Frente_N_preguntas_Cyn (3) (1).xlsx` | Revisión de las 3 preguntas de criterio (granularidad, los 4 al borde, listas sin verbo). **Contiene el FLIP del chofer** (hoja `3-listas sin verbo`). |
| `Frente_N_3_preguntas_finales_Cyn (1) (2) (1).xlsx` | Las 3 fronteras finales: herramienta+verbo≠tarea (RG-TAR-008), HSE/compliance (RG-TAR-009), tarea en el pitch (RG-TAR-004). |
| `Enseñanza_para_Qwen_Notas_Metodologicas.docx.docx` | Notas metodológicas (§ tareas + § skills). |

## Dominio SKILLS (NO se toca — futuro FRENTE O)

| Archivo | Rol |
|---|---|
| `QWEN_CASOS_ENTRENAMIENTO_SKILLS.xlsx` | 40 casos de entrenamiento de skills. **Se commitea, no se consume en v12.4.** |
| `REGLAS_GENERALES_SKILLS..xlsx` | Reglas generales de skills + `COMO_USAR_CON_QWEN`. **Se commitea, no se consume en v12.4.** |

> El dominio skills queda reservado para el frente O. Este commit lo preserva como
> fuente; el FRENTE N v12.4 compila **solo** el dominio tareas.
