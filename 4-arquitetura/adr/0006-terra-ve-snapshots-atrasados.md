# ADR-006: A Terra vê snapshots atrasados, com a hora de origem

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-005

## Contexto

Mostrar dados de 12 minutos atrás como se fossem ao vivo leva Houston a decidir sobre uma situação que já mudou.

## Decisão

Toda informação carrega a hora em que foi gerada e a hora em que chegou. O console mostra "você está vendo o passado" e o atraso do perfil de missão. Pareceres de Houston são revisões, não comandos.

## Alternativas consideradas

- **Esconder o atraso:** Interface mais limpa, mas engana quem decide.

## Consequências

**Positivas**

- Houston decide sabendo de quando é o dado.

**Negativas**

- Interfaces mostram dois relógios, o de geração e o de recebimento.
