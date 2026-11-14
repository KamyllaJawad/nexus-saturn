# ADR-013: Calendário do ciclo no relógio, com cuidado leve

- **Status:** aceita
- **Data:** 2026-11-12
- **Relacionadas:** ADR-007, ADR-012

## Contexto

Homens e mulheres voam. Cada pessoa embarca com a própria ficha de solo, e a Cosmo lê essa ficha antes de falar. Quando a ficha tem calendário menstrual, ela traz o método hormonal, a última menstruação, a duração típica e o trecho em que os sintomas costumavam ser mais intensos. Esse calendário foi fechado em solo, meses antes do lançamento. No pulso, uma variação leve de frequência, temperatura, sono ou HRV nesse trecho pode parecer anomalia. A família não participa dessa leitura.

## Decisão

A direção da resposta sai da ficha, não de um gênero genérico. Se a ficha tem calendário, a Cosmo prevê o trecho intenso e avisa só aquela pessoa, cerca de dois dias antes. Se a ficha não tem calendário, a pergunta de cólica não abre, e a Cosmo segue a linha de base pessoal: sono, hidratação, treino e osso. Na tripulação da demo, Sarah e Elena têm calendário; Marcus e Kenji não têm. O calendário da Elena fica no relógio dela até ela autorizar. O relógio avisa os sintomas do trecho intenso: cólica, inchaço ou humor mais baixo. O método não fica repetido na tela. A Cosmo só cita supressão (pílula, DIU ou implante) ou ausência de método quando precisa explicar uma resposta. Na supressão, essa explicação não trata o trecho como ovulação. Sem método, a janela segue a última menstruação e a duração típica. A tela não fala em ovulação nem em janela fértil.

A pergunta de cólica, inchaço ou humor só aparece quando as três condições valem juntas: o calendário diz que ela está no trecho intenso, os sinais leves acompanham (frequência e temperatura da pele um pouco acima da mediana dela, sono mais curto ou HRV mais baixo) e o M2 classifica o sinal como bom. O estado de três níveis não muda por causa desse trecho.

O cuidado é nível 2, e ela aceita ou recusa: respirar um minuto, treino mais leve, modo noite mais cedo, água só se a hidratação do dia estiver baixa. Analgésico do kit continua com o oficial médico, em passo separado, e só se ela pedir. A Cosmo não troca método e não recomenda suprimir.

O oficial médico e Houston só veem o calendário e o sintoma com consentimento dela. A comandante, quando for outra pessoa, não vê. A família não recebe fase, calendário, método nem sintoma. Fora da janela, sinal crítico ou fibrilação atrial seguem o fluxo da [ADR-012](0012-linha-de-base-com-isolation-forest.md).

O método na ficha é nenhum, pílula combinada contínua, DIU de levonorgestrel ou implante. A injeção trimestral de progestina fica de fora: a perda óssea do voo é tratada como irreversível, e essa injeção reduz a massa óssea.

## Alternativas consideradas

- **Detectar a fase pelo relógio:** Não há estudo que valide essa detecção em microgravidade. A ficha de solo já traz o calendário.
- **Tratar a supressão como ciclo ovulatório:** A pílula contínua não mantém fase ovulatória. A Cosmo só diz isso quando a resposta precisa desse contexto.
- **Avisar a família:** O dado é de quem tem o calendário. O feed da família continua em frases de status, sem ciclo.
- **Uma resposta só, igual para toda a tripulação:** Homens e mulheres voam, e a ficha de cada um muda o que a Cosmo pode perguntar.

## Consequências

**Positivas**

- O alarme mensal falso não abre, e o cuidado leve chega antes do trecho intenso.
- A privacidade segue o mesmo desenho da saúde mental.

**Negativas**

- A previsão enfraquece quando a última data confirmada fica velha ou o ritmo de sono quebra. Ela pode corrigir o dia no relógio.
- O efeito da pílula contínua sobre o osso em microgravidade segue em aberto. A Cosmo cita essa lacuna só quando explica a resposta, não no cartão que o médico vê o tempo todo.
