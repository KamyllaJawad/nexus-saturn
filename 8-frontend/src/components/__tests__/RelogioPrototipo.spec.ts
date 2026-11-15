import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RelogioPrototipo from '../RelogioPrototipo.vue'
import { PREVIA_ESTADO } from '@/mocks/relogio'

describe('RelogioPrototipo', () => {
  it('mostra o estado, os sinais e o chip do ciclo da astronauta', () => {
    const w = mount(RelogioPrototipo, {
      props: { nivel: 0, sexo: 'f', estado: PREVIA_ESTADO[0], ciclo: { dia: 16, fase: 'lútea' } },
    })
    expect(w.text()).toContain('Ótimo')
    expect(w.text()).toContain('Fase lútea · no seu padrão')
    expect(w.text()).toContain('D16')
  })

  it('em atenção e crítico, o motivo vem do sinal, nunca da fase do ciclo', () => {
    for (const nivel of [1, 2] as const) {
      const w = mount(RelogioPrototipo, {
        props: { nivel, sexo: 'f', estado: PREVIA_ESTADO[nivel], ciclo: { dia: 24, fase: 'lútea' } },
      })
      expect(w.text()).toContain(PREVIA_ESTADO[nivel].motivo)
      expect(w.text()).not.toContain('Fase lútea')
      expect(w.text()).toContain('D24') // o ciclo continua visível, como contexto
    }
  })

  it('não mostra chip de ciclo para quem não tem contexto hormonal', () => {
    const w = mount(RelogioPrototipo, { props: { nivel: 0, sexo: 'm', estado: PREVIA_ESTADO[0] } })
    expect(w.text()).not.toContain('♀')
  })
})
