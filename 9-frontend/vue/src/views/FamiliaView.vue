<script setup lang="ts">
// App Terra-Órbita no celular da família, no formato do celular da demo
// (1-demo-mvp): ilha, barra de status, cabeçalho do app e três abas (Início, Elo
// e Mensagens). A família recebe frases com o atraso da missão e nunca um número
// de saúde, diagnóstico, humor ou ciclo (ADR-007 e ADR-013): onde a demo mostrava
// sono e hidratação, aqui ficam o estado em palavras de cada tripulante.
import { computed, onUnmounted, ref } from 'vue'
import {
  BatteryFull,
  Check,
  Droplet,
  Footprints,
  House,
  Leaf,
  MessageCircle,
  Mic,
  Orbit,
  Radiation,
  ShieldCheck,
  Signal,
  UserRound,
  WifiOff,
} from 'lucide-vue-next'
import AstronautaAvatar from '../components/AstronautaAvatar.vue'
import { pedir } from '@/servicos/api'
import { usarConsulta } from '@/servicos/consulta'
import { embutida, hora, nome } from '@/servicos/formato'

interface Pacote {
  id: string
  rotulo: string
  estado: string
  gerado_em: string
  entregue_em?: string | null
  falta_s?: number | null
}
interface Feed {
  frase: string
  tripulacao: Record<string, string>
  ultimas: { frase: string; gerado_em: string; recebido_em: string }[]
  atraso: string
  sem_sinal: boolean
  dado_de: string | null
  elo: {
    estufa_nivel: number
    estufa_pct: number
    // Como a família vê o brinde, pelos pacotes do link: fila, enviado, chegou, feito.
    brinde: 'fila' | 'enviado' | 'chegou' | 'feito' | null
    brinde_falta_s?: number | null
    corrida: string
  }
  enviadas: Pacote[]
}

const feed = usarConsulta<Feed>(() => '/familia/feed')
const d = computed(() => feed.dados.value)
const acao = (tipo: 'brinde' | 'corrida' | 'mensagem') =>
  feed.executar(() => pedir('/familia/acao', { tipo }))

type Aba = 'inicio' | 'elo' | 'mensagens'
const aba = ref<Aba>('inicio')
const ABAS = [
  { id: 'inicio' as const, rotulo: 'Início', icone: House },
  { id: 'elo' as const, rotulo: 'Elo', icone: Leaf },
  { id: 'mensagens' as const, rotulo: 'Mensagens', icone: MessageCircle },
]

// Hora do celular (na Terra)
const agora = ref(new Date())
const idRelogio = window.setInterval(() => (agora.value = new Date()), 10_000)
onUnmounted(() => window.clearInterval(idRelogio))
const horaCelular = computed(() =>
  agora.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
)

// Destaque da tela inicial: sem sinal, abrigo por tempestade solar, equipe médica ou tudo bem.
const heroi = computed(() => {
  const f = d.value
  if (!f) return null
  if (f.sem_sinal)
    return {
      tipo: 'escuro' as const,
      icone: WifiOff,
      titulo: 'Sem sinal da nave por enquanto',
      texto: f.frase,
    }
  const ultima = f.ultimas[0]?.frase ?? ''
  if (/abrigo/.test(ultima) && !/saiu do abrigo|já saiu/.test(ultima))
    return {
      tipo: 'escuro' as const,
      icone: Radiation,
      titulo: 'A tripulação está no abrigo por precaução',
      texto:
        'Uma tempestade solar está passando. A nave tem um abrigo com proteção extra, e ir para lá é procedimento de rotina. Todos estão bem.',
    }
  if (f.frase.includes('equipe médica'))
    return {
      tipo: 'medico' as const,
      icone: ShieldCheck,
      titulo: 'A Sarah está sendo acompanhada pela equipe médica',
      texto:
        'Detalhes de saúde ficam entre a tripulação e os médicos da NASA. A NASA vai entrar em contato com novidades.',
    }
  return {
    tipo: 'ok' as const,
    icone: null,
    titulo: 'A Sarah está bem',
    texto: `As notícias da nave chegam com ${f.atraso} de atraso, o tempo que o sinal leva para viajar até aqui.`,
  }
})
const outros = computed(() =>
  Object.entries(d.value?.tripulacao ?? {}).filter(([k]) => k !== 'sarah'),
)

