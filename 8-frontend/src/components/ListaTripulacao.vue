<script setup lang="ts">
import type { Tripulante } from '@/mocks/tripulacao'

defineProps<{ tripulantes: Tripulante[] }>()


const selecionado = defineModel<string>({ required: true })

const NOMES_NIVEL = ['ótimo', 'atenção', 'crítico']
</script>

<template>
  <nav class="lista" aria-label="Tripulação">
    <button
      v-for="t in tripulantes"
      :key="t.id"
      type="button"
      class="item"
      :class="{ selecionado: t.id === selecionado }"
      :aria-pressed="t.id === selecionado"
      @click="selecionado = t.id"
    >
      <span class="bolinha" :class="`nivel-${t.nivel}`" :title="NOMES_NIVEL[t.nivel]"></span>
      <span class="nome">{{ t.nome }}</span>
      <small class="cargo">
        {{ t.cargo }}<template v-if="t.destaque"> · {{ t.destaque }}</template>
      </small>
    </button>
  </nav>
</template>

<style scoped>
.lista {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 10px;
  border-right: 1px solid var(--linha);
}

.item {
  display: grid;
  grid-template-columns: 10px 1fr;
  align-items: center;
  gap: 2px 10px;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--texto);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
}

.item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.item.selecionado {
  background: var(--superficie);
  box-shadow: inset 0 0 0 1px var(--linha-forte);
}

.item:focus-visible {
  outline: 2px solid var(--ok);
  outline-offset: 2px;
}

.bolinha {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.nivel-0 {
  background: var(--ok);
}

.nivel-1 {
  background: var(--warn);
}

.nivel-2 {
  background: var(--crit);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.25);
}

.nome {
  font-size: 14px;
  font-weight: 600;
}

.cargo {
  grid-column: 2;
  font-size: 12px;
  line-height: 1.4;
  color: var(--texto-fraco);
}
</style>
