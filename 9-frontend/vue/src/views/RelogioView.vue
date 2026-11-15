<script setup lang="ts">
// Relógio de pulso, no formato da demo (1-demo-mvp): tudo acontece dentro do
// mostrador (início, dica, sinais, Cosmo, estufa, Elo, sincronia, evento e
// respiração), com a coroa e os pontos para trocar de tela. Fora do relógio
// ficam só a escolha da tripulante e os gatilhos de evento.
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RelogioPrototipo from '../components/RelogioPrototipo.vue'
import { tripulacaoMock, type NivelSaude } from '@/mocks/tripulacao'
import { CICLO_NO_RELOGIO, PREVIA_ESTADO } from '@/mocks/relogio'
import { notificacao, paraMostrador, usarRelogio, type BotaoRelogio } from '@/servicos/relogio'
import { pedir, perguntarApi } from '@/servicos/api'
import { EVENTOS_BORDO, SINAIS_RELOGIO, type Gatilho } from '@/servicos/cenarios'
import { ajustarEquipe, classeFaixa, embutida, nome, num } from '@/servicos/formato'

const tripulacao = tripulacaoMock
const route = useRoute()
const router = useRouter()

// ?quem=kenji abre o pulso de outra pessoa (um pulso por aba).
const quem = computed({
  get: () => {
    const q = String(route.query.quem ?? 'sarah')
    return tripulacao.some((t) => t.id === q) ? q : 'sarah'
  },
  set: (id: string) => {
    router.replace({ query: { ...route.query, quem: id } })
  },
})
const { dados, erro, conexao, decidir, beber, respirou, enviar, carregar } = usarRelogio(quem)
watch(() => dados.value?.equipe, (eq) => ajustarEquipe(eq))

const tripulante = computed(() => tripulacao.find((t) => t.id === quem.value) ?? tripulacao[0]!)
const nomePulso = computed(() => dados.value?.eu.nome ?? tripulante.value.nome)

// Offline: a prévia dos três estados, com os dados de exemplo.
const nivelPrevia = ref<NivelSaude>(0)
const mostrador = computed(() => {
  const d = dados.value
  if (!d)
    return {
      nivel: nivelPrevia.value,
      estado: PREVIA_ESTADO[nivelPrevia.value],
      ciclo: CICLO_NO_RELOGIO[tripulante.value.id],
      missao: 'LEO',
      sexo: tripulante.value.sexo,
    }
  const sexo = d.eu.sexo === 'feminino' ? ('f' as const) : d.eu.sexo === 'masculino' ? ('m' as const) : tripulante.value.sexo
  return { ...paraMostrador(d), sexo }
})
const aviso = computed(() => (dados.value ? notificacao(dados.value) : null))
const emergencia = computed(() => !!dados.value?.emergencia)

// ------------------------------------------------------------ telas dentro do relógio
type Tela = 'evento' | 'inicio' | 'dica' | 'sinais' | 'cosmo' | 'estufa' | 'elo' | 'sinc'
const ROTULO: Record<Tela, string> = {
  evento: 'Evento',
  inicio: 'Início',
  dica: 'Dica da Cosmo',
  sinais: 'Seus sinais',
  cosmo: 'Cosmo',
  estufa: 'Estufa',
  elo: 'Elo Terra',
  sinc: 'Sincronia',
}
const listaTelas = computed<Tela[]>(() => {
  if (!dados.value) return []
  const e: Tela[] = aviso.value ? ['evento'] : []
  // Na emergência, só o que ajuda agora (como no relógio da demo).
  return emergencia.value ? [...e, 'sinais', 'cosmo', 'sinc'] : [...e, 'inicio', 'dica', 'sinais', 'cosmo', 'estufa', 'elo', 'sinc']
})
const telas = computed(() =>
  listaTelas.value.map((id) => ({ id, rotulo: id === 'evento' && emergencia.value ? 'Alerta médico' : ROTULO[id] })),
)
const tela = ref<Tela>('inicio')
const telaVisivel = computed<Tela>(() => (listaTelas.value.includes(tela.value) ? tela.value : (listaTelas.value[0] ?? 'inicio')))

