<script setup lang="ts">
// Console de Houston: a Terra vê o passado (o retrato que já atravessou o link).
// Com médico a bordo, parecer é revisão; sem médico a bordo, a médica de voo decide daqui.
import { computed, ref, watch } from 'vue'
import ListaTripulacao from '../components/ListaTripulacao.vue'
import PacienteHeader from '../components/PacienteHeader.vue'
import GradeSinais from '../components/GradeSinais.vue'
import CardSilhueta from '../components/CardSilhueta.vue'
import ChatCosmo from '../components/ChatCosmo.vue'
import TrilhaCosmo from '../components/TrilhaCosmo.vue'
import EventoHouston from '../components/EventoHouston.vue'
import StatusChip from '../components/StatusChip.vue'
import { pedir, paraTripulante, type ApiTripulante } from '@/servicos/api'
import { usarConsulta } from '@/servicos/consulta'
import { ajustarEquipe, hora, num, sono } from '@/servicos/formato'
import type { Trilha } from '@/servicos/trilha'
import type { Tripulante } from '@/mocks/tripulacao'

/* eslint-disable @typescript-eslint/no-explicit-any */
interface Console {
  missao: Record<string, any>
  dado_de: string | null
  tripulantes: ApiTripulante[]
  eventos: Record<string, any>[]
  compartilhados: Record<string, any>[]
  recebidos: Record<string, any>[]
  enviados: Record<string, any>[]
  trilha_cosmo: Trilha
}

const atual = ref('sarah')
const consola = usarConsulta<Console>(() => '/houston/console')
const serie = usarConsulta<{ gerada_em: string; fc: number }[]>(() => `/houston/serie/${atual.value}?segundos=60`)
const d = computed(() => consola.dados.value)
const m = computed(() => d.value?.missao ?? {})
const terra = computed(() => m.value.equipe?.local === 'terra')
watch(() => d.value?.missao.equipe, (eq) => ajustarEquipe(eq))

// Os componentes do painel recebem o retrato atrasado no mesmo formato. Houston não vê
// saúde hormonal: ela chega só no quadro "Compartilhado só com você", com consentimento.
const tripulantes = computed<Tripulante[]>(() =>
  (d.value?.tripulantes ?? []).map((t) => ({
    ...paraTripulante(t, { missao: m.value as any, avisos_compartilhados: [] }),
    destaque: `dado de ${hora(t.gerada_em, true)}`,
    hormonal: undefined,
  })),
)
const tripulante = computed(() => tripulantes.value.find((t) => t.id === atual.value) ?? tripulantes.value[0])
const bruto = computed(() => d.value?.tripulantes.find((t) => t.tripulante_id === atual.value))

const alerta = computed(() => d.value?.eventos.find((e) => e.tipo === 'arritmia' && !['resolvido', 'encerrado'].includes(e.estado)))
const banner = computed(() => {
  if (!d.value) return null
  const mm = m.value
  if (mm.blackout)
    return {
      classe: 'semsinal',
      texto:
        `Sem sinal desde ${hora(d.value.dado_de, true)}. ${mm.motivo_blackout}. Mostrando o último dado recebido; o contato volta em ` +
        `${mm.volta_em}. ` +
        (terra.value
          ? `Sem médico a bordo, o CMO segue só os protocolos pré-aprovados. Daqui nada sai; na FA, vale a ordem permanente ${mm.ordem_permanente?.id} que você assinou antes do voo.`
          : 'A nave segue decidindo a bordo.'),
    }
  const a = alerta.value
  if (a)
    return {
      classe: 'alerta',
      texto:
        `Alerta médico de ${a.nome}. Isto aconteceu a bordo às ${hora(a.gerado_em, true)} e chegou aqui às ${hora(a.recebido_em, true)}: ` +
        (a.medico_local !== 'terra'
          ? 'a tripulação já está agindo.'
          : a.medicacao?.via === 'ordem_permanente'
            ? 'sem sinal, o CMO usou a ordem permanente; a revisão é sua, por parecer.'
            : 'não há médico a bordo, e a decisão é sua.'),
    }
  if (mm.atraso_real_s >= 1)
    return {
      classe: '',
      texto: `Você está vendo o passado: estes dados saíram da nave há ${mm.atraso_txt}${mm.comprimido ? ' (na demo, 1 min de atraso = 1 s)' : ''}. Link: ${mm.link}.`,
    }
  return { classe: '', texto: `Dados quase em tempo real via ${mm.link}.` }
})

