# ADR-007: Consentimento granular para saúde mental; exceção só em risco de vida

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-002

## Contexto

Se o astronauta achar que tudo o que sente vai para o médico e para a Terra, ele esconde sintomas, e o sistema perde valor justamente no isolamento.

## Decisão

Alertas de bem-estar ficam só com o astronauta até ele autorizar. O consentimento é por tipo de dado e por destinatário, e pode ser revogado. Sem consentimento, nada sai do relógio. A única exceção é risco de vida, que vai ao médico e fica registrado na auditoria.

## Alternativas consideradas

- **O médico vê tudo:** Mais informação clínica, menos confiança da tripulação.
- **Nada é monitorado:** Privacidade total, mas o risco de isolamento fica sem resposta.

## Consequências

**Positivas**

- Confiança da tripulação no sistema.
- Alinhado à LGPD (dado sensível).

**Negativas**

- O médico pode não saber de algo que ele gostaria de saber.
