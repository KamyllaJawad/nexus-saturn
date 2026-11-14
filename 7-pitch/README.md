# Pitch

Para quem vai montar slides, fala e vídeo. O texto longo está em [guia-pitch.md](guia-pitch.md). As parcerias em potencial estão em [parcerias.md](parcerias.md).

A arquitetura continua em `4-arquitetura/`. As 25 tarefas do hackathon continuam em `5-plano-do-time/`.

## Por onde começar

1. Tire a frase de abertura da tese, seção 1.2 do guia, e coloque no primeiro slide.
2. Ensaie o roteiro dos segundos 0 a 90, seção 6, com as quatro telas da demo abertas.
3. Decore as sete respostas da sabatina, seção 7.
4. Passe o checklist, seção 8, na hora da gravação.
5. Se a conversa for para hardware brasileiro, sono ou ritmo circadiano, use a ficha da Condor em [parcerias.md](parcerias.md).

## O que usar de cada seção do guia

| Seção | Uso |
| --- | --- |
| 1.2 Tese | Slide de abertura e a última frase do vídeo. |
| 1.1 RIDGE | Um slide, se a banca pedir o problema. Isolamento (I) é o gancho da actigrafia e da Condor. |
| 2 Princípios e níveis 0 a 4 | Resposta quando perguntarem quem decide. Medicamento, procedimento invasivo e saúde mental ficam com um humano. |
| 3 Sensores | Slide de hardware. A linha de actigrafia aponta para a Condor. |
| 4.1 a 4.3 M1, M2 e M3 | Slide de modelos. O M3 é z robusto por sinal e um Isolation Forest por tripulante ([ADR-012](../4-arquitetura/adr/0012-linha-de-base-com-isolation-forest.md)). A ficha escolhe a direção: calendário do ciclo ou linha de base pessoal ([ADR-013](../4-arquitetura/adr/0013-calendario-do-ciclo.md)). |
| 4.4 Cosmo | O card "Por que a Cosmo sugeriu isso?". A Cosmo explica. O motor decide. |
| 5 Custos | O hackathon é o cenário A, R$ 0. Os cenários B, C e D ficam de reserva se perguntarem de bancada ou de voo. |
| 6 Roteiro de 90 s | O que se fala, na ordem das quatro telas. |
| 7 Sabatina | As sete respostas prontas. A sétima cobre os dois gêneros: calendário só quando a ficha tem, e a família não fica sabendo. |
| 8 Checklist | Conferência antes de gravar. |
| 9 Referências | Créditos dos slides. A matéria da Condor é o item 19. |

## O que abrir junto

- Demo: [../1-demo-mvp/astrohealth-demo.html](../1-demo-mvp/astrohealth-demo.html). Relógio, painel de bordo, celular da família e Houston.
- Linha de base: [ADR-012](../4-arquitetura/adr/0012-linha-de-base-com-isolation-forest.md).
- Calendário do ciclo: [ADR-013](../4-arquitetura/adr/0013-calendario-do-ciclo.md). Na demo, os botões **Padrão hormonal · supressão** e **Padrão hormonal · sem método** em Injetar evento.
- Gamificação: [../3-documentos/4-Gamificação.pdf](../3-documentos/4-Gamificação.pdf). Cooperativa, sem ranking e sem punição, com a família no Elo.
- Aviso que entra no rodapé: protótipo experimental, não é dispositivo médico.
