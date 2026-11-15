// Trilha mínima da Cosmo (ADR-018): tokens, latência, custo, decisão e passos.
import { num } from './formato'

export interface RegistroTrilha {
  id: string
  quando: string
  superficie: string
  origem: string
  pergunta?: string | null
  modo: string
  via_link?: boolean
  recebido_em?: string
  tokens: { entrada: number; saida: number; total: number; fonte: string }
  latencia_ms: number
  custo: { usd: number; energia_mwh: number; base: string }
  decisao: { tipo: string; resumo: string }
  passos: { etapa: string; detalhe: string; ms: number }[]
}
export interface ResumoTrilha {
  chamadas: number
  tokens_entrada: number
  tokens_saida: number
  latencia_media_ms: number
  latencia_p95_ms: number
  custo_usd: number
  energia_mwh: number
  watts: number
  com_llm: number
  por_decisao: Record<string, number>
}
export interface Trilha {
  resumo: ResumoTrilha
  resumo_bordo?: ResumoTrilha
  registros: RegistroTrilha[]
}

export const ms = (v: number) => `${num(v, v < 10 ? 2 : 1)} ms`
export const usd = (v: number) => `US$ ${num(v, 4)}`

// Rodapé curto de cada resposta no chat.
export const rodapeTrilha = (t: Pick<RegistroTrilha, 'tokens' | 'latencia_ms' | 'custo' | 'decisao'>) =>
  `${num(t.tokens.total)} tokens · ${ms(t.latencia_ms)} · ${usd(t.custo.usd)} · ${t.decisao.tipo}`
