# Perfiles polivalentes argentinos — debate sobre representación en MOL

**Fecha:** 2026-04-26
**Estado:** Documento para debate de equipo
**Autores:** Gerardo + Claude (a partir de análisis SPEC O R162)
**Audiencia:** equipo MOL (Cynthia, Diego, Gerardo, Sergio)

---

## 1. Resumen ejecutivo

Detectamos que **ESCO oficial no contempla un perfil laboral muy frecuente en el mercado argentino**: el "técnico polivalente de mantenimiento". Este patrón se está repitiendo en otras ocupaciones también, lo que sugiere que el mercado laboral se está re-estructurando hacia roles que combinan saberes que ESCO clasifica como especialidades separadas.

La pregunta de fondo: **¿son ocupaciones nuevas que hay que agregar al ESCO Argentino, o son ocupaciones ESCO existentes con un set extendido de skills?** La respuesta tiene implicaciones para todo el sistema MOL.

---

## 2. Caso concreto: Técnico de Mantenimiento Edilicio

### 2.1 Diagnóstico

La regla actual `R162_tecnico_mantenimiento_edilicio` matchea 140 ofertas y las manda a `7131.1 pintor de obra` — un target absurdo. Al cambiar de target, encontramos que **ningún código ESCO captura bien el perfil**:

| Candidato ESCO | Por qué no calza |
|---|---|
| `5153.1 conserje de edificio` | Connotación de portería/limpieza, perfil de baja calificación |
| `7233.7 mecánico de maquinaria industrial` | Solo "maquinaria", excluye plomería/obra civil |
| `7411.1 electricista` | Solo eléctrico |
| `7126.4 técnico de calefacción` | Solo HVAC |
| `2141.8 técnico mantenimiento y reparación` | ISCO 2141 = ingeniero industrial (jerarquía sobreestimada) |
| `3113.1.2 ing. técnico electromecánica` | ISCO 3 = ingeniero técnico (sobreestimada) |

### 2.2 Evidencia: 5 ofertas reales

**Oferta 1 — `1118102093` "Técnico de Mantenimiento Edilicio (San Martín)"**
> Empresa Industrial. Mantenimiento edilicio completo. **Electricidad** industrial y edilicia: tableros iluminación. **Termomecánica y climatización**: aires acondicionados. **Fontanería**: cañerías, bombas. **Obra civil menor**: albañilería, pintura, cerrajería. **Aire comprimido**. Seguridad e Higiene. Trabajos en altura. Permisos de trabajo. Gestión Ambiental. **Secundario Técnico**.

**Oferta 2 — `1118086188` "Técnico/a en mantenimiento edilicio" (Adecco / Zarate)**
> Mantenimiento integral edificios corporativos. Conocimientos en **plomería, sanitarios, pintura, electricidad, mecánica y climatización**. Secundario completo, preferentemente técnico.

**Oferta 3 — `1118104668` "Técnico Electromec. Mantenimiento edilicio y equipos fitness"**
> Mantenimiento de equipos de gimnasio. **Estudios Técnico Electromecánico finalizado**. Manejo elementos de medición en electricidad y electrónica. Soldadura eléctrica.

**Oferta 4 — `1117953680` "Técnico Mantenimiento Edilicio – Electricidad & Refrigeración"**
> Operación y mantenimiento integral de grandes edificios corporativos. **Electricidad** baja/media tensión. **Refrigeración central VRV**. **PLC**. **Grupos electrógenos**. Secundario técnico eléctrico o electromecánico.

**Oferta 5 — `1118071239` (idéntica a 2)**

### 2.3 Patrón común

| Skills demandadas | Cobertura ESCO |
|---|---|
| Electricidad industrial + baja tensión | `7411.1.1.2 electricista industrial` |
| Plomería / fontanería | `7126.8 fontanero` |
| Climatización / refrigeración | `7126.4 técnico calefacción` |
| Mecánica básica | `7233.7 mecánico maquinaria industrial` |
| Obra civil menor (albañilería, pintura) | `7131.1 pintor obra` + `7115.1 albañil` |
| PLC / grupos electrógenos | `3113.1 ing. téc. electricidad` |
| Cerrajería | `7222.3 cerrajero` |
| Trabajos en altura, seguridad | `3257.5 inspector salud trabajo` |

**El "técnico polivalente" hace TODO eso simultáneamente, con un sueldo de oficio calificado.** ESCO esperaría 8 ocupaciones distintas, con 8 personas distintas.

---

## 3. Hipótesis para el equipo

### Hipótesis 1 — Es una ocupación NUEVA argentina

> En Argentina existe un rol consolidado culturalmente ("el manitas técnico que arregla todo en la planta/edificio") que ESCO no representa. Los empleadores lo reconocen, los trabajadores se identifican como tales, hay convenios sindicales (SMATA categoría 2 en Oferta 2). **Por tanto: agregarlo al Catálogo MOL Argentino como código local nuevo.**