// Uma pendência nova toma a tela, como uma notificação no pulso.
let vistoEvento: string | null = null
watch(aviso, (a) => {
  if (a && a.id !== vistoEvento) {
    vistoEvento = a.id
    tela.value = 'evento'
    respirando.value = 0
  }
})
watch(quem, () => {
  tela.value = 'inicio'
  conversa.value = []
  vistoEvento = null
  respirando.value = 0
})

function irPara(id: string) {
  respirando.value = 0
  tela.value = id as Tela
}
function proxima() {
  if (respirando.value) return (respirando.value = 0)
  const l = listaTelas.value
  tela.value = l[(l.indexOf(telaVisivel.value) + 1) % l.length] ?? 'inicio'
}

// Notificação curta no topo do relógio quando chega um aviso novo.
const notificacaoTopo = ref<string | null>(null)
let idNotif = 0
watch(
  () => dados.value?.avisos?.[0]?.texto,
  (texto, antes) => {
    if (!texto || texto === antes) return
    notificacaoTopo.value = texto
    window.clearTimeout(idNotif)
    idNotif = window.setTimeout(() => (notificacaoTopo.value = null), 5000)
  },
)

// Respiração guiada: 10 s na demo; no fim, conta para a missão do dia.
const respirando = ref(0)
let idRespira = 0
function respirar() {
  respirando.value = 10
  window.clearInterval(idRespira)
  idRespira = window.setInterval(() => {
    if (respirando.value <= 0) return window.clearInterval(idRespira)
    if (--respirando.value > 0) return
    window.clearInterval(idRespira)
    if (dados.value) respirou()
  }, 1000)
}
onUnmounted(() => {
  window.clearInterval(idRespira)
  window.clearTimeout(idNotif)
})

function tocar(b: BotaoRelogio) {
  if (b.tipo === 'respirar') return respirar()
  if (b.tipo === 'agua') return beber()
  if (b.tipo === 'decidir' && aviso.value) return decidir(aviso.value.id, b.acao)
}

// Dica da Cosmo: uma sugestão por vez, como o "insight" da demo.
const dica = computed(() => {
  const d = dados.value
  if (!d) return null
  if (d.jogo?.brinde === 'chegou')
    return { tag: 'Elo Terra', cor: 'agua', texto: 'A Ana propôs um brinde hídrico lá da Terra. Beba 250 ml junto com ela.', botao: 'Brindar · +250 ml', acao: 'agua' }
  if (d.link.blackout)
    return { tag: 'IA local', cor: 'warn', texto: 'Sem sinal com a Terra. Seus dados ficam salvos no relógio e eu sigo acompanhando você.', botao: 'Ver meus sinais', acao: 'sinais' }
  if (d.eu.agua_ml_dia / d.eu.agua_meta < 0.7)
    return {
      tag: 'Hidratação',
      cor: 'agua',
      texto: `Faltam ${num(d.eu.agua_meta - d.eu.agua_ml_dia)} ml para a meta de hoje. Beba 250 ml agora.`,
      botao: '+250 ml',
      acao: 'agua',
    }
  if (d.eu.metricas.hrv?.faixa !== 'padrao' || (d.eu.estresse ?? 0) >= 60)
    return { tag: 'Estresse', cor: 'warn', texto: 'Seu HRV caiu um pouco. Um minuto de respiração lenta ajuda a recuperar.', botao: 'Respirar 1 min', acao: 'respirar' }
  return { tag: 'Tudo certo', cor: '', texto: 'Sinais estáveis. Siga no seu ritmo; eu aviso se algo mudar.', botao: 'Ver meus sinais', acao: 'sinais' }
})
function usarDica(acao: string) {
  if (acao === 'agua') return beber()
  if (acao === 'respirar') return respirar()
  irPara(acao)
}