// Frequência cardíaca recebida nos últimos 60 s
const spark = computed(() => {
  const pts = serie.dados.value ?? []
  if (pts.length < 2) return null
  const v = pts.map((p) => p.fc)
  const lo = Math.min(...v) - 2
  const hi = Math.max(...v) + 2
  const d = v.map((x, i) => `${i ? 'L' : 'M'}${((i / (v.length - 1)) * 600).toFixed(1)} ${(66 - ((x - lo) / (hi - lo)) * 62).toFixed(1)}`).join(' ')
  return { d, min: Math.min(...v), max: Math.max(...v) }
})

function enviarParecer(evento_id: string, texto: string) {
  return consola.executar(() => pedir('/houston/parecer', { evento_id, texto }))
}
function decidirTerra(corpo: { evento_id: string; acao: string; dose?: string; pin?: string; detalhe?: Record<string, unknown> }) {
  return consola.executar(() => pedir('/houston/decisao', corpo))
}
function marcarConversa(evento_id: string) {
  return decidirTerra({ evento_id, acao: 'marcar_conversa', detalhe: { hora: '19:00' } })
}
function situacao(x: any): { texto: string; classe: string } {
  if (x.estado === 'aplicada') return { texto: `chegou a bordo às ${hora(x.chegou_em, true)} e foi aplicada`, classe: 'c-ok' }
  if (x.estado === 'não aplicada') return { texto: `chegou, mas não se aplicou: ${x.motivo}`, classe: 'c-warn' }
  if (x.pacote_estado === 'fila') return { texto: 'na fila: sem sinal', classe: 'c-warn' }
  return { texto: `a caminho · chega a bordo em ${x.falta_s} s`, classe: '' }
}
const tempoPacote = (p: any) =>
  p.estado === 'entregue'
    ? `gerado ${hora(p.gerado_em, true)} · recebido ${hora(p.entregue_em, true)}`
    : p.estado === 'fila'
      ? 'na fila: sem sinal'
      : `a caminho · chega em ${p.falta_s} s`
</script>

