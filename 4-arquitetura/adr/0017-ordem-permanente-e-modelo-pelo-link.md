# ADR-017: Sem médico a bordo, ordem permanente no blackout e aprovação de modelo pelo link

- **Status:** aceita
- **Data:** 2026-11-15
- **Relacionadas:** ADR-004, ADR-005, ADR-010, ADR-015 (altera)

## Contexto

A ADR-015 trata o médico a bordo como hipótese. Sem médico a bordo, a médica de voo decide de Houston, e cada decisão viaja com o atraso da missão. Pela ADR-015, sem sinal a medicação fica bloqueada até o contato voltar. Rumo a Marte, a conjunção solar dura cerca de 14 dias, e uma fibrilação atrial que não cede às ações seguras não pode esperar tanto.

A aprovação de modelo também tinha um atalho. Na demo, a aprovação da médica de voo valia na hora, sem o atraso que as decisões clínicas já respeitavam.

## Decisão

1. **Ordem permanente.** Antes do voo, a médica de voo assina a ordem `OP-FA-01` para fibrilação atrial. Ela tem dose fixa e só vale com todos os critérios:
   - não há médico a bordo;
   - não há sinal com a Terra;
   - as ações seguras já foram iniciadas;
   - o M1 ainda vê FA na última leitura com sinal bom;
   - nenhuma dose foi aplicada no evento.

   O motor confere os critérios. O CMO, ou quem o substitui na cadeia, aplica e registra, e a dose não muda. O uso fica assinado na auditoria e sobe como P1. Quando o sinal volta, a médica revisa por parecer. O uso da ordem não vira rótulo do M1, porque o CMO não é médico. Se uma liberação da Terra chegar depois, ela não se aplica e o motivo fica registrado.
2. **Aprovação de modelo pelo link.** Sem médico a bordo, aprovar ou rejeitar um candidato em sombra vira um pacote P4 de Houston para a nave. A decisão só vale quando chega e só para a versão que a médica viu. Se o candidato mudar no caminho, ela não se aplica e o motivo fica na auditoria. No blackout, o pacote espera na fila.

## Alternativas consideradas

- **Manter a medicação bloqueada no blackout:** Mais simples, mas deixa a tripulação sem tratamento por dias numa arritmia que não cedeu.
- **Deixar a Cosmo liberar a dose sem sinal:** Viola a ADR-002 e a ADR-004. Medicação nunca é decisão da IA.
- **Liberar a dose para o CMO decidir no blackout:** O CMO não tem formação médica. A ordem permanente transfere a decisão para antes do voo, com critérios objetivos.

## Consequências

**Positivas**

- A tripulação tem tratamento no blackout longo sem que a IA ou um não médico decida a dose.
- A aprovação de modelo vinda da Terra tem a mesma regra das decisões clínicas: só vale o que chegou.

**Negativas**

- A ordem é escrita sem ver o paciente. Os critérios precisam de revisão clínica antes de uso real; a dose da demo não é orientação clínica.
- Um modelo melhor demora pelo menos um trecho de link para entrar em serviço.
- O pedido de retreino feito da Terra continua imediato na demo. Ele só cria um candidato em sombra, que não age.