// Cosmo no relógio: só o que é da pessoa.
interface Fala {
  quem: 'eu' | 'cosmo'
  texto: string
}
const conversa = ref<Fala[]>([])
const perguntando = ref(false)
const perguntasCosmo = computed(() =>
  emergencia.value
    ? ['O que está acontecendo?', 'O que é fibrilação atrial?']
    : dados.value?.link.blackout
      ? ['Quando volta o sinal?', 'Como estou?']
      : ['Como estou?', 'Por que estou cansada?'],
)
async function perguntar(q: string) {
  if (perguntando.value) return
  conversa.value.push({ quem: 'eu', texto: q })
  perguntando.value = true
  try {
    const r = await perguntarApi(q, 'relogio', quem.value)
    conversa.value.push({ quem: 'cosmo', texto: r.resposta })
  } catch {
    conversa.value.push({ quem: 'cosmo', texto: 'Não consegui responder agora.' })
  } finally {
    perguntando.value = false
  }
}

const sinais = computed(() => {
  const e = dados.value?.eu
  if (!e) return []
  const m = e.metricas
  return [
    { rotulo: 'FC', valor: num(e.fc), un: 'bpm', faixa: m.fc?.faixa },
    { rotulo: 'SpO₂', valor: num(e.spo2), un: '%', faixa: m.spo2?.faixa },
    { rotulo: 'HRV', valor: num(e.hrv), un: 'ms', faixa: m.hrv?.faixa },
    { rotulo: 'Água', valor: num(e.agua_ml_dia), un: `/ ${num(e.agua_meta)} ml`, faixa: m.hidratacao?.faixa },
  ]
})
const fila = computed(() => dados.value?.link.fila ?? [])

