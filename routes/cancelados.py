from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, pode_editar, checar_tela


def _checar_edicao():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not pode_editar():
        return jsonify({'erro': 'Sem permissão para editar.'}), 403
    return None


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Cancelados', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


cancelados_bp = Blueprint('cancelados', __name__)


@cancelados_bp.route('/cancelados')
def aba_cancelados():
    bloqueio = checar_tela('cancelados')
    if bloqueio:
        return bloqueio

    registros       = banco.listar_cancelados()
    registros.sort(key=lambda r: r.get('id', 0), reverse=True)
    lista_tecnicos  = banco.listar_tecnicos()
    cores_tecnicos  = banco.cores_por_tecnico()
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
    err = _checar_edicao()
    if err: return err
    dados = request.get_json() or {}
    id_novo = banco.adicionar_cancelado(dados, criado_por=session.get('usuario', ''))
    _log('INSERIU', f'Inseriu cancelado #{id_novo} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True, 'id': id_novo})


@cancelados_bp.route('/cancelados/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_cancelado(id_registro):
    err = _checar_edicao()
    if err: return err
    dados = request.get_json() or {}
    banco.atualizar_cancelado(id_registro, dados)
    _log('EDITOU', f'Editou cancelado #{id_registro} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True})


@cancelados_bp.route('/cancelados/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_cancelado(id_registro):
    err = _checar_edicao()
    if err: return err
    empresa = banco.buscar_empresa_log('cancelados', id_registro)
    banco.deletar_cancelado(id_registro)
    _log('DELETOU', f'Deletou cancelado #{id_registro} — {empresa}')
    return jsonify({'sucesso': True})
