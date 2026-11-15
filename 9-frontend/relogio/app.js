import { ESTADO, SINAL, TRIPULACAO, ajustarEquipe, api, cls, clsFaixa, decidir, erro, esc, hora, ligarAcoes, nome, num, pintar, prazo, repetir, sono } from "../compartilhado/api.js";

const tela = document.querySelector("#tela");
const dots = document.querySelector("#dots");
const bezel = document.querySelector("#bezel");
const TELAS = [["inicio", "Início"], ["sinais", "Sinais"], ["cosmo", "Cosmo"], ["estufa", "Estufa"], ["elo", "Elo"], ["sinc", "Sincronia"]];
let eu = new URLSearchParams(location.search).get("quem") || "sarah";
let vista = "inicio";
let d = null;          // última resposta de /tripulantes/{id}/relogio
let conversa = [];     // chat com a Cosmo
let respirando = 0;    // segundos restantes da respiração guiada
let vistoEvento = null;

document.querySelector("#quem").innerHTML = TRIPULACAO.map((p) =>
  `<button type="button" data-acao="quem" data-arg="${p.id}"><span>${p.nome}</span></button>`).join("");

const fazer = (ev, acao, extra) => decidir(ev, eu, acao, extra).then(carregar);

ligarAcoes({
  quem: (id) => { eu = id; vista = "inicio"; conversa = []; d = null; return carregar(); },
  tela: (t) => { vista = t; desenhar(); },
  decidir: (arg) => { const [ev, acao] = arg.split("|"); return fazer(ev, acao); },
  beber: () => api("/habitos/agua", { tripulante_id: eu }).then(carregar),
  respirar: () => { respirando = 10; vista = "respira"; desenhar(); },
  parar: () => { respirando = 0; vista = "inicio"; desenhar(); },
  enviar: (tipo) => api("/relogio/enviar", { tripulante_id: eu, tipo }).then(carregar),
  perguntar: async (q) => {
    conversa.push({ quem: "eu", texto: q });
    vista = "cosmo"; desenhar();
    const r = await api("/cosmo/chat", { pergunta: q, superficie: "relogio", tripulante_id: eu });
    conversa.push({ quem: "cosmo", texto: r.resposta, fonte: r.fonte, modo: r.modo });
    desenhar();
  },
}, erro);

setInterval(async () => {
  if (respirando > 0 && --respirando === 0) {
    await api("/habitos/respiracao", { tripulante_id: eu });
    vista = "inicio"; carregar();
  } else if (respirando > 0) desenhar();
}, 1000);

async function carregar() {
  d = await api(`/tripulantes/${eu}/relogio`);
  ajustarEquipe(d.equipe);
  // Uma pendência nova toma a tela, como uma notificação no pulso.
  const topo = d.pendencias[0] || d.acompanhando.find((e) => e.tipo === "arritmia");
  if (topo && topo.id !== vistoEvento) { vistoEvento = topo.id; if (vista !== "respira") vista = "evento"; }
  if (!topo && vista === "evento") vista = "inicio";
  desenhar();
}

function desenhar() {
  if (!d) return;
  document.querySelectorAll("#quem button").forEach((b) => {
    b.setAttribute("aria-pressed", b.dataset.arg === eu);
    b.querySelector("span").textContent = nome(b.dataset.arg);  // o Marcus vira CMO sem médico a bordo
  });
  const temEvento = d.pendencias.length || d.acompanhando.some((e) => e.tipo === "arritmia");
  const lista = (temEvento ? [["evento", d.emergencia ? "Alerta" : "Evento"]] : []).concat(d.emergencia ? TELAS.filter((t) => ["sinais", "cosmo", "sinc"].includes(t[0])) : TELAS);
  pintar(dots, vista === "respira" ? "" : lista.map(([k, r]) => `<button type="button" data-acao="tela" data-arg="${k}" aria-current="${k === vista}">${r}</button>`).join(""));
  bezel.className = "bezel " + (d.emergencia ? "crit" : cls(d.eu.estado) === "warn" ? "warn" : "");
  const corpo = { inicio, sinais, cosmo, estufa, elo, sinc, evento, respira }[vista] || inicio;
  pintar(tela, corpo());
  const av = d.avisos[0];
  const el = document.querySelector("#aviso");
  el.hidden = !av; el.textContent = av ? av.texto : "";
  document.querySelector("#onde").innerHTML = `A bordo · ${hora(d.eu.gerada_em, true)}<br>${d.link.blackout ? "IA local · sem sinal" : esc(d.link.rotulo)}`;
  document.querySelector("#legenda").textContent = `${d.eu.nome} · ${d.eu.papel}. Esta tela só mostra o que é de ${d.eu.nome}; o que ela ou ele não compartilha não sai daqui.`;
}

