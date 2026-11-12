# ADR-001: IA na borda primeiro; a Terra só apoia

- **Status:** aceita
- **Data:** 2026-11-11
- **Relacionadas:** ADR-005, ADR-010

## Contexto

A caminho de Marte, cada mensagem leva de 3 a 22 min por trecho, e conjunções solares cortam o contato por dias. Uma arritmia ou uma tempestade solar exigem resposta em segundos.

## Decisão

Toda detecção e toda decisão que protege a vida rodam a bordo: o relógio detecta e alerta sozinho; o servidor da nave abre o evento e chama o humano responsável. A Terra recebe, revisa e devolve pareceres.

## Alternativas consideradas

- **Processar tudo na Terra:** Simples e com modelos maiores, mas inútil com minutos de atraso e blackouts.
- **Processar tudo no servidor da nave:** Bom para modelos médios, mas o relógio ficaria sem alerta se o servidor ou a rede local caíssem.

## Consequências

**Positivas**

- Alerta crítico em menos de 1 s, mesmo sem rede local.
- A tripulação continua protegida durante blackouts.

**Negativas**

- Modelos a bordo são menores e precisam de validação cuidadosa.
- Mais software para manter em vários nós.
