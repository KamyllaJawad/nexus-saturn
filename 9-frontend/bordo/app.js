import { criarChat } from "../compartilhado/chat.js";
import { desenharTrilha } from "../compartilhado/trilha.js";
import { ESTADO, ESTADO_EVENTO, SINAL, TIPO, ajustarEquipe, api, cls, clsFaixa, decidir, erro, esc, hora, ligarAcoes, nome, num, pintar, prazo, repetir, sono } from "../compartilhado/api.js";

const EU = "marcus";   // esta tela é do oficial médico (ou do CMO, sem médico a bordo)
const $ = (s) => document.querySelector(s);
let atual = "sarah";
let d = null;
let explicacoes = {};  // evento -> card "Por que a Cosmo sugeriu isso?"
let ultimoAlerta = null;

ligarAcoes({
  quem: (id) => { atual = id; desenhar(); desenharEcg(); },
  decidir: (arg, b) => {
    const [ev, acao] = arg.split("|");
    const extra = {};
    if (acao === "liberar_medicacao") {
      extra.dose = document.querySelector(`[data-campo="dose-${ev}"]`).value.trim();
      extra.pin = document.querySelector(`[data-campo="pin-${ev}"]`).value.trim();
    }
    if (acao === "ordem_permanente" && !window.confirm(`Aplicar ${d.missao.ordem_permanente.dose} pela ordem permanente ${d.missao.ordem_permanente.id}? Fica assinado por você e sobe como P1.`)) return null;
    if (acao === "registrar_kit") extra.detalhe = { spo2_kit: Number(document.querySelector(`[data-campo="kit-${ev}"]`).value) };
    if (acao === "marcar_conversa") extra.detalhe = { hora: "19:00" };
    if (acao === "recusar") extra.detalhe = { motivo: "falso alarme, avaliado pelo oficial médico" };
    return decidir(ev, EU, acao, extra).then(carregar);
  },
  explicar: async (ev) => {
    explicacoes[ev] = explicacoes[ev] ? null : await api(`/eventos/${ev}/explicacao`);
    desenhar();
  },
}, erro);

async function carregar() {
  d = await api("/bordo");
  ajustarEquipe(d.missao.equipe);
  // Um alerta clínico novo leva o painel direto para a pessoa.
  const alerta = d.eventos.find((e) => e.tipo === "arritmia" && e.estado === "aguardando_humano");
  if (alerta && alerta.id !== ultimoAlerta) { ultimoAlerta = alerta.id; atual = alerta.tripulante_id; }
  desenhar();
}

