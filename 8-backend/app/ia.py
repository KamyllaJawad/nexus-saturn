"""ia.py · M1, M2 e M3 numa função só: `analisar(leitura)`.

- M2 `qualidade`: o trecho de sinal do relógio é bom ou suspeito? Suspeito segura o M1.
- M1 `arritmia-borda`: Random Forest sobre atributos de RR (normal, fa, outro).
- M3 z: mediana e MAD de cada tripulante, por sinal -> faixa e estado de três níveis.
- M3 floresta: Isolation Forest por tripulante -> combinação fora do padrão.
- Ciclo: contagem de dias da ficha de solo (regra, não é modelo treinado).

Este módulo não muda estado de evento nenhum. Quem decide é o motor (ADR-002).
Modelos em modo sombra rodam em paralelo e só são comparados (ADR-010).
"""
import csv
import json
from collections import defaultdict, deque
from datetime import date, datetime

import joblib
import numpy as np

from . import sinais
from .config import BRONZE, FS, MODELOS, PISO_MAD, SINAIS_IF, TRIPULACAO


# Direção que preocupa em cada sinal: SpO2 e HRV só para baixo.
DIRECAO = dict(fc=0, hrv=-1, spo2=-1, temp_pele=0, respiracao=0)
Z_ATENCAO, Z_CRITICO = 3.5, 7.0
NOME_METRICA = dict(fc="fc", hrv="hrv", spo2="spo2", temp_pele="temperatura", respiracao="respiracao")

_ativos: dict = {}
_sombra: dict = {}
_placar_sombra = defaultdict(lambda: dict(leituras=0, concordam=0, divergem=0, exemplos=[]))
_janelas = defaultdict(lambda: deque(maxlen=30))
_ficha: dict = {}


# ------------------------------------------------------------------ registro
def _registro() -> dict:
    caminho = MODELOS / "registro.json"
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {"ativos": {}, "sombra": {}}


