# Análisis de Matching Rules v8.3

> **Fecha:** 2025-12-06
> **Objetivo:** Documentar la lógica de validación para mejorar el sistema de muestreo

---

## Estructura General

El sistema tiene **2 niveles de clasificación**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NIVEL 1: ISCO_KEYWORDS (match_ofertas_multicriteria.py:91-114)             │
│  - Filtra candidatos ESCO por grupos ISCO permitidos                        │
│  - 9 grupos basados en keywords del título                                  │
│  - Se aplica ANTES del scoring                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  NIVEL 2: FAMILIAS FUNCIONALES (matching_rules_v83.py)                      │
│  - 10 reglas de ajuste de score                                             │
│  - Penalizan mismatches semánticos                                          │
│  - Activan flag never_confirm para revisión obligatoria                     │
│  - Se aplica DESPUÉS del scoring base                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## NIVEL 1: Diccionario ISCO_KEYWORDS

**Ubicación:** `match_ofertas_multicriteria.py:91-114`

| Grupo ISCO | Keywords de Oferta | Descripción |
|------------|-------------------|-------------|
| **1xxx** | gerente, director, jefe, coordinador, supervisor, líder | Directivos/Gerentes |
| **2xxx** | ingeniero, contador, abogado, analista, médico, programador, developer, auditor | Profesionales |
| **3xxx, 7xxx** | técnico, mecánico, electricista | Técnicos/Operarios calificados |
| **4xxx** | administrativo, secretario, recepcionista, asistente | Empleados de oficina |
| **5xxx** | vendedor, repositor, cajero, mozo, cocinero, chef, asesor comercial | Comercio/Servicios |
| **6xxx** | agricultor, tractorista, peón rural | Agropecuarios |
| **7xxx** | operario, soldador, tornero, fresador, matricero | Operarios calificados |
| **8xxx** | operador, chofer, conductor, maquinista | Operadores maquinaria |
| **9xxx** | limpieza, peón, ayudante | Ocupaciones elementales |

**Lógica:** Si el título contiene "Vendedor", solo se consideran candidatos ESCO del grupo 5xxx.

---

## NIVEL 2: Familias Funcionales (10 Reglas)

### Familia 1: ADMIN/CONTABLE

**Keywords Oferta:** `matching_rules_v83.py:28-34`
```
administrativo, administrativa, auxiliar administrativo, auxiliar contable,
facturacion, cuentas a pagar, cuentas a cobrar, registro contable,
liquidacion, archivo, secretaria, recepcionista, data entry,
ingreso de datos, back office, asistente de oficina
```

**Keywords ESCO:** `matching_rules_v83.py:165-169`
```
empleado administrativo, auxiliar contable, empleado de oficina,
recepcionista, secretario, secretaria, oficinista,
empleado de archivo, archivista, asistente administrativo
```

**Regla 1 (línea 386-393):**
- Si oferta es ADMIN → ESCO es "negocios": **-0.20, never_confirm=True**
- Si oferta es ADMIN → ESCO es ADMIN: **+0.05**

---

### Familia 2: COMERCIAL/VENTAS

**Keywords Oferta:** `matching_rules_v83.py:36-43`
```
vendedor, vendedora, ejecutivo de cuentas, ejecutivo comercial,
account executive, asesor comercial, sales, ventas,
representante comercial, representante de ventas, hunter,
business development, desarrollo de negocios, kam, key account
```

**Keywords ESCO:** `matching_rules_v83.py:177-194`
```
representante comercial, representante de ventas, agente comercial,
vendedor, vendedora, ejecutivo de cuentas, dependiente, promotor de ventas,
teleoperador, agente de call center, representante técnico de ventas,
director de ventas, gestor de cuentas, asistente de ventas,
vendedor especializado, jefe de ventas, key account, account manager
```

**Regla 2 (línea 398-405):**
- Si oferta es COMERCIAL → ESCO NO es comercial: **-0.20, never_confirm=True**
- Si oferta es COMERCIAL → ESCO es comercial: **+0.05**

---

### Familia 3: SERVICIOS/ATENCIÓN

**Keywords Oferta:** `matching_rules_v83.py:45-50`
```
atencion al cliente, customer service, soporte tecnico,
help desk, call center, telefonista, operador telefonico,
recepcion, front desk, mesero, mozo, camarero,
servicio al cliente, asistencia al cliente
```

