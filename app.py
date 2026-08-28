"""
app.py — Ponto de entrada do Sisplan.
"""

import os
import time
import datetime
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, session, redirect, url_for, g, render_template, request, jsonify
from flask_compress import Compress
import banco
from routes.auth        import auth_bp
from routes.pendente    import pendente_bp
from routes.homologados import homologados_bp
from routes.cancelados  import cancelados_bp
from routes.controle_os import controle_os_bp
from routes.conversor_certificado import conversor_certificado_bp
from routes.gerador_certificado_itau import gerador_certificado_itau_bp
from routes.home import home_bp
from routes.importacao  import importacao_bp
from routes.config      import config_bp
from routes.melhorias   import melhorias_bp
from routes.hub         import hub_bp
from routes.acesso      import acesso_bp
from routes.ajuda           import ajuda_bp
from routes.escritural      import escritural_bp
from routes.discord_notif       import discord_bp
from routes.email_escritural    import email_escritural_bp, iniciar_polling
from routes.logs                import logs_bp
from routes.email_modelos       import email_modelos_bp
from routes.sql_editor          import sql_editor_bp
from routes.sessoes             import sessoes_bp
from routes.notificacoes        import notificacoes_bp
from routes.credenciais         import credenciais_bp, iniciar_checker as iniciar_checker_credenciais
from routes.sla                 import sla_bp
from routes.usuarios            import usuarios_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sisplan-escritural-chave-secreta-2026')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)
app.config['COMPRESS_MIMETYPES'] = [
    'text/html', 'text/css', 'text/javascript',
    'application/javascript', 'application/json',
]
app.config['COMPRESS_MIN_SIZE'] = 1024
Compress(app)

# Serve static files via WhiteNoise (bypasses Python on Render/gunicorn)
try:
    from whitenoise import WhiteNoise
    app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'), prefix='static')
except ImportError:
    pass

# ── Caches em memória ──────────────────────────────────────
_MANUT_TTL   = 5   # segundos
_SESSAO_TTL  = 30  # segundos

_manut_cache  = {'val': None, 'ts': 0.0}
_sessao_cache: dict = {}  # jti -> {'info': dict|None, 'ts': float}


def _get_manutencao() -> str:
    now = time.monotonic()
    if now - _manut_cache['ts'] < _MANUT_TTL:
        return _manut_cache['val']
    v = banco.get_config('manutencao')
    _manut_cache['val'] = v
    _manut_cache['ts']  = now
    return v


def _invalidar_manutencao():
    _manut_cache['ts'] = 0.0


def _sessao_valida_cached(jti: str):
    now = time.monotonic()
    entry = _sessao_cache.get(jti)
    if entry and now - entry['ts'] < _SESSAO_TTL:
        return entry['info']
    info = banco.sessao_valida(jti)
    if info is not None:
        _sessao_cache[jti] = {'info': info, 'ts': now}
    else:
        _sessao_cache.pop(jti, None)
    return info

banco.inicializar_banco()
banco.migrar_pendentes_legados()
banco.migrar_senhas_plaintext()
banco.migrar_flags_avisos()
banco.migrar_hub_v2()
banco.migrar_sla()

