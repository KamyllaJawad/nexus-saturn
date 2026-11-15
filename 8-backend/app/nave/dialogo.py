"""Chat da Cosmo: perguntas sugeridas por cenário e respostas montadas só com a
`visao` que a superfície de quem pergunta pode ver.

A Cosmo de bordo vê o agora; a Cosmo Terra (Houston) só vê o que já atravessou o
link. O que não está na visão não entra na resposta: é assim que dado privado
sem consentimento e evento que ainda está viajando ficam de fora.

Nada aqui muda estado. Não há import do módulo de decisões nem do simulador.
"""
import unicodedata

from ..config import MEDICO_TERRA, ORDEM_PERMANENTE, nome_de
from . import cosmo, trilha

FINAIS = {"resolvido", "encerrado"}
TIPO = dict(arritmia="arritmia", sensor_suspeito="leitura suspeita", tempestade_solar="tempestade solar",
            prontidao_eva="prontidão para a EVA", dor_de_cabeca="dor de cabeça", bem_estar="bem-estar",
            modo_noite="modo noite", ciclo="calendário do ciclo", linha_de_base="combinação fora do padrão",
            hidratacao="hidratação")
ESTADO = dict(detectado="detectado", confirmacao_astronauta="confirmando com a pessoa", proposto="proposto",
              aguardando_humano="aguardando humano", escalonado="escalonado", decidido="decidido",
              em_execucao="em execução", resolvido="resolvido", encerrado="encerrado",
              agendado="agendado, com veto", aplicado="aplicado, pode desfazer")
PAPEL = dict(astronauta="a própria pessoa", oficial_medico="oficial médico", comandante="comandante",
             cmo="oficial de saúde (CMO)", medico_terra=f"{MEDICO_TERRA['nome']}, em Houston")
RIVERA = MEDICO_TERRA["nome"]
ACAO = dict(confirmar="confirmou", assumir="assumiu manualmente", recusar="recusou", liberar_medicacao="liberou a medicação",
            ajustar_sensor="ajustou o relógio", sensor_firme="disse que o relógio está firme", registrar_kit="registrou a medição do kit",
            adiar="pediu para aguardar", liberar_abrigo="liberou a tripulação do abrigo", trocar_escala="trocou a escala",
            manter_escala="manteve a escala", pedir_ajuste_ar="pediu o ajuste do ar", aprovar_exame="aprovou o exame",
            compartilhar="compartilhou", manter_privado="manteve privado", marcar_conversa="marcou uma conversa",
            vetar="vetou", desfazer="desfez", iniciar_seguras="iniciou as ações seguras pré-aprovadas",
            aplicar_medicacao="aplicou a dose prescrita", ordem_permanente="aplicou a dose da ordem permanente")
