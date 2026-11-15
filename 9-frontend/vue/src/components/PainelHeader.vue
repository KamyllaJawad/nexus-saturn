<script setup lang="ts">
import { computed } from 'vue'
import { Network, Signal, Wind, WifiOff } from 'lucide-vue-next'
import StatusChip from './StatusChip.vue'
import type { StatusNave } from '@/mocks/nave'

const props = defineProps<{ status: StatusNave }>()

const LIMITE_CO2 = 3

const co2Texto = computed(() => props.status.co2.toFixed(1).replace('.', ','))
const co2Alto = computed(() => props.status.co2 > LIMITE_CO2)
</script>

<template>
    <header class="painel-header">
        <div  class="painel-header-content">
            <h1 class="titulo">{{ status.titulo ?? 'Enfermaria · Dr. Marcus' }}</h1>
            <p class="subtitulo">{{ status.subtitulo ?? 'Oficial médico da tripulação' }}</p>
        </div>
        <div class="chips">
            <StatusChip v-if="status.houstonOnline" :icone="Signal">
                Houston · {{ status.atrasoHouston }}
            </StatusChip>
            <StatusChip v-else variante="warn" :icone="WifiOff">
                Houston fora de alcance
            </StatusChip>

            <StatusChip variante="ok" :icone="Network">
                Rede local · {{ status.tripulantes }} tripulantes
            </StatusChip>

            <StatusChip :variante="co2Alto ? 'warn' : 'normal'" :icone="Wind">
                CO₂ {{ co2Texto }} mmHg
            </StatusChip>
        </div>
    </header>
</template>

<style scoped>
header {
    color: white;
    padding: 10px;
}

.painel-header-content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 20px;
    font-family:'DM Sans', sans-serif;
}

.titulo{
    font-size: 20px;
    margin: 30px 0px 0px 40px ;
}

.subtitulo{
    font-size: 14px;
    margin: 0px 0px 0px 40px;
    color: #a0a0a0;
}

.chips{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin:0px 60px;
}
</style>