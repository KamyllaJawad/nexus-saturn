"""Constantes do protótipo: pastas, tripulação, perfis de missão e prazos.

Os números da tripulação são os mesmos de dados/bronze/sintetico/gerar_dados.py,
para o simulador ao vivo cair na mesma distribuição em que o M3 foi treinado.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
BRONZE = DADOS / "bronze"
PRATA = DADOS / "prata"
OURO = DADOS / "ouro"
TREINO = DADOS / "treino"
MODELOS = RAIZ / "modelos"
PROTOCOLOS = RAIZ / "protocolos" / "protocolos.json"
BANCO = RAIZ / "astrohealth.db"
FRONT = RAIZ.parent / "9-frontend"

FS = 300  # Hz do ECG (igual ao CinC 2017)
JANELA_S = 30  # segundos de ECG analisados pelo M1 e pelo M2

TRIPULACAO = {
    "sarah": dict(nome="Sarah", papel="Comandante", funcao="comandante",
                  fc=72, spo2=98, hrv=64, temp=36.8, resp=14, pa=(118, 76),
                  sono=420, sono_base=460, agua=1700, agua_meta=2400, estresse=42,
                  dose=0.450, prontidao=88),
    "marcus": dict(nome="Dr. Marcus", papel="Oficial médico", funcao="oficial_medico",
                   fc=64, spo2=98, hrv=71, temp=36.6, resp=13, pa=(122, 80),
                   sono=422, sono_base=425, agua=1900, agua_meta=2600, estresse=30,
                   dose=0.450, prontidao=90),
    "elena": dict(nome="Elena", papel="Engenheira de voo", funcao="astronauta",
                  fc=78, spo2=97, hrv=46, temp=36.9, resp=15, pa=(114, 72),
                  sono=370, sono_base=370, agua=1250, agua_meta=2400, estresse=48,
                  dose=0.468, prontidao=64),
    "kenji": dict(nome="Kenji", papel="Especialista de missão", funcao="astronauta",
                  fc=58, spo2=98, hrv=82, temp=36.5, resp=12, pa=(126, 82),
                  sono=453, sono_base=450, agua=2100, agua_meta=2500, estresse=24,
                  dose=0.451, prontidao=91),
}
ORDEM = ["sarah", "marcus", "elena", "kenji"]

# Médico da missão é uma hipótese (ADR-015, "médico a bordo é hipótese"). A bordo: o
# Dr. Marcus decide na nave. Só na Terra: o Marcus vira oficial de saúde (CMO) e só
# inicia ações seguras pré-aprovadas; quem confirma o protocolo e libera medicação é
# a médica de voo em Houston, com o atraso do link.
MEDICO_TERRA = dict(id="rivera", nome="Dra. Rivera", papel="Flight surgeon · Houston")
EQUIPE_MEDICA = {
    "bordo": dict(medico="marcus", nome_marcus="Dr. Marcus", papel_marcus="Oficial médico", funcao_marcus="oficial_medico",
                  rotulo="Médico a bordo",
                  resumo="O Dr. Marcus confirma o protocolo e libera a medicação a bordo. Houston revisa depois, com parecer."),
    "terra": dict(medico="rivera", nome_marcus="Marcus", papel_marcus="Oficial de saúde (CMO)", funcao_marcus="cmo",
                  rotulo="Médico só na Terra",
                  resumo="Sem médico a bordo. O Marcus é o oficial de saúde (CMO) e inicia só as ações seguras pré-aprovadas "
                         "(repouso, O₂ e ECG de 12 derivações), que não esperam o atraso. A Dra. Rivera, em Houston, confirma o "
                         "protocolo e libera a medicação; cada decisão viaja com o atraso da missão. Sem sinal, só vale a ordem "
                         "permanente que ela assinou antes do voo (ADR-017)."),
}

# Ordem permanente (ADR-017): dose pré-autorizada pela médica de voo antes do voo, para
# uma conjunção solar longa sem médico a bordo. Só vale sem sinal com a Terra, depois das
# ações seguras, com a FA ainda presente. O CMO aplica e registra; a dose não muda.
# Dose de demonstração; não é orientação clínica.
ORDEM_PERMANENTE = dict(
    id="OP-FA-01", tipo="arritmia", titulo="Fibrilação atrial sem contato com a Terra",
    dose="amiodarona 150 mg IV em 10 min", assinada_por="rivera", assinada_em="2026-10-30",
    criterios=["sem médico a bordo", "sem sinal com a Terra", "ações seguras já iniciadas",
               "o M1 ainda vê FA na última leitura com sinal bom", "nenhuma dose aplicada neste evento"],
    depois="O uso sobe como P1 e a Dra. Rivera revisa quando o sinal voltar.")


def nome_de(hid: str) -> str:
    if hid == MEDICO_TERRA["id"]:
        return MEDICO_TERRA["nome"]
    return TRIPULACAO.get(hid, {}).get("nome", hid)

# Limite do ruído AR(1) de cada sinal, igual ao gerador dos dados de treino.
RUIDO = dict(fc=3, hrv=4, spo2=1, temp=0.1, resp=1)

# Sinais contínuos que entram no Isolation Forest (um modelo por tripulante).
SINAIS_IF = ["fc", "hrv", "spo2", "temp_pele", "respiracao"]

# Perfis de missão. atraso_s é o tempo real de ida; demo_s é o que a demo espera
# (acima de 5 s, 1 min de atraso vira 1 s, como na demo original).
MISSOES = {
    "leo": dict(rotulo="ISS · órbita baixa", link="Satélites TDRS", atraso_s=0.6, atraso_txt="menos de 1 s",
                autonomia="Houston acompanha em tempo real e pode decidir junto com a tripulação.",
                blackout="Perda de sinal entre satélites TDRS", volta="cerca de 10 min"),
    "gateway": dict(rotulo="Gateway · órbita lunar", link="Deep Space Network", atraso_s=1.3, atraso_txt="1,3 s",
                    autonomia="Houston responde em segundos; a Cosmo cobre as pausas de antena.",
                    blackout="Antenas da DSN alocadas a outra missão", volta="cerca de 45 min"),
    "mars": dict(rotulo="Trânsito para Marte", link="Deep Space Network", atraso_s=500, atraso_txt="8 min 20 s",
                 autonomia="Decisões médicas acontecem a bordo: a Cosmo recomenda, o oficial médico confirma, Houston revisa depois.",
                 blackout="Conjunção solar: o Sol está entre a Terra e a nave", volta="cerca de 14 dias"),
    "marsSurf": dict(rotulo="Superfície de Marte", link="Orbitador de relay + DSN", atraso_s=750, atraso_txt="12 min 30 s",
                     autonomia="Decisões médicas acontecem a bordo: a Cosmo recomenda, o oficial médico confirma, Houston revisa depois.",
                     blackout="Orbitador de relay abaixo do horizonte", volta="cerca de 40 min"),
}


def autonomia(missao: str, local: str) -> str:
    """Texto do modo de autonomia, que depende do perfil de missão e de onde está o médico."""
    if local == "bordo":
        return MISSOES[missao]["autonomia"]
    if MISSOES[missao]["atraso_s"] <= 5:
        return ("Sem médico a bordo: a Dra. Rivera decide de Houston quase em tempo real e o CMO executa. "
                "Ações seguras pré-aprovadas não esperam a resposta.")
    return (f"Sem médico a bordo: a Cosmo recomenda, a Dra. Rivera decide de Houston com {MISSOES[missao]['atraso_txt']} de ida "
            "e o CMO executa. Ações seguras pré-aprovadas não esperam o atraso; medicação espera. Sem sinal, vale a "
            "ordem permanente assinada antes do voo.")


def atraso_demo(missao: str) -> float:
    a = MISSOES[missao]["atraso_s"]
    return a / 60.0 if a > 5 else a


# Quem decide cada tipo de evento, prazo e cadeia de escalonamento (docs/05).
# O escalonamento sempre aponta para outro humano, nunca para a IA (ADR-004).
REGRAS = {
    "arritmia": dict(nivel=3, papel="oficial_medico", prazo_s=60, prioridade=1,
                     cadeia=["marcus", "sarah", "kenji"], destinos=["oficial_medico", "houston"]),
    "sensor_suspeito": dict(nivel=2, papel="astronauta", prazo_s=20, prioridade=2,
                            cadeia=["{tripulante}", "marcus"], destinos=["astronauta"]),
    "tempestade_solar": dict(nivel=4, papel="comandante", prazo_s=120, prioridade=1,
                             cadeia=["sarah", "kenji", "marcus"], destinos=["comandante", "oficial_medico", "houston", "familia"]),
    "prontidao_eva": dict(nivel=2, papel="comandante", prazo_s=None, prioridade=3,
                          cadeia=["sarah", "kenji"], destinos=["comandante", "houston"]),
    "dor_de_cabeca": dict(nivel=3, papel="oficial_medico", prazo_s=60, prioridade=2,
                          cadeia=["marcus", "sarah"], destinos=["oficial_medico", "houston"]),
    "bem_estar": dict(nivel=2, papel="astronauta", prazo_s=None, prioridade=3,
                      cadeia=["{tripulante}"], destinos=["astronauta"]),
    "ciclo": dict(nivel=2, papel="astronauta", prazo_s=None, prioridade=3,
                  cadeia=["{tripulante}"], destinos=["astronauta"]),
    "modo_noite": dict(nivel=4, papel="astronauta", prazo_s=15, prioridade=4,
                       cadeia=["{tripulante}"], destinos=["astronauta"]),
    "hidratacao": dict(nivel=2, papel="astronauta", prazo_s=None, prioridade=4,
                       cadeia=["{tripulante}"], destinos=["astronauta"]),
    "linha_de_base": dict(nivel=1, papel="astronauta", prazo_s=None, prioridade=3,
                          cadeia=["{tripulante}"], destinos=["astronauta", "oficial_medico"]),
}

# Piso do MAD por sinal: os sintéticos são inteiros, e um MAD de 0 ou 1 explodiria o z.
PISO_MAD = dict(fc=1.5, hrv=2.0, spo2=0.7, temp_pele=0.1, respiracao=0.7)
