from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import checar_tela, tem_acesso_tela

hub_bp = Blueprint('hub', __name__)


def _pode_editar():
    nivel = session.get('nivel_acesso', '')
    if nivel in ('admin', 'master'):
        return True
    return tem_acesso_tela('hub_edicao')


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('usuario', ''),
        tela='hub',
        acao=acao,
        descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


# ── Visualização ──────────────────────────────────────────

@hub_bp.route('/hub')
def aba_hub():
    bloqueio = checar_tela('hub')
    if bloqueio:
        return bloqueio
    bancos      = banco.hub_listar_bancos_v2()
    categorias  = banco.hub_listar_categorias()
    servicos    = banco.hub_listar_servicos()
    pode_editar = _pode_editar()
    return render_template('aba_hub.html',
                           bancos=bancos,
                           categorias=categorias,
                           servicos=servicos,
                           pode_editar=pode_editar)


@hub_bp.route('/hub/print')
def hub_print():
    from datetime import date
    bloqueio = checar_tela('hub')
    if bloqueio:
        return bloqueio
    ids_raw = request.args.get('ids', '')
    ids = [int(x) for x in ids_raw.split(',') if x.strip().isdigit()]
    todos = banco.hub_listar_bancos_v2()
    bancos_sel = [b for b in todos if b['id'] in ids] if ids else todos
    return render_template('hub_print.html',
                           bancos=bancos_sel,
                           data_emissao=date.today().strftime('%d/%m/%Y'))


# ── API: Bancos ───────────────────────────────────────────

@hub_bp.route('/api/hub/bancos', methods=['POST'])
def api_hub_adicionar_banco():
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'Nome obrigatório'}), 400
    novo_id = banco.hub_adicionar_banco_v2(nome, int(d.get('ordem', 99)))
    servico_ids = d.get('servicos', [])
    if servico_ids:
        banco.hub_sincronizar_banco_servicos(novo_id, servico_ids)
    _log('criar_banco', f'Banco criado: {nome}')
    return jsonify({'sucesso': True, 'id': novo_id})


@hub_bp.route('/api/hub/bancos/<int:banco_id>', methods=['PUT'])
def api_hub_atualizar_banco(banco_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'Nome obrigatório'}), 400
    banco.hub_atualizar_banco_v2(banco_id, nome, int(d.get('ordem', 99)))
    if 'servicos' in d:
        banco.hub_sincronizar_banco_servicos(banco_id, d['servicos'])
    _log('editar_banco', f'Banco #{banco_id} atualizado: {nome}')
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/bancos/<int:banco_id>', methods=['DELETE'])
def api_hub_remover_banco(banco_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_remover_banco(banco_id)
    _log('remover_banco', f'Banco #{banco_id} removido')
    return jsonify({'sucesso': True})


# ── API: Serviços por banco ───────────────────────────────

@hub_bp.route('/api/hub/bancos/<int:banco_id>/servicos', methods=['PUT'])
def api_hub_servicos_banco(banco_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    servico_ids = d.get('servicos', [])
    banco.hub_sincronizar_banco_servicos(banco_id, servico_ids)
    _log('editar_servicos_banco', f'Serviços do banco #{banco_id} atualizados')
    return jsonify({'sucesso': True})


# ── API: Instruções ───────────────────────────────────────

@hub_bp.route('/api/hub/bancos/<int:banco_id>/instrucoes', methods=['POST'])
def api_hub_adicionar_instrucao(banco_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    cod  = (d.get('codigo')    or '').strip()
    desc = (d.get('descricao') or '').strip()
    if not cod or not desc:
        return jsonify({'erro': 'Código e descrição obrigatórios'}), 400
    banco.hub_adicionar_instrucao(banco_id, cod, desc, int(d.get('ordem', 99)))
    _log('criar_instrucao', f'Instrução adicionada ao banco #{banco_id}: [{cod}] {desc}')
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/instrucoes/<int:instrucao_id>', methods=['DELETE'])
def api_hub_remover_instrucao(instrucao_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_remover_instrucao(instrucao_id)
    _log('remover_instrucao', f'Instrução #{instrucao_id} removida')
    return jsonify({'sucesso': True})


# ── API: Categorias ───────────────────────────────────────

@hub_bp.route('/api/hub/categorias', methods=['GET'])
def api_hub_listar_categorias():
    bloqueio = checar_tela('hub')
    if bloqueio:
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.hub_listar_categorias())


@hub_bp.route('/api/hub/categorias', methods=['POST'])
def api_hub_adicionar_categoria():
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'Nome obrigatório'}), 400
    novo_id = banco.hub_adicionar_categoria(nome, int(d.get('ordem', 99)))
    _log('criar_categoria', f'Categoria criada: {nome}')
    return jsonify({'sucesso': True, 'id': novo_id})


@hub_bp.route('/api/hub/categorias/<int:cat_id>', methods=['PUT'])
def api_hub_atualizar_categoria(cat_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'Nome obrigatório'}), 400
    banco.hub_atualizar_categoria(cat_id, nome, int(d.get('ordem', 99)))
    _log('editar_categoria', f'Categoria #{cat_id} atualizada: {nome}')
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/categorias/<int:cat_id>', methods=['DELETE'])
def api_hub_remover_categoria(cat_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_remover_categoria(cat_id)
    _log('remover_categoria', f'Categoria #{cat_id} removida (com seus serviços)')
    return jsonify({'sucesso': True})


# ── API: Serviços (tipos) ─────────────────────────────────

@hub_bp.route('/api/hub/servicos', methods=['GET'])
def api_hub_listar_servicos():
    bloqueio = checar_tela('hub')
    if bloqueio:
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.hub_listar_servicos())


@hub_bp.route('/api/hub/servicos', methods=['POST'])
def api_hub_adicionar_servico():
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome or not d.get('categoria_id'):
        return jsonify({'erro': 'Nome e categoria obrigatórios'}), 400
    novo_id = banco.hub_adicionar_servico(
        int(d['categoria_id']), nome,
        d.get('cor_bg', '#dbeafe'), d.get('cor_texto', '#1d4ed8'),
        int(d.get('ordem', 99))
    )
    _log('criar_servico', f'Serviço criado: {nome} (cat #{d["categoria_id"]})')
    return jsonify({'sucesso': True, 'id': novo_id})


@hub_bp.route('/api/hub/servicos/<int:serv_id>', methods=['PUT'])
def api_hub_atualizar_servico(serv_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome or not d.get('categoria_id'):
        return jsonify({'erro': 'Nome e categoria obrigatórios'}), 400
    banco.hub_atualizar_servico(
        serv_id, int(d['categoria_id']), nome,
        d.get('cor_bg', '#dbeafe'), d.get('cor_texto', '#1d4ed8'),
        int(d.get('ordem', 99))
    )
    _log('editar_servico', f'Serviço #{serv_id} atualizado: {nome}')
    return jsonify({'sucesso': True})


@hub_bp.route('/api/hub/servicos/<int:serv_id>', methods=['DELETE'])
def api_hub_remover_servico(serv_id):
    if not _pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.hub_remover_servico(serv_id)
    _log('remover_servico', f'Serviço #{serv_id} removido')
    return jsonify({'sucesso': True})
