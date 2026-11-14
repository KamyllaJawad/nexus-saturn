"""Gera a página interativa de arquitetura a partir dos arquivos do repositório.

Uso: python3 ferramentas/gerar_pagina.py  (na raiz da pasta arquitetura)
Saída: pagina/arquitetura.html
"""
import html
import json
import re
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent.parent
DEMO = "https://claude.ai/artifact/CE5bxpHxaLhi8Af9SY7NmU"
DOC = "https://claude.ai/artifact/VAc7XDqgnsWmbqsZRo5kvB"

SECOES = [
    ("01-visao-geral.md", "visao", "Visão geral"),
    ("02-requisitos.md", "requisitos", "Requisitos"),
    ("03-c4.md", "c4", "Arquitetura C4"),
    ("04-implantacao-comunicacao.md", "comunicacao", "Implantação e comunicação"),
    ("05-motor-de-decisoes.md", "decisoes", "Motor de decisões"),
    ("06-fluxos.md", "fluxos", "Fluxos"),
    ("07-modelo-de-dados.md", "dados", "Modelo de dados"),
    ("08-stack.md", "stack", "Stack híbrida"),
    ("09-seguranca-privacidade.md", "seguranca", "Segurança e privacidade"),
    ("10-roadmap-riscos.md", "roadmap", "Roadmap e riscos"),
]
ANCORA_DOC = {f: a for f, a, _ in SECOES}

DEMO_EVENTO = {
    "Emergência cardíaca": "Cenário → Emergência; depois confirme o protocolo no tablet",
    "Tempestade solar": "Injetar evento → Tempestade solar",
    "Sensor solto": "Injetar evento → Sensor solto",
    "Saúde mental com consentimento": "Injetar evento → Queda de humor",
    "Blackout e volta do sinal": "Cenário → Blackout; depois Normal",
}


def slug(txt):
    t = txt.lower()
    for a, b in zip("áàâãéêíóôõúç", "aaaaeeiooouc"):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def ajustar_links(h):
    def troca(m):
        alvo = m.group(1)
        nome = alvo.split("/")[-1]
        if alvo.startswith("http"):
            return f'href="{alvo}" target="_blank" rel="noopener"'
        if "adr/" in alvo and nome.endswith(".md"):
            return f'href="#adr-{nome[:4]}"'
        if nome in ANCORA_DOC:
            return f'href="#{ANCORA_DOC[nome]}"'
        if "contratos" in alvo:
            return 'href="#contrato"'
        return f'href="#{alvo}"'

    return re.sub(r'href="([^"]+)"', troca, h)


def md_para_html(texto, sec):
    texto = re.sub(r"^# .*\n", "", texto, count=1)  # o título vira o cabeçalho da seção
    corpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])

    def mermaid(m):
        codigo = html.unescape(m.group(1))
        return f'<figure class="diagrama"><pre class="mermaid">{html.escape(codigo)}</pre></figure>'

    corpo = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', mermaid, corpo, flags=re.S)
    corpo = corpo.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
    corpo = corpo.replace("[ ]", '<span class="caixa" aria-hidden="true"></span>')

    def h2(m):
        t = m.group(1)
        extra = ""
        if sec == "fluxos" and re.sub("<.*?>", "", t) in DEMO_EVENTO:
            dica = DEMO_EVENTO[re.sub("<.*?>", "", t)]
            extra = f'<p class="na-demo">Na demo: <b>{dica}</b> · <a href="{DEMO}" target="_blank" rel="noopener">abrir a demo</a></p>'
        return f'<h3 id="{sec}-{slug(re.sub("<.*?>", "", t))}">{t}</h3>{extra}'

    corpo = re.sub(r"<h2>(.*?)</h2>", h2, corpo)
    corpo = re.sub(r"<h3>(.*?)</h3>(?!<p class=\"na-demo\")", lambda m: f"<h4>{m.group(1)}</h4>", corpo)
    return ajustar_links(corpo)


def adrs_html():
    itens = []
    for f in sorted((RAIZ / "adr").glob("0*.md")):
        texto = f.read_text()
        titulo = texto.splitlines()[0].lstrip("# ").strip()
        num = f.name[:4]
        corpo = markdown.markdown(re.sub(r"^# .*\n", "", texto, count=1), extensions=["sane_lists"])
        corpo = re.sub(r"<h2>(.*?)</h2>", r"<h4>\1</h4>", corpo)
        corpo = re.sub(r"ADR-(\d{3})", lambda m: f'<a href="#adr-0{m.group(1)}">ADR-{m.group(1)}</a>', corpo)
        itens.append(
            f'<details class="adr" id="adr-{num}"><summary><span class="adr-n">ADR-{num[1:]}</span>'
            f'<span class="adr-t">{html.escape(titulo.split(": ", 1)[-1])}</span></summary><div class="adr-b">{corpo}</div></details>'
        )
    return "\n".join(itens)


def main():
    secoes = []
    nav = []
    for i, (arq, ancora, nome) in enumerate(SECOES, 1):
        corpo = md_para_html((RAIZ / "docs" / arq).read_text(), ancora)
        if ancora == "dados":
            contrato = (RAIZ / "contratos/exemplos/evento-arritmia.json").read_text()
            corpo += (
                '<h3 id="contrato">Exemplo de mensagem <code>evento.atualizado</code></h3>'
                '<div class="codigo"><button class="copiar" type="button" data-alvo="json-contrato">Copiar</button>'
                f'<pre id="json-contrato"><code>{html.escape(contrato)}</code></pre></div>'
            )
        secoes.append(
            f'<section id="{ancora}" class="secao"><p class="sec-n">{i:02d}</p><h2>{nome}</h2>{corpo}</section>'
        )
        nav.append(f'<a href="#{ancora}" data-nav="{ancora}"><span>{i:02d}</span>{nome}</a>')
    secoes.append(
        '<section id="adrs" class="secao"><p class="sec-n">11</p><h2>Decisões de arquitetura</h2>'
        '<p>Doze decisões no formato MADR, todas aceitas. Abra cada uma para ver contexto, alternativas e consequências.</p>'
        f'<div class="adr-ctl"><button type="button" id="abrir-adrs">Abrir todas</button></div>{adrs_html()}</section>'
    )
    nav.append('<a href="#adrs" data-nav="adrs"><span>11</span>Decisões (ADRs)</a>')

    modelo = (RAIZ / "ferramentas/modelo_pagina.html").read_text()
    pagina = (
        modelo.replace("{{NAV}}", "\n".join(nav))
        .replace("{{SECOES}}", "\n".join(secoes))
        .replace("{{DEMO}}", DEMO)
        .replace("{{DOC}}", DOC)
    )
    saida = RAIZ / "pagina/arquitetura.html"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(pagina)
    print(saida, len(pagina) // 1024, "KB", pagina.count('class="mermaid"'), "diagramas")


if __name__ == "__main__":
    main()
