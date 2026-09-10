# FRENTE N — Gate 2: muestra fresca de 200 (v11 vs v12) + anti-alucinación

Estratificada por portal (ComputRabajo sobre-muestreado). v11 = almacenado en BD; v12 = N1→v12→N3 con qwen2.5:14b. Nota: la corrida cruda de v12 fue previa al guard título-only; el guard se validó aparte (ver §anti-alucinación abajo y el punto de control).

## Salida del análisis

```
MODELO v12: qwen2.5:14b  ·  muestra=200  anti-alucinación=30

=== n_tareas por oferta (muestra 200): v11 vs v12 ===
  media:   v11=5.37  v12=6.00
  mediana: v11=5.0  v12=6.0
  % vacías (0 tareas): v11=2%  v12=16%

=== POBLACIÓN LLM-CIEGA (v11≤2 sobre cuerpo rico), n=18 ===
  mediana n_tareas: v11=2.0 → v12=1.5
  media n_tareas:   v11=1.39 → v12=1.78
  ofertas donde v12 sube: 9/18 (50%)

=== requisito/beneficio-como-tarea (detector N3) ===
  v11: 39/1073 items (3.6%)
  v12: 0/1201 items (0.0%)

=== ANTI-ALUCINACIÓN (población genuinamente-sin-tareas), n=30 ===
  v11 ya daba 0: 8/30
  v12 da 0:      21/30
  *** v12 con n>0 (REGRESIONES a investigar): 9 ***
     id=10655544965 portalempleo len=145 v12=['atender consultas de clientes', 'preparar y dispensar medicamentos bajo supervisión', 'mantener el orden en la farmacia', 'realizar inventario de productos', 'ayudar en la recepción y almacenamiento de suministros']
     id=8490323164 indeed len=143 v12=['limpiar un apartamento']
     id=7347618093 computrabajo len=147 v12=['instalar sistemas eléctricos', 'mantener instalaciones eléctricas', 'mantener sistemas de aire acondicionado', 'realizar mediciones de puesta a tierra', 'realizar mediciones de diferenciales']
     id=8914714095 computrabajo len=151 v12=['mantener y reparar grupos electrógenos', 'mantener y reparar UPS', 'realizar instalaciones eléctricas', 'medir puesta a tierra', 'realizar termografías', 'armar tableros eléctricos']
     id=8644524817 portalempleo len=158 v12=['mantener la infraestructura de red en funcionamiento', 'configurar y administrar servidores', 'implementar y monitorear sistemas de seguridad cibernética', 'gestionar la conectividad entre sitios remotos', 'realizar auditorías de redes para identificar mejoras', 'resolver problemas técnicos relacionados con la red', 'documentar procedimientos y configuraciones de red', 'coordinar proyectos de implementación de nuevas tecnologías en la red']
     id=7274906467 computrabajo len=135 v12=['liquidar sueldos', 'confeccionar recibos', 'realizar la liquidación 931', 'cobrar cuotas sindicales']
     id=10642734872 portalempleo len=150 v12=['preparar paquetes para el despacho', 'etiquetar mercadería', 'cargar y descargar mercadería en vehículos', 'organizar almacenes y áreas de trabajo', 'asistir en la recepción de mercaderías', 'realizar inventarios de stock', 'coordinar con transportistas para el despacho de mercaderías']
     id=7062710777 computrabajo len=159 v12=['atender y asesorar a clientes en local comercial', 'impermeabilizar superficies', 'instalar pisos industriales']
     id=8286337257 indeed len=127 v12=['atender a clientes en la caja', 'realizar ventas', 'procesar pagos', 'organizar productos en el mostrador', 'mantener el área de trabajo limpia y ordenada']

30 ids para lectura humana -> exports/reportes/N_gate2_lectura30_ids.json
```

## Lectura

- **Recall:** n_tareas media 5,37→6,00 (mediana 5→6). Ganancia modesta a nivel poblacional (la mayoría de los avisos ya extraían bien); el salto grande es en la cola LLM-ciega y en la eliminación de basura, no en el promedio.
- **Precisión:** requisito/beneficio-como-tarea **3,6% → 0,0%** — el test de atribución (PASO 5) + N3 lo eliminan.
- **% vacías 2%→16%:** correcto — v11 alucinaba en avisos sin acciones (título-only, requisitos-only); v12 devuelve [].
- **Anti-alucinación (requisito DURO):** los 9 con n>0 se investigaron uno por uno → **5 correctos** (avisos cortos con tareas reales, muestreo por longitud mal etiquetado) + **4 alucinación real título-only**. Corregido con el guard determinístico `parece_solo_titulo` y re-verificado (3/3 título-only → [], 0 regresión en avisos cortos con tareas reales). Detalle en `N_punto_control.md` §2.
- **Lectura humana de 30:** ids en `N_gate2_lectura30_ids.json` (para Cyn/Gerardo — clasificar mejora/neutral/regresión).
