"""Motor de decisões: regras + máquina de estados determinística (ADR-002).

É o único componente que muda o estado de um evento. A Cosmo anexa a sugestão;
só um humano registra decisão. Prazo vencido escala para outro humano, nunca
para a IA (ADR-004). Medicação é sempre um passo separado, do oficial médico.

Cada decisão humana também vira rótulo para o próximo treino (human-in-the-loop).

O médico pode estar a bordo ou só na Terra. Na Terra, o CMO de bordo inicia só as
ações seguras pré-aprovadas; confirmar o protocolo, aprovar exame e liberar
medicação são da médica de voo, e a decisão dela só vale quando o pacote chega.
Sem sinal, na FA, o CMO pode usar a ordem permanente que ela assinou antes do voo
(ADR-017), com critérios checados aqui.
"""
import hashlib

from ..config import MEDICO_TERRA, ORDEM_PERMANENTE, REGRAS, TRIPULACAO, nome_de
from ..terra import familia
from . import cosmo, registro, trilha

TRANSICOES = {
    "detectado": {"confirmacao_astronauta", "proposto", "agendado"},
    "confirmacao_astronauta": {"encerrado", "proposto"},
    "proposto": {"aguardando_humano"},
    "aguardando_humano": {"escalonado", "decidido"},
    "escalonado": {"aguardando_humano"},
    "decidido": {"em_execucao", "encerrado"},
    "em_execucao": {"resolvido"},
    "agendado": {"aplicado", "encerrado"},
    "aplicado": {"encerrado"},
}
FINAIS = {"resolvido", "encerrado"}
AVISOS = {"linha_de_base", "ciclo", "hidratacao"}  # sugestões no relógio; não são evento clínico
PRIVADOS = {"bem_estar", "ciclo"}                   # só saem do relógio com consentimento
PIN_MEDICO = "2026"                                 # PIN de demonstração para liberar medicação
MEDICO = "marcus"                                   # médico a bordo (ou CMO, quando o médico está na Terra)
CLINICOS = {"arritmia", "dor_de_cabeca"}           # decisões que pedem um médico
MEDICAS_TERRA = {"confirmar", "recusar", "aprovar_exame", "pedir_ajuste_ar", "liberar_medicacao", "marcar_conversa"}

# ação -> (tipos de evento, estados em que vale, quem pode: "responsavel" | "medico" | "dono")
ACOES = {
    "confirmar": ({"arritmia", "tempestade_solar", "dor_de_cabeca"}, {"aguardando_humano"}, "responsavel"),
    "assumir": ({"arritmia"}, {"aguardando_humano"}, "responsavel"),
    "recusar": ({"arritmia", "tempestade_solar", "dor_de_cabeca"}, {"aguardando_humano"}, "responsavel"),
    "liberar_medicacao": ({"arritmia"}, {"em_execucao"}, "medico"),
    "ajustar_sensor": ({"sensor_suspeito"}, {"confirmacao_astronauta"}, "dono"),
    "sensor_firme": ({"sensor_suspeito"}, {"confirmacao_astronauta"}, "dono"),
    "registrar_kit": ({"sensor_suspeito"}, {"aguardando_humano"}, "responsavel"),
    "adiar": ({"tempestade_solar"}, {"aguardando_humano"}, "responsavel"),
    "liberar_abrigo": ({"tempestade_solar"}, {"em_execucao"}, "responsavel"),
    "trocar_escala": ({"prontidao_eva"}, {"aguardando_humano"}, "responsavel"),
    "manter_escala": ({"prontidao_eva"}, {"aguardando_humano"}, "responsavel"),
    "pedir_ajuste_ar": ({"dor_de_cabeca"}, {"aguardando_humano", "em_execucao"}, "medico"),
    "aprovar_exame": ({"dor_de_cabeca"}, {"aguardando_humano", "em_execucao"}, "medico"),
    "compartilhar": ({"bem_estar", "ciclo"}, {"aguardando_humano"}, "dono"),
    "manter_privado": ({"bem_estar", "ciclo"}, {"aguardando_humano"}, "dono"),
    "marcar_conversa": ({"bem_estar"}, {"em_execucao"}, "medico"),
    "confirmar_sintoma": ({"ciclo", "linha_de_base"}, {"aguardando_humano"}, "dono"),
    "falso_alarme": ({"linha_de_base", "ciclo"}, {"aguardando_humano"}, "dono"),
    "aceitar_cuidado": ({"hidratacao"}, {"aguardando_humano"}, "dono"),
    "dispensar": ({"hidratacao"}, {"aguardando_humano"}, "dono"),
    "vetar": ({"modo_noite"}, {"agendado"}, "dono"),
    "desfazer": ({"modo_noite"}, {"aplicado"}, "dono"),
    # só com o médico na Terra: o que o CMO faz a bordo sem esperar o atraso
    "iniciar_seguras": ({"arritmia", "dor_de_cabeca"}, {"aguardando_humano"}, "responsavel"),
    "aplicar_medicacao": ({"arritmia"}, {"em_execucao"}, "cmo"),
    # só com o médico na Terra e sem sinal: dose pré-autorizada antes do voo (ADR-017)
    "ordem_permanente": ({"arritmia"}, {"aguardando_humano"}, "cmo"),
}


class Recusa(Exception):
    """A regra não permite: quem pediu não é o humano responsável, ou o passo está fora de ordem."""