**Implicaciones:**
- Crear código tipo `MOL.AR.tecnico_polivalente_mantenimiento` (o similar) en el Catálogo MOL.
- Mapear soft a un parent ISCO ("padre") para análisis con ESCO oficial — probablemente ISCO 7233 o 7411.
- Permitir que reportes filtren "perfiles polivalentes argentinos" como categoría visible.

### Hipótesis 2 — Es una ocupación ESCO EXISTENTE con skills extendidas

> El rol existe en ESCO, pero las descripciones argentinas piden **más skills de las que ESCO le asocia oficialmente**. La taxonomía ESCO está desactualizada respecto al mercado real. **Por tanto: usar el código ESCO más cercano + extender el set de skills esenciales asociadas en MOL.**

**Implicaciones:**
- Mantener `7233.7 mecánico maquinaria industrial` como código pivote.
- Agregar un set "skills extendidas argentinas" para ese código: electricidad, plomería, climatización, etc.
- No crear códigos nuevos, solo enriquecer los existentes con metadata MOL.

### Hipótesis 3 — Es una **combinación** de varias ocupaciones ESCO simultáneas

> La oferta requiere realmente 3-4 ocupaciones ESCO simultáneas. ESCO permite multi-clasificación (tagging). El sistema MOL podría guardar varias ocupaciones por oferta. **Por tanto: cambiar el modelo de datos para soportar 1:N ocupaciones por oferta.**

**Implicaciones:**
- Cambio estructural mayor en `ofertas_esco_matching` (de "una occupation" a "lista de occupations").
- Re-diseño de dashboards (cómo mostrar "una oferta clasificada como electricista + fontanero + mecánico").
- Más fiel a la realidad pero alta complejidad.

---

## 4. Por qué esto NO es un caso aislado

Suponemos que el patrón se va a repetir en muchas ocupaciones, porque el mercado laboral argentino está reestructurándose hacia perfiles polivalentes. Predicciones:

### Candidatos a tener el mismo problema

| Perfil argentino | Skills demandadas | ESCO esperaría |
|---|---|---|
| **Asistente comercial admin** | Ventas + facturación + atención + Excel | 4 ocupaciones (3322 vendedor + 4311 contable + 4222 receptionist + ...) |
| **Operario/maquinista** | Operar 5 máquinas distintas + mantenimiento básico + carga/descarga | 3-5 ocupaciones operarias |
| **Recepcionista admin** | Atención + caja + facturación + redes sociales + agenda | 3-4 ocupaciones |
| **Encargado retail** | Ventas + RRHH + caja + reposición + abrir/cerrar local | 3-4 ocupaciones |
| **Asistente de gerencia** | Agenda + viajes + traducción + redacción + reportes + Excel | 4-5 ocupaciones |
| **Comunity manager + diseñador** | Redes + Photoshop + redacción + estrategia + análisis | 3 ocupaciones |
| **Analista IT + soporte** | Programación + helpdesk + redes + bases de datos | 3-4 ocupaciones |

Todos comparten el patrón: **el rol argentino concentra skills que ESCO separa en oficios distintos**, generalmente porque las empresas argentinas no pueden o no quieren contratar especialistas separados.

### Causas del fenómeno

1. **Estructura empresaria PyME.** El 99% de las empresas argentinas son PyME. No tienen presupuesto para especialistas separados — un trabajador hace lo que en empresas grandes hacen 3.
2. **Inflación y costos laborales.** Reduce demanda de especialistas, aumenta demanda de polivalentes.
3. **Tecnología convergente.** Antes electricidad/electrónica/automatización eran disciplinas separadas; hoy un técnico moderno usa los 3.
4. **Mercado laboral inestable.** Trabajadores deben "defenderse solos", aprenden múltiples saberes para ser empleables.
5. **Sindicatos y categorías en transición.** Convenios viejos (SMATA, UOM, SUTERH) tipifican oficios; las ofertas reales rompen esos límites.

---

## 5. Costo de no resolver

Si dejamos el sistema como está (mappear cada perfil polivalente a UN solo código ESCO subóptimo):

- **Estadísticas distorsionadas.** Reportar 1,500 "mecánicos de maquinaria industrial" cuando el 60% son polivalentes que apenas tocan maquinaria.
- **Análisis de demanda errados.** Política pública o capacitación basada en "faltan electricistas" cuando lo que falta son polivalentes.
- **Skills mal asignadas.** El extractor de skills le agregaría plomería/climatización a "mecánico maquinaria industrial", aumentando ruido.
- **Confianza erosionada.** Cuando Cyn/Diego validen, van a ver constantemente que el código no calza con la realidad.

---

## 6. Soluciones a debate

