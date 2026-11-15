<script setup lang="ts">
// Dados e IA: do sensor ao modelo, com o humano no circuito. Lakehouse, métricas
// medidas, rótulo → retreino → modo sombra → aprovação médica e auditoria encadeada.
import { computed, ref, watch } from 'vue'
import { pedir } from '@/servicos/api'
import { usarConsulta } from '@/servicos/consulta'
import { ajustarEquipe, hora, nome, num, TRIPULACAO } from '@/servicos/formato'

/* eslint-disable @typescript-eslint/no-explicit-any */
const painel = usarConsulta<Record<string, any>>(() => '/ia/painel', 2500)
const quem = ref('sarah')
const analise = usarConsulta<Record<string, any>>(() => `/ia/analise/${quem.value}`, 1500)
const auditoria = usarConsulta<Record<string, any>>(() => '/auditoria?limite=14', 1500)
const missao = usarConsulta<Record<string, any>>(() => '/missao', 1500)

const p = computed(() => painel.dados.value)
watch(() => p.value?.equipe, (eq) => ajustarEquipe(eq))
// Quem aprova é o médico da missão: o Dr. Marcus a bordo ou, sem médico a bordo, a Dra. Rivera.
const medico = computed(() => p.value?.equipe?.medico_id ?? 'marcus')
const outro = computed(() => (medico.value === 'marcus' ? 'kenji' : 'marcus'))

const ocupado = ref<string | null>(null)
async function retreinar(peca: string) {
  ocupado.value = peca
  try {
    await painel.executar(() => pedir('/ia/retreinar', { peca, humano_id: medico.value }))
  } finally {
    ocupado.value = null
  }
}
const modelo = (peca: string, acao: 'aprovar' | 'rejeitar', humano_id = medico.value) =>
  painel.executar(() => pedir(`/ia/modelos/${peca}/${acao}`, { peca, humano_id }))

const linhas = (itens: any[] = []) => itens

const AJUDA: Record<string, string> = {
  m1: 'Nasce quando o médico confirma ou recusa um alerta de arritmia.',
  m2: 'Nasce quando a pessoa ajusta o relógio ou o kit confirma a leitura.',
  'm3-if': 'Nasce quando a pessoa responde ao aviso de combinação fora do padrão.',
}
function resumo(peca: string, x: any): string {
  if (!x) return ''
  if (peca === 'm1')
    return `F1 FA ${num(x.f1_fa, 3)} · recall ${num(x.recall_fa, 2)} · precisão ${num(x.precisao_fa, 2)} · ${x.rotulos_humanos} rótulo(s) humano(s)`
  if (peca === 'm2') return `recall suspeito ${num(x.recall_suspeito, 3)} · precisão ${num(x.precisao_suspeito, 3)} · ${x.rotulos_humanos} rótulo(s) humano(s)`
  return Object.entries(x.por_tripulante ?? {})
    .map(([t, v]: [string, any]) => {
      const r = (v.rotulos_humanos?.normal ?? 0) + (v.rotulos_humanos?.anomalia ?? 0)
      return `${nome(t)}: limiar ${num(v.limiar, 3)}, recall 3 sinais ${num(v.recall_desvio_em_3_sinais, 2)}${r ? `, ${r} leituras rotuladas` : ''}`
    })
    .join(' · ')
}
function situacaoTerra(x: any): { texto: string; classe: string } {
  if (x.estado === 'aplicada') return { texto: `chegou às ${hora(x.chegou_em, true)} e foi aplicada`, classe: 'c-ok' }
  if (x.estado === 'não aplicada') return { texto: `chegou, mas não se aplicou: ${x.motivo}`, classe: 'c-warn' }
  if (x.pacote_estado === 'fila') return { texto: 'na fila: sem sinal', classe: 'c-warn' }
  return { texto: `a caminho · chega a bordo em ${x.falta_s} s`, classe: '' }
}
const pecas = computed(() =>
  Object.entries(p.value?.pecas ?? {}).map(([peca, rotulo]) => {
    const daTerra = (p.value?.decisoes_modelo ?? []).filter((x: any) => x.peca === peca)
    return {
      peca,
      rotulo: rotulo as string,
      rt: p.value?.rotulos[peca],
      cand: p.value?.candidatos[peca],
      sb: p.value?.sombra[peca],
      at: p.value?.ativos[peca],
      daTerra,
      aCaminho: daTerra.some((x: any) => x.estado === 'a caminho'),
    }
  }),
)
</script>

