import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  conexao,
  paraCard,
  paraDecisao,
  paraStatus,
  paraTripulante,
  type ApiBordo,
  type ApiEvento,
  type ApiTripulante,
} from '../api'
import { perguntarCosmo } from '../cosmo'

// Leitura real de GET /api/bordo (Sarah em rotina), sem os campos que o adaptador não usa.
const sarah: ApiTripulante = {
  tripulante_id: 'sarah',
  nome: 'Sarah',
  papel: 'Comandante',
  gerada_em: '2026-11-14T12:40:40Z',
  estado: 'otimo',
  homeostase: 100,
  qualidade: 'bom',
  fc: 72,
  hrv: 67,
  spo2: 98,
  temp_pele: 36.8,
  respiracao: 14,
  sono_min_noite: 420,
  agua_ml_dia: 1700,
  pa_sys: 118,
  pa_dia: 76,
  estresse: 43,
  dose_msv_dia: 2.402,
  agua_meta: 2400,
  metricas: {
    fc: { z: 0, faixa: 'padrao' },
    hrv: { z: 1, faixa: 'padrao' },
    spo2: { z: 0, faixa: 'padrao' },
    temperatura: { z: 0, faixa: 'padrao' },
    respiracao: { z: 0, faixa: 'padrao' },
    sono: { z: -0.9, faixa: 'padrao' },
    hidratacao: { z: -0.9, faixa: 'padrao' },
  },
  m1: { classe: 'normal', confianca: 0.89, versao_modelo: 'arritmia-borda-0.3' },
}

const kenji: ApiTripulante = { ...sarah, tripulante_id: 'kenji', nome: 'Kenji', papel: 'Especialista de missão' }

const missao: ApiBordo['missao'] = {
  hora_nave: '2026-11-14T12:40:40Z',
  missao: 'mars',
  rotulo: 'Trânsito para Marte',
  atraso_txt: '8 min 20 s',
  blackout: false,
  cabine: { co2: 2.4, fluxo: 'normal', luz: 'dia' },
  equipe: { local: 'bordo', medico_nome: 'Dr. Marcus', marcus: { nome: 'Dr. Marcus', papel: 'Oficial médico' } },
}

function evento(parcial: Partial<ApiEvento>): ApiEvento {
  return {
    id: 'ev-1',
    classe: 'evento',
    tipo: 'arritmia',
    tripulante_id: 'sarah',
    nome: 'Sarah',
    estado: 'aguardando_humano',
    nivel_autonomia: 2,
    responsavel_id: 'marcus',
    responsavel_nome: 'Dr. Marcus',
    medico_local: 'bordo',
    medico_nome: 'Dr. Marcus',
    prazo_restante_s: 40,
    gerado_em: '2026-11-14T12:41:00Z',
    sugestao: { confianca: 0.87, versao_modelo: 'arritmia-borda-0.3' },
    decisoes: [],
    dados: {},
    ...parcial,
  }
}

const bordo = (p: Partial<ApiBordo> = {}): ApiBordo => ({
  missao,
  tripulantes: [sarah, kenji],
  eventos: [],
  avisos_compartilhados: [],
  ...p,
})

