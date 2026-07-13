import os
import uuid
import datetime
import jwt as pyjwt
from flask import request, g, session, redirect, url_for

SECRET      = os.environ.get('SECRET_KEY', 'sisplan-escritural-chave-secreta-2026')
ACCESS_TTL  = 60   # minutos
REFRESH_TTL = 30   # dias

def _encode(payload: dict) -> str:
    return pyjwt.encode(payload, SECRET, algorithm='HS256')


def _decode(token: str) -> dict | None:
    try:
        return pyjwt.decode(token, SECRET, algorithms=['HS256'])
    except pyjwt.PyJWTError:
        return None

def criar_tokens(usuario_row: dict, jti: str | None = None) -> tuple[str, str, str]:
    if jti is None:
        jti = str(uuid.uuid4())
    agora = datetime.datetime.utcnow()
    access = _encode({
        'sub':   str(usuario_row['id']),
        'usr':   usuario_row['usuario'],
        'nome':  usuario_row['nome'],
        'niv':   usuario_row['nivel'],
        'tec':   usuario_row.get('tecnico_vinculado') or '',
        'setor': usuario_row.get('setor') or '',
        'tema':  usuario_row.get('tema') or 'light',
        'cor':   usuario_row.get('cor') or '',
        'mp':    int(usuario_row.get('mudar_senha') or 0),
        'jti':   jti,
        'type':  'access',
        'exp':   agora + datetime.timedelta(minutes=ACCESS_TTL),
    })
    refresh = _encode({
        'sub':  str(usuario_row['id']),
        'jti':  jti,
        'type': 'refresh',
        'exp':  agora + datetime.timedelta(days=REFRESH_TTL),
    })
    return access, refresh, jti


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
    session['cor']               = payload.get('cor', '')
    session['mudar_senha']       = int(payload.get('mp', 0))


def pode_editar() -> bool:
    return session.get('nivel_acesso') in ('admin', 'master') or bool(session.get('tecnico_vinculado'))

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
    if session.get('nivel_acesso') not in ('admin', 'master'):
        return redirect(url_for('auth.inicio'))
    return None

def tem_acesso_tela(tela: str) -> bool:
    if session.get('nivel_acesso') == 'master':
        return True
    return tela in (session.get('telas') or [])

def checar_tela(tela: str):
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio
    if not tem_acesso_tela(tela):
        return redirect(url_for('auth.inicio'))
    return None

def checar_master():
    bloqueio = checar_login()
    if bloqueio:
        return bloqueio
    if session.get('nivel_acesso') != 'master':
        return redirect(url_for('auth.inicio'))
    return None
