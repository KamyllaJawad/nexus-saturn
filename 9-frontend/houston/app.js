import { criarChat } from "../compartilhado/chat.js";
import { desenharTrilha } from "../compartilhado/trilha.js";
import { ESTADO, ESTADO_EVENTO, TIPO, ajustarEquipe, api, cls, clsFaixa, erro, esc, hora, ligarAcoes, nome, num, pintar, repetir, sono } from "../compartilhado/api.js";

const $ = (s) => document.querySelector(s);
const ACAO = { iniciar_seguras: "ações seguras iniciadas pelo CMO", aplicar_medicacao: "dose aplicada pelo CMO", liberar_medicacao: "medicação liberada",
  confirmar: "protocolo confirmado", assumir: "atendimento manual", recusar: "recusado", aprovar_exame: "exame aprovado",
  ordem_permanente: "ordem permanente aplicada pelo CMO, sem sinal" };
let atual = "sarah";
let d = null;
let serie = [];

ligarAcoes({
  quem: (id) => { atual = id; return carregar(); },
  parecer: async (ev) => {
    const texto = document.querySelector(`[data-campo="parecer-${ev}"]`).value.trim();
    if (!texto) return;
    await api("/houston/parecer", { evento_id: ev, texto });
    return carregar();
  },
  // Sem médico a bordo: a decisão médica sai daqui, assinada pela Dra. Rivera, e viaja pelo link.
  terra: async (arg) => {
    const [ev, acao] = arg.split("|");
    const extra = {};
    if (acao === "liberar_medicacao") {
      extra.dose = document.querySelector(`[data-campo="dose-${ev}"]`).value.trim();
      extra.pin = document.querySelector(`[data-campo="pin-${ev}"]`).value.trim();
    }
    if (acao === "marcar_conversa") extra.detalhe = { hora: "19:00" };
    await api("/houston/decisao", { evento_id: ev, acao, ...extra });
    return carregar();
  },
}, erro);

async function carregar() {
  d = await api("/houston/console");
  ajustarEquipe(d.missao.equipe);
  serie = await api(`/houston/serie/${atual}?segundos=60`);
  desenhar();
}

