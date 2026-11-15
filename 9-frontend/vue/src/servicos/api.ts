// Cliente da API do 8-backend e adaptador para os tipos que os componentes já usam.
//
// Os componentes continuam recebendo `Tripulante`, `StatusNave` e `CardDoTripulante`.
// Este arquivo só traduz o que a API manda (GET /api/bordo) para esses tipos.
// Servido pela API (porta 8000) ou pelo `npm run dev` (proxy de /api), o caminho é relativo.

import { ref } from 'vue'
import type { ChaveSinal, NivelSaude, Orgao, Tripulante } from '@/mocks/tripulacao'
import type { StatusNave } from '@/mocks/nave'
import type { Acao, CardDoTripulante, Decisao } from '@/mocks/decisoes'
import type { TrechoEcg } from '@/ecg/tocador'
import type { RegistroTrilha, Trilha } from './trilha'

export const API_BASE: string = import.meta.env.VITE_API_URL ?? ''

// 'api': os dados vêm do back. 'offline': a API não respondeu e a tela usa os mocks.
export const conexao = ref<'testando' | 'api' | 'offline'>('testando')

// ---------------------------------------------------------------- formato da API
export type Faixa = 'padrao' | 'atencao' | 'critico'

export interface ApiTripulante {
  tripulante_id: string
  nome: string
  papel: string
  gerada_em: string
  estado: 'otimo' | 'atencao' | 'critico' | 'suspeito'
  homeostase: number
  qualidade: string
  fc: number
  hrv: number
  spo2: number
  temp_pele: number
  respiracao: number
  sono_min_noite: number
  agua_ml_dia: number
  pa_sys: number
  pa_dia: number
  estresse: number
  dose_msv_dia: number
  agua_meta: number
  metricas: Record<string, { z: number; faixa: Faixa }>
  m1: {
    classe: 'normal' | 'fa' | 'outro' | null
    confianca?: number
    prob_fa?: number
    versao_modelo?: string
    motivo?: string
  } | null
  m2?: { qualidade: string; confianca: number; motivo: string | null; versao_modelo: string }
  isolation_forest?: {
    anomalo: boolean
    score: number
    limiar: number
    acima_do_limiar: boolean
    seguidas: number
    persistencia: number
    evidencias: string[]
    versao_modelo: string
  }
  sombra?: Record<string, { versao_modelo: string; score: number; limiar: number; anomalo: boolean }>
  versao_z?: string
  // Campos do passo 4 (s.clinico() e /api/bordo). Opcionais: uma API mais antiga não manda.
  sexo?: 'feminino' | 'masculino' | null
  corpo?: Record<Orgao, Faixa>
  saude_hormonal?: { compartilhado: false } | { compartilhado: true; resumo: string } | null
}

export interface ApiEvento {
  id: string
  classe: 'evento' | 'aviso'
  tipo: string
  tripulante_id: string
  nome: string
  estado: string
  nivel_autonomia: number
  responsavel_id: string
  responsavel_nome: string
  medico_local: 'bordo' | 'terra'
  medico_nome: string
  prazo_restante_s: number | null
  escalonamentos?: number
  gerado_em: string
  sugestao: { texto?: string; confianca?: number; versao_modelo?: string; alternativa?: string; evidencias?: string[] } | null
  decisoes: { acao: string; humano_id: string; decidida_em: string }[]
  dados: Record<string, unknown>
}

export interface OrdemPermanente {
  id: string
  titulo: string
  dose: string
  assinada_por_nome: string
  assinada_em: string
  depois: string
  em_vigor: boolean
  vale_agora: boolean
}

