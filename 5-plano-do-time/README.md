# Plano do time · issues

Plano para 3 pessoas, sábado 14/11 e domingo 15/11, com entrega no domingo às 15h.

- `issues-astrohealth.csv`: as 25 tarefas do MVP, cada uma com critério de pronto, uma dica de por onde começar, dependências, prazo, marco e labels.
  - Pessoa 1: dados e IA (8 tarefas, 19 h).
  - Pessoa 2: telas do relógio, do painel de bordo, do celular da família e de Houston, copiadas da demo original (6 tarefas, 19 h).
  - Pessoa 3: back-end em FastAPI + SQLite (9 tarefas, 17 h).
  - Todas: ensaio e vídeo (2 tarefas, 3 h).
- `simulado-no-mvp.csv`: as 2 partes que ficam só simuladas na demo, sem dado real (copiloto de Houston e buffer offline do relógio).
- `../1-demo-mvp/astrohealth-demo.html`: a demo original, base do MVP. Cada tela é uma função (`watchHTML`, `tabletHTML`, `phoneHTML`, `desktopHTML`) que a Pessoa 2 copia.
- `criar_issues_github.sh`: cria labels, marcos e as issues num repositório do GitHub.

## Stack do MVP (simplificada)

- Telas: HTML, CSS e JavaScript puro, copiando as funções de cada tela da demo original (`astrohealth-demo.html`). Sem framework e sem build.
- Back-end: Python com FastAPI e SQLite. As telas buscam os dados a cada 1 s.
- IA: um módulo `ia.py` que o back-end importa. O M3 leva o z robusto por sinal e um Isolation Forest por tripulante. A Cosmo usa Ollama e ChromaDB.

## GitHub

```bash
gh auth login                       # uma vez
./criar_issues_github.sh minha-org/astrohealth
```

Depois, adicione as issues a um GitHub Project e atribua as pessoas. O script não atribui ninguém, porque o plano usa "Pessoa 1, 2 e 3" no lugar dos nomes.

## Jira

Em **Configurações do sistema → Importação externa → CSV**, mapeie: `Titulo` → Resumo, `Descricao` → Descrição, `Prazo` → Data limite, `Estimativa (h)` → Estimativa original, `Labels` → Rótulos (separador `;`).

