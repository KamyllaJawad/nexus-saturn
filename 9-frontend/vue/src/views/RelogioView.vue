<script setup lang="ts">
import { computed, ref } from 'vue'
import RelogioPrototipo from '../components/RelogioPrototipo.vue'
import { tripulacaoMock, type NivelSaude } from '@/mocks/tripulacao'
import { CICLO_NO_RELOGIO, PREVIA_ESTADO } from '@/mocks/relogio'

const tripulacao = tripulacaoMock
const selecionado = ref('sarah')
const nivel = ref<NivelSaude>(0)

const tripulante = computed(
    () => tripulacao.find((t) => t.id === selecionado.value) ?? tripulacao[0]!,
)

const NIVEIS: { valor: NivelSaude; nome: string }[] = [
    { valor: 0, nome: 'Ótimo' },
    { valor: 1, nome: 'Atenção' },
    { valor: 2, nome: 'Crítico' },
]
</script>

<template>
    <main class="pagina">
        <header>
            <p class="etiqueta"><span>A bordo</span> Relógio circular · 45 mm</p>
            <h1>Relógio de {{ tripulante.nome }}</h1>
        </header>

        <RelogioPrototipo
            :nivel="nivel"
            :sexo="tripulante.sexo"
            :estado="PREVIA_ESTADO[nivel]"
            :ciclo="CICLO_NO_RELOGIO[tripulante.id]"
        />

        
        <section class="controles" aria-label="Prévia do protótipo">
            <div class="grupo" role="group" aria-label="Tripulante">
                <button
                    v-for="t in tripulacao"
                    :key="t.id"
                    type="button"
                    :aria-pressed="t.id === selecionado"
                    @click="selecionado = t.id"
                >
                    {{ t.nome }}
                </button>
            </div>
            <div class="grupo" role="group" aria-label="Estado">
                <button
                    v-for="n in NIVEIS"
                    :key="n.valor"
                    type="button"
                    :class="`n${n.valor}`"
                    :aria-pressed="n.valor === nivel"
                    @click="nivel = n.valor"
                >
                    {{ n.nome }}
                </button>
            </div>
        </section>
    </main>
</template>

<style scoped>
.pagina {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
    min-height: 100vh;
    padding: 40px 16px;
}

header {
    text-align: center;
}
.etiqueta {
    margin: 0 0 6px;
    font-family: ui-monospace, monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--texto-fraco);
}
.etiqueta span {
    margin-right: 6px;
    padding: 2px 7px;
    border-radius: 99px;
    border: 1px solid rgba(0, 229, 255, 0.4);
    color: var(--acento);
}
h1 {
    margin: 0;
    font-size: 20px;
}

.controles {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}
.grupo {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;
    padding: 4px;
    border-radius: 12px;
    border: 1px solid var(--linha);
    background: rgba(255, 255, 255, 0.02);
}
.grupo button {
    padding: 7px 14px;
    border: 0;
    border-radius: 9px;
    background: transparent;
    color: var(--texto-fraco);
    font: inherit;
    font-size: 13px;
    cursor: pointer;
}
.grupo button:hover {
    color: var(--texto);
}
.grupo button[aria-pressed='true'] {
    background: var(--superficie);
    color: var(--texto);
    box-shadow: inset 0 0 0 1px var(--linha-forte);
}
.grupo button.n0[aria-pressed='true'] {
    color: var(--ok);
}
.grupo button.n1[aria-pressed='true'] {
    color: var(--warn);
}
.grupo button.n2[aria-pressed='true'] {
    color: var(--crit);
}
.grupo button:focus-visible {
    outline: 2px solid var(--acento);
    outline-offset: 2px;
}
</style>
