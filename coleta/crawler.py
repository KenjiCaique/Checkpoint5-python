import argparse
import time
from datetime import datetime

import requests
from pymongo.errors import PyMongoError

from banco.conexao import preparar_banco, salvar_livro
from coleta.extracao import extrair_detalhe, extrair_lista

URL_INICIAL = "https://books.toscrape.com/catalogue/page-1.html"
FONTE = "books.toscrape.com"
CABECALHO = {"User-Agent": "Projeto-Faculdade-Crawler (uso educacional)"}
TENTATIVAS = 3


def baixar_pagina(sessao, url):
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = sessao.get(url, timeout=20)
        except requests.exceptions.RequestException:
            print("Erro de conexão em", url, "- tentativa", tentativa, "de", TENTATIVAS)
            time.sleep(1)
            continue

        if resposta.status_code != 200:
            print("O site respondeu com erro", resposta.status_code, "em", url)
            return None

        resposta.encoding = "utf-8"
        return resposta.text

    return None


def coletar(limite_paginas, pausa):
    try:
        preparar_banco()
    except PyMongoError:
        print("Não foi possível conectar ao MongoDB. Confira se o serviço está ligado.")
        return

    sessao = requests.Session()
    sessao.headers.update(CABECALHO)

    novos = 0
    atualizados = 0
    ignorados = 0
    paginas_lidas = 0
    url_lista = URL_INICIAL

    print("Iniciando coleta em", URL_INICIAL)

    while url_lista is not None:
        if limite_paginas > 0 and paginas_lidas >= limite_paginas:
            break

        html_lista = baixar_pagina(sessao, url_lista)
        if html_lista is None:
            print("Não foi possível abrir a listagem. Encerrando.")
            break

        paginas_lidas = paginas_lidas + 1
        links, proxima = extrair_lista(html_lista, url_lista)
        print("Página", paginas_lidas, "-", len(links), "livros encontrados")

        for url_livro in links:
            time.sleep(pausa)

            html_livro = baixar_pagina(sessao, url_livro)
            if html_livro is None:
                ignorados = ignorados + 1
                continue

            livro = extrair_detalhe(html_livro, url_livro)
            if livro is None:
                ignorados = ignorados + 1
                continue

            livro["fonte"] = FONTE
            livro["data_coleta"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if salvar_livro(livro) == "novo":
                novos = novos + 1
            else:
                atualizados = atualizados + 1

        url_lista = proxima

    print("Coleta finalizada!")
    print("Páginas lidas:", paginas_lidas)
    print("Livros novos:", novos)
    print("Livros atualizados:", atualizados)
    print("Registros ignorados:", ignorados)


def ler_argumentos():
    leitor = argparse.ArgumentParser(description="Coleta livros de books.toscrape.com")
    leitor.add_argument(
        "--paginas",
        type=int,
        default=0,
        help="quantidade de páginas da listagem a coletar (0 = todas)",
    )
    leitor.add_argument(
        "--pausa",
        type=float,
        default=0.2,
        help="segundos de espera entre as requisições",
    )
    return leitor.parse_args()


if __name__ == "__main__":
    argumentos = ler_argumentos()
    coletar(argumentos.paginas, argumentos.pausa)
