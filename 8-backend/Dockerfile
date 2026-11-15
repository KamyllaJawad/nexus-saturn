# API do AstroHealth OS para hospedagem com processo contínuo (Render, Railway, Fly.io).
# O simulador guarda o estado em memória e roda um passo por segundo: use UM processo
# (uvicorn sem --workers). Os modelos treinados e os dados ouro/prata vêm do git.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COSMO_OLLAMA=0

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# O Render informa a porta em $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
