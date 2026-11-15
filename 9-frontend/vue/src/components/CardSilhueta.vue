<script setup lang="ts">
import { computed } from 'vue'
import { Lock, Radiation } from 'lucide-vue-next'
import SilhuetaCorpo from './SilhuetaCorpo.vue'
import type { NivelSaude, Tripulante } from '@/mocks/tripulacao'

const props = defineProps<{ tripulante: Tripulante }>()

const NIVEL = ['ótimo', 'atenção', 'crítico']
const INTENSIDADE = ['baixo', 'moderado', 'alto']
const LIMITE_RADIACAO_MSV = 600 // limite de carreira da NASA, igual para todos desde 2022

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
  return 'Compartilhado: cuidado leve, sem alerta'
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

</style>
