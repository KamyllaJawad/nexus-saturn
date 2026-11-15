<script setup lang="ts">
// Trilha mínima da Cosmo (ADR-018): o mesmo quadro no painel de bordo e em Houston.
// O servidor decide o que cada superfície vê (Houston recebe pelo link a trilha das
// sugestões de bordo, sem a pergunta de ninguém).
import { computed } from 'vue'
import { hora, num } from '@/servicos/formato'
import { ms, usd, type RegistroTrilha, type ResumoTrilha, type Trilha } from '@/servicos/trilha'

const props = defineProps<{ trilha: Trilha | null | undefined; superficie: 'bordo' | 'houston' }>()
const MOSTRAR = 12

const registros = computed(() => props.trilha?.registros.slice(0, MOSTRAR) ?? [])
const bordo = computed(() => (props.superficie === 'houston' ? props.trilha?.resumo_bordo : undefined))

const decisoes = (s: ResumoTrilha) =>
  Object.entries(s.por_decisao)
    .map(([k, v]) => `${k} ${v}`)
    .join(' · ')
const origem = (r: RegistroTrilha) =>
  r.via_link
    ? `sugestão da Cosmo de bordo · chegou à Terra às ${hora(r.recebido_em, true)}`
    : `${r.origem === 'sugestao' ? 'sugestão' : r.origem} · ${r.superficie === 'houston' ? 'Cosmo Terra' : 'Cosmo de bordo'}`
const tag = (t: string) => (t === 'recusou agir' ? 'warn' : t === 'sugeriu' ? 'acento' : t === 'sem resposta' ? 'fraco' : '')
</script>

<template>
  <div v-if="trilha" class="trilha">
    <div class="kpis">
      <div><b>{{ num(trilha.resumo.chamadas) }}</b><small>chamadas</small></div>
      <div>
        <b>{{ num(trilha.resumo.tokens_entrada + trilha.resumo.tokens_saida) }}</b>
        <small>tokens · {{ num(trilha.resumo.tokens_entrada) }} entrada, {{ num(trilha.resumo.tokens_saida) }} saída</small>
      </div>
      <div>
        <b>{{ ms(trilha.resumo.latencia_media_ms) }}</b><small>latência média · p95 {{ ms(trilha.resumo.latencia_p95_ms) }}</small>
      </div>
      <div>
        <b>{{ usd(trilha.resumo.custo_usd) }}</b
        ><small>custo · {{ num(trilha.resumo.energia_mwh, 3) }} mWh a {{ num(trilha.resumo.watts) }} W</small>
      </div>
    </div>
    <p class="meta">
      <template v-if="decisoes(trilha.resumo)">Decisões: {{ decisoes(trilha.resumo) }}. </template>
      {{
        trilha.resumo.com_llm
          ? `${trilha.resumo.com_llm} de ${trilha.resumo.chamadas} com LLM local.`
          : 'Sem LLM: regras locais e tokens estimados.'
      }}
      O custo em US$ é zero porque tudo roda local, sem API paga.
    </p>
    <p v-if="bordo && bordo.chamadas" class="meta">
      Pelo link, da Cosmo de bordo: {{ num(bordo.chamadas) }} sugestão(ões), {{ num(bordo.tokens_entrada + bordo.tokens_saida) }} tokens,
      latência média {{ ms(bordo.latencia_media_ms) }}, {{ num(bordo.energia_mwh, 3) }} mWh a bordo.
    </p>

    <div v-if="registros.length" class="itens">
      <details v-for="r in registros" :key="r.id" class="item">
        <summary>
          <span class="hora">{{ hora(r.quando, true) }}</span>
          <span class="tag" :class="tag(r.decisao.tipo)">{{ r.decisao.tipo }}</span>
          <span class="assunto">{{ r.via_link ? '↓ ' : '' }}{{ r.pergunta ? `“${r.pergunta}”` : r.decisao.resumo }}</span>
          <span class="numeros">{{ num(r.tokens.total) }} tok · {{ ms(r.latencia_ms) }} · {{ usd(r.custo.usd) }}</span>
        </summary>
        <div class="corpo">
          <p class="nota"><b>{{ origem(r) }}</b> · {{ r.id }} · {{ r.modo }}</p>
          <p class="nota">Decisão da Cosmo: {{ r.decisao.resumo }}. Pode agir: não.</p>
          <ol class="passos">
            <li v-for="(p, i) in r.passos" :key="i">
              <b>{{ p.etapa }}</b><span>{{ p.detalhe }}</span><time>{{ ms(p.ms) }}</time>
            </li>
          </ol>
          <p class="meta">
            Tokens: entrada {{ num(r.tokens.entrada) }} · saída {{ num(r.tokens.saida) }}, {{ r.tokens.fonte }}. Energia
            {{ num(r.custo.energia_mwh, 4) }} mWh. Base do custo: {{ r.custo.base }}.
          </p>
        </div>
      </details>
      <p v-if="trilha.registros.length > MOSTRAR" class="meta">
        Mostrando as {{ MOSTRAR }} mais recentes de {{ trilha.registros.length }}. A trilha inteira fica no SQLite de bordo e na
        auditoria encadeada.
      </p>
    </div>
    <p v-else class="nota">
      {{
        superficie === 'houston'
          ? 'A Cosmo Terra ainda não falou, e nenhuma sugestão de bordo chegou.'
          : 'A Cosmo ainda não falou nesta sessão.'
      }}
    </p>
  </div>
</template>

<style scoped>
.trilha {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 6px;
}
.kpis > div {
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--linha);
  background: rgba(255, 255, 255, 0.02);
}
.kpis b {
  font-size: 15px;
  font-variant-numeric: tabular-nums;
}
.kpis small {
  font-size: 10.5px;
  color: var(--texto-fraco);
}
.itens {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.item {
  border-radius: 9px;
  border: 1px solid var(--linha);
  background: rgba(255, 255, 255, 0.02);
}
.item summary {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 6px 9px;
  font-size: 12px;
  cursor: pointer;
}
.hora,
.numeros {
  font: 500 10.5px var(--mono);
  color: var(--texto-fraco);
}
.assunto {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tag {
  padding: 1px 7px;
  border-radius: 99px;
  border: 1px solid var(--linha-forte);
  font-size: 10.5px;
}
.tag.warn {
  color: var(--warn);
  border-color: rgba(245, 158, 11, 0.5);
}
.tag.acento {
  color: var(--acento);
  border-color: rgba(0, 229, 255, 0.4);
}
.tag.fraco {
  color: var(--texto-fraco);
}
.corpo {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 10px 10px;
}
.passos {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
}
.passos li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 6px;
}
.passos span {
  color: var(--texto-medio);
}
.passos time {
  font: 500 10.5px var(--mono);
  color: var(--texto-fraco);
}
@media (max-width: 560px) {
  .numeros {
    display: none;
  }
  .item summary {
    grid-template-columns: auto auto minmax(0, 1fr);
  }
}
</style>
