from flask import Blueprint, render_template, request, jsonify, session, make_response, current_app
import banco
import os
import uuid
from werkzeug.utils import secure_filename
from utils import checar_admin, checar_login, usuario_logado, criar_tokens, _preencher_sessao, tem_acesso_tela

config_bp = Blueprint('config', __name__)


def _log(tela, acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela=tela, acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@config_bp.route('/api/contadores')
def api_contadores():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify(banco.contar_todos())


@config_bp.route('/configuracoes')
def pagina_configuracoes():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio
    if session.get('nivel_acesso') not in ('admin', 'master') \
            and not tem_acesso_tela('importar_homologacoes_pendentes') \
            and not tem_acesso_tela('importar_novas_homologacoes') \
            and not tem_acesso_tela('escritural'):
        return checar_admin()
    contadores = banco.contar_todos()
    return render_template(
        'configuracoes.html',
        tecnicos=banco.listar_tecnicos(),
        usuarios=banco.listar_usuarios(),
        lista_status=banco.listar_status(),
        lista_status_escritural=banco.listar_status_escritural(),
        lista_servicos=banco.listar_servicos_completo(),
        lista_setores=banco.listar_setores(),
        total_pendentes=contadores['pendentes'],
        total_hom_cobranca_db=contadores['cobranca'],
        total_hom_pagamentos_db=contadores['pagamentos'],
        total_hom_extrato_db=contadores['extrato'],
        total_cancelados_db=contadores['cancelados'],
    )


# ── API Técnicos ──────────────────────────────────────────

@config_bp.route('/api/tecnicos', methods=['POST'])
def api_adicionar_tecnico():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d  = request.get_json()
    nome = d.get('nome', '')
    ok = banco.adicionar_tecnico(nome, '#64748b')
    if ok:
        _log('Configurações', 'INSERIU', f'Adicionou técnico: {nome}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Técnico já cadastrado.'}), 409)


@config_bp.route('/api/tecnicos/<nome>', methods=['PUT'])
def api_atualizar_tecnico(nome):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json()
    novo_nome = d.get('nome', nome)
    banco.atualizar_tecnico(nome, novo_nome, '#64748b')
    _log('Configurações', 'EDITOU', f'Renomeou técnico: {nome} → {novo_nome}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/tecnicos/<nome>', methods=['DELETE'])
def api_remover_tecnico(nome):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_tecnico(nome)
    _log('Configurações', 'DELETOU', f'Removeu técnico: {nome}')
    return jsonify({'sucesso': True})


# ── API Usuários ──────────────────────────────────────────

@config_bp.route('/api/usuarios', methods=['POST'])
def api_adicionar_usuario():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json()
    ok = banco.adicionar_usuario(d)
    if ok:
        _log('Configurações', 'INSERIU', f'Criou usuário: {d.get("usuario","")} ({d.get("nome","")})')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Login já cadastrado.'}), 409)


@config_bp.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
def api_atualizar_usuario(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if alvo and alvo.get('nivel') == 'master' and id_usuario != session.get('id_usuario'):
        return jsonify({'erro': 'Usuário master não pode ser editado.'}), 403
    dados = request.get_json()
    if alvo and alvo.get('nivel') == 'master':
        dados['nivel'] = 'master'
    banco.atualizar_usuario(id_usuario, dados)
    _log('Configurações', 'EDITOU', f'Editou usuário #{id_usuario} — {alvo.get("nome","") if alvo else "?"}')
    if id_usuario == session.get('id_usuario'):
        u = banco.buscar_usuario_por_id(id_usuario)
        _preencher_sessao({
            'usr': u['usuario'], 'nome': u['nome'], 'niv': u['nivel'],
            'tec': u.get('tecnico_vinculado') or '', 'tema': u.get('tema') or 'light',
            'sub': u['id'], 'mp': int(u.get('mudar_senha') or 0),
            'cor': u.get('cor') or '', 'setor': u.get('setor') or '',
        })
        access, *_ = criar_tokens(u)
        resp = make_response(jsonify({'sucesso': True}))
        resp.set_cookie('access_token', access, max_age=15*60, httponly=True, samesite='Lax', path='/')
        return resp
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>/resetar-senha', methods=['POST'])
def api_resetar_senha(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo = banco.buscar_usuario_por_id(id_usuario)
    banco.resetar_senha_usuario(id_usuario)
    _log('Configurações', 'SENHA', f'Resetou senha do usuário #{id_usuario} — {alvo.get("nome","") if alvo else "?"}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>/limpar-troca', methods=['POST'])
def api_limpar_troca(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.limpar_mudar_senha(id_usuario)
    return jsonify({'sucesso': True})


@config_bp.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
def api_remover_usuario(id_usuario):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    alvo = banco.buscar_usuario_por_id(id_usuario)
    if alvo and alvo.get('nivel') == 'master':
        return jsonify({'erro': 'Usuário master não pode ser removido.'}), 403
    ok = banco.remover_usuario(id_usuario)
    if ok:
        _log('Configurações', 'DELETOU', f'Removeu usuário #{id_usuario} — {alvo.get("nome","") if alvo else "?"}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Não é possível remover o único administrador.'}), 400)


# ── API Status ────────────────────────────────────────────

@config_bp.route('/api/status', methods=['POST'])
def api_adicionar_status():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    texto = request.get_json().get('texto', '')
    ok = banco.adicionar_status(texto)
    if ok:
        _log('Configurações', 'INSERIU', f'Adicionou status: {texto}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Status já cadastrado.'}), 409)


