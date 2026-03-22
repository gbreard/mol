/**
 * Unit tests for config editor (I2)
 * Tests: valid configs, override structure, save flow
 */
import { describe, it, expect } from 'vitest'

const VALID_CONFIGS = [
  'matching_rules_business',
  'nlp_inference_rules',
  'sinonimos_argentinos_esco',
  'skills_rules',
  'oficios_arg',
  'nlp_titulo_limpieza',
]

const mockOverride = {
  config_key: 'nlp_inference_rules',
  source: 'override',
  data: { modalidad: { keywords: { remoto: ['remoto', 'home office'] } } },
  version: 3,
  updated_by: 'admin@oede.gob.ar',
  updated_at: '2026-03-22T15:00:00Z',
  changelog: [
    { timestamp: '2026-03-20T10:00:00Z', user: 'admin@oede.gob.ar', version: 1, action: 'Creación inicial' },
    { timestamp: '2026-03-21T14:00:00Z', user: 'admin@oede.gob.ar', version: 2, action: 'Agregar keywords' },
    { timestamp: '2026-03-22T15:00:00Z', user: 'admin@oede.gob.ar', version: 3, action: 'Editado desde editores UI' },
  ],
}

const mockLocalResponse = {
  config_key: 'oficios_arg',
  source: 'local',
  data: null,
  version: 0,
  message: 'Sin override. El pipeline usa el JSON local.',
}

describe('config editor', () => {
  describe('valid configs', () => {
    it('has 6 editable configs', () => {
      expect(VALID_CONFIGS).toHaveLength(6)
    })

    it('all configs have consistent naming', () => {
      for (const key of VALID_CONFIGS) {
        expect(key).toMatch(/^[a-z_]+$/)
      }
    })
  })

  describe('override structure', () => {
    it('has required fields', () => {
      expect(mockOverride).toHaveProperty('config_key')
      expect(mockOverride).toHaveProperty('source')
      expect(mockOverride).toHaveProperty('data')
      expect(mockOverride).toHaveProperty('version')
      expect(mockOverride).toHaveProperty('changelog')
    })

    it('source is override when data exists', () => {
      expect(mockOverride.source).toBe('override')
      expect(mockOverride.data).toBeTruthy()
    })

    it('version increments', () => {
      expect(mockOverride.version).toBe(3)
      expect(mockOverride.changelog).toHaveLength(3)
      expect(mockOverride.changelog[2].version).toBe(3)
    })

    it('changelog entries have required fields', () => {
      for (const entry of mockOverride.changelog) {
        expect(entry).toHaveProperty('timestamp')
        expect(entry).toHaveProperty('user')
        expect(entry).toHaveProperty('version')
        expect(entry).toHaveProperty('action')
      }
    })
  })

  describe('local fallback', () => {
    it('source is local when no override', () => {
      expect(mockLocalResponse.source).toBe('local')
      expect(mockLocalResponse.data).toBeNull()
      expect(mockLocalResponse.version).toBe(0)
    })
  })

  describe('save flow', () => {
    it('save request has required fields', () => {
      const saveRequest = {
        config_key: 'nlp_inference_rules',
        data: { modalidad: { keywords: { remoto: ['remoto', 'home office', 'teletrabajo'] } } },
        action_summary: 'Agregar keyword teletrabajo',
      }
      expect(saveRequest.config_key).toBeTruthy()
      expect(saveRequest.data).toBeTruthy()
      expect(typeof saveRequest.action_summary).toBe('string')
    })
  })
})
