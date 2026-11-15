<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { conexao } from '@/servicos/api'
import { embutida, RODAPE } from '@/servicos/formato'

const TELAS = [
  { para: '/', nome: 'Sala de simulação' },
  { para: '/relogio', nome: 'Relógio' },
  { para: '/bordo', nome: 'Painel de bordo' },
  { para: '/houston', nome: 'Houston' },
  { para: '/familia', nome: 'Família' },
  { para: '/dados-ia', nome: 'Dados e IA' },
]

const RAG_COSMO = 'https://nexus-saturn-sg9y3bs4xtruk7h9we6gww.streamlit.app/'
</script>

<template>
  <!-- Dentro do iframe da sala, cada tela aparece sozinha, sem a navegação. -->
  <nav v-if="!embutida" class="nav" aria-label="Telas do AstroHealth OS">
    <span class="marca">AstroHealth OS</span>
    <RouterLink v-for="t in TELAS" :key="t.para" :to="t.para" class="link">{{ t.nome }}</RouterLink>
    <a
      :href="RAG_COSMO"
      target="_blank"
      rel="noopener noreferrer"
      class="rag"
      title="Abre em outra aba o RAG da Cosmo no Streamlit Cloud"
    >
      <span aria-hidden="true">✦</span> Teste o RAG da Cosmo
      <span aria-hidden="true" class="seta">↗</span>
    </a>
    <span class="conexao" :class="conexao" :title="conexao === 'api' ? 'Dados da API' : 'Sem API: dados de exemplo'">
      {{ conexao === 'api' ? 'API no ar' : conexao === 'offline' ? 'Modo offline' : 'Conectando…' }}
    </span>
  </nav>
  <RouterView />
  <p v-if="!embutida" class="rodape">{{ RODAPE }} A Cosmo explica; quem decide é um humano.</p>
</template>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 6px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--linha);
  background: rgba(13, 18, 28, 0.88);
  backdrop-filter: blur(8px);
}
.marca {
  margin-right: 10px;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.link {
  padding: 5px 10px;
  border-radius: 8px;
  color: var(--texto-fraco);
  font-size: 13px;
  text-decoration: none;
}
.link:hover {
  color: var(--texto);
}
.link.router-link-exact-active {
  color: var(--texto);
  background: var(--superficie);
  box-shadow: inset 0 0 0 1px var(--linha-forte);
}
.link:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
.rag {
  margin-left: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #0b1220;
  text-decoration: none;
  background: linear-gradient(135deg, #7dd3fc, #c4b5fd);
  box-shadow: 0 0 0 0 rgba(125, 211, 252, 0.55);
  animation: pulso 2.4s ease-out infinite;
}
.rag:hover {
  filter: brightness(1.08);
}
.rag:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 2px;
}
.rag .seta {
  font-size: 12px;
}
@keyframes pulso {
  0% {
    box-shadow: 0 0 0 0 rgba(125, 211, 252, 0.55);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(125, 211, 252, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(125, 211, 252, 0);
  }
}
@media (prefers-reduced-motion: reduce) {
  .rag {
    animation: none;
  }
}
.conexao {
  margin-left: auto;
  font: 500 11px var(--mono);
  color: var(--texto-fraco);
}
.conexao.api {
  color: var(--ok);
}
.conexao.offline {
  color: var(--warn);
}
.rodape {
  padding: 18px 16px 24px;
  text-align: center;
  font-size: 11.5px;
  color: var(--texto-fraco);
}
</style>