---

### Familia 4: OPERARIO/PRODUCCIÓN

**Keywords Oferta:** `matching_rules_v83.py:52-57`
```
operario, operaria, operador, operadora, produccion,
manufactura, planta, fabrica, almacen, deposito,
logistica, chofer, conductor, camionero, repartidor,
repositor, repositora, picking, packing, montacargas
```

**Regla 6 (línea 435-439):**
- Si oferta es OPERARIO → ESCO es "negocios": **-0.20, never_confirm=True**

---

### Familia 5: SALUD/FARMACIA

**Keywords Oferta:** `matching_rules_v83.py:59-64`
```
farmaceutico, farmaceutica, farmacia, farmacias,
enfermero, enfermera, medico, medica, doctor, doctora,
kinesiologo, fisioterapeuta, nutricionista, psicologo,
odontologo, laboratorio clinico, bioquimico
```

**Regla 3 (línea 410-414):**
- Si oferta es SALUD/FARMACIA → ESCO es "ingeniero": **-0.20, never_confirm=True**

---

### Familia 6: PROGRAMAS/PASANTÍAS

**Keywords Oferta:** `matching_rules_v83.py:66-71`
```
pasantia, pasantias, programa de pasantias,
trainee, jovenes profesionales, joven profesional,
primer empleo, sin experiencia previa, graduate program,
young professionals, programa de insercion
```

**Regla 4 (línea 418-421):**
- Si oferta es PASANTÍA: **never_confirm=True** (siempre revisión)

---

### Familia 7: VENTAS DE VEHÍCULOS (v8.3)

**Keywords Oferta:** `matching_rules_v83.py:78-85`
```
0km, 0 km, okm, concesionaria, concesionario,
autos, automotor, automotriz, vehiculos, vehiculo,
motos, motocicletas, motovehiculos, automoviles
```

**Keywords ESCO Prohibidos:** `matching_rules_v83.py:87-90`
```
repuestos, piezas de repuesto, recambios,
taller, servicio de reparacion, mecanico
```

**Regla 7 (línea 444-452):**
- Si oferta es VEHÍCULOS → ESCO es repuestos: **-0.15, never_confirm=True**
- Si oferta es VEHÍCULOS → ESCO es transporte: **-0.10, never_confirm=True**

**Ejemplo:** "Vendedor 0KM Concesionaria" → NO debe matchear con "vendedor de piezas de repuesto"

---

### Familia 8: BARISTA/GASTRONOMÍA (v8.3)

**Keywords Oferta:** `matching_rules_v83.py:98-102`
```
barista, cafeteria, cafe de especialidad,
barman, bartender, coctelero, servicio de bebidas
```

**Keywords ESCO Prohibidos:** `matching_rules_v83.py:104-111`
```
especialista en importacion y exportacion de cafe,
importacion y exportacion de cafe, te, cacao,
comercio internacional de alimentos, comercio de cafe
```

**Regla 8 (línea 457-461):**
- Si oferta es BARISTA → ESCO es comercio café: **-0.15, never_confirm=True**
- Si oferta es BARISTA → ESCO es cocina especializada: **-0.15, never_confirm=True**

---

### Familia 9: PROFESIONAL JURÍDICO (v8.3)

**Keywords Oferta:** `matching_rules_v83.py:120-126`
```
abogado, abogada, abog., letrado, letrada, litigios, litigante,
derecho penal, derecho civil, derecho comercial, derecho laboral,
derecho, jurista, juridico profesional
```

**Keywords ESCO Correctos:** `matching_rules_v83.py:135-139`
```
abogado, abogada, jurista, asesor juridico, letrado, fiscal
```

**Keywords ESCO Incorrectos:** `matching_rules_v83.py:128-133`
```
empleado administrativo en el ambito juridico,
auxiliar juridico, asistente juridico,
secretario juridico, administrativo legal
```

**Regla 9 (línea 466-473):**
- Si oferta es ABOGADO → ESCO es admin jurídico: **-0.15, never_confirm=True**
- Si oferta es ABOGADO → ESCO es abogado: **+0.05**

---

### Familia 10: NIVEL JERÁRQUICO (v8.3)

**Keywords Junior Oferta:** `matching_rules_v83.py:142-149`
```
junior, jr, jr., asistente, auxiliar,
administrativo, administrativa, liquidador, liquidadora,
analista jr, analista junior, entry level, sin experiencia
```

