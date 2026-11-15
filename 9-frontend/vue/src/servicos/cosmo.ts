// Sem VITE_COSMO_URL no .env, responde com mock.

import { tripulacaoMock, type Tripulante } from '@/mocks/tripulacao'
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

const URL_COSMO: string | undefined = import.meta.env.VITE_COSMO_URL

export async function perguntarCosmo(
  pergunta: PerguntaCosmo,
  opcoes: { signal?: AbortSignal; atrasoMs?: number } = {},
): Promise<RespostaCosmo> {
  if (URL_COSMO) {
    const r = await fetch(`${URL_COSMO}/cosmo/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pergunta),
      signal: opcoes.signal,
    })
    if (!r.ok) throw new Error(`A Cosmo respondeu com erro ${r.status}`)
    return (await r.json()) as RespostaCosmo
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
        `${t.nome} não compartilhou o contexto hormonal com você. Eu uso essa informação só a bordo, ` +
        'para não gerar alarme falso, e não mostro nada sem consentimento. Ela pode compartilhar pelo relógio.',
      fontes: [{ titulo: 'ADR-013 · consentimento de saúde reprodutiva' }],
    }
  const fase = h.dia ? `dia ${h.dia} de ${h.duracao}, fase ${h.fase.toLowerCase()}` : h.fase.toLowerCase()
  return {
    resposta: `${t.nome}: ${h.metodo.toLowerCase()}, ${fase}. ${h.efeito}. Pela linha de base desta fase, está no padrão dela, sem alerta.`,
    fontes: [{ titulo: 'Linha de base por fase do ciclo (m3-fase-0.1)' }],
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
