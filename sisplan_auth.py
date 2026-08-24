"""
sisplan_auth.py — Login com usuário Sisplan, batendo na API central da
Sisplan Sistemas (mesma usada pelo LoginEdicaoRelatorio.pas do ERP).

Fluxo (replica o Delphi):
1. GET /ping — confere se a API está no ar.
2. GET /Login?USUARIO=...&SENHA=... — senha vai cifrada (mesma cifra
   XOR/LCG de banco.criptografar_valor) + base64.
3. Resposta 'FALSE' = credenciais inválidas. Qualquer outra coisa é um
   JSON com accessToken/refreshToken/expiresIn/usuario.

Credenciais da aplicação (Basic Auth fixo, não é do usuário) vêm de
variável de ambiente — nunca hardcoded aqui.
"""

import base64
import os

import requests
import banco

URL_API = os.environ.get('SISPLAN_API_URL', 'https://api.sisplansistemas.com.br')
_API_USER  = os.environ.get('SISPLAN_API_USER', 'SISPLAN')
_API_SENHA = os.environ.get('SISPLAN_API_SENHA', 'REwrCPMWrBSWa2qkX')
_TIMEOUT = 4


def _configurado() -> bool:
    return bool(_API_USER and _API_SENHA)


def validar_login_sisplan(usuario: str, senha: str) -> dict | None:
    """Tenta autenticar contra a API central do Sisplan.

    Retorna o dict de resposta (accessToken etc.) em caso de sucesso,
    ou None se as credenciais forem inválidas, a API estiver fora do
    ar, ou a integração não estiver configurada (sem gerar erro pro
    fluxo de login local, que continua funcionando normalmente)."""
    if not _configurado() or not usuario or not senha:
        return None

    usuario = usuario.strip().upper()  # a API do Sisplan espera o usuário em maiúsculo

    try:
        ping = requests.get(
            f'{URL_API}/ping',
            auth=(_API_USER, _API_SENHA),
            timeout=_TIMEOUT,
        )
        if ping.status_code != 200 or ping.json().get('Result') != 'OK':
            return None

        senha_cifrada = base64.b64encode(banco.criptografar_valor(senha).encode('utf-8')).decode('ascii')
        resp = requests.get(
            f'{URL_API}/Login',
            auth=(_API_USER, _API_SENHA),
            params={'USUARIO': usuario, 'SENHA': senha_cifrada},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200 or resp.text.strip() == 'FALSE':
            return None

        return resp.json()
    except (requests.RequestException, ValueError):
        return None
