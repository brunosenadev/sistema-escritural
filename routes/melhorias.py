from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import banco
from utils import usuario_logado, checar_tela

melhorias_bp = Blueprint('melhorias', __name__)

_SETORES_VISUALIZACAO = {'PROGRAMAÇÃO', 'SUPORTE'}
_SETORES_EDICAO       = {'PROGRAMAÇÃO'}


def _setor():
    return (session.get('setor') or '').upper().strip()

def _nivel():
    return session.get('nivel_acesso', '')

def _pode_criar():
    return _nivel() in ('admin', 'master') or _setor() in _SETORES_VISUALIZACAO

def _pode_mover():
    return _nivel() in ('admin', 'master') or _setor() in _SETORES_EDICAO


def _guard_ver():
    bloqueio = checar_tela('melhorias')
    return bloqueio

def _guard_criar():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not _pode_criar():
        return jsonify({'erro': 'Sem permissão'}), 403
    return None

def _guard_mover():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not _pode_mover():
        return jsonify({'erro': 'Sem permissão'}), 403
    return None


def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Melhorias', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@melhorias_bp.route('/melhorias')
def aba_melhorias():
    err = _guard_ver()
    if err:
        return err
    todas = banco.listar_melhorias()
    por_estagio = {'analisa': [], 'em_analise': [], 'em_programacao': [], 'concluida': [], 'rejeitada': []}
    for m in todas:
        estagio = m.get('estagio', 'analisa')
        if estagio in por_estagio:
            por_estagio[estagio].append(m)
    return render_template(
        'aba_melhorias.html',
        por_estagio=por_estagio,
        programadores=banco.listar_programadores(),
        pode_mover=_pode_mover(),
        pode_criar=_pode_criar(),
    )


@melhorias_bp.route('/melhorias/adicionar', methods=['POST'])
def api_adicionar_melhoria():
    err = _guard_criar()
    if err:
        return err
    dados = request.get_json() or {}
    dados['criado_por'] = session.get('nome', '')
    if not _pode_mover():
        dados['estagio'] = 'analisa'
    novo_id = banco.adicionar_melhoria(dados)
    _log('INSERIU', f'Criou melhoria #{novo_id} — {dados.get("titulo", dados.get("descricao","?"))[:80]}')
    titulo_mel = (dados.get('titulo') or dados.get('descricao') or '')[:60]
    quem = session.get('nome', 'Alguém')
    for u in banco.listar_usuarios_com_flag('recebe_aviso_melhorias'):
        banco.criar_notificacao(
            u['id'],
            f'Nova melhoria #{novo_id}',
            f'{quem}: {titulo_mel}',
            'info',
        )
    return jsonify({'sucesso': True, 'id': novo_id})


@melhorias_bp.route('/melhorias/atualizar/<int:id_melhoria>', methods=['PUT'])
def api_atualizar_melhoria(id_melhoria):
    err = _guard_mover()
    if err:
        return err
    dados = request.get_json() or {}
    banco.atualizar_melhoria(id_melhoria, dados)
    _log('EDITOU', f'Editou melhoria #{id_melhoria}')
    return jsonify({'sucesso': True})


@melhorias_bp.route('/melhorias/mover/<int:id_melhoria>', methods=['POST'])
def api_mover_melhoria(id_melhoria):
    err = _guard_mover()
    if err:
        return err
    dados = request.get_json() or {}
    estagio = dados.get('estagio', '')
    if estagio not in ('analisa', 'em_analise', 'em_programacao', 'concluida', 'rejeitada'):
        return jsonify({'erro': 'Estágio inválido'}), 400
    banco.mover_estagio_melhoria(id_melhoria, estagio, dados.get('motivo', ''))
    _log('MOVEU', f'Moveu melhoria #{id_melhoria} → {estagio}')
    return jsonify({'sucesso': True})


@melhorias_bp.route('/melhorias/deletar/<int:id_melhoria>', methods=['DELETE'])
def api_deletar_melhoria(id_melhoria):
    err = _guard_mover()
    if err:
        return err
    banco.remover_melhoria(id_melhoria)
    _log('DELETOU', f'Deletou melhoria #{id_melhoria}')
    return jsonify({'sucesso': True})