<template>
  <main class="dados">
    <header class="topo">
      <div>
        <h1>Dados e IA</h1>
        <p class="subtitulo">Do sensor ao modelo · humano no circuito</p>
      </div>
      <p v-if="missao.dados.value" class="onde">Hora da nave {{ hora(missao.dados.value.hora_nave, true) }}</p>
    </header>
    <p v-if="!p" class="aviso-faixa offline">Aguardando a API: esta tela mostra os dados e os modelos que estão rodando nela.</p>
    <p v-if="painel.erro.value" class="aviso-faixa erro" role="alert">{{ painel.erro.value }}</p>

    <template v-if="p">
      <!-- 1 · Caminho do dado -->
      <section class="cartao">
        <h3>1 · Caminho do dado</h3>
        <div class="zonas">
          <div class="zona bronze">
            <h4>Bronze · cru, só inclusão</h4>
            <ul>
              <li v-for="i in linhas(p.zonas.bronze)" :key="i.nome">
                <span class="mono">{{ i.nome }}</span> · {{ num(i.linhas) }}<template v-if="i.origem"> · origem {{ i.origem }}</template>
              </li>
            </ul>
          </div>
          <div class="zona prata">
            <h4>Prata · tratado</h4>
            <ul>
              <li v-for="i in linhas(p.zonas.prata)" :key="i.nome"><span class="mono">{{ i.nome }}</span> · {{ num(i.linhas) }}</li>
            </ul>
            <p class="nota">
              Unidade e faixa física, picos R, atributos e split {{ p.lote.ecg.split.treino }}/{{ p.lote.ecg.split.validacao }}/{{
                p.lote.ecg.split.teste
              }}
              por gravação. {{ p.lote.vitais.suspeitas }} leituras ficaram como suspeitas.
            </p>
          </div>
          <div class="zona ouro">
            <h4>Ouro · uma tabela por modelo</h4>
            <ul>
              <li v-for="i in linhas(p.zonas.ouro)" :key="i.nome"><span class="mono">{{ i.nome }}</span> · {{ num(i.linhas) }}</li>
            </ul>
            <p class="nota">Amostra suspeita, FA e relógio folgado não treinam a floresta. Ciclo e sintoma não entram em atributo.</p>
          </div>
          <div class="zona art">
            <h4>Artefatos · sobem para a nave</h4>
            <ul>
              <li v-for="(v, k) in p.versoes.ativos" :key="k"><span class="mono">{{ v }}</span></li>
            </ul>
            <p class="nota">Lote {{ p.lote.id }}. Treino em lote; a leitura de 1 Hz não atualiza peso nenhum.</p>
          </div>
        </div>
        <p class="nota espaco">
          ECG:
          <template v-if="p.lote.ecg.origem === 'cinc'">
            PhysioNet/CinC 2017, {{ num(p.lote.ecg.gravacoes) }} gravações reais ({{
              Object.entries(p.lote.ecg.classes)
                .map(([k, v]) => `${k} ${num(v)}`)
                .join(', ')
            }})</template
          >
          <template v-else>sintético (o zip do CinC não estava disponível)</template>. Sinais vitais da tripulação: sintéticos, declarados.
          Para o simulador foram separadas {{ p.lote.ecg.banco_simulador.normal + p.lote.ecg.banco_simulador.fa }} gravações do conjunto de
          teste, que nenhum modelo viu no treino.
        </p>
      </section>

      <!-- 2 · Modelos com a métrica medida -->
      <section class="cartao">
        <h3>2 · Modelos em serviço, com a métrica medida</h3>
        <div class="duas">
          <article class="cartao interno">
            <h4>
              M1 · {{ p.versoes.ativos.m1 }}
              <span class="selo" :class="p.relatorio.m1.metricas.bateu_meta ? 'ok' : 'warn'">{{
                p.relatorio.m1.metricas.bateu_meta ? 'meta batida' : 'meta não batida'
              }}</span>
            </h4>
            <p>{{ p.relatorio.m1.algoritmo }} sobre {{ Object.keys(p.relatorio.m1.metricas.importancias).length }} atributos de RR.</p>
            <div class="kv">
              <div><span>F1 da FA no teste</span><b>{{ num(p.relatorio.m1.metricas.f1_fa, 3) }}</b></div>
              <div>
                <span>IC 95%</span><b>{{ p.relatorio.m1.metricas.f1_fa_ic95.map((x: number) => num(x, 2)).join(' a ') }}</b>
              </div>
              <div><span>F1 na validação</span><b>{{ num(p.relatorio.m1.metricas.f1_fa_validacao, 3) }}</b></div>
              <div>
                <span>Recall / precisão</span><b>{{ num(p.relatorio.m1.metricas.recall_fa, 2) }} / {{ num(p.relatorio.m1.metricas.precisao_fa, 2) }}</b>
              </div>
            </div>
            <div class="rolagem">
              <table class="tabela">
                <tr>
                  <th>verdade \ previsto</th>
                  <th v-for="r in p.relatorio.m1.metricas.matriz_confusao.rotulos" :key="r">{{ r }}</th>
                </tr>
                <tr v-for="(l, i) in p.relatorio.m1.metricas.matriz_confusao.valores" :key="i">
                  <td>{{ p.relatorio.m1.metricas.matriz_confusao.rotulos[i] }}</td>
                  <td v-for="(v, j) in l" :key="j" class="n" :class="{ 'c-ok': i === j }">{{ v }}</td>
                </tr>
              </table>
            </div>
            <p class="meta">
              Meta: {{ p.relatorio.m1.metricas.meta }}. O limiar ({{ p.relatorio.m1.metricas.limiar_fa }}) foi escolhido na validação, nunca no
              teste. Mais pesam: {{ Object.keys(p.relatorio.m1.metricas.importancias).slice(0, 3).join(', ') }}.
            </p>
          </article>

          <article class="cartao interno">
            <h4>
              M2 · {{ p.versoes.ativos.m2 }}
              <span class="selo" :class="p.relatorio.m2.metricas.bateu_meta ? 'ok' : 'warn'">{{
                p.relatorio.m2.metricas.bateu_meta ? 'meta batida' : 'meta não batida'
              }}</span>
            </h4>
            <p>
              Estimador escolhido por medição: {{ String(p.relatorio.m2.metricas.estimador_escolhido).replace('_', ' ') }} (precisão na validação:
              {{
                Object.entries(p.relatorio.m2.metricas.comparacao)
                  .map(([k, v]: [string, any]) => `${k.replace('_', ' ')} ${num(v.precisao_validacao, 2)}`)
                  .join(' · ')
              }}).
            </p>
            <div class="kv">
              <div><span>Recall de suspeito</span><b>{{ num(p.relatorio.m2.metricas.recall_suspeito, 3) }}</b></div>
              <div><span>Precisão</span><b>{{ num(p.relatorio.m2.metricas.precisao_suspeito, 3) }}</b></div>
              <div><span>Bom marcado suspeito</span><b>{{ num(p.relatorio.m2.metricas.falso_suspeito_em_bom * 100, 1) }}%</b></div>
              <div><span>Limiar</span><b>{{ p.relatorio.m2.metricas.limiar }}</b></div>
            </div>
            <div class="rolagem">
              <table class="tabela">
                <tr>
                  <th>verdade \ previsto</th>
                  <th v-for="r in p.relatorio.m2.metricas.matriz_confusao.rotulos" :key="r">{{ r }}</th>
                </tr>
                <tr v-for="(l, i) in p.relatorio.m2.metricas.matriz_confusao.valores" :key="i">
                  <td>{{ p.relatorio.m2.metricas.matriz_confusao.rotulos[i] }}</td>
                  <td v-for="(v, j) in l" :key="j" class="n" :class="{ 'c-ok': i === j }">{{ v }}</td>
                </tr>
              </table>
            </div>
            <p class="meta">Meta: {{ p.relatorio.m2.metricas.meta }}. Preferimos perguntar demais a alarmar errado.</p>
          </article>

          <article class="cartao interno">
            <h4>
              M3 floresta · {{ p.versoes.ativos['m3-if'] }}
              <span class="selo" :class="p.relatorio['m3-if'].metricas.bateu_meta ? 'ok' : 'warn'">{{
                p.relatorio['m3-if'].metricas.bateu_meta ? 'meta batida' : 'meta não batida'
              }}</span>
            </h4>
            <p>{{ p.relatorio['m3-if'].algoritmo }}.</p>
            <div class="rolagem">
              <table class="tabela">
                <tr>
                  <th>pessoa</th>
                  <th>limiar</th>
                  <th>alarmes/dia</th>
                  <th>recall 2 / 3 / 4 sinais</th>
                </tr>
                <tr v-for="(v, t) in p.relatorio['m3-if'].metricas.por_tripulante" :key="t">
                  <td>{{ nome(String(t)) }}</td>
                  <td class="n">{{ num(v.limiar, 3) }}</td>
                  <td class="n">{{ num(v.alarmes_fora_da_amostra_por_dia, 2) }}</td>
                  <td class="n">
                    {{ num(v.recall_desvio_em_2_sinais, 2) }} / {{ num(v.recall_desvio_em_3_sinais, 2) }} /
                    {{ num(v.recall_desvio_em_4_sinais, 2) }}
                  </td>
                </tr>
              </table>
            </div>
            <p class="meta">
              Meta: {{ p.relatorio['m3-if'].metricas.meta }}. {{ p.relatorio['m3-if'].metricas.limitacao }} Episódios excluídos do treino
              acima do limiar: {{ p.relatorio['m3-if'].metricas.episodios_excluidos.acima_do_limiar }} de
              {{ p.relatorio['m3-if'].metricas.episodios_excluidos.total }}.
            </p>
          </article>

          <article class="cartao interno">
            <h4>M3 z · {{ p.versoes.ativos['m3-z'] }} e calendário do ciclo</h4>
            <p>
              Mediana e MAD de cada tripulante, por sinal: pinta o estado de três níveis. O calendário conta dias da ficha de solo; é regra, não
              modelo treinado.
            </p>
            <p class="meta">A Cosmo é busca local nos protocolos e não aprende com as leituras. O motor, o hash e a fila também não aprendem.</p>
          </article>
        </div>
      </section>

      <!-- 3 · Human-in-the-loop -->
      <section class="cartao">
        <h3>3 · Human-in-the-loop: rótulo → retreino → modo sombra → aprovação médica</h3>
        <p class="nota">
          A decisão clínica fica com o humano, e o aprendizado também: o modelo só muda depois que um humano rotula, pede o retreino e o médico
          da missão aprova (ADR-010).
        </p>
        <article v-for="x in pecas" :key="x.peca" class="cartao interno hitl">
          <h4>
            {{ x.rotulo }} <span class="selo">em serviço: {{ x.at?.versao }}</span>
            <span v-if="x.cand" class="selo warn">em sombra: {{ x.cand.versao }}</span>
          </h4>
          <div class="passo">
            <span class="n">1</span>
            <div>
              <b>Rótulos humanos: {{ x.rt?.total ?? 0 }}</b>
              <span v-for="(v, k) in x.rt?.por_rotulo ?? {}" :key="k" class="selo">{{ k }}: {{ v }}</span>
              <p class="nota">
                <template v-if="x.rt?.ultimos?.length">
                  <template v-for="(u, i) in x.rt.ultimos" :key="i"
                    >{{ hora(u.criado_em, true) }} · {{ nome(u.humano_id) }} rotulou "{{ u.rotulo }}" ({{ u.origem }}, sobre
                    {{ u.versao_modelo }})<br
                  /></template>
                </template>
                <template v-else>{{ AJUDA[x.peca] }}</template>
              </p>
            </div>
          </div>
          <div class="passo">
            <span class="n">2</span>
            <div>
              <button type="button" class="btn principal sm" :disabled="!x.rt?.total || !!ocupado" @click="retreinar(x.peca)">
                {{ ocupado === x.peca ? 'Treinando…' : 'Retreinar com os rótulos humanos' }}
              </button>
              <p class="nota">Ouro + rótulos de bordo → candidato com versão nova. Ele não entra em serviço.</p>
            </div>
          </div>
          <div class="passo">
            <span class="n">3</span>
            <div>
              <b>Modo sombra</b>
              <template v-if="x.cand">
                <p class="nota">Em serviço · {{ resumo(x.peca, x.at) }}</p>
                <p class="nota c-acento">Candidato {{ x.cand.versao }} · {{ resumo(x.peca, x.cand) }}</p>
                <p v-if="x.sb" class="nota">
                  {{ x.sb.leituras }} leituras comparadas: {{ x.sb.concordam }} iguais,
                  <b :class="{ 'c-warn': x.sb.divergem }">{{ x.sb.divergem }} divergentes</b>.
                </p>
                <p v-else class="nota">Aguardando leituras.</p>
              </template>
              <p v-else class="nota">
                Nenhum candidato. O candidato roda em cada leitura, sem agir, e é comparado com o modelo em serviço.
              </p>
            </div>
          </div>
          <div class="passo ultimo">
            <span class="n">4</span>
            <div>
              <b>Aprovação do médico da missão</b>
              <p v-if="p.equipe.local === 'terra'" class="nota">
                Sem médico a bordo, quem aprova é a médica de voo, em Houston. A decisão dela viaja pelo link como P4 e só vale quando chega,
                para a versão que ela viu (ADR-017).
              </p>
              <p v-for="(t, i) in x.daTerra.slice(0, 3)" :key="i" class="nota">
                Decisão da {{ nome('rivera') }} às {{ hora(t.enviada_em, true) }}: <b>{{ t.rotulo }}</b> ·
                <span :class="situacaoTerra(t).classe">{{ situacaoTerra(t).texto }}</span>
              </p>
              <div class="acoes">
                <button type="button" class="btn principal sm" :disabled="!x.cand || x.aCaminho" @click="modelo(x.peca, 'aprovar')">
                  Aprovar como {{ p.equipe.medico_nome }}
                </button>
                <button type="button" class="btn sm" :disabled="!x.cand || x.aCaminho" @click="modelo(x.peca, 'rejeitar')">Rejeitar</button>
                <button type="button" class="btn sm" :disabled="!x.cand" @click="modelo(x.peca, 'aprovar', outro)">
                  Tentar aprovar como {{ nome(outro) }}
                </button>
              </div>
            </div>
          </div>
        </article>

        <p class="etiqueta espaco">Histórico de versões</p>
        <div class="rolagem">
          <table class="tabela">
            <tr>
              <th>versão</th>
              <th>estado</th>
              <th>lote</th>
              <th>treinado</th>
              <th>quem</th>
            </tr>
            <tr v-for="h in p.historico" :key="h.versao">
              <td class="mono">{{ h.versao }}</td>
              <td>
                <span class="selo" :class="h.estado === 'ativo' ? 'ok' : h.estado === 'sombra' ? 'warn' : ''">{{ h.estado }}</span>
              </td>
              <td class="mono">{{ h.lote }}</td>
              <td>{{ String(h.treinado_em ?? '').replace('T', ' ').replace('Z', '') }}</td>
              <td>
                {{ h.decidido_por ? `decidido por ${nome(h.decidido_por)}` : h.pedido_por ? `pedido por ${nome(h.pedido_por)}` : h.aprovado_por ?? '' }}
              </td>
            </tr>
          </table>
        </div>
      </section>

      <!-- 4 e 5 · Ao vivo -->
      <div class="duas">
        <section class="cartao">
          <h3>4 · Saída ao vivo de <span class="mono">ia.analisar(leitura)</span></h3>
          <div class="selos espaco-baixo">
            <button v-for="t in TRIPULACAO" :key="t.id" type="button" class="selecao" :aria-pressed="t.id === quem" @click="quem = t.id">
              {{ nome(t.id) }}
            </button>
          </div>
          <pre class="json">{{ analise.dados.value ? JSON.stringify(analise.dados.value, null, 1) : '…' }}</pre>
        </section>
        <section v-if="auditoria.dados.value" class="cartao">
          <h3>5 · Trilha de auditoria com hash encadeado</h3>
          <p :class="auditoria.dados.value.cadeia.integra ? 'c-ok' : 'c-crit'">
            {{
              auditoria.dados.value.cadeia.integra
                ? `Cadeia íntegra: ${auditoria.dados.value.cadeia.registros} registros, último hash ${String(auditoria.dados.value.cadeia.ultimo_hash ?? '').slice(0, 16)}…`
                : `Cadeia quebrada no registro ${auditoria.dados.value.cadeia.quebrou_em}`
            }}
          </p>
          <p class="nota">Só inclusão. Cada registro guarda o hash do anterior; alterar um deles quebra os seguintes.</p>
          <div class="rolagem">
            <table class="tabela">
              <tr>
                <th>#</th>
                <th>quando</th>
                <th>ator</th>
                <th>o quê</th>
                <th>hash</th>
              </tr>
              <tr v-for="r in auditoria.dados.value.registros" :key="r.seq">
                <td class="n">{{ r.seq }}</td>
                <td>{{ hora(r.quando, true) }}</td>
                <td>
                  <b :class="{ 'c-acento': !['motor', 'cosmo', 'apresentador'].includes(r.ator) }">{{ r.ator }}</b>
                </td>
                <td>{{ r.entidade }} {{ r.entidade_id }}<template v-if="r.para_estado"> → {{ r.para_estado }}</template></td>
                <td class="mono">{{ String(r.hash).slice(0, 8) }}</td>
              </tr>
            </table>
          </div>
          <p class="meta">Atores em destaque são humanos. "motor" é regra determinística; "cosmo" só aparece em sugestão.</p>
        </section>
      </div>
    </template>
    <p class="meta credito">ECG: PhysioNet/CinC Challenge 2017 (Clifford et al., 2017), licença ODC-By.</p>
  </main>