| # | Solución | Esfuerzo | Beneficio | Riesgo |
|---|---|---:|---:|---|
| **A** | Aceptar imperfección, documentar `requiere_revision` | Bajo | Bajo | Acumulación de casos sin resolver |
| **B** | Desactivar reglas problemáticas, dejar semántico decida | Bajo | Medio | Inestabilidad de clasificación oferta a oferta |
| **C** | Catálogo MOL Argentino con códigos locales `MOL.AR.*` | Alto | Alto | Trabajo de curación humana, divergencia con ESCO |
| **D** | Skills extendidas por código ESCO en MOL | Medio | Medio | Sigue mappeando a código subóptimo, solo agrega skills |
| **E** | Multi-clasificación (1 oferta → N ocupaciones) | Muy alto | Alto | Cambio estructural, dashboards reescritos |
| **F** | Híbrido: catálogo MOL para top-20 perfiles polivalentes + skills extendidas para el resto | Medio-Alto | Alto | Pragmático |

---

## 7. Propuesta para discutir

**Recomendación de Claude para discutir** (no es decisión):

**Combinar B + C en fases:**

1. **Inmediato (hoy)**: Solución B → desactivar reglas con target subóptimo confirmado (R162 ahora; R110 a evaluar). Marcar las ofertas afectadas con `_linaje.requiere_catalogo_mol = true`. El semántico distribuye por skills hasta que el catálogo exista.

2. **Corto plazo (sprint próximo)**: Iniciar Catálogo MOL Argentino con los **5 perfiles polivalentes más frecuentes**. Cynthia + Diego curan manualmente:
   - Técnico polivalente de mantenimiento
   - Asistente comercial-administrativo
   - Operario polivalente de planta
   - Encargado retail polivalente
   - Recepcionista-admin

3. **Mediano plazo**: cuando el catálogo MOL tenga 20-30 perfiles cubiertos, las reglas argentinas apuntan al código local correspondiente. ESCO oficial queda como "padre" para análisis comparativo internacional.

4. **Largo plazo**: contribuir hallazgos a ESCO oficial. Si encontramos 1,500 "técnicos polivalentes" en Argentina, posiblemente otros países también — vale la pena reportarlo a la comunidad ESCO.

---

## 8. Preguntas abiertas para el equipo

1. **¿Coincidimos en que ESCO no representa bien al mercado argentino?** ¿O hay buenos motivos para forzar el mapping aunque sea imperfecto?

2. **Si creamos códigos locales `MOL.AR.*`, quién los curará?** ¿Cynthia, Diego, externo?

3. **¿Qué peso le damos a "comparabilidad internacional"?** Un código local rompe la posibilidad de comparar con datos europeos directamente.

4. **¿El equipo ya pensó esto antes?** Hay menciones de "Catálogo MOL Argentino" en `docs/plan/03_WIREFRAMES/fabrica-procesamiento.md` — ¿en qué estado está esa discusión?

5. **Para los reportes a usuarios finales, ¿les sirve más "mecánico maquinaria industrial" (ESCO oficial) o "técnico polivalente mantenimiento" (MOL local)?** Probablemente lo segundo.

6. **¿Qué hacemos con las ofertas YA codificadas mal?** ¿Re-codificación masiva tras decisión, o flag de "pendiente catálogo"?

---

## 9. Próximos pasos sugeridos

1. **Revisar este documento** en reunión de equipo (Gerardo / Cyn / Diego / Sergio).
2. **Decidir hipótesis dominante** (1, 2 o 3) o combinación.
3. **Definir alcance del Catálogo MOL Argentino** — número de perfiles iniciales, criterio de inclusión, proceso de curación.
4. **Inventariar perfiles candidatos** — repetir el análisis de R162 con otras reglas que tengan `dual_coinciden=0` alto + cobertura ≥50.
5. **Implementar piloto** — un solo perfil (técnico polivalente mantenimiento) como prueba de concepto antes de escalar.

---

## 10. Anexo: ejemplos de otras reglas con sospecha del mismo patrón

De SPEC O M3 (reglas con divergencia regla-vs-semántico ≥90%):

| Regla | Cobertura | Hipótesis |
|---|---:|---|
| R49_jefe_generico | 1,042 | "Jefe genérico" — ESCO no tiene "jefe polivalente PyME" |
| R33_desarrollador_software | 1,008 | Probablemente OK, ISCO 2512 cubre bien |
| R170_asesor_comercial | 1,199 | "Asesor comercial" en Argentina es vendedor + ATC + admin |
| R109_ejecutivo_ventas | 757 | Idem asesor comercial |
| R34_cajero | 556 | "Cajero" argentino atiende + cobra + repone |
| R15_customer_care | 505 | "Customer care" en Argentina hace ventas + soporte + admin |
| R166_cocinero_planchero | 426 | "Cocinero planchero" PyME hace cocina completa |
| R31_mozo_camarero | 418 | "Mozo" argentino atiende + cobra + arma mesa + barra |

Cada una de estas merece el mismo análisis que R162.