// Elo: hábitos registrados pela família e o brinde hídrico Terra–órbita.
const habitos = computed(() =>
  (d.value?.enviadas ?? []).filter((p) => /corrida|brinde/i.test(p.rotulo)),
)
const TITULO_BRINDE: Record<string, string> = {
  novo: 'Beba junto com a Sarah',
  fila: 'Convite guardado: sem sinal',
  enviado: 'Convite a caminho da nave',
  chegou: 'A Sarah recebeu seu convite',
  feito: 'A Sarah brindou de volta!',
}
const ETAPAS = [
  'Você convidou',
  'Chegou ao relógio da Sarah',
  'A Sarah brindou',
  'A resposta chegou aqui',
]
// Em que etapa está o brinde (0 a 4). "A Sarah brindou" só aparece quando a resposta chega.
const etapa = computed(() => {
  const b = d.value?.elo.brinde
  return b === 'feito' ? 4 : b === 'chegou' ? 2 : b === 'enviado' || b === 'fila' ? 1 : 0
})
const situacao = (p: Pacote) =>
  p.estado === 'entregue'
    ? `Entregue · ${hora(p.entregue_em)}`
    : p.estado === 'fila'
      ? 'Na fila: sem sinal'
      : `A caminho · chega em ${p.falta_s ?? '…'} s`

// Mensagens: o que a família mandou e o que chegou da nave, em ordem de tempo.
const conversa = computed(() => {
  const f = d.value
  if (!f) return []
  const minhas = f.enviadas
    .filter((p) => !/corrida|brinde/i.test(p.rotulo))
    .map((p) => ({
      de: 'eu' as const,
      texto: p.rotulo,
      quando: p.gerado_em,
      nota: situacao(p),
      fila: p.estado === 'fila',
    }))
  const dela = f.ultimas.map((u) => ({
    de: 'ela' as const,
    texto: u.frase,
    quando: u.gerado_em,
    nota: `Recebido · ${hora(u.recebido_em)}`,
    fila: false,
  }))
  return [...dela, ...minhas].sort((a, b) => a.quando.localeCompare(b.quando))
})
</script>