**Keywords Directivo ESCO:** `matching_rules_v83.py:151-158`
```
director, directora, gerente, gerenta,
jefe de departamento, tesorero corporativo,
director comercial, director de operaciones,
ceo, cfo, coo, cto
```

**Regla 10 (línea 478-482):**
- Si oferta es JUNIOR → ESCO es DIRECTIVO: **-0.20, never_confirm=True**

---

## Resumen de Reglas

| # | Regla | Ajuste | never_confirm | Problema que resuelve |
|---|-------|--------|---------------|----------------------|
| 1 | Admin vs Negocios | -0.20 | ✓ | Auxiliar contable → analista de negocios |
| 2 | Comercial mismatch | -0.20 | ✓ | Vendedor → cargo no comercial |
| 3 | Farmacia vs Ingeniero | -0.20 | ✓ | Farmacéutico → ingeniero farmacéutico |
| 4 | Pasantías | 0.00 | ✓ | Trainee nunca auto-confirmar |
| 5 | Servicios vs Directivo | -0.15 | ✓ | Vendedor → director comercial |
| 6 | Operario vs Negocios | -0.20 | ✓ | Repositor → analista de negocios |
| 7 | Vehículos vs Repuestos | -0.15 | ✓ | Vendedor 0KM → repuestos |
| 8 | Barista vs Comercio | -0.15 | ✓ | Barista → importador café |
| 9 | Abogado vs Admin | -0.15 | ✓ | Abogado → admin jurídico |
| 10 | Junior vs Directivo | -0.20 | ✓ | Auxiliar → Director |

---

## Cobertura de Familias Funcionales (datos reales)

**Fecha de análisis:** 2025-12-06
**Total ofertas con matching:** 6,521

| Familia | Ofertas | % Total | En Revisión | % Revisión |
|---------|---------|---------|-------------|------------|
| **SIN_FAMILIA** | 2,466 | 37.8% | 2,397 | 97.2% |
| comercial_ventas | 1,308 | 20.1% | 1,258 | 96.2% |
| admin_contable | 1,017 | 15.6% | 939 | 92.3% |
| operario_produccion | 991 | 15.2% | 953 | 96.2% |
| salud_farmacia | 224 | 3.4% | 215 | 96.0% |
| nivel_junior | 217 | 3.3% | 207 | 95.4% |
| servicios_atencion | 183 | 2.8% | 177 | 96.7% |
| profesional_juridico | 76 | 1.2% | 74 | 97.4% |
| barista_gastronomia | 20 | 0.3% | 20 | 100% |
| programa_pasantia | 19 | 0.3% | 19 | 100% |
| ventas_vehiculos | 0 | 0.0% | 0 | - |

**Cobertura total por familias:** 62.2% (4,055 ofertas)
**Sin clasificar:** 37.8% (2,466 ofertas)

---

## GAPS IDENTIFICADOS

### Patrones frecuentes en ofertas SIN_FAMILIA (2,466)

| Patrón | Frecuencia | Familia sugerida |
|--------|------------|------------------|
| Analista Contable | 20x | Ya debería ser admin_contable ⚠️ |
| Recepcionista | 16x | Ya debería ser servicios_atencion ⚠️ |
| Asesor Comercial | 16x | Ya debería ser comercial_ventas ⚠️ |
| Agente Inmobiliario | 16x | **NUEVA: inmobiliaria** |
| Gerente de operaciones | 14x | **NUEVA: gerencia/directivos** |
| Social Media Strategist | 13x | **NUEVA: marketing_digital** |
| Gerente de Administración | 13x | **NUEVA: gerencia/directivos** |
| Analista de RRHH | 12x | **NUEVA: recursos_humanos** |
| Community Manager | 9x | **NUEVA: marketing_digital** |
| Ayudante de Cocina | 9x | Ya debería ser operario_produccion ⚠️ |
| Técnico Electromecánico | 8x | Ya debería ser operario_produccion ⚠️ |

### Keywords que no están capturando bien

- **"Analista Contable"** → "analista" no está en KEYWORDS_ADMIN_CONTABLE_OFERTA
- **"Recepcionista"** → está pero solo detecta si está sola
- **"Ayudante de Cocina"** → "ayudante" no está en KEYWORDS_OPERARIO_PRODUCCION_OFERTA
- **"Técnico Electromecánico"** → falta en operario

