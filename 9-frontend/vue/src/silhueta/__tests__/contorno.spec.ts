import { describe, it, expect } from 'vitest'
import { caminhoSuave, SILHUETA } from '../contorno'

describe('contorno da silhueta', () => {
  it('gera um caminho fechado para as duas versões', () => {
    for (const s of Object.values(SILHUETA)) {
      expect(s.d.startsWith('M')).toBe(true)
      expect(s.d.endsWith('Z')).toBe(true)
    }
    expect(SILHUETA.f.d).not.toBe(SILHUETA.m.d)
  })

  it('espelha a metade direita: um ponto vira dois, simétricos em x = 100', () => {
    // topo (100,0) → (120,50) → virilha (100,100): o espelho acrescenta (80,50)
    const d = caminhoSuave([
      [100, 0],
      [120, 50],
      [100, 100],
    ])
    expect(d).toContain(' 120 50')
    expect(d).toContain(' 80 50')
    expect(d.match(/C/g)).toHaveLength(4) // 4 pontos no contorno fechado = 4 curvas
  })
})
