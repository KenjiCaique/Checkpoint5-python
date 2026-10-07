import math
import re
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from banco.conexao import colecao

app = FastAPI(title="API de Livros")

ORDENACOES = {
    "titulo": ("titulo", 1),
    "preco_menor": ("preco", 1),
    "preco_maior": ("preco", -1),
    "avaliacao": ("avaliacao", -1),
}


def contar_por(campo):
    pipeline = [
        {"$match": {campo: {"$nin": ["", 0, None]}}},
        {"$group": {"_id": "$" + campo, "quantidade": {"$sum": 1}}},
        {"$sort": {"quantidade": -1, "_id": 1}},
    ]

    resultado = []
    for item in colecao.aggregate(pipeline):
        resultado.append({"nome": item["_id"], "quantidade": item["quantidade"]})
    return resultado


@app.get("/")
def inicio():
    return {
        "mensagem": "API de Livros funcionando",
        "documentacao": "/docs",
        "dashboard": "/dashboard/",
    }


@app.get("/livros")
def listar_livros(
    busca: str = "",
    categoria: str = "",
    avaliacao_minima: int = Query(0, ge=0, le=5),
    preco_maximo: float = Query(0, ge=0),
    ordenar: Literal["titulo", "preco_menor", "preco_maior", "avaliacao"] = "titulo",
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
):
    filtro = {}

    if busca != "":
        filtro["titulo"] = {"$regex": re.escape(busca), "$options": "i"}

    if categoria != "":
        filtro["categoria"] = categoria

    if avaliacao_minima > 0:
        filtro["avaliacao"] = {"$gte": avaliacao_minima}

    if preco_maximo > 0:
        filtro["preco"] = {"$lte": preco_maximo}

    total = colecao.count_documents(filtro)

    campo, direcao = ORDENACOES[ordenar]
    ordem = [(campo, direcao)]
    if campo != "titulo":
        ordem.append(("titulo", 1))

    pular = (pagina - 1) * limite
    cursor = colecao.find(filtro, {"_id": 0}).sort(ordem).skip(pular).limit(limite)

    return {
        "total": total,
        "pagina": pagina,
        "total_paginas": math.ceil(total / limite),
        "livros": list(cursor),
    }


@app.get("/livros/{upc}")
def buscar_livro(upc: str):
    livro = colecao.find_one({"upc": upc}, {"_id": 0})

    if livro is None:
        raise HTTPException(status_code=404, detail="Livro não encontrado")

    return livro


@app.get("/categorias")
def listar_categorias():
    categorias = []
    for nome in colecao.distinct("categoria"):
        if nome != "":
            categorias.append(nome)

    categorias.sort()
    return categorias


@app.get("/estatisticas")
def estatisticas():
    total = colecao.count_documents({})

    if total == 0:
        return {"total": 0}

    pipeline = [
        {
            "$group": {
                "_id": None,
                "preco_medio": {"$avg": "$preco"},
                "avaliacao_media": {"$avg": "$avaliacao"},
                "em_estoque": {"$sum": {"$cond": ["$em_estoque", 1, 0]}},
                "ultima_coleta": {"$max": "$data_coleta"},
            }
        }
    ]
    resumo = list(colecao.aggregate(pipeline))[0]

    campos = {"_id": 0, "titulo": 1, "preco": 1}
    mais_caro = colecao.find_one({}, campos, sort=[("preco", -1)])
    mais_barato = colecao.find_one({}, campos, sort=[("preco", 1)])

    por_categoria = contar_por("categoria")

    return {
        "total": total,
        "total_categorias": len(por_categoria),
        "categoria_mais_comum": por_categoria[0] if por_categoria else None,
        "preco_medio": round(resumo["preco_medio"], 2),
        "avaliacao_media": round(resumo["avaliacao_media"], 2),
        "percentual_em_estoque": round(resumo["em_estoque"] / total * 100, 1),
        "livro_mais_caro": mais_caro,
        "livro_mais_barato": mais_barato,
        "ultima_coleta": resumo["ultima_coleta"],
    }


@app.get("/graficos/por-categoria")
def grafico_por_categoria():
    return contar_por("categoria")


@app.get("/graficos/por-avaliacao")
def grafico_por_avaliacao():
    resultado = contar_por("avaliacao")
    resultado.sort(key=lambda item: item["nome"])
    return resultado


@app.get("/graficos/por-faixa-preco")
def grafico_por_faixa_preco():
    pipeline = [
        {
            "$group": {
                "_id": {"$floor": {"$divide": ["$preco", 10]}},
                "quantidade": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    resultado = []
    for item in colecao.aggregate(pipeline):
        inicio_faixa = int(item["_id"]) * 10
        nome = "£" + str(inicio_faixa) + " a £" + str(inicio_faixa + 9)
        resultado.append({"nome": nome, "quantidade": item["quantidade"]})
    return resultado


app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")
