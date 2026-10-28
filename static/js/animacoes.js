// Animações do Escritural WEB — adaptadas do laboratório de animações do Sisplan WEB.
// Expõe window.Fx com os efeitos usados pelas telas.
(function () {
  'use strict';

  var reduzido = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var podeAnimar = !reduzido && typeof Element.prototype.animate === 'function';

  // Re-dispara uma animação de classe (remove, força o layout e devolve).
  function retocar(el, classe, duracaoMs) {
    if (!el) return;
    el.classList.remove(classe);
    void el.offsetWidth;
    el.classList.add(classe);
    if (duracaoMs) setTimeout(function () { el.classList.remove(classe); }, duracaoMs);
  }

  // ── Tremida de validação ──
  function tremer(el) {
    if (!el || !podeAnimar) return;
    el.animate(
      [0, -10, 10, -8, 8, -4, 0].map(function (x) { return { transform: 'translateX(' + x + 'px)' }; }),
      { duration: 420, easing: 'ease-in-out' }
    );
  }

  // Campo inválido: treme e acende a borda em vermelho por um instante.
  function marcarErro(campo) {
    if (!campo) return;
    tremer(campo);
    if (!podeAnimar) return;
    campo.animate(
      [{ borderColor: '#e2457a', boxShadow: '0 0 0 3px rgba(226,69,122,0.25)' }, { boxShadow: '0 0 0 0 transparent' }],
      { duration: 900, easing: 'ease-out' }
    );
    campo.focus();
  }

  // Botão confirma com um pulso verde.
  function confirmar(botao) {
    if (!botao || !podeAnimar) return;
    botao.animate(
      [{ transform: 'scale(1)' }, { transform: 'scale(1.06)', filter: 'brightness(1.1)', offset: 0.3 }, { transform: 'scale(1)' }],
      { duration: 450, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)' }
    );
  }

  // ── Contador com easing ──
  function contar(el, alvo, opcoes) {
    if (!el) return;
    opcoes = opcoes || {};
    // só conta números simples ("1234", "12.5"); texto formatado fica como está
    if (typeof alvo === 'string' && !/^-?\d+(\.\d+)?$/.test(alvo.trim())) return;
    alvo = Number(alvo);
    if (!isFinite(alvo)) return;
    var formato = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: opcoes.casas || 0, minimumFractionDigits: opcoes.casas || 0 });
    var sufixo = opcoes.sufixo || '';
    var de = Number(opcoes.de || 0);
    if (reduzido || alvo === de) { el.textContent = formato.format(alvo) + sufixo; return; }
    var duracao = opcoes.duracao || 1200;
    var inicio = performance.now();
    (function passo(agora) {
      var t = Math.min((agora - inicio) / duracao, 1);
      var suave = 1 - Math.pow(1 - t, 4);
      el.textContent = formato.format(de + (alvo - de) * suave) + sufixo;
      if (t < 1) requestAnimationFrame(passo);
    })(inicio);
  }

  // ── Linha de tabela que mudou ──
  function piscarLinha(tr, ok) {
    retocar(tr, ok === false ? 'fx-linha-erro' : 'fx-linha-ok', 1500);
  }

  // ── Elemento que aparece (banner, aviso): desce e surge ──
  function surgir(el) {
    if (!el || !podeAnimar) return;
    el.animate(
      [{ opacity: 0, transform: 'translateY(-8px) scale(0.98)' }, { opacity: 1, transform: 'none' }],
      { duration: 320, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }
    );
  }

  // ── Linha removida: desliza e some antes de sair do DOM ──
  function removerLinha(tr, depois) {
    if (!tr) { if (depois) depois(); return; }
    if (!podeAnimar) { tr.remove(); if (depois) depois(); return; }
    tr.style.pointerEvents = 'none';
    var animacao = tr.animate(
      [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateX(24px)' }],
      { duration: 260, easing: 'ease-in', fill: 'forwards' }
    );
    var limite = new Promise(function (r) { setTimeout(r, 500); });
    Promise.race([animacao.finished.catch(function () {}), limite]).then(function () {
      tr.remove();
      if (depois) depois();
    });
  }

  // ── Linhas de tabela entram em cascata (só as primeiras, para tabela grande não demorar) ──
  function linhasEntrando(tbody) {
    if (!tbody || reduzido) return;
    var visiveis = Array.prototype.filter.call(tbody.rows, function (tr) { return tr.style.display !== 'none'; });
    visiveis.slice(0, 15).forEach(function (tr, k) {
      tr.style.setProperty('--fx-i', k);
      retocar(tr, 'fx-linha-entra');
      setTimeout(function () { tr.classList.remove('fx-linha-entra'); }, 420 + k * 35);
    });
  }

  // ── FLIP: mede, muda o DOM (mover), mede de novo e anima a diferença ──
  function flip(el, mover) {
    var antes = el.getBoundingClientRect();
    mover();
    if (!podeAnimar) return Promise.resolve();
    var depois = el.getBoundingClientRect();
    var dx = antes.left - depois.left;
    var dy = antes.top - depois.top;
    if (!dx && !dy) return Promise.resolve();
    return el.animate(
      [{ transform: 'translate(' + dx + 'px, ' + dy + 'px) scale(1.03)' }, { transform: 'none' }],
      { duration: 550, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }
    ).finished.catch(function () {});
  }

  // ── Entrada em cascata ──
  function cascata(elementos) {
    if (reduzido) return;
    Array.prototype.forEach.call(elementos, function (el, k) {
      el.style.setProperty('--fx-i', Math.min(k, 10));
      retocar(el, 'fx-cascata');
      el.addEventListener('animationend', function fim(e) {
        if (e.target !== el) return;
        el.classList.remove('fx-cascata');
        el.removeEventListener('animationend', fim);
      });
    });
  }

  // ── Menu suspenso: abre/fecha com element.animate() e itens em cascata ──
  function abrirMenu(lista, itens) {
    if (!lista) return;
    lista.style.display = lista.dataset.fxDisplay || 'block';
    if (!podeAnimar) return;
    lista.animate(
      [{ opacity: 0, transform: 'translateY(-6px) scale(0.97)' }, { opacity: 1, transform: 'none' }],
      { duration: 180, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' }
    );
    Array.prototype.forEach.call(itens || [], function (item, k) {
      item.animate([{ opacity: 0, transform: 'translateX(-6px)' }, { opacity: 1, transform: 'none' }], {
        duration: 240, delay: k * 35, easing: 'ease-out', fill: 'backwards'
      });
    });
  }

  function fecharMenu(lista) {
    if (!lista || lista.style.display === 'none') return;
    if (!podeAnimar) { lista.style.display = 'none'; return; }
    var animacao = lista.animate(
      [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(-4px) scale(0.98)' }],
      { duration: 130, easing: 'ease-in' }
    );
    // Promise.race: se a animação for cancelada, o menu fecha mesmo assim
    var limite = new Promise(function (r) { setTimeout(r, 450); });
    Promise.race([animacao.finished.catch(function () {}), limite]).then(function () {
      lista.style.display = 'none';
    });
  }

  // ── Toast: da bolinha ao cartão, com anel marcando o tempo ──
  var TOASTS = {
    sucesso: { cor: '#16a874', titulo: 'Sucesso', icone: '<polyline points="20 6 9 17 4 12"/>' },
    erro: { cor: '#e2457a', titulo: 'Erro', icone: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>' },
    aviso: { cor: '#d98a0b', titulo: 'Atenção', icone: '<line x1="12" y1="7" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' },
    info: { cor: '#3b6cf6', titulo: 'Informação', icone: '<line x1="12" y1="11" x2="12" y2="17"/><line x1="12" y1="7" x2="12.01" y2="7"/>' }
  };
  var ENTRADA_MS = 560;

  function fecharToast(toast) {
    if (toast.classList.contains('saindo')) return;
    toast.classList.remove('entrando');
    toast.classList.add('saindo');
    setTimeout(function () { toast.remove(); }, reduzido ? 0 : 450);
  }

  // Mesma assinatura do mostrarToast antigo; a mensagem continua aceitando HTML.
  function toast(tipo, mensagem, duracao) {
    var area = document.getElementById('area-toasts');
    if (!area) return;
    var t = TOASTS[tipo] || TOASTS.info;
    var el = document.createElement('div');
    el.className = 'toast-fx entrando';
    el.setAttribute('role', tipo === 'erro' ? 'alert' : 'status');
    el.style.setProperty('--cor', t.cor);
    el.innerHTML =
      '<span class="toast-fundo"></span>' +
      '<svg class="toast-anel" aria-hidden="true"><rect pathLength="1" /></svg>' +
      '<span class="toast-icone"><svg viewBox="0 0 24 24">' + t.icone + '</svg></span>' +
      '<div class="toast-texto"><strong></strong><span></span></div>' +
      '<button type="button" class="toast-fechar" aria-label="Fechar">×</button>';
    el.querySelector('strong').textContent = t.titulo;
    el.querySelector('.toast-texto span').innerHTML = mensagem;
    el.querySelector('.toast-fechar').addEventListener('click', function () { fecharToast(el); });
    area.appendChild(el);

    var rect = el.querySelector('.toast-anel rect');
    rect.setAttribute('x', 1.25);
    rect.setAttribute('y', 1.25);
    rect.setAttribute('width', Math.max(el.offsetWidth + 12 - 2.5, 0));
    rect.setAttribute('height', Math.max(el.offsetHeight + 12 - 2.5, 0));
    rect.setAttribute('rx', 21);

    var tempoMs = duracao || 3500;
    if (typeof rect.animate !== 'function') {
      setTimeout(function () { fecharToast(el); }, tempoMs);
      return;
    }
    var tempo = rect.animate(
      [{ strokeDashoffset: 0 }, { strokeDashoffset: -1 }],
      { duration: tempoMs, delay: reduzido ? 0 : ENTRADA_MS, easing: 'linear', fill: 'both' }
    );
    tempo.finished.then(function () { fecharToast(el); }).catch(function () {});
    el.addEventListener('mouseenter', function () { tempo.pause(); });
    el.addEventListener('mouseleave', function () { if (tempo.playState === 'paused') tempo.play(); });
  }

  // ── Holofote nos cartões .fx-luz (o JS só grava --mx/--my) ──
  function iniciarLuz() {
    var pendente = null;
    var raf = 0;
    document.addEventListener('pointermove', function (e) {
      pendente = e;
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = 0;
        var alvo = pendente.target instanceof Element ? pendente.target.closest('.fx-luz') : null;
        if (!alvo) return;
        var l = alvo.getBoundingClientRect();
        alvo.style.setProperty('--mx', pendente.clientX - l.left + 'px');
        alvo.style.setProperty('--my', pendente.clientY - l.top + 'px');
      });
    }, { passive: true });
    document.addEventListener('pointerout', function (e) {
      var alvo = e.target instanceof Element ? e.target.closest('.fx-luz') : null;
      if (alvo && !alvo.contains(e.relatedTarget)) {
        alvo.style.removeProperty('--mx');
        alvo.style.removeProperty('--my');
      }
    });
  }

  // ── Abas com indicador deslizante ──
  // barra: contêiner das abas; seletorAtiva: aba atual; indicador: elemento criado aqui.
  // linha=true: em vez de um fundo, uma linha de 2px desliza por baixo da aba (abas sublinhadas).
  function abas(barra, seletorAtiva, classeIndicador, linha) {
    if (!barra) return null;
    barra.classList.add('fx-abas');
    if (linha) {
      barra.classList.add('fx-abas--linha');
      classeIndicador = (classeIndicador || '') + ' fx-abas-linha';
    }
    var indicador = document.createElement('span');
    indicador.className = 'fx-abas-indicador ' + (classeIndicador || '');
    indicador.setAttribute('aria-hidden', 'true');
    barra.appendChild(indicador);
    function posicionar(semTransicao) {
      var ativa = barra.querySelector(seletorAtiva);
      // aba escondida (ex.: dentro de modal fechado) não tem medida: espera o próximo posicionar()
      if (!ativa || !ativa.offsetWidth) { indicador.style.opacity = '0'; return; }
      if (semTransicao) indicador.style.transition = 'none';
      indicador.style.opacity = '1';
      var altura = linha ? 2 : ativa.offsetHeight;
      var topo = linha ? ativa.offsetTop + ativa.offsetHeight - 2 : ativa.offsetTop;
      indicador.style.width = ativa.offsetWidth + 'px';
      indicador.style.height = altura + 'px';
      indicador.style.top = '0';
      indicador.style.translate = ativa.offsetLeft + 'px ' + topo + 'px';
      if (semTransicao) { void indicador.offsetWidth; indicador.style.transition = ''; }
    }
    posicionar(true);
    window.addEventListener('resize', function () { posicionar(true); });
    return posicionar;
  }

  window.Fx = {
    reduzido: reduzido,
    retocar: retocar,
    tremer: tremer,
    marcarErro: marcarErro,
    confirmar: confirmar,
    contar: contar,
    piscarLinha: piscarLinha,
    surgir: surgir,
    removerLinha: removerLinha,
    linhasEntrando: linhasEntrando,
    flip: flip,
    cascata: cascata,
    abrirMenu: abrirMenu,
    fecharMenu: fecharMenu,
    toast: toast,
    abas: abas
  };

  function iniciar() {
    iniciarLuz();
    // conteúdo da página entra em cascata (cada tela pode marcar mais blocos com data-fx-cascata)
    var area = document.querySelector('.area-conteudo');
    if (area) {
      var blocos = Array.prototype.slice.call(area.children).filter(function (el) {
        return el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE' && el.offsetParent !== null;
      });
      Array.prototype.forEach.call(area.querySelectorAll('[data-fx-cascata]'), function (grupo) {
        // o grupo não anima inteiro, só os filhos (senão o deslocamento soma)
        blocos = blocos.filter(function (b) { return !b.contains(grupo); });
        Array.prototype.push.apply(blocos, Array.prototype.slice.call(grupo.children));
      });
      cascata(blocos);
      Array.prototype.forEach.call(area.querySelectorAll('tbody'), linhasEntrando);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
