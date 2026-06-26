"""
banco.py — Camada de acesso ao banco de dados (SQLite).

Em produção (Render) define DB_PATH=/data/banco_dados.db para usar o disco persistente.
Localmente usa banco_dados.db na raiz do projeto.
"""

import os
import sqlite3
from datetime import datetime

CAMINHO_BANCO = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), 'banco_dados.db'))

# ── Dados iniciais ────────────────────────────────────────

USUARIOS_INICIAIS = [
    {'usuario': 'admin',  'senha': 'admin123',  'nome': 'Administrador', 'nivel': 'admin',  'tecnico_vinculado': None},
    {'usuario': 'heitor', 'senha': 'heitor123', 'nome': 'Heitor',        'nivel': 'normal', 'tecnico_vinculado': 'HEITOR'},
    {'usuario': 'camili', 'senha': 'camili123', 'nome': 'Camili',        'nivel': 'normal', 'tecnico_vinculado': 'CAMILI'},
    {'usuario': 'diogo',  'senha': 'diogo123',  'nome': 'Diogo',         'nivel': 'normal', 'tecnico_vinculado': 'DIOGO D.'},
]

TECNICOS_INICIAIS = [
    {'nome': 'HEITOR',   'cor': '#1d4ed8'},
    {'nome': 'CAMILI',   'cor': '#0891b2'},
    {'nome': 'DIOGO D.', 'cor': '#7c3aed'},
    {'nome': 'SEM TEC.', 'cor': '#64748b'},
]

STATUS_INICIAIS = [
    'AGUARDANDO BANCO', 'AGUARDANDO CLIENTE', 'AGUARDANDO COMERCIAL',
    'AGUARDANDO ATUALIZAÇÃO', 'HOMOLOGADO', 'FALTA CADASTRAR',
    'PENDENTE DE TREINAMENTO', 'PENDENCIA EM PROG', 'EM PROCESSO', 'CANCELADO',
]

SERVICOS_INICIAIS = [
    'COBRANÇA', 'COBRANÇA/API', 'PAGFOR', 'PAGFOR/API', 'EXTRATO', 'PAGAMENTO',
]

# ── Conexão ───────────────────────────────────────────────

def conectar():
    conn = sqlite3.connect(CAMINHO_BANCO)
    conn.row_factory = sqlite3.Row
    return conn

# ── Inicialização ─────────────────────────────────────────

