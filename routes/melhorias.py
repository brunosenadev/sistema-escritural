from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import banco
from utils import usuario_logado, pode_editar

melhorias_bp = Blueprint('melhorias', __name__)

_SETORES_PERMITIDOS = {'PROGRAMAÇÃO'}


def _acesso_melhorias():
    if not usuario_logado():
        return redirect(url_for('auth.login'))
    setor = (session.get('setor') or '').upper().strip()
    nivel = session.get('nivel_acesso', '')
    if nivel != 'admin' and setor not in _SETORES_PERMITIDOS:
        return redirect(url_for('pendente.aba_pendente'))
    return None


def _sem_permissao():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not pode_editar():
        return jsonify({'erro': 'Sem permissão'}), 403
    return None


@melhorias_bp.route('/melhorias')
def aba_melhorias():
    bloqueio = _acesso_melhorias()
    if bloqueio:
        return bloqueio
    todas = banco.listar_melhorias()
    por_estagio = {'em_analise': [], 'em_programacao': [], 'concluida': [], 'rejeitada': []}
    for m in todas:
        estagio = m.get('estagio', 'em_analise')
        if estagio in por_estagio:
            por_estagio[estagio].append(m)
    tecnicos = banco.listar_tecnicos()
    return render_template('aba_melhorias.html', por_estagio=por_estagio, tecnicos=tecnicos)


@melhorias_bp.route('/melhorias/adicionar', methods=['POST'])
def api_adicionar_melhoria():
    bloqueio = _sem_permissao()
    if bloqueio:
        return bloqueio
    dados = request.get_json() or {}
    dados['criado_por'] = session.get('nome', '')
    novo_id = banco.adicionar_melhoria(dados)
    return jsonify({'sucesso': True, 'id': novo_id})


@melhorias_bp.route('/melhorias/atualizar/<int:id_melhoria>', methods=['PUT'])
def api_atualizar_melhoria(id_melhoria):
    bloqueio = _sem_permissao()
    if bloqueio:
        return bloqueio
    banco.atualizar_melhoria(id_melhoria, request.get_json() or {})
    return jsonify({'sucesso': True})


@melhorias_bp.route('/melhorias/mover/<int:id_melhoria>', methods=['POST'])
def api_mover_melhoria(id_melhoria):
    bloqueio = _sem_permissao()
    if bloqueio:
        return bloqueio
    dados = request.get_json() or {}
    estagio = dados.get('estagio', '')
    motivo = dados.get('motivo', '')
    estagios_validos = ('em_analise', 'em_programacao', 'concluida', 'rejeitada')
    if estagio not in estagios_validos:
        return jsonify({'erro': 'Estágio inválido'}), 400
    banco.mover_estagio_melhoria(id_melhoria, estagio, motivo)
    return jsonify({'sucesso': True})


@melhorias_bp.route('/melhorias/deletar/<int:id_melhoria>', methods=['DELETE'])
def api_deletar_melhoria(id_melhoria):
    bloqueio = _sem_permissao()
    if bloqueio:
        return bloqueio
    banco.remover_melhoria(id_melhoria)
    return jsonify({'sucesso': True})
