import { describe, it, expect } from 'vitest'
import { AMOSTRAS_POR_SEGUNDO, GeradorEcg, type ClasseRitmo } from '../gerador'

// Gerador de números "aleatórios" previsível, para o teste dar sempre o mesmo resultado.
function aleatorioComSemente(semente: number) {
  return () => {
    semente = (semente * 1664525 + 1013904223) % 4294967296
    return semente / 4294967296
  }
}

// Grava `segundos` de ECG e devolve o intervalo (s) entre cada par de picos R.
function intervalosEntrePicos(fc: number, classe: ClasseRitmo, segundos = 20): number[] {
  const total = segundos * AMOSTRAS_POR_SEGUNDO
  const gerador = new GeradorEcg(total + 10, aleatorioComSemente(42))
  for (let i = 0; i < segundos * 60; i++) gerador.avancar(1 / 60, fc, classe)

  const v = gerador.buffer
  const picos: number[] = []
  for (let i = 1; i < total - 1; i++) {
    if (v[i]! > 0.6 && v[i]! >= v[i - 1]! && v[i]! > v[i + 1]!) picos.push(i)
  }
  const intervalos = picos.slice(1).map((p, i) => (p - picos[i]!) / AMOSTRAS_POR_SEGUNDO)
  // Ignora o primeiro batimento, que começa com uma duração padrão (0,83 s).
  return intervalos.slice(1)
}

function media(xs: number[]) {
  return xs.reduce((a, b) => a + b, 0) / xs.length
}

describe('GeradorEcg', () => {
  it('no ritmo normal, bate na frequência pedida e de forma regular', () => {
    const intervalos = intervalosEntrePicos(60, 'normal')

    expect(media(intervalos)).toBeCloseTo(1, 1) // 60 bpm = 1 batimento por segundo
    for (const i of intervalos) {
      expect(i).toBeGreaterThan(0.95)
      expect(i).toBeLessThan(1.05)
    }
  })

  it('acompanha a FC: com 120 bpm, os batimentos ficam com metade da duração', () => {
    expect(media(intervalosEntrePicos(120, 'normal'))).toBeCloseTo(0.5, 1)
  })

  it('na fibrilação atrial, a distância entre os batimentos fica irregular', () => {
    const intervalos = intervalosEntrePicos(60, 'fa')
    const m = media(intervalos)
    const desvio = Math.sqrt(media(intervalos.map((i) => (i - m) ** 2)))

    // Coeficiente de variação: no normal fica perto de 2%; na FA, bem acima de 10%.
    expect(desvio / m).toBeGreaterThan(0.1)
  })
})