// Gatilhos de evento (fora do relógio): os mesmos da sala de simulação.
const disparando = ref(false)
async function disparar([, cenario, tid]: Gatilho) {
  disparando.value = true
  try {
    await pedir('/simulador/cenario', { cenario, tripulante_id: tid })
    if (tid && tid !== quem.value && cenario !== 'rotina') quem.value = tid
    await carregar()
  } finally {
    disparando.value = false
  }
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
      <p class="etiqueta-topo"><span>A bordo</span> Relógio circular · 45 mm</p>
      <h1>Relógio de {{ nomePulso }}</h1>
      <p v-if="conexao === 'offline'" class="offline" role="status">
        Modo offline: prévia com dados de exemplo. O relógio volta sozinho quando a API responder.
      </p>
    </header>

    <RelogioPrototipo
      :nivel="mostrador.nivel"
      :sexo="mostrador.sexo"
      :estado="mostrador.estado"
      :ciclo="mostrador.ciclo"
      :missao="mostrador.missao"
      :telas="dados ? telas : undefined"
      :tela-atual="respirando ? 'respira' : telaVisivel"
      :fundo="!respirando && telaVisivel === 'evento' && aviso ? (aviso.variante === 'crit' ? 'crit' : aviso.variante === 'warn' ? 'warn' : aviso.variante === 'roxo' ? 'roxo' : '') : ''"
      @proxima="proxima"
      @tela="irPara"
    >
      <template #tela>
        <div v-if="dados" class="w">
          <!-- Respiração guiada -->
          <template v-if="respirando">
            <p class="w-tag">Respiração guiada</p>
            <div class="w-respira" aria-hidden="true"><span></span></div>
            <p class="w-sub">Inspire 4 s · solte 6 s<br /><b>{{ respirando }}</b> s restantes</p>
            <button type="button" class="w-btn fantasma sm" @click="respirando = 0">Parar</button>
          </template>

          <!-- Evento ou alerta que pede resposta -->
          <template v-else-if="telaVisivel === 'evento' && aviso">
            <div class="w-rola">
              <p class="w-tag" :class="aviso.variante">{{ aviso.etiqueta }}</p>
              <p v-if="aviso.titulo" class="w-grande">{{ aviso.titulo }}</p>
              <p class="w-texto">{{ aviso.texto }}</p>
              <template v-if="aviso.botoes.length">
                <button type="button" class="w-btn" :class="aviso.botoes[0]!.variante" @click="tocar(aviso.botoes[0]!)">
                  {{ aviso.botoes[0]!.rotulo }}
                </button>
                <div v-if="aviso.botoes.length > 1" class="w-chips">
                  <button v-for="b in aviso.botoes.slice(1)" :key="b.rotulo" type="button" @click="tocar(b)">{{ b.rotulo }}</button>
                </div>
              </template>
              <p v-if="aviso.nota" class="w-sub">{{ aviso.nota }}</p>
            </div>
          </template>

          <!-- Dica da Cosmo -->
          <template v-else-if="telaVisivel === 'dica' && dica">
            <p class="w-tag" :class="dica.cor">{{ dica.tag }}</p>
            <p class="w-texto">{{ dica.texto }}</p>
            <button type="button" class="w-btn" :class="dica.cor === 'agua' ? 'agua' : dica.acao === 'sinais' ? 'fantasma' : ''" @click="usarDica(dica.acao)">
              {{ dica.botao }}
            </button>
          </template>

          <!-- Seus sinais -->
          <template v-else-if="telaVisivel === 'sinais'">
            <p class="w-tag">Seus sinais</p>
            <div class="w-sinais">
              <div v-for="s in sinais" :key="s.rotulo" class="w-sinal" :class="`f-${classeFaixa(s.faixa)}`">
                <span>{{ s.rotulo }}</span><b>{{ s.valor }}<small>{{ s.un }}</small></b>
              </div>
            </div>
            <p class="w-sub">Comparado com o seu próprio padrão</p>
          </template>

          <!-- Cosmo -->
          <template v-else-if="telaVisivel === 'cosmo'">
            <p class="w-tag" :class="{ warn: dados.link.blackout }">Cosmo · {{ dados.link.blackout ? 'IA local' : 'no relógio' }}</p>
            <div class="w-fio" aria-live="polite">
              <div v-if="!conversa.length" class="w-bolha cosmo">Pergunte algo. Eu explico; quem decide é um humano.</div>
              <div v-for="(m, i) in conversa.slice(-4)" :key="i" class="w-bolha" :class="m.quem">{{ m.texto }}</div>
              <div v-if="perguntando" class="w-bolha cosmo digitando" aria-label="Cosmo digitando"><i></i><i></i><i></i></div>
            </div>
            <div class="w-chips">
              <button v-for="q in perguntasCosmo" :key="q" type="button" :disabled="perguntando" @click="perguntar(q)">{{ q }}</button>
            </div>
          </template>

          <!-- Estufa cooperativa -->
          <template v-else-if="telaVisivel === 'estufa'">
            <template v-if="dados.jogo">
              <p class="w-tag ok">Bioma cooperativo</p>
              <svg class="w-planta" viewBox="0 0 60 60" aria-hidden="true">
                <ellipse cx="30" cy="56" rx="14" ry="2" fill="currentColor" opacity=".25" />
                <path d="M19 44h22l-3 10H22z" fill="#101a30" stroke="currentColor" stroke-width="1.5" />
                <path d="M30 44V16" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                <g fill="currentColor" fill-opacity=".85">
                  <path v-if="dados.jogo.nivel >= 1" d="M30 40c-6 0-11-3-12-8 6-1 11 2 12 8z" />
                  <path v-if="dados.jogo.nivel >= 2" d="M30 34c6 0 11-3 12-8-6-1-11 2-12 8z" />
                  <path v-if="dados.jogo.nivel >= 3" d="M30 28c-5 0-9-3-10-7 5-1 9 2 10 7z" />
                  <path v-if="dados.jogo.nivel >= 4" d="M30 23c5 0 9-3 10-7-5-1-9 2-10 7z" />
                  <path v-if="dados.jogo.nivel >= 5" d="M30 18c-4 0-7-2-8-5 4-1 7 1 8 5z" />
                </g>
                <circle cx="30" cy="13" r="3.2" fill="#00e5ff" />
              </svg>
              <p class="w-xp">Nível {{ dados.jogo.nivel }} · estufa {{ dados.jogo.pct }}% · <b>{{ dados.jogo.xp }} XP</b></p>
              <div class="w-missoes">
                <div class="w-missao" :class="{ feita: dados.jogo.missoes.treino }">
                  <span>{{ dados.jogo.missoes.treino ? '✓' : '·' }}</span>Esteira<small>{{ dados.jogo.missoes.treino ? 'feito' : '14:00' }}</small>
                </div>
                <component
                  :is="dados.jogo.missoes.agua ? 'div' : 'button'"
                  type="button"
                  class="w-missao"
                  :class="{ feita: dados.jogo.missoes.agua }"
                  @click="!dados.jogo.missoes.agua && beber()"
                >
                  <span>{{ dados.jogo.missoes.agua ? '✓' : '+' }}</span>Água do dia<small>{{ dados.jogo.missoes.agua ? 'feito' : '+250 ml' }}</small>
                </component>
                <component
                  :is="dados.jogo.missoes.respiracao ? 'div' : 'button'"
                  type="button"
                  class="w-missao"
                  :class="{ feita: dados.jogo.missoes.respiracao }"
                  @click="!dados.jogo.missoes.respiracao && respirar()"
                >
                  <span>{{ dados.jogo.missoes.respiracao ? '✓' : '+' }}</span>Escudo mental<small>{{ dados.jogo.missoes.respiracao ? 'feito' : '1 min' }}</small>
                </component>
              </div>
            </template>
            <p v-else class="w-sub">Missões pausadas durante o alerta.</p>
          </template>

          <!-- Elo com a família -->
          <template v-else-if="telaVisivel === 'elo'">
            <template v-if="dados.jogo">
              <p class="w-tag agua">Elo Terra · família</p>
              <div class="w-corrida">
                <div><span>Corrida Terra–órbita</span><b>{{ num(dados.jogo.corrida_km, 1) }}/{{ dados.jogo.corrida_meta }} km</b></div>
                <div class="w-barra"><i :style="{ width: `${Math.min(100, (dados.jogo.corrida_km / dados.jogo.corrida_meta) * 100)}%` }"></i></div>
              </div>
              <div class="w-familia">
                <div v-for="(m, i) in (dados.mensagens ?? []).slice(0, 2)" :key="i" class="w-msg">
                  <span class="av">TE</span><span class="tx">{{ m.texto }}</span>
                </div>
                <p v-if="!(dados.mensagens ?? []).length" class="w-sub">Nenhuma mensagem nova da família.</p>
              </div>
              <button v-if="dados.jogo.brinde === 'chegou'" type="button" class="w-btn agua sm" @click="beber()">Brindar com a Ana · +250 ml</button>
              <div v-else class="w-chips">
                <button type="button" @click="enviar('incentivo')">Incentivo ao Lucas</button>
                <button type="button" @click="enviar('recado_familia')">Recado</button>
              </div>
            </template>
            <p v-else class="w-sub">Elo pausado durante o alerta.</p>
          </template>

          <!-- Sincronia com a Terra -->
          <template v-else-if="telaVisivel === 'sinc'">
            <p class="w-tag" :class="{ warn: dados.link.blackout }">Sincronia · {{ dados.link.blackout ? 'sem sinal' : dados.link.link }}</p>
            <p class="w-atraso">{{ dados.link.blackout ? dados.link.volta_em : dados.link.atraso_txt }}</p>
            <p class="w-sub">
              {{ dados.link.blackout ? 'até a próxima janela' : 'de atraso até a Terra' }} · {{ fila.length }} na fila<template
                v-if="dados.link.fila_mb"
              >
                · {{ num(dados.link.fila_mb, 1) }} MB</template
              >
            </p>
            <div class="w-fila" aria-hidden="true">
              <i v-for="(p, i) in fila" :key="i" :class="`p${p.prioridade}`"></i>
              <i v-if="!fila.length" class="p4 vazio"></i>
            </div>
            <div class="w-pacotes">
              <div v-for="(p, i) in fila.slice(0, 2)" :key="i" class="w-pacote" :class="[`p${p.prioridade}`, { q: p.estado === 'fila' }]">
                <span class="tx">{{ p.rotulo ?? `Pacote P${p.prioridade}` }}</span><small>{{ p.estado === 'fila' ? 'na fila' : `${p.falta_s} s` }}</small>
              </div>
              <div v-if="!fila.length" class="w-pacote ok"><span class="tx">✓ Tudo sincronizado</span></div>
            </div>
            <button v-if="emergencia" type="button" class="w-btn crit sm" @click="enviar('sos')">Enviar SOS prioritário</button>
            <button v-else type="button" class="w-btn sm" @click="enviar('sincronia')">Sincronizar agora</button>
          </template>
        </div>
      </template>

      <template #aviso>
        <div v-if="notificacaoTopo" class="w-notificacao" role="status">{{ notificacaoTopo }}</div>
      </template>
    </RelogioPrototipo>

    <p v-if="erro" class="aviso-faixa erro" role="alert">{{ erro }}</p>
    <p v-if="dados" class="legenda">Toque nos pontos ou na coroa para trocar de tela.</p>

    <!-- Fora do relógio: só quem está com o pulso e os gatilhos de evento -->
    <section class="controles" aria-label="Controles da demonstração">
      <div class="grupo" role="group" aria-label="Tripulante">
        <button v-for="t in tripulacao" :key="t.id" type="button" :aria-pressed="t.id === quem" @click="quem = t.id">
          {{ dados ? nome(t.id) : t.nome }}
        </button>
      </div>
      <template v-if="dados && !embutida">
        <p class="etiqueta">Disparar evento</p>
        <div class="gatilhos">
          <button
            v-for="g in [...SINAIS_RELOGIO, ...EVENTOS_BORDO]"
            :key="g[0]"
            type="button"
            class="selecao"
            :disabled="disparando"
            @click="disparar(g)"
          >
            {{ g[0] }}
          </button>
        </div>
      </template>
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
  gap: 16px;
  min-height: 100vh;
  padding: 28px 16px;
}
header {
  text-align: center;
}
.etiqueta-topo {
  margin: 0 0 6px;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--texto-fraco);
}
.etiqueta-topo span {
  margin-right: 6px;
  padding: 2px 7px;
  border-radius: 99px;
  border: 1px solid rgba(0, 229, 255, 0.4);
  color: var(--acento);
}
h1 {
  font-size: 20px;
}
.offline {
  margin-top: 8px;
  font-size: 12.5px;
  color: var(--warn);
}
.legenda {
  max-width: 360px;
  font-size: 11.5px;
  line-height: 1.45;
  text-align: center;
  color: var(--texto-fraco);
}

