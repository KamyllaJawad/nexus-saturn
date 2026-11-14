# ADR-013 · Médico a bordo é hipótese; cenários por sexo; 4 fases do ciclo

Status: aceita em 2026-11-14

## Contexto

Não dá para garantir que toda missão terá um médico na tripulação. Muitas missões levam só um oficial de saúde (CMO) com treino de primeiros socorros. Também faltava mostrar que o sistema cuida de homens e mulheres de jeitos diferentes, e o ciclo hormonal aparecia numa fase só.

## Decisão

1. **Médico da missão é uma hipótese da demo**, com duas opções:
   - **A bordo:** o Dr. Marcus confirma o protocolo e libera a medicação no painel de bordo. Houston revisa depois.
   - **Só na Terra:** o Marcus vira CMO. No painel de bordo ele só inicia as **ações seguras pré-aprovadas** (repouso, O₂ a 2 L/min, ECG de 12 derivações), que não esperam o atraso. **Quem confirma o protocolo e libera a medicação é a médica de voo no console de Houston** (Dra. Rivera). Cada decisão viaja com o atraso da missão; rumo a Marte, a ida e volta passa de 16 min.
   - Sem sinal e sem médico a bordo: só protocolos pré-aprovados; a medicação fica bloqueada até o contato voltar.
2. **Cenários por sexo.** A hipótese "Quem usa o relógio" troca entre Sarah (mulher) e Kenji (homem):
   - Mulheres: ciclo hormonal (M4), intolerância ortostática no pouso e infecção urinária, mais frequentes em mulheres.
   - Homens: SANS (visão e pressão intracraniana), um pouco mais frequente em homens. A Cosmo pergunta sobre visão embaçada e pede ultrassom ocular a quem for o médico. Audiometria periódica, porque a audição cai mais rápido com a idade em homens.
   - A diferença entre pessoas costuma ser maior que a diferença entre sexos. Por isso os alertas sempre partem da linha de base de cada um (M3); o sexo só muda o que a Cosmo pergunta e vigia.
3. **O M4 estima 4 fases** em um ciclo de exemplo de 28 dias, ajustado pela temperatura de cada mulher: menstrual (1–5), folicular (6–12), ovulatória (13–15) e lútea (16–28), com a lútea tardia (TPM) a partir do dia 22. O relógio avisa a fase atual com os sintomas possíveis **e** a próxima fase, com quantos dias faltam e o que pode começar.
4. **Privacidade do ciclo:** o ciclo vai só para o médico, onde ele estiver, e só com consentimento. Com o médico na Terra, ele vai só para a Dra. Rivera; o CMO, o resto de Houston e a família não veem.

## Consequências

- O motor de decisões ganha um campo `medico_local: bordo | terra` que muda quem pode confirmar cada ação.
- Pessoa 3 precisa rotear a decisão médica para o console de Houston quando `medico_local = terra`.
- Pessoa 2 ganha a tela "Visão (SANS)" no relógio e o bloco de decisão no console de Houston.
- O gerador de ciclos sintéticos (B-10) precisa cobrir as 4 fases e a lútea tardia.
