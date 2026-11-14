# ADR-012: Ciclo hormonal monitorado com ou sem supressão, privado por padrão

- **Status:** aceita
- **Data:** 2026-11-14
- **Relacionadas:** ADR-001, ADR-003, ADR-007

## Contexto

O mapa de riscos tratava a tripulação sem considerar o ciclo hormonal. Em missões longas, astronautas costumam suprimir a menstruação com pílula combinada contínua, e DIU ou implante são opções seguras, mas ainda pouco usadas em voo ([Jain e Wotring, 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5516549)). Com ou sem método, o corpo continua dando sinais: no pulso, a temperatura da pele sobe cerca de 0,3 °C na fase lútea ([Shilaih et al., 2018](https://pubmed.ncbi.nlm.nih.gov/29175999/)), e FC e respiração também mudam por fase ([Goodale et al., 2019](https://www.jmir.org/2019/4/e13404/)). Sem esse contexto, a linha de base pessoal (M3) confunde a fase lútea com febre ou estresse.

## Decisão

Um quarto modelo (M4) roda no relógio e estima a fase do ciclo a partir das noites: deslocamento térmico (3 noites acima das 6 anteriores) e um HMM de 2 estados, sem supervisão. Ele também lê os registros da astronauta (sangramento, sintomas e método). A saída tem dois usos:

1. Avisar a astronauta, antes, quando os sintomas devem chegar.
2. Ajustar a linha de base do M3, para a fase lútea não virar alarme.

O ciclo é privado por padrão. Só a astronauta vê a fase; compartilhar com o oficial médico é escolha dela e pode ser revogado, como na ADR-007. Houston e a família nunca recebem o ciclo. O ajuste da linha de base vale mesmo sem compartilhamento, porque não expõe a fase.

## Alternativas consideradas

- **Ignorar o ciclo quando há supressão:** Mais simples, mas perde os sinais de escape e mantém os falsos alarmes do M3.
- **Ciclo visível para o oficial médico por padrão:** Mais contexto clínico, mas expõe dado reprodutivo sem escolha da astronauta.
- **Modelo supervisionado treinado em dado real:** Mais preciso, mas o mcPHASES (PhysioNet) exige credenciamento e não chega a tempo do hackathon; fica para a validação.

## Consequências

**Positivas**

- Diferencial de cuidado com a mulher, ligado a um ganho técnico: menos falsos alarmes no M3.
- Dado reprodutivo tratado como sensível (LGPD, art. 11), com consentimento explícito.

**Negativas**

- No hackathon, o M4 só é testado em ciclos sintéticos.
- Mais um consentimento para a astronauta gerenciar.
