<script setup lang="ts">
import { computed } from 'vue'
import { Lock, Radiation } from 'lucide-vue-next'
import SilhuetaCorpo from './SilhuetaCorpo.vue'
import type { NivelSaude, Tripulante } from '@/mocks/tripulacao'

const props = defineProps<{ tripulante: Tripulante }>()

const NIVEL = ['ótimo', 'atenção', 'crítico']
const INTENSIDADE = ['baixo', 'moderado', 'alto']
const LIMITE_RADIACAO_MSV = 600 // limite de carreira da NASA, igual para todos desde 2022


const FASES: [string, number, number][] = [
  ['Menstrual', 1, 5],
  ['Folicular', 6, 13],
  ['Ovulação', 14, 15],
  ['Lútea', 16, 28],
]

const linhas = computed(() => {
  const t = props.tripulante
  const c = t.corpo
  const agua = Math.round((t.vitais.agua / t.vitais.aguaMeta) * 100)
  return [
    { nivel: c.cerebro, nome: 'Cérebro', texto: `estresse ${INTENSIDADE[c.cerebro]}` },
    {
      nivel: c.coracao,
      nome: 'Coração',
      texto: t.ritmo === 'fa' ? 'ritmo irregular' : `ritmo regular · ${NIVEL[c.coracao]}`,
    },
    { nivel: c.pulmoes, nome: 'Pulmões', texto: NIVEL[c.pulmoes]! },
    { nivel: c.rins, nome: 'Rins', texto: `risco ${INTENSIDADE[c.rins]} · água ${agua}%` },
  ] satisfies { nivel: NivelSaude; nome: string; texto: string }[]
})

const hormonal = computed(() => props.tripulante.hormonal)
const estadoHormonal = computed(() =>
  !hormonal.value ? 'nenhum' : hormonal.value.compartilhado ? 'compartilhado' : 'privado',
)
const textoHormonal = computed(() => {
  const h = hormonal.value
  if (!h) return ''
  if (!h.compartilhado) return `Privado · ${props.tripulante.nome} decide no relógio`
  return h.dia ? `${h.fase} · dia ${h.dia} · sem alerta` : `${h.metodo} · ${h.fase.toLowerCase()}`
})

const ciclo = computed(() => {
  const h = hormonal.value
  if (!h?.compartilhado || !h.dia || !h.duracao) return null
  return {
    dia: h.dia,
    duracao: h.duracao,
    fase: h.fase,
    efeito: h.efeito,
    marcador: `${(((h.dia - 0.5) / h.duracao) * 100).toFixed(1)}%`,
    fases: FASES.map(([nome, ini, fim]) => ({
      nome,
      ini,
      fim,
      atual: h.dia! >= ini && h.dia! <= fim,
    })),
  }
})

const rotulo = computed(
  () =>
    `Silhueta de ${props.tripulante.nome}: ` +
    linhas.value.map((l) => `${l.nome} ${l.texto}`).join(', ') +
    (hormonal.value ? `, Saúde hormonal ${textoHormonal.value}` : ''),
)

const doseHoje = computed(() => props.tripulante.radiacao.hojeMsv.toFixed(2).replace('.', ','))
</script>

<template>
  <section class="card" aria-label="Silhueta e órgãos">
    <SilhuetaCorpo
      :sexo="tripulante.sexo"
      :orgaos="tripulante.corpo"
      :hormonal="estadoHormonal"
      :rotulo="rotulo"
    />

    <ul class="legenda">
      <li v-for="l in linhas" :key="l.nome">
        <i :class="`n${l.nivel}`"></i>
        <b>{{ l.nome }}</b>
        <small>{{ l.texto }}</small>
      </li>
      <li v-if="hormonal">
        <i v-if="hormonal.compartilhado" class="ciclo"></i>
        <Lock v-else :size="11" class="icone-ciclo" aria-hidden="true" />
        <b>Saúde hormonal</b>
        <small>{{ textoHormonal }}</small>
      </li>
      <li>
        <Radiation :size="11" class="icone-radiacao" aria-hidden="true" />
        <b>Radiação</b>
        <small>
          {{ doseHoje }} mSv hoje · missão {{ tripulante.radiacao.missaoMsv }}/{{ LIMITE_RADIACAO_MSV }}
        </small>
      </li>
      <li class="sensores">
        <i></i>
        <small>Sensores<template v-if="hormonal"> (rosa tracejado: conceito)</template></small>
      </li>
    </ul>

    <div v-if="ciclo" class="barra-ciclo">
      <div
        class="trilho"
        role="img"
        :aria-label="`Ciclo de ${ciclo.duracao} dias: dia ${ciclo.dia}, fase ${ciclo.fase.toLowerCase()}`"
      >
        <span
          v-for="f in ciclo.fases"
          :key="f.nome"
          :class="{ atual: f.atual }"
          :style="{ flex: f.fim - f.ini + 1 }"
          :title="`${f.nome} · dias ${f.ini} a ${f.fim}`"
        ></span>
        <i :style="{ left: ciclo.marcador }"></i>
      </div>
      <b>Dia {{ ciclo.dia }} de {{ ciclo.duracao }} · fase {{ ciclo.fase.toLowerCase() }}</b>
      <small>{{ ciclo.efeito }}. Linha de base por fase: no padrão dela.</small>
    </div>
  </section>
</template>

<style scoped>
.card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px 14px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}

.legenda {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
  min-width: 0;
  font-size: 12px;
}
.legenda li {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  align-items: center;
  gap: 0 8px;
}
.legenda i {
  justify-self: center;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.legenda b {
  font-weight: 600;
}
.legenda small {
  grid-column: 2;
  font-size: 11px;
  line-height: 1.35;
  color: var(--texto-fraco);
}
.n0 {
  background: var(--ok);
}
.n1 {
  background: var(--warn);
}
.n2 {
  background: var(--crit);
}
.legenda i.ciclo {
  background: var(--ciclo);
}
.icone-ciclo {
  color: var(--ciclo);
  justify-self: center;
}
.icone-radiacao {
  color: var(--warn);
  justify-self: center;
}
.sensores i {
  background: #05070e;
  box-shadow: inset 0 0 0 1.5px var(--acento);
}

.barra-ciclo {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 10px;
  border-top: 1px solid var(--linha);
}
.trilho {
  position: relative;
  display: flex;
  gap: 2px;
  height: 7px;
  margin-bottom: 3px;
}
.trilho span {
  border-radius: 3px;
  background: var(--ciclo);
  opacity: 0.28;
}
.trilho span.atual {
  opacity: 1;
}
.trilho i {
  position: absolute;
  top: -3px;
  width: 3px;
  height: 13px;
  margin-left: -1.5px;
  border-radius: 2px;
  background: #fff;
  box-shadow: 0 0 0 2px #05070e;
}
.barra-ciclo b {
  font-size: 12px;
  font-weight: 600;
  color: #f9a8d4;
}
.barra-ciclo small {
  font-size: 11px;
  line-height: 1.35;
  color: var(--texto-fraco);
}
</style>
