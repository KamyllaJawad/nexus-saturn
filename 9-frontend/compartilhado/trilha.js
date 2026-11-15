// Trilha mínima da Cosmo (ADR-018): tokens, latência, custo, decisão e passos de
// cada fala. O mesmo quadro no painel de bordo e em Houston; o servidor decide o que
// cada superfície vê (Houston recebe a trilha das sugestões de bordo pelo link, sem
// as perguntas de ninguém).
import { esc, hora, num, pintar } from "./api.js";

const ms = (v) => `${num(v, v < 10 ? 2 : 1)} ms`;
const usd = (v) => `US$ ${num(v, 4)}`;
const ORIGEM = { chat: "chat", sugestao: "sugestão" };
const MOSTRAR = 12;

function origem(r) {
  if (r.via_link) return `sugestão da Cosmo de bordo · chegou à Terra às ${hora(r.recebido_em, true)}`;
  return `${ORIGEM[r.origem] || r.origem} · ${r.superficie === "houston" ? "Cosmo Terra" : "Cosmo de bordo"}`;
}

function linha(r, aberto) {
  const assunto = r.pergunta ? `“${r.pergunta}”` : r.decisao.resumo;
  const tipo = r.decisao.tipo;
  return `<details class="tr-item" data-id="${esc(r.id)}"${aberto ? " open" : ""}><summary>
      <span class="tr-hora">${hora(r.quando, true)}</span>
      <span class="tr-tag ${tipo === "recusou agir" ? "warn" : tipo === "sugeriu" ? "acc" : tipo === "sem resposta" ? "fraco" : ""}">${esc(tipo)}</span>
      <span class="tr-assunto">${r.via_link ? "↓ " : ""}${esc(assunto)}</span>
      <span class="tr-num">${num(r.tokens.total)} tok · ${ms(r.latencia_ms)} · ${usd(r.custo.usd)}</span></summary>
    <div class="tr-corpo">
      <p><b>${esc(origem(r))}</b> · ${esc(r.id)} · ${esc(r.modo)}</p>
      <p>Decisão da Cosmo: ${esc(r.decisao.resumo)}. Pode agir: não.</p>
      <ol class="tr-passos">${r.passos.map((p) => `<li><b>${esc(p.etapa)}</b><span>${esc(p.detalhe)}</span><time>${ms(p.ms)}</time></li>`).join("")}</ol>
      <p class="tr-meta">Tokens: entrada ${num(r.tokens.entrada)} · saída ${num(r.tokens.saida)}, ${esc(r.tokens.fonte)}. Energia ${num(r.custo.energia_mwh, 4)} mWh. Base do custo: ${esc(r.custo.base)}.</p>
    </div></details>`;
}

function kpis(s) {
  const dec = Object.entries(s.por_decisao).map(([k, v]) => `${k} ${v}`).join(" · ");
  return `<div class="tr-kpis">
      <div><b>${num(s.chamadas)}</b><small>chamadas</small></div>
      <div><b>${num(s.tokens_entrada + s.tokens_saida)}</b><small>tokens · ${num(s.tokens_entrada)} entrada, ${num(s.tokens_saida)} saída</small></div>
      <div><b>${ms(s.latencia_media_ms)}</b><small>latência média · p95 ${ms(s.latencia_p95_ms)}</small></div>
      <div><b>${usd(s.custo_usd)}</b><small>custo · ${num(s.energia_mwh, 3)} mWh a ${num(s.watts)} W</small></div>
    </div>
    <p class="tr-meta">${dec ? `Decisões: ${esc(dec)}. ` : ""}${s.com_llm ? `${s.com_llm} de ${s.chamadas} com LLM local.` : "Sem LLM: regras locais e tokens estimados."} O custo em US$ é zero porque tudo roda local, sem API paga.</p>`;
}

export function desenharTrilha(el, t, { superficie }) {
  if (!el || !t) return;
  const abertos = new Set([...el.querySelectorAll("details[open]")].map((x) => x.dataset.id));
  const regs = t.registros.slice(0, MOSTRAR);
  const bordo = t.resumo_bordo;
  const cab = superficie === "houston"
    ? `${kpis(t.resumo)}${bordo && bordo.chamadas ? `<p class="tr-meta">Pelo link, da Cosmo de bordo: ${num(bordo.chamadas)} sugestão(ões), ${num(bordo.tokens_entrada + bordo.tokens_saida)} tokens, latência média ${ms(bordo.latencia_media_ms)}, ${num(bordo.energia_mwh, 3)} mWh a bordo.</p>` : ""}`
    : kpis(t.resumo);
  pintar(el, `${cab}
    ${regs.length ? `<div class="tr-lista">${regs.map((r) => linha(r, abertos.has(r.id))).join("")}</div>
      ${t.registros.length > MOSTRAR ? `<p class="tr-meta">Mostrando as ${MOSTRAR} mais recentes de ${t.registros.length}. A trilha inteira fica no SQLite de bordo (cosmo_trilha) e na auditoria encadeada.</p>` : ""}`
      : `<p class="nota">${superficie === "houston" ? "A Cosmo Terra ainda não falou, e nenhuma sugestão de bordo chegou." : "A Cosmo ainda não falou nesta sessão."}</p>`}`);
}

// Rodapé curto de cada resposta no chat.
export const rodapeChat = (t) => `${num(t.tokens.total)} tokens · ${ms(t.latencia_ms)} · ${usd(t.custo.usd)} · ${t.decisao.tipo}`;
