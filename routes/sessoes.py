from flask import Blueprint, render_template, jsonify, session, request
import banco
from utils import checar_master

sessoes_bp = Blueprint('sessoes', __name__)


@sessoes_bp.route('/sessoes')
def pagina_sessoes():
    bloqueio = checar_master()
    if bloqueio:
        return bloqueio
    return render_template('aba_sessoes.html', aba_ativa='sessoes')


@sessoes_bp.route('/api/sessoes')
def api_listar():
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Acesso negado'}), 403
    meu_id = session.get('id_usuario')
    sessoes = banco.listar_sessoes_ativas()
    for s in sessoes:
        s['sou_eu'] = (s['usuario_id'] == meu_id)
    return jsonify(sessoes)


@sessoes_bp.route('/api/sessoes/<int:id_sessao>', methods=['DELETE'])
def api_encerrar(id_sessao):
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Acesso negado'}), 403
    banco.encerrar_sessao_por_id(id_sessao)
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', ''),
        tela='Sessões', acao='LOGOUT',
        descricao=f'Forçou logout da sessão #{id_sessao}',
        usuario_id=session.get('id_usuario'),
        nivel='master',
        ip=request.remote_addr,
    )
    return jsonify({'sucesso': True})
