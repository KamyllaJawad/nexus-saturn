"""Ensaio do roteiro pela API, com o servidor no ar e o relógio de verdade correndo.

Uso (com `uvicorn app.main:app --port 8000` rodando em outro terminal):
    python testes/ensaio_ao_vivo.py

Não é pytest: leva cerca de 1 minuto e imprime o que cada superfície vê.
"""
import json
import sys
import time
import urllib.error
import urllib.request

API = "http://127.0.0.1:8000/api"


def chamar(caminho, corpo=None):
    req = urllib.request.Request(API + caminho, data=None if corpo is None else json.dumps(corpo).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return dict(recusado=e.code, motivo=json.loads(e.read()).get("detail"))


def decidir(ev, humano, acao, **extra):
    return chamar("/decisoes", dict(evento_id=ev, humano_id=humano, acao=acao, **extra))


def evento(tipo):
    return next((e for e in chamar("/bordo")["eventos"] if e["tipo"] == tipo), None)


def principal():
    falhas = []

    def conferir(nome, ok, detalhe=""):
        print(("  ok   " if ok else "  FALHA ") + nome + (f" · {detalhe}" if detalhe else ""))
        if not ok:
            falhas.append(nome)

    print("Reiniciando em Trânsito para Marte…")
    chamar("/simulador/reiniciar", {}); chamar("/simulador/cenario", dict(cenario="mars")); time.sleep(4)
    s = chamar("/bordo")["tripulantes"][0]
    conferir("rotina: Sarah ótima, M1 sem FA", s["estado"] == "otimo" and s["m1"]["classe"] != "fa", f"FC {s['fc']}, SpO2 {s['spo2']}")

    print("\n1. Relógio folgado (M2 segura o alarme)")
    chamar("/simulador/cenario", dict(cenario="sensor_solto", tripulante_id="sarah")); time.sleep(3)
    r = chamar("/tripulantes/sarah/relogio")
    p = r["pendencias"][0] if r["pendencias"] else {}
    conferir("o relógio pergunta antes de alarmar", p.get("estado") == "confirmacao_astronauta", f"estado '{r['eu']['estado']}', prazo {p.get('prazo_restante_s')} s")
    conferir("nenhum alerta de arritmia abriu", evento("arritmia") is None)
    decidir(p["id"], "sarah", "ajustar_sensor"); time.sleep(6)
    conferir("ajustou: volta a ótimo", chamar("/tripulantes/sarah/relogio")["eu"]["estado"] == "otimo")

    print("\n2. Fibrilação atrial (M1 em ECG real do conjunto de teste)")
    t0 = time.time()
    chamar("/simulador/cenario", dict(cenario="fa", tripulante_id="sarah"))
    ev = None
    while not ev and time.time() - t0 < 6:
        time.sleep(0.3); ev = evento("arritmia")
    conferir("evento aberto em até 2 s", bool(ev) and time.time() - t0 <= 2.6, f"{time.time() - t0:.1f} s")
    s = chamar("/bordo")["tripulantes"][0]
    print(f"       Sarah: {s['estado']}, FC {s['fc']}, SpO2 {s['spo2']}, P(FA) {s['m1']['prob_fa']}, gravação {s['ecg_origem']}")
    print(f"       sugestão: {ev['sugestao']['texto']} · confiança {ev['sugestao']['confianca']} · {ev['sugestao']['evidencias']}")
    conferir("nível 3, com o oficial médico", ev["nivel_autonomia"] == 3 and ev["responsavel_id"] == "marcus")
    conferir("o jogo some do relógio na emergência", chamar("/tripulantes/sarah/relogio")["jogo"] is None)
    conferir("quem não é responsável é recusado", decidir(ev["id"], "elena", "confirmar").get("recusado") == 403)
    conferir("Houston ainda não sabe", chamar("/houston/console")["eventos"] == [])
    conferir("a família ainda não sabe", chamar("/familia/feed")["ultimas"] == [])
    conferir("o médico confirma", decidir(ev["id"], "marcus", "confirmar").get("estado") == "em_execucao")
    conferir("medicação sem PIN é recusada", decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="0").get("recusado") == 403)
    conferir("medicação em passo separado", "medicacao" in decidir(ev["id"], "marcus", "liberar_medicacao", dose="150 mg", pin="2026").get("dados", {}))
    x = chamar(f"/eventos/{ev['id']}/explicacao")
    conferir("explicação cita o protocolo", bool(x["protocolo"]["fonte"]) and len(x["evidencias"]) == 3, x["protocolo"]["titulo"])
    time.sleep(10)
    h = chamar("/houston/console")
    conferir("Houston recebe com atraso, já com a decisão", bool(h["eventos"]) and bool(h["eventos"][0].get("decisao")), f"dado de {h['dado_de'][11:19]}, nave {h['missao']['hora_nave'][11:19]}")
    chamar("/houston/parecer", dict(evento_id=ev["id"], texto="De acordo com a conduta."))
    f = chamar("/familia/feed")
    textos = " ".join([f["frase"]] + [i["frase"] for i in f["ultimas"]])
    conferir("família: frase, sem número", "oficial médico" in textos and not any(c.isdigit() for c in textos), textos)
    time.sleep(14)
    ev = evento("arritmia")
    conferir("parecer chega a bordo como revisão", ev["dados"].get("parecer", {}).get("texto") == "De acordo com a conduta.")
    conferir("o motor resolve quando o quadro cede", ev["estado"] == "resolvido")

    print("\n3. Combinação fora do padrão (Isolation Forest) e human-in-the-loop")
    chamar("/simulador/cenario", dict(cenario="combinacao", tripulante_id="kenji")); time.sleep(9)
    r = chamar("/tripulantes/kenji/relogio")
    p = next((e for e in r["pendencias"] if e["tipo"] == "linha_de_base"), None)
    conferir("sugestão de nível 1 no relógio do Kenji, estado não crítico", bool(p) and p["nivel_autonomia"] == 1 and r["eu"]["estado"] != "critico")
    if p:
        time.sleep(25)
        decidir(p["id"], "kenji", "falso_alarme")
        painel = chamar("/ia/painel")
        conferir("a resposta virou rótulo", painel["rotulos"]["m3-if"]["total"] >= 1)

    print("\n4. Privacidade")
    chamar("/simulador/cenario", dict(cenario="humor", tripulante_id="sarah")); time.sleep(2)
    conferir("queda de humor não aparece no painel sem consentimento", evento("bem_estar") is None)
    a = chamar("/auditoria")
    conferir("auditoria íntegra", a["cadeia"]["integra"], f"{a['cadeia']['registros']} registros")
    chamar("/simulador/cenario", dict(cenario="rotina"))
    print("\n" + ("Tudo certo." if not falhas else f"{len(falhas)} falha(s): {falhas}"))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(principal())
