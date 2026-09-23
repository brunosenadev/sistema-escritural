from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import checar_master

solicitacoes_exclusao_bp = Blueprint('solicitacoes_exclusao', __name__)


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='solicitacoes_exclusao',
        acao=acao,
        descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@solicitacoes_exclusao_bp.route('/solicitacoes-exclusao')
def pagina_solicitacoes_exclusao():
    bloqueio = checar_master()
    if bloqueio:
        return bloqueio
    pendentes = banco.listar_solicitacoes_exclusao('pendente')
    return render_template(
        'aba_solicitacoes_exclusao.html',
        aba_ativa='solicitacoes_exclusao',
        pendentes=pendentes,
    )


@solicitacoes_exclusao_bp.route('/api/solicitacoes-exclusao')
def api_listar_solicitacoes_exclusao():
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Sem permissão'}), 403
    pendentes = banco.listar_solicitacoes_exclusao('pendente')
    return jsonify(pendentes)


@solicitacoes_exclusao_bp.route('/api/solicitacoes-exclusao/<int:id_sol>/aprovar', methods=['POST'])
def api_aprovar_solicitacao_exclusao(id_sol):
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Sem permissão'}), 403
    nome = session.get('nome') or session.get('usuario', '')
    resultado = banco.aprovar_solicitacao_exclusao(id_sol, nome)
    if not resultado:
        return jsonify({'erro': 'Solicitação não encontrada ou já respondida.'}), 404
    banco.criar_notificacao(
        resultado['solicitante_id'],
        'Exclusão aprovada',
        f'{nome} aprovou sua solicitação: {resultado["descricao"]}',
        tipo='sucesso',
        link='/solicitacoes-exclusao',
    )
    _log('APROVOU_EXCLUSAO', f'Aprovou solicitação #{id_sol} — {resultado["descricao"]}')
    return jsonify({'sucesso': True})


@solicitacoes_exclusao_bp.route('/api/solicitacoes-exclusao/<int:id_sol>/negar', methods=['POST'])
def api_negar_solicitacao_exclusao(id_sol):
    if session.get('nivel_acesso') != 'master':
        return jsonify({'erro': 'Sem permissão'}), 403
    nome = session.get('nome') or session.get('usuario', '')
    d = request.get_json(silent=True) or {}
    motivo = (d.get('motivo') or '').strip() or None
    resultado = banco.negar_solicitacao_exclusao(id_sol, nome, motivo)
    if not resultado:
        return jsonify({'erro': 'Solicitação não encontrada ou já respondida.'}), 404
    banco.criar_notificacao(
        resultado['solicitante_id'],
        'Exclusão negada',
        f'{nome} negou sua solicitação: {resultado["descricao"]}' + (f' — Motivo: {motivo}' if motivo else ''),
        tipo='erro',
        link='/solicitacoes-exclusao',
    )
    _log('NEGOU_EXCLUSAO', f'Negou solicitação #{id_sol} — {resultado["descricao"]}')
    return jsonify({'sucesso': True})
