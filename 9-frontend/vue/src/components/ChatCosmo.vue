<script setup lang="ts">
// Só conversa, sem botão de ação (ADR-002). Com a API no ar, as perguntas sugeridas
// vêm de /api/cosmo/perguntas (o grupo "Agora" segue o cenário em curso) e cada
// resposta mostra a fonte, o que a Cosmo vê nesta superfície e a trilha.
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { Eraser, Orbit, SendHorizontal, ShieldCheck } from 'lucide-vue-next'
import StatusChip from './StatusChip.vue'
import { perguntarCosmo, type Fonte } from '@/servicos/cosmo'
import { buscarPerguntas, conexao, type GrupoPerguntas } from '@/servicos/api'
import { rodapeTrilha, type RegistroTrilha } from '@/servicos/trilha'
import type { Tripulante } from '@/mocks/tripulacao'

const props = withDefaults(
  defineProps<{
    tripulante: Tripulante
    superficie?: 'bordo' | 'houston'
    titulo?: string
    saudacao?: string
  }>(),
  {
    superficie: 'bordo',
    titulo: 'Cosmo · copiloto médico',
    saudacao:
      'Bom dia, Dr. Marcus. Estou rodando no computador da nave, sem depender da Terra. ' +
      'Pergunte sobre qualquer tripulante, um evento, o link ou os modelos.',
  },
)

interface Mensagem {
  autor: 'cosmo' | 'eu'
  texto: string
  fontes?: Fonte[]
  erro?: boolean
  modo?: string
  visao?: string
  trilha?: RegistroTrilha
}

const inicial = (): Mensagem[] => [{ autor: 'cosmo', texto: props.saudacao }]
const mensagens = ref<Mensagem[]>(inicial())
const texto = ref('')
const digitando = ref(false)
const lista = ref<HTMLElement | null>(null)
let controle: AbortController | null = null

// Sugestões: da API quando ela está no ar; senão, os atalhos do protótipo.
const grupos = ref<GrupoPerguntas[]>([])
const grupoAtivo = ref<string | null>(null)
let escolhido = false // quem escolheu outro grupo não é puxado de volta para "Agora"
async function carregarSugestoes() {
  if (conexao.value !== 'api') {
    grupos.value = []
    return
  }
  try {
    grupos.value = await buscarPerguntas(props.superficie, props.tripulante.id)
    const nomes = grupos.value.map((g) => g.grupo)
    if (nomes.includes('Agora') && !escolhido) grupoAtivo.value = 'Agora'
    if (!grupoAtivo.value || !nomes.includes(grupoAtivo.value)) grupoAtivo.value = nomes[0] ?? null
  } catch {
    grupos.value = []
  }
}
function escolherGrupo(g: string) {
  grupoAtivo.value = g
  escolhido = g !== 'Agora'
}
watch(() => [props.tripulante.id, conexao.value], carregarSugestoes, { immediate: true })
const idSugestoes = setInterval(carregarSugestoes, 3000)

const atalhos = computed(() => {
  if (grupos.value.length) return grupos.value.find((g) => g.grupo === grupoAtivo.value)?.perguntas ?? []
  const t = props.tripulante
  const a = ['Quem precisa de atenção hoje?', `Resumo: ${t.nome}`, 'Situação do kit médico']
  if (t.hormonal) a.push(`Saúde hormonal: ${t.nome}`)
  return a
})

async function rolarParaOFim() {
  await nextTick()
  lista.value?.scrollTo({ top: lista.value.scrollHeight })
}

async function enviar(pergunta: string) {
  pergunta = pergunta.trim()
  if (!pergunta || digitando.value) return

  mensagens.value.push({ autor: 'eu', texto: pergunta })
  texto.value = ''
  digitando.value = true
  rolarParaOFim()

  controle = new AbortController()
  try {
    const r = await perguntarCosmo(
      {
        origem: props.superficie === 'bordo' ? 'painel' : 'houston',
        tripulante_id: props.tripulante.id,
        mensagem: pergunta,
      },
      { signal: controle.signal },
    )
    mensagens.value.push({ autor: 'cosmo', texto: r.resposta, fontes: r.fontes, modo: r.modo, visao: r.visao, trilha: r.trilha })
  } catch (e) {
    if ((e as Error).name === 'AbortError') return
    mensagens.value.push({
      autor: 'cosmo',
      texto: 'Não consegui responder agora. Tente de novo em instantes.',
      erro: true,
    })
  } finally {
    digitando.value = false
    controle = null
    rolarParaOFim()
    carregarSugestoes()
  }
}

function limpar() {
  mensagens.value = inicial()
}

onUnmounted(() => {
  controle?.abort()
  clearInterval(idSugestoes)
})
</script>