function desenhar() {
  if (!d) return;
  const m = d.missao, terra = m.equipe.local === "terra";
  $("#onde").innerHTML = `A bordo · ${hora(m.hora_nave, true)}<br>${esc(m.rotulo)}`;
  pintar($("#brand"), terra ? `<b>Enfermaria · Marcus (CMO)</b><small>Sem médico a bordo · decisões médicas com a ${esc(m.equipe.medico_nome)}, em Houston</small>`
    : "<b>Enfermaria · Dr. Marcus</b><small>Painel de bordo · oficial médico</small>");
  $("#titulo-cosmo").textContent = terra ? "Cosmo · chat do copiloto do CMO" : "Cosmo · chat do copiloto médico";
  pintar($("#chips"), `<span class="chip ${terra ? "warn" : "ok"}">${terra ? "Médico na Terra · " + esc(m.equipe.medico_nome) : "Médico a bordo"}</span>
    <span class="chip ${m.blackout ? "warn" : ""}">${m.blackout ? "Houston fora de alcance" : "Houston · " + esc(m.atraso_txt)}</span>
    <span class="chip ok">Rede local · 4 tripulantes</span>
    <span class="chip ${m.cabine.co2 > 3 ? "warn" : ""}">CO₂ ${num(m.cabine.co2, 1)} mmHg</span>
    ${m.cabine.fluxo !== "normal" ? `<span class="chip warn">Prótons: fluxo ${m.cabine.fluxo}</span>` : ""}
    ${m.cabine.luz === "noite" ? '<span class="chip">Modo noite</span>' : ""}`);
  pintar($("#quem"), d.tripulantes.map((t) => {
    const fora = Object.entries(t.metricas).find(([, v]) => v.faixa !== "padrao");
    return `<button type="button" data-acao="quem" data-arg="${t.tripulante_id}" aria-pressed="${t.tripulante_id === atual}">
      <span><i class="marca ${cls(t.estado)}"></i>${esc(t.nome)}</span>
      <small>${esc(t.papel)}${fora ? ` · ${SINAL[fora[0]] || fora[0]} ${fora[1].faixa === "critico" ? "crítico" : "em atenção"}` : ""}</small></button>`;
  }).join(""));
  const t = d.tripulantes.find((x) => x.tripulante_id === atual);
  pintar($("#topo"), `<div class="topo-pessoa"><b>${esc(t.nome)} · ${esc(t.papel)}</b>
    <span class="pill ${cls(t.estado)}">${ESTADO[t.estado]} · homeostase ${t.homeostase}%</span></div>
    <p class="nota">Leitura de ${hora(t.gerada_em, true)} · cada faixa compara ${esc(t.nome)} com a própria linha de base (z robusto ${t.versao_z}).</p>`);
  pintar($("#ficha"), ficha(t));
  pintar($("#eventos"), d.eventos.length ? d.eventos.map(cartao).join("") : '<p class="nota">Nenhuma decisão pendente.</p>');
  pintar($("#avisos"), d.avisos_compartilhados.length ? d.avisos_compartilhados.map(aviso).join("")
    : terra ? `<p class="nota">Sem médico a bordo, saúde mental e ciclo não chegam a este painel: com consentimento, vão só para a ${esc(m.equipe.medico_nome)}, em Houston.</p>`
    : '<p class="nota">Ninguém compartilhou um aviso. Saúde mental e ciclo só chegam aqui com consentimento.</p>');
  desenharTrilha($("#trilha"), d.trilha_cosmo, { superficie: "bordo" });
  const s = Object.entries(d.sombra);
  $("#sombra").hidden = !s.length;
  pintar($("#sombra"), s.length ? `<h3>Modelo em modo sombra</h3>${s.map(([p, v]) =>
    `<p class="nota"><b class="c-acc">${v.versao}</b> roda em paralelo, sem agir: ${v.leituras} leituras, ${v.divergem} divergências do modelo em serviço.</p>`).join("")}
    <div class="acoes"><a class="btn sm" href="../dados-ia/" target="_top">Revisar e aprovar</a></div>` : "");
}

function ladrilho(rot, valor, un, fonte, m) {
  const z = m ? ` · z ${num(m.z, 1)}` : "";
  return `<article class="tile ${m ? clsFaixa(m.faixa) : "neutro"}"><div class="l">${rot}</div><div class="v">${valor}<small>${un}</small></div><div class="src">${fonte}${z}</div></article>`;
}

