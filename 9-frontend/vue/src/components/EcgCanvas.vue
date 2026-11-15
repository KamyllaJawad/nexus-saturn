<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { GeradorEcg, type ClasseRitmo } from '@/ecg/gerador'
import { TocadorEcg, type TrechoEcg } from '@/ecg/tocador'
import type { NivelSaude } from '@/mocks/tripulacao'

const props = defineProps<{
  fc: number
  ritmo: ClasseRitmo
  nivel: NivelSaude
  nome: string 
  // Trecho real do relógio (CinC 2017). Sem ele, o desenho é sintético.
  trecho?: TrechoEcg | null
}>()

const VARIAVEL_COR = ['--ok', '--warn', '--crit'] as const
const LARGURA_FALHA = 10

const canvas = ref<HTMLCanvasElement | null>(null)
const gerador = new GeradorEcg()
let tocador = new TocadorEcg()
const origem = ref('')

// Trocar de pessoa recomeça o traçado; um trecho novo da mesma pessoa entra no fim do atual.
watch(() => props.nome, () => (tocador = new TocadorEcg()))
watch(
  () => props.trecho,
  (t) => {
    if (t) tocador.carregar(t)
  },
  { immediate: true },
)
const real = () => !!props.trecho && tocador.pronto
let cor = '#10b981'
let idAnimacao = 0
let ultimoQuadro = 0


function atualizarCor() {
  if (!canvas.value) return
  const valor = getComputedStyle(canvas.value).getPropertyValue(VARIAVEL_COR[props.nivel]).trim()
  if (valor) cor = valor
}
watch(() => props.nivel, atualizarCor)

function desenhar(ctx: CanvasRenderingContext2D, el: HTMLCanvasElement) {
  const dpr = window.devicePixelRatio || 1
  const w = el.clientWidth
  const h = el.clientHeight
  if (!w || !h) return
  if (el.width !== Math.round(w * dpr) || el.height !== Math.round(h * dpr)) {
    el.width = Math.round(w * dpr)
    el.height = Math.round(h * dpr)
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, w, h)

  ctx.strokeStyle = 'rgba(148, 163, 184, 0.08)'
  ctx.lineWidth = 1
  ctx.beginPath()
  for (let x = 0; x < w; x += 16) {
    ctx.moveTo(x + 0.5, 0)
    ctx.lineTo(x + 0.5, h)
  }
  for (let y = 0; y < h; y += 16) {
    ctx.moveTo(0, y + 0.5)
    ctx.lineTo(w, y + 0.5)
  }
  ctx.stroke()

  const { buffer, posicao } = real() ? tocador : gerador
  const n = buffer.length
  ctx.strokeStyle = cor
  ctx.lineWidth = 1.7
  ctx.lineJoin = 'round'
  ctx.shadowColor = cor
  ctx.shadowBlur = 6
  ctx.beginPath()
  let tracando = false
  for (let i = 0; i < n; i++) {
    if ((i - posicao + n) % n < LARGURA_FALHA) {
      tracando = false
      continue
    }
    const x = (i / (n - 1)) * w
    const y = h * 0.64 - buffer[i]! * h * 0.52
    if (tracando) ctx.lineTo(x, y)
    else {
      ctx.moveTo(x, y)
      tracando = true
    }
  }
  ctx.stroke()
  ctx.shadowBlur = 0
}

function quadro(agora: number) {
  // Limita o salto a 0,1 s: se a aba ficou em segundo plano, não "acelera" ao voltar.
  const dt = Math.min(0.1, (agora - (ultimoQuadro || agora)) / 1000)
  ultimoQuadro = agora
  if (real()) {
    tocador.avancar(dt)
    origem.value = `ECG do relógio · CinC 2017 (teste) ${tocador.origem}`
  } else {
    gerador.avancar(dt, props.fc, props.ritmo)
    origem.value = 'ECG ilustrativo (sintético)'
  }

  const el = canvas.value
  const ctx = el?.getContext('2d')
  if (el && ctx) desenhar(ctx, el)
  idAnimacao = requestAnimationFrame(quadro)
}

onMounted(() => {
  atualizarCor()
  idAnimacao = requestAnimationFrame(quadro)
})

// Para o loop ao sair da tela; senão ele continuaria rodando para sempre.
onUnmounted(() => cancelAnimationFrame(idAnimacao))
</script>

<template>
  <div class="ecg">
    <canvas
      ref="canvas"
      role="img"
      :aria-label="`ECG ao vivo de ${nome}: ${fc} bpm, ritmo ${ritmo === 'fa' ? 'irregular (fibrilação atrial)' : 'regular'}`"
    ></canvas>
    <small class="origem">{{ origem }}</small>
  </div>
</template>

<style scoped>
.ecg {
  position: relative;
  border-radius: 12px;
  border: 1px solid var(--linha);
  background: #05070e;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 110px;
}

.origem {
  position: absolute;
  right: 10px;
  bottom: 6px;
  font-family: ui-monospace, monospace;
  font-size: 10px;
  color: var(--texto-fraco);
}
</style>
