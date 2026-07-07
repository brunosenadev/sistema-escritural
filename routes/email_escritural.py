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


def _extrair_html(msg_email):
    """Extrai o corpo HTML de uma mensagem (prefere text/html)."""
    html = ''
    if msg_email.is_multipart():
        for part in msg_email.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if ct == 'text/html' and 'attachment' not in cd:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or 'utf-8'
                html = payload.decode(charset, errors='replace')
                break
    else:
        if msg_email.get_content_type() == 'text/html':
            payload = msg_email.get_payload(decode=True)
            charset = msg_email.get_content_charset() or 'utf-8'
            if payload:
                html = payload.decode(charset, errors='replace')
    return html


_RE_BLOCKQUOTE  = re.compile(r'<blockquote[^>]*>.*?</blockquote>', re.DOTALL | re.IGNORECASE)
_RE_CITE_PREFIX = re.compile(
    r'<(?:div|p)[^>]*class=["\'][^"\']*(?:moz-cite-prefix|gmail_quote_attribution|WordSection)[^"\']*["\'][^>]*>.*?</(?:div|p)>',
    re.DOTALL | re.IGNORECASE,
)
_RE_SCRIPT      = re.compile(r'<script[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)
_RE_ON_ATTRS    = re.compile(r'\s+on\w+="[^"]*"', re.IGNORECASE)


def _strip_quoted_html(html):
    """Remove blocos de citação (histórico) do HTML e scripts."""
    if not html:
        return html
    html = _RE_SCRIPT.sub('', html)
    html = _RE_ON_ATTRS.sub('', html)
    html = _RE_CITE_PREFIX.sub('', html)
    html = _RE_BLOCKQUOTE.sub('', html)
    return html


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

def enviar_email_smtp(cfg, destinatario, assunto, corpo_texto, in_reply_to=None, references=None, assinatura_html=''):
    """
    Envia um e-mail usando as credenciais do cfg.
    Se assinatura_html for fornecida, inclui parte HTML (corpo plain + assinatura).
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

    if assinatura_html:
        corpo_escaped = (corpo_texto
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('\n', '<br>'))
        html_completo = (
            f'<div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;">'
            f'{corpo_escaped}'
            f'</div>'
            f'<br><hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0;">'
            f'{assinatura_html}'
        )
        msg.attach(MIMEText(html_completo, 'html', 'utf-8'))

    srv = _conectar_smtp(cfg)
    srv.sendmail(cfg['email'], [destinatario], msg.as_string())
    srv.quit()
    return msg_id


# ── IMAP polling ──────────────────────────────────────────

def _processar_mensagem_imap(cfg, uid, msg_bytes, direcao=None):
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
    corpo_html = _strip_quoted_html(_extrair_html(msg))

    try:
        dt = email_lib.utils.parsedate_to_datetime(data_hora)
        data_hora_fmt = dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        data_hora_fmt = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Auto-detect direction: se o From é o próprio email do usuário → enviado
    if direcao is None:
        _, from_addr = parseaddr(remetente)
        direcao = 'enviado' if from_addr.lower() == cfg['email'].lower() else 'recebido'

    # Para emails enviados: destinatário vem do header To
    if direcao == 'enviado':
        destinatario = _decodificar_header(msg.get('To', '')) or ''
        _, to_addr = parseaddr(destinatario)
        destinatario = to_addr or destinatario
        _, nome_exib = parseaddr(remetente)
        enviado_por = remetente.split('<')[0].strip().strip('"') or nome_exib
    else:
        destinatario = cfg['email']
        enviado_por = ''

    banco.salvar_email_thread(escritural_id, {
        'message_id': message_id,
        'in_reply_to': in_reply_to,
        'assunto': assunto_raw,
        'remetente': remetente,
        'destinatario': destinatario,
        'corpo_texto': corpo,
        'corpo_html': corpo_html,
        'data_hora': data_hora_fmt,
        'direcao': direcao,
        'enviado_por': enviado_por,
    })

    if direcao == 'recebido':
        try:
            nome_tec = banco.buscar_tecnico_escritural(escritural_id)
            if nome_tec:
                dest = banco.buscar_usuario_por_tecnico(nome_tec)
                if dest and dest.get('recebe_aviso_escritural'):
                    _, from_addr = parseaddr(remetente)
                    banco.criar_notificacao(
                        dest['id'],
                        f'Novo e-mail — Escritural #{escritural_id}',
                        f'De: {from_addr or remetente}',
                        'info',
                    )
        except Exception:
            pass


def _poll_pasta(M, cfg, direcao):
    try:
        _, data = M.search(None, 'SUBJECT "[SISPLAN-"')
        uids = (data[0] or b'').split()
        for uid in uids:
            try:
                _, msg_data = M.fetch(uid, '(RFC822)')
                if msg_data and msg_data[0]:
                    _processar_mensagem_imap(cfg, uid, msg_data[0][1], direcao)
            except Exception:
                pass
    except Exception:
        pass


# Nomes comuns da pasta Enviados em diferentes servidores
_PASTAS_ENVIADOS = ['Sent', 'Sent Messages', 'Sent Items', 'INBOX.Sent', 'Enviad',
                    '[Gmail]/Sent Mail', 'Junk', 'Drafts']


def _poll_usuario(cfg):
    try:
        M = _conectar_imap(cfg)

        # INBOX — emails recebidos
        M.select('INBOX')
        _poll_pasta(M, cfg, 'recebido')

        # Pasta de enviados — emails enviados via Thunderbird/outro cliente
        for nome_pasta in _PASTAS_ENVIADOS:
            try:
                status, _ = M.select(nome_pasta)
                if status == 'OK':
                    _poll_pasta(M, cfg, 'enviado')
                    break
            except Exception:
                continue

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

    # Monta histórico citado (thread) abaixo do novo corpo
    corpo_envio = corpo
    if in_reply_to:
        historico = banco.listar_thread_escritural(escritural_id)
        linhas_hist = []
        for m in historico:
            remetente_h = m.get('remetente') or m.get('enviado_por') or 'Remetente'
            data_h = m.get('data_hora', '')
            corpo_h = (m.get('corpo_texto') or '').strip()
            linhas_hist.append(f'\nEm {data_h}, {remetente_h} escreveu:')
            for linha in corpo_h.splitlines():
                linhas_hist.append(f'> {linha}')
        if linhas_hist:
            corpo_envio = corpo + '\n\n' + '\n'.join(linhas_hist)

    cfg['nome_exibicao'] = session.get('nome', '')
    assinatura_html = (cfg.get('assinatura') or '').strip()
    if assinatura_html:
        base = request.host_url.rstrip('/')
        assinatura_html = re.sub(r'src="(/[^"]*)"', lambda m: f'src="{base}{m.group(1)}"', assinatura_html)
    try:
        msg_id = enviar_email_smtp(cfg, destinatario, assunto, corpo_envio, in_reply_to, references, assinatura_html)
    except Exception as e:
        return jsonify({'erro': f'Falha ao enviar: {e}'}), 502

    banco.salvar_email_thread(escritural_id, {
        'message_id': msg_id,
        'in_reply_to': in_reply_to or '',
        'assunto': assunto,
        'remetente': cfg['email'],
        'destinatario': destinatario,
        'corpo_texto': corpo,  # salva só o novo texto, sem a citação
        'data_hora': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'direcao': 'enviado',
        'enviado_por': session.get('nome', ''),
    })
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Escritural', acao='EMAIL',
        descricao=f'Enviou email para {destinatario} — escritural #{escritural_id} ({assunto})',
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )
    return jsonify({'sucesso': True, 'message_id': msg_id})


@email_escritural_bp.route('/email/thread/<int:escritural_id>', methods=['GET'])
def email_thread_get(escritural_id):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.marcar_lidos_thread(escritural_id)
    msgs = banco.listar_thread_escritural(escritural_id)
    return jsonify(msgs)


# ── Rotas admin: config de e-mail por usuário ─────────────

@email_escritural_bp.route('/api/email-config/<int:usuario_id>', methods=['GET'])
def admin_email_config_get(usuario_id):
    nivel = session.get('nivel_acesso', '')
    if nivel not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    cfg = banco.buscar_email_config(usuario_id) or {}
    cfg.pop('senha', None)
    return jsonify(cfg)


@email_escritural_bp.route('/api/email-config/<int:usuario_id>', methods=['POST'])
def admin_email_config_set(usuario_id):
    nivel = session.get('nivel_acesso', '')
    if nivel not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    dados = request.get_json(silent=True) or {}
    banco.salvar_email_config(usuario_id, dados)
    return jsonify({'sucesso': True})


@email_escritural_bp.route('/api/email-modelo/para-registro/<int:escritural_id>')
def api_modelo_para_registro(escritural_id):
    if checar_tela('escritural'):
        return jsonify({'erro': 'Sem permissão'}), 403
    conn = banco.conectar()
    row = conn.execute("SELECT * FROM escritural WHERE id=?", (escritural_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({}), 200
    registro = dict(row)
    servico = registro.get('servico') or ''
    modelo = banco.buscar_email_modelo_por_servico(servico)
    if not modelo:
        return jsonify({}), 200
    usuario_nome = session.get('nome', '')
    corpo_final, assunto_final = banco.aplicar_parametros_modelo(
        modelo['corpo'], modelo['assunto'], registro, usuario_nome
    )
    return jsonify({
        'modelo_id': modelo['id'],
        'nome': modelo['nome'],
        'assunto': assunto_final,
        'corpo': corpo_final,
    })


@email_escritural_bp.route('/api/email-config/<int:usuario_id>/testar', methods=['POST'])
def admin_email_config_testar(usuario_id):
    nivel = session.get('nivel_acesso', '')
    if nivel not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    cfg = banco.buscar_email_config(usuario_id)
    if not cfg or not cfg.get('smtp_host'):
        return jsonify({'erro': 'Configure o e-mail antes de testar.'}), 400
    try:
        srv = _conectar_smtp(cfg)
        srv.quit()
        return jsonify({'sucesso': True, 'msg': 'Conexão SMTP OK!'})
    except Exception as e:
        return jsonify({'erro': f'Falha SMTP: {e}'}), 502
