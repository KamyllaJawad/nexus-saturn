<script setup lang="ts">
// Relógio de pulso: o mostrador da Isabelle no topo e, embaixo, as telas do relógio
// (início, sinais, Cosmo, estufa, Elo, sincronia e o evento que pede resposta).
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RelogioPrototipo from '../components/RelogioPrototipo.vue'
import { tripulacaoMock, type NivelSaude } from '@/mocks/tripulacao'
import { CICLO_NO_RELOGIO, PREVIA_ESTADO } from '@/mocks/relogio'
import { notificacao, paraMostrador, usarRelogio, type BotaoRelogio } from '@/servicos/relogio'
import { perguntarApi } from '@/servicos/api'
import { ajustarEquipe, classe, classeFaixa, ESTADO, hora, nome, num, sono } from '@/servicos/formato'

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
const { dados, erro, conexao, decidir, beber, respirou, enviar } = usarRelogio(quem)
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

// ------------------------------------------------------------ telas do relógio
type Tela = 'evento' | 'inicio' | 'sinais' | 'cosmo' | 'estufa' | 'elo' | 'sinc'
const TODAS: [Tela, string][] = [
  ['inicio', 'Início'],
  ['sinais', 'Sinais'],
  ['cosmo', 'Cosmo'],
  ['estufa', 'Estufa'],
  ['elo', 'Elo'],
  ['sinc', 'Sincronia'],
]
const tela = ref<Tela>('inicio')
const telas = computed<[Tela, string][]>(() => {
  const emergencia = !!dados.value?.emergencia
  const base = emergencia ? TODAS.filter(([k]) => ['sinais', 'cosmo', 'sinc'].includes(k)) : TODAS
  return aviso.value ? [['evento', emergencia ? 'Alerta' : 'Evento'], ...base] : base
})
// Uma pendência nova toma a tela, como uma notificação no pulso.
let vistoEvento: string | null = null
watch(aviso, (a) => {
  if (a && a.id !== vistoEvento) {
    vistoEvento = a.id
    tela.value = 'evento'
  }
  if (!a && tela.value === 'evento') tela.value = 'inicio'
})
watch(quem, () => {
  tela.value = 'inicio'
  conversa.value = []
  vistoEvento = null
})
watch(telas, (ts) => {
  if (!ts.some(([k]) => k === tela.value)) tela.value = ts[0]?.[0] ?? 'inicio'
})

// Respiração guiada: 10 s na demo; no fim, conta para a missão do dia.
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

// Cosmo no relógio: só o que é da pessoa.
interface Fala {
  quem: 'eu' | 'cosmo'
  texto: string
  fonte?: string
  modo?: string
}
const conversa = ref<Fala[]>([])
const perguntando = ref(false)
const perguntasCosmo = computed(() =>
  dados.value?.emergencia
    ? ['O que está acontecendo?', 'O que é fibrilação atrial?']
    : dados.value?.link.blackout
      ? ['Quando volta o sinal?', 'Como estou?']
      : ['Como estou?', 'Por que estou cansada?', 'Preciso beber água?'],
)
async function perguntar(q: string) {
  if (perguntando.value) return
  conversa.value.push({ quem: 'eu', texto: q })
  perguntando.value = true
  try {
    const r = await perguntarApi(q, 'relogio', quem.value)
    conversa.value.push({ quem: 'cosmo', texto: r.resposta, fonte: r.fonte?.titulo, modo: r.modo })
  } catch {
    conversa.value.push({ quem: 'cosmo', texto: 'Não consegui responder agora.' })
  } finally {
    perguntando.value = false
  }
}

