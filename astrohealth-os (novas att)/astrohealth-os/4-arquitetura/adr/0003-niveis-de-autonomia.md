# ADR-003: Níveis de autonomia de 0 a 4 e a lista do que a IA nunca faz sozinha

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-002, ADR-004

## Contexto

Ações diferentes têm risco e reversibilidade diferentes: acender a rota até o abrigo não se compara a liberar um medicamento.

## Decisão

Cada tipo de evento tem um nível: 0 observar, 1 informar, 2 sugerir, 3 preparar e pedir confirmação, 4 agir e avisar com desfazer (só ações urgentes e reversíveis). Medicação, procedimentos invasivos, compartilhar saúde mental e tirar alguém de tarefa crítica nunca acontecem sem um humano.

## Alternativas consideradas

- **Autonomia ligada ou desligada:** Simples de explicar, mas força o mesmo tratamento para riscos muito diferentes.
- **Autonomia decidida caso a caso pelo LLM:** Imprevisível e impossível de auditar.

## Consequências

**Positivas**

- Política de autonomia explícita e revisável pelo time médico.
- A banca vê com clareza onde a IA para.

**Negativas**

- Cada novo evento precisa ser classificado antes de entrar em produção.
