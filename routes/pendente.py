from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, checar_login

pendente_bp = Blueprint('pendente', __name__)


@pendente_bp.route('/pendente')
def aba_pendente():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio

    registros       = banco.listar_pendentes()
    lista_tecnicos  = banco.listar_tecnicos()
    resumo_tecnicos = {}
    resumo_status   = {}

    for reg in registros:
        tecnico = reg.get('tecnico') or 'SEM TEC.'
        status  = reg.get('status')  or 'SEM STATUS'
        resumo_tecnicos[tecnico] = resumo_tecnicos.get(tecnico, 0) + 1
        resumo_status[status]    = resumo_status.get(status, 0) + 1

    resumo_tecnicos = dict(sorted(resumo_tecnicos.items(), key=lambda x: x[1], reverse=True))
    resumo_status   = dict(sorted(resumo_status.items(),   key=lambda x: x[1], reverse=True))

    tecnico_logado = session.get('tecnico_vinculado', '') or ''
    if tecnico_logado:
        registros.sort(key=lambda r: (0 if (r.get('tecnico') or '') == tecnico_logado else 1))
    else:
        registros.sort(key=lambda r: (0 if not (r.get('tecnico') or '').strip()
                                          or (r.get('tecnico') or '').upper() == 'SEM TEC.' else 1))

    cores_tecnicos = {t['nome']: t['cor'] for t in lista_tecnicos}

    return render_template(
        'aba_pendente.html',
        registros=registros,
        resumo_tecnicos=resumo_tecnicos,
        resumo_status=resumo_status,
        lista_tecnicos=lista_tecnicos,
        lista_status=banco.listar_status(),
        lista_servicos=banco.listar_servicos(),
        cores_tecnicos=cores_tecnicos,
    )


@pendente_bp.route('/pendente/adicionar', methods=['POST'])
def adicionar_pendente():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_novo = banco.adicionar_pendente(request.get_json(), criado_por=session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})


@pendente_bp.route('/pendente/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_pendente(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.atualizar_pendente(id_registro, request.get_json())
    return jsonify({'sucesso': True})


@pendente_bp.route('/pendente/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_pendente(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.deletar_pendente(id_registro)
    return jsonify({'sucesso': True})


@pendente_bp.route('/pendente/cancelar/<int:id_registro>', methods=['POST'])
def cancelar_pendente(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_novo = banco.mover_pendente_para_cancelado(id_registro)
    if id_novo:
        return jsonify({'sucesso': True, 'id_cancelado': id_novo})
    return jsonify({'erro': 'Registro não encontrado'}), 404


@pendente_bp.route('/pendente/homologar/<int:id_registro>', methods=['POST'])
def homologar_pendente(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_novo, aba = banco.mover_pendente_para_homologado(id_registro)
    if id_novo:
        nomes = {
            'cobranca':   'Homologados Cobrança',
            'pagamentos': 'Homologados Pagamentos',
            'extrato':    'Homologados Extrato Cartão',
        }
        return jsonify({'sucesso': True, 'id_homologado': id_novo, 'aba': aba, 'nome_aba': nomes.get(aba, aba)})
    return jsonify({'erro': 'Registro não encontrado'}), 404
