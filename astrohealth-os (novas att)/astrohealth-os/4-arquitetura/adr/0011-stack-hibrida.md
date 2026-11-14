# ADR-011: Stack híbrida: padrão NASA nos diagramas, stack do time no protótipo

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-005

## Contexto

O hackathon dura 48 h. Implementar ION, firmware de relógio e modelos certificados não cabe nesse prazo, mas a banca espera uma arquitetura plausível.

## Decisão

Os diagramas descrevem a referência para produção (DTN/ION, modelos embarcados, LLM local). O protótipo implementa as mesmas fronteiras com Python, FastAPI, LangChain ou CrewAI, ChromaDB, Ollama, SQLite e um simulador de atraso.

## Alternativas consideradas

- **Implementar o ION real no hackathon:** Mais fiel, mas consome o evento inteiro.
- **Só a stack do time, sem referência NASA:** Rápido, mas menos convincente para a banca.

## Consequências

**Positivas**

- Entrega em 48 h sem mudar as fronteiras do sistema.

**Negativas**

- Parte do valor depende de explicar bem a diferença entre referência e protótipo.
