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
from utils import checar_login, usuario_logado, checar_admin, checar_tela

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
    return render_template('aba_credenciais.html', credenciais=creds, aba_ativa='credenciais')


@credenciais_bp.route('/api/credenciais', methods=['GET'])
def api_listar():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify(banco.listar_credenciais())


@credenciais_bp.route('/api/credenciais/empresas')
def api_empresas():
    if not usuario_logado():
        return jsonify([]), 401
    q = (request.args.get('q') or '').strip()
    if len(q) < 3:
        return jsonify([])
    return jsonify(banco.buscar_empresas_sistema(q))


@credenciais_bp.route('/api/credenciais', methods=['POST'])
def api_adicionar():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json(silent=True) or {}
    d['criado_por'] = session.get('nome', '')
    if not d.get('nome') or not d.get('data_validade'):
        return jsonify({'erro': 'Nome e data de validade são obrigatórios.'}), 400
    cid = banco.adicionar_credencial(d)
    _log('INSERIU', f'Adicionou credencial #{cid} — {d.get("nome")} ({d.get("cnpj")})')
    return jsonify({'sucesso': True, 'id': cid})


@credenciais_bp.route('/api/credenciais/<int:cid>', methods=['PUT'])
def api_atualizar(cid):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
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
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    novo = banco.toggle_silenciar_credencial(cid)
    _log('SILENCIOU' if novo else 'REATIVOU',
         f'{"Silenciou" if novo else "Reativou"} avisos da credencial #{cid}')
    return jsonify({'sucesso': True, 'silenciado': novo})
