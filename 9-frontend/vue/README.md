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

As rotas usam `#`: `/v2/#/bordo` e `/v2/#/relogio`.

## De onde vêm os dados

| Peça | Situação |
| --- | --- |
| Painel de bordo | Lê `GET /api/bordo` a cada 1 s. `src/servicos/api.ts` traduz a resposta para os tipos de `src/mocks/` e os componentes não mudam. |
| Decisões | Os eventos abertos viram o card de decisão; o botão chama `POST /api/decisoes`. Medicação com PIN, médico na Terra e ordem permanente ainda mandam para o painel completo em `bordo/`. |
| Chat da Cosmo | `POST /api/cosmo/chat` com `superficie: "bordo"`. |
| ECG | Desenho sintético a partir da FC e do ritmo do M1. O trecho real do CinC (`/api/tripulantes/{id}/ecg`) é o próximo passo. |
| Silhueta (`corpo`) e `sexo` | Calculados no adaptador por enquanto; vão para o back (`s.clinico()`). |
| Ciclo | Só aparece o que a pessoa compartilhou pelo relógio, sem método nem fase (ADR-013 e ADR-014). |
| Relógio | Ainda nos mocks. |

Sem a API no ar, o painel mostra os mocks com o aviso "Modo offline" e volta sozinho quando ela responde.

`VITE_API_URL` aponta para outra API (ex.: `http://127.0.0.1:8000`); sem ele, o caminho é relativo.