function ficha(t) {
  const m = t.metricas, f = t.isolation_forest, m1 = t.m1, m2 = t.m2;
  const renal = t.agua_ml_dia / t.agua_meta;
  return `<div class="tiles" style="margin-top:10px">
    ${ladrilho("Frequência cardíaca", num(t.fc), "bpm", "Relógio · PPG + ECG", m.fc)}
    ${ladrilho("Saturação de O₂", num(t.spo2), "%", "Relógio · oxímetro", m.spo2)}
    ${ladrilho("Variabilidade", num(t.hrv), "ms", "Relógio · PPG", m.hrv)}
    ${ladrilho("Respiração", num(t.respiracao), "irpm", "Patch torácico", m.respiracao)}
    ${ladrilho("Temperatura da pele", num(t.temp_pele, 1), "°C", "Relógio · pele", m.temperatura)}
    ${ladrilho("Pressão", `${t.pa_sys}/${t.pa_dia}`, "mmHg", "Manguito do kit · manhã")}
    ${ladrilho("Água", num(t.agua_ml_dia), `de ${num(t.agua_meta)} ml`, "Registro", m.hidratacao)}
    ${ladrilho("Sono", sono(t.sono_min_noite), "", "Actigrafia", m.sono)}
    ${ladrilho("Estresse", num(t.estresse), "/100", "Derivado: HRV + sono")}
    ${ladrilho("Dose hoje", num(t.dose_msv_dia, 2), "mSv", "Dosímetro pessoal")}
  </div>
  <p class="nota" style="margin:8px 0">Rins: risco <b class="${renal < 0.6 ? "c-crit" : renal < 0.8 ? "c-warn" : "c-ok"}">${renal < 0.6 ? "alto" : renal < 0.8 ? "moderado" : "baixo"}</b> (água em ${Math.round(renal * 100)}% da meta + perda óssea do voo).</p>
  <div class="modelos">
    <div class="modelo"><b>M2 · ${m2.versao_modelo}</b>Sinal ${m2.qualidade === "bom" ? '<span class="c-ok">bom</span>' : '<span class="c-warn">suspeito</span>'} (${num(m2.confianca, 2)})${m2.motivo ? `<br>${esc(m2.motivo)}` : ""}</div>
    <div class="modelo"><b>M1 · ${m1.versao_modelo}</b>${m1.classe ? `Ritmo: <span class="${m1.classe === "fa" ? "c-crit" : ""}">${m1.classe === "fa" ? "fibrilação atrial" : m1.classe === "outro" ? "outro ritmo" : "normal"}</span> · P(FA) ${num(m1.prob_fa, 2)}` : `<span class="c-warn">${esc(m1.motivo)}</span>`}</div>
    <div class="modelo"><b>M3 floresta · ${f.versao_modelo}</b>Escore ${num(f.score, 3)} · limiar ${num(f.limiar, 3)}<br>${f.anomalo ? `<span class="c-warn">combinação fora do padrão</span>${f.evidencias.length ? ": " + f.evidencias.map((k) => SINAL[k] || k).join(", ") : ""}` : f.acima_do_limiar ? `acima do limiar há ${f.seguidas} de ${f.persistencia} leituras` : "combinação no padrão"}</div>
    ${t.sombra["m3-if"] ? `<div class="modelo"><b>sombra · ${t.sombra["m3-if"].versao_modelo}</b>Escore ${num(t.sombra["m3-if"].score, 3)} · limiar ${num(t.sombra["m3-if"].limiar, 3)}<br>${t.sombra["m3-if"].anomalo ? "marcaria anomalia" : "não marcaria anomalia"} · não age</div>` : ""}
  </div>`;
}

const bt = (ev, rot, acao, c = "") => `<button class="btn sm ${c}" data-acao="decidir" data-arg="${ev.id}|${acao}">${rot}</button>`;

const parecerHtml = (dd) => (dd.parecer ? `<div class="explica"><b>Parecer de Houston</b> (revisão, não comando)<br>${esc(dd.parecer.texto)}<br><i>Enviado ${hora(dd.parecer.enviado_em, true)} · chegou a bordo ${hora(dd.parecer.recebido_em, true)}</i></div>` : "");

function explicacao(e) {
  const x = explicacoes[e.id];
  return `<button class="btn sm ghost" data-acao="explicar" data-arg="${e.id}">${x ? "Ocultar explicação" : "Por que a Cosmo sugeriu isso?"}</button>
    ${x ? `<div class="explica"><b>Evidências que mais pesaram</b><br>${x.evidencias.map(esc).join(" · ")}<br><b>Alternativa a considerar</b><br>${esc(x.alternativa)}<br>
      <b>Protocolo citado</b><br>${esc(x.protocolo.titulo)}: ${esc(x.protocolo.trecho)}<br><i>${esc(x.protocolo.fonte)}</i><br><b>Modelos</b><br>${x.modelos.map(esc).join("<br>")}</div>` : ""}`;
}

