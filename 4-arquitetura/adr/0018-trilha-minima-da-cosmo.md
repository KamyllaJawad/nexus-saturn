# ADR-018: Trilha mínima da Cosmo no painel de bordo e em Houston

- **Status:** aceita
- **Data:** 2026-11-15
- **Relacionadas:** ADR-002, ADR-006, ADR-007, ADR-008

## Contexto

A auditoria encadeada (ADR-008) registra o que muda estado: eventos, decisões humanas e modelos. A Cosmo não muda estado, mas fala o tempo todo, nas sugestões dos eventos e nos chats. Sem registro, não dá para responder quanto ela custa, quanto demora, o que decidiu responder e por qual caminho.

## Decisão

Cada fala da Cosmo gera um registro com cinco campos:

| Campo | O que guarda |
| --- | --- |
| Tokens | Entrada e saída. Com Ollama, a contagem dele; sem LLM, estimativa de 4 caracteres por token, marcada como estimada |
| Latência | Tempo total em ms e de cada passo |
| Custo | US$ pelo preço por milhão de tokens (padrão 0, porque tudo roda local) e energia estimada a bordo (latência × 15 W) |
| Decisão da Cosmo | `respondeu`, `recusou agir`, `sugeriu` ou `sem resposta`, com um resumo. `pode_agir` é sempre falso |
| Passos | No chat: visão, intenção, busca, resposta, redação e guarda. Na sugestão: entrada, protocolo e entrega |

O registro vai para a tabela `cosmo_trilha`, só de inclusão. Também entra na auditoria encadeada, só com as métricas: o texto da pergunta não vai para lá.

Cada superfície vê só a sua parte:

- **Painel de bordo:** o chat do painel e as sugestões dos eventos que o painel pode ver. A sugestão de um dado privado sem consentimento não aparece. O chat do relógio é da pessoa e também não aparece.
- **Houston:** a Cosmo Terra e a trilha das sugestões de bordo que já chegaram. Essa trilha viaja no pacote do evento e não leva pergunta nenhuma.

## Alternativas consideradas

- **Só registrar na auditoria encadeada:** Simples, mas mistura métricas de uso com mudanças de estado e não mostra os passos.
- **Telemetria externa (OpenTelemetry, LangSmith):** Padrão de mercado, mas exige serviço fora da nave e manda texto para fora. Pode substituir esta tabela depois.

## Consequências

**Positivas**

- A banca e a médica de voo veem quanto a Cosmo custa e demora, e que ela nunca agiu.
- Houston audita as sugestões de bordo com o mesmo atraso dos eventos (ADR-006).

**Negativas**

- Sem LLM, os tokens são estimados. O custo em US$ é zero enquanto tudo rodar local.
- A trilha cresce com cada pergunta. A tela mostra a sessão atual e o SQLite guarda o resto.
