"""Simulador do link nave <-> Terra: fila por prioridade e atraso por perfil de
missão (ADR-005). Não é DTN real: cada pacote guarda `chega_em = agora + atraso`,
e no blackout tudo fica na fila. P1 sai primeiro quando a janela abre.
"""
from ..config import MISSOES, atraso_demo
from . import registro


class Link:
    def __init__(self, relogio):
        self.relogio = relogio          # função que devolve o tempo da simulação em segundos
        self.missao = "mars"
        self.blackout = False
        self.pacotes = []
        self._seq = 0
        self.ao_entregar = None         # callback(pacote), ligado pelo simulador

    # ---- envio
    def enviar(self, direcao: str, rotulo: str, prioridade: int = 3, destinos=(), carga=None,
               frase_familia=None, de="nave", tamanho_mb=0.1, gerado_em=None) -> dict:
        self._seq += 1
        p = dict(id=f"pct-{self._seq:04d}", direcao=direcao, rotulo=rotulo, prioridade=prioridade,
                 destinos=list(destinos), carga=carga or {}, frase_familia=frase_familia, de=de,
                 tamanho_mb=tamanho_mb, gerado_em=gerado_em, enviado_t=self.relogio(), chega_t=None,
                 entregue_em=None, estado="fila" if self.blackout else "transito")
        if not self.blackout:
            p["chega_t"] = self.relogio() + atraso_demo(self.missao)
        self.pacotes.append(p)
        registro.incluir("pacotes", pacote_id=p["id"], direcao=direcao, prioridade=prioridade,
                         estado=p["estado"], rotulo=rotulo, quando=gerado_em)
        return p

    # ---- relógio do link
    def tick(self, agora_iso: str):
        t = self.relogio()
        for p in self.pacotes:
            if p["estado"] == "transito" and t >= p["chega_t"]:
                p["estado"], p["entregue_em"] = "entregue", agora_iso
                registro.incluir("pacotes", pacote_id=p["id"], direcao=p["direcao"], prioridade=p["prioridade"],
                                 estado="entregue", rotulo=p["rotulo"], quando=agora_iso)
                if self.ao_entregar:
                    self.ao_entregar(p)
        if len(self.pacotes) > 400:
            self.pacotes = self.pacotes[-300:]

    def definir_blackout(self, ligado: bool):
        if ligado == self.blackout:
            return 0
        self.blackout = ligado
        if ligado:
            return 0
        # Janela de contato abriu: a fila descarrega por prioridade, P1 primeiro.
        fila = sorted((p for p in self.pacotes if p["estado"] == "fila"), key=lambda p: (p["prioridade"], p["enviado_t"]))
        for i, p in enumerate(fila):
            p["estado"] = "transito"
            p["chega_t"] = self.relogio() + atraso_demo(self.missao) + 0.5 * i
        return len(fila)

    # ---- leitura
    def resumo(self) -> dict:
        m = MISSOES[self.missao]
        pend = [p for p in self.pacotes if p["direcao"] == "up" and p["estado"] != "entregue"]
        return dict(missao=self.missao, rotulo=m["rotulo"], link=m["link"], atraso_txt=m["atraso_txt"],
                    atraso_real_s=m["atraso_s"], atraso_demo_s=round(atraso_demo(self.missao), 2),
                    comprimido=m["atraso_s"] > 5, blackout=self.blackout, motivo_blackout=m["blackout"],
                    volta_em=m["volta"], autonomia=m["autonomia"],
                    fila=[self.publico(p) for p in sorted(pend, key=lambda p: (p["prioridade"], p["enviado_t"]))],
                    fila_mb=round(sum(p["tamanho_mb"] for p in pend), 1))

    def publico(self, p: dict) -> dict:
        falta = None if p["chega_t"] is None or p["estado"] != "transito" else max(0.0, round(p["chega_t"] - self.relogio(), 1))
        return dict(id=p["id"], direcao=p["direcao"], rotulo=p["rotulo"], prioridade=p["prioridade"], estado=p["estado"],
                    de=p["de"], gerado_em=p["gerado_em"], entregue_em=p["entregue_em"], falta_s=falta,
                    tamanho_mb=p["tamanho_mb"])

    def entregues(self, destino: str, direcao="up") -> list:
        return [p for p in self.pacotes if p["direcao"] == direcao and p["estado"] == "entregue" and destino in p["destinos"]]
