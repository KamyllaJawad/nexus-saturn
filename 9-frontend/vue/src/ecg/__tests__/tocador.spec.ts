import { describe, expect, it } from 'vitest'
import { AMOSTRAS_POR_SEGUNDO } from '../gerador'
import { TocadorEcg, normalizar } from '../tocador'

// 1 s a 100 Hz com um "pico R" por segundo.
const trecho = (origem: string, pico = 2) => ({
  fs: 100,
  origem,
  amostras: Array.from({ length: 100 }, (_, i) => (i === 50 ? pico : 0.1)),
})

describe('TocadorEcg', () => {
  it('normaliza para a linha de base ficar em 0', () => {
    const n = normalizar(trecho('A1').amostras)
    expect(n[0]).toBeCloseTo(0)
    expect(Math.max(...n)).toBeLessThanOrEqual(1.2)
  })

  it('escreve no buffer no mesmo ritmo do gerador', () => {
    const t = new TocadorEcg(600)
    t.carregar(trecho('A1'))
    t.avancar(1)
    expect(t.posicao).toBe(AMOSTRAS_POR_SEGUNDO)
    expect(t.origem).toBe('A1')
  })

  it('o trecho novo só entra quando o atual termina', () => {
    const t = new TocadorEcg(600)
    t.carregar(trecho('A1'))
    t.avancar(0.5)
    t.carregar(trecho('A2'))
    expect(t.origem).toBe('A1')
    t.avancar(0.6)
    expect(t.origem).toBe('A2')
  })

  it('sem trecho, não escreve nada', () => {
    const t = new TocadorEcg(600)
    t.avancar(1)
    expect(t.pronto).toBe(false)
    expect(t.posicao).toBe(0)
  })
})
