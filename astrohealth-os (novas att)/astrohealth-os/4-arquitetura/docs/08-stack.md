# 8. Stack híbrida

Os diagramas descrevem o sistema como ele seria numa nave real. O protótipo do hackathon implementa as mesmas fronteiras com a stack que o time já domina. Regra para as duas colunas: o LLM conversa, explica e resume, mas quem decide o estado de um evento é o motor de decisões determinístico.

| Camada | Referência para produção (padrão NASA) | Protótipo do hackathon |
| --- | --- | --- |
| Relógio (borda) | Wear OS, watchOS ou firmware dedicado; modelos pequenos quantizados (TFLite/LiteRT, ONNX) para arritmia e qualidade de sinal | Relógio simulado na demo web; modelos em Python com ONNX Runtime ou scikit-learn |
| Rede local da nave | Wi-Fi e BLE da nave; mensageria com QoS e autenticação mútua | MQTT (Mosquitto) ou WebSocket local |
| Cosmo nave | LLM local quantizado + RAG sobre protocolos médicos e manual do kit, sem internet | Python + FastAPI; LangChain ou CrewAI; ChromaDB com os protocolos; LLM local via Ollama |
| Motor de decisões | Regras + máquina de estados determinística, certificável e testável | Python com máquina de estados (biblioteca transitions ou própria) |
| Armazenamento | Banco embarcado + log de auditoria só de inclusão, com hash encadeado | SQLite + tabela de eventos só de inclusão |
| Link nave ⇄ Terra | DTN com Bundle Protocol (por exemplo, o ION da NASA), custódia e prioridade | Simulador de atraso em Python: fila por prioridade e atraso configurável por perfil de missão |
| Cosmo Terra (Houston) | Modelos maiores, inclusive em nuvem, sob regras para dados de saúde | FastAPI + LangChain; API da OpenAI permitida só aqui, nunca a bordo |
| App da família | App móvel; filtro de privacidade aplicado no servidor da Terra | Página web responsiva, como na demo |
| Testes | Testes de cenário e de tempo real | Robot Framework para aceitação dos fluxos + pytest nas regras |

**Por que híbrida:** a banca vê uma arquitetura plausível para uma nave real, e o time entrega código funcionando em 48 h. Trocar o simulador pelo ION ou o relógio simulado por um real não muda as fronteiras entre os componentes ([ADR-011](../adr/0011-stack-hibrida.md)).

## Estrutura sugerida do código do protótipo

```text
astrohealth/
├── nave/
│   ├── ingestao/          # leituras + qualidade de sinal
│   ├── detectores/        # arritmia, artefato, prontidão, humor
│   ├── motor/             # máquina de estados + regras + prazos
│   ├── cosmo/             # LangChain/CrewAI + ChromaDB + Ollama
│   ├── auditoria/         # log com hash encadeado (SQLite)
│   └── gateway_dtn/       # fila por prioridade + simulador de atraso
├── terra/
│   ├── servidor/          # recepção, confirmação, filtro de privacidade
│   └── cosmo_terra/       # copiloto de Houston
├── apps/                  # relógio, tablet, console, família (web)
├── contratos/             # JSON Schemas compartilhados
└── testes/
    ├── aceitacao/         # Robot Framework, um .robot por fluxo
    └── unidade/           # pytest
```