export interface ApiMissao {
  hora_nave: string
  missao: string
  rotulo: string
  atraso_txt: string
  blackout: boolean
  cabine: { co2: number; fluxo: string; luz: string }
  equipe: {
    local: 'bordo' | 'terra'
    medico_nome: string
    medico_id?: string
    resumo?: string
    marcus: { nome: string; papel: string }
  }
  // Usados nos fluxos sem médico a bordo e no blackout.
  link?: string
  comprimido?: boolean
  atraso_real_s?: number
  atraso_demo_s?: number
  volta_em?: string
  motivo_blackout?: string
  autonomia?: string
  ordem_permanente?: OrdemPermanente
}

export interface ApiBordo {
  missao: ApiMissao
  tripulantes: ApiTripulante[]
  eventos: ApiEvento[]
  avisos_compartilhados: ApiEvento[]
  sombra?: Record<string, { versao: string; leituras: number; divergem: number }>
  trilha_cosmo?: Trilha
}

// ---------------------------------------------------------------- chamadas
export async function pedir<T>(caminho: string, corpo?: unknown, signal?: AbortSignal): Promise<T> {
  const r = await fetch(
    `${API_BASE}/api${caminho}`,
    corpo === undefined
      ? { signal }
      : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo), signal },
  )
  if (!r.ok) {
    let msg = `A API respondeu ${r.status}`
    try {
      msg = ((await r.json()) as { detail?: string }).detail || msg
    } catch {
      /* corpo vazio */
    }
    throw new Error(msg)
  }
  return (await r.json()) as T
}

export const buscarBordo = () => pedir<ApiBordo>('/bordo')

// 6 s de ECG do relógio: gravação do conjunto de teste do CinC 2017 (FA no cenário de FA).
export const buscarEcg = (tid: string) => pedir<TrechoEcg>(`/tripulantes/${encodeURIComponent(tid)}/ecg`)

// Esta tela é do oficial médico (ou do CMO, sem médico a bordo), como o bordo/ atual.
export const EU = 'marcus'

// Decisão com tudo o que a rota aceita: dose e PIN na medicação, detalhe nos demais.
export function decidirEvento(corpo: {
  evento_id: string
  acao: string
  humano_id?: string
  dose?: string
  pin?: string
  detalhe?: Record<string, unknown>
}) {
  return pedir('/decisoes', { humano_id: EU, ...corpo })
}

export function enviarDecisao(evento_id: string, acao: string, detalhe?: Record<string, unknown>, humano_id = EU) {
  return pedir('/decisoes', { evento_id, humano_id, acao, ...(detalhe ? { detalhe } : {}) })
}

export interface RespostaChatApi {
  resposta: string
  fonte: { titulo: string; referencia?: string } | null
  modo?: string
  visao?: string
  trilha?: RegistroTrilha
}

export interface GrupoPerguntas {
  grupo: string
  perguntas: string[]
}
export const buscarPerguntas = (superficie: string, tripulante_id: string) =>
  pedir<GrupoPerguntas[]>(`/cosmo/perguntas?superficie=${superficie}&tripulante_id=${encodeURIComponent(tripulante_id)}`)

export function perguntarApi(
  pergunta: string,
  superficie: 'bordo' | 'relogio' | 'houston',
  tripulante_id?: string,
  signal?: AbortSignal,
) {
  return pedir<RespostaChatApi>('/cosmo/chat', { pergunta, superficie, tripulante_id: tripulante_id ?? null }, signal)
}

// ---------------------------------------------------------------- tradução
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

const NOME_SINAL: Record<string, string> = {
  fc: 'FC',
  hrv: 'HRV',
  spo2: 'SpO₂',
  temperatura: 'temperatura',
  respiracao: 'respiração',
  sono: 'sono',
  hidratacao: 'hidratação',
}

const FINAIS = ['resolvido', 'encerrado']

// Reserva para uma API sem os campos do passo 4 (sexo, corpo, saude_hormonal).
const SEXO: Record<string, 'f' | 'm'> = { sarah: 'f', elena: 'f', marcus: 'm', kenji: 'm' }

// Dose acumulada estimada por perfil de missão, a mesma da demo (1-demo-mvp).
const DOSE_MISSAO: Record<string, number> = { leo: 38, gateway: 96, mars: 212, marsSurf: 340 }

