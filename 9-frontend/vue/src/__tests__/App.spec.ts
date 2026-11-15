import { describe, it, expect } from 'vitest'

import { flushPromises, mount } from '@vue/test-utils'
import App from '../App.vue'
import router from '../router'

describe('App', () => {
  it('abre a sala de simulação na rota inicial, com a navegação entre as telas', async () => {
    router.push('/')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('sala')
    expect(wrapper.text()).toContain('Sala de simulação')
    for (const tela of ['Relógio', 'Painel de bordo', 'Houston', 'Família', 'Dados e IA']) expect(wrapper.text()).toContain(tela)
    wrapper.unmount()
  })

  it('abre o painel de bordo em /bordo', async () => {
    router.push('/bordo')
    await router.isReady()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await flushPromises()

    expect(router.currentRoute.value.name).toBe('bordo')
    expect(wrapper.text()).toContain('Enfermaria')
    wrapper.unmount()
  })
})
