# ADR-014 · Cobrir os 17 riscos do NASA Human Research Program

Status: aceita em 2026-11-14

## Contexto

O NASA Human Research Program (HRP) organiza o voo em 5 perigos (radiação, isolamento e confinamento, distância da Terra, campos de gravidade e ambiente hostil e fechado) e lista 17 riscos de saúde em 3 categorias. A NASA alerta que os perigos se alimentam uns dos outros. A demo cobria 7 riscos inteiros, 4 em parte e deixava 6 de fora.

Fontes: https://www.nasa.gov/hrp/hazards/ · https://www.nasa.gov/hrp/risks/ · https://www.nasa.gov/hrp/ongoing-hrp-research/

## Decisão

Oito acréscimos na demo, todos com o mesmo princípio: a IA recomenda e o médico decide, a bordo ou na Terra (ADR-013).

| # | Acréscimo | Riscos do HRP |
|---|---|---|
| 1 | Evento **Volta à gravidade**: soro oral e cinto antes da reentrada, acelerações do assento + relato, pergunta sobre tontura e enjoo, teste em pé de 3 min, soro na veia com o médico. Muda com a missão: Terra (1 g), Lua (0,16 g), Marte (0,38 g) | Sensório-motor e vestibular, cargas dinâmicas, cardiovascular |
| 2 | **Ciclo da EVA**: escala pela comandante, pré-respiração com O₂ puro, SpO₂ e fadiga durante a EVA, dor articular depois e recompressão com o médico | Doença descompressiva, hipóxia, lesão na EVA |
| 3 | **Mapa dos 17 riscos** e dos 5 perigos na visão Dados e IA, com o que cobre cada risco e a situação | Todos |
| 4 | **Luz forte** depois das 18h no relógio e no JSON (`luz_lux`), como o actígrafo de pulso do Artemis II | Sono |
| 5 | Evento **Imunidade**: temperatura acima da linha de base já corrigida pelo ciclo (M3 + M4), pergunta sobre feridas, saliva do kit, antiviral com o médico | Resposta imune |
| 6 | Tela **Nutrição**: calorias, proteína, "comida enjoando?" e colheita da estufa | Nutrição; isolamento (estufa) |
| 7 | **Contramedidas da SANS**: depois do ultrassom, faixas nas coxas sugeridas ao médico; vitamina B citada como "em estudo", nunca sugerida pela Cosmo | SANS |
| 8 | **Riscos que se somam**: com 3 fatores ao mesmo tempo (distância, sono, hidratação, nutrição, CO₂, radiação, humor, imunidade), a Cosmo sobe a prioridade | Todos os perigos |

Uma fila genérica de decisões médicas (`dq`) leva cada pedido ao Dr. Marcus no painel de bordo ou, sem médico a bordo, à Dra. Rivera no console de Houston, com o atraso da missão nos dois sentidos.

## Resultado

13 riscos cobertos, 2 parciais (microrganismos e câncer por radiação) e 2 como próximos passos (trabalho em equipe e apoio a sistemas). Ver `../proximos-passos.md`.

## Consequências

- O roteiro passa de 16 para 19 passos.
- Novos tipos de evento no back-end: `volta_gravidade`, `imunidade`, `eva` com 4 fases, e a fila `decisoes_medicas`.
- Pessoa 2 copia a tela Nutrição e os cards novos; Pessoa 3 implementa a fila de decisões com `medico_local`.
