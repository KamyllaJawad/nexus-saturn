<script setup lang="ts">
// Painel de bordo do oficial médico (ou do Marcus como CMO, sem médico a bordo).
// Tudo o que o bordo/ em JS puro fazia, no visual do painel da Isabelle.
import { computed, onUnmounted, ref, shallowRef, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import PainelHeader from '../components/PainelHeader.vue'
import ListaTripulacao from '../components/ListaTripulacao.vue'
import PacienteHeader from '../components/PacienteHeader.vue'
import EcgCanvas from '../components/EcgCanvas.vue'
import GradeSinais from '../components/GradeSinais.vue'
import CardSilhueta from '../components/CardSilhueta.vue'
import CardDecisao from '../components/CardDecisao.vue'
import ChatCosmo from '../components/ChatCosmo.vue'
import EventoBordo from '../components/EventoBordo.vue'
import TrilhaCosmo from '../components/TrilhaCosmo.vue'
import { DECISOES, type Acao } from '@/mocks/decisoes'
import { usarBordo } from '@/servicos/bordo'
import { buscarEcg } from '@/servicos/api'
import { ajustarEquipe, embutida, hora, num, SINAL } from '@/servicos/formato'
import type { TrechoEcg } from '@/ecg/tocador'

const { tripulantes, status, bordo, erro, conexao, decidir, decidirCorpo } = usarBordo()
// /#/bordo?quem=kenji abre o painel já nessa pessoa.
const selecionado = ref(String(useRoute().query.quem ?? 'sarah'))
const acoesFeitas = ref<Record<string, string>>({})

const tripulante = computed(() => tripulantes.value.find((t) => t.id === selecionado.value) ?? tripulantes.value[0]!)
const bruto = computed(() => bordo.value?.tripulantes.find((t) => t.tripulante_id === selecionado.value))
const terra = computed(() => bordo.value?.missao.equipe.local === 'terra')
watch(() => bordo.value?.missao.equipe, (eq) => ajustarEquipe(eq))

// Um alerta de arritmia novo leva o painel direto para a pessoa.
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

// Offline: o card de decisão do protótipo, com os mocks.
async function registrarAcao(acao: Acao) {
  try {
    await decidir(acao)
    acoesFeitas.value[acao.chave] = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch {
    // a mensagem fica em `erro`
  }
}

const sombra = computed(() => Object.entries(bordo.value?.sombra ?? {}))
const saudacao = computed(() =>
  terra.value
    ? 'Sou a Cosmo de bordo. Sem médico a bordo, eu ajudo o CMO com as ações seguras; a decisão médica é da Dra. Rivera, em Houston.'
    : 'Bom dia, Dr. Marcus. Estou rodando no computador da nave, sem depender da Terra. As perguntas do cenário em curso aparecem em “Agora”.',
)
</script>

<template>
  <PainelHeader :status="status" />
  <p v-if="conexao === 'offline'" class="aviso-faixa offline" role="status">
    Modo offline: a API não respondeu, então a tela mostra dados de exemplo. Ela volta sozinha quando a API responder.
  </p>
  <p v-if="erro" class="aviso-faixa erro" role="alert">{{ erro }}</p>
  <div class="layout">
    <div class="esquerda">
      <ListaTripulacao v-model="selecionado" :tripulantes="tripulantes" />
      <section v-if="sombra.length" class="cartao sombra">
        <h3>Modelo em modo sombra</h3>
        <p v-for="[p, v] in sombra" :key="p" class="nota">
          <b class="c-acento">{{ v.versao }}</b> roda em paralelo, sem agir: {{ v.leituras }} leituras, {{ v.divergem }} divergências do
          modelo em serviço.
        </p>
        <div class="acoes">
          <RouterLink v-if="!embutida" to="/dados-ia" class="btn sm">Revisar e aprovar</RouterLink>
          <a v-else href="#/dados-ia" target="_top" class="btn sm">Revisar e aprovar</a>
        </div>
      </section>
    </div>

    <main>
      <PacienteHeader :tripulante="tripulante" />
      <p v-if="bruto" class="meta">
        Leitura de {{ hora(bruto.gerada_em, true) }} · cada faixa compara {{ bruto.nome }} com a própria linha de base (z robusto
        {{ bruto.versao_z }}).
      </p>
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

      <!-- O que os modelos dizem desta pessoa agora -->
      <section v-if="bruto && bruto.m2 && bruto.isolation_forest" class="cartao modelos" aria-label="Saída dos modelos">
        <div>
          <span class="etiqueta">M2 · {{ bruto.m2.versao_modelo }}</span>
          <p>
            Sinal
            <b :class="bruto.m2.qualidade === 'bom' ? 'c-ok' : 'c-warn'">{{ bruto.m2.qualidade === 'bom' ? 'bom' : 'suspeito' }}</b>
            ({{ num(bruto.m2.confianca, 2) }})<template v-if="bruto.m2.motivo"> · {{ bruto.m2.motivo }}</template>
          </p>
        </div>
        <div v-if="bruto.m1">
          <span class="etiqueta">M1 · {{ bruto.m1.versao_modelo }}</span>
          <p v-if="bruto.m1.classe">
            Ritmo:
            <b :class="{ 'c-crit': bruto.m1.classe === 'fa' }">{{
              bruto.m1.classe === 'fa' ? 'fibrilação atrial' : bruto.m1.classe === 'outro' ? 'outro ritmo' : 'normal'
            }}</b>
            · P(FA) {{ num(bruto.m1.prob_fa, 2) }}
          </p>
          <p v-else class="c-warn">{{ bruto.m1.motivo }}</p>
        </div>
        <div>
          <span class="etiqueta">M3 floresta · {{ bruto.isolation_forest.versao_modelo }}</span>
          <p>
            Escore {{ num(bruto.isolation_forest.score, 3) }} · limiar {{ num(bruto.isolation_forest.limiar, 3) }} ·
            <template v-if="bruto.isolation_forest.anomalo">
              <span class="c-warn">combinação fora do padrão</span
              ><template v-if="bruto.isolation_forest.evidencias.length"
                >: {{ bruto.isolation_forest.evidencias.map((k) => SINAL[k] ?? k).join(', ') }}</template
              >
            </template>
            <template v-else-if="bruto.isolation_forest.acima_do_limiar">
              acima do limiar há {{ bruto.isolation_forest.seguidas }} de {{ bruto.isolation_forest.persistencia }} leituras
            </template>
            <template v-else>combinação no padrão</template>
          </p>
        </div>
        <div v-if="bruto.sombra?.['m3-if']">
          <span class="etiqueta">sombra · {{ bruto.sombra['m3-if'].versao_modelo }}</span>
          <p>
            Escore {{ num(bruto.sombra['m3-if'].score, 3) }} ·
            {{ bruto.sombra['m3-if'].anomalo ? 'marcaria anomalia' : 'não marcaria anomalia' }} · não age
          </p>
        </div>
      </section>

      <!-- Decisões: com a API, os eventos reais; offline, o card do protótipo -->
      <section v-if="bordo" class="pilha" aria-label="Decisões">
        <h2 class="secao">Decisões</h2>
        <EventoBordo
          v-for="ev in bordo.eventos"
          :key="ev.id"
          :evento="ev"
          :missao="bordo.missao"
          :tripulantes="bordo.tripulantes"
          @decidir="decidirCorpo"
        />
        <p v-if="!bordo.eventos.length" class="cartao nota">Nenhuma decisão pendente.</p>

        <h2 class="secao">Compartilhado pela tripulação</h2>
        <template v-if="bordo.avisos_compartilhados.length">
          <article v-for="a in bordo.avisos_compartilhados" :key="a.id" class="cartao roxo">
            <template v-if="a.tipo === 'ciclo'">
              <h4>{{ a.nome }} compartilhou um aviso</h4>
              <p>
                Ela pode ter cólica, inchaço ou humor mais baixo neste trecho e pediu cuidado leve. O estado segue como está. Não é
                diagnóstico. Analgésico do kit só se ela pedir, em passo separado.
              </p>
              <p class="meta">Você vê só isto. Houston e a família não recebem.</p>
            </template>
            <template v-else>
              <h4>{{ a.nome }} · combinação fora do padrão <span class="selo">nível 1</span></h4>
              <p>
                {{ a.nome }} respondeu que não está bem. Sinais que mais pesaram:
                {{ (a.sugestao?.evidencias ?? []).map((k) => SINAL[k] ?? k).join(', ') || 'combinação' }}. Nenhum sinal crítico sozinho; é
                informação, não evento clínico.
              </p>
              <p class="meta">{{ a.sugestao?.versao_modelo }} · {{ hora(a.gerado_em, true) }}</p>
            </template>
          </article>
        </template>
        <p v-else class="cartao nota">
          {{
            terra
              ? `Sem médico a bordo, saúde mental e ciclo não chegam a este painel: com consentimento, vão só para a ${bordo.missao.equipe.medico_nome}, em Houston.`
              : 'Ninguém compartilhou um aviso. Saúde mental e ciclo só chegam aqui com consentimento.'
          }}
        </p>

        <h2 class="secao">Trilha da Cosmo · auditoria</h2>
        <div class="cartao"><TrilhaCosmo :trilha="bordo.trilha_cosmo" superficie="bordo" /></div>
      </section>
      <CardDecisao v-else :card="DECISOES[tripulante.id]!" :feitas="acoesFeitas" @acao="registrarAcao" />
    </main>

    <ChatCosmo
      class="chat"
      :tripulante="tripulante"
      superficie="bordo"
      :titulo="terra ? 'Cosmo · copiloto do CMO' : 'Cosmo · copiloto médico'"
      :saudacao="saudacao"
    />
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 360px;
  min-height: calc(100vh - 200px);
  border-top: 1px solid var(--linha);
}
.esquerda {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-right: 1px solid var(--linha);
}
.esquerda :deep(.lista) {
  border-right: 0;
}
.sombra {
  margin: 0 10px 12px;
}

main {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  padding: 16px 24px;
}

.sinais-e-corpo {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  align-items: start;
  gap: 12px;
}

.modelos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px 16px;
}
.modelos p {
  margin-top: 3px;
  font-size: 12.5px;
}

.secao {
  margin-top: 6px;
  font-size: 15px;
  font-weight: 600;
}

/* Chat fixo à direita enquanto o centro rola */
.chat {
  align-self: start;
  position: sticky !important;
  top: 52px;
  height: calc(100vh - 64px);
  min-height: 520px;
}

/* Telas mais estreitas, como o iframe da sala de simulação (~620 px):
   o chat desce e, abaixo de 820 px, tudo vira uma coluna. */
@media (max-width: 1180px) {
  .layout {
    grid-template-columns: 200px minmax(0, 1fr);
  }
  .chat {
    grid-column: 1 / -1;
    position: relative !important;
    height: 460px;
    border-left: 0;
    border-top: 1px solid var(--linha);
  }
}
@media (max-width: 820px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .esquerda {
    border-right: 0;
    border-bottom: 1px solid var(--linha);
  }
  .esquerda :deep(.lista) {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .esquerda :deep(.item) {
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
</style>
