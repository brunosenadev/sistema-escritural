(function () {
  'use strict';

  var reduzido =
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var MODO_LEVE = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;

  var REFERENCIA_LARGURA = 1600;
  var REFERENCIA_ALTURA = 940;
  var ESCALA_MINIMA = 0.7;
  var escala = 1;

  function zoomNavegador() {
    if (!window.outerWidth || !window.innerWidth) return 1;
    var zoom = window.outerWidth / window.innerWidth;
    return zoom > 0.95 && zoom < 1.1 ? 1 : zoom;
  }

  function calcularEscala() {
    if (window.innerWidth < 1024) return 1;
    var zoom = zoomNavegador();
    var ajuste = Math.min(1, Math.max(ESCALA_MINIMA, Math.min(
      (window.innerWidth * zoom) / REFERENCIA_LARGURA,
      (window.innerHeight * zoom) / REFERENCIA_ALTURA
    )));
    return zoom < 1 ? ajuste / zoom : ajuste;
  }

  function atualizarEscala() {
    escala = calcularEscala();
    document.body.style.setProperty('--lp-escala', escala.toFixed(3));
  }

  var LOGO_LARGURA = 1124;
  var LOGO_ALTURA = 1178;
  var ESCALA_AMOSTRA = 0.25;
  var FRACAO_BORDA = 0.45;
  var COR_PARTICULA = 'rgb(214, 233, 255)';
  var cachePontos = {};

  function limitar(t) {
    return t < 0 ? 0 : t > 1 ? 1 : t;
  }

  function suavizar(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function prepararCanvas(canvas, largura, altura) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.round(largura * dpr));
    canvas.height = Math.max(1, Math.round(altura * dpr));
    var ctx = canvas.getContext('2d');
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return ctx;
  }

  function amostrarForma(chave, total, desenhar) {
    if (cachePontos[chave]) return cachePontos[chave];
    var largura = Math.ceil(LOGO_LARGURA * ESCALA_AMOSTRA);
    var altura = Math.ceil(LOGO_ALTURA * ESCALA_AMOSTRA);
    var pontos = new Float32Array(total * 2);
    var tela = document.createElement('canvas');
    tela.width = largura;
    tela.height = altura;
    var ctx = tela.getContext('2d', { willReadFrequently: true });
    var i;
    if (!ctx) {
      for (i = 0; i < total; i += 1) {
        pontos[i * 2] = Math.random() * LOGO_LARGURA;
        pontos[i * 2 + 1] = Math.random() * LOGO_ALTURA;
      }
      return pontos;
    }
    ctx.scale(ESCALA_AMOSTRA, ESCALA_AMOSTRA);
    ctx.fillStyle = '#fff';
    desenhar(ctx);

    var dados = ctx.getImageData(0, 0, largura, altura).data;
    function cheio(x, y) {
      return x >= 0 && y >= 0 && x < largura && y < altura && dados[(y * largura + x) * 4 + 3] > 127;
    }
    var borda = [];
    var interior = [];
    for (var y = 0; y < altura; y += 1) {
      for (var x = 0; x < largura; x += 1) {
        if (!cheio(x, y)) continue;
        var ehBorda = !cheio(x - 1, y) || !cheio(x + 1, y) || !cheio(x, y - 1) || !cheio(x, y + 1);
        (ehBorda ? borda : interior).push(y * largura + x);
      }
    }
    var totalBorda = Math.round(total * FRACAO_BORDA);
    for (i = 0; i < total; i += 1) {
      var fonte = (i < totalBorda && borda.length) || !interior.length ? borda : interior;
      var pixel = fonte.length ? fonte[Math.floor(Math.random() * fonte.length)] : 0;
      pontos[i * 2] = ((pixel % largura) + Math.random()) / ESCALA_AMOSTRA;
      pontos[i * 2 + 1] = (Math.floor(pixel / largura) + Math.random()) / ESCALA_AMOSTRA;
    }
    for (i = total - 1; i > 0; i -= 1) {
      var troca = Math.floor(Math.random() * (i + 1));
      var px = pontos[i * 2];
      var py = pontos[i * 2 + 1];
      pontos[i * 2] = pontos[troca * 2];
      pontos[i * 2 + 1] = pontos[troca * 2 + 1];
      pontos[troca * 2] = px;
      pontos[troca * 2 + 1] = py;
    }
    cachePontos[chave] = pontos;
    return pontos;
  }

  function pontosEsfera(total) {
    var pontos = new Float32Array(total * 3);
    var angulo = Math.PI * (3 - Math.sqrt(5));
    for (var i = 0; i < total; i += 1) {
      var y = 1 - (i / Math.max(total - 1, 1)) * 2;
      var raio = Math.sqrt(1 - y * y);
      var theta = angulo * i;
      pontos[i * 3] = Math.cos(theta) * raio;
      pontos[i * 3 + 1] = y;
      pontos[i * 3 + 2] = Math.sin(theta) * raio;
    }
    return pontos;
  }

  function desenharParticulas(ctx, posicoes, tamanhos, alfas, alfaGlobal) {
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = COR_PARTICULA;
    for (var i = 0; i < tamanhos.length; i += 1) {
      var alfa = alfas[i] * alfaGlobal;
      if (alfa <= 0.01) continue;
      var tamanho = tamanhos[i] * escala;
      ctx.globalAlpha = alfa > 1 ? 1 : alfa;
      ctx.fillRect(posicoes[i * 2] - tamanho / 2, posicoes[i * 2 + 1] - tamanho / 2, tamanho, tamanho);
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
  }

  function iniciarOrbes(painel) {
    var TOTAL = MODO_LEVE ? 22 : 46;
    var RAIO_ATRACAO = 230;
    var RAIO_LINHA = 170;
    var CORES = ['228,31,26', '150,110,215', '59,123,230', '139,188,255', '230,240,255'];
    var TAMANHO_SPRITE = 64;
    var NUCLEO = 0.3;

    var canvas = document.createElement('canvas');
    canvas.className = 'lp-fx-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    var luz = document.createElement('div');
    luz.className = 'lp-fx-luz';
    luz.setAttribute('aria-hidden', 'true');
    var grade = painel.querySelector('.lp-left-grid');
    painel.insertBefore(canvas, grade ? grade.nextSibling : painel.firstChild);
    painel.insertBefore(luz, canvas);
    var ctx = canvas.getContext('2d');
    if (!ctx) return;

    var sprites = CORES.map(function (cor) {
      var sprite = document.createElement('canvas');
      sprite.width = TAMANHO_SPRITE;
      sprite.height = TAMANHO_SPRITE;
      var c = sprite.getContext('2d');
      if (c) {
        var meio = TAMANHO_SPRITE / 2;
        var g = c.createRadialGradient(meio, meio, 0, meio, meio, meio);
        g.addColorStop(0, 'rgba(255,255,255,1)');
        g.addColorStop(NUCLEO * 0.45, 'rgba(' + cor + ',1)');
        g.addColorStop(NUCLEO, 'rgba(' + cor + ',1)');
        g.addColorStop(NUCLEO + 0.06, 'rgba(' + cor + ',0.42)');
        g.addColorStop(0.62, 'rgba(' + cor + ',0.1)');
        g.addColorStop(1, 'rgba(' + cor + ',0)');
        c.fillStyle = g;
        c.fillRect(0, 0, TAMANHO_SPRITE, TAMANHO_SPRITE);
      }
      return sprite;
    });

    var particulas = [];
    for (var i = 0; i < TOTAL; i += 1) {
      particulas.push({
        baseX: Math.random(),
        baseY: Math.random(),
        raio: 0.75 + Math.random() * 0.75,
        sprite: i % sprites.length,
        alfa: 0.7 + Math.random() * 0.3,
        fase: Math.random() * Math.PI * 2,
        velocidade: 0.00012 + Math.random() * 0.00018,
        amplitude: 16 + Math.random() * 30,
        orbita: 38 + Math.random() * 82,
        sentido: Math.random() < 0.5 ? -1 : 1,
        ox: 0, oy: 0, vx: 0, vy: 0
      });
    }
    var posicoes = new Float32Array(TOTAL * 2);
    var largura = 0;
    var altura = 0;
    var raf = 0;
    var mouse = { x: 0, y: 0, ativo: false };
    var luzPos = { x: 0, y: 0, alvoX: 0, alvoY: 0 };

    function desenhar(tempo) {
      ctx.clearRect(0, 0, largura, altura);
      particulas.forEach(function (p, index) {
        var deriva = tempo * p.velocidade + p.fase;
        var x = p.baseX * largura + Math.sin(deriva) * p.amplitude * escala;
        var y = p.baseY * altura + Math.cos(deriva * 0.8) * p.amplitude * 0.75 * escala;
        if (!reduzido) {
          var retorno = 0.012;
          if (mouse.ativo) {
            var dx = mouse.x - (x + p.ox);
            var dy = mouse.y - (y + p.oy);
            var distancia = Math.hypot(dx, dy) || 1;
            if (distancia < RAIO_ATRACAO * escala) {
              var peso = 1 - distancia / (RAIO_ATRACAO * escala);
              var radial = (distancia - p.orbita * escala) * 0.0045 * (0.4 + peso);
              var tangencial = 0.22 * peso * p.sentido * escala;
              p.vx += (dx / distancia) * radial + (-dy / distancia) * tangencial;
              p.vy += (dy / distancia) * radial + (dx / distancia) * tangencial;
              retorno = 0.0015;
            }
          }
          p.vx = (p.vx - p.ox * retorno) * 0.9;
          p.vy = (p.vy - p.oy * retorno) * 0.9;
          p.ox += p.vx;
          p.oy += p.vy;
        }
        posicoes[index * 2] = x + p.ox;
        posicoes[index * 2 + 1] = y + p.oy;
      });

      if (mouse.ativo && !reduzido) {
        ctx.lineWidth = 0.7 * escala;
        for (var j = 0; j < TOTAL; j += 1) {
          var px = posicoes[j * 2];
          var py = posicoes[j * 2 + 1];
          var d = Math.hypot(px - mouse.x, py - mouse.y);
          if (d >= RAIO_LINHA * escala) continue;
          ctx.strokeStyle = 'rgba(190,215,255,' + ((1 - d / (RAIO_LINHA * escala)) * 0.38).toFixed(3) + ')';
          ctx.beginPath();
          ctx.moveTo(mouse.x, mouse.y);
          ctx.lineTo(px, py);
          ctx.stroke();
        }
      }

      particulas.forEach(function (p, index) {
        var cintila = 0.85 + Math.sin(tempo * 0.0016 + p.fase) * 0.15;
        var tamanho = ((p.raio * 2) / NUCLEO) * escala;
        ctx.globalAlpha = p.alfa * cintila;
        ctx.drawImage(sprites[p.sprite], posicoes[index * 2] - tamanho / 2, posicoes[index * 2 + 1] - tamanho / 2, tamanho, tamanho);
      });
      ctx.globalAlpha = 1;
    }

    function quadro(tempo) {
      raf = 0;
      if (largura === 0 || document.hidden) return;
      luzPos.x += (luzPos.alvoX - luzPos.x) * 0.14;
      luzPos.y += (luzPos.alvoY - luzPos.y) * 0.14;
      luz.style.transform = 'translate3d(' + luzPos.x + 'px, ' + luzPos.y + 'px, 0)';
      desenhar(tempo);
      raf = window.requestAnimationFrame(quadro);
    }

    function iniciar() {
      if (reduzido) {
        desenhar(0);
        return;
      }
      if (!raf && largura > 0 && !document.hidden) raf = window.requestAnimationFrame(quadro);
    }

    function redimensionar() {
      var limites = painel.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      largura = limites.width;
      altura = limites.height;
      canvas.width = Math.round(largura * dpr);
      canvas.height = Math.round(altura * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (largura === 0 && raf) {
        window.cancelAnimationFrame(raf);
        raf = 0;
      } else {
        iniciar();
      }
    }

    painel.addEventListener('pointermove', function (event) {
      var limites = painel.getBoundingClientRect();
      mouse.x = event.clientX - limites.left;
      mouse.y = event.clientY - limites.top;
      luzPos.alvoX = mouse.x;
      luzPos.alvoY = mouse.y;
      if (!mouse.ativo) {
        luzPos.x = mouse.x;
        luzPos.y = mouse.y;
        mouse.ativo = true;
        luz.dataset.ativa = 'true';
      }
    }, { passive: true });
    painel.addEventListener('pointerleave', function () {
      mouse.ativo = false;
      luz.dataset.ativa = 'false';
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        if (raf) window.cancelAnimationFrame(raf);
        raf = 0;
      } else {
        iniciar();
      }
    });
    if (typeof ResizeObserver === 'function') new ResizeObserver(redimensionar).observe(painel);
    redimensionar();
  }

  function iniciarLogoParticulas(painel) {
    var alvo = painel.querySelector('.lp-left-svg-wrap');
    var svg = alvo && alvo.querySelector('svg');
    var area = svg && svg.querySelector(':scope > g[fill]');
    if (!alvo || !svg || !area) return;
    area.classList.add('lp-logo-hit');

    var caminhos = Array.prototype.map.call(area.querySelectorAll('path'), function (path) {
      return path.getAttribute('d');
    });

    var FORMA = MODO_LEVE ? 1300 : 2400;
    var ORBE = MODO_LEVE ? 350 : 700;
    var TOTAL = FORMA + ORBE;
    var DURACAO_MORFO_MS = 1050;
    var ATRASO_MAX_MORFO_MS = 300;
    var PAUSA_TEXTO_MS = 1100;
    var INICIO_MORFO_CLIQUE_MS = DURACAO_MORFO_MS + ATRASO_MAX_MORFO_MS + PAUSA_TEXTO_MS;
    var SAIDA_MS = 420;
    var LIMITE_RETORNO_MS = 2600;
    var LIMIAR_ARRASTO_PX = 6;
    var ARRASTO_TEXTO_PX = 140;

    function desenharLogo(ctx) {
      caminhos.forEach(function (d) {
        ctx.fill(new Path2D(d), 'evenodd');
      });
    }

    function desenharTexto(ctx) {
      var familia = 'Inter, "Segoe UI", Arial, sans-serif';
      var larguraUtil = LOGO_LARGURA * 0.94;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = '800 100px ' + familia;
      var tamanhoNome = Math.min(330, (larguraUtil / ctx.measureText('ESCRITURAL').width) * 100);
      var tamanhoWeb = tamanhoNome * 0.82;
      ctx.font = '800 ' + tamanhoNome + 'px ' + familia;
      ctx.fillText('ESCRITURAL',LOGO_LARGURA / 2, LOGO_ALTURA / 2 - tamanhoWeb * 0.5);
      ctx.font = '800 ' + tamanhoWeb + 'px ' + familia;
      ctx.fillText('WEB', LOGO_LARGURA / 2, LOGO_ALTURA / 2 + tamanhoNome * 0.62);
    }

    var canvas = document.createElement('canvas');
    canvas.className = 'lp-fx-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    painel.insertBefore(canvas, alvo);

    var logoForma = amostrarForma('logo-' + FORMA, FORMA, desenharLogo);
    var logoOrbe = amostrarForma('logo-' + ORBE, ORBE, desenharLogo);
    var texto = amostrarForma('texto-' + FORMA, FORMA, desenharTexto);
    var esfera = pontosEsfera(ORBE);

    var posicoes = new Float32Array(TOTAL * 2);
    var casas = new Float32Array(FORMA * 2);
    var casasTexto = new Float32Array(FORMA * 2);
    var velocidades = new Float32Array(FORMA * 2);
    var tamanhos = new Float32Array(TOTAL);
    var alfas = new Float32Array(TOTAL);
    var alfaLogo = new Float32Array(TOTAL);
    var alfaTexto = new Float32Array(TOTAL);
    var atrasos = new Float32Array(TOTAL);
    for (var i = 0; i < TOTAL; i += 1) {
      tamanhos[i] = i < FORMA ? 1.2 + Math.random() * 1.1 : 0.9 + Math.random() * 1.1;
      alfaLogo[i] = 0.3 + Math.random() * 0.4;
      alfaTexto[i] = 0.75 + Math.random() * 0.25;
      atrasos[i] = Math.random() * ATRASO_MAX_MORFO_MS;
    }

    var ctx = null;
    var largura = 0;
    var altura = 0;
    var raf = 0;
    var modo = 'parado';
    var deLogo = false;
    var inicio = 0;
    var anterior = 0;
    var inicioSaida = 0;
    var inicioVisivel = 0;
    var segurando = false;
    var pressionado = false;
    var pressaoX = 0;
    var pressaoY = 0;
    var arrastoX = 0;
    var arrastoY = 0;

    function medirLogo() {
      var lc = canvas.getBoundingClientRect();
      var ll = svg.getBoundingClientRect();
      return { x: ll.left - lc.left, y: ll.top - lc.top, largura: ll.width, altura: ll.height };
    }

    function prepararTela() {
      var limites = canvas.getBoundingClientRect();
      if (limites.width === 0 || svg.getBoundingClientRect().width === 0) return false;
      if (limites.width !== largura || limites.height !== altura || !ctx) {
        largura = limites.width;
        altura = limites.height;
        ctx = prepararCanvas(canvas, largura, altura);
      }
      return Boolean(ctx);
    }

    function atualizarCasas() {
      var logo = medirLogo();
      var ex = logo.largura / LOGO_LARGURA;
      var ey = logo.altura / LOGO_ALTURA;
      for (var k = 0; k < FORMA * 2; k += 2) {
        casas[k] = logo.x + logoForma[k] * ex;
        casas[k + 1] = logo.y + logoForma[k + 1] * ey;
        casasTexto[k] = logo.x + texto[k] * ex;
        casasTexto[k + 1] = logo.y + texto[k + 1] * ey;
      }
      return logo;
    }

    function encerrar() {
      if (raf) window.cancelAnimationFrame(raf);
      raf = 0;
      modo = 'parado';
      inicioSaida = 0;
      if (ctx) ctx.clearRect(0, 0, largura, altura);
    }

    function iniciarSaida(agora) {
      if (inicioSaida) return;
      inicioSaida = agora;
      alvo.dataset.espalhada = 'false';
    }

    function quadroSequencia(t, agora) {
      var logo = atualizarCasas();
      var exLogo = logo.largura / LOGO_LARGURA;
      var eyLogo = logo.altura / LOGO_ALTURA;
      var escalaTexto = (logo.largura * 0.58) / LOGO_LARGURA;
      var raio = logo.largura * 0.36;
      var extensao = raio * 1.34 + 24;
      var logoCentroX = logo.x + logo.largura / 2;
      var logoCentroY = logo.y + logo.altura / 2;
      var centroX = Math.max(extensao, Math.min(largura - extensao, logoCentroX));
      var centroY = Math.max(extensao, Math.min(altura - extensao, logoCentroY));
      var giro = agora * 0.0011;
      var cosGiro = Math.cos(giro);
      var senGiro = Math.sin(giro);
      var cosInc = Math.cos(0.38);
      var senInc = Math.sin(0.38);
      var inicioMorfo = deLogo ? INICIO_MORFO_CLIQUE_MS : PAUSA_TEXTO_MS;

      for (var index = 0; index < TOTAL; index += 1) {
        var ix = index * 2;
        var iy = ix + 1;
        var formadoX, formadoY, alfaFormado, logoX, logoY;
        if (index < FORMA) {
          formadoX = centroX + (texto[ix] - LOGO_LARGURA / 2) * escalaTexto;
          formadoY = centroY + (texto[iy] - LOGO_ALTURA / 2) * escalaTexto;
          alfaFormado = alfaTexto[index];
          logoX = casas[ix];
          logoY = casas[iy];
        } else {
          var io = index - FORMA;
          var ex = esfera[io * 3];
          var ey = esfera[io * 3 + 1];
          var ez = esfera[io * 3 + 2];
          var x = ex * cosGiro + ez * senGiro;
          var z1 = -ex * senGiro + ez * cosGiro;
          var y = ey * cosInc - z1 * senInc;
          var z = ey * senInc + z1 * cosInc;
          var perspectiva = 4 / (4 - z);
          formadoX = centroX + x * raio * perspectiva;
          formadoY = centroY + y * raio * perspectiva;
          var borda = 1 - Math.abs(z);
          alfaFormado = (0.16 + 0.84 * borda * borda) * (z > 0 ? 0.85 : 0.5);
          logoX = logo.x + logoOrbe[io * 2] * exLogo;
          logoY = logo.y + logoOrbe[io * 2 + 1] * eyLogo;
        }

        var k = t < inicioMorfo
          ? (deLogo ? 1 - suavizar(limitar((t - atrasos[index]) / DURACAO_MORFO_MS)) : 0)
          : suavizar(limitar((t - inicioMorfo - atrasos[index]) / DURACAO_MORFO_MS));
        var angulo = k * Math.PI * 1.5;
        var cosAng = Math.cos(angulo);
        var senAng = Math.sin(angulo);
        var relX = formadoX - centroX;
        var relY = formadoY - centroY;
        var giradoX = centroX + relX * cosAng - relY * senAng + (logoCentroX - centroX) * k;
        var giradoY = centroY + relX * senAng + relY * cosAng + (logoCentroY - centroY) * k;

        posicoes[ix] = giradoX + (logoX - giradoX) * k * k;
        posicoes[iy] = giradoY + (logoY - giradoY) * k * k;
        alfas[index] = alfaFormado + (alfaLogo[index] - alfaFormado) * k;
      }
    }

    function quadroFisica(passo, decorrido, agora) {
      var mistura = modo === 'arrasto' ? Math.min(Math.abs(arrastoX) / ARRASTO_TEXTO_PX, 1) : 0;
      var limiteX = largura * 0.12;
      var deslocX = modo === 'arrasto' ? Math.max(-limiteX, Math.min(limiteX, arrastoX * 0.55)) : 0;
      var deslocY = modo === 'arrasto' ? Math.max(-40, Math.min(40, arrastoY * 0.25)) : 0;
      var mola = modo === 'arrasto' ? 0.09 : 0.045;
      var atrito = Math.pow(modo === 'arrasto' ? 0.8 : 0.86, passo);
      var maiorDistancia = 0;
      for (var index = 0; index < FORMA; index += 1) {
        var ix = index * 2;
        var iy = ix + 1;
        var destinoX = casas[ix] + (casasTexto[ix] - casas[ix]) * mistura + deslocX;
        var destinoY = casas[iy] + (casasTexto[iy] - casas[iy]) * mistura + deslocY;
        velocidades[ix] += (destinoX - posicoes[ix]) * mola * passo;
        velocidades[iy] += (destinoY - posicoes[iy]) * mola * passo;
        velocidades[ix] *= atrito;
        velocidades[iy] *= atrito;
        posicoes[ix] += velocidades[ix] * passo;
        posicoes[iy] += velocidades[iy] * passo;
        alfas[index] = alfaLogo[index] + (alfaTexto[index] - alfaLogo[index]) * mistura;
        var distancia = Math.abs(casas[ix] - posicoes[ix]) + Math.abs(casas[iy] - posicoes[iy]);
        if (distancia > maiorDistancia) maiorDistancia = distancia;
      }
      for (var o = FORMA; o < TOTAL; o += 1) alfas[o] = 0;
      if (modo === 'retorno' && (maiorDistancia < 1.2 || decorrido > LIMITE_RETORNO_MS)) iniciarSaida(agora);
    }

    function quadro(agora) {
      raf = 0;
      if (!ctx || modo === 'parado') return;
      if (svg.getBoundingClientRect().width === 0) {
        encerrar();
        alvo.dataset.espalhada = 'false';
        return;
      }
      var passo = Math.min((agora - anterior) / 16.67, 3);
      anterior = agora;
      if (segurando) inicio = agora;
      var decorrido = agora - inicio;
      if (modo === 'sequencia') {
        quadroSequencia(decorrido, agora);
        var inicioMorfo = deLogo ? INICIO_MORFO_CLIQUE_MS : PAUSA_TEXTO_MS;
        if (decorrido >= inicioMorfo + DURACAO_MORFO_MS + ATRASO_MAX_MORFO_MS) iniciarSaida(agora);
      } else {
        quadroFisica(passo, decorrido, agora);
      }
      var alfaGlobal = inicioSaida ? 1 - Math.min((agora - inicioSaida) / SAIDA_MS, 1) : 1;
      if (alfaGlobal <= 0) {
        encerrar();
        return;
      }
      if (inicioVisivel) alfaGlobal *= Math.min((agora - inicioVisivel) / 260, 1);
      ctx.clearRect(0, 0, largura, altura);
      desenharParticulas(ctx, posicoes, tamanhos, alfas, alfaGlobal);
      raf = window.requestAnimationFrame(quadro);
    }

    function animar(novoModo) {
      modo = novoModo;
      inicioSaida = 0;
      inicio = performance.now();
      anterior = inicio;
      if (!raf) raf = window.requestAnimationFrame(quadro);
    }

    function iniciarSequencia(partindoDaLogo) {
      if (!prepararTela()) return;
      deLogo = partindoDaLogo;
      alvo.dataset.espalhada = 'true';
      animar('sequencia');
    }

    function iniciarArrasto() {
      if (!prepararTela()) return;
      atualizarCasas();
      if (modo === 'parado') {
        posicoes.set(casas);
        velocidades.fill(0);
      }
      alvo.dataset.espalhada = 'true';
      animar('arrasto');
    }

    function aoMover(event) {
      if (!pressionado) return;
      arrastoX = event.clientX - pressaoX;
      arrastoY = event.clientY - pressaoY;
      if (modo !== 'arrasto' && Math.hypot(arrastoX, arrastoY) > LIMIAR_ARRASTO_PX) iniciarArrasto();
    }

    function aoSoltar(event) {
      if (!pressionado) return;
      pressionado = false;
      window.removeEventListener('pointermove', aoMover);
      window.removeEventListener('pointerup', aoSoltar);
      window.removeEventListener('pointercancel', aoSoltar);
      if (modo === 'arrasto') {
        arrastoX = 0;
        arrastoY = 0;
        modo = 'retorno';
        inicio = performance.now();
        return;
      }
      if (event.type === 'pointerup') iniciarSequencia(true);
    }

    area.addEventListener('pointerdown', function (event) {
      if (event.button !== 0 || pressionado || modo === 'sequencia') return;
      event.preventDefault();
      pressionado = true;
      pressaoX = event.clientX;
      pressaoY = event.clientY;
      arrastoX = 0;
      arrastoY = 0;
      window.addEventListener('pointermove', aoMover);
      window.addEventListener('pointerup', aoSoltar);
      window.addEventListener('pointercancel', aoSoltar);
    });

    alvo.dataset.espalhada = 'true';
    var fonte = document.fonts && document.fonts.load ? document.fonts.load('800 100px Inter') : Promise.resolve();
    Promise.race([fonte, new Promise(function (r) { setTimeout(r, 250); })]).then(function () {
      delete cachePontos['texto-' + FORMA];
      texto = amostrarForma('texto-' + FORMA, FORMA, desenharTexto);
      segurando = true;
      inicioVisivel = performance.now();
      iniciarSequencia(false);
      if (modo !== 'sequencia') {
        segurando = false;
        alvo.dataset.espalhada = 'false';
        return;
      }
      esperarCarregamento().then(function () {
        segurando = false;
      });
    });
  }

  function esperarCarregamento() {
    var comeco = Date.now();
    var visto = false;
    var livres = 0;
    return new Promise(function (resolve) {
      (function verificar() {
        var loader = document.querySelector('.sisplan-loader');
        var visivel = Boolean(loader && loader.getBoundingClientRect().width > 0);
        if (visivel) visto = true;
        livres = visivel ? 0 : livres + 1;
        var decorrido = Date.now() - comeco;
        if ((visto && livres >= 3) || (!visto && decorrido > 150) || decorrido > 8000) return resolve();
        setTimeout(verificar, 80);
      })();
    });
  }

  function iniciarBrilhos() {
    var pendente = null;
    var raf = 0;
    var wrapper = document.querySelector('.lp-wrapper');

    document.addEventListener('pointermove', function (event) {
      var el = event.target instanceof Element ? event.target.closest('.lp-input-wrap') : null;
      if (el) {
        var l = el.getBoundingClientRect();
        pendente = { el: el, x: (event.clientX - l.left) / escala, y: (event.clientY - l.top) / escala };
      }
      if (wrapper && wrapper.contains(event.target)) {
        var lw = wrapper.getBoundingClientRect();
        wrapper.style.setProperty('--lp-px', (event.clientX - lw.left) / escala + 'px');
        wrapper.style.setProperty('--lp-py', (event.clientY - lw.top) / escala + wrapper.scrollTop + 'px');
      }
      if (pendente && !raf) {
        raf = window.requestAnimationFrame(function () {
          raf = 0;
          if (!pendente) return;
          pendente.el.style.setProperty('--lp-gx', pendente.x + 'px');
          pendente.el.style.setProperty('--lp-gy', pendente.y + 'px');
          pendente = null;
        });
      }
    }, { passive: true });

    document.addEventListener('pointerdown', function (event) {
      if (reduzido) return;
      var anel = document.createElement('span');
      anel.className = 'lp-clique';
      anel.setAttribute('aria-hidden', 'true');
      anel.style.left = event.clientX + 'px';
      anel.style.top = event.clientY + 'px';
      anel.addEventListener('animationend', function () { anel.remove(); }, { once: true });
      document.body.appendChild(anel);

      var botao = event.target instanceof Element ? event.target.closest('.lp-btn-enter') : null;
      if (!botao || botao.disabled) return;
      var lb = botao.getBoundingClientRect();
      var diametro = (Math.max(lb.width, lb.height) * 0.9) / escala;
      var onda = document.createElement('span');
      onda.className = 'lp-ripple';
      onda.setAttribute('aria-hidden', 'true');
      onda.style.width = diametro + 'px';
      onda.style.height = diametro + 'px';
      onda.style.left = (event.clientX - lb.left) / escala - diametro / 2 + 'px';
      onda.style.top = (event.clientY - lb.top) / escala - diametro / 2 + 'px';
      onda.addEventListener('animationend', function () { onda.remove(); }, { once: true });
      botao.appendChild(onda);
    });
  }

  var envio = { ativo: false, entrando: false, overlayOriginal: null };

  function botaoEntrar() {
    return document.querySelector('.lp-btn-enter');
  }

  function silenciarOverlay() {
    var $ = window.jQuery;
    if (!$ || typeof $.LoadingOverlay !== 'function' || envio.overlayOriginal) return;
    envio.overlayOriginal = $.LoadingOverlay;
    $.LoadingOverlay = function (acao) {
      if (acao === 'show') return undefined;
      return envio.overlayOriginal.apply(this, arguments);
    };
    envio.overlayOriginal('hide', true);
  }

  function restaurarOverlay() {
    var $ = window.jQuery;
    if ($ && envio.overlayOriginal) $.LoadingOverlay = envio.overlayOriginal;
    envio.overlayOriginal = null;
  }

  function tremer() {
    if (reduzido) return;
    var alvos = [document.querySelector('.lp-form-fields'), botaoEntrar()];
    alvos.forEach(function (alvo) {
      if (!alvo || typeof alvo.animate !== 'function') return;
      alvo.animate(
        [
          { transform: 'translateX(0)' },
          { transform: 'translateX(-10px)' },
          { transform: 'translateX(10px)' },
          { transform: 'translateX(-10px)' },
          { transform: 'translateX(10px)' },
          { transform: 'translateX(0)' }
        ],
        { duration: 400, easing: 'ease-in-out' }
      );
    });
  }

  function modalAberto() {
    return Boolean(document.querySelector('.modal.show'));
  }

  window.LoginFx = {
    iniciarEnvio: function () {
      if (envio.ativo) return false;
      envio.ativo = true;
      envio.entrando = false;
      var botao = botaoEntrar();
      if (botao) {
        botao.classList.add('lp-btn-carregando');
        botao.setAttribute('aria-busy', 'true');
      }
      silenciarOverlay();
      return true;
    },
    marcarEntrando: function () {
      envio.entrando = true;
    },
    concluirEnvio: function (falhou) {
      if (!envio.ativo || envio.entrando) return;
      envio.ativo = false;
      restaurarOverlay();
      var botao = botaoEntrar();
      if (botao) {
        botao.classList.remove('lp-btn-carregando');
        botao.removeAttribute('aria-busy');
      }
      window.setTimeout(function () {
        if (falhou || modalAberto()) tremer();
      }, 60);
    }
  };

  function iniciarTitulo() {
    var titulo = document.querySelector('.lp-left-h2');
    if (!titulo || titulo.querySelector('.lp-titulo-brilho')) return;
    var brilho = document.createElement('span');
    brilho.className = 'lp-titulo-brilho';
    while (titulo.firstChild) brilho.appendChild(titulo.firstChild);
    titulo.appendChild(brilho);
  }

  function formatarEmpresa(estado) {
    if (!estado.id || !estado.element || !window.jQuery) return estado.text;
    var opcao = window.jQuery(estado.element);
    var fantasia = (opcao.attr('title') || '').trim();
    var nome = opcao.attr('data-nome') || estado.text;
    var bloco = window.jQuery('<span class="lp-empresa"></span>');
    bloco.append(window.jQuery('<span class="lp-empresa__nome"></span>').text(nome));
    if (fantasia) bloco.append(window.jQuery('<small class="lp-empresa__fantasia"></small>').text(fantasia));
    return bloco;
  }

  window.LoginFx.formatarEmpresa = formatarEmpresa;

  function iniciar() {
    document.body.classList.add('lp-fx');
    atualizarEscala();
    window.addEventListener('resize', atualizarEscala);
    iniciarTitulo();
    iniciarBrilhos();
    var painel = document.querySelector('.lp-left-panel');
    if (!painel) return;
    iniciarOrbes(painel);
    if (!reduzido) iniciarLogoParticulas(painel);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