// ---- sem médico a bordo: o CMO inicia as ações seguras; a decisão médica vem da Terra
function esperaTerra(e) {
  const m = d.missao;
  if (m.blackout) return `<p class="c-warn">Sem sinal e sem médico a bordo: só os protocolos pré-aprovados. A decisão da ${esc(e.medico_nome)} fica bloqueada até o contato voltar (${esc(m.volta_em)})${e.tipo === "arritmia" ? "; na FA, vale a ordem permanente que ela assinou antes do voo" : ""}.</p>`;
  return `<p>O alerta saiu para Houston às ${hora(e.gerado_em, true)}. A resposta da ${esc(e.medico_nome)} leva ida e volta: ${esc(m.atraso_txt)} por trecho${m.comprimido ? ` (na demo, cerca de ${Math.round(2 * m.atraso_demo_s)} s no total)` : ""}. Daqui não dá para ver o pacote dela no caminho.</p>`;
}

function segurasHtml(e, texto) {
  const sg = e.dados.seguras;
  if (sg) return `<p class="c-ok">✓ Ações seguras em curso desde ${hora(sg.quando, true)}, por ${esc(nome(sg.por))}: ${esc(sg.acoes)}.</p>`;
  return e.responsavel_id === EU
    ? `<div class="acoes">${bt(e, `Iniciar ações seguras (${texto})`, "iniciar_seguras", "crit")}</div><p class="meta">Pré-aprovadas no protocolo: não esperam o atraso.</p>`
    : `<p class="c-warn">Prazo vencido: as ações seguras passaram para ${esc(e.responsavel_nome)}.</p>`;
}

// Sem sinal: a dose pré-autorizada pela médica de voo antes do voo (ADR-017).
function ordemHtml(e) {
  const m = d.missao, op = m.ordem_permanente, dd = e.dados;
  if (!op || !op.em_vigor || !m.blackout) return "";
  const crit = [["Sem médico a bordo", true], ["Sem sinal com a Terra", m.blackout], ["Ações seguras iniciadas", !!dd.seguras],
    ["O M1 ainda vê FA na última leitura", !!dd.fa_agora], ["Nenhuma dose aplicada neste evento", !dd.medicacao]];
  const ok = crit.every(([, v]) => v);
  return `<div class="op-box"><h5>Ordem permanente ${esc(op.id)} · assinada pela ${esc(op.assinada_por_nome)} em ${esc(op.assinada_em)}</h5>
    <p>${esc(op.titulo)}: <b>${esc(op.dose)}</b>. A dose não muda aqui.</p>
    <ul>${crit.map(([t, v]) => `<li class="${v ? "c-ok" : "c-warn"}">${v ? "✓" : "✗"} ${t}</li>`).join("")}</ul>
    <div class="acoes"><button class="btn sm warn" data-acao="decidir" data-arg="${e.id}|ordem_permanente"${ok ? "" : " disabled"}>Aplicar a dose da ordem permanente</button></div>
    <p class="meta">${esc(op.depois)}</p></div>`;
}

