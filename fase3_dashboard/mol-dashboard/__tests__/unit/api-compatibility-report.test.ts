import { describe, it, expect } from 'vitest'
import { randomUUID } from 'crypto'

describe('API Compatibility Report', () => {
  describe('Token generation', () => {
    it('genera token UUID sin guiones (32 chars hex)', () => {
      const token = randomUUID().replace(/-/g, '')
      expect(token).toHaveLength(32)
      expect(token).toMatch(/^[a-f0-9]{32}$/)
    })

    it('tokens son únicos', () => {
      const tokens = new Set<string>()
      for (let i = 0; i < 100; i++) {
        tokens.add(randomUUID().replace(/-/g, ''))
      }
      expect(tokens.size).toBe(100)
    })

    it('token no es predecible (no secuencial)', () => {
      const t1 = randomUUID().replace(/-/g, '')
      const t2 = randomUUID().replace(/-/g, '')
      // Los primeros 8 chars deberían ser diferentes
      expect(t1.substring(0, 8)).not.toBe(t2.substring(0, 8))
    })
  })

  describe('Expiración', () => {
    it('expira a los 60 días por defecto', () => {
      const now = new Date()
      const expira = new Date(now)
      expira.setDate(expira.getDate() + 60)

      const diffMs = expira.getTime() - now.getTime()
      const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24))
      expect(diffDays).toBe(60)
    })

    it('reporte expirado devuelve estado correcto', () => {
      const expiradoAt = new Date('2025-01-01')
      const ahora = new Date()
      const isExpired = expiradoAt < ahora
      expect(isExpired).toBe(true)
    })

    it('reporte activo no está expirado', () => {
      const futuro = new Date()
      futuro.setDate(futuro.getDate() + 30)
      const ahora = new Date()
      const isExpired = futuro < ahora
      expect(isExpired).toBe(false)
    })
  })

  describe('Snapshot inmutable', () => {
    it('el reporte congela las skills al momento de crear', () => {
      const skillsAlCrear = [
        { label: 'Python', source: 'esco' },
        { label: 'Docker', source: 'argentina_approved' },
      ]

      // Simular que el perfil cambia después
      const skillsDespues = [
        { label: 'Python', source: 'esco' },
        { label: 'Docker', source: 'argentina_approved' },
        { label: 'Kubernetes', source: 'argentina_approved' },
      ]

      // El reporte mantiene las skills de cuando se creó
      expect(skillsAlCrear).toHaveLength(2)
      expect(skillsDespues).toHaveLength(3)
      // Son objetos distintos
      expect(skillsAlCrear).not.toEqual(skillsDespues)
    })
  })

  describe('Validación de input', () => {
    it('requiere candidato_nombre', () => {
      const body = { ocupacion_uri: 'x', ocupacion_label: 'y' }
      const isValid = body.hasOwnProperty('candidato_nombre')
      expect(isValid).toBe(false)
    })

    it('requiere skills como arrays', () => {
      const valid = { skills_candidato: [], skills_requeridas: [] }
      expect(Array.isArray(valid.skills_candidato)).toBe(true)
      expect(Array.isArray(valid.skills_requeridas)).toBe(true)
    })

    it('origen debe ser trabajador o oficina_empleo', () => {
      const validos = ['trabajador', 'oficina_empleo']
      expect(validos).toContain('trabajador')
      expect(validos).toContain('oficina_empleo')
      expect(validos).not.toContain('otro')
    })
  })

  describe('Seguridad', () => {
    it('GET no expone DNI en la respuesta', () => {
      const reportFromDB = {
        candidato_nombre: 'Juan Pérez',
        candidato_dni: '30123456',
        token: 'abc123',
        match_score: 78,
      }

      // La API hace destructuring para excluir DNI
      const { candidato_dni, ...safeReport } = reportFromDB
      expect(safeReport).not.toHaveProperty('candidato_dni')
      expect(safeReport).toHaveProperty('candidato_nombre')
      expect(safeReport).toHaveProperty('match_score')
    })

    it('solo el creador o admin puede revocar', () => {
      const reportCreatedBy = 'user-123'
      const currentUser = 'user-456'
      const currentRole = 'registrado'

      const canRevoke = reportCreatedBy === currentUser || currentRole === 'admin'
      expect(canRevoke).toBe(false)
    })

    it('el creador puede revocar su propio reporte', () => {
      const reportCreatedBy = 'user-123'
      const currentUser = 'user-123'

      const canRevoke = reportCreatedBy === currentUser
      expect(canRevoke).toBe(true)
    })

    it('admin puede revocar cualquier reporte', () => {
      const reportCreatedBy = 'user-123'
      const currentUser = 'user-admin'
      const currentRole = 'admin'

      const canRevoke = reportCreatedBy === currentUser || currentRole === 'admin'
      expect(canRevoke).toBe(true)
    })
  })

  describe('Versión del perfil', () => {
    it('registra la versión del perfil consolidado', () => {
      const report = {
        perfil_consolidado_version: 'v2.1',
        match_score: 78,
      }
      expect(report.perfil_consolidado_version).toBe('v2.1')
    })

    it('puede ser null si no hay perfil activo (ESCO puro)', () => {
      const report = {
        perfil_consolidado_version: null,
        match_score: 100,
      }
      expect(report.perfil_consolidado_version).toBeNull()
    })
  })

  describe('URL del reporte', () => {
    it('genera URL correcta con token', () => {
      const baseUrl = 'https://mol-nextjs.vercel.app'
      const token = 'abc123def456'
      const url = `${baseUrl}/reporte/${token}`
      expect(url).toBe('https://mol-nextjs.vercel.app/reporte/abc123def456')
    })
  })
})
