"""
Ponto de entrada do EscrituralWeb.exe (servidor Windows, rodando como serviço pelo NSSM).

  EscrituralWeb.exe            -> sobe o sistema na porta 8000 (ou PORTA do .env)
  EscrituralWeb.exe backup     -> cópia do banco em data\\backups (mantém as 7 últimas)

O .env, a pasta data\\ e logs\\ ficam ao lado do .exe e não fazem parte do build.
Gerar o .exe: deploy\\windows\\build_exe.bat
"""
import datetime
import glob
import os
import sqlite3
import sys

PASTA = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
os.chdir(PASTA)

from dotenv import load_dotenv  # noqa: E402

# .env primeiro: o DB_PATH dele vale; sem ele, o banco fica em data\banco_dados.db
load_dotenv(os.path.join(PASTA, '.env'))
os.environ.setdefault('DB_PATH', os.path.join(PASTA, 'data', 'banco_dados.db'))


def backup():
    origem = os.environ['DB_PATH']
    pasta = os.path.join(os.path.dirname(origem), 'backups')
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, datetime.datetime.now().strftime('banco_%Y-%m-%d_%H-%M.db'))
    with sqlite3.connect(origem) as de, sqlite3.connect(destino) as para:
        de.backup(para)  # cópia consistente mesmo com o sistema no ar
    for antigo in sorted(glob.glob(os.path.join(pasta, 'banco_*.db')))[:-7]:
        os.remove(antigo)
    print('Backup criado:', destino)


def servir():
    from werkzeug.serving import run_simple
    from app import app
    porta = int(os.environ.get('PORTA', '8000'))
    print(f'Escritural Web em http://0.0.0.0:{porta}  (banco: {os.environ["DB_PATH"]})', flush=True)
    run_simple('0.0.0.0', porta, app, threaded=True, use_reloader=False, use_debugger=False)


if __name__ == '__main__':
    backup() if sys.argv[1:2] == ['backup'] else servir()
