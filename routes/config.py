from flask import Blueprint, render_template, request, jsonify, session, make_response
import banco
from utils import checar_admin, usuario_logado, criar_tokens, _preencher_sessao

config_bp = Blueprint('config', __name__)


@config_bp.route('/api/contadores')
def api_contadores():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify(banco.contar_todos())


@config_bp.route('/configuracoes')
def pagina_configuracoes():
    bloqueio = checar_admin()
    if bloqueio:
        return bloqueio
    contadores = banco.contar_todos()
    return render_template(
        'configuracoes.html',
        tecnicos=banco.listar_tecnicos(),
        usuarios=banco.listar_usuarios(),
        lista_status=banco.listar_status(),
        lista_servicos=banco.listar_servicos_completo(),
        lista_setores=banco.listar_setores(),
        total_pendentes=contadores['pendentes'],
        total_hom_cobranca_db=contadores['cobranca'],
        total_hom_pagamentos_db=contadores['pagamentos'],
        total_hom_extrato_db=contadores['extrato'],
        total_cancelados_db=contadores['cancelados'],
    )


# ── API Técnicos ──────────────────────────────────────────

@config_bp.route('/api/tecnicos', methods=['POST'])
def api_adicionar_tecnico():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d  = request.get_json()
    ok = banco.adicionar_tecnico(d.get('nome', ''), '#64748b')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Técnico já cadastrado.'}), 409)


@config_bp.route('/api/tecnicos/<nome>', methods=['PUT'])
def api_atualizar_tecnico(nome):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json()
    banco.atualizar_tecnico(nome, d.get('nome', nome), '#64748b')
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
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if alvo and alvo.get('nivel') == 'master' and id_usuario != session.get('id_usuario'):
        return jsonify({'erro': 'Usuário master não pode ser editado.'}), 403
    banco.atualizar_usuario(id_usuario, request.get_json())
    # Se atualizou o próprio usuário, renova o token com dados frescos
    if id_usuario == session.get('id_usuario'):
        u = banco.buscar_usuario_por_id(id_usuario)
        _preencher_sessao({
            'usr': u['usuario'], 'nome': u['nome'], 'niv': u['nivel'],
            'tec': u.get('tecnico_vinculado') or '', 'tema': u.get('tema') or 'light',
            'sub': u['id'], 'mp': int(u.get('mudar_senha') or 0),
        })
        access, _ = criar_tokens(u)
        resp = make_response(jsonify({'sucesso': True}))
        resp.set_cookie('access_token', access, max_age=15*60, httponly=True, samesite='Lax', path='/')
        return resp
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>/resetar-senha', methods=['POST'])
def api_resetar_senha(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.resetar_senha_usuario(id_usuario)
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>/limpar-troca', methods=['POST'])
def api_limpar_troca(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.limpar_mudar_senha(id_usuario)
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
def api_remover_usuario(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if alvo and alvo.get('nivel') == 'master':
        return jsonify({'erro': 'Usuário master não pode ser removido.'}), 403
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


# ── API Setores ───────────────────────────────────────────

@config_bp.route('/api/setores', methods=['POST'])
def api_adicionar_setor():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    ok = banco.adicionar_setor(request.get_json().get('texto', ''))
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Setor já cadastrado.'}), 409)


@config_bp.route('/api/setores/<path:texto>', methods=['DELETE'])
def api_remover_setor(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_setor(texto)
    return jsonify({'sucesso': True})