function desenhar() {
  if (!d) return;
  const m = d.missao, terra = m.equipe.local === "terra";
  $("#onde").innerHTML = `Hora da nave ${hora(m.hora_nave, true)}<br>dado de ${hora(d.dado_de, true)}`;
  pintar($("#brand"), terra ? `<b>Mission Control · ${esc(m.equipe.medico_nome)}</b><small>Médica responsável · não há médico a bordo</small>`
    : "<b>Mission Control · Houston</b><small>Console do flight surgeon</small>");
  $("#nao-chega").textContent = terra
    ? `Sem médico a bordo, saúde mental e ciclo chegam só para a ${m.equipe.medico_nome}, com consentimento, no quadro “Compartilhado só com você”. O resto de Houston e a família não veem. Sugestões de nível 1 do relógio ficam na nave.`
    : "Aviso de saúde mental e do ciclo ficam na nave. Houston não tem botão de protocolo nem de medicação: parecer é revisão, não comando.";
  const alerta = d.eventos.find((e) => e.tipo === "arritmia" && !["resolvido", "encerrado"].includes(e.estado));
  pintar($("#banner"), m.blackout
    ? `<p class="banner semsinal">Sem sinal desde ${hora(d.dado_de, true)}. ${esc(m.motivo_blackout)}. Mostrando o último dado recebido; o contato volta em ${esc(m.volta_em)}. ${terra ? `Sem médico a bordo, o CMO segue só os protocolos pré-aprovados. Daqui nada sai; na FA, vale a ordem permanente ${esc(m.ordem_permanente.id)} que você assinou antes do voo.` : "A nave segue decidindo a bordo."}</p>`
    : alerta ? `<p class="banner alerta">Alerta médico de ${esc(alerta.nome)}. Isto aconteceu a bordo às ${hora(alerta.gerado_em, true)} e chegou aqui às ${hora(alerta.recebido_em, true)}: ${alerta.medico_local !== "terra" ? "a tripulação já está agindo." : (alerta.medicacao || {}).via === "ordem_permanente" ? "sem sinal, o CMO usou a ordem permanente; a revisão é sua, por parecer." : "não há médico a bordo, e a decisão é sua."}</p>`
    : m.atraso_real_s >= 1 ? `<p class="banner">Você está vendo o passado: estes dados saíram da nave há ${esc(m.atraso_txt)}${m.comprimido ? " (na demo, 1 min de atraso = 1 s)" : ""}. Link: ${esc(m.link)}.</p>`
    : `<p class="banner">Dados quase em tempo real via ${esc(m.link)}.</p>`);
  const op = m.ordem_permanente;
  pintar($("#autonomia"), `<h3>Modo de autonomia</h3><p class="nota">${esc(m.autonomia)}</p>
    ${op.em_vigor ? `<div class="op-box"><h5>Ordem permanente ${esc(op.id)} · em vigor</h5><p class="nota">Assinada por você em ${esc(op.assinada_em)}: ${esc(op.dose)} na FA, só sem sinal, depois das ações seguras e com a FA ainda presente. ${m.blackout ? "<b>Vale agora:</b> a nave está sem sinal." : "Com sinal, quem decide é você, por este console."}</p></div>` : ""}`);
  pintar($("#quem"), d.tripulantes.map((t) => `<button type="button" data-acao="quem" data-arg="${t.tripulante_id}" aria-pressed="${t.tripulante_id === atual}">
    <span><i class="marca ${cls(t.estado)}"></i>${esc(t.nome)}</span><small>${ESTADO[t.estado]} · dado de ${hora(t.gerada_em, true)}</small></button>`).join("") || '<p class="nota">Nenhum dado recebido ainda.</p>');
  const t = d.tripulantes.find((x) => x.tripulante_id === atual);
  if (t) {
    const lad = (rot, v, un, k) => `<article class="tile ${k && t.metricas[k] ? clsFaixa(t.metricas[k].faixa) : "neutro"}"><div class="l">${rot}</div><div class="v">${v}<small>${un}</small></div></article>`;
    pintar($("#painel"), `<div class="topo-pessoa"><b>${esc(t.nome)} · ${esc(t.papel)}</b><span class="pill ${cls(t.estado)}">${ESTADO[t.estado]} · homeostase ${t.homeostase}%</span></div>
      <p class="nota">Gerado a bordo às ${hora(t.gerada_em, true)}. A hora de geração prevalece sobre a hora em que a Terra recebeu.</p>
      <div><span class="eyebrow">Frequência cardíaca · últimos 60 s recebidos</span>${spark(serie)}</div>
      <div class="tiles">${lad("Frequência", num(t.fc), "bpm", "fc")}${lad("SpO₂", num(t.spo2), "%", "spo2")}${lad("HRV", num(t.hrv), "ms", "hrv")}
        ${lad("Respiração", num(t.respiracao), "irpm", "respiracao")}${lad("Pele", num(t.temp_pele, 1), "°C", "temperatura")}${lad("Pressão", `${t.pa_sys}/${t.pa_dia}`, "mmHg")}
        ${lad("Água", num(t.agua_ml_dia), "ml", "hidratacao")}${lad("Sono", sono(t.sono_min_noite), "", "sono")}${lad("Dose", num(t.dose_msv_dia, 2), "mSv")}</div>
      <p class="nota">Modelos a bordo nesse instante: M1 ${esc(t.m1.versao_modelo)}${t.m1.classe ? ` (${t.m1.classe}, P(FA) ${num(t.m1.prob_fa, 2)})` : " (não disparou: sinal suspeito)"} · M2 ${esc(t.m2.versao_modelo)} (${t.m2.qualidade}) · M3 ${esc(t.isolation_forest.versao_modelo)}.</p>`);
  }
  pintar($("#eventos"), d.eventos.length ? d.eventos.map((e) => {
    const fim = ["resolvido", "encerrado"].includes(e.estado);
    const deTerra = e.medico_local === "terra";
    return `<div class="dec ${e.tipo === "arritmia" && !fim ? "crit" : ""} ${fim ? "fim" : ""}"><h4>${TIPO[e.tipo]} · ${esc(e.nome)} <span class="chip">${ESTADO_EVENTO[e.estado]}</span></h4>
      <p>Sugestão da Cosmo a bordo: ${esc(e.sugestao.texto)} (confiança ${Math.round(e.sugestao.confianca * 100)}%, ${esc(e.sugestao.versao_modelo)}).</p>
      ${deTerra && ["arritmia", "dor_de_cabeca"].includes(e.tipo) ? decisaoTerra(e, fim) : ""}
      ${e.decisao ? `<p>${e.decisao.humano_id === "rivera" ? "Sua decisão, aplicada a bordo" : "Decisão a bordo"}: <b>${esc(ACAO[e.decisao.acao] || e.decisao.acao.replace(/_/g, " "))}</b> por ${esc(nome(e.decisao.humano_id))} às ${hora(e.decisao.decidida_em, true)}${e.decisao.dose ? ` · dose ${esc(e.decisao.dose)}` : ""}.</p>`
        : deTerra ? "" : "<p>A decisão do humano a bordo ainda não chegou.</p>"}
      <p class="meta">gerado ${hora(e.gerado_em, true)} · último pacote enviado ${hora(e.enviado_em, true)} · recebido ${hora(e.recebido_em, true)}</p>
      ${e.parecer_entregue ? '<p class="c-ok">Parecer entregue a bordo.</p>' : `<textarea class="campo" data-campo="parecer-${e.id}">De acordo com a conduta. Manter O₂ por 20 min, repetir ECG de 12 derivações em 1 h e suspender treino por 24 h.</textarea>
      <div class="acoes"><button class="btn sm primary" data-acao="parecer" data-arg="${e.id}"${m.blackout ? " disabled" : ""}>Enviar parecer à nave</button><span class="nota">chega a bordo em ${esc(m.atraso_txt)}</span></div>`}</div>`;
  }).join("") : '<p class="nota">Nenhum evento clínico chegou ainda.</p>');
  const lista = (ps, vazio) => (ps.length ? `<ul class="lista">${ps.map((p) => `<li class="p${p.prioridade}"><time>${p.estado === "entregue" ? `gerado ${hora(p.gerado_em, true)} · recebido ${hora(p.entregue_em, true)}` : p.estado === "fila" ? "na fila: sem sinal" : `a caminho · chega em ${p.falta_s} s`} · P${p.prioridade}</time>${esc(p.rotulo)}</li>`).join("")}</ul>` : `<p class="nota">${vazio}</p>`);
  $("#privados").hidden = !terra && !d.compartilhados.length;
  pintar($("#compartilhados"), d.compartilhados.length ? d.compartilhados.map((c) => {
    const conversa = c.minhas_decisoes.find((x) => x.acao === "marcar_conversa");
    return `<div class="dec roxo"><h4>${esc(c.nome)} · ${c.tipo === "bem_estar" ? "bem-estar" : c.tipo === "ciclo" ? "ciclo" : "não está bem"}</h4>
      <p>${esc(c.resumo)}</p>
      ${c.tipo === "bem_estar" ? (conversa ? `<p>${statusTerra(conversa)}</p>` : `<div class="acoes"><button class="btn sm ghost" data-acao="terra" data-arg="${c.evento_id}|marcar_conversa"${m.blackout ? " disabled" : ""}>Marcar conversa privada às 19:00</button></div>`) : ""}
      <p class="meta">consentimento da própria pessoa · gerado ${hora(c.gerado_em, true)} · recebido ${hora(c.recebido_em, true)} · o CMO, o resto de Houston e a família não veem</p></div>`;
  }).join("") : '<p class="nota">Nada compartilhado com você. Sem consentimento, saúde mental e ciclo não saem do relógio.</p>');
  desenharTrilha($("#trilha"), d.trilha_cosmo, { superficie: "houston" });
  pintar($("#recebido"), lista(d.recebidos, "Nada recebido ainda nesta sessão.") + (d.enviados.length ? `<p class="eyebrow" style="margin-top:10px">Enviado para a nave</p>${lista(d.enviados, "")}` : ""));
}

