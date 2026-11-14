# 5. Motor de decisões com humano no controle

Todo evento de saúde vira uma máquina de estados com um humano responsável. A IA só age sozinha em ações urgentes e reversíveis, e mesmo assim o humano pode desfazer.

## Níveis de autonomia

| Nível | O que a Cosmo faz | Exemplos na demo |
| --- | --- | --- |
| 0 · Observar | Registra e aprende o padrão de cada tripulante | Linha de base de FC, sono e HRV |
| 1 · Informar | Avisa, sem recomendar nada | Dose de radiação do dia, tendência de sono |
| 2 · Sugerir | Propõe; o humano decide | Beber água, respirar, prontidão para EVA |
| 3 · Preparar e pedir confirmação | Deixa tudo pronto e executa após um toque | Protocolo de emergência, abrigo, ultrassom guiado |
| 4 · Agir e avisar, com desfazer | Executa ações urgentes e reversíveis | Rota até o abrigo, modo noite, SOS na frente da fila |
| Nunca sozinha | Sempre exige um humano | Medicação, procedimentos invasivos, compartilhar saúde mental, tirar alguém de tarefa crítica |

## Quem decide cada tipo de evento

Os prazos são metas de projeto, a validar com o time médico.

| Tipo de decisão | Humano responsável | Prazo para responder | Sem resposta, vai para |
| --- | --- | --- | --- |
| Leitura suspeita do sensor | O próprio astronauta | 20 s | Oficial médico |
| Protocolo clínico | Oficial médico | 60 s | Comandante e tripulante com treino médico |
| Medicação | Oficial médico | Sem escalonamento automático | Oficial médico substituto |
| Abrigo contra radiação | Comandante | 2 min | Próximo na cadeia de comando |
| Escala de tarefa crítica | Comandante | Até o início da tarefa | Próximo na cadeia de comando |
| Compartilhar saúde mental | O próprio astronauta | Não escala | Ninguém; exceção só em risco de vida |
| Ação de nível 4 | O próprio astronauta, por veto | 15 s para vetar | Aplica e oferece desfazer |

## Estados de um evento

```mermaid
stateDiagram-v2
  state "Detectado" as Detectado
  state "Confirmação com o astronauta" as Confirmacao
  state "Proposto" as Proposto
  state "Aguardando humano" as Aguardando
  state "Escalonado" as Escalonado
  state "Decidido" as Decidido
  state "Em execução" as Execucao
  state "Resolvido" as Resolvido
  state "Encerrado" as Encerrado
  state "Agendado com veto" as Agendado
  state "Aplicado" as Aplicado

  [*] --> Detectado
  Detectado --> Confirmacao: sinal ruim
  Confirmacao --> Encerrado: ajustou o sensor
  Confirmacao --> Proposto: confirmou ou 20 s sem resposta
  Detectado --> Proposto: nível 2 ou 3
  Detectado --> Agendado: nível 4
  Proposto --> Aguardando
  Aguardando --> Escalonado: prazo vencido
  Escalonado --> Aguardando: próximo humano, novo prazo
  Aguardando --> Decidido: humano confirma, ajusta ou recusa
  Decidido --> Execucao: confirmado
  Decidido --> Encerrado: recusado
  Execucao --> Resolvido
  Agendado --> Aplicado: sem veto
  Agendado --> Encerrado: vetado
  Aplicado --> Encerrado: mantido ou desfeito
  Resolvido --> [*]
  Encerrado --> [*]
```

Cada transição grava na auditoria: evento, estado anterior e novo, quem decidiu, quando, versão do modelo e evidências usadas. O escalonamento sempre aponta para outro humano, nunca para a IA ([ADR-004](../adr/0004-humano-responsavel-e-escalonamento.md)).
