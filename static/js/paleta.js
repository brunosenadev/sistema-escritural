// Paleta de telas (Ctrl+K) — adaptada do sisplan.paleta.js do Sisplan WEB para o menu do Escritural.
// Busca as telas que o usuário vê no menu lateral, com favoritas (Ctrl+D) e recentes no localStorage.
(function () {
  'use strict';

  if (window.__escrituralPaletaTelas) return;
  window.__escrituralPaletaTelas = true;

  var CHAVE_RECENTES = '@escritural_recentes';
  var CHAVE_FAVORITOS = '@escritural_favoritos';
  var MAX_RECENTES = 8;
  var MAX_FAVORITOS = 100;
  var MAX_RESULTADOS = 60;
  var SELETOR_MENU = '.sidebar-nav a.nav-item';
  var ICONE_ESTRELA = '<svg viewBox="0 0 24 24" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>';
  var ICONE_TELA = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/></svg>';

  var estado = { aberta: false, itens: [], porChave: {}, linhas: [], selecionado: -1, retorno: null };
  var raiz = null, campo = null, lista = null, botaoFechar = null, status = null, botaoHeader = null;

  function lerLista(chave) {
    try {
      var valor = JSON.parse(window.localStorage.getItem(chave) || '[]');
      return Array.isArray(valor) ? valor.filter(function (item) { return typeof item === 'string' && item; }) : [];
    } catch (erro) {
      return [];
    }
  }

  function gravarLista(chave, valor) {
    try { window.localStorage.setItem(chave, JSON.stringify(valor)); } catch (erro) { }
  }

  function registrarRecente(chave) {
    var recentes = lerLista(CHAVE_RECENTES).filter(function (item) { return item !== chave; });
    recentes.unshift(chave);
    gravarLista(CHAVE_RECENTES, recentes.slice(0, MAX_RECENTES));
  }

  function ehFavorito(chave) {
    return lerLista(CHAVE_FAVORITOS).indexOf(chave) !== -1;
  }

  function alternarFavorito(chave) {
    var favoritos = lerLista(CHAVE_FAVORITOS);
    var indice = favoritos.indexOf(chave);
    if (indice === -1) favoritos.unshift(chave); else favoritos.splice(indice, 1);
    gravarLista(CHAVE_FAVORITOS, favoritos.slice(0, MAX_FAVORITOS));
    return indice === -1;
  }

  // sem acento e minúsculo, mantendo o mesmo tamanho (as marcas usam as posições do texto original)
  function normalizar(texto) {
    var saida = '';
    for (var i = 0; i < texto.length; i++) {
      var c = texto.charAt(i);
      var base = (c.normalize ? c.normalize('NFD').charAt(0) : c).toLowerCase().charAt(0);
      saida += base || c;
    }
    return saida;
  }

  function hrefValido(href) {
    return !!href && href.charAt(0) !== '#' && !/^javascript:/i.test(href);
  }

  function coletarItens() {
    var itens = [];
    var vistos = {};
    Array.prototype.forEach.call(document.querySelectorAll(SELETOR_MENU), function (link) {
      var href = link.getAttribute('href');
      if (!hrefValido(href) || vistos[href]) return;
      var rotulo = link.querySelector('.nav-item-texto');
      var nome = (rotulo ? rotulo.textContent : link.textContent).replace(/\s+/g, ' ').trim();
      if (!nome) return;
      var grupo = link.closest('.nav-grupo');
      var tituloGrupo = grupo ? grupo.querySelector('.nav-grupo-btn > span') : null;
      var trilha = tituloGrupo ? [tituloGrupo.textContent.trim()] : [];
      var svg = link.querySelector('svg');
      vistos[href] = true;
      var caminho = trilha.concat(nome).join(' › ');
      itens.push({
        chave: href, nome: nome, caminho: caminho, el: link,
        icone: svg ? svg.outerHTML : ICONE_TELA,
        nNome: normalizar(nome), nCaminho: normalizar(caminho)
      });
    });
    return itens;
  }

  function subsequencia(texto, termo) {
    var posicoes = [];
    var alvo = 0;
    for (var i = 0; i < texto.length && alvo < termo.length; i++) {
      if (texto.charAt(i) === termo.charAt(alvo)) { posicoes.push(i); alvo++; }
    }
    if (alvo < termo.length) return null;
    var extensao = posicoes[posicoes.length - 1] - posicoes[0] + 1;
    return extensao <= termo.length * 3 ? posicoes : null;
  }

  function pontuarTermo(item, termo, marcas) {
    var indice = item.nNome.indexOf(termo);
    if (indice !== -1) {
      marcas.push([indice, indice + termo.length]);
      var inicioDePalavra = indice === 0 || /[^a-z0-9]/.test(item.nNome.charAt(indice - 1));
      return (indice === 0 ? 120 : inicioDePalavra ? 100 : 70) - Math.min(indice, 20) / 4;
    }
    if (item.nCaminho.indexOf(termo) !== -1) return 30;
    if (termo.length >= 3) {
      var posicoes = subsequencia(item.nNome, termo);
      if (posicoes) {
        posicoes.forEach(function (p) { marcas.push([p, p + 1]); });
        return 20;
      }
    }
    return -1;
  }

  function unirMarcas(marcas) {
    marcas.sort(function (a, b) { return a[0] - b[0]; });
    var unidas = [];
    marcas.forEach(function (marca) {
      var ultima = unidas[unidas.length - 1];
      if (ultima && marca[0] <= ultima[1]) ultima[1] = Math.max(ultima[1], marca[1]);
      else unidas.push([marca[0], marca[1]]);
    });
    return unidas;
  }

  function buscar(consulta) {
    var termos = normalizar(consulta).split(/\s+/).filter(Boolean);
    var favoritos = lerLista(CHAVE_FAVORITOS);
    var recentes = lerLista(CHAVE_RECENTES);
    var encontrados = [];
    estado.itens.forEach(function (item) {
      var marcas = [];
      var total = 0;
      for (var i = 0; i < termos.length; i++) {
        var pontos = pontuarTermo(item, termos[i], marcas);
        if (pontos < 0) return;
        total += pontos;
      }
      if (favoritos.indexOf(item.chave) !== -1) total += 8;
      if (recentes.indexOf(item.chave) !== -1) total += 4;
      encontrados.push({ item: item, marcas: unirMarcas(marcas), pontos: total });
    });
    encontrados.sort(function (a, b) {
      if (b.pontos !== a.pontos) return b.pontos - a.pontos;
      if (a.item.nome.length !== b.item.nome.length) return a.item.nome.length - b.item.nome.length;
      return a.item.nome.localeCompare(b.item.nome);
    });
    return encontrados.slice(0, MAX_RESULTADOS);
  }

  function resolverChaves(chaves) {
    return chaves.map(function (chave) { return estado.porChave[chave]; })
      .filter(Boolean)
      .map(function (item) { return { item: item, marcas: [] }; });
  }

  function criarElemento(tag, classe, texto) {
    var el = document.createElement(tag);
    if (classe) el.className = classe;
    if (texto) el.textContent = texto;
    return el;
  }

  function preencherComMarcas(el, texto, marcas) {
    var cursor = 0;
    marcas.forEach(function (marca) {
      if (marca[0] > cursor) el.appendChild(document.createTextNode(texto.slice(cursor, marca[0])));
      el.appendChild(criarElemento('mark', '', texto.slice(marca[0], marca[1])));
      cursor = marca[1];
    });
    if (cursor < texto.length) el.appendChild(document.createTextNode(texto.slice(cursor)));
  }

  function atualizarEstrela(botao, ativo, nome) {
    botao.setAttribute('aria-pressed', ativo ? 'true' : 'false');
    botao.setAttribute('aria-label', (ativo ? 'Remover dos favoritos: ' : 'Favoritar: ') + nome);
    botao.title = ativo ? 'Remover dos favoritos' : 'Favoritar';
    botao.classList.toggle('paleta-telas__estrela--ativa', ativo);
  }

  function criarLinha(entrada, indice) {
    var item = entrada.item;
    var linha = criarElemento('div', 'paleta-telas__linha');
    linha.setAttribute('role', 'presentation');
    linha.setAttribute('data-indice', String(indice));

    var opcao = criarElemento('div', 'paleta-telas__item');
    opcao.id = 'paleta-telas-opcao-' + indice;
    opcao.setAttribute('role', 'option');
    opcao.setAttribute('aria-selected', 'false');

    var icone = criarElemento('span', 'paleta-telas__icone');
    icone.setAttribute('aria-hidden', 'true');
    icone.innerHTML = item.icone;
    opcao.appendChild(icone);

    var texto = criarElemento('span', 'paleta-telas__texto');
    var nome = criarElemento('span', 'paleta-telas__nome');
    preencherComMarcas(nome, item.nome, entrada.marcas);
    texto.appendChild(nome);
    texto.appendChild(criarElemento('span', 'paleta-telas__caminho', item.caminho));
    opcao.appendChild(texto);
    linha.appendChild(opcao);

    var estrela = criarElemento('button', 'paleta-telas__estrela');
    estrela.type = 'button';
    estrela.tabIndex = -1;
    estrela.innerHTML = ICONE_ESTRELA;
    atualizarEstrela(estrela, ehFavorito(item.chave), item.nome);
    linha.appendChild(estrela);
    return linha;
  }

  function definirSelecao(indice, rolar) {
    var anterior = estado.linhas[estado.selecionado];
    if (anterior) {
      anterior.el.classList.remove('paleta-telas__linha--selecionada');
      anterior.el.firstChild.setAttribute('aria-selected', 'false');
    }
    estado.selecionado = indice;
    var atual = estado.linhas[indice];
    if (!atual) { campo.removeAttribute('aria-activedescendant'); return; }
    atual.el.classList.add('paleta-telas__linha--selecionada');
    atual.el.firstChild.setAttribute('aria-selected', 'true');
    campo.setAttribute('aria-activedescendant', atual.el.firstChild.id);
    if (rolar) atual.el.scrollIntoView({ block: 'nearest' });
  }

  function renderizar(manterChave) {
    var consulta = campo.value.trim();
    var grupos = [];
    if (!consulta) {
      var favoritas = resolverChaves(lerLista(CHAVE_FAVORITOS));
      var recentes = resolverChaves(lerLista(CHAVE_RECENTES));
      if (favoritas.length) grupos.push({ titulo: 'Favoritas', entradas: favoritas });
      if (recentes.length) grupos.push({ titulo: 'Recentes', entradas: recentes });
    } else {
      var resultados = buscar(consulta);
      if (resultados.length) grupos.push({ titulo: '', entradas: resultados });
    }

    lista.textContent = '';
    estado.linhas = [];
    estado.selecionado = -1;

    if (!grupos.length) {
      var vazio = criarElemento('div', 'paleta-telas__vazio');
      vazio.setAttribute('role', 'presentation');
      vazio.appendChild(criarElemento('strong', '', consulta ? 'Nenhuma tela encontrada' : 'Busque qualquer tela do sistema'));
      vazio.appendChild(criarElemento('span', '', consulta ? 'Tente outro termo ou parte do nome da tela.' : 'Suas telas favoritas e recentes aparecem aqui.'));
      status.textContent = consulta ? 'Nenhum resultado' : '';
      lista.appendChild(vazio);
      campo.removeAttribute('aria-activedescendant');
      return;
    }

    grupos.forEach(function (grupo) {
      var bloco = criarElemento('div', 'paleta-telas__grupo');
      bloco.setAttribute('role', 'group');
      if (grupo.titulo) {
        bloco.setAttribute('aria-label', grupo.titulo);
        var titulo = criarElemento('div', 'paleta-telas__titulo-grupo', grupo.titulo);
        titulo.setAttribute('aria-hidden', 'true');
        bloco.appendChild(titulo);
      }
      grupo.entradas.forEach(function (entrada) {
        var linha = criarLinha(entrada, estado.linhas.length);
        estado.linhas.push({ item: entrada.item, el: linha });
        bloco.appendChild(linha);
      });
      lista.appendChild(bloco);
    });

    var indice = 0;
    if (manterChave) {
      for (var i = 0; i < estado.linhas.length; i++) {
        if (estado.linhas[i].item.chave === manterChave) { indice = i; break; }
      }
    }
    definirSelecao(indice, false);
    lista.scrollTop = 0;
    if (consulta) status.textContent = estado.linhas.length + (estado.linhas.length === 1 ? ' resultado' : ' resultados');
  }

  function mover(delta) {
    var total = estado.linhas.length;
    if (!total) return;
    var proximo = Math.abs(delta) === 1
      ? (estado.selecionado + delta + total) % total
      : Math.max(0, Math.min(total - 1, estado.selecionado + delta));
    definirSelecao(proximo, true);
  }

  function abrirItem(item) {
    fechar(false);
    if (item.el && item.el.isConnected) item.el.click();
  }

  function abrirSelecionado() {
    var linha = estado.linhas[estado.selecionado];
    if (linha) abrirItem(linha.item);
  }

  function alternarSelecionado() {
    var linha = estado.linhas[estado.selecionado];
    if (!linha) return;
    alternarFavorito(linha.item.chave);
    renderizar(linha.item.chave);
  }

  function cicloDeFoco(inverso) {
    var focaveis = [campo, botaoFechar];
    var indice = focaveis.indexOf(document.activeElement);
    var proximo = indice === -1 ? 0 : (indice + (inverso ? -1 : 1) + focaveis.length) % focaveis.length;
    focaveis[proximo].focus();
  }

  function construir() {
    if (raiz) return;
    raiz = criarElemento('div', 'paleta-telas');
    raiz.hidden = true;

    var painel = criarElemento('div', 'paleta-telas__painel');
    painel.setAttribute('role', 'dialog');
    painel.setAttribute('aria-modal', 'true');
    painel.setAttribute('aria-label', 'Buscar telas');

    var busca = criarElemento('div', 'paleta-telas__busca');
    var lupa = criarElemento('span', 'paleta-telas__lupa');
    lupa.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>';
    busca.appendChild(lupa);

    campo = document.createElement('input');
    campo.type = 'text';
    campo.className = 'paleta-telas__campo';
    campo.placeholder = 'Buscar telas...';
    campo.autocomplete = 'off';
    campo.spellcheck = false;
    campo.setAttribute('role', 'combobox');
    campo.setAttribute('aria-label', 'Buscar telas');
    campo.setAttribute('aria-expanded', 'true');
    campo.setAttribute('aria-controls', 'paleta-telas-lista');
    campo.setAttribute('aria-autocomplete', 'list');
    busca.appendChild(campo);

    botaoFechar = criarElemento('button', 'paleta-telas__fechar', 'esc');
    botaoFechar.type = 'button';
    botaoFechar.setAttribute('aria-label', 'Fechar busca de telas');
    busca.appendChild(botaoFechar);
    painel.appendChild(busca);

    lista = criarElemento('div', 'paleta-telas__lista');
    lista.id = 'paleta-telas-lista';
    lista.setAttribute('role', 'listbox');
    lista.setAttribute('aria-label', 'Telas');
    painel.appendChild(lista);

    status = criarElemento('div', 'paleta-telas__status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    painel.appendChild(status);

    var rodape = criarElemento('div', 'paleta-telas__rodape');
    rodape.setAttribute('aria-hidden', 'true');
    [[['↑', '↓'], 'navegar'], [['Enter'], 'abrir'], [['Ctrl', 'D'], 'favoritar'], [['Esc'], 'fechar']].forEach(function (dica) {
      var bloco = criarElemento('span', 'paleta-telas__dica');
      dica[0].forEach(function (tecla) { bloco.appendChild(criarElemento('kbd', '', tecla)); });
      bloco.appendChild(document.createTextNode(' ' + dica[1]));
      rodape.appendChild(bloco);
    });
    painel.appendChild(rodape);
    raiz.appendChild(painel);

    raiz.addEventListener('mousedown', function (e) {
      if (e.target === raiz) { e.preventDefault(); fechar(true); return; }
      if (e.target !== campo) e.preventDefault();
    });
    lista.addEventListener('mousemove', function (e) {
      var linha = e.target.closest('.paleta-telas__linha');
      if (!linha) return;
      var indice = parseInt(linha.getAttribute('data-indice'), 10);
      if (indice !== estado.selecionado) definirSelecao(indice, false);
    });
    lista.addEventListener('click', function (e) {
      var linha = e.target.closest('.paleta-telas__linha');
      if (!linha) return;
      var entrada = estado.linhas[parseInt(linha.getAttribute('data-indice'), 10)];
      if (!entrada) return;
      if (e.target.closest('.paleta-telas__estrela')) {
        alternarFavorito(entrada.item.chave);
        renderizar(entrada.item.chave);
        return;
      }
      abrirItem(entrada.item);
    });
    botaoFechar.addEventListener('click', function () { fechar(true); });
    campo.addEventListener('input', function () { renderizar(); });
    document.body.appendChild(raiz);
  }

  // não abre por cima de modal ou diálogo do sistema
  function bloqueado() {
    if (document.querySelector('.overlay-modal.aberto')) return true;
    return ['overlay-dialogo', 'overlay-minha-senha'].some(function (id) {
      var el = document.getElementById(id);
      return el && el.style.display && el.style.display !== 'none';
    });
  }

  function abrir() {
    if (estado.aberta) return true;
    if (bloqueado()) return false;
    construir();
    estado.itens = coletarItens();
    estado.porChave = {};
    estado.itens.forEach(function (item) { estado.porChave[item.chave] = item; });
    estado.retorno = document.activeElement;
    campo.value = '';
    renderizar();
    raiz.hidden = false;
    void raiz.offsetWidth;
    raiz.classList.add('paleta-telas--aberta');
    estado.aberta = true;
    if (botaoHeader) botaoHeader.setAttribute('aria-expanded', 'true');
    campo.focus();
    return true;
  }

  function fechar(devolverFoco) {
    if (!estado.aberta) return;
    estado.aberta = false;
    raiz.classList.remove('paleta-telas--aberta');
    raiz.hidden = true;
    if (botaoHeader) botaoHeader.setAttribute('aria-expanded', 'false');
    var retorno = estado.retorno;
    estado.retorno = null;
    if (devolverFoco && retorno && retorno.isConnected && typeof retorno.focus === 'function') {
      retorno.focus({ preventScroll: true });
    }
  }

  function ehAtalho(e) {
    return (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey && String(e.key || '').toLowerCase() === 'k';
  }

  function aoTeclarAberta(e) {
    e.stopPropagation();
    if (e.isComposing || e.keyCode === 229) return;
    var tecla = e.key;
    var comando = e.ctrlKey || e.metaKey;
    if (tecla === 'Escape' || (comando && String(tecla).toLowerCase() === 'k')) { e.preventDefault(); fechar(true); }
    else if (tecla === 'ArrowDown') { e.preventDefault(); mover(1); }
    else if (tecla === 'ArrowUp') { e.preventDefault(); mover(-1); }
    else if (tecla === 'PageDown') { e.preventDefault(); mover(5); }
    else if (tecla === 'PageUp') { e.preventDefault(); mover(-5); }
    else if (tecla === 'Enter') {
      if (document.activeElement === botaoFechar) return;
      e.preventDefault();
      abrirSelecionado();
    }
    else if (tecla === 'Tab') { e.preventDefault(); cicloDeFoco(e.shiftKey); }
    else if (comando && String(tecla).toLowerCase() === 'd') { e.preventDefault(); alternarSelecionado(); }
    else if (!comando && !e.altKey && document.activeElement !== campo && document.activeElement !== botaoFechar) campo.focus();
  }

  window.addEventListener('keydown', function (e) {
    if (estado.aberta) { aoTeclarAberta(e); return; }
    if (!ehAtalho(e) || e.repeat) return;
    if (abrir()) { e.preventDefault(); e.stopPropagation(); }
  }, true);
  ['keyup', 'keypress'].forEach(function (tipo) {
    window.addEventListener(tipo, function (e) { if (estado.aberta) e.stopPropagation(); }, true);
  });

  // clique em qualquer tela do menu entra nas recentes (a paleta também abre pelo clique)
  document.addEventListener('click', function (e) {
    var link = e.target instanceof Element ? e.target.closest(SELETOR_MENU) : null;
    if (link && hrefValido(link.getAttribute('href'))) registrarRecente(link.getAttribute('href'));
  }, true);

  botaoHeader = document.getElementById('btn-paleta-telas');
  if (botaoHeader) {
    botaoHeader.setAttribute('aria-expanded', 'false');
    botaoHeader.addEventListener('click', function () {
      if (estado.aberta) fechar(true); else abrir();
    });
  }

  window.PaletaTelas = { abrir: abrir, fechar: fechar };
})();
