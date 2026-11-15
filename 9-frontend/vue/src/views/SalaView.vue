<script setup lang="ts">
// Sala de simulação: quem apresenta injeta cenários e vê as quatro telas lado a lado.
// O relógio é simulado; os modelos, o motor de decisões e o link são os da API.
import { computed, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { pedir } from '@/servicos/api'
import { usarConsulta } from '@/servicos/consulta'
import { ajustarEquipe, hora, nome, TIPO } from '@/servicos/formato'
import { EVENTOS_BORDO as EVENTOS, SINAIS_RELOGIO as SINAIS } from '@/servicos/cenarios'

interface Estado {
  hora_nave: string
  missao: string
  fases: Record<string, string>
  blackout: boolean
  abertos: { id: string; tipo: string; tripulante_id: string; responsavel_id: string }[]
  banco_ecg: { em_uso: { normal: number; fa: number } }
}
interface Missao {
  rotulo: string
  atraso_txt: string
  comprimido: boolean
  perfis: Record<string, string>
  equipe: { local: 'bordo' | 'terra'; resumo: string; medico_nome: string; marcus: { nome: string; papel: string } }
}

const estado = usarConsulta<Estado>(() => '/simulador/estado')
const missao = usarConsulta<Missao>(() => '/missao')
const erro = computed(() => estado.erro.value)

const terra = computed(() => missao.dados.value?.equipe.local === 'terra')
watch(() => missao.dados.value?.equipe, (eq) => ajustarEquipe(eq), { immediate: true })

function cenario(c: string, tripulante_id: string | null = null) {
  return estado.executar(() => pedir('/simulador/cenario', { cenario: c, tripulante_id })).then(() => missao.carregar())
}
function reiniciar() {
  return estado.executar(() => pedir('/simulador/reiniciar', {})).then(() => missao.carregar())
}

const FASE: Record<string, string> = {
  rotina: 'rotina',
  fa: 'fibrilação atrial',
  fa_o2: 'fibrilação atrial, com O₂ do CMO',
  fa_tratada: 'em recuperação',
  sensor_solto: 'relógio folgado',
  combinacao: 'combinação fora do padrão',
  ciclo: 'desvio leve (trecho do ciclo)',
}

const fases = computed(() => {
  const f = Object.entries(estado.dados.value?.fases ?? {}).filter(([, v]) => v !== 'rotina')
  return f.map(([t, v]) => `${nome(t)}: ${FASE[v] ?? v}`).join(' · ') || 'todos em rotina'
})
const abertos = computed(
  () =>
    (estado.dados.value?.abertos ?? [])
      .map((e) => `${TIPO[e.tipo] ?? e.tipo} (${nome(e.tripulante_id)}) → decide ${nome(e.responsavel_id)}`)
      .join(' · ') || 'nenhum',
)

const base = import.meta.env.BASE_URL
const TELAS = computed(() => [
  { titulo: 'A bordo · Relógio', rota: '#/relogio?quem=sarah' },
  { titulo: terra.value ? 'A bordo · Painel do CMO (sem médico a bordo)' : 'A bordo · Painel do oficial médico', rota: '#/bordo' },
  { titulo: 'Na Terra · Celular da família', rota: '#/familia' },
  {
    titulo: terra.value ? `Na Terra · Console da ${missao.dados.value?.equipe.medico_nome} (médica responsável)` : 'Na Terra · Console de Houston',
    rota: '#/houston',
  },
])
</script>

<template>
  <main class="sala">
    <header class="cabeca">
      <div>
        <h1>Sala de simulação</h1>
        <p class="nota">O relógio é simulado; os modelos, as decisões e o link com atraso são reais.</p>
      </div>
      <div class="onde" v-if="estado.dados.value && missao.dados.value">
        Hora da nave {{ hora(estado.dados.value.hora_nave, true) }}<br />
        {{ missao.dados.value.rotulo }} · atraso {{ missao.dados.value.atraso_txt }}
      </div>
      <RouterLink to="/dados-ia" class="btn sm">Dados e IA · human-in-the-loop</RouterLink>
    </header>

    <section class="cartao controles" aria-label="Controles da simulação">
      <div class="grupo">
        <span class="etiqueta">Perfil de missão (muda o atraso)</span>
        <div class="selos">
          <button
            v-for="(rotulo, k) in missao.dados.value?.perfis ?? {}"
            :key="k"
            type="button"
            class="selecao"
            :aria-pressed="k === estado.dados.value?.missao"
            @click="cenario(String(k))"
          >
            {{ rotulo }}
          </button>
        </div>
      </div>
      <div class="grupo">
        <span class="etiqueta">Médico da missão (hipótese)</span>
        <div class="selos">
          <button type="button" class="selecao" :aria-pressed="!terra" @click="cenario('medico_bordo')">Dr. Marcus a bordo</button>
          <button type="button" class="selecao" :aria-pressed="terra" @click="cenario('medico_terra')">Só na Terra · Dra. Rivera</button>
        </div>
      </div>
      <div class="grupo">
        <span class="etiqueta">Link com a Terra</span>
        <div class="selos">
          <button type="button" class="selecao" :aria-pressed="!!estado.dados.value?.blackout" @click="cenario('blackout')">Blackout</button>
          <button type="button" class="selecao" @click="cenario('sinal_volta')">O sinal volta</button>
        </div>
      </div>
      <div class="grupo largo">
        <span class="etiqueta">Sinal do relógio (quem detecta são os modelos)</span>
        <div class="selos">
          <button v-for="[r, c, t] in SINAIS" :key="r" type="button" class="selecao" @click="cenario(c, t)">{{ r }}</button>
        </div>
      </div>
      <div class="grupo largo">
        <span class="etiqueta">Eventos de bordo</span>
        <div class="selos">
          <button v-for="[r, c, t] in EVENTOS" :key="r" type="button" class="selecao" @click="cenario(c, t)">{{ r }}</button>
          <button type="button" class="btn sm" @click="reiniciar()">Reiniciar a simulação</button>
        </div>
      </div>
      <p v-if="estado.dados.value && missao.dados.value" class="nota estado">
        <b>Médico:</b> {{ missao.dados.value.equipe.resumo }}<br />
        <b>Sinal injetado:</b> {{ fases }}. <b>Link:</b>
        <span :class="{ 'c-warn': estado.dados.value.blackout }">{{ estado.dados.value.blackout ? 'sem sinal' : 'ativo' }}</span
        >{{ missao.dados.value.comprimido ? ' (na demo, 1 min de atraso = 1 s)' : '' }}. <b>Aguardando humano:</b> {{ abertos }}.
        <b>ECG:</b> {{ estado.dados.value.banco_ecg.em_uso.normal }} gravações normais e {{ estado.dados.value.banco_ecg.em_uso.fa }} de FA
        do teste do CinC 2017.
      </p>
      <p v-else class="aviso-faixa offline">
        A API não respondeu. A sala precisa dela para injetar cenários (8-backend, ou VITE_API_URL apontando para a API publicada).
      </p>
      <p v-if="erro" class="aviso-faixa erro" role="alert">{{ erro }}</p>
    </section>

    <div class="grade">
      <div v-for="t in TELAS" :key="t.rota" class="moldura">
        <header>
          <span>{{ t.titulo }}</span>
          <a :href="`${base}${t.rota}`" target="_blank" rel="noopener">abrir em aba</a>
        </header>
        <iframe :src="`${base}${t.rota}`" :title="t.titulo"></iframe>
      </div>
    </div>
  </main>
</template>

<style scoped>
.sala {
  max-width: 1440px;
  margin: 0 auto;
  padding: 20px 16px 8px;
}
.cabeca {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 20px;
  margin-bottom: 14px;
}
.cabeca h1 {
  font-size: 22px;
}
.onde {
  margin-left: auto;
  text-align: right;
  font: 500 11px var(--mono);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--acento);
}
.controles {
  display: flex;
  flex-wrap: wrap;
  gap: 14px 28px;
}
.grupo {
  flex: 1 1 240px;
}
.grupo.largo {
  flex: 2 1 480px;
}
.grupo .etiqueta {
  display: block;
  margin-bottom: 6px;
}
.estado,
.controles .aviso-faixa {
  flex: 1 1 100%;
}
.grade {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}
.moldura {
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--linha-forte);
  background: var(--bg-fim);
}
.moldura header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--linha);
  font-size: 12.5px;
  font-weight: 600;
}
.moldura a {
  color: var(--acento);
  font-weight: 400;
}
.moldura iframe {
  display: block;
  width: 100%;
  height: 680px;
  border: 0;
  background: var(--bg-fim);
}
@media (max-width: 1080px) {
  .grade {
    grid-template-columns: minmax(0, 1fr);
  }
  .onde {
    margin-left: 0;
    text-align: left;
  }
}
</style>
