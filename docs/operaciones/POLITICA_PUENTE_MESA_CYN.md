# Política de operación — Puente validación→diccionario (mesa de Cyn)

> SPEC S1C-PUENTE, fase 1 (C1 sugeridor + C3 escritura git-first + bandeja mínima).
> C2 (UI de bandeja) diferido a demanda real post-sesión con Cyn.

## Encuadre

**Triage seguro + bandeja ordenada, no carga masiva.** Se industrializa la *generación*
de candidatas; la *decisión* es humana, caso por caso. El clasificador protege del error
caro (cargar como diccionario plano algo cuyo destino depende de las tareas); la barra es
**0 falsos vocabulario**.

## Circuito

```
wizard (Cyn) → validacion_correcciones (jsonb, ocupacion_corregida)
   → sugeridor_candidatas.py  (resuelve G3, clasifica, detecta conflicto retroactivo)
      → bandeja_<fecha>.md    (Gerardo confirma sobre ella)
         → aplicar_candidata  (comando poller, escritura git-first, squash=1 commit)
            → config/sinonimos_argentinos_esco.json  (el matcher lo lee via load_config)
```

## Umbrales y reglas

| Regla | Valor | Motivo |
|---|---|---|
| **Umbral de sugerencia** | 1 corrección | Cada corrección de ocupación entra a la bandeja. |
| **Tope de tanda** | 50 candidatas | Tanda = commit = unidad de revert. |
| **Tanda = commit = revert** | 1 sesión → 1 commit (squash) | El linaje por entrada vive en el JSON; sobrevive al squash. |
| **HOLD por blast** | blast exacto ≥ 50 → HOLD | No se escribe; se reporta antes. El blast se mide con el **resolver real** (normalización + longest-match, entrada en memoria, ofertas que *cambian*), NO substring literal. |
| **Error post-tanda** | ≥1 error → la tanda entera se re-revisa | No se parchea una entrada suelta; se re-audita el commit. |
| **Rechazo ruidoso** | esco_code que no resuelve al catálogo → rechazo con log | Nunca se inventa ni se degrada a label. |
| **Colisión longest-match** | substring con otra entrada de distinto código → rechazo | No se pisa en silencio. |

## Auditoría out-of-sample (validación de generalización)

El clasificador se ajustó mirando 5 errores sobre 34 casos y se midió sobre los mismos 34
(`_estatus` en `config/clasificador_candidatas.json`: "AJUSTADO sin contraejemplos restantes
sobre 34 casos — NO validado out-of-sample").

**Las primeras 20 correcciones nuevas que entren por el puente se auditan contra el
clasificador** (¿señal correcta? ¿falso vocabulario nuevo?) aunque la bandeja las procese
igual. Es la única validación de generalización que el ajuste sobre 34 no da. Si aparece un
falso vocabulario nuevo → revisar la config de señales (regresión del ajuste, actualiza la
fixture y su test).

## Deudas registradas del puente

- **(a) Preview-por-head se cae por timeout en heads amplios** (los de mayor riesgo, ej.
  `tecnico`=921). Para el flujo continuo el mecanismo confiable es el **dry-run local por
  variante exacta** (el que corre P5). El preview Supabase queda como señal best-effort.
- **(b) El HOLD debería disparar también por heterogeneidad** de las ofertas matcheadas
  (sectores/ISCOs dispares), no solo por conteo. El "operario de producción → 72" era
  peligroso por amplitud semántica, no por frecuencia. Hoy el HOLD es solo por conteo (≥50).

## Diferido (C2 — UI de bandeja)

No se construye en esta fase. Si el goteo de correcciones revive tras la sesión con Cyn,
la UI de bandeja (confirmar → encolar → poller → git) va con su E2E en Playwright, que de
paso salda la deuda E2E del wizard.
