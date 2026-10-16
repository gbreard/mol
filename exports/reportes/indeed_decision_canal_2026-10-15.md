# Indeed — decisión sobre el canal (preparación, NO ejecutada)

**Fecha:** 2026-10-15 · **Estado:** para decisión de Gerardo · **No se ejecuta nada.**

## Situación
Indeed congelado desde **2026-09-16** (0 ofertas nuevas en ~4 semanas). El motor
headed bajo xvfb ya no pasa Cloudflare: **61 probes desde el 08-10, 0 GO** (59
challenge). La ventana intermitente de GO (7/103 en septiembre) **se cerró**. El
fix del selector (sonda + advance gateado) quedó armado pero **no se puede
ejecutar sin un GO**. No es cuestión de esperar: cambió el muro.

## Qué aportaba Indeed al corpus (medido)
| | |
|---|---|
| Share del corpus | **15,6%** (20.817 / 133.178) — 4º portal (CT 41,5%, bumeran 25,6%, zonajobs 16,0%) |
| Indeed con ISCO | 17.970 (86% matcheadas) |
| **ISCOs exclusivos de Indeed** (0 en otros portales) | **8 ISCOs = 23 ofertas** |

**Lectura:** Indeed aporta **volumen** (15,6%) pero **cobertura ocupacional única
casi nula**: solo 8 ocupaciones / 23 ofertas que ningún otro portal cubre
(<0,02% del corpus; ISCOs de cola larga, 1-9 ofertas c/u). El panorama ocupacional
y de skills lo sostienen CT/bumeran/zonajobs. → Perder Indeed cuesta
**representatividad/volumen**, casi nada de **cobertura de ocupaciones**.

## Costo de un proxy residencial (orden de magnitud — requiere cotización real)
- Proveedores (Bright Data / Oxylabs / Smartproxy): tier residencial típico
  **~USD 50-300/mes** según GB. El scraper headed mueve HTML modesto (~690 fichas/día
  con descripción → pocos GB/mes), así que caería en la banda baja-media.
- ⚠️ **No es fix garantizado.** El proxy cambia la **IP** (ayuda si el bloqueo es
  por reputación de IP), pero el challenge de Cloudflare también usa
  **fingerprint del browser/comportamiento**. Un residencial puede destrabar o no;
  es una **apuesta**, no una solución segura. Antes de pagar: probar un trial corto.
- Costo adicional: integrar el proxy al motor headed (ruteo + rotación) — trabajo
  de ingeniería menor, pero real.

## Qué implica documentar la baja del canal (si se decide dar de baja)
1. CLAUDE.md: fila Indeed → "suspendido 2026-09-16 (CF headed bloqueado); baja de
   canal". Quitar/relajar el cron cada-3h del probe (hoy gasta xvfb+chromium cada
   3h para 0 resultado).
2. Nota metodológica: el corpus desde ~09-16 **no incorpora Indeed** (−15,6% de
   volumen de aquí en más). Las **20.817 ya captadas quedan** (histórico), solo deja
   de refrescarse.
3. ⚠️ **Discontinuidad temporal:** cualquier indicador de **volumen absoluto o
   tendencia** que cruce el 09-16 tiene un quiebre (−15,6%). Los indicadores de
   **composición ocupacional** NO se afectan (cobertura única era 23 ofertas).
4. El fix del selector (rama `fix/indeed-run-vacio`, mergeado) queda inerte pero
   disponible si alguna vez se reabre el canal por otra vía.

## Opciones para Gerardo
- **A — Dar de baja el canal:** documentar (arriba), apagar el probe cada-3h.
  Costo: −15,6% volumen, ~0 cobertura ocupacional. El más barato y honesto hoy.
- **B — Proxy residencial (apuesta):** trial corto primero; si pasa CF, se recupera
  el 15,6%. Si no pasa, se cae en A. Costo ~USD 50-300/mes + integración.
- **C — Esperar:** mantener el probe; si CF afloja, la ventana reabre sola. Costo:
  xvfb cada 3h para 0; sin horizonte (4 semanas ya sin GO).

**Recomendación:** dado que la cobertura ocupacional única es ~0, el canal NO es
crítico para el panorama; A es defendible ya. B solo si el volumen (15,6%) se
considera necesario y se acepta la apuesta + costo. C no tiene horizonte.
