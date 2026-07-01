"""
routes/email_escritural.py — Envio e recebimento de e-mails por solicitação escritural.

Cada usuário configura suas próprias credenciais SMTP/IMAP (as mesmas do Thunderbird).
Um thread daemon faz polling IMAP a cada 3 minutos procurando respostas às threads abertas.
"""

import imaplib
import smtplib
import ssl
import re
import threading
import time
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.utils import parseaddr, formataddr, make_msgid
from datetime import datetime

from flask import Blueprint, request, jsonify, session
import banco
from utils import checar_tela

email_escritural_bp = Blueprint('email_escritural', __name__)

_PREFIXO_ASSUNTO = '[SISPLAN-{id}]'
_RE_ID_NO_ASSUNTO = re.compile(r'\[SISPLAN-(\d+)\]', re.IGNORECASE)
_POLLING_INTERVALO = 180  # segundos


# ── Helpers ───────────────────────────────────────────────

def _decodificar_header(valor):
    if not valor:
        return ''
    partes = decode_header(valor)
    resultado = []
    for parte, enc in partes:
        if isinstance(parte, bytes):
            resultado.append(parte.decode(enc or 'utf-8', errors='replace'))
        else:
            resultado.append(parte)
    return ''.join(resultado)


def _extrair_texto(msg_email):
    """Extrai o corpo em texto puro de uma mensagem email.Message."""
    corpo = ''
    if msg_email.is_multipart():
        for part in msg_email.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in cd:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                corpo = payload.decode(charset, errors='replace')
                break
    else:
        payload = msg_email.get_payload(decode=True)
        charset = msg_email.get_content_charset() or 'utf-8'
        if payload:
            corpo = payload.decode(charset, errors='replace')
    return corpo.strip()


def _conectar_smtp(cfg):
    porta = int(cfg.get('smtp_port', 587))
    host = cfg['smtp_host']
    if cfg.get('smtp_ssl'):
        ctx = ssl.create_default_context()
        srv = smtplib.SMTP_SSL(host, porta, context=ctx, timeout=10)
    else:
        srv = smtplib.SMTP(host, porta, timeout=10)
        srv.ehlo()
        srv.starttls()
        srv.ehlo()
    srv.login(cfg['email'], cfg['senha'])
    return srv


def _conectar_imap(cfg):
    porta = int(cfg.get('imap_port', 993))
    host = cfg['imap_host']
    if cfg.get('imap_ssl', True):
        ctx = ssl.create_default_context()
        M = imaplib.IMAP4_SSL(host, porta, ssl_context=ctx)
    else:
        M = imaplib.IMAP4(host, porta)
    M.login(cfg['email'], cfg['senha'])
    return M


# ── Envio via SMTP ────────────────────────────────────────

def enviar_email_smtp(cfg, destinatario, assunto, corpo_texto, in_reply_to=None, references=None):
    """
    Envia um e-mail usando as credenciais do cfg.
    Retorna o Message-ID gerado.
    """
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((cfg.get('nome_exibicao', ''), cfg['email']))
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg_id = make_msgid(domain=cfg['email'].split('@')[-1])
    msg['Message-ID'] = msg_id
    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to
        msg['References'] = (references or in_reply_to)
    msg.attach(MIMEText(corpo_texto, 'plain', 'utf-8'))

    srv = _conectar_smtp(cfg)
    srv.sendmail(cfg['email'], [destinatario], msg.as_string())
    srv.quit()
    return msg_id


# ── IMAP polling ──────────────────────────────────────────

def _processar_mensagem_imap(cfg, uid, msg_bytes):
    msg = email_lib.message_from_bytes(msg_bytes)
    message_id = (msg.get('Message-ID') or '').strip()

    if banco.message_id_existe(message_id):
        return

    assunto_raw = _decodificar_header(msg.get('Subject', ''))
    match = _RE_ID_NO_ASSUNTO.search(assunto_raw)
    if not match:
        return

    escritural_id = int(match.group(1))
    remetente = _decodificar_header(msg.get('From', ''))
    data_hora = _decodificar_header(msg.get('Date', ''))
    in_reply_to = (msg.get('In-Reply-To') or '').strip()
    corpo = _extrair_texto(msg)

    try:
        dt = email_lib.utils.parsedate_to_datetime(data_hora)
        data_hora_fmt = dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        data_hora_fmt = datetime.now().strftime('%d/%m/%Y %H:%M')

    banco.salvar_email_thread(escritural_id, {
        'message_id': message_id,
        'in_reply_to': in_reply_to,
        'assunto': assunto_raw,
        'remetente': remetente,
        'destinatario': cfg['email'],
        'corpo_texto': corpo,
        'data_hora': data_hora_fmt,
        'direcao': 'recebido',
        'enviado_por': '',
    })


