from flask import Blueprint, render_template, request, jsonify, session, make_response, current_app
import banco
import os
import uuid
from utils import checar_master, checar_login, usuario_logado, criar_tokens, _preencher_sessao, tem_acesso_tela, _payload_access
from flask import redirect, url_for

usuarios_bp = Blueprint('usuarios', __name__)

_EXTENSOES_IMAGEM = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
_RE_LOGIN_SEGURO  = __import__('re').compile(r'[^A-Za-z0-9_\-]')


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Usuários', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


def _eh_master():
    return session.get('nivel_acesso') == 'master'


def _pode_gerir():
    """Master sempre pode, a não ser que tenha o acesso à gestão de usuários
    explicitamente bloqueado por outro master. Admin com tela 'usuarios'
    também pode (exceto ações sobre masters)."""
    if session.get('nivel_acesso') == 'master':
        return not session.get('bloqueado_usuarios')
    return session.get('nivel_acesso') == 'admin' and tem_acesso_tela('usuarios')


@usuarios_bp.route('/usuarios')
def pagina_usuarios():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio
    if session.get('nivel_acesso') == 'master':
        if session.get('bloqueado_usuarios'):
            return redirect(url_for('auth.inicio'))
    elif not tem_acesso_tela('usuarios'):
        return redirect(url_for('auth.inicio'))
    return render_template(
        'gerenciar_usuarios.html',
        usuarios=banco.listar_usuarios(),
        tecnicos=banco.listar_tecnicos(),
        lista_setores=banco.listar_setores(),
    )


# ── API Usuários (somente master) ─────────────────────────

@usuarios_bp.route('/api/usuarios', methods=['POST'])
def api_adicionar_usuario():
    if not _pode_gerir():
        return jsonify({'erro': 'Sem permissão'}), 403
    d  = request.get_json()
    # Admins (não-master) não podem criar usuários master
    if not _eh_master() and (d.get('nivel') or '') == 'master':
        d['nivel'] = 'admin'
    ok = banco.adicionar_usuario(d)
    if ok:
        _log('INSERIU', f'Criou usuário: {d.get("usuario","")} ({d.get("nome","")})')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Login já cadastrado.'}), 409)


@usuarios_bp.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
def api_atualizar_usuario(id_usuario):
    if not _pode_gerir():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo  = banco.buscar_usuario_por_id(id_usuario)
    # Admins (não-master) não podem editar usuários master
    if not _eh_master() and alvo and alvo.get('nivel') == 'master':
        return jsonify({'erro': 'Sem permissão para editar usuário master'}), 403
    dados = request.get_json()
    if alvo and alvo.get('nivel') == 'master':
        dados['nivel'] = 'master'
    # Admins não podem elevar nível para master
    if not _eh_master() and (dados.get('nivel') or '') == 'master':
        dados['nivel'] = 'admin'
    nivel_mudou = bool(alvo) and (dados.get('nivel') or '') != (alvo.get('nivel') or '')
    banco.atualizar_usuario(id_usuario, dados)
    _log('EDITOU', f'Editou usuário #{id_usuario} — {alvo.get("nome","") if alvo else "?"}')
    if id_usuario != session.get('id_usuario') and nivel_mudou:
        # Mudou o nível de outra pessoa — a sessão dela não se autoatualiza,
        # força relogin pra já valer com o nível novo.
        banco.encerrar_sessoes_usuario(id_usuario)
    if id_usuario == session.get('id_usuario'):
        u = banco.buscar_usuario_por_id(id_usuario)
        _preencher_sessao({
            'usr': u['usuario'], 'nome': u['nome'], 'niv': u['nivel'],
            'tec': u.get('tecnico_vinculado') or '', 'tema': u.get('tema') or 'light',
            'sub': u['id'], 'mp': int(u.get('mudar_senha') or 0),
            'bg': int(u.get('bloqueado_usuarios') or 0),
            'cor': u.get('cor') or '', 'setor': u.get('setor') or '',
            'tela_inicial': u.get('tela_inicial') or 'home',
        })
        jti_atual = (_payload_access() or {}).get('jti')
        access, *_ = criar_tokens(u, jti=jti_atual)
        resp = make_response(jsonify({'sucesso': True}))
        resp.set_cookie('access_token', access, max_age=60*60, httponly=True, samesite='Lax', path='/')
        return resp
    return jsonify({'sucesso': True})


