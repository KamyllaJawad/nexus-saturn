<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { BatteryFull, House, Leaf, MessageSquare, Orbit, Signal } from 'lucide-vue-next'
import type { Aba } from '@/mocks/familia'

defineProps<{ aba: Aba }>()
const emit = defineEmits<{ 'update:aba': [aba: Aba] }>()

const ABAS = [
  { id: 'inicio', nome: 'Início', icone: House },
  { id: 'elo', nome: 'Elo', icone: Leaf },
  { id: 'mensagens', nome: 'Mensagens', icone: MessageSquare },
] as const

const hora = ref('')
let intervalo = 0
function atualizarHora() {
  hora.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
onMounted(() => {
  atualizarHora()
  intervalo = window.setInterval(atualizarHora, 10_000)
})
onUnmounted(() => window.clearInterval(intervalo))
</script>

<template>
  <div class="moldura">
    <div class="tela">
      <div class="ilha" aria-hidden="true"></div>
      <div class="status">
        <span>{{ hora }}</span>
        <span class="icones"><Signal :size="14" aria-hidden="true" /><BatteryFull :size="15" aria-hidden="true" /></span>
      </div>

      <header class="cabecalho">
        <div class="logo"><Orbit :size="18" aria-hidden="true" /></div>
        <div>
          <b>Terra-Órbita</b>
          <small>Família da Sarah · Houston</small>
        </div>
      </header>

      <div class="corpo">
        <slot />
      </div>

      <nav class="abas" aria-label="Seções do app">
        <button
          v-for="a in ABAS"
          :key="a.id"
          type="button"
          :aria-current="a.id === aba ? 'page' : undefined"
          @click="emit('update:aba', a.id)"
        >
          <component :is="a.icone" :size="19" aria-hidden="true" />{{ a.nome }}
        </button>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.moldura {
  width: 340px;
  max-width: 100%;
  height: 700px;
  padding: 10px;
  border-radius: 52px;
  background: linear-gradient(160deg, #252e42, #0d121c 70%);
  box-shadow: inset 0 0 0 1px #2e3850, 0 24px 60px rgba(0, 0, 0, 0.6);
}
.tela {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 42px;
  overflow: hidden;
  background: #05070e;
}
.ilha {
  position: absolute;
  top: 10px;
  left: 50%;
  z-index: 3;
  width: 96px;
  height: 27px;
  border-radius: 20px;
  transform: translateX(-50%);
  background: #000;
}
.status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 28px 4px;
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.icones {
  display: flex;
  gap: 4px;
}
.cabecalho {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px 10px;
}
.logo {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.35), rgba(0, 229, 255, 0.25));
  color: #fff;
}
.cabecalho b {
  display: block;
  font-size: 16px;
  line-height: 1.1;
}
.cabecalho small {
  font-size: 11.5px;
  color: var(--texto-fraco);
}
.corpo {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px 16px 16px;
  overflow-y: auto;
  scrollbar-width: thin;
}
.abas {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  padding: 8px 8px 20px;
  border-top: 1px solid var(--linha);
  background: #070a13;
}
.abas button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 4px;
  border: 0;
  background: transparent;
  color: var(--texto-fraco);
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.abas button[aria-current='page'] {
  color: var(--acento);
}
.abas button:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
  border-radius: 8px;
}
</style>
