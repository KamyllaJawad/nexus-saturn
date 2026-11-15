"""Rotas FastAPI do módulo de IA. A Pessoa 3 só precisa de duas linhas no back-end:

    from api_ia import router as ia_router
    app.include_router(ia_router)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import ia

router = APIRouter(prefix="/ia", tags=["ia"])


class Dia(BaseModel):
    data: Optional[str] = Field(None, description="AAAA-MM-DD")
    sono_h: Optional[float] = Field(None, ge=0, le=24)
    agua_ml: Optional[float] = Field(None, ge=0)
    exercicio_min: Optional[float] = Field(None, ge=0)
    humor: Optional[int] = Field(None, ge=1, le=5)
    fc_repouso: Optional[float] = Field(None, ge=20, le=250)
    tarefas_planejadas: Optional[int] = Field(None, ge=0)
    tarefas_feitas: Optional[int] = Field(None, ge=0)
    pendentes: Optional[list[str]] = None


class PedidoPrevencao(BaseModel):
    dias: list[Dia] = Field(..., min_length=1, description="Do mais antigo ao mais recente")
    consentimento_saude_mental: bool = False
    usar_rag: bool = True
    explicar: bool = True


class PedidoBusca(BaseModel):
    consulta: str
    k: int = Field(3, ge=1, le=10)


@router.get("/status")
def status():
    return ia.status()


@router.post("/indice")
def reconstruir_indice():
    """Lê 8-ia-base-conhecimento e recria o índice do RAG (demora alguns minutos)."""
    try:
        r = ia.construir_indice()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"Ollama indisponível: {e}")
    ia._cache.clear()
    return r


@router.post("/prevencao")
def prevencao(p: PedidoPrevencao):
    return ia.avaliar_prevencao(
        [d.model_dump() for d in p.dias],
        consentimento_saude_mental=p.consentimento_saude_mental,
        usar_rag=p.usar_rag,
        explicar=p.explicar,
    )


class PedidoTela(BaseModel):
    pergunta: str
    consentimento_saude_mental: bool = False
    k: int = Field(4, ge=1, le=10)


@router.post("/tela/{tela}")
def tela(tela: str, p: PedidoTela):
    """tela = hidratacao | saude_mental | exercicios. Cada tela consulta só o seu tema."""
    try:
        return ia.responder_tela(tela, p.pergunta, p.consentimento_saude_mental, p.k)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except FileNotFoundError as e:
        raise HTTPException(409, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"Ollama indisponível: {e}")


class PedidoChat(BaseModel):
    mensagem: str
    tema: Optional[str] = None
    consentimento_saude_mental: bool = False
    k: int = Field(4, ge=1, le=10)


@router.post("/chat")
def chat(p: PedidoChat):
    """Chatbot geral da Cosmo. Usado no relógio, tablet de bordo e consoles."""
    try:
        return ia.chat_cosmo(p.mensagem, p.tema, p.consentimento_saude_mental, p.k)
    except FileNotFoundError as e:
        raise HTTPException(409, str(e))
    except Exception as e:
        raise HTTPException(503, f"Ollama indisponível: {e}")


@router.post("/buscar")
def buscar(p: PedidoBusca):
    try:
        return ia.buscar(p.consulta, p.k)
    except FileNotFoundError as e:
        raise HTTPException(409, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"Ollama indisponível: {e}")

