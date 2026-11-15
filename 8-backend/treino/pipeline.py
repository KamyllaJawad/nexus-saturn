"""Lakehouse do protótipo e treino em lote: bronze -> prata -> ouro -> modelos/.

Uso (na pasta 8-backend):
    python -m treino.pipeline            # trata os dados e treina M1, M2 e M3
    python -m treino.pipeline --sem-cinc # força o ECG sintético (sem o zip do CinC)

Cada job lê uma tabela de ouro, grava um artefato com versão e registra o lote.
Nada aqui roda a cada leitura: a bordo, o `ia.analisar` só usa os artefatos.
"""
import csv
import io
import json
import sys
import time
import zipfile
from datetime import datetime, timezone

import joblib
import numpy as np
from scipy.io import loadmat
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler

from app import sinais
from app.config import BRONZE, FS, JANELA_S, MODELOS, ORDEM, OURO, PISO_MAD, PRATA, SINAIS_IF, TREINO

SEMENTE = 20261114
CLASSES_CINC = {"N": "normal", "A": "fa", "O": "outro", "~": "ruidoso"}
FAIXA_FISICA = dict(fc=(25, 230), hrv=(3, 250), spo2=(60, 100), temp_pele=(30, 42), respiracao=(4, 50))


def _agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _csv(caminho, linhas, campos=None):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos or list(linhas[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(linhas)
    return len(linhas)


def _ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# =============================================================== bronze -> prata
def tratar_vitais():
    """Confere unidade e faixa física; fora da faixa a linha fica na prata como
    suspeita e não segue para o ouro. Monta o ouro do M3 só com minutos normais."""
    bruto = _ler(BRONZE / "sintetico" / "vitais_minuto.csv")
    prata, ouro = [], []
    for l in bruto:
        for sinal, (lo, hi) in FAIXA_FISICA.items():
            if not lo <= float(l[sinal]) <= hi:
                l["qualidade"] = "suspeito"
        prata.append(l)
        # O trecho do ciclo fica fora do treino da floresta: ele carrega um desvio
        # injetado, e quem explica essa janela é o calendário da ficha (ADR-013).
        if l["qualidade"] == "bom" and l["excluir_treino_if"] == "false" and l["cenario"] != "ciclo":
            ouro.append({k: l[k] for k in ["minuto_utc", "tripulante_id", *SINAIS_IF]})
    _csv(PRATA / "vitais.csv", prata)
    _csv(OURO / "m3_vitais_normais.csv", ouro)
    return dict(bronze=len(bruto), prata=len(prata), ouro=len(ouro),
                suspeitas=sum(1 for l in prata if l["qualidade"] == "suspeito"))


def _registros_cinc():
    """Lê o zip do CinC 2017 (bronze) e devolve (id, classe, ecg em mV)."""
    with zipfile.ZipFile(BRONZE / "cinc2017" / "training2017.zip") as z:
        ref = z.read("training2017/REFERENCE.csv").decode().strip().splitlines()
        for linha in ref:
            rid, rotulo = linha.split(",")
            mat = loadmat(io.BytesIO(z.read(f"training2017/{rid}.mat")))
            yield rid, CLASSES_CINC[rotulo], mat["val"][0].astype(np.float32) / 1000.0


def _registros_sinteticos(n=2400):
    """Plano B sem o zip: ECG sintético com as mesmas quatro classes."""
    rng = np.random.default_rng(SEMENTE)
    for i in range(n):
        classe = rng.choice(["normal", "fa", "outro", "ruidoso"], p=[0.6, 0.12, 0.25, 0.03])
        fc = rng.uniform(95, 165) if classe == "fa" else rng.uniform(50, 100)
        base = "normal" if classe == "ruidoso" else classe
        ecg = sinais.ecg_sintetico(sinais.rr_sintetico(base, JANELA_S, fc, rng), fa=classe == "fa", rng=rng)
        if classe == "ruidoso":
            ecg = sinais.sujar(ecg, rng)
        yield f"S{i:05d}", classe, ecg.astype(np.float32)


def tratar_ecg(usar_cinc=True):
    """Atributos de RR e de qualidade por gravação, split 70/15/15 por gravação,
    ruído sintético para o M2 e o banco de trechos de teste que o simulador toca."""
    tem_zip = (BRONZE / "cinc2017" / "training2017.zip").exists()
    origem = "cinc" if (usar_cinc and tem_zip) else "sintetico"
    rng = np.random.default_rng(SEMENTE)
    linhas, guardados = [], {}
    for rid, classe, ecg in (_registros_cinc() if origem == "cinc" else _registros_sinteticos()):
        rr = np.diff(sinais.picos_r(ecg)) / FS
        linhas.append(dict(id=rid, classe=classe, segundos=round(len(ecg) / FS, 1),
                           **sinais.atributos_rr(rr), **sinais.atributos_qualidade(ecg)))
        if len(ecg) >= JANELA_S * FS and classe in ("normal", "fa"):
            guardados[rid] = ecg[: JANELA_S * FS]
    ids = [l["id"] for l in linhas]
    classes = [l["classe"] for l in linhas]
    treino, resto = train_test_split(ids, test_size=0.30, stratify=classes, random_state=SEMENTE)
    cl_resto = [classes[ids.index(i)] for i in resto] if len(ids) < 4000 else None
    if cl_resto is None:
        mapa = dict(zip(ids, classes)); cl_resto = [mapa[i] for i in resto]
    val, teste = train_test_split(resto, test_size=0.50, stratify=cl_resto, random_state=SEMENTE)
    split = {**{i: "treino" for i in treino}, **{i: "validacao" for i in val}, **{i: "teste" for i in teste}}
    for l in linhas:
        l["split"] = split[l["id"]]
    _csv(PRATA / "ecg_atributos.csv", linhas)

    # Ouro do M1: só gravações limpas (o ruidoso é assunto do M2).
    _csv(OURO / "m1_rr.csv", [{k: l[k] for k in ["id", "classe", "split", *sinais.ATRIBUTOS_RR]}
                              for l in linhas if l["classe"] != "ruidoso"])

    # Ouro do M2: gravações limpas = bom; ruidosas reais + ruído injetado = suspeito.
    ouro_m2 = [dict(id=l["id"], rotulo="suspeito" if l["classe"] == "ruidoso" else "bom", split=l["split"],
                    origem_ruido="real" if l["classe"] == "ruidoso" else "",
                    **{k: l[k] for k in sinais.ATRIBUTOS_QUALIDADE}) for l in linhas]
    limpos = [rid for rid in guardados if split[rid] in ("treino", "validacao", "teste")]
    for rid in rng.choice(limpos, size=min(2000, len(limpos)), replace=False):
        sujo = sinais.sujar(guardados[rid], rng)
        ouro_m2.append(dict(id=f"{rid}-ruido", rotulo="suspeito", split=split[rid], origem_ruido="sintetico",
                            **sinais.atributos_qualidade(sujo)))
    _csv(OURO / "m2_qualidade.csv", ouro_m2)

    # Banco do simulador: só gravações do TESTE, que nenhum modelo viu no treino.
    por_id = {l["id"]: l for l in linhas}
    banco_ids = [rid for rid in guardados if split[rid] == "teste"
                 and por_id[rid]["regularidade_picos"] > 0.9 and por_id[rid]["fracao_achatada"] < 0.03]
    normais = [r for r in banco_ids if por_id[r]["classe"] == "normal" and por_id[r]["rr_irregular_30s"] < 0.08]
    fas = sorted((r for r in banco_ids if por_id[r]["classe"] == "fa" and por_id[r]["fc_media"] >= 100),
                 key=lambda r: -por_id[r]["fc_media"])[:30]
    normais = list(rng.choice(normais, size=min(60, len(normais)), replace=False))
    escolhidos = normais + fas
    TREINO.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(TREINO / "banco_ecg.npz",
                        ecg=np.array([guardados[r] for r in escolhidos], dtype=np.float32),
                        ids=np.array(escolhidos), classes=np.array([por_id[r]["classe"] for r in escolhidos]),
                        fc=np.array([por_id[r]["fc_media"] for r in escolhidos], dtype=np.float32))
    contagem = {c: classes.count(c) for c in sorted(set(classes))}
    return dict(origem=origem, gravacoes=len(linhas), classes=contagem,
                split={s: sum(1 for v in split.values() if v == s) for s in ("treino", "validacao", "teste")},
                ouro_m1=sum(1 for l in linhas if l["classe"] != "ruidoso"), ouro_m2=len(ouro_m2),
                banco_simulador=dict(normal=len(normais), fa=len(fas)))


# =============================================================== treino
def _xy(linhas, atributos, alvo, split):
    sel = [l for l in linhas if l["split"] == split]
    return np.array([[float(l[k]) for k in atributos] for l in sel]), np.array([l[alvo] for l in sel])


def treinar_m1(versao="arritmia-borda-0.3", rotulos_humanos=None, lote=None):
    """Random Forest sobre atributos de RR. O limiar de FA sai da validação;
    a métrica do pitch é o F1 da classe FA no teste, nunca só a acurácia."""
    linhas = _ler(OURO / "m1_rr.csv")
    atr = sinais.ATRIBUTOS_RR
    Xt, yt = _xy(linhas, atr, "classe", "treino")
    Xv, yv = _xy(linhas, atr, "classe", "validacao")
    Xs, ys = _xy(linhas, atr, "classe", "teste")
    peso = np.ones(len(yt))
    n_humanos = 0
    if rotulos_humanos:
        Xh = np.array([[float(r["atributos"][k]) for k in atr] for r in rotulos_humanos])
        yh = np.array([r["rotulo"] for r in rotulos_humanos])
        Xt, yt = np.vstack([Xt, Xh]), np.concatenate([yt, yh])
        peso = np.concatenate([peso, np.full(len(yh), 5.0)])  # rótulo humano de bordo pesa mais
        n_humanos = len(yh)
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced",
                                random_state=SEMENTE, n_jobs=-1).fit(Xt, yt, sample_weight=peso)
    rf.n_jobs = 1
    i_fa = list(rf.classes_).index("fa")
    pv = rf.predict_proba(Xv)[:, i_fa]
    limiar = max(np.arange(0.20, 0.81, 0.02), key=lambda t: f1_score(yv == "fa", pv >= t))

    def prever(X):
        proba = rf.predict_proba(X)
        resto = proba.copy(); resto[:, i_fa] = -1
        return np.where(proba[:, i_fa] >= limiar, "fa", rf.classes_[resto.argmax(axis=1)])

    pred = prever(Xs)
    rot = list(rf.classes_)
    prec, rec, f1, sup = precision_recall_fscore_support(ys, pred, labels=rot, zero_division=0)
    # Intervalo do F1 por reamostragem do teste: são poucas FAs, e o número oscila.
    rb = np.random.default_rng(SEMENTE)
    amostras = [f1_score(ys[i] == "fa", pred[i] == "fa", zero_division=0)
                for i in (rb.integers(0, len(ys), len(ys)) for _ in range(300))]
    metricas = dict(f1_fa=round(float(f1[i_fa]), 3),
                    f1_fa_ic95=[round(float(np.percentile(amostras, 2.5)), 3), round(float(np.percentile(amostras, 97.5)), 3)],
                    f1_fa_validacao=round(float(f1_score(yv == "fa", pv >= limiar)), 3),
                    precisao_fa=round(float(prec[i_fa]), 3),
                    recall_fa=round(float(rec[i_fa]), 3), limiar_fa=round(float(limiar), 2),
                    acuracia=round(float((pred == ys).mean()), 3),
                    por_classe={c: dict(precisao=round(float(prec[i]), 3), recall=round(float(rec[i]), 3),
                                        f1=round(float(f1[i]), 3), n=int(sup[i])) for i, c in enumerate(rot)},
                    matriz_confusao=dict(rotulos=rot, valores=confusion_matrix(ys, pred, labels=rot).tolist()),
                    importancias=dict(sorted(zip(atr, np.round(rf.feature_importances_, 3).tolist()), key=lambda kv: -kv[1])),
                    meta="F1 da classe FA >= 0,75 no teste", bateu_meta=bool(f1[i_fa] >= 0.75),
                    n_treino=int(len(yt)), n_validacao=int(len(yv)), n_teste=int(len(ys)), rotulos_humanos=n_humanos)
    art = dict(peca="m1", versao=versao, modelo=rf, atributos=atr, limiar_fa=float(limiar),
               medianas={k: float(np.median(Xt[:, i])) for i, k in enumerate(atr)},
               metricas=metricas, lote=lote, treinado_em=_agora(), algoritmo="RandomForestClassifier(300, balanced)")
    return art


def treinar_m2(versao="qualidade-0.2", rotulos_humanos=None, lote=None):
    """O estimador estava em aberto no plano: aqui a escolha é medida. Treina
    regressão logística e Random Forest e fica com quem dá mais precisão na
    validação mantendo o recall de `suspeito` em pelo menos 0,9."""
    linhas = _ler(OURO / "m2_qualidade.csv")
    atr = sinais.ATRIBUTOS_QUALIDADE
    Xt, yt = _xy(linhas, atr, "rotulo", "treino")
    Xv, yv = _xy(linhas, atr, "rotulo", "validacao")
    Xs, ys = _xy(linhas, atr, "rotulo", "teste")
    yt, yv, ys = (yt == "suspeito").astype(int), (yv == "suspeito").astype(int), (ys == "suspeito").astype(int)
    peso = np.ones(len(yt)); n_humanos = 0
    if rotulos_humanos:
        Xh = np.array([[float(r["atributos"][k]) for k in atr] for r in rotulos_humanos])
        yh = np.array([1 if r["rotulo"] == "suspeito" else 0 for r in rotulos_humanos])
        Xt, yt = np.vstack([Xt, Xh]), np.concatenate([yt, yh])
        peso = np.concatenate([peso, np.full(len(yh), 5.0)]); n_humanos = len(yh)
    candidatos = {
        "regressao_logistica": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
        "random_forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=2, class_weight="balanced",
                                                random_state=SEMENTE, n_jobs=-1),
    }
    comparacao, melhor = {}, None
    for nome, est in candidatos.items():
        if nome == "random_forest":
            est.fit(Xt, yt, sample_weight=peso); est.n_jobs = 1
        else:
            est.fit(Xt, yt, logisticregression__sample_weight=peso)
        pv = est.predict_proba(Xv)[:, 1]
        # maior limiar que ainda mantém recall >= 0,93 na validação (folga sobre a meta de 0,9)
        limiar = 0.5
        for t in np.arange(0.90, 0.04, -0.01):
            if ((pv >= t) & (yv == 1)).sum() / max(1, yv.sum()) >= 0.93:
                limiar = float(t); break
        pred_v = pv >= limiar
        precisao_v = float((pred_v & (yv == 1)).sum() / max(1, pred_v.sum()))
        comparacao[nome] = dict(limiar=round(limiar, 2), precisao_validacao=round(precisao_v, 3))
        if melhor is None or precisao_v > melhor[2]:
            melhor = (nome, est, precisao_v, limiar)
    nome, est, _, limiar = melhor
    pred = (est.predict_proba(Xs)[:, 1] >= limiar).astype(int)
    prec, rec, f1, sup = precision_recall_fscore_support(ys, pred, labels=[0, 1], zero_division=0)
    metricas = dict(recall_suspeito=round(float(rec[1]), 3), precisao_suspeito=round(float(prec[1]), 3),
                    f1_suspeito=round(float(f1[1]), 3), falso_suspeito_em_bom=round(float(1 - rec[0]), 3),
                    limiar=round(limiar, 2), estimador_escolhido=nome, comparacao=comparacao,
                    matriz_confusao=dict(rotulos=["bom", "suspeito"], valores=confusion_matrix(ys, pred, labels=[0, 1]).tolist()),
                    meta="recall de suspeito >= 0,9 no teste", bateu_meta=bool(rec[1] >= 0.9),
                    n_treino=int(len(yt)), n_teste=int(len(ys)), rotulos_humanos=n_humanos)
    return dict(peca="m2", versao=versao, modelo=est, atributos=atr, limiar=limiar, metricas=metricas,
                lote=lote, treinado_em=_agora(), algoritmo=nome)


