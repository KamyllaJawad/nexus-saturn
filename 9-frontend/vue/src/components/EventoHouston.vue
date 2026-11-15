<script setup lang="ts">
// Um evento que já chegou a Houston. Com médico a bordo, Houston só revisa por
// parecer. Sem médico a bordo, a decisão médica sai daqui, assinada pela médica de
// voo, e só vale quando o pacote chega à nave.
import { computed, ref } from 'vue'
import { ESTADO_EVENTO, FINAIS, hora, nome, TIPO } from '@/servicos/formato'

/* eslint-disable @typescript-eslint/no-explicit-any */
const props = defineProps<{ evento: Record<string, any>; missao: Record<string, any> }>()
const emit = defineEmits<{
  parecer: [evento_id: string, texto: string]
  decidir: [corpo: { evento_id: string; acao: string; dose?: string; pin?: string; detalhe?: Record<string, unknown> }]
}>()

const e = computed(() => props.evento)
const m = computed(() => props.missao)
const fim = computed(() => FINAIS.includes(e.value.estado))
const deTerra = computed(() => e.value.medico_local === 'terra')
const bloqueado = computed(() => !!m.value.blackout)
const minhas = computed<any[]>(() => e.value.minhas_decisoes ?? [])
const tem = (a: string) => minhas.value.find((x) => x.acao === a && x.estado !== 'não aplicada')
const conduta = computed(() => tem('confirmar') || tem('recusar'))
const sg = computed(() => e.value.acoes_seguras)
const med = computed(() => e.value.medicacao)

const ACAO: Record<string, string> = {
  iniciar_seguras: 'ações seguras iniciadas pelo CMO',
  aplicar_medicacao: 'dose aplicada pelo CMO',
  liberar_medicacao: 'medicação liberada',
  confirmar: 'protocolo confirmado',
  assumir: 'atendimento manual',
  recusar: 'recusado',
  aprovar_exame: 'exame aprovado',
  ordem_permanente: 'ordem permanente aplicada pelo CMO, sem sinal',
}

const parecer = ref(
  'De acordo com a conduta. Manter O₂ por 20 min, repetir ECG de 12 derivações em 1 h e suspender treino por 24 h.',
)
const dose = ref('')
const pin = ref('')

function situacao(x: any): { texto: string; classe: string } {
  if (x.estado === 'aplicada') return { texto: `chegou a bordo às ${hora(x.chegou_em, true)} e foi aplicada`, classe: 'c-ok' }
  if (x.estado === 'não aplicada') return { texto: `chegou, mas não se aplicou: ${x.motivo}`, classe: 'c-warn' }
  if (x.pacote_estado === 'fila') return { texto: 'na fila: sem sinal', classe: 'c-warn' }
  return { texto: `a caminho · chega a bordo em ${x.falta_s} s`, classe: '' }
}
const decidir = (acao: string, extra: { dose?: string; pin?: string; detalhe?: Record<string, unknown> } = {}) =>
  emit('decidir', { evento_id: e.value.id, acao, ...extra })
</script>

