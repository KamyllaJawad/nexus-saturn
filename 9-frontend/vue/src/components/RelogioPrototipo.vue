<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Heart } from 'lucide-vue-next'
import AstronautaAvatar from './AstronautaAvatar.vue'
import type { NivelSaude } from '@/mocks/tripulacao'
import type { Sexo } from '@/silhueta/contorno'
import type { CicloNoRelogio, EstadoRelogio } from '@/mocks/relogio'

const props = withDefaults(
  defineProps<{
    nivel: NivelSaude
    sexo: Sexo
    estado: EstadoRelogio
    ciclo?: CicloNoRelogio
    missao?: string
  }>(),
  { missao: 'LEO' },
)

const NOMES = ['Ótimo', 'Atenção', 'Crítico']
const CIRCUNFERENCIA = 2 * Math.PI * 47
const traco = computed(() => {
  const cheio = (Math.max(0, Math.min(100, props.estado.homeostase)) / 100) * CIRCUNFERENCIA
  return `${cheio} ${CIRCUNFERENCIA}`
})


const subtitulo = computed(() => {
  const c = props.ciclo
  if (props.nivel === 0 && c && 'dia' in c) return `Fase ${c.fase} · no seu padrão`
  return props.estado.motivo
})

const chipCiclo = computed(() => {
  const c = props.ciclo
  if (!c) return null
  return 'dia' in c ? { valor: `D${c.dia}`, rotulo: 'ciclo' } : { valor: c.metodo, rotulo: '' }
})


const hora = ref('')
let relogio = 0
function atualizarHora() {
  hora.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
onMounted(() => {
  atualizarHora()
  relogio = window.setInterval(atualizarHora, 10_000)
})
onUnmounted(() => window.clearInterval(relogio))
</script>

<template>
  <div class="aro" :class="`n${nivel}`">
    <div class="botao" aria-hidden="true"></div>
    <div class="tela" role="img" :aria-label="`Relógio: ${NOMES[nivel]}, ${subtitulo}, FC ${estado.fc} bpm, SpO₂ ${estado.spo2}%`">
      <svg class="anel" viewBox="0 0 100 100" aria-hidden="true">
        <circle class="trilho" cx="50" cy="50" r="47" />
        <circle class="progresso" cx="50" cy="50" r="47" :stroke-dasharray="traco" transform="rotate(-90 50 50)" />
      </svg>

      <div class="conteudo">
        <div class="topo">
          <span class="hora">{{ hora }}</span>
          <span class="missao">{{ missao }}</span>
        </div>
        <AstronautaAvatar :nivel="nivel" :sexo="sexo" />
        <div class="estado">{{ NOMES[nivel] }}</div>
        <div class="subtitulo">{{ subtitulo }}</div>
        <div class="chips">
          <span class="chip"><Heart :size="11" class="coracao" aria-hidden="true" /><b>{{ estado.fc }}</b> bpm</span>
          <span class="chip"><span class="o2">O₂</span><b>{{ estado.spo2 }}</b> %</span>
          <span v-if="chipCiclo" class="chip ciclo">♀ <b>{{ chipCiclo.valor }}</b> {{ chipCiclo.rotulo }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.aro {
  --cor: var(--ok);
  position: relative;
  width: 320px;
  height: 320px;
  padding: 16px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 22%, #2b3448, #0e131d 62%);
  box-shadow: inset 0 0 0 1px #2e3850, 0 24px 50px rgba(0, 0, 0, 0.65);
}
.n1 {
  --cor: var(--warn);
}
.n2 {
  --cor: var(--crit);
}

.botao {
  position: absolute;
  top: 50%;
  right: -9px;
  width: 13px;
  height: 40px;
  transform: translateY(-50%);
  border-radius: 5px;
  background: linear-gradient(90deg, #3a4560, #1d2433);
  box-shadow: inset 0 0 0 1px #46526f;
}

.tela {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  background: #000;
}

.anel {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.trilho {
  fill: none;
  stroke: #1a2233;
  stroke-width: 1.4;
}
.progresso {
  fill: none;
  stroke: var(--cor);
  stroke-width: 1.4;
  stroke-linecap: round;
  filter: drop-shadow(0 0 1.5px var(--cor));
  transition: stroke-dasharray 0.6s;
}

.conteudo {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding-bottom: 30px;
  text-align: center;
}

.conteudo :deep(.astro) {
  width: 76px;
}

.topo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}
.hora {
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.missao {
  padding: 1px 7px;
  border-radius: 99px;
  border: 1px solid var(--linha-forte);
  font-size: 10px;
  color: var(--texto-fraco);
}

.estado {
  margin-top: 4px;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--cor);
}
.subtitulo {
  font-size: 11px;
  color: #a6b2c7;
}

.chips {
  display: flex;
  justify-content: center;
  gap: 4px;
  margin-top: 6px;
  max-width: 236px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 7px;
  border-radius: 99px;
  background: #101a30;
  border: 1px solid var(--linha);
  font-size: 9.5px;
  white-space: nowrap;
  color: var(--texto-fraco);
}
.chip b {
  font-size: 12px;
  color: var(--texto);
}
.coracao {
  color: var(--crit);
}
.o2 {
  color: var(--acento);
  font-weight: 600;
}
.chip.ciclo {
  border-color: rgba(196, 181, 253, 0.35);
  background: rgba(139, 92, 246, 0.12);
  color: #c4b5fd;
}
</style>
