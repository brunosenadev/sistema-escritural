import io
import os
import re
import zipfile

from flask import Blueprint, render_template, request, send_file, session
import banco
from certificados import converter_pfx, SenhaInvalidaError
from utils import checar_tela

conversor_certificado_bp = Blueprint('conversor_certificado', __name__)

TIPOS_SERVICO = [
    ('cobranca',  'Cobrança',  'COBRANCA'),
    ('pagamento', 'Pagamento', 'PAGAMENTO'),
    ('extrato',   'Extrato',   'EXTRATO'),
    ('pix',       'Pix',       'PIX'),
]
_PASTA_POR_TIPO = {chave: pasta for chave, _, pasta in TIPOS_SERVICO}


def _log(descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Conversor de Certificado', acao='CONVERTEU', descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


def _nome_arquivo_seguro(nome):
    nome = re.sub(r'[^A-Za-z0-9_-]+', '_', (nome or '').strip())
    return nome.strip('_') or 'certificado'


@conversor_certificado_bp.route('/conversor-certificado')
def aba_conversor_certificado():
    bloqueio = checar_tela('conversor_certificado')
    if bloqueio:
        return bloqueio
    return render_template('aba_conversor_certificado.html', erro=None, tipos_servico=TIPOS_SERVICO)


@conversor_certificado_bp.route('/conversor-certificado/converter', methods=['POST'])
def converter():
    bloqueio = checar_tela('conversor_certificado')
    if bloqueio:
        return bloqueio

    conta       = request.form.get('conta', '').strip()
    senha       = request.form.get('senha', '')
    tipos_sel   = request.form.getlist('tipos')
    arq         = request.files.get('pfx')

    def _erro(msg):
        return render_template(
            'aba_conversor_certificado.html', erro=msg,
            conta=conta, tipos_servico=TIPOS_SERVICO, tipos_marcados=tipos_sel,
        )

    if not arq or not arq.filename:
        return _erro('Selecione o arquivo .pfx.')
    if os.path.splitext(arq.filename)[1].lower() != '.pfx':
        return _erro('O arquivo deve ter extensão .pfx.')
    if not senha:
        return _erro('Informe a senha do certificado.')
    if not conta:
        return _erro('Informe a conta.')
    if not tipos_sel:
        return _erro('Selecione ao menos um tipo de serviço.')

    pfx_bytes = arq.read()

    try:
        arquivos = converter_pfx(pfx_bytes, senha)
    except SenhaInvalidaError as e:
        return _erro(str(e))
    finally:
        pfx_bytes = None  # nunca fica retido além do necessário pra conversão

    conta_segura = _nome_arquivo_seguro(conta)

    buffer_zip = io.BytesIO()
    with zipfile.ZipFile(buffer_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for tipo in tipos_sel:
            pasta = _PASTA_POR_TIPO.get(tipo)
            if not pasta:
                continue
            zf.writestr(f'{conta_segura}/{pasta}/certificate.crt', arquivos['crt'])
            zf.writestr(f'{conta_segura}/{pasta}/certificate.key', arquivos['key'])
            zf.writestr(f'{conta_segura}/{pasta}/certificate.pem', arquivos['pem'])
    buffer_zip.seek(0)

    pastas_geradas = ', '.join(_PASTA_POR_TIPO[t] for t in tipos_sel if t in _PASTA_POR_TIPO)
    _log(f'Converteu certificado — conta {conta} ({pastas_geradas})')

    return send_file(
        buffer_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{conta_segura}.zip',
    )