const NIVEL_FAIXA: Record<Faixa, NivelSaude> = { padrao: 0, atencao: 1, critico: 2 }

export function nivelDoEstado(estado: ApiTripulante['estado']): NivelSaude {
  return estado === 'critico' ? 2 : estado === 'atencao' || estado === 'suspeito' ? 1 : 0
}

const nivelDe = (m?: { faixa: Faixa }): NivelSaude => (m ? NIVEL_FAIXA[m.faixa] : 0)
const maior = (...n: NivelSaude[]) => Math.max(...n) as NivelSaude

function destaque(t: ApiTripulante): string | undefined {
  const fora = Object.entries(t.metricas).find(([, v]) => v.faixa !== 'padrao')
  if (!fora) return undefined
  const [sinal, m] = fora
  if (sinal === 'hidratacao') return `Água ${Math.round((t.agua_ml_dia / t.agua_meta) * 100)}%`
  return `${NOME_SINAL[sinal] ?? sinal} ${m.faixa === 'critico' ? 'crítico' : 'em atenção'}`
}

// Reserva: as mesmas regras de `corpo()` em 8-backend/app/nave/simulador.py.
function corpoLocal(t: ApiTripulante, faixas: Record<ChaveSinal, NivelSaude>): Record<Orgao, NivelSaude> {
  const fa = t.m1?.classe === 'fa'
  const agua = t.agua_ml_dia / t.agua_meta
  return {
    cerebro: maior(t.estresse >= 70 ? 2 : t.estresse >= 50 ? 1 : 0, nivelDe(t.metricas.sono)),
    coracao: fa ? 2 : maior(faixas.fc, faixas.hrv),
    pulmoes: maior(faixas.spo2, faixas.resp),
    rins: agua < 0.6 ? 2 : agua < 0.8 ? 1 : 0,
  }
}

export function paraTripulante(t: ApiTripulante, b: Pick<ApiBordo, 'missao' | 'avisos_compartilhados'>): Tripulante {
  const m = t.metricas
  const faixas: Record<ChaveSinal, NivelSaude> = {
    fc: nivelDe(m.fc),
    spo2: nivelDe(m.spo2),
    pa: 0, // a API não classifica a pressão; o manguito é medido de manhã
    resp: nivelDe(m.respiracao),
    hrv: nivelDe(m.hrv),
    agua: nivelDe(m.hidratacao),
  }
  const sexo = t.sexo ? (t.sexo === 'feminino' ? 'f' : 'm') : (SEXO[t.tripulante_id] ?? 'm')
  return {
    id: t.tripulante_id,
    nome: t.nome,
    cargo: t.papel,
    nivel: nivelDoEstado(t.estado),
    homeostase: t.homeostase,
    destaque: destaque(t),
    ritmo: t.m1?.classe === 'fa' ? 'fa' : 'normal',
    vitais: {
      fc: t.fc,
      spo2: t.spo2,
      paSis: t.pa_sys,
      paDia: t.pa_dia,
      resp: t.respiracao,
      hrv: t.hrv,
      agua: t.agua_ml_dia,
      aguaMeta: t.agua_meta,
    },
    faixas,
    sexo,
    corpo: t.corpo
      ? {
          cerebro: NIVEL_FAIXA[t.corpo.cerebro],
          coracao: NIVEL_FAIXA[t.corpo.coracao],
          pulmoes: NIVEL_FAIXA[t.corpo.pulmoes],
          rins: NIVEL_FAIXA[t.corpo.rins],
        }
      : corpoLocal(t, faixas),
    radiacao: { hojeMsv: t.dose_msv_dia, missaoMsv: DOSE_MISSAO[b.missao.missao] ?? 0 },
    hormonal: hormonal(t, sexo, b),
  }
}

