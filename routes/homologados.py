from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import usuario_logado, pode_editar, checar_tela


def _sem_permissao():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not pode_editar():
        return jsonify({'erro': 'Sem permissão para editar.'}), 403
    return None

homologados_bp = Blueprint('homologados', __name__)

_CONFIGS = {
    'cobranca':   ('listar_homologados_cobranca',   'Homologados Cobrança',       'homologados_cobranca'),
    'pagamentos': ('listar_homologados_pagamentos',  'Homologados Pagamentos',      'homologados_pagamentos'),
    'extrato':    ('listar_homologados_extrato',     'Homologados Extrato Cartão',  'homologados_extrato'),
}


def _chave_data(s):
    """Converte 'dd/mm/yyyy' para chave de ordenação 'yyyy/mm/dd'. Vazio vai para o fim."""
    if not s or s.strip() == '':
        return '0000/00/00'  # vai para o fim com reverse=True
    partes = s.strip().split('/')
    if len(partes) == 3:
        return f'{partes[2]}/{partes[1]}/{partes[0]}'
    return '0000/00/00'


def _render(tipo):
    tela_map = {'cobranca': 'homologados_cobranca', 'pagamentos': 'homologados_pagamentos', 'extrato': 'homologados_extrato'}
    bloqueio = checar_tela(tela_map.get(tipo, tipo))
    if bloqueio:
        return bloqueio
    listar_fn, nome_aba, aba_ativa = _CONFIGS[tipo]
    registros      = getattr(banco, listar_fn)()
    lista_tecnicos = banco.listar_tecnicos()
    cores_tecnicos = {t['nome']: t['cor'] for t in lista_tecnicos}

    # Ordena: registro mais recente (maior id) primeiro — reflete a ordem da planilha invertida
    registros.sort(key=lambda r: r.get('id', 0), reverse=True)

    resumo_tecnicos = {}
    for reg in registros:
        tec = reg.get('tecnico') or 'SEM TEC.'
        resumo_tecnicos[tec] = resumo_tecnicos.get(tec, 0) + 1
    resumo_tecnicos = dict(sorted(resumo_tecnicos.items(), key=lambda x: x[1], reverse=True))
    return render_template(
        'aba_homologados.html',
        tipo=tipo, nome_aba=nome_aba, aba_ativa=aba_ativa,
        registros=registros, resumo_tecnicos=resumo_tecnicos,
        lista_tecnicos=lista_tecnicos, lista_servicos=banco.listar_servicos(),
        lista_status=banco.listar_status(),
        cores_tecnicos=cores_tecnicos,
    )


# ── Cobrança ──────────────────────────────────────────────

@homologados_bp.route('/homologados-cobranca')
def aba_homologados_cobranca():
    return _render('cobranca')

@homologados_bp.route('/homologados-cobranca/adicionar', methods=['POST'])
def adicionar_hom_cobranca():
    err = _sem_permissao()
    if err: return err
    id_novo = banco.adicionar_homologado_cobranca(request.get_json(), session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-cobranca/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_cobranca(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.atualizar_homologado_cobranca(id_registro, request.get_json())
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-cobranca/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_cobranca(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.deletar_homologado_cobranca(id_registro)
    return jsonify({'sucesso': True})


# ── Pagamentos ────────────────────────────────────────────

@homologados_bp.route('/homologados-pagamentos')
def aba_homologados_pagamentos():
    return _render('pagamentos')

@homologados_bp.route('/homologados-pagamentos/adicionar', methods=['POST'])
def adicionar_hom_pagamentos():
    err = _sem_permissao()
    if err: return err
    id_novo = banco.adicionar_homologado_pagamentos(request.get_json(), session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-pagamentos/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_pagamentos(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.atualizar_homologado_pagamentos(id_registro, request.get_json())
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-pagamentos/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_pagamentos(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.deletar_homologado_pagamentos(id_registro)
    return jsonify({'sucesso': True})


# ── Extrato ───────────────────────────────────────────────

@homologados_bp.route('/homologados-extrato')
def aba_homologados_extrato():
    return _render('extrato')

@homologados_bp.route('/homologados-extrato/adicionar', methods=['POST'])
def adicionar_hom_extrato():
    err = _sem_permissao()
    if err: return err
    id_novo = banco.adicionar_homologado_extrato(request.get_json(), session.get('usuario', ''))
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-extrato/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_extrato(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.atualizar_homologado_extrato(id_registro, request.get_json())
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-extrato/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_extrato(id_registro):
    err = _sem_permissao()
    if err: return err
    banco.deletar_homologado_extrato(id_registro)
    return jsonify({'sucesso': True})


# ── Mover homologado → pendente ou cancelado ──────────────

@homologados_bp.route('/homologados-<tipo>/retornar-pendente/<int:id_registro>', methods=['POST'])
def retornar_homologado_pendente(tipo, id_registro):
    if tipo not in _CONFIGS:
        return jsonify({'erro': 'Tipo inválido'}), 400
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    dados = request.get_json() or {}
    novo_status = dados.get('status', 'AGUARDANDO BANCO')
    id_novo = banco.mover_homologado_para_pendente(id_registro, tipo, novo_status)
    if id_novo:
        return jsonify({'sucesso': True, 'id_pendente': id_novo})
    return jsonify({'erro': 'Registro não encontrado'}), 404


@homologados_bp.route('/homologados-<tipo>/assumir/<int:id_registro>', methods=['POST'])
def assumir_homologado(tipo, id_registro):
    if tipo not in _CONFIGS:
        return jsonify({'erro': 'Tipo inválido'}), 400
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    tecnico = (session.get('tecnico_vinculado') or '').strip()
    if not tecnico:
        return jsonify({'erro': 'Seu usuário não tem técnico vinculado.'}), 400
    ok = banco.assumir_homologado(id_registro, tipo, tecnico)
    if ok:
        return jsonify({'sucesso': True, 'tecnico': tecnico})
    return jsonify({'erro': 'Registro não encontrado ou já possui técnico.'}), 404


@homologados_bp.route('/homologados-<tipo>/cancelar/<int:id_registro>', methods=['POST'])
def cancelar_homologado(tipo, id_registro):
    if tipo not in _CONFIGS:
        return jsonify({'erro': 'Tipo inválido'}), 400
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    id_novo = banco.mover_homologado_para_cancelado(id_registro, tipo)
    if id_novo:
        return jsonify({'sucesso': True, 'id_cancelado': id_novo})
    return jsonify({'erro': 'Registro não encontrado'}), 404
