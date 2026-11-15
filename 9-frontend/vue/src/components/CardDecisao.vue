<script setup lang="ts">
import { CircleCheck } from 'lucide-vue-next'
import type { Acao, CardDoTripulante } from '@/mocks/decisoes'

defineProps<{
  card: CardDoTripulante
  feitas: Record<string, string>
}>()

const emit = defineEmits<{ acao: [acao: Acao] }>()
</script>

<template>
  <div class="cards">
    <section v-if="card.decisao" class="card decisao" :class="{ urgente: card.decisao.urgente }">
      <h3>{{ card.decisao.titulo }}</h3>
      <p>{{ card.decisao.texto }}</p>
      <a
        v-if="card.decisao.painelCompleto"
        class="botao principal"
        href="/bordo/"
        target="_top"
      >
        Decidir no painel completo
      </a>
      <button
        v-else-if="card.decisao.acao"
        type="button"
        class="botao principal"
        :disabled="!!feitas[card.decisao.acao.chave]"
        @click="emit('acao', card.decisao.acao)"
      >
        <template v-if="feitas[card.decisao.acao.chave]">
          <CircleCheck :size="15" aria-hidden="true" />
          {{ card.decisao.acao.feito }} às {{ feitas[card.decisao.acao.chave] }}
        </template>
        <template v-else>{{ card.decisao.acao.rotulo }}</template>
      </button>
    </section>

    <section class="card">
      <h3>{{ card.acompanhamento.titulo }}</h3>
      <ul>
        <li v-for="item in card.acompanhamento.itens" :key="item">{{ item }}</li>
      </ul>
      <button
        v-if="card.acompanhamento.acao"
        type="button"
        class="botao"
        :disabled="!!feitas[card.acompanhamento.acao.chave]"
        @click="emit('acao', card.acompanhamento.acao)"
      >
        <template v-if="feitas[card.acompanhamento.acao.chave]">
          <CircleCheck :size="15" aria-hidden="true" />
          {{ card.acompanhamento.acao.feito }} às {{ feitas[card.acompanhamento.acao.chave] }}
        </template>
        <template v-else>{{ card.acompanhamento.acao.rotulo }}</template>
      </button>
    </section>
  </div>
</template>

<style scoped>
.cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
.decisao {
  border-color: rgba(0, 229, 255, 0.35);
}
.decisao.urgente {
  border-color: rgba(239, 68, 68, 0.55);
  background: linear-gradient(140deg, rgba(239, 68, 68, 0.1), var(--superficie) 70%);
}
a.botao {
  text-decoration: none;
}
h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
p {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: #a6b2c7;
}
ul {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 10px 0 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.45;
}
.botao {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--linha-forte);
  background: #1d2a47;
  color: var(--texto);
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.botao.principal {
  border-color: transparent;
  background: var(--acento);
  color: #03141a;
}
.botao:hover:not(:disabled) {
  filter: brightness(1.1);
}
.botao:disabled {
  cursor: default;
  border-color: rgba(16, 185, 129, 0.45);
  background: rgba(16, 185, 129, 0.1);
  color: #6ee7b7;
}
.botao:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
</style>
