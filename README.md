# AstroHealth OS · NASA Space Apps Challenge 2026

Monitoramento da saúde da tripulação com IA local (Cosmo) e um humano sempre no controle.
O MVP é a demo original: relógio, painel de bordo, celular da família e console de Houston.
O hackathon é no sábado 14/11 e no domingo 15/11, com entrega às 15h de domingo.

## O que tem em cada pasta

| Pasta | Conteúdo |
| --- | --- |
| `1-demo-mvp/` | `astrohealth-demo.html`, a demo navegável e base do MVP. Abra no navegador, sem instalar nada. |
| `2-mockups/` | Fonte das 14 telas do canvas de mockups, tiradas da demo. Só abrem dentro do canvas (link abaixo). |
| `3-documentos/` | PDFs do plano do time, do MVP (dados, modelos e telas) e da arquitetura de software, exportados em 11/11. O Isolation Forest entrou no M3 depois disso: vale a ADR-012. |
| `4-arquitetura/` | Arquitetura em formato de repositório: docs, 12 ADRs, contratos JSON, diagramas Mermaid e SVG, e a página interativa. |
| `5-plano-do-time/` | CSV com as 25 tarefas para 3 pessoas, as partes só simuladas e o script que cria as issues no GitHub. |
| `6-origem/` | As telas do Stitch que deram origem ao projeto. |
| `7-pitch/` | Guia, mapa de uso e parcerias em potencial para quem monta o pitch. |
| `8-pesquisa/` | Pesquisa sobre saúde da mulher astronauta: lacunas, artigos, dados, parceiros, onde a proposta entra no projeto e respostas para a banca. |

## Versões online (editáveis)

- Demo (MVP): https://claude.ai/artifact/CE5bxpHxaLhi8Af9SY7NmU
- Mockups: https://claude.ai/artifact/3ekC2gNufdfniHNwZY374Q
- Plano do time: https://claude.ai/artifact/DPQG3jxXj2h9eFcsJpsmAN
- MVP · dados, modelos e telas: https://claude.ai/artifact/7cs25yVBYhkGgKk1ywLaRT
- Arquitetura (doc): https://claude.ai/artifact/VAc7XDqgnsWmbqsZRo5kvB
- Arquitetura (página interativa): https://claude.ai/artifact/Lego72b78ToDUQFZ46EGYe

Os links são privados até serem compartilhados pelo menu Share de cada um.

## Divisão do time

| Quem | Frente | Carga |
| --- | --- | --- |
| Pessoa 1 | Dados e IA: contratos JSON, sintéticos, CinC 2017, M1, M2 e M3 (z robusto e Isolation Forest) em `ia.py`, protocolos e Cosmo | 19 h |
| Pessoa 2 | Telas, copiadas da demo: relógio, painel de bordo, celular da família e Houston | 19 h |
| Pessoa 3 | Back-end: FastAPI + SQLite, simulador, regras de decisão, atraso nave ↔ Terra, feed da família e testes | 17 h |

Todos os dados das telas são simulados. Não é dispositivo médico.
