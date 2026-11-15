// Relógio em Vue ligado à API: GET /api/tripulantes/{id}/relogio.
// O mostrador (RelogioPrototipo) recebe o estado da pessoa; o que espera uma resposta
// dela vira uma notificação com os mesmos botões do relógio atual (9-frontend/relogio).

import { onUnmounted, ref, shallowRef, watch, type Ref } from 'vue'
import type { NivelSaude } from '@/mocks/tripulacao'
import type { CicloNoRelogio, EstadoRelogio } from '@/mocks/relogio'
import { conexao, enviarDecisao, nivelDoEstado, pedir, type ApiEvento, type ApiTripulante, type Faixa } from './api'

export interface ApiRelogio {
  eu: Pick<
    ApiTripulante,
    'tripulante_id' | 'nome' | 'papel' | 'gerada_em' | 'estado' | 'homeostase' | 'qualidade' | 'fc' | 'spo2' | 'hrv'
    | 'agua_ml_dia' | 'agua_meta' | 'dose_msv_dia' | 'metricas' | 'sexo'
  > &
    Partial<Pick<ApiTripulante, 'temp_pele' | 'respiracao' | 'sono_min_noite' | 'estresse'>>
  contagem: { otimos: number; atencao: number; criticos: number }
  pendencias: ApiEvento[]
  acompanhando: ApiEvento[]
  emergencia: boolean
  ciclo: { na_janela: boolean; aviso_dias: number; privado: true } | null
  link: {
    missao: string
    rotulo: string
    blackout: boolean
    atraso_txt: string
    link?: string
    comprimido?: boolean
    volta_em?: string
    motivo_blackout?: string
    fila?: { prioridade: number; estado: string; falta_s?: number; rotulo?: string }[]
    fila_mb?: number
  }
  jogo?: {
    nivel: number
    pct: number
    xp: number
    missoes: { treino: boolean; agua: boolean; respiracao: boolean }
    corrida_km: number
    corrida_meta: number
    brinde: string | null
  } | null
  mensagens?: { texto: string; enviado_em: string; recebido_em: string }[]
  avisos?: { texto: string }[]
  equipe: { local: 'bordo' | 'terra'; medico_nome: string; marcus: { nome: string; papel: string } }
}

export const buscarRelogio = (tid: string) => pedir<ApiRelogio>(`/tripulantes/${encodeURIComponent(tid)}/relogio`)
export const beberAgua = (tid: string) => pedir('/habitos/agua', { tripulante_id: tid })
export const registrarRespiracao = (tid: string) => pedir('/habitos/respiracao', { tripulante_id: tid })
// Elo, sincronia e SOS: recado à família, incentivo, sincronizar o link, SOS prioritário.
export const enviarDoRelogio = (tid: string, tipo: string) => pedir('/relogio/enviar', { tripulante_id: tid, tipo })

// ---------------------------------------------------------------- mostrador
const MISSAO_CURTA: Record<string, string> = { leo: 'LEO', gateway: 'Gateway', mars: 'Marte', marsSurf: 'Marte' }
const NOME_SINAL: Record<string, [string, string, string]> = {
  // [nome, quando sobe, quando desce]
  fc: ['FC', 'alta', 'baixa'],
  spo2: ['SpO₂', 'alta', 'baixa'],
  hrv: ['HRV', 'alta', 'baixa'],
  temperatura: ['Pele', 'quente', 'fria'],
  respiracao: ['Respiração', 'rápida', 'lenta'],
  sono: ['Sono', 'longo', 'curto'],
  hidratacao: ['Água', 'alta', 'baixa'],
}

export function motivo(r: ApiRelogio): string {
  if (r.emergencia) return 'Alerta médico'
  if (r.eu.qualidade !== 'bom') return 'Sinal a confirmar'
  const fora = Object.entries(r.eu.metricas)
    .filter(([, m]) => m.faixa !== 'padrao')
    .sort(([, a], [, b]) => peso(b.faixa) - peso(a.faixa))
    .slice(0, 2)
    .map(([k, m]) => {
      const [n, sobe, desce] = NOME_SINAL[k] ?? [k, 'alto', 'baixo']
      return `${n} ${m.z >= 0 ? sobe : desce}`
    })
  return fora.length ? fora.join(' e ') : 'No seu padrão'
}
const peso = (f: Faixa) => (f === 'critico' ? 2 : f === 'atencao' ? 1 : 0)