function inicio() {
  const e = d.eu, c = d.contagem;
  const ciclo = d.ciclo && d.ciclo.na_janela ? `<p class="w-sub c-roxo">Só você vê · calendário de solo: trecho de cólica</p>` : "";
  return `<p class="w-sub">${e.nome} · ${hora(e.gerada_em)}</p>
    <h2 class="${cls(e.estado)}">${(ESTADO[e.estado] || e.estado).toUpperCase()}</h2>
    <p class="w-num">${num(e.fc)}<small>bpm</small> · ${num(e.spo2)}<small>% SpO₂</small></p>
    <p class="w-sub">homeostase ${e.homeostase}% · ${c.otimos} ótimos · ${c.atencao} atenção · ${c.criticos} críticos</p>
    <p class="w-sub">${e.qualidade === "bom" ? "Sinal bom" : "Sinal a confirmar antes de alarmar"}</p>${ciclo}`;
}

function sinais() {
  const e = d.eu;
  const linha = (rot, v, un, k) => `<span class="chip ${clsFaixa((e.metricas[k] || {}).faixa)}">${rot} ${v}${un}</span>`;
  return `<div class="w-tag">Seus sinais</div>
    <div class="chips" style="justify-content:center">${linha("FC", num(e.fc), " bpm", "fc")}${linha("SpO₂", num(e.spo2), "%", "spo2")}${linha("HRV", num(e.hrv), " ms", "hrv")}
    ${linha("Pele", num(e.temp_pele, 1), " °C", "temperatura")}${linha("Resp", num(e.respiracao), "", "respiracao")}${linha("Sono", sono(e.sono_min_noite), "", "sono")}
    ${linha("Água", num(e.agua_ml_dia), ` / ${num(e.agua_meta)} ml`, "hidratacao")}</div>
    <p class="w-sub">estresse ${e.estresse}/100 · dose ${num(e.dose_msv_dia, 2)} mSv hoje</p>
    <p class="w-sub">Cada faixa compara você com a sua própria linha de base.</p>`;
}

function cosmo() {
  const chips = d.emergencia ? ["O que está acontecendo?", "O que é fibrilação atrial?"]
    : d.link.blackout ? ["Quando volta o sinal?", "Como estou?"] : ["Como estou?", "Por que estou cansada?", "Preciso beber água?"];
  const fala = conversa.slice(-3).map((m) => `<div class="wb ${m.quem}">${esc(m.texto)}${m.fonte ? `<small>Fonte: ${esc(m.fonte.titulo)} · ${esc(m.modo)}</small>` : m.modo ? `<small>${esc(m.modo)}</small>` : ""}</div>`).join("");
  return `<div class="w-tag ${d.link.blackout ? "warn" : ""}">Cosmo · ${d.link.blackout ? "IA local, sem a Terra" : "no relógio"}</div>
    <div class="w-thread">${fala || '<div class="wb">Pergunte algo. Eu explico e cito o protocolo; quem decide é um humano.</div>'}</div>
    <div class="acoes">${chips.map((q) => `<button class="chip-btn" data-acao="perguntar" data-arg="${q}">${q}</button>`).join("")}</div>`;
}

