"""Filtro de privacidade da família: um dicionário de estado para frase.

A família recebe frases prontas e nunca um número. Nenhuma frase daqui tem
dígito, sinal vital, escore, faixa, diagnóstico, humor ou ciclo (ADR-007, ADR-013).
"""
from ..config import TRIPULACAO

FRASES = {
    ("arritmia", "em_execucao"): "{nome} está em repouso e sendo acompanhada pelo oficial médico.",
    ("arritmia", "resolvido"): "{nome} está bem e segue em repouso por precaução.",
    ("tempestade_solar", "em_execucao"): "A tripulação foi para o abrigo da nave por precaução contra uma tempestade solar. É procedimento de rotina.",
    ("tempestade_solar", "resolvido"): "A tempestade solar passou e a tripulação já saiu do abrigo. Todos bem.",
}
ESTADO_PALAVRA = dict(otimo="bem", atencao="bem", critico="sendo acompanhada pela equipe médica", suspeito="bem")


def frase_do_evento(tipo: str, estado: str, tripulante_id: str):
    modelo = FRASES.get((tipo, estado))
    return modelo.format(nome="A " + TRIPULACAO[tripulante_id]["nome"]) if modelo else None


def feed(link, retrato_terra, missao: dict) -> dict:
    """Só o que já atravessou o link: frases de pacotes entregues e o estado em
    uma palavra, tirado do retrato atrasado que a Terra tem."""
    itens = [dict(frase=p["frase_familia"], gerado_em=p["gerado_em"], recebido_em=p["entregue_em"])
             for p in link.entregues("familia") if p["frase_familia"]][-6:][::-1]
    if retrato_terra is None or missao["blackout"]:
        principal = "Sem sinal da nave por enquanto. Isso é esperado, e a tripulação segue a rotina. Suas mensagens ficam guardadas e seguem quando o sinal voltar."
        estados = {}
    else:
        estados = {tid: ESTADO_PALAVRA.get(v["estado"], "bem") for tid, v in retrato_terra["tripulantes"].items()}
        s = estados.get("sarah", "bem")
        principal = "A Sarah está bem." if s == "bem" else "A Sarah está sendo acompanhada pela equipe médica. Detalhes de saúde ficam entre a tripulação e os médicos."
    return dict(frase=principal, tripulacao=estados, ultimas=itens, atraso=missao["atraso_txt"],
                sem_sinal=missao["blackout"], dado_de=None if retrato_terra is None else retrato_terra["gerada_em"])