### Familias nuevas sugeridas

1. **INMOBILIARIA**: agente inmobiliario, asesor inmobiliario, broker
2. **MARKETING_DIGITAL**: social media, community manager, content creator, SEO
3. **RECURSOS_HUMANOS**: analista RRHH, selector, recruiter, talent acquisition
4. **GERENCIA**: gerente, CEO, director general, líder de área
5. **TECNOLOGÍA/IT**: desarrollador, programador, DevOps, analista de sistemas

### Problema con ventas_vehiculos

La regla no matchea ninguna oferta porque:
- La condición es muy restrictiva: `tiene_ventas AND tiene_vehiculos AND NOT es_repuestos`
- `comercial_ventas` se evalúa primero y captura las ofertas de ventas de autos

---

## Familias con Más Errores (priorizar validación)

1. **barista_gastronomia** - 100% en revisión (20/20)
2. **programa_pasantia** - 100% en revisión (19/19)
3. **profesional_juridico** - 97.4% en revisión (74/76)
4. **SIN_FAMILIA** - 97.2% en revisión (2,397/2,466)

---

## Recomendaciones para Muestreo Estratificado

```python
# Propuesta de estratos para muestreo
ESTRATOS_MUESTREO = {
    # Estrato 1: Alta cobertura - muestreo proporcional
    'comercial_ventas': {'n': 130, 'prioridad': 'alta'},
    'admin_contable': {'n': 100, 'prioridad': 'alta'},
    'operario_produccion': {'n': 100, 'prioridad': 'media'},

    # Estrato 2: Media cobertura - sobremuestreo
    'salud_farmacia': {'n': 30, 'prioridad': 'media'},
    'nivel_junior': {'n': 30, 'prioridad': 'alta'},
    'servicios_atencion': {'n': 25, 'prioridad': 'media'},

    # Estrato 3: Baja cobertura - censo completo
    'profesional_juridico': {'n': 20, 'prioridad': 'alta'},
    'barista_gastronomia': {'n': 20, 'prioridad': 'alta'},
    'programa_pasantia': {'n': 19, 'prioridad': 'baja'},

    # Estrato 4: SIN_FAMILIA - crítico
    'SIN_FAMILIA': {'n': 200, 'prioridad': 'critica'},
}
```

---

## Código para Clasificar Ofertas

```python
from matching_rules_v83 import (
    es_oferta_admin_contable, es_oferta_comercial_ventas,
    es_oferta_servicios_atencion, es_oferta_operario_produccion,
    es_oferta_salud_farmacia, es_oferta_programa_pasantia,
    es_oferta_ventas_vehiculos, es_oferta_barista_gastronomia,
    es_oferta_profesional_juridico, es_oferta_nivel_junior
)

def clasificar_oferta(titulo, descripcion=""):
    """Retorna la familia funcional de una oferta"""
    if es_oferta_admin_contable(titulo, descripcion):
        return 'admin_contable'
    elif es_oferta_comercial_ventas(titulo, descripcion):
        return 'comercial_ventas'
    elif es_oferta_servicios_atencion(titulo, descripcion):
        return 'servicios_atencion'
    elif es_oferta_operario_produccion(titulo, descripcion):
        return 'operario_produccion'
    elif es_oferta_salud_farmacia(titulo, descripcion):
        return 'salud_farmacia'
    elif es_oferta_programa_pasantia(titulo, descripcion):
        return 'programa_pasantia'
    elif es_oferta_ventas_vehiculos(titulo, descripcion):
        return 'ventas_vehiculos'
    elif es_oferta_barista_gastronomia(titulo, descripcion):
        return 'barista_gastronomia'
    elif es_oferta_profesional_juridico(titulo, descripcion):
        return 'profesional_juridico'
    elif es_oferta_nivel_junior(titulo, descripcion):
        return 'nivel_junior'
    return 'SIN_FAMILIA'
```

---

## Archivos Relacionados

| Archivo | Descripción |
|---------|-------------|
| `database/matching_rules_v83.py` | Reglas de validación y familias funcionales |
| `database/match_ofertas_multicriteria.py` | Algoritmo de matching multicriteria |
| `database/analyze_familias_cobertura.py` | Script para analizar cobertura |
| `database/test_gold_set_manual.py` | Benchmark con gold set |

---

> **Última actualización:** 2025-12-06
