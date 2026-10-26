import { describe, it, expect } from 'vitest'
import fijadas from '@/lib/demo/recomendaciones-demo.json'
import { parseTrayectoria } from '@/lib/recomendacion-ia'

// Las recomendaciones DEMO se sirven tal cual (sin pasar por el modelo ni el parser):
// tienen que cumplir la misma forma y las reglas de texto acordadas.
describe('recomendaciones DEMO fijadas', () => {
  const entradas = Object.entries(fijadas as Record<string, any>)

  it('son las 5 de los perfiles DEMO, a nivel perfil', () => {
    expect(entradas).toHaveLength(5)
    for (const [clave] of entradas) expect(clave).toMatch(/^[0-9a-f-]{36}\|$/)
  })

  it.each(entradas)('%s cumple la forma de la trayectoria', (_clave, reco) => {
    expect(parseTrayectoria(JSON.stringify(reco))).not.toBeNull()
    expect(reco.alternativas.length).toBeLessThanOrEqual(2)
    expect(reco.pasos.length).toBeLessThanOrEqual(3)
  })

  it('sin promesas, certificaciones ni invitaciones a postular a avisos vencidos', () => {
    const texto = JSON.stringify(fijadas)
    for (const prohibido of [/postular a los/i, /certific/i, /exactamente/i, /rápidamente/i, /completar (el|tu) perfil/i]) {
      expect(texto).not.toMatch(prohibido)
    }
  })
})
