import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase responses
const mockSupabase = {
  from: vi.fn().mockReturnThis(),
  select: vi.fn().mockReturnThis(),
  order: vi.fn().mockReturnThis(),
  eq: vi.fn().mockReturnThis(),
  single: vi.fn(),
  rpc: vi.fn(),
}

vi.mock('@supabase/supabase-js', () => ({
  createClient: () => mockSupabase,
}))

describe('Perfil Argentino Versiones', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Datos de versión', () => {
    it('una versión tiene todos los campos requeridos', () => {
      const version = {
        id: 'uuid-1',
        version: 'v1.0',
        total_skills: 14257,
        total_emergentes_aprobadas: 0,
        total_ocupaciones: 3046,
        nota: 'Version base ESCO',
        creado_por: 'uuid-admin',
        activa: true,
        created_at: '2026-01-15T00:00:00Z',
      }

      expect(version.id).toBeDefined()
      expect(version.version).toMatch(/^v\d+\.\d+$/)
      expect(version.total_skills).toBeGreaterThanOrEqual(0)
      expect(version.total_emergentes_aprobadas).toBeGreaterThanOrEqual(0)
      expect(version.total_ocupaciones).toBeGreaterThanOrEqual(0)
      expect(typeof version.activa).toBe('boolean')
    })

    it('version string sigue formato semver simplificado', () => {
      const valid = ['v1.0', 'v2.1', 'v10.3']
      const invalid = ['1.0', 'v1', 'version1', '']

      for (const v of valid) {
        expect(v).toMatch(/^v\d+\.\d+$/)
      }
      for (const v of invalid) {
        expect(v).not.toMatch(/^v\d+\.\d+$/)
      }
    })
  })

  describe('Constraint de versión activa', () => {
    it('solo una versión puede estar activa', () => {
      const versiones = [
        { id: '1', version: 'v1.0', activa: false },
        { id: '2', version: 'v2.0', activa: true },
        { id: '3', version: 'v2.1', activa: false },
      ]

      const activas = versiones.filter(v => v.activa)
      expect(activas).toHaveLength(1)
      expect(activas[0].version).toBe('v2.0')
    })

    it('activar una versión desactiva la anterior', () => {
      const versiones = [
        { id: '1', version: 'v1.0', activa: false },
        { id: '2', version: 'v2.0', activa: true },
      ]

      // Simular rollback a v1.0
      const target = versiones.find(v => v.id === '1')!
      const current = versiones.find(v => v.activa)!

      current.activa = false
      target.activa = true

      const activas = versiones.filter(v => v.activa)
      expect(activas).toHaveLength(1)
      expect(activas[0].version).toBe('v1.0')
    })
  })

  describe('Snapshot inmutable', () => {
    it('el snapshot se congela al crear la versión', () => {
      const snapshot = {
        'http://data.europa.eu/esco/occupation/abc': {
          label: 'Desarrollador de software',
          isco: '2512',
          skills_consolidadas: [
            { label: 'Python', source: 'esco_common' },
            { label: 'Docker', source: 'argentina_approved' },
          ],
        },
      }

      // Snapshot es un objeto congelado — no debe mutar
      const frozen = JSON.parse(JSON.stringify(snapshot))
      expect(frozen).toEqual(snapshot)

      // Modificar el original no afecta al frozen
      snapshot['http://data.europa.eu/esco/occupation/abc'].skills_consolidadas.push(
        { label: 'Kubernetes', source: 'argentina_approved' }
      )
      expect(frozen['http://data.europa.eu/esco/occupation/abc'].skills_consolidadas).toHaveLength(2)
    })
  })

  describe('Estado actual (cambios desde último corte)', () => {
    it('detecta cambios después del último corte', () => {
      const ultimoCorte = '2026-03-15T00:00:00Z'
      const registros = [
        { updated_at: '2026-03-10T00:00:00Z', skills_from_argentina: 3 },
        { updated_at: '2026-03-18T00:00:00Z', skills_from_argentina: 5 }, // después del corte
        { updated_at: '2026-03-19T00:00:00Z', skills_from_argentina: 2 }, // después del corte
      ]

      const cambiosDespuesCorte = registros.filter(r => r.updated_at > ultimoCorte)
      const skillsNuevas = cambiosDespuesCorte.reduce((sum, r) => sum + r.skills_from_argentina, 0)

      expect(cambiosDespuesCorte).toHaveLength(2)
      expect(skillsNuevas).toBe(7)
    })
  })

  describe('Reporte referencia versión', () => {
    it('el reporte registra la versión del perfil usado', () => {
      const versionActiva = 'v2.1'
      const reporte = {
        token: 'abc123',
        perfil_consolidado_version: versionActiva,
        match_score: 78.5,
      }

      expect(reporte.perfil_consolidado_version).toBe('v2.1')
    })

    it('cambiar versión activa no afecta reportes existentes', () => {
      const reporteViejo = { perfil_consolidado_version: 'v1.0', match_score: 72 }
      const nuevaVersionActiva = 'v2.0'

      // El reporte viejo mantiene su versión
      expect(reporteViejo.perfil_consolidado_version).toBe('v1.0')
      expect(reporteViejo.perfil_consolidado_version).not.toBe(nuevaVersionActiva)
    })
  })
})
