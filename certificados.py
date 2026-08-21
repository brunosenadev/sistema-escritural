"""
certificados.py — Conversão de certificado .pfx pra .crt/.key/.pem,
reproduzindo em Python os comandos openssl que o time do escritural
roda manualmente (ver manual do Diogo Donner).

Tudo em memória — nunca escreve o .pfx nem a chave privada em disco.
"""

from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption


class SenhaInvalidaError(Exception):
    pass


def converter_pfx(pfx_bytes: bytes, senha: str) -> dict:
    """Retorna {'crt': bytes, 'key': bytes, 'pem': bytes} em formato PEM.

    - crt: certificado do cliente, sem chave (openssl -clcerts -nokeys)
    - key: certificado do cliente + chave privada sem senha (openssl -clcerts -nodes)
    - pem: certificado do cliente + cadeia de CA, sem chave (openssl -nokeys)
    """
    try:
        chave, cert, cas = pkcs12.load_key_and_certificates(pfx_bytes, senha.encode('utf-8'))
    except ValueError as e:
        raise SenhaInvalidaError('Senha incorreta ou arquivo .pfx inválido.') from e

    if cert is None:
        raise SenhaInvalidaError('O arquivo .pfx não contém um certificado válido.')

    cert_pem = cert.public_bytes(Encoding.PEM)

    key_pem = cert_pem
    if chave is not None:
        key_pem = cert_pem + chave.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        )

    pem_completo = cert_pem
    for ca in (cas or []):
        pem_completo += ca.public_bytes(Encoding.PEM)

    return {'crt': cert_pem, 'key': key_pem, 'pem': pem_completo}
