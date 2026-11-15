"""Simulador do relógio e dos sensores de bordo: uma leitura por segundo por
tripulante. Não há smartwatch real; o que é real é o caminho depois da leitura:
`ia.analisar` -> motor de decisões -> humano -> auditoria -> link.

O ruído de rotina segue o mesmo processo AR(1) do gerador dos dados de treino,
e o trecho de ECG vem de gravações do conjunto de TESTE do CinC 2017, que nenhum
modelo viu no treino. O cenário só muda o sinal; quem detecta são os modelos.
"""
import threading
from collections import deque
from datetime import datetime, timedelta, timezone

import numpy as np

from .. import ia, sinais
from ..config import EQUIPE_MEDICA, MEDICO_TERRA, MISSOES, ORDEM, RUIDO, SINAIS_IF, TREINO, TRIPULACAO, nome_de
from . import registro
from .link import Link
from .motor import Motor, Recusa

INICIO = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)  # onde os dados de treino terminam
DESVIOS = {  # o que cada cenário soma ao sinal de rotina
    "ciclo": dict(fc=3, hrv=-8, temp_pele=0.3),
    "combinacao": dict(fc=4, hrv=-7, respiracao=2, temp_pele=0.2),
}
DOSE_BASE = dict(leo=0.0002, gateway=0.0005, mars=0.0008, marsSurf=0.0003)
CANAIS = [("fc", "relogio-ppg", "bpm"), ("hrv", "relogio-ppg", "ms"), ("spo2", "relogio-oximetro", "%"),
          ("temp_pele", "relogio-termistor", "C"), ("respiracao", "patch-toracico", "irpm")]


