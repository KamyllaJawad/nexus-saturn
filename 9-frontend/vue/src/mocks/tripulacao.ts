// Dados mockados da tripulação para utilizar sem o back

import type { ClasseRitmo } from '@/ecg/gerador'

// 0 = ótimo · 1 = atenção · 2 = crítico
export type NivelSaude = 0 | 1 | 2
export type ChaveSinal = 'fc' | 'spo2' | 'pa' | 'resp' | 'hrv' | 'agua'


export interface Tripulante {
  id: string
  nome: string
  cargo: string
  nivel: NivelSaude
  homeostase: number // % · quanto dos sinais está no padrão da pessoa (vem do back)
  // Sinal que pede atenção, mostrado ao lado do cargo (ex.: "Água 63%").
  destaque?: string
  ritmo: ClasseRitmo
  vitais: Vitais
  // Faixa de cada sinal. Vem pronta do back: o front não decide o que é normal.
  faixas: Record<ChaveSinal, NivelSaude>
  sexo: 'f' | 'm' // define qual silhueta aparece
  // Estado de cada órgão destacado na silhueta. Também vem pronto do back.
  corpo: Record<Orgao, NivelSaude>
  radiacao: { hojeMsv: number; missaoMsv: number }
  // Só existe para quem registrou contexto hormonal (ADR-013).
  hormonal?: ContextoHormonal
}

export type Orgao = 'cerebro' | 'coracao' | 'pulmoes' | 'rins'

// ADR-013 e ADR-014: o calendário do ciclo fica no relógio e é privado por padrão.
// O painel recebe só o que a pessoa compartilhou pelo relógio (sintomas e pedido de
// cuidado leve), nunca o método nem a fase. Sem consentimento: { compartilhado: false }.
export type ContextoHormonal =
  | { compartilhado: false }
  | {
      compartilhado: true
      resumo: string // o que ela autorizou o oficial médico a ver
    }

export interface Vitais {
  fc: number        // bpm
  spo2: number      // %
  paSis: number     // pressão sistólica, mmHg
  paDia: number     // pressão diastólica, mmHg
  resp: number      // respirações por minuto
  hrv: number       // ms
  agua: number      // ml bebidos hoje
  aguaMeta: number  // ml
}

export const tripulacaoMock: Tripulante[] = [
  {
    id: 'sarah',
    nome: 'Sarah',
    cargo: 'Comandante',
    nivel: 0,
    homeostase: 94,
    ritmo: 'normal',
    vitais: { fc: 71, spo2: 98, paSis: 118, paDia: 76, resp: 14, hrv: 64, agua: 1450, aguaMeta: 2400 },
    faixas: { fc: 0, spo2: 0, pa: 0, resp: 0, hrv: 0, agua: 1 },
    sexo: 'f',
    corpo: { cerebro: 1, coracao: 0, pulmoes: 0, rins: 1 },
    radiacao: { hojeMsv: 0.42, missaoMsv: 38 },
    hormonal: { compartilhado: false },
  },
  {
    id: 'marcus',
    nome: 'Dr. Marcus',
    cargo: 'Oficial médico',
    nivel: 0,
    homeostase: 100,
    ritmo: 'normal',
    vitais: { fc: 64, spo2: 98, paSis: 122, paDia: 80, resp: 13, hrv: 71, agua: 1900, aguaMeta: 2600 },
    faixas: { fc: 0, spo2: 0, pa: 0, resp: 0, hrv: 0, agua: 0 },
    sexo: 'm',
    corpo: { cerebro: 0, coracao: 0, pulmoes: 0, rins: 0 },
    radiacao: { hojeMsv: 0.4, missaoMsv: 38 },
  },
  {
    id: 'elena',
    nome: 'Elena',
    cargo: 'Engenheira de voo',
    nivel: 1,
    homeostase: 91,
    destaque: 'Água 63%',
    ritmo: 'normal',
    vitais: { fc: 82, spo2: 97, paSis: 114, paDia: 72, resp: 15, hrv: 46, agua: 1510, aguaMeta: 2400 },
    faixas: { fc: 0, spo2: 0, pa: 0, resp: 0, hrv: 0, agua: 1 },
    sexo: 'f',
    corpo: { cerebro: 1, coracao: 0, pulmoes: 0, rins: 1 },
    radiacao: { hojeMsv: 0.45, missaoMsv: 38 },
    hormonal: { compartilhado: false },
  },
  {
    id: 'kenji',
    nome: 'Kenji',
    cargo: 'Especialista de missão',
    nivel: 0,
    homeostase: 100,
    ritmo: 'normal',
    vitais: { fc: 68, spo2: 98, paSis: 126, paDia: 82, resp: 12, hrv: 82, agua: 2100, aguaMeta: 2500 },
    faixas: { fc: 0, spo2: 0, pa: 0, resp: 0, hrv: 0, agua: 0 },
    sexo: 'm',
    corpo: { cerebro: 0, coracao: 0, pulmoes: 0, rins: 0 },
    radiacao: { hojeMsv: 0.41, missaoMsv: 38 },
  },
]
