# 9-frontend · telas

HTML, CSS e JavaScript puro, sem build. Cada página busca a API a cada 1 s e mostra só o que aquela superfície pode ver; o filtro é feito no servidor.

Suba a API em `8-backend` (ela serve esta pasta) e abra <http://127.0.0.1:8000/>.

| Página | Quem usa | O que vê |
| --- | --- | --- |
| `index.html` | Quem apresenta | Sala de simulação: injeta cenários e mostra as quatro telas lado a lado. |
| `relogio/` | Quem está com o pulso (troque a pessoa no topo) | Os próprios sinais, as perguntas que só ela responde, Cosmo, estufa, Elo e sincronia. |
| `bordo/` | Dr. Marcus, ou o Marcus como CMO sem médico a bordo | Tripulação, ECG, saída dos modelos, decisões, só os avisos que alguém compartilhou, o chat da Cosmo de bordo e a trilha da Cosmo (tokens, latência, custo, decisão e passos). Sem médico a bordo: o botão das ações seguras, o de aplicar a dose que chegou da Terra e, sem sinal, a ordem permanente com os critérios marcados. |
| `houston/` | Flight surgeon, ou a Dra. Rivera sem médico a bordo | O retrato atrasado, o que já chegou, o parecer, o chat da Cosmo Terra e a trilha da Cosmo (a da Terra e a das sugestões de bordo que chegaram). Com médico a bordo, sem botão de protocolo ou medicação. Sem médico a bordo: confirmar protocolo, aprovar ultrassom, liberar medicação, a ordem permanente em vigor e o quadro "Compartilhado só com você". |
| `familia/` | Família | Frases, com o atraso. Nunca número, diagnóstico, humor ou ciclo. |
| `dados-ia/` | Banca e time | Lakehouse, métricas medidas, human-in-the-loop dos modelos e auditoria. |

O relógio aceita `?quem=kenji` na URL, para abrir um pulso por aba.