class Simulador:
    def __init__(self, semente=20261114):
        self.trava = threading.RLock()
        self.rng = np.random.default_rng(semente)
        self.t = 0.0
        self.link = Link(self.relogio)
        self.motor = Motor(self.relogio, self.agora_iso, self.link)
        self.motor.sim = self
        self.link.ao_entregar = self._entregue
        self.medico_local = None
        self.definir_medico("bordo")
        self.decisoes_terra = []   # o que a médica de voo mandou de Houston, e o que aconteceu quando chegou
        self.decisoes_modelo = []  # aprovações de modelo vindas da Terra (ADR-017), que só valem quando chegam
        self.decidir_modelo = None # ligado pela API: hitl._decidir
        self.cabine = dict(co2=2.4, fluxo="normal", abrigo=False, luz="dia")
        self.jogo = dict(nivel=4, pct=86, xp=450, missoes=dict(treino=True, agua=False, respiracao=False),
                         corrida_km=43.6, corrida_meta=60, brinde=None)
        self.mensagens, self.historico = [], deque(maxlen=1500)
        self.retrato_antes_do_blackout = None
        self.pessoas = {}
        for tid in ORDEM:
            p = TRIPULACAO[tid]
            self.pessoas[tid] = dict(fase="rotina", fase_t=0.0, ruido={k: 0.0 for k in RUIDO}, agua=p["agua"],
                                     dose=p["dose"], hrv30=deque(maxlen=30), ecg=None, ecg_fc=None, ecg_id=None,
                                     ecg_classe=None, trecho=None,
                                     m1=None, m2=None, analise=None, leitura=None, avisos=deque(maxlen=4))
        self._carregar_banco()
        self.passo()

    # ------------------------------------------------------------ equipe médica
    def definir_medico(self, local: str) -> dict:
        """Hipótese da missão: médico a bordo ou só na Terra. Vale para os eventos que
        abrirem daqui em diante; um evento aberto segue a regra com que nasceu."""
        if local not in EQUIPE_MEDICA:
            raise ValueError(f"local do médico desconhecido: {local}")
        e = EQUIPE_MEDICA[local]
        TRIPULACAO["marcus"].update(nome=e["nome_marcus"], papel=e["papel_marcus"], funcao=e["funcao_marcus"])
        mudou, self.medico_local = self.medico_local != local, local
        if mudou and hasattr(self, "pessoas"):
            registro.auditar("equipe_medica", local, None, local, "apresentador", dict(resumo=e["resumo"]), self.agora_iso())
        return self.equipe()

    def equipe(self) -> dict:
        e = EQUIPE_MEDICA[self.medico_local]
        medico = e["medico"]
        return dict(local=self.medico_local, rotulo=e["rotulo"], resumo=e["resumo"], medico_id=medico, medico_nome=nome_de(medico),
                    medico_papel=MEDICO_TERRA["papel"] if medico == MEDICO_TERRA["id"] else TRIPULACAO["marcus"]["papel"],
                    cmo_id="marcus" if self.medico_local == "terra" else None,
                    marcus=dict(nome=TRIPULACAO["marcus"]["nome"], papel=TRIPULACAO["marcus"]["papel"]))

    # ------------------------------------------------------------ tempo
    def relogio(self) -> float:
        return self.t

    def agora_iso(self) -> str:
        return self.iso_em(0)

    def iso_em(self, segundos: float) -> str:
        return (INICIO + timedelta(seconds=self.t + segundos)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------ banco de ECG
    def _carregar_banco(self):
        """Gravações de teste do CinC. Para a demo não disparar sozinha, ficam só
        aquelas em que os modelos em serviço acertam; a taxa de erro real dos
        modelos está no relatório de treino, não aqui."""
        ia.carregar()
        b = np.load(TREINO / "banco_ecg.npz")
        self.banco = dict(normal=[], fa=[])
        total = dict(normal=0, fa=0)
        for ecg, rid, classe, fc in zip(b["ecg"], b["ids"], b["classes"], b["fc"]):
            classe = str(classe); total[classe] += 1
            m2 = ia._m2(ia._ativos["m2"], ecg)
            if m2["qualidade"] != "bom":
                continue
            previsto = ia._m1(ia._ativos["m1"], ecg)["classe"]
            if (classe == "fa") == (previsto == "fa"):
                self.banco[classe].append(dict(id=str(rid), ecg=ecg, fc=float(fc)))
        self.banco_info = dict(origem="CinC 2017, conjunto de teste", disponiveis=total,
                               em_uso={k: len(v) for k, v in self.banco.items()})

    def _escolher_ecg(self, tid, forcar=False):
        p = self.pessoas[tid]
        if p["fase"] in ("fa", "fa_o2"):
            if forcar or p["ecg_classe"] != "fa":
                g = self.banco["fa"][int(self.rng.integers(0, len(self.banco["fa"])))]
                p.update(ecg=g["ecg"], ecg_fc=g["fc"], ecg_id=g["id"], ecg_classe="fa")
            return
        alvo = 105 if p["fase"] == "fa_tratada" else TRIPULACAO[tid]["fc"]
        if forcar or p.get("ecg_classe") != "normal" or abs(p["ecg_fc"] - alvo) > 14:
            g = min(self.banco["normal"], key=lambda g: abs(g["fc"] - alvo) + self.rng.uniform(0, 4))
            p.update(ecg=g["ecg"], ecg_fc=g["fc"], ecg_id=g["id"], ecg_classe="normal")

    # ------------------------------------------------------------ leitura
    def _leitura(self, tid) -> dict:
        p, base = self.pessoas[tid], TRIPULACAO[tid]
        for k, lim in RUIDO.items():
            p["ruido"][k] = float(np.clip(0.85 * p["ruido"][k] + self.rng.normal(0, lim * 0.33), -lim, lim))
        r, d = p["ruido"], DESVIOS.get(p["fase"], {})
        v = dict(fc=base["fc"] + r["fc"], hrv=base["hrv"] + r["hrv"], spo2=base["spo2"] + r["spo2"],
                 temp_pele=base["temp"] + r["temp"], respiracao=base["resp"] + r["resp"])
        for k, delta in d.items():
            v[k] += delta
        desde = self.t - p["fase_t"]
        if p["fase"] == "fa":
            v.update(fc=p["ecg_fc"] + r["fc"], spo2=88 + r["spo2"], hrv=18 + r["hrv"] / 2,
                     respiracao=base["resp"] + 10 + r["resp"], temp_pele=base["temp"] + 0.4 + r["temp"])
        elif p["fase"] == "fa_o2":
            # ações seguras do CMO: o ritmo segue irregular, mas o O₂ tira a SpO₂ da faixa crítica
            v.update(fc=p["ecg_fc"] - 6 + r["fc"], spo2=min(94, 88 + desde / 2) + r["spo2"] / 2, hrv=20 + r["hrv"] / 2,
                     respiracao=base["resp"] + 6 + r["resp"], temp_pele=base["temp"] + 0.3 + r["temp"])
        elif p["fase"] == "fa_tratada":
            # o protocolo foi confirmado: o quadro cede aos poucos até a linha de base
            k = min(1.0, desde / 40.0)
            v.update(fc=112 + (base["fc"] - 112) * k + r["fc"], spo2=94 + (base["spo2"] - 94) * min(1, desde / 12) + r["spo2"] / 2,
                     hrv=28 + (base["hrv"] - 28) * k + r["hrv"] / 2, respiracao=base["resp"] + 6 * (1 - k) + r["resp"])
            if k >= 1.0:
                p["fase"] = "rotina"
        elif p["fase"] == "sensor_solto":
            v["spo2"] = 84
        if self.cabine["fluxo"] == "subindo":
            p["dose"] += 0.012 * (1.08 if tid == "elena" else 1)
        elif self.cabine["abrigo"]:
            p["dose"] += 0.0015 if self.cabine["fluxo"] != "caindo" else 0.0008
        p["dose"] += DOSE_BASE[self.link.missao]
        p["hrv30"].append(v["hrv"])
        estresse = base["estresse"] + 0.6 * (base["hrv"] - float(np.mean(p["hrv30"]))) + 0.05 * (base["sono_base"] - base["sono"])
        return dict(tripulante_id=tid, gerada_em=self.agora_iso(), fc=int(round(v["fc"])), hrv=int(round(v["hrv"])),
                    spo2=int(round(min(100, v["spo2"]))), temp_pele=round(v["temp_pele"], 1), respiracao=int(round(v["respiracao"])),
                    sono_min_noite=base["sono"], agua_ml_dia=p["agua"], pa_sys=base["pa"][0], pa_dia=base["pa"][1],
                    estresse=int(np.clip(round(estresse), 0, 100)), dose_msv_dia=round(p["dose"], 3))

    def passo(self):
        """Um segundo de missão: leitura -> ia.analisar -> motor -> link."""
        with self.trava:
            self.t += 1.0
            agora, linhas = self.agora_iso(), []
            for i, tid in enumerate(ORDEM):
                p = self.pessoas[tid]
                leitura = self._leitura(tid)
                # O trecho de sinal é reanalisado a cada 4 s (escalonado entre as pessoas) ou na troca de cenário.
                if p["m2"] is None or p.pop("reanalisar", False) or int(self.t) % 4 == i:
                    self._escolher_ecg(tid)
                    trecho = sinais.sujar(p["ecg"], self.rng) if p["fase"] == "sensor_solto" else p["ecg"]
                    p["trecho"] = trecho
                    a = ia.analisar(dict(leitura, ecg=trecho))
                    p["m1"], p["m2"] = a["m1"], a["m2"]
                else:
                    a = ia.analisar(leitura)
                    a["m1"], a["m2"] = p["m1"], p["m2"]
                    if p["m2"]["qualidade"] != "bom" and a["m3"]["estado"] != "otimo":
                        a["m3"]["estado"] = "suspeito"
                p["leitura"], p["analise"] = leitura, a
                q = p["m2"]["qualidade"]
                linhas += [(tid, disp, canal, leitura[canal], un, q, agora, agora) for canal, disp, un in CANAIS]
                self.motor.processar(a, [float(leitura[s]) for s in SINAIS_IF])
            linhas.append((None, "cabine-co2", "co2", self.cabine["co2"], "mmHg", "bom", agora, agora))
            registro.incluir_varias("leituras", ["tripulante_id", "dispositivo_id", "canal", "valor", "unidade",
                                                 "qualidade_sinal", "gerada_em", "recebida_em"], linhas)
            self.motor.tick()
            self.link.tick(agora)
            self.historico.append(dict(t=self.t, gerada_em=agora, cabine=dict(self.cabine),
                                       tripulantes={tid: self.clinico(tid) for tid in ORDEM}))

    # ------------------------------------------------------------ visões
    def clinico(self, tid) -> dict:
        """Tudo o que o oficial médico pode ver de uma pessoa (sem avisos privados)."""
        p, base = self.pessoas[tid], TRIPULACAO[tid]
        l, a = p["leitura"], p["analise"]
        limpa = lambda m: None if m is None else {k: v for k, v in m.items() if not k.startswith("_")}
        return dict(tripulante_id=tid, nome=base["nome"], papel=base["papel"], gerada_em=l["gerada_em"],
                    estado=a["m3"]["estado"], homeostase=a["m3"]["homeostase"], qualidade=p["m2"]["qualidade"],
                    **{k: l[k] for k in ("fc", "hrv", "spo2", "temp_pele", "respiracao", "sono_min_noite", "agua_ml_dia",
                                         "pa_sys", "pa_dia", "estresse", "dose_msv_dia")},
                    agua_meta=base["agua_meta"], prontidao=base["prontidao"], metricas=a["m3"]["metricas"],
                    m1=limpa(p["m1"]), m2=limpa(p["m2"]), isolation_forest=a["m3"]["isolation_forest"],
                    versao_z=a["m3"]["versao_z"], sombra=a["sombra"], ecg_origem=p["ecg_id"])

    def retrato_terra(self):
        """O que a Terra tem agora: o retrato de `atraso` atrás. No blackout, o último que chegou."""
        if self.link.blackout:
            return self.retrato_antes_do_blackout
        alvo = self.t - self.link.resumo()["atraso_demo_s"]
        for r in reversed(self.historico):
            if r["t"] <= alvo:
                return r
        return self.historico[0] if self.historico else None

    def ecg(self, tid, segundos=6) -> dict:
        p = self.pessoas[tid]
        inicio = (int(self.t) * 60) % max(1, len(p["trecho"]) - segundos * 300)
        return dict(fs=100, origem=p["ecg_id"], amostras=[round(float(x), 3) for x in p["trecho"][inicio:inicio + segundos * 300:3]])

    # ------------------------------------------------------------ cenários
    def injetar(self, cenario: str, tid: str | None = None) -> dict:
        with self.trava:
            agora = self.agora_iso()
            registro.auditar("simulador", cenario, None, None, "apresentador", dict(tripulante=tid), agora)
            if cenario in ("fa", "sensor_solto", "combinacao", "ciclo"):
                tid = tid or dict(fa="sarah", sensor_solto="sarah", combinacao="kenji", ciclo="sarah")[cenario]
                self._fase(tid, cenario)
                tipo = dict(fa="arritmia", sensor_solto="sensor_suspeito", combinacao="linha_de_base", ciclo="ciclo")[cenario]
                self.motor.espera.pop((tipo, tid), None)
            elif cenario == "rotina":
                for t_ in ORDEM:
                    self._fase(t_, "rotina")
                self.cabine.update(co2=2.4, fluxo="normal", abrigo=False, luz="dia")
            elif cenario == "humor":
                self.motor.abrir_manual("bem_estar", tid or "sarah", dict(
                    padrao="sono mais curto, voz mais baixa nas conversas e HRV abaixo do padrão dela nesta semana"))
            elif cenario == "tempestade_solar":
                self.cabine["fluxo"] = "subindo"
                self.motor.abrir_manual("tempestade_solar", "sarah")
            elif cenario == "eva":
                self.motor.abrir_manual("prontidao_eva", "sarah", dict(
                    tarefa="EVA das 15:00", prontidao={t_: TRIPULACAO[t_]["prontidao"] for t_ in ORDEM},
                    motivo="Elena: sono curto e reação mais lenta"))
            elif cenario == "dor_de_cabeca":
                self.cabine["co2"] = 4.1
                self.motor.abrir_manual("dor_de_cabeca", tid or "sarah", dict(co2=4.1, outros_com_sintoma=["elena", "kenji"]))
            elif cenario == "modo_noite":
                self.motor.abrir_manual("modo_noite", tid or "sarah")
            elif cenario in ("blackout", "sinal_volta"):
                if cenario == "blackout" and not self.link.blackout:
                    self.retrato_antes_do_blackout = self.retrato_terra()
                n = self.link.definir_blackout(cenario == "blackout")
                registro.auditar("link", self.link.missao, None, cenario, "apresentador", dict(pacotes_liberados=n), agora)
            elif cenario in MISSOES:
                self.link.missao = cenario
            elif cenario in ("medico_bordo", "medico_terra"):
                self.definir_medico(cenario.split("_")[1])
            else:
                raise ValueError(f"cenário desconhecido: {cenario}")
            return dict(cenario=cenario, tripulante_id=tid, quando=agora)

    def _fase(self, tid, fase):
        p = self.pessoas[tid]
        p.update(fase=fase, fase_t=self.t, reanalisar=True)
        if fase == "fa":
            self._escolher_ecg(tid, forcar=True)

    def avisar(self, tid, texto):
        self.pessoas[tid]["avisos"].append(dict(texto=texto, quando=self.agora_iso()))

    def efeito(self, nome: str, ev: dict):
        """Consequência física de uma decisão humana ou de uma ação de nível 4."""
        tid = ev["tripulante_id"]
        if nome == "fa_tratada":
            self._fase(tid, "fa_tratada")
            conduta = ev["dados"].get("conduta", "")
            self.avisar(tid, f"{TRIPULACAO['marcus']['nome']} (CMO) aplicou a {conduta} · O₂ 2 L/min" if conduta.startswith("ordem permanente")
                        else f"{MEDICO_TERRA['nome']} confirmou o protocolo · O₂ 2 L/min" if ev["medico_local"] == "terra"
                        else f"{nome_de(ev['decisoes'][-1]['humano_id'])} a caminho")
        elif nome == "o2":
            self._fase(tid, "fa_o2"); self.avisar(tid, f"{TRIPULACAO['marcus']['nome']} (CMO) com você · O₂ 2 L/min")
        elif nome == "rotina":
            self._fase(tid, "rotina")
        elif nome == "abrigo":
            self.cabine.update(abrigo=True, fluxo="alto")
        elif nome == "fluxo_caindo":
            self.cabine["fluxo"] = "caindo"; self.avisar("sarah", "Fluxo caindo · liberar a tripulação?")
        elif nome == "fim_tempestade":
            self.cabine.update(abrigo=False, fluxo="normal")
        elif nome == "ar_ajustado":
            self.cabine["co2"] = 2.6
        elif nome == "luz_noite":
            self.cabine["luz"] = "noite"; self.avisar(tid, "Modo noite ativado")
        elif nome == "luz_normal":
            self.cabine["luz"] = "dia"
        elif nome == "beber":
            self.beber(tid)

    # ------------------------------------------------------------ hábitos e jogo
    def beber(self, tid, ml=250):
        with self.trava:
            p = self.pessoas[tid]
            p["agua"] += ml
            j = self.jogo
            if tid == "sarah" and j["brinde"] == "chegou":
                j["brinde"] = "feito"; self._estufa(3)
                self.link.enviar("up", "Brinde hídrico: a Sarah respondeu a Ana", prioridade=4, destinos=["familia"],
                                 frase_familia="A Sarah brindou de volta com um copo de água.", gerado_em=self.agora_iso(),
                                 carga=dict(tipo="brinde_feito"))
            if tid == "sarah" and not j["missoes"]["agua"] and p["agua"] >= TRIPULACAO[tid]["agua_meta"]:
                self.missao_feita("agua", "Hidratação do dia")
            return p["agua"]

    def _estufa(self, pct):
        j = self.jogo
        j["pct"] += pct
        if j["pct"] >= 100:
            j["pct"] -= 100; j["nivel"] += 1

    def missao_feita(self, chave, nome):
        j = self.jogo
        if j["missoes"].get(chave):
            return
        j["missoes"][chave] = True; j["xp"] += 150; self._estufa(2)
        if not self.motor.abertos(tipo="arritmia"):  # o jogo some na emergência
            self.link.enviar("up", f"Missão concluída: {nome}", prioridade=4, destinos=["familia"],
                             frase_familia=f"A Sarah completou a missão \"{nome}\".", gerado_em=self.agora_iso())

    # ------------------------------------------------------------ chegada de pacotes
    def _entregue(self, p: dict):
        if p["direcao"] != "down":
            return
        c = p["carga"]
        if c.get("tipo") == "decisao":
            self._decisao_da_terra(p, c)
        elif c.get("tipo") == "modelo":
            self._modelo_da_terra(p, c)
        elif c.get("tipo") == "parecer":
            ev = self.motor.eventos.get(c["evento_id"])
            if ev:
                ev["dados"]["parecer"] = dict(texto=c["texto"], de=c["de"], enviado_em=p["gerado_em"], recebido_em=p["entregue_em"])
                registro.auditar("parecer", ev["id"], None, None, c["de"], dict(texto=c["texto"], revisao="não é comando"), p["entregue_em"])
                self.avisar(ev["tripulante_id"], "Houston revisou seu atendimento")
        elif c.get("tipo") == "brinde":
            self.jogo["brinde"] = "chegou"; self.avisar("sarah", "Ana propôs um brinde hídrico")
        elif c.get("tipo") == "corrida":
            self.jogo["corrida_km"] = round(self.jogo["corrida_km"] + c.get("km", 5), 1); self._estufa(1)
            self.avisar("sarah", "Lucas correu na Terra · a corrida Terra–órbita andou")
        if c.get("tipo") in ("mensagem", "brinde", "corrida"):
            self.mensagens.append(dict(de=c.get("de", "família"), texto=p["rotulo"], enviado_em=p["gerado_em"], recebido_em=p["entregue_em"]))

    def _modelo_da_terra(self, p, c):
        """Aprovação de modelo da médica de voo: vale quando chega e só para a versão que
        ela viu. Se o candidato em sombra mudou no caminho, não se aplica."""
        reg = next((x for x in self.decisoes_modelo if x["pacote_id"] == p["id"]), None)
        try:
            self.decidir_modelo(c["peca"], c["humano_id"], c["acao"] == "aprovar", c["humano_id"], c["versao"])
            resultado, motivo = "aplicada", None
        except Exception as e:  # hitl.Negado: candidato trocou ou sumiu
            resultado, motivo = "não aplicada", str(e)
        registro.auditar("modelo_terra", c["versao"], "a caminho", resultado, c["humano_id"],
                         dict(acao=c["acao"], peca=c["peca"], pacote=p["id"], enviada_em=p["gerado_em"], chegou_em=p["entregue_em"],
                              motivo=motivo), p["entregue_em"])
        if reg:
            reg.update(estado=resultado, chegou_em=p["entregue_em"], motivo=motivo)

    def _decisao_da_terra(self, p, c):
        """A decisão da médica de voo só vale quando chega. Se a nave já avançou, ela não
        se aplica e isso fica registrado: a Terra decidiu sobre um retrato do passado."""
        reg = next((x for x in self.decisoes_terra if x["pacote_id"] == p["id"]), None)
        try:
            self.motor.decidir(c["evento_id"], c["humano_id"], c["acao"], c.get("dose"), c.get("pin"), c.get("detalhe"), via="link")
            resultado, motivo = "aplicada", None
        except Recusa as e:
            resultado, motivo = "não aplicada", str(e)
        registro.auditar("decisao_terra", c["evento_id"], "a caminho", resultado, c["humano_id"],
                         dict(acao=c["acao"], pacote=p["id"], enviada_em=p["gerado_em"], chegou_em=p["entregue_em"], motivo=motivo), p["entregue_em"])
        if reg:
            reg.update(estado=resultado, chegou_em=p["entregue_em"], motivo=motivo)