def _vitais_por_pessoa():
    por = {t: [] for t in ORDEM}
    for l in _ler(OURO / "m3_vitais_normais.csv"):
        por[l["tripulante_id"]].append([float(l[s]) for s in SINAIS_IF])
    return {t: np.array(v) for t, v in por.items()}


def treinar_m3_z(versao="m3-z-0.1", lote=None):
    trip = {}
    for t, X in _vitais_por_pessoa().items():
        med = np.median(X, axis=0)
        mad = np.median(np.abs(X - med), axis=0)
        trip[t] = {s: dict(mediana=float(med[i]), mad=float(mad[i])) for i, s in enumerate(SINAIS_IF)}
    return dict(peca="m3-z", versao=versao, tripulantes=trip, lote=lote, treinado_em=_agora(),
                algoritmo="mediana e MAD por tripulante", metricas=dict(sinais=SINAIS_IF, n_por_tripulante={t: int(len(X)) for t, X in _vitais_por_pessoa().items()}))


def _floresta():
    return make_pipeline(RobustScaler(), IsolationForest(n_estimators=200, random_state=SEMENTE))


PERSISTENCIA = 5  # leituras seguidas acima do limiar para a combinação contar como anomalia
PASSO_ANOMALIA = np.array([4.0, -7.0, -1.5, 0.2, 2.0])  # fc, hrv, spo2, temp, resp


