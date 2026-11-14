# 6. Fluxos principais

Nos cinco fluxos, a decisão acontece a bordo, e a Terra fica sabendo depois. Setas `--)` cruzam o link com a Terra e levam de menos de 1 s a 22 min, conforme o perfil de missão.

## Emergência cardíaca

```mermaid
sequenceDiagram
  autonumber
  participant R as Relógio (Sarah)
  participant M as Motor + Cosmo (nave)
  participant T as Tablet (Dr. Marcus)
  participant G as Gateway DTN
  participant H as Houston
  R->>R: detecta FC 168 irregular e SpO₂ 88%
  R->>R: alerta no pulso: pare e sente-se
  R->>M: evento arritmia + ECG
  M->>T: protocolo + evidências (nível 3)
  M->>G: alerta P1
  T->>M: confirma protocolo (assinado)
  M->>R: médico a caminho
  T->>M: libera antiarrítmico e define a dose
  G--)H: alerta chega com atraso
  H--)G: parecer
  G->>T: parecer chega a bordo
```

## Tempestade solar

```mermaid
sequenceDiagram
  autonumber
  participant D as Dosímetro
  participant M as Motor + Cosmo
  participant C as Relógio da comandante
  participant T as Tablet
  participant G as Gateway DTN
  participant E as Houston e família
  D->>M: fluxo de prótons subindo
  M->>M: nível 4: acende a rota até o abrigo
  M->>C: abrigo para todos?
  opt comandante adia 5 min
    C->>M: aguardar
    M->>C: fluxo ainda subindo, pergunta de novo
  end
  C->>M: abrigo para todos
  M->>T: dose de cada tripulante
  M->>G: alerta P1: tripulação no abrigo
  G--)E: chega minutos depois
  D->>M: fluxo caindo
  M->>C: liberar a tripulação?
  C->>M: libera
```

## Sensor solto

```mermaid
sequenceDiagram
  autonumber
  participant S as Oxímetro do relógio
  participant R as Cosmo borda
  participant A as Astronauta
  participant T as Tablet (médico)
  S->>R: SpO₂ 84% com sinal fraco
  R->>A: o relógio está folgado?
  alt ajustou
    A->>R: ajustei
    R->>R: leitura volta a 98% e o trecho vira artefato
  else está firme ou 20 s sem resposta
    R->>T: leitura suspeita
    T->>R: oxímetro do kit marca 97%
  end
```

## Saúde mental com consentimento

```mermaid
sequenceDiagram
  autonumber
  participant C as Cosmo (relógio)
  participant A as Astronauta
  participant T as Tablet (médico)
  participant F as Família
  C->>C: sono, voz e HRV indicam queda de humor
  C->>A: só você vê isto. Quer conversar?
  opt pede chamada com a família
    A->>C: pedir chamada
    C--)F: pedido de chamada (P3)
  end
  alt compartilhar
    A->>C: contar ao Dr. Marcus
    C->>T: resumo, sem gravações
    T->>A: conversa marcada às 19:00
  else só comigo
    A->>C: só comigo
    Note over C: nada sai do relógio
  end
```

## Blackout e volta do sinal

```mermaid
sequenceDiagram
  autonumber
  participant N as Nave (motor)
  participant G as Fila DTN
  participant T as Terra
  Note over N,T: link cai (conjunção solar)
  N->>G: P2 telemetria (guardada)
  N->>G: P1 alerta (guardado)
  T->>T: mensagens da Terra esperam do lado da Terra
  Note over N,T: janela de contato abre
  G--)T: P1 primeiro
  G--)T: depois P2, P3 e P4
  T--)G: confirma cada pacote
  T->>T: copiloto de Houston resume o período
```
