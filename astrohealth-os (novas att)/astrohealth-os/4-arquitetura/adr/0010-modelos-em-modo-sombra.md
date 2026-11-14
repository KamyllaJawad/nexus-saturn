# ADR-010: Modelos novos entram em modo sombra e exigem aprovação médica

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-001, ADR-008

## Contexto

A Terra pode treinar modelos melhores durante a missão, mas um modelo novo pode piorar justamente em casos raros.

## Decisão

Um modelo novo roda em paralelo, sem agir, comparando suas previsões com as do modelo atual. Só entra em uso depois que o oficial médico aprova, e a versão fica registrada em cada sugestão.

## Alternativas consideradas

- **Atualização automática vinda da Terra:** Rápida, mas arrisca trocar um modelo bom por um pior no meio da missão.

## Consequências

**Positivas**

- Atualizações seguras e rastreáveis.

**Negativas**

- Atualizações demoram mais para valer.
