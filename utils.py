from flask import session, redirect, url_for


def usuario_logado():
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
