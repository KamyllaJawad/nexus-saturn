<script setup lang="ts">
import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import CelularPrototipo from '../components/CelularPrototipo.vue'
import CelularInicio from '../components/CelularInicio.vue'
import CelularElo from '../components/CelularElo.vue'
import CelularMensagens from '../components/CelularMensagens.vue'
import { tripulacaoMock } from '@/mocks/tripulacao'
import {
    ATRASO_MS,
    DESAFIO_INICIAL,
    ESTUFA_INICIAL,
    TEMPO_PARA_SARAH_BRINDAR_MS,
    type Aba,
    type Cenario,
    type FaseBrinde,
    type ItemFeed,
    type Mensagem,
} from '@/mocks/familia'

const cenario = ref<Cenario>('normal')
const aba = ref<Aba>('inicio')
const mensagens = ref<Mensagem[]>([])
const feed = ref<ItemFeed[]>([])
const estufa = reactive({ ...ESTUFA_INICIAL })
const desafio = reactive({ ...DESAFIO_INICIAL })
const brinde = ref<FaseBrinde | null>(null)
const idDoConvite = ref<number | null>(null)

const sarah = tripulacaoMock.find((t) => t.id === 'sarah')!
const hidratacaoPct = Math.round((sarah.vitais.agua / sarah.vitais.aguaMeta) * 100)

const CENARIOS: { valor: Cenario; nome: string }[] = [
    { valor: 'normal', nome: 'Normal' },
    { valor: 'emergencia', nome: 'Emergência' },
    { valor: 'blackout', nome: 'Blackout' },
]

const timers = new Set<number>()
function depois(ms: number, fn: () => void) {
    const t = window.setTimeout(() => {
        timers.delete(t)
        fn()
    }, ms)
    timers.add(t)
}
onUnmounted(() => timers.forEach((t) => window.clearTimeout(t)))

const agora = () => new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

let ultimoId = 0
const aoChegar = new Map<number, () => void>()

function enviar(texto: string, quandoChegar?: () => void): number {
    const id = ++ultimoId
    const status = cenario.value === 'blackout' ? 'fila' : 'caminho'
    mensagens.value.push({ id, texto, status })
    if (quandoChegar) aoChegar.set(id, quandoChegar)
    if (status === 'caminho') agendarEntrega(id)
    return id
}

function agendarEntrega(id: number) {
    depois(ATRASO_MS, () => {
        const m = mensagens.value.find((x) => x.id === id)
        if (!m) return
        m.status = 'entregue'
        m.hora = agora()
        aoChegar.get(id)?.()
        aoChegar.delete(id)
    })
}

watch(cenario, (novo, antigo) => {
    if (antigo !== 'blackout' || novo === 'blackout') return
    for (const m of mensagens.value.filter((x) => x.status === 'fila')) {
        m.status = 'caminho'
        agendarEntrega(m.id)
    }
})

function crescerEstufa(pontos: number) {
    estufa.pct += pontos
    if (estufa.pct >= 100) {
        estufa.pct -= 100
        estufa.nivel++
    }
}

function registrarNoFeed(texto: string) {
    feed.value = [{ texto, hora: agora() }, ...feed.value].slice(0, 3)
}

function correr() {
    desafio.km += 5
    enviar('Lucas registrou 5 km de corrida', () => crescerEstufa(1))
}

function brindar() {
    if (brinde.value && brinde.value !== 'concluido') return
    brinde.value = 'enviado'
    idDoConvite.value = enviar('Convite da Ana: brinde hídrico de 250 ml', () => {
        brinde.value = 'chegou'
        depois(TEMPO_PARA_SARAH_BRINDAR_MS, () => {
            brinde.value = 'brindou'
            depois(ATRASO_MS, () => {
                brinde.value = 'concluido'
                crescerEstufa(3)
                registrarNoFeed('A Sarah brindou com a Ana: +250 ml')
            })
        })
    })
}

function enviarAudio() {
    enviar('Áudio do Lucas: "Boa noite, mãe! Corri 5 km hoje."')
}

const conviteNaFila = computed(
    () => mensagens.value.find((m) => m.id === idDoConvite.value)?.status === 'fila',
)
</script>

<template>
    <main class="pagina">
        <header>
            <p class="etiqueta"><span>Na Terra</span> Celular da família</p>
            <h1>App Terra-Órbita</h1>
        </header>

        <CelularPrototipo v-model:aba="aba">
            <CelularInicio
                v-if="aba === 'inicio'"
                :cenario="cenario"
                :hidratacao-pct="hidratacaoPct"
                :feed="feed"
            />
            <CelularElo
                v-else-if="aba === 'elo'"
                :estufa="estufa"
                :desafio="desafio"
                :brinde="brinde"
                :brinde-na-fila="conviteNaFila"
                @correr="correr"
                @brindar="brindar"
            />
            <CelularMensagens v-else :mensagens="mensagens" @enviar-audio="enviarAudio" />
        </CelularPrototipo>

        <section class="controles" aria-label="Prévia do protótipo">
            <div class="grupo" role="group" aria-label="Cenário">
                <button
                    v-for="c in CENARIOS"
                    :key="c.valor"
                    type="button"
                    :class="c.valor"
                    :aria-pressed="c.valor === cenario"
                    @click="cenario = c.valor"
                >
                    {{ c.nome }}
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
    gap: 28px;
    min-height: 100vh;
    padding: 40px 16px;
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
    border: 1px solid rgba(139, 92, 246, 0.5);
    color: #c4b5fd;
}
h1 {
    margin: 0;
    font-size: 20px;
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
    font: inherit;
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
.grupo button.emergencia[aria-pressed='true'] {
    color: var(--crit);
}
.grupo button.blackout[aria-pressed='true'] {
    color: var(--warn);
}
.grupo button:focus-visible {
    outline: 2px solid var(--acento);
    outline-offset: 2px;
}
</style>
