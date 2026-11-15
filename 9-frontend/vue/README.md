# 9-frontend/vue · site do AstroHealth OS

Todas as telas em Vue 3 + TypeScript (Vite, Vitest), no visual do painel de bordo da isacdcunha. Elas leem a API do `8-backend`; quem detecta são os modelos treinados e quem decide é um humano.

Protótipo experimental com dados simulados. Não é dispositivo médico.

| Rota | Quem usa | O que vê |
| --- | --- | --- |
| `#/` | Quem apresenta | Sala de simulação: injeta cenários e mostra relógio, painel de bordo, família e Houston lado a lado. |
| `#/relogio?quem=sarah` | Quem está com o pulso | Mostrador com avatar, notificações que pedem resposta, sinais, Cosmo, estufa, Elo e sincronia. |
| `#/bordo?quem=sarah` | Dr. Marcus, ou o Marcus como CMO sem médico a bordo | Tripulação, ECG real do CinC, silhueta, saída dos modelos, decisões (protocolo de FA, medicação com PIN, ações seguras, ordem permanente), avisos compartilhados, chat e trilha da Cosmo. |
| `#/houston` | Flight surgeon, ou a Dra. Rivera sem médico a bordo | O retrato atrasado, eventos que chegaram, parecer, decisão da Terra sem médico a bordo, compartilhado só com ela, pacotes do link, Cosmo Terra e trilha. |
| `#/familia` | Família | Frases com o atraso da missão. Nunca número, diagnóstico, humor ou ciclo. |
| `#/dados-ia` | Banca e time | Lakehouse, métricas medidas, human-in-the-loop dos modelos e auditoria encadeada. |

## Rodar no computador

Requer Node `^22.18` ou `>=24.12` e a API no ar (veja `8-backend/README.md`).

```sh
npm ci
npm run dev          # http://localhost:5173/  (/api vai para a API em 127.0.0.1:8000)
npm run test:unit    # Vitest
npm run build:api    # gera ../v2, que a API serve em http://127.0.0.1:8000/v2/
```

Sem a API no ar, o painel e o relógio mostram dados de exemplo com o aviso "Modo offline"; as outras telas esperam a API.

## Publicar (Vercel + Render)

O site é estático e vai para a Vercel. A API precisa de um processo contínuo (o simulador dá um passo por segundo e guarda o estado em memória), então vai para o Render, com o `Dockerfile` do `8-backend`.

1. **API no Render.** Em <https://render.com>: New > Blueprint, escolha este repositório. O `render.yaml` da raiz cria o serviço `astrohealth-api` (Docker, plano gratuito, checagem de saúde em `/api/missao`). Anote a URL, por exemplo `https://astrohealth-api.onrender.com`.
2. **Site na Vercel.** Em <https://vercel.com>: Add New > Project, este repositório, **Root Directory `9-frontend/vue`**. O `vercel.json` já define o build (`npm run build`, saída `dist`). Em Environment Variables, cadastre `VITE_API_URL` com a URL do passo 1 e faça o deploy.
3. Abra o site da Vercel: a sala de simulação é a página inicial.

Pontos de atenção:

- No plano gratuito, o Render desliga a API depois de 15 min sem uso; a primeira visita depois disso leva cerca de 1 min. Antes de apresentar, abra o site uma vez para acordá-la.
- Há um simulador só, compartilhado por todos os visitantes: um cenário injetado por alguém aparece para todos. "Reiniciar a simulação" volta tudo ao começo.
- Sem Ollama no servidor, a Cosmo responde com as regras locais e a busca nos protocolos (`COSMO_OLLAMA=0`).
- A cada deploy do Render, o banco da sessão e os candidatos retreinados recomeçam; os modelos em serviço são os do git.
- As rotas usam `#`, então a Vercel não precisa de regra de reescrita.