def carregar():
    """Lê os artefatos em serviço e os candidatos em modo sombra."""
    _ativos.clear(); _sombra.clear()
    reg = _registro()
    for peca, arq in reg["ativos"].items():
        _ativos[peca] = joblib.load(MODELOS / arq)
    for peca, arq in reg["sombra"].items():
        _sombra[peca] = joblib.load(MODELOS / arq)
    _ficha.clear()
    with open(BRONZE / "sintetico" / "ficha.csv", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            _ficha[linha["tripulante_id"]] = linha
    return {p: m["versao"] for p, m in _ativos.items()}


def versoes() -> dict:
    return dict(ativos={p: m["versao"] for p, m in _ativos.items()},
                sombra={p: m["versao"] for p, m in _sombra.items()})


def placar_sombra() -> dict:
    return {p: dict(versao=_sombra[p]["versao"], **{k: v for k, v in _placar_sombra[p].items()})
            for p in _sombra}


def zerar_sombra(peca: str):
    _placar_sombra.pop(peca, None)


# ------------------------------------------------------------------ inferência rápida
# A bordo cada leitura é uma linha só. O scikit-learn despacha uma tarefa do joblib
# por árvore, o que custa dezenas de ms por chamada; aqui as árvores são percorridas
# direto. O resultado é o mesmo (conferido em testes/test_modelos.py) e, se a
# estrutura interna mudar numa versão futura, vale o caminho padrão do scikit-learn.
def proba(modelo, X) -> np.ndarray:
    try:
        X32 = np.ascontiguousarray(X, dtype=np.float32)
        soma = 0.0
        for arvore in modelo.estimators_:
            v = arvore.tree_.value[arvore.tree_.apply(X32)][:, 0, :]
            soma = soma + v / v.sum(axis=1, keepdims=True)
        return soma / len(modelo.estimators_)
    except AttributeError:
        return modelo.predict_proba(X)


def escore_floresta(pipeline, E) -> np.ndarray:
    """-score_samples do pipeline RobustScaler + IsolationForest."""
    try:
        escala, floresta = pipeline.steps[0][1], pipeline.steps[-1][1]
        X32 = np.ascontiguousarray(escala.transform(E), dtype=np.float32)
        prof = np.zeros(len(X32))
        for arvore, caminho, media in zip(floresta.estimators_, floresta._decision_path_lengths,
                                          floresta._average_path_length_per_tree):
            folhas = arvore.tree_.apply(X32)
            prof += caminho[folhas] + media[folhas] - 1.0
        from sklearn.ensemble._iforest import _average_path_length
        denom = len(floresta.estimators_) * _average_path_length(np.array([floresta._max_samples]))
        return 2.0 ** (-prof / denom)
    except (AttributeError, ImportError):
        return -pipeline.score_samples(E)


# ------------------------------------------------------------------ M2 e M1
def _m2(modelo, ecg) -> dict:
    atr = sinais.atributos_qualidade(ecg)
    x = np.array([[atr[k] for k in modelo["atributos"]]])
    p = float(proba(modelo["modelo"], x)[0, 1])  # probabilidade de suspeito
    suspeito = p >= modelo["limiar"]
    motivo = None
    if suspeito:
        if atr["fracao_achatada"] > 0.2:
            motivo = "sinal achatado: o sensor perdeu contato"
        elif atr["potencia_baixa_freq"] > 0.5:
            motivo = "deriva de linha de base"
        else:
            motivo = "artefato de movimento"
    return dict(qualidade="suspeito" if suspeito else "bom",
                confianca=round(p if suspeito else 1 - p, 2), motivo=motivo,
                versao_modelo=modelo["versao"], _atributos=atr)


def _m1(modelo, ecg) -> dict:
    picos = sinais.picos_r(ecg)
    atr = sinais.atributos_rr(np.diff(picos) / FS)
    nomes = modelo["atributos"]
    x = np.array([[atr[k] for k in nomes]])
    classes = list(modelo["modelo"].classes_)
    probs = proba(modelo["modelo"], x)[0]
    p_fa = float(probs[classes.index("fa")])
    if p_fa >= modelo["limiar_fa"]:
        classe = "fa"
    else:
        resto = [(p, c) for p, c in zip(probs, classes) if c != "fa"]
        classe = max(resto)[1]
    saida = dict(classe=classe, confianca=round(p_fa if classe == "fa" else float(max(probs)), 2),
                 prob_fa=round(p_fa, 3), versao_modelo=modelo["versao"], atributos=[],
                 fc_ecg=round(atr["fc_media"]), _atributos=atr)
    if classe == "fa":
        # Explicação: troca cada atributo pela mediana do treino e mede quanto a
        # probabilidade de FA cai. Ficam os 3 que mais pesaram nesta leitura.
        lote = np.repeat(x, len(nomes), axis=0)
        for i, k in enumerate(nomes):
            lote[i, i] = modelo["medianas"][k]
        queda = p_fa - proba(modelo["modelo"], lote)[:, classes.index("fa")]
        saida["atributos"] = [nomes[i] for i in np.argsort(-queda)[:3]]
    return saida


# ------------------------------------------------------------------ M3
def _faixa(sinal: str, z: float) -> str:
    d = DIRECAO[sinal]
    grave = abs(z) if d == 0 else max(0.0, -z if d < 0 else z)
    return "critico" if grave >= Z_CRITICO else "atencao" if grave >= Z_ATENCAO else "padrao"


def _m3_z(modelo, leitura) -> dict:
    base = modelo["tripulantes"][leitura["tripulante_id"]]
    metricas = {}
    for sinal in SINAIS_IF:
        if leitura.get(sinal) is None:
            continue
        mad = max(base[sinal]["mad"], PISO_MAD[sinal])
        z = 0.6745 * (leitura[sinal] - base[sinal]["mediana"]) / mad
        metricas[NOME_METRICA[sinal]] = dict(z=round(z, 1), faixa=_faixa(sinal, z))
    p = TRIPULACAO[leitura["tripulante_id"]]
    if leitura.get("sono_min_noite") is not None:
        z = 0.6745 * (leitura["sono_min_noite"] - p["sono_base"]) / 30.0
        metricas["sono"] = dict(z=round(z, 1), faixa="critico" if z <= -3.5 else "atencao" if z <= -1.5 else "padrao")
    if leitura.get("agua_ml_dia") is not None:
        fr = leitura["agua_ml_dia"] / p["agua_meta"]
        z = (fr - 0.85) / 0.15
        metricas["hidratacao"] = dict(z=round(z, 1), faixa="critico" if fr < 0.4 else "atencao" if fr < 0.7 else "padrao")
    return metricas


def _estado(metricas: dict) -> tuple:
    crit = sum(1 for m in metricas.values() if m["faixa"] == "critico")
    aten = sum(1 for m in metricas.values() if m["faixa"] == "atencao")
    vital = any(metricas.get(k, {}).get("faixa") == "atencao" for k in ("fc", "spo2", "respiracao"))
    estado = "critico" if crit else "atencao" if (vital or aten >= 3) else "otimo"
    return estado, max(12, 100 - 3 * aten - 15 * crit)


def _vetor(leitura) -> np.ndarray:
    return np.array([[float(leitura[s]) for s in SINAIS_IF]])


_seguidas = defaultdict(int)  # (versão, tripulante) -> leituras seguidas acima do limiar


def _m3_if(modelo, leitura) -> dict:
    """`anomalo` só fica verdadeiro depois de `persistencia` leituras seguidas
    acima do limiar. A evidência troca cada sinal pela mediana da pessoa e fica
    com os que mais reduzem o escore."""
    tid = leitura["tripulante_id"]
    m = modelo["tripulantes"][tid]
    med, mad = np.array(m["mediana"]), np.array(m["mad"])
    x = _vetor(leitura)
    score = float(escore_floresta(m["pipeline"], sinais.expandir_if(x, med, mad))[0])
    acima = score > m["limiar"]
    chave = (modelo["versao"], tid)
    _seguidas[chave] = _seguidas[chave] + 1 if acima else 0
    evidencias = []
    if acima:
        lote = np.repeat(x, len(SINAIS_IF), axis=0)
        for i in range(len(SINAIS_IF)):
            lote[i, i] = med[i]
        queda = score - escore_floresta(m["pipeline"], sinais.expandir_if(lote, med, mad))
        evidencias = [NOME_METRICA[SINAIS_IF[i]] for i in np.argsort(-queda)[:3] if queda[i] > 0.005]
    return dict(anomalo=bool(_seguidas[chave] >= m["persistencia"]), score=round(score, 3),
                limiar=round(m["limiar"], 3), acima_do_limiar=bool(acima), seguidas=_seguidas[chave],
                persistencia=m["persistencia"], evidencias=evidencias, versao_modelo=modelo["versao"])


# ------------------------------------------------------------------ ciclo
def _ciclo(tid: str, hoje: date, metricas: dict, m2_bom: bool, estado: str, leitura: dict):
    ficha = _ficha.get(tid, {})
    if ficha.get("calendario") != "true":
        return None
    dur = int(ficha["duracao_tipica_dias"])
    dia = (hoje - date.fromisoformat(ficha["ultima_menstruacao"])).days % dur + 1
    inicio_intenso = dur - 6  # "segunda_quinzena": os 7 últimos dias do calendário de solo
    # Sinais leves: mediana móvel do z, para o ruído de uma leitura não contar.
    jan = _janelas[tid]
    med = {k: float(np.median([j[k] for j in jan])) for k in ("fc", "temperatura", "hrv")} if jan else {}
    leves = [k for k, ok in (("fc", med.get("fc", 0) >= 1.0), ("temperatura", med.get("temperatura", 0) >= 1.0),
                             ("hrv", med.get("hrv", 0) <= -1.5),
                             ("sono", metricas.get("sono", {}).get("z", 0) <= -0.8)) if ok]
    na_janela = dia >= inicio_intenso - 2
    ajustada = False
    if not na_janela and ficha["metodo"] == "nenhum" and dia >= inicio_intenso - 5 and {"fc", "temperatura"} <= set(leves):
        na_janela = ajustada = True  # sem supressão, FC e temperatura adiantam a janela
    sugestoes = ["respirar", "treino_leve", "modo_noite"]
    if metricas.get("hidratacao", {}).get("faixa") != "padrao":
        sugestoes.append("agua")
    return dict(na_janela=na_janela, aviso_dias=max(0, inicio_intenso - dia), dia_do_calendario=dia,
                sinais_leves=leves, janela_ajustada=ajustada,
                perguntar=bool(na_janela and len(leves) >= 2 and m2_bom and estado != "critico"),
                sugestoes=sugestoes, compartilhado=False, versao="ciclo-calendario-0.1")


def ficha_de(tid: str) -> dict:
    f = _ficha.get(tid, {})
    saida = dict(sexo=f.get("sexo"), calendario=f.get("calendario") == "true", versao_ficha=f.get("versao_ficha"))
    if saida["calendario"]:
        saida.update(metodo=f["metodo"], ultima_menstruacao=f["ultima_menstruacao"],
                     duracao_tipica_dias=int(f["duracao_tipica_dias"]), trecho_intenso=f["trecho_intenso"])
    return saida


# ------------------------------------------------------------------ análise
def analisar(leitura: dict) -> dict:
    """Recebe uma leitura (sinais do minuto + trecho de ECG opcional) e devolve a
    análise no formato de 4-arquitetura/contratos/exemplos/analise-*.json."""
    if not _ativos:
        carregar()
    tid = leitura["tripulante_id"]
    ecg = leitura.get("ecg")
    m1 = m2 = None
    if ecg is not None:
        m2 = _m2(_ativos["m2"], ecg)
        if m2["qualidade"] == "bom":
            m1 = _m1(_ativos["m1"], ecg)
        else:
            m1 = dict(classe=None, confianca=0.0, prob_fa=None, atributos=[],
                      versao_modelo=_ativos["m1"]["versao"], motivo="sinal suspeito: o M1 não dispara")
    metricas = _m3_z(_ativos["m3-z"], leitura)
    estado, homeostase = _estado(metricas)
    _janelas[tid].append({k: metricas[k]["z"] for k in ("fc", "temperatura", "hrv") if k in metricas})
    floresta = _m3_if(_ativos["m3-if"], leitura)
    m2_bom = m2 is None or m2["qualidade"] == "bom"
    if not m2_bom and estado != "otimo":
        estado = "suspeito"
    hoje = datetime.fromisoformat(leitura["gerada_em"].replace("Z", "+00:00")).date()
    ciclo = _ciclo(tid, hoje, metricas, m2_bom, estado, leitura)

    # Modo sombra: o candidato roda na mesma leitura e só é comparado.
    sombra = {}
    if "m3-if" in _sombra:
        cand = _m3_if(_sombra["m3-if"], leitura)
        _comparar("m3-if", floresta["anomalo"], cand["anomalo"], tid, leitura["gerada_em"])
        sombra["m3-if"] = dict(anomalo=cand["anomalo"], score=cand["score"], limiar=cand["limiar"], versao_modelo=cand["versao_modelo"])
    if ecg is not None and "m2" in _sombra:
        cand = _m2(_sombra["m2"], ecg)
        _comparar("m2", m2["qualidade"], cand["qualidade"], tid, leitura["gerada_em"])
        sombra["m2"] = dict(qualidade=cand["qualidade"], versao_modelo=cand["versao_modelo"])
    if ecg is not None and m2_bom and "m1" in _sombra:
        cand = _m1(_sombra["m1"], ecg)
        _comparar("m1", m1["classe"], cand["classe"], tid, leitura["gerada_em"])
        sombra["m1"] = dict(classe=cand["classe"], prob_fa=cand["prob_fa"], versao_modelo=cand["versao_modelo"])

    return dict(tripulante_id=tid, gerada_em=leitura["gerada_em"], ficha=ficha_de(tid), m1=m1, m2=m2,
                m3=dict(estado=estado, homeostase=homeostase, versao_z=_ativos["m3-z"]["versao"],
                        metricas=metricas, isolation_forest=floresta),
                ciclo=ciclo, sombra=sombra)


def _comparar(peca, ativo, candidato, tid, quando):
    p = _placar_sombra[peca]
    p["leituras"] += 1
    if ativo == candidato:
        p["concordam"] += 1
    else:
        p["divergem"] += 1
        if len(p["exemplos"]) < 8:
            p["exemplos"].append(dict(tripulante_id=tid, quando=quando, ativo=str(ativo), candidato=str(candidato)))