export function paraMostrador(r: ApiRelogio): {
  nivel: NivelSaude
  estado: EstadoRelogio
  ciclo?: CicloNoRelogio
  missao: string
} {
  return {
    nivel: r.emergencia ? 2 : nivelDoEstado(r.eu.estado),
    estado: { fc: r.eu.fc, spo2: r.eu.spo2, homeostase: r.eu.homeostase, motivo: motivo(r) },
    // ADR-013: só o trecho do calendário, sem método nem fase, e só quando ele chega.
    ciclo: r.ciclo?.na_janela ? { aviso: r.ciclo.aviso_dias ? `${r.ciclo.aviso_dias}d` : 'hoje' } : undefined,
    missao: MISSAO_CURTA[r.link.missao] ?? r.link.missao,
  }
}

// ---------------------------------------------------------------- notificações
export type BotaoRelogio =
  | { rotulo: string; variante?: string; tipo: 'decidir'; acao: string }
  | { rotulo: string; variante?: string; tipo: 'respirar' | 'agua' }

export interface Notificacao {
  id: string
  etiqueta: string
  variante: '' | 'ok' | 'warn' | 'crit' | 'roxo' | 'agua'
  titulo?: string
  texto: string
  nota?: string
  botoes: BotaoRelogio[]
}

const n0 = (v: unknown, casas = 0) =>
  typeof v === 'number' ? v.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas }) : '—'
const prazo = (e: ApiEvento) => (e.prazo_restante_s == null ? '' : ` · ${e.prazo_restante_s} s`)
const dec = (rotulo: string, acao: string, variante = ''): BotaoRelogio => ({ rotulo, acao, variante, tipo: 'decidir' })
const SINAL_CURTO: Record<string, string> = { fc: 'FC', hrv: 'HRV', spo2: 'SpO₂', temperatura: 'temperatura', respiracao: 'respiração', sono: 'sono', hidratacao: 'hidratação' }

