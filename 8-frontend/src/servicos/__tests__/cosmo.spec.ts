import { describe, it, expect } from 'vitest'
import { perguntarCosmo, responderMock } from '../cosmo'
import { tripulacaoMock } from '@/mocks/tripulacao'

describe('Cosmo (mock)', () => {
  it('resume o tripulante citado com os sinais dele', () => {
    const r = responderMock({ origem: 'painel', mensagem: 'Como está a Elena?' })
    expect(r.resposta).toContain('Elena')
    expect(r.resposta).toContain('FC 82 bpm')
    expect(r.fontes.length).toBeGreaterThan(0)
  })

  it('não revela o contexto hormonal sem consentimento', () => {
    const sarah = tripulacaoMock.find((t) => t.id === 'sarah')!
    const original = sarah.hormonal
    sarah.hormonal = { compartilhado: false }
    try {
      const r = responderMock({ origem: 'painel', tripulante_id: 'sarah', mensagem: 'Qual a fase do ciclo?' })
      expect(r.resposta).toContain('não compartilhou')
      expect(r.resposta).not.toMatch(/lútea|dia 16/i)
    } finally {
      sarah.hormonal = original
    }
  })

  it('pode ser cancelada', async () => {
    const c = new AbortController()
    const p = perguntarCosmo({ origem: 'painel', mensagem: 'oi' }, { signal: c.signal, atrasoMs: 50 })
    c.abort()
    await expect(p).rejects.toThrow('cancelada')
  })
})
