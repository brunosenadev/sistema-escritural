"""
routes/credenciais.py — Controle de validade de credenciais de API.

Avisos pré-vencimento : 30, 15, 7, 3 dias antes
Avisos pós-vencimento : 3d, 7d, 15d, 1m, 3m, 6m, 1a em atraso
"""

import threading
import time
from datetime import date, datetime

from flask import Blueprint, render_template, request, jsonify, session
import banco
from utils import checar_login, usuario_logado, checar_admin, checar_tela, tem_acesso_tela

credenciais_bp = Blueprint('credenciais', __name__)

# (tipo_aviso, dias_relativos)  — negativo = em atraso
_THRESHOLDS = [
    ('pre_30d',  30),
    ('pre_15d',  15),
    ('pre_7d',    7),
    ('pre_3d',    3),
    ('atr_0d',    0),   # dia do vencimento
    ('atr_3d',   -3),
    ('atr_7d',   -7),
    ('atr_15d', -15),
    ('atr_1m',  -30),
    ('atr_3m',  -90),
    ('atr_6m', -180),
    ('atr_1a', -365),
]

_LABELS = {
    'pre_30d': 'vence em 30 dias',
    'pre_15d': 'vence em 15 dias',
    'pre_7d':  'vence em 7 dias',
    'pre_3d':  'vence em 3 dias',
    'atr_0d':  'venceu hoje',
    'atr_3d':  '3 dias em atraso',
    'atr_7d':  '7 dias em atraso',
    'atr_15d': '15 dias em atraso',
    'atr_1m':  '1 mês em atraso',
    'atr_3m':  '3 meses em atraso',
    'atr_6m':  '6 meses em atraso',
    'atr_1a':  '1 ano em atraso',
}


def _parse_validade(data_str):
    """Converte YYYY-MM-DD para date. Retorna None se inválido."""
    try:
        return date.fromisoformat(data_str)
    except Exception:
        return None


def _checar_e_notificar():
    """Verifica todas as credenciais e dispara notificações se necessário."""
    try:
        credenciais = banco.listar_credenciais()
        hoje = date.today()
        destinatarios = banco.listar_usuarios_com_flag('recebe_aviso_credenciais')
        if not destinatarios:
            return
        for cred in credenciais:
            if cred.get('silenciado'):
                continue
            val = _parse_validade(cred.get('data_validade', ''))
            if not val:
                continue
            dias_restantes = (val - hoje).days  # positivo = falta X dias; negativo = X dias atraso
            for tipo_aviso, limiar in _THRESHOLDS:
                if limiar >= 0:
                    deve_avisar = (0 <= dias_restantes <= limiar)
                else:
                    deve_avisar = (dias_restantes <= limiar)
                if deve_avisar:
                    novo = banco.registrar_aviso_credencial(cred['id'], tipo_aviso)
                    if novo:
                        label = _LABELS.get(tipo_aviso, tipo_aviso)
                        titulo = f'Credencial {label} — {cred["nome"]}'
                        msg = (
                            f'CNPJ {cred["cnpj"]} | Banco {cred["banco"]} | '
                            f'Conta {cred["conta"]} | Tipo: {cred["tipo"]}'
                        )
                        for u in destinatarios:
                            banco.criar_notificacao(u['id'], titulo, msg,
                                                    'aviso' if dias_restantes >= 0 else 'erro')
    except Exception:
        pass


def _loop_checker():
    # Primeira checagem 1 minuto após o boot; depois a cada hora
    time.sleep(60)
    while True:
        _checar_e_notificar()
        time.sleep(3600)


def iniciar_checker():
    t = threading.Thread(target=_loop_checker, daemon=True, name='credenciais-checker')
    t.start()


# ── Rotas ─────────────────────────────────────────────────