def _anomalias_injetadas(X, rng, n_sinais, n=300):
    """Desvio combinado e sustentado em `n_sinais` sinais, a partir da mediana da
    pessoa, do tamanho que o z robusto sozinho não classifica como atenção."""
    med = np.median(X, axis=0)
    A = med + (X[rng.integers(0, len(X), n)] - med) * 0.3
    for a in A:
        quais = rng.choice(len(PASSO_ANOMALIA), size=n_sinais, replace=False)
        a[quais] += PASSO_ANOMALIA[quais] * rng.uniform(1.0, 1.6, size=n_sinais)
    return A


def _sequencias(acima, k: int) -> int:
    """Quantas vezes o escore fica k leituras seguidas acima do limiar."""
    n = seq = 0
    for v in acima:
        seq = seq + 1 if v else 0
        if seq == k:
            n += 1
    return n


def treinar_m3_if(versao="m3-if-0.1", rotulos_humanos=None, lote=None):
    """Um Isolation Forest por tripulante, só com minutos normais.

    Entram os 5 sinais e o desvio conjunto (soma dos |z| robustos). O alarme pede
    PERSISTENCIA leituras seguidas acima do limiar, e o limiar é o menor escore
    fora-da-amostra (4 blocos no tempo) que cabe em no máximo 1 alarme por pessoa
    por dia simulado.
    Rótulo humano "normal" (falso alarme) entra no treino; rótulo "anomalia"
    (confirmado) nunca entra e serve de teto para o limiar."""
    rng = np.random.default_rng(SEMENTE)
    trip, met = {}, {}
    for t, X in _vitais_por_pessoa().items():
        med = np.median(X, axis=0)
        mad = np.maximum(np.median(np.abs(X - med), axis=0), [PISO_MAD[s] for s in SINAIS_IF])
        E = sinais.expandir_if(X, med, mad)
        hum = [r for r in (rotulos_humanos or []) if r["tripulante_id"] == t]
        normais_h = np.array([r["vetor"] for r in hum if r["rotulo"] == "normal"])
        confirm_h = np.array([r["vetor"] for r in hum if r["rotulo"] == "anomalia"])
        fora = np.zeros(len(X))
        for b in np.array_split(np.arange(len(X)), 4):
            resto = np.setdiff1d(np.arange(len(X)), b)
            fora[b] = -_floresta().fit(E[resto]).score_samples(E[b])
        dias = len(X) / 1440.0
        limiar = float(fora.max()) + 1e-4
        for q in np.arange(0.80, 1.0, 0.005):
            cand = float(np.quantile(fora, q))
            if _sequencias(fora > cand, PERSISTENCIA) / dias <= 1.0:
                limiar = cand
                break
        Efinal = E
        if len(normais_h):
            # O humano disse que esse padrão é dele: entra no treino como região normal,
            # com peso de ~20% do conjunto e um pouco do ruído de rotina em volta.
            # O limiar NÃO é empurrado para cima: se fosse, o modelo ficaria cego.
            # Poucos segundos rotulados não cobrem a oscilação do sinal: o padrão vira o
            # centro rotulado mais o ruído de rotina da própria pessoa.
            n_rep = max(600, len(X) // 5)
            rep = np.median(normais_h, axis=0) + 1.25 * (X[rng.integers(0, len(X), n_rep)] - med)
            Efinal = np.vstack([E, sinais.expandir_if(rep, med, mad)])
        pipe = _floresta().fit(Efinal)
        escore = lambda V: -pipe.score_samples(sinais.expandir_if(V, med, mad))
        if len(confirm_h):
            limiar = min(limiar, float(escore(confirm_h).min()) - 1e-3)
        trip[t] = dict(pipeline=pipe, limiar=limiar, persistencia=PERSISTENCIA,
                       mediana=med.tolist(), mad=mad.tolist(),
                       medianas={s: float(med[i]) for i, s in enumerate(SINAIS_IF)})
        met[t] = dict(n_treino=int(len(Efinal)), limiar=round(limiar, 3),
                      alarmes_fora_da_amostra_por_dia=round(_sequencias(fora > limiar, PERSISTENCIA) / dias, 2),
                      recall_desvio_em_2_sinais=round(float((escore(_anomalias_injetadas(X, rng, 2)) > limiar).mean()), 3),
                      recall_desvio_em_3_sinais=round(float((escore(_anomalias_injetadas(X, rng, 3)) > limiar).mean()), 3),
                      recall_desvio_em_4_sinais=round(float((escore(_anomalias_injetadas(X, rng, 4)) > limiar).mean()), 3),
                      rotulos_humanos=dict(normal=int(len(normais_h)), anomalia=int(len(confirm_h)),
                                           normais_abaixo_do_limiar=None if not len(normais_h) else round(float((escore(normais_h) <= limiar).mean()), 3),
                                           anomalias_acima_do_limiar=None if not len(confirm_h) else round(float((escore(confirm_h) > limiar).mean()), 3)))
    # Episódios que ficaram fora do treino (FA e relógio folgado) têm de ficar acima do limiar.
    eps = [l for l in _ler(PRATA / "vitais.csv") if l["excluir_treino_if"] == "true"]
    pegos = 0
    for l in eps:
        m = trip[l["tripulante_id"]]
        v = sinais.expandir_if([[float(l[s]) for s in SINAIS_IF]], np.array(m["mediana"]), np.array(m["mad"]))
        pegos += int(-m["pipeline"].score_samples(v)[0] > m["limiar"])
    metricas = dict(por_tripulante=met, persistencia=PERSISTENCIA,
                    episodios_excluidos=dict(total=len(eps), acima_do_limiar=pegos),
                    meta="no máximo 1 alarme por pessoa por dia simulado; >= 90% dos desvios combinados em 3 ou mais sinais",
                    bateu_meta=bool(all(m["alarmes_fora_da_amostra_por_dia"] <= 1 and m["recall_desvio_em_3_sinais"] >= 0.9
                                        and m["recall_desvio_em_4_sinais"] >= 0.9 for m in met.values())),
                    limitacao="Desvio em só 2 sinais fica dentro da nuvem normal da pessoa; o número medido está em recall_desvio_em_2_sinais.")
    return dict(peca="m3-if", versao=versao, tripulantes=trip, metricas=metricas, lote=lote, treinado_em=_agora(),
                algoritmo=f"RobustScaler + IsolationForest(200) por tripulante, 5 sinais + desvio conjunto, persistência de {PERSISTENCIA} leituras")


# =============================================================== registro
TREINADORES = {"m1": treinar_m1, "m2": treinar_m2, "m3-if": treinar_m3_if}


def salvar(art: dict, pasta="") -> str:
    destino = MODELOS / pasta
    destino.mkdir(parents=True, exist_ok=True)
    nome = f"{pasta + '/' if pasta else ''}{art['versao']}.joblib"
    joblib.dump(art, MODELOS / nome)
    return nome


def ler_registro() -> dict:
    c = MODELOS / "registro.json"
    return json.loads(c.read_text(encoding="utf-8")) if c.exists() else {"ativos": {}, "sombra": {}, "historico": []}


def gravar_registro(reg: dict):
    (MODELOS / "registro.json").write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def proxima_versao(versao: str) -> str:
    base, _, n = versao.rpartition(".")
    return f"{base}.{int(n) + 1}"


def principal(usar_cinc=True):
    t0 = time.time()
    lote = dict(id=f"lote-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}", criado_em=_agora())
    print("1/5 prata e ouro dos vitais sintéticos…"); lote["vitais"] = tratar_vitais(); lote["vitais"]["origem"] = "sintetico"
    print("2/5 prata e ouro do ECG (picos R, atributos, split 70/15/15)…"); lote["ecg"] = tratar_ecg(usar_cinc)
    print(f"    origem do ECG: {lote['ecg']['origem']} · {lote['ecg']['gravacoes']} gravações · {time.time() - t0:.0f} s")
    reg = dict(ativos={}, sombra={}, historico=[])
    relatorio = dict(lote=lote, modelos={})
    for i, (peca, fn) in enumerate([("m1", treinar_m1), ("m2", treinar_m2), ("m3-z", treinar_m3_z), ("m3-if", treinar_m3_if)], start=3):
        print(f"{min(i, 5)}/5 treinando {peca}…")
        art = fn(lote=lote["id"])
        reg["ativos"][peca] = salvar(art)
        reg["historico"].append(dict(versao=art["versao"], peca=peca, estado="ativo", lote=lote["id"],
                                     treinado_em=art["treinado_em"], aprovado_por="lote inicial (pré-voo)"))
        relatorio["modelos"][peca] = dict(versao=art["versao"], algoritmo=art["algoritmo"], metricas=art["metricas"])
    gravar_registro(reg)
    (MODELOS / "relatorio.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    (TREINO / "lote.json").write_text(json.dumps(lote, ensure_ascii=False, indent=2), encoding="utf-8")
    m = relatorio["modelos"]
    print(f"\nPronto em {time.time() - t0:.0f} s. Relatório em modelos/relatorio.json")
    print(f"  M1  F1 da FA no teste: {m['m1']['metricas']['f1_fa']}  (meta 0,75)")
    print(f"  M2  recall de suspeito: {m['m2']['metricas']['recall_suspeito']}  (meta 0,9) · estimador: {m['m2']['metricas']['estimador_escolhido']}")
    print(f"  M3  floresta bateu a meta: {m['m3-if']['metricas']['bateu_meta']}")
    return relatorio


if __name__ == "__main__":
    principal(usar_cinc="--sem-cinc" not in sys.argv)
