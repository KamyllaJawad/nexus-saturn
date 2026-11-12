# 7. Modelo de dados e contratos

O centro do modelo é o Evento: leituras abrem eventos, a Cosmo anexa sugestões e só humanos registram decisões. Toda entidade carrega a hora em que foi gerada; a Terra acrescenta a hora em que recebeu.

```mermaid
erDiagram
  TRIPULANTE ||--o{ LEITURA : gera
  TRIPULANTE ||--o{ CONSENTIMENTO : concede
  TRIPULANTE ||--o{ EVENTO : envolve
  LEITURA }o--o| EVENTO : abre
  EVENTO ||--o{ SUGESTAO : recebe
  EVENTO ||--o{ DECISAO : recebe
  EVENTO ||--o{ PACOTE : vira
  PERFIL_MISSAO ||--o{ PACOTE : define_atraso
  EVENTO ||--o{ REGISTRO_AUDITORIA : registra

  TRIPULANTE {
    string id PK
    string nome
    string papel
    json linha_de_base
  }
  LEITURA {
    string id PK
    string tripulante_id FK
    string metrica
    float valor
    string unidade
    string fonte_sensor
    float qualidade_sinal
    datetime gerada_em
  }
  EVENTO {
    string id PK
    string tipo
    string estado
    int nivel_autonomia
    string papel_responsavel
    datetime prazo_em
    datetime gerado_em
  }
  SUGESTAO {
    string id PK
    string evento_id FK
    string texto
    json evidencias
    float confianca
    string alternativa
    string versao_modelo
  }
  DECISAO {
    string id PK
    string evento_id FK
    string humano_id FK
    string acao
    string dose
    string assinatura
    datetime decidida_em
  }
  CONSENTIMENTO {
    string id PK
    string tripulante_id FK
    string tipo_dado
    string destinatario
    datetime valido_ate
    datetime revogado_em
  }
  PACOTE {
    string id PK
    int prioridade
    string destino
    string estado
    datetime gerado_em
    datetime enviado_em
    datetime confirmado_em
  }
  REGISTRO_AUDITORIA {
    int seq PK
    string entidade
    string de_estado
    string para_estado
    string ator
    datetime quando
    string hash_anterior
    string hash
  }
  PERFIL_MISSAO {
    string id PK
    float atraso_ida_s
    string link
    json janelas_previstas
  }
```

## Regras de escrita

- **Sugestão:** escrita só pela Cosmo; nunca muda o estado do evento.
- **Decisão:** escrita só por humanos, sempre assinada.
- **Registro de auditoria:** só inclusão; cada registro guarda o hash do anterior.

## Contrato `evento.atualizado`

O mesmo formato vai para o tablet pela rede local e para a Terra num pacote DTN. Schema em [contratos/evento-atualizado.schema.json](../contratos/evento-atualizado.schema.json); exemplo em [contratos/exemplos/evento-arritmia.json](../contratos/exemplos/evento-arritmia.json).

## Análise dos modelos

O `ia.py` devolve M1, M2 e M3 no formato de [contratos/exemplos/analise-fa.json](../contratos/exemplos/analise-fa.json). Os números desse arquivo são ilustrativos, até o treino do sábado. Em `m3.metricas`, cada sinal traz o z robusto e a faixa (`padrao`, `atencao`, `critico`). Em `m3.isolation_forest`, `score` é o `-score_samples` depois do `RobustScaler` daquela pessoa: quanto maior, mais a combinação se afasta do padrão dela. `evidencias` lista os sinais cuja troca pela mediana mais reduz esse escore. Quem decide se isso vira sugestão é o motor, pela [ADR-012](../adr/0012-linha-de-base-com-isolation-forest.md).

## Interfaces do protótipo

| Interface | Tipo | Quem publica ou chama | Quem consome |
| --- | --- | --- | --- |
| `tripulante/{id}/leituras` | Tópico MQTT | Relógio, sensores | Ingestão, detectores |
| `eventos/{id}` | Tópico MQTT | Motor de decisões | Relógio, tablet, gateway |
| `POST /decisoes` | REST (FastAPI) | Relógio, tablet (assinado) | Motor de decisões |
| `POST /consentimentos` | REST | Relógio | Motor, gateway |
| `POST /cosmo/chat` | REST | Relógio, tablet, console | Cosmo (nave ou Terra) |
| `GET /familia/feed` | REST, só na Terra | App da família | Filtro de privacidade |
