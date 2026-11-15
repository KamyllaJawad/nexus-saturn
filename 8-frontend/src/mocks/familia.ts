export type Cenario = 'normal' | 'emergencia' | 'blackout'
export type Aba = 'inicio' | 'elo' | 'mensagens'
export type FaseBrinde = 'enviado' | 'chegou' | 'brindou' | 'concluido'

export interface Mensagem {
  id: number
  texto: string
  status: 'fila' | 'caminho' | 'entregue'
  hora?: string
}

export interface ItemFeed {
  texto: string
  hora: string
}

export const MISSAO = {
  local: 'Estação Espacial Internacional',
  distancia: 'a 408 km de altitude',
  atraso: '< 1 s',
  blackout: { motivo: 'Perda de sinal entre satélites TDRS', volta: '~10 min' },
}

export const ATRASO_MS = 800
export const TEMPO_PARA_SARAH_BRINDAR_MS = 2500

export const RESUMO_DIA = {
  sono: '7h40',
  treino: '45 min na esteira',
  humor: 'Dia tranquilo',
}

export const ESTUFA_INICIAL = { nivel: 4, pct: 86 }
export const DESAFIO_INICIAL = { km: 43.6, meta: 60 }

export const HABITOS = [
  { texto: 'Lucas correu 5 km na praia', efeito: '+15% energia' },
  { texto: 'Ana bebeu 500 ml de água', efeito: '+25% hidro-pod' },
]

export const MENSAGEM_DA_SARAH = { texto: 'Oi, família! Treino feito por hoje.', hora: 'Ontem · 21:10' }
