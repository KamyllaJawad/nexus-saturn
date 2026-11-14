# ADR-009: Com sinal ruim, perguntar ao astronauta antes de alarmar

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-004

## Contexto

Sensores de pulso erram quando o relógio está folgado. Alarmes falsos cansam a equipe médica, e alarmes descartados em silêncio escondem eventos reais.

## Decisão

Quando a qualidade do sinal é baixa, a Cosmo pergunta ao astronauta se o relógio está folgado. Se ele ajusta e a leitura volta, o trecho vira artefato. Se ele confirma, ou não responde em 20 s, o caso vai ao oficial médico.

## Alternativas consideradas

- **Alarmar sempre:** Seguro no papel, mas gera fadiga de alarme.
- **Descartar leituras ruins em silêncio:** Sem ruído, mas pode esconder um evento real.

## Consequências

**Positivas**

- Menos alarmes falsos sem esconder eventos reais.

**Negativas**

- Exige um bom estimador de qualidade de sinal.