app.register_blueprint(auth_bp)
app.register_blueprint(pendente_bp)
app.register_blueprint(homologados_bp)
app.register_blueprint(cancelados_bp)
app.register_blueprint(controle_os_bp)
app.register_blueprint(conversor_certificado_bp)
app.register_blueprint(gerador_certificado_itau_bp)
app.register_blueprint(home_bp)
app.register_blueprint(importacao_bp)
app.register_blueprint(config_bp)
app.register_blueprint(melhorias_bp)
app.register_blueprint(hub_bp)
app.register_blueprint(acesso_bp)
app.register_blueprint(ajuda_bp)
app.register_blueprint(escritural_bp)
app.register_blueprint(discord_bp)
app.register_blueprint(email_escritural_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(email_modelos_bp)
app.register_blueprint(sql_editor_bp)
app.register_blueprint(sessoes_bp)
app.register_blueprint(notificacoes_bp)
app.register_blueprint(credenciais_bp)
app.register_blueprint(sla_bp)
app.register_blueprint(usuarios_bp)

iniciar_polling()
iniciar_checker_credenciais()

_MANUT_BYPASS = {'static', None, 'auth.pagina_login', 'auth.sair',
                 'api_status_manutencao', 'api_toggle_manutencao'}

@app.before_request
def _modo_manutencao():
    from flask import request as req
    if req.endpoint in _MANUT_BYPASS:
        return
    if _get_manutencao() != '1':
        return
    if session.get('nivel_acesso') == 'master':
        return
    return render_template('manutencao.html'), 503


@app.route('/api/manutencao/status')
def api_status_manutencao():
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify({'ativo': banco.get_config('manutencao') == '1'})


@app.route('/api/manutencao', methods=['POST'])
def api_toggle_manutencao():
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json(silent=True, force=True) or {}
    novo = '1' if d.get('ativo') else '0'
    banco.set_config('manutencao', novo)
    _invalidar_manutencao()
    return jsonify({'sucesso': True, 'ativo': novo == '1'})

_ROTAS_PUBLICAS = {
    'auth.pagina_login', 'auth.sair', 'static',
    'escritural.formulario_publico', 'escritural.enviar_formulario_publico',
    'escritural.api_publico_bancos',
}

_ROTAS_TROCA_SENHA = {'auth.trocar_senha', 'auth.sair', 'static'}

@app.before_request
def _jwt_guard():
    from flask import request as req
    if req.endpoint in _ROTAS_PUBLICAS or req.endpoint is None:
        return

    from utils import _payload_access, _payload_refresh, _preencher_sessao, criar_tokens

    payload = _payload_access()
    if payload:
        jti = payload.get('jti')
        if jti:
            info = _sessao_valida_cached(jti)
            if info is None:
                # sessão foi encerrada (force logout)
                session.clear()
                if req.path.startswith('/api/'):
                    from flask import jsonify as _json
                    return _json({'erro': 'Sessão encerrada', 'redirect': '/login'}), 401
                return redirect(url_for('auth.pagina_login'))
            # sobrescreve mp/bg com valor real do banco (evita bypass via JWT antigo)
            payload = dict(payload)
            payload['mp'] = info.get('mudar_senha', payload.get('mp', 0))
            payload['bg'] = info.get('bloqueado_usuarios', payload.get('bg', 0))
        # só preenche session quando ainda não está populada
        if not session.get('usuario'):
            _preencher_sessao(payload)
        # telas não está no JWT — restaura do banco só quando a session foi perdida
        if not session.get('telas'):
            niv = payload.get('niv', '')
            try:
                uid = int(payload.get('sub', 0))
                session['telas'] = '__all__' if niv == 'master' else banco.listar_telas_usuario(uid)
            except (ValueError, TypeError):
                pass
        return

    # 2. Access expirado — tentar refresh token
    payload_r = _payload_refresh()
    if payload_r:
        jti = payload_r.get('jti')
        if jti and _sessao_valida_cached(jti) is None:
            session.clear()
            return redirect(url_for('auth.pagina_login'))
        u = banco.buscar_usuario_por_id(int(payload_r['sub']))
        if u:
            new_access, new_refresh, _ = criar_tokens(u, jti=jti)
            _preencher_sessao({
                'usr':  u['usuario'], 'nome': u['nome'],
                'niv':  u['nivel'],   'tec':  u.get('tecnico_vinculado') or '',
                'setor': u.get('setor') or '',
                'tema': u.get('tema') or 'light', 'sub': u['id'], 'mp': int(u.get('mudar_senha') or 0),
                'bg': int(u.get('bloqueado_usuarios') or 0),
                'tela_inicial': u.get('tela_inicial') or 'home',
            })
            session['cor']   = u.get('cor') or ''
            session['telas'] = '__all__' if u['nivel'] == 'master' else banco.listar_telas_usuario(u['id'])
            g._novo_access  = new_access
            g._novo_refresh = new_refresh
            return

    session.clear()
    return redirect(url_for('auth.pagina_login'))


@app.before_request
def _mudar_senha_guard():
    from flask import request as req
    if req.endpoint in _ROTAS_TROCA_SENHA or req.endpoint is None:
        return
    if session.get('mudar_senha'):
        return redirect(url_for('auth.trocar_senha'))


@app.after_request
def _set_token_cookies(response):
    if hasattr(g, '_novo_access'):
        opts = dict(httponly=True, samesite='Lax', path='/')
        response.set_cookie('access_token',  g._novo_access,  max_age=60*60,    **opts)
        response.set_cookie('refresh_token', g._novo_refresh, max_age=30*86400, **opts)
    return response


# ── Filtro de template ────────────────────────────────────

@app.template_filter('fmt_data')
def filtro_fmt_data(valor):
    """Converte ISO datetime ('2026-01-12 00:00:00') para 'dd/mm/yyyy'. Passa strings não-ISO intactas."""
    s = str(valor).strip() if valor else ''
    if len(s) >= 10 and s[4:5] == '-' and s[7:8] == '-':
        return f'{s[8:10]}/{s[5:7]}/{s[0:4]}'
    return s or '—'


@app.template_filter('css_status')
def filtro_css_status(status_texto):
    mapa = {
        'aguardando banco':        'status-aguardando-banco',
        'aguardando cliente':      'status-aguardando-cliente',
        'aguardando comercial':    'status-aguardando-comercial',
        'aguardando atualização':  'status-aguardando-atualizacao',
        'aguardando atualizacao':  'status-aguardando-atualizacao',
        'homologado':              'status-homologado',
        'falta cadastrar':         'status-falta-cadastrar',
        'pendente de treinamento': 'status-pendente-treinamento',
        'pendencia em prog':       'status-pendencia-em-prog',
        'em processo':             'status-em-processo',
        'cancelado':               'status-cancelado',
    }
    return mapa.get(str(status_texto).lower().strip(), 'status-padrao')


@app.context_processor
def injetar_globais():
    logado = 'usuario' in session
    nivel  = session.get('nivel_acesso', '')
    _pe    = logado and (nivel in ('admin', 'master') or bool(session.get('tecnico_vinculado')))
    telas  = session.get('telas') or []
    return {
        'nivel_acesso':  nivel,
        'nome_usuario':  session.get('nome', ''),
        'tema_usuario':  session.get('tema', 'light'),
        'cor_usuario':   session.get('cor', ''),
        'pode_editar':   _pe,
        'setor_usuario': session.get('setor', ''),
        'telas_acesso':  telas,
        'bloqueado_usuarios': bool(session.get('bloqueado_usuarios')),
    }


if __name__ == '__main__':
    app.run(debug=True, port=5000)