const SINAIS_PULSO = computed(() => {
  const e = dados.value?.eu
  if (!e) return []
  const m = e.metricas
  return [
    ['FC', `${num(e.fc)} bpm`, m.fc?.faixa],
    ['SpO₂', `${num(e.spo2)}%`, m.spo2?.faixa],
    ['HRV', `${num(e.hrv)} ms`, m.hrv?.faixa],
    ['Pele', `${num(e.temp_pele, 1)} °C`, m.temperatura?.faixa],
    ['Resp', num(e.respiracao), m.respiracao?.faixa],
    ['Sono', sono(e.sono_min_noite), m.sono?.faixa],
    ['Água', `${num(e.agua_ml_dia)} / ${num(e.agua_meta)} ml`, m.hidratacao?.faixa],
  ] as [string, string, string | undefined][]
})

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
    />

    <p v-if="dados?.avisos?.[0]" class="toast" role="status">{{ dados.avisos[0].texto }}</p>
    <p v-if="erro" class="aviso-faixa erro" role="alert">{{ erro }}</p>

    <!-- Telas do relógio (com a API) -->
    <template v-if="dados">
      <nav class="telas" aria-label="Telas do relógio">
        <button
          v-for="[k, rotulo] in telas"
          :key="k"
          type="button"
          class="selecao"
          :class="{ alerta: k === 'evento' }"
          :aria-pressed="k === tela"
          @click="tela = k"
        >
          {{ rotulo }}
        </button>
      </nav>

      <section v-if="respirando" class="cartao painel" aria-live="polite">
        <p class="etiqueta">Respiração guiada</p>
        <div class="respira" aria-hidden="true"></div>
        <p class="texto">Inspire 4 s · solte 6 s. <b>{{ respirando }}</b> s restantes.</p>
        <div class="acoes"><button type="button" class="btn sm" @click="respirando = 0">Parar</button></div>
      </section>

      <section v-else-if="tela === 'evento' && aviso" class="cartao painel" :class="aviso.variante" role="alert">
        <p class="etiqueta">{{ aviso.etiqueta }}</p>
        <p v-if="aviso.titulo" class="titulo">{{ aviso.titulo }}</p>
        <p class="texto">{{ aviso.texto }}</p>
        <div v-if="aviso.botoes.length" class="botoes">
          <button v-for="b in aviso.botoes" :key="b.rotulo" type="button" :class="b.variante" @click="tocar(b)">
            {{ b.rotulo }}
          </button>
        </div>
        <p v-if="aviso.nota" class="meta">{{ aviso.nota }}</p>
      </section>

      <section v-else-if="tela === 'inicio'" class="cartao painel">
        <p class="etiqueta">{{ dados.eu.nome }} · {{ hora(dados.eu.gerada_em) }}</p>
        <p class="titulo" :class="`c-${classe(dados.eu.estado)}`">{{ (ESTADO[dados.eu.estado] ?? dados.eu.estado).toUpperCase() }}</p>
        <p class="texto">
          Homeostase {{ dados.eu.homeostase }}% · {{ dados.contagem.otimos }} ótimos · {{ dados.contagem.atencao }} atenção ·
          {{ dados.contagem.criticos }} críticos
        </p>
        <p class="meta">{{ dados.eu.qualidade === 'bom' ? 'Sinal bom' : 'Sinal a confirmar antes de alarmar' }}</p>
        <p v-if="dados.ciclo?.na_janela" class="meta c-roxo">Só você vê · calendário de solo: trecho de cólica</p>
        <div v-if="!dados.emergencia" class="acoes">
          <button type="button" class="btn agua sm" @click="beber()">+250 ml</button>
          <button type="button" class="btn sm" @click="respirar()">Respirar 1 min</button>
        </div>
      </section>

      <section v-else-if="tela === 'sinais'" class="cartao painel">
        <p class="etiqueta">Seus sinais</p>
        <div class="selos sinais">
          <span v-for="[r, v, f] in SINAIS_PULSO" :key="r" class="selo" :class="classeFaixa(f)">{{ r }} {{ v }}</span>
        </div>
        <p class="meta">Estresse {{ dados.eu.estresse }}/100 · dose {{ num(dados.eu.dose_msv_dia, 2) }} mSv hoje.</p>
        <p class="meta">Cada faixa compara você com a sua própria linha de base.</p>
      </section>

      <section v-else-if="tela === 'cosmo'" class="cartao painel">
        <p class="etiqueta" :class="{ 'c-warn': dados.link.blackout }">
          Cosmo · {{ dados.link.blackout ? 'IA local, sem a Terra' : 'no relógio' }}
        </p>
        <div class="fio" aria-live="polite">
          <div v-if="!conversa.length" class="bolha cosmo">Pergunte algo. Eu explico e cito o protocolo; quem decide é um humano.</div>
          <div v-for="(m, i) in conversa.slice(-4)" :key="i" class="bolha" :class="m.quem">
            {{ m.texto }}
            <small v-if="m.fonte || m.modo">{{ m.fonte ? `Fonte: ${m.fonte} · ` : '' }}{{ m.modo }}</small>
          </div>
          <div v-if="perguntando" class="meta">Cosmo está pensando…</div>
        </div>
        <div class="acoes">
          <button v-for="q in perguntasCosmo" :key="q" type="button" class="selecao" :disabled="perguntando" @click="perguntar(q)">
            {{ q }}
          </button>
        </div>
      </section>

      <section v-else-if="tela === 'estufa'" class="cartao painel">
        <template v-if="dados.jogo">
          <p class="etiqueta c-ok">Bioma cooperativo</p>
          <p class="titulo">Estufa nível {{ dados.jogo.nivel }}</p>
          <div class="barra"><i :style="{ width: `${dados.jogo.pct}%` }"></i></div>
          <p class="meta">{{ dados.jogo.pct }}% do nível · {{ dados.jogo.xp }} XP da tripulação · sem ranking</p>
          <div class="acoes">
            <span class="selo" :class="{ ok: dados.jogo.missoes.treino }">{{ dados.jogo.missoes.treino ? '✓ ' : '' }}Esteira</span>
            <span class="selo" :class="{ ok: dados.jogo.missoes.agua }">{{ dados.jogo.missoes.agua ? '✓ ' : '' }}Água do dia</span>
            <button v-if="!dados.jogo.missoes.agua" type="button" class="btn agua sm" @click="beber()">+250 ml</button>
            <span class="selo" :class="{ ok: dados.jogo.missoes.respiracao }">{{ dados.jogo.missoes.respiracao ? '✓ ' : '' }}Escudo mental</span>
            <button v-if="!dados.jogo.missoes.respiracao" type="button" class="btn sm" @click="respirar()">Respirar</button>
          </div>
        </template>
        <p v-else class="nota">Missões pausadas durante o alerta.</p>
      </section>

      <section v-else-if="tela === 'elo'" class="cartao painel">
        <template v-if="dados.jogo">
          <p class="etiqueta">Elo Terra · família</p>
          <p class="texto">Corrida Terra–órbita: {{ num(dados.jogo.corrida_km, 1) }} de {{ dados.jogo.corrida_meta }} km</p>
          <div class="barra">
            <i :style="{ width: `${Math.min(100, (dados.jogo.corrida_km / dados.jogo.corrida_meta) * 100)}%` }"></i>
          </div>
          <div class="fio">
            <div v-for="(m, i) in dados.mensagens ?? []" :key="i" class="bolha cosmo">
              {{ m.texto }}<small>saiu da Terra {{ hora(m.enviado_em, true) }} · chegou {{ hora(m.recebido_em, true) }}</small>
            </div>
            <p v-if="!(dados.mensagens ?? []).length" class="meta">Nenhuma mensagem nova da família.</p>
          </div>
          <div class="acoes">
            <button v-if="dados.jogo.brinde === 'chegou'" type="button" class="btn agua sm" @click="beber()">Brindar com a Ana · +250 ml</button>
            <button type="button" class="btn sm" @click="enviar('incentivo')">Incentivo ao Lucas</button>
            <button type="button" class="btn sm" @click="enviar('recado_familia')">Recado</button>
          </div>
        </template>
        <p v-else class="nota">Elo pausado durante o alerta.</p>
      </section>

      <section v-else-if="tela === 'sinc'" class="cartao painel">
        <p class="etiqueta" :class="{ 'c-warn': dados.link.blackout }">
          Sincronia · {{ dados.link.blackout ? 'sem sinal' : dados.link.link }}
        </p>
        <p class="titulo">{{ dados.link.blackout ? dados.link.volta_em : dados.link.atraso_txt }}</p>
        <p class="meta">
          {{
            dados.link.blackout
              ? `até a próxima janela · ${dados.link.motivo_blackout}`
              : `de atraso até a Terra${dados.link.comprimido ? ' · na demo, 1 min = 1 s' : ''}`
          }}
        </p>
        <p class="meta">{{ (dados.link.fila ?? []).length }} pacote(s) na fila · {{ num(dados.link.fila_mb, 1) }} MB</p>
        <div class="selos">
          <span v-for="(p, i) in (dados.link.fila ?? []).slice(0, 3)" :key="i" class="selo" :class="{ crit: p.prioridade === 1 }">
            P{{ p.prioridade }} · {{ p.estado === 'fila' ? 'na fila' : `chega em ${p.falta_s} s` }}
          </span>
        </div>
        <div class="acoes">
          <button type="button" class="btn sm" @click="enviar('sincronia')">Sincronizar</button>
          <button type="button" class="btn crit sm" @click="enviar('sos')">SOS prioritário</button>
        </div>
      </section>

      <p class="meta legenda">
        {{ dados.eu.nome }} · {{ dados.eu.papel }}. Esta tela só mostra o que é de {{ dados.eu.nome }}; o que não é compartilhado não sai
        daqui.
      </p>
    </template>

    <section class="controles" aria-label="Controles do relógio">
      <div class="grupo" role="group" aria-label="Tripulante">
        <button v-for="t in tripulacao" :key="t.id" type="button" :aria-pressed="t.id === quem" @click="quem = t.id">
          {{ dados ? nome(t.id) : t.nome }}
        </button>
      </div>
      <div v-if="!dados" class="grupo" role="group" aria-label="Estado da prévia">
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
  gap: 18px;
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
.toast {
  max-width: 380px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 229, 255, 0.35);
  background: rgba(0, 229, 255, 0.06);
  font-size: 12.5px;
  text-align: center;
}

