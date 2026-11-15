// Toca um trecho de ECG real (CinC 2017, via GET /api/tripulantes/{id}/ecg) no mesmo
// buffer circular do GeradorEcg, para o EcgCanvas desenhar os dois do mesmo jeito.
// O trecho repete em loop; um trecho novo entra quando o atual termina, sem salto.

import { AMOSTRAS_POR_SEGUNDO } from './gerador'

export interface TrechoEcg {
  fs: number
  origem: string
  amostras: number[]
}

/** Centra na mediana e escala para o pico R ficar perto de 1, como no gerador. */
export function normalizar(amostras: number[]): Float32Array {
  const saida = new Float32Array(amostras.length)
  if (!amostras.length) return saida
  const ordenadas = [...amostras].sort((a, b) => a - b)
  const mediana = ordenadas[Math.floor(ordenadas.length / 2)]!
  const alto = ordenadas[Math.floor(ordenadas.length * 0.99)]!
  const escala = alto - mediana || 1
  for (let i = 0; i < amostras.length; i++) {
    saida[i] = Math.max(-0.6, Math.min(1.2, (amostras[i]! - mediana) / escala))
  }
  return saida
}

export class TocadorEcg {
  readonly buffer: Float32Array
  posicao = 0
  origem = ''

  private atual: Float32Array | null = null
  private proximo: { sinal: Float32Array; fs: number; origem: string } | null = null
  private fs = 100
  private leitura = 0 // posição no trecho atual, em amostras de origem
  private pendente = 0

  constructor(tamanho = 600) {
    this.buffer = new Float32Array(tamanho)
  }

  get pronto() {
    return this.atual !== null || this.proximo !== null
  }

  carregar(trecho: TrechoEcg): void {
    const novo = { sinal: normalizar(trecho.amostras), fs: trecho.fs, origem: trecho.origem }
    if (!this.atual) this.trocar(novo)
    else this.proximo = novo
  }

  avancar(segundos: number): void {
    if (!this.atual && this.proximo) this.trocar(this.proximo)
    if (!this.atual) return
    this.pendente += segundos * AMOSTRAS_POR_SEGUNDO
    const passo = this.fs / AMOSTRAS_POR_SEGUNDO
    while (this.pendente >= 1) {
      this.pendente--
      this.leitura += passo
      if (this.leitura >= this.atual.length) {
        this.leitura -= this.atual.length
        if (this.proximo) {
          this.trocar(this.proximo)
          this.leitura = 0
        }
      }
      this.buffer[this.posicao] = this.atual[Math.floor(this.leitura)] ?? 0
      this.posicao = (this.posicao + 1) % this.buffer.length
    }
  }

  private trocar(t: { sinal: Float32Array; fs: number; origem: string }) {
    this.atual = t.sinal
    this.fs = t.fs
    this.origem = t.origem
    this.proximo = null
  }
}
