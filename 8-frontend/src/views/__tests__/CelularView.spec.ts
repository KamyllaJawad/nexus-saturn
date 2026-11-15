import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import CelularView from '../CelularView.vue'
import { ATRASO_MS, TEMPO_PARA_SARAH_BRINDAR_MS } from '@/mocks/familia'

const botao = (w: VueWrapper, texto: string) => {
  const b = w.findAll('button').find((x) => x.text().includes(texto))
  if (!b) throw new Error(`botão "${texto}" não encontrado`)
  return b
}

describe('CelularView', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('na emergência, a família não vê os detalhes de saúde', async () => {
    const w = mount(CelularView)
    expect(w.text()).toContain('A Sarah está bem')
    expect(w.text()).toContain('Dormiu')

    await botao(w, 'Emergência').trigger('click')
    expect(w.text()).toContain('acompanhada pela equipe médica')
    expect(w.text()).not.toContain('Dormiu')
    expect(w.text()).not.toContain('% da meta')
  })

  it('a mensagem sai "A caminho" e vira "Entregue" depois do atraso', async () => {
    const w = mount(CelularView)
    await botao(w, 'Mensagens').trigger('click')
    await botao(w, 'Enviar áudio do Lucas').trigger('click')
    expect(w.text()).toContain('A caminho')

    await vi.advanceTimersByTimeAsync(ATRASO_MS)
    expect(w.text()).toContain('Entregue')
  })

  it('no blackout a mensagem fica na fila e sai quando o sinal volta', async () => {
    const w = mount(CelularView)
    await botao(w, 'Blackout').trigger('click')
    await botao(w, 'Mensagens').trigger('click')
    await botao(w, 'Enviar áudio do Lucas').trigger('click')
    expect(w.text()).toContain('Na fila: sem sinal')

    await vi.advanceTimersByTimeAsync(ATRASO_MS * 3)
    expect(w.text()).toContain('Na fila: sem sinal')

    await botao(w, 'Normal').trigger('click')
    await vi.advanceTimersByTimeAsync(ATRASO_MS)
    expect(w.text()).toContain('Entregue')
  })

  it('o brinde vai até "Brinde concluído" e aparece nas últimas da nave', async () => {
    const w = mount(CelularView)
    await botao(w, 'Elo').trigger('click')
    expect(w.text()).toContain('Ecossistema 86% saudável')
    await botao(w, 'Brindar com a Sarah').trigger('click')
    expect(w.text()).toContain('Convite a caminho')

    await vi.advanceTimersByTimeAsync(ATRASO_MS + TEMPO_PARA_SARAH_BRINDAR_MS + ATRASO_MS)
    expect(w.text()).toContain('Brinde concluído')
    expect(w.text()).toContain('Ecossistema 89% saudável')

    await botao(w, 'Início').trigger('click')
    expect(w.text()).toContain('A Sarah brindou com a Ana')
  })
})