function estufa() {
  const j = d.jogo;
  if (!j) return `<p class="w-sub">Missões pausadas durante o alerta.</p>`;
  const m = (ok, rot, botao) => `<span class="chip ${ok ? "ok" : ""}">${ok ? "✓ " : ""}${rot}</span>${ok ? "" : botao}`;
  return `<div class="w-tag ok">Bioma cooperativo</div>
    <p class="w-big">Estufa nível ${j.nivel}</p><div class="barra"><i style="width:${j.pct}%"></i></div>
    <p class="w-sub">${j.pct}% do nível · ${j.xp} XP da tripulação · sem ranking</p>
    <div class="acoes">${m(j.missoes.treino, "Esteira", "")}
      ${m(j.missoes.agua, "Água do dia", '<button class="btn water" data-acao="beber">+250 ml</button>')}
      ${m(j.missoes.respiracao, "Escudo mental", '<button class="btn" data-acao="respirar">Respirar</button>')}</div>`;
}

function elo() {
  const j = d.jogo;
  if (!j) return `<p class="w-sub">Elo pausado durante o alerta.</p>`;
  const msgs = d.mensagens.map((m) => `<div class="wb">${esc(m.texto)}<small>saiu da Terra ${hora(m.enviado_em, true)} · chegou ${hora(m.recebido_em, true)}</small></div>`).join("");
  return `<div class="w-tag">Elo Terra · família</div>
    <p class="w-sub">Corrida Terra–órbita: ${num(j.corrida_km, 1)} de ${j.corrida_meta} km</p>
    <div class="barra"><i style="width:${Math.min(100, j.corrida_km / j.corrida_meta * 100)}%"></i></div>
    <div class="w-thread">${msgs || '<p class="w-sub">Nenhuma mensagem nova da família.</p>'}</div>
    <div class="acoes">${j.brinde === "chegou" ? '<button class="btn water" data-acao="beber">Brindar com a Ana · +250 ml</button>' : ""}
      <button class="btn ghost" data-acao="enviar" data-arg="incentivo">Incentivo ao Lucas</button>
      <button class="btn ghost" data-acao="enviar" data-arg="recado_familia">Recado</button></div>`;
}

function sinc() {
  const l = d.link;
  const fila = l.fila.slice(0, 3).map((p) => `<span class="chip ${p.prioridade === 1 ? "crit" : ""}">P${p.prioridade} · ${p.estado === "fila" ? "na fila" : `chega em ${p.falta_s} s`}</span>`).join("");
  return `<div class="w-tag ${l.blackout ? "warn" : ""}">Sincronia · ${l.blackout ? "sem sinal" : esc(l.link)}</div>
    <p class="w-big">${l.blackout ? esc(l.volta_em) : esc(l.atraso_txt)}</p>
    <p class="w-sub">${l.blackout ? "até a próxima janela · " + esc(l.motivo_blackout) : "de atraso até a Terra" + (l.comprimido ? " · na demo, 1 min = 1 s" : "")}</p>
    <p class="w-sub">${l.fila.length} pacote(s) na fila · ${num(l.fila_mb, 1)} MB</p>
    <div class="chips" style="justify-content:center">${fila}</div>
    <div class="acoes"><button class="btn" data-acao="enviar" data-arg="sincronia">Sincronizar</button>
      <button class="btn crit" data-acao="enviar" data-arg="sos">SOS prioritário</button></div>`;
}

function respira() {
  return `<div class="w-tag">Respiração guiada</div><div class="respira"></div>
    <p class="w-sub">Inspire 4 s · solte 6 s<br><b>${respirando}</b> s restantes</p>
    <button class="btn ghost" data-acao="parar">Parar</button>`;
}

function evento() {
  const p = d.pendencias[0];
  if (p) return pendencia(p);
  const a = d.acompanhando.find((e) => e.tipo === "arritmia");
  if (!a) return inicio();
  const terra = a.medico_local === "terra";
  const fase = terra
    ? (a.estado === "em_execucao" ? `A ${esc(a.medico_nome)} confirmou de Houston · O₂ 2 L/min`
      : a.dados.seguras ? `${esc(nome(a.dados.seguras.por))} com você · O₂ 2 L/min. Médica na Terra decidindo.`
      : a.escalonamentos ? `Sem resposta no prazo: agora com ${esc(a.responsavel_nome)}` : `Médica na Terra avisada. ${esc(nome("marcus"))} vem ajudar.`)
    : a.estado === "em_execucao" ? `${a.responsavel_nome === nome(eu) ? "Atendimento" : esc(nome("marcus"))} a caminho · O₂ 2 L/min`
    : a.escalonamentos ? `Sem resposta no prazo: agora com ${esc(a.responsavel_nome)}` : "Oficial médico avisado. Respire devagar.";
  return `<div class="w-tag crit">Alerta médico</div><p class="w-big">Pare e sente-se</p>
    <p class="w-num">${num(d.eu.fc)}<small>bpm</small> · ${num(d.eu.spo2)}<small>%</small></p>
    <p class="w-sub">${fase}</p><p class="w-sub">Dizer "estou bem" não cancela este alerta: quem avalia é o médico.</p>`;
}

