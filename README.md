# Projeto: Web Crawler, API e Dashboard de Livros

Fluxo do sistema: **Site → Web Crawler → MongoDB → FastAPI → Dashboard**

## 1. Site escolhido e dados coletados

**Site:** [Books to Scrape](https://books.toscrape.com), uma livraria fictícia criada para praticar web scraping. O catálogo tem 1000 livros em 50 páginas e 50 categorias. Os preços, avaliações e estoques são fictícios.

**Por que esse site:** ele foi feito para ser coletado, então o uso educacional é permitido, e não há dados pessoais nem conteúdo privado.

**Como o crawler funciona:** ele lê o **HTML** das páginas (com `requests` e `BeautifulSoup`). Primeiro abre a listagem e pega o link de cada livro; depois abre a página de cada livro e extrai os dados; por fim segue o botão "next" até a última página. Faz uma pausa entre as requisições para não sobrecarregar o site.

**O que é coletado de cada livro:** título, categoria, preço (em libras), avaliação (1 a 5 estrelas), quantidade em estoque, descrição, UPC (código único do produto) e link da página.

## 2. Estrutura do projeto

```
projeto_livros/
├── coleta/
│   ├── crawler.py        # COLETA: percorre as páginas e controla o fluxo
│   └── extracao.py       # COLETA: lê o HTML e extrai os campos
├── banco/
│   └── conexao.py        # PERSISTÊNCIA: conexão e gravação no MongoDB
├── api/
│   └── app.py            # API: FastAPI que lê o MongoDB
├── dashboard/            # INTERFACE: só consome a API
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
├── README.md
└── EXPLICACAO.md         # explicação didática para a apresentação
```

## 3. Como instalar e executar

Todos os comandos são executados **dentro da pasta `projeto_livros`**.

1. Instale o Python 3.10+ e o **MongoDB Community** (deixe o serviço rodando em `localhost:27017`).
2. Instale as bibliotecas:
   ```
   pip install -r requirements.txt
   ```
3. Rode o crawler:
   ```
   python -m coleta.crawler
   ```
   A coleta completa (1000 livros) leva alguns minutos. Para uma demonstração rápida, limite as páginas (cada página tem 20 livros):
   ```
   python -m coleta.crawler --paginas 3
   ```
   Opção `--pausa` muda a espera entre requisições (padrão: 0.2 segundo).
4. Ligue a API:
   ```
   python -m uvicorn api.app:app --reload
   ```
5. Abra no navegador:
   - Dashboard: http://127.0.0.1:8000/dashboard/
   - Documentação automática da API: http://127.0.0.1:8000/docs

Se o MongoDB não estiver em `localhost:27017`, defina a variável de ambiente `MONGO_URI` com o endereço correto.

> O dashboard carrega os gráficos (Chart.js) e a fonte pela internet, então o computador precisa estar online.

Você pode rodar o crawler de novo quando quiser: os livros já existentes são **atualizados**, não duplicados, e nada é apagado.

## 4. Estrutura do banco de dados

- Banco: `livros_db`
- Coleção: `livros`
- Índice único no campo `upc`, que garante que o mesmo livro não seja gravado duas vezes.

Exemplo de documento:

```json
{
  "upc": "a897fe39b1053632",
  "titulo": "A Light in the Attic",
  "categoria": "Poetry",
  "preco": 51.77,
  "avaliacao": 3,
  "estoque": 22,
  "em_estoque": true,
  "descricao": "It's hard to imagine a world without A Light in the Attic...",
  "url_livro": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "fonte": "books.toscrape.com",
  "data_coleta": "2026-10-07 14:30:00",
  "primeira_coleta": "2026-10-07 14:30:00"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| upc | texto | Código único do livro no site (usado para evitar duplicados) |
| titulo | texto | Título do livro |
| categoria | texto | Categoria (Poetry, Travel, Mystery...) |
| preco | número | Preço em libras (£) |
| avaliacao | número | Nota de 1 a 5 estrelas |
| estoque | número | Quantidade disponível |
| em_estoque | booleano | `true` se há pelo menos uma unidade |
| descricao | texto | Descrição do livro (pode ficar vazia) |
| url_livro | texto | Página do livro no site |
| fonte | texto | De qual site veio o dado |
| data_coleta | texto | Data e hora da coleta mais recente |
| primeira_coleta | texto | Data e hora da primeira vez que o livro foi coletado |

## 5. Endpoints da API

| Método | Endereço | O que faz |
|---|---|---|
| GET | `/` | Mensagem de boas-vindas |
| GET | `/livros` | Lista livros com filtros, ordenação e paginação |
| GET | `/livros/{upc}` | Retorna um livro específico (404 se não existir) |
| GET | `/categorias` | Lista as categorias (para o filtro) |
| GET | `/estatisticas` | Total, preço médio, avaliação média, % em estoque, categoria mais comum, livros mais caro e mais barato, última coleta |
| GET | `/graficos/por-categoria` | Quantidade de livros por categoria (gráfico 1) |
| GET | `/graficos/por-avaliacao` | Quantidade de livros por nota (gráfico 2) |
| GET | `/graficos/por-faixa-preco` | Quantidade de livros por faixa de preço (gráfico 3) |

Parâmetros opcionais de `/livros`: `busca` (parte do título), `categoria`, `avaliacao_minima` (0 a 5), `preco_maximo`, `ordenar` (`titulo`, `preco_menor`, `preco_maior` ou `avaliacao`), `pagina` e `limite` (1 a 100).

Exemplo: `http://127.0.0.1:8000/livros?busca=love&categoria=Poetry&avaliacao_minima=3&ordenar=preco_menor`