<template>
  <article class="cartao" :class="[{ crit: e.tipo === 'arritmia' && !fim, fim }]">
    <h4>
      {{ TIPO[e.tipo] ?? e.tipo }} · {{ e.nome }} <span class="selo">{{ ESTADO_EVENTO[e.estado] ?? e.estado }}</span>
    </h4>
    <p v-if="e.sugestao">
      Sugestão da Cosmo a bordo: {{ e.sugestao.texto }} (confiança {{ Math.round((e.sugestao.confianca ?? 0) * 100) }}%,
      {{ e.sugestao.versao_modelo }}).
    </p>

    <!-- Sem médico a bordo: a decisão médica é daqui -->
    <div v-if="deTerra && ['arritmia', 'dor_de_cabeca'].includes(e.tipo)" class="caixa" :class="med?.via === 'ordem_permanente' ? 'ordem' : 'terra'">
      <template v-if="med && med.via === 'ordem_permanente'">
        <h5>Usada a ordem permanente {{ med.ordem }}</h5>
        <p>
          Sem sinal, {{ nome(med.aplicada_por) }} (CMO) aplicou {{ med.dose }} às {{ hora(med.aplicada_em, true) }}, depois das ações
          seguras<template v-if="sg"> ({{ hora(sg.quando, true) }})</template>. Não há o que liberar daqui: a revisão é sua, por parecer.
        </p>
      </template>
      <template v-else>
        <h5>{{ fim ? 'Decisão médica na Terra' : 'Você decide: não há médico a bordo' }}</h5>
        <p>
          {{ sg ? `O CMO iniciou as ações seguras às ${hora(sg.quando, true)}: ${sg.acoes}.` : 'As ações seguras do CMO ainda não constam no que chegou.' }}
          {{
            e.tipo === 'arritmia'
              ? 'A Cosmo propõe repouso, O₂ 2 L/min, ECG de 12 derivações e antiarrítmico do kit.'
              : 'A Cosmo sugere ultrassom ocular guiado para descartar SANS.'
          }}
        </p>
        <p v-for="(x, i) in minhas" :key="i">
          Você enviou às {{ hora(x.enviada_em, true) }}: <b>{{ x.rotulo }}</b><template v-if="x.dose"> ({{ x.dose }})</template> ·
          <span :class="situacao(x).classe">{{ situacao(x).texto }}</span>.
        </p>

        <div v-if="!fim && e.estado === 'aguardando_humano' && !conduta" class="acoes">
          <template v-if="e.tipo === 'arritmia'">
            <button type="button" class="btn crit sm" :disabled="bloqueado" @click="decidir('confirmar')">Confirmar protocolo</button>
            <button type="button" class="btn sm" :disabled="bloqueado" @click="decidir('recusar')">Recusar: falso alarme</button>
          </template>
          <template v-else-if="!tem('aprovar_exame')">
            <button type="button" class="btn principal sm" :disabled="bloqueado" @click="decidir('aprovar_exame')">Aprovar ultrassom ocular</button>
            <button type="button" class="btn sm" :disabled="bloqueado" @click="decidir('recusar')">Recusar</button>
          </template>
        </div>

        <template v-if="e.tipo === 'arritmia' && !fim && (tem('confirmar') || e.estado === 'em_execucao')">
          <p v-if="tem('liberar_medicacao') && med?.aplicada" class="c-ok">
            O CMO registrou a aplicação da dose às {{ hora(med.aplicada_em, true) }}.
          </p>
          <template v-else-if="!tem('liberar_medicacao')">
            <form class="acoes" @submit.prevent="decidir('liberar_medicacao', { dose: dose.trim(), pin: pin.trim() })">
              <input v-model="dose" class="entrada" placeholder="Dose (você define)" size="16" aria-label="Dose" />
              <input v-model="pin" class="entrada" placeholder="PIN" size="5" type="password" aria-label="PIN" />
              <button type="submit" class="btn warn sm" :disabled="bloqueado">Liberar antiarrítmico</button>
            </form>
            <p class="meta">Medicação é sempre um passo separado. PIN de demonstração: 2026. O CMO aplica quando a liberação chegar.</p>
          </template>
        </template>

        <p v-if="bloqueado" class="c-warn">Sem sinal: nada sai daqui até o contato voltar. A bordo, só protocolos pré-aprovados.</p>
        <p v-else-if="!fim" class="meta">
          Cada decisão chega a bordo em {{ m.atraso_txt }}{{ m.comprimido ? ' (na demo, 1 min = 1 s)' : '' }} e só vale quando chega.
        </p>
      </template>
    </div>

    <p v-if="e.decisao">
      {{ e.decisao.humano_id === 'rivera' ? 'Sua decisão, aplicada a bordo' : 'Decisão a bordo' }}:
      <b>{{ ACAO[e.decisao.acao] ?? String(e.decisao.acao).replace(/_/g, ' ') }}</b> por {{ nome(e.decisao.humano_id) }} às
      {{ hora(e.decisao.decidida_em, true) }}<template v-if="e.decisao.dose"> · dose {{ e.decisao.dose }}</template>.
    </p>
    <p v-else-if="!deTerra">A decisão do humano a bordo ainda não chegou.</p>

    <p class="meta">
      gerado {{ hora(e.gerado_em, true) }} · último pacote enviado {{ hora(e.enviado_em, true) }} · recebido {{ hora(e.recebido_em, true) }}
    </p>

    <p v-if="e.parecer_entregue" class="c-ok">Parecer entregue a bordo.</p>
    <form v-else class="parecer" @submit.prevent="parecer.trim() && emit('parecer', e.id, parecer.trim())">
      <textarea v-model="parecer" class="entrada" aria-label="Parecer para a nave"></textarea>
      <div class="acoes">
        <button type="submit" class="btn principal sm" :disabled="bloqueado">Enviar parecer à nave</button>
        <span class="meta">chega a bordo em {{ m.atraso_txt }}</span>
      </div>
    </form>
  </article>
</template>

<style scoped>
.parecer {
  margin-top: 8px;
}
</style>