.telas {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
}
.telas .alerta {
  color: var(--warn);
}

.painel {
  width: min(380px, 100%);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.painel .acoes {
  margin-top: 4px;
}
.titulo {
  font-size: 17px;
  font-weight: 600;
}
.texto {
  font-size: 13px;
  line-height: 1.5;
}
.legenda {
  max-width: 380px;
  text-align: center;
}
.sinais {
  justify-content: center;
}

.fio {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bolha {
  max-width: 92%;
  padding: 7px 10px;
  border-radius: 12px;
  font-size: 12.5px;
  line-height: 1.45;
}
.bolha small {
  display: block;
  margin-top: 3px;
  font-size: 10.5px;
  color: var(--texto-fraco);
}
.bolha.cosmo {
  align-self: flex-start;
  border: 1px solid rgba(0, 229, 255, 0.25);
  background: linear-gradient(140deg, rgba(0, 229, 255, 0.08), var(--superficie) 70%);
}
.bolha.eu {
  align-self: flex-end;
  border: 1px solid var(--linha-forte);
  background: #1d2a47;
}

.respira {
  width: 70px;
  height: 70px;
  margin: 6px auto;
  border-radius: 50%;
  border: 2px solid var(--acento);
  animation: respira 10s ease-in-out infinite;
}
@keyframes respira {
  0%,
  100% {
    transform: scale(0.7);
  }
  40% {
    transform: scale(1.05);
  }
}
@media (prefers-reduced-motion: reduce) {
  .respira {
    animation: none;
  }
}

/* Notificação no pulso */
.cartao.agua {
  border-color: rgba(59, 130, 246, 0.5);
}
.warn .etiqueta {
  color: var(--warn);
}
.crit .etiqueta {
  color: var(--crit);
}
.roxo .etiqueta {
  color: #c4b5fd;
}
.ok .etiqueta {
  color: var(--ok);
}
.agua .etiqueta {
  color: var(--agua);
}
.botoes {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}
.botoes button {
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--linha-forte);
  background: transparent;
  color: var(--texto);
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
.grupo button:focus-visible,
.botoes button:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
</style>
