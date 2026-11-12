# 2. Requisitos

## Requisitos funcionais

São 26 requisitos, 16 deles essenciais para o MVP. Cada um vem de um fluxo que já existe na demo.

| ID | Requisito | Ator | Origem na demo | Prioridade |
| --- | --- | --- | --- | --- |
| RF01 | Ver o estado de saúde em 3 níveis (ótimo, atenção, crítico) com avatar e homeostase | Astronauta | Relógio · início | Essencial (MVP) |
| RF02 | Receber insights da Cosmo com ação em um toque (beber, respirar) | Astronauta | Relógio · insight | Essencial (MVP) |
| RF03 | Conversar com a Cosmo por voz ou texto, sem conexão com a Terra | Astronauta | Relógio · chat | Essencial (MVP) |
| RF04 | Confirmar ou negar uma leitura suspeita antes de virar alarme | Astronauta | Evento sensor solto | Essencial (MVP) |
| RF05 | Decidir se um alerta de bem-estar é compartilhado com o médico | Astronauta | Evento queda de humor | Essencial (MVP) |
| RF06 | Vetar ou desfazer ações automáticas reversíveis | Astronauta | Evento hora de dormir | Importante |
| RF07 | Ver atraso, fila e próxima janela de contato; disparar SOS prioritário | Astronauta | Relógio · sincronia | Essencial (MVP) |
| RF08 | Participar das missões da estufa e do Elo Terra com a família | Astronauta | Relógio · missões e Elo | Desejável |
| RF09 | Decidir se a tripulação vai para o abrigo de radiação | Comandante | Evento tempestade solar | Essencial (MVP) |
| RF10 | Decidir a escala de tarefas críticas a partir da prontidão de cada um | Comandante | Evento prontidão EVA | Importante |
| RF11 | Ver o painel de cada tripulante com ECG, sinais e a fonte de cada sensor | Oficial médico | Tablet | Essencial (MVP) |
| RF12 | Confirmar, rejeitar ou assumir protocolos da Cosmo, vendo evidências e confiança | Oficial médico | Emergência | Essencial (MVP) |
| RF13 | Liberar medicação em passo separado, definindo a dose | Oficial médico | Emergência | Essencial (MVP) |
| RF14 | Aprovar exames guiados e pedir ajustes à engenharia | Oficial médico | Evento dor de cabeça | Importante |
| RF15 | Enviar lembretes ao relógio de um tripulante | Oficial médico | Painel da Elena | Importante |
| RF16 | Ver dose de radiação, risco renal e CO₂ da cabine | Oficial médico | Tablet · faixa | Importante |
| RF17 | Perguntar ao copiloto sobre a tripulação, um tripulante ou o kit médico | Oficial médico | Tablet · copiloto | Importante |
| RF18 | Ver dados com a hora em que foram gerados e o estado do link | Flight surgeon | Console de Houston | Essencial (MVP) |
| RF19 | Revisar decisões tomadas a bordo e enviar parecer | Flight surgeon | Emergência | Essencial (MVP) |
| RF20 | Pedir ao copiloto um resumo do que houve desde o último contato | Flight surgeon | Houston · copiloto | Importante |
| RF21 | Ver o estado da tripulação em linguagem simples, sem sinais vitais | Família | App Terra-Órbita | Essencial (MVP) |
| RF22 | Trocar mensagens, brindes e corridas, vendo o atraso de entrega | Família | App · Elo e mensagens | Desejável |
| RF23 | Guardar e reenviar dados por prioridade quando o link cair | Sistema | Cenário blackout | Essencial (MVP) |
| RF24 | Escalonar ao próximo humano quando ninguém responde no prazo | Sistema | Evento sensor solto | Essencial (MVP) |
| RF25 | Registrar toda sugestão, decisão e escalonamento em trilha de auditoria | Sistema | Linha do tempo | Essencial (MVP) |
| RF26 | Ajustar o comportamento ao perfil de missão (atraso, link, autonomia) | Sistema | Perfil de missão | Importante |

## Atributos de qualidade

Três atributos guiam as decisões: segurança do paciente, operação sem a Terra e controle humano. Em conflito, vale a ordem da tabela. Os números são metas de projeto, a validar em teste.

| Ordem | Atributo | Estímulo | Resposta esperada (meta) |
| --- | --- | --- | --- |
| 1 | Segurança do paciente | Arritmia detectada no relógio | Alerta no pulso em menos de 1 s; protocolo no tablet em menos de 2 s, sem depender da Terra |
| 2 | Disponibilidade offline | Link com a Terra cai por 14 dias | Todas as funções de bordo seguem; nenhum dado se perde |
| 3 | Controle humano e auditoria | Qualquer decisão clínica | 100% com um humano responsável registrado, com sugestão, evidências e versão do modelo |
| 4 | Tolerância a atraso | Mensagem para a Terra com 3 a 22 min de atraso | Entrega garantida; prioridade 1 sai à frente na próxima janela |
| 5 | Privacidade | Alerta de bem-estar sem consentimento | Nenhum dado sai do relógio; a família recebe só texto de status |
| 6 | Confiabilidade dos alarmes | Leitura com sinal ruim | O astronauta confirma antes de escalar; menos de 1 alarme falso por tripulante por semana |
| 7 | Explicabilidade | Protocolo proposto pela Cosmo | Evidências, confiança e alternativa visíveis; o médico decide em menos de 30 s |
| 8 | Usabilidade sob estresse | Alerta crítico | Entendido num olhar (cor, avatar, uma ação); operável por voz e com luva |
| 9 | Eficiência de energia | Monitoramento contínuo no relógio | Bateria de pelo menos 24 h; modelos grandes rodam fora do relógio |
| 10 | Segurança da informação | Dispositivo perdido ou nó invadido | Dados cifrados em repouso e em trânsito; autenticação mútua entre nós |
| 11 | Modificabilidade | Novo sensor ou novo tipo de evento | Entra como regra e máquina de estados, sem mudar os apps; perfil de missão por configuração |

### Conflitos já resolvidos pela ordem

- **Segurança acima de privacidade, só em risco de vida:** uma emergência clínica vai ao médico sem pedir consentimento. Saúde mental fora de emergência continua exigindo consentimento.
- **Offline acima de eficiência:** o relógio guarda dados localmente mesmo gastando mais bateria, e a fila nunca descarta alertas.
- **Controle humano acima de velocidade:** até numa emergência, a Cosmo orienta o astronauta na hora, mas o protocolo só é aplicado depois da confirmação do médico.
