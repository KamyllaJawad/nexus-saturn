"""Back-end mínimo só para testar o módulo de IA. O back-end real é da Pessoa 3 (FastAPI + SQLite).

    uvicorn app_demo:app --port 8000      (rode dentro de 8-ia/)
    http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI

from api_ia import router as ia_router

app = FastAPI(title="AstroHealth OS · IA (demo)")
app.include_router(ia_router)

