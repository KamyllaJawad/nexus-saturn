<script setup lang="ts">
import { computed, onUnmounted, ref, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import PainelHeader from '../components/PainelHeader.vue'
import ListaTripulacao from '../components/ListaTripulacao.vue'
import PacienteHeader from '../components/PacienteHeader.vue'
import EcgCanvas from '../components/EcgCanvas.vue'
import GradeSinais from '../components/GradeSinais.vue'
import CardSilhueta from '../components/CardSilhueta.vue'
import CardDecisao from '../components/CardDecisao.vue'
import ChatCosmo from '../components/ChatCosmo.vue'
import { DECISOES, type Acao } from '@/mocks/decisoes'
import { usarBordo } from '@/servicos/bordo'
import { buscarEcg, paraCard } from '@/servicos/api'
import type { TrechoEcg } from '@/ecg/tocador'

const { tripulantes, status, bordo, erro, conexao, decidir } = usarBordo()
// /v2/#/bordo?quem=kenji abre o painel já nessa pessoa.
const selecionado = ref(String(useRoute().query.quem ?? 'sarah'))
const acoesFeitas = ref<Record<string, string>>({})

const tripulante = computed(
  () => tripulantes.value.find((t) => t.id === selecionado.value) ?? tripulantes.value[0]!,
)
// Com a API no ar, o card sai dos eventos reais; offline, dos mocks.
const card = computed(() =>
  bordo.value ? paraCard(tripulante.value.id, bordo.value) : DECISOES[tripulante.value.id]!,
)

// Um alerta de arritmia novo leva o painel direto para a pessoa, como no bordo/ atual.
let ultimoAlerta: string | null = null
watch(bordo, (b) => {
  const alerta = b?.eventos.find((e) => e.tipo === 'arritmia' && e.estado === 'aguardando_humano')
  if (alerta && alerta.id !== ultimoAlerta) {
    ultimoAlerta = alerta.id
    selecionado.value = alerta.tripulante_id
  }
})

// ECG real do relógio da pessoa selecionada, renovado a cada 5 s (o trecho tem 6 s).
const trecho = shallowRef<TrechoEcg | null>(null)
async function carregarEcg() {
  if (conexao.value !== 'api') return (trecho.value = null)
  const tid = selecionado.value
  try {
    const t = await buscarEcg(tid)
    if (tid === selecionado.value) trecho.value = t
  } catch {
    trecho.value = null
  }
}
watch([selecionado, conexao], () => {
  trecho.value = null
  carregarEcg()
})
const idEcg = setInterval(carregarEcg, 5000)
onUnmounted(() => clearInterval(idEcg))

const agora = () => new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

async function registrarAcao(acao: Acao) {
  try {
    await decidir(acao)
    acoesFeitas.value[acao.chave] = agora()
  } catch {
    // a mensagem fica em `erro` e aparece no aviso abaixo
  }
}
</script>

<template>
  <PainelHeader :status="status" />
  <p v-if="conexao === 'offline'" class="aviso offline" role="status">
    Modo offline: a API não respondeu, então a tela mostra dados de exemplo. Suba o 8-backend
    (uvicorn app.main:app --port 8000) e ela volta sozinha.
  </p>
  <p v-if="erro" class="aviso erro" role="alert">{{ erro }}</p>
  <div class="layout">
    <ListaTripulacao v-model="selecionado" :tripulantes="tripulantes" />
    <main>
      <PacienteHeader :tripulante="tripulante" />
      <EcgCanvas
        :fc="tripulante.vitais.fc"
        :ritmo="tripulante.ritmo"
        :nivel="tripulante.nivel"
        :nome="tripulante.nome"
        :trecho="trecho"
      />
      <div class="sinais-e-corpo">
        <GradeSinais :tripulante="tripulante" />
        <CardSilhueta :tripulante="tripulante" />
      </div>
      <CardDecisao :card="card" :feitas="acoesFeitas" @acao="registrarAcao" />
    </main>
    <ChatCosmo :tripulante="tripulante" />
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 360px;
  min-height: calc(100vh - 200px);
  border-top: 1px solid var(--linha);
}

main {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 24px;
}

.sinais-e-corpo {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  align-items: start;
  gap: 12px;
}

/* Telas mais estreitas, como o iframe da sala de simulação (~620 px):
   o chat desce e, abaixo de 820 px, tudo vira uma coluna. */
@media (max-width: 1180px) {
  .layout {
    grid-template-columns: 200px minmax(0, 1fr);
  }
  .chat {
    grid-column: 1 / -1;
    height: 420px;
    border-left: 0;
    border-top: 1px solid var(--linha);
  }
}
@media (max-width: 820px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .lista {
    flex-direction: row;
    flex-wrap: wrap;
    border-right: 0;
    border-bottom: 1px solid var(--linha);
  }
  .lista :deep(.item) {
    width: auto;
    flex: 1 1 140px;
  }
  main {
    padding: 14px 16px;
  }
  .sinais-e-corpo {
    grid-template-columns: minmax(0, 1fr);
  }
}

.aviso {
  margin: 0;
  padding: 8px 24px;
  font-size: 12.5px;
  border-top: 1px solid var(--linha);
}
.offline {
  color: var(--warn);
  background: rgba(245, 158, 11, 0.08);
}
.erro {
  color: #fecaca;
  background: rgba(239, 68, 68, 0.12);
}
</style>
