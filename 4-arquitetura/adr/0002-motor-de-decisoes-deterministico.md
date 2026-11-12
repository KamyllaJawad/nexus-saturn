# ADR-002: Motor de decisões determinístico separado do LLM

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-003, ADR-004, ADR-008

## Contexto

LLMs são ótimos para conversar, explicar e resumir, mas podem alucinar e são difíceis de certificar. Uma decisão clínica precisa ser previsível, testável e auditável.

## Decisão

Só o motor de decisões (regras + máquina de estados) muda o estado de um evento. A Cosmo (LLM + RAG) lê o estado, explica evidências e conversa, mas não tem permissão de ação. Toda saída do LLM que sugira ação vira uma Sugestão, nunca uma Decisão.

## Alternativas consideradas

- **Agente de LLM decidindo (CrewAI/LangChain com ferramentas de ação):** Flexível, mas imprevisível, difícil de testar e vulnerável a injeção de instruções.
- **Sem LLM:** Mais simples, mas perde a conversa, a explicabilidade e os resumos para Houston.

## Consequências

**Positivas**

- Comportamento previsível e testável com Robot Framework e pytest.
- Injeção de instruções no LLM não consegue aprovar nada.

**Negativas**

- Regras precisam ser escritas e mantidas à mão.
- Duas peças para integrar: motor e Cosmo.