function arritmiaTerra(e) {
  const dd = e.dados, med = dd.medicacao;
  if (e.estado === "aguardando_humano") {
    return `<p><b>Cosmo propõe um protocolo · confiança ${Math.round(e.sugestao.confianca * 100)}%</b> (${esc(e.sugestao.versao_modelo)})</p>
      <ol><li>Interromper o esforço; ${esc(e.nome)} sentada em repouso.</li><li>O₂ por máscara a 2 L/min.</li><li>ECG de 12 derivações com o kit.</li><li>Desfibrilador de prontidão; reavaliar em 10 min.</li><li>Antiarrítmico do kit: só com a liberação da ${esc(e.medico_nome)}.</li></ol>
      <div class="terra-box"><h5>Decisão médica na Terra · ${esc(e.medico_nome)}</h5>
        <p>Não há médico a bordo: confirmar o protocolo e liberar o antiarrítmico é com ela, no console de Houston. Você inicia só as ações seguras.</p>
        ${segurasHtml(e, "repouso, O₂, ECG")}${esperaTerra(e)}</div>
      ${ordemHtml(e)}
      ${explicacao(e)}`;
  }
  if (med && med.via === "ordem_permanente") {
    return `<p>Conduta sem sinal: <b>ordem permanente ${esc(med.ordem)}</b>, assinada pela ${esc(nome(med.liberada_por))} em ${esc(med.quando)}, antes do voo.</p>
      <ul><li>${dd.seguras ? `Repouso e O₂ desde ${hora(dd.seguras.quando, true)} (ações seguras do CMO)` : "Repouso e O₂ 2 L/min"}</li><li>ECG de 12 derivações</li>
        <li>${esc(med.dose)}: aplicada por ${esc(nome(med.aplicada_por))} às ${hora(med.aplicada_em, true)}</li></ul>
      <p class="meta">O uso subiu como P1${d.missao.blackout ? " e está na fila até o sinal voltar" : ""}; a ${esc(e.medico_nome)} revisa por parecer.</p>
      ${parecerHtml(dd)}
      ${e.estado === "resolvido" ? '<p class="c-ok">Quadro resolvido: sem FA no M1 e SpO₂ fora da faixa crítica por 10 leituras seguidas.</p>' : ""}`;
  }
  if (e.estado === "em_execucao" || e.estado === "resolvido") {
    const dc = e.decisoes.find((x) => x.acao === "confirmar");
    const linhaMed = med ? (med.aplicada ? `Antiarrítmico ${esc(med.dose)}: liberado pela ${esc(nome(med.liberada_por))}, aplicado por ${esc(nome(med.aplicada_por))} às ${hora(med.aplicada_em, true)}`
      : `Liberação da ${esc(nome(med.liberada_por))} chegou às ${hora(med.quando, true)}: ${esc(med.dose)}`) : `Antiarrítmico: só se a ${esc(e.medico_nome)} liberar, de Houston`;
    return `<p>Protocolo confirmado pela ${esc(e.medico_nome)}, em Houston: a decisão chegou a bordo às ${hora(dc.decidida_em, true)}.</p>
      <ul><li>${dd.seguras ? `Repouso e O₂ desde ${hora(dd.seguras.quando, true)} (ações seguras do CMO)` : "Repouso e O₂ 2 L/min"}</li><li>ECG de 12 derivações</li><li>${linhaMed}</li></ul>
      ${med && !med.aplicada && e.estado === "em_execucao" ? `<div class="acoes">${bt(e, "Aplicar a dose prescrita", "aplicar_medicacao", "warn")}</div><p class="meta">Você aplica a dose que a médica definiu. A dose não muda aqui.</p>` : ""}
      ${!med && e.estado === "em_execucao" && d.missao.blackout ? esperaTerra(e) : ""}
      ${parecerHtml(dd)}
      ${e.estado === "resolvido" ? '<p class="c-ok">Quadro resolvido: sem FA no M1 e SpO₂ fora da faixa crítica por 10 leituras seguidas.</p>' : ""}`;
  }
  return `<p>Recusado pela ${esc(nome(e.decisoes[e.decisoes.length - 1].humano_id))}, em Houston: falso alarme. A recusa virou rótulo para o próximo treino do M1.</p>`;
}

