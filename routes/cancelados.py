from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, checar_login

cancelados_bp = Blueprint('cancelados', __name__)


@cancelados_bp.route('/cancelados')
def aba_cancelados():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio

    registros       = banco.listar_cancelados()
    registros.sort(key=lambda r: r.get('id', 0), reverse=True)
    lista_tecnicos  = banco.listar_tecnicos()
    cores_tecnicos  = {t['nome']: t['cor'] for t in lista_tecnicos}
    resumo_tecnicos = {}
    for reg in registros:
        tecnico = reg.get('tecnico') or 'SEM TEC.'
        resumo_tecnicos[tecnico] = resumo_tecnicos.get(tecnico, 0) + 1
    resumo_tecnicos = dict(sorted(resumo_tecnicos.items(), key=lambda x: x[1], reverse=True))

    return render_template(
        'aba_cancelados.html',
        registros=registros,
        resumo_tecnicos=resumo_tecnicos,
        lista_tecnicos=lista_tecnicos,
        lista_servicos=banco.listar_servicos(),
        cores_tecnicos=cores_tecnicos,
    )


@cancelados_bp.route('/cancelados/adicionar', methods=['POST'])
def adicionar_cancelado():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_novo = banco.adicionar_cancelado(request.get_json(), criado_por=session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})


@cancelados_bp.route('/cancelados/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_cancelado(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.atualizar_cancelado(id_registro, request.get_json())
    return jsonify({'sucesso': True})


@cancelados_bp.route('/cancelados/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_cancelado(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.deletar_cancelado(id_registro)
    return jsonify({'sucesso': True})