/* ------------------------------------------------------------------
   Telas dentro do relógio (formato do relógio da demo 1-demo-mvp)
   ------------------------------------------------------------------ */
.w {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  max-height: 100%;
}
.w-rola {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  max-height: 212px;
  overflow-y: auto;
  scrollbar-width: none;
}
.w-rola::-webkit-scrollbar {
  display: none;
}
.w-tag {
  font: 600 10.5px var(--mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--acento);
}
.w-tag.crit {
  color: #fca5a5;
}
.w-tag.warn {
  color: var(--warn);
}
.w-tag.agua {
  color: #93c5fd;
}
.w-tag.ok {
  color: var(--ok);
}
.w-tag.roxo {
  color: #c4b5fd;
}
.w-grande {
  font-size: 18px;
  font-weight: 700;
  line-height: 1.15;
  color: #fff;
  text-wrap: balance;
}
.w-texto {
  font-size: 12.5px;
  line-height: 1.38;
  color: var(--texto);
}
.w-sub {
  font-size: 11px;
  line-height: 1.35;
  color: var(--texto-medio);
}
.w-btn {
  width: 100%;
  padding: 8px 12px;
  border: 0;
  border-radius: 99px;
  background: var(--acento);
  color: #03141a;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}
.w-btn.sm {
  width: auto;
  padding: 6px 14px;
  font-size: 12px;
}
.w-btn.agua {
  background: var(--agua);
  color: #fff;
}
.w-btn.crit {
  background: var(--crit);
  color: #fff;
}
.w-btn.warn {
  background: var(--warn);
  color: #1a1205;
}
.w-btn.fantasma {
  background: var(--superficie-2);
  color: var(--texto);
}
.w-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
}
.w-chips button {
  padding: 4px 9px;
  border: 0;
  border-radius: 99px;
  background: var(--superficie-2);
  color: var(--texto);
  font-size: 10.5px;
  cursor: pointer;
}
.w-btn:focus-visible,
.w-chips button:focus-visible,
.w-missao:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}

