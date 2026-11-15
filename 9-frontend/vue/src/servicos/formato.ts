// Formatação e nomes usados em todas as telas (o mesmo que compartilhado/api.js fazia
// nas telas em JS puro).

import { reactive } from 'vue'

export const TRIPULACAO = [
  { id: 'sarah', nome: 'Sarah', papel: 'Comandante' },
  { id: 'marcus', nome: 'Dr. Marcus', papel: 'Oficial médico' },
  { id: 'elena', nome: 'Elena', papel: 'Engenheira de voo' },
  { id: 'kenji', nome: 'Kenji', papel: 'Especialista de missão' },
]
export const MEDICA_TERRA = { id: 'rivera', nome: 'Dra. Rivera', papel: 'Flight surgeon · Houston' }

// Sem médico a bordo o Marcus vira oficial de saúde (CMO). A API manda em `equipe`.
const marcus = reactive({ nome: 'Dr. Marcus', papel: 'Oficial médico' })
export function ajustarEquipe(eq?: { marcus?: { nome: string; papel: string } } | null) {
  if (eq?.marcus) Object.assign(marcus, eq.marcus)
}
export function nome(id: string | null | undefined): string {
  if (!id) return '—'
  if (id === 'marcus') return marcus.nome
  return [...TRIPULACAO, MEDICA_TERRA].find((p) => p.id === id)?.nome ?? id
}
export function papel(id: string): string {
  if (id === 'marcus') return marcus.papel
  return TRIPULACAO.find((p) => p.id === id)?.papel ?? ''
}

export const ESTADO: Record<string, string> = { otimo: 'Ótimo', atencao: 'Atenção', critico: 'Crítico', suspeito: 'Sinal a confirmar' }
export const classe = (e: string) => (e === 'critico' ? 'crit' : e === 'atencao' || e === 'suspeito' ? 'warn' : 'ok')
export const classeFaixa = (f?: string) => (f === 'critico' ? 'crit' : f === 'atencao' ? 'warn' : 'ok')

export const TIPO: Record<string, string> = {
  arritmia: 'Arritmia',
  sensor_suspeito: 'Leitura suspeita',
  tempestade_solar: 'Tempestade solar',
  prontidao_eva: 'Prontidão para a EVA',
  dor_de_cabeca: 'Dor de cabeça',
  bem_estar: 'Bem-estar',
  modo_noite: 'Modo noite',
  ciclo: 'Calendário do ciclo',
  linha_de_base: 'Combinação fora do padrão',
  hidratacao: 'Hidratação',
}
export const ESTADO_EVENTO: Record<string, string> = {
  detectado: 'detectado',
  confirmacao_astronauta: 'confirmando com o astronauta',
  proposto: 'proposto',
  aguardando_humano: 'aguardando humano',
  escalonado: 'escalonado',
  decidido: 'decidido',
  em_execucao: 'em execução',
  resolvido: 'resolvido',
  encerrado: 'encerrado',
  agendado: 'agendado com veto',
  aplicado: 'aplicado',
}
export const SINAL: Record<string, string> = {
  fc: 'FC',
  hrv: 'HRV',
  spo2: 'SpO₂',
  temperatura: 'temperatura',
  respiracao: 'respiração',
  sono: 'sono',
  hidratacao: 'hidratação',
}
export const FINAIS = ['resolvido', 'encerrado']

export const num = (v: unknown, casas = 0) =>
  v === null || v === undefined || v === '' || Number.isNaN(Number(v))
    ? '—'
    : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
export const hora = (iso?: string | null, seg = false) => (iso ? iso.slice(11, seg ? 19 : 16) : '—')
export const sono = (min?: number | null) =>
  min == null ? '—' : `${Math.floor(min / 60)}h${String(Math.round(min % 60)).padStart(2, '0')}`
export const pct = (v: number) => `${Math.round(v * 100)}%`

// A tela está dentro de um iframe da sala de simulação?
export const embutida = (() => {
  try {
    return window.self !== window.top
  } catch {
    return true
  }
})()

export const RODAPE = 'Protótipo experimental com dados simulados. Não é dispositivo médico.'
