import re
from flask import Blueprint, render_template, request, jsonify, session
import sqlite3
import banco
from utils import usuario_logado

_RE_NOME_TABELA = re.compile(r'^[A-Za-z0-9_]+$')

sql_editor_bp = Blueprint('sql_editor', __name__)


def _tem_acesso():
    if not usuario_logado():
        return False
    if session.get('nivel_acesso') == 'master':
        return True
    return 'editor_sql' in (session.get('telas') or [])


@sql_editor_bp.route('/editor-sql')
def pagina_sql():
    if not _tem_acesso():
        return 'Acesso negado', 403
    return render_template('aba_sql.html', aba_ativa='sql_editor')


@sql_editor_bp.route('/api/sql/tabelas')
def listar_tabelas():
    if not _tem_acesso():
        return jsonify({'erro': 'Acesso negado'}), 403
    conn = banco.conectar()
    try:
        tabelas = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        resultado = {}
        for t in tabelas:
            if not _RE_NOME_TABELA.match(t):
                continue
            cols = conn.execute(f'PRAGMA table_info("{t}")').fetchall()
            resultado[t] = [{'nome': c[1], 'tipo': c[2]} for c in cols]
        return jsonify(resultado)
    finally:
        conn.close()


@sql_editor_bp.route('/api/sql/executar', methods=['POST'])
def executar_sql():
    if not _tem_acesso():
        return jsonify({'erro': 'Acesso negado'}), 403

    sql = (request.get_json() or {}).get('sql', '').strip()
    if not sql:
        return jsonify({'erro': 'SQL vazio'}), 400

    banco.registrar_log(
        usuario=session.get('nome') or session.get('usuario', ''),
        tela='Editor SQL', acao='SQL',
        descricao=sql[:500],
        usuario_id=session.get('id_usuario'),
        nivel=session.get('nivel_acesso', ''),
        ip=request.remote_addr,
    )

    resultados = []
    conn = banco.conectar()
    try:
        # executa cada statement separado por ;
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        for stmt in statements:
            cur = conn.execute(stmt)
            palavra = stmt.split()[0].upper() if stmt.split() else ''
            if palavra == 'SELECT' or cur.description:
                cols = [d[0] for d in (cur.description or [])]
                rows = [list(r) for r in cur.fetchall()]
                resultados.append({
                    'tipo': 'select',
                    'colunas': cols,
                    'linhas': rows,
                    'total': len(rows),
                    'sql': stmt,
                })
            else:
                conn.commit()
                resultados.append({
                    'tipo': 'dml',
                    'afetadas': cur.rowcount,
                    'sql': stmt,
                })
    except Exception as e:
        return jsonify({'erro': str(e)})
    finally:
        conn.close()

    return jsonify({'resultados': resultados})
