from flask import Blueprint, render_template, request, jsonify
import banco
from utils import checar_admin, usuario_logado

config_bp = Blueprint('config', __name__)


@config_bp.route('/configuracoes')
def pagina_configuracoes():
    bloqueio = checar_admin()
    if bloqueio:
        return bloqueio
    return render_template(
        'configuracoes.html',
        tecnicos=banco.listar_tecnicos(),
        usuarios=banco.listar_usuarios(),
        lista_status=banco.listar_status(),
        lista_servicos=banco.listar_servicos_completo(),
        total_pendentes=banco.contar_pendentes(),
    )


# ── API Técnicos ──────────────────────────────────────────

@config_bp.route('/api/tecnicos', methods=['POST'])
def api_adicionar_tecnico():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d  = request.get_json()
    ok = banco.adicionar_tecnico(d.get('nome', ''), d.get('cor', '#64748b'))
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Técnico já cadastrado.'}), 409)


@config_bp.route('/api/tecnicos/<nome>', methods=['PUT'])
def api_atualizar_tecnico(nome):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json()
    banco.atualizar_tecnico(nome, d.get('nome', nome), d.get('cor', '#64748b'))
    return jsonify({'sucesso': True})


@config_bp.route('/api/tecnicos/<nome>', methods=['DELETE'])
def api_remover_tecnico(nome):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_tecnico(nome)
    return jsonify({'sucesso': True})


# ── API Usuários ──────────────────────────────────────────

@config_bp.route('/api/usuarios', methods=['POST'])
def api_adicionar_usuario():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    ok = banco.adicionar_usuario(request.get_json())
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Login já cadastrado.'}), 409)


@config_bp.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
def api_atualizar_usuario(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.atualizar_usuario(id_usuario, request.get_json())
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>/resetar-senha', methods=['POST'])
def api_resetar_senha(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.resetar_senha_usuario(id_usuario)
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
def api_remover_usuario(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    ok = banco.remover_usuario(id_usuario)
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Não é possível remover o único administrador.'}), 400)


# ── API Status ────────────────────────────────────────────

@config_bp.route('/api/status', methods=['POST'])
def api_adicionar_status():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    ok = banco.adicionar_status(request.get_json().get('texto', ''))
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Status já cadastrado.'}), 409)


@config_bp.route('/api/status/<path:texto>', methods=['DELETE'])
def api_remover_status(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_status(texto)
    return jsonify({'sucesso': True})


# ── API Serviços ──────────────────────────────────────────

@config_bp.route('/api/servicos', methods=['POST'])
def api_adicionar_servico():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    ok = banco.adicionar_servico(request.get_json().get('texto', ''))
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Serviço já cadastrado.'}), 409)


@config_bp.route('/api/servicos/<path:texto>', methods=['PUT'])
def api_atualizar_servico(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    banco.atualizar_destino_servico(texto, d.get('destino', ''))
    return jsonify({'sucesso': True})


@config_bp.route('/api/servicos/<path:texto>', methods=['DELETE'])
def api_remover_servico(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_servico(texto)
    return jsonify({'sucesso': True})
