import os
import re
import time
from collections import defaultdict
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
import banco
from planilha import ler_escritural_do_excel
from utils import checar_tela

escritural_bp = Blueprint('escritural', __name__)

_PASTA_UPLOADS = '/tmp' if os.environ.get('RENDER') else os.path.join(os.path.dirname(__file__), '..', 'uploads')

_CAMPOS_BASE_OBRIGATORIOS = (
    'empresa', 'cnpj', 'responsavel', 'fone_responsavel', 'email_responsavel',
    'banco', 'conta_corrente', 'agencia', 'convenio',
)
_CAMPOS_BOLETOS_OBRIGATORIOS = (
    'carteira', 'desc_carteira', 'variacao', 'juros', 'multa',
    'protesto', 'emissor', 'ultima_numeracao', 'solicitante', 'nome_solicitante',
)
_CAMPOS_BOLETOS_OPCIONAIS = ('cnab', 'obs_emissao')
_CAMPOS_FORNECEDORES_OBRIGATORIOS = ('modalidades', 'solicitante_pagto', 'nome_solicitante_pagto')
_CAMPOS_FORNECEDORES_OPCIONAIS = ('obs_pagto',)

_TAMANHO_MAX_CAMPO = 200
_TAMANHO_MAX_CAMPO_LONGO = 1000
_CAMPOS_LONGOS = {'protesto', 'modalidades', 'obs_emissao', 'obs_pagto'}

_REGEX_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_SERVICOS_PUBLICOS_VALIDOS = ('Emissão de Boletos.', 'Pagamento de Fornecedores.')
_EMISSOR_VALIDOS = ('Banco', 'Empresa')
_SOLICITANTE_BOLETOS_VALIDOS = ('Cliente Sisplan', 'Consultor Externo')
_SOLICITANTE_FORNECEDORES_VALIDOS = ('Cliente Sisplan', 'Consultores Externos')

_LIMITE_ENVIOS_POR_IP = 5
_JANELA_LIMITE_SEGUNDOS = 3600
_envios_por_ip = defaultdict(list)


def _ip_excedeu_limite(ip):
    agora = time.time()
    historico = [t for t in _envios_por_ip[ip] if agora - t < _JANELA_LIMITE_SEGUNDOS]
    _envios_por_ip[ip] = historico
    if len(historico) >= _LIMITE_ENVIOS_POR_IP:
        return True
    historico.append(agora)
    return False


def _ler_campo(dados, campo, obrigatorio):
    valor = dados.get(campo, '')
    if not isinstance(valor, str):
        return None, f'Campo inválido: {campo}.'
    valor = valor.strip()
    limite = _TAMANHO_MAX_CAMPO_LONGO if campo in _CAMPOS_LONGOS else _TAMANHO_MAX_CAMPO
    if obrigatorio and not valor:
        return None, f'Preencha o campo "{banco.LABELS_ESCRITURAL.get(campo, campo)}".'
    if len(valor) > limite:
        return None, f'O campo "{banco.LABELS_ESCRITURAL.get(campo, campo)}" é muito longo.'
    return valor, None


def _validar_formulario_publico(dados):
    """Valida e sanitiza o payload do formulário público (2 etapas, ramificado por
    serviço, igual ao Google Forms original). Retorna (dados_limpos, erro)."""
    if not isinstance(dados, dict):
        return None, 'Dados inválidos.'

    limpos = {}

    for campo in _CAMPOS_BASE_OBRIGATORIOS:
        valor, erro = _ler_campo(dados, campo, obrigatorio=True)
        if erro:
            return None, erro
        limpos[campo] = valor

    digitos_cnpj = re.sub(r'\D', '', limpos['cnpj'])
    if len(digitos_cnpj) != 14:
        return None, 'CNPJ inválido — informe os 14 dígitos.'

    if not _REGEX_EMAIL.match(limpos['email_responsavel']):
        return None, 'E-mail do responsável inválido.'

    digitos_fone = re.sub(r'\D', '', limpos['fone_responsavel'])
    if len(digitos_fone) < 8:
        return None, 'Telefone do responsável inválido.'

    servico, erro = _ler_campo(dados, 'servico', obrigatorio=True)
    if erro:
        return None, erro
    if servico not in _SERVICOS_PUBLICOS_VALIDOS:
        return None, 'Selecione um serviço válido.'
    limpos['servico'] = servico

    if servico == 'Emissão de Boletos.':
        for campo in _CAMPOS_BOLETOS_OBRIGATORIOS:
            valor, erro = _ler_campo(dados, campo, obrigatorio=True)
            if erro:
                return None, erro
            limpos[campo] = valor
        for campo in _CAMPOS_BOLETOS_OPCIONAIS:
            valor, erro = _ler_campo(dados, campo, obrigatorio=False)
            if erro:
                return None, erro
            limpos[campo] = valor
        if limpos['emissor'] not in _EMISSOR_VALIDOS:
            return None, 'Selecione o responsável pela emissão dos boletos.'
        if limpos['solicitante'] not in _SOLICITANTE_BOLETOS_VALIDOS:
            return None, 'Selecione quem está realizando a solicitação.'
        for campo in _CAMPOS_FORNECEDORES_OBRIGATORIOS + _CAMPOS_FORNECEDORES_OPCIONAIS:
            limpos[campo] = ''
    else:
        for campo in _CAMPOS_FORNECEDORES_OBRIGATORIOS:
            valor, erro = _ler_campo(dados, campo, obrigatorio=True)
            if erro:
                return None, erro
            limpos[campo] = valor
        for campo in _CAMPOS_FORNECEDORES_OPCIONAIS:
            valor, erro = _ler_campo(dados, campo, obrigatorio=False)
            if erro:
                return None, erro
            limpos[campo] = valor
        if limpos['solicitante_pagto'] not in _SOLICITANTE_FORNECEDORES_VALIDOS:
            return None, 'Selecione quem está realizando a solicitação.'
        for campo in _CAMPOS_BOLETOS_OBRIGATORIOS + _CAMPOS_BOLETOS_OPCIONAIS:
            limpos[campo] = ''

    return limpos, None


