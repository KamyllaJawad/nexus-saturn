<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RelogioPrototipo from '../components/RelogioPrototipo.vue'
import { tripulacaoMock, type NivelSaude } from '@/mocks/tripulacao'
import { CICLO_NO_RELOGIO, PREVIA_ESTADO } from '@/mocks/relogio'
import { notificacao, paraMostrador, usarRelogio, type BotaoRelogio } from '@/servicos/relogio'

const tripulacao = tripulacaoMock
const route = useRoute()
const router = useRouter()

// ?quem=kenji abre o pulso de outra pessoa, como no relógio atual (um pulso por aba).
const quem = computed({
  get: () => {
    const q = String(route.query.quem ?? 'sarah')
    return tripulacao.some((t) => t.id === q) ? q : 'sarah'
  },
  set: (id: string) => {
    router.replace({ query: { ...route.query, quem: id } })
  },
})
const { dados, erro, conexao, decidir, beber, respirou } = usarRelogio(quem)

const tripulante = computed(() => tripulacao.find((t) => t.id === quem.value) ?? tripulacao[0]!)
const nome = computed(() => dados.value?.eu.nome ?? tripulante.value.nome)

// Offline: a prévia dos três estados, com os dados de exemplo.
const nivelPrevia = ref<NivelSaude>(0)
const mostrador = computed(() =>
  dados.value
    ? { ...paraMostrador(dados.value), sexo: dados.value.eu.sexo === 'feminino' ? ('f' as const) : dados.value.eu.sexo === 'masculino' ? ('m' as const) : tripulante.value.sexo }
    : {
        nivel: nivelPrevia.value,
        estado: PREVIA_ESTADO[nivelPrevia.value],
        ciclo: CICLO_NO_RELOGIO[tripulante.value.id],
        missao: 'LEO',
        sexo: tripulante.value.sexo,
      },
)
const aviso = computed(() => (dados.value ? notificacao(dados.value) : null))

// Respiração guiada: 10 s na demo, como no relógio atual; no fim, conta para a missão do dia.
const respirando = ref(0)
let idRespira = 0
function respirar() {
  respirando.value = 10
  window.clearInterval(idRespira)
  idRespira = window.setInterval(() => {
    if (--respirando.value > 0) return
    window.clearInterval(idRespira)
    if (dados.value) respirou()
  }, 1000)
}
onUnmounted(() => window.clearInterval(idRespira))

function tocar(b: BotaoRelogio) {
  if (b.tipo === 'respirar') return respirar()
  if (b.tipo === 'agua') return beber()
  if (b.tipo === 'decidir' && aviso.value) return decidir(aviso.value.id, b.acao)
}

const NIVEIS: { valor: NivelSaude; nome: string }[] = [
  { valor: 0, nome: 'Ótimo' },
  { valor: 1, nome: 'Atenção' },
  { valor: 2, nome: 'Crítico' },
]
</script>

<template>
  <main class="pagina">
    <header>
      <p class="etiqueta"><span>A bordo</span> Relógio circular · 45 mm</p>
      <h1>Relógio de {{ nome }}</h1>
      <p v-if="conexao === 'offline'" class="offline" role="status">
        Modo offline: prévia com dados de exemplo. Suba o 8-backend e o relógio volta sozinho.
      </p>
    </header>

    <RelogioPrototipo
      :nivel="mostrador.nivel"
      :sexo="mostrador.sexo"
      :estado="mostrador.estado"
      :ciclo="mostrador.ciclo"
      :missao="mostrador.missao"
    />

    <section v-if="respirando" class="cartao" aria-live="polite">
      <p class="etiqueta-cartao">Respiração guiada</p>
      <p class="texto">Inspire 4 s · solte 6 s. <b>{{ respirando }}</b> s restantes.</p>
      <div class="botoes"><button type="button" @click="respirando = 0">Parar</button></div>
    </section>

    <section v-else-if="aviso" class="cartao" :class="aviso.variante" role="alert">
      <p class="etiqueta-cartao">{{ aviso.etiqueta }}</p>
      <p v-if="aviso.titulo" class="titulo">{{ aviso.titulo }}</p>
      <p class="texto">{{ aviso.texto }}</p>
      <div v-if="aviso.botoes.length" class="botoes">
        <button v-for="b in aviso.botoes" :key="b.rotulo" type="button" :class="b.variante" @click="tocar(b)">
          {{ b.rotulo }}
        </button>
      </div>
      <p v-if="aviso.nota" class="nota">{{ aviso.nota }}</p>
    </section>

    <p v-if="erro" class="erro" role="alert">{{ erro }}</p>

    <section class="controles" aria-label="Controles do relógio">
      <div class="grupo" role="group" aria-label="Tripulante">
        <button
          v-for="t in tripulacao"
          :key="t.id"
          type="button"
          :aria-pressed="t.id === quem"
          @click="quem = t.id"
        >
          {{ t.nome }}
        </button>
      </div>
      <div v-if="dados && !dados.emergencia" class="grupo" role="group" aria-label="Cuidados">
        <button type="button" @click="beber()">+250 ml</button>
        <button type="button" @click="respirar()">Respirar 1 min</button>
        <a :href="`/relogio/?quem=${quem}`" target="_top">Cosmo, estufa e Elo</a>
      </div>
      <div v-else-if="!dados" class="grupo" role="group" aria-label="Estado da prévia">
        <button
          v-for="n in NIVEIS"
          :key="n.valor"
          type="button"
          :class="`n${n.valor}`"
          :aria-pressed="n.valor === nivelPrevia"
          @click="nivelPrevia = n.valor"
        >
          {{ n.nome }}
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.pagina {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  min-height: 100vh;
  padding: 32px 16px;
}

