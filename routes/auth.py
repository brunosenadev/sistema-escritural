from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, make_response
import banco
import sisplan_auth
from utils import usuario_logado, criar_tokens, tem_acesso_tela

auth_bp = Blueprint('auth', __name__)

_COOKIE_OPTS = dict(httponly=True, samesite='Lax', path='/')


def _set_tokens(response, usuario_row: dict, ip: str = '', registrar: bool = False):
    access, refresh, jti = criar_tokens(usuario_row)
    if registrar:
        banco.registrar_sessao(jti, usuario_row['id'], usuario_row.get('nome', ''), usuario_row.get('nivel', ''), ip)
    response.set_cookie('access_token',  access,  max_age=60*60,    **_COOKIE_OPTS)
    response.set_cookie('refresh_token', refresh, max_age=30*86400, **_COOKIE_OPTS)
    return response


_TELAS_ORDEM = [
    ('pendente',                 'pendente.aba_pendente',                  {}),
    ('homologados_cobranca',     'homologados.aba_homologados_cobranca',   {}),
    ('homologados_pagamentos',   'homologados.aba_homologados_pagamentos', {}),
    ('homologados_extrato',      'homologados.aba_homologados_extrato',    {}),
    ('homologados_ext_bancario', 'homologados.aba_homologados_ext_bancario', {}),
    ('cancelados',                'cancelados.aba_cancelados',  {}),
    ('melhorias',                 'melhorias.aba_melhorias',    {}),
    ('hub',                       'hub.aba_hub',                {}),
    ('acesso',                    'acesso.aba_acesso',          {}),
]

