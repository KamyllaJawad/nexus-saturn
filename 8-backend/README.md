# 8-backend · serviço da nave e da Terra

MVP funcional do AstroHealth OS. O relógio é simulado; o que vem depois da leitura é de verdade: modelos treinados, motor de decisões determinístico, humano decidindo, auditoria encadeada e link com atraso.

Protótipo experimental com dados simulados. **Não é dispositivo médico.**

## Rodar

Na raiz do repositório (Windows; no Linux/macOS troque `.venv\Scripts\` por `.venv/bin/`):

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r 8-backend/requirements.txt
cd 8-backend
..\.venv\Scripts\python -m treino.pipeline        # trata os dados e treina M1, M2 e M3 (~40 s)
..\.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Abra <http://127.0.0.1:8000/>. A API serve as telas de `9-frontend/`; a documentação das rotas fica em `/docs`.

O treino usa o **PhysioNet/CinC Challenge 2017** se o arquivo `dados/bronze/cinc2017/training2017.zip` existir (94,6 MB, fora do git):

```bash
curl -L -o dados/bronze/cinc2017/training2017.zip https://physionet.org/files/challenge-2017/1.0.0/training2017.zip
```

Sem o zip, o pipeline gera ECG sintético e marca `origem: sintetico` no lote (`python -m treino.pipeline --sem-cinc` força esse caminho).

## Testar

```bash
..\.venv\Scripts\python -m pytest testes -q            # 49 testes, cerca de 3 min, sem servidor
..\.venv\Scripts\python testes/ensaio_ao_vivo.py       # roteiro pela API, com o servidor no ar
..\.venv\Scripts\python -m treino.ver_relatorio        # métricas do último treino
```

## O que é real e o que é simulado

| Peça | Situação |
| --- | --- |
| Relógio, patch, kit, dosímetro e CO₂ | **Simulados.** Uma leitura por segundo por tripulante, com o mesmo ruído AR(1) dos dados de treino. |
| Trecho de ECG | **Real.** Gravações do conjunto de *teste* do CinC 2017, que nenhum modelo viu no treino. |
| M1, M2, M3 | **Treinados e rodando.** O cenário só muda o sinal; quem detecta é o modelo. |
| Motor de decisões, auditoria, consentimento | **Reais**, com testes. |
| Link nave ↔ Terra | Simulador de atraso e fila P1–P4. Não é DTN/Bundle Protocol. |
| Cosmo | Busca TF-IDF local nos 12 protocolos de `protocolos/`, com a fonte citada. Usa Ollama em `127.0.0.1:11434` se houver (`COSMO_MODELO`, padrão `llama3.2:3b`); sem ele, respostas locais. Não usa ChromaDB nem LangChain. |
| MQTT | Não usado. As telas buscam a API a cada 1 s, como no plano do time. |

## Métricas medidas (lote com o CinC 2017)

Rode `python -m treino.ver_relatorio` para os números do seu treino. No lote de 14/11:

| Modelo | Resultado no teste | Meta | |
| --- | --- | --- | --- |
| M1 `arritmia-borda-0.3` · Random Forest, 18 atributos de RR | F1 da FA **0,69** (IC 95% 0,62–0,75; validação 0,76) | ≥ 0,75 | **não batida** |
| M2 `qualidade-0.2` · Random Forest (escolhido contra regressão logística, na validação) | recall de suspeito **0,92**, precisão 0,89 | ≥ 0,9 | batida |
| M3 `m3-if-0.1` · Isolation Forest por tripulante | ≤ 1 alarme/pessoa/dia; recall 1,0 com desvio em 3 ou 4 sinais | ≤ 1/dia e ≥ 0,9 | batida |

Limitações que valem para o pitch:

- **M1 abaixo da meta.** Só intervalos RR, sem morfologia da onda P. O erro principal é FA × "outro ritmo". O número é reportado como saiu; o limiar foi escolhido na validação.
- **Banco do simulador curado.** Das 90 gravações de teste separadas para a demo, o simulador usa só as 84 em que os modelos em serviço acertam, para a demo não disparar sozinha. A taxa de erro real é a da tabela, não a que se vê na tela.
- **M3: desvio em só 2 sinais** fica dentro da nuvem normal da pessoa (recall ~0,8). O alarme pede 5 leituras seguidas acima do limiar.
- **Vitais sintéticos:** 2 dias por tripulante. O M3 prova o mecanismo, não a precisão clínica.
- O trecho do ciclo fica **fora** do treino da floresta (diferente do `ouro_vitais_normais.csv` original): quem explica essa janela é o calendário (ADR-013).

## Human-in-the-loop

Dois circuitos, os dois com um humano nomeado na auditoria.

**Decisão clínica** (`app/nave/motor.py`): o `ia.analisar` não muda estado. O motor abre o evento, a Cosmo anexa a sugestão e só `POST /api/decisoes` com um `humano_id` da tripulação avança. Prazo vencido escala para outro humano. Medicação é passo separado, só do oficial médico, com dose e PIN (demo: `2026`).

**Aprendizado do modelo** (`app/hitl.py`, ADR-010):

1. Cada resposta humana vira rótulo: o médico confirma ou recusa a FA (M1); a pessoa ajusta o relógio ou o kit desmente a leitura (M2); a pessoa responde "é o meu normal" ou "não estou bem" ao aviso da floresta (M3).
2. `POST /api/ia/retreinar` junta o ouro com os rótulos e gera um candidato com versão nova.
3. O candidato entra em **modo sombra**: roda em cada leitura, sem agir, e é comparado com o modelo em serviço.
4. Só o oficial médico promove (`/api/ia/modelos/{peca}/aprovar`). Outro tripulante recebe 403.

A tela **Dados e IA** mostra o custo antes da aprovação. Exemplo medido: declarar normal um padrão do Kenji tira o aviso falso, e o recall dele para desvios de 3 sinais cai de 1,0 para ~0,84.

## Chat da Cosmo (painel de bordo e Houston)

As duas telas têm um chat com histórico e perguntas sugeridas (`GET /api/cosmo/perguntas`). O grupo **Agora** traz as perguntas do cenário em curso e muda com o estado do evento; os outros grupos ficam sempre disponíveis. As respostas (`POST /api/cosmo/chat`) saem de `app/nave/dialogo.py`, montadas só com a visão daquela superfície:

- **Bordo:** o agora. Dado privado sem consentimento não entra na visão, então a Cosmo não fala dele nem confirma que existe.
- **Houston:** só o retrato atrasado e os eventos cujo pacote já chegou. Cada resposta diz de quando é o dado.
- Pedido de ação ("aprove", "libere") recebe recusa: a Cosmo não tem rota que mude estado.

`testes/test_cosmo_chat.py` percorre os 11 cenários e faz todas as perguntas sugeridas nas duas telas.

## Médico a bordo ou só na Terra

Nem toda missão leva médico. A hipótese da [ADR-015](../4-arquitetura/adr/0015-medico-a-bordo-e-cenarios-por-sexo.md) ("médico a bordo é hipótese") troca na sala de simulação (`medico_bordo` ou `medico_terra`). Com o médico na Terra:

| | A bordo | Só na Terra |
| --- | --- | --- |
| Marcus | Dr. Marcus, oficial médico | Marcus, oficial de saúde (CMO), sem formação médica |
| Arritmia | O Dr. Marcus confirma o protocolo no painel | O CMO só inicia as **ações seguras pré-aprovadas** (repouso, O₂, ECG de 12 derivações), sem esperar o atraso. A Dra. Rivera confirma o protocolo no console de Houston (`POST /api/houston/decisao`) |
| Medicação | O Dr. Marcus define a dose, assina com PIN e aplica | A Dra. Rivera define a dose e assina com PIN em Houston. A liberação viaja pelo link e o CMO registra a aplicação a bordo |
| Dor de cabeça + CO₂ | O médico aprova o ultrassom | O CMO ajusta o ar (ação segura); a Dra. Rivera aprova o ultrassom |
| Prazo vencido | Escala na cadeia de bordo | As ações seguras escalam na cadeia de bordo. A decisão médica espera a Terra e não escala para a IA |
| Sem sinal | A bordo nada para | Só protocolos pré-aprovados; Houston recebe 409. Na FA, o CMO pode usar a **ordem permanente** `OP-FA-01`, assinada pela Dra. Rivera antes do voo ([ADR-017](../4-arquitetura/adr/0017-ordem-permanente-e-modelo-pelo-link.md)) |
| Saúde mental e ciclo | Com consentimento, vão ao Dr. Marcus | Com consentimento, vão só à Dra. Rivera. O CMO, o resto de Houston e a família não veem |
| Modelo novo | O Dr. Marcus aprova na hora | A aprovação da Dra. Rivera viaja como P4 e só vale quando chega, para a versão que ela viu (ADR-017) |

A decisão da Terra só vale quando o pacote chega (`decidir(..., via="link")`). Se a nave já tiver avançado quando o pacote chega, a decisão não se aplica, e isso fica registrado na auditoria (`decisao_terra`). Um evento aberto segue a regra com que nasceu, mesmo que a hipótese troque no meio. `testes/test_medico_terra.py` cobre esses casos.

**Ordem permanente** (`config.ORDEM_PERMANENTE`, ação `ordem_permanente` no motor). O motor só aceita com todos os critérios:

- não há médico a bordo;
- não há sinal com a Terra;
- as ações seguras já foram iniciadas;
- o M1 ainda vê FA na última leitura;
- nenhuma dose foi aplicada no evento.

A dose é a da ordem, mesmo que outra seja enviada. O uso sobe como P1 e não vira rótulo do M1, porque o CMO não é médico. Se uma liberação da Terra chegar depois, não se aplica. A dose da demo não é orientação clínica.

## Trilha da Cosmo (tokens, latência, custo, decisão, passos)

Cada fala da Cosmo gera um registro em `app/nave/trilha.py` ([ADR-018](../4-arquitetura/adr/0018-trilha-minima-da-cosmo.md)). A trilha aparece no painel de bordo e no console de Houston, e cada resposta do chat mostra um rodapé curto com os mesmos números.

| Campo | Como é medido |
| --- | --- |
| Tokens | Contados pelo Ollama quando ele responde; sem LLM, estimados (4 caracteres por token) e marcados como estimados |
| Latência | Tempo de parede da chamada e de cada passo, em ms |
| Custo | `COSMO_USD_1M_ENTRADA` e `COSMO_USD_1M_SAIDA` (US$ por milhão de tokens; padrão 0, tudo local) e energia estimada com `COSMO_WATTS` (padrão 15 W) |
| Decisão | `respondeu`, `recusou agir`, `sugeriu` ou `sem resposta`; `pode_agir` sempre falso |
| Passos | Chat: visão, intenção, busca, resposta, redação, guarda. Sugestão: entrada, protocolo, entrega |

O que cada superfície vê:

- **Bordo:** o chat do painel e as sugestões dos eventos que o painel pode ver. O chat do relógio e a sugestão de dado privado sem consentimento não aparecem.
- **Houston:** a Cosmo Terra e a trilha das sugestões de bordo que já chegaram pelo link, sem pergunta nenhuma.

Tudo fica na tabela `cosmo_trilha`, só de inclusão, e na auditoria encadeada (entidade `cosmo`, só métricas). Rota: `GET /api/cosmo/trilha?superficie=bordo|houston`. `testes/test_ordem_e_trilha.py` cobre a ordem, a aprovação pelo link e a trilha.

## Cenários (`POST /api/simulador/cenario`)

| `cenario` | O que acontece | Quem decide |
| --- | --- | --- |
| `fa` | ECG de FA do teste → M1 abre arritmia nível 3 | Oficial médico; em 60 s escala |
| `sensor_solto` | Ruído no trecho + SpO₂ 84% → M2 segura o M1 e o relógio pergunta | A própria pessoa; em 20 s vai ao médico |
| `combinacao` | Desvio leve em 4 sinais → floresta → sugestão nível 1, sem evento | A pessoa responde; vira rótulo |
| `ciclo` | Desvio leve + calendário da ficha → pergunta privada nível 2 | Só ela; compartilha se quiser |
| `humor` | Alerta de bem-estar privado | Só a pessoa; não escala |
| `tempestade_solar` | Rota acesa (nível 4) e pergunta de abrigo | Comandante |
| `eva`, `dor_de_cabeca`, `modo_noite` | Escala, CO₂ + ultrassom, ação com veto de 15 s | Comandante, médico, a pessoa |
| `blackout`, `sinal_volta` | Fila guarda tudo; P1 sai primeiro | — |
| `leo`, `gateway`, `mars`, `marsSurf` | Perfil de missão (acima de 5 s, 1 min de atraso = 1 s) | — |
| `medico_bordo`, `medico_terra` | Onde está o médico da missão: vale para os eventos que abrirem depois | — |
| `rotina` | Sinais de volta ao normal | — |

## Pastas

```text
app/
  ia.py            M1, M2, M3 e calendário: analisar(leitura)
  sinais.py        picos R, atributos de RR e de qualidade, ruído
  hitl.py          rótulos, retreino, modo sombra, aprovação
  main.py          API (uma visão por superfície)
  nave/            simulador, motor, link, cosmo, dialogo (chat), registro (SQLite + auditoria)
  terra/           frases da família
treino/pipeline.py bronze -> prata -> ouro -> modelos/
dados/             bronze, prata, ouro, treino (zonas do lakehouse)
modelos/           artefatos .joblib, registro.json, relatorio.json
protocolos/        base da Cosmo
testes/
```

Contrato `evento.atualizado` na versão 1.1: além do schema de `4-arquitetura/contratos/`, o campo `acao` aceita as ações novas listadas em `ACOES` (`motor.py`), e os avisos do relógio (`ciclo`, `linha_de_base`, `hidratacao`) não viram essa mensagem.

## Créditos dos dados

ECG: Clifford GD et al. *AF Classification from a Short Single Lead ECG Recording: the PhysioNet/Computing in Cardiology Challenge 2017.* Computing in Cardiology, 2017. PhysioNet, licença ODC-By 1.0.
