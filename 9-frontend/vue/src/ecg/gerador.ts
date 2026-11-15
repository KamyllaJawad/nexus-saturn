// Gerador de ECG sintético.
//
// Não é um ECG real: é um desenho matemático de cada batimento, feito para
// ilustrar o estado do tripulante na tela. Quem decide a FC e o ritmo é o back
// (ou o mock). Este arquivo só transforma esses dados em uma onda.
//
// Cada batimento é a soma de "sinos" (curvas gaussianas), um para cada onda:
//   P   → átrios se contraem        (pequena, positiva)
//   QRS → ventrículos se contraem   (Q e S para baixo, R é o pico alto)
//   T   → ventrículos se recuperam  (média, positiva)

// Mesmo nome usado no contrato do back (m1.classe em analise-fa.json).
export type ClasseRitmo = 'normal' | 'fa'

export const AMOSTRAS_POR_SEGUNDO = 150

// Um "sino" centrado em `centro`, com altura `altura` e largura `largura` (em segundos).
function sino(t: number, centro: number, altura: number, largura: number): number {
  return altura * Math.exp(-((t - centro) ** 2) / (2 * largura ** 2))
}

/**
 * Valor do ECG num instante do batimento.
 * @param t tempo desde o início do batimento atual (s)
 * @param rr duração do batimento atual (s) = 60 / FC
 * @param classe ritmo normal ou fibrilação atrial
 * @param tempoTotal tempo desde o início da gravação (s), usado no tremor da FA
 */
export function valorEcg(
  t: number,
  rr: number,
  classe: ClasseRitmo,
  tempoTotal: number,
  aleatorio: () => number = Math.random,
): number {
  // Batimentos curtos (FC alta) ficam "espremidos" para caber.
  const k = Math.min(1, rr / 0.8)

  let v =
    sino(t, 0.2 * k, -0.1, 0.01 * k) + // Q
    sino(t, 0.23 * k, 1, 0.011 * k) + // R
    sino(t, 0.26 * k, -0.22, 0.012 * k) + // S
    sino(t, 0.46 * k, 0.28, 0.045 * k) // T

  if (classe === 'fa') {
    // Na FA a onda P some: no lugar dela, os átrios "tremem" (ondas f).
    v += 0.05 * Math.sin(tempoTotal * 2 * Math.PI * 6.5) + (aleatorio() - 0.5) * 0.05
  } else {
    v += sino(t, 0.1 * k, 0.12, 0.025 * k) // P
  }
  return v
}

/**
 * Gera o ECG continuamente e guarda as últimas amostras num buffer circular
 * (quando chega ao fim, volta a escrever do começo, como no monitor do hospital).
 */
export class GeradorEcg {
  readonly buffer: Float32Array
  /** Próxima posição do buffer a ser escrita. */
  posicao = 0

  private tempoNoBatimento = 0
  private rr = 0.83
  private tempoTotal = 0
  private pendente = 0

  constructor(
    tamanho = 600,
    private readonly aleatorio: () => number = Math.random,
  ) {
    this.buffer = new Float32Array(tamanho)
  }

  /** Avança o relógio do gerador em `segundos`, escrevendo as amostras novas. */
  avancar(segundos: number, fc: number, classe: ClasseRitmo): void {
    this.pendente += segundos * AMOSTRAS_POR_SEGUNDO
    const passo = 1 / AMOSTRAS_POR_SEGUNDO

    while (this.pendente >= 1) {
      this.pendente--
      this.tempoTotal += passo
      this.tempoNoBatimento += passo

      if (this.tempoNoBatimento >= this.rr) {
        this.tempoNoBatimento -= this.rr
        this.rr = this.proximoRR(fc, classe)
      }

      this.buffer[this.posicao] = valorEcg(
        this.tempoNoBatimento,
        this.rr,
        classe,
        this.tempoTotal,
        this.aleatorio,
      )
      this.posicao = (this.posicao + 1) % this.buffer.length
    }
  }

  // Duração do próximo batimento.
  private proximoRR(fc: number, classe: ClasseRitmo): number {
    const base = 60 / Math.max(30, fc)
    // Normal: varia só ±3% (variação natural).
    // FA: varia de 60% a 140%, o "irregularmente irregular" típico da fibrilação.
    return classe === 'fa'
      ? base * (0.6 + this.aleatorio() * 0.8)
      : base * (0.97 + this.aleatorio() * 0.06)
  }
}
