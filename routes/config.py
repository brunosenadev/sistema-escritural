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
        sla_config=banco.listar_sla_config(),
        nomes_servicos=banco.listar_servicos(),
        tecnico_padrao=banco.get_config('tecnico_padrao'),
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
        resp.set_cookie('access_token', access, max_age=60*60, httponly=True, samesite='Lax', path='/')
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


# ── API Config Geral ─────────────────────────────────────

@config_bp.route('/api/config-geral', methods=['GET'])
def api_get_config_geral():
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    chave = request.args.get('chave', '')
    if not chave:
        return jsonify({'erro': 'Chave obrigatória'}), 400
    return jsonify({'valor': banco.get_config(chave)})


@config_bp.route('/api/config-geral', methods=['POST'])
def api_set_config_geral():
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    chave = (d.get('chave') or '').strip()
    valor = str(d.get('valor', ''))
    if not chave:
        return jsonify({'erro': 'Chave obrigatória'}), 400
    banco.set_config(chave, valor)
    _log('Configurações', 'EDITOU', f'Config geral: {chave}={valor}')
    return jsonify({'sucesso': True})


# ── API SLA Config ────────────────────────────────────────

@config_bp.route('/api/sla-config', methods=['GET'])
def api_listar_sla_config():
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.listar_sla_config())


@config_bp.route('/api/sla-config', methods=['POST'])
def api_salvar_sla_servico():
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    servico = (d.get('servico') or '').strip()
    if not servico:
        return jsonify({'erro': 'Serviço obrigatório'}), 400
    try:
        banco.salvar_sla_servico(
            servico,
            int(d.get('dias_atencao', 15)),
            int(d.get('dias_atrasado', 25)),
            int(d.get('dias_critico', 40)),
        )
    except (ValueError, TypeError):
        return jsonify({'erro': 'Dias inválidos'}), 400
    _log('Configurações', 'EDITOU', f'SLA config salvo: {servico}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/sla-config/<int:id_sla>', methods=['DELETE'])
def api_remover_sla_servico(id_sla):
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_sla_servico(id_sla)
    _log('Configurações', 'DELETOU', f'SLA config removido: #{id_sla}')
    return jsonify({'sucesso': True})


# ── API SLA Avisos ────────────────────────────────────────

@config_bp.route('/api/sla-avisos', methods=['GET'])
def api_listar_sla_avisos():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    apenas_ativos = request.args.get('ativos') == '1'
    return jsonify(banco.listar_sla_avisos(apenas_ativos=apenas_ativos))


@config_bp.route('/api/sla-avisos', methods=['POST'])
def api_adicionar_sla_aviso():
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    texto = (d.get('texto') or '').strip()
    if not texto:
        return jsonify({'erro': 'Texto obrigatório'}), 400
    banco.adicionar_sla_aviso(
        texto, d.get('tipo', 'info'), d.get('expira_em', ''),
        session.get('nome', '')
    )
    _log('Configurações', 'INSERIU', f'Aviso SLA criado: {texto[:60]}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/sla-avisos/<int:id_aviso>', methods=['DELETE'])
def api_remover_sla_aviso(id_aviso):
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_sla_aviso(id_aviso)
    _log('Configurações', 'DELETOU', f'Aviso SLA removido: #{id_aviso}')
    return jsonify({'sucesso': True})


@config_bp.route('/api/sla-notif-pref', methods=['GET'])
def api_get_notif_pref():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    uid = session.get('id_usuario')
    return jsonify(banco.listar_notif_pref_usuario(uid))


@config_bp.route('/api/sla-notif-pref', methods=['POST'])
def api_salvar_notif_pref():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    dados = request.get_json() or {}
    uid = session.get('id_usuario')
    for faixa in ('critico', 'atrasado', 'atencao'):
        if faixa in dados:
            pref = dados[faixa]
            banco.salvar_notif_pref(uid, faixa, pref.get('ativo', 0), max(1, int(pref.get('freq_dias', 1))))
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
