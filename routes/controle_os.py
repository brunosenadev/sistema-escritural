from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, checar_tela

controle_os_bp = Blueprint('controle_os', __name__)

NOMES_ABA = {
    'cobranca':     'Hom. Cobrança',
    'pagamentos':   'Hom. Pagamentos',
    'extrato':      'Hom. Extrato Cartão',
    'ext_bancario': 'Hom. Extrato Bancário',
}


def _eh_master_ou_admin():
    return session.get('nivel_acesso') in ('admin', 'master')


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Controle de O.S.', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@controle_os_bp.route('/controle-os')
def aba_controle_os():
    bloqueio = checar_tela('controle_os')
    if bloqueio:
        return bloqueio

    ve_tudo = _eh_master_ou_admin()
    registros = banco.listar_os() if ve_tudo else banco.listar_os(session.get('id_usuario'))
    tecnicos_distintos = sorted({(reg.get('tecnico') or 'SEM TEC.') for reg in registros})

    return render_template(
        'aba_controle_os.html',
        registros=registros,
        ve_tudo=ve_tudo,
        usuarios_lista=banco.listar_usuarios() if ve_tudo else [],
        nomes_aba=NOMES_ABA,
        tecnicos_distintos=tecnicos_distintos,
        cores_tecnicos=banco.cores_por_tecnico(),
    )


@controle_os_bp.route('/controle-os/status/<int:id_os>', methods=['PATCH'])
def atualizar_status_os(id_os):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    reg = banco.buscar_os(id_os)
    if not reg:
        return jsonify({'erro': 'O.S. não encontrada'}), 404
    if not _eh_master_ou_admin() and reg.get('usuario_id') != session.get('id_usuario'):
        return jsonify({'erro': 'Sem permissão para alterar esta O.S.'}), 403
    novo_status = (request.get_json() or {}).get('status', '')
    if novo_status not in ('PENDENTE', 'CONCLUIDA', 'BONIFICADA'):
        return jsonify({'erro': 'Status inválido'}), 400
    banco.atualizar_status_os(id_os, novo_status)
    _log('STATUS', f'Alterou status da O.S. #{id_os} ({reg.get("empresa","?")}) → {novo_status}')
    return jsonify({'sucesso': True})


@controle_os_bp.route('/controle-os/atribuir/<int:id_os>', methods=['POST'])
def atribuir_os(id_os):
    if not usuario_logado() or not _eh_master_ou_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    reg = banco.buscar_os(id_os)
    if not reg:
        return jsonify({'erro': 'O.S. não encontrada'}), 404
    dados = request.get_json() or {}
    usuario_id = dados.get('usuario_id')
    if not usuario_id:
        return jsonify({'erro': 'Usuário não informado'}), 400
    usr = banco.buscar_usuario_por_id(int(usuario_id))
    if not usr:
        return jsonify({'erro': 'Usuário não encontrado'}), 404
    banco.atribuir_os(id_os, usr['id'], usr.get('tecnico_vinculado', ''))
    _log('ATRIBUIU', f'Atribuiu O.S. #{id_os} ({reg.get("empresa","?")}) → {usr.get("nome","?")}')
    return jsonify({'sucesso': True})
