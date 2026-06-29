import os
from flask import Blueprint, request, jsonify, send_file, session
import banco
from planilha import ler_planilha_completa, exportar_pendentes_para_excel
from utils import usuario_logado, checar_login

importacao_bp = Blueprint('importacao', __name__)

_PASTA_UPLOADS = '/tmp' if os.environ.get('RENDER') else os.path.join(os.path.dirname(__file__), '..', 'uploads')


def _checar_admin():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão.'}), 403
    return None


def _salvar_temp(arquivo):
    os.makedirs(_PASTA_UPLOADS, exist_ok=True)
    caminho = os.path.join(_PASTA_UPLOADS, 'importacao_temp.xlsx')
    arquivo.save(caminho)
    return caminho


@importacao_bp.route('/importar-planilha', methods=['POST'])
def importar_planilha():
    err = _checar_admin()
    if err:
        return err

    if 'arquivo' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado.'}), 400

    arq = request.files['arquivo']
    if os.path.splitext(arq.filename)[1].lower() not in ('.xlsx', '.xls'):
        return jsonify({'erro': 'O arquivo deve ser .xlsx ou .xls.'}), 400

    caminho    = _salvar_temp(arq)
    substituir = request.form.get('modo', 'substituir') == 'substituir'
    dados      = ler_planilha_completa(caminho)

    if not dados:
        return jsonify({'erro': 'Não foi possível abrir o arquivo.'}), 400

    totais = {}

    if dados.get('pendente'):
        totais['pendente'] = banco.importar_pendentes(dados['pendente'], substituir=substituir)
        # Move imediatamente qualquer HOMOLOGADO/CANCELADO que vieram na aba Pendente
        banco.migrar_pendentes_legados()

    if dados.get('cobranca'):
        totais['cobranca'] = banco.importar_homologados_cobranca(dados['cobranca'], substituir=substituir)

    if dados.get('pagamentos'):
        totais['pagamentos'] = banco.importar_homologados_pagamentos(dados['pagamentos'], substituir=substituir)

    if dados.get('extrato'):
        totais['extrato'] = banco.importar_homologados_extrato(dados['extrato'], substituir=substituir)

    if dados.get('cancelados'):
        totais['cancelados'] = banco.importar_cancelados(dados['cancelados'], substituir=substituir)

    if not totais:
        return jsonify({'erro': 'Nenhuma aba reconhecida na planilha.'}), 400

    importados = {k: len(dados[k]) for k in totais}
    return jsonify({'sucesso': True, 'importados': importados, 'totais_banco': totais})


@importacao_bp.route('/exportar-planilha')
def exportar_planilha():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio

    registros = banco.listar_pendentes()
    os.makedirs(_PASTA_UPLOADS, exist_ok=True)
    caminho = os.path.join(_PASTA_UPLOADS, 'exportacao_pendente.xlsx')
    exportar_pendentes_para_excel(registros, caminho)

    return send_file(caminho, as_attachment=True, download_name='pendente_exportado.xlsx')
