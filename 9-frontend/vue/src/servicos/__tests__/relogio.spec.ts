import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { motivo, notificacao, paraMostrador, usarRelogio, type ApiRelogio } from '../relogio'
import type { ApiEvento } from '../api'

const base: ApiRelogio = {
  eu: {
    tripulante_id: 'sarah',
    nome: 'Sarah',
    papel: 'Comandante',
    gerada_em: '2026-11-14T12:51:09Z',
    estado: 'otimo',
    homeostase: 100,
    qualidade: 'bom',
    fc: 74,
    spo2: 98,
    hrv: 62,
    agua_ml_dia: 1700,
    agua_meta: 2400,
    dose_msv_dia: 2.9,
    sexo: 'feminino',
    metricas: { fc: { z: 0.9, faixa: 'padrao' }, spo2: { z: 0, faixa: 'padrao' } },
  },
  contagem: { otimos: 7, atencao: 0, criticos: 0 },
  pendencias: [],
  acompanhando: [],
  emergencia: false,
  ciclo: null,
  link: { missao: 'mars', rotulo: 'Trânsito para Marte', blackout: false, atraso_txt: '8 min 20 s' },
  equipe: { local: 'bordo', medico_nome: 'Dr. Marcus', marcus: { nome: 'Dr. Marcus' } },
}

const ev = (p: Partial<ApiEvento>): ApiEvento => ({
  id: 'ev-1',
  classe: 'aviso',
  tipo: 'ciclo',
  tripulante_id: 'sarah',
  nome: 'Sarah',
  estado: 'aguardando_humano',
  nivel_autonomia: 2,
  responsavel_id: 'sarah',
  responsavel_nome: 'Sarah',
  medico_local: 'bordo',
  medico_nome: 'Dr. Marcus',
  prazo_restante_s: null,
  gerado_em: '2026-11-14T12:52:00Z',
  sugestao: null,
  decisoes: [],
  dados: {},
  ...p,
})

describe('mostrador', () => {
  it('em rotina, "No seu padrão"; fora do padrão, o sinal e a direção', () => {
    expect(motivo(base)).toBe('No seu padrão')
    const r = { ...base, eu: { ...base.eu, metricas: { spo2: { z: -3, faixa: 'critico' as const }, fc: { z: 2, faixa: 'atencao' as const } } } }
    expect(motivo(r)).toBe('SpO₂ baixa e FC alta')
  })

  it('emergência deixa o relógio crítico', () => {
    const m = paraMostrador({ ...base, emergencia: true })
    expect(m.nivel).toBe(2)
    expect(m.estado.motivo).toBe('Alerta médico')
  })

  it('o ciclo aparece só no trecho do calendário e sem método', () => {
    expect(paraMostrador(base).ciclo).toBeUndefined()
    const m = paraMostrador({ ...base, ciclo: { na_janela: true, aviso_dias: 2, privado: true } })
    expect(m.ciclo).toEqual({ aviso: '2d' })
    expect(JSON.stringify(m)).not.toMatch(/pilula|pílula|lútea/i)
    expect(m.missao).toBe('Marte')
  })
})

describe('notificações do pulso', () => {
  it('sem pendência, nada', () => {
    expect(notificacao(base)).toBeNull()
  })

  it('ciclo pergunta antes e só depois oferece contar', () => {
    const antes = notificacao({ ...base, pendencias: [ev({ dados: { aviso_dias: 2 } })] })!
    expect(antes.texto).toContain('Em 2 dia(s)')
    expect(antes.botoes.map((b) => b.rotulo)).toEqual(['Estou sentindo', 'Estou bem'])
    const depois = notificacao({ ...base, pendencias: [ev({ dados: { sintoma: true } })] })!
    expect(depois.botoes.map((b) => b.rotulo)).toContain('Contar ao Dr. Marcus')
  })

  it('sem médico a bordo, o ciclo só vai à médica da Terra', () => {
    const n = notificacao({
      ...base,
      pendencias: [ev({ dados: { sintoma: true }, medico_local: 'terra', medico_nome: 'Dra. Rivera' })],
    })!
    expect(n.texto).toContain('O CMO e a família não veem')
    expect(n.botoes.map((b) => b.rotulo)).toContain('Contar só à Dra. Rivera')
  })

  it('arritmia acompanhada: alerta sem botão de cancelar', () => {
    const n = notificacao({ ...base, emergencia: true, acompanhando: [ev({ tipo: 'arritmia', classe: 'evento', responsavel_id: 'marcus' })] })!
    expect(n.variante).toBe('crit')
    expect(n.botoes).toEqual([])
  })
})

describe('usarRelogio', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('a decisão no pulso é assinada pela dona do relógio', async () => {
    const fetch = vi.fn(async (url: string, _init?: RequestInit) => new Response(JSON.stringify(url.includes('/relogio') ? base : { ok: true })))
    vi.stubGlobal('fetch', fetch)
    let api!: ReturnType<typeof usarRelogio>
    const C = defineComponent({
      setup() {
        api = usarRelogio(ref('elena'), 60_000)
        return () => h('div')
      },
    })
    const w = mount(C)
    await flushPromises()
    await api.decidir('ev-9', 'compartilhar')
    const post = fetch.mock.calls.find(([u]) => String(u).endsWith('/api/decisoes'))!
    expect(JSON.parse(post[1]!.body as string)).toEqual({ evento_id: 'ev-9', humano_id: 'elena', acao: 'compartilhar' })
    w.unmount()
  })
})
