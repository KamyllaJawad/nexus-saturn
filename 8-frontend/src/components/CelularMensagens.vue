<script setup lang="ts">
import { Mic } from 'lucide-vue-next'
import { MENSAGEM_DA_SARAH, MISSAO, type Mensagem } from '@/mocks/familia'

defineProps<{ mensagens: Mensagem[] }>()

const emit = defineEmits<{ 'enviar-audio': [] }>()
</script>

<template>
  <div class="pc">
    <div class="sobretitulo">Conversa com a Sarah</div>
    <p>Cada mensagem leva {{ MISSAO.atraso }} para chegar.</p>
  </div>

  <div class="conversa" role="log" aria-live="polite">
    <div class="balao dela">
      {{ MENSAGEM_DA_SARAH.texto }}<small>{{ MENSAGEM_DA_SARAH.hora }}</small>
    </div>
    <div v-for="m in mensagens" :key="m.id" class="balao meu">
      {{ m.texto }}
      <small v-if="m.status === 'fila'" class="fila">Na fila: sem sinal</small>
      <small v-else-if="m.status === 'caminho'">A caminho…</small>
      <small v-else>Entregue · {{ m.hora }}</small>
    </div>
  </div>

  <button type="button" class="botao" @click="emit('enviar-audio')">
    <Mic :size="15" aria-hidden="true" /> Enviar áudio do Lucas
  </button>
</template>

<style scoped>
.pc {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid var(--linha);
  background: var(--superficie);
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
.conversa {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.balao {
  max-width: 86%;
  padding: 9px 12px;
  border-radius: 16px;
  font-size: 12.5px;
  line-height: 1.38;
}
.balao.meu {
  align-self: flex-end;
  border-bottom-right-radius: 5px;
  background: #1e2a4a;
}
.balao.dela {
  align-self: flex-start;
  border: 1px solid var(--linha);
  border-bottom-left-radius: 5px;
  background: var(--superficie);
}
.balao small {
  display: block;
  margin-top: 4px;
  font-family: ui-monospace, monospace;
  font-size: 10.5px;
  color: var(--texto-fraco);
}
.balao small.fila {
  color: var(--warn);
}
.botao {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 14px;
  border: 0;
  border-radius: 12px;
  background: var(--acento);
  color: #03141a;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.botao:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
</style>