def _poll_usuario(cfg):
    try:
        M = _conectar_imap(cfg)
        M.select('INBOX')
        _, data = M.search(None, 'SUBJECT "[SISPLAN-"')
        uids = data[0].split()
        for uid in uids:
            _, msg_data = M.fetch(uid, '(RFC822)')
            if msg_data and msg_data[0]:
                _processar_mensagem_imap(cfg, uid, msg_data[0][1])
        M.logout()
    except Exception:
        pass


def _loop_polling():
    while True:
        try:
            configs = banco.listar_email_configs_ativos()
            for cfg in configs:
                _poll_usuario(cfg)
        except Exception:
            pass
        time.sleep(_POLLING_INTERVALO)


def iniciar_polling():
    t = threading.Thread(target=_loop_polling, daemon=True, name='imap-polling')
    t.start()


# ── Rotas Flask ───────────────────────────────────────────

@email_escritural_bp.route('/email/config', methods=['GET'])
def email_config_get():
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    uid = session.get('id_usuario')
    if not uid:
        return jsonify({'erro': 'Sessão inválida'}), 401
    cfg = banco.buscar_email_config(uid) or {}
    cfg.pop('senha', None)
    return jsonify(cfg)


@email_escritural_bp.route('/email/config', methods=['POST'])
def email_config_set():
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    uid = session.get('id_usuario')
    if not uid:
        return jsonify({'erro': 'Sessão inválida'}), 401
    dados = request.get_json(silent=True) or {}
    banco.salvar_email_config(uid, dados)
    return jsonify({'sucesso': True})


@email_escritural_bp.route('/email/config/testar', methods=['POST'])
def email_config_testar():
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    uid = session.get('id_usuario')
    cfg = banco.buscar_email_config(uid)
    if not cfg or not cfg.get('smtp_host'):
        return jsonify({'erro': 'Configure o e-mail antes de testar.'}), 400
    try:
        srv = _conectar_smtp(cfg)
        srv.quit()
        return jsonify({'sucesso': True, 'msg': 'Conexão SMTP OK!'})
    except Exception as e:
        return jsonify({'erro': f'Falha SMTP: {e}'}), 502


@email_escritural_bp.route('/email/enviar', methods=['POST'])
def email_enviar():
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    uid = session.get('id_usuario')
    cfg = banco.buscar_email_config(uid)
    if not cfg or not cfg.get('smtp_host') or not cfg.get('senha'):
        return jsonify({'erro': 'Configure seu e-mail em "Configurar e-mail" antes de enviar.'}), 400

    dados = request.get_json(silent=True) or {}
    escritural_id = dados.get('escritural_id')
    destinatario = (dados.get('destinatario') or '').strip()
    assunto = (dados.get('assunto') or '').strip()
    corpo = (dados.get('corpo') or '').strip()
    in_reply_to = (dados.get('in_reply_to') or '').strip() or None
    references = (dados.get('references') or '').strip() or None

    if not escritural_id or not destinatario or not assunto or not corpo:
        return jsonify({'erro': 'Preencha todos os campos.'}), 400

    # Garante o prefixo rastreável no assunto
    if f'[SISPLAN-{escritural_id}]' not in assunto:
        assunto = f'[SISPLAN-{escritural_id}] {assunto}'

    cfg['nome_exibicao'] = session.get('nome', '')
    try:
        msg_id = enviar_email_smtp(cfg, destinatario, assunto, corpo, in_reply_to, references)
    except Exception as e:
        return jsonify({'erro': f'Falha ao enviar: {e}'}), 502

    banco.salvar_email_thread(escritural_id, {
        'message_id': msg_id,
        'in_reply_to': in_reply_to or '',
        'assunto': assunto,
        'remetente': cfg['email'],
        'destinatario': destinatario,
        'corpo_texto': corpo,
        'data_hora': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'direcao': 'enviado',
        'enviado_por': session.get('nome', ''),
    })
    return jsonify({'sucesso': True, 'message_id': msg_id})


@email_escritural_bp.route('/email/thread/<int:escritural_id>', methods=['GET'])
def email_thread_get(escritural_id):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.marcar_lidos_thread(escritural_id)
    msgs = banco.listar_thread_escritural(escritural_id)
    return jsonify(msgs)
