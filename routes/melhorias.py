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


@melhorias_bp.route('/melhorias')
def aba_melhorias():
    err = _guard_ver()
    if err:
        return err
    todas = banco.listar_melhorias()
    por_estagio = {'em_analise': [], 'em_programacao': [], 'concluida': [], 'rejeitada': []}
    for m in todas:
        estagio = m.get('estagio', 'em_analise')
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
    # SUPORTE só pode criar em análise
    if not _pode_mover():
        dados['estagio'] = 'em_analise'
    novo_id = banco.adicionar_melhoria(dados)
    return jsonify({'sucesso': True, 'id': novo_id})


@melhorias_bp.route('/melhorias/atualizar/<int:id_melhoria>', methods=['PUT'])
def api_atualizar_melhoria(id_melhoria):
    err = _guard_mover()
    if err:
        return err
    banco.atualizar_melhoria(id_melhoria, request.get_json() or {})
    return jsonify({'sucesso': True})


@melhorias_bp.route('/melhorias/mover/<int:id_melhoria>', methods=['POST'])
def api_mover_melhoria(id_melhoria):
    err = _guard_mover()
    if err:
        return err
    dados = request.get_json() or {}
    estagio = dados.get('estagio', '')
    if estagio not in ('em_analise', 'em_programacao', 'concluida', 'rejeitada'):
        return jsonify({'erro': 'Estágio inválido'}), 400
    banco.mover_estagio_melhoria(id_melhoria, estagio, dados.get('motivo', ''))
    return jsonify({'sucesso': True})


@melhorias_bp.route('/melhorias/deletar/<int:id_melhoria>', methods=['DELETE'])
def api_deletar_melhoria(id_melhoria):
    err = _guard_mover()
    if err:
        return err
    banco.remover_melhoria(id_melhoria)
    return jsonify({'sucesso': True})