class Motor:
    def __init__(self, relogio, agora_iso, link):
        self.relogio, self.agora_iso, self.link = relogio, agora_iso, link
        self.eventos, self.seq = {}, 0
        self.espera = {}            # (tipo, tripulante) -> tempo até poder abrir de novo
        self.anomalo_ha = {}        # tripulante -> leituras seguidas com a floresta marcando anomalia
        self.sim = None             # ligado pelo simulador: recebe os efeitos das decisões
        self.rotular = None         # ligado pelo HITL: grava o rótulo humano

    # ---------------------------------------------------------- equipe médica
    def local(self):
        return getattr(self.sim, "medico_local", "bordo")

    def medico(self):
        return MEDICO_TERRA["id"] if self.local() == "terra" else MEDICO

    # ---------------------------------------------------------- consulta
    def abertos(self, tid=None, tipo=None):
        return [e for e in self.eventos.values() if e["estado"] not in FINAIS
                and (tid is None or e["tripulante_id"] == tid) and (tipo is None or e["tipo"] == tipo)]

    def _tem(self, tid, tipo):
        return bool(self.abertos(tid, tipo)) or self.relogio() < self.espera.get((tipo, tid), 0)

    # ---------------------------------------------------------- abrir e mudar
    def abrir(self, tipo, tid, analise=None, dados=None, ator="motor"):
        regra = REGRAS[tipo]
        self.seq += 1
        cadeia = [tid if h == "{tripulante}" else h for h in regra["cadeia"]]
        passos = trilha.Passos()
        sugestao = cosmo.sugerir(tipo, analise, passos)
        if tipo in ("arritmia", "dor_de_cabeca"):  # o paciente não decide o próprio protocolo
            cadeia = [h for h in cadeia if h != tid] or cadeia
        ev = dict(id=f"evt-{self.seq:04d}", classe="aviso" if tipo in AVISOS else "evento", tipo=tipo,
                  tripulante_id=tid, estado="detectado", nivel_autonomia=regra["nivel"],
                  responsavel_papel=regra["papel"], responsavel_id=cadeia[0], cadeia=cadeia, prazo_t=None, prazo_em=None,
                  gerado_em=self.agora_iso(), gerado_t=self.relogio(), dados=dados or {}, decisoes=[], historico=[],
                  privado=tipo in PRIVADOS, consentido=False, escalonamentos=0,
                  medico_local=self.local(), medico_id=self.medico(),
                  sugestao=sugestao)
        if ev["medico_local"] == "terra" and tipo in CLINICOS:
            ev["responsavel_papel"] = "cmo"  # a bordo, o CMO cuida das ações seguras; a decisão médica é da Terra
        self.eventos[ev["id"]] = ev
        s = ev["sugestao"]
        s["trilha"] = trilha.compacto(trilha.registrar(
            "sugestao", "bordo", ev["gerado_em"], passos,
            dict(tipo="sugeriu", resumo=f"{s['protocolo']['id']} com confiança {s['confianca']}; aguarda um humano"),
            entrada=f"{tipo} {s['versao_modelo']} " + " ".join(str(x) for x in s["evidencias"]),
            saida=f"{s['texto']} {s['alternativa']}", evento_id=ev["id"], tripulante_id=tid))
        registro.incluir("sugestoes", evento_id=ev["id"], texto=s["texto"], evidencias=s["evidencias"],
                         confianca=s["confianca"], alternativa=s["alternativa"], versao_modelo=s["versao_modelo"],
                         criada_em=ev["gerado_em"])
        registro.auditar("evento", ev["id"], None, "detectado", ator,
                         dict(tipo=tipo, tripulante=tid, nivel=regra["nivel"], versao_modelo=s["versao_modelo"],
                              evidencias=s["evidencias"]), ev["gerado_em"])
        registro.auditar("sugestao", ev["id"], None, None, "cosmo", dict(texto=s["texto"], confianca=s["confianca"]), ev["gerado_em"])
        self._gravar(ev)
        return ev

    def _mudar(self, ev, novo, ator, detalhe=None):
        if novo not in TRANSICOES.get(ev["estado"], ()):
            raise Recusa(f"transição {ev['estado']} -> {novo} não existe na máquina de estados")
        antes, ev["estado"] = ev["estado"], novo
        quando = self.agora_iso()
        ev["historico"].append(dict(de=antes, para=novo, ator=ator, quando=quando))
        registro.auditar("evento", ev["id"], antes, novo, ator, detalhe, quando)
        self._gravar(ev)
        if novo in FINAIS:
            ev["prazo_t"] = ev["prazo_em"] = None
            self.espera[(ev["tipo"], ev["tripulante_id"])] = self.relogio() + (300 if ev["classe"] == "aviso" else 20)
        self._publicar(ev)

    def _gravar(self, ev):
        registro.incluir("eventos", evento_id=ev["id"], tipo=ev["tipo"], tripulante_id=ev["tripulante_id"],
                         estado=ev["estado"], quando=self.agora_iso(), corpo=self.mensagem(ev))

    def _prazo(self, ev, segundos):
        ev["prazo_t"] = None if segundos is None else self.relogio() + segundos
        ev["prazo_em"] = None if segundos is None else self.sim.iso_em(segundos)

    def _aguardar(self, ev, ator="motor"):
        self._mudar(ev, "proposto", ator)
        self._prazo(ev, REGRAS[ev["tipo"]]["prazo_s"])
        self._mudar(ev, "aguardando_humano", ator, dict(responsavel=ev["responsavel_id"], prazo_em=ev["prazo_em"]))

    # ---------------------------------------------------------- contrato e link
    def mensagem(self, ev) -> dict:
        """Mensagem `evento.atualizado` (4-arquitetura/contratos, versão 1.1)."""
        regra, s = REGRAS[ev["tipo"]], ev["sugestao"]
        msg = dict(tipo_msg="evento.atualizado", versao_contrato="1.1",
                   evento=dict(id=ev["id"], tipo=ev["tipo"], tripulante_id=ev["tripulante_id"], estado=ev["estado"],
                               nivel_autonomia=ev["nivel_autonomia"], responsavel_papel=ev["responsavel_papel"],
                               gerado_em=ev["gerado_em"]),
                   sugestao=dict(texto=s["texto"], confianca=s["confianca"], alternativa=s["alternativa"],
                                 evidencias=[str(x) for x in s["evidencias"]], versao_modelo=s["versao_modelo"],
                                 trilha=s.get("trilha")),
                   pacote=dict(prioridade=regra["prioridade"], destinos=regra["destinos"]))
        if ev["prazo_em"]:
            msg["evento"]["prazo_em"] = ev["prazo_em"]
        msg["evento"]["medico_local"] = ev["medico_local"]
        if ev["dados"].get("seguras"):
            msg["acoes_seguras"] = dict(ev["dados"]["seguras"])
        if ev["dados"].get("medicacao"):
            msg["medicacao"] = dict(ev["dados"]["medicacao"])
        if ev["decisoes"]:
            d = ev["decisoes"][-1]
            msg["decisao"] = {k: d[k] for k in ("humano_id", "acao", "assinatura", "decidida_em")}
            if d.get("dose"):
                msg["decisao"]["dose"] = d["dose"]
        return msg

    def _publicar(self, ev):
        """Para a Terra só vai evento clínico, nos estados que importam. Aviso do
        relógio e dado privado sem consentimento não entram em pacote nenhum."""
        regra = REGRAS[ev["tipo"]]
        if ev["classe"] == "aviso" or ev["privado"] or "houston" not in regra["destinos"]:
            return
        if ev["estado"] not in ("aguardando_humano", "decidido", "em_execucao", "resolvido", "encerrado"):
            return
        nome = TRIPULACAO[ev["tripulante_id"]]["nome"]
        quem = (f"decisão da {MEDICO_TERRA['nome']}" if ev["medico_local"] == "terra" and ev["tipo"] in CLINICOS
                else ev["responsavel_papel"].replace("_", " "))
        rotulo = {"aguardando_humano": f"Alerta: {ev['tipo'].replace('_', ' ')} · {nome} · aguardando {quem}",
                  "decidido": f"Decisão a bordo: {ev['tipo'].replace('_', ' ')} · {nome}",
                  "em_execucao": f"Em execução a bordo: {ev['tipo'].replace('_', ' ')} · {nome}",
                  "resolvido": f"Resolvido a bordo: {ev['tipo'].replace('_', ' ')} · {nome}",
                  "encerrado": f"Encerrado a bordo: {ev['tipo'].replace('_', ' ')} · {nome}"}[ev["estado"]]
        frase = familia.frase_do_evento(ev["tipo"], ev["estado"], ev["tripulante_id"])
        destinos = ["houston"] + (["familia"] if frase else [])
        self.link.enviar("up", rotulo, prioridade=regra["prioridade"], destinos=destinos, carga=dict(mensagem=self.mensagem(ev)),
                         frase_familia=frase, gerado_em=self.agora_iso(), tamanho_mb=3.2 if ev["tipo"] == "arritmia" and ev["estado"] == "aguardando_humano" else 0.2)

    # ---------------------------------------------------------- regras sobre a análise
    def processar(self, a: dict, vetor: list):
        """Recebe a saída do `ia.analisar` e aplica as regras. Nada aqui é aprendido."""
        tid, m1, m2, m3 = a["tripulante_id"], a["m1"], a["m2"], a["m3"]
        m2_bom = m2 is None or m2["qualidade"] == "bom"
        fa = bool(m1 and m1.get("classe") == "fa" and m2_bom)

        # ADR-009: sinal ruim com leitura fora da faixa -> perguntar antes de alarmar.
        if not m2_bom and m3["estado"] == "suspeito" and not self._tem(tid, "sensor_suspeito"):
            ev = self.abrir("sensor_suspeito", tid, a, dict(m2_atributos=m2["_atributos"], spo2=vetor[2], motivo=m2["motivo"]))
            self._prazo(ev, REGRAS["sensor_suspeito"]["prazo_s"])
            self._mudar(ev, "confirmacao_astronauta", "motor", dict(pergunta="o relógio está folgado?", prazo_em=ev["prazo_em"]))

        # M1 com sinal bom -> evento de arritmia, nível 3, com o oficial médico.
        # Risco de vida vai ao médico sem pedir consentimento, e isso fica na auditoria.
        if fa and not self._tem(tid, "arritmia"):
            ev = self.abrir("arritmia", tid, a, dict(m1_atributos=m1["_atributos"], prob_fa=m1["prob_fa"], estaveis=0))
            registro.auditar("consentimento", ev["id"], None, None, "motor",
                             dict(excecao="risco de vida: encaminhado ao oficial médico sem consentimento"))
            self._aguardar(ev)
        for ev in self.abertos(tid, "arritmia"):
            ev["dados"]["fa_agora"] = fa
            if ev["estado"] == "em_execucao":
                critico_spo2 = m3["metricas"].get("spo2", {}).get("faixa") == "critico"
                ev["dados"]["estaveis"] = 0 if (fa or critico_spo2) else ev["dados"]["estaveis"] + 1
                if ev["dados"]["estaveis"] >= 10:
                    self._mudar(ev, "resolvido", "motor", dict(regra="10 leituras seguidas sem FA e com SpO2 fora da faixa crítica"))

        clinico = self.abertos(tid, "arritmia") or self.abertos(tid, "sensor_suspeito")
        ciclo = a.get("ciclo")
        # ADR-013: calendário + sinais leves + M2 bom -> pergunta privada, nível 2.
        if ciclo and ciclo["perguntar"] and not clinico and not self._tem(tid, "ciclo"):
            ev = self.abrir("ciclo", tid, a, dict(sinais_leves=ciclo["sinais_leves"], aviso_dias=ciclo["aviso_dias"], vetores=[vetor]))
            self._aguardar(ev)
        # ADR-012: floresta marca anomalia + M2 bom + nenhum sinal crítico -> sugestão de nível 1.
        # Se o calendário já explica o trecho, a sugestão não abre.
        # Dentro da janela do calendário ele tem a vez: a floresta espera 30 leituras.
        f = m3["isolation_forest"]
        self.anomalo_ha[tid] = self.anomalo_ha.get(tid, 0) + 1 if f["anomalo"] else 0
        espera_calendario = 30 if (ciclo and ciclo["na_janela"]) else 1
        if (f["anomalo"] and m2_bom and m3["estado"] != "critico" and not clinico and self.anomalo_ha[tid] >= espera_calendario
                and not (ciclo and ciclo["perguntar"]) and not self._tem(tid, "ciclo") and not self._tem(tid, "linha_de_base")):
            ev = self.abrir("linha_de_base", tid, a, dict(score=f["score"], limiar=f["limiar"], vetores=[vetor]))
            self._aguardar(ev)
        for ev in self.abertos(tid, "linha_de_base") + self.abertos(tid, "ciclo"):
            if len(ev["dados"]["vetores"]) < 90:
                ev["dados"]["vetores"].append(vetor)  # leituras do episódio: viram rótulo quando o humano responde
        if m3["metricas"].get("hidratacao", {}).get("faixa") == "atencao" and not clinico and not self._tem(tid, "hidratacao"):
            self._aguardar(self.abrir("hidratacao", tid, a))

    # ---------------------------------------------------------- decisão humana
    def decidir(self, evento_id, humano_id, acao, dose=None, pin=None, detalhe=None, via="bordo"):
        """`via="link"` só para a decisão da médica de voo, quando o pacote dela chega à nave."""
        ev = self.eventos.get(evento_id)
        if not ev:
            raise Recusa("evento não existe")
        terra, medico = ev["medico_local"] == "terra", ev["medico_id"]
        if humano_id not in TRIPULACAO and humano_id != medico:
            raise Recusa("decisão só de um humano identificado; a Cosmo não decide")
        if humano_id == MEDICO_TERRA["id"] and via != "link":
            raise Recusa(f"a {MEDICO_TERRA['nome']} decide pelo console de Houston, e a decisão só vale quando o pacote chega à nave")
        if acao not in ACOES:
            raise Recusa(f"ação desconhecida: {acao}")
        tipos, estados, quem = ACOES[acao]
        if ev["tipo"] not in tipos or ev["estado"] not in estados:
            raise Recusa(f"'{acao}' não vale para {ev['tipo']} em {ev['estado']}")
        if terra and acao in MEDICAS_TERRA and (ev["tipo"] in CLINICOS or acao == "marcar_conversa"):
            quem = "medico"  # sem médico a bordo, a decisão médica é da Terra
        if acao in ("iniciar_seguras", "aplicar_medicacao", "ordem_permanente") and not terra:
            raise Recusa("com médico a bordo, o próprio Dr. Marcus confirma o protocolo e aplica a medicação")
        if acao == "assumir" and terra:
            raise Recusa("sem médico a bordo, não há atendimento manual que substitua a decisão médica: "
                         "o CMO inicia as ações seguras e a decisão é da Terra")
        if acao == "iniciar_seguras" and ev["dados"].get("seguras"):
            raise Recusa("as ações seguras já foram iniciadas")
        if quem == "dono" and humano_id != ev["tripulante_id"]:
            raise Recusa("essa resposta é só da própria pessoa")
        if quem == "medico" and humano_id != medico:
            raise Recusa(f"só a {MEDICO_TERRA['nome']}, pelo console de Houston, pode fazer isso: não há médico a bordo"
                         if terra else "só o oficial médico pode fazer isso")
        if quem == "responsavel" and humano_id != ev["responsavel_id"]:
            raise Recusa(f"o humano responsável agora é {nome_de(ev['responsavel_id'])}")
        if quem == "cmo" and humano_id not in ev["cadeia"]:
            raise Recusa("quem aplica a dose a bordo é o oficial de saúde (CMO) ou quem o substitui na cadeia")
        if acao == "aplicar_medicacao":
            med = ev["dados"].get("medicacao")
            if not med:
                raise Recusa(f"a liberação da {MEDICO_TERRA['nome']} ainda não chegou a bordo")
            if med.get("aplicada"):
                raise Recusa("a dose já foi aplicada")
        if acao == "ordem_permanente":
            self._criterios_ordem(ev)
            dose = ORDEM_PERMANENTE["dose"]  # a dose é a da ordem assinada; o CMO não escolhe
        if acao == "liberar_medicacao":
            if not dose:
                raise Recusa("a dose é definida pelo oficial médico")
            if pin != PIN_MEDICO:
                raise Recusa("PIN do oficial médico inválido")
            if (ev["dados"].get("medicacao") or {}).get("via") == "ordem_permanente":
                raise Recusa(f"a dose da ordem permanente {ORDEM_PERMANENTE['id']} já foi aplicada a bordo neste evento")
            if ev["dados"].get("medicacao"):
                raise Recusa("medicação já liberada neste evento")
        quando = self.agora_iso()
        d = dict(humano_id=humano_id, acao=acao, dose=dose, decidida_em=quando, detalhe=detalhe or {}, via=via,
                 assinatura=hashlib.sha256(f"{humano_id}|{evento_id}|{acao}|{quando}|chave-do-dispositivo".encode()).hexdigest()[:24])
        ev["decisoes"].append(d)
        registro.incluir("decisoes", evento_id=evento_id, humano_id=humano_id, acao=acao, dose=dose,
                         assinatura=d["assinatura"], decidida_em=quando, detalhe=d["detalhe"])
        registro.auditar("decisao", evento_id, None, None, humano_id,
                         dict(acao=acao, dose=dose, assinatura=d["assinatura"], versao_modelo=ev["sugestao"]["versao_modelo"], via=via), quando)
        getattr(self, "_d_" + ev["tipo"])(ev, humano_id, acao, d)
        return ev

    def _criterios_ordem(self, ev):
        """Ordem permanente (ADR-017): só sem sinal, depois das ações seguras, com FA presente."""
        op = ORDEM_PERMANENTE["id"]
        if not self.link.blackout:
            raise Recusa(f"há sinal com a Terra: quem decide a medicação é a {MEDICO_TERRA['nome']}. "
                         f"A ordem permanente {op} só vale sem contato")
        if not ev["dados"].get("seguras"):
            raise Recusa(f"inicie antes as ações seguras: a ordem permanente {op} vem depois delas")
        if not ev["dados"].get("fa_agora"):
            raise Recusa(f"o M1 já não vê FA na última leitura: a ordem permanente {op} não se aplica")
        if ev["dados"].get("medicacao"):
            raise Recusa("já há medicação registrada neste evento")

    def _rotulo(self, peca, ev, rotulo, humano_id, dados):
        if self.rotular:
            self.rotular(peca=peca, tripulante_id=ev["tripulante_id"], rotulo=rotulo, humano_id=humano_id,
                         origem=f"{ev['id']}:{ev['decisoes'][-1]['acao']}", dados=dados)

    def _seguras(self, ev, h, d, texto, mb):
        """Ações seguras pré-aprovadas: o CMO inicia sem esperar a Terra. A decisão médica segue com a médica de voo."""
        ev["dados"]["seguras"] = dict(por=h, quando=d["decidida_em"], acoes=texto)
        ev["responsavel_papel"], ev["responsavel_id"] = "medico_terra", ev["medico_id"]
        ev["prazo_t"] = ev["prazo_em"] = None  # o prazo a bordo foi cumprido; agora espera a Terra, sem escalar para a IA
        registro.auditar("evento", ev["id"], ev["estado"], ev["estado"], h, dict(acao="ações seguras pré-aprovadas", acoes=texto))
        self._gravar(ev)
        self.link.enviar("up", f"Ações seguras iniciadas a bordo pelo CMO: {texto} · {TRIPULACAO[ev['tripulante_id']]['nome']}",
                         prioridade=1 if ev["tipo"] == "arritmia" else 2, destinos=["houston"], carga=dict(mensagem=self.mensagem(ev)),
                         gerado_em=d["decidida_em"], tamanho_mb=mb)

    def _d_arritmia(self, ev, h, acao, d):
        if acao == "iniciar_seguras":
            self._seguras(ev, h, d, "repouso, O₂ a 2 L/min e ECG de 12 derivações", 1.8)
            self.sim.efeito("o2", ev)
        elif acao == "aplicar_medicacao":
            ev["dados"]["medicacao"].update(aplicada=True, aplicada_por=h, aplicada_em=d["decidida_em"])
            self._gravar(ev)
            self.link.enviar("up", f"Medicação aplicada a bordo pelo CMO: dose definida pela {MEDICO_TERRA['nome']}",
                             prioridade=1, destinos=["houston"], carga=dict(mensagem=self.mensagem(ev)), gerado_em=d["decidida_em"])
        elif acao == "ordem_permanente":
            op = ORDEM_PERMANENTE
            ev["dados"]["conduta"] = f"ordem permanente {op['id']}"
            ev["dados"]["medicacao"] = dict(dose=op["dose"], liberada_por=op["assinada_por"], quando=op["assinada_em"],
                                            via="ordem_permanente", ordem=op["id"], aplicada=True, aplicada_por=h,
                                            aplicada_em=d["decidida_em"])
            self._mudar(ev, "decidido", h, dict(acao=acao, ordem=op["id"], assinada_por=op["assinada_por"], dose=op["dose"],
                                                criterios=op["criterios"]))
            self._mudar(ev, "em_execucao", h)
            # Sem rótulo para o M1: quem confirma FA é um médico, e o CMO não é. A revisão da Terra vem depois.
            self.sim.efeito("fa_tratada", ev)
            self.link.enviar("up", f"Ordem permanente {op['id']} usada a bordo pelo CMO, sem sinal: {op['dose']} · "
                                   f"{TRIPULACAO[ev['tripulante_id']]['nome']}", prioridade=1, destinos=["houston"],
                             carga=dict(mensagem=self.mensagem(ev)), gerado_em=d["decidida_em"], tamanho_mb=0.4)
        elif acao in ("confirmar", "assumir"):
            ev["dados"]["conduta"] = "protocolo da Cosmo" if acao == "confirmar" else "atendimento manual"
            self._mudar(ev, "decidido", h, dict(acao=acao))
            self._mudar(ev, "em_execucao", h)
            self._rotulo("m1", ev, "fa", h, dict(atributos=ev["dados"]["m1_atributos"]))
            self.sim.efeito("fa_tratada", ev)
        elif acao == "recusar":
            self._mudar(ev, "decidido", h, dict(acao=acao, motivo=d["detalhe"].get("motivo", "falso alarme")))
            self._mudar(ev, "encerrado", h)
            self._rotulo("m1", ev, "normal", h, dict(atributos=ev["dados"]["m1_atributos"]))
            self.sim.efeito("rotina", ev)
        elif acao == "liberar_medicacao" and ev["medico_local"] == "terra":
            ev["dados"]["medicacao"] = dict(dose=d["dose"], liberada_por=h, quando=d["decidida_em"], aplicada=False)
            self._gravar(ev)
            self.sim.avisar(ev["tripulante_id"], f"Liberação da {MEDICO_TERRA['nome']} chegou: o CMO aplica a dose")
        elif acao == "liberar_medicacao":
            ev["dados"]["medicacao"] = dict(dose=d["dose"], liberada_por=h, quando=d["decidida_em"], aplicada=True, aplicada_por=h)
            self._gravar(ev)
            self.link.enviar("up", f"Medicação liberada a bordo: antiarrítmico, dose definida por {TRIPULACAO[h]['nome']}",
                             prioridade=1, destinos=["houston"], carga=dict(mensagem=self.mensagem(ev)), gerado_em=d["decidida_em"])

    def _d_sensor_suspeito(self, ev, h, acao, d):
        if acao == "ajustar_sensor":
            ev["dados"]["desfecho"] = "artefato: a pessoa ajustou o relógio"
            self._mudar(ev, "encerrado", h, dict(acao=acao))
            self._rotulo("m2", ev, "suspeito", h, dict(atributos=ev["dados"]["m2_atributos"]))
            self.sim.efeito("rotina", ev)
        elif acao == "sensor_firme":
            self._escalar_sensor(ev, h, "a pessoa disse que o relógio está firme")
        elif acao == "registrar_kit":
            valor = float(d["detalhe"].get("spo2_kit", 97))
            ev["dados"]["spo2_kit"] = valor
            real = valor < 92
            ev["dados"]["desfecho"] = "o kit confirmou a leitura baixa" if real else "o kit desmentiu o relógio: era o sensor"
            self._mudar(ev, "decidido", h, dict(spo2_kit=valor))
            self._mudar(ev, "encerrado", h)
            self._rotulo("m2", ev, "bom" if real else "suspeito", h, dict(atributos=ev["dados"]["m2_atributos"], spo2_kit=valor))
            self.sim.efeito("rotina", ev)

    def _escalar_sensor(self, ev, ator, motivo):
        papel = "cmo" if ev["medico_local"] == "terra" else "oficial_medico"  # medir com o kit é tarefa de bordo
        ev["responsavel_papel"], ev["responsavel_id"], ev["dados"]["escalou_por"] = papel, MEDICO, motivo
        self._mudar(ev, "proposto", ator, dict(motivo=motivo))
        self._prazo(ev, 60)
        self._mudar(ev, "aguardando_humano", "motor", dict(responsavel=MEDICO, prazo_em=ev["prazo_em"]))

    def _d_tempestade_solar(self, ev, h, acao, d):
        if acao == "adiar":
            ev["dados"]["adiado"] = True
            self._prazo(ev, 8)  # o fluxo segue subindo: pergunta de novo em instantes
            registro.auditar("evento", ev["id"], ev["estado"], ev["estado"], h, dict(acao="adiar"))
        elif acao == "confirmar":
            self._mudar(ev, "decidido", h, dict(acao="abrigo para todos"))
            self._mudar(ev, "em_execucao", h)
            ev["dados"].update(fase="abrigo", cai_t=self.relogio() + 18)
            self.sim.efeito("abrigo", ev)
        elif acao == "recusar":
            self._mudar(ev, "decidido", h, dict(acao="sem abrigo"))
            self._mudar(ev, "encerrado", h)
            self.sim.efeito("fim_tempestade", ev)
        elif acao == "liberar_abrigo":
            if ev["dados"].get("fase") != "fluxo_caindo":
                raise Recusa("o fluxo ainda está alto")
            self._mudar(ev, "resolvido", h, dict(acao="tripulação liberada"))
            self.sim.efeito("fim_tempestade", ev)

    def _d_prontidao_eva(self, ev, h, acao, d):
        ev["dados"]["resultado"] = "Kenji no lugar da Elena" if acao == "trocar_escala" else "Elena mantida, com monitoramento de fadiga reforçado"
        self._mudar(ev, "decidido", h, dict(acao=acao))
        self._mudar(ev, "em_execucao", h)
        self._mudar(ev, "resolvido", "motor", dict(escala=ev["dados"]["resultado"]))

    def _d_dor_de_cabeca(self, ev, h, acao, d):
        if acao == "iniciar_seguras":
            if not ev["dados"].get("ar"):
                ev["dados"].update(ar="pedido", ar_t=self.relogio() + 6)
            self._seguras(ev, h, d, "repouso e ajuste do ar da cabine (CO₂)", 0.3)
            return
        if acao == "recusar":
            self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "encerrado", h); return
        if ev["estado"] == "aguardando_humano":
            self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "em_execucao", h)
        if acao in ("pedir_ajuste_ar", "confirmar") and not ev["dados"].get("ar"):
            ev["dados"].update(ar="pedido", ar_t=self.relogio() + 6)
        if acao in ("aprovar_exame", "confirmar") and not ev["dados"].get("exame"):
            ev["dados"].update(exame="em andamento", exame_t=self.relogio() + 9)
        self._gravar(ev)

    def _d_bem_estar(self, ev, h, acao, d):
        if acao == "compartilhar":
            self._consentir(ev, "saude_mental", h)
            terra = ev["medico_local"] == "terra"
            ev["responsavel_papel"], ev["responsavel_id"] = ("medico_terra", ev["medico_id"]) if terra else ("oficial_medico", MEDICO)
            self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "em_execucao", h)
        elif acao == "manter_privado":
            self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "encerrado", h)
        elif acao == "marcar_conversa":
            ev["dados"]["conversa"] = d["detalhe"].get("hora", "19:00")
            self._mudar(ev, "resolvido", h, dict(conversa=ev["dados"]["conversa"]))
            if ev["medico_local"] == "terra":
                self.sim.avisar(ev["tripulante_id"], f"{MEDICO_TERRA['nome']} marcou uma conversa privada às {ev['dados']['conversa']}")

    def _consentir(self, ev, tipo_dado, h):
        """O dado vai só para o médico, onde ele estiver. Com o médico na Terra, só para a
        médica de voo: o CMO, o resto de Houston e a família não veem."""
        ev["consentido"] = True
        dest = "medico_terra" if ev["medico_local"] == "terra" else "oficial_medico"
        registro.incluir("consentimentos", tripulante_id=ev["tripulante_id"], tipo_dado=tipo_dado,
                         destinatario=dest, acao="concedido", quando=self.agora_iso())
        registro.auditar("consentimento", ev["id"], None, "concedido", h, dict(tipo_dado=tipo_dado, destinatario=dest))
        if dest == "medico_terra":
            self._para_medica(ev, tipo_dado)

    def _para_medica(self, ev, tipo_dado):
        nome = TRIPULACAO[ev["tripulante_id"]]["nome"]
        resumo = dict(saude_mental=f"{nome} autorizou ver este resumo, sem gravações: {ev['dados'].get('padrao', '')}.",
                      ciclo=f"{nome} pode ter cólica, inchaço ou humor mais baixo neste trecho do ciclo e pediu cuidado leve. Não é diagnóstico.",
                      linha_de_base=f"{nome} respondeu que não está bem: combinação de sinais fora do padrão dela(e), sem sinal crítico.")[tipo_dado]
        self.link.enviar("up", f"Compartilhado com consentimento · só para a {MEDICO_TERRA['nome']}", prioridade=3,
                         destinos=["medico_terra"], gerado_em=self.agora_iso(), tamanho_mb=0.02,
                         carga=dict(privado=dict(evento_id=ev["id"], tipo=ev["tipo"], tipo_dado=tipo_dado, tripulante_id=ev["tripulante_id"],
                                                 nome=nome, resumo=resumo, gerado_em=self.agora_iso())))

    def _d_ciclo(self, ev, h, acao, d):
        if acao == "confirmar_sintoma":       # "estou sentindo": abre o cuidado leve, ainda privado
            ev["dados"]["sintoma"] = True
            registro.auditar("evento", ev["id"], ev["estado"], ev["estado"], h, dict(acao=acao))
            return
        if acao == "falso_alarme":            # "estou bem"
            ev["dados"]["sintoma"] = False
        if acao == "compartilhar":
            self._consentir(ev, "ciclo", h)
        self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "encerrado", h)

    def _d_linha_de_base(self, ev, h, acao, d):
        confirmou = acao == "confirmar_sintoma"
        terra = ev["medico_local"] == "terra"
        ev["dados"]["resposta"] = (("não está bem: informado ao CMO e à " + MEDICO_TERRA["nome"]) if terra else
                                   "não está bem: informado ao oficial médico") if confirmou else "é o padrão dela(e) hoje"
        ev["consentido"] = confirmou
        if confirmou and terra:
            self._para_medica(ev, "linha_de_base")
        self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "encerrado", h)
        self._rotulo("m3-if", ev, "anomalia" if confirmou else "normal", h, dict(vetores=ev["dados"]["vetores"]))

    def _d_hidratacao(self, ev, h, acao, d):
        self._mudar(ev, "decidido", h, dict(acao=acao)); self._mudar(ev, "encerrado", h)
        if acao == "aceitar_cuidado":
            self.sim.efeito("beber", ev)

    def _d_modo_noite(self, ev, h, acao, d):
        ev["dados"]["desfecho"] = "vetado" if acao == "vetar" else "desfeito"
        self._mudar(ev, "encerrado", h, dict(acao=acao))
        self.sim.efeito("luz_normal", ev)

    # ---------------------------------------------------------- relógio do motor
    def tick(self):
        t = self.relogio()
        for ev in list(self.abertos()):
            dados, venceu = ev["dados"], ev["prazo_t"] is not None and t >= ev["prazo_t"]
            if ev["tipo"] == "sensor_suspeito" and ev["estado"] == "confirmacao_astronauta" and venceu:
                self._escalar_sensor(ev, "motor", "20 s sem resposta da pessoa")
            elif ev["tipo"] == "modo_noite" and ev["estado"] == "agendado" and venceu:
                self._prazo(ev, 14)
                self._mudar(ev, "aplicado", "motor", dict(regra="15 s sem veto", desfazer=True))
                self.sim.efeito("luz_noite", ev)
            elif ev["tipo"] == "modo_noite" and ev["estado"] == "aplicado" and venceu:
                dados["desfecho"] = "mantido"
                self._mudar(ev, "encerrado", "motor", dict(regra="mantido sem desfazer"))
            elif ev["tipo"] == "tempestade_solar" and ev["estado"] == "aguardando_humano" and venceu and dados.get("adiado"):
                dados["adiado"] = False
                self._prazo(ev, REGRAS["tempestade_solar"]["prazo_s"])
                registro.auditar("evento", ev["id"], ev["estado"], ev["estado"], "motor", dict(regra="fluxo ainda subindo: pergunta de novo"))
            elif ev["estado"] == "aguardando_humano" and venceu:
                self._escalar(ev)
            if ev["tipo"] == "tempestade_solar" and dados.get("fase") == "abrigo" and t >= dados["cai_t"]:
                dados["fase"] = "fluxo_caindo"
                self.sim.efeito("fluxo_caindo", ev)
            if ev["tipo"] == "dor_de_cabeca" and ev["estado"] in ("aguardando_humano", "em_execucao"):
                if dados.get("ar") == "pedido" and t >= dados["ar_t"]:
                    dados["ar"] = "feito"; self.sim.efeito("ar_ajustado", ev)
            if ev["tipo"] == "dor_de_cabeca" and ev["estado"] == "em_execucao":
                if dados.get("exame") == "em andamento" and t >= dados["exame_t"]:
                    dados["exame"] = "feito"
                    self.link.enviar("up", "Ultrassom ocular guiado: imagens para laudo", prioridade=2, destinos=["houston"],
                                     gerado_em=self.agora_iso(), tamanho_mb=6.5)
                if dados.get("ar") == "feito" and dados.get("exame") == "feito":
                    self._mudar(ev, "resolvido", "motor", dict(regra="ar ajustado e exame concluído"))

    def _escalar(self, ev):
        """Prazo vencido: passa para o próximo humano da cadeia. Nunca para a IA."""
        i = ev["cadeia"].index(ev["responsavel_id"]) if ev["responsavel_id"] in ev["cadeia"] else -1
        if i + 1 >= len(ev["cadeia"]):
            ev["prazo_t"] = ev["prazo_em"] = None  # fim da cadeia: segue aguardando um humano
            return
        anterior, proximo = ev["responsavel_id"], ev["cadeia"][i + 1]
        self._mudar(ev, "escalonado", "motor", dict(de=anterior, para=proximo, motivo="prazo vencido sem resposta"))
        ev["responsavel_id"], ev["escalonamentos"] = proximo, ev["escalonamentos"] + 1
        self._prazo(ev, REGRAS[ev["tipo"]]["prazo_s"])
        self._mudar(ev, "aguardando_humano", "motor", dict(responsavel=proximo, prazo_em=ev["prazo_em"]))

    # ---------------------------------------------------------- eventos injetados (sem modelo)
    def abrir_manual(self, tipo, tid, dados=None):
        if self.abertos(tid, tipo):
            return self.abertos(tid, tipo)[0]
        ev = self.abrir(tipo, tid, None, dados)
        if tipo == "modo_noite":            # nível 4: agenda sozinho, com 15 s para vetar
            self._prazo(ev, REGRAS[tipo]["prazo_s"])
            self._mudar(ev, "agendado", "motor", dict(acao="modo noite", veto_ate=ev["prazo_em"]))
        else:
            if tipo == "tempestade_solar":  # nível 4 reversível: a rota até o abrigo já acende
                ev["dados"].update(rota_acesa=True, fase="fluxo_subindo")
                registro.auditar("evento", ev["id"], "detectado", "detectado", "motor",
                                 dict(nivel=4, acao_automatica="rota até o abrigo acesa", reversivel=True))
            self._aguardar(ev)
        return ev
