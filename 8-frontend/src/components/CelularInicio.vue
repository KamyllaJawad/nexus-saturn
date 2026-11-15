<script setup lang="ts">
import { Brain, Check, Droplet, Moon, Orbit, ShieldCheck, WifiOff, Zap } from 'lucide-vue-next'
import AstronautaAvatar from './AstronautaAvatar.vue'
import { MISSAO, RESUMO_DIA, type Cenario, type ItemFeed } from '@/mocks/familia'

defineProps<{
  cenario: Cenario
  hidratacaoPct: number
  feed: ItemFeed[]
}>()
</script>

<template>
  <div v-if="cenario === 'blackout'" class="pc hero aviso">
    <WifiOff :size="26" class="hero-icone amarelo" aria-hidden="true" />
    <div>
      <div class="sobretitulo">Sarah · Comandante</div>
      <h4>Sem sinal da nave por enquanto</h4>
      <p>
        {{ MISSAO.blackout.motivo }}. Isso é esperado e a tripulação segue a rotina normalmente. O contato
        volta em {{ MISSAO.blackout.volta }}.
      </p>
      <p>Suas mensagens ficam guardadas e seguem quando o sinal voltar.</p>
    </div>
  </div>

  <!-- Na emergência, a família não recebe detalhes de saúde: só a equipe médica. -->
  <div v-else-if="cenario === 'emergencia'" class="pc hero medico">
    <ShieldCheck :size="26" class="hero-icone lilas" aria-hidden="true" />
    <div>
      <div class="sobretitulo">Sarah · Comandante</div>
      <h4>A Sarah está sendo acompanhada pela equipe médica</h4>
      <p>Detalhes de saúde ficam entre a tripulação e os médicos da NASA. A NASA vai entrar em contato com novidades.</p>
    </div>
  </div>

  <template v-else>
    <div class="pc hero bem">
      <AstronautaAvatar :nivel="0" sexo="f" class="avatar" />
      <div>
        <div class="sobretitulo">Sarah · Comandante</div>
        <h4>A Sarah está bem</h4>
        <p>As notícias da nave chegam quase em tempo real.</p>
      </div>
    </div>
    <div class="mini-grade">
      <div class="mini"><Moon :size="16" class="roxo" aria-hidden="true" /><b>Dormiu {{ RESUMO_DIA.sono }}</b><span>Sono bom</span></div>
      <div class="mini"><Zap :size="16" class="verde" aria-hidden="true" /><b>Treino feito</b><span>{{ RESUMO_DIA.treino }}</span></div>
      <div class="mini"><Droplet :size="16" class="azul" aria-hidden="true" /><b>{{ hidratacaoPct }}% da meta</b><span>Hidratação</span></div>
      <div class="mini"><Brain :size="16" class="amarelo" aria-hidden="true" /><b>{{ RESUMO_DIA.humor }}</b><span>Humor e energia</span></div>
    </div>
  </template>

  <div class="pc">
    <div class="sobretitulo">Últimas da nave</div>
    <div class="feed">
      <template v-if="feed.length">
        <div v-for="item in feed" :key="item.texto + item.hora" class="feed-item">
          <Check :size="14" aria-hidden="true" />
          <span>{{ item.texto }} <span class="fraco">· {{ item.hora }}</span></span>
        </div>
      </template>
      <div v-else class="feed-item fraco">Nada novo por enquanto.</div>
    </div>
  </div>

  <div class="local"><Orbit :size="14" aria-hidden="true" />{{ MISSAO.local }} · {{ MISSAO.distancia }}</div>
</template>

<style scoped>
.pc {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
h4 {
  margin: 0;
  font-size: 15px;
  line-height: 1.25;
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
.hero {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.hero.bem {
  align-items: center;
  border-color: rgba(16, 185, 129, 0.35);
  background: linear-gradient(140deg, rgba(16, 185, 129, 0.12), var(--superficie) 60%);
}
.hero.medico {
  border-color: rgba(139, 92, 246, 0.45);
  background: linear-gradient(140deg, rgba(139, 92, 246, 0.16), var(--superficie) 60%);
}
.hero.aviso {
  border-color: rgba(245, 158, 11, 0.4);
  background: linear-gradient(140deg, rgba(245, 158, 11, 0.1), var(--superficie) 60%);
}
.hero-icone {
  flex: none;
  margin-top: 2px;
}
.hero .avatar {
  flex: none;
  width: 54px;
  animation: none;
}
.mini-grade {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.mini {
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid var(--linha);
  background: var(--superficie);
}
.mini b {
  display: block;
  margin-top: 4px;
  font-size: 14px;
}
.mini span {
  font-size: 11px;
  color: var(--texto-fraco);
}
.feed {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.feed-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12.5px;
  color: #a6b2c7;
}
.feed-item svg {
  flex: none;
  margin-top: 2px;
  color: var(--acento);
}
.local {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #a6b2c7;
}
.local svg {
  color: var(--acento);
}
.fraco {
  color: var(--texto-fraco);
}
.verde {
  color: var(--ok);
}
.amarelo {
  color: var(--warn);
}
.azul {
  color: var(--agua);
}
.roxo,
.lilas {
  color: #c4b5fd;
}
</style>
