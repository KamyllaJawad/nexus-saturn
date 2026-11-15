"""Processamento de sinal usado no treino e a bordo: picos R, atributos de RR
(entrada do M1), atributos de qualidade (entrada do M2), ruído sintético e um
gerador de ECG para quando o CinC 2017 não está disponível.

O mesmo código roda no treino em lote e no `ia.analisar`, para o modelo ver a
bordo exatamente os atributos em que foi treinado.
"""
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from scipy.stats import kurtosis

from .config import FS

ATRIBUTOS_RR = ["rr_irregular_30s", "fc_media", "sdnn", "rmssd", "pnn50", "cv_rr",
                "sd1", "sd2", "razao_sd", "entropia_amostral", "rr_min_max",
                "mad_delta_rr", "pnn20_rel", "entropia_delta_rr", "fracao_viradas",
                "fracao_fora_da_mediana", "rr_irregular_limpo", "cv_limpo"]
ATRIBUTOS_QUALIDADE = ["curtose", "fracao_achatada", "potencia_baixa_freq",
                       "potencia_alta_freq", "picos_r_por_s", "regularidade_picos",
                       "fracao_saturada"]

_B, _A = butter(2, [5 / (FS / 2), 18 / (FS / 2)], btype="band")


def picos_r(ecg: np.ndarray, fs: int = FS) -> np.ndarray:
    """Índices dos picos R: passa-faixa 5–18 Hz, energia e limiar adaptativo."""
    if len(ecg) < fs:
        return np.array([], dtype=int)
    x = filtfilt(_B, _A, ecg.astype(float))
    energia = x * x
    janela = max(1, int(0.12 * fs))
    env = np.convolve(energia, np.ones(janela) / janela, mode="same")
    teto = np.percentile(env, 98)
    if teto <= 0:
        return np.array([], dtype=int)
    picos, _ = find_peaks(env, distance=int(0.25 * fs), height=0.25 * teto)
    if len(picos) > 4:
        # Busca de volta: num buraco maior que 1,6x o RR mediano, aceita picos menores.
        rr_med = np.median(np.diff(picos))
        folga = int(0.25 * fs)
        extras = []
        for a, b in zip(picos[:-1], picos[1:]):
            if b - a > 1.6 * rr_med:
                trecho = env[a + folga: b - folga]
                if len(trecho) > 3:
                    cand, _ = find_peaks(trecho, distance=folga, height=0.08 * teto)
                    extras.extend(cand + a + folga)
        if extras:
            picos = np.sort(np.concatenate([picos, np.array(extras, dtype=int)]))
    return picos


def _entropia_amostral(x: np.ndarray, m: int = 2, r_frac: float = 0.2) -> float:
    n = len(x)
    if n < m + 3:
        return 0.0
    r = r_frac * (np.std(x) + 1e-9)

    def conta(mm):
        emb = np.array([x[i:i + mm] for i in range(n - mm)])
        d = np.max(np.abs(emb[:, None, :] - emb[None, :, :]), axis=2)
        return (np.sum(d <= r) - len(emb)) / 2.0

    b, a = conta(m), conta(m + 1)
    if a <= 0 or b <= 0:
        return 2.5
    return float(-np.log(a / b))


