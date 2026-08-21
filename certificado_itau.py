"""
certificado_itau.py — Geração automatizada do certificado dinâmico mTLS do
Itaú, reproduzindo em Python o script oficial do Itaú (ver
"INSTRUCOES-GERACAO-DO-CERTIFICADO-WINDOWS-1.pdf"):

1. Gera chave privada + CSR localmente (equivalente a `openssl req -new`).
2. Envia o CSR pro endpoint de solicitação do Itaú, autenticado com o
   access_token fornecido pelo próprio Itaú junto com o client_id.
3. Extrai o certificado assinado (.crt) e o Secret da resposta.
4. Opcionalmente empacota tudo num .pfx.

Tudo em memória — nunca escreve nada em disco nem persiste em banco.
"""

import re
import unicodedata

import requests
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

URL_SOLICITACAO = 'https://sts.itau.com.br/seguranca/v1/certificado/solicitacao'


class ErroGeracaoItau(Exception):
    pass


def normalizar_maiusculas(texto: str) -> str:
    """Maiúsculas sem acento/cedilha — mesmo padrão exigido pelo script do Itaú."""
    texto = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode('ascii')
    return texto.strip().upper()


def gerar_chave_e_csr(client_id: str, nome_empresa: str, cidade: str, uf: str):
    """Retorna (chave_privada, chave_pem, csr_pem) — equivalente ao `openssl req -new -newkey rsa:2048`."""
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    nome = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, client_id),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, nome_empresa),
        x509.NameAttribute(NameOID.LOCALITY_NAME, cidade),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, uf),
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'BR'),
    ])
    csr = x509.CertificateSigningRequestBuilder().subject_name(nome).sign(chave, hashes.SHA512())

    csr_pem = csr.public_bytes(serialization.Encoding.PEM)
    chave_pem = chave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return chave, chave_pem, csr_pem


def solicitar_certificado(csr_pem: bytes, access_token: str) -> dict:
    """Envia o CSR pro Itaú e devolve {'secret': str, 'certificado_pem': bytes}."""
    try:
        resp = requests.post(
            URL_SOLICITACAO,
            data=csr_pem,
            headers={
                'Content-Type': 'text/plain',
                'Authorization': f'Bearer {access_token}',
            },
            timeout=30,
        )
    except requests.RequestException as e:
        raise ErroGeracaoItau(f'Falha de comunicação com o Itaú: {e}') from e

    if resp.status_code != 200:
        raise ErroGeracaoItau(f'Itaú retornou erro {resp.status_code}: {resp.text[:300]}')

    texto = resp.text
    m_secret = re.search(r'^Secret:\s*(.+)$', texto, re.MULTILINE)
    m_cert = re.search(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', texto, re.DOTALL)
    if not m_secret or not m_cert:
        raise ErroGeracaoItau('Não foi possível extrair o certificado ou o Secret da resposta do Itaú.')

    return {
        'secret': m_secret.group(1).strip(),
        'certificado_pem': (m_cert.group(0) + '\n').encode('utf-8'),
    }


def montar_pfx(chave, certificado_pem: bytes, senha: str) -> bytes:
    certificado = x509.load_pem_x509_certificate(certificado_pem)
    return pkcs12.serialize_key_and_certificates(
        name=b'certificado',
        key=chave,
        cert=certificado,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(senha.encode('utf-8')),
    )