<template>
  <aside class="chat" aria-label="Chat com a Cosmo">
    <div class="interno">
      <header class="topo">
        <h2 class="titulo"><Orbit :size="15" aria-hidden="true" /> {{ titulo }}</h2>
        <StatusChip variante="ok">IA local</StatusChip>
      </header>

      <div ref="lista" class="mensagens" role="log" aria-live="polite">
        <div v-for="(m, i) in mensagens" :key="i" class="mensagem" :class="[m.autor, { erro: m.erro }]">
          {{ m.texto }}
          <ul v-if="m.fontes?.length || m.modo || m.trilha" class="fontes">
            <li v-for="f in m.fontes ?? []" :key="f.titulo">
              Fonte: {{ f.titulo }}<template v-if="f.trecho"> · {{ f.trecho }}</template>
            </li>
            <li v-if="m.modo">{{ m.modo }}<template v-if="m.visao"> · vê {{ m.visao }}</template></li>
            <li v-if="m.trilha" title="Trilha da Cosmo">{{ rodapeTrilha(m.trilha) }}</li>
          </ul>
        </div>
        <div v-if="digitando" class="digitando">Cosmo está digitando…</div>
      </div>

      <footer class="rodape">
        <div v-if="grupos.length > 1" class="grupos" role="group" aria-label="Grupos de perguntas">
          <button
            v-for="g in grupos"
            :key="g.grupo"
            type="button"
            :class="{ agora: g.grupo === 'Agora' }"
            :aria-pressed="g.grupo === grupoAtivo"
            @click="escolherGrupo(g.grupo)"
          >
            {{ g.grupo }}<template v-if="g.grupo === 'Agora'"> · cenário em curso</template>
          </button>
        </div>
        <div class="atalhos">
          <button v-for="a in atalhos" :key="a" type="button" :disabled="digitando" @click="enviar(a)">
            {{ a }}
          </button>
        </div>
        <form class="campo" @submit.prevent="enviar(texto)">
          <input
            v-model="texto"
            type="text"
            maxlength="300"
            autocomplete="off"
            placeholder="Pergunte sobre a tripulação…"
            aria-label="Mensagem para a Cosmo"
          />
          <button type="submit" class="enviar" :disabled="digitando || !texto.trim()" aria-label="Enviar">
            <SendHorizontal :size="16" aria-hidden="true" />
          </button>
          <button type="button" class="limpar" title="Limpar a conversa" aria-label="Limpar a conversa" @click="limpar">
            <Eraser :size="15" aria-hidden="true" />
          </button>
        </form>
        <p class="aviso">
          <ShieldCheck :size="12" aria-hidden="true" />
          {{
            superficie === 'houston'
              ? 'A Cosmo Terra só sabe o que já chegou pelo link. Ela explica; quem decide é você.'
              : 'A Cosmo sugere e cita o protocolo; quem decide é você.'
          }}
        </p>
      </footer>
    </div>
  </aside>
</template>

<style scoped>
.chat {
  position: relative;
  min-width: 0;
  border-left: 1px solid var(--linha);
}
.interno {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
}

.topo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--linha);
}
.titulo {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}
.titulo svg {
  color: var(--acento);
}

.mensagens {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  overflow-y: auto;
}
.mensagem {
  max-width: 90%;
  padding: 9px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.mensagem.cosmo {
  align-self: flex-start;
  border: 1px solid rgba(0, 229, 255, 0.25);
  border-bottom-left-radius: 4px;
  background: linear-gradient(140deg, rgba(0, 229, 255, 0.08), var(--superficie) 70%);
}
.mensagem.eu {
  align-self: flex-end;
  border: 1px solid var(--linha-forte);
  border-bottom-right-radius: 4px;
  background: #1d2a47;
}
.mensagem.erro {
  border-color: rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.08);
}
.fontes {
  margin: 6px 0 0;
  padding: 0;
  list-style: none;
  font-size: 11px;
  color: var(--texto-fraco);
}
.digitando {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: var(--texto-fraco);
}

.rodape {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--linha);
}
.atalhos {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.atalhos button {
  padding: 5px 10px;
  border-radius: 99px;
  border: 1px solid var(--linha-forte);
  background: #1d2a47;
  color: var(--texto);
  font: inherit;
  font-size: 11.5px;
  cursor: pointer;
}
.atalhos button:hover:not(:disabled) {
  border-color: var(--acento);
}
.campo {
  display: flex;
  gap: 6px;
}
.campo input {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--linha-forte);
  background: var(--superficie);
  color: var(--texto);
  font: inherit;
  font-size: 13px;
}
.campo input::placeholder {
  color: var(--texto-fraco);
}
.campo input:focus-visible {
  outline: none;
  border-color: var(--acento);
}
.enviar {
  display: grid;
  place-items: center;
  width: 40px;
  border: 0;
  border-radius: 10px;
  background: var(--acento);
  color: #03141a;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: default;
}
button:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
.aviso {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  font-size: 11px;
  color: var(--texto-fraco);
}
.grupos {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.grupos button {
  padding: 3px 9px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--texto-fraco);
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.grupos button[aria-pressed='true'] {
  color: var(--texto);
  border-color: var(--linha-forte);
  background: var(--superficie);
}
.grupos button.agora {
  color: var(--acento);
}
.limpar {
  display: grid;
  place-items: center;
  width: 40px;
  border-radius: 10px;
  border: 1px solid var(--linha-forte);
  background: transparent;
  color: var(--texto-fraco);
  cursor: pointer;
}
.grupos {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.grupos button {
  padding: 3px 9px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--texto-fraco);
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.grupos button[aria-pressed='true'] {
  color: var(--texto);
  border-color: var(--linha-forte);
  background: var(--superficie);
}
.grupos button.agora {
  color: var(--acento);
}
.limpar {
  display: grid;
  place-items: center;
  width: 40px;
  border-radius: 10px;
  border: 1px solid var(--linha-forte);
  background: transparent;
  color: var(--texto-fraco);
  cursor: pointer;
}
</style>

