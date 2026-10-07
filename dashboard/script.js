const API = "";
const LIMITE = 20;

let paginaAtual = 1;


async function buscarJson(endereco) {
  const resposta = await fetch(API + endereco);
  if (!resposta.ok) {
    throw new Error("Erro " + resposta.status + " em " + endereco);
  }
  return await resposta.json();
}

function mostrarAviso(texto) {
  const aviso = document.getElementById("aviso");
  aviso.textContent = texto;
  aviso.hidden = false;
}

function formatarPreco(valor) {
  return "£" + valor.toFixed(2);
}

function montarEstrelas(nota) {
  return "★".repeat(nota) + "☆".repeat(5 - nota);
}

function separarLista(lista) {
  const nomes = [];
  const quantidades = [];

  for (let i = 0; i < lista.length; i++) {
    nomes.push(lista[i].nome);
    quantidades.push(lista[i].quantidade);
  }

  return { nomes: nomes, quantidades: quantidades };
}


async function carregarEstatisticas() {
  const dados = await buscarJson("/estatisticas");

  document.getElementById("total").textContent = dados.total;

  if (dados.total === 0) {
    mostrarAviso("Ainda não há livros no banco. Execute o crawler e recarregue a página.");
    return;
  }

  document.getElementById("preco-medio").textContent = formatarPreco(dados.preco_medio);
  document.getElementById("avaliacao-media").textContent = dados.avaliacao_media.toFixed(2) + " de 5";
  document.getElementById("em-estoque").textContent = dados.percentual_em_estoque + "%";
  document.getElementById("categoria-top").textContent =
    dados.categoria_mais_comum.nome + " (" + dados.categoria_mais_comum.quantidade + " livros)";
  document.getElementById("mais-caro").textContent =
    dados.livro_mais_caro.titulo + " (" + formatarPreco(dados.livro_mais_caro.preco) + ")";
  document.getElementById("ultima-coleta").textContent = dados.ultima_coleta;
}


