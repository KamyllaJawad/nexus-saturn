<script setup lang="ts">
// Um evento no painel de bordo, com todos os fluxos do painel em JS puro: protocolo
// de FA, medicação com dose e PIN, médico só na Terra (ações seguras do CMO e espera
// pelo link), ordem permanente sem sinal, explicação da Cosmo e parecer de Houston.
import { computed, ref } from 'vue'
import { EU, pedir, type ApiEvento, type ApiMissao, type ApiTripulante } from '@/servicos/api'
import { ESTADO_EVENTO, FINAIS, hora, nome, num, TIPO } from '@/servicos/formato'

/* eslint-disable @typescript-eslint/no-explicit-any */
const props = defineProps<{ evento: ApiEvento; missao: ApiMissao; tripulantes: ApiTripulante[] }>()
const emit = defineEmits<{
  decidir: [corpo: { evento_id: string; acao: string; dose?: string; pin?: string; detalhe?: Record<string, unknown> }]
}>()

const e = computed(() => props.evento)
const d = computed(() => e.value.dados as Record<string, any>)
const m = computed(() => props.missao)
const fim = computed(() => FINAIS.includes(e.value.estado))
const meu = computed(() => e.value.responsavel_id === EU)
const terra = computed(() => e.value.medico_local === 'terra')
const med = computed(() => d.value.medicacao as Record<string, any> | undefined)
const sugestao = computed(() => (e.value.sugestao ?? {}) as Record<string, any>)

const classe = computed(() => {
  if (e.value.tipo === 'bem_estar') return 'roxo'
  if (e.value.tipo === 'arritmia' && !fim.value) return 'crit'
  return fim.value ? 'fim' : ''
})

// Campos digitados (dose, PIN, medição do kit)
const dose = ref('')
const pin = ref('')
const kit = ref(97)

function decidir(acao: string, extra: { dose?: string; pin?: string; detalhe?: Record<string, unknown> } = {}) {
  emit('decidir', { evento_id: e.value.id, acao, ...extra })
}
function liberarMedicacao() {
  decidir('liberar_medicacao', { dose: dose.value.trim(), pin: pin.value.trim() })
}
function aplicarOrdem() {
  const op = m.value.ordem_permanente
  if (!op) return
  if (!window.confirm(`Aplicar ${op.dose} pela ordem permanente ${op.id}? Fica assinado por você e sobe como P1.`)) return
  decidir('ordem_permanente')
}

// "Por que a Cosmo sugeriu isso?"
const explicacao = ref<Record<string, any> | null>(null)
async function alternarExplicacao() {
  explicacao.value = explicacao.value ? null : await pedir<Record<string, any>>(`/eventos/${e.value.id}/explicacao`)
}

const ordem = computed(() => {
  const op = m.value.ordem_permanente
  if (!op || !op.em_vigor || !m.value.blackout) return null
  const criterios: [string, boolean][] = [
    ['Sem médico a bordo', true],
    ['Sem sinal com a Terra', !!m.value.blackout],
    ['Ações seguras iniciadas', !!d.value.seguras],
    ['O M1 ainda vê FA na última leitura', !!d.value.fa_agora],
    ['Nenhuma dose aplicada neste evento', !d.value.medicacao],
  ]
  return { op, criterios, ok: criterios.every(([, v]) => v) }
})

const esperaTerra = computed(() => {
  if (m.value.blackout)
    return {
      aviso: true,
      texto:
        `Sem sinal e sem médico a bordo: só os protocolos pré-aprovados. A decisão da ${e.value.medico_nome} fica bloqueada até o ` +
        `contato voltar (${m.value.volta_em ?? '—'})${e.value.tipo === 'arritmia' ? '; na FA, vale a ordem permanente que ela assinou antes do voo' : ''}.`,
    }
  const total = m.value.comprimido && m.value.atraso_demo_s ? ` (na demo, cerca de ${Math.round(2 * m.value.atraso_demo_s)} s no total)` : ''
  return {
    aviso: false,
    texto:
      `O alerta saiu para Houston às ${hora(e.value.gerado_em, true)}. A resposta da ${e.value.medico_nome} leva ida e volta: ` +
      `${m.value.atraso_txt} por trecho${total}. Daqui não dá para ver o pacote dela no caminho.`,
  }
})