// ---- sem médico a bordo: a médica de voo decide daqui
function statusTerra(x) {
  const onde = x.estado === "aplicada" ? `<span class="c-ok">chegou a bordo às ${hora(x.chegou_em, true)} e foi aplicada</span>`
    : x.estado === "não aplicada" ? `<span class="c-warn">chegou, mas não se aplicou: ${esc(x.motivo)}</span>`
    : x.pacote_estado === "fila" ? '<span class="c-warn">na fila: sem sinal</span>' : `a caminho · chega a bordo em ${x.falta_s} s`;
  return `Você enviou às ${hora(x.enviada_em, true)}: <b>${esc(x.rotulo)}</b>${x.dose ? ` (${esc(x.dose)})` : ""} · ${onde}.`;
}

function decisaoTerra(e, fim) {
  const m = d.missao, minhas = e.minhas_decisoes, bloq = m.blackout ? " disabled" : "";
  const tem = (a) => minhas.find((x) => x.acao === a && x.estado !== "não aplicada");
  const conduta = tem("confirmar") || tem("recusar");
  const sg = e.acoes_seguras;
  if (e.medicacao && e.medicacao.via === "ordem_permanente") {
    return `<div class="op-box"><h5>Usada a ordem permanente ${esc(e.medicacao.ordem)}</h5>
      <p>Sem sinal, ${esc(nome(e.medicacao.aplicada_por))} (CMO) aplicou ${esc(e.medicacao.dose)} às ${hora(e.medicacao.aplicada_em, true)}, depois das ações seguras${sg ? ` (${hora(sg.quando, true)})` : ""}. Não há o que liberar daqui: a revisão é sua, por parecer.</p></div>`;
  }
  let botoes = "";
  if (!fim && e.estado === "aguardando_humano" && !conduta) {
    botoes = e.tipo === "arritmia"
      ? `<div class="acoes"><button class="btn sm crit" data-acao="terra" data-arg="${e.id}|confirmar"${bloq}>Confirmar protocolo</button><button class="btn sm ghost" data-acao="terra" data-arg="${e.id}|recusar"${bloq}>Recusar: falso alarme</button></div>`
      : tem("aprovar_exame") ? "" : `<div class="acoes"><button class="btn sm primary" data-acao="terra" data-arg="${e.id}|aprovar_exame"${bloq}>Aprovar ultrassom ocular</button><button class="btn sm ghost" data-acao="terra" data-arg="${e.id}|recusar"${bloq}>Recusar</button></div>`;
  }
  let med = "";
  if (e.tipo === "arritmia" && !fim && (tem("confirmar") || e.estado === "em_execucao")) {
    med = tem("liberar_medicacao") ? (e.medicacao && e.medicacao.aplicada ? `<p class="c-ok">O CMO registrou a aplicação da dose às ${hora(e.medicacao.aplicada_em, true)}.</p>` : "")
      : `<div class="acoes"><input class="campo" data-campo="dose-${e.id}" placeholder="Dose (você define)" size="16"><input class="campo" data-campo="pin-${e.id}" placeholder="PIN" size="5" type="password"><button class="btn sm warn" data-acao="terra" data-arg="${e.id}|liberar_medicacao"${bloq}>Liberar antiarrítmico</button></div><p class="meta">Medicação é sempre um passo separado. PIN de demonstração: 2026. O CMO aplica quando a liberação chegar.</p>`;
  }
  return `<div class="terra-box"><h5>${fim ? "Decisão médica na Terra" : "Você decide: não há médico a bordo"}</h5>
    <p>${sg ? `O CMO iniciou as ações seguras às ${hora(sg.quando, true)}: ${esc(sg.acoes)}.` : "As ações seguras do CMO ainda não constam no que chegou."} ${e.tipo === "arritmia" ? "A Cosmo propõe repouso, O₂ 2 L/min, ECG de 12 derivações e antiarrítmico do kit." : "A Cosmo sugere ultrassom ocular guiado para descartar SANS."}</p>
    ${minhas.map((x) => `<p>${statusTerra(x)}</p>`).join("")}
    ${botoes}${med}
    ${m.blackout ? '<p class="c-warn">Sem sinal: nada sai daqui até o contato voltar. A bordo, só protocolos pré-aprovados.</p>' : !fim ? `<p class="meta">Cada decisão chega a bordo em ${esc(m.atraso_txt)}${m.comprimido ? " (na demo, 1 min = 1 s)" : ""} e só vale quando chega.</p>` : ""}</div>`;
}

function spark(pontos) {
  if (pontos.length < 2) return '<p class="nota">Ainda sem pontos suficientes.</p>';
  const v = pontos.map((p) => p.fc), lo = Math.min(...v) - 2, hi = Math.max(...v) + 2;
  const dd = v.map((x, i) => `${i ? "L" : "M"}${((i / (v.length - 1)) * 600).toFixed(1)} ${(66 - ((x - lo) / (hi - lo)) * 62).toFixed(1)}`).join(" ");
  return `<svg class="spark" viewBox="0 0 600 70" preserveAspectRatio="none" role="img" aria-label="Frequência cardíaca recebida, de ${Math.min(...v)} a ${Math.max(...v)} bpm"><path d="${dd}"></path></svg>
    <p class="nota">mínima ${Math.min(...v)} · máxima ${Math.max(...v)} bpm</p>`;
}

criarChat($("#cosmo"), {
  superficie: "houston", foco: () => atual,
  saudacao: "Sou a Cosmo Terra. Só sei o que já atravessou o link: cada resposta diz de quando é o dado. Com médico a bordo, parecer é revisão; sem médico a bordo, a decisão médica é sua.",
});
repetir(carregar, 1000);