@usuarios_bp.route('/api/usuarios/<int:id_usuario>/resetar-senha', methods=['POST'])
def api_resetar_senha(id_usuario):
    if not _pode_gerir():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if not _eh_master() and alvo and alvo.get('nivel') == 'master':
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.resetar_senha_usuario(id_usuario)
    _log('SENHA', f'Resetou senha do usuário #{id_usuario} — {alvo.get("nome","") if alvo else "?"}')
    return jsonify({'sucesso': True})


@usuarios_bp.route('/api/usuarios/<int:id_usuario>/bloqueio-gestao', methods=['POST'])
def api_bloqueio_gestao(id_usuario):
    """Só um master (de verdade, não bloqueado) pode bloquear/liberar OUTRO
    master no acesso ao Cadastro de Usuários. Não existe pra admin."""
    if not _eh_master() or session.get('bloqueado_usuarios'):
        return jsonify({'erro': 'Sem permissão'}), 403
    try:
        id_proprio = int(session.get('id_usuario') or 0)
    except (TypeError, ValueError):
        id_proprio = 0
    if id_usuario == id_proprio:
        return jsonify({'erro': 'Não é possível bloquear a si mesmo.'}), 400
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if not alvo or alvo.get('nivel') != 'master':
        return jsonify({'erro': 'Só é possível bloquear/liberar outro usuário master.'}), 400
    bloqueado = bool((request.get_json() or {}).get('bloqueado'))
    banco.definir_bloqueio_usuarios(id_usuario, bloqueado)
    banco.encerrar_sessoes_usuario(id_usuario)
    verbo = 'Bloqueou' if bloqueado else 'Liberou'
    _log('BLOQUEIO_GESTAO', f'{verbo} acesso de {alvo.get("nome","")} ao Cadastro de Usuários')
    return jsonify({'sucesso': True})


@usuarios_bp.route('/api/usuarios/<int:id_usuario>/limpar-troca', methods=['POST'])
def api_limpar_troca(id_usuario):
    if not _pode_gerir():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.limpar_mudar_senha(id_usuario)
    return jsonify({'sucesso': True})


@usuarios_bp.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
def api_remover_usuario(id_usuario):
    if not _pode_gerir():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if alvo and alvo.get('nivel') == 'master':
        return jsonify({'erro': 'Usuário master não pode ser removido.'}), 403
    ok = banco.remover_usuario(id_usuario)
    if ok:
        _log('DELETOU', f'Removeu usuário #{id_usuario} — {alvo.get("nome","") if alvo else "?"}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Não é possível remover o único administrador.'}), 400)


@usuarios_bp.route('/api/upload-assinatura', methods=['POST'])
def api_upload_assinatura():
    if not _pode_gerir():
        return jsonify({'erro': 'Sem permissão'}), 403
    arquivo    = request.files.get('imagem')
    usuario_id = request.form.get('usuario_id', '').strip()
    if not arquivo or not arquivo.filename:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    ext = arquivo.filename.rsplit('.', 1)[-1].lower() if '.' in arquivo.filename else ''
    if ext not in _EXTENSOES_IMAGEM:
        return jsonify({'erro': 'Tipo de arquivo não permitido'}), 400
    pasta_usuario = 'geral'
    if usuario_id:
        u = banco.buscar_usuario_por_id(int(usuario_id))
        if u:
            login_raw = u.get('usuario') or u.get('nome') or str(usuario_id)
            pasta_usuario = _RE_LOGIN_SEGURO.sub('_', login_raw).lower()
    nome_arquivo = f'{uuid.uuid4().hex}.{ext}'
    pasta = os.path.join(current_app.root_path, 'static', 'assinaturas', pasta_usuario)
    os.makedirs(pasta, exist_ok=True)
    arquivo.save(os.path.join(pasta, nome_arquivo))
    return jsonify({'url': f'/static/assinaturas/{pasta_usuario}/{nome_arquivo}'})