const confirmacaoTerra = computed(() => e.value.decisoes.find((x) => x.acao === 'confirmar'))
const primeiraDecisao = computed(() => e.value.decisoes[0])
const ultimaDecisao = computed(() => e.value.decisoes[e.value.decisoes.length - 1])

const faseTempestade = computed(() =>
  e.value.estado === 'aguardando_humano'
    ? 'aguardando a comandante'
    : d.value.fase === 'fluxo_caindo'
      ? 'fluxo caindo, a comandante decide a saída'
      : fim.value
        ? 'encerrada'
        : 'tripulação no abrigo',
)
</script>

<template>
  <article class="cartao evento" :class="classe">
    <h4>
      {{ TIPO[e.tipo] ?? e.tipo }} · {{ e.nome }}
      <span class="selo">{{ ESTADO_EVENTO[e.estado] ?? e.estado }}</span>
      <span v-if="!fim && e.prazo_restante_s != null" class="selo warn">{{ e.prazo_restante_s }} s</span>
    </h4>

    <!-- ============ Arritmia sem médico a bordo ============ -->
    <template v-if="e.tipo === 'arritmia' && terra">
      <template v-if="e.estado === 'aguardando_humano'">
        <p><b>Cosmo propõe um protocolo · confiança {{ Math.round((sugestao.confianca ?? 0) * 100) }}%</b> ({{ sugestao.versao_modelo }})</p>
        <ol>
          <li>Interromper o esforço; {{ e.nome }} sentada em repouso.</li>
          <li>O₂ por máscara a 2 L/min.</li>
          <li>ECG de 12 derivações com o kit.</li>
          <li>Desfibrilador de prontidão; reavaliar em 10 min.</li>
          <li>Antiarrítmico do kit: só com a liberação da {{ e.medico_nome }}.</li>
        </ol>
        <div class="caixa terra">
          <h5>Decisão médica na Terra · {{ e.medico_nome }}</h5>
          <p>
            Não há médico a bordo: confirmar o protocolo e liberar o antiarrítmico é com ela, no console de Houston. Você inicia só as
            ações seguras.
          </p>
          <p v-if="d.seguras" class="c-ok">
            ✓ Ações seguras em curso desde {{ hora(d.seguras.quando, true) }}, por {{ nome(d.seguras.por) }}: {{ d.seguras.acoes }}.
          </p>
          <template v-else-if="meu">
            <div class="acoes"><button type="button" class="btn crit sm" @click="decidir('iniciar_seguras')">Iniciar ações seguras (repouso, O₂, ECG)</button></div>
            <p class="meta">Pré-aprovadas no protocolo: não esperam o atraso.</p>
          </template>
          <p v-else class="c-warn">Prazo vencido: as ações seguras passaram para {{ e.responsavel_nome }}.</p>
          <p :class="{ 'c-warn': esperaTerra.aviso }">{{ esperaTerra.texto }}</p>
        </div>
      </template>
      <template v-else-if="med && med.via === 'ordem_permanente'">
        <p>
          Conduta sem sinal: <b>ordem permanente {{ med.ordem }}</b>, assinada pela {{ nome(med.liberada_por) }} em {{ med.quando }}, antes do
          voo.
        </p>
        <ul>
          <li>{{ d.seguras ? `Repouso e O₂ desde ${hora(d.seguras.quando, true)} (ações seguras do CMO)` : 'Repouso e O₂ 2 L/min' }}</li>
          <li>ECG de 12 derivações</li>
          <li>{{ med.dose }}: aplicada por {{ nome(med.aplicada_por) }} às {{ hora(med.aplicada_em, true) }}</li>
        </ul>
        <p class="meta">O uso subiu como P1{{ m.blackout ? ' e está na fila até o sinal voltar' : '' }}; a {{ e.medico_nome }} revisa por parecer.</p>
      </template>
      <template v-else-if="e.estado === 'em_execucao' || e.estado === 'resolvido'">
        <p v-if="confirmacaoTerra">
          Protocolo confirmado pela {{ e.medico_nome }}, em Houston: a decisão chegou a bordo às {{ hora(confirmacaoTerra.decidida_em, true) }}.
        </p>
        <ul>
          <li>{{ d.seguras ? `Repouso e O₂ desde ${hora(d.seguras.quando, true)} (ações seguras do CMO)` : 'Repouso e O₂ 2 L/min' }}</li>
          <li>ECG de 12 derivações</li>
          <li v-if="!med">Antiarrítmico: só se a {{ e.medico_nome }} liberar, de Houston</li>
          <li v-else-if="med.aplicada">
            Antiarrítmico {{ med.dose }}: liberado pela {{ nome(med.liberada_por) }}, aplicado por {{ nome(med.aplicada_por) }} às
            {{ hora(med.aplicada_em, true) }}
          </li>
          <li v-else>Liberação da {{ nome(med.liberada_por) }} chegou às {{ hora(med.quando, true) }}: {{ med.dose }}</li>
        </ul>
        <template v-if="med && !med.aplicada && e.estado === 'em_execucao'">
          <div class="acoes"><button type="button" class="btn warn sm" @click="decidir('aplicar_medicacao')">Aplicar a dose prescrita</button></div>
          <p class="meta">Você aplica a dose que a médica definiu. A dose não muda aqui.</p>
        </template>
        <p v-if="!med && e.estado === 'em_execucao' && m.blackout" class="c-warn">{{ esperaTerra.texto }}</p>
      </template>
      <p v-else-if="ultimaDecisao">
        Recusado pela {{ nome(ultimaDecisao.humano_id) }}, em Houston: falso alarme. A recusa virou rótulo para o próximo treino do M1.
      </p>

      <div v-if="ordem" class="caixa ordem">
        <h5>Ordem permanente {{ ordem.op.id }} · assinada pela {{ ordem.op.assinada_por_nome }} em {{ ordem.op.assinada_em }}</h5>
        <p>{{ ordem.op.titulo }}: <b>{{ ordem.op.dose }}</b>. A dose não muda aqui.</p>
        <ul class="criterios">
          <li v-for="[t, v] in ordem.criterios" :key="t" :class="v ? 'c-ok' : 'c-warn'">{{ v ? '✓' : '✗' }} {{ t }}</li>
        </ul>
        <div class="acoes">
          <button type="button" class="btn warn sm" :disabled="!ordem.ok" @click="aplicarOrdem">Aplicar a dose da ordem permanente</button>
        </div>
        <p class="meta">{{ ordem.op.depois }}</p>
      </div>
    </template>

    <!-- ============ Arritmia com médico a bordo ============ -->
    <template v-else-if="e.tipo === 'arritmia'">
      <template v-if="e.estado === 'aguardando_humano'">
        <p><b>Cosmo propõe um protocolo · confiança {{ Math.round((sugestao.confianca ?? 0) * 100) }}%</b> ({{ sugestao.versao_modelo }})</p>
        <ol>
          <li>Interromper o esforço; {{ e.nome }} sentada em repouso.</li>
          <li>O₂ por máscara a 2 L/min.</li>
          <li>ECG de 12 derivações com o kit.</li>
          <li>Desfibrilador de prontidão; reavaliar em 10 min.</li>
          <li>Antiarrítmico do kit: só com a sua liberação, em passo separado.</li>
        </ol>
        <p>
          Nada é aplicado sem a confirmação de um humano.
          <b v-if="!meu" class="c-warn">Prazo vencido: escalonado para {{ e.responsavel_nome }}.</b>
        </p>
        <div v-if="meu" class="acoes">
          <button type="button" class="btn crit sm" @click="decidir('confirmar')">Confirmar protocolo</button>
          <button type="button" class="btn sm" @click="decidir('assumir')">Assumir manualmente</button>
          <button
            type="button"
            class="btn sm"
            @click="decidir('recusar', { detalhe: { motivo: 'falso alarme, avaliado pelo oficial médico' } })"
          >
            Recusar: falso alarme
          </button>
        </div>
      </template>
      <template v-else-if="(e.estado === 'em_execucao' || e.estado === 'resolvido') && primeiraDecisao">
        <p>
          {{ d.conduta === 'atendimento manual' ? 'Atendimento manual' : 'Protocolo da Cosmo' }} confirmado por
          {{ nome(primeiraDecisao.humano_id) }} às {{ hora(primeiraDecisao.decidida_em, true) }}.
        </p>
        <ul>
          <li>Repouso e O₂ 2 L/min</li>
          <li>ECG de 12 derivações</li>
          <li>
            {{ med ? `Antiarrítmico liberado: ${med.dose}, por ${nome(med.liberada_por)} às ${hora(med.quando, true)}` : 'Antiarrítmico: aguardando a sua liberação' }}
          </li>
        </ul>
        <template v-if="!med && e.estado === 'em_execucao'">
          <form class="acoes" @submit.prevent="liberarMedicacao">
            <input v-model="dose" class="entrada" placeholder="Dose (você define)" size="16" aria-label="Dose" />
            <input v-model="pin" class="entrada" placeholder="PIN" size="5" type="password" aria-label="PIN" />
            <button type="submit" class="btn warn sm">Liberar medicação</button>
          </form>
          <p class="meta">PIN de demonstração: 2026. Medicação nunca é automática.</p>
        </template>
        <p v-if="!d.parecer" class="meta">Houston recebe com o atraso da missão e revisa depois. A decisão é de bordo.</p>
      </template>
      <p v-else-if="primeiraDecisao">
        Recusado por {{ nome(primeiraDecisao.humano_id) }}: falso alarme. A recusa virou rótulo para o próximo treino do M1.
      </p>
    </template>

    <!-- ============ Leitura suspeita ============ -->
    <template v-else-if="e.tipo === 'sensor_suspeito'">
      <p v-if="e.estado === 'confirmacao_astronauta'">
        SpO₂ de {{ num(d.spo2) }}% com sinal suspeito. A Cosmo perguntou a {{ e.nome }} se o relógio está folgado. Ainda não é alarme.
      </p>
      <template v-else-if="e.estado === 'aguardando_humano'">
        <p>
          SpO₂ de {{ num(d.spo2) }}% no relógio com sinal de baixa qualidade ({{ d.motivo ?? '' }}). Chegou aqui porque {{ d.escalou_por }}.
          Sugestão da Cosmo: medir com o oxímetro de dedo do kit.
        </p>
        <form class="acoes" @submit.prevent="decidir('registrar_kit', { detalhe: { spo2_kit: Number(kit) } })">
          <input v-model="kit" class="entrada" size="4" inputmode="numeric" aria-label="SpO₂ medida no kit" />
          <button type="submit" class="btn principal sm">Registrar medição do kit</button>
        </form>
      </template>
      <p v-else>{{ d.desfecho ?? '' }}. Virou rótulo para o M2.</p>
    </template>

    <!-- ============ Tempestade solar ============ -->
    <template v-else-if="e.tipo === 'tempestade_solar'">
      <p>Rota até o abrigo acesa automaticamente (nível 4, reversível). Situação: {{ faseTempestade }}.</p>
      <div class="kv">
        <div v-for="t in tripulantes" :key="t.tripulante_id"><span>{{ t.nome }}</span><b>{{ num(t.dose_msv_dia, 2) }} mSv</b></div>
      </div>
      <p class="meta">A decisão de abrigo é da comandante; você acompanha a dose.</p>
    </template>

    <!-- ============ Prontidão para a EVA ============ -->
    <template v-else-if="e.tipo === 'prontidao_eva'">
      <div class="kv">
        <div v-for="(v, k) in d.prontidao ?? {}" :key="k">
          <span>{{ nome(String(k)) }}</span><b :class="{ 'c-warn': Number(v) < 70 }">{{ v }}%</b>
        </div>
      </div>
      <p>{{ d.resultado ? `Decisão da comandante: ${d.resultado}.` : `${d.motivo}. A decisão da escala é da comandante.` }}</p>
    </template>

    <!-- ============ Dor de cabeça e CO₂ ============ -->
    <template v-else-if="e.tipo === 'dor_de_cabeca'">
      <p>
        A Cosmo cruzou a queixa de {{ e.nome }} com o ar da cabine: CO₂ em {{ num(d.co2, 1) }} mmHg na hora da queixa (alvo abaixo de 3) e
        mais {{ (d.outros_com_sintoma ?? []).length }} tripulantes com sintoma. Hipótese principal: CO₂ elevado. A descartar:
        {{ sugestao.alternativa }}.
      </p>
      <ul>
        <li>
          {{ d.ar === 'feito' ? `✓ Ar ajustado pela Elena: ${num(m.cabine.co2, 1)} mmHg` : d.ar ? '… Elena ajustando os filtros de CO₂' : 'Ajuste do ar: pendente' }}
        </li>
        <li>
          {{
            d.exame === 'feito'
              ? '✓ Ultrassom ocular concluído; imagens enviadas a Houston para laudo'
              : d.exame
                ? '… Ultrassom guiado em andamento'
                : terra
                  ? `Ultrassom ocular: aguardando a aprovação da ${e.medico_nome}`
                  : 'Ultrassom ocular: aguardando a sua aprovação'
          }}
        </li>
      </ul>
      <template v-if="!fim">
        <div v-if="terra && e.estado === 'aguardando_humano'" class="caixa terra">
          <h5>Decisão médica na Terra · {{ e.medico_nome }}</h5>
          <p>Sem médico a bordo, o ultrassom ocular (SANS) é aprovado de Houston. O ajuste do ar não espera.</p>
          <p v-if="d.seguras" class="c-ok">✓ Ações seguras em curso desde {{ hora(d.seguras.quando, true) }}: {{ d.seguras.acoes }}.</p>
          <div v-else-if="meu" class="acoes">
            <button type="button" class="btn crit sm" @click="decidir('iniciar_seguras')">Iniciar ações seguras (repouso e ajuste do ar)</button>
          </div>
          <p :class="{ 'c-warn': esperaTerra.aviso }">{{ esperaTerra.texto }}</p>
        </div>
        <div v-else-if="!terra" class="acoes">
          <button v-if="!d.ar" type="button" class="btn sm" @click="decidir('pedir_ajuste_ar')">Pedir ajuste do ar à Elena</button>
          <button v-if="!d.exame" type="button" class="btn principal sm" @click="decidir('aprovar_exame')">Aprovar ultrassom guiado</button>
        </div>
      </template>
    </template>

    <!-- ============ Bem-estar (compartilhado com consentimento) ============ -->
    <template v-else-if="e.tipo === 'bem_estar'">
      <p>{{ e.nome }} autorizou só você a ver este resumo, sem gravações: {{ d.padrao }}.</p>
      <div v-if="e.estado === 'em_execucao'" class="acoes">
        <button type="button" class="btn sm" @click="decidir('marcar_conversa', { detalhe: { hora: '19:00' } })">Marcar conversa às 19:00</button>
      </div>
      <p v-else-if="d.conversa">Conversa marcada às {{ d.conversa }}.</p>
    </template>

    <!-- ============ Modo noite ============ -->
    <p v-else-if="e.tipo === 'modo_noite'">
      Ação de nível 4, reversível:
      {{ e.estado === 'agendado' ? 'agendada, com janela de veto' : e.estado === 'aplicado' ? 'aplicada, pode ser desfeita' : d.desfecho || 'encerrada' }}.
    </p>

    <!-- Explicação e parecer (arritmia) -->
    <template v-if="e.tipo === 'arritmia'">
      <div v-if="e.estado === 'aguardando_humano'" class="acoes">
        <button type="button" class="btn sm" @click="alternarExplicacao">
          {{ explicacao ? 'Ocultar explicação' : 'Por que a Cosmo sugeriu isso?' }}
        </button>
      </div>
      <div v-if="explicacao" class="caixa explica">
        <b>Evidências que mais pesaram</b><br />{{ (explicacao.evidencias ?? []).join(' · ') }}<br />
        <b>Alternativa a considerar</b><br />{{ explicacao.alternativa }}<br />
        <b>Protocolo citado</b><br />{{ explicacao.protocolo?.titulo }}: {{ explicacao.protocolo?.trecho }}<br /><i>{{ explicacao.protocolo?.fonte }}</i><br />
        <b>Modelos</b><br />
        <template v-for="x in explicacao.modelos ?? []" :key="x">{{ x }}<br /></template>
      </div>
      <div v-if="d.parecer" class="caixa explica">
        <b>Parecer de Houston</b> (revisão, não comando)<br />{{ d.parecer.texto }}<br />
        <i>Enviado {{ hora(d.parecer.enviado_em, true) }} · chegou a bordo {{ hora(d.parecer.recebido_em, true) }}</i>
      </div>
      <p v-if="e.estado === 'resolvido'" class="c-ok">
        Quadro resolvido: sem FA no M1 e SpO₂ fora da faixa crítica por 10 leituras seguidas.
      </p>
    </template>

    <p class="meta rodape-evento">
      nível {{ e.nivel_autonomia }} · responsável: {{ e.responsavel_nome }} · aberto {{ hora(e.gerado_em, true) }}
      <template v-if="e.escalonamentos"> · {{ e.escalonamentos }} escalonamento(s)</template>
    </p>
  </article>
</template>

<style scoped>
.evento ol,
.evento ul {
  margin-top: 6px;
}
.criterios {
  list-style: none;
  padding-left: 0 !important;
}
.rodape-evento {
  margin-top: 10px;
}
</style>
