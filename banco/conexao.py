import os

from pymongo import MongoClient

URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

cliente = MongoClient(URI)
banco = cliente["livros_db"]
colecao = banco["livros"]


def preparar_banco():
    colecao.create_index("upc", unique=True)


def salvar_livro(livro):
    resultado = colecao.update_one(
        {"upc": livro["upc"]},
        {
            "$set": livro,
            "$setOnInsert": {"primeira_coleta": livro["data_coleta"]},
        },
        upsert=True,
    )

    if resultado.upserted_id is not None:
        return "novo"
    return "atualizado"
