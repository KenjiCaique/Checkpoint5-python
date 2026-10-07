import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

NOTAS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def limpar(valor):
    if valor is None:
        return ""
    return " ".join(str(valor).split())


def converter_preco(texto):
    achados = re.findall(r"\d+\.\d+|\d+", texto)
    if len(achados) == 0:
        return 0.0
    return float(achados[0])


def extrair_lista(html, url_pagina):
    sopa = BeautifulSoup(html, "html.parser")

    links = []
    for artigo in sopa.select("article.product_pod"):
        link = artigo.select_one("h3 a")
        if link is None or not link.get("href"):
            continue
        links.append(urljoin(url_pagina, link["href"]))

    proxima = None
    botao = sopa.select_one("li.next a")
    if botao is not None and botao.get("href"):
        proxima = urljoin(url_pagina, botao["href"])

    return links, proxima


def extrair_detalhe(html, url_livro):
    sopa = BeautifulSoup(html, "html.parser")

    titulo_tag = sopa.select_one("div.product_main h1")
    if titulo_tag is None:
        return None
    titulo = limpar(titulo_tag.get_text())

    tabela = {}
    for linha in sopa.select("table.table-striped tr"):
        cabecalho = linha.find("th")
        valor = linha.find("td")
        if cabecalho is not None and valor is not None:
            tabela[limpar(cabecalho.get_text())] = limpar(valor.get_text())

    upc = tabela.get("UPC", "")
    if titulo == "" or upc == "":
        return None

    migalhas = sopa.select("ul.breadcrumb li")
    categoria = ""
    if len(migalhas) >= 3:
        categoria = limpar(migalhas[2].get_text())

    avaliacao = 0
    tag_nota = sopa.select_one("div.product_main p.star-rating")
    if tag_nota is not None:
        for classe in tag_nota.get("class", []):
            if classe in NOTAS:
                avaliacao = NOTAS[classe]

    descricao = ""
    bloco_descricao = sopa.select_one("#product_description")
    if bloco_descricao is not None:
        paragrafo = bloco_descricao.find_next_sibling("p")
        if paragrafo is not None:
            descricao = limpar(paragrafo.get_text())

    estoque = 0
    achado = re.search(r"\d+", tabela.get("Availability", ""))
    if achado is not None:
        estoque = int(achado.group())

    return {
        "upc": upc,
        "titulo": titulo,
        "categoria": categoria,
        "preco": converter_preco(tabela.get("Price (incl. tax)", "")),
        "avaliacao": avaliacao,
        "estoque": estoque,
        "em_estoque": estoque > 0,
        "descricao": descricao,
        "url_livro": url_livro,
    }
