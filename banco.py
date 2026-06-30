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

SETORES_INICIAIS = [
    'GESTOR SUPORTE', 'GESTOR PROGRAMAÇÃO', 'PROGRAMAÇÃO', 'SUPORTE',
]

HUB_BANCOS_INICIAIS = [
    # (nome, envio, instrucao, retorno, bol, pix, extrato, dda, ordem)
    ('Ailos',          1, 0, 1, 0, 0, 0, 0, 1),
    ('Banco do Brasil',1, 1, 1, 1, 0, 0, 0, 2),
    ('Banrisul',       1, 0, 1, 0, 0, 0, 0, 3),
    ('Bradesco',       1, 1, 1, 0, 1, 1, 0, 4),
    ('Itaú',           1, 1, 1, 0, 0, 0, 0, 5),
    ('Santander',      1, 1, 1, 1, 0, 0, 1, 6),
    ('Sicredi',        1, 1, 1, 0, 0, 0, 0, 7),
    ('Sicoob',         1, 1, 1, 0, 0, 0, 0, 8),
]

# banco_nome -> [(codigo, descricao, ordem), ...]
HUB_INSTRUCOES_INICIAIS = {
    'Banco do Brasil': [
        ('02','Baixa de Boleto',1),('04','Concessão de Abatimento',2),
        ('06','Alteração de Vencimento',3),('09','Protestar',4),
        ('10','Sustar o Protesto',5),('11','Dispensar Juros',6),
        ('19','Dispensar Multa',7),('24','Cancelar o Protesto',8),
        ('25','Alterar os Dias de Protesto',9),
    ],
    'Bradesco': [
        ('02','Baixa de Boleto',1),('04','Concessão de Abatimento',2),
        ('05','Cancelar o Abatimento',3),('06','Alteração de Vencimento',4),
        ('09','Protestar',5),('11','Dispensar Juros',6),
        ('19','Dispensar Multa',7),('24','Cancelar o Protesto',8),
    ],
    'Itaú': [
        ('02','Baixa de Boleto',1),('04','Concessão de Abatimento',2),
        ('05','Cancelar o Abatimento',3),('06','Alteração de Vencimento',4),
        ('09','Protestar',5),('11','Dispensar Juros',6),
        ('19','Dispensar Multa',7),('24','Cancelar o Protesto',8),
    ],
    'Santander': [
        ('02','Baixa de Boleto',1),('04','Concessão de Abatimento',2),
        ('05','Cancelar o Abatimento',3),('06','Alteração de Vencimento',4),
        ('09','Protestar',5),('11','Dispensar Juros',6),
        ('19','Dispensar Multa',7),('24','Cancelar o Protesto',8),
        ('25','Alterar os Dias de Protesto',9),
    ],
    'Sicredi': [
        ('02','Baixa de Boleto',1),('04','Concessão de Abatimento',2),
        ('05','Cancelar o Abatimento',3),('06','Alteração de Vencimento',4),
        ('09','Protestar',5),('10','Sustar o Protesto',6),
        ('13','Alterar Juros Mora',7),('11','Dispensar Juros',8),
        ('24','Cancelar o Protesto',9),
    ],
    'Sicoob': [
        ('02','Baixa de Boleto',1),('04','Concessão de Abatimento',2),
        ('06','Alteração de Vencimento',3),('09','Protestar',4),
        ('10','Sustar o Protesto',5),('11','Dispensar Juros',6),
        ('19','Dispensar Multa',7),('24','Cancelar o Protesto',8),
    ],
}

# ── Telas do sistema ─────────────────────────────────────

