// Uma função só para falar com a API. Servido pelo FastAPI (em qualquer porta) o caminho
// é relativo; aberto como arquivo ou pelo Live Server (5500), aponta para a API local.
export const API = location.protocol === "file:" || location.port === "5500" ? "http://127.0.0.1:8000" : "";

export const TRIPULACAO = [
  { id: "sarah", nome: "Sarah", papel: "Comandante" },
  { id: "marcus", nome: "Dr. Marcus", papel: "Oficial médico" },
  { id: "elena", nome: "Elena", papel: "Engenheira de voo" },
  { id: "kenji", nome: "Kenji", papel: "Especialista de missão" },
];
export const MEDICA_TERRA = { id: "rivera", nome: "Dra. Rivera", papel: "Flight surgeon · Houston" };
export const nome = (id) => (TRIPULACAO.concat([MEDICA_TERRA]).find((p) => p.id === id) || { nome: id }).nome;

// Hipótese da missão: médico a bordo ou só na Terra. A API manda em `missao.equipe`;
// com o médico na Terra o Marcus vira oficial de saúde (CMO).
export function ajustarEquipe(eq) {
  if (!eq) return;
  const m = TRIPULACAO.find((p) => p.id === "marcus");
  m.nome = eq.marcus.nome; m.papel = eq.marcus.papel;
}
export const PAPEL = { cmo: "oficial de saúde (CMO)", oficial_medico: "oficial médico", medico_terra: "Dra. Rivera, em Houston", comandante: "comandante", astronauta: "a própria pessoa" };

export const ESTADO = { otimo: "Ótimo", atencao: "Atenção", critico: "Crítico", suspeito: "Sinal a confirmar" };
export const cls = (e) => (e === "critico" ? "crit" : e === "atencao" || e === "suspeito" ? "warn" : "ok");
export const clsFaixa = (f) => (f === "critico" ? "crit" : f === "atencao" ? "warn" : "ok");
export const TIPO = {
  arritmia: "Arritmia", sensor_suspeito: "Leitura suspeita", tempestade_solar: "Tempestade solar",
  prontidao_eva: "Prontidão para a EVA", dor_de_cabeca: "Dor de cabeça", bem_estar: "Bem-estar",
  modo_noite: "Modo noite", ciclo: "Calendário do ciclo", linha_de_base: "Combinação fora do padrão", hidratacao: "Hidratação",
};
export const ESTADO_EVENTO = {
  detectado: "detectado", confirmacao_astronauta: "confirmando com o astronauta", proposto: "proposto",
  aguardando_humano: "aguardando humano", escalonado: "escalonado", decidido: "decidido", em_execucao: "em execução",
  resolvido: "resolvido", encerrado: "encerrado", agendado: "agendado com veto", aplicado: "aplicado",
};
export const SINAL = { fc: "FC", hrv: "HRV", spo2: "SpO₂", temperatura: "temperatura", respiracao: "respiração", sono: "sono", hidratacao: "hidratação" };

export const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const num = (v, casas = 0) => (v === null || v === undefined || v === "" ? "—"
  : Number(v).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas }));
export const hora = (iso, seg = false) => (iso ? iso.slice(11, seg ? 19 : 16) : "—");
export const sono = (min) => (min == null ? "—" : `${Math.floor(min / 60)}h${String(Math.round(min % 60)).padStart(2, "0")}`);
export const pct = (v) => `${Math.round(v * 100)}%`;

export async function api(caminho, body) {
  const r = await fetch(API + "/api" + caminho, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!r.ok) {
    let msg = `A API respondeu ${r.status}`;
    try { msg = (await r.json()).detail || msg; } catch { /* corpo vazio */ }
    throw new Error(msg);
  }
  return r.json();
}

// Só troca o HTML quando ele muda, e devolve o que estava digitado nos campos.
export function pintar(el, html) {
  if (!el || el.__html === html) return;
  const foco = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.campo : null;
  const valores = {};
  el.querySelectorAll("[data-campo]").forEach((c) => { valores[c.dataset.campo] = c.value; });
  el.innerHTML = html;
  el.__html = html;
  el.querySelectorAll("[data-campo]").forEach((c) => {
    if (valores[c.dataset.campo] !== undefined) c.value = valores[c.dataset.campo];
    if (c.dataset.campo === foco) c.focus();
  });
}

// Botões com data-acao="nome" data-arg="..." chamam acoes[nome](arg, botão).
export function ligarAcoes(acoes, aoErrar) {
  document.addEventListener("click", async (ev) => {
    const b = ev.target.closest("[data-acao]");
    if (!b || !acoes[b.dataset.acao]) return;
    try { await acoes[b.dataset.acao](b.dataset.arg, b); } catch (e) { aoErrar(e.message); }
  });
}

export function repetir(fn, ms = 1000) {
  const rodar = async () => { try { await fn(); } catch (e) { erro(e.message); } };
  rodar();
  return setInterval(rodar, ms);
}

export function erro(msg) {
  const el = document.querySelector("#erro");
  if (!el) return;
  el.hidden = !msg;
  el.textContent = msg ? (msg.includes("Failed to fetch") ? "API fora do ar. Na pasta 8-backend: uvicorn app.main:app --port 8000" : msg) : "";
  if (msg) { clearTimeout(el.__t); el.__t = setTimeout(() => { el.hidden = true; }, 6000); }
}

export const decidir = (evento_id, humano_id, acao, extra = {}) => api("/decisoes", { evento_id, humano_id, acao, ...extra });

export function prazo(ev) {
  return ev.prazo_restante_s == null ? "" : `<span class="prazo">${ev.prazo_restante_s} s</span>`;
}

export const RODAPE = "Protótipo experimental com dados simulados. Não é dispositivo médico.";