<template>
  <header class="topo">
    <div>
      <h1>{{ terra ? `Mission Control · ${m.equipe?.medico_nome}` : 'Mission Control · Houston' }}</h1>
      <p class="subtitulo">{{ terra ? 'Médica responsável · não há médico a bordo' : 'Console do flight surgeon' }}</p>
    </div>
    <div class="selos">
      <StatusChip :variante="m.blackout ? 'warn' : 'normal'">{{ m.blackout ? 'Sem sinal' : `Atraso ${m.atraso_txt ?? '—'}` }}</StatusChip>
      <StatusChip>Hora da nave {{ hora(m.hora_nave, true) }}</StatusChip>
      <StatusChip>Dado de {{ hora(d?.dado_de, true) }}</StatusChip>
    </div>
  </header>
  <p v-if="banner" class="banner" :class="banner.classe">{{ banner.texto }}</p>
  <p v-if="!d" class="aviso-faixa offline">Aguardando a API. Houston precisa dela para receber o que a nave manda.</p>
  <p v-if="consola.erro.value" class="aviso-faixa erro" role="alert">{{ consola.erro.value }}</p>

  <div v-if="d" class="layout">
    <div class="esquerda pilha">
      <ListaTripulacao v-if="tripulantes.length" v-model="atual" :tripulantes="tripulantes" />
      <p v-else class="nota">Nenhum dado recebido ainda.</p>
      <section class="cartao">
        <h3>Modo de autonomia</h3>
        <p class="nota">{{ m.autonomia }}</p>
        <div v-if="m.ordem_permanente?.em_vigor" class="caixa ordem">
          <h5>Ordem permanente {{ m.ordem_permanente.id }} · em vigor</h5>
          <p class="nota">
            Assinada por você em {{ m.ordem_permanente.assinada_em }}: {{ m.ordem_permanente.dose }} na FA, só sem sinal, depois das ações
            seguras e com a FA ainda presente.
            <b v-if="m.blackout">Vale agora: a nave está sem sinal.</b>
            <template v-else>Com sinal, quem decide é você, por este console.</template>
          </p>
        </div>
      </section>
    </div>

    <main class="pilha centro">
      <template v-if="tripulante && bruto">
        <PacienteHeader :tripulante="tripulante" />
        <p class="meta">
          Gerado a bordo às {{ hora(bruto.gerada_em, true) }}. A hora de geração prevalece sobre a hora em que a Terra recebeu.
        </p>
        <section class="cartao">
          <span class="etiqueta">Frequência cardíaca · últimos 60 s recebidos</span>
          <template v-if="spark">
            <svg class="spark" viewBox="0 0 600 70" preserveAspectRatio="none" role="img" :aria-label="`FC recebida, de ${spark.min} a ${spark.max} bpm`">
              <path :d="spark.d" />
            </svg>
            <p class="meta">mínima {{ spark.min }} · máxima {{ spark.max }} bpm</p>
          </template>
          <p v-else class="nota">Ainda sem pontos suficientes.</p>
        </section>
        <div class="sinais-e-corpo">
          <GradeSinais :tripulante="tripulante" />
          <CardSilhueta :tripulante="tripulante" />
        </div>
        <div class="kv">
          <div><span>Pele</span><b>{{ num(bruto.temp_pele, 1) }} °C</b></div>
          <div><span>Sono</span><b>{{ sono(bruto.sono_min_noite) }}</b></div>
          <div><span>Dose hoje</span><b>{{ num(bruto.dose_msv_dia, 2) }} mSv</b></div>
        </div>
        <p class="nota">
          Modelos a bordo nesse instante: M1 {{ bruto.m1?.versao_modelo }}
          <template v-if="bruto.m1?.classe">({{ bruto.m1.classe }}, P(FA) {{ num(bruto.m1.prob_fa, 2) }})</template>
          <template v-else>(não disparou: sinal suspeito)</template>
          · M2 {{ bruto.m2?.versao_modelo }} ({{ bruto.m2?.qualidade }}) · M3 {{ bruto.isolation_forest?.versao_modelo }}.
        </p>
      </template>

      <h2 class="secao">Eventos que já chegaram</h2>
      <EventoHouston
        v-for="e in d.eventos"
        :key="e.id"
        :evento="e"
        :missao="m"
        @parecer="enviarParecer"
        @decidir="decidirTerra"
      />
      <p v-if="!d.eventos.length" class="cartao nota">Nenhum evento clínico chegou ainda.</p>

      <template v-if="terra || d.compartilhados.length">
        <h2 class="secao c-roxo">Compartilhado só com você</h2>
        <article v-for="c in d.compartilhados" :key="c.evento_id" class="cartao roxo">
          <h4>{{ c.nome }} · {{ c.tipo === 'bem_estar' ? 'bem-estar' : c.tipo === 'ciclo' ? 'ciclo' : 'não está bem' }}</h4>
          <p>{{ c.resumo }}</p>
          <template v-if="c.tipo === 'bem_estar'">
            <p v-for="x in (c.minhas_decisoes ?? []).filter((y: any) => y.acao === 'marcar_conversa')" :key="x.enviada_em">
              Você enviou às {{ hora(x.enviada_em, true) }}: <b>{{ x.rotulo }}</b> · <span :class="situacao(x).classe">{{ situacao(x).texto }}</span>.
            </p>
            <div v-if="!(c.minhas_decisoes ?? []).some((y: any) => y.acao === 'marcar_conversa')" class="acoes">
              <button type="button" class="btn sm" :disabled="m.blackout" @click="marcarConversa(c.evento_id)">Marcar conversa privada às 19:00</button>
            </div>
          </template>
          <p class="meta">
            consentimento da própria pessoa · gerado {{ hora(c.gerado_em, true) }} · recebido {{ hora(c.recebido_em, true) }} · o CMO, o resto de
            Houston e a família não veem
          </p>
        </article>
        <p v-if="!d.compartilhados.length" class="cartao nota">
          Nada compartilhado com você. Sem consentimento, saúde mental e ciclo não saem do relógio.
        </p>
      </template>

      <h2 class="secao">Recebido da nave</h2>
      <section class="cartao">
        <ul v-if="d.recebidos.length" class="pacotes">
          <li v-for="(p, i) in d.recebidos" :key="i" :class="`p${p.prioridade}`">
            <time>{{ tempoPacote(p) }} · P{{ p.prioridade }}</time>{{ p.rotulo }}
          </li>
        </ul>
        <p v-else class="nota">Nada recebido ainda nesta sessão.</p>
        <template v-if="d.enviados.length">
          <p class="etiqueta enviado">Enviado para a nave</p>
          <ul class="pacotes">
            <li v-for="(p, i) in d.enviados" :key="i" :class="`p${p.prioridade}`">
              <time>{{ tempoPacote(p) }} · P{{ p.prioridade }}</time>{{ p.rotulo }}
            </li>
          </ul>
        </template>
      </section>

      <h2 class="secao">Trilha da Cosmo · auditoria</h2>
      <div class="cartao"><TrilhaCosmo :trilha="d.trilha_cosmo" superficie="houston" /></div>

      <section class="cartao">
        <h3>O que não chega aqui</h3>
        <p class="nota">
          {{
            terra
              ? `Sem médico a bordo, saúde mental e ciclo chegam só para a ${m.equipe?.medico_nome}, com consentimento, no quadro “Compartilhado só com você”. O resto de Houston e a família não veem. Sugestões de nível 1 do relógio ficam na nave.`
              : 'Aviso de saúde mental e do ciclo ficam na nave. Houston não tem botão de protocolo nem de medicação: parecer é revisão, não comando.'
          }}
        </p>
      </section>
    </main>

    <ChatCosmo
      v-if="tripulante"
      class="chat"
      :tripulante="tripulante"
      superficie="houston"
      titulo="Cosmo Terra · copiloto"
      saudacao="Sou a Cosmo Terra. Só sei o que já atravessou o link: cada resposta diz de quando é o dado. Com médico a bordo, parecer é revisão; sem médico a bordo, a decisão médica é sua."
    />
  </div>
