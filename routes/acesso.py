from flask import Blueprint, render_template, request, jsonify
import banco
from utils import checar_master

acesso_bp = Blueprint('acesso', __name__)


@acesso_bp.route('/acesso')
def aba_acesso():
    bloqueio = checar_master()
    if bloqueio:
        return bloqueio
    usuarios = banco.listar_usuarios_permissoes()
    return render_template('aba_acesso.html', usuarios=usuarios, grupos=banco.TELAS_AGRUPADAS, telas=banco.TELAS_SISTEMA)


@acesso_bp.route('/api/acesso/usuario/<int:usuario_id>/toggle', methods=['POST'])
def api_toggle_permissao(usuario_id):
    bloqueio = checar_master()
    if bloqueio:
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    tela     = d.get('tela', '')
    permitido = bool(d.get('permitido', False))
    telas_validas = {t[0] for t in banco.TELAS_SISTEMA}
    if tela not in telas_validas:
        return jsonify({'erro': 'Tela inválida'}), 400
    banco.toggle_permissao(usuario_id, tela, permitido)
    return jsonify({'sucesso': True})


@acesso_bp.route('/api/acesso/usuario/<int:usuario_id>/telas', methods=['PUT'])
def api_salvar_permissoes(usuario_id):
    bloqueio = checar_master()
    if bloqueio:
        return jsonify({'erro': 'Sem permissão'}), 403
    d     = request.get_json() or {}
    telas = d.get('telas', [])
    telas_validas = {t[0] for t in banco.TELAS_SISTEMA}
    telas = [t for t in telas if t in telas_validas]
    banco.salvar_permissoes_usuario(usuario_id, telas)
    return jsonify({'sucesso': True})
