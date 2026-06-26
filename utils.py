import os
import datetime
import jwt as pyjwt
from flask import request, g, session, redirect, url_for

SECRET      = os.environ.get('SECRET_KEY', 'sisplan-escritural-chave-secreta-2026')
ACCESS_TTL  = 15   # minutos
REFRESH_TTL = 7    # dias


# ── JWT helpers ───────────────────────────────────────────

def _encode(payload: dict) -> str:
    return pyjwt.encode(payload, SECRET, algorithm='HS256')


def _decode(token: str) -> dict | None:
    try:
        return pyjwt.decode(token, SECRET, algorithms=['HS256'])
    except pyjwt.PyJWTError:
        return None


def criar_tokens(usuario_row: dict) -> tuple[str, str]:
    """Gera (access_token, refresh_token) para o usuário."""
    agora = datetime.datetime.utcnow()
    access = _encode({
        'sub':   usuario_row['id'],
        'usr':   usuario_row['usuario'],
        'nome':  usuario_row['nome'],
        'niv':   usuario_row['nivel'],
        'tec':   usuario_row.get('tecnico_vinculado') or '',
        'setor': usuario_row.get('setor') or '',
        'tema':  usuario_row.get('tema') or 'light',
        'mp':    int(usuario_row.get('mudar_senha') or 0),
        'type':  'access',
        'exp':   agora + datetime.timedelta(minutes=ACCESS_TTL),
    })
    refresh = _encode({
        'sub':  usuario_row['id'],
        'type': 'refresh',
        'exp':  agora + datetime.timedelta(days=REFRESH_TTL),
    })
    return access, refresh


def _payload_access() -> dict | None:
    token = request.cookies.get('access_token')
    if not token:
        return None
    data = _decode(token)
    return data if (data and data.get('type') == 'access') else None


def _payload_refresh() -> dict | None:
    token = request.cookies.get('refresh_token')
    if not token:
        return None
    data = _decode(token)
    return data if (data and data.get('type') == 'refresh') else None


def _preencher_sessao(payload: dict):
    session['usuario']           = payload['usr']
    session['nome']              = payload['nome']
    session['nivel_acesso']      = payload['niv']
    session['tecnico_vinculado'] = payload.get('tec', '')
    session['setor']             = payload.get('setor', '')
    session['id_usuario']        = payload['sub']
    session['tema']              = payload.get('tema', 'light')


def pode_editar() -> bool:
    """True se o usuário pode fazer alterações (admin ou tem técnico vinculado)."""
    return session.get('nivel_acesso') == 'admin' or bool(session.get('tecnico_vinculado'))


# ── Guards usados nas rotas ───────────────────────────────

def usuario_logado() -> bool:
    return 'usuario' in session


def checar_login():
    if not usuario_logado():
        return redirect(url_for('auth.pagina_login'))
    return None


def checar_admin():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio
    if session.get('nivel_acesso') != 'admin':
        return redirect(url_for('auth.inicio'))
    return None