def atributos_rr(rr_s: np.ndarray) -> dict:
    """Atributos de variabilidade a partir dos intervalos RR em segundos."""
    rr = np.asarray(rr_s, dtype=float)
    rr = rr[(rr > 0.25) & (rr < 2.5)]
    if len(rr) < 5:
        return {k: 0.0 for k in ATRIBUTOS_RR}
    d = np.diff(rr)
    media = rr.mean()
    med = np.median(rr)
    rel = np.abs(d) / med
    limpo = rr[(rr > 0.6 * med) & (rr < 1.5 * med)]  # sem batimento perdido nem duplicado
    dl = np.diff(limpo) if len(limpo) > 3 else np.array([0.0])
    hist, _ = np.histogram(np.clip(d / med, -0.6, 0.6), bins=16, range=(-0.6, 0.6))
    ph = hist[hist > 0] / hist.sum()
    viradas = float(np.mean((d[1:] * d[:-1]) < 0)) if len(d) > 2 else 0.0
    sdnn = rr.std()
    sd1 = np.sqrt(0.5) * d.std()
    sd2 = np.sqrt(max(2 * sdnn ** 2 - 0.5 * d.std() ** 2, 1e-12))
    return {
        "rr_irregular_30s": float(np.mean(np.abs(d)) / media),
        "fc_media": float(60.0 / media),
        "sdnn": float(sdnn * 1000),
        "rmssd": float(np.sqrt(np.mean(d ** 2)) * 1000),
        "pnn50": float(np.mean(np.abs(d) > 0.05)),
        "cv_rr": float(sdnn / media),
        "sd1": float(sd1 * 1000),
        "sd2": float(sd2 * 1000),
        "razao_sd": float(sd1 / sd2),
        "entropia_amostral": _entropia_amostral(rr[:120]),
        "rr_min_max": float(rr.min() / rr.max()),
        "mad_delta_rr": float(np.median(rel)),
        "pnn20_rel": float(np.mean(rel > 0.08)),
        "entropia_delta_rr": float(-(ph * np.log(ph)).sum()),
        "fracao_viradas": viradas,
        "fracao_fora_da_mediana": float(1 - len(limpo) / len(rr)),
        "rr_irregular_limpo": float(np.mean(np.abs(dl)) / med),
        "cv_limpo": float(limpo.std() / med) if len(limpo) > 3 else 0.0,
    }


