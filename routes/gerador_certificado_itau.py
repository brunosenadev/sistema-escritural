import io
import re
import zipfile

from flask import Blueprint, render_template, request, send_file, session
import banco
from certificado_itau import (
    gerar_chave_e_csr, solicitar_certificado, montar_pfx,
    normalizar_maiusculas, ErroGeracaoItau,
)
from utils import checar_tela

gerador_certificado_itau_bp = Blueprint('gerador_certificado_itau', __name__)


def _log(descricao):
    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', 'sistema'),
        tela='Gerador de Certificado Itaú', acao='GEROU', descricao=descricao,
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )


def _nome_arquivo_seguro(nome):
    nome = re.sub(r'[^A-Za-z0-9_-]+', '_', (nome or '').strip())
    return nome.strip('_') or 'certificado'


@gerador_certificado_itau_bp.route('/gerador-certificado-itau')
def aba_gerador_certificado_itau():
    bloqueio = checar_tela('gerador_certificado_itau')
    if bloqueio:
        return bloqueio
    return render_template('aba_gerador_certificado_itau.html', erro=None)


@gerador_certificado_itau_bp.route('/gerador-certificado-itau/gerar', methods=['POST'])
def gerar():
    bloqueio = checar_tela('gerador_certificado_itau')
    if bloqueio:
        return bloqueio

    campos = {
        'client_id':    request.form.get('client_id', '').strip(),
        'access_token': request.form.get('access_token', '').strip(),
        'nome_empresa': request.form.get('nome_empresa', '').strip(),
        'cidade':       request.form.get('cidade', '').strip(),
        'uf':           request.form.get('uf', '').strip(),
        'senha_pfx':    request.form.get('senha_pfx', ''),
    }

    def _erro(msg):
        campos_sem_sensiveis = {k: v for k, v in campos.items() if k not in ('access_token', 'senha_pfx')}
        return render_template('aba_gerador_certificado_itau.html', erro=msg, **campos_sem_sensiveis)

    obrigatorios = ['client_id', 'access_token', 'nome_empresa', 'cidade', 'uf', 'senha_pfx']
    faltando = [c for c in obrigatorios if not campos[c]]
    if faltando:
        return _erro('Preencha todos os campos.')

    nome_empresa = normalizar_maiusculas(campos['nome_empresa'])
    cidade       = normalizar_maiusculas(campos['cidade'])
    uf           = normalizar_maiusculas(campos['uf'])

    try:
        chave, chave_pem, csr_pem = gerar_chave_e_csr(campos['client_id'], nome_empresa, cidade, uf)
        resultado = solicitar_certificado(csr_pem, campos['access_token'])
        pfx_bytes = montar_pfx(chave, resultado['certificado_pem'], campos['senha_pfx'])
    except ErroGeracaoItau as e:
        return _erro(str(e))

    base = _nome_arquivo_seguro(campos['client_id'])

    buffer_zip = io.BytesIO()
    with zipfile.ZipFile(buffer_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('certificate.crt', resultado['certificado_pem'])
        zf.writestr('certificate.key', chave_pem)
        zf.writestr('certificado.pfx', pfx_bytes)
        zf.writestr(
            'ClientID_e_Secret.txt',
            f"Secret: {resultado['secret']}\nClient_ID: {campos['client_id']}\n"
        )
    buffer_zip.seek(0)

    _log(f"Gerou certificado Itaú — client_id {campos['client_id']} ({nome_empresa})")

    return send_file(
        buffer_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'certificado_itau_{base}.zip',
    )