<template>
  <main class="familia" :class="{ embutida }">
    <div class="celular">
      <div class="tela">
        <div class="ilha" aria-hidden="true"></div>
        <div class="status">
          <span>{{ horaCelular }}</span>
          <span class="icones"
            ><Signal :size="14" aria-hidden="true" /><BatteryFull :size="15" aria-hidden="true"
          /></span>
        </div>
        <header class="app">
          <div class="logo"><Orbit :size="18" aria-hidden="true" /></div>
          <div>
            <b>Terra-Órbita</b>
            <small>Família da Sarah · Houston</small>
          </div>
        </header>

        <div class="corpo">
          <p v-if="!d" class="pc nota">Aguardando notícias da nave (a API não respondeu).</p>

          <!-- ================= Início ================= -->
          <template v-else-if="aba === 'inicio'">
            <section v-if="heroi" class="pc heroi" :class="heroi.tipo">
              <AstronautaAvatar v-if="heroi.tipo === 'ok'" class="avatar" :nivel="0" sexo="f" />
              <component
                :is="heroi.icone"
                v-else
                class="icone-heroi"
                :size="26"
                aria-hidden="true"
              />
              <div>
                <p class="olho">Sarah · Comandante</p>
                <h4>{{ heroi.titulo }}</h4>
                <p>{{ heroi.texto }}</p>
              </div>
            </section>

            <div class="mini-grade">
              <div v-for="[k, v] in outros" :key="k" class="mini">
                <UserRound :size="16" class="c-acento" aria-hidden="true" />
                <b>{{ nome(k) }}</b
                ><span>{{ v === 'bem' ? 'Está bem' : 'Com a equipe médica' }}</span>
              </div>
              <div class="mini">
                <Leaf :size="16" class="c-ok" aria-hidden="true" />
                <b>Estufa nível {{ d.elo.estufa_nivel }}</b
                ><span>{{ d.elo.estufa_pct }}% saudável</span>
              </div>
            </div>

            <section class="pc">
              <p class="olho">Últimas da nave</p>
              <div class="feed">
                <div v-for="(u, i) in d.ultimas.slice(0, 4)" :key="i" class="feed-i">
                  <Check :size="14" class="c-acento" aria-hidden="true" />
                  <span
                    >{{ u.frase }} <span class="hora">· {{ hora(u.recebido_em) }}</span></span
                  >
                </div>
                <div v-if="!d.ultimas.length" class="feed-i fraco">Nada novo por enquanto.</div>
              </div>
            </section>
            <p class="linha-status">
              <Orbit :size="14" class="c-acento" aria-hidden="true" />
              Atraso {{ d.atraso
              }}<template v-if="d.dado_de"> · notícia de {{ hora(d.dado_de) }}</template>
            </p>
          </template>

          <!-- ================= Elo ================= -->
          <template v-else-if="aba === 'elo'">
            <!-- Brinde hídrico Terra–órbita: a relação do celular com o relógio da Sarah -->
            <section class="pc brinde" :class="{ celebra: d.elo.brinde === 'feito' }">
              <p class="olho">Brinde hídrico Terra–órbita</p>
              <h4 class="com-icone">
                <Droplet :size="16" class="c-agua" aria-hidden="true" />
                {{ TITULO_BRINDE[d.elo.brinde ?? 'novo'] }}
              </h4>
              <p v-if="!d.elo.brinde">
                Beba 250 ml e convide a Sarah a beber junto. O convite chega ao relógio dela em
                {{ d.atraso }}.
              </p>
              <p v-else-if="d.elo.brinde === 'fila'" class="c-warn">
                Sem sinal agora. O convite fica guardado e sai quando o contato voltar.
              </p>
              <p v-else-if="d.elo.brinde === 'enviado'">
                Chega ao relógio da Sarah em <b>{{ d.elo.brinde_falta_s ?? '…' }} s</b>.
              </p>
              <p v-else-if="d.elo.brinde === 'chegou'">
                O convite já está no relógio dela. Quando ela beber, a resposta viaja de volta para
                cá ({{ d.atraso }}).
              </p>
              <p v-else>
                Você e a Sarah beberam juntas, cada uma no seu planeta. A estufa cresceu.
              </p>

              <ol class="etapas" aria-label="Etapas do brinde">
                <li
                  v-for="(e, n) in ETAPAS"
                  :key="e"
                  :class="{ feita: etapa > n, atual: etapa === n }"
                >
                  <i aria-hidden="true">{{ etapa > n ? '✓' : n + 1 }}</i
                  >{{ e }}
                </li>
              </ol>

              <button v-if="!d.elo.brinde" type="button" class="botao agua" @click="acao('brinde')">
                Brindar com a Sarah
              </button>
              <button
                v-else-if="d.elo.brinde === 'feito'"
                type="button"
                class="botao fantasma"
                @click="acao('brinde')"
              >
                Brindar de novo
              </button>
            </section>
            <section class="pc">
              <p class="olho">Estufa da tripulação · nível {{ d.elo.estufa_nivel }}</p>
              <h4 class="com-icone">
                <Leaf :size="16" class="c-ok" aria-hidden="true" /> Ecossistema
                {{ d.elo.estufa_pct }}% saudável
              </h4>
              <div class="barra-t"><i :style="{ width: `${d.elo.estufa_pct}%` }"></i></div>
              <p>
                Hábitos saudáveis da tripulação e das famílias fazem a estufa crescer. Ninguém joga
                sozinho e ninguém perde.
              </p>
            </section>

            <section class="pc">
              <p class="olho">Desafio da semana · família + tripulação</p>
              <h4>Corrida Terra–órbita</h4>
              <p>
                {{ d.elo.corrida }} A esteira da Sarah e as corridas da família somam no mesmo
                desafio.
              </p>
            </section>

            <section class="pc">
              <p class="olho">Hábitos da família hoje</p>
              <div class="habitos">
                <div v-for="p in habitos" :key="p.id" class="habito">
                  <span>{{ p.rotulo }}</span
                  ><b>{{
                    p.estado === 'entregue'
                      ? 'chegou à nave'
                      : p.estado === 'fila'
                        ? 'na fila'
                        : 'a caminho'
                  }}</b>
                </div>
                <p v-if="!habitos.length" class="fraco">Nenhum hábito registrado ainda.</p>
              </div>
              <button type="button" class="botao fantasma" @click="acao('corrida')">
                <Footprints :size="15" aria-hidden="true" /> Registrar corrida do Lucas · 5 km
              </button>
            </section>
          </template>

          <!-- ================= Mensagens ================= -->
          <template v-else>
            <section class="pc">
              <p class="olho">Conversa com a Sarah</p>
              <p>Cada mensagem leva {{ d.atraso }} para chegar.</p>
            </section>
            <div class="conversa">
              <div v-for="(m, i) in conversa" :key="i" class="bolha" :class="m.de">
                {{ m.texto }}<small :class="{ fila: m.fila }">{{ m.nota }}</small>
              </div>
              <div v-if="!conversa.length" class="bolha ela">
                Oi, família! Treino feito por hoje.<small>Ontem · 21:10</small>
              </div>
            </div>
            <button type="button" class="botao" @click="acao('mensagem')">
              <Mic :size="15" aria-hidden="true" /> Enviar áudio do Lucas
            </button>
          </template>

          <p v-if="feed.erro.value" class="pc erro" role="alert">{{ feed.erro.value }}</p>
        </div>

        <nav class="abas" aria-label="Seções do app">
          <button
            v-for="a in ABAS"
            :key="a.id"
            type="button"
            :aria-current="a.id === aba"
            @click="aba = a.id"
          >
            <component :is="a.icone" :size="19" aria-hidden="true" />{{ a.rotulo }}
          </button>
        </nav>
      </div>
    </div>
    <p v-if="!embutida" class="legenda">
      A família recebe frases prontas, com o atraso da missão. Nunca sinais vitais, diagnóstico,
      humor ou ciclo.
    </p>
  </main>
