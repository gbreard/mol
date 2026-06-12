# docs(spec-s1b6): cierre SPEC S1.B.6 — Relevamiento de Pipeline

## Qué cierra

Sexto spec de la fase S1.B. Releva la orquestación del pipeline: el comando único, la selección de procesamiento, los validadores intermedios, la cadena completa y los bloqueos para la automatización.

- **5.1** Memoria operativa: el operador del pipeline es Claude Code bajo demanda de Gerardo; los validadores que Gerardo no controla; la visión human-in-the-loop con re-encolado.
- **5.2** Estado relevado: anatomía del comando único (v3.3, 8 pasos + loop de reproceso), los 4 mecanismos de selección superpuestos, los dos validadores identificados (NLP Gate + auto_validator), la cadena completa con latencias por tramo, el inventario de bloqueos.
- **5.3** Deuda observada (11 ítems en 4 categorías, sin priorizar).
- **5.4** Principios de diseño objetivo (7 principios).

## Hallazgos centrales

**El hueco de automatización está localizado**: los extremos corren solos (auto_sync por hora, poller por minuto); solo el núcleo NLP+matching es on-demand. Latencia por tramo: 6,6 días el tramo manual, 1 día el resto. Automatizar un eslabón elimina el cuello entero.

**El gate marca 278.565 veces y bloquea 70 (0,1%)**: la percepción de Gerardo ("no tengo control ni visibilidad") cuantificada. Y la configurabilidad YA existe en JSON sin exposición — el control que falta es de UI, no de capacidad técnica.

**El re-encolado con corrección humana no existe**: es el hueco exacto de la visión human-in-the-loop (Cyn corrige en vivo, la oferta vuelve a la cola corregida).

**D-15 sexta aparición consecutiva** con variante nueva: "documentado sin existir" (launch_nlp_batch.py como entry point fantasma en CLAUde.md).

## Próximo paso

Último spec del paraguas: S1.B.7 — UI, con toda la deuda de Cyn ya registrada esperando. Después: master S1.C.

## DEPLOY_RULES

Documento de relevamiento. Sin impacto en producción.