/* sinais */
.w-sinais {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}
.w-sinal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  border-radius: 12px;
  border: 1px solid var(--linha);
  background: var(--superficie);
  font-size: 11px;
  color: var(--texto-medio);
}
.w-sinal b {
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--texto);
}
.w-sinal small {
  margin-left: 3px;
  font-size: 9.5px;
  font-weight: 500;
  color: var(--texto-fraco);
}
.w-sinal.f-warn {
  border-color: rgba(245, 158, 11, 0.5);
}
.w-sinal.f-crit {
  border-color: rgba(239, 68, 68, 0.6);
  background: rgba(239, 68, 68, 0.1);
}

/* Cosmo */
.w-fio {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  max-height: 118px;
  padding-top: 8px;
  overflow-y: auto;
  text-align: left;
  scrollbar-width: none;
  mask-image: linear-gradient(to bottom, transparent, #000 14px);
}
.w-fio::-webkit-scrollbar {
  display: none;
}
.w-bolha {
  max-width: 94%;
  padding: 6px 9px;
  border-radius: 12px;
  font-size: 11px;
  line-height: 1.33;
}
.w-bolha.cosmo {
  align-self: flex-start;
  border-bottom-left-radius: 4px;
  background: var(--superficie-2);
}
.w-bolha.eu {
  align-self: flex-end;
  border-bottom-right-radius: 4px;
  background: rgba(0, 229, 255, 0.16);
  color: #cffafe;
}
.digitando {
  display: flex;
  gap: 3px;
}
.digitando i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--texto-medio);
  animation: digitando 1s infinite;
}
.digitando i:nth-child(2) {
  animation-delay: 0.15s;
}
.digitando i:nth-child(3) {
  animation-delay: 0.3s;
}
@keyframes digitando {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

/* estufa */
.w-planta {
  width: 44px;
  height: 44px;
  color: var(--ok);
  filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.5));
}
.w-xp {
  font-size: 11px;
  font-weight: 600;
  color: var(--texto-medio);
}
.w-xp b {
  color: var(--ok);
}
.w-missoes {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
}
.w-missao {
  display: grid;
  grid-template-columns: 12px 1fr auto;
  gap: 6px;
  align-items: center;
  width: 100%;
  padding: 4px 8px;
  border-radius: 10px;
  border: 1px solid var(--linha);
  background: var(--superficie);
  color: var(--texto);
  font-size: 11px;
  text-align: left;
}
button.w-missao {
  cursor: pointer;
}
button.w-missao:hover {
  border-color: var(--acento);
}
.w-missao span {
  color: var(--acento);
}
.w-missao small {
  font: 500 9.5px var(--mono);
  color: var(--texto-fraco);
}
.w-missao.feita {
  opacity: 0.75;
}
.w-missao.feita span,
.w-missao.feita small {
  color: var(--ok);
}

