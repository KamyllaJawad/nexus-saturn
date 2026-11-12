# ADR-004: Um humano responsável por tipo de decisão; sem resposta, escala para outro humano

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-003, ADR-008

## Contexto

Sob pressão de tempo, é tentador deixar a IA decidir quando ninguém responde. Isso tiraria a responsabilidade humana justo nos momentos mais críticos.

## Decisão

Cada tipo de decisão tem um papel responsável (astronauta, oficial médico, comandante) e um prazo. Prazo vencido escala para o próximo humano da cadeia, nunca para a IA. Exceção: ações de nível 4, que já são reversíveis.

## Alternativas consideradas

- **A IA assume depois do prazo:** Rápido, mas transfere decisões clínicas para a máquina.
- **Esperar indefinidamente pelo responsável:** Mantém a responsabilidade, mas pode custar vidas.

## Consequências

**Positivas**

- Responsabilidade humana preservada e registrada.
- Tempo de resposta limitado pela cadeia de escalonamento.

**Negativas**

- Exige definir a cadeia de substitutos de cada papel.