@auth_bp.route('/')
def inicio():
    if not usuario_logado():
        return redirect(url_for('auth.pagina_login'))
    tela_pref = session.get('tela_inicial') or 'home'
    if tela_pref != 'home':
        for chave, endpoint, kwargs in _TELAS_ORDEM:
            if chave == tela_pref and tem_acesso_tela(chave):
                return redirect(url_for(endpoint, **kwargs))
    return redirect(url_for('home.pagina_home'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def pagina_login():
    if usuario_logado():
        return redirect(url_for('auth.inicio'))

    erro = None
    if request.method == 'POST':
        usuario_digitado = request.form.get('usuario', '').strip()
        senha_digitada    = request.form.get('senha', '').strip()

        usuario     = None
        via_sisplan = False

        # 1) tenta validar direto na API do Sisplan com o que foi digitado
        if sisplan_auth.validar_login_sisplan(usuario_digitado, senha_digitada):
            usuario = banco.buscar_usuario_por_usuario_sisplan(usuario_digitado)
            if not usuario:
                banco.registrar_log(
                    usuario=usuario_digitado,
                    tela='Login', acao='LOGIN_FALHA',
                    descricao='Login validado no Sisplan, mas usuário sem vínculo no sistema',
                    ip=request.remote_addr,
                )
                return render_template(
                    'login.html',
                    erro='Usuário Sisplan não vinculado a nenhum usuário local do sistema.',
                    ano_atual=datetime.now().year,
                )
            via_sisplan = True

        # 2) se o Sisplan não validou (senha errada, indisponível, etc.),
        #    tenta como login local — mas só se essa conta não tiver um
        #    usuário Sisplan vinculado (nesse caso o login local fica bloqueado)
        if not usuario:
            id_local    = banco.buscar_id_usuario(usuario_digitado)
            conta_local = banco.buscar_usuario_por_id(id_local) if id_local else None
            if conta_local and (conta_local.get('usuario_sisplan') or '').strip():
                banco.registrar_log(
                    usuario=usuario_digitado,
                    tela='Login', acao='LOGIN_FALHA',
                    descricao='Tentativa de login local em conta vinculada ao Sisplan',
                    ip=request.remote_addr,
                )
                return render_template(
                    'login.html',
                    erro='Usuário Sisplan vinculado ao usuário local, favor usar usuário Sisplan pra fazer login.',
                    ano_atual=datetime.now().year,
                )
            usuario = banco.buscar_usuario_por_login(usuario_digitado, senha_digitada)

        if usuario:
            session.permanent            = True
            session['usuario']           = usuario['usuario']
            session['nome']              = usuario['nome']
            session['nivel_acesso']      = usuario['nivel']
            session['tecnico_vinculado'] = usuario.get('tecnico_vinculado') or ''
            session['id_usuario']        = usuario['id']
            session['tema']              = usuario.get('tema') or 'light'
            session['cor']               = usuario.get('cor') or ''
            session['tela_inicial']      = usuario.get('tela_inicial') or 'home'
            session['bloqueado_usuarios'] = int(usuario.get('bloqueado_usuarios') or 0)
            session['telas']             = '__all__' if usuario['nivel'] == 'master' else banco.listar_telas_usuario(usuario['id'])

            banco.registrar_log(
                usuario=usuario['nome'] or usuario['usuario'],
                tela='Login', acao='LOGIN',
                descricao='Entrou no sistema' + (' (via usuário Sisplan)' if via_sisplan else ''),
                usuario_id=usuario['id'],
                nivel=usuario['nivel'],
                ip=request.remote_addr,
            )

            destino = url_for('auth.trocar_senha') if usuario.get('mudar_senha') else url_for('auth.inicio')
            resp = make_response(redirect(destino))
            _set_tokens(resp, usuario, ip=request.remote_addr, registrar=True)
            return resp

        banco.registrar_log(
            usuario=usuario_digitado,
            tela='Login', acao='LOGIN_FALHA',
            descricao='Tentativa de login com credenciais inválidas',
            ip=request.remote_addr,
        )
        erro = 'Usuário ou senha incorretos.'

    return render_template('login.html', erro=erro, ano_atual=datetime.now().year)


@auth_bp.route('/trocar-senha', methods=['GET', 'POST'])
def trocar_senha():
    if not usuario_logado():
        return redirect(url_for('auth.pagina_login'))
    erro = None
    if request.method == 'POST':
        nova     = request.form.get('nova_senha', '').strip()
        confirma = request.form.get('confirma_senha', '').strip()
        if len(nova) < 6:
            erro = 'A senha deve ter pelo menos 6 caracteres.'
        elif nova == '123456':
            erro = 'Escolha uma senha diferente da senha padrão.'
        elif nova != confirma:
            erro = 'As senhas não coincidem.'
        else:
            id_u = session.get('id_usuario') or banco.buscar_id_usuario(session.get('usuario', ''))
            banco.alterar_minha_senha(id_u, nova)
            banco.registrar_log(
                usuario=session.get('nome') or session.get('usuario', ''),
                tela='Login', acao='SENHA',
                descricao='Alterou a própria senha',
                usuario_id=id_u,
                nivel=session.get('nivel_acesso', ''),
                ip=request.remote_addr,
            )
            u = banco.buscar_usuario_por_id(id_u)
            resp = make_response(redirect(url_for('auth.inicio')))
            _set_tokens(resp, u)
            return resp
    return render_template('trocar_senha.html', erro=erro)


@auth_bp.route('/api/minha-senha', methods=['PUT'])
def api_minha_senha():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_usuario = session.get('id_usuario')
    if not id_usuario:
        id_usuario = banco.buscar_id_usuario(session.get('usuario', ''))
        if not id_usuario:
            return jsonify({'erro': 'Sessão inválida, faça login novamente.'}), 401
        session['id_usuario'] = id_usuario
    d = request.get_json() or {}
    nova = d.get('nova_senha', '').strip()
    if len(nova) < 6:
        return jsonify({'erro': 'Senha deve ter pelo menos 6 caracteres.'}), 400
    if nova == '123456':
        return jsonify({'erro': 'Escolha uma senha diferente da senha padrão.'}), 400
    banco.alterar_minha_senha(id_usuario, nova)
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', ''),
        tela='Login', acao='SENHA',
        descricao='Alterou a própria senha',
        usuario_id=id_usuario,
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )
    return jsonify({'sucesso': True})


@auth_bp.route('/api/minha-cor', methods=['PUT'])
def api_minha_cor():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_usuario = session.get('id_usuario')
    if not id_usuario:
        return jsonify({'erro': 'Sessão inválida'}), 401
    d   = request.get_json() or {}
    cor = d.get('cor', '').strip()
    banco.atualizar_cor_usuario(id_usuario, cor)
    session['cor'] = cor
    return jsonify({'sucesso': True})


@auth_bp.route('/sair')
def sair():
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', ''),
        tela='Login', acao='LOGOUT',
        descricao='Saiu do sistema',
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )
    from utils import _payload_refresh
    payload_r = _payload_refresh()
    if payload_r and payload_r.get('jti'):
        banco.encerrar_sessao(payload_r['jti'])
    session.clear()
    resp = make_response(redirect(url_for('auth.pagina_login')))
    resp.delete_cookie('access_token',  path='/')
    resp.delete_cookie('refresh_token', path='/')
    return resp