// O servidor decide (ADR-013 e ADR-014): null quando o painel não pode saber de nada.
function hormonal(t: ApiTripulante, sexo: 'f' | 'm', b: Pick<ApiBordo, 'avisos_compartilhados'>): Tripulante['hormonal'] {
  if (t.saude_hormonal !== undefined) return t.saude_hormonal ?? undefined
  if (sexo !== 'f') return undefined
  // Reserva: o aviso do ciclo só chega em /api/bordo se ela autorizou.
  const compartilhou = b.avisos_compartilhados.some((e) => e.tipo === 'ciclo' && e.tripulante_id === t.tripulante_id)
  return compartilhou
    ? { compartilhado: true, resumo: 'pode ter cólica, inchaço ou humor mais baixo e pediu cuidado leve' }
    : { compartilhado: false }
}

export function paraStatus(m: ApiMissao): StatusNave {
  const terra = m.equipe.local === 'terra'
  return {
    houstonOnline: !m.blackout,
    atrasoHouston: m.atraso_txt,
    tripulantes: 4,
    co2: m.cabine.co2,
    titulo: terra ? 'Enfermaria · Marcus (CMO)' : 'Enfermaria · Dr. Marcus',
    subtitulo: terra
      ? `Sem médico a bordo · decisões médicas com a ${m.equipe.medico_nome}, em Houston`
      : 'Oficial médico da tripulação',
    extras: [
      terra ? { texto: `Médico na Terra · ${m.equipe.medico_nome}`, variante: 'warn' } : { texto: 'Médico a bordo', variante: 'ok' },
      ...(m.cabine.fluxo !== 'normal' ? [{ texto: `Prótons: fluxo ${m.cabine.fluxo}`, variante: 'warn' as const }] : []),
      ...(m.cabine.luz === 'noite' ? [{ texto: 'Modo noite', variante: 'normal' as const }] : []),
    ],
  }
}

function acao(e: ApiEvento, acao_api: string, rotulo: string, feito: string, detalhe?: Record<string, unknown>): Acao {
  return { chave: `${e.id}:${acao_api}`, rotulo, feito, evento_id: e.id, acao_api, detalhe }
}

const num = (v: unknown, casas = 0) =>
  typeof v === 'number' ? v.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas }) : '—'

