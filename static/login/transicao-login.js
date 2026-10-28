(function () {
  'use strict';

  var CHAVE = 'sisplan-transicao-login';
  var COBRIR_MS = 420;
  var PAUSA_MS = 120;
  var PAUSA_POUSO_MS = 450;
  var POUSO_MS = 560;
  var ESPERA_MAXIMA_MS = 6000;
  var VALIDADE_MARCA_MS = 15000;
  var TAMANHO_LOGO_PX = 96;
  var SELETOR_LOGO_SISTEMA = '.marca-sisplan__logo';
  var SELETOR_BOTAO_LOGIN = '.lp-btn-enter';
  var SUAVE = 'cubic-bezier(0.4, 0, 0.2, 1)';
  var CIRCULO = 'cubic-bezier(0.55, 0, 0.45, 1)';

  var script = document.currentScript;
  var base = script && script.src ? script.src.replace(/login\/transicao-login\.js.*$/, '') : '';
  var LOGO_URL = base + 'img/icon.png';

  var MODO_LEVE = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  var FUNDO_CORTINA = MODO_LEVE
    ? 'background:rgba(226,232,244,.92)'
    : 'background:rgba(15,23,42,.14);-webkit-backdrop-filter:blur(22px) saturate(1.2);backdrop-filter:blur(22px) saturate(1.2)';

  var ESTILO =
    '.entrada-transicao{position:fixed;inset:0;z-index:1000001;pointer-events:none}' +
    '.entrada-cortina{position:absolute;inset:0;display:grid;place-items:center;' + FUNDO_CORTINA + '}' +
    '.entrada-orbe{width:8.5rem;height:8.5rem;border-radius:9999px;border:2px solid rgba(255,255,255,.22);' +
    'border-top-color:rgba(255,255,255,.95);box-shadow:0 0 0 1px rgba(15,23,42,.06);animation:entrada-orbe-gira .9s linear infinite}' +
    '@keyframes entrada-orbe-gira{to{transform:rotate(360deg)}}' +
    '.entrada-logo{position:absolute;left:50%;top:50%;height:auto;translate:-50% -50%;' +
    'filter:drop-shadow(0 0 1px rgba(255,255,255,.9)) drop-shadow(0 6px 18px rgba(0,0,0,.25))}';

  function reduzirMovimento() {
    return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function suportado() {
    return typeof Element !== 'undefined' && typeof Element.prototype.animate === 'function' && !reduzirMovimento();
  }

  function esperar(ms) {
    return new Promise(function (resolve) { window.setTimeout(resolve, ms); });
  }

  function marcar(etapa) {
    try {
      window.sessionStorage.setItem(CHAVE, JSON.stringify({ etapa: etapa, em: Date.now() }));
    } catch (e) { /* sem sessionStorage a próxima página só não continua a transição */ }
  }

  function lerMarca() {
    try {
      var valor = window.sessionStorage.getItem(CHAVE);
      window.sessionStorage.removeItem(CHAVE);
      var marca = valor ? JSON.parse(valor) : null;
      return marca && Date.now() - marca.em < VALIDADE_MARCA_MS ? marca.etapa : null;
    } catch (e) {
      return null;
    }
  }

  function esperarElemento(seletor) {
    var limite = Date.now() + ESPERA_MAXIMA_MS;
    return new Promise(function (resolve) {
      (function procurar() {
        var el = document.querySelector(seletor);
        var pronto = el && (el.tagName !== 'IMG' || el.complete) && el.getBoundingClientRect().width > 0;
        if (pronto) return resolve(el);
        if (Date.now() > limite) return resolve(null);
        window.setTimeout(procurar, 50);
      })();
    });
  }

  function centroDe(rect) {
    return rect
      ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
      : { x: window.innerWidth / 2, y: window.innerHeight / 2 };
  }

  function raioAte(ponto) {
    return Math.hypot(Math.max(ponto.x, window.innerWidth - ponto.x), Math.max(ponto.y, window.innerHeight - ponto.y));
  }

  function escalaTela() {
    if (window.innerWidth < 1024) return 1;
    var zoom = window.outerWidth && window.innerWidth ? window.outerWidth / window.innerWidth : 1;
    if (zoom > 0.95 && zoom < 1.1) zoom = 1;
    var ajuste = Math.min(1, Math.max(0.7, Math.min((window.innerWidth * zoom) / 1600, (window.innerHeight * zoom) / 940)));
    return zoom < 1 ? ajuste / zoom : ajuste;
  }

  function criarCamadas() {
    if (!document.getElementById('entrada-transicao-estilo')) {
      var estilo = document.createElement('style');
      estilo.id = 'entrada-transicao-estilo';
      estilo.textContent = ESTILO;
      (document.head || document.documentElement).appendChild(estilo);
    }
    var raiz = document.createElement('div');
    raiz.className = 'entrada-transicao';
    raiz.setAttribute('aria-hidden', 'true');
    var cortina = document.createElement('div');
    cortina.className = 'entrada-cortina';
    var orbe = document.createElement('div');
    orbe.className = 'entrada-orbe';
    cortina.appendChild(orbe);
    var logo = document.createElement('img');
    logo.className = 'entrada-logo';
    logo.src = LOGO_URL;
    logo.alt = '';
    var escala = escalaTela();
    logo.style.width = TAMANHO_LOGO_PX * escala + 'px';
    orbe.style.width = 8.5 * escala + 'rem';
    orbe.style.height = 8.5 * escala + 'rem';
    raiz.appendChild(cortina);
    raiz.appendChild(logo);
    (document.body || document.documentElement).appendChild(raiz);
    window.setTimeout(function () {
      raiz.remove();
      var logoSistema = document.querySelector(SELETOR_LOGO_SISTEMA);
      if (logoSistema) logoSistema.style.removeProperty('opacity');
    }, COBRIR_MS + ESPERA_MAXIMA_MS + PAUSA_POUSO_MS + POUSO_MS + 1500);
    return { raiz: raiz, cortina: cortina, orbe: orbe, logo: logo };
  }

  function deslocamentoAte(logo, rect) {
    var l = logo.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0, escala: 0.4 };
    return {
      x: rect.left + rect.width / 2 - (l.left + l.width / 2),
      y: rect.top + rect.height / 2 - (l.top + l.height / 2),
      escala: l.height ? rect.height / l.height : 0.4,
    };
  }

  function cobrir(origem) {
    if (!suportado()) return Promise.resolve();
    var camadas = criarCamadas();
    var c = centroDe(origem);
    var raio = raioAte(c);
    camadas.cortina.animate(
      [{ clipPath: 'circle(0px at ' + c.x + 'px ' + c.y + 'px)' }, { clipPath: 'circle(' + raio + 'px at ' + c.x + 'px ' + c.y + 'px)' }],
      { duration: COBRIR_MS, easing: CIRCULO, fill: 'forwards' }
    );
    camadas.logo.animate(
      [{ opacity: 0, transform: 'scale(0.92)' }, { opacity: 1, transform: 'scale(1)' }],
      { duration: 320, delay: COBRIR_MS * 0.5, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', fill: 'backwards' }
    );
    marcar('entrada');
    return esperar(COBRIR_MS);
  }

  function sair() {
    if (!suportado()) return Promise.resolve();
    var logoSistema = document.querySelector(SELETOR_LOGO_SISTEMA);
    var origem = logoSistema ? logoSistema.getBoundingClientRect() : null;
    var camadas = criarCamadas();
    var d = deslocamentoAte(camadas.logo, origem);
    if (logoSistema) logoSistema.style.opacity = '0';
    camadas.cortina.animate([{ opacity: 0 }, { opacity: 1 }], { duration: POUSO_MS, easing: SUAVE });
    camadas.orbe.animate([{ opacity: 0 }, { opacity: 1 }], {
      duration: POUSO_MS * 0.4, delay: POUSO_MS * 0.6, easing: SUAVE, fill: 'backwards'
    });
    camadas.logo.animate(
      [
        { transform: 'translate(' + d.x + 'px, ' + d.y + 'px) scale(' + d.escala + ')', opacity: origem ? 1 : 0 },
        { transform: 'translate(0, 0) scale(1)', opacity: 1 }
      ],
      { duration: POUSO_MS, easing: SUAVE }
    );
    marcar('saida');
    return esperar(POUSO_MS + PAUSA_MS);
  }

  function pousarNoSistema() {
    var camadas = criarCamadas();
    esperarElemento(SELETOR_LOGO_SISTEMA).then(function (logoSistema) {
      return esperar(PAUSA_POUSO_MS).then(function () {
        var destino = logoSistema ? logoSistema.getBoundingClientRect() : null;
        var d = deslocamentoAte(camadas.logo, destino);
        if (logoSistema) logoSistema.style.opacity = '0';
        camadas.orbe.animate([{ opacity: 1 }, { opacity: 0 }], { duration: POUSO_MS * 0.4, easing: SUAVE, fill: 'forwards' });
        camadas.cortina.animate([{ opacity: 1 }, { opacity: 0 }], { duration: POUSO_MS, easing: SUAVE, fill: 'forwards' });
        var voo = camadas.logo.animate(
          [
            { transform: 'translate(0, 0) scale(1)' },
            { transform: 'translate(' + d.x + 'px, ' + d.y + 'px) scale(' + d.escala + ')', opacity: destino ? 1 : 0 }
          ],
          { duration: POUSO_MS, easing: SUAVE, fill: 'forwards' }
        );
        return voo.finished.catch(function () {}).then(function () {
          if (logoSistema) logoSistema.style.removeProperty('opacity');
          camadas.raiz.remove();
        });
      });
    });
  }

  function abrirNoLogin() {
    var camadas = criarCamadas();
    esperarElemento(SELETOR_BOTAO_LOGIN).then(function (botao) {
      var c = centroDe(botao ? botao.getBoundingClientRect() : null);
      var raio = raioAte(c);
      camadas.logo.animate([{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(0.92)' }], {
        duration: 220, easing: SUAVE, fill: 'forwards'
      });
      var fechar = camadas.cortina.animate(
        [{ clipPath: 'circle(' + raio + 'px at ' + c.x + 'px ' + c.y + 'px)' }, { clipPath: 'circle(0px at ' + c.x + 'px ' + c.y + 'px)' }],
        { duration: COBRIR_MS, easing: CIRCULO, fill: 'forwards' }
      );
      return fechar.finished.catch(function () {}).then(function () { camadas.raiz.remove(); });
    });
  }

  window.SisplanTransicaoLogin = { cobrir: cobrir, sair: sair };

  var etapa = suportado() ? lerMarca() : null;
  if (etapa === 'entrada' && script && script.hasAttribute('data-lado-sistema')) pousarNoSistema();
  if (etapa === 'saida' && script && script.hasAttribute('data-lado-login')) abrirNoLogin();
})();
