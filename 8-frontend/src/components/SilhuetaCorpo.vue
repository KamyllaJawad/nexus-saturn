<script setup lang="ts">
// Só o desenho: silhueta em estilo holograma, órgãos coloridos pelo nível e sensores.
// Não decide nada: recebe os níveis prontos.
import { computed, useId } from 'vue'
import { SILHUETA, type Sexo } from '@/silhueta/contorno'
import type { NivelSaude, Orgao } from '@/mocks/tripulacao'

const props = defineProps<{
  sexo: Sexo
  orgaos: Record<Orgao, NivelSaude>
  // 'nenhum' = sem contexto hormonal (não desenha a região pélvica)
  hormonal: 'nenhum' | 'privado' | 'compartilhado'
  rotulo: string // descrição para leitor de tela
}>()

const s = computed(() => SILHUETA[props.sexo])

// Ids únicos por instância: <defs> com id repetido na página quebraria o desenho.
const uid = useId()
const id = (nome: string) => `${uid}-${nome}`
const url = (nome: string) => `url(#${id(nome)})`
</script>

<template>
  <svg class="silhueta" viewBox="0 0 200 440" role="img" :aria-label="rotulo">
    <defs>
      <linearGradient :id="id('grad')" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#22d3ee" stop-opacity=".42" />
        <stop offset="1" stop-color="#0ea5e9" stop-opacity=".16" />
      </linearGradient>
      <pattern :id="id('malha')" width="7" height="7" patternUnits="userSpaceOnUse">
        <path d="M7 0H0V7" fill="none" stroke="#67e8f9" stroke-opacity=".22" stroke-width=".6" />
      </pattern>
      <clipPath :id="id('corpo')"><path :d="s.d" /></clipPath>
      <filter :id="id('brilho')" x="-20%" y="-10%" width="140%" height="120%">
        <feGaussianBlur stdDeviation="3" />
      </filter>
    </defs>

    <!-- Anéis de radar ao fundo -->
    <g class="radar">
      <circle cx="100" cy="215" r="96" />
      <circle cx="100" cy="215" r="70" stroke-dasharray="2 4" />
      <path d="M100 100v14M100 316v14M4 215h14M182 215h14" />
    </g>

    <!-- Corpo: brilho, preenchimento em degradê, malha e contorno -->
    <path :d="s.d" fill="#22d3ee" opacity=".35" :filter="url('brilho')" />
    <path :d="s.d" :fill="url('grad')" />
    <rect width="200" height="440" :fill="url('malha')" :clip-path="url('corpo')" />
    <path d="M100 82V232" class="eixo" :clip-path="url('corpo')" />
    <path :d="s.d" class="contorno" />

    <!-- Órgãos, pintados pelo nível -->
    <ellipse :class="['orgao', `n${orgaos.cerebro}`]" cx="100" cy="32" rx="10" ry="8" />
    <g :class="['orgao', 'pulmao', `n${orgaos.pulmoes}`]">
      <ellipse cx="88" cy="124" rx="10" ry="20" />
      <ellipse cx="112" cy="124" rx="10" ry="20" />
    </g>
    <path
      :class="['orgao', `n${orgaos.coracao}`]"
      d="M106 152s-10-6.5-10-13.5a5.2 5.2 0 0 1 10-2.4a5.2 5.2 0 0 1 10 2.4c0 7-10 13.5-10 13.5z"
    />
    <g :class="['orgao', `n${orgaos.rins}`]">
      <ellipse cx="90" cy="180" rx="5" ry="8" />
      <ellipse cx="110" cy="180" rx="5" ry="8" />
    </g>

    <!-- Saúde hormonal: rosa com consentimento, cinza sem -->
    <template v-if="hormonal !== 'nenhum'">
      <g :class="['hormonal', hormonal]">
        <path d="M92 204h16l-4 12h-8z" />
        <circle cx="86" cy="209" r="3.2" />
        <circle cx="114" cy="209" r="3.2" />
      </g>
      <circle class="sensor conceito" :cx="s.suor[0]" :cy="s.suor[1]" r="6">
        <title>Adesivo de suor · estradiol em tempo real (conceito, ainda não testado no espaço)</title>
      </circle>
    </template>

    <!-- Sensores -->
    <circle class="sensor" :cx="s.relogio[0]" :cy="s.relogio[1]" r="6">
      <title>Relógio · FC, SpO₂, HRV, ECG de 1 derivação, temperatura da pele</title>
    </circle>
    <circle class="sensor" :cx="s.patch[0]" :cy="s.patch[1]" r="6">
      <title>Patch torácico · respiração</title>
    </circle>
    <circle class="sensor" :cx="s.manguito[0]" :cy="s.manguito[1]" r="6">
      <title>Manguito do kit · pressão arterial</title>
    </circle>
  </svg>
</template>

<style scoped>
.silhueta {
  display: block;
  height: 240px;
  width: auto;
}
.radar {
  fill: none;
  stroke: #22d3ee;
  stroke-opacity: 0.14;
}
.eixo {
  stroke: #a5f3fc;
  stroke-opacity: 0.25;
  stroke-width: 0.8;
}
.contorno {
  fill: none;
  stroke: #67e8f9;
  stroke-width: 1.4;
  stroke-opacity: 0.9;
}
.orgao {
  stroke: #05070e;
  stroke-width: 1.4;
  opacity: 0.92;
}
.orgao.n0 {
  fill: var(--ok);
}
.orgao.n1 {
  fill: var(--warn);
}
.orgao.n2 {
  fill: var(--crit);
}
.pulmao {
  opacity: 0.62;
}
.hormonal.compartilhado > * {
  fill: var(--ciclo);
}
.hormonal.privado > * {
  fill: #3a475e;
}
.sensor {
  fill: #05070e;
  stroke: var(--acento);
  stroke-width: 2.2;
}
.sensor.conceito {
  stroke: var(--ciclo);
  stroke-dasharray: 4 3;
}
</style>