function cartao(e) {
  const fim = ["resolvido", "encerrado"].includes(e.estado);
  const meu = e.responsavel_id === EU;
  const dd = e.dados;
  let corpo = "", cl = "";
  const cab = `<h4>${TIPO[e.tipo]} · ${esc(e.nome)} <span class="chip">${ESTADO_EVENTO[e.estado]}</span>${fim ? "" : prazo(e)}</h4>`;
  if (e.tipo === "arritmia" && e.medico_local === "terra") {
    cl = fim ? "" : "crit";
    corpo = arritmiaTerra(e);
  } else if (e.tipo === "arritmia") {
    cl = fim ? "" : "crit";
    if (e.estado === "aguardando_humano") {
      const x = explicacoes[e.id];
      corpo = `<p><b>Cosmo propõe um protocolo · confiança ${Math.round(e.sugestao.confianca * 100)}%</b> (${esc(e.sugestao.versao_modelo)})</p>
        <ol><li>Interromper o esforço; ${esc(e.nome)} sentada em repouso.</li><li>O₂ por máscara a 2 L/min.</li><li>ECG de 12 derivações com o kit.</li><li>Desfibrilador de prontidão; reavaliar em 10 min.</li><li>Antiarrítmico do kit: só com a sua liberação, em passo separado.</li></ol>
        <p>Nada é aplicado sem a confirmação de um humano.${meu ? "" : ` <b class="c-warn">Prazo vencido: escalonado para ${esc(e.responsavel_nome)}.</b>`}</p>
        <button class="btn sm ghost" data-acao="explicar" data-arg="${e.id}">${x ? "Ocultar explicação" : "Por que a Cosmo sugeriu isso?"}</button>
        ${x ? `<div class="explica"><b>Evidências que mais pesaram</b><br>${x.evidencias.map(esc).join(" · ")}<br><b>Alternativa a considerar</b><br>${esc(x.alternativa)}<br>
          <b>Protocolo citado</b><br>${esc(x.protocolo.titulo)}: ${esc(x.protocolo.trecho)}<br><i>${esc(x.protocolo.fonte)}</i><br><b>Modelos</b><br>${x.modelos.map(esc).join("<br>")}</div>` : ""}
        ${meu ? `<div class="acoes">${bt(e, "Confirmar protocolo", "confirmar", "crit")}${bt(e, "Assumir manualmente", "assumir", "ghost")}${bt(e, "Recusar: falso alarme", "recusar", "ghost")}</div>` : ""}`;
    } else if (e.estado === "em_execucao" || e.estado === "resolvido") {
      const med = dd.medicacao;
      corpo = `<p>${esc(dd.conduta === "atendimento manual" ? "Atendimento manual" : "Protocolo da Cosmo")} confirmado por ${esc(nome(e.decisoes[0].humano_id))} às ${hora(e.decisoes[0].decidida_em, true)}.</p>
        <ul><li>Repouso e O₂ 2 L/min</li><li>ECG de 12 derivações</li>
        <li>${med ? `Antiarrítmico liberado: ${esc(med.dose)}, por ${esc(nome(med.liberada_por))} às ${hora(med.quando, true)}` : "Antiarrítmico: aguardando a sua liberação"}</li></ul>
        ${!med && e.estado === "em_execucao" ? `<div class="acoes"><input class="campo" data-campo="dose-${e.id}" placeholder="Dose (você define)" size="16"><input class="campo" data-campo="pin-${e.id}" placeholder="PIN" size="5" type="password">${bt(e, "Liberar medicação", "liberar_medicacao", "warn")}</div><p class="meta">PIN de demonstração: 2026. Medicação nunca é automática.</p>` : ""}
        ${dd.parecer ? `<div class="explica"><b>Parecer de Houston</b> (revisão, não comando)<br>${esc(dd.parecer.texto)}<br><i>Enviado ${hora(dd.parecer.enviado_em, true)} · chegou a bordo ${hora(dd.parecer.recebido_em, true)}</i></div>` : '<p class="meta">Houston recebe com o atraso da missão e revisa depois. A decisão é de bordo.</p>'}
        ${e.estado === "resolvido" ? '<p class="c-ok">Quadro resolvido: sem FA no M1 e SpO₂ fora da faixa crítica por 10 leituras seguidas.</p>' : ""}`;
    } else corpo = `<p>Recusado por ${esc(nome(e.decisoes[0].humano_id))}: falso alarme. A recusa virou rótulo para o próximo treino do M1.</p>`;
  } else if (e.tipo === "sensor_suspeito") {
    corpo = e.estado === "confirmacao_astronauta" ? `<p>SpO₂ de ${num(dd.spo2)}% com sinal suspeito. A Cosmo perguntou a ${esc(e.nome)} se o relógio está folgado. Ainda não é alarme.</p>`
      : e.estado === "aguardando_humano" ? `<p>SpO₂ de ${num(dd.spo2)}% no relógio com sinal de baixa qualidade (${esc(dd.motivo || "")}). Chegou aqui porque ${esc(dd.escalou_por)}. Sugestão da Cosmo: medir com o oxímetro de dedo do kit.</p>
        <div class="acoes"><input class="campo" data-campo="kit-${e.id}" value="97" size="4" inputmode="numeric" aria-label="SpO₂ medida no kit">${bt(e, "Registrar medição do kit", "registrar_kit", "primary")}</div>`
        : `<p>${esc(dd.desfecho || "")}. Virou rótulo para o M2.</p>`;
  } else if (e.tipo === "tempestade_solar") {
    const fase = e.estado === "aguardando_humano" ? "aguardando a comandante" : dd.fase === "fluxo_caindo" ? "fluxo caindo, a comandante decide a saída" : fim ? "encerrada" : "tripulação no abrigo";
    corpo = `<p>Rota até o abrigo acesa automaticamente (nível 4, reversível). Situação: ${fase}.</p>
      <div class="kv">${d.tripulantes.map((t) => `<div><span>${esc(t.nome)}</span><b>${num(t.dose_msv_dia, 2)} mSv</b></div>`).join("")}</div>
      <p class="meta">A decisão de abrigo é da comandante; você acompanha a dose.</p>`;
  } else if (e.tipo === "prontidao_eva") {
    corpo = `<div class="kv">${Object.entries(dd.prontidao).map(([k, v]) => `<div><span>${esc(nome(k))}</span><b class="${v < 70 ? "c-warn" : ""}">${v}%</b></div>`).join("")}</div>
      <p>${dd.resultado ? `Decisão da comandante: ${esc(dd.resultado)}.` : `${esc(dd.motivo)}. A decisão da escala é da comandante.`}</p>`;
  } else if (e.tipo === "dor_de_cabeca") {
    const li = (est, feito, andando, pend) => `<li>${est === "feito" ? "✓ " + feito : est ? "… " + andando : pend}</li>`;
    corpo = `<p>A Cosmo cruzou a queixa de ${esc(e.nome)} com o ar da cabine: CO₂ em ${num(dd.co2, 1)} mmHg na hora da queixa (alvo abaixo de 3) e mais ${dd.outros_com_sintoma.length} tripulantes com sintoma. Hipótese principal: CO₂ elevado. A descartar: ${esc(e.sugestao.alternativa)}.</p>
      <ul>${li(dd.ar, `Ar ajustado pela Elena: ${num(d.missao.cabine.co2, 1)} mmHg`, "Elena ajustando os filtros de CO₂", "Ajuste do ar: pendente")}
      ${li(dd.exame, "Ultrassom ocular concluído; imagens enviadas a Houston para laudo", "Ultrassom guiado em andamento",
        e.medico_local === "terra" ? `Ultrassom ocular: aguardando a aprovação da ${esc(e.medico_nome)}` : "Ultrassom ocular: aguardando a sua aprovação")}</ul>
      ${fim ? "" : e.medico_local === "terra"
        ? (e.estado === "aguardando_humano" ? `<div class="terra-box"><h5>Decisão médica na Terra · ${esc(e.medico_nome)}</h5><p>Sem médico a bordo, o ultrassom ocular (SANS) é aprovado de Houston. O ajuste do ar não espera.</p>${segurasHtml(e, "repouso e ajuste do ar")}${esperaTerra(e)}</div>` : "")
        : `<div class="acoes">${dd.ar ? "" : bt(e, "Pedir ajuste do ar à Elena", "pedir_ajuste_ar", "ghost")}${dd.exame ? "" : bt(e, "Aprovar ultrassom guiado", "aprovar_exame", "primary")}</div>`}`;
  } else if (e.tipo === "bem_estar") {
    cl = "roxo";
    corpo = `<p>${esc(e.nome)} autorizou só você a ver este resumo, sem gravações: ${esc(dd.padrao)}.</p>
      ${e.estado === "em_execucao" ? `<div class="acoes">${bt(e, "Marcar conversa às 19:00", "marcar_conversa", "ghost")}</div>` : dd.conversa ? `<p>Conversa marcada às ${esc(dd.conversa)}.</p>` : ""}`;
  } else if (e.tipo === "modo_noite") {
    corpo = `<p>Ação de nível 4, reversível: ${e.estado === "agendado" ? "agendada, com janela de veto" : e.estado === "aplicado" ? "aplicada, pode ser desfeita" : esc(dd.desfecho || "encerrada")}.</p>`;
  }
  return `<div class="dec ${cl} ${fim ? "fim" : ""}">${cab}${corpo}
    <p class="meta">nível ${e.nivel_autonomia} · responsável: ${esc(e.responsavel_nome)} · aberto ${hora(e.gerado_em, true)}${e.escalonamentos ? ` · ${e.escalonamentos} escalonamento(s)` : ""}</p></div>`;
}

