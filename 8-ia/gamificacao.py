"""AstroHealth OS · Módulo de Gamificação (Bioma Cooperativo e Elo Terra-Espaço).

Conforme definido na arquitetura do projeto:
1. Bioma cooperativo: agrega métricas de adesão coletiva da tripulação (hidratação, exercício, sono, rotina)
   em um índice de vitalidade do ecossistema espacial (Missões da Estufa).
2. Elo Terra-espaço: sincroniza metas e incentivos entre o astronauta e seus familiares na Terra.
   Respeita rigorosamente a ADR-007: só cruza dados que o astronauta consentiu explicitamente em compartilhar.

Toda a lógica de pontuação é determinística. O Ollama local (llama3.2:3b) atua como a Cosmo,
gerando a síntese narrativa cooperativa e as mensagens de incentivo, sem aconselhamento médico punitivo.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODELO_CHAT = os.environ.get("COSMO_MODELO", "llama3.2:3b")


def _ollama_generate(prompt: str, max_tokens: int = 150) -> Optional[str]:
    try:
        payload = {
            "model": MODELO_CHAT,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read().decode("utf-8"))
            return res.get("response", "").strip()
    except Exception:
        return None


# --------------------------------------------------------------------------- Bioma Cooperativo
def calcular_bioma_cooperativo(tripulantes: List[Dict[str, Any]], gerar_narrativa_ollama: bool = True) -> Dict[str, Any]:
    """Calcula a vitalidade do Bioma Cooperativo (Estufa Espacial) a partir da adesão coletiva da tripulação.
    tripulantes: lista de dicionários contendo nome, agua_ml (meta: 2400), exercicio_min (meta: 60), sono_h (meta: 7.0).
    """
    if not tripulantes:
        return {"vitalidade_pct": 0, "status": "sem_dados", "fase_estufa": "latente"}

    taxas_agua, taxas_exercicio, taxas_sono = [], [], []

    for t in tripulantes:
        # metas de referência padrão
        meta_agua = t.get("meta_agua_ml", 2400)
        meta_ex = t.get("meta_exercicio_min", 60)
        meta_sono = t.get("meta_sono_h", 7.0)

        taxas_agua.append(min(1.0, (t.get("agua_ml", 0) / meta_agua) if meta_agua else 0))
        taxas_exercicio.append(min(1.0, (t.get("exercicio_min", 0) / meta_ex) if meta_ex else 0))
        taxas_sono.append(min(1.0, (t.get("sono_h", 0) / meta_sono) if meta_sono else 0))

    media_agua = sum(taxas_agua) / len(taxas_agua)
    media_ex = sum(taxas_exercicio) / len(taxas_exercicio)
    media_sono = sum(taxas_sono) / len(taxas_sono)

    # Índice de Vitalidade Global ponderado (Água 35%, Exercício 35%, Sono 30%)
    vitalidade_pct = round((media_agua * 0.35 + media_ex * 0.35 + media_sono * 0.30) * 100, 1)

    if vitalidade_pct >= 85:
        fase_estufa = "Florescendo (Ecossistema Vibrante)"
        status_bioma = "Excelente"
    elif vitalidade_pct >= 65:
        fase_estufa = "Crescendo (Estável)"
        status_bioma = "Bom"
    elif vitalidade_pct >= 45:
        fase_estufa = "Brotando (Necessita Atenção)"
        status_bioma = "Moderado"
    else:
        fase_estufa = "Murchando (Déficit Coletivo)"
        status_bioma = "Crítico"

    narrativa = None
    if gerar_narrativa_ollama:
        prompt = (
            f"Você é a Cosmo, IA de suporte da tripulação espacial. O Bioma Cooperativo da estufa da nave está em "
            f"{vitalidade_pct}% de vitalidade ({status_bioma}). Adesão média: Hidratação {media_agua*100:.0f}%, "
            f"Exercício {media_ex*100:.0f}%, Sono {media_sono*100:.0f}%. "
            f"Gere uma mensagem curta em português (2 frases), calorosa e cooperativa para o visor do smartwatch, "
            f"incentivando o trabalho em equipe na estufa."
        )
        narrativa = _ollama_generate(prompt, max_tokens=100)

    return {
        "vitalidade_pct": vitalidade_pct,
        "status": status_bioma,
        "fase_estufa": fase_estufa,
        "tripulantes_ativos": len(tripulantes),
        "medias_adesao_pct": {
            "hidratacao": round(media_agua * 100, 1),
            "exercicio": round(media_ex * 100, 1),
            "sono": round(media_sono * 100, 1),
        },
        "narrativa_cosmo": narrativa,
    }


# --------------------------------------------------------------------------- Elo Terra-Espaço
def calcular_elo_terra_espaco(
    astronauta: Dict[str, Any],
    familiar: Dict[str, Any],
    consentimento: Dict[str, bool],
    gerar_mensagem_ollama: bool = True,
) -> Dict[str, Any]:
    """Cruza atividades do astronauta com o familiar na Terra (ex: Desafio Corrida Terra-Órbita).
    consentimento: chaves booleanas como 'compartilhar_atividades', 'compartilhar_sinais_vitais', 'permitir_mensagens'.
    Se consentimento['compartilhar_atividades'] for False, nenhum dado físico é compartilhado (ADR-007).
    """
    pode_compartilhar_atividades = consentimento.get("compartilhar_atividades", False)

    # Desafio Cooperativo Padrão: Corrida Terra–Órbita (Meta conjunta de km na semana)
    km_meta_conjunta = 60.0
    km_astro = astronauta.get("km_esteira", 0.0) if pode_compartilhar_atividades else 0.0
    km_fam = familiar.get("km_corrida", 0.0)
    km_total = round(km_astro + km_fam, 1)
    progresso_pct = min(100.0, round((km_total / km_meta_conjunta) * 100, 1))

    mensagem_incentivo = None
    if gerar_mensagem_ollama and consentimento.get("permitir_mensagens", True):
        prompt = (
            f"Você é a Cosmo facilitando o Elo Terra-Espaço entre o astronauta {astronauta.get('nome', 'Astronauta')} "
            f"e seu familiar na Terra ({familiar.get('nome', 'Família')}). "
            f"Juntos no desafio Corrida Terra-Órbita eles alcançaram {km_total} de {km_meta_conjunta} km ({progresso_pct}% da meta). "
            f"Gere uma mensagem curta em português (2 frases) de conexão afetiva e incentivo mútuo para aparecer no relógio e no app da Terra."
        )
        mensagem_incentivo = _ollama_generate(prompt, max_tokens=100)

    return {
        "desafio": "Corrida Terra–Órbita",
        "consentimento_ativo": pode_compartilhar_atividades,
        "km_meta": km_meta_conjunta,
        "km_astronauta": km_astro if pode_compartilhar_atividades else "privado_pelo_astronauta",
        "km_familiar": km_fam,
        "km_total_conjunto": km_total if pode_compartilhar_atividades else km_fam,
        "progresso_pct": progresso_pct if pode_compartilhar_atividades else round((km_fam / km_meta_conjunta) * 100, 1),
        "privacidade_adr007": "Respeitada: dados de saúde mental e sinais biométricos brutos são restritos ao relógio.",
        "mensagem_incentivo_cosmo": mensagem_incentivo,
    }

