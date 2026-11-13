# ADR-013: Linha de base por fase do ciclo e consentimento de saúde reprodutiva

- **Status:** proposta
- **Data:** 2026-11-12
- **Relacionadas:** ADR-007, ADR-010, ADR-012

## Contexto

O M3 compara cada tripulante com a própria mediana ([ADR-012](0012-linha-de-base-com-isolation-forest.md)). Metade da tripulação da demo é mulher, e o ciclo muda o que o relógio mede: depois da ovulação, a frequência cardíaca de repouso sobe cerca de 3 bpm e a temperatura da pele cerca de 0,3 °C. A pílula também muda o padrão. Uma mediana que ignora a fase dá alarme na fase lútea ou fica larga demais e esconde um problema real.

A própria NASA reconhece que quase todos os dados de risco do voo espacial vêm de homens e pede que as astronautas liderem a proteção dos dados de saúde reprodutiva. A pesquisa completa, com as fontes, está em [8-pesquisa](../../8-pesquisa/README.md).

## Decisão

- O perfil da tripulante guarda o contexto hormonal: ciclo natural, pílula, DIU ou implante, e a fase atual, por registro rápido ou contagem de dias.
- O M3 calcula a mediana e o MAD por fase do ciclo (`m3-fase-0.1`) para quem informar o contexto. Sem contexto, vale a linha de base única. A versão nova entra em modo sombra antes de valer ([ADR-010](0010-modelos-em-modo-sombra.md)).
- Quando a variação cabe na faixa da fase, a Cosmo só informa no relógio (nível 1) e não abre evento.
- Um novo tipo de consentimento, `saude_reprodutiva`, segue a [ADR-007](0007-consentimento-saude-mental.md): é por destinatário, pode ser revogado e nunca vai para o feed da família. O oficial médico só vê a fase com consentimento. Risco de vida continua sendo a única exceção.

## Alternativas consideradas

- **Linha de base única para todos:** Mais simples, mas gera alarme falso todo mês ou esconde um sinal real.
- **Fase como variável só no Isolation Forest:** Ajuda a marcar a combinação, mas o z robusto, que define o estado no relógio e no painel, continuaria sem saber da fase.
- **O médico vê o ciclo sempre:** Mais informação clínica, menos confiança da tripulante, que pode deixar de informar o contexto.

## Consequências

**Positivas**

- Menos alarmes falsos, o que ajuda a meta de menos de 1 por tripulante por semana.
- Dados separados por sexo, com consentimento, que hoje faltam na medicina espacial.

**Negativas**

- Os vitais sintéticos precisam cobrir pelo menos um ciclo de 28 dias; hoje são 14.
- Mais um campo no perfil e mais um tipo de consentimento no banco.
- A fase estimada pelo calendário pode errar, então a contagem de dias e os sinais do relógio entram juntos.

## Na demo

Evento "Ciclo e linha de base" e passo 10 do roteiro: a Cosmo informa a Sarah no relógio, ela decide se mostra ao Dr. Marcus, e o copiloto do painel só cita o ciclo com consentimento.