async function desenharGraficoCategorias() {
  const lista = await buscarJson("/graficos/por-categoria");
  const dados = separarLista(lista.slice(0, 10));

  new Chart(document.getElementById("grafico-categorias"), {
    type: "bar",
    data: {
      labels: dados.nomes,
      datasets: [{
        label: "Livros",
        data: dados.quantidades,
        backgroundColor: "#14213d"
      }]
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

async function desenharGraficoAvaliacoes() {
  const lista = await buscarJson("/graficos/por-avaliacao");
  const dados = separarLista(lista);

  const rotulos = [];
  for (let i = 0; i < dados.nomes.length; i++) {
    rotulos.push(montarEstrelas(dados.nomes[i]));
  }

  new Chart(document.getElementById("grafico-avaliacoes"), {
    type: "bar",
    data: {
      labels: rotulos,
      datasets: [{
        label: "Livros",
        data: dados.quantidades,
        backgroundColor: "#d99a00"
      }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

async function desenharGraficoPrecos() {
  const lista = await buscarJson("/graficos/por-faixa-preco");
  const dados = separarLista(lista);

  new Chart(document.getElementById("grafico-precos"), {
    type: "bar",
    data: {
      labels: dados.nomes,
      datasets: [{
        label: "Livros",
        data: dados.quantidades,
        backgroundColor: "#1f6f7a"
      }]
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}


async function preencherCategorias() {
  const categorias = await buscarJson("/categorias");
  const select = document.getElementById("filtro-categoria");

  for (let i = 0; i < categorias.length; i++) {
    const opcao = document.createElement("option");
    opcao.value = categorias[i];
    opcao.textContent = categorias[i];
    select.appendChild(opcao);
  }
}


function criarCelula(texto, classe) {
  const celula = document.createElement("td");
  celula.textContent = texto;
  if (classe) {
    celula.className = classe;
  }
  return celula;
}

function criarLinha(livro) {
  const linha = document.createElement("tr");

  const celulaTitulo = document.createElement("td");
  const link = document.createElement("a");
  link.href = livro.url_livro;
  link.target = "_blank";
  link.rel = "noopener";
  link.textContent = livro.titulo;
  celulaTitulo.appendChild(link);
  linha.appendChild(celulaTitulo);

  linha.appendChild(criarCelula(livro.categoria));
  linha.appendChild(criarCelula(formatarPreco(livro.preco), "numero"));

  const celulaNota = criarCelula(montarEstrelas(livro.avaliacao), "estrelas");
  celulaNota.title = livro.avaliacao + " de 5";
  linha.appendChild(celulaNota);

  const textoEstoque = livro.estoque > 0 ? livro.estoque : "Esgotado";
  linha.appendChild(criarCelula(textoEstoque, "numero"));
  linha.appendChild(criarCelula(livro.data_coleta));

  return linha;
}

async function carregarLivros() {
  const parametros = new URLSearchParams({
    pagina: paginaAtual,
    limite: LIMITE,
    busca: document.getElementById("filtro-busca").value,
    categoria: document.getElementById("filtro-categoria").value,
    avaliacao_minima: document.getElementById("filtro-avaliacao").value,
    ordenar: document.getElementById("filtro-ordem").value
  });

  const precoMaximo = document.getElementById("filtro-preco").value;
  if (precoMaximo !== "") {
    parametros.set("preco_maximo", precoMaximo);
  }

  const dados = await buscarJson("/livros?" + parametros.toString());

  const corpo = document.getElementById("corpo-tabela");
  corpo.replaceChildren();

  if (dados.livros.length === 0) {
    const linha = document.createElement("tr");
    const celula = criarCelula("Nenhum livro encontrado com esses filtros.", "vazio");
    celula.colSpan = 6;
    linha.appendChild(celula);
    corpo.appendChild(linha);
  }

  for (let i = 0; i < dados.livros.length; i++) {
    corpo.appendChild(criarLinha(dados.livros[i]));
  }

  const totalPaginas = Math.max(dados.total_paginas, 1);

  document.getElementById("resumo-tabela").textContent =
    dados.total + " livro(s) encontrado(s)";
  document.getElementById("texto-pagina").textContent =
    "Página " + paginaAtual + " de " + totalPaginas;

  document.getElementById("botao-anterior").disabled = paginaAtual <= 1;
  document.getElementById("botao-proxima").disabled = paginaAtual >= totalPaginas;
}


async function executar(tarefa) {
  try {
    await tarefa();
  } catch (erro) {
    console.error(erro);
    mostrarAviso("Não foi possível carregar os dados da API. Confira se o MongoDB e a API estão ligados e se o crawler já foi executado.");
  }
}

function clicouFiltrar() {
  paginaAtual = 1;
  executar(carregarLivros);
}

function clicouLimpar() {
  document.getElementById("filtro-busca").value = "";
  document.getElementById("filtro-categoria").value = "";
  document.getElementById("filtro-avaliacao").value = "0";
  document.getElementById("filtro-preco").value = "";
  document.getElementById("filtro-ordem").value = "titulo";
  clicouFiltrar();
}

function clicouAnterior() {
  paginaAtual = paginaAtual - 1;
  executar(carregarLivros);
}

function clicouProxima() {
  paginaAtual = paginaAtual + 1;
  executar(carregarLivros);
}

function apertouEnter(evento) {
  if (evento.key === "Enter") {
    clicouFiltrar();
  }
}

document.getElementById("botao-filtrar").onclick = clicouFiltrar;
document.getElementById("botao-limpar").onclick = clicouLimpar;
document.getElementById("botao-anterior").onclick = clicouAnterior;
document.getElementById("botao-proxima").onclick = clicouProxima;
document.getElementById("filtro-busca").onkeydown = apertouEnter;
document.getElementById("filtro-preco").onkeydown = apertouEnter;

executar(carregarEstatisticas);
executar(desenharGraficoCategorias);
executar(desenharGraficoAvaliacoes);
executar(desenharGraficoPrecos);
executar(preencherCategorias);
executar(carregarLivros);
