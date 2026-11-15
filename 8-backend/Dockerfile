# API + telas num serviço só (Render). O contexto do build é a raiz do repositório:
#   docker build -f 8-backend/Dockerfile .
# O simulador guarda o estado em memória e roda um passo por segundo: use UM processo
# (uvicorn sem --workers). Os modelos treinados e os dados ouro/prata vêm do git.
# O v2 não está no git; o estágio Node gera 9-frontend/v2 (base /v2/).

FROM node:22-bookworm-slim AS frontend

WORKDIR /src/9-frontend/vue
COPY 9-frontend/vue/package.json 9-frontend/vue/package-lock.json ./
RUN npm ci
COPY 9-frontend/vue/ ./
RUN npm run build:api

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COSMO_OLLAMA=0

WORKDIR /srv/8-backend
COPY 8-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY 8-backend/ .
COPY 9-frontend /srv/9-frontend
COPY --from=frontend /src/9-frontend/v2 /srv/9-frontend/v2

EXPOSE 8000
# O Render informa a porta em $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
