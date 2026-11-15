// Lê uma rota da API a cada `ms`, como o `repetir()` das telas em JS puro.
// Sem resposta, marca a conexão como offline e tenta de novo no próximo ciclo.

import { onUnmounted, ref, shallowRef, watch } from 'vue'
import { conexao, pedir } from './api'

export function usarConsulta<T>(caminho: () => string | null, ms = 1000) {
  const dados = shallowRef<T | null>(null)
  const erro = ref<string | null>(null)
  let emCurso = false

  async function carregar() {
    const c = caminho()
    if (!c || emCurso) return
    emCurso = true
    try {
      const r = await pedir<T>(c)
      if (c === caminho()) dados.value = r
      conexao.value = 'api'
    } catch {
      conexao.value = 'offline'
    } finally {
      emCurso = false
    }
  }

  // Ações (POST) passam por aqui: o erro vira aviso na tela e os dados recarregam.
  async function executar<R>(f: () => Promise<R>): Promise<R | undefined> {
    try {
      erro.value = null
      return await f()
    } catch (e) {
      erro.value = (e as Error).message
      return undefined
    } finally {
      await carregar()
    }
  }

  watch(caminho, () => carregar())
  carregar()
  const id = setInterval(carregar, ms)
  onUnmounted(() => clearInterval(id))
  return { dados, erro, carregar, executar }
}
