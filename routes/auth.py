from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import banco
from utils import usuario_logado

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def inicio():
    if not usuario_logado():
        return redirect(url_for('auth.pagina_login'))
    return redirect(url_for('pendente.aba_pendente'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def pagina_login():
    if usuario_logado():
        return redirect(url_for('auth.inicio'))

    erro = None
    if request.method == 'POST':
        usuario = banco.buscar_usuario_por_login(
            request.form.get('usuario', '').strip(),
            request.form.get('senha', '').strip(),
        )
        if usuario:
            session['usuario']           = usuario['usuario']
            session['nome']              = usuario['nome']
            session['nivel_acesso']      = usuario['nivel']
            session['tecnico_vinculado'] = usuario.get('tecnico_vinculado') or ''
            session['id_usuario']        = usuario['id']
            if usuario.get('mudar_senha'):
                return redirect(url_for('auth.trocar_senha'))
            return redirect(url_for('auth.inicio'))
        erro = 'Usuário ou senha incorretos.'

    return render_template('login.html', erro=erro)


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
        elif nova != confirma:
            erro = 'As senhas não coincidem.'
        else:
            id_u = session.get('id_usuario') or banco.buscar_id_usuario(session.get('usuario', ''))
            banco.alterar_minha_senha(id_u, nova)
            return redirect(url_for('auth.inicio'))
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
    banco.alterar_minha_senha(id_usuario, nova)
    return jsonify({'sucesso': True})


@auth_bp.route('/sair')
def sair():
    session.clear()
    return redirect(url_for('auth.pagina_login'))
