# ADR-012: Linha de base com z robusto e Isolation Forest

- **Status:** aceita
- **Data:** 2026-11-12
- **Relacionadas:** ADR-002, ADR-003, ADR-010

## Contexto

O M3 descreve o padrão de cada tripulante. O z robusto diz, sinal por sinal, se a leitura está no padrão, em atenção ou crítica. Uma combinação pode sair do padrão da pessoa mesmo quando nenhum sinal cruza a faixa sozinho. O plano de 11/11 deixava o Isolation Forest para se sobrasse tempo.

## Decisão

O M3 entra no hackathon com as duas peças, e as duas saem de `analisar(leitura)`.

- O **z robusto** (mediana e MAD de cada tripulante, por sinal) define a faixa de FC, SpO₂, HRV, temperatura, sono e hidratação. A soma dessas faixas vira o estado de três níveis e a homeostase do relógio e do painel.
- O **Isolation Forest** (`m3-if-0.1`) é um modelo por tripulante, treinado só nos minutos normais dos vitais sintéticos. O pipeline ajusta um `RobustScaler` naquela pessoa e, em seguida, a floresta. O limiar é o escore que, na validação, gera no máximo 1 alarme por pessoa por dia simulado. A explicação troca cada sinal pela mediana daquela pessoa e lista os que mais reduzem o escore.

O bloco `isolation_forest` traz `anomalo`, `score`, `limiar`, `evidencias` e `versao_modelo`. O escore não substitui a frase por sinal.

O motor abre uma sugestão de nível 1 só quando as três condições valem juntas: o Isolation Forest marca anomalia, o M2 classifica o sinal como bom e nenhum sinal está crítico sozinho. A sugestão não muda estado clínico. Se o M1 já abriu fibrilação atrial, ou se um sinal está crítico, permanece o evento aberto. A família não recebe escore nem faixa.

## Alternativas consideradas

- **Só o z robusto:** Explica cada sinal e deixa passar a combinação em que nenhum sinal cruza a faixa sozinho.
- **Só o Isolation Forest:** Marca a combinação e não diz qual sinal subiu ou desceu, que é o que o relógio e o painel mostram.
- **Isolation Forest no lugar do M1:** O M1 classifica fibrilação atrial em ECG rotulado e devolve classe, confiança e atributos de RR. A floresta não faz isso.

## Consequências

**Positivas**

- O painel mostra a faixa de cada sinal e, quando cabe, a combinação que saiu do padrão.
- A versão `m3-if-0.1` fica registrada em cada sugestão.

**Negativas**

- Mais um artefato para treinar e um limiar para calibrar.
- O escore não é probabilidade clínica.
