<script setup lang="ts">
import type { Component } from 'vue'

type Variante = 'normal' | 'ok' | 'warn' | 'crit'

withDefaults(defineProps<{ variante?: Variante; icone?: Component }>(), {
  variante: 'normal',
})
</script>

<template>
  <span class="chip" :class="variante">
    <component :is="icone" v-if="icone" :size="12" aria-hidden="true" />
    <slot />
  </span>
</template>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 99px;
  border: 1px solid rgba(148, 163, 184, 0.26);
  color: #a6b2c7;
  font: 500 11px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: nowrap;
}

.ok {
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.45);
}

.warn {
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.5);
}

.crit {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.55);
}
</style>
