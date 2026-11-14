# AstroHealth OS · Arquitetura

Monitoramento da saúde da tripulação com IA local (Cosmo) e humano no controle, mesmo sem contato com a Terra.
Projeto para o desafio **Create Health Monitoring Software for Astronauts…** da NASA Space Apps Challenge 2026 (14 e 15 de novembro de 2026).

## Como navegar

| Pasta / arquivo | Conteúdo |
| --- | --- |
| [docs/01-visao-geral.md](docs/01-visao-geral.md) | Problema, escopo, princípios, perigos RIDGE |
| [docs/02-requisitos.md](docs/02-requisitos.md) | 28 requisitos funcionais e 11 atributos de qualidade |
| [docs/03-c4.md](docs/03-c4.md) | Contexto, containers e componentes (C4) |
| [docs/04-implantacao-comunicacao.md](docs/04-implantacao-comunicacao.md) | Nós, DTN, fila por prioridade, perfis de missão |
| [docs/05-motor-de-decisoes.md](docs/05-motor-de-decisoes.md) | Níveis de autonomia, responsáveis, máquina de estados |
| [docs/06-fluxos.md](docs/06-fluxos.md) | Cinco diagramas de sequência |
| [docs/07-modelo-de-dados.md](docs/07-modelo-de-dados.md) | Entidades, relações e interfaces do protótipo |
| [docs/08-stack.md](docs/08-stack.md) | Stack híbrida: referência NASA × protótipo |
| [docs/09-seguranca-privacidade.md](docs/09-seguranca-privacidade.md) | Ameaças (STRIDE + IA) e regras de privacidade |
| [docs/10-roadmap-riscos.md](docs/10-roadmap-riscos.md) | Roadmap, riscos e próximos passos |
| [adr/](adr/) | 12 decisões de arquitetura no formato MADR |
| [contratos/](contratos/) | JSON Schema da mensagem `evento.atualizado` e exemplo |
| [diagramas/](diagramas/) | Fonte `.mmd` e SVG de cada diagrama |
| [ferramentas/](ferramentas/) | Gerador da página interativa a partir destes arquivos |
| [pagina/](pagina/) | Página interativa gerada (HTML único) |

Os diagramas estão em Mermaid dentro dos próprios arquivos `.md`; o GitHub os renderiza sozinho.

## Regra de ouro

O LLM conversa, explica e resume. Só o **motor de decisões determinístico** muda o estado de um evento, e toda decisão clínica tem um humano responsável ([ADR-002](adr/0002-motor-de-decisoes-deterministico.md)).

## Artefatos relacionados

- Demo navegável, base do MVP (relógio com tela do ciclo, painel de bordo, celular da família, Houston e visão Dados e IA): <https://claude.ai/artifact/CE5bxpHxaLhi8Af9SY7NmU>
- Documento de arquitetura (editável): <https://claude.ai/artifact/VAc7XDqgnsWmbqsZRo5kvB>
- Página interativa de arquitetura: <https://claude.ai/artifact/Lego72b78ToDUQFZ46EGYe> (gerada por `python3 ferramentas/gerar_pagina.py`; saída em `pagina/arquitetura.html`)

## Pendência

O enunciado oficial do desafio bloqueia leitura automática. Cole o texto e os critérios de avaliação em `docs/01-visao-geral.md` e cruze com os requisitos.