describe('paraTripulante', () => {
  it('traduz a leitura da API para o formato dos componentes', () => {
    const t = paraTripulante(sarah, bordo())
    expect(t).toMatchObject({
      id: 'sarah',
      cargo: 'Comandante',
      nivel: 0,
      ritmo: 'normal',
      vitais: { fc: 72, paSis: 118, paDia: 76, resp: 14, agua: 1700, aguaMeta: 2400 },
      faixas: { fc: 0, spo2: 0, pa: 0, resp: 0, hrv: 0, agua: 0 },
      radiacao: { hojeMsv: 2.402, missaoMsv: 212 },
    })
  })

  it('FA no M1 deixa o coração crítico e o ECG em FA', () => {
    const t = paraTripulante({ ...sarah, estado: 'critico', m1: { classe: 'fa' } }, bordo())
    expect(t.nivel).toBe(2)
    expect(t.ritmo).toBe('fa')
    expect(t.corpo.coracao).toBe(2)
  })

  it('mostra o destaque da hidratação como no mock', () => {
    const t = paraTripulante(
      { ...sarah, agua_ml_dia: 1510, metricas: { ...sarah.metricas, hidratacao: { z: -2, faixa: 'atencao' } } },
      bordo(),
    )
    expect(t.destaque).toBe('Água 63%')
    expect(t.faixas.agua).toBe(1)
  })

  it('ciclo: privado por padrão e, com consentimento, sem método nem fase', () => {
    expect(paraTripulante(sarah, bordo()).hormonal).toEqual({ compartilhado: false })
    expect(paraTripulante(kenji, bordo()).hormonal).toBeUndefined()

    const aviso = evento({ id: 'av-1', classe: 'aviso', tipo: 'ciclo', estado: 'encerrado' })
    const h = paraTripulante(sarah, bordo({ avisos_compartilhados: [aviso] })).hormonal
    expect(h?.compartilhado).toBe(true)
    expect(JSON.stringify(h)).not.toMatch(/lútea|folicular|pílula|\bdiu\b|implante|dia \d/i)
  })
})

describe('paraStatus', () => {
  it('blackout e médico na Terra mudam o cabeçalho', () => {
    const s = paraStatus({
      ...missao,
      blackout: true,
      equipe: { ...missao.equipe, local: 'terra', medico_nome: 'Dra. Rivera' },
    })
    expect(s.houstonOnline).toBe(false)
    expect(s.titulo).toContain('CMO')
    expect(s.subtitulo).toContain('Dra. Rivera')
  })
})

describe('paraDecisao e paraCard', () => {
  it('arritmia aguardando o oficial médico vira "Confirmar protocolo"', () => {
    const d = paraDecisao(evento({}))
    expect(d.urgente).toBe(true)
    expect(d.acao).toMatchObject({ evento_id: 'ev-1', acao_api: 'confirmar' })
    expect(d.texto).toContain('87%')
  })

  it('sem médico a bordo, manda para o painel completo', () => {
    const d = paraDecisao(evento({ medico_local: 'terra', medico_nome: 'Dra. Rivera' }))
    expect(d.painelCompleto).toBe(true)
    expect(d.acao).toBeUndefined()
  })

  it('não oferece botão quando o responsável é outra pessoa', () => {
    const d = paraDecisao(evento({ responsavel_id: 'sarah', responsavel_nome: 'Sarah' }))
    expect(d.acao).toBeUndefined()
    expect(d.texto).toContain('Quem decide agora: Sarah')
  })

  it('sem eventos, o card diz que não há decisão pendente', () => {
    const c = paraCard('kenji', bordo({ eventos: [evento({})] }))
    expect(c.decisao).toBeUndefined()
    expect(c.acompanhamento.titulo).toBe('Nenhuma decisão pendente')
  })

  it('o evento aberto da pessoa vira a decisão do card', () => {
    const c = paraCard('sarah', bordo({ eventos: [evento({})] }))
    expect(c.decisao?.titulo).toBe('Arritmia · Sarah')
  })
})

describe('Cosmo pela API', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    conexao.value = 'testando'
  })

  it('usa o contrato de POST /api/cosmo/chat e traduz a fonte', async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ resposta: 'Sarah estável.', fonte: { titulo: 'Protocolo FA', referencia: 'NASA' } }), {
        status: 200,
      }),
    )
    vi.stubGlobal('fetch', fetch)
    conexao.value = 'api'

    const r = await perguntarCosmo({ origem: 'painel', tripulante_id: 'sarah', mensagem: 'Como está a Sarah?' })

    const [url, init] = fetch.mock.calls[0]!
    expect(url).toBe('/api/cosmo/chat')
    expect(JSON.parse(init.body)).toEqual({ pergunta: 'Como está a Sarah?', superficie: 'bordo', tripulante_id: 'sarah' })
    expect(r.resposta).toBe('Sarah estável.')
    expect(r.fontes).toEqual([{ titulo: 'Protocolo FA', trecho: 'NASA' }])
  })
})
