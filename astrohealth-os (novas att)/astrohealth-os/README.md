# AstroHealth OS · NASA Space Apps Challenge 2026

Monitoramento da saúde da tripulação com IA local (Cosmo) e um humano sempre no controle.
O MVP é a demo original: relógio, painel de bordo, celular da família, console de Houston e a visão Dados e IA.
Diferenciais: saúde da mulher, com as 4 fases do ciclo hormonal acompanhadas com ou sem método de supressão (M4); cenários para homens (visão e pressão intracraniana, SANS); a hipótese de não haver médico a bordo, quando a médica de voo em Houston toma as decisões no console; a engenharia e ciência de dados visíveis do sensor ao modelo; e uma gamificação cooperativa, sem ranking nem punição, que envolve a família (ver `3-documentos/4-Gamificação.pdf`).

A demo cobre 13 dos 17 riscos de saúde do NASA Human Research Program (2 em parte e 2 como próximos passos), com o mapa completo na visão "Dados e IA". Os próximos passos estão em `4-arquitetura/proximos-passos.md`.

Na demo, a faixa "Hipóteses" abaixo da barra troca quem usa o relógio (Sarah ou Kenji), onde está o médico (a bordo ou só na Terra) e a fase do ciclo da Sarah.
O hackathon é no sábado 14/11 e no domingo 15/11, com entrega às 15h de domingo.

## O que tem em cada pasta

| Pasta | Conteúdo |
| --- | --- |
| `1-demo-mvp/` | `astrohealth-demo.html`, a demo navegável e base do MVP. Abra no navegador, sem instalar nada. |
| `2-mockups/` | Fonte das 16 telas do canvas de mockups, tiradas da demo, e em `telas-novas/` 3 pranchas em PNG com as telas de 14/11 (relógio, painel de bordo e Houston, mapa de riscos). |
| `3-documentos/` | PDFs exportados em 14/11 dos 4 documentos: plano do time, MVP (dados, modelos e telas), arquitetura de software e gamificação. As versões editáveis estão nos links abaixo. |
| `4-arquitetura/` | Arquitetura em formato de repositório: docs, 14 ADRs (ADR-012: ciclo hormonal; ADR-013: médico a bordo ou na Terra, cenários por sexo e 4 fases; ADR-014: cobertura dos 17 riscos da NASA), contratos JSON, diagramas Mermaid e SVG, e a página interativa. |
| `5-plano-do-time/` | CSV com as 28 tarefas para 3 pessoas, as partes só simuladas e o script que cria as issues no GitHub. |
| `6-origem/` | As telas do Stitch que deram origem ao projeto. |

## Versões online (editáveis)

- Demo (MVP): https://claude.ai/artifact/CE5bxpHxaLhi8Af9SY7NmU
- Mockups: https://claude.ai/artifact/3ekC2gNufdfniHNwZY374Q
- Plano do time: https://claude.ai/artifact/DPQG3jxXj2h9eFcsJpsmAN
- MVP · dados, modelos e telas: https://claude.ai/artifact/7cs25yVBYhkGgKk1ywLaRT
- Arquitetura (doc): https://claude.ai/artifact/VAc7XDqgnsWmbqsZRo5kvB
- Arquitetura (página interativa): https://claude.ai/artifact/Lego72b78ToDUQFZ46EGYe
- Gamificação: https://claude.ai/artifact/F8cWbKnNstNTQRTeEUW6qM

Os links são privados até serem compartilhados pelo menu Share de cada um.

## Divisão do time

| Quem | Frente | Carga |
| --- | --- | --- |
| Kamylla | Dados e IA: contratos JSON, sintéticos, CinC 2017, M1, M2, M3 e M4 em `ia.py`, protocolos e Cosmo | 19 h |
| Pessoa 2 | Telas, copiadas da demo: relógio (com ciclo), painel de bordo, celular da família, Houston e Dados e IA | 20 h |
| Pessoa 3 | Back-end: FastAPI + SQLite, simulador, ciclos sintéticos, regras de decisão, atraso nave ↔ Terra, feed da família e testes | 18 h |

Todos os dados das telas são simulados. Não é dispositivo médico.
