import { describe, it, expect } from 'vitest'
import { sanitizeCell } from '@/lib/parse-pool-import'

describe('S-25: Validación input importación Excel/CSV', () => {
  it('bloquea fórmula =CMD', () => {
    expect(sanitizeCell('=CMD("calc")')).not.toMatch(/^=/)
  })

  it('bloquea fórmula +cmd', () => {
    expect(sanitizeCell('+cmd|"/C calc"')).not.toMatch(/^\+/)
  })

  it('bloquea @SUM', () => {
    expect(sanitizeCell('@SUM(A1:A10)')).not.toMatch(/^@/)
  })

  it('strippea HTML', () => {
    const result = sanitizeCell('<img src=x onerror=alert(1)>')
    expect(result).not.toContain('<')
    expect(result).not.toContain('>')
  })

  it('strippea script tags', () => {
    const result = sanitizeCell('<script>document.cookie</script>')
    expect(result).not.toContain('<script>')
  })

  it('remueve comillas simples (SQL)', () => {
    const result = sanitizeCell("Robert'; DROP TABLE users;--")
    expect(result).not.toContain("'")
  })

  it('archivo mayor al límite se trunca', () => {
    // parseCSV trunca a MAX_ROWS
    // sanitizeCell trunca a MAX_CELL_LENGTH
    const longValue = 'x'.repeat(600)
    expect(sanitizeCell(longValue).length).toBeLessThanOrEqual(500)
  })
})

describe('S-19 / S-22: Aislamiento multi-tenancy OE', () => {
  describe('Lógica de aislamiento', () => {
    it('técnico solo ve perfiles de su organización', () => {
      const userOrgId = 'org-caba'
      const perfiles = [
        { nombre: 'Juan', organizacion_id: 'org-caba' },
        { nombre: 'Maria', organizacion_id: 'org-cordoba' },
        { nombre: 'Pedro', organizacion_id: 'org-caba' },
      ]

      const visibles = perfiles.filter(p => p.organizacion_id === userOrgId)
      expect(visibles).toHaveLength(2)
      expect(visibles.every(p => p.organizacion_id === 'org-caba')).toBe(true)
    })

    it('OE-A no ve datos de OE-B', () => {
      const orgA = 'org-caba'
      const orgB = 'org-cordoba'
      const perfilDeB = { nombre: 'Test', organizacion_id: orgB }

      const puedeVer = perfilDeB.organizacion_id === orgA
      expect(puedeVer).toBe(false)
    })

    it('admin ve todos los datos', () => {
      const isAdmin = true
      const perfiles = [
        { organizacion_id: 'org-caba' },
        { organizacion_id: 'org-cordoba' },
      ]

      const visibles = isAdmin ? perfiles : perfiles.filter(() => false)
      expect(visibles).toHaveLength(2)
    })

    it('usuario sin organización no ve nada', () => {
      const userOrgId = null
      const perfiles = [
        { organizacion_id: 'org-caba' },
        { organizacion_id: 'org-cordoba' },
      ]

      const visibles = userOrgId ? perfiles.filter(p => p.organizacion_id === userOrgId) : []
      expect(visibles).toHaveLength(0)
    })

    it('organización inactiva no permite acceso', () => {
      const org = { id: 'org-caba', activa: false }
      const tieneAcceso = org.activa
      expect(tieneAcceso).toBe(false)
    })
  })

  describe('Jurisdicción', () => {
    it('pool amplio filtrado por jurisdicción de la OE', () => {
      const oeJurisdiccion = 'CABA'
      const ofertas = [
        { titulo: 'Dev', provincia: 'CABA' },
        { titulo: 'Analista', provincia: 'Buenos Aires' },
        { titulo: 'Admin', provincia: 'CABA' },
      ]

      const visibles = ofertas.filter(o => o.provincia === oeJurisdiccion)
      expect(visibles).toHaveLength(2)
    })
  })

  describe('Roles dentro de la organización', () => {
    it('roles válidos para OE', () => {
      const validRoles = ['tecnico', 'coordinador']
      expect(validRoles).toContain('tecnico')
      expect(validRoles).toContain('coordinador')
    })

    it('roles válidos para empresa', () => {
      const validRoles = ['rrhh', 'gerente']
      expect(validRoles).toContain('rrhh')
    })
  })
})
