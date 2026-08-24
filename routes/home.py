from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, make_response
import banco
from utils import usuario_logado, tem_acesso_tela, criar_tokens, _payload_access

home_bp = Blueprint('home', __name__)

_HOMOLOGADOS = [
    ('homologados_cobranca',     'homologados_cobranca',     'Cobrança'),
    ('homologados_pagamentos',   'homologados_pagamentos',   'Pagamentos'),
    ('homologados_extrato',      'homologados_extrato',      'Extrato Cartão'),
    ('homologados_ext_bancario', 'homologados_ext_bancario', 'Extrato Bancário'),
]

_TELAS_INICIAL = [
    ('home',                      'Home'),
    ('pendente',                  'Pendente'),
    ('homologados_cobranca',      'Homologados Cobrança'),
    ('homologados_pagamentos',    'Homologados Pagamentos'),
    ('homologados_extrato',       'Homologados Extrato Cartão'),
    ('homologados_ext_bancario',  'Homologados Extrato Bancário'),
    ('cancelados',                'Cancelados'),
    ('melhorias',                 'Melhorias'),
    ('hub',                       'Hub Bancário'),
]


@home_bp.route('/home')
def pagina_home():
    if not usuario_logado():
        return redirect(url_for('auth.pagina_login'))

    dados = {}

    if tem_acesso_tela('pendente'):
        dados['total_pendentes'] = banco.contar_pendentes()
        atrasadas = [p for p in banco.calcular_sla_pendentes() if p['sla_faixa'] in ('vencido', 'atrasado', 'critico')]
        dados['mais_atrasadas'] = atrasadas[:8]

    tipos_visiveis = [(tela, tabela, nome) for tela, tabela, nome in _HOMOLOGADOS if tem_acesso_tela(tela)]
    if tipos_visiveis:
        contagens = [(nome, banco.contar_registros_homologado(tabela)) for _, tabela, nome in tipos_visiveis]
        maior_tipo = max((qtd for _, qtd in contagens), default=1) or 1
        dados['homologados_por_tipo'] = [
            {'nome': nome, 'qtd': qtd, 'pct': round(qtd / maior_tipo * 100, 1)}
            for nome, qtd in contagens
        ]
        dados['total_homologadas'] = sum(qtd for _, qtd in contagens)
        ranking = banco.ranking_tecnicos_homologados([tabela for _, tabela, _ in tipos_visiveis])
        maior_ranking = max(ranking.values()) if ranking else 1
        cores_tecnicos = banco.cores_por_tecnico()
        dados['ranking_tecnicos'] = [
            {'tecnico': tec, 'qtd': qtd, 'pct': round(qtd / maior_ranking * 100, 1),
             'cor': cores_tecnicos.get(tec) or '#94a3b8'}
            for tec, qtd in ranking.items()
        ]

    if tem_acesso_tela('cancelados'):
        dados['total_cancelados'] = banco.contar_cancelados()

    tela_inicial_atual = session.get('tela_inicial') or 'home'
    opcoes_tela_inicial = [(chave, nome) for chave, nome in _TELAS_INICIAL if chave == 'home' or tem_acesso_tela(chave)]

    return render_template(
        'aba_home.html',
        dados=dados,
        tem_algum_card=bool(dados),
        tela_inicial_atual=tela_inicial_atual,
        opcoes_tela_inicial=opcoes_tela_inicial,
    )


@home_bp.route('/api/minha-tela-inicial', methods=['PUT'])
def api_minha_tela_inicial():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    tela = (request.get_json() or {}).get('tela', 'home')
    chaves_validas = {chave for chave, _ in _TELAS_INICIAL}
    if tela not in chaves_validas:
        return jsonify({'erro': 'Tela inválida'}), 400
    if tela != 'home' and not tem_acesso_tela(tela):
        return jsonify({'erro': 'Sem acesso a essa tela'}), 403

    id_usuario = session.get('id_usuario')
    banco.atualizar_tela_inicial(id_usuario, tela)
    session['tela_inicial'] = tela

    u = banco.buscar_usuario_por_id(id_usuario)
    jti_atual = (_payload_access() or {}).get('jti')
    access, *_ = criar_tokens(u, jti=jti_atual)
    resp = make_response(jsonify({'sucesso': True}))
    resp.set_cookie('access_token', access, max_age=60*60, httponly=True, samesite='Lax', path='/')
    return resp
