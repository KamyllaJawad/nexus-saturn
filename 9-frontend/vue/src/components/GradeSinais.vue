<script setup lang="ts">
import CardSinalVital from './CardSinalVital.vue'
import { SINAIS } from '@/sinais/catalogo'
import type { Tripulante } from '@/mocks/tripulacao'

defineProps<{ tripulante: Tripulante }>()
</script>

<template>
  <div class="grade">
    <CardSinalVital
      v-for="s in SINAIS"
      :key="s.chave"
      :nome="s.nome"
      :valor="s.formatar(tripulante.vitais)"
      :unidade="s.unidade"
      :fonte="s.fonte"
      :icone="s.icone"
      :cor-icone="s.corIcone"
      :faixa="tripulante.faixas[s.chave]"
    />
  </div>
</template>

<style scoped>
.grade {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
</style>