</template>

<style scoped>
.familia {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 16px;
}
.familia.embutida {
  padding: 8px 0;
  zoom: 0.92;
}
.legenda {
  max-width: 360px;
  font-size: 12px;
  line-height: 1.45;
  text-align: center;
  color: var(--texto-fraco);
}

/* Moldura do celular, como na demo */
.celular {
  width: 340px;
  max-width: 100%;
  height: 700px;
  padding: 10px;
  border-radius: 52px;
  background: linear-gradient(160deg, #252e42, #0d121c 70%);
  box-shadow:
    inset 0 0 0 1px #2e3850,
    0 24px 60px rgba(0, 0, 0, 0.6);
}
.tela {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border-radius: 42px;
  background: #05070e;
}
.ilha {
  position: absolute;
  top: 10px;
  left: 50%;
  z-index: 3;
  width: 96px;
  height: 27px;
  border-radius: 20px;
  background: #000;
  transform: translateX(-50%);
}
.status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 28px 4px;
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.icones {
  display: inline-flex;
  gap: 4px;
}
.app {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px 10px;
}
.logo {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.35), rgba(0, 229, 255, 0.25));
  color: #fff;
}
.app b {
  display: block;
  font-size: 16px;
  line-height: 1.1;
}
.app small {
  font-size: 11.5px;
  color: var(--texto-fraco);
}
.corpo {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 16px 16px;
  overflow-y: auto;
  scrollbar-width: thin;
}
.abas {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding: 8px 8px 20px;
  border-top: 1px solid var(--linha);
  background: #070a13;
}
.abas button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 4px;
  border: 0;
  background: transparent;
  color: var(--texto-fraco);
  font-size: 11px;
  cursor: pointer;
}
.abas button[aria-current='true'] {
  color: var(--acento);
}
.abas button:focus-visible,
.botao:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}

