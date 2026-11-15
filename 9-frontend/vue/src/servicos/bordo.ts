// Estado do painel de bordo: lê GET /api/bordo a cada segundo, como as telas atuais.
// Se a API não responder, a tela continua de pé com os mocks e avisa "modo offline".

import { onUnmounted, ref, shallowRef } from 'vue'
import { tripulacaoMock, type Tripulante } from '@/mocks/tripulacao'
import { statusNaveMock, type StatusNave } from '@/mocks/nave'
import type { Acao } from '@/mocks/decisoes'
import { buscarBordo, conexao, decidirEvento, enviarDecisao, paraStatus, paraTripulante, type ApiBordo } from './api'

export function usarBordo(intervaloMs = 1000) {
  const tripulantes = ref<Tripulante[]>(tripulacaoMock)
  const status = ref<StatusNave>(statusNaveMock)
  const bordo = shallowRef<ApiBordo | null>(null)
  const erro = ref<string | null>(null)
  let emCurso = false

  async function carregar() {
    if (emCurso) return
    emCurso = true
    try {
      const b = await buscarBordo()
      bordo.value = b
      tripulantes.value = b.tripulantes.map((t) => paraTripulante(t, b))
      status.value = paraStatus(b.missao)
      conexao.value = 'api'
    } catch {
      bordo.value = null
      tripulantes.value = tripulacaoMock
      status.value = statusNaveMock
      conexao.value = 'offline'
    } finally {
      emCurso = false
    }
  }

  // Devolve true quando a decisão foi para a API; false quando é do modo offline.
  async function decidir(acao: Acao): Promise<boolean> {
    if (!acao.evento_id || !acao.acao_api || conexao.value !== 'api') return false
    try {
      erro.value = null
      await enviarDecisao(acao.evento_id, acao.acao_api, acao.detalhe)
    } catch (e) {
      erro.value = (e as Error).message
      throw e
    } finally {
      await carregar()
    }
    return true
  }

  // Decisão completa (dose, PIN, detalhe), usada pelos cartões de evento.
  async function decidirCorpo(corpo: Parameters<typeof decidirEvento>[0]) {
    try {
      erro.value = null
      await decidirEvento(corpo)
    } catch (e) {
      erro.value = (e as Error).message
    } finally {
      await carregar()
    }
  }

  carregar()
  const id = setInterval(carregar, intervaloMs)
  onUnmounted(() => clearInterval(id))

  return { tripulantes, status, bordo, erro, conexao, carregar, decidir, decidirCorpo }
}