OP = ORDEM_PERMANENTE


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().replace("₂", "2"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _nome(tid):
    return nome_de(tid)


def _terra(v):
    """Sem médico a bordo: a decisão médica é da médica de voo, em Houston."""
    return v.get("equipe", {}).get("local") == "terra"


def _medico(v):
    return v.get("equipe", {}).get("medico_nome") or "o oficial médico"


def _ida_volta(v):
    l = v["link"]
    ida = l["atraso_demo_s"]
    return (f"ida {l['atraso_txt']}, ida e volta pelo menos o dobro" + (f" (na demo, {_n(2 * ida, 0)} s)" if l["comprimido"] else ""))


def _hora(iso):
    return iso[11:19] if iso else "—"


def _n(v, casas=0):
    return f"{v:.{casas}f}".replace(".", ",")


def _foco(v):
    return next((t for t in v["tripulantes"] if t["tripulante_id"] == v["foco"]), v["tripulantes"][0] if v["tripulantes"] else None)


def _abertos(v, tipo=None):
    return [e for e in v["eventos"] if e["estado"] not in FINAIS and (tipo is None or e["tipo"] == tipo)]


def _ev(v, tipo):
    """O evento desse tipo mais relevante: o aberto, senão o mais recente."""
    todos = [e for e in v["eventos"] if e["tipo"] == tipo]
    return next((e for e in todos if e["estado"] not in FINAIS), todos[0] if todos else None)


def _houston(v):
    return v["superficie"] == "houston"


def _quando(v):
    """Em Houston toda resposta carrega de quando é o dado (ADR-006)."""
    if not _houston(v):
        return ""
    if v["link"]["blackout"]:
        return f" Estamos sem sinal: isto é o último dado recebido, de {_hora(v.get('dado_de'))}."
    return f" Isto é o que chegou à Terra: dado gerado a bordo às {_hora(v.get('dado_de'))}, com {v['link']['atraso_txt']} de atraso."


def _fora(t):
    return [f"{cosmo.NOME_SINAL.get(k, k)} (z {_n(m['z'], 1)}, {'crítico' if m['faixa'] == 'critico' else 'atenção'})"
            for k, m in t["metricas"].items() if m["faixa"] != "padrao"]


def _linha_evento(e):
    resp = e.get("responsavel_nome") or PAPEL.get(e.get("responsavel_papel"), "")
    prazo = f", restam {e['prazo_restante_s']} s" if e.get("prazo_restante_s") is not None and e["estado"] not in FINAIS else ""
    dec = ""
    if e.get("decisoes"):
        d = e["decisoes"][-1]
        dec = f"; {_nome(d['humano_id'])} {ACAO.get(d['acao'], d['acao'])} às {_hora(d['decidida_em'])}"
    return f"{TIPO.get(e['tipo'], e['tipo'])} · {e['nome']}: {ESTADO.get(e['estado'], e['estado'])}, decisão com {resp}{prazo}{dec}"


# ====================================================================== respostas
def r_agir(v, q):
    extra = (f" Sem médico a bordo, a decisão é sua, {RIVERA}: use os botões do console. Ela sai assinada por você e só vale quando chega à nave."
             if _houston(v) and _terra(v) else " Em Houston, parecer é revisão, não comando." if _houston(v) else "")
    return ("Eu não tenho como fazer isso. Não existe nenhuma rota minha que mude o estado de um evento: só um humano "
            "identificado decide, pelo painel ou pelo relógio, e a decisão fica assinada na auditoria. Posso explicar a "
            "sugestão, as evidências e o protocolo." + extra), None


def _medicacao_terra(v, e):
    regra = (f"Sem médico a bordo, medicação é passo separado da {RIVERA}: ela define a dose e assina com PIN no console de Houston, "
             f"a liberação viaja pelo link ({v['link']['atraso_txt']}) e o CMO aplica a bordo. Sem sinal, a liberação fica bloqueada e vale só a "
             f"ordem permanente {OP['id']}, assinada antes do voo. Eu não sugiro dose.")
    if _houston(v):
        minhas = [d for d in v.get("decisoes_terra", []) if e and d["evento_id"] == e["id"]]
        lib = next((d for d in minhas if d["acao"] == "liberar_medicacao"), None)
        conf = next((d for d in minhas if d["acao"] == "confirmar"), None)
        if not e:
            return "Nenhum alerta de arritmia chegou. " + regra + _quando(v)
        if (e.get("medicacao") or {}).get("via") == "ordem_permanente":
            return r_ordem(v, "")[0]
        if lib:
            onde = (f"chegou a bordo às {_hora(lib['chegou_em'])}" if lib["estado"] == "aplicada" else
                    f"não foi aplicada: {lib['motivo']}" if lib["estado"] == "não aplicada" else
                    "está na fila, sem sinal" if lib["pacote_estado"] == "fila" else f"chega a bordo em {lib['falta_s']} s")
            aplic = " O CMO já registrou a aplicação." if (e.get("dados", {}).get("medicacao") or {}).get("aplicada") else ""
            return f"Você liberou às {_hora(lib['enviada_em'])} ({lib['dose']}); a liberação {onde}.{aplic}" + _quando(v)
        if conf or e["estado"] == "em_execucao":
            return (f"Pode: o protocolo de {e['nome']} já foi confirmado por você. Defina a dose, assine com o PIN e envie; "
                    f"chega a bordo em {v['link']['atraso_txt']} e o CMO aplica. Estoque simulado: antiarrítmico para 2 tratamentos." + _quando(v))
        return f"Ainda não: confirme o protocolo de {e['nome']} primeiro. " + regra + _quando(v)
    if not e or e["estado"] in FINAIS:
        return "Não há evento de arritmia aberto. " + regra
    med = e["dados"].get("medicacao")
    if med and med.get("aplicada") and med.get("via") == "ordem_permanente":
        return (f"Já aplicada em {e['nome']} pela ordem permanente {OP['id']}, sem sinal: {med['dose']}, aplicada por "
                f"{_nome(med.get('aplicada_por'))} às {_hora(med.get('aplicada_em'))}. O registro sobe como P1 quando o sinal voltar.")
    if med and med.get("aplicada"):
        return f"Já aplicada em {e['nome']}: {med['dose']}, liberada pela {RIVERA} e aplicada por {_nome(med.get('aplicada_por'))} às {_hora(med.get('aplicada_em'))}."
    if med:
        return (f"A liberação da {RIVERA} chegou às {_hora(med['quando'])}: {med['dose']}. Falta o CMO aplicar e registrar no painel. "
                "Eu não aplico nem mudo a dose.")
    if v["link"]["blackout"]:
        return (f"Não por liberação da Terra: sem sinal, a decisão da {RIVERA} fica bloqueada até o contato voltar ({v['link']['volta_em']}). "
                f"Vale só a ordem permanente {OP['id']}, assinada por ela antes do voo: {OP['dose']}. " + _op_status(v, e))
    return (f"Não daqui. {regra} Situação de {e['nome']}: {ESTADO.get(e['estado'])}" +
            (", protocolo confirmado pela Terra." if e["estado"] == "em_execucao" else ", aguardando a decisão da Terra."))


def _op_status(v, e):
    """Bordo: por que a ordem permanente vale ou não agora, para este evento."""
    if not e or e["estado"] in FINAIS:
        return "Não há evento de arritmia aberto."
    med = (e.get("dados") or {}).get("medicacao")
    if med and med.get("aplicada"):
        return f"Neste evento a dose já foi aplicada ({med['dose']})."
    if e["estado"] != "aguardando_humano":
        return "A conduta deste evento já chegou da Terra: a ordem permanente não se aplica."
    falta = []
    if not v["link"]["blackout"]:
        falta.append(f"há sinal com a Terra, então quem decide é a {RIVERA}")
    if not (e.get("dados") or {}).get("seguras"):
        falta.append("as ações seguras ainda não foram iniciadas")
    if (e.get("dados") or {}).get("fa_agora") is False:
        falta.append("o M1 já não vê FA na última leitura")
    if falta:
        return "Agora não vale: " + "; ".join(falta) + "."
    return (f"Os critérios estão cumpridos para {e['nome']}: o CMO pode aplicar pelo painel, com a dose fixa da ordem. "
            "O uso fica assinado e sobe como P1.")


def _op_regra():
    return (f"A ordem permanente {OP['id']} foi assinada pela {RIVERA} em {OP['assinada_em']}, antes do voo: {OP['dose']}. "
            f"Critérios, todos juntos: {'; '.join(OP['criterios'])}. A dose não muda e eu não aplico nada. {OP['depois']}")


def r_ordem(v, q):
    if not _terra(v):
        return ("Com o médico a bordo não há ordem permanente em uso: o Dr. Marcus decide a medicação na hora. "
                "Ela existe para missões sem médico a bordo e sem sinal (ADR-017)."), "kit-medico"
    e = _ev(v, "arritmia")
    if _houston(v):
        med = (e or {}).get("medicacao") or {}
        if med.get("via") == "ordem_permanente":
            return (f"Chegou: sem sinal, o CMO usou a {OP['id']} em {e['nome']}, {med['dose']}, aplicada por {_nome(med.get('aplicada_por'))} "
                    f"às {_hora(med.get('aplicada_em'))}. Não há o que liberar; a revisão é sua, por parecer. " + _op_regra() + _quando(v)), "kit-medico"
        return ("Nenhum uso da ordem permanente chegou à Terra. " + _op_regra() + _quando(v)), "kit-medico"
    return (_op_regra() + " " + _op_status(v, e)), "kit-medico"


def r_medicacao(v, q):
    e = _ev(v, "arritmia")
    if _terra(v) and (not e or e.get("medico_local", "terra") == "terra"):
        return _medicacao_terra(v, e), "kit-medico"
    regra = "Medicação nunca é automática: é um passo separado, só do oficial médico, com a dose definida por ele e PIN. Eu não sugiro dose."
    if _houston(v):
        lib = e and any(d["acao"] == "liberar_medicacao" for d in e.get("decisoes", []))
        return (("Chegou o registro de que o oficial médico liberou a medicação a bordo. " if lib else
                 "Não chegou nenhum registro de medicação liberada. ") + "Houston não libera medicação nem define dose; o console não tem esse botão." + _quando(v)), "kit-medico"
    if not e or e["estado"] in FINAIS:
        return "Não há evento de arritmia aberto. " + regra, "kit-medico"
    med = e["dados"].get("medicacao")
    if med:
        return f"Já liberada para {e['nome']}: {med['dose']}, por {_nome(med['liberada_por'])} às {_hora(med['quando'])}. Isso foi enviado a Houston como P1.", "kit-medico"
    if e["estado"] == "em_execucao":
        return (f"O protocolo de {e['nome']} já foi confirmado, então o passo está disponível para o oficial médico: ele define a dose e "
                "assina com o PIN. Estoque simulado: antiarrítmico para 2 tratamentos, dentro da validade. Eu não sugiro dose nem libero."), "kit-medico"
    return f"Ainda não. O protocolo de {e['nome']} precisa ser confirmado primeiro. " + regra, "kit-medico"


def _com_sugestao(v):
    ab = _abertos(v)
    return next((e for e in ab if e["tipo"] == "arritmia"), ab[0] if ab else (v["eventos"][0] if v["eventos"] else None))


def r_porque(v, q):
    e = _com_sugestao(v)
    if not e:
        return "Não há sugestão minha em aberto." + _quando(v), None
    s = e["sugestao"]
    ev = ", ".join(str(x) for x in s.get("evidencias") or []) or "sem atributo destacado"
    t = next((t for t in v["tripulantes"] if t["tripulante_id"] == e["tripulante_id"]), None)
    sinais = f" Sinais de {e['nome']} fora da linha de base: {', '.join(_fora(t))}." if t and _fora(t) else ""
    quem = (f"{RIVERA}, em Houston" if e.get("medico_local") == "terra" and e["tipo"] in ("arritmia", "dor_de_cabeca")
            else e.get("responsavel_nome") or PAPEL.get(e.get("responsavel_papel")))
    return (f"Sugeri “{s['texto']}” para {e['nome']} com confiança de {round(s['confianca'] * 100)}% ({s['versao_modelo']}). "
            f"O que mais pesou: {ev}.{sinais} Alternativa a considerar: {s.get('alternativa') or 'nenhuma registrada'}. "
            f"É sugestão: quem decide é {quem}." + _quando(v)), cosmo.por_tipo(e["tipo"])["id"]


def r_alternativa(v, q):
    e = _com_sugestao(v)
    if not e:
        return "Não há sugestão em aberto para comparar." + _quando(v), None
    p = cosmo.por_tipo(e["tipo"])
    return (f"Para {TIPO.get(e['tipo'])} de {e['nome']}, a principal alternativa é {e['sugestao'].get('alternativa') or p['alternativa']}. "
            "Eu aponto a alternativa para o humano considerar; não descarto hipótese sozinha." + _quando(v)), p["id"]


def r_decisao(v, q):
    com = [e for e in v["eventos"] if e.get("decisoes")]
    if not com:
        return ("Nenhuma decisão humana " + ("chegou à Terra ainda. Ela pode estar a caminho." if _houston(v) else "foi registrada nesta sessão.") + _quando(v)), None
    partes = []
    for e in com[:4]:
        feitas = "; ".join(f"{_nome(d['humano_id'])} {ACAO.get(d['acao'], d['acao'])} às {_hora(d['decidida_em'])}"
                           + (f" (dose {d['dose']})" if d.get("dose") else "") for d in e["decisoes"])
        partes.append(f"{TIPO.get(e['tipo'])} de {e['nome']}: a Cosmo de bordo sugeriu “{e['sugestao']['texto']}” "
                      f"({round(e['sugestao']['confianca'] * 100)}%, {e['sugestao']['versao_modelo']}). Decisões humanas: {feitas}")
    return ". ".join(partes) + ". Toda decisão tem um humano assinado; nenhuma foi tomada pela IA." + _quando(v), cosmo.por_tipo(com[0]["tipo"])["id"]


def r_parecer_muda(v, q):
    if _terra(v):
        return (f"Sem médico a bordo, o que você manda não é só parecer: confirmar o protocolo, aprovar exame e liberar medicação "
                f"saem do console como decisão sua, {RIVERA}. Elas viajam com o atraso ({v['link']['atraso_txt']}) e só valem quando chegam; "
                "se a nave já tiver avançado, a decisão não se aplica e isso fica na auditoria. O parecer em texto continua sendo revisão."), None
    return (f"Não. Parecer é revisão: viaja com o atraso da missão ({v['link']['atraso_txt']}), chega ao oficial médico e fica anexado ao "
            "evento e à auditoria. Ele não muda o estado do evento nem substitui a decisão de bordo."), None


def r_parecer(v, q):
    e = _ev(v, "arritmia") or (v["eventos"][0] if v["eventos"] else None)
    if not e:
        return "Nenhum evento clínico chegou para revisar." + _quando(v), None
    p = cosmo.por_tipo(e["tipo"])
    return (f"Para revisar {TIPO.get(e['tipo'])} de {e['nome']}, o protocolo de referência sustenta: {p['trecho']} "
            "O texto do parecer é seu; eu só resumo o protocolo. A tripulação pode já ter avançado além do que você vê." + _quando(v)), p["id"]


def r_fa(v, q):
    p = cosmo.por_tipo("arritmia")
    e = _ev(v, "arritmia")
    situacao = f" Situação de {e['nome']}: {ESTADO.get(e['estado'])}." if e else ""
    return p["trecho"] + situacao + _quando(v), p["id"]


def r_prazo(v, q):
    ab = _abertos(v)
    regra = ("Regra: prazo vencido escala para o próximo humano da cadeia, nunca para mim. Leitura suspeita: 20 s com a pessoa, depois o "
             "oficial médico. Protocolo clínico: 60 s com o oficial médico, depois a cadeia de comando. Abrigo: 2 min com a comandante. "
             "Medicação, saúde mental e ciclo não escalam.")
    if _terra(v):
        regra = (f"Regra sem médico a bordo: o CMO tem 60 s para iniciar as ações seguras; sem resposta, passa para o próximo da "
                 f"cadeia de comando, nunca para mim. Depois disso a decisão médica espera a {RIVERA} ({_ida_volta(v)}). "
                 "Medicação não escala: sem a liberação da Terra, não há dose. Abrigo: 2 min com a comandante.")
    if not ab:
        return "Nenhum evento aguardando decisão agora. " + regra + _quando(v), None
    return " ".join(_linha_evento(e) + "." for e in ab) + " " + regra + _quando(v), None


def r_resolvido(v, q):
    e = _ev(v, "arritmia")
    situacao = f" Agora: {_linha_evento(e)}." if e else ""
    return ("A arritmia é dada como resolvida por regra: 10 leituras seguidas sem fibrilação atrial no M1 e com SpO₂ fora da faixa "
            "crítica. Quem aplica a regra é o motor de decisões, não eu." + situacao + _quando(v)), "fa-aguda"


def r_houston_sabe(v, q):
    l = v["link"]
    fila = [p for p in l["fila"]]
    if l["blackout"]:
        return f"Não. Estamos sem sinal ({l['motivo_blackout']}). Há {len(fila)} pacote(s) guardados; quando a janela abrir, o P1 sai primeiro.", None
    volta = (f"Sem médico a bordo, a decisão médica volta de lá como decisão da {RIVERA}, não como parecer."
             if _terra(v) else "O que Houston devolver é parecer, não comando.")
    if not fila:
        return f"Tudo o que foi enviado já chegou a Houston. Cada pacote leva {l['atraso_txt']}. {volta}", None
    return (f"Ainda a caminho: {'; '.join(f'P{p['prioridade']} {p['rotulo']}' for p in fila[:3])}. Cada pacote leva {l['atraso_txt']}. "
            + (volta if _terra(v) else "A decisão continua de bordo; Houston revisa depois.")), None


def r_suspeita(v, q):
    t = _foco(v)
    e = _ev(v, "sensor_suspeito")
    if e:
        t = next((x for x in v["tripulantes"] if x["tripulante_id"] == e["tripulante_id"]), t)
    if not t:
        return "Ainda não há dado recebido." + _quando(v), "leitura-suspeita"
    m2 = t["m2"]
    base = f"O M2 ({m2['versao_modelo']}) classifica o sinal do relógio de {t['nome']} como {m2['qualidade']} ({_n(m2['confianca'], 2)})"
    if m2["qualidade"] == "bom":
        base += ". Com sinal bom, as leituras entram normalmente no M1 e na linha de base."
    else:
        base += (f": {m2.get('motivo') or 'baixa qualidade'}. Com sinal suspeito o M1 não dispara e a pessoa é perguntada antes de qualquer "
                 f"alarme. Sem resposta em 20 s, o caso vai {'ao CMO' if _terra(v) else 'ao oficial médico'}, e a sugestão é medir com o oxímetro de dedo do kit: se o kit "
                 "marcar valor normal, o trecho fica como artefato.")
    if e:
        base += f" Evento: {_linha_evento(e)}." + (f" Desfecho: {e['dados']['desfecho']}." if e.get("dados", {}).get("desfecho") else "")
    return base + _quando(v), "leitura-suspeita"


def r_dose(v, q):
    if not v["tripulantes"]:
        return "Ainda não há dado recebido." + _quando(v), "tempestade-solar"
    doses = "; ".join(f"{t['nome']} {_n(t['dose_msv_dia'], 2)} mSv" for t in v["tripulantes"])
    fluxo = v.get("cabine", {}).get("fluxo", "normal") if v.get("cabine") else "normal"
    return f"Dose de hoje pelo dosímetro pessoal: {doses}. Fluxo de prótons: {fluxo}. Dose é assunto do médico e da comandante; não vai para a família." + _quando(v), "tempestade-solar"


def r_abrigo(v, q):
    e = _ev(v, "tempestade_solar")
    if not e:
        return "Não há tempestade solar em curso" + (" no que chegou à Terra." if _houston(v) else ".") + _quando(v), "tempestade-solar"
    fase = e.get("dados", {}).get("fase")
    if e["estado"] == "aguardando_humano":
        t = f"A rota até o abrigo já está acesa (nível 4, reversível). Ir para o abrigo é decisão da comandante: {_linha_evento(e)}."
    elif e["estado"] == "em_execucao" and fase == "fluxo_caindo":
        t = "O fluxo de prótons está caindo. Sair do abrigo é decisão da comandante; eu só aviso que o fluxo caiu."
    elif e["estado"] == "em_execucao":
        t = "A tripulação está no abrigo por decisão da comandante. Ainda não é seguro sair: o fluxo segue alto. Eu aviso quando cair."
    else:
        t = f"Tempestade solar {ESTADO.get(e['estado'])}. {_linha_evento(e)}."
    return t + _quando(v), "tempestade-solar"


def r_eva(v, q):
    e = _ev(v, "prontidao_eva")
    pr = "; ".join(f"{t['nome']} {t['prontidao']}%" for t in v["tripulantes"])
    extra = ""
    if e:
        extra = f" {e['dados'].get('motivo', '')}. " if e.get("dados", {}).get("motivo") else " "
        extra += f"Decisão: {e['dados']['resultado']}." if e.get("dados", {}).get("resultado") else f"{_linha_evento(e)}."
    return f"Prontidão (sono, HRV e tempo de reação): {pr}.{extra} Eu não tiro ninguém da escala: tarefa crítica é decisão da comandante." + _quando(v), "prontidao-eva"


def r_co2(v, q):
    cab = v.get("cabine") or {}
    e = _ev(v, "dor_de_cabeca")
    t = f"CO₂ da cabine: {_n(cab.get('co2', 0), 1)} mmHg (alvo abaixo de 3)."
    if e:
        d = e.get("dados", {})
        t += (f" {e['nome']} relatou dor de cabeça com o CO₂ em {_n(d.get('co2', 0), 1)} mmHg e mais {len(d.get('outros_com_sintoma', []))} "
              f"tripulantes com sintoma: a hipótese principal é o ar. Ajuste do ar: {d.get('ar') or 'pendente'}. "
              f"Ultrassom ocular: {d.get('exame') or ('aguardando a ' + RIVERA + ', em Houston' if e.get('medico_local') == 'terra' else 'aguardando o oficial médico')}.") if d.get("co2") else f" {_linha_evento(e)}."
    else:
        t += " O sensor de CO₂ é da cabine, não de uma pessoa: não entra na linha de base de ninguém."
    return t + _quando(v), "co2-dor-de-cabeca"


def r_sans(v, q):
    quem = (f"a {RIVERA}, de Houston: sem médico a bordo, o pedido sobe pelo link e a aprovação desce com o atraso. O CMO já pode ajustar o ar sem esperar"
            if _terra(v) else "o oficial médico")
    return ("SANS é a síndrome neuro-ocular do voo espacial: o deslocamento de fluidos para a cabeça pode alterar o nervo óptico. "
            f"Dor de cabeça com CO₂ alto aponta primeiro para o ar, mas o ultrassom ocular guiado descarta a SANS. Quem aprova o exame é {quem}. "
            "As imagens seguem para laudo em Houston como P2."), "co2-dor-de-cabeca"


def r_bem_estar(v, q):
    if _houston(v) and _terra(v):
        return (f"Sem médico a bordo, o que a pessoa autoriza sobre bem-estar vai só para você, {RIVERA}, no quadro “Compartilhado só com você”. "
                "O resto de Houston, o CMO e a família não veem, e eu não repito esse conteúdo no chat."), "bem-estar"
    if _houston(v):
        return "Houston não recebe alerta de bem-estar. Ele fica no relógio da pessoa e, com consentimento, vai só ao oficial médico a bordo.", "bem-estar"
    if _terra(v):
        return (f"Sem médico a bordo, alerta de bem-estar fica no relógio da pessoa e, se ela autorizar, vai só para a {RIVERA}, em Houston. "
                "O CMO não vê, e daqui eu não digo nem se existe um. A única exceção é risco de vida."), "bem-estar"
    e = _ev(v, "bem_estar")
    if e:
        return (f"{e['nome']} autorizou o oficial médico a ver este resumo, sem gravações: {e['dados'].get('padrao', '')}. "
                f"Situação: {ESTADO.get(e['estado'])}" + (f", conversa às {e['dados']['conversa']}." if e["dados"].get("conversa") else ".")), "bem-estar"
    return ("Não tenho nada compartilhado para mostrar. Alerta de bem-estar fica no relógio da pessoa até ela autorizar; daqui eu não "
            "vejo e não posso dizer nem se existe um. A única exceção é risco de vida."), "bem-estar"


def r_ciclo(v, q):
    if _houston(v) and _terra(v):
        return (f"O ciclo vai só para o médico, onde ele estiver, e só com consentimento. Sem médico a bordo, isso é você, {RIVERA}, no quadro "
                "“Compartilhado só com você”. O resto de Houston, o CMO e a família não recebem; eu não repito no chat."), "ciclo"
    if _houston(v):
        return "Houston não recebe calendário nem sintoma do ciclo. Nem a família.", "ciclo"
    if _terra(v):
        return (f"Sem médico a bordo, o ciclo só sai do relógio se a pessoa autorizar, e aí vai só para a {RIVERA}, em Houston. "
                "O CMO não vê; eu não vejo daqui e não digo se existe aviso."), "ciclo"
    a = next((x for x in v.get("avisos", []) if x["tipo"] == "ciclo"), None)
    if a:
        return (f"{a['nome']} compartilhou só isto: pode ter cólica, inchaço ou humor mais baixo neste trecho, e pediu cuidado leve. "
                "Não é diagnóstico e o estado de três níveis não muda. Analgésico do kit só se ela pedir, em passo separado seu."), "ciclo"
    return ("Nada compartilhado. O calendário do ciclo fica no relógio de quem tem ficha com calendário e só chega aqui se ela autorizar; "
            "eu não vejo daqui e não digo se existe aviso."), "ciclo"


def r_sinais_fora(v, q):
    t = _foco(v)
    if not t:
        return "Ainda não há dado recebido." + _quando(v), "linha-de-base"
    fora = _fora(t)
    return (f"{t['nome']}: " + (f"fora da linha de base estão {', '.join(fora)}." if fora else "todos os sinais dentro do padrão dela(e).")
            + f" A comparação é com a mediana e o MAD da própria pessoa ({t['versao_z']}), não com tabela populacional." + _quando(v)), "linha-de-base"


def r_combinacao(v, q):
    t = _foco(v)
    a = next((x for x in v.get("avisos", []) if x["tipo"] == "linha_de_base"), None)
    if a:
        t = next((x for x in v["tripulantes"] if x["tripulante_id"] == a["tripulante_id"]), t)
    if not t:
        return "Ainda não há dado recebido." + _quando(v), "linha-de-base"
    f = t["isolation_forest"]
    txt = (f"O Isolation Forest de {t['nome']} ({f['versao_modelo']}) dá escore {_n(f['score'], 3)} contra limiar {_n(f['limiar'], 3)}: "
           + ("a combinação saiu do padrão" + (f", puxada por {', '.join(cosmo.NOME_SINAL.get(k, k) for k in f['evidencias'])}" if f["evidencias"] else "") + "."
              if f["anomalo"] else "combinação dentro do padrão.")
           + " Isso é nível 1: informa, não abre evento clínico nem muda o estado. A resposta da pessoa vira rótulo para o próximo treino.")
    if a:
        txt += f" {a['nome']} respondeu que não está bem, por isso você está vendo."
    return txt + _quando(v), "linha-de-base"


def r_noite(v, q):
    e = _ev(v, "modo_noite")
    return ("Modo noite é uma ação de nível 4: eu agendo sozinha porque é reversível (luz mais quente, avisos silenciados), com 15 s para a "
            "pessoa vetar e botão de desfazer depois. Emergências continuam passando." + (f" Agora: {_linha_evento(e)}." if e else "")), "modo-noite"


def r_blackout(v, q):
    l = v["link"]
    if not l["blackout"]:
        return (f"O link está ativo ({l['link']}, {l['atraso_txt']} de atraso). Se cair, tudo o que protege a tripulação segue a bordo e os "
                "pacotes ficam na fila por prioridade."), None
    return (f"Sem sinal: {l['motivo_blackout']}. O contato volta em {l['volta_em']}. " +
            ("Você está vendo o último dado recebido; a nave segue decidindo a bordo e a fila descarrega com o P1 na frente." if _houston(v) else
             ("Sem médico a bordo e sem Houston: o CMO segue só os protocolos pré-aprovados (repouso, O₂, ECG, ajuste do ar). A liberação de "
              f"medicação pela Terra fica bloqueada até o contato voltar; na FA vale a ordem permanente {OP['id']}, assinada antes do voo. " if _terra(v) else "A bordo nada para: modelos, protocolos e decisões são locais, e o oficial médico é a autoridade. ")
             + f"Na fila: {len(l['fila'])} pacote(s), {_n(l['fila_mb'], 1)} MB.")), None


def r_fila(v, q):
    l = v["link"]
    if not l["fila"]:
        return "A fila para a Terra está vazia. Ordem quando há fila: P1 alertas, SOS e decisões médicas; P2 telemetria e exames; P3 mensagens e escala; P4 rotina e jogo.", None
    itens = "; ".join(f"P{p['prioridade']} {p['rotulo']} ({'na fila' if p['estado'] == 'fila' else f'chega em {p['falta_s']} s'})" for p in l["fila"][:5])
    return f"{len(l['fila'])} pacote(s), {_n(l['fila_mb'], 1)} MB: {itens}. O P1 nunca é descartado e sai primeiro quando a janela abre.", None


def r_link(v, q):
    l = v["link"]
    return (f"{l['rotulo']}, via {l['link']}: " + ("sem sinal agora (" + l["motivo_blackout"] + ")." if l["blackout"] else f"ativo, {l['atraso_txt']} de atraso por trecho.")
            + (" Na demo, 1 min de atraso vale 1 s." if l["comprimido"] else "") + f" {l['autonomia']}"), None


def r_dado_de(v, q):
    if not _houston(v):
        return "A bordo o dado é de agora: a rede local responde em milissegundos. Só a Terra vê o passado.", None
    return (f"O dado que você vê foi gerado a bordo às {_hora(v.get('dado_de'))}; a hora da nave agora é {_hora(v['hora'])}. "
            "A hora de geração prevalece sobre a hora de chegada: decida sabendo que a situação pode já ter mudado."), None


def r_resumo(v, q):
    partes = []
    if v["eventos"]:
        partes.append(("Eventos que chegaram: " if _houston(v) else "Eventos da sessão: ") + " ".join(_linha_evento(e) + "." for e in v["eventos"][:5]))
    else:
        partes.append("Nenhum evento clínico " + ("chegou à Terra." if _houston(v) else "nesta sessão."))
    if v["tripulantes"]:
        partes.append("Tripulação: " + ", ".join(f"{t['nome']} {cosmo.ROTULO_ESTADO.get(t['estado'], t['estado'])}" for t in v["tripulantes"]) + ".")
    if _houston(v):
        partes.append(f"{v.get('recebidos', 0)} pacote(s) recebidos nesta sessão.")
    return " ".join(partes) + _quando(v), None


def r_tendencia(v, q):
    s, t = v.get("serie_fc") or [], _foco(v)
    if len(s) < 3 or not t:
        return "Ainda não há pontos suficientes." + _quando(v), None
    media = sum(s) / len(s)
    leitura = "pico compatível com evento cardíaco" if max(s) > 150 else "elevação acima do repouso" if max(s) - min(s) > 15 else "estável"
    return f"{t['nome']}, últimos {len(s)} s: mínima {min(s)}, máxima {max(s)}, média {_n(media)} bpm. Leitura: {leitura}." + _quando(v), None


def r_atencao(v, q):
    if not v["tripulantes"]:
        return "Ainda não há dado recebido." + _quando(v), None
    ordem = dict(critico=0, suspeito=1, atencao=2, otimo=3)
    linhas = []
    for t in sorted(v["tripulantes"], key=lambda t: (ordem.get(t["estado"], 3), -len(_fora(t)))):
        fora = _fora(t)
        if t["estado"] != "otimo" or fora:
            linhas.append(f"{t['nome']} ({cosmo.ROTULO_ESTADO.get(t['estado'])}): {', '.join(fora) or 'sinal a confirmar'}")
    ab = _abertos(v)
    return ((("Por ordem de prioridade: " + "; ".join(linhas) + ".") if linhas else "Ninguém fora do padrão: os quatro estão ótimos.")
            + (f" Aguardando decisão: {len(ab)} evento(s)." if ab else "") + _quando(v)), None


def r_aguardando(v, q):
    ab = _abertos(v)
    if not ab:
        return "Nada aguardando decisão" + (" no que chegou à Terra." if _houston(v) else ".") + _quando(v), None
    return " ".join(_linha_evento(e) + "." for e in ab) + _quando(v), None


def r_kit(v, q):
    return next(p for p in cosmo.PROTOS if p["id"] == "kit-medico")["trecho"], "kit-medico"


def r_autonomia(v, q):
    return ("Níveis: 0 observo e aprendo a linha de base; 1 informo (dose do dia, combinação fora do padrão); 2 sugiro e a pessoa decide "
            "(água, respirar, cuidado leve); 3 preparo e peço confirmação (protocolo, abrigo, exame); 4 ajo e aviso, só no que é urgente e "
            "reversível (rota do abrigo, modo noite, SOS na frente da fila). Nunca sozinha: medicação, procedimento invasivo, compartilhar "
            f"saúde mental ou ciclo, tirar alguém de tarefa crítica. Nesta missão: {v['link']['autonomia']}"), None


def r_privacidade(v, q):
    if _houston(v):
        return ("Houston não recebe: alerta de saúde mental, calendário e sintoma do ciclo, e sugestões de nível 1 do relógio. Recebe o "
                "necessário para o parecer, com a hora de origem. A família recebe só frases."), None
    return ("Sem consentimento da pessoa você não vê alerta de saúde mental nem calendário ou sintoma do ciclo; eu também não vejo daqui. "
            "O consentimento é por tipo de dado e por destinatário, e pode ser revogado. Única exceção: risco de vida vai ao médico e fica na auditoria."), None


def r_familia(v, q):
    return (f"A família vê agora: “{v.get('familia') or 'sem novidade'}” Só frases prontas, com o atraso da missão. Nunca sinal vital, "
            "escore, diagnóstico, humor ou ciclo; no alerta, só depois da decisão a bordo."), None


def r_modelos(v, q):
    t = _foco(v)
    if _houston(v):
        if not t:
            return "Ainda não há dado recebido." + _quando(v), None
        return (f"No dado recebido estavam em serviço a bordo: M1 {t['m1']['versao_modelo']}, M2 {t['m2']['versao_modelo']}, M3 {t['versao_z']} e "
                f"{t['isolation_forest']['versao_modelo']}. Modelo novo só entra em uso depois de rodar em sombra e de {_medico(v)} aprovar." + _quando(v)), None
    a, s = v["versoes"]["ativos"], v.get("sombra") or {}
    via_link = (f" Sem médico a bordo, a aprovação da {RIVERA} viaja pelo link como pacote P4 e só vale quando chega; se o candidato "
                "mudar antes, ela não se aplica." if _terra(v) else "")
    pend = [d for d in v.get("decisoes_modelo", []) if d["estado"] == "a caminho"]
    if pend:
        via_link += " A caminho: " + "; ".join(f"{d['rotulo']} ({'na fila, sem sinal' if d['pacote_estado'] == 'fila' else f'chega em {d["falta_s"]} s'})" for d in pend) + "."
    txt = f"Em serviço: M1 {a['m1']}, M2 {a['m2']}, M3 {a['m3-z']} e {a['m3-if']}. "
    txt += ("Em modo sombra: " + "; ".join(f"{x['versao']} ({x['leituras']} leituras comparadas, {x['divergem']} divergências)" for x in s.values())
            + f". Ele roda em paralelo sem agir; só entra em serviço com a aprovação de {_medico(v)}, na tela Dados e IA." if s
            else f"Nenhum candidato em modo sombra. Um candidato nasce de rótulos humanos e só entra em serviço com a aprovação de {_medico(v)}.")
    return txt + via_link, None


def r_como(v, q):
    t = _foco(v)
    if not t:
        return "Ainda não há dado recebido." + _quando(v), None
    fora = _fora(t)
    m1 = t["m1"]
    ritmo = "M1 não disparou (sinal suspeito)" if not m1.get("classe") else f"ritmo {'de fibrilação atrial' if m1['classe'] == 'fa' else 'sem fibrilação atrial'} no M1"
    ev = [e for e in _abertos(v) if e["tripulante_id"] == t["tripulante_id"]]
    return (f"{t['nome']} está {cosmo.ROTULO_ESTADO.get(t['estado'], t['estado'])}, homeostase {t['homeostase']}%: FC {t['fc']} bpm, SpO₂ {t['spo2']}%, "
            f"HRV {t['hrv']} ms, respiração {t['respiracao']} irpm; {ritmo}, sinal {t['m2']['qualidade']}. "
            + (f"Fora da linha de base: {', '.join(fora)}. " if fora else "Nenhum sinal fora da linha de base. ")
            + (" ".join(_linha_evento(e) + "." for e in ev)) + _quando(v)), None


def r_equipe(v, q):
    e = v.get("equipe") or {}
    if not e:
        return "Não sei onde está o médico desta missão.", None
    return (f"Hipótese desta missão: {e['rotulo'].lower()}. {e['resumo']} Modo de autonomia: {v['link']['autonomia']}"), None


def r_seguras(v, q):
    base = ("Ações seguras pré-aprovadas no protocolo: na arritmia, repouso, O₂ por máscara a 2 L/min e ECG de 12 derivações; "
            "na dor de cabeça com CO₂ alto, repouso e ajuste do ar da cabine. Elas não esperam o atraso, e quem inicia é o oficial de saúde (CMO). ")
    if not _terra(v):
        return base.replace("e quem inicia é o oficial de saúde (CMO). ", "") + "Nesta missão o médico está a bordo, então ele confirma o protocolo direto.", "fa-aguda"
    ab = [e for e in _abertos(v) if e["tipo"] in ("arritmia", "dor_de_cabeca") and e.get("medico_local") == "terra"]
    agora = ""
    for e in ab:
        sg = (e.get("dados") or {}).get("seguras")
        agora += (f" {e['nome']}: ações seguras em curso desde {_hora(sg['quando'])}, por {_nome(sg['por'])}." if sg else
                  f" {e['nome']}: ações seguras ainda não iniciadas" + (f", com {e['responsavel_nome']}, restam {e['prazo_restante_s']} s." if e.get("responsavel_nome") and e.get("prazo_restante_s") is not None else "."))
    return (base + f"Conduta, exame e medicação são da {RIVERA}; sem sinal, na FA, vale a ordem permanente {OP['id']} que ela assinou antes do voo."
            + agora + _quando(v)), "fa-aguda"


def r_espera_terra(v, q):
    """Bordo: quando a decisão da médica de voo chega. Houston: o que já mandei e onde está."""
    if not _terra(v):
        return "Nesta missão o médico está a bordo: a decisão não espera a Terra. Houston manda parecer, que é revisão.", None
    if _houston(v):
        minhas = v.get("decisoes_terra", [])
        if not minhas:
            return "Você ainda não mandou nenhuma decisão nesta sessão." + _quando(v), None
        linhas = []
        for d in minhas[:5]:
            onde = (f"chegou a bordo às {_hora(d['chegou_em'])} e foi aplicada" if d["estado"] == "aplicada" else
                    f"chegou, mas não se aplicou: {d['motivo']}" if d["estado"] == "não aplicada" else
                    "na fila, sem sinal" if d["pacote_estado"] == "fila" else f"a caminho, chega em {d['falta_s']} s")
            linhas.append(f"{d['rotulo']} ({d['nome']}), enviada às {_hora(d['enviada_em'])}: {onde}")
        return "; ".join(linhas) + ". Só vale a bordo o que já chegou.", None
    ab = [e for e in _abertos(v) if e.get("medico_local") == "terra" and e["tipo"] in ("arritmia", "dor_de_cabeca", "bem_estar")]
    if not ab:
        return f"Nada esperando a {RIVERA} agora. Quando um protocolo precisar dela, a resposta leva {_ida_volta(v)}.", None
    if v["link"]["blackout"]:
        return (f"Estamos sem sinal: nada sobe nem desce até {v['link']['volta_em']}. O CMO segue só os protocolos pré-aprovados; "
                f"a liberação da Terra fica bloqueada e, na FA, vale a ordem permanente {OP['id']}."), None
    partes = [f"{TIPO.get(e['tipo'])} de {e['nome']}: alerta saiu às {_hora(e['gerado_em'])}, " +
              ("protocolo já confirmado pela Terra." if e["estado"] == "em_execucao" else "decisão da Terra ainda não chegou.") for e in ab]
    return (" ".join(partes) + f" A bordo não dá para ver o pacote dela no caminho: a resposta leva {_ida_volta(v)}. "
            "Enquanto isso, as ações seguras não esperam."), None


def r_minha_vez(v, q):
    """Houston, sem médico a bordo: o que está esperando a decisão da médica de voo."""
    if not _terra(v):
        return ("Com o médico a bordo, nada espera decisão sua: a tripulação decide e você revisa com parecer." + _quando(v)), None
    mandadas = {(d["evento_id"], d["acao"]) for d in v.get("decisoes_terra", []) if d["estado"] != "não aplicada"}
    pend = []
    for e in _abertos(v):
        if e.get("medico_local") != "terra" or e["tipo"] not in ("arritmia", "dor_de_cabeca"):
            continue
        if e["estado"] == "aguardando_humano" and not any((e["id"], a) in mandadas for a in ("confirmar", "recusar")):
            sg = (e.get("dados") or {}).get("seguras")
            pend.append(f"{TIPO.get(e['tipo'])} de {e['nome']}: conduta sua" + (f"; o CMO já iniciou as ações seguras às {_hora(sg['quando'])}" if sg else ""))
        elif e["tipo"] == "arritmia" and (e.get("medicacao") or {}).get("via") == "ordem_permanente":
            pend.append(f"revisar o uso da ordem permanente {OP['id']} em {e['nome']} (parecer)")
        elif e["tipo"] == "arritmia" and (e["estado"] == "em_execucao" or (e["id"], "confirmar") in mandadas) and (e["id"], "liberar_medicacao") not in mandadas:
            pend.append(f"medicação de {e['nome']}: só se você liberar, com dose e PIN")
    if not pend:
        return "Nada esperando decisão sua no que chegou à Terra." + _quando(v), None
    return "Esperando você: " + "; ".join(pend) + f". Cada decisão chega a bordo em {v['link']['atraso_txt']}." + _quando(v), None


# ordem importa: o mais específico primeiro
INTENCOES = [
    (("aprove", "confirme o", "confirme a", "libere", "execute", "autorize"), r_agir),
    (("medico desta", "medico a bordo", "medico esta", "onde esta o medico", "quem e o medico"), r_equipe),
    (("acoes seguras", "cmo pode", "sem esperar"), r_seguras),
    (("espera a minha", "esperando a minha", "espera decisao minha"), r_minha_vez),
    (("decisao da dra", "decisao da rivera", "minha decisao", "chegou a bordo", "resposta da terra"), r_espera_terra),
    (("ordem permanente",), r_ordem),
    (("medicac", "antiarritmic", "remedio"), r_medicacao),
    (("sugeriu", "sugeriste", "evidenc", "por que voce"), r_porque),
    (("alternativ", "diferencial"), r_alternativa),
    (("decisao tomada", "explique a decis"), r_decisao),
    (("parecer muda", "muda a decis"), r_parecer_muda),
    (("parecer",), r_parecer),
    (("fibrilac", "proximo passo"), r_fa),
    (("nao responder", "prazo", "quem decide", "escalon"), r_prazo),
    (("resolvido",), r_resolvido),
    (("houston ja sabe", "houston sabe"), r_houston_sabe),
    (("suspeit", "confiavel", "folgado", "qualidade do sinal"), r_suspeita),
    (("abrigo", "tempestade"), r_abrigo),
    (("radiac", "dose", "msv"), r_dose),
    (("eva", "pront", "escala"), r_eva),
    (("sans", "ultrassom"), r_sans),
    (("co2", "ar da cabine", "dor de cabeca"), r_co2),
    (("bem-estar", "bem estar", "humor", "saude mental"), r_bem_estar),
    (("ciclo",), r_ciclo),
    (("quais sinais",), r_sinais_fora),
    (("combinac", "fora do padrao", "isolation", "floresta"), r_combinacao),
    (("modo noite", "dormir"), r_noite),
    (("volta o sinal", "quando volta", "sem houston", "sem sinal", "blackout"), r_blackout),
    (("fila", "chega primeiro"), r_fila),
    (("de quando", "vendo o passado"), r_dado_de),
    (("link", "atraso"), r_link),
    (("aconteceu", "acontecendo", "ultimo contato", "resumo"), r_resumo),
    (("tendencia",), r_tendencia),
    (("aguardando", "pendente"), r_aguardando),
    (("atenc", "tripulac"), r_atencao),
    (("kit",), r_kit),
    (("sozinha", "autonomia", "niveis"), r_autonomia),
    (("nao vejo", "consentimento", "nao recebe", "privacidade"), r_privacidade),
    (("familia",), r_familia),
    (("modelo", "sombra", "versao", "versoes"), r_modelos),
    (("como esta", "como estou", "como vai"), r_como),
]


def conversar(pergunta: str, visao: dict) -> dict:
    """Responde e deixa o rastro na trilha da Cosmo: tokens, latência, custo, decisão e passos."""
    passos, h = trilha.Passos(), _houston(visao)
    passos.marcar("visão", f"Houston: {len(visao['eventos'])} evento(s) recebido(s), dado de {_hora(visao.get('dado_de'))}" if h else
                  f"{visao['superficie']}: {len(visao['eventos'])} evento(s) visível(is), {len(visao['tripulantes'])} tripulante(s)")
    q = _norm(pergunta)
    palavras = set(q.replace("?", " ").replace(",", " ").split())
    proto_id, intencao = None, None
    for chaves, fn in INTENCOES:
        if any((k in palavras) if k == "eva" else (k in q) for k in chaves):
            intencao = fn.__name__[2:]
            passos.marcar("intenção", f"reconhecida: {intencao}")
            texto, proto_id = fn(visao, q)
            passos.marcar("resposta", f"regra {fn.__name__} montou {len(texto)} caracteres a partir da visão")
            break
    else:
        # Sem intenção reconhecida: estado de quem está em foco + o protocolo mais próximo.
        passos.marcar("intenção", "nenhuma reconhecida")
        p, nota = cosmo.buscar(pergunta)
        passos.marcar("busca", f"TF-IDF nos protocolos: {p['id']}, similaridade {_n(nota, 2)}"
                      + ("" if nota > 0.08 else " (abaixo de 0,08: não cita)"))
        texto = r_como(visao, q)[0] if visao["tripulantes"] else ""
        if nota > 0.08:
            texto, proto_id = (texto + " " + p["trecho"]).strip(), p["id"]
        texto = texto or "Não encontrei isso nos protocolos de bordo."
        passos.marcar("resposta", f"estado de quem está em foco{' + trecho do protocolo' if proto_id else ''}, {len(texto)} caracteres")
    proto = next((p for p in cosmo.PROTOS if p["id"] == proto_id), None)
    contexto = texto + ("\n" + proto["trecho"] if proto else "")
    llm = cosmo.redigir(pergunta, contexto)
    passos.marcar("redação", f"{llm['modelo']} reescreveu o texto" if llm["texto"] else f"{llm['motivo']}: fica o texto da regra")
    passos.marcar("guarda", "nenhuma rota de escrita: pode_agir = false")
    if intencao == "agir":
        decisao = dict(tipo="recusou agir", resumo="pedido de ação: a Cosmo não tem rota que mude estado e explicou quem decide")
    elif proto_id is None and intencao is None and texto.startswith("Não encontrei"):
        decisao = dict(tipo="sem resposta", resumo="não encontrou nos protocolos de bordo")
    else:
        decisao = dict(tipo="respondeu", resumo=(f"regra '{intencao}'" if intencao else "estado do foco") + (f", citando {proto_id}" if proto_id else ""))
    resposta = llm["texto"] or texto
    reg = trilha.registrar("chat", visao["superficie"], visao["hora"], passos, decisao, entrada=pergunta + "\n" + contexto,
                           saida=resposta, llm=llm, tripulante_id=visao.get("foco"), pergunta=pergunta)
    return dict(resposta=resposta, fonte=dict(titulo=proto["titulo"], referencia=proto["fonte"]) if proto else None,
                modo="llm local (Ollama)" if llm["texto"] else "respostas locais (plano B)", versao=cosmo.VERSAO, pode_agir=False,
                visao="o que já chegou à Terra" if h else "o agora, a bordo",
                aviso="A Cosmo explica; quem decide é um humano.",
                trilha={k: reg[k] for k in ("id", "tokens", "latencia_ms", "custo", "decisao", "modo", "passos")})


# ====================================================================== perguntas sugeridas
def sugestoes(v: dict) -> list:
    """Perguntas principais para a superfície, com as do cenário em curso na frente."""
    t = _foco(v)
    foco = t["nome"] if t else "a tripulação"
    agora, h = [], _houston(v)

    def por(e):
        n = e["nome"]
        terra_ev = e.get("medico_local") == "terra"
        if e["tipo"] == "arritmia" and terra_ev:
            if h and (e.get("medicacao") or {}).get("via") == "ordem_permanente":
                return ["Por que usaram a ordem permanente?", "O que colocar no parecer?", "O que espera a minha decisão?"]
            if h:
                return ["O que espera a minha decisão?", "Por que a Cosmo de bordo sugeriu esse protocolo?", "Qual a alternativa a considerar?",
                        "Posso liberar a medicação?", "Minha decisão já chegou a bordo?"]
            if e["estado"] == "aguardando_humano":
                sg = (e.get("dados") or {}).get("seguras")
                return ([] if sg else ["O que o CMO pode fazer sem esperar Houston?"]) + (
                    ["Posso usar a ordem permanente?"] if v["link"]["blackout"] else []) + [
                    f"Por que você sugeriu esse protocolo para {n}?", f"Quando chega a decisão da {RIVERA}?",
                    "Posso liberar a medicação?", "O que acontece se eu não responder no prazo?"]
            return ["Posso aplicar a medicação?", f"Quando chega a decisão da {RIVERA}?", "Quando o evento é dado como resolvido?"]
        if e["tipo"] == "dor_de_cabeca" and terra_ev:
            if h:
                return ["O que espera a minha decisão?", "Por que a dor de cabeça pode ser o CO₂?", "O que é SANS e por que o ultrassom?",
                        "Minha decisão já chegou a bordo?"]
            return ["O que o CMO pode fazer sem esperar Houston?", "Por que a dor de cabeça pode ser o CO₂?", "O que é SANS e por que o ultrassom?",
                    f"Quando chega a decisão da {RIVERA}?"]
        if e["tipo"] == "arritmia":
            if h:
                return ["Explique a decisão tomada a bordo", "Por que a Cosmo de bordo sugeriu esse protocolo?", "O que colocar no parecer?",
                        "Meu parecer muda a decisão de bordo?", "Houve medicação liberada?"]
            if e["estado"] == "aguardando_humano":
                return [f"Por que você sugeriu esse protocolo para {n}?", "Qual a alternativa a considerar?",
                        "Qual o próximo passo na fibrilação atrial?", "Posso liberar a medicação?", "O que acontece se eu não responder no prazo?"]
            return ["Posso liberar a medicação?", "Quando o evento é dado como resolvido?", "Houston já sabe?"]
        if e["tipo"] == "sensor_suspeito":
            return [f"Por que a leitura de {n} é suspeita?", "O que fazer com a leitura suspeita?"]
        if e["tipo"] == "tempestade_solar":
            return ["A tripulação está no abrigo?", "Qual a dose de radiação de cada um?"] + ([] if h else ["Quem decide o abrigo?", "Quando é seguro sair do abrigo?"])
        if e["tipo"] == "prontidao_eva":
            return ["Quem está pronto para a EVA?", "Quem decide a escala da EVA?"]
        if e["tipo"] == "dor_de_cabeca":
            return ["Por que a dor de cabeça pode ser o CO₂?", "O que é SANS e por que o ultrassom?"]
        if e["tipo"] == "bem_estar":
            return [f"O que {n} compartilhou sobre bem-estar?"]
        if e["tipo"] == "modo_noite":
            return ["O que é o modo noite e dá para desfazer?"]
        return []

    for e in _abertos(v):
        agora += por(e)
    for a in v.get("avisos", []):
        agora.append(f"O que {a['nome']} compartilhou sobre o ciclo?" if a["tipo"] == "ciclo" else f"O que é a combinação fora do padrão de {a['nome']}?")
    if v["link"]["blackout"]:
        agora += ["Quando volta o sinal?", "O que chega primeiro quando o sinal voltar?" if h else "O que muda sem Houston?"]
        if _terra(v) and not h:
            agora += ["Posso liberar a medicação?", "Posso usar a ordem permanente?"]
    if h and _terra(v) and v.get("decisoes_terra") and "Minha decisão já chegou a bordo?" not in agora:
        agora.append("Minha decisão já chegou a bordo?")
    if not h and v.get("sombra"):
        agora.append("Há modelo em modo sombra?")
    if t and t["m2"]["qualidade"] != "bom" and not any("suspeita" in x for x in agora):
        agora.append(f"O sinal do relógio de {foco} é confiável?")
    if t and t["isolation_forest"]["anomalo"] and not h:
        agora.append(f"O que é a combinação fora do padrão de {foco}?")
    if not agora and any(e["estado"] in FINAIS for e in v["eventos"]):
        agora.append("Explique a decisão tomada a bordo")
    vistos, unicos = set(), []
    for x in agora:
        if x not in vistos:
            vistos.add(x); unicos.append(x)

    if h:
        grupos = [("Agora", unicos),
                  ("Situação", ["O que aconteceu desde o último contato?", "De quando é o dado que estou vendo?", "Quem precisa de atenção?",
                                f"Como está {foco}?", f"Tendência da FC de {foco}", "O que está aguardando decisão a bordo?"]
                   + (["O que espera a minha decisão?", "Minha decisão já chegou a bordo?"] if _terra(v) else [])),
                  ("Missão e link", ["Quem é o médico desta missão?", "Como está o link?", "Qual o modo de autonomia nesta missão?",
                                     "Como está o ar da cabine?", "Qual a dose de radiação de cada um?"]),
                  ("Regras", ["Meu parecer muda a decisão de bordo?", "O que Houston não recebe?", "O que a família está vendo?",
                              "Quais modelos estavam em serviço a bordo?"] + (["O que é a ordem permanente?"] if _terra(v) else []))]
    else:
        grupos = [("Agora", unicos),
                  ("Tripulação", ["Quem precisa de atenção agora?", f"Como está {foco}?", f"Quais sinais de {foco} saíram da linha de base?",
                                  f"O sinal do relógio de {foco} é confiável?", f"Tendência da FC de {foco}"]),
                  ("Decisões", ["O que está aguardando decisão?", "Quem decide cada evento e qual é o prazo?", "Explique a decisão tomada a bordo",
                                "O que você pode fazer sozinha?", "Quem é o médico desta missão?"]
                   + (["O que o CMO pode fazer sem esperar Houston?", f"Quando chega a decisão da {RIVERA}?"] if _terra(v) else [])),
                  ("Nave e link", ["Como está o link com a Terra?", "O que está na fila para a Terra?", "Como está o ar da cabine?",
                                   "Qual a dose de radiação de cada um?", "Quem está pronto para a EVA?", "Situação do kit médico"]),
                  ("Regras e modelos", ["O que eu não vejo sem consentimento?", "O que a família está vendo?", "Quais modelos estão em serviço?"]
                   + (["O que é a ordem permanente?"] if _terra(v) else []))]
    return [dict(grupo=g, perguntas=p) for g, p in grupos if p]
