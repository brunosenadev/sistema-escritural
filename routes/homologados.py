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
    'cobranca':     ('listar_homologados_cobranca',       'Homologados Cobrança',          'homologados_cobranca'),
    'pagamentos':   ('listar_homologados_pagamentos',     'Homologados Pagamentos',         'homologados_pagamentos'),
    'extrato':      ('listar_homologados_extrato',        'Homologados Extrato Cartão',     'homologados_extrato'),
    'ext-bancario': ('listar_homologados_ext_bancario',  'Homologados Extrato Bancário',   'homologados_ext_bancario'),
}

_NOME_ABA = {
    'cobranca':     'Hom. Cobrança',
    'pagamentos':   'Hom. Pagamentos',
    'extrato':      'Hom. Extrato Cartão',
    'ext-bancario': 'Hom. Extrato Bancário',
}

_TABELA_DB = {
    'cobranca':     'homologados_cobranca',
    'pagamentos':   'homologados_pagamentos',
    'extrato':      'homologados_extrato',
    'ext-bancario': 'homologados_ext_bancario',
}


def _log(tipo, acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela=_NOME_ABA.get(tipo, tipo), acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


def _chave_data(s):
    if not s or s.strip() == '':
        return '0000/00/00'
    partes = s.strip().split('/')
    if len(partes) == 3:
        return f'{partes[2]}/{partes[1]}/{partes[0]}'
    return '0000/00/00'


def _render(tipo):
    tela_map = {
        'cobranca':     'homologados_cobranca',
        'pagamentos':   'homologados_pagamentos',
        'extrato':      'homologados_extrato',
        'ext-bancario': 'homologados_ext_bancario',
    }
    bloqueio = checar_tela(tela_map.get(tipo, tipo))
    if bloqueio:
        return bloqueio
    listar_fn, nome_aba, aba_ativa = _CONFIGS[tipo]
    registros      = getattr(banco, listar_fn)()
    lista_tecnicos = banco.listar_tecnicos()
    cores_tecnicos = banco.cores_por_tecnico()

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
    dados = request.get_json() or {}
    id_novo = banco.adicionar_homologado_cobranca(dados, session.get('usuario', ''))
    _log('cobranca', 'INSERIU', f'Inseriu Hom. Cobrança #{id_novo} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-cobranca/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_cobranca(id_registro):
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    banco.atualizar_homologado_cobranca(id_registro, dados)
    _log('cobranca', 'EDITOU', f'Editou Hom. Cobrança #{id_registro} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-cobranca/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_cobranca(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('homologados_cobranca', id_registro)
    banco.deletar_homologado_cobranca(id_registro)
    _log('cobranca', 'DELETOU', f'Deletou Hom. Cobrança #{id_registro} — {empresa}')
    return jsonify({'sucesso': True})


# ── Pagamentos ────────────────────────────────────────────

@homologados_bp.route('/homologados-pagamentos')
def aba_homologados_pagamentos():
    return _render('pagamentos')

@homologados_bp.route('/homologados-pagamentos/adicionar', methods=['POST'])
def adicionar_hom_pagamentos():
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    id_novo = banco.adicionar_homologado_pagamentos(dados, session.get('usuario', ''))
    _log('pagamentos', 'INSERIU', f'Inseriu Hom. Pagamentos #{id_novo} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-pagamentos/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_pagamentos(id_registro):
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    banco.atualizar_homologado_pagamentos(id_registro, dados)
    _log('pagamentos', 'EDITOU', f'Editou Hom. Pagamentos #{id_registro} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-pagamentos/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_pagamentos(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('homologados_pagamentos', id_registro)
    banco.deletar_homologado_pagamentos(id_registro)
    _log('pagamentos', 'DELETOU', f'Deletou Hom. Pagamentos #{id_registro} — {empresa}')
    return jsonify({'sucesso': True})


# ── Extrato ───────────────────────────────────────────────

@homologados_bp.route('/homologados-extrato')
def aba_homologados_extrato():
    return _render('extrato')

@homologados_bp.route('/homologados-extrato/adicionar', methods=['POST'])
def adicionar_hom_extrato():
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    id_novo = banco.adicionar_homologado_extrato(dados, session.get('usuario', ''))
    _log('extrato', 'INSERIU', f'Inseriu Hom. Extrato Cartão #{id_novo} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-extrato/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_extrato(id_registro):
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    banco.atualizar_homologado_extrato(id_registro, dados)
    _log('extrato', 'EDITOU', f'Editou Hom. Extrato Cartão #{id_registro} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-extrato/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_extrato(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('homologados_extrato', id_registro)
    banco.deletar_homologado_extrato(id_registro)
    _log('extrato', 'DELETOU', f'Deletou Hom. Extrato Cartão #{id_registro} — {empresa}')
    return jsonify({'sucesso': True})


# ── Extrato Bancário ──────────────────────────────────────

@homologados_bp.route('/homologados-ext-bancario')
def aba_homologados_ext_bancario():
    return _render('ext-bancario')

@homologados_bp.route('/homologados-ext-bancario/adicionar', methods=['POST'])
def adicionar_hom_ext_bancario():
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    id_novo = banco.adicionar_homologado_ext_bancario(dados, session.get('usuario', ''))
    _log('ext-bancario', 'INSERIU', f'Inseriu Hom. Extrato Bancário #{id_novo} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True, 'id': id_novo})

@homologados_bp.route('/homologados-ext-bancario/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_hom_ext_bancario(id_registro):
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    banco.atualizar_homologado_ext_bancario(id_registro, dados)
    _log('ext-bancario', 'EDITOU', f'Editou Hom. Extrato Bancário #{id_registro} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True})

@homologados_bp.route('/homologados-ext-bancario/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_hom_ext_bancario(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('homologados_ext_bancario', id_registro)
    banco.deletar_homologado_ext_bancario(id_registro)
    _log('ext-bancario', 'DELETOU', f'Deletou Hom. Extrato Bancário #{id_registro} — {empresa}')
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
    empresa = banco.buscar_empresa_log(_TABELA_DB.get(tipo, ''), id_registro)
    id_novo = banco.mover_homologado_para_pendente(id_registro, tipo, novo_status)
    if id_novo:
        _log(tipo, 'MOVEU', f'Retornou {_NOME_ABA[tipo]} #{id_registro} ({empresa}) → Pendentes #{id_novo}')
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
        _log(tipo, 'ASSUMIU', f'Assumiu {_NOME_ABA[tipo]} #{id_registro} → técnico {tecnico}')
        return jsonify({'sucesso': True, 'tecnico': tecnico})
    return jsonify({'erro': 'Registro não encontrado ou já possui técnico.'}), 404


@homologados_bp.route('/homologados-<tipo>/gerar-os/<int:id_registro>', methods=['POST'])
def gerar_os_homologado(tipo, id_registro):
    if tipo not in _CONFIGS:
        return jsonify({'erro': 'Tipo inválido'}), 400
    err = _sem_permissao()
    if err: return err
    reg = banco.buscar_registro_homologado(_TABELA_DB[tipo], id_registro)
    if not reg:
        return jsonify({'erro': 'Registro não encontrado'}), 404
    dono = banco.buscar_usuario_por_tecnico(reg.get('tecnico', ''))
    id_os = banco.criar_os({
        'usuario_id':     dono['id'] if dono else None,
        'tecnico':        reg.get('tecnico', ''),
        'empresa':        reg.get('empresa', ''),
        'banco':          reg.get('banco', ''),
        'servico':        reg.get('servico', ''),
        'aba_homologado': tipo.replace('-', '_'),
        'id_homologado':  id_registro,
    })
    _log(tipo, 'OS_CRIADA', f'Gerou nova O.S. #{id_os} para {_NOME_ABA[tipo]} #{id_registro} ({reg.get("empresa","?")})')
    return jsonify({'sucesso': True, 'id_os': id_os, 'tecnico': dono['nome'] if dono else None})


@homologados_bp.route('/homologados-<tipo>/cancelar/<int:id_registro>', methods=['POST'])
def cancelar_homologado(tipo, id_registro):
    if tipo not in _CONFIGS:
        return jsonify({'erro': 'Tipo inválido'}), 400
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    empresa = banco.buscar_empresa_log(_TABELA_DB.get(tipo, ''), id_registro)
    id_novo = banco.mover_homologado_para_cancelado(id_registro, tipo)
    if id_novo:
        _log(tipo, 'MOVEU', f'Cancelou {_NOME_ABA[tipo]} #{id_registro} ({empresa}) → Cancelados #{id_novo}')
        return jsonify({'sucesso': True, 'id_cancelado': id_novo})
    return jsonify({'erro': 'Registro não encontrado'}), 404
