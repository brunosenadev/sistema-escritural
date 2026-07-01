import os
import threading
import requests
from flask import Blueprint, request, jsonify, session
from utils import checar_tela

discord_bp = Blueprint('discord', __name__)

_token_override = None
_canal_override = None


def _token():
    return _token_override or os.environ.get('DISCORD_BOT_TOKEN', '')


def _canal():
    return _canal_override or os.environ.get('DISCORD_CANAL_ID', '')


def _enviar_bg(token, canal_id, mensagem):
    try:
        requests.post(
            f'https://discord.com/api/v10/channels/{canal_id}/messages',
            headers={'Authorization': f'Bot {token}'},
            json={'content': mensagem},
            timeout=5,
        )
    except Exception:
        pass 


def notificar_nova_homologacao(cliente):
    token = _token()
    canal_id = _canal()
    if not token or not canal_id:
        return
    mensagem = f'📋 Uma nova homologação foi cadastrada do cliente **{cliente}**.'
    threading.Thread(target=_enviar_bg, args=(token, canal_id, mensagem), daemon=True).start()


def notificar_discord(mensagem):
    token = _token()
    canal_id = _canal()
    if not token or not canal_id:
        return
    threading.Thread(target=_enviar_bg, args=(token, canal_id, mensagem), daemon=True).start()

@discord_bp.route('/discord/config', methods=['GET'])
def discord_config_get():
    if checar_tela('config'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify({
        'token_configurado': bool(_token()),
        'canal_configurado': bool(_canal()),
        'canal_id': _canal(),
    })

@discord_bp.route('/discord/config', methods=['POST'])
def discord_config_set():
    global _token_override, _canal_override
    if checar_tela('config'):
        return jsonify({'erro': 'Sem permissão'}), 403
    dados = request.get_json(silent=True) or {}
    novo_token = (dados.get('token') or '').strip()
    novo_canal = (dados.get('canal_id') or '').strip()
    if novo_token:
        _token_override = novo_token
    if novo_canal:
        _canal_override = novo_canal
    return jsonify({'sucesso': True})

@discord_bp.route('/discord/testar', methods=['POST'])
def discord_testar():
    if checar_tela('config'):
        return jsonify({'erro': 'Sem permissão'}), 403
    token = _token()
    canal_id = _canal()
    if not token or not canal_id:
        return jsonify({'erro': 'Token ou canal não configurados.'}), 400
    try:
        resp = requests.post(
            f'https://discord.com/api/v10/channels/{canal_id}/messages',
            headers={'Authorization': f'Bot {token}'},
            json={'content': '✅ Teste de notificação do Sisplan — conexão OK!'},
            timeout=5,
        )
        if resp.status_code in (200, 201):
            return jsonify({'sucesso': True})
        return jsonify({'erro': f'Discord retornou {resp.status_code}: {resp.text}'}), 502
    except Exception as e:
        return jsonify({'erro': f'Erro de conexão: {e}'}), 502
