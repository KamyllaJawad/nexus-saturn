# 7. Modelo de dados e contratos

O centro do modelo é o Evento: leituras abrem eventos, a Cosmo anexa sugestões e só humanos registram decisões. Toda entidade carrega a hora em que foi gerada; a Terra acrescenta a hora em que recebeu.

```mermaid
erDiagram
  TRIPULANTE ||--o{ DISPOSITIVO : porta
  TRIPULANTE ||--o| FICHA : embarca
  DISPOSITIVO ||--o{ LEITURA : mede
  TRIPULANTE ||--o{ LEITURA : gera
  TRIPULANTE ||--o{ CONSENTIMENTO : concede
  TRIPULANTE ||--o{ EVENTO : envolve
  LEITURA }o--o| EVENTO : abre
  LOTE ||--o{ MODELO : produz
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
  DISPOSITIVO {
    string id PK
    string classe
    string tripulante_id FK
    string grandeza
  }
  FICHA {
    string tripulante_id PK
    bool calendario
    string metodo
    date ultima_menstruacao
  }
  LEITURA {
    string id PK
    string tripulante_id FK
    string dispositivo_id FK
    string canal
    float valor
    string unidade
    float qualidade_sinal
    datetime gerada_em
    datetime recebida_em
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
  LOTE {
    string id PK
    string zona
    string origem
  }
  MODELO {
    string versao PK
    string peca
    string lote_id FK
    string artefato
  }
```

`DISPOSITIVO.classe` é `relogio`, `patch`, `kit`, `cabine` ou `registro`. O CO₂ da cabine não tem tripulante: `tripulante_id` fica vazio e a leitura continua válida. A dose do dosímetro é da pessoa. A ficha de solo não é uma leitura. Estresse não é sensor: sai na zona prata, a partir de HRV e sono. O caminho dessas leituras até o lakehouse, o tratamento e o treino estão em [11-dados-lakehouse.md](11-dados-lakehouse.md).

## Ingestão e saída

A leitura entra pelo tópico MQTT. A ingestão grava fonte, hora e qualidade, e o `ia.py` devolve a análise. O z robusto pinta o estado no relógio e no painel. O motor escolhe o restante da saída. A Cosmo só lê esse estado e anexa a sugestão. O humano devolve a decisão assinada.

```mermaid
flowchart TB
  subgraph entrada[Entrada]
    src[Relógio, sensores de bordo e cabine]
    lei["MQTT tripulante/{id}/leituras"]
    ing["Ingestão<br/>fonte, hora e qualidade"]
  end

  subgraph analise[Análise]
    ia["ia.analisar(leitura)"]
    z[Z robusto por sinal]
    det["M1 arritmia · M2 qualidade<br/>Isolation Forest · calendário"]
  end

  subgraph decisao[Decisão a bordo]
    motor[Motor de decisões]
    cosmo[Cosmo]
    humano["POST /decisoes assinado"]
  end

  subgraph saida[Saída]
    painel["Estado de três níveis<br/>relógio e painel"]
    evento[Evento clínico]
    n1["Sugestão nível 1<br/>sem abrir evento"]
    aviso["Aviso no relógio<br/>dessa pessoa"]
    msg["evento.atualizado<br/>MQTT eventos/{id}"]
    local["Rede local<br/>relógio, tablet e gateway"]
    dtn[Pacote DTN]
    terra["Terra<br/>filtro de privacidade"]
    houston[Console de Houston]
    familia["App da família<br/>só frases"]
    audit[(Auditoria)]
  end

  src --> lei --> ing --> ia
  ia --> z
  ia --> det
  z --> motor
  det --> motor
  motor -->|"estado, só leitura"| cosmo
  cosmo -->|anexa sugestão| motor
  humano --> motor
  z --> painel
  motor -->|FA ou sinal crítico| evento
  motor -->|"anomalia, sinal bom<br/>e nenhum sinal crítico"| n1
  motor -->|calendário na ficha| aviso
  evento --> msg
  msg --> local
  msg --> dtn --> terra
  terra --> houston
  terra --> familia
  motor --> audit
```

A sugestão de nível 1 sai quando o Isolation Forest marca anomalia, o M2 diz que o sinal é bom e nenhum sinal está crítico sozinho. Se o M1 já abriu fibrilação atrial, ou se um sinal está crítico, permanece o evento aberto, no contrato `evento.atualizado`. Com calendário na ficha, o aviso do trecho intenso fica no relógio dessa pessoa. A Terra recebe o pacote DTN e aplica o filtro: Houston vê o necessário para o parecer, e a família recebe frases prontas, sem escore, faixa ou ciclo. No relógio, com o servidor fora, seguem a ingestão, o detector de arritmia, o de artefato e a fila local.

## Regras de escrita

- **Sugestão:** escrita só pela Cosmo; nunca muda o estado do evento.
- **Decisão:** escrita só por humanos, sempre assinada.
- **Registro de auditoria:** só inclusão; cada registro guarda o hash do anterior.

## Contrato `evento.atualizado`

O mesmo formato vai para o tablet pela rede local e para a Terra num pacote DTN. Schema em [contratos/evento-atualizado.schema.json](../contratos/evento-atualizado.schema.json); exemplo em [contratos/exemplos/evento-arritmia.json](../contratos/exemplos/evento-arritmia.json).

## Análise dos modelos

O `ia.py` devolve M1, M2 e M3 no formato de [contratos/exemplos/analise-fa.json](../contratos/exemplos/analise-fa.json). Os números desse arquivo são ilustrativos, até o treino do sábado. Em `m3.metricas`, cada sinal traz o z robusto e a faixa (`padrao`, `atencao`, `critico`). Em `m3.isolation_forest`, `score` é o `-score_samples` depois do `RobustScaler` daquela pessoa: quanto maior, mais a combinação se afasta do padrão dela. `evidencias` lista os sinais cuja troca pela mediana mais reduz esse escore. Quem decide se isso vira sugestão é o motor, pela [ADR-012](../adr/0012-linha-de-base-com-isolation-forest.md).

O calendário do ciclo sai no formato de [contratos/exemplos/analise-ciclo.json](../contratos/exemplos/analise-ciclo.json). Os números também são ilustrativos. `ficha.calendario` diz se a Cosmo pode falar de ciclo. `ciclo.na_janela` e `ciclo.aviso_dias` vêm dessa ficha. `ciclo.perguntar` só fica verdadeiro quando a janela coincide com sinais leves e o M2 diz que o sinal é bom. `ciclo.compartilhado` começa falso: médico e Houston só entram depois do consentimento. A família não está nesse contrato.

Quem não tem calendário sai no formato de [contratos/exemplos/analise-kenji.json](../contratos/exemplos/analise-kenji.json). `ciclo` fica nulo e a sugestão usa a linha de base pessoal. A regra dos dois caminhos está na [ADR-013](../adr/0013-calendario-do-ciclo.md).

## Interfaces do protótipo

| Interface | Tipo | Quem publica ou chama | Quem consome |
| --- | --- | --- | --- |
| `tripulante/{id}/leituras` | Tópico MQTT | Relógio, sensores | Ingestão, detectores |
| `eventos/{id}` | Tópico MQTT | Motor de decisões | Relógio, tablet, gateway |
| `POST /decisoes` | REST (FastAPI) | Relógio, tablet (assinado) | Motor de decisões |
| `POST /consentimentos` | REST | Relógio | Motor, gateway |
| `POST /cosmo/chat` | REST | Relógio, tablet, console | Cosmo (nave ou Terra) |
| `GET /familia/feed` | REST, só na Terra | App da família | Filtro de privacidade |
