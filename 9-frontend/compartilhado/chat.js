// Chat da Cosmo, usado no painel de bordo e em Houston. Guarda a conversa na
// página, busca as perguntas principais do cenário em curso e mostra a fonte de
// cada resposta. A Cosmo só lê: nenhuma chamada daqui muda o estado de um evento.
import { api, erro, esc, pintar } from "./api.js";
import { rodapeChat } from "./trilha.js";

export function criarChat(el, { superficie, foco, saudacao }) {
  const conversa = [{ quem: "cosmo", texto: saudacao }];
  let ocupado = false;
  el.innerHTML = `<div class="chat-fio" aria-live="polite"></div>
    <div class="chat-sug"></div>
    <form class="chat-form"><input class="campo" placeholder="Pergunte à Cosmo" aria-label="Pergunta para a Cosmo" autocomplete="off">
      <button class="btn sm primary" type="submit">Perguntar</button>
      <button class="btn sm ghost" type="button" data-limpar>Limpar</button></form>
    <p class="meta">A Cosmo explica e cita o protocolo; não tem permissão de ação. ${superficie === "houston" ? "Aqui ela só sabe o que já chegou à Terra." : "Dado privado sem consentimento não entra na resposta."}</p>`;
  const fio = el.querySelector(".chat-fio"), sug = el.querySelector(".chat-sug"), campo = el.querySelector("input");

  function desenhar() {
    fio.innerHTML = conversa.map((m) => `<div class="chat-msg ${m.quem}">${esc(m.texto)}${m.fonte ? `<small>Fonte: ${esc(m.fonte.titulo)} · ${esc(m.fonte.referencia)}</small>` : ""}${m.modo ? `<small>${esc(m.modo)} · vê ${esc(m.visao)}</small>` : ""}${m.trilha ? `<small title="Trilha da Cosmo">${esc(rodapeChat(m.trilha))}</small>` : ""}</div>`).join("")
      + (ocupado ? '<div class="chat-msg cosmo"><i>…</i></div>' : "");
    fio.scrollTop = fio.scrollHeight;
  }

  async function perguntar(q) {
    q = (q || "").trim();
    if (!q || ocupado) return;
    conversa.push({ quem: "eu", texto: q });
    ocupado = true; desenhar();
    try {
      const r = await api("/cosmo/chat", { pergunta: q, superficie, tripulante_id: foco() });
      conversa.push({ quem: "cosmo", texto: r.resposta, fonte: r.fonte, modo: r.modo, visao: r.visao, trilha: r.trilha });
    } catch (e) {
      conversa.push({ quem: "cosmo", texto: "Não consegui responder agora." }); erro(e.message);
    }
    ocupado = false; desenhar(); sugerir();
  }

  async function sugerir() {
    const grupos = await api(`/cosmo/perguntas?superficie=${superficie}&tripulante_id=${foco()}`);
    const abertos = new Set([...sug.querySelectorAll("details[open]")].map((d) => d.dataset.grupo));
    const primeira = !sug.__html;
    pintar(sug, grupos.map((g) => `<details data-grupo="${esc(g.grupo)}" ${g.grupo === "Agora" || abertos.has(g.grupo) || (primeira && g === grupos[0]) ? "open" : ""}>
      <summary class="${g.grupo === "Agora" ? "agora" : ""}">${esc(g.grupo)}${g.grupo === "Agora" ? " · cenário em curso" : ""} <span>${g.perguntas.length}</span></summary>
      <div class="chips">${g.perguntas.map((q) => `<button type="button" class="chip-btn" data-pergunta="${esc(q)}">${esc(q)}</button>`).join("")}</div></details>`).join(""));
  }

  el.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-pergunta]");
    if (b) perguntar(b.dataset.pergunta);
    if (ev.target.closest("[data-limpar]")) { conversa.length = 1; desenhar(); }
  });
  el.querySelector("form").addEventListener("submit", (ev) => { ev.preventDefault(); const q = campo.value; campo.value = ""; perguntar(q); });
  desenhar();
  sugerir().catch(() => {});
  setInterval(() => sugerir().catch(() => {}), 2000);
  return { perguntar, sugerir };
}