/* elo */
.w-corrida {
  width: 100%;
  text-align: left;
}
.w-corrida > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  font-size: 10.5px;
  color: var(--texto-medio);
}
.w-corrida b {
  font-size: 11px;
  color: var(--texto);
}
.w-barra {
  height: 5px;
  margin-top: 4px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}
.w-barra i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--agua), var(--acento));
}
.w-familia {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
}
.w-msg {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  gap: 6px;
  align-items: center;
  padding: 4px 8px;
  border-radius: 10px;
  border: 1px solid var(--linha);
  background: var(--superficie);
  font-size: 10.5px;
  text-align: left;
}
.w-msg .av {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.28);
  color: #ddd6fe;
  font-size: 8.5px;
  font-weight: 600;
}
.w-msg .tx {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* sincronia */
.w-atraso {
  font-size: 19px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #fff;
}
.w-fila {
  display: flex;
  gap: 2px;
  width: 100%;
  height: 6px;
  border-radius: 4px;
  overflow: hidden;
  background: #1b2437;
}
.w-fila i {
  flex: 1;
  display: block;
}
.w-fila .p1 {
  background: var(--crit);
}
.w-fila .p2 {
  background: var(--acento);
}
.w-fila .p3 {
  background: var(--agua);
}
.w-fila .p4 {
  background: var(--ok);
}
.w-fila .vazio {
  opacity: 0.4;
}
.w-pacotes {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
}
.w-pacote {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px;
  padding: 4px 8px;
  border-left: 3px solid var(--acento);
  border-radius: 9px;
  background: var(--superficie);
  font-size: 10.5px;
  text-align: left;
}
.w-pacote .tx {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.w-pacote small {
  font: 500 9.5px var(--mono);
  color: var(--texto-fraco);
}
.w-pacote.p1 {
  border-left-color: var(--crit);
}
.w-pacote.p3 {
  border-left-color: var(--agua);
}
.w-pacote.p4,
.w-pacote.ok {
  border-left-color: var(--ok);
}
.w-pacote.q small {
  color: var(--warn);
}

/* respiração */
.w-respira {
  display: grid;
  place-items: center;
  width: 90px;
  height: 90px;
}
.w-respira span {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  border: 2px solid var(--acento);
  background: rgba(0, 229, 255, 0.12);
  animation: respira 10s ease-in-out infinite;
}
@keyframes respira {
  0% {
    transform: scale(0.55);
  }
  40% {
    transform: scale(1);
  }
  100% {
    transform: scale(0.55);
  }
}
@media (prefers-reduced-motion: reduce) {
  .w-respira span,
  .digitando i {
    animation: none;
  }
}

/* notificação no topo do relógio */
.w-notificacao {
  position: absolute;
  top: 12%;
  left: 50%;
  z-index: 2;
  max-width: 78%;
  padding: 5px 11px;
  border-radius: 99px;
  border: 1px solid var(--linha-forte);
  background: #1b2740;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transform: translateX(-50%);
  animation: desce 0.3s ease-out;
}
@keyframes desce {
  from {
    opacity: 0;
    transform: translate(-50%, -8px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

/* ------------------------------------------------------------------
   Fora do relógio: tripulante e gatilhos de evento
   ------------------------------------------------------------------ */
.controles {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  max-width: 640px;
}
.gatilhos {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
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
.grupo button {
  padding: 7px 14px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: var(--texto-fraco);
  font-size: 13px;
  cursor: pointer;
}
.grupo button:hover {
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
.grupo button:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
</style>
