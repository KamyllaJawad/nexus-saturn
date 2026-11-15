<script setup lang="ts">
// App da família da Sarah: frases prontas, com o atraso da missão. Nunca sinais
// vitais, diagnóstico, humor ou ciclo.
import { computed } from 'vue'
import { pedir } from '@/servicos/api'
import { usarConsulta } from '@/servicos/consulta'
import { hora, nome } from '@/servicos/formato'

interface Feed {
  frase: string
  tripulacao: Record<string, string>
  ultimas: { frase: string; gerado_em: string; recebido_em: string }[]
  atraso: string
  sem_sinal: boolean
  dado_de: string | null
  elo: { estufa_nivel: number; estufa_pct: number; brinde: string | null; corrida: string }
  enviadas: { rotulo: string; estado: string; entregue_em?: string; falta_s?: number }[]
}

const feed = usarConsulta<Feed>(() => '/familia/feed')
const d = computed(() => feed.dados.value)
const medico = computed(() => !!d.value?.frase.includes('equipe médica'))
const outros = computed(() => Object.entries(d.value?.tripulacao ?? {}).filter(([k]) => k !== 'sarah'))
const BRINDE: Record<string, string> = {
  enviado: 'Convite a caminho da nave.',
  chegou: 'A Sarah recebeu seu convite. Quando ela beber, a confirmação viaja de volta.',
  feito: 'Brinde concluído: vocês beberam juntas, cada uma no seu planeta.',
}
const acao = (tipo: string) => feed.executar(() => pedir('/familia/acao', { tipo }))
</script>

<template>
  <main class="familia">
    <header class="topo">
      <div>
        <h1>Terra-Órbita</h1>
        <p class="subtitulo">App da família da Sarah</p>
      </div>
      <p v-if="d" class="onde">
        Terra<template v-if="d.dado_de"> · notícia de {{ hora(d.dado_de) }}</template><br />atraso {{ d.atraso }}
      </p>
    </header>

    <div class="fone">
      <template v-if="d">
        <section class="heroi" :class="{ semsinal: d.sem_sinal, med: medico }">
          <span class="etiqueta">Sarah · Comandante</span>
          <p class="frase">{{ d.frase }}</p>
          <p v-if="!d.sem_sinal" class="nota">
            As notícias da nave chegam com {{ d.atraso }} de atraso, o tempo que o sinal leva para viajar.
          </p>
        </section>

        <div class="selos">
          <span v-for="[k, v] in outros" :key="k" class="selo">{{ nome(k) }}: {{ v === 'bem' ? 'bem' : 'acompanhada' }}</span>
        </div>

        <section class="cartao">
          <h3>Últimas da nave</h3>
          <ul v-if="d.ultimas.length" class="pacotes">
            <li v-for="(i, n) in d.ultimas" :key="n" class="p3">
              <time>saiu da nave {{ hora(i.gerado_em, true) }} · chegou {{ hora(i.recebido_em, true) }}</time>{{ i.frase }}
            </li>
          </ul>
          <p v-else class="nota">Nada novo por enquanto.</p>
        </section>

        <section class="cartao">
          <h3>Elo Terra · estufa da tripulação</h3>
          <div class="barra"><i :style="{ width: `${d.elo.estufa_pct}%` }"></i></div>
          <p class="nota espaco">
            Hábitos saudáveis da tripulação e da família fazem a estufa crescer. Ninguém joga sozinho e ninguém perde. {{ d.elo.corrida }}
          </p>
          <p v-if="d.elo.brinde && BRINDE[d.elo.brinde]" class="nota c-acento">{{ BRINDE[d.elo.brinde] }}</p>
          <div class="acoes">
            <button type="button" class="btn agua sm" @click="acao('brinde')">Brindar com a Sarah</button>
            <button type="button" class="btn sm" @click="acao('corrida')">Registrar corrida do Lucas</button>
            <button type="button" class="btn sm" @click="acao('mensagem')">Enviar áudio do Lucas</button>
          </div>
        </section>

        <section class="cartao">
          <h3>Enviado para a nave</h3>
          <ul v-if="d.enviadas.length" class="pacotes">
            <li v-for="(p, n) in d.enviadas" :key="n" class="p4">
              <time>{{
                p.estado === 'entregue'
                  ? `entregue ${hora(p.entregue_em, true)}`
                  : p.estado === 'fila'
                    ? 'guardado: sem sinal, segue quando o contato voltar'
                    : `a caminho · chega em ${p.falta_s} s`
              }}</time
              >{{ p.rotulo }}
            </li>
          </ul>
          <p v-else class="nota">Cada mensagem leva {{ d.atraso }} para chegar.</p>
        </section>
        <p v-if="feed.erro.value" class="aviso-faixa erro" role="alert">{{ feed.erro.value }}</p>
      </template>
      <p v-else class="aviso-faixa offline">Aguardando notícias da nave (a API não respondeu).</p>
    </div>
    <p class="nota legenda">
      A família recebe frases prontas, com o atraso da missão. Nunca sinais vitais, diagnóstico, humor ou ciclo.
    </p>
  </main>
</template>

<style scoped>
.familia {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 16px;
}
.topo {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  width: min(420px, 100%);
}
.topo h1 {
  font-size: 20px;
}
.subtitulo {
  margin-top: 4px;
  font-size: 13px;
  color: #c4b5fd;
}
.onde {
  text-align: right;
  font: 500 11px var(--mono);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #c4b5fd;
}
.fone {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: min(420px, 100%);
  padding: 18px 16px;
  border-radius: 32px;
  border: 1px solid var(--linha-forte);
  background: linear-gradient(170deg, #1a2440, #0b1120 70%);
  box-shadow: 0 30px 70px rgba(0, 0, 0, 0.45);
}
.heroi {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 185, 129, 0.4);
  background: linear-gradient(140deg, rgba(16, 185, 129, 0.12), var(--superficie) 70%);
}
.heroi.med {
  border-color: rgba(245, 158, 11, 0.5);
  background: linear-gradient(140deg, rgba(245, 158, 11, 0.12), var(--superficie) 70%);
}
.heroi.semsinal {
  border-color: rgba(148, 163, 184, 0.4);
  background: var(--superficie);
}
.frase {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.35;
}
.espaco {
  margin-top: 6px;
}
.legenda {
  max-width: 420px;
  text-align: center;
}
</style>