def atributos_qualidade(ecg: np.ndarray, fs: int = FS) -> dict:
    """Atributos de morfologia: sinal achatado, deriva, ruído e picos R detectáveis."""
    x = np.asarray(ecg, dtype=float)
    faixa = np.percentile(x, 99.5) - np.percentile(x, 0.5)
    if faixa <= 1e-9:
        return dict(curtose=0.0, fracao_achatada=1.0, potencia_baixa_freq=0.0,
                    potencia_alta_freq=0.0, picos_r_por_s=0.0, regularidade_picos=0.0,
                    fracao_saturada=1.0)
    # "Achatado" é um trecho de 0,4 s em que o sinal não se mexe; a linha
    # isoelétrica normal entre batimentos não conta.
    passo = int(0.4 * fs)
    blocos = x[: len(x) // passo * passo].reshape(-1, passo)
    achatada = float(np.mean((blocos.max(axis=1) - blocos.min(axis=1)) < 0.012 * faixa))
    saturada = float(np.mean((x >= x.max() - 1e-3 * faixa) | (x <= x.min() + 1e-3 * faixa)))
    espectro = np.abs(np.fft.rfft(x - x.mean())) ** 2
    freq = np.fft.rfftfreq(len(x), 1 / fs)
    total = espectro.sum() + 1e-12
    picos = picos_r(x, fs)
    rr = np.diff(picos) / fs if len(picos) > 2 else np.array([])
    plausivel = float(np.mean((rr > 0.3) & (rr < 1.8))) if len(rr) else 0.0
    return {
        "curtose": float(kurtosis(x)),
        "fracao_achatada": achatada,
        "potencia_baixa_freq": float(espectro[freq < 1.0].sum() / total),
        "potencia_alta_freq": float(espectro[freq > 40.0].sum() / total),
        "picos_r_por_s": float(len(picos) / (len(x) / fs)),
        "regularidade_picos": plausivel,
        "fracao_saturada": saturada,
    }


# ------------------------------------------------------------------ sintéticos
def ecg_sintetico(rr_s: np.ndarray, fs: int = FS, fa: bool = False, rng=None) -> np.ndarray:
    """ECG de uma derivação montado batimento a batimento (P, QRS, T gaussianas).
    Na fibrilação atrial a onda P some e entra uma ondulação fina de base."""
    rng = rng or np.random.default_rng()
    n = int(np.sum(rr_s) * fs) + fs
    t = np.arange(n) / fs
    x = np.zeros(n)
    inicio = 0.4
    for rr in rr_s:
        ondas = [(-0.03, 0.010, -0.12), (0.0, 0.011, 1.0), (0.03, 0.012, -0.22),
                 (min(0.26, 0.38 * rr), 0.045, 0.28)]
        if not fa:
            ondas.append((-0.17, 0.022, 0.13))
        for desloc, larg, amp in ondas:
            c = inicio + desloc
            i0, i1 = max(0, int((c - 5 * larg) * fs)), min(n, int((c + 5 * larg) * fs))
            x[i0:i1] += amp * np.exp(-0.5 * ((t[i0:i1] - c) / larg) ** 2)
        inicio += rr
    if fa:
        x += 0.04 * np.sin(2 * np.pi * rng.uniform(5, 8) * t + rng.uniform(0, 6))
    x += 0.012 * rng.standard_normal(n) + 0.03 * np.sin(2 * np.pi * 0.25 * t)
    return x[: int(np.sum(rr_s) * fs)]


def rr_sintetico(classe: str, segundos: float, fc: float, rng) -> np.ndarray:
    """Série RR: sinusal com arritmia respiratória, FA irregular ou ritmo com extrassístoles."""
    base, rr, t = 60.0 / fc, [], 0.0
    while t < segundos:
        if classe == "fa":
            v = base * rng.uniform(0.6, 1.45)
        elif classe == "outro":
            v = base * (1 + 0.04 * np.sin(2 * np.pi * 0.25 * t) + 0.02 * rng.standard_normal())
            if rng.random() < 0.12:
                rr.append(v * 0.6); t += v * 0.6
                v = v * 1.4
        else:
            v = base * (1 + 0.04 * np.sin(2 * np.pi * 0.25 * t) + 0.015 * rng.standard_normal())
        v = float(np.clip(v, 0.3, 2.0))
        rr.append(v); t += v
    return np.array(rr)


def sujar(ecg: np.ndarray, rng, fs: int = FS, forca: float = 1.0) -> np.ndarray:
    """Ruído de relógio folgado: deriva de linha de base, movimento e sinal achatado."""
    x = np.array(ecg, dtype=float)
    n = len(x)
    amp = (np.percentile(x, 99.5) - np.percentile(x, 0.5)) or 1.0
    t = np.arange(n) / fs
    tipos = rng.choice(["deriva", "movimento", "achatado"], size=rng.integers(2, 4), replace=False)
    if "deriva" in tipos:
        x += forca * amp * rng.uniform(0.8, 2.0) * np.sin(2 * np.pi * rng.uniform(0.1, 0.5) * t + rng.uniform(0, 6))
    if "movimento" in tipos:
        for _ in range(rng.integers(3, 9)):
            i = rng.integers(0, n - fs)
            dur = rng.integers(int(0.3 * fs), int(1.5 * fs))
            x[i:i + dur] += forca * amp * rng.uniform(1.0, 3.0) * rng.standard_normal(len(x[i:i + dur]))
    if "achatado" in tipos:
        for _ in range(rng.integers(1, 4)):
            i = rng.integers(0, n - fs)
            dur = rng.integers(int(1.5 * fs), int(6 * fs))
            x[i:i + dur] = x[i]
    return x


def expandir_if(X: np.ndarray, mediana: np.ndarray, mad: np.ndarray) -> np.ndarray:
    """Vetor que entra no Isolation Forest: os sinais e o desvio conjunto (soma
    dos |z| robustos). Sem ele a floresta não vê o tamanho do desvio: um ponto
    um pouco fora da caixa cai na mesma folha que o canto da caixa."""
    X = np.atleast_2d(np.asarray(X, dtype=float))
    z = 0.6745 * (X - mediana) / mad
    return np.hstack([X, np.abs(z).sum(axis=1, keepdims=True)])
