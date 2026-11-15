<script setup lang="ts">
import { computed } from 'vue'
import { Droplet, Leaf, Zap } from 'lucide-vue-next'
import { HABITOS, MISSAO, type FaseBrinde } from '@/mocks/familia'

const props = defineProps<{
  estufa: { nivel: number; pct: number }
  desafio: { km: number; meta: number }
  brinde: FaseBrinde | null
  brindeNaFila: boolean
}>()

const emit = defineEmits<{ correr: []; brindar: [] }>()

const kmTexto = computed(() => props.desafio.km.toFixed(1).replace('.', ','))
const progressoDesafio = computed(() => `${Math.min(100, (props.desafio.km / props.desafio.meta) * 100).toFixed(1)}%`)
</script>

<template>
  <div class="pc">
    <div class="sobretitulo">Estufa da tripulação · nível {{ estufa.nivel }}</div>
    <h4 class="com-icone"><Leaf :size="15" class="verde" aria-hidden="true" /> Ecossistema {{ estufa.pct }}% saudável</h4>
    <div class="barra"><i :style="{ width: `${estufa.pct}%` }"></i></div>
    <p>Hábitos saudáveis da tripulação e das famílias fazem a estufa crescer.</p>
  </div>

  <div class="pc">
    <div class="sobretitulo">Desafio da semana · família + tripulação</div>
    <h4>Corrida Terra–órbita</h4>
    <div class="barra"><i class="corrida" :style="{ width: progressoDesafio }"></i></div>
    <p>{{ kmTexto }} de {{ desafio.meta }} km somando a esteira da Sarah e as corridas da família.</p>
  </div>

  <div class="pc">
    <div class="sobretitulo">Hábitos da família hoje</div>
    <div class="habitos">
      <div v-for="h in HABITOS" :key="h.texto" class="habito">
        <span>{{ h.texto }}</span><b>{{ h.efeito }}</b>
      </div>
    </div>
    <button type="button" class="botao secundario" @click="emit('correr')">
      <Zap :size="15" aria-hidden="true" /> Registrar corrida do Lucas · 5 km
    </button>
  </div>

  <div v-if="!brinde" class="pc">
    <h4 class="com-icone"><Droplet :size="15" class="azul" aria-hidden="true" /> Brinde hídrico Terra–órbita</h4>
    <p>Beba 250 ml e convide a Sarah a beber junto. O convite chega à nave em {{ MISSAO.atraso }}.</p>
    <button type="button" class="botao agua" @click="emit('brindar')">Brindar com a Sarah</button>
  </div>
  <div v-else-if="brinde === 'enviado'" class="pc">
    <h4>Convite a caminho da nave</h4>
    <p v-if="brindeNaFila" class="amarelo">Sem sinal agora. O convite sai quando o contato voltar.</p>
    <p v-else>Chega em {{ MISSAO.atraso }}.</p>
  </div>
  <div v-else-if="brinde === 'chegou'" class="pc">
    <h4>A Sarah recebeu seu convite</h4>
    <p>Quando ela beber, a confirmação viaja de volta para cá.</p>
  </div>
  <div v-else-if="brinde === 'brindou'" class="pc">
    <h4>A Sarah brindou!</h4>
    <p>A confirmação está a caminho da Terra.</p>
  </div>
  <div v-else class="pc celebrar">
    <Leaf :size="30" class="verde" aria-hidden="true" />
    <h4>Brinde concluído</h4>
    <p>Você e a Sarah beberam juntas, a 408 km de distância. A estufa ganhou +3%.</p>
    <button type="button" class="botao secundario" @click="emit('brindar')">Brindar de novo</button>
  </div>
</template>

<style scoped>
.pc {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
h4 {
  margin: 4px 0 0;
  font-size: 15px;
  line-height: 1.25;
}
.com-icone {
  display: flex;
  align-items: center;
  gap: 6px;
}
p {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: #a6b2c7;
}
.sobretitulo {
  font-family: ui-monospace, monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--texto-fraco);
}
.barra {
  height: 7px;
  margin-top: 8px;
  border-radius: 9px;
  overflow: hidden;
  background: #1b2437;
}
.barra i {
  display: block;
  height: 100%;
  border-radius: 9px;
  background: var(--ok);
  transition: width 0.6s;
}
.barra i.corrida {
  background: linear-gradient(90deg, var(--agua), var(--acento));
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
  font-weight: 600;
  white-space: nowrap;
  color: var(--acento);
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
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.botao.agua {
  background: var(--agua);
  color: #fff;
}
.botao.secundario {
  border: 1px solid var(--linha-forte);
  background: #1d2a47;
  color: var(--texto);
}
.botao:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
.celebrar {
  text-align: center;
  border-color: rgba(16, 185, 129, 0.5);
  background: linear-gradient(140deg, rgba(16, 185, 129, 0.18), var(--superficie));
}
.verde {
  color: var(--ok);
}
.azul {
  color: var(--agua);
}
.amarelo {
  color: var(--warn);
}
</style>
