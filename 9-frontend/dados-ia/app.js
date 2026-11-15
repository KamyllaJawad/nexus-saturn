import { TRIPULACAO, ajustarEquipe, api, erro, esc, hora, ligarAcoes, nome, num, pintar, repetir } from "../compartilhado/api.js";

const $ = (s) => document.querySelector(s);
let p = null;
let quem = "sarah";
let ocupado = null;
let ultimo = null;  // resultado do último retreino
// Quem aprova é o médico da missão: o Dr. Marcus a bordo ou, sem médico a bordo, a Dra. Rivera.
const medico = () => (p && p.equipe ? p.equipe.medico_id : "marcus");

ligarAcoes({
  quem: (id) => { quem = id; return vivo(); },
  retreinar: async (peca) => {
    ocupado = peca; desenhar();
    try { ultimo = await api("/ia/retreinar", { peca, humano_id: medico() }); } finally { ocupado = null; }
    return carregar();
  },
  aprovar: (peca) => api(`/ia/modelos/${peca}/aprovar`, { peca, humano_id: medico() }).then(carregar),
  rejeitar: (peca) => api(`/ia/modelos/${peca}/rejeitar`, { peca, humano_id: medico() }).then(carregar),
  aprovar_outro: (peca) => api(`/ia/modelos/${peca}/aprovar`, { peca, humano_id: medico() === "marcus" ? "kenji" : "marcus" }).then(carregar),
}, erro);

async function carregar() { p = await api("/ia/painel"); ajustarEquipe(p.equipe); desenhar(); }

async function vivo() {
  const [a, aud, m] = await Promise.all([api(`/ia/analise/${quem}`), api("/auditoria?limite=14"), api("/missao")]);
  $("#onde").innerHTML = `Hora da nave ${hora(m.hora_nave, true)}`;
  pintar($("#quem"), TRIPULACAO.map((t) => `<button class="chip-btn" data-acao="quem" data-arg="${t.id}" aria-pressed="${t.id === quem}">${t.nome}</button>`).join(""));
  $("#analise").textContent = JSON.stringify(a, null, 1);
  const c = aud.cadeia;
  pintar($("#auditoria"), `<p class="${c.integra ? "c-ok" : "c-crit"}">${c.integra ? `Cadeia íntegra: ${c.registros} registros, último hash ${esc((c.ultimo_hash || "").slice(0, 16))}…` : `Cadeia quebrada no registro ${c.quebrou_em}`}</p>
    <p class="nota">Só inclusão. Cada registro guarda o hash do anterior; alterar um deles quebra os seguintes.</p>
    <table class="t"><tr><th>#</th><th>quando</th><th>ator</th><th>o quê</th><th>hash</th></tr>${aud.registros.map((r) => `<tr><td class="n">${r.seq}</td><td>${hora(r.quando, true)}</td>
      <td><b class="${["motor", "cosmo", "apresentador"].includes(r.ator) ? "" : "c-acc"}">${esc(r.ator)}</b></td>
      <td>${esc(r.entidade)} ${esc(r.entidade_id)}${r.para_estado ? ` → ${esc(r.para_estado)}` : ""}</td><td class="mono">${esc(r.hash.slice(0, 8))}</td></tr>`).join("")}</table>
    <p class="nota">Atores em destaque são humanos. "motor" é regra determinística; "cosmo" só aparece em sugestão.</p>`);
}

const meta = (ok) => `<span class="chip ${ok ? "ok" : "warn"}">${ok ? "meta batida" : "meta não batida"}</span>`;
const matriz = (m) => `<table class="t"><tr><th>verdade \\ previsto</th>${m.rotulos.map((r) => `<th>${r}</th>`).join("")}</tr>${m.valores.map((l, i) => `<tr><td>${m.rotulos[i]}</td>${l.map((v, j) => `<td class="n ${i === j ? "c-ok" : ""}">${v}</td>`).join("")}</tr>`).join("")}</table>`;

