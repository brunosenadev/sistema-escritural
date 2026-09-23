from flask import Blueprint, render_template, request, jsonify, session
import banco
import exclusoes
from utils import usuario_logado, pode_editar, checar_tela

pendente_bp = Blueprint('pendente', __name__)


def _sem_permissao():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not pode_editar():
        return jsonify({'erro': 'Sem permissão para editar.'}), 403
    return None


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Pendentes', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


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
        lista_servicos_mapa={s['texto']: s['destino_homologado'] for s in banco.listar_servicos_completo()},
        cores_tecnicos=cores_tecnicos,
        tecnico_padrao=banco.get_config('tecnico_padrao'),
        sla_conf=banco.listar_sla_config(),
    )


@pendente_bp.route('/api/pendente/versao')
def api_pendente_versao():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    conn = banco.conectar()
    row = conn.execute(
        "SELECT COUNT(*) as total, COALESCE(MAX(id), 0) as max_id FROM pendentes WHERE status != 'CANCELADO'"
    ).fetchone()
    conn.close()
    return jsonify({'total': row['total'], 'max_id': row['max_id']})


@pendente_bp.route('/pendente/adicionar', methods=['POST'])
def adicionar_pendente():
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    dados['status'] = 'FALTA CADASTRAR'
    tec = (dados.get('tecnico') or '').strip()
    if not tec or tec.upper() == 'SEM TEC.':
        tec = (banco.get_config('tecnico_padrao') or '').strip()
    if not tec:
        return jsonify({'erro': 'Técnico é obrigatório.'}), 400
    dados['tecnico'] = tec
    id_novo = banco.adicionar_pendente(dados, criado_por=session.get('usuario', ''))
    _log('INSERIU', f'Inseriu pendente #{id_novo} — {dados.get("empresa","?")} ({dados.get("banco","?")} · {dados.get("servico","?")})')
    return jsonify({'sucesso': True, 'id': id_novo})


@pendente_bp.route('/pendente/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    dados = request.get_json() or {}
    banco.atualizar_pendente(id_registro, dados)
    _log('EDITOU', f'Editou pendente #{id_registro} — {dados.get("empresa","?")}')
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
    _log('STATUS', f'Alterou status do pendente #{id_registro} → {novo_status}')
    return jsonify({'sucesso': True, 'dt_status': _dt.now().strftime('%d/%m/%Y')})


@pendente_bp.route('/pendente/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('pendentes', id_registro)
    payload, status = exclusoes.processar_exclusao(
        'pendente', id_registro, f'Pendente #{id_registro} — {empresa}', 'Pendentes', _log
    )
    return jsonify(payload), status


@pendente_bp.route('/pendente/cancelar/<int:id_registro>', methods=['POST'])
def cancelar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('pendentes', id_registro)
    id_novo = banco.mover_pendente_para_cancelado(id_registro)
    if id_novo:
        _log('MOVEU', f'Moveu pendente #{id_registro} ({empresa}) → Cancelados #{id_novo}')
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
        _log('ASSUMIU', f'Assumiu pendente #{id_registro} → técnico {tecnico}')
        tec_sessao = (session.get('tecnico_vinculado') or '').strip()
        if tecnico.lower() != tec_sessao.lower():
            dest = banco.buscar_usuario_por_tecnico(tecnico)
            if dest:
                quem = session.get('nome', 'Alguém')
                banco.criar_notificacao(
                    dest['id'],
                    f'Pendente #{id_registro} atribuído a você',
                    f'{quem} te atribuiu uma nova pendente.',
                    'info',
                )
        return jsonify({'sucesso': True, 'tecnico': tecnico})
    return jsonify({'erro': 'Registro não encontrado ou já possui técnico.'}), 404


@pendente_bp.route('/pendente/obs-interna/<int:id_registro>', methods=['PATCH'])
def atualizar_obs_interna(id_registro):
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    texto = (request.get_json() or {}).get('obs_interna', '')
    banco.salvar_obs_interna(id_registro, texto)
    _log('OBS', f'Obs. interna atualizada no pendente #{id_registro}')
    return jsonify({'sucesso': True})


@pendente_bp.route('/pendente/homologar/<int:id_registro>', methods=['POST'])
def homologar_pendente(id_registro):
    err = _sem_permissao()
    if err: return err
    empresa = banco.buscar_empresa_log('pendentes', id_registro)
    id_novo, aba, dados_pend = banco.mover_pendente_para_homologado(id_registro)
    if id_novo:
        nomes = {
            'cobranca':   'Hom. Cobrança',
            'pagamentos': 'Hom. Pagamentos',
            'extrato':    'Hom. Extrato Cartão',
            'ext_bancario': 'Hom. Extrato Bancário',
        }
        _log('MOVEU', f'Homologou pendente #{id_registro} ({empresa}) → {nomes.get(aba, aba)} #{id_novo}')

        try:
            dono = banco.buscar_usuario_por_tecnico(dados_pend.get('tecnico', ''))
            banco.criar_os({
                'usuario_id':     dono['id'] if dono else None,
                'tecnico':        dados_pend.get('tecnico', ''),
                'empresa':        dados_pend.get('empresa', ''),
                'banco':          dados_pend.get('banco', ''),
                'servico':        dados_pend.get('servico', ''),
                'aba_homologado': aba,
                'id_homologado':  id_novo,
            })
        except Exception:
            pass  # a homologação já foi efetivada; falha ao gerar a O.S. não pode travar o fluxo

        return jsonify({'sucesso': True, 'id_homologado': id_novo, 'aba': aba, 'nome_aba': nomes.get(aba, aba)})
    return jsonify({'erro': 'Registro não encontrado'}), 404
