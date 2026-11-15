<script setup lang="ts">
import type { Tripulante } from '@/mocks/tripulacao'

defineProps<{ tripulante: Tripulante }>()

const NOMES = ['Ótimo', 'Atenção', 'Crítico']
</script>

<template>
  <div class="cabecalho">
    <h2>{{ tripulante.nome }} · {{ tripulante.cargo }}</h2>
    <span class="estado" :class="`n${tripulante.nivel}`">
      {{ NOMES[tripulante.nivel] }} · homeostase {{ tripulante.homeostase }}%
    </span>
  </div>
</template>

<style scoped>
.cabecalho {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
.estado {
  padding: 4px 10px;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.n0 {
  background: rgba(16, 185, 129, 0.14);
  color: #6ee7b7;
}
.n1 {
  background: rgba(245, 158, 11, 0.14);
  color: #fcd34d;
}
.n2 {
  background: rgba(239, 68, 68, 0.18);
  color: #fca5a5;
}
</style>
