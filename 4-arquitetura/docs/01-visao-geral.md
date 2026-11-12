# 1. Visão geral

O AstroHealth OS monitora a saúde da tripulação a bordo e apoia decisões com um humano no controle, mesmo sem contato com a Terra. Esta arquitetura sai direto da demo navegável: cada fluxo dela vira requisito, componente e diagrama.

**Problema.** Quanto mais longe da Terra, maior o atraso e mais longos os períodos sem sinal. A caminho de Marte, cada mensagem leva minutos para chegar. Houston deixa de ser quem responde primeiro, e a nave precisa de medicina própria.

## Escopo desta fase

- **Dentro:** monitoramento contínuo pelo relógio, IA local (Cosmo), motor de decisões com humano no controle, painel do oficial médico, console de Houston, app da família e comunicação tolerante a atraso.
- **Fora, por ora:** certificação médica, integração com o hardware real da nave e controle de sistemas de suporte de vida. Nesses sistemas a Cosmo só sugere; quem age é a engenharia.

## Princípios de arquitetura

1. **Offline primeiro:** tudo o que protege a vida roda a bordo, sem depender da Terra.
2. **Humano no controle:** a IA nunca toma sozinha uma decisão clínica ou irreversível.
3. **O humano certo decide:** astronauta, oficial médico ou comandante, conforme o tipo de decisão.
4. **Atraso é dado:** toda informação carrega quando foi gerada e quando chegou.
5. **Privacidade por padrão:** saúde mental só sai do relógio com consentimento; a família nunca vê sinais vitais.
6. **Sensores honestos:** cada métrica declara sua fonte e a qualidade do sinal.
7. **Auditoria total:** toda sugestão, decisão e escalonamento fica registrado.

## Como a arquitetura responde aos perigos RIDGE

A NASA organiza os riscos de voos longos em cinco perigos ([NASA HRP](https://www.nasa.gov/hrp/hazards)).

| Perigo (RIDGE) | Risco para a tripulação | Resposta da arquitetura |
| --- | --- | --- |
| Radiação | Câncer, danos ao sistema nervoso, mal agudo em tempestades solares | Dosímetro + Cosmo detectam o pico a bordo; a comandante decide o abrigo |
| Isolamento e confinamento | Queda de humor, conflitos, saudade | Alerta de bem-estar com consentimento; Elo Terra com a família |
| Distância da Terra | Ajuda médica demora ou some | IA local, decisões a bordo, rede tolerante a atraso |
| Gravidade | Perda óssea e muscular, coração, olhos (SANS), rins | Treino prescrito, hidratação, ultrassom guiado |
| Ambiente hostil e fechado | CO₂ alto, calor no traje, medicamentos degradados | Cruzamento de sintomas com o ar da cabine; farmácia de bordo |

## Ligação com o desafio

O projeto responde ao desafio [Create Health Monitoring Software for Astronauts…](https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/) da NASA Space Apps 2026. O evento acontece em 14 e 15 de novembro de 2026; as submissões fecham dia 15 às 23:59, no horário local ([Space Apps 2026](https://www.spaceappschallenge.org/2026/)).

> **Pendente:** colar aqui o enunciado oficial e os critérios de avaliação, e cruzar cada critério com os requisitos de [02-requisitos.md](02-requisitos.md).
