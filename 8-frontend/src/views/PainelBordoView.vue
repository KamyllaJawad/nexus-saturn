<script setup lang="ts">
import { computed, ref } from 'vue'
import PainelHeader from '../components/PainelHeader.vue'
import ListaTripulacao from '../components/ListaTripulacao.vue'
import PacienteHeader from '../components/PacienteHeader.vue'
import EcgCanvas from '../components/EcgCanvas.vue'
import GradeSinais from '../components/GradeSinais.vue'
import CardSilhueta from '../components/CardSilhueta.vue'
import CardDecisao from '../components/CardDecisao.vue'
import ChatCosmo from '../components/ChatCosmo.vue'
import { statusNaveMock } from '@/mocks/nave'
import { tripulacaoMock } from '@/mocks/tripulacao'
import { DECISOES, type Acao } from '@/mocks/decisoes'

const statusNave = ref(statusNaveMock)
const tripulacao = ref(tripulacaoMock)
const selecionado = ref('sarah')
const acoesFeitas = ref<Record<string, string>>({})

const tripulante = computed(
    () => tripulacao.value.find((t) => t.id === selecionado.value) ?? tripulacao.value[0]!,
)
const card = computed(() => DECISOES[tripulante.value.id]!)

function registrarAcao(acao: Acao) {
    // TODO: chamar POST /decisoes quando o back existir
    acoesFeitas.value[acao.chave] = new Date().toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
    })
}
</script>

<template>
    <PainelHeader :status="statusNave" />
    <div class="layout">
        <ListaTripulacao v-model="selecionado" :tripulantes="tripulacao" />
        <main>
            <PacienteHeader :tripulante="tripulante" />
            <EcgCanvas
                :fc="tripulante.vitais.fc"
                :ritmo="tripulante.ritmo"
                :nivel="tripulante.nivel"
                :nome="tripulante.nome"
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
</style>