@escritural_bp.route('/escritural/formulario', methods=['GET'])
def formulario_publico():
    return render_template('escritural_publico.html')


@escritural_bp.route('/api/publico/bancos', methods=['GET'])
def api_publico_bancos():
    bancos = banco.listar_bancos_cadastro(apenas_ativos=True)
    return jsonify([{'id': b['id'], 'codigo': b['codigo'], 'nome': b['nome'], 'tem_api': b['tem_api']} for b in bancos])


@escritural_bp.route('/escritural/formulario/enviar', methods=['POST'])
def enviar_formulario_publico():
    corpo = request.get_json(silent=True) or {}

    # Honeypot: campo invisível que só bots preenchem. Se vier preenchido,
    # finge sucesso (não denuncia ao bot que foi detectado) mas não grava nada.
    if (corpo.get('confirmacao_contato') or '').strip():
        return jsonify({'sucesso': True})

    dados, erro = _validar_formulario_publico(corpo)
    if erro:
        return jsonify({'erro': erro}), 400

    # O limite só conta tentativas que passaram na validação: erros de digitação
    # não devem travar o usuário, mas uma onda de gravações reais sim.
    ip = request.remote_addr or 'desconhecido'
    if _ip_excedeu_limite(ip):
        return jsonify({'erro': 'Muitas solicitações enviadas recentemente. Tente novamente mais tarde.'}), 429

    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    status_lista = banco.listar_status_escritural()
    status_inicial = 'AGUARDANDO' if 'AGUARDANDO' in status_lista else (status_lista[0] if status_lista else 'AGUARDANDO')

    dados['status'] = status_inicial
    dados['data_solicitacao'] = agora
    dados['dt_status'] = agora

    banco.adicionar_escritural(dados, criado_por='Formulário público')

    from routes.discord_notif import notificar_nova_homologacao
    notificar_nova_homologacao(dados.get('empresa', ''))

    return jsonify({'sucesso': True})


@escritural_bp.route('/escritural')
def aba_escritural():
    bloqueio = checar_tela('escritural')
    if bloqueio:
        return bloqueio
    from flask import url_for
    from collections import Counter
    registros = banco.listar_escritural()
    resumo_banco = dict(
        sorted(Counter(r.get('banco') or 'Sem banco' for r in registros).items(),
               key=lambda x: x[1], reverse=True)
    )
    return render_template(
        'aba_escritural.html',
        registros=registros,
        campos=banco.CAMPOS_ESCRITURAL,
        labels=banco.LABELS_ESCRITURAL,
        lista_status=banco.listar_status_escritural(),
        link_publico=url_for('escritural.formulario_publico', _external=True),
        nao_lidos=banco.contar_nao_lidos_escritural(),
        resumo_banco=resumo_banco,
    )


def _log(tela, acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela=tela, acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@escritural_bp.route('/escritural/adicionar', methods=['POST'])
def adicionar_escritural():
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    dados = request.get_json() or {}
    id_novo = banco.adicionar_escritural(dados, criado_por=session.get('usuario', ''))
    _log('Escritural', 'INSERIU',
         f'Inseriu escritural #{id_novo} — {dados.get("empresa","?")} ({dados.get("banco","?")} · {dados.get("servico","?")})')
    return jsonify({'sucesso': True, 'id': id_novo})


@escritural_bp.route('/escritural/atualizar/<int:id_registro>', methods=['PUT'])
def atualizar_escritural(id_registro):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    dados = request.get_json() or {}
    banco.atualizar_escritural(id_registro, dados)
    _log('Escritural', 'EDITOU',
         f'Editou escritural #{id_registro} — {dados.get("empresa","?")}')
    return jsonify({'sucesso': True})


@escritural_bp.route('/escritural/deletar/<int:id_registro>', methods=['DELETE'])
def deletar_escritural(id_registro):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    empresa = banco.buscar_empresa_log('escritural', id_registro)
    banco.deletar_escritural(id_registro)
    _log('Escritural', 'DELETOU', f'Deletou escritural #{id_registro} — {empresa}')
    return jsonify({'sucesso': True})


@escritural_bp.route('/escritural/status/<int:id_registro>', methods=['PATCH'])
def atualizar_status_escritural(id_registro):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    novo_status = (request.get_json() or {}).get('status', '')
    if not novo_status:
        return jsonify({'erro': 'Status não informado'}), 400
    banco.atualizar_status_escritural(id_registro, novo_status)
    _log('Escritural', 'STATUS', f'Alterou status do escritural #{id_registro} → {novo_status}')
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
    _log('Escritural', 'IMPORTOU',
         f'Importou planilha: {len(registros)} lidos, {novos} novos, {len(registros)-novos} duplicados')
    return jsonify({
        'sucesso': True,
        'lidos': len(registros),
        'novos': novos,
        'duplicados': len(registros) - novos,
    })
