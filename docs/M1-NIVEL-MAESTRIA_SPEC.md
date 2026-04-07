# M1-NIVEL-MAESTRIA — Nivel de maestría por skill en Perfil de Competencias

## Contexto

`perfil_skills` ya tiene columna `nivel` (default 'intermedio') y `certificado`
(default false). No están expuestos en la UI. Este spec los agrega al panel
derecho de M1 (SkillProfilePanel) y los persiste en Supabase.

---

## Pre-condición (verificar antes de arrancar)

```sql
-- nivel y certificado ya existen
SELECT column_name, column_default 
FROM information_schema.columns 
WHERE table_name = 'perfil_skills' 
AND column_name IN ('nivel', 'certificado');
-- Esperado: nivel DEFAULT 'intermedio', certificado DEFAULT false
```

---

## Decisión de diseño — escala de nivel

**4 niveles:** Básico · Intermedio · Avanzado · Experto

Razón: 3 niveles es poco para capturar la diferencia entre alguien que
aprendió algo hace un año y alguien con 10 años de experiencia. "Experto"
es el nivel que se puede certificar o validar institucionalmente.

**Certificado:** flag independiente del nivel. Alguien puede tener
certificado de nivel básico. Se muestra como badge separado.

---

## Cambios en el tipo SkillItem

```typescript
// Agregar a la interfaz existente:
export interface SkillItem {
  // campos existentes...
  nivel?: 'basico' | 'intermedio' | 'avanzado' | 'experto'  // default: 'intermedio'
  certificado?: boolean                                       // default: false
}
```

---

## Cambios en SkillProfilePanel.tsx

Cada skill en el panel derecho pasa de chip simple a chip con controles
inline de nivel y certificado. El técnico los asigna durante la entrevista.

### UI por skill

```
┌─────────────────────────────────────────────────────┐
│ soldadura MIG/MAG          ███ esencial         [×] │
│ [Básico] [Intermedio●] [Avanzado] [Experto]  [✓ Cert]│
└─────────────────────────────────────────────────────┘
```

**Reglas:**
- Los 4 botones de nivel son mutuamente excluyentes
- El nivel activo tiene fondo coloreado (ej: teal)
- `[✓ Cert]` es toggle independiente — verde cuando activo
- Default al agregar una skill: Intermedio, sin certificado
- Los controles aparecen siempre (no solo en hover) — 
  el técnico los asigna durante la entrevista, no después

### Colores de nivel

| Nivel | Color activo |
|-------|-------------|
| Básico | gris azulado |
| Intermedio | teal |
| Avanzado | azul |
| Experto | violeta |

---

## Cambios en useSkillCapture.ts

El hook maneja el estado de skills. Al agregar una skill nueva,
inicializarla con nivel 'intermedio' y certificado false:

```typescript
// Al agregar skills (addSkills):
const nuevasConNivel = incoming.map(s => ({
  ...s,
  nivel: s.nivel ?? 'intermedio',
  certificado: s.certificado ?? false
}))
```

Agregar función para actualizar nivel/certificado de una skill existente:

```typescript
const updateSkillNivel = (uri: string, nivel: NivelMaestria) => {
  // Actualizar en el array de skills del store
}

const toggleSkillCertificado = (uri: string) => {
  // Toggle certificado en el array de skills del store
}
```

---

## Cambios en APIs

### POST /api/perfiles/[id]/skills

Ya acepta `via_captura`, `estado`, `confianza`. Agregar `nivel` y
`certificado` al row mapping:

```typescript
// Agregar al insert:
nivel: skill.nivel ?? 'intermedio',
certificado: skill.certificado ?? false,
```

### PUT /api/perfiles/[id] (edición completa)

El PUT ya borra skills viejas y reinserta. Asegurarse de que el DELETE +
INSERT preserve nivel y certificado de las skills que se mantienen.

---

## Criterios de aceptación

- [ ] Cada skill en el panel derecho muestra 4 botones de nivel
- [ ] El nivel activo tiene indicador visual diferenciado
- [ ] Click en nivel → actualiza estado local inmediatamente
- [ ] `[✓ Cert]` toggle funciona independiente del nivel
- [ ] Al guardar el perfil, nivel y certificado se persisten en Supabase
- [ ] Al editar un perfil existente, nivel y certificado se cargan 
      correctamente en los botones
- [ ] Skills nuevas inician con nivel 'intermedio' y certificado false
- [ ] La DemandBar y badge 'esencial' siguen funcionando sin cambios

---

## Tests

`tests/m1-nivel-maestria.test.ts`
- Agregar skill → nivel default 'intermedio'
- Click en 'avanzado' → nivel cambia a 'avanzado'
- Click en cert → certificado toggle a true
- Guardar perfil → Supabase tiene nivel y certificado correctos
- Cargar perfil con nivel 'experto' → botón 'experto' activo

---

## Notas

- No modificar las vías de captura (OccupationSkillPicker, 
  FreeTextSkillExtractor, etc.) — el nivel se asigna en el 
  panel derecho después de agregar la skill, no durante la captura.
- El nivel 'experto' implica que el técnico puede validar 
  institucionalmente — en el futuro se conectará con el 
  campo `validado_por_tecnico`. Por ahora es solo declarativo.
- `certificado` y `validado_por_tecnico` son distintos:
  certificado = la persona declara tener un certificado
  validado_por_tecnico = el técnico vio el certificado físico
  Por ahora solo implementar certificado. validado_por_tecnico
  se activa en una iteración futura.
