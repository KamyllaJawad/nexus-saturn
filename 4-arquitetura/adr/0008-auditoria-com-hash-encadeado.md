# ADR-008: Trilha de auditoria só de inclusão, com hash encadeado

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-004

## Contexto

Depois de um evento, é preciso saber o que a IA sugeriu, quem decidiu e quando, e provar que nada foi alterado.

## Decisão

Cada transição de estado, sugestão, decisão e escalonamento gera um registro só de inclusão, com o hash do registro anterior. A trilha é copiada para a Terra em P2.

## Alternativas consideradas

- **Logs comuns da aplicação:** Fáceis, mas editáveis e incompletos.

## Consequências

**Positivas**

- Revisão confiável de decisões; base para pareceres e para a pesquisa.

**Negativas**

- Mais armazenamento e mais tráfego de baixa prioridade.
