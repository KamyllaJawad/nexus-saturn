"""AstroHealth OS · módulo de IA (Passo 5 e 6).

Predição de prevenção = REGRAS DETERMINÍSTICAS (ADR-002) + RAG no protocolo + Cosmo (Ollama) só para explicar.

- O motor de regras decide se existe um alerta. O LLM nunca decide (ADR-002).
- Nível de autonomia máximo: 2, sugerir (ADR-003). Nada é executado, e toda sugestão pede revisão humana.
- Cada alerta tem um humano responsável (ADR-004).
- Medicamento fica fora: a saída do LLM passa por um filtro e é trocada se citar fármaco ou dose.
- Saúde mental só é avaliada com consentimento e nunca passa pelo RAG ou pelo LLM (ADR-003 e ADR-007).

Sem dependências externas (só biblioteca padrão). Requer o Ollama local com
`nomic-embed-text` (embeddings) e `llama3.2:3b` (Cosmo).
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

# --------------------------------------------------------------------------- config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODELO_CHAT = os.environ.get("COSMO_MODELO", "llama3.2:3b")
MODELO_EMB = os.environ.get("EMB_MODELO", "nomic-embed-text")

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
BASE_CONHECIMENTO = RAIZ / "8-ia-base-conhecimento"
MANIFESTO = RAIZ / "8-ia-scripts" / "manifesto_documentos.csv"
INDICE = AQUI / "indice_rag.json"

AVISO = "Protótipo experimental com dados simulados. Não é dispositivo médico. A decisão final é sempre de um humano."

# Limites iniciais. NÃO são clínicos: devem ser revisados e aprovados pelo médico de voo (ADR-010).
LIMITES = {
    "sono_h_min": 6.0,       "dias_sono": 3,
    "agua_ml_min": 2000,     "dias_agua": 2,
    "exercicio_min_min": 60, "dias_exercicio": 2,
    "humor_max": 2,          "dias_humor": 3,   # humor de 1 (muito mal) a 5 (muito bem)
    "fc_delta_pct": 10.0,    "dias_fc": 3,      # FC de repouso acima da linha de base
    "rotina_pct_min": 70.0,  "dias_rotina": 2,
}

# --------------------------------------------------------------------------- Ollama
def _ollama(caminho: str, payload: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(
        OLLAMA_URL + caminho,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ollama_ok() -> dict:
    """Confere se o Ollama responde e se os dois modelos estão baixados."""
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=5) as r:
            nomes = [m["name"] for m in json.loads(r.read().decode("utf-8")).get("models", [])]
    except Exception as e:  # noqa: BLE001
        return {"ollama": False, "erro": str(e)}
    return {
        "ollama": True,
        "chat": any(n.startswith(MODELO_CHAT) for n in nomes),
        "embeddings": any(n.startswith(MODELO_EMB) for n in nomes),
    }


def _embed(textos: list[str], prefixo: str) -> list[list[float]]:
    # nomic-embed-text espera o prefixo search_document: / search_query:
    r = _ollama("/api/embed", {"model": MODELO_EMB, "input": [prefixo + t for t in textos]})
    return r["embeddings"]


# --------------------------------------------------------------------------- RAG
def _temas_excluidos() -> set[str]:
    """Arquivos que o manifesto marcou como 'irrelevante' não entram no índice."""
    fora: set[str] = set()
    if MANIFESTO.exists():
        with open(MANIFESTO, encoding="utf-8-sig", newline="") as f:
            for linha in csv.DictReader(f):
                if linha.get("tema") == "irrelevante":
                    fora.add(linha["arquivo"])
    return fora


def _trechos(texto: str, maximo: int = 1200) -> list[str]:
    """Divide por parágrafos, juntando até ~1200 caracteres por trecho."""
    saida, atual = [], ""
    for p in re.split(r"\n\s*\n", texto):
        p = p.strip()
        if not p:
            continue
        while len(p) > maximo:  # parágrafo gigante
            saida.append(p[:maximo])
            p = p[maximo:]
        if len(atual) + len(p) + 2 > maximo and atual:
            saida.append(atual)
            atual = ""
        atual = (atual + "\n\n" + p).strip()
    if atual:
        saida.append(atual)
    return [s for s in saida if len(s) > 80]


_TEMAS_RX = {  # mesmas palavras-chave de 8-ia-scripts/05_construir_indice_rag.ps1
    "hidratacao": (re.compile(r"hydrat|dehydrat|fluid (intake|loss|shift|balance|volume)|water intake|drinking water|thirst|urine output|hidrata", re.I), 1),
    "saude_mental": (re.compile(r"mental health|behavio(u)?ral health|psycholog|depress|anxiety|mood|cognitive (perform|function|decline)|isolation|confinement|sleep|circadian|fatigue|sa[uú]de mental|comportament", re.I), 2),
    "exercicio": (re.compile(r"exercise|treadmill|resistive|\bARED\b|ergometer|aerobic|muscle (atrophy|loss|strength)|bone (loss|density)|exerc[ií]cio", re.I), 2),
}


def _temas_do_trecho(texto: str) -> list[str]:
    t = [k for k, (rx, minimo) in _TEMAS_RX.items() if len(rx.findall(texto)) >= minimo]
    return t or ["geral"]


def construir_indice() -> dict:
    """Lê os .md/.txt de 8-ia-base-conhecimento (só a pasta raiz, sem _duplicados e sem README),
    gera embeddings no Ollama e grava indice_rag.json. (Alternativa em PowerShell, sem Python:
    8-ia-scripts/05_construir_indice_rag.ps1, que divide por títulos.)"""
    fora = _temas_excluidos()
    itens: list[dict] = []
    usados, ignorados = [], []
    for arq in sorted(BASE_CONHECIMENTO.iterdir()):
        if not arq.is_file() or arq.suffix.lower() not in (".md", ".txt") or arq.name.lower() == "readme.md":
            continue
        if arq.name in fora:
            ignorados.append(arq.name)
            continue
        usados.append(arq.name)
        for t in _trechos(arq.read_text(encoding="utf-8", errors="ignore")):
            itens.append({"fonte": arq.name, "secao": None, "pagina": None, "temas": _temas_do_trecho(t), "texto": t})
    for i in range(0, len(itens), 16):  # lotes de 16
        lote = itens[i : i + 16]
        for it, v in zip(lote, _embed([x["texto"] for x in lote], "search_document: ")):
            it["v"] = v
    INDICE.write_text(json.dumps({"modelo": MODELO_EMB, "itens": itens}), encoding="utf-8")
    return {"documentos": len(usados), "trechos": len(itens), "ignorados_irrelevantes": ignorados}


_cache: dict[str, Any] = {}


def _carregar_indice() -> list[dict]:
    if "itens" not in _cache:
        if not INDICE.exists():
            raise FileNotFoundError("Índice RAG não existe. Rode construir_indice() (POST /ia/indice).")
        _cache["itens"] = json.loads(INDICE.read_text(encoding="utf-8"))["itens"]
    return _cache["itens"]


def _cos(a: list[float], b: list[float]) -> float:
    d = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return d / (na * nb) if na and nb else 0.0


TEMAS = ("hidratacao", "saude_mental", "exercicio")
# Cada tela só consulta o seu tema (Trilha B). saude_mental exige consentimento (ADR-007).
TELAS = {"hidratacao": "hidratacao", "saude_mental": "saude_mental", "exercicios": "exercicio"}


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def _chamar_gemini_rest(prompt: str, api_key: Optional[str] = None) -> Optional[str]:
    """Chama a API do Google Gemini como fallback na nuvem (Streamlit Cloud)."""
    key = api_key or GEMINI_API_KEY or os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300},
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            res = json.loads(r.read().decode("utf-8"))
            return res["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def _buscar_fallback_tokens(consulta: str, itens: list[dict], k: int = 4) -> list[tuple[float, dict]]:
    """Busca léxica quando o Ollama local estiver indisponível (ex: Streamlit Cloud)."""
    tokens = set(re.findall(r"\w{3,}", consulta.lower()))
    if not tokens:
        return [(0.5, it) for it in itens[:k]]
    pontuados = []
    for it in itens:
        texto_low = (str(it.get("fonte", "")) + " " + str(it.get("secao", "")) + " " + it["texto"]).lower()
        score = sum(texto_low.count(tok) for tok in tokens)
        pontuados.append((float(score), it))
    pontuados.sort(key=lambda p: p[0], reverse=True)
    return pontuados[:k]


def buscar(consulta: str, k: int = 3, tema: Optional[str] = None) -> list[dict]:
    """Devolve os k trechos mais próximos da consulta, com a fonte e a seção.
    tema: filtra os trechos marcados com esse tema no índice (hidratacao, saude_mental, exercicio)."""
    itens = _carregar_indice()
    if tema:
        itens = [it for it in itens if tema in (it.get("temas") or [])]
    if not itens:
        return []
    try:
        q = _embed([consulta], "search_query: ")[0]
        pontuados = sorted(((_cos(q, it["v"]), it) for it in itens), key=lambda p: p[0], reverse=True)[:k]
    except Exception:
        pontuados = _buscar_fallback_tokens(consulta, itens, k=k)

    return [{"fonte": it["fonte"], "secao": it.get("secao"), "pagina": it.get("pagina"),
             "trecho": it["texto"][:1400], "similaridade": round(s, 3)} for s, it in pontuados]


def responder_tela(tela: str, pergunta: str, consentimento_saude_mental: bool = False, k: int = 4) -> dict:
    """RAG de uma tela: busca só no tema da tela e a Cosmo responde citando [n].
    O que o RAG não souber, a Cosmo admite. Medicamento e dose são filtrados (ADR-003)."""
    if tela not in TELAS:
        raise ValueError(f"Tela desconhecida: {tela}. Use uma de {list(TELAS)}.")
    if tela == "saude_mental" and not consentimento_saude_mental:
        return {"tela": tela, "bloqueado": True, "resposta": None,
                "motivo": "Saúde mental só é consultada com o consentimento do astronauta (ADR-007).", "aviso": AVISO}
    trechos = buscar(pergunta, k=k, tema=TELAS[tela])
    if not trechos:
        return {"tela": tela, "resposta": "Não encontrei essa informação nos documentos.", "fontes": [], "aviso": AVISO}
    ctx = "\n\n".join(f"[{i}] (fonte: {t['fonte']}) {t['trecho']}" for i, t in enumerate(trechos, 1))
    prompt = (
        "Responda em português, em no máximo 4 frases, usando SOMENTE os trechos abaixo. Cite a fonte no formato [n] "
        "após cada afirmação. Se os trechos não trouxerem a resposta, responda exatamente: "
        "'Não encontrei essa informação nos documentos.' Não invente números. NUNCA cite medicamentos ou doses; "
        f"para isso, diga que a decisão é do oficial médico.\n\nPERGUNTA: {pergunta}\n\nTRECHOS:\n{ctx}"
    )
    try:
        r = _ollama("/api/generate", {"model": MODELO_CHAT, "prompt": prompt, "stream": False,
                                      "options": {"temperature": 0, "num_predict": 260}})
        resposta = _filtrar_farmaco(r.get("response", "").strip())
    except Exception as e:  # noqa: BLE001
        resposta = None
        trechos = trechos  # os trechos ainda ajudam a tela mesmo sem a Cosmo
        return {"tela": tela, "resposta": resposta, "erro": f"Ollama indisponível: {e}", "fontes": trechos, "aviso": AVISO}
    return {"tela": tela, "resposta": resposta, "fontes": trechos, "aviso": AVISO}


def chat_cosmo(
    mensagem: str,
    tema: Optional[str] = None,
    consentimento_saude_mental: bool = False,
    k: int = 4,
    api_key: Optional[str] = None,
) -> dict:
    """Chatbot interativo da Cosmo (relógio, tablet de bordo, console ou Streamlit).
    Usa o RAG e responde de forma empática e precisa, sem diagnósticos punitivos nem medicamentos."""
    if tema == "saude_mental" and not consentimento_saude_mental:
        return {
            "resposta": "Para conversar sobre saúde mental e bem-estar, preciso da sua autorização no relógio (ADR-007).",
            "fontes": [],
            "aviso": AVISO,
        }
    trechos = buscar(mensagem, k=k, tema=tema)
    ctx = "\n\n".join(f"[{i}] ({t['fonte']}): {t['trecho']}" for i, t in enumerate(trechos, 1)) if trechos else "(sem trechos específicos)"
    prompt = (
        "Você é a Cosmo, a assistente de IA amigável e atenciosa de suporte à saúde dos astronautas a bordo.\n"
        "Responda à mensagem do astronauta em português, em 2 a 4 frases, de forma acolhedora, objetiva e prática.\n"
        "Se houver informações relevantes nos trechos abaixo, use-as e cite a fonte no formato [n]. "
        "Se a pergunta exigir informação que não está nos documentos, admita gentilmente sem inventar.\n"
        "REGRA CRÍTICA: NUNCA prescreva medicamentos, remédios ou dosagens. Havendo qualquer sintoma grave, "
        f"oriente procurar o oficial médico da missão.\n\n"
        f"MENSAGEM DO ASTRONAUTA: {mensagem}\n\n"
        f"TRECHOS DE PROTOCOLO:\n{ctx}"
    )
    # 1. Tenta Ollama local
    try:
        r = _ollama(
            "/api/generate",
            {"model": MODELO_CHAT, "prompt": prompt, "stream": False, "options": {"temperature": 0.2, "num_predict": 250}},
            timeout=10,
        )
        resp = _filtrar_farmaco(r.get("response", "").strip())
        if resp:
            return {"resposta": resp, "fontes": trechos, "aviso": AVISO, "motor": "Ollama local"}
    except Exception:
        pass

    # 2. Fallback na nuvem (Gemini API)
    resp_gemini = _chamar_gemini_rest(prompt, api_key=api_key)
    if resp_gemini:
        return {
            "resposta": _filtrar_farmaco(resp_gemini),
            "fontes": trechos,
            "aviso": AVISO,
            "motor": "Google Gemini (Nuvem)",
        }

    # 3. Fallback informativo demonstrando o RAG mesmo sem LLM online
    msg_demo = (
        "🔍 **Modo Protocolo RAG:** Os trechos oficiais da NASA foram recuperados com sucesso para esta consulta. "
        "Para síntese textual pela IA na nuvem, adicione uma chave `GEMINI_API_KEY` na barra lateral ou nas configurações do Streamlit."
    )
    return {"resposta": msg_demo, "fontes": trechos, "aviso": AVISO, "motor": "Protocolo RAG direto"}


# --------------------------------------------------------------------------- regras
@dataclass
class Alerta:
    id: str
    tema: str                 # sono | hidratacao | exercicio | rotina | frequencia_cardiaca | saude_mental
    nivel: str                # atencao | alerta
    titulo: str
    evidencia: str            # números que dispararam a regra
    responsavel: str          # humano responsável (ADR-004)
    autonomia: int = 2        # ADR-003: no máximo "sugerir"
    status: str = "pendente_revisao_humana"
    compartilhavel_com_terra: bool = True
    orientacao: list[dict] = field(default_factory=list)  # trechos do protocolo (RAG)
    explicacao: Optional[str] = None                      # texto da Cosmo, só para explicar


def _sequencia_final(dias: list[dict], cond: Callable[[dict], Optional[bool]]) -> int:
    """Quantos dias seguidos, até o último registro, cumprem a condição. Dado ausente (None) quebra a sequência."""
    n = 0
    for d in reversed(dias):
        if cond(d) is True:
            n += 1
        else:
            break
    return n


def _nivel(seq: int, minimo: int) -> str:
    return "alerta" if seq >= minimo + 2 else "atencao"


def _lt(campo: str, limite: float) -> Callable[[dict], Optional[bool]]:
    return lambda d: None if d.get(campo) is None else d[campo] < limite


def _regra_sono(dias, L):
    seq = _sequencia_final(dias, _lt("sono_h", L["sono_h_min"]))
    if seq >= L["dias_sono"]:
        m = sum(d["sono_h"] for d in dias[-seq:]) / seq
        return Alerta("sono_baixo", "sono", _nivel(seq, L["dias_sono"]), "Sono abaixo do mínimo",
                      f"{seq} dias seguidos com menos de {L['sono_h_min']:g} h de sono (média {m:.1f} h).",
                      "Oficial médico" if seq >= L["dias_sono"] + 2 else "Astronauta")
    return None


def _regra_agua(dias, L):
    seq = _sequencia_final(dias, _lt("agua_ml", L["agua_ml_min"]))
    if seq >= L["dias_agua"]:
        m = sum(d["agua_ml"] for d in dias[-seq:]) / seq
        return Alerta("hidratacao_baixa", "hidratacao", _nivel(seq, L["dias_agua"]), "Hidratação abaixo do mínimo",
                      f"{seq} dias seguidos abaixo de {L['agua_ml_min']:g} mL (média {m:.0f} mL).", "Astronauta")
    return None


def _regra_exercicio(dias, L):
    seq = _sequencia_final(dias, _lt("exercicio_min", L["exercicio_min_min"]))
    if seq >= L["dias_exercicio"]:
        m = sum(d["exercicio_min"] for d in dias[-seq:]) / seq
        return Alerta("exercicio_baixo", "exercicio", _nivel(seq, L["dias_exercicio"]),
                      "Exercício abaixo do mínimo (perda óssea e muscular em microgravidade)",
                      f"{seq} dias seguidos abaixo de {L['exercicio_min_min']:g} min (média {m:.0f} min).",
                      "Oficial médico" if seq >= L["dias_exercicio"] + 2 else "Astronauta")
    return None


def _regra_rotina(dias, L):
    def pct(d):
        p, f = d.get("tarefas_planejadas"), d.get("tarefas_feitas")
        return None if not p or f is None else f / p * 100 < L["rotina_pct_min"]

    seq = _sequencia_final(dias, pct)
    if seq >= L["dias_rotina"]:
        pend = dias[-1].get("pendentes") or []
        extra = f" Pendentes hoje: {', '.join(pend)}." if pend else ""
        return Alerta("rotina_atrasada", "rotina", _nivel(seq, L["dias_rotina"]), "Rotina de saúde atrasada",
                      f"{seq} dias seguidos com menos de {L['rotina_pct_min']:g}% das tarefas feitas.{extra}", "Astronauta")
    return None


def _regra_fc(dias, L):
    k = L["dias_fc"]
    base = [d["fc_repouso"] for d in dias[:-k] if d.get("fc_repouso") is not None]
    if len(base) < 3:
        return None  # sem linha de base suficiente: não alerta (ADR-009: não alarmar sem dado)
    media = sum(base) / len(base)
    teto = media * (1 + L["fc_delta_pct"] / 100)
    seq = _sequencia_final(dias, lambda d: None if d.get("fc_repouso") is None else d["fc_repouso"] > teto)
    if seq >= k:
        ult = dias[-1]["fc_repouso"]
        return Alerta("fc_repouso_subindo", "frequencia_cardiaca", _nivel(seq, k), "FC de repouso acima da linha de base",
                      f"{seq} dias seguidos acima de {teto:.0f} bpm (linha de base {media:.0f} bpm, último {ult:.0f} bpm).",
                      "Oficial médico")
    return None


def _regra_humor(dias, L):
    seq = _sequencia_final(dias, lambda d: None if d.get("humor") is None else d["humor"] <= L["humor_max"])
    if seq >= L["dias_humor"]:
        # ADR-007: fica só com o astronauta; sem texto de RAG/LLM (ADR-003)
        return Alerta("humor_baixo", "saude_mental", "atencao", "Seu humor está baixo há alguns dias",
                      f"{seq} dias seguidos com humor baixo. Isso fica só com você até você autorizar o compartilhamento.",
                      "Astronauta", autonomia=1, compartilhavel_com_terra=False)
    return None


REGRAS = [_regra_sono, _regra_agua, _regra_exercicio, _regra_rotina, _regra_fc]

CONSULTAS_RAG = {  # em inglês, porque a base de conhecimento é quase toda em inglês
    "sono": "astronaut sleep loss fatigue countermeasures circadian rhythm schedule",
    "hidratacao": "astronaut hydration fluid intake dehydration microgravity",
    "exercicio": "exercise countermeasures bone loss muscle atrophy astronauts spaceflight",
    "rotina": "crew health routine medical checks monitoring astronaut schedule",
    "frequencia_cardiaca": "cardiovascular deconditioning heart rate astronauts spaceflight",
}

# --------------------------------------------------------------------------- Cosmo
_FARMACO = re.compile(
    r"\b(mg|mcg|ml/kg|dosagem|comprimid\w*|medicament\w*|medicaç\w*|rem[eé]dio\w*|analg[eé]sic\w*|"
    r"ibuprofeno|paracetamol|dipirona|melatonina|zolpidem|antidepressiv\w*|ansiol[ií]tic\w*|sedativ\w*|"
    r"medication\w*|drug\w*|pill\w*|tablet\w*|prescri\w+)\b",
    re.IGNORECASE,
)
_SEGURO = ("Não posso falar de medicamentos nem de doses. Essa decisão é do oficial médico: converse com ele.")


def _filtrar_farmaco(texto: str) -> str:
    return _SEGURO if _FARMACO.search(texto) else texto


def _cosmo_explica(a: Alerta) -> Optional[str]:
    trechos = "\n---\n".join(f"[{o['fonte']}] {o['trecho']}" for o in a.orientacao) or "(sem trechos)"
    prompt = (
        "Você é a Cosmo, assistente de saúde de astronautas. Explique em português, em no máximo 3 frases simples, "
        "por que este alerta apareceu e que hábito pode ajudar, usando SOMENTE os trechos. "
        "NUNCA cite medicamentos, doses ou diagnósticos. Termine lembrando que a decisão é de "
        f"{a.responsavel.lower()}.\n\nALERTA: {a.titulo}. {a.evidencia}\n\nTRECHOS:\n{trechos}"
    )
    try:
        r = _ollama("/api/generate", {"model": MODELO_CHAT, "prompt": prompt, "stream": False,
                                      "options": {"temperature": 0.2, "num_predict": 220}}, timeout=300)
        return _filtrar_farmaco(r.get("response", "").strip()) or None
    except Exception:  # noqa: BLE001  (o alerta existe sem o LLM; ele só explica)
        return None


# --------------------------------------------------------------------------- API do módulo
def avaliar_prevencao(
    dias: list[dict],
    consentimento_saude_mental: bool = False,
    usar_rag: bool = True,
    explicar: bool = True,
    limites: Optional[dict] = None,
) -> dict:
    """dias: lista de registros diários, do mais antigo ao mais recente. Campos (todos opcionais):
    data, sono_h, agua_ml, exercicio_min, humor (1..5), fc_repouso, tarefas_planejadas, tarefas_feitas, pendentes.
    """
    L = {**LIMITES, **(limites or {})}
    dias = sorted(dias, key=lambda d: str(d.get("data", "")))
    alertas = [a for a in (r(dias, L) for r in REGRAS) if a]
    if consentimento_saude_mental:  # ADR-007: sem consentimento, nem avalia
        h = _regra_humor(dias, L)
        if h:
            alertas.append(h)

    if usar_rag:
        for a in alertas:
            if a.tema in CONSULTAS_RAG:
                try:
                    a.orientacao = buscar(CONSULTAS_RAG[a.tema], k=2)
                except Exception:  # noqa: BLE001  (índice ausente ou Ollama parado)
                    a.orientacao = []
            if explicar and a.orientacao:
                a.explicacao = _cosmo_explica(a)

    alertas.sort(key=lambda a: 0 if a.nivel == "alerta" else 1)
    return {"dias_analisados": len(dias), "total_alertas": len(alertas),
            "alertas": [asdict(a) for a in alertas], "aviso": AVISO}


def status() -> dict:
    return {**ollama_ok(), "indice_rag": INDICE.exists(), "limites": LIMITES}