function desenhar() {
  if (!p) return;
  const e = p.lote.ecg, z = p.zonas, r = p.relatorio;
  const li = (itens) => itens.map((i) => `<li><span class="mono">${esc(i.nome)}</span> · ${num(i.linhas)} ${i.origem ? `· origem ${esc(i.origem)}` : ""}</li>`).join("");
  pintar($("#trilho"), `<div class="trilho">
    <div class="zona bronze"><h4>Bronze · cru, só inclusão</h4><ul>${li(z.bronze)}</ul></div>
    <div class="zona prata"><h4>Prata · tratado</h4><ul>${li(z.prata)}</ul><p class="nota">Unidade e faixa física, picos R, atributos e split ${e.split.treino}/${e.split.validacao}/${e.split.teste} por gravação. ${p.lote.vitais.suspeitas} leituras ficaram como suspeitas.</p></div>
    <div class="zona ouro"><h4>Ouro · uma tabela por modelo</h4><ul>${li(z.ouro)}</ul><p class="nota">Amostra suspeita, FA e relógio folgado não treinam a floresta. Ciclo e sintoma não entram em atributo.</p></div>
    <div class="zona art"><h4>Artefatos · sobem para a nave</h4><ul>${Object.entries(p.versoes.ativos).map(([k, v]) => `<li><span class="mono">${esc(v)}</span></li>`).join("")}</ul><p class="nota">Lote ${esc(p.lote.id)}. Treino em lote; a leitura de 1 Hz não atualiza peso nenhum.</p></div></div>
    <p class="nota" style="margin-top:8px">ECG: ${e.origem === "cinc" ? `PhysioNet/CinC 2017, ${num(e.gravacoes)} gravações reais (${Object.entries(e.classes).map(([k, v]) => `${k} ${num(v)}`).join(", ")})` : "sintético (o zip do CinC não estava disponível)"}. Sinais vitais da tripulação: sintéticos, declarados. Para o simulador foram separadas ${e.banco_simulador.normal + e.banco_simulador.fa} gravações do conjunto de teste, que nenhum modelo viu no treino; ele toca só aquelas em que os modelos em serviço acertam.</p>`);
  const m1 = r.m1.metricas, m2 = r.m2.metricas, m3 = r["m3-if"].metricas;
  pintar($("#modelos"), `
    <div class="dec"><h4>M1 · ${esc(p.versoes.ativos.m1)} ${meta(m1.bateu_meta)}</h4><p>${esc(r.m1.algoritmo)} sobre ${Object.keys(m1.importancias).length} atributos de RR.</p>
      <div class="kv"><div><span>F1 da FA no teste</span><b>${num(m1.f1_fa, 3)}</b></div><div><span>IC 95%</span><b>${m1.f1_fa_ic95.map((x) => num(x, 2)).join(" a ")}</b></div>
      <div><span>F1 na validação</span><b>${num(m1.f1_fa_validacao, 3)}</b></div><div><span>Recall / precisão</span><b>${num(m1.recall_fa, 2)} / ${num(m1.precisao_fa, 2)}</b></div></div>
      ${matriz(m1.matriz_confusao)}<p class="meta">Meta: ${esc(m1.meta)}. O número é o que saiu; o limiar (${m1.limiar_fa}) foi escolhido na validação, nunca no teste. Mais pesam: ${Object.keys(m1.importancias).slice(0, 3).join(", ")}.</p></div>
    <div class="dec"><h4>M2 · ${esc(p.versoes.ativos.m2)} ${meta(m2.bateu_meta)}</h4><p>Estimador escolhido por medição: ${esc(m2.estimador_escolhido.replace("_", " "))} (precisão na validação: ${Object.entries(m2.comparacao).map(([k, v]) => `${k.replace("_", " ")} ${num(v.precisao_validacao, 2)}`).join(" · ")}).</p>
      <div class="kv"><div><span>Recall de suspeito</span><b>${num(m2.recall_suspeito, 3)}</b></div><div><span>Precisão</span><b>${num(m2.precisao_suspeito, 3)}</b></div>
      <div><span>Bom marcado suspeito</span><b>${num(m2.falso_suspeito_em_bom * 100, 1)}%</b></div><div><span>Limiar</span><b>${m2.limiar}</b></div></div>
      ${matriz(m2.matriz_confusao)}<p class="meta">Meta: ${esc(m2.meta)}. Preferimos perguntar demais a alarmar errado.</p></div>
    <div class="dec"><h4>M3 floresta · ${esc(p.versoes.ativos["m3-if"])} ${meta(m3.bateu_meta)}</h4><p>${esc(r["m3-if"].algoritmo)}.</p>
      <table class="t"><tr><th>pessoa</th><th>limiar</th><th>alarmes/dia</th><th>recall 2 / 3 / 4 sinais</th></tr>${Object.entries(m3.por_tripulante).map(([t, v]) => `<tr><td>${nome(t)}</td><td class="n">${num(v.limiar, 3)}</td><td class="n">${num(v.alarmes_fora_da_amostra_por_dia, 2)}</td><td class="n">${num(v.recall_desvio_em_2_sinais, 2)} / ${num(v.recall_desvio_em_3_sinais, 2)} / ${num(v.recall_desvio_em_4_sinais, 2)}</td></tr>`).join("")}</table>
      <p class="meta">Meta: ${esc(m3.meta)}. ${esc(m3.limitacao)} Episódios excluídos do treino acima do limiar: ${m3.episodios_excluidos.acima_do_limiar} de ${m3.episodios_excluidos.total}.</p></div>
    <div class="dec"><h4>M3 z · ${esc(p.versoes.ativos["m3-z"])} e calendário do ciclo</h4><p>Mediana e MAD de cada tripulante, por sinal: pinta o estado de três níveis. O calendário conta dias da ficha de solo; é regra, não modelo treinado.</p>
      <p class="meta">A Cosmo é busca local nos protocolos e não aprende com as leituras. O motor, o hash e a fila também não aprendem.</p></div>`);

  const passos = Object.entries(p.pecas).map(([peca, rot]) => {
    const rt = p.rotulos[peca], cand = p.candidatos[peca], sb = p.sombra[peca], at = p.ativos[peca];
    const daTerra = (p.decisoes_modelo || []).filter((x) => x.peca === peca);
    const caminho = daTerra.find((x) => x.estado === "a caminho");
    const resumo = (x) => peca === "m1" ? `F1 FA ${num(x.f1_fa, 3)} · recall ${num(x.recall_fa, 2)} · precisão ${num(x.precisao_fa, 2)} · ${x.rotulos_humanos} rótulo(s) humano(s)`
      : peca === "m2" ? `recall suspeito ${num(x.recall_suspeito, 3)} · precisão ${num(x.precisao_suspeito, 3)} · ${x.rotulos_humanos} rótulo(s) humano(s)`
      : Object.entries(x.por_tripulante).map(([t, v]) => `${nome(t)}: limiar ${num(v.limiar, 3)}, recall 3 sinais ${num(v.recall_desvio_em_3_sinais, 2)}${v.rotulos_humanos.normal + v.rotulos_humanos.anomalia ? `, ${v.rotulos_humanos.normal + v.rotulos_humanos.anomalia} leituras rotuladas` : ""}`).join(" · ");
    return `<div class="dec"><h4>${esc(rot)} <span class="chip">em serviço: ${esc(at.versao)}</span>${cand ? `<span class="chip warn">em sombra: ${esc(cand.versao)}</span>` : ""}</h4>
      <div class="passo"><span class="n">1</span><div><b>Rótulos humanos: ${rt.total}</b> ${Object.entries(rt.por_rotulo).map(([k, v]) => `<span class="chip">${k}: ${v}</span>`).join(" ")}
        <p class="nota">${rt.ultimos.length ? rt.ultimos.map((u) => `${hora(u.criado_em, true)} · ${esc(nome(u.humano_id))} rotulou "${esc(u.rotulo)}" (${esc(u.origem)}, sobre ${esc(u.versao_modelo)})`).join("<br>") : { m1: "Nasce quando o médico confirma ou recusa um alerta de arritmia.", m2: "Nasce quando a pessoa ajusta o relógio ou o kit confirma a leitura.", "m3-if": "Nasce quando a pessoa responde ao aviso de combinação fora do padrão." }[peca]}</p></div></div>
      <div class="passo"><span class="n">2</span><div><button class="btn sm primary" data-acao="retreinar" data-arg="${peca}"${!rt.total || ocupado ? " disabled" : ""}>${ocupado === peca ? "Treinando…" : "Retreinar com os rótulos humanos"}</button>
        <p class="nota">Ouro + rótulos de bordo → candidato com versão nova. Ele não entra em serviço.</p></div></div>
      <div class="passo"><span class="n">3</span><div><b>Modo sombra</b>${cand ? `<p class="nota">Em serviço · ${esc(resumo(at))}</p><p class="nota c-acc">Candidato ${esc(cand.versao)} · ${esc(resumo(cand))}</p>
        <p class="nota">${sb ? `${sb.leituras} leituras comparadas: ${sb.concordam} iguais, <b class="${sb.divergem ? "c-warn" : ""}">${sb.divergem} divergentes</b>.${sb.exemplos.length ? " Ex.: " + sb.exemplos.slice(-3).map((x) => `${nome(x.tripulante_id)} ${hora(x.quando, true)} (serviço: ${x.ativo}, candidato: ${x.candidato})`).join("; ") : ""}` : "Aguardando leituras."}</p>` : '<p class="nota">Nenhum candidato. O candidato roda em cada leitura, sem agir, e é comparado com o modelo em serviço.</p>'}</div></div>
      <div class="passo" style="border:0"><span class="n">4</span><div><b>Aprovação do médico da missão</b>${p.equipe.local === "terra" ? `<p class="nota">Sem médico a bordo, quem aprova é a médica de voo, em Houston. A decisão dela viaja pelo link como P4 e só vale quando chega, para a versão que ela viu (ADR-017).</p>` : ""}
        ${daTerra.slice(0, 3).map((x) => `<p class="nota">Decisão da ${esc(nome("rivera"))} às ${hora(x.enviada_em, true)}: <b>${esc(x.rotulo)}</b> · ${x.estado === "aplicada" ? `<span class="c-ok">chegou às ${hora(x.chegou_em, true)} e foi aplicada</span>` : x.estado === "não aplicada" ? `<span class="c-warn">chegou, mas não se aplicou: ${esc(x.motivo)}</span>` : x.pacote_estado === "fila" ? '<span class="c-warn">na fila: sem sinal</span>' : `a caminho · chega a bordo em ${x.falta_s} s`}</p>`).join("")}
        <div class="acoes"><button class="btn sm primary" data-acao="aprovar" data-arg="${peca}"${cand && !caminho ? "" : " disabled"}>Aprovar como ${esc(p.equipe.medico_nome)}</button>
        <button class="btn sm ghost" data-acao="rejeitar" data-arg="${peca}"${cand && !caminho ? "" : " disabled"}>Rejeitar</button>
        <button class="btn sm ghost" data-acao="aprovar_outro" data-arg="${peca}"${cand ? "" : " disabled"}>Tentar aprovar como ${esc(nome(medico() === "marcus" ? "kenji" : "marcus"))}</button></div></div></div></div>`;
  }).join("");
  pintar($("#hitl"), `<p class="nota" style="margin-bottom:8px">A decisão clínica fica com o humano, e o aprendizado também: o modelo só muda depois que um humano rotula, pede o retreino e o médico da missão aprova (ADR-010).</p>
    ${passos}
    <p class="eyebrow" style="margin-top:12px">Histórico de versões</p>
    <table class="t"><tr><th>versão</th><th>estado</th><th>lote</th><th>treinado</th><th>quem</th></tr>${p.historico.map((h) => `<tr><td class="mono">${esc(h.versao)}</td><td><span class="chip ${h.estado === "ativo" ? "ok" : h.estado === "sombra" ? "warn" : ""}">${esc(h.estado)}</span></td><td class="mono">${esc(h.lote)}</td><td>${esc((h.treinado_em || "").replace("T", " ").replace("Z", ""))}</td><td>${esc(h.decidido_por ? `decidido por ${nome(h.decidido_por)}` : h.pedido_por ? `pedido por ${nome(h.pedido_por)}` : h.aprovado_por || "")}</td></tr>`).join("")}</table>`);
}

repetir(carregar, 2500);
repetir(vivo, 1500);
