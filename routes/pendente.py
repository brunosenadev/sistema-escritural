from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, pode_editar, checar_tela

pendente_bp = Blueprint('pendente', __name__)


def _sem_permissao():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not pode_editar():
        return jsonify({'erro': 'Sem permissão para editar.'}), 403
    return None


@pendente_bp.route('/pendente')
def aba_pendente():
    bloqueio = checar_tela('pendente')
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
        registros.sort(key=lambda r: (
            0 if (r.get('tecnico') or '') == tecnico_logado else 1,
            (r.get('tecnico') or 'ZZZ'),
            r.get('id', 0),
        ))
    else:
        def _sort_sem_logado(r):
            tec = (r.get('tecnico') or '').strip().upper()
            sem = not tec or tec == 'SEM TEC.'
            return (0 if sem else 1, r.get('tecnico') or '', r.get('id', 0))
        registros.sort(key=_sort_sem_logado)

    cores_tecnicos = banco.cores_por_tecnico()

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
    err = _sem_permissao()
    if err: return err
    id_novo = banco.adicionar_pendente(request.get_json(), criado_por=session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})


@pendente_bp.route('/pendente/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.atualizar_pendente(id_registro, request.get_json())
    return jsonify({'sucesso': True})


@pendente_bp.route('/pendente/status/<int:id_registro>', methods=['PATCH'])
def atualizar_status_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    novo_status = (request.get_json() or {}).get('status', '')
    if not novo_status:
        return jsonify({'erro': 'Status não informado'}), 400
    from datetime import datetime as _dt
    banco.atualizar_status_pendente(id_registro, novo_status)
    return jsonify({'sucesso': True, 'dt_status': _dt.now().strftime('%d/%m/%Y')})


@pendente_bp.route('/pendente/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.deletar_pendente(id_registro)
    return jsonify({'sucesso': True})


@pendente_bp.route('/pendente/cancelar/<int:id_registro>', methods=['POST'])
def cancelar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    id_novo = banco.mover_pendente_para_cancelado(id_registro)
    if id_novo:
        return jsonify({'sucesso': True, 'id_cancelado': id_novo})
    return jsonify({'erro': 'Registro não encontrado'}), 404


@pendente_bp.route('/pendente/assumir/<int:id_registro>', methods=['POST'])
def assumir_pendente(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    dados = request.get_json() or {}
    tecnico = (dados.get('tecnico') or session.get('tecnico_vinculado') or '').strip()
    if not tecnico:
        return jsonify({'erro': 'Nenhum técnico selecionado.'}), 400
    ok = banco.assumir_pendente(id_registro, tecnico)
    if ok:
        return jsonify({'sucesso': True, 'tecnico': tecnico})
    return jsonify({'erro': 'Registro não encontrado ou já possui técnico.'}), 404


@pendente_bp.route('/pendente/homologar/<int:id_registro>', methods=['POST'])
def homologar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    id_novo, aba = banco.mover_pendente_para_homologado(id_registro)
    if id_novo:
        nomes = {
            'cobranca':   'Homologados Cobrança',
            'pagamentos': 'Homologados Pagamentos',
            'extrato':    'Homologados Extrato Cartão',
        }
        return jsonify({'sucesso': True, 'id_homologado': id_novo, 'aba': aba, 'nome_aba': nomes.get(aba, aba)})
    return jsonify({'erro': 'Registro não encontrado'}), 404