def inicializar_banco():
    conn = conectar()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario           TEXT    UNIQUE NOT NULL,
            senha             TEXT    NOT NULL,
            nome              TEXT    NOT NULL,
            nivel             TEXT    NOT NULL DEFAULT 'normal',
            tecnico_vinculado TEXT,
            mudar_senha       INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS tecnicos (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT    UNIQUE NOT NULL,
            cor  TEXT    NOT NULL DEFAULT '#64748b'
        );
        CREATE TABLE IF NOT EXISTS status_lista (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT    UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS servicos_lista (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            texto              TEXT    UNIQUE NOT NULL,
            destino_homologado TEXT    DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS pendentes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tecnico       TEXT,
            empresa       TEXT,
            servico       TEXT,
            banco         TEXT,
            dt_solicita   TEXT,
            dt_status     TEXT,
            status        TEXT,
            obs           TEXT,
            criado_por    TEXT,
            criado_em     TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS cancelados (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tecnico       TEXT,
            empresa       TEXT,
            servico       TEXT,
            banco         TEXT,
            carteira      TEXT,
            conta         TEXT,
            dt_solicita   TEXT,
            dt_status     TEXT,
            status        TEXT DEFAULT 'CANCELADO',
            retorno       TEXT,
            ordem_servico TEXT,
            obs           TEXT,
            criado_por    TEXT,
            criado_em     TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS homologados_cobranca (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tecnico       TEXT,
            empresa       TEXT,
            servico       TEXT,
            banco         TEXT,
            dt_solicita   TEXT,
            dt_status     TEXT,
            status        TEXT DEFAULT 'HOMOLOGADO',
            obs           TEXT,
            criado_por    TEXT,
            criado_em     TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS homologados_pagamentos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tecnico       TEXT,
            empresa       TEXT,
            servico       TEXT,
            banco         TEXT,
            dt_solicita   TEXT,
            dt_status     TEXT,
            status        TEXT DEFAULT 'HOMOLOGADO',
            obs           TEXT,
            criado_por    TEXT,
            criado_em     TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS homologados_extrato (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tecnico       TEXT,
            empresa       TEXT,
            servico       TEXT,
            banco         TEXT,
            dt_solicita   TEXT,
            dt_status     TEXT,
            status        TEXT DEFAULT 'HOMOLOGADO',
            obs           TEXT,
            criado_por    TEXT,
            criado_em     TEXT DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        for u in USUARIOS_INICIAIS:
            conn.execute(
                "INSERT INTO usuarios (usuario,senha,nome,nivel,tecnico_vinculado) VALUES (?,?,?,?,?)",
                (u['usuario'], u['senha'], u['nome'], u['nivel'], u['tecnico_vinculado'])
            )

    if conn.execute("SELECT COUNT(*) FROM tecnicos").fetchone()[0] == 0:
        for t in TECNICOS_INICIAIS:
            conn.execute("INSERT INTO tecnicos (nome,cor) VALUES (?,?)", (t['nome'], t['cor']))

    for s in STATUS_INICIAIS:
        conn.execute("INSERT OR IGNORE INTO status_lista (texto) VALUES (?)", (s,))

    if conn.execute("SELECT COUNT(*) FROM servicos_lista").fetchone()[0] == 0:
        for s in SERVICOS_INICIAIS:
            conn.execute("INSERT INTO servicos_lista (texto) VALUES (?)", (s,))

    conn.commit()

    # Migrações para bancos já existentes
    for ddl in [
        "ALTER TABLE servicos_lista ADD COLUMN destino_homologado TEXT DEFAULT ''",
        "ALTER TABLE usuarios ADD COLUMN mudar_senha INTEGER DEFAULT 0",
    ]:
        try:
            conn.execute(ddl)
            conn.commit()
        except Exception:
            pass

    conn.close()

# ── Autenticação ──────────────────────────────────────────

def buscar_id_usuario(login):
    conn = conectar()
    row = conn.execute("SELECT id FROM usuarios WHERE LOWER(usuario)=LOWER(?)", (login,)).fetchone()
    conn.close()
    return row['id'] if row else None


def buscar_usuario_por_login(usuario_digitado, senha_digitada):
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE LOWER(usuario)=LOWER(?) AND senha=?",
        (usuario_digitado.strip(), senha_digitada)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

# ── Técnicos ──────────────────────────────────────────────

def listar_tecnicos():
    conn = conectar()
    rows = conn.execute("SELECT * FROM tecnicos ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_tecnico(nome, cor):
    try:
        conn = conectar()
        conn.execute("INSERT INTO tecnicos (nome,cor) VALUES (?,?)", (nome.strip().upper(), cor))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def atualizar_tecnico(nome_original, novo_nome, nova_cor):
    conn = conectar()
    conn.execute("UPDATE tecnicos SET nome=?,cor=? WHERE nome=?", (novo_nome.strip().upper(), nova_cor, nome_original))
    conn.commit()
    conn.close()


def remover_tecnico(nome):
    conn = conectar()
    conn.execute("DELETE FROM tecnicos WHERE nome=?", (nome,))
    conn.commit()
    conn.close()

# ── Usuários ──────────────────────────────────────────────

def listar_usuarios():
    conn = conectar()
    rows = conn.execute("SELECT * FROM usuarios ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_usuario(dados):
    try:
        conn = conectar()
        conn.execute(
            "INSERT INTO usuarios (usuario,senha,nome,nivel,tecnico_vinculado,mudar_senha) VALUES (?,?,?,?,?,1)",
            (dados['usuario'].strip().lower(), dados['senha'], dados['nome'].strip(),
             dados['nivel'], dados.get('tecnico_vinculado') or None)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def atualizar_usuario(id_usuario, campos):
    conn = conectar()
    if campos.get('senha'):
        conn.execute(
            "UPDATE usuarios SET nome=?,nivel=?,tecnico_vinculado=?,senha=? WHERE id=?",
            (campos.get('nome'), campos.get('nivel'), campos.get('tecnico_vinculado') or None,
             campos['senha'], id_usuario)
        )
    else:
        conn.execute(
            "UPDATE usuarios SET nome=?,nivel=?,tecnico_vinculado=? WHERE id=?",
            (campos.get('nome'), campos.get('nivel'), campos.get('tecnico_vinculado') or None,
             id_usuario)
        )
    conn.commit()
    conn.close()


def resetar_senha_usuario(id_usuario):
    conn = conectar()
    conn.execute("UPDATE usuarios SET senha=?,mudar_senha=1 WHERE id=?", ('123456', id_usuario))
    conn.commit()
    conn.close()


def alterar_minha_senha(id_usuario, nova_senha):
    conn = conectar()
    conn.execute("UPDATE usuarios SET senha=?,mudar_senha=0 WHERE id=?", (nova_senha, id_usuario))
    conn.commit()
    conn.close()


def remover_usuario(id_usuario):
    conn = conectar()
    usuario = conn.execute("SELECT nivel FROM usuarios WHERE id=?", (id_usuario,)).fetchone()
    if usuario and usuario['nivel'] == 'admin':
        total = conn.execute("SELECT COUNT(*) FROM usuarios WHERE nivel='admin'").fetchone()[0]
        if total <= 1:
            conn.close()
            return False
    conn.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
    conn.commit()
    conn.close()
    return True

# ── Status ────────────────────────────────────────────────

def listar_status():
    conn = conectar()
    rows = conn.execute("SELECT texto FROM status_lista ORDER BY id").fetchall()
    conn.close()
    return [r['texto'] for r in rows]


def adicionar_status(texto):
    try:
        conn = conectar()
        conn.execute("INSERT INTO status_lista (texto) VALUES (?)", (texto.strip().upper(),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def remover_status(texto):
    conn = conectar()
    conn.execute("DELETE FROM status_lista WHERE texto=?", (texto,))
    conn.commit()
    conn.close()

# ── Serviços ──────────────────────────────────────────────

def listar_servicos():
    conn = conectar()
    rows = conn.execute("SELECT texto FROM servicos_lista ORDER BY id").fetchall()
    conn.close()
    return [r['texto'] for r in rows]


def listar_servicos_completo():
    conn = conectar()
    rows = conn.execute("SELECT texto,destino_homologado FROM servicos_lista ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_servico(texto):
    try:
        conn = conectar()
        conn.execute("INSERT INTO servicos_lista (texto) VALUES (?)", (texto.strip().upper(),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def remover_servico(texto):
    conn = conectar()
    conn.execute("DELETE FROM servicos_lista WHERE texto=?", (texto,))
    conn.commit()
    conn.close()


def atualizar_destino_servico(texto, destino):
    conn = conectar()
    conn.execute("UPDATE servicos_lista SET destino_homologado=? WHERE texto=?", (destino or '', texto))
    conn.commit()
    conn.close()

# ── Contadores (sidebar) ──────────────────────────────────

def contar_todos():
    conn = conectar()
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM pendentes)              AS pendentes,
            (SELECT COUNT(*) FROM cancelados)             AS cancelados,
            (SELECT COUNT(*) FROM homologados_cobranca)   AS cobranca,
            (SELECT COUNT(*) FROM homologados_pagamentos) AS pagamentos,
            (SELECT COUNT(*) FROM homologados_extrato)    AS extrato
    """).fetchone()
    conn.close()
    return dict(row)


def contar_pendentes():
    conn = conectar()
    n = conn.execute("SELECT COUNT(*) FROM pendentes").fetchone()[0]
    conn.close()
    return n


def contar_cancelados():
    conn = conectar()
    n = conn.execute("SELECT COUNT(*) FROM cancelados").fetchone()[0]
    conn.close()
    return n


def contar_homologados_cobranca():
    conn = conectar()
    n = conn.execute("SELECT COUNT(*) FROM homologados_cobranca").fetchone()[0]
    conn.close()
    return n


def contar_homologados_pagamentos():
    conn = conectar()
    n = conn.execute("SELECT COUNT(*) FROM homologados_pagamentos").fetchone()[0]
    conn.close()
    return n


def contar_homologados_extrato():
    conn = conectar()
    n = conn.execute("SELECT COUNT(*) FROM homologados_extrato").fetchone()[0]
    conn.close()
    return n

# ── Aba Pendente ──────────────────────────────────────────

def listar_pendentes():
    conn = conectar()
    rows = conn.execute("SELECT * FROM pendentes ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_pendente(dados, criado_por=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO pendentes (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status',''), dados.get('obs',''), criado_por)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_pendente(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE pendentes SET tecnico=?,empresa=?,servico=?,banco=?,dt_solicita=?,dt_status=?,status=?,obs=?,atualizado_em=? WHERE id=?",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status',''), dados.get('obs',''), agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def deletar_pendente(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM pendentes WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


def importar_pendentes(lista_registros, substituir=True):
    conn = conectar()
    if substituir:
        conn.execute("DELETE FROM pendentes")
    for reg in lista_registros:
        conn.execute(
            "INSERT INTO pendentes (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
            (reg.get('tecnico',''), reg.get('empresa',''), reg.get('servico',''),
             reg.get('banco',''), reg.get('dt_solicita',''), reg.get('dt_status',''),
             reg.get('status',''), reg.get('obs',''), 'importação planilha')
        )
    total = conn.execute("SELECT COUNT(*) FROM pendentes").fetchone()[0]
    conn.commit()
    conn.close()
    return total


def migrar_pendentes_legados():
    conn = conectar()
    hom = [dict(r) for r in conn.execute("SELECT * FROM pendentes WHERE UPPER(TRIM(status))='HOMOLOGADO'").fetchall()]
    can = [dict(r) for r in conn.execute("SELECT * FROM pendentes WHERE UPPER(TRIM(status))='CANCELADO'").fetchall()]
    conn.close()
    for d in hom:
        mover_pendente_para_homologado(d['id'])
    for d in can:
        mover_pendente_para_cancelado(d['id'])
    return len(hom), len(can)

# ── Aba Cancelados ────────────────────────────────────────

def listar_cancelados():
    conn = conectar()
    rows = conn.execute("SELECT * FROM cancelados ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_cancelado(dados, criado_por=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO cancelados (tecnico,empresa,servico,banco,carteira,conta,dt_solicita,dt_status,status,retorno,ordem_servico,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('carteira',''), dados.get('conta',''),
         dados.get('dt_solicita',''), dados.get('dt_status',''), dados.get('status','CANCELADO'),
         dados.get('retorno',''), dados.get('ordem_servico',''), dados.get('obs',''), criado_por)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_cancelado(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE cancelados SET tecnico=?,empresa=?,servico=?,banco=?,carteira=?,conta=?,dt_solicita=?,dt_status=?,status=?,retorno=?,ordem_servico=?,obs=?,atualizado_em=? WHERE id=?",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('carteira',''), dados.get('conta',''),
         dados.get('dt_solicita',''), dados.get('dt_status',''), dados.get('status','CANCELADO'),
         dados.get('retorno',''), dados.get('ordem_servico',''), dados.get('obs',''),
         agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def deletar_cancelado(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM cancelados WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


def mover_pendente_para_cancelado(id_pendente):
    conn = conectar()
    row = conn.execute("SELECT * FROM pendentes WHERE id=?", (id_pendente,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    cur = conn.execute(
        "INSERT INTO cancelados (tecnico,empresa,servico,banco,carteira,conta,dt_solicita,dt_status,status,retorno,ordem_servico,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (d['tecnico'], d['empresa'], d['servico'], d['banco'], '', '',
         d['dt_solicita'], d['dt_status'], 'CANCELADO', '', '', d['obs'], d.get('criado_por',''))
    )
    conn.execute("DELETE FROM pendentes WHERE id=?", (id_pendente,))
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def importar_cancelados(lista_registros, substituir=True):
    conn = conectar()
    if substituir:
        conn.execute("DELETE FROM cancelados")
    for reg in lista_registros:
        conn.execute(
            "INSERT INTO cancelados (tecnico,empresa,servico,banco,carteira,conta,dt_solicita,dt_status,status,retorno,ordem_servico,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (reg.get('tecnico',''), reg.get('empresa',''), reg.get('servico',''),
             reg.get('banco',''), reg.get('carteira',''), reg.get('conta',''),
             reg.get('dt_solicita',''), reg.get('dt_status',''), reg.get('status','CANCELADO'),
             reg.get('retorno',''), reg.get('ordem_servico',''), reg.get('obs',''), 'importação planilha')
        )
    total = conn.execute("SELECT COUNT(*) FROM cancelados").fetchone()[0]
    conn.commit()
    conn.close()
    return total

# ── Roteamento de homologados ─────────────────────────────

def _aba_homologado(servico):
    conn = conectar()
    row = conn.execute(
        "SELECT destino_homologado FROM servicos_lista WHERE UPPER(TRIM(texto))=UPPER(TRIM(?))",
        (servico or '',)
    ).fetchone()
    conn.close()
    if row and row['destino_homologado']:
        return row['destino_homologado']
    s = (servico or '').upper().strip()
    if 'EXTRAT' in s: return 'extrato'
    if 'COBR' in s:   return 'cobranca'
    return 'pagamentos'


_TABELA_HOMOLOGADO = {
    'cobranca':   'homologados_cobranca',
    'pagamentos': 'homologados_pagamentos',
    'extrato':    'homologados_extrato',
}


def mover_pendente_para_homologado(id_pendente):
    conn = conectar()
    row = conn.execute("SELECT * FROM pendentes WHERE id=?", (id_pendente,)).fetchone()
    if not row:
        conn.close()
        return None, None
    d      = dict(row)
    aba    = _aba_homologado(d['servico'])
    tabela = _TABELA_HOMOLOGADO[aba]
    cur = conn.execute(
        f"INSERT INTO {tabela} (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (d['tecnico'], d['empresa'], d['servico'], d['banco'],
         d['dt_solicita'], d['dt_status'], 'HOMOLOGADO', d['obs'], d.get('criado_por',''))
    )
    conn.execute("DELETE FROM pendentes WHERE id=?", (id_pendente,))
    conn.commit()
    conn.close()
    return cur.lastrowid, aba


def mover_homologado_para_pendente(id_registro, tipo, novo_status):
    tabela = f'homologados_{tipo}'
    conn = conectar()
    row = conn.execute(f"SELECT * FROM {tabela} WHERE id=?", (id_registro,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    cur = conn.execute(
        "INSERT INTO pendentes (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (d.get('tecnico',''), d.get('empresa',''), d.get('servico',''), d.get('banco',''),
         d.get('dt_solicita',''), d.get('dt_status',''), novo_status, d.get('obs',''), 'retorno de homologados')
    )
    conn.execute(f"DELETE FROM {tabela} WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return cur.lastrowid


def mover_homologado_para_cancelado(id_registro, tipo):
    tabela = f'homologados_{tipo}'
    conn = conectar()
    row = conn.execute(f"SELECT * FROM {tabela} WHERE id=?", (id_registro,)).fetchone()
    if not row:
        conn.close()
        return None
    d = dict(row)
    cur = conn.execute(
        "INSERT INTO cancelados (tecnico,empresa,servico,banco,carteira,conta,dt_solicita,dt_status,status,retorno,ordem_servico,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (d.get('tecnico',''), d.get('empresa',''), d.get('servico',''), d.get('banco',''),
         '', '', d.get('dt_solicita',''), d.get('dt_status',''), 'CANCELADO',
         '', '', d.get('obs',''), 'movido de homologados')
    )
    conn.execute(f"DELETE FROM {tabela} WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return cur.lastrowid

# ── Homologados Cobrança ──────────────────────────────────

def listar_homologados_cobranca():
    conn = conectar()
    rows = conn.execute("SELECT * FROM homologados_cobranca ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_homologado_cobranca(dados, criado_por=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO homologados_cobranca (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), criado_por)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_homologado_cobranca(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE homologados_cobranca SET tecnico=?,empresa=?,servico=?,banco=?,dt_solicita=?,dt_status=?,status=?,obs=?,atualizado_em=? WHERE id=?",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def deletar_homologado_cobranca(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM homologados_cobranca WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


def importar_homologados_cobranca(lista_registros, substituir=True):
    conn = conectar()
    if substituir:
        conn.execute("DELETE FROM homologados_cobranca")
    for reg in lista_registros:
        conn.execute(
            "INSERT INTO homologados_cobranca (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
            (reg.get('tecnico',''), reg.get('empresa',''), reg.get('servico',''),
             reg.get('banco',''), reg.get('dt_solicita',''), reg.get('dt_status',''),
             reg.get('status','HOMOLOGADO'), reg.get('obs',''), 'importação planilha')
        )
    total = conn.execute("SELECT COUNT(*) FROM homologados_cobranca").fetchone()[0]
    conn.commit()
    conn.close()
    return total

# ── Homologados Pagamentos ────────────────────────────────

def listar_homologados_pagamentos():
    conn = conectar()
    rows = conn.execute("SELECT * FROM homologados_pagamentos ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_homologado_pagamentos(dados, criado_por=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO homologados_pagamentos (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), criado_por)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_homologado_pagamentos(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE homologados_pagamentos SET tecnico=?,empresa=?,servico=?,banco=?,dt_solicita=?,dt_status=?,status=?,obs=?,atualizado_em=? WHERE id=?",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def deletar_homologado_pagamentos(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM homologados_pagamentos WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


def importar_homologados_pagamentos(lista_registros, substituir=True):
    conn = conectar()
    if substituir:
        conn.execute("DELETE FROM homologados_pagamentos")
    for reg in lista_registros:
        conn.execute(
            "INSERT INTO homologados_pagamentos (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
            (reg.get('tecnico',''), reg.get('empresa',''), reg.get('servico',''),
             reg.get('banco',''), reg.get('dt_solicita',''), reg.get('dt_status',''),
             reg.get('status','HOMOLOGADO'), reg.get('obs',''), 'importação planilha')
        )
    total = conn.execute("SELECT COUNT(*) FROM homologados_pagamentos").fetchone()[0]
    conn.commit()
    conn.close()
    return total

# ── Homologados Extrato ───────────────────────────────────

def listar_homologados_extrato():
    conn = conectar()
    rows = conn.execute("SELECT * FROM homologados_extrato ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_homologado_extrato(dados, criado_por=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO homologados_extrato (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), criado_por)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_homologado_extrato(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE homologados_extrato SET tecnico=?,empresa=?,servico=?,banco=?,dt_solicita=?,dt_status=?,status=?,obs=?,atualizado_em=? WHERE id=?",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def deletar_homologado_extrato(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM homologados_extrato WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


def importar_homologados_extrato(lista_registros, substituir=True):
    conn = conectar()
    if substituir:
        conn.execute("DELETE FROM homologados_extrato")
    for reg in lista_registros:
        conn.execute(
            "INSERT INTO homologados_extrato (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
            (reg.get('tecnico',''), reg.get('empresa',''), reg.get('servico',''),
             reg.get('banco',''), reg.get('dt_solicita',''), reg.get('dt_status',''),
             reg.get('status','HOMOLOGADO'), reg.get('obs',''), 'importação planilha')
        )
    total = conn.execute("SELECT COUNT(*) FROM homologados_extrato").fetchone()[0]
    conn.commit()
    conn.close()
    return total
