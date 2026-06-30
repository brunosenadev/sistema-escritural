import os
from flask import Blueprint, render_template, request, jsonify, session
import banco
from planilha import ler_escritural_do_excel
from utils import checar_tela

escritural_bp = Blueprint('escritural', __name__)

_PASTA_UPLOADS = '/tmp' if os.environ.get('RENDER') else os.path.join(os.path.dirname(__file__), '..', 'uploads')


@escritural_bp.route('/escritural')
def aba_escritural():
    bloqueio = checar_tela('escritural')
    if bloqueio:
        return bloqueio
    registros = banco.listar_escritural()
    return render_template(
        'aba_escritural.html',
        registros=registros,
        campos=banco.CAMPOS_ESCRITURAL,
        labels=banco.LABELS_ESCRITURAL,
    )


@escritural_bp.route('/escritural/adicionar', methods=['POST'])
def adicionar_escritural():
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    id_novo = banco.adicionar_escritural(request.get_json() or {}, criado_por=session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})


@escritural_bp.route('/escritural/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_escritural(id_registro):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.atualizar_escritural(id_registro, request.get_json() or {})
    return jsonify({'sucesso': True})


@escritural_bp.route('/escritural/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_escritural(id_registro):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.deletar_escritural(id_registro)
    return jsonify({'sucesso': True})


@escritural_bp.route('/escritural/importar', methods=['POST'])
def importar_escritural():
    if checar_tela('importar_novas_homologacoes'):
        return jsonify({'erro': 'Sem permissão'}), 403

    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado.'}), 400

    arq = request.files['arquivo']
    if os.path.splitext(arq.filename)[1].lower() not in ('.xlsx', '.xls'):
        return jsonify({'erro': 'O arquivo deve ser .xlsx ou .xls.'}), 400

    os.makedirs(_PASTA_UPLOADS, exist_ok=True)
    caminho = os.path.join(_PASTA_UPLOADS, 'escritural_importacao_temp.xlsx')
    arq.save(caminho)

    registros = ler_escritural_do_excel(caminho)
    if not registros:
        return jsonify({'erro': 'Não foi possível reconhecer colunas/registros nessa planilha.'}), 400

    novos = banco.importar_escritural(registros, criado_por=session.get('usuario', '') or 'importação planilha')
    return jsonify({
        'sucesso': True,
        'lidos': len(registros),
        'novos': novos,
        'duplicados': len(registros) - novos,
    })
