<script setup lang="ts">
import type { Component } from 'vue'
import type { NivelSaude } from '@/mocks/tripulacao'

defineProps<{
  nome: string
  valor: string
  unidade: string
  fonte: string
  icone: Component
  corIcone: string
  faixa: NivelSaude
}>()
</script>

<template>
  <div class="card" :class="`faixa-${faixa}`">
    <div class="nome">
      <component :is="icone" :size="13" :style="{ color: corIcone }" aria-hidden="true" />
      {{ nome }}
    </div>
    <div class="valor">
      {{ valor }}<small>{{ unidade }}</small>
    </div>
    <div class="fonte">{{ fonte }}</div>
  </div>
</template>

<style scoped>
.card {
  min-width: 0;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
.nome {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--texto-fraco);
}
.valor {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.valor small {
  margin-left: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--texto-fraco);
}
.fonte {
  margin-top: 4px;
  font-family: ui-monospace, monospace;
  font-size: 10px;
  color: var(--texto-fraco);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* faixa 1: atenção */
.faixa-1 { border-color: rgba(245, 158, 11, 0.5); }
.faixa-1 .valor { color: #fcd34d; }

/* faixa 2: crítico */
.faixa-2 { border-color: rgba(239, 68, 68, 0.6); background: rgba(239, 68, 68, 0.08); }
.faixa-2 .valor { color: #fca5a5; }
</style>