TELAS_SISTEMA = [
    ('pendente',               'Pendente'),
    ('homologados_cobranca',   'Homologados Cobrança'),
    ('homologados_pagamentos', 'Homologados Pagamentos'),
    ('homologados_extrato',    'Homologados Extrato Cartão'),
    ('cancelados',             'Cancelados'),
    ('melhorias',              'Melhorias'),
    ('hub',                    'Hub Bancário'),
    ('sispbol',                'SispBol'),
    ('api_pagamentos',         'API Pagamentos'),
    ('ajuda',                  'Ajuda'),
    ('importacao',             'Importação'),
    ('config',                 'Configurações'),
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
        CREATE TABLE IF NOT EXISTS setores_lista (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT    UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS melhorias (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo          TEXT    NOT NULL,
            descricao       TEXT    DEFAULT '',
            estagio         TEXT    DEFAULT 'em_analise',
            prioridade      TEXT    DEFAULT 'media',
            programador     TEXT    DEFAULT '',
            solicitante     TEXT    DEFAULT '',
            dt_conclusao    TEXT    DEFAULT '',
            motivo_rejeicao TEXT    DEFAULT '',
            criado_por      TEXT    DEFAULT '',
            criado_em       TEXT    DEFAULT (datetime('now','localtime')),
            atualizado_em   TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS hub_bancos (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            nome               TEXT    UNIQUE NOT NULL,
            cobranca_envio     INTEGER DEFAULT 0,
            cobranca_instrucao INTEGER DEFAULT 0,
            cobranca_retorno   INTEGER DEFAULT 0,
            pagamento_boleto   INTEGER DEFAULT 0,
            pagamento_pix      INTEGER DEFAULT 0,
            extrato_consulta   INTEGER DEFAULT 0,
            dda_consulta       INTEGER DEFAULT 0,
            ordem              INTEGER DEFAULT 99
        );
        CREATE TABLE IF NOT EXISTS hub_instrucoes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            banco_id  INTEGER NOT NULL,
            codigo    TEXT    NOT NULL,
            descricao TEXT    NOT NULL,
            ordem     INTEGER DEFAULT 99,
            FOREIGN KEY (banco_id) REFERENCES hub_bancos(id)
        );
        CREATE TABLE IF NOT EXISTS permissoes_telas (
            usuario_id INTEGER NOT NULL,
            tela       TEXT    NOT NULL,
            PRIMARY KEY (usuario_id, tela)
        );
        CREATE TABLE IF NOT EXISTS ajuda_topicos (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT    NOT NULL,
            ordem INTEGER DEFAULT 99
        );
        CREATE TABLE IF NOT EXISTS ajuda_posts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            topico_id     INTEGER NOT NULL,
            titulo        TEXT    NOT NULL,
            descricao     TEXT    DEFAULT '',
            conteudo      TEXT    DEFAULT '',
            ordem         INTEGER DEFAULT 99,
            criado_por    TEXT    DEFAULT '',
            criado_em     TEXT    DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (topico_id) REFERENCES ajuda_topicos(id)
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

    for s in SETORES_INICIAIS:
        conn.execute("INSERT OR IGNORE INTO setores_lista (texto) VALUES (?)", (s,))

    # Hub bancário — seed apenas se vazio
    if conn.execute("SELECT COUNT(*) FROM hub_bancos").fetchone()[0] == 0:
        for b in HUB_BANCOS_INICIAIS:
            conn.execute(
                "INSERT INTO hub_bancos (nome,cobranca_envio,cobranca_instrucao,cobranca_retorno,"
                "pagamento_boleto,pagamento_pix,extrato_consulta,dda_consulta,ordem) VALUES (?,?,?,?,?,?,?,?,?)", b
            )
        for nome_banco, instrucoes in HUB_INSTRUCOES_INICIAIS.items():
            bid = conn.execute("SELECT id FROM hub_bancos WHERE nome=?", (nome_banco,)).fetchone()
            if bid:
                for cod, desc, ord_ in instrucoes:
                    conn.execute(
                        "INSERT INTO hub_instrucoes (banco_id,codigo,descricao,ordem) VALUES (?,?,?,?)",
                        (bid[0], cod, desc, ord_)
                    )

    conn.commit()

    # Garantir existência e nível do usuário master
    conn.execute("""
        INSERT OR IGNORE INTO usuarios (usuario, senha, nome, nivel, mudar_senha)
        VALUES ('bruno', 'bruno123', 'Bruno', 'master', 0)
    """)
    conn.execute("UPDATE usuarios SET nivel='master' WHERE usuario='bruno'")
    conn.commit()

    # Migrações para bancos já existentes
    for ddl in [
        "ALTER TABLE servicos_lista ADD COLUMN destino_homologado TEXT DEFAULT ''",
        "ALTER TABLE usuarios ADD COLUMN mudar_senha INTEGER DEFAULT 0",
        "ALTER TABLE usuarios ADD COLUMN tema TEXT DEFAULT 'light'",
        "ALTER TABLE usuarios ADD COLUMN setor TEXT DEFAULT ''",
        "ALTER TABLE usuarios ADD COLUMN cor  TEXT DEFAULT ''",
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


def buscar_usuario_por_id(user_id):
    conn = conectar()
    row = conn.execute("SELECT * FROM usuarios WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


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


def listar_programadores():
    """Usuários com setor de programação (UPPER() não funciona com acentos no SQLite)."""
    conn = conectar()
    rows = conn.execute(
        "SELECT nome FROM usuarios WHERE setor IN ('PROGRAMAÇÃO','GESTOR PROGRAMAÇÃO') ORDER BY nome"
    ).fetchall()
    conn.close()
    return [r['nome'] for r in rows]


def adicionar_usuario(dados):
    try:
        conn = conectar()
        conn.execute(
            "INSERT INTO usuarios (usuario,senha,nome,nivel,tecnico_vinculado,setor,cor,mudar_senha) VALUES (?,?,?,?,?,?,?,1)",
            (dados['usuario'].strip().lower(), dados['senha'], dados['nome'].strip(),
             dados['nivel'], dados.get('tecnico_vinculado') or None,
             dados.get('setor') or '', dados.get('cor') or '')
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def atualizar_usuario(id_usuario, campos):
    conn = conectar()
    cor = campos.get('cor') or ''
    if campos.get('senha'):
        conn.execute(
            "UPDATE usuarios SET nome=?,nivel=?,tecnico_vinculado=?,senha=?,setor=?,cor=? WHERE id=?",
            (campos.get('nome'), campos.get('nivel'), campos.get('tecnico_vinculado') or None,
             campos['senha'], campos.get('setor') or '', cor, id_usuario)
        )
    else:
        conn.execute(
            "UPDATE usuarios SET nome=?,nivel=?,tecnico_vinculado=?,setor=?,cor=? WHERE id=?",
            (campos.get('nome'), campos.get('nivel'), campos.get('tecnico_vinculado') or None,
             campos.get('setor') or '', cor, id_usuario)
        )
    conn.commit()
    conn.close()


def cores_por_tecnico() -> dict:
    """Retorna {tecnico_vinculado: cor} baseado nos usuários cadastrados."""
    conn = conectar()
    rows = conn.execute(
        "SELECT tecnico_vinculado, cor FROM usuarios WHERE tecnico_vinculado IS NOT NULL AND tecnico_vinculado != ''"
    ).fetchall()
    conn.close()
    return {r['tecnico_vinculado']: (r['cor'] or '') for r in rows}


def resetar_senha_usuario(id_usuario):
    conn = conectar()
    conn.execute("UPDATE usuarios SET senha=?,mudar_senha=1 WHERE id=?", ('123456', id_usuario))
    conn.commit()
    conn.close()


def limpar_mudar_senha(id_usuario):
    conn = conectar()
    conn.execute("UPDATE usuarios SET mudar_senha=0 WHERE id=?", (id_usuario,))
    conn.commit()
    conn.close()


def atualizar_tema(id_usuario, tema):
    conn = conectar()
    conn.execute("UPDATE usuarios SET tema=? WHERE id=?", (tema, id_usuario))
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

# ── Setores ───────────────────────────────────────────────

def listar_setores():
    conn = conectar()
    rows = conn.execute("SELECT texto FROM setores_lista ORDER BY id").fetchall()
    conn.close()
    return [r['texto'] for r in rows]


def adicionar_setor(texto):
    try:
        conn = conectar()
        conn.execute("INSERT INTO setores_lista (texto) VALUES (?)", (texto.strip().upper(),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def remover_setor(texto):
    conn = conectar()
    conn.execute("DELETE FROM setores_lista WHERE texto=?", (texto,))
    conn.commit()
    conn.close()


# ── Melhorias ─────────────────────────────────────────────

def listar_melhorias():
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM melhorias ORDER BY criado_em DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_melhoria(dados: dict) -> int:
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    cur = conn.execute(
        """INSERT INTO melhorias (titulo, descricao, prioridade, programador, solicitante, criado_por, criado_em, atualizado_em)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            dados.get('titulo', ''),
            dados.get('descricao', ''),
            dados.get('prioridade', 'media'),
            dados.get('programador', ''),
            dados.get('solicitante', ''),
            dados.get('criado_por', ''),
            agora, agora,
        )
    )
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar_melhoria(id_melhoria: int, dados: dict):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        """UPDATE melhorias
           SET titulo=?, descricao=?, prioridade=?, programador=?, solicitante=?, atualizado_em=?
           WHERE id=?""",
        (
            dados.get('titulo', ''),
            dados.get('descricao', ''),
            dados.get('prioridade', 'media'),
            dados.get('programador', ''),
            dados.get('solicitante', ''),
            agora, id_melhoria,
        )
    )
    conn.commit()
    conn.close()


def mover_estagio_melhoria(id_melhoria: int, novo_estagio: str, motivo: str = ''):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    dt_conclusao = agora if novo_estagio in ('concluida', 'rejeitada') else ''
    conn = conectar()
    conn.execute(
        """UPDATE melhorias
           SET estagio=?, motivo_rejeicao=?, dt_conclusao=?, atualizado_em=?
           WHERE id=?""",
        (novo_estagio, motivo, dt_conclusao, agora, id_melhoria)
    )
    conn.commit()
    conn.close()


def remover_melhoria(id_melhoria: int):
    conn = conectar()
    conn.execute("DELETE FROM melhorias WHERE id=?", (id_melhoria,))
    conn.commit()
    conn.close()


def buscar_melhoria(id_melhoria: int):
    conn = conectar()
    row = conn.execute("SELECT * FROM melhorias WHERE id=?", (id_melhoria,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Hub Bancário ─────────────────────────────────────────

def hub_listar_bancos():
    conn = conectar()
    bancos = conn.execute("SELECT * FROM hub_bancos ORDER BY ordem, nome").fetchall()
    result = []
    for b in bancos:
        b = dict(b)
        b['instrucoes'] = [dict(r) for r in conn.execute(
            "SELECT * FROM hub_instrucoes WHERE banco_id=? ORDER BY ordem", (b['id'],)
        ).fetchall()]
        result.append(b)
    conn.close()
    return result


def hub_adicionar_banco(dados: dict) -> int:
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO hub_bancos (nome,cobranca_envio,cobranca_instrucao,cobranca_retorno,"
        "pagamento_boleto,pagamento_pix,extrato_consulta,dda_consulta,ordem) VALUES (?,?,?,?,?,?,?,?,?)",
        (dados['nome'], int(dados.get('cobranca_envio',0)), int(dados.get('cobranca_instrucao',0)),
         int(dados.get('cobranca_retorno',0)), int(dados.get('pagamento_boleto',0)),
         int(dados.get('pagamento_pix',0)), int(dados.get('extrato_consulta',0)),
         int(dados.get('dda_consulta',0)), int(dados.get('ordem', 99)))
    )
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def hub_atualizar_banco(banco_id: int, dados: dict):
    conn = conectar()
    conn.execute(
        "UPDATE hub_bancos SET nome=?,cobranca_envio=?,cobranca_instrucao=?,cobranca_retorno=?,"
        "pagamento_boleto=?,pagamento_pix=?,extrato_consulta=?,dda_consulta=?,ordem=? WHERE id=?",
        (dados['nome'], int(dados.get('cobranca_envio',0)), int(dados.get('cobranca_instrucao',0)),
         int(dados.get('cobranca_retorno',0)), int(dados.get('pagamento_boleto',0)),
         int(dados.get('pagamento_pix',0)), int(dados.get('extrato_consulta',0)),
         int(dados.get('dda_consulta',0)), int(dados.get('ordem', 99)), banco_id)
    )
    conn.commit()
    conn.close()


def hub_remover_banco(banco_id: int):
    conn = conectar()
    conn.execute("DELETE FROM hub_instrucoes WHERE banco_id=?", (banco_id,))
    conn.execute("DELETE FROM hub_bancos WHERE id=?", (banco_id,))
    conn.commit()
    conn.close()


def hub_listar_instrucoes(banco_id: int):
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM hub_instrucoes WHERE banco_id=? ORDER BY ordem", (banco_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def hub_adicionar_instrucao(banco_id: int, codigo: str, descricao: str, ordem: int = 99):
    conn = conectar()
    conn.execute(
        "INSERT INTO hub_instrucoes (banco_id,codigo,descricao,ordem) VALUES (?,?,?,?)",
        (banco_id, codigo, descricao, ordem)
    )
    conn.commit()
    conn.close()


def hub_atualizar_instrucao(instrucao_id: int, codigo: str, descricao: str, ordem: int = 99):
    conn = conectar()
    conn.execute(
        "UPDATE hub_instrucoes SET codigo=?,descricao=?,ordem=? WHERE id=?",
        (codigo, descricao, ordem, instrucao_id)
    )
    conn.commit()
    conn.close()


def hub_remover_instrucao(instrucao_id: int):
    conn = conectar()
    conn.execute("DELETE FROM hub_instrucoes WHERE id=?", (instrucao_id,))
    conn.commit()
    conn.close()


# ── Controle de acesso por tela ───────────────────────────

def listar_usuarios_permissoes():
    """Retorna todos os usuários não-master com suas telas permitidas."""
    conn = conectar()
    usuarios = conn.execute(
        "SELECT id, usuario, nome, nivel, setor FROM usuarios WHERE nivel != 'master' ORDER BY nome"
    ).fetchall()
    rows = conn.execute("SELECT usuario_id, tela FROM permissoes_telas").fetchall()
    conn.close()
    perms = {}
    for r in rows:
        perms.setdefault(r['usuario_id'], set()).add(r['tela'])
    return [{'id': u['id'], 'usuario': u['usuario'], 'nome': u['nome'],
             'nivel': u['nivel'], 'setor': u['setor'] or '',
             'telas': perms.get(u['id'], set())} for u in usuarios]


def listar_telas_usuario(usuario_id: int) -> list:
    conn = conectar()
    rows = conn.execute("SELECT tela FROM permissoes_telas WHERE usuario_id=?", (usuario_id,)).fetchall()
    conn.close()
    return [r['tela'] for r in rows]


def toggle_permissao(usuario_id: int, tela: str, permitido: bool):
    conn = conectar()
    if permitido:
        conn.execute("INSERT OR IGNORE INTO permissoes_telas (usuario_id, tela) VALUES (?,?)", (usuario_id, tela))
    else:
        conn.execute("DELETE FROM permissoes_telas WHERE usuario_id=? AND tela=?", (usuario_id, tela))
    conn.commit()
    conn.close()


def salvar_permissoes_usuario(usuario_id: int, telas: list):
    """Substitui todas as permissões de um usuário."""
    conn = conectar()
    conn.execute("DELETE FROM permissoes_telas WHERE usuario_id=?", (usuario_id,))
    for tela in telas:
        conn.execute("INSERT INTO permissoes_telas (usuario_id, tela) VALUES (?,?)", (usuario_id, tela))
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


def atualizar_status_pendente(id_registro, novo_status):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    hoje  = datetime.now().strftime('%d/%m/%Y')
    conn  = conectar()
    conn.execute(
        "UPDATE pendentes SET status=?, dt_status=?, atualizado_em=? WHERE id=?",
        (novo_status, hoje, agora, id_registro)
    )
    conn.commit()
    conn.close()


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


def assumir_homologado(id_registro, tipo, nome_tecnico):
    tabela = f'homologados_{tipo}'
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        f"UPDATE {tabela} SET tecnico=?, atualizado_em=? WHERE id=? AND (tecnico IS NULL OR UPPER(TRIM(tecnico))='' OR UPPER(TRIM(tecnico))='SEM TEC.')",
        (nome_tecnico, agora, id_registro)
    )
    changed = conn.total_changes
    conn.commit()
    conn.close()
    return changed > 0


def assumir_pendente(id_registro, nome_tecnico):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE pendentes SET tecnico=?, atualizado_em=? WHERE id=? AND (tecnico IS NULL OR UPPER(TRIM(tecnico))='' OR UPPER(TRIM(tecnico))='SEM TEC.')",
        (nome_tecnico, agora, id_registro)
    )
    changed = conn.total_changes
    conn.commit()
    conn.close()
    return changed > 0


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

# ── Ajuda (manuais) ───────────────────────────────────────

def listar_ajuda_topicos():
    conn = conectar()
    rows = conn.execute("SELECT * FROM ajuda_topicos ORDER BY ordem, nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_ajuda_completo():
    """Tópicos com seus posts aninhados, na ordem de exibição."""
    conn = conectar()
    topicos = conn.execute("SELECT * FROM ajuda_topicos ORDER BY ordem, nome").fetchall()
    result = []
    for t in topicos:
        t = dict(t)
        t['posts'] = [dict(r) for r in conn.execute(
            "SELECT * FROM ajuda_posts WHERE topico_id=? ORDER BY ordem, titulo", (t['id'],)
        ).fetchall()]
        result.append(t)
    conn.close()
    return result


def adicionar_ajuda_topico(nome, ordem=99):
    conn = conectar()
    cur = conn.execute("INSERT INTO ajuda_topicos (nome,ordem) VALUES (?,?)", (nome.strip(), int(ordem or 99)))
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar_ajuda_topico(id_topico, nome, ordem=99):
    conn = conectar()
    conn.execute("UPDATE ajuda_topicos SET nome=?,ordem=? WHERE id=?", (nome.strip(), int(ordem or 99), id_topico))
    conn.commit()
    conn.close()


def remover_ajuda_topico(id_topico):
    conn = conectar()
    conn.execute("DELETE FROM ajuda_posts WHERE topico_id=?", (id_topico,))
    conn.execute("DELETE FROM ajuda_topicos WHERE id=?", (id_topico,))
    conn.commit()
    conn.close()


def buscar_ajuda_post(id_post):
    conn = conectar()
    row = conn.execute("SELECT * FROM ajuda_posts WHERE id=?", (id_post,)).fetchone()
    conn.close()
    return dict(row) if row else None


def adicionar_ajuda_post(dados, criado_por=''):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    cur = conn.execute(
        """INSERT INTO ajuda_posts (topico_id,titulo,descricao,conteudo,ordem,criado_por,criado_em,atualizado_em)
           VALUES (?,?,?,?,?,?,?,?)""",
        (int(dados['topico_id']), dados.get('titulo','').strip(), dados.get('descricao','').strip(),
         dados.get('conteudo',''), int(dados.get('ordem', 99) or 99), criado_por, agora, agora)
    )
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar_ajuda_post(id_post, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        """UPDATE ajuda_posts SET topico_id=?,titulo=?,descricao=?,conteudo=?,ordem=?,atualizado_em=?
           WHERE id=?""",
        (int(dados['topico_id']), dados.get('titulo','').strip(), dados.get('descricao','').strip(),
         dados.get('conteudo',''), int(dados.get('ordem', 99) or 99), agora, id_post)
    )
    conn.commit()
    conn.close()


def remover_ajuda_post(id_post):
    conn = conectar()
    conn.execute("DELETE FROM ajuda_posts WHERE id=?", (id_post,))
    conn.commit()
    conn.close()
