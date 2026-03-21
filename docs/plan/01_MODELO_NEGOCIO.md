# 1. Modelo de Negocio

> Última actualización: 2026-03-20
> Versión: 3.0 — Modelo híbrido + Skills Intelligence (3 servicios, roles ampliados)

## Referencias

| Documento | Relación |
|-----------|----------|
| [02_ARQUITECTURA_PANTALLAS](./02_ARQUITECTURA_PANTALLAS.md) | Features por nivel determinan acceso a pantallas |
| [04_MODELO_DATOS](./04_MODELO_DATOS.md) | Tablas T-planes, T-suscripciones, T-solicitudes_acceso, T-contenidos |
| [05_USER_FLOWS](./05_USER_FLOWS.md) | Flujos F-01 a F-05 |
| [09_ROADMAP](./09_ROADMAP.md) | Fases de implementación comercial |

## Matriz de Impacto

| Si cambia... | Actualizar... |
|--------------|---------------|
| Tipos de usuario | 02_ARQUITECTURA (permisos), 06_SEGURIDAD (RLS) |
| Features por nivel | 02_ARQUITECTURA (acceso a rutas) |
| Pricing | 09_ROADMAP, 04_MODELO (T-planes) |
| Flujo de acceso (gated) | 05_USER_FLOWS, 03_WIREFRAMES |

---

## Visión del Producto

Plataforma de **inteligencia del mercado laboral argentino** con dos dimensiones:
1. **Dashboard de análisis** — para analistas, consultoras y organismos que analizan el mercado laboral
2. **Skills Intelligence** — 3 servicios (trabajador, oficina de empleo, empresa) para conectar competencias con empleo

> "Inteligencia de datos para un mercado de trabajo y un sistema productivo en transformación"
> — Propuesta narrativa OEDE

> **Documento técnico:** `docs/MOL_Skills_Intelligence.docx` v5.0 + `docs/mol_screens_v5.html` (32 wireframes)

| Dimensión | Segmento | Propuesta |
|-----------|----------|-----------|
| **Dashboard** | Público | Landing + registro libre |
| **Dashboard** | Registrado | Informes, notas y contenido por email |
| **Dashboard** | Suscriptor tablero | Dashboard completo (previa solicitud + aprobación MOL) |
| **Dashboard** | Institucional | Todo + documentos a demanda |
| **Dashboard** | Admin (OEDE) | Panel admin + gestión de accesos y contenido |
| **Skills Int.** | Trabajador (S1) | Evaluar skills, ver ofertas, capacitación, generar reporte |
| **Skills Int.** | Oficina de Empleo (S2) | Atención al trabajador, gestión vacantes, pools, inteligencia local |
| **Skills Int.** | Empresa (S3) | Reporte QR (libre) + selección, reskilling, inteligencia (registrada) |

---

## Flujo de Acceso (Modelo Híbrido)

```
VISITANTE ──────────────── Landing, navegar
     │
     ▼ (se registra)
REGISTRADO ─────────────── Informes, notas, contenido por email
     │                     (CMS genera y distribuye)
     │
     │ (solicita acceso al tablero)
     ▼
SOLICITUD ──────────────── MOL/OEDE revisa y aprueba
     │
     ▼ (aprobado)
FREE TRIAL (7 días) ────── Dashboard con limitaciones (TBD)
     │
     │ (quiere más)
     ▼
SUSCRIPTOR ─────────────── Dashboard completo
     │                     Pago: MercadoPago (individuos/consultoras)
     │                           o mecanismo institucional (organismos)
     ▼
INSTITUCIONAL ──────────── Todo + documentos a demanda
                           Pago: orden de compra / transferencia
```

---

## Tipos de Usuario

### U-VISITANTE
- **Acceso:** Landing, `/precios`, `/informes` (preview)
- **Auth:** No
- **Objetivo:** Convertir a U-REGISTRADO

### U-REGISTRADO
- **Acceso:** Contenido completo (informes, notas, análisis publicados)
- **Auth:** Sí (registro con email)
- **Paga:** No
- **Recibe:** Notificaciones por email de nuevo contenido (link o PDF)
- **Objetivo:** Consumir contenido + eventualmente solicitar acceso al tablero
- **Nota:** NO tiene acceso al dashboard interactivo