function aviso(e) {
  if (e.tipo === "ciclo") return `<div class="dec roxo"><h4>${esc(e.nome)} compartilhou um aviso</h4>
    <p>Ela pode ter cólica, inchaço ou humor mais baixo neste trecho e pediu cuidado leve. O estado segue como está. Não é diagnóstico. Analgésico do kit só se ela pedir, em passo separado.</p>
    <p class="meta">Você vê só isto. Houston e a família não recebem.</p></div>`;
  return `<div class="dec"><h4>${esc(e.nome)} · combinação fora do padrão <span class="chip">nível 1</span></h4>
    <p>${esc(e.nome)} respondeu que não está bem. Sinais que mais pesaram: ${e.sugestao.evidencias.map((k) => SINAL[k] || k).join(", ") || "combinação"}. Nenhum sinal crítico sozinho; é informação, não evento clínico.</p>
    <p class="meta">${esc(e.sugestao.versao_modelo)} · ${hora(e.gerado_em, true)}</p></div>`;
}

async function desenharEcg() {
  const r = await api(`/tripulantes/${atual}/ecg`);
  const cv = $("#ecg"), g = cv.getContext("2d"), a = r.amostras;
  const lo = Math.min(...a), hi = Math.max(...a), alt = cv.height, larg = cv.width;
  const t = d && d.tripulantes.find((x) => x.tripulante_id === atual);
  g.clearRect(0, 0, larg, alt);
  g.strokeStyle = "rgba(148,163,184,.12)"; g.lineWidth = 1;
  for (let x = 0; x < larg; x += 30) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, alt); g.stroke(); }
  g.strokeStyle = t && t.estado === "critico" ? "#ef4444" : t && t.qualidade !== "bom" ? "#f59e0b" : "#10b981"; g.lineWidth = 2; g.beginPath();
  a.forEach((v, i) => { const x = (i / (a.length - 1)) * larg, y = alt - 12 - ((v - lo) / (hi - lo || 1)) * (alt - 24); i ? g.lineTo(x, y) : g.moveTo(x, y); });
  g.stroke();
  $("#ecg-origem").textContent = `trecho de ECG · CinC 2017 (teste) ${r.origem}`;
}

criarChat($("#cosmo"), {
  superficie: "bordo", foco: () => atual,
  saudacao: "Sou a Cosmo de bordo. Pergunte sobre a tripulação, um evento, o link ou os modelos. As perguntas do cenário em curso aparecem em “Agora”.",
});
repetir(carregar, 1000);
repetir(desenharEcg, 2000);