def _log(acao, descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Credenciais', acao=acao, descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


@credenciais_bp.route('/credenciais')
def pagina_credenciais():
    bloqueio = checar_tela('credenciais')
    if bloqueio:
        return bloqueio
    creds = banco.listar_credenciais()
    hoje = date.today()
    for c in creds:
        val = _parse_validade(c.get('data_validade', ''))
        if val:
            c['dias'] = (val - hoje).days
            c['data_br'] = val.strftime('%d/%m/%Y')
        else:
            c['dias'] = None
            c['data_br'] = c.get('data_validade', '')
        # Máscara CNPJ
        raw = (c.get('cnpj') or '').replace('.','').replace('/','').replace('-','')
        if len(raw) == 14:
            c['cnpj_fmt'] = f'{raw[:2]}.{raw[2:5]}.{raw[5:8]}/{raw[8:12]}-{raw[12:]}'
        else:
            c['cnpj_fmt'] = c.get('cnpj') or ''
    return render_template('aba_credenciais.html', credenciais=creds, aba_ativa='credenciais')


@credenciais_bp.route('/api/credenciais', methods=['GET'])
def api_listar():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify(banco.listar_credenciais())


@credenciais_bp.route('/api/credenciais/simular', methods=['POST'])
def api_simular():
    if session.get('nivel_acesso') not in ('master', 'admin'):
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json(silent=True) or {}
    cid = d.get('id_credencial')
    tipo_aviso = d.get('tipo_aviso')
    if not cid or not tipo_aviso:
        return jsonify({'erro': 'Parâmetros inválidos'}), 400
    cred = banco.buscar_credencial(cid)
    if not cred:
        return jsonify({'erro': 'Credencial não encontrada'}), 404
    label = _LABELS.get(tipo_aviso, tipo_aviso)
    titulo = f'[SIMULAÇÃO] Credencial {label} — {cred["nome"]}'
    msg = (
        f'CNPJ {cred["cnpj"] or "—"} | Banco {cred["banco"] or "—"} | '
        f'Conta {cred["conta"] or "—"} | Tipo: {cred["tipo"] or "—"}'
    )
    uid = session.get('id_usuario')
    tipo_notif = 'erro' if tipo_aviso.startswith('atr_') else 'aviso'
    banco.criar_notificacao(uid, titulo, msg, tipo_notif)
    _log('SIMULOU', f'Simulou aviso "{tipo_aviso}" para credencial #{cid} — {cred["nome"]}')
    return jsonify({'sucesso': True})


@credenciais_bp.route('/api/credenciais/empresas')
def api_empresas():
    if not usuario_logado():
        return jsonify([]), 401
    q = (request.args.get('q') or '').strip()
    if len(q) < 3:
        return jsonify([])
    return jsonify(banco.buscar_empresas_sistema(q))


def _checar_acesso_cred():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not tem_acesso_tela('credenciais'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return None


@credenciais_bp.route('/api/credenciais', methods=['POST'])
def api_adicionar():
    err = _checar_acesso_cred()
    if err: return err
    d = request.get_json(silent=True) or {}
    d['criado_por'] = session.get('nome', '')
    if not d.get('nome') or not d.get('data_validade'):
        return jsonify({'erro': 'Nome e data de validade são obrigatórios.'}), 400
    cid = banco.adicionar_credencial(d)
    _log('INSERIU', f'Adicionou credencial #{cid} — {d.get("nome")} ({d.get("cnpj")})')
    return jsonify({'sucesso': True, 'id': cid})


@credenciais_bp.route('/api/credenciais/<int:cid>', methods=['PUT'])
def api_atualizar(cid):
    err = _checar_acesso_cred()
    if err: return err
    d = request.get_json(silent=True) or {}
    if not d.get('nome') or not d.get('data_validade'):
        return jsonify({'erro': 'Nome e data de validade são obrigatórios.'}), 400
    banco.atualizar_credencial(cid, d)
    _log('EDITOU', f'Editou credencial #{cid} — {d.get("nome")}')
    return jsonify({'sucesso': True})


@credenciais_bp.route('/api/credenciais/<int:cid>', methods=['DELETE'])
def api_deletar(cid):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    c = banco.buscar_credencial(cid)
    banco.deletar_credencial(cid)
    _log('DELETOU', f'Removeu credencial #{cid} — {c.get("nome","?") if c else "?"}')
    return jsonify({'sucesso': True})


@credenciais_bp.route('/api/credenciais/<int:cid>/silenciar', methods=['POST'])
def api_silenciar(cid):
    err = _checar_acesso_cred()
    if err: return err
    novo = banco.toggle_silenciar_credencial(cid)
    _log('SILENCIOU' if novo else 'REATIVOU',
         f'{"Silenciou" if novo else "Reativou"} avisos da credencial #{cid}')
    return jsonify({'sucesso': True, 'silenciado': novo})


# ── Descriptografia de credenciais ────────────────────────────────────────────

def _pode_descriptografar():
    if not usuario_logado():
        return False
    u = banco.buscar_usuario_por_id(session.get('id_usuario'))
    if not u:
        return False
    return bool(u.get('pode_descriptografar')) or session.get('nivel_acesso') == 'master'


@credenciais_bp.route('/descriptografar')
def pagina_descriptografar():
    bloqueio = checar_tela('descriptografar')
    if bloqueio:
        return bloqueio
    banco.limpar_solicitacoes_expiradas()
    pode_aprovar  = _pode_descriptografar()
    pendentes     = banco.listar_solicitacoes_descriptografia('pendente') if pode_aprovar else []
    minha_sol     = banco.buscar_ultima_solicitacao_usuario(session.get('id_usuario'))
    return render_template(
        'aba_descriptografar.html',
        aba_ativa='descriptografar',
        pode_aprovar=pode_aprovar,
        pendentes=pendentes,
        minha_sol=minha_sol,
    )


@credenciais_bp.route('/api/descriptografar/solicitar', methods=['POST'])
def api_solicitar_decrypt():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    d = request.get_json(silent=True) or {}
    client_id_enc     = (d.get('client_id_enc') or '').strip()
    client_secret_enc = (d.get('client_secret_enc') or '').strip()
    if not client_id_enc or not client_secret_enc:
        return jsonify({'erro': 'Preencha os dois campos.'}), 400
    uid  = session.get('id_usuario')
    nome = session.get('nome') or session.get('usuario', '')
    id_sol = banco.criar_solicitacao_descriptografia(uid, nome, client_id_enc, client_secret_enc)
    # Notifica quem pode aprovar
    aprovadores = banco.listar_usuarios_com_flag('pode_descriptografar')
    for ap in aprovadores:
        banco.criar_notificacao(
            ap['id'],
            f'Solicitação de descriptografia — {nome}',
            f'Usuário {nome} solicitou descriptografia de credenciais. Acesse a tela para aprovar ou negar.',
            'aviso',
        )
    _log('SOLICITOU', f'Solicitou descriptografia #{id_sol}')
    return jsonify({'sucesso': True, 'id': id_sol})


@credenciais_bp.route('/api/descriptografar/status')
def api_status_decrypt():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    banco.limpar_solicitacoes_expiradas()
    sol = banco.buscar_ultima_solicitacao_usuario(session.get('id_usuario'))
    if not sol:
        return jsonify({'status': None})
    resp = {
        'id':     sol['id'],
        'status': sol['status'],
        'expira_em': sol.get('expira_em'),
    }
    if sol['status'] == 'aprovado':
        resp['client_id_dec']     = sol.get('client_id_dec', '')
        resp['client_secret_dec'] = sol.get('client_secret_dec', '')
        resp['aprovado_por']      = sol.get('aprovado_por', '')
    return jsonify(resp)


@credenciais_bp.route('/api/descriptografar/solicitacoes')
def api_listar_solicitacoes():
    if not _pode_descriptografar():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.limpar_solicitacoes_expiradas()
    pendentes = banco.listar_solicitacoes_descriptografia('pendente')
    return jsonify(pendentes)


@credenciais_bp.route('/api/descriptografar/<int:id_sol>/aprovar', methods=['POST'])
def api_aprovar_decrypt(id_sol):
    if not _pode_descriptografar():
        return jsonify({'erro': 'Sem permissão'}), 403
    nome = session.get('nome') or session.get('usuario', '')
    resultado = banco.aprovar_solicitacao_descriptografia(id_sol, nome)
    if not resultado:
        return jsonify({'erro': 'Solicitação não encontrada ou já respondida.'}), 404
    banco.criar_notificacao(
        resultado['solicitante_id'],
        'Descriptografia aprovada',
        f'{nome} aprovou sua solicitação. Acesse a tela para ver as credenciais (válido por 3 min).',
        tipo='sucesso',
        link='/descriptografar',
    )
    _log('APROVOU', f'Aprovou solicitação de descriptografia #{id_sol}')
    return jsonify({'sucesso': True})


@credenciais_bp.route('/api/descriptografar/<int:id_sol>/negar', methods=['POST'])
def api_negar_decrypt(id_sol):
    if not _pode_descriptografar():
        return jsonify({'erro': 'Sem permissão'}), 403
    nome = session.get('nome') or session.get('usuario', '')
    resultado = banco.negar_solicitacao_descriptografia(id_sol, nome)
    if resultado:
        banco.criar_notificacao(
            resultado['solicitante_id'],
            'Descriptografia negada',
            f'{nome} negou sua solicitação de descriptografia.',
            tipo='erro',
            link='/descriptografar',
        )
    _log('NEGOU', f'Negou solicitação de descriptografia #{id_sol}')
    return jsonify({'sucesso': True})