/* Cartões do app */
.pc {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
.pc h4 {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.25;
}
.pc p {
  margin-top: 4px;
  font-size: 12.5px;
  line-height: 1.45;
  color: var(--texto-medio);
}
.pc.erro {
  color: #fecaca;
  border-color: rgba(239, 68, 68, 0.5);
}
.olho {
  margin: 0 0 4px !important;
  font: 500 10px var(--mono) !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--texto-fraco) !important;
}
.com-icone {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.heroi {
  display: flex;
  gap: 12px;
  align-items: center;
}
.heroi.ok {
  border-color: rgba(16, 185, 129, 0.35);
  background: linear-gradient(140deg, rgba(16, 185, 129, 0.12), var(--superficie) 60%);
}
.heroi.ok .avatar {
  flex: none;
  width: 54px;
  color: var(--ok);
}
.heroi.medico {
  align-items: flex-start;
  border-color: rgba(139, 92, 246, 0.45);
  background: linear-gradient(140deg, rgba(139, 92, 246, 0.16), var(--superficie) 60%);
}
.heroi.medico .icone-heroi {
  color: #c4b5fd;
}
.heroi.escuro {
  align-items: flex-start;
  border-color: rgba(245, 158, 11, 0.4);
  background: linear-gradient(140deg, rgba(245, 158, 11, 0.1), var(--superficie) 60%);
}
.heroi.escuro .icone-heroi {
  color: var(--warn);
}
.icone-heroi {
  flex: none;
  margin-top: 2px;
}
.mini-grade {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.mini {
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
.mini b {
  display: block;
  margin-top: 4px;
  font-size: 14px;
}
.mini span {
  font-size: 11px;
  color: var(--texto-fraco);
}
.feed {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.feed-i {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 12.5px;
  line-height: 1.4;
  color: var(--texto-medio);
}
.feed-i svg {
  flex: none;
  margin-top: 2px;
}
.hora,
.fraco {
  color: var(--texto-fraco);
}
.linha-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--texto-medio);
}
.barra-t {
  height: 7px;
  margin-top: 8px;
  border-radius: 9px;
  background: #1b2437;
  overflow: hidden;
}
.barra-t i {
  display: block;
  height: 100%;
  border-radius: 9px;
  background: var(--ok);
  transition: width 0.6s;
}
.habitos {
  margin-top: 6px;
}
.habito {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 9px 0;
  border-top: 1px solid var(--linha);
  font-size: 12.5px;
}
.habito:first-child {
  border-top: 0;
}
.habito b {
  color: var(--acento);
  font-weight: 600;
  white-space: nowrap;
}
.habitos .fraco {
  font-size: 12.5px;
}
.botao {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  margin-top: 10px;
  padding: 10px 14px;
  border: 0;
  border-radius: 12px;
  background: var(--acento);
  color: #03141a;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.botao.agua {
  background: var(--agua);
  color: #fff;
}
.botao.fantasma {
  border: 1px solid var(--linha-forte);
  background: var(--superficie-2);
  color: var(--texto);
}
.celebra {
  text-align: center;
  border-color: rgba(16, 185, 129, 0.5);
  background: linear-gradient(140deg, rgba(16, 185, 129, 0.18), var(--superficie));
}
.conversa {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bolha {
  max-width: 86%;
  padding: 9px 12px;
  border-radius: 16px;
  font-size: 12.5px;
  line-height: 1.38;
}
.bolha.eu {
  align-self: flex-end;
  border-bottom-right-radius: 5px;
  background: #1e2a4a;
}
.bolha.ela {
  align-self: flex-start;
  border: 1px solid var(--linha);
  border-bottom-left-radius: 5px;
  background: var(--superficie);
}
.bolha small {
  display: block;
  margin-top: 4px;
  font: 500 10.5px var(--mono);
  color: var(--texto-fraco);
}
.bolha small.fila {
  color: var(--warn);
}
.c-agua {
  color: var(--agua);
}
.etapas {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
  color: var(--texto-fraco);
}
.etapas li {
  display: flex;
  align-items: center;
  gap: 8px;
}
.etapas i {
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid var(--linha-forte);
  font: 600 10px var(--mono);
  font-style: normal;
}
.etapas li.feita {
  color: var(--texto);
}
.etapas li.feita i {
  border-color: transparent;
  background: var(--ok);
  color: #022c1f;
}
.etapas li.atual {
  color: var(--acento);
}
.etapas li.atual i {
  border-color: var(--acento);
}
.brinde.celebra .etapas {
  align-items: center;
}
</style>
