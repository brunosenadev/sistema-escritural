from datetime import date
from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, checar_admin

hub_bp = Blueprint('hub', __name__)


@hub_bp.route('/hub')
def aba_hub():
    if not usuario_logado():
        from flask import redirect, url_for
        return redirect(url_for('auth.pagina_login'))
    bancos = banco.hub_listar_bancos()
    return render_template('aba_hub.html', bancos=bancos)


@hub_bp.route('/hub/print')
def hub_print():
    if not usuario_logado():
        from flask import redirect, url_for
        return redirect(url_for('auth.pagina_login'))
    ids_raw = request.args.get('ids', '')
    ids = [int(x) for x in ids_raw.split(',') if x.strip().isdigit()]
    todos = banco.hub_listar_bancos()
    bancos_sel = [b for b in todos if b['id'] in ids] if ids else todos
    data_emissao = date.today().strftime('%d/%m/%Y')
    return render_template('hub_print.html', bancos=bancos_sel, data_emissao=data_emissao)

@hub_bp.route('/api/hub/bancos', methods=['POST'])
def api_hub_adicionar_banco():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    novo_id = banco.hub_adicionar_banco(request.get_json() or {})
    return jsonify({'sucesso': True, 'id': novo_id})


@hub_bp.route('/api/hub/bancos/<int:banco_id>', methods=['PUT'])
def api_hub_atualizar_banco(banco_id):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_atualizar_banco(banco_id, request.get_json() or {})
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/bancos/<int:banco_id>', methods=['DELETE'])
def api_hub_remover_banco(banco_id):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_remover_banco(banco_id)
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/bancos/<int:banco_id>/instrucoes', methods=['POST'])
def api_hub_adicionar_instrucao(banco_id):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    banco.hub_adicionar_instrucao(banco_id, d.get('codigo',''), d.get('descricao',''), int(d.get('ordem',99)))
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/instrucoes/<int:instrucao_id>', methods=['PUT'])
def api_hub_atualizar_instrucao(instrucao_id):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    banco.hub_atualizar_instrucao(instrucao_id, d.get('codigo',''), d.get('descricao',''), int(d.get('ordem',99)))
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/instrucoes/<int:instrucao_id>', methods=['DELETE'])
def api_hub_remover_instrucao(instrucao_id):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_remover_instrucao(instrucao_id)
    return jsonify({'sucesso': True})