### U-TRIAL
- **Acceso:** Dashboard con limitaciones por 7 días
- **Auth:** Sí + aprobación de MOL/OEDE
- **Paga:** No
- **Limitaciones:** TBD (ver [Decisiones Pendientes](#decisiones-pendientes))
- **Flujo:** U-REGISTRADO solicita acceso → OEDE aprueba → 7 días trial
- **Objetivo:** Que valore el dashboard y decida suscribirse

### U-SUSCRIPTOR
- **Acceso:** Dashboard completo + histórico
- **Auth:** Sí + plan activo
- **Paga:** Sí
- **Features:**
  - Histórico completo
  - Exports Excel/PDF
  - Hasta 10 alertas
  - Análisis de empresas
  - Skills Intelligence completo

### U-INSTITUCIONAL
- **Acceso:** Todo de suscriptor + documentos a demanda
- **Auth:** Sí + contrato institucional
- **Paga:** Sí (mecanismo institucional: orden de compra, transferencia, etc.)
- **Features:**
  - Todo de U-SUSCRIPTOR
  - API REST
  - Documentos/reportes a demanda
  - Soporte dedicado

### U-ADMIN
- **Acceso:** Panel admin + gestión de accesos + gestión de contenido
- **Paga:** No (usuarios internos OEDE)
- **Funciones:**
  - Aprobar/rechazar solicitudes de acceso al tablero
  - Publicar contenido (informes, notas) via CMS
  - Monitorear sistema y métricas
  - Gestionar ESCO Argentino (aprobar skills emergentes)

---

## Roles Skills Intelligence (v5)

> Los roles de Skills Intelligence son paralelos a los tipos de usuario del dashboard. Un usuario puede tener ambos (ej: un registrado que también es trabajador S1).

### U-TRABAJADOR (S1 — Mi Futuro Laboral)
- **Acceso:** Flujo completo de evaluación: diagnóstico → matching → capacitación → reporte
- **Auth:** Dos modos:
  - Anónimo: perfil temporal (no se persiste, pierde al cerrar)
  - Registro mínimo: email + nombre → perfil persistente + historial de reportes
- **Paga:** No (servicio gratuito)
- **Datos propios:** Su perfil de skills, sus reportes generados
- **Opt-in:** Puede aceptar ser visible en búsquedas de OEs y empresas
- **No puede:** Ver datos de otros trabajadores, acceder a funciones de OE o empresa

### U-TECNICO_OE (S2 — Oficina de Empleo)
- **Acceso:** Atención al trabajador, gestión de vacantes, formación, inteligencia local, exportar diagnósticos
- **Auth:** Login institucional (email de la OE) + rol `oficina_empleo`
- **Organización:** Pertenece a una OE (tenant). Solo ve datos de su jurisdicción
- **Paga:** Según acuerdo institucional (OE como cliente)
- **Datos propios:** Cartera de casos, vacantes locales, catálogo de cursos del territorio
- **Pool amplio:** Acceso de lectura al pool MOL en su jurisdicción (ofertas del mercado general + trabajadores con opt-in)
- **Funciones exclusivas:**
  - Importar pools via Excel/CSV (personas, vacantes, cursos)
  - Nota del técnico (campos no derivables: carnet, motivación, situación)
  - Exportar PDF institucional con firma del técnico
  - Matching bidireccional: empresa trae vacante → ranking cartera por match

### U-EMPRESA_LIBRE (S3 nivel libre)
- **Acceso:** Solo el reporte específico al que apunta el QR
- **Auth:** Ninguna — accede por token del QR
- **Paga:** No
- **Funciones:**
  - Ver reporte de compatibilidad del candidato
  - Personalizar competencias y recalcular (no persiste)
  - Ver skills validadas por OE vs autodeclaradas (cuando aplique)
- **No puede:** Buscar candidatos, ver otros reportes, guardar datos

### U-EMPRESA_REGISTRADA (S3 nivel registrado — v2)
- **Acceso:** Todo de empresa_libre + módulos de selección, reskilling, inteligencia
- **Auth:** Registro con email empresa + cuenta
- **Organización:** Pertenece a una empresa (tenant)
- **Paga:** Según plan (TBD — Etapa 3 del roadmap)
- **Funciones:**
  - Publicar búsquedas → recibir candidatos rankeados
  - Perfiles de puesto reutilizables
  - Historial y comparación de candidatos
  - Benchmark del mercado: disponibilidad de skills en el pool
  - Búsqueda proactiva en pool (trabajadores con opt-in)
  - Reskilling de plantilla (v2)
  - Inteligencia sectorial (v2)
- **Etapa:** Etapa 3-4 del roadmap

### Relación entre roles

```
Un usuario puede tener MÁS DE UN ROL simultáneamente:

  registrado + trabajador       → analista que también evalúa sus skills
  institucional + oficina_empleo → OE que también tiene acceso al dashboard
  suscriptor + empresa_registrada → consultora RRHH con ambos accesos
  admin + todo                  → OEDE tiene acceso completo
```

### Multi-tenancy (organizaciones)

Los roles S2 y S3-registrado operan dentro de una organización (OE o empresa). Cada organización es un "tenant" con datos aislados:

| Concepto | OE (S2) | Empresa (S3) |
|----------|---------|-------------|
| Identificador | organizacion_id | empresa_id |
| Aislamiento | Solo ve su jurisdicción | Solo ve sus vacantes y candidatos |
| Pool propio | Personas + vacantes locales + cursos | Vacantes + plantilla |
| Pool amplio | Lee pool MOL en su jurisdicción | Lee pool candidatos con opt-in |
| Roles internos | técnico, coordinador | rrhh, gerente |

---

## Planes y Pricing

| Plan | Precio | Facturación | Dashboard | Contenido |
|------|--------|-------------|-----------|-----------|
| **Registrado** | $0 | - | No | Sí (informes, notas) |
| **Trial** | $0 (7 días) | - | Sí (limitado) | Sí |
| **Suscriptor** | TBD | Mensual | Sí (completo) | Sí |
| **Institucional** | A consultar | Según acuerdo | Sí (completo + API) | Sí + a demanda |

### Decisiones Pendientes

- [ ] **Precio Suscriptor** — No hay benchmark de servicios comparables en Argentina
- [ ] **Limitaciones del Trial** — ¿Qué se restringe en 7 días? Opciones:
  - Solo últimos 7 días de datos (como Free original)
  - Dashboard completo pero sin exports
  - Todo abierto pero con marca de agua / límite de vistas
- [ ] **Proceso de aprobación** — ¿Quién aprueba? ¿Criterios? ¿Automático vs manual?
- [ ] **Mecanismo institucional de pago** — Orden de compra, transferencia bancaria, etc.
- [ ] **Pricing comparativo** — Investigar servicios similares (LinkedIn Talent Insights, Indeed Hiring Lab, Burning Glass)

---

## Features por Nivel (Matriz)

### Dashboard de análisis

| Feature | Registrado | Trial | Suscriptor | Institucional |
|---------|------------|-------|------------|---------------|
| Contenido/informes | ✓ | ✓ | ✓ | ✓ |
| Email con nuevo contenido | ✓ | ✓ | ✓ | ✓ |
| Dashboard interactivo | ✗ | ✓ (TBD) | ✓ | ✓ |
| Histórico completo | ✗ | TBD | ✓ | ✓ |
| Skills Intelligence (admin) | ✗ | ✗ | ✗ | ✗ (solo admin) |
| Análisis de empresas | ✗ | ✗ | ✓ | ✓ |
| Export Excel/PDF | ✗ | ✗ | ✓ | ✓ |
| Alertas por email | ✗ | ✗ | ✓ (10) | ✓ (∞) |
| API REST | ✗ | ✗ | ✗ | ✓ |
| Documentos a demanda | ✗ | ✗ | ✗ | ✓ |
| Soporte | - | Email | Email | Dedicado |

### Skills Intelligence (3 servicios)

| Feature | Trabajador S1 | Técnico OE S2 | Empresa libre S3 | Empresa reg. S3 |
|---------|--------------|---------------|-------------------|-----------------|
| Diagnóstico skills (4 vías) | ✓ (propias) | ✓ (del trabajador) | ✗ | ✗ |
| Matching ocupaciones | ✓ | ✓ | ✗ | ✗ |
| Matching ofertas reales | ✓ | ✓ (OE + pool MOL) | ✗ | ✓ (publicar búsqueda) |
| Matching formación | ✓ | ✓ (catálogo OE) | ✗ | ✓ (reskilling) |
| Reporte PDF + QR | ✓ (propio) | ✓ (institucional) | ✓ (ver por QR) | ✓ (ver por QR) |
| Personalizar competencias | ✗ | ✗ | ✓ | ✓ |
| Gestión de pools | ✗ | ✓ (importar Excel) | ✗ | ✓ (vacantes) |
| Matching bidireccional | ✗ | ✓ (vacante→cartera) | ✗ | ✓ (búsqueda→pool) |
| Inteligencia de mercado | ✗ | ✓ (local, v2) | ✗ | ✓ (sectorial, v2) |
| Nota del técnico | ✗ | ✓ | ✗ | ✗ |
| Comparar casos/candidatos | ✗ | ✓ | ✗ | ✓ |
| Opt-in visibilidad pool | ✓ | ✗ (gestiona) | ✗ | ✗ (busca) |

---

## Sistema de Contenidos (CMS) — NUEVO

### Requerimiento

Generar y distribuir contenido a usuarios registrados:
- **Fuente:** Datos del dashboard (ofertas, skills, tendencias)
- **Salida:** Documentos/notas/informes
- **Distribución:** Email con link o PDF adjunto (lo más eficiente)

### Funcionalidades CMS

| Función | Descripción | Quién |
|---------|-------------|-------|
| Crear contenido | Generar informe/nota desde datos del dashboard | Admin OEDE |
| Programar envío | Configurar frecuencia (mensual, semanal, ad-hoc) | Admin OEDE |
| Distribuir | Enviar por email a registrados (link o PDF) | Sistema |
| Gestionar | CRUD de contenidos publicados | Admin OEDE |
| Métricas | Aperturas, descargas, clicks | Admin OEDE |

### Decisiones Pendientes CMS

- [ ] ¿Email con link a web o PDF adjunto? (link es más trackeable, PDF es offline)
- [ ] ¿Generación automática desde datos o redacción manual?
- [ ] ¿Segmentación por interés? (ej: solo IT, solo CABA)
- [ ] Herramienta: ¿Custom en Next.js o servicio externo (Resend, SendGrid)?

### Tablas Relacionadas

- `T-contenidos` — Informes/notas publicados
- `T-envios_contenido` — Registro de distribución
- Ver [04_MODELO_DATOS](./04_MODELO_DATOS.md)

---

## Pasarela de Pago (Dual)

### Canal 1: MercadoPago (individuos y consultoras)

**Para:** Consultoras pequeñas, recruiters independientes, investigadores

- Tarjeta de crédito/débito
- Transferencia bancaria
- Efectivo (Pago Fácil, Rapipago)

### Canal 2: Mecanismo Institucional (organismos y gobierno)

**Para:** Ministerios, universidades, organismos internacionales, grandes consultoras

- Orden de compra
- Transferencia bancaria directa
- Facturación a 30/60 días
- Proceso manual (MOL gestiona)

### Integración

- Ver [F-04](./05_USER_FLOWS.md#f-04-webhook-mercadopago) para flujo MercadoPago
- Ver [04_MODELO_DATOS](./04_MODELO_DATOS.md#t-pagos) para tablas
- Ver [06_SEGURIDAD](./06_SEGURIDAD.md) para webhooks

---

## Métricas de Negocio Objetivo

### MVP (3 meses)

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 200 |
| Solicitudes de tablero | 50 |
| Suscriptores activos | 10 |
| Contenidos publicados | 6 |

### 6 meses

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 1,000 |
| Suscriptores activos | 50 |
| Institucionales | 3 |
| Contenidos publicados | 15 |
| Tasa apertura emails | > 30% |

### 1 año

| Métrica | Objetivo |
|---------|----------|
| Usuarios registrados | 5,000 |
| Suscriptores activos | 200 |
| Institucionales | 10 |
| NPS | > 50 |

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-02-05 | 1.0 | Modelo SaaS clásico (Free/Pro/Enterprise) |
| 2026-02-07 | 2.0 | Modelo híbrido: registro libre + acceso gated + CMS + pago dual. Basado en feedback colegas OEDE |
| 2026-03-20 | 3.0 | Skills Intelligence v5: 4 roles nuevos (trabajador, técnico OE, empresa libre, empresa registrada), multi-tenancy por organización, relación entre roles, matrices de features por servicio. Fuente: MOL_Skills_Intelligence.docx v5 |