@config_bp.route('/api/status/<path:texto>', methods=['DELETE'])
def api_remover_status(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_status(texto)
    _log('Configurações', 'DELETOU', f'Removeu status: {texto}')
    return jsonify({'sucesso': True})


# ── API Status (Novos Escriturais) ────────────────────────

@config_bp.route('/api/status-escritural', methods=['POST'])
def api_adicionar_status_escritural():
    if not usuario_logado() or not tem_acesso_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    texto = request.get_json().get('texto', '')
    ok = banco.adicionar_status_escritural(texto)
    if ok:
        _log('Configurações', 'INSERIU', f'Adicionou status escritural: {texto}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Status já cadastrado.'}), 409)


@config_bp.route('/api/status-escritural/<path:texto>', methods=['DELETE'])
def api_remover_status_escritural(texto):
    if not usuario_logado() or not tem_acesso_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_status_escritural(texto)
    _log('Configurações', 'DELETOU', f'Removeu status escritural: {texto}')
    return jsonify({'sucesso': True})


# ── API Serviços ──────────────────────────────────────────

@config_bp.route('/api/servicos', methods=['POST'])
def api_adicionar_servico():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    texto = request.get_json().get('texto', '')
    ok = banco.adicionar_servico(texto)
    if ok:
        _log('Configurações', 'INSERIU', f'Adicionou serviço: {texto}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Serviço já cadastrado.'}), 409)


@config_bp.route('/api/servicos/<path:texto>', methods=['PUT'])
def api_atualizar_servico(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    destino = d.get('destino', '')
    banco.atualizar_destino_servico(texto, destino)
    _log('Configurações', 'EDITOU', f'Alterou destino do serviço "{texto}" → {destino}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/servicos/<path:texto>', methods=['DELETE'])
def api_remover_servico(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_servico(texto)
    _log('Configurações', 'DELETOU', f'Removeu serviço: {texto}')
    return jsonify({'sucesso': True})


# ── API Setores ───────────────────────────────────────────

@config_bp.route('/api/setores', methods=['POST'])
def api_adicionar_setor():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    texto = request.get_json().get('texto', '')
    ok = banco.adicionar_setor(texto)
    if ok:
        _log('Configurações', 'INSERIU', f'Adicionou setor: {texto}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Setor já cadastrado.'}), 409)


@config_bp.route('/api/setores/<path:texto>', methods=['DELETE'])
def api_remover_setor(texto):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_setor(texto)
    _log('Configurações', 'DELETOU', f'Removeu setor: {texto}')
    return jsonify({'sucesso': True})


# ── API Bancos Cadastro ───────────────────────────────────

@config_bp.route('/api/bancos-cadastro', methods=['GET'])
def api_listar_bancos_cadastro():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify(banco.listar_bancos_cadastro())


@config_bp.route('/api/bancos-cadastro', methods=['POST'])
def api_adicionar_banco_cadastro():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    codigo = (d.get('codigo') or '').strip()
    nome   = (d.get('nome') or '').strip()
    if not codigo or not nome:
        return jsonify({'erro': 'Código e nome são obrigatórios.'}), 400
    ok = banco.adicionar_banco_cadastro(codigo, nome, d.get('tem_api', 0))
    if ok:
        _log('Configurações', 'INSERIU', f'Adicionou banco: {codigo} - {nome}')
    return jsonify({'sucesso': True}) if ok else (jsonify({'erro': 'Erro ao inserir banco.'}), 500)


@config_bp.route('/api/bancos-cadastro/<int:id_banco>', methods=['PUT'])
def api_atualizar_banco_cadastro(id_banco):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    codigo = (d.get('codigo') or '').strip()
    nome   = (d.get('nome') or '').strip()
    if not codigo or not nome:
        return jsonify({'erro': 'Código e nome são obrigatórios.'}), 400
    banco.atualizar_banco_cadastro(id_banco, codigo, nome, d.get('tem_api', 0), d.get('ativo', 1))
    _log('Configurações', 'EDITOU', f'Editou banco #{id_banco}: {codigo} - {nome}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/bancos-cadastro/<int:id_banco>', methods=['DELETE'])
def api_remover_banco_cadastro(id_banco):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_banco_cadastro(id_banco)
    _log('Configurações', 'DELETOU', f'Removeu banco #{id_banco}')
    return jsonify({'sucesso': True})


_EXTENSOES_IMAGEM = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
_RE_LOGIN_SEGURO = __import__('re').compile(r'[^A-Za-z0-9_\-]')

@config_bp.route('/api/upload-assinatura', methods=['POST'])
def api_upload_assinatura():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    arquivo = request.files.get('imagem')
    usuario_id = request.form.get('usuario_id', '').strip()
    if not arquivo or not arquivo.filename:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
    ext = arquivo.filename.rsplit('.', 1)[-1].lower() if '.' in arquivo.filename else ''
    if ext not in _EXTENSOES_IMAGEM:
        return jsonify({'erro': 'Tipo de arquivo não permitido'}), 400

    # Determina nome da pasta: login do usuário ou fallback "geral"
    pasta_usuario = 'geral'
    if usuario_id:
        u = banco.buscar_usuario_por_id(int(usuario_id))
        if u:
            login_raw = u.get('usuario') or u.get('nome') or str(usuario_id)
            pasta_usuario = _RE_LOGIN_SEGURO.sub('_', login_raw).lower()

    nome_arquivo = f'{uuid.uuid4().hex}.{ext}'
    pasta = os.path.join(current_app.root_path, 'static', 'assinaturas', pasta_usuario)
    os.makedirs(pasta, exist_ok=True)
    arquivo.save(os.path.join(pasta, nome_arquivo))
    return jsonify({'url': f'/static/assinaturas/{pasta_usuario}/{nome_arquivo}'})
