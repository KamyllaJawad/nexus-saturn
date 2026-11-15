"""Cosmo nave: busca nos protocolos de bordo e responde citando a fonte.

A Cosmo conversa, explica e resume. Não importa o motor e não tem nenhuma função
que mude o estado de um evento (ADR-002): recebe o estado pronto, só para leitura.

A busca é TF-IDF local (scikit-learn). Se houver um Ollama em 127.0.0.1:11434, a
redação passa por ele; se não houver, valem as respostas locais (plano B do pitch).
"""
import json
import os
import urllib.request

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import PROTOCOLOS, TRIPULACAO

_base = json.loads(PROTOCOLOS.read_text(encoding="utf-8"))
PROTOS = _base["protocolos"]
AVISO = _base["aviso"]
_vet = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)
_matriz = _vet.fit_transform([f"{p['titulo']} {p['palavras']} {p['trecho']}" for p in PROTOS])
VERSAO = "cosmo-rag-local-0.1"
ROTULO_ESTADO = dict(otimo="ótimo", atencao="em atenção", critico="crítico", suspeito="com sinal a confirmar")
NOME_SINAL = dict(fc="frequência cardíaca", hrv="HRV", spo2="SpO₂", temperatura="temperatura da pele",
                  respiracao="respiração", sono="sono", hidratacao="hidratação")


def buscar(texto: str) -> tuple:
    sim = cosine_similarity(_vet.transform([texto]), _matriz)[0]
    i = int(sim.argmax())
    return PROTOS[i], float(sim[i])


def por_tipo(tipo: str) -> dict:
    return next((p for p in PROTOS if tipo in p["tipos"]), PROTOS[0])


def sugerir(tipo: str, analise: dict | None = None, passos=None) -> dict:
    """Sugestão anexada a um evento. É texto com evidência; nunca é decisão.
    Com `passos` (trilha.Passos), marca o caminho para a trilha da Cosmo."""
    marcar = passos.marcar if passos else (lambda *a: None)
    p = por_tipo(tipo)
    s = dict(texto=p["conduta"], confianca=0.8, alternativa=p["alternativa"], evidencias=[],
             versao_modelo=VERSAO, protocolo=dict(id=p["id"], titulo=p["titulo"], trecho=p["trecho"], fonte=p["fonte"]))
    if not analise:
        marcar("entrada", f"evento injetado pelo cenário ({tipo}), sem saída de modelo")
        marcar("protocolo", f"{p['id']}, escolhido pelo tipo do evento")
        marcar("entrega", "sugestão anexada com confiança padrão 0,8; quem decide é um humano")
        return s
    m1, m2, m3 = analise.get("m1"), analise.get("m2"), analise["m3"]
    if tipo == "arritmia" and m1:
        s.update(confianca=m1["confianca"], evidencias=m1["atributos"], versao_modelo=m1["versao_modelo"])
        marcar("entrada", f"M1 {m1['versao_modelo']}: probabilidade de FA {m1['prob_fa']}")
    elif tipo == "sensor_suspeito" and m2:
        s.update(confianca=m2["confianca"], evidencias=[m2["motivo"] or "sinal de baixa qualidade"], versao_modelo=m2["versao_modelo"])
        marcar("entrada", f"M2 {m2['versao_modelo']}: sinal {m2['qualidade']}")
    elif tipo == "linha_de_base":
        f = m3["isolation_forest"]
        s.update(confianca=min(0.99, round(f["score"], 2)), evidencias=f["evidencias"], versao_modelo=f["versao_modelo"])
        marcar("entrada", f"Isolation Forest {f['versao_modelo']}: escore {f['score']} contra limiar {f['limiar']}")
    elif tipo == "ciclo" and analise.get("ciclo"):
        s.update(evidencias=analise["ciclo"]["sinais_leves"], versao_modelo=analise["ciclo"]["versao"])
        marcar("entrada", f"calendário {analise['ciclo']['versao']} e sinais leves")
    else:
        marcar("entrada", f"análise da leitura ({tipo})")
    marcar("protocolo", f"{p['id']}, escolhido pelo tipo do evento")
    marcar("entrega", f"sugestão anexada com {len(s['evidencias'])} evidência(s) e confiança {s['confianca']}; quem decide é um humano")
    return s


def explicar(evento: dict, analise: dict | None) -> dict:
    """O card "Por que a Cosmo sugeriu isso?": conduta, confiança e versão,
    evidências, trecho do protocolo e alternativa."""
    s = evento.get("sugestao") or {}
    modelos = []
    if analise:
        m1, m2, f = analise.get("m1"), analise.get("m2"), analise["m3"]["isolation_forest"]
        if m1 and m1.get("classe"):
            modelos.append(f"M1 {m1['versao_modelo']}: classe {m1['classe']}, probabilidade de FA {m1['prob_fa']}")
        if m2:
            modelos.append(f"M2 {m2['versao_modelo']}: sinal {m2['qualidade']} ({m2['confianca']})")
        fora = [f"{NOME_SINAL.get(k, k)} z {v['z']}" for k, v in analise["m3"]["metricas"].items() if v["faixa"] != "padrao"]
        modelos.append(f"M3 {analise['m3']['versao_z']}: " + (", ".join(fora) if fora else "todos os sinais no padrão da pessoa"))
        modelos.append(f"Isolation Forest {f['versao_modelo']}: escore {f['score']} contra limiar {f['limiar']}"
                       + (" (combinação fora do padrão)" if f["anomalo"] else ""))
    return dict(conduta=s.get("texto"), confianca=s.get("confianca"), versao_modelo=s.get("versao_modelo"),
                evidencias=s.get("evidencias", []), alternativa=s.get("alternativa"),
                protocolo=s.get("protocolo"), modelos=modelos, aviso=AVISO)


def redigir(pergunta: str, contexto: str) -> dict:
    """Passa a resposta pelo LLM local, se houver. Devolve o texto (ou None), os tokens
    contados pelo Ollama e o motivo quando fica o texto das regras."""
    modelo = os.environ.get("COSMO_MODELO", "llama3.2:3b")
    if os.environ.get("COSMO_OLLAMA", "1") == "0":
        return dict(texto=None, modelo=modelo, motivo="Ollama desligado (COSMO_OLLAMA=0)")
    corpo = json.dumps(dict(model=modelo, stream=False,
                            prompt=("Você é a Cosmo, assistente de saúde a bordo. Responda em português, em até 3 frases, "
                                    "usando só o contexto. Você não decide nada: quem decide é um humano.\n\n"
                                    f"Contexto:\n{contexto}\n\nPergunta: {pergunta}\nResposta:"))).encode()
    limite = float(os.environ.get("COSMO_TIMEOUT", "1.5"))
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=corpo, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=limite) as r:
            j = json.loads(r.read())
        return dict(texto=j["response"].strip(), modelo=modelo, tokens_entrada=j.get("prompt_eval_count"),
                    tokens_saida=j.get("eval_count"), motivo=None)
    except Exception as e:
        motivo = "Ollama não respondeu" + (f" em {limite:g} s" if "timed out" in str(e) else " (não está rodando)")
        return dict(texto=None, modelo=modelo, motivo=motivo)