header {
  text-align: center;
}
.etiqueta {
  margin: 0 0 6px;
  font-family: ui-monospace, monospace;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--texto-fraco);
}
.etiqueta span {
  margin-right: 6px;
  padding: 2px 7px;
  border-radius: 99px;
  border: 1px solid rgba(0, 229, 255, 0.4);
  color: var(--acento);
}
h1 {
  margin: 0;
  font-size: 20px;
}
.offline {
  margin: 8px 0 0;
  font-size: 12.5px;
  color: var(--warn);
}
.erro {
  margin: 0;
  font-size: 12.5px;
  color: #fecaca;
}

/* Notificação no pulso: o que espera uma resposta desta pessoa */
.cartao {
  width: min(360px, 100%);
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid var(--linha-forte);
  background: var(--superficie);
}
.cartao.warn {
  border-color: rgba(245, 158, 11, 0.5);
}
.cartao.crit {
  border-color: rgba(239, 68, 68, 0.6);
  background: linear-gradient(140deg, rgba(239, 68, 68, 0.12), var(--superficie) 70%);
}
.cartao.roxo {
  border-color: rgba(139, 92, 246, 0.5);
}
.cartao.ok {
  border-color: rgba(16, 185, 129, 0.5);
}
.cartao.agua {
  border-color: rgba(59, 130, 246, 0.5);
}
.etiqueta-cartao {
  margin: 0;
  font-family: ui-monospace, monospace;
  font-size: 10.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--texto-fraco);
}
.warn .etiqueta-cartao {
  color: var(--warn);
}
.crit .etiqueta-cartao {
  color: var(--crit);
}
.roxo .etiqueta-cartao {
  color: #c4b5fd;
}
.ok .etiqueta-cartao {
  color: var(--ok);
}
.agua .etiqueta-cartao {
  color: var(--agua);
}
.titulo {
  margin: 6px 0 0;
  font-size: 17px;
  font-weight: 600;
}
.texto {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.5;
}
.nota {
  margin: 8px 0 0;
  font-size: 11.5px;
  color: var(--texto-fraco);
}
.botoes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.botoes button {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--linha-forte);
  background: transparent;
  color: var(--texto);
  font: inherit;
  font-size: 12.5px;
  cursor: pointer;
}
.botoes button:hover {
  border-color: var(--acento);
}
.botoes .principal {
  background: var(--acento);
  color: #03141a;
  border-color: transparent;
  font-weight: 600;
}
.botoes .crit {
  background: var(--crit);
  color: #fff;
  border-color: transparent;
  font-weight: 600;
}
.botoes .warn {
  background: var(--warn);
  color: #1a1200;
  border-color: transparent;
  font-weight: 600;
}
.botoes .agua {
  background: var(--agua);
  color: #fff;
  border-color: transparent;
}

.controles {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.grupo {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
  padding: 4px;
  border-radius: 12px;
  border: 1px solid var(--linha);
  background: rgba(255, 255, 255, 0.02);
}
.grupo button,
.grupo a {
  padding: 7px 14px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: var(--texto-fraco);
  font: inherit;
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
}
.grupo button:hover,
.grupo a:hover {
  color: var(--texto);
}
.grupo button[aria-pressed='true'] {
  background: var(--superficie);
  color: var(--texto);
  box-shadow: inset 0 0 0 1px var(--linha-forte);
}
.grupo button.n0[aria-pressed='true'] {
  color: var(--ok);
}
.grupo button.n1[aria-pressed='true'] {
  color: var(--warn);
}
.grupo button.n2[aria-pressed='true'] {
  color: var(--crit);
}
.grupo button:focus-visible,
.grupo a:focus-visible,
.botoes button:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
</style>