</template>

<style scoped>
.topo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 24px 24px 16px;
}
.topo h1 {
  font-size: 20px;
}
.subtitulo {
  margin-top: 4px;
  font-size: 13px;
  color: #c4b5fd;
}
.banner {
  margin: 0 24px 12px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid rgba(196, 181, 253, 0.35);
  background: rgba(139, 92, 246, 0.08);
  font-size: 13px;
  line-height: 1.5;
}
.banner.alerta {
  border-color: rgba(239, 68, 68, 0.55);
  background: rgba(239, 68, 68, 0.1);
}
.banner.semsinal {
  border-color: rgba(245, 158, 11, 0.55);
  background: rgba(245, 158, 11, 0.08);
}
.aviso-faixa {
  margin: 0 24px 12px;
}
.layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 360px;
  border-top: 1px solid var(--linha);
}
.esquerda {
  padding-bottom: 16px;
  border-right: 1px solid var(--linha);
}
.esquerda :deep(.lista) {
  border-right: 0;
}
.esquerda > .cartao {
  margin: 0 10px;
}
.centro {
  padding: 16px 24px;
}
.sinais-e-corpo {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  align-items: start;
  gap: 12px;
}
.spark {
  display: block;
  width: 100%;
  height: 70px;
  margin-top: 6px;
}
.spark path {
  fill: none;
  stroke: #c4b5fd;
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}
.secao {
  margin-top: 6px;
  font-size: 15px;
  font-weight: 600;
}
.enviado {
  display: block;
  margin: 12px 0 6px;
}
.chat {
  align-self: start;
  position: sticky !important;
  top: 52px;
  height: calc(100vh - 64px);
  min-height: 520px;
}
@media (max-width: 1180px) {
  .layout {
    grid-template-columns: 200px minmax(0, 1fr);
  }
  .chat {
    grid-column: 1 / -1;
    position: relative !important;
    height: 460px;
    border-left: 0;
    border-top: 1px solid var(--linha);
  }
}
@media (max-width: 820px) {
  .topo {
    padding: 16px;
  }
  .banner,
  .aviso-faixa {
    margin: 0 16px 12px;
  }
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .esquerda {
    border-right: 0;
    border-bottom: 1px solid var(--linha);
  }
  .esquerda :deep(.lista) {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .esquerda :deep(.item) {
    width: auto;
    flex: 1 1 140px;
  }
  .centro {
    padding: 14px 16px;
  }
  .sinais-e-corpo {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
