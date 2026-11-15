#!/usr/bin/env python3
"""Gera o pacote de dados sinteticos JA TRATADOS do MVP AstroHealth OS.

Uso: python3 gerar_dados.py [pasta_de_saida]
Saida: 6 CSVs (UTF-8, virgula, cabecalho, decimal com ponto).
Semente fixa: rodar de novo gera exatamente os mesmos arquivos.
"""
import csv
import os
import random
import sys
from datetime import datetime, timedelta, timezone

SEED = 20261114
OUT = sys.argv[1] if len(sys.argv) > 1 else "astrohealth_dados"
UTC = timezone.utc
AGORA = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
INICIO = datetime(2026, 11, 12, 12, 1, tzinfo=UTC)
MINUTOS = [INICIO + timedelta(minutes=i) for i in range(2880)]
DIAS = [datetime(2026, 11, d, tzinfo=UTC) for d in (12, 13, 14)]


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def T(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


# ---------------------------------------------------------------- tripulacao
# acorda: (hora, minuto) UTC. sono: minutos ao acordar em 13/11 e 14/11.
# agua_meio_dia: acumulado as 12:00 UTC (o valor que o MVP mostra "agora").
P = {
    "sarah": dict(fc=72, spo2=98, hrv=64, temp=36.8, resp=14, pa=(118, 76),
                  sono_base=460, sono={13: 460, 14: 420}, acorda=(6, 0),
                  agua_meio_dia=1700, estresse=42, dose_fim=0.450,
                  treino=[(7, 0, 40), (14, 0, 45)]),
    "marcus": dict(fc=64, spo2=98, hrv=71, temp=36.6, resp=13, pa=(122, 80),
                   sono_base=425, sono={13: 425, 14: 422}, acorda=(6, 15),
                   agua_meio_dia=1900, estresse=30, dose_fim=0.450,
                   treino=[(7, 30, 45), (15, 0, 40)]),
    "elena": dict(fc=78, spo2=97, hrv=46, temp=36.9, resp=15, pa=(114, 72),
                  sono_base=370, sono={13: 370, 14: 370}, acorda=(5, 50),
                  agua_meio_dia=1250, estresse=48, dose_fim=0.468,
                  treino=[(8, 0, 35), (16, 30, 40)]),
    "kenji": dict(fc=58, spo2=98, hrv=82, temp=36.5, resp=12, pa=(126, 82),
                  sono_base=450, sono={13: 450, 14: 453}, acorda=(6, 30),
                  agua_meio_dia=2100, estresse=24, dose_fim=0.451,
                  treino=[(8, 30, 50), (16, 0, 45)]),
}
ORDEM = ["sarah", "marcus", "elena", "kenji"]

# ----------------------------------------------------------------- episodios
EP_CICLO = (T("2026-11-14T10:00:00Z"), T("2026-11-14T12:00:00Z"))
EP_HIDRA = (T("2026-11-13T05:50:00Z"), T("2026-11-14T12:00:00Z"))
EP_SENSOR = (T("2026-11-13T16:10:00Z"), T("2026-11-13T16:11:00Z"))
EP_FA = (T("2026-11-13T09:42:00Z"), T("2026-11-13T09:44:00Z"))
EP_OSSO = (T("2026-11-14T00:00:00Z"), T("2026-11-14T12:00:00Z"))
EP_CO2 = (T("2026-11-14T11:20:00Z"), T("2026-11-14T11:40:00Z"))


def dentro(t, ep):
    return ep[0] <= t <= ep[1]


def ar_serie(rng, n, limite, phi=0.85):
    """Ruido suave (AR1) limitado a +-limite."""
    sigma = limite * 0.33
    x, out = 0.0, []
    for _ in range(n):
        x = phi * x + rng.gauss(0, sigma)
        x = max(-limite, min(limite, x))
        out.append(x)
    return out


def curva_agua(rng, pid, dia):
    """Acumulado de agua por minuto do dia (0..1439), monotono, zera 00:00."""
    p = P[pid]
    acorda = p["acorda"][0] * 60 + p["acorda"][1]
    deita = 22 * 60 + 30
    alvo = p["agua_meio_dia"]
    if dia.day != 14:  # so o "agora" e exato; os outros dias variam um pouco
        alvo += rng.choice([-60, -30, 0, 30, 60])
    # goles da manha somam o alvo as 12:00; a tarde/noite soma ~25% a mais
    def goles(ini, fim, total):
        momentos, m = [], ini + rng.randint(5, 20)
        while m < fim:
            momentos.append(m)
            m += rng.randint(30, 55)
        pesos = [rng.uniform(0.6, 1.4) for _ in momentos]
        s = sum(pesos)
        ml = [int(round(total * w / s / 10.0)) * 10 for w in pesos]
        ml[-1] += total - sum(ml)
        return list(zip(momentos, ml))
    eventos = goles(acorda, 12 * 60, alvo)
    tarde = int(round(alvo * 0.25 / 10.0)) * 10
    eventos += goles(12 * 60 + 10, deita, tarde)
    curva, acc, ev = [], 0, dict(eventos)
    for m in range(1440):
        acc += ev.get(m, 0)
        curva.append(acc)
    assert curva[12 * 60] == alvo
    return curva


def curva_atividade(rng, pid):
    """Minutos ativos acumulados no dia (0..1439), zera 00:00."""
    p = P[pid]
    acorda = p["acorda"][0] * 60 + p["acorda"][1]
    ativo = set()
    for h, m, dur in p["treino"]:
        ini = h * 60 + m + rng.randint(-5, 5)
        ativo.update(range(ini, ini + dur + rng.randint(-3, 3)))
    for m in range(acorda, 22 * 60):  # movimentacao leve ao longo do turno
        if rng.random() < 0.03:
            ativo.add(m)
    curva, acc = [], 0
    for m in range(1440):
        acc += 1 if m in ativo else 0
        curva.append(acc)
    return curva


CAMPOS_VITAIS = ["minuto_utc", "tripulante_id", "fc", "hrv", "spo2", "temp_pele",
                 "respiracao", "atividade_min", "agua_ml_dia", "sono_min_noite",
                 "pa_sys", "pa_dia", "spo2_kit", "dose_mSv_dia", "qualidade",
                 "fracao_suspeito", "estresse", "excluir_treino_if", "cenario"]


def gerar_vitais():
    por_pessoa = {}
    for pid in ORDEM:
        p = P[pid]
        rng = random.Random("%s-%s" % (SEED, pid))
        n = len(MINUTOS)
        r_fc, r_hrv = ar_serie(rng, n, 3), ar_serie(rng, n, 4)
        r_spo2, r_temp = ar_serie(rng, n, 1), ar_serie(rng, n, 0.1)
        r_resp = ar_serie(rng, n, 1)
        agua = {d.day: curva_agua(rng, pid, d) for d in DIAS}
        ativ = {d.day: curva_atividade(rng, pid) for d in DIAS}
        acorda_min = p["acorda"][0] * 60 + p["acorda"][1]
        pa_min = acorda_min + rng.randint(30, 50)
        ultimo_sono = p["sono_base"]
        janela_hrv = []
        linhas = []
        for i, t in enumerate(MINUTOS):
            mdia = t.hour * 60 + t.minute
            fc = int(round(p["fc"] + r_fc[i]))
            hrv = int(round(p["hrv"] + r_hrv[i]))
            spo2 = int(round(p["spo2"] + r_spo2[i]))
            temp = round(p["temp"] + r_temp[i], 1)
            resp = int(round(p["resp"] + r_resp[i]))
            qualidade, fracao = "bom", round(rng.uniform(0.0, 0.04), 2)
            excluir, cenario, kit = "false", "rotina", ""

            if pid == "sarah" and dentro(t, EP_CICLO):
                fc += 3
                hrv -= 8
                temp = round(temp + 0.3, 1)
                cenario = "ciclo"
            if pid == "elena" and dentro(t, EP_HIDRA):
                cenario = "hidratacao"
            if pid == "sarah" and dentro(t, EP_SENSOR):
                spo2, qualidade, fracao = 84, "suspeito", 0.7
                excluir, cenario, kit = "true", "sensor_solto", 97
            if pid == "sarah" and dentro(t, EP_FA):
                fc, spo2, hrv = 158, 89, 18
                excluir, cenario = "true", "fa"

            sono = ""
            if mdia == acorda_min and t.day in p["sono"]:
                sono = p["sono"][t.day]
                ultimo_sono = sono
            pa_sys = pa_dia = ""
            if mdia == pa_min and t.day in (13, 14):
                pa_sys = p["pa"][0] + rng.randint(-3, 3)
                pa_dia = p["pa"][1] + rng.randint(-2, 2)

            # estresse derivado: desvio da HRV (media movel 30 min) e do sono
            # em relacao a linha de base da propria pessoa.
            janela_hrv.append(hrv)
            if len(janela_hrv) > 30:
                janela_hrv.pop(0)
            hrv_med = sum(janela_hrv) / float(len(janela_hrv))
            est = (p["estresse"] + 0.6 * (p["hrv"] - hrv_med)
                   + 0.05 * (p["sono_base"] - ultimo_sono))
            est = int(round(max(0, min(100, est))))

            dose = round(0.400 + (p["dose_fim"] - 0.400) * i / (n - 1.0), 3)
            linhas.append({
                "minuto_utc": iso(t), "tripulante_id": pid, "fc": fc, "hrv": hrv,
                "spo2": spo2, "temp_pele": "%.1f" % temp, "respiracao": resp,
                "atividade_min": ativ[t.day][mdia], "agua_ml_dia": agua[t.day][mdia],
                "sono_min_noite": sono, "pa_sys": pa_sys, "pa_dia": pa_dia,
                "spo2_kit": kit, "dose_mSv_dia": "%.3f" % dose,
                "qualidade": qualidade, "fracao_suspeito": "%.2f" % fracao,
                "estresse": est, "excluir_treino_if": excluir, "cenario": cenario,
            })
        por_pessoa[pid] = linhas
    # ordena por minuto e depois pela ordem da tripulacao
    saida = []
    for i in range(len(MINUTOS)):
        for pid in ORDEM:
            saida.append(por_pessoa[pid][i])
    return saida


def escrever(nome, campos, linhas):
    caminho = os.path.join(OUT, nome)
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    return len(linhas)


def main():
    os.makedirs(OUT, exist_ok=True)
    cont = {}

    cont["ficha.csv"] = escrever("ficha.csv",
        ["tripulante_id", "sexo", "calendario", "metodo", "ultima_menstruacao",
         "duracao_tipica_dias", "trecho_intenso", "versao_ficha"],
        [dict(tripulante_id="sarah", sexo="feminino", calendario="true",
              metodo="pilula_combinada_continua", ultima_menstruacao="2026-06-02",
              duracao_tipica_dias=28, trecho_intenso="segunda_quinzena",
              versao_ficha="pre-voo-0.1"),
         dict(tripulante_id="elena", sexo="feminino", calendario="true",
              metodo="nenhum", ultima_menstruacao="2026-10-18",
              duracao_tipica_dias=28, trecho_intenso="segunda_quinzena",
              versao_ficha="pre-voo-0.1"),
         dict(tripulante_id="marcus", sexo="masculino", calendario="false",
              versao_ficha="pre-voo-0.1"),
         dict(tripulante_id="kenji", sexo="masculino", calendario="false",
              versao_ficha="pre-voo-0.1")])

    vitais = gerar_vitais()
    cont["vitais_minuto.csv"] = escrever("vitais_minuto.csv", CAMPOS_VITAIS, vitais)

    rng = random.Random("%s-cabine" % SEED)
    cabine = []
    for t in MINUTOS:
        alto = dentro(t, EP_CO2)
        valor = 4.1 if alto else round(2.4 + max(-0.05, min(0.05, rng.gauss(0, 0.02))), 2)
        cabine.append(dict(minuto_utc=iso(t), canal="co2", valor=valor,
                           unidade="mmHg", qualidade="bom",
                           cenario="co2_alto" if alto else ""))
    cont["cabine_minuto.csv"] = escrever("cabine_minuto.csv",
        ["minuto_utc", "canal", "valor", "unidade", "qualidade", "cenario"], cabine)

    cont["exame_kenji.csv"] = escrever("exame_kenji.csv",
        ["tripulante_id", "exame", "data", "delta_pct", "janela", "dentro_do_esperado"],
        [dict(tripulante_id="kenji", exame="dxa", data="2026-11-14",
              delta_pct="-1.2", janela="3 meses", dentro_do_esperado="true")])

    ouro = [l for l in vitais
            if l["qualidade"] == "bom" and l["excluir_treino_if"] == "false"]
    cont["ouro_vitais_normais.csv"] = escrever("ouro_vitais_normais.csv",
                                               CAMPOS_VITAIS, ouro)

    eps = [
        ("ep01", "sarah", "ciclo", EP_CICLO, "false",
         "Avisar só a Sarah: sintomas em dois dias ou já no trecho; estado ótimo; não compartilhar."),
        ("ep02", "elena", "hidratacao", EP_HIDRA, "false",
         "Lembrete de água para a Elena."),
        ("ep03", "sarah", "sensor_solto", EP_SENSOR, "true",
         "Perguntar à Sarah antes de alarmar; o kit confirma 97%."),
        ("ep04", "sarah", "fa", EP_FA, "true",
         "Abrir evento de arritmia; não usar esses minutos no Isolation Forest."),
        ("ep05", "kenji", "osso", EP_OSSO, "false",
         "Manter treino resistivo do Kenji; sem pergunta de ciclo."),
    ]
    cont["episodios.csv"] = escrever("episodios.csv",
        ["id", "tripulante_id", "cenario", "inicio_utc", "fim_utc",
         "excluir_treino_if", "o_que_o_mvp_deve_fazer"],
        [dict(id=e[0], tripulante_id=e[1], cenario=e[2], inicio_utc=iso(e[3][0]),
              fim_utc=iso(e[3][1]), excluir_treino_if=e[4],
              o_que_o_mvp_deve_fazer=e[5]) for e in eps])

    for nome, n in cont.items():
        print("%-26s %6d linhas" % (nome, n))


if __name__ == "__main__":
    main()