// Mesma lógica de `pendencia()` e `evento()` em 9-frontend/relogio/app.js.
export function notificacao(r: ApiRelogio): Notificacao | null {
  const marcus = r.equipe.marcus.nome
  // O alerta médico da própria pessoa vem antes de qualquer outra pendência
  // (uma pergunta do ciclo em aberto não pode esconder a FA).
  const pendArritmia = r.pendencias.find((x) => x.tipo === 'arritmia')
  const minhaArritmia = r.acompanhando.find((x) => x.tipo === 'arritmia')
  const e = pendArritmia ?? (minhaArritmia ? undefined : r.pendencias[0])
  if (!e) {
    const a = minhaArritmia
    if (!a) return null
    const terra = a.medico_local === 'terra'
    const seguras = a.dados.seguras as { por?: string } | undefined
    const fase = terra
      ? a.estado === 'em_execucao'
        ? `A ${a.medico_nome} confirmou de Houston · O₂ 2 L/min`
        : seguras
          ? `${marcus} com você · O₂ 2 L/min. Médica na Terra decidindo.`
          : `Médica na Terra avisada. ${marcus} vem ajudar.`
      : a.estado === 'em_execucao'
        ? `${marcus} a caminho · O₂ 2 L/min`
        : 'Oficial médico avisado. Respire devagar.'
    return {
      id: a.id,
      etiqueta: 'Alerta médico',
      variante: 'crit',
      titulo: 'Pare e sente-se',
      texto: `${n0(r.eu.fc)} bpm · SpO₂ ${n0(r.eu.spo2)}%. ${fase}`,
      nota: 'Dizer "estou bem" não cancela este alerta: quem avalia é o médico.',
      botoes: [],
    }
  }

  const d = e.dados
  const contar = e.medico_local === 'terra' ? `Contar só à ${e.medico_nome}` : `Contar ao ${marcus}`
  const base = { id: e.id }
  switch (e.tipo) {
    case 'sensor_suspeito':
      if (e.estado === 'confirmacao_astronauta')
        return {
          ...base,
          etiqueta: `Leitura estranha${prazo(e)}`,
          variante: 'warn',
          titulo: `SpO₂ ${n0(d.spo2)}%?`,
          texto: `O sinal está fraco (${String(d.motivo ?? 'baixa qualidade')}). Antes de avisar o médico: seu relógio está folgado?`,
          botoes: [dec('Ajustei o relógio', 'ajustar_sensor', 'principal'), dec('Está firme', 'sensor_firme')],
        }
      return { ...base, etiqueta: 'Leitura suspeita', variante: 'warn', texto: 'Aguardando a medição com o oxímetro do kit, no painel de bordo.', botoes: [] }
    case 'tempestade_solar':
      if (e.estado === 'aguardando_humano')
        return {
          ...base,
          etiqueta: `Tempestade solar${prazo(e)}`,
          variante: 'warn',
          titulo: 'Fluxo de prótons subindo',
          texto: 'A rota até o abrigo já está acesa (ação reversível). Levar a tripulação agora?',
          nota: d.adiado ? 'Aguardando. Pergunto de novo em instantes.' : undefined,
          botoes: d.adiado ? [] : [dec('Abrigo para todos', 'confirmar', 'warn'), dec('Aguardar', 'adiar')],
        }
      if (d.fase === 'fluxo_caindo')
        return {
          ...base,
          etiqueta: 'Fluxo caindo',
          variante: 'ok',
          titulo: 'Liberar a tripulação?',
          texto: `Sua dose hoje: ${n0(r.eu.dose_msv_dia, 2)} mSv`,
          botoes: [dec('Liberar do abrigo', 'liberar_abrigo', 'principal')],
        }
      return { ...base, etiqueta: 'No abrigo', variante: 'warn', texto: `Dose hoje: ${n0(r.eu.dose_msv_dia, 2)} mSv. Tripulação protegida; eu aviso quando for seguro sair.`, botoes: [] }
    case 'prontidao_eva': {
      const p = (d.prontidao ?? {}) as Record<string, number>
      return {
        ...base,
        etiqueta: `Escala · ${String(d.tarefa ?? 'EVA')}`,
        variante: '',
        texto: `Prontidão da Elena: ${p.elena ?? '—'}% (sono curto, reação mais lenta). Kenji: ${p.kenji ?? '—'}%.`,
        nota: 'A Cosmo não tira ninguém da escala. A decisão é sua.',
        botoes: [dec('Trocar pelo Kenji', 'trocar_escala', 'principal'), dec('Manter a Elena', 'manter_escala')],
      }
    }
    case 'bem_estar':
      return {
        ...base,
        etiqueta: 'Só você vê isto',
        variante: 'roxo',
        texto: `Notei ${String(d.padrao ?? 'uma mudança no seu padrão')}. Quer conversar?`,
        botoes: [{ rotulo: 'Respirar 1 min', tipo: 'respirar' }, dec(contar, 'compartilhar'), dec('Só comigo', 'manter_privado')],
      }
    case 'ciclo':
      if (d.sintoma !== true)
        return {
          ...base,
          etiqueta: 'Só você vê isto',
          variante: 'roxo',
          texto: `${d.aviso_dias ? `Em ${d.aviso_dias} dia(s)` : 'Neste trecho'}: cólica, inchaço ou humor mais baixo. Você está sentindo?`,
          botoes: [dec('Estou sentindo', 'confirmar_sintoma', 'principal'), dec('Estou bem', 'falso_alarme')],
        }
      return {
        ...base,
        etiqueta: 'Só você vê isto',
        variante: 'roxo',
        texto:
          e.medico_local === 'terra'
            ? `Sem médico a bordo: se contar, só a ${e.medico_nome}, em Houston, vê esses sintomas e o pedido de cuidado leve. O CMO e a família não veem.`
            : `Se contar ao ${marcus}, ele vê só isto: esses sintomas e o pedido de cuidado leve. Sem alarme. A família não vê.`,
        botoes: [{ rotulo: 'Respirar 1 min', tipo: 'respirar' }, dec(contar, 'compartilhar'), dec('Só comigo', 'manter_privado')],
      }
    case 'linha_de_base': {
      const ev = e.sugestao?.evidencias ?? []
      return {
        ...base,
        etiqueta: 'Fora do seu padrão · nível 1',
        variante: '',
        texto: `A combinação dos seus sinais saiu do seu padrão${ev.length ? ` (${ev.map((k) => SINAL_CURTO[k] ?? k).join(', ')})` : ''}. Nenhum sinal está crítico sozinho. Como você está?`,
        nota: 'Sua resposta vira rótulo para o próximo treino do modelo.',
        botoes: [dec('É o meu normal hoje', 'falso_alarme', 'principal'), dec('Não estou bem', 'confirmar_sintoma')],
      }
    }
    case 'hidratacao':
      return {
        ...base,
        etiqueta: 'Hidratação',
        variante: 'agua',
        texto: `Faltam ${n0(r.eu.agua_meta - r.eu.agua_ml_dia)} ml para a meta de hoje. Beber 250 ml agora?`,
        botoes: [dec('+250 ml', 'aceitar_cuidado', 'agua'), dec('Agora não', 'dispensar')],
      }
    case 'modo_noite':
      if (e.estado === 'agendado')
        return {
          ...base,
          etiqueta: `Modo noite${prazo(e)}`,
          variante: 'roxo',
          texto: 'Vou deixar a luz mais quente e silenciar avisos. É reversível: você pode vetar.',
          botoes: [dec('Vetar', 'vetar')],
        }
      return { ...base, etiqueta: 'Modo noite ativo', variante: 'ok', texto: 'Luz em 2700 K e avisos silenciados. Emergências continuam passando.', botoes: [dec('Desfazer', 'desfazer')] }
    case 'arritmia':
      if (e.medico_local === 'terra')
        return {
          ...base,
          etiqueta: `${e.nome} precisa de você${prazo(e)}`,
          variante: 'crit',
          texto: 'Sem médico a bordo: inicie as ações seguras (repouso, O₂ 2 L/min, ECG de 12 derivações).',
          nota: `Protocolo e medicação: só com a ${e.medico_nome}, em Houston.`,
          botoes: [dec('Iniciar ações seguras', 'iniciar_seguras', 'crit')],
        }
      return {
        ...base,
        etiqueta: `${e.nome} precisa de você${prazo(e)}`,
        variante: 'crit',
        texto: 'O protocolo da Cosmo aguarda um humano.',
        nota: 'Medicação continua só com o oficial médico.',
        botoes: [dec('Confirmar protocolo', 'confirmar', 'crit'), dec('Assumir manualmente', 'assumir')],
      }
    default:
      return { ...base, etiqueta: e.tipo, variante: '', texto: 'Decida no painel de bordo.', botoes: [] }
  }
}

