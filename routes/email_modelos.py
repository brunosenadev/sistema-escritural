from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
import banco
import exclusoes
from utils import checar_tela, usuario_logado

email_modelos_bp = Blueprint('email_modelos', __name__)


def _tem_acesso():
    return not checar_tela('email_modelos')


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Modelos de E-mail', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@email_modelos_bp.route('/email-modelos')
def aba_email_modelos():
    bloqueio = checar_tela('email_modelos')
    if bloqueio:
        return bloqueio
    return render_template(
        'aba_email_modelos.html',
        modelos=banco.listar_email_modelos(),
        servicos=banco.listar_servicos(),
        params=banco.PARAMS_EMAIL_MODELO,
        now=datetime.now().strftime('%d/%m/%Y'),
    )


@email_modelos_bp.route('/api/email-modelos', methods=['GET'])
def api_listar_email_modelos():
    if not _tem_acesso():
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.listar_email_modelos())


@email_modelos_bp.route('/api/email-modelos', methods=['POST'])
def api_adicionar_email_modelo():
    if not _tem_acesso():
        return jsonify({'erro': 'Sem permissão'}), 403
    dados = request.get_json() or {}
    if not (dados.get('nome') or '').strip():
        return jsonify({'erro': 'Informe o nome do modelo.'}), 400
    id_novo = banco.adicionar_email_modelo(dados)
    _log('INSERIU', f'Criou modelo de e-mail #{id_novo} — {dados.get("nome","")} (serviço: {dados.get("servico","") or "todos"})')
    return jsonify({'sucesso': True, 'id': id_novo})


@email_modelos_bp.route('/api/email-modelos/<int:id_modelo>', methods=['PUT'])
def api_atualizar_email_modelo(id_modelo):
    if not _tem_acesso():
        return jsonify({'erro': 'Sem permissão'}), 403
    dados = request.get_json() or {}
    if not (dados.get('nome') or '').strip():
        return jsonify({'erro': 'Informe o nome do modelo.'}), 400
    banco.atualizar_email_modelo(id_modelo, dados)
    _log('EDITOU', f'Editou modelo de e-mail #{id_modelo} — {dados.get("nome","")}')
    return jsonify({'sucesso': True})


@email_modelos_bp.route('/api/email-modelos/<int:id_modelo>', methods=['DELETE'])
def api_remover_email_modelo(id_modelo):
    if not _tem_acesso():
        return jsonify({'erro': 'Sem permissão'}), 403
    modelo = banco.buscar_email_modelo(id_modelo)
    nome = modelo.get('nome', '') if modelo else '?'
    payload, status = exclusoes.processar_exclusao(
        'email_modelo', id_modelo, f'Modelo de e-mail #{id_modelo} — {nome}', 'Modelos de E-mail', _log
    )
    return jsonify(payload), status


@email_modelos_bp.route('/api/email-modelos/por-servico/<path:servico>')
def api_modelo_por_servico(servico):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    modelo = banco.buscar_email_modelo_por_servico(servico)
    return jsonify(modelo or {})
