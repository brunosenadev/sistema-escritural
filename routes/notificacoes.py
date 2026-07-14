from flask import Blueprint, jsonify, request, session, render_template
import banco
from utils import checar_login, usuario_logado, checar_tela

notificacoes_bp = Blueprint('notificacoes', __name__)


def _uid():
    return session.get('id_usuario')


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Notificações', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@notificacoes_bp.route('/notificacoes')
def pagina_notificacoes():
    bloqueio = checar_tela('notificacoes')
    if bloqueio:
        return bloqueio
    uid = _uid()
    notifs = banco.listar_notificacoes(uid, limite=100)
    u = banco.buscar_usuario_por_id(uid) or {}
    pode_enviar = bool(u.get('pode_enviar_notificacao'))
    usuarios = banco.listar_usuarios() if pode_enviar else []
    setores  = banco.listar_setores() if pode_enviar else []
    return render_template(
        'aba_notificacoes.html',
        notificacoes=notifs,
        aba_ativa='notificacoes',
        usuarios_lista=usuarios,
        lista_setores=setores,
        pode_enviar=pode_enviar,
    )


@notificacoes_bp.route('/api/notificacoes')
def api_listar():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    notifs = banco.listar_notificacoes(_uid(), limite=50)
    return jsonify(notifs)


@notificacoes_bp.route('/api/notificacoes/contagem')
def api_contagem():
    if not usuario_logado():
        return jsonify({'nao_lidas': 0, 'novas': []}), 200
    uid = _uid()
    desde_id = request.args.get('desde_id', type=int)
    nao_lidas = banco.contar_nao_lidas_notif(uid)
    novas = banco.buscar_notificacoes_novas(uid, desde_id) if desde_id is not None else []
    return jsonify({'nao_lidas': nao_lidas, 'novas': novas})


@notificacoes_bp.route('/api/notificacoes/<int:notif_id>/lida', methods=['POST'])
def api_marcar_lida(notif_id):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.marcar_notificacao_lida(notif_id, _uid())
    return jsonify({'sucesso': True})


@notificacoes_bp.route('/api/notificacoes/marcar-todas-lidas', methods=['POST'])
def api_marcar_todas_lidas():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.marcar_todas_notificacoes_lidas(_uid())
    return jsonify({'sucesso': True})


@notificacoes_bp.route('/api/notificacoes/<int:notif_id>', methods=['DELETE'])
def api_deletar(notif_id):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.deletar_notificacao(notif_id, _uid())
    return jsonify({'sucesso': True})


@notificacoes_bp.route('/api/notificacoes/lidas', methods=['DELETE'])
def api_deletar_lidas():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.deletar_notificacoes_lidas(_uid())
    return jsonify({'sucesso': True})


@notificacoes_bp.route('/api/notificacoes/enviar', methods=['POST'])
def api_enviar():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    u = banco.buscar_usuario_por_id(_uid()) or {}
    if not u.get('pode_enviar_notificacao'):
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json(silent=True) or {}
    titulo = (d.get('titulo') or '').strip()
    mensagem = (d.get('mensagem') or '').strip()
    tipo = d.get('tipo', 'info')
    destino = d.get('destino', 'todos')
    usuario_id = d.get('usuario_id')

    if not titulo:
        return jsonify({'erro': 'Título obrigatório'}), 400
    if tipo not in ('info', 'sucesso', 'aviso', 'erro'):
        tipo = 'info'

    if destino == 'todos':
        banco.criar_notificacao_todos(titulo, mensagem, tipo)
        _log('ENVIOU', f'Notificação para todos — "{titulo}"')
    elif destino == 'setor':
        setor = (d.get('setor') or '').strip()
        if not setor:
            return jsonify({'erro': 'Setor não informado'}), 400
        ids = banco.listar_usuarios_por_setor(setor)
        if not ids:
            return jsonify({'erro': f'Nenhum usuário encontrado no setor "{setor}"'}), 400
        for uid in ids:
            banco.criar_notificacao(uid, titulo, mensagem, tipo)
        _log('ENVIOU', f'Notificação para setor {setor} ({len(ids)} usuário(s)) — "{titulo}"')
    else:
        if not usuario_id:
            return jsonify({'erro': 'Usuário não informado'}), 400
        banco.criar_notificacao(int(usuario_id), titulo, mensagem, tipo)
        dest = banco.buscar_usuario_por_id(int(usuario_id))
        _log('ENVIOU', f'Notificação para {dest.get("nome","?") if dest else usuario_id} — "{titulo}"')

    return jsonify({'sucesso': True})