</template>

<style scoped>
.dados {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px;
}
.topo {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.topo h1 {
  font-size: 22px;
}
.subtitulo {
  margin-top: 4px;
  font-size: 13px;
  color: var(--texto-medio);
}
.onde {
  font: 500 11px var(--mono);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--acento);
}
.zonas {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}
.zona {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--linha);
  border-top-width: 3px;
  background: rgba(255, 255, 255, 0.02);
}
.zona h4 {
  margin-bottom: 6px;
  font-size: 13px;
}
.zona ul {
  padding-left: 16px;
  font-size: 12.5px;
}
.zona .nota {
  margin-top: 6px;
}
.bronze {
  border-top-color: #b45309;
}
.prata {
  border-top-color: #94a3b8;
}
.ouro {
  border-top-color: #eab308;
}
.art {
  border-top-color: var(--acento);
}
.duas {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 12px;
}
.interno {
  background: rgba(255, 255, 255, 0.02);
}
.hitl {
  margin-top: 10px;
}
.passo {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--linha);
}
.passo.ultimo {
  border-bottom: 0;
}
.passo .n {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid var(--acento);
  color: var(--acento);
  font: 600 12px var(--mono);
}
.passo b {
  margin-right: 6px;
  font-size: 13px;
}
.passo .nota {
  margin-top: 4px;
}
.json {
  max-height: 420px;
  overflow: auto;
  margin: 0;
  padding: 10px;
  border-radius: 10px;
  background: #070b14;
  border: 1px solid var(--linha);
  font: 11px/1.45 var(--mono);
  color: var(--texto-medio);
}
.espaco {
  margin-top: 10px;
}
.espaco-baixo {
  margin-bottom: 8px;
}
.credito {
  text-align: center;
}
@media (max-width: 560px) {
  .duas {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
