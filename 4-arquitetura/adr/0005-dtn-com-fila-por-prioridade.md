# ADR-005: DTN com Bundle Protocol e fila por prioridade

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-006, ADR-011

## Contexto

Protocolos comuns da internet assumem conexão contínua e atrasos de milissegundos. Entre a nave e a Terra há minutos de atraso e quedas de dias.

## Decisão

A comunicação nave ⇄ Terra usa DTN (Bundle Protocol), com custódia, reenvio e quatro classes de prioridade: P1 alertas, SOS e decisões médicas; P2 telemetria e exames; P3 mensagens e escala; P4 rotina e gamificação. P1 tem banda reservada e nunca é descartado.

## Alternativas consideradas

- **TCP/IP direto:** Quebra com atrasos longos e quedas.
- **MQTT ponta a ponta:** Ótimo na rede local, mas não foi feito para minutos de atraso e blackouts.

## Consequências

**Positivas**

- Nada se perde no blackout; alertas chegam primeiro.
- Alinhado ao que a NASA já usa (ION).

**Negativas**

- No hackathon, o DTN é simulado em Python.
