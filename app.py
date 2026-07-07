"""
app.py — Ponto de entrada do Sisplan.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, session, redirect, url_for, g
import banco
from routes.auth        import auth_bp
from routes.pendente    import pendente_bp
from routes.homologados import homologados_bp
from routes.cancelados  import cancelados_bp
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

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sisplan-escritural-chave-secreta-2026')

banco.inicializar_banco()
banco.migrar_pendentes_legados()
banco.migrar_senhas_plaintext()
banco.migrar_flags_avisos()

app.register_blueprint(auth_bp)
app.register_blueprint(pendente_bp)
app.register_blueprint(homologados_bp)
app.register_blueprint(cancelados_bp)
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

iniciar_polling()

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
            info = banco.sessao_valida(jti)
            if info is None:
                # sessão foi encerrada (force logout)
                session.clear()
                from flask import request as req
                if req.path.startswith('/api/'):
                    from flask import jsonify as _json
                    return _json({'erro': 'Sessão encerrada', 'redirect': '/login'}), 401
                return redirect(url_for('auth.pagina_login'))
            # sobrescreve mp com valor real do banco (evita bypass via JWT antigo)
            payload = dict(payload)
            payload['mp'] = info.get('mudar_senha', payload.get('mp', 0))
        _preencher_sessao(payload)
        return

    # 2. Access expirado — tentar refresh token
    payload_r = _payload_refresh()
    if payload_r:
        jti = payload_r.get('jti')
        if jti and not banco.sessao_valida(jti):
            session.clear()
            return redirect(url_for('auth.pagina_login'))
        u = banco.buscar_usuario_por_id(payload_r['sub'])
        if u:
            new_access, new_refresh, _ = criar_tokens(u, jti=jti)
            _preencher_sessao({
                'usr':  u['usuario'], 'nome': u['nome'],
                'niv':  u['nivel'],   'tec':  u.get('tecnico_vinculado') or '',
                'setor': u.get('setor') or '',
                'tema': u.get('tema') or 'light', 'sub': u['id'], 'mp': int(u.get('mudar_senha') or 0),
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
        response.set_cookie('access_token',  g._novo_access,  max_age=15*60,    **opts)
        response.set_cookie('refresh_token', g._novo_refresh, max_age=7*86400,  **opts)
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
    }


if __name__ == '__main__':
    app.run(debug=True, port=5000)