const contar = (e) => (e.medico_local === "terra" ? `Contar só à ${e.medico_nome}` : `Contar ao ${nome("marcus")}`);

function pendencia(e) {
  const b = (rot, acao, c = "") => `<button class="btn ${c}" data-acao="decidir" data-arg="${e.id}|${acao}">${rot}</button>`;
  const dd = e.dados;
  switch (e.tipo) {
    case "sensor_suspeito":
      if (e.estado === "confirmacao_astronauta") return `<div class="w-tag warn">Leitura estranha ${prazo(e)}</div><p class="w-big">SpO₂ ${num(dd.spo2)}%?</p>
        <p class="w-text">O sinal está fraco (${esc(dd.motivo || "baixa qualidade")}). Antes de avisar o médico: seu relógio está folgado?</p>
        <div class="acoes">${b("Ajustei o relógio", "ajustar_sensor", "primary")}${b("Está firme", "sensor_firme", "ghost")}</div>`;
      return `<div class="w-tag warn">Leitura suspeita · ${esc(e.nome)}</div><p class="w-text">Aguardando a medição com o oxímetro do kit. Registre no painel de bordo.</p>`;
    case "tempestade_solar":
      if (e.estado === "aguardando_humano") return `<div class="w-tag warn">Tempestade solar ${prazo(e)}</div><p class="w-big">Fluxo de prótons subindo</p>
        <p class="w-text">A rota até o abrigo já está acesa (ação reversível). Levar a tripulação agora?</p>
        ${dd.adiado ? '<p class="w-sub">Aguardando. Pergunto de novo em instantes.</p>' : `<div class="acoes">${b("Abrigo para todos", "confirmar", "warn")}${b("Aguardar", "adiar", "ghost")}</div>`}`;
      if (dd.fase === "fluxo_caindo") return `<div class="w-tag ok">Fluxo caindo</div><p class="w-big">Liberar a tripulação?</p>
        <p class="w-sub">Sua dose hoje: ${num(d.eu.dose_msv_dia, 2)} mSv</p><div class="acoes">${b("Liberar do abrigo", "liberar_abrigo", "primary")}</div>`;
      return `<div class="w-tag warn">No abrigo</div><p class="w-big">${num(d.eu.dose_msv_dia, 2)} mSv</p><p class="w-sub">sua dose hoje · fluxo ainda alto</p><p class="w-text">Tripulação protegida. Eu aviso quando for seguro sair.</p>`;
    case "prontidao_eva":
      return `<div class="w-tag">Escala · ${esc(dd.tarefa)}</div><p class="w-text">Prontidão da Elena: <b class="c-warn">${dd.prontidao.elena}%</b> (sono curto, reação mais lenta). Kenji: <b class="c-ok">${dd.prontidao.kenji}%</b>.</p>
        <p class="w-sub">A Cosmo não tira ninguém da escala. A decisão é sua.</p>
        <div class="acoes">${b("Trocar pelo Kenji", "trocar_escala", "primary")}${b("Manter a Elena", "manter_escala", "ghost")}</div>`;
    case "bem_estar":
      return `<div class="w-tag roxo">Só você vê isto</div><p class="w-text">Notei ${esc(dd.padrao)}. Quer conversar?</p>
        <div class="acoes"><button class="btn" data-acao="respirar">Respirar 1 min</button><button class="btn ghost" data-acao="enviar" data-arg="recado_familia">Pedir contato com a família</button></div>
        <div class="acoes">${b(contar(e), "compartilhar", "ghost")}${b("Só comigo", "manter_privado", "ghost")}</div>`;
    case "ciclo":
      if (dd.sintoma !== true) return `<div class="w-tag roxo">Só você vê isto</div>
        <p class="w-text">${dd.aviso_dias ? `Em ${dd.aviso_dias} dia(s)` : "Neste trecho"}: cólica, inchaço ou humor mais baixo. Você está sentindo?</p>
        <div class="acoes">${b("Estou sentindo", "confirmar_sintoma", "primary")}${b("Estou bem", "falso_alarme", "ghost")}</div>`;
      return `<div class="w-tag roxo">Só você vê isto</div><p class="w-text">${e.medico_local === "terra"
          ? `Sem médico a bordo: se contar, só a ${esc(e.medico_nome)}, em Houston, vê esses sintomas e o pedido de cuidado leve. O CMO e a família não veem.`
          : "Se contar ao Dr. Marcus, ele vê só isto: esses sintomas e o pedido de cuidado leve. Sem alarme. A família não vê."}</p>
        <div class="acoes"><button class="btn" data-acao="respirar">Respirar 1 min</button>${b(contar(e), "compartilhar", "ghost")}${b("Só comigo", "manter_privado", "ghost")}</div>`;
    case "linha_de_base":
      return `<div class="w-tag">Fora do seu padrão · nível 1</div>
        <p class="w-text">A combinação dos seus sinais saiu do seu padrão${e.sugestao.evidencias.length ? ` (${e.sugestao.evidencias.map((k) => SINAL[k] || k).join(", ")})` : ""}. Nenhum sinal está crítico sozinho. Como você está?</p>
        <div class="acoes">${b("É o meu normal hoje", "falso_alarme", "primary")}${b("Não estou bem", "confirmar_sintoma", "ghost")}</div>
        <p class="w-sub">Sua resposta vira rótulo para o próximo treino do modelo.</p>`;
    case "hidratacao":
      return `<div class="w-tag" style="color:var(--water)">Hidratação</div><p class="w-text">Faltam ${num(d.eu.agua_meta - d.eu.agua_ml_dia)} ml para a meta de hoje. Beber 250 ml agora?</p>
        <div class="acoes">${b("+250 ml", "aceitar_cuidado", "water")}${b("Agora não", "dispensar", "ghost")}</div>`;
    case "modo_noite":
      if (e.estado === "agendado") return `<div class="w-tag roxo">Modo noite ${prazo(e)}</div><p class="w-text">Vou deixar a luz mais quente e silenciar avisos. É reversível: você pode vetar.</p>
        <div class="acoes">${b("Vetar", "vetar", "ghost")}</div>`;
      return `<div class="w-tag ok">Modo noite ativo</div><p class="w-text">Luz em 2700 K e avisos silenciados. Emergências continuam passando.</p><div class="acoes">${b("Desfazer", "desfazer", "ghost")}</div>`;
    case "arritmia":
      if (e.medico_local === "terra") return `<div class="w-tag crit">${esc(e.nome)} precisa de você ${prazo(e)}</div>
        <p class="w-text">${e.escalonamentos ? "O responsável anterior não respondeu no prazo. " : ""}Sem médico a bordo: inicie as ações seguras (repouso, O₂ 2 L/min, ECG de 12 derivações).</p>
        <div class="acoes">${b("Iniciar ações seguras", "iniciar_seguras", "crit")}</div>
        <p class="w-sub">Protocolo e medicação: só com a ${esc(e.medico_nome)}, em Houston.</p>`;
      return `<div class="w-tag crit">${esc(e.nome)} precisa de você ${prazo(e)}</div>
        <p class="w-text">${e.escalonamentos ? "O responsável anterior não respondeu no prazo. " : ""}O protocolo da Cosmo aguarda um humano: ${esc(e.sugestao.texto)}.</p>
        <div class="acoes">${b("Confirmar protocolo", "confirmar", "crit")}${b("Assumir manualmente", "assumir", "ghost")}</div>
        <p class="w-sub">Medicação continua só com o oficial médico.</p>`;
    default:
      return `<div class="w-tag">${esc(e.tipo)}</div><p class="w-text">${esc(e.sugestao.texto)}</p><p class="w-sub">Decida no painel de bordo.</p>`;
  }
}

repetir(carregar, 1000);
