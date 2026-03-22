/**
 * Unit tests for scraping commands (H2)
 * Tests: command structure, valid states, create validation
 */
import { describe, it, expect } from 'vitest'
import { mockScrapingCommandsRPC, mockCreateCommandResponse } from '../mocks/fixtures/scraping-commands'

const VALID_COMMANDS = ['lanzar_portal', 'lanzar_todos', 'sync_vps_local', 'pausar_portal'];
const VALID_STATES = ['pendiente', 'ejecutando', 'completado', 'error', 'cancelado'];

describe('scraping commands', () => {
  describe('command list structure', () => {
    it('is an array of commands', () => {
      expect(mockScrapingCommandsRPC).toBeInstanceOf(Array)
      expect(mockScrapingCommandsRPC.length).toBeGreaterThan(0)
    })

    it('each command has required fields', () => {
      for (const cmd of mockScrapingCommandsRPC) {
        expect(cmd).toHaveProperty('id')
        expect(cmd).toHaveProperty('comando')
        expect(cmd).toHaveProperty('estado')
        expect(cmd).toHaveProperty('creado_por')
        expect(cmd).toHaveProperty('created_at')
      }
    })

    it('commands have valid tipo', () => {
      for (const cmd of mockScrapingCommandsRPC) {
        expect(VALID_COMMANDS).toContain(cmd.comando)
      }
    })

    it('commands have valid estado', () => {
      for (const cmd of mockScrapingCommandsRPC) {
        expect(VALID_STATES).toContain(cmd.estado)
      }
    })
  })

  describe('command states', () => {
    it('completado has completed_at and resultado', () => {
      const completed = mockScrapingCommandsRPC.find(c => c.estado === 'completado')
      expect(completed).toBeDefined()
      expect(completed!.completed_at).toBeTruthy()
      expect(completed!.resultado).toBeTruthy()
      expect(completed!.error_mensaje).toBeNull()
    })

    it('ejecutando has started_at but no completed_at', () => {
      const executing = mockScrapingCommandsRPC.find(c => c.estado === 'ejecutando')
      expect(executing).toBeDefined()
      expect(executing!.started_at).toBeTruthy()
      expect(executing!.completed_at).toBeNull()
    })

    it('error has error_mensaje', () => {
      const errored = mockScrapingCommandsRPC.find(c => c.estado === 'error')
      expect(errored).toBeDefined()
      expect(errored!.error_mensaje).toBeTruthy()
    })

    it('pendiente has no started_at or completed_at', () => {
      const pending = mockScrapingCommandsRPC.find(c => c.estado === 'pendiente')
      expect(pending).toBeDefined()
      expect(pending!.started_at).toBeNull()
      expect(pending!.completed_at).toBeNull()
    })
  })

  describe('lanzar_portal requires portal param', () => {
    it('lanzar_portal commands have params.portal', () => {
      const portalCmds = mockScrapingCommandsRPC.filter(c => c.comando === 'lanzar_portal')
      for (const cmd of portalCmds) {
        expect(cmd.params).toHaveProperty('portal')
        expect(typeof cmd.params.portal).toBe('string')
      }
    })
  })

  describe('create command response', () => {
    it('has id and estado pendiente', () => {
      expect(mockCreateCommandResponse.id).toBeTruthy()
      expect(mockCreateCommandResponse.estado).toBe('pendiente')
    })

    it('has creado_por', () => {
      expect(mockCreateCommandResponse.creado_por).toBeTruthy()
    })
  })

  describe('duracion_seg calculation', () => {
    it('completed command has positive duration', () => {
      const completed = mockScrapingCommandsRPC.find(c => c.estado === 'completado')
      expect(completed!.duracion_seg).toBeGreaterThan(0)
    })

    it('pending command has null duration', () => {
      const pending = mockScrapingCommandsRPC.find(c => c.estado === 'pendiente')
      expect(pending!.duracion_seg).toBeNull()
    })
  })
})