// ---------------------------------------------------------------- estado da tela
export function usarRelogio(quem: Ref<string>, intervaloMs = 1000) {
  const dados = shallowRef<ApiRelogio | null>(null)
  const erro = ref<string | null>(null)
  let emCurso = false

  async function carregar() {
    if (emCurso) return
    emCurso = true
    const tid = quem.value
    try {
      const r = await buscarRelogio(tid)
      if (tid === quem.value) dados.value = r
      conexao.value = 'api'
    } catch {
      dados.value = null
      conexao.value = 'offline'
    } finally {
      emCurso = false
    }
  }

  async function executar(f: () => Promise<unknown>) {
    try {
      erro.value = null
      await f()
    } catch (e) {
      erro.value = (e as Error).message
    } finally {
      await carregar()
    }
  }

  const decidir = (evento_id: string, acao: string) => executar(() => enviarDecisao(evento_id, acao, undefined, quem.value))
  const beber = () => executar(() => beberAgua(quem.value))
  const enviar = (tipo: string) => executar(() => enviarDoRelogio(quem.value, tipo))
  const respirou = () => executar(() => registrarRespiracao(quem.value))

  watch(quem, () => {
    dados.value = null
    carregar()
  })
  carregar()
  const id = setInterval(carregar, intervaloMs)
  onUnmounted(() => clearInterval(id))

  return { dados, erro, conexao, carregar, decidir, beber, respirou, enviar }
}
