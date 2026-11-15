<script setup lang="ts">
import type { NivelSaude } from '@/mocks/tripulacao'
import type { Sexo } from '@/silhueta/contorno'

defineProps<{ nivel: NivelSaude; sexo: Sexo }>()
</script>

<template>
  <svg class="astro" :class="`n${nivel}`" viewBox="0 0 120 140" aria-hidden="true">
    <ellipse cx="60" cy="135" rx="28" ry="4" fill="currentColor" opacity=".2" />

    <!-- Mochila, braços e pernas -->
    <rect x="26" y="58" width="68" height="54" rx="16" fill="#0b1222" stroke="currentColor" stroke-opacity=".35" stroke-width="1.5" />
    <rect x="15" y="66" width="15" height="36" rx="7.5" fill="#101a30" stroke="currentColor" stroke-width="2" />
    <!-- Braço direito: acena quando está tudo bem -->
    <g :class="{ aceno: nivel === 0 }">
      <rect x="90" y="66" width="15" height="36" rx="7.5" fill="#101a30" stroke="currentColor" stroke-width="2"
        :transform="nivel === 0 ? 'rotate(-135 97.5 70)' : undefined" />
    </g>
    <rect x="40" y="104" width="16" height="27" rx="7" fill="#101a30" stroke="currentColor" stroke-width="2" />
    <rect x="64" y="104" width="16" height="27" rx="7" fill="#101a30" stroke="currentColor" stroke-width="2" />

    <!-- Tronco e emblema do peito -->
    <rect x="31" y="60" width="58" height="54" rx="20" fill="#101a30" stroke="currentColor" stroke-width="2.5" />
    <rect x="45" y="76" width="30" height="20" rx="6" fill="#060b16" stroke="currentColor" stroke-width="1.5" />
    <path v-if="sexo === 'm'" class="pulso" d="M48 86h7l3-6 4 12 3-6h7" fill="none" stroke="currentColor"
      stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    <g v-else fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="60" cy="83" r="4.5" />
      <path d="M60 87.5v6M57 91h6" />
    </g>

    <!-- Antena -->
    <path d="M60 9V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    <circle cx="60" cy="2.5" r="2" fill="currentColor" />

    
    <g v-if="sexo === 'f'" fill="#101a30" stroke="#A14FE3" stroke-width="2">
      <rect x="25" y="31" width="8" height="15" rx="4" />
      <rect x="87" y="31" width="8" height="15" rx="4" />
    </g>

    <!-- Capacete e visor -->
    <circle cx="60" cy="38" r="29" fill="#0c1426" stroke="currentColor" stroke-width="2.5" />
    <ellipse cx="60" cy="41" rx="21" ry="15" fill="currentColor" opacity=".3" />
    <!-- Cabelo visível no visor (feminino) -->
    <path v-if="sexo === 'f'" d="M39.5 37c1-8 9-12 20.5-12s19.5 4 20.5 12c-5-4-12-5.5-20.5-5.5S44.5 33 39.5 37z" fill="#A14FE3" opacity=".9" />
    <ellipse cx="60" cy="41" rx="21" ry="15" fill="none" stroke="currentColor" stroke-width="1.5" />

    <!-- Expressão -->
    <g fill="none" stroke="#fff" stroke-linecap="round">
      <template v-if="nivel === 0">
        <path d="M49 42q4-5 8 0M63 42q4-5 8 0" stroke-width="2.4" />
        <path d="M54 48q6 4 12 0" stroke-width="2" />
      </template>
      <template v-else-if="nivel === 1">
        <path d="M48.5 36.5l8 1.5M71.5 36.5l-8 1.5" stroke-width="2" />
        <path d="M52.5 41.5v3M67.5 41.5v3" stroke-width="3.2" />
        <path d="M55 49h10" stroke-width="2" />
      </template>
      <template v-else>
        <path d="M49 37l7 3.5M71 37l-7 3.5" stroke-width="2.6" />
        <path d="M52.5 43v2M67.5 43v2" stroke-width="3.2" />
        <path d="M53 51q7-4 14 0" stroke-width="2" />
      </template>
    </g>
    <ellipse cx="51" cy="32" rx="7" ry="2.6" fill="#fff" opacity=".22" />
  </svg>
</template>

<style scoped>
.astro {
  width: 92px;
  height: auto;
  overflow: visible;
  filter: drop-shadow(0 0 12px color-mix(in srgb, currentColor 45%, transparent));
  animation: flutuar 4s ease-in-out infinite;
}
.n0 {
  color: var(--ok);
}
.n1 {
  color: var(--warn);
}
.n2 {
  color: var(--crit);
}
.pulso {
  animation: bater 1s ease-in-out infinite;
}
.aceno {
  transform-origin: 97.5px 70px;
  animation: acenar 2.4s ease-in-out infinite;
}
@keyframes flutuar {
  50% {
    transform: translateY(-4px);
  }
}
@keyframes bater {
  50% {
    opacity: 0.45;
  }
}
@keyframes acenar {
  0%, 60%, 100% {
    transform: rotate(0deg);
  }
  70%, 90% {
    transform: rotate(-12deg);
  }
  80% {
    transform: rotate(8deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .astro,
  .pulso,
  .aceno {
    animation: none;
  }
}
</style>
