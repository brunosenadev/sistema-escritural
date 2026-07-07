from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import banco
from utils import usuario_logado, checar_tela

logs_bp = Blueprint('logs', __name__)

_TELAS = [
    'Login', 'Escritural', 'Pendentes', 'Hom. Cobrança', 'Hom. Pagamentos',
    'Hom. Extrato Cartão', 'Hom. Extrato Bancário', 'Cancelados', 'Ajuda',
    'Melhorias', 'Configurações', 'Acesso', 'Notificações', 'Credenciais',
]
_ACOES = [
    'LOGIN', 'LOGIN_FALHA', 'LOGOUT', 'INSERIU', 'EDITOU', 'DELETOU',
    'STATUS', 'MOVEU', 'ASSUMIU', 'EMAIL', 'IMPORTOU', 'SENHA', 'ACESSO',
    'ENVIOU', 'SILENCIOU', 'REATIVOU', 'SIMULOU',
]


def _tem_acesso():
    if not usuario_logado():
        return False
    nivel = session.get('nivel_acesso', '')
    if nivel in ('admin', 'master'):
        return True
    telas = session.get('telas') or []
    return 'logs' in telas


@logs_bp.route('/logs')
def aba_logs():
    if not _tem_acesso():
        return redirect(url_for('auth.pagina_login'))
    usuarios = [u['nome'] for u in banco.listar_usuarios()]
    return render_template('aba_logs.html',
                           telas=_TELAS, acoes=_ACOES, usuarios=usuarios)


@logs_bp.route('/api/logs')
def api_logs():
    if not _tem_acesso():
        return jsonify({'erro': 'Sem permissão'}), 403

    pagina     = max(1, int(request.args.get('pagina', 1)))
    por_pagina = min(int(request.args.get('por_pagina', 100)), 500)

    registros, total = banco.listar_logs(
        busca    = request.args.get('busca')    or None,
        usuario  = request.args.get('usuario')  or None,
        tela     = request.args.get('tela')     or None,
        acao     = request.args.get('acao')     or None,
        data_ini = request.args.get('data_ini') or None,
        data_fim = request.args.get('data_fim') or None,
        pagina   = pagina,
        por_pagina = por_pagina,
    )
    return jsonify({'registros': registros, 'total': total,
                    'pagina': pagina, 'por_pagina': por_pagina})