// Um evento aberto vira o card de decisão. Os fluxos mais longos (medicação com PIN,
// médico na Terra, ordem permanente) mandam para o painel completo em bordo/.
export function paraDecisao(e: ApiEvento): Decisao {
  const titulo = `${TIPO[e.tipo] ?? e.tipo} · ${e.nome}`
  const meu = e.responsavel_id === EU
  const d = e.dados
  const prazo = e.prazo_restante_s != null ? ` Prazo: ${e.prazo_restante_s} s.` : ''
  const deOutro = meu ? '' : ` Quem decide agora: ${e.responsavel_nome}.`

  if (e.medico_local === 'terra' && (e.tipo === 'arritmia' || e.tipo === 'dor_de_cabeca'))
    return {
      titulo,
      texto: `Sem médico a bordo: a decisão médica é da ${e.medico_nome}, em Houston, e você inicia as ações seguras.${prazo}`,
      painelCompleto: true,
      urgente: e.tipo === 'arritmia',
    }

  switch (e.tipo) {
    case 'arritmia': {
      if (e.estado === 'aguardando_humano') {
        const conf = Math.round((e.sugestao?.confianca ?? 0) * 100)
        return {
          titulo,
          texto:
            `A Cosmo propõe o protocolo de FA · confiança ${conf}% (${e.sugestao?.versao_modelo ?? 'M1'}): repouso, ` +
            `O₂ 2 L/min, ECG de 12 derivações e desfibrilador de prontidão. Antiarrítmico só em passo separado.${prazo}${deOutro}`,
          acao: meu ? acao(e, 'confirmar', 'Confirmar protocolo', 'Protocolo confirmado') : undefined,
          urgente: true,
        }
      }
      return {
        titulo,
        texto: d.medicacao
          ? 'Protocolo em execução, com o antiarrítmico já liberado. A Cosmo acompanha até 10 leituras seguidas sem FA.'
          : 'Protocolo em execução. O antiarrítmico espera a sua liberação, com dose e PIN.',
        painelCompleto: !d.medicacao,
        urgente: true,
      }
    }
    case 'sensor_suspeito':
      if (e.estado === 'aguardando_humano')
        return {
          titulo,
          texto: `SpO₂ de ${num(d.spo2)}% no relógio com sinal de baixa qualidade. Sugestão da Cosmo: medir com o oxímetro de dedo do kit.${deOutro}`,
          acao: meu ? acao(e, 'registrar_kit', 'Registrar medição do kit: 97%', 'Medição registrada', { spo2_kit: 97 }) : undefined,
        }
      return { titulo, texto: `SpO₂ de ${num(d.spo2)}% com sinal suspeito. A Cosmo perguntou se o relógio está folgado. Ainda não é alarme.` }
    case 'dor_de_cabeca':
      return {
        titulo,
        texto: `A Cosmo cruzou a queixa com o ar da cabine: CO₂ em ${num(d.co2, 1)} mmHg na hora da queixa (alvo abaixo de 3). Hipótese principal: CO₂ elevado.${deOutro}`,
        acao: !meu
          ? undefined
          : !d.ar
            ? acao(e, 'pedir_ajuste_ar', 'Pedir ajuste do ar à Elena', 'Ajuste pedido')
            : !d.exame
              ? acao(e, 'aprovar_exame', 'Aprovar ultrassom guiado', 'Ultrassom aprovado')
              : undefined,
      }
    case 'bem_estar':
      return {
        titulo,
        texto: `${e.nome} autorizou só você a ver este resumo, sem gravações: ${String(d.padrao ?? '')}.`,
        acao:
          meu && e.estado === 'em_execucao'
            ? acao(e, 'marcar_conversa', 'Marcar conversa às 19:00', 'Conversa marcada', { hora: '19:00' })
            : undefined,
      }
    default:
      return { titulo, texto: `Situação: ${ESTADO_EVENTO[e.estado] ?? e.estado}. Responsável: ${e.responsavel_nome}.` }
  }
}

export function paraCard(tid: string, b: ApiBordo): CardDoTripulante {
  const t = b.tripulantes.find((x) => x.tripulante_id === tid)
  const nome = t?.nome ?? tid
  const meus = b.eventos.filter((e) => e.tripulante_id === tid)
  const abertos = meus.filter((e) => !FINAIS.includes(e.estado))
  const principal = abertos[0]

  const itens: string[] = []
  for (const e of meus) if (e !== principal) itens.push(`${TIPO[e.tipo] ?? e.tipo} · ${ESTADO_EVENTO[e.estado] ?? e.estado}`)
  for (const a of b.avisos_compartilhados.filter((x) => x.tripulante_id === tid))
    itens.push(
      a.tipo === 'ciclo'
        ? `${nome} compartilhou: pode ter cólica, inchaço ou humor mais baixo e pediu cuidado leve. Não é diagnóstico.`
        : `${nome} respondeu que não está bem: combinação fora do padrão, sem sinal crítico sozinho.`,
    )
  if (t)
    for (const [sinal, m] of Object.entries(t.metricas))
      if (m.faixa !== 'padrao')
        itens.push(`${NOME_SINAL[sinal] ?? sinal} ${m.faixa === 'critico' ? 'crítico' : 'em atenção'} (z ${num(m.z, 1)})`)
  if (!itens.length) itens.push(`Sinais de ${nome} no padrão da própria linha de base.`)

  return {
    decisao: principal ? paraDecisao(principal) : undefined,
    acompanhamento: { titulo: principal ? `Acompanhamento · ${nome}` : 'Nenhuma decisão pendente', itens },
  }
}
