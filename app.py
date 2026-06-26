"""
app.py — Ponto de entrada do Sisplan.
Cria o app Flask, registra os blueprints e inicia o servidor.
"""

import os
from flask import Flask, session
import banco
from routes.auth        import auth_bp
from routes.pendente    import pendente_bp
from routes.homologados import homologados_bp
from routes.cancelados  import cancelados_bp
from routes.importacao  import importacao_bp
from routes.config      import config_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sisplan-escritural-chave-secreta-2026')

if not os.environ.get('DATABASE_URL'):
    # Localmente inicializa o SQLite normalmente
    banco.inicializar_banco()
    banco.migrar_pendentes_legados()
else:
    # Em produção (Vercel+Neon) as tabelas já existem; só inicializa na primeira vez
    try:
        banco.conectar().execute("SELECT 1 FROM usuarios LIMIT 1")
    except Exception:
        banco.inicializar_banco()

app.register_blueprint(auth_bp)
app.register_blueprint(pendente_bp)
app.register_blueprint(homologados_bp)
app.register_blueprint(cancelados_bp)
app.register_blueprint(importacao_bp)
app.register_blueprint(config_bp)


@app.template_filter('css_status')
def filtro_css_status(status_texto):
    mapa = {
        'aguardando banco':        'status-aguardando-banco',
        'aguardando cliente':      'status-aguardando-cliente',
        'aguardando comercial':    'status-aguardando-comercial',
        'aguardando atualização':  'status-aguardando-atualizacao',
        'aguardando atualizacao':  'status-aguardando-atualizacao',
        'homologado':              'status-homologado',
        'falta cadastrar':         'status-falta-cadastrar',
        'pendente de treinamento': 'status-pendente-treinamento',
        'pendencia em prog':       'status-pendencia-em-prog',
        'em processo':             'status-em-processo',
        'cancelado':               'status-cancelado',
    }
    return mapa.get(str(status_texto).lower().strip(), 'status-padrao')


@app.context_processor
def injetar_globais():
    totais = banco.contar_todos()
    return {
        'nivel_acesso':            session.get('nivel_acesso', ''),
        'nome_usuario':            session.get('nome', ''),
        'total_pendentes_db':      totais['pendentes'],
        'total_cancelados_db':     totais['cancelados'],
        'total_hom_cobranca_db':   totais['cobranca'],
        'total_hom_pagamentos_db': totais['pagamentos'],
        'total_hom_extrato_db':    totais['extrato'],
    }


if __name__ == '__main__':
    app.run(debug=True, port=5000)
