# 9-frontend/vue · telas novas em Vue

Painel de bordo e relógio em Vue 3 + TypeScript (Vite, Vitest). Convivem com as telas em JS puro de `9-frontend/` até a migração terminar.

Protótipo experimental com dados simulados. Não é dispositivo médico.

## Rodar

Requer Node `^22.18` ou `>=24.12`.

```sh
npm ci
npm run dev          # http://localhost:5173/v2/  (/api vai para a API em 127.0.0.1:8000)
npm run build        # gera ../v2, que a API serve em http://127.0.0.1:8000/v2/
npm run test:unit    # Vitest
```

As rotas usam `#`: `/v2/#/bordo` e `/v2/#/relogio?quem=sarah`. Na sala de simulação, "Visual: Novo (Vue)" troca o relógio e o painel por estas telas.

## De onde vêm os dados

| Peça | Situação |
| --- | --- |
| Painel de bordo | Lê `GET /api/bordo` a cada 1 s. `src/servicos/api.ts` traduz a resposta para os tipos de `src/mocks/` e os componentes não mudam. |
| Decisões | Os eventos abertos viram o card de decisão; o botão chama `POST /api/decisoes`. Medicação com PIN, médico na Terra e ordem permanente ainda mandam para o painel completo em `bordo/`. |
| Chat da Cosmo | `POST /api/cosmo/chat` com `superficie: "bordo"`. |
| ECG | Trecho real do relógio (`/api/tripulantes/{id}/ecg`, conjunto de teste do CinC 2017), a cada 5 s. Sem a API, desenho sintético. |
| Silhueta, sexo e ciclo | Vêm prontos do back: `corpo` e `sexo` em `s.clinico()`, `saude_hormonal` em `/api/bordo`. Com uma API mais antiga, o adaptador calcula com as mesmas regras. |
| Ciclo | O painel vê só o que a pessoa compartilhou pelo relógio, sem método nem fase, e nada sem médico a bordo (ADR-013 e ADR-014). |
| Relógio | `GET /api/tripulantes/{id}/relogio` a cada 1 s: mostrador com o estado real e as notificações que pedem resposta (mesmos botões do relógio atual). `?quem=elena` troca o pulso. Cosmo, estufa, Elo e sincronia seguem no relógio atual. |

Sem a API no ar, o painel mostra os mocks com o aviso "Modo offline" e volta sozinho quando ela responde.

`VITE_API_URL` aponta para outra API (ex.: `http://127.0.0.1:8000`); sem ele, o caminho é relativo.
