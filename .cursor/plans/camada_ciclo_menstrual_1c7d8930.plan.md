---
name: Camada ciclo menstrual
overview: Registrar a camada do ciclo como ADR-013, ligá-la à privacidade, ao motor e ao pitch, e mostrá-la na demo e nos mockups como aviso privado no relógio da Sarah, sem a família ver.
todos:
  - id: adr-013
    content: Escrever a ADR-013 e atualizar os índices de 12 para 13 decisões
    status: completed
  - id: docs
    content: Ligar a decisão em requisitos, motor, fluxos, dados, stack, C4, privacidade e no exemplo JSON
    status: completed
  - id: pagina
    content: Regenerar a página de arquitetura
    status: completed
  - id: demo
    content: Trocar as frases de dia 14 e adicionar o evento Padrão hormonal na demo
    status: completed
  - id: mockups
    content: Acrescentar as pranchetas do ciclo no canvas e a linha permanente no relógio de início
    status: completed
  - id: pitch
    content: Acrescentar o parágrafo do M3 e a resposta de sabatina no guia do pitch
    status: completed
  - id: todo-1794534869334-30qp3zsxs
    content: orientar o usuario onde validar na demo visual em html
    status: completed
isProject: false
---

# Camada do ciclo na documentação e na demo

A ficha de solo prevê o trecho intenso, a Cosmo avisa só a astronauta e oferece cuidado leve. A família não recebe fase, calendário nem sintoma. As 25 tarefas de [5-plano-do-time/issues-astrohealth.csv](5-plano-do-time/issues-astrohealth.csv) e os PDFs de `3-documentos/` ficam como estão.

## Decisão

Criar [4-arquitetura/adr/0013-calendario-do-ciclo.md](4-arquitetura/adr/0013-calendario-do-ciclo.md) no formato da ADR-012 (aceita em 2026-11-12, relacionada à ADR-007 e à ADR-012):

- A ficha pré-voo traz método (nenhum, pílula combinada contínua, DIU de levonorgestrel, implante), última menstruação, duração típica e o trecho de sintomas intensos. A injeção trimestral de progestina fica de fora.
- O relógio mostra esse status só para ela. Na supressão, o texto fala do calendário de solo, não de ovulação nem de janela fértil.
- Cerca de dois dias antes do trecho, a Cosmo avisa no relógio. A pergunta de cólica, inchaço ou humor só aparece quando esse trecho coincide com sinais leves (FC e temperatura da pele um pouco acima da mediana dela, sono mais curto ou HRV mais baixo) e o M2 classifica o sinal como bom.
- O cuidado é nível 2: respirar, treino mais leve, modo noite, água só se a hidratação do dia estiver baixa. Analgésico do kit continua com o médico, em passo separado.
- Fora da janela, sinal crítico ou fibrilação atrial seguem o fluxo atual. Médico e Houston só veem com consentimento. Comandante (quando for outra pessoa) e família não veem.

Atualizar a contagem para 13 decisões em [4-arquitetura/adr/README.md](4-arquitetura/adr/README.md), [4-arquitetura/README.md](4-arquitetura/README.md) e a linha de `4-arquitetura/` no [README.md](README.md).

## Documentos que passam a citar a ADR-013

- [4-arquitetura/docs/02-requisitos.md](4-arquitetura/docs/02-requisitos.md): RF27, prioridade importante. O texto de “26 requisitos” passa a 27.
- [4-arquitetura/docs/05-motor-de-decisoes.md](4-arquitetura/docs/05-motor-de-decisoes.md): parágrafo ao lado da regra da linha de base.
- [4-arquitetura/docs/06-fluxos.md](4-arquitetura/docs/06-fluxos.md): fluxo curto no formato do de saúde mental.
- [4-arquitetura/docs/07-modelo-de-dados.md](4-arquitetura/docs/07-modelo-de-dados.md) e exemplo novo [4-arquitetura/contratos/exemplos/analise-ciclo.json](4-arquitetura/contratos/exemplos/analise-ciclo.json). O exemplo de fibrilação atrial não muda.
- [4-arquitetura/docs/08-stack.md](4-arquitetura/docs/08-stack.md) e a linha de detectores em [4-arquitetura/docs/03-c4.md](4-arquitetura/docs/03-c4.md).
- [4-arquitetura/docs/09-seguranca-privacidade.md](4-arquitetura/docs/09-seguranca-privacidade.md): linha na matriz de acesso.

Regenerar [4-arquitetura/pagina/arquitetura.html](4-arquitetura/pagina/arquitetura.html) com `4-arquitetura/ferramentas/gerar_pagina.py`. O número 11 dessa página é a seção de ADRs, não a quantidade de decisões.

## Demo

Em [1-demo-mvp/astrohealth-demo.html](1-demo-mvp/astrohealth-demo.html):

- Remover “ciclo no dia 14 (janela fértil)” do chat da Cosmo (por volta da linha 820) e do resumo do Dr. Marcus (por volta da linha 1361).
- Na tela inicial do relógio, uma linha permanente só dela: “Pílula contínua · calendário de solo: trecho de cólica”.
- Novo evento injetável **Padrão hormonal**, no mesmo molde de sensor solto e queda de humor: anel em Ótimo, aviso de que o trecho começa em dois dias, botões **Estou** e **Estou bem**. Em **Estou**, **Respirar 1 min** e **Contar ao Dr. Marcus**. O painel só ganha um cartão calmo se ela contar. Houston e o celular da família não recebem esse dado.

## Mockups

As pranchetas de [2-mockups/](2-mockups/) são fotos estáticas da demo. Entram três telas novas, no mesmo formato `.dc.html` de [2-mockups/Relogio-Folgado.dc.html](2-mockups/Relogio-Folgado.dc.html), e uma alteração na tela que já existe:

- [2-mockups/Main.dc.html](2-mockups/Main.dc.html): na tela inicial, debaixo do anel verde, a linha permanente “Pílula contínua · calendário de solo: trecho de cólica”.
- `2-mockups/Relogio-Ciclo.dc.html`: cartão privado “Só você vê isto”, trecho de cólica em dois dias, botões **Estou** e **Estou bem**. O estado não vai para crítico.
- `2-mockups/Relogio-Ciclo-Cuidado.dc.html`: o toque seguinte, com **Respirar 1 min** e **Contar ao Dr. Marcus**.
- `2-mockups/Bordo-Ciclo.dc.html`: painel do Dr. Marcus em Ótimo, cartão calmo só porque a Sarah compartilhou. Sem faixa vermelha e sem protocolo.

[2-mockups/Familia.dc.html](2-mockups/Familia.dc.html), [2-mockups/Familia-Emergencia.dc.html](2-mockups/Familia-Emergencia.dc.html), [2-mockups/Houston.dc.html](2-mockups/Houston.dc.html) e [2-mockups/Houston-Emergencia.dc.html](2-mockups/Houston-Emergencia.dc.html) ficam sem menção ao ciclo.

Registrar as três pranchetas em [2-mockups/canvas.json](2-mockups/canvas.json) (`boards` e `order`), na fileira do relógio e ao lado do painel de rotina. Atualizar a contagem de 14 para 17 em [2-mockups/README.md](2-mockups/README.md) e na linha de `2-mockups/` do [README.md](README.md).

## Pitch

- [7-pitch/guia-pitch.md](7-pitch/guia-pitch.md): parágrafo na seção 4.3 e uma sétima resposta de sabatina. O roteiro de 90 segundos não ganha cena; o evento fica de reserva.
- [7-pitch/README.md](7-pitch/README.md): uma linha apontando essa resposta.
