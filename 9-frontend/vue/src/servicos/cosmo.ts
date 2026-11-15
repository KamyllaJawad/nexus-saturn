// Com a API no ar, a pergunta vai para POST /api/cosmo/chat (Cosmo do 8-backend, com a
// visão da superfície e a trilha de auditoria). Offline, responde com o mock abaixo.

import { tripulacaoMock, type Tripulante } from '@/mocks/tripulacao'
import { conexao, perguntarApi } from './api'
import { statusNaveMock } from '@/mocks/nave'
import { DECISOES, KIT_MEDICO } from '@/mocks/decisoes'

export interface PerguntaCosmo {
  origem: 'painel' | 'relogio'
  tripulante_id?: string
  mensagem: string
}

export interface Fonte {
  titulo: string
  trecho?: string
}

export interface RespostaCosmo {
  resposta: string
  fontes: Fonte[]
  gerada_em: string
}

export async function perguntarCosmo(
  pergunta: PerguntaCosmo,
  opcoes: { signal?: AbortSignal; atrasoMs?: number } = {},
): Promise<RespostaCosmo> {
  if (conexao.value === 'api') {
    const superficie = pergunta.origem === 'painel' ? 'bordo' : 'relogio'
    const r = await perguntarApi(pergunta.mensagem, superficie, pergunta.tripulante_id, opcoes.signal)
    return {
      resposta: r.resposta,
      fontes: r.fonte ? [{ titulo: r.fonte.titulo, trecho: r.fonte.referencia }] : [],
      gerada_em: new Date().toISOString(),
    }
  }

  await esperar(opcoes.atrasoMs ?? 900, opcoes.signal)
  return { ...responderMock(pergunta), gerada_em: new Date().toISOString() }
}

function esperar(ms: number, signal?: AbortSignal) {
  return new Promise<void>((ok, erro) => {
    const t = setTimeout(ok, ms)
    signal?.addEventListener('abort', () => {
      clearTimeout(t)
      erro(new DOMException('Pergunta cancelada', 'AbortError'))
    })
  })
}

const NIVEL = ['ótimo', 'atenção', 'crítico']

function resumo(t: Tripulante): string {
  const v = t.vitais
  return (
    `${t.nome}: ${NIVEL[t.nivel]}, FC ${v.fc} bpm, SpO₂ ${v.spo2}%, PA ${v.paSis}/${v.paDia}, ` +
    `homeostase ${t.homeostase}%. ${DECISOES[t.id]?.acompanhamento.itens[0] ?? ''}`
  ).trim()
}

function hormonal(t: Tripulante): Omit<RespostaCosmo, 'gerada_em'> {
  const h = t.hormonal
  if (!h) return { resposta: `O perfil de ${t.nome} não tem contexto hormonal registrado.`, fontes: [] }
  if (!h.compartilhado)
    return {
      resposta:
        `${t.nome} não compartilhou nada sobre o ciclo com você. O calendário fica no relógio dela; ` +
        'método e fase não aparecem no painel, e nada sai sem o consentimento dela.',
      fontes: [{ titulo: 'ADR-013 · calendário do ciclo no relógio' }],
    }
  return {
    resposta:
      `${t.nome} compartilhou: ${h.resumo}. O estado segue como está e isso não é diagnóstico. ` +
      'Método e fase não aparecem no painel. Analgésico do kit só se ela pedir.',
    fontes: [{ titulo: 'ADR-014 · ciclo hormonal, privado por padrão' }],
  }
}

export function responderMock(p: PerguntaCosmo): Omit<RespostaCosmo, 'gerada_em'> {
  const texto = p.mensagem.toLowerCase()
  const citado = tripulacaoMock.find(
    (t) => texto.includes(t.id) || texto.includes(t.nome.toLowerCase()),
  )
  const alvo = citado ?? tripulacaoMock.find((t) => t.id === p.tripulante_id) ?? tripulacaoMock[0]!

  if (/kit|rem[eé]dio|estoque|medica/.test(texto))
    return { resposta: KIT_MEDICO, fontes: [{ titulo: 'Inventário do kit médico' }] }

  if (/ciclo|horm[oô]n|menstrua|p[ií]lula|\bdiu\b|ovula|estrog/.test(texto)) return hormonal(alvo)

  if (/houston|terra|sinal/.test(texto)) {
    const s = statusNaveMock
    return {
      resposta: s.houstonOnline
        ? `Houston está a ${s.atrasoHouston} de distância de sinal. O que você decidir aqui chega lá com esse atraso.`
        : 'Houston está fora de alcance. Eu continuo funcionando com os modelos locais da nave.',
      fontes: [],
    }
  }

  if (citado || /resumo|como (est|t[aá])/.test(texto))
    return { resposta: resumo(alvo), fontes: [{ titulo: 'Sinais vitais do relógio e do kit médico' }] }

  if (/aten[cç]|quem|prioridade|hoje/.test(texto)) {
    const atencao = tripulacaoMock.filter((t) => t.nivel > 0)
    const estaveis = tripulacaoMock.filter((t) => t.nivel === 0).map((t) => t.nome)
    return {
      resposta:
        atencao.map((t) => `${t.nome}: ${t.destaque ?? NIVEL[t.nivel]}; vale conversar hoje.`).join(' ') +
        ` Estáveis: ${estaveis.join(', ')}.`,
      fontes: [{ titulo: 'Estado da tripulação' }],
    }
  }

  return {
    resposta:
      'Neste protótipo eu respondo sobre a tripulação, o kit médico, Houston e saúde hormonal. ' +
      'Tente citar um nome, como "Como está a Elena?".',
    fontes: [],
  }
}
