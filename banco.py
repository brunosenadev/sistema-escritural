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

STATUS_ESCRITURAL_INICIAIS = [
    'AGUARDANDO', 'APROVADO', 'REPASSADO', 'PENDENTE',
    'VERIFICANDO COM COMERCIAL', 'CANCELADO', 'RECUSADO',
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
# Agrupadas espelhando as seções da sidebar (Abas / Sistema / Referência),
# para a tela de Controle de Acesso exibir os toggles na mesma organização.

TELAS_AGRUPADAS = [
    ('Abas', [
        ('pendente',               'Pendente'),
        ('homologados_cobranca',   'Homologados Cobrança'),
        ('homologados_pagamentos', 'Homologados Pagamentos'),
        ('homologados_extrato',         'Homologados Extrato Cartão'),
        ('homologados_ext_bancario',    'Homologados Extrato Bancário'),
        ('cancelados',             'Cancelados'),
        ('sispbol',                'SispBol'),
        ('escritural',             'Novos Escriturais'),
    ]),
    ('Sistema', [
        ('melhorias',                          'Melhorias'),
        ('config',                             'Configurações'),
        ('email_modelos',                      'Modelos de E-mail'),
        ('importar_homologacoes_pendentes',    'Importar Homologações Pendentes'),
        ('importar_novas_homologacoes',        'Importar Novas Homologações'),
        ('logs',                               'Logs do Sistema'),
    ]),
    ('Referência', [
        ('hub',                    'Hub Bancário'),
        ('api_pagamentos',         'API Pagamentos'),
        ('ajuda',                  'Ajuda'),
        ('ajuda_gerenciar',        'Gerenciar Ajuda'),
    ]),
]

TELAS_SISTEMA = [tela for _, telas in TELAS_AGRUPADAS for tela in telas]

# ── Conexão ───────────────────────────────────────────────

def conectar():
    conn = sqlite3.connect(CAMINHO_BANCO, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
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
        CREATE TABLE IF NOT EXISTS status_escritural_lista (
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
        CREATE TABLE IF NOT EXISTS collections (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            banco         TEXT    NOT NULL DEFAULT '',
            titulo        TEXT    NOT NULL DEFAULT '',
            descricao     TEXT    DEFAULT '',
            conteudo      TEXT    DEFAULT '',
            ordem         INTEGER DEFAULT 99,
            criado_por    TEXT    DEFAULT '',
            criado_em     TEXT    DEFAULT (datetime('now','localtime')),
            atualizado_em TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS email_modelos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      TEXT    NOT NULL,
            servico   TEXT    NOT NULL DEFAULT '',
            assunto   TEXT    DEFAULT '',
            corpo     TEXT    DEFAULT '',
            ativo     INTEGER DEFAULT 1,
            criado_em TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora   TEXT    NOT NULL,
            usuario     TEXT    DEFAULT '',
            usuario_id  INTEGER,
            nivel       TEXT    DEFAULT '',
            tela        TEXT    DEFAULT '',
            acao        TEXT    DEFAULT '',
            descricao   TEXT    DEFAULT '',
            ip          TEXT    DEFAULT ''
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
        CREATE TABLE IF NOT EXISTS homologados_ext_bancario (
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
        CREATE TABLE IF NOT EXISTS email_config_usuario (
            usuario_id  INTEGER PRIMARY KEY,
            email       TEXT    DEFAULT '',
            smtp_host   TEXT    DEFAULT '',
            smtp_port   INTEGER DEFAULT 587,
            smtp_ssl    INTEGER DEFAULT 0,
            imap_host   TEXT    DEFAULT '',
            imap_port   INTEGER DEFAULT 993,
            imap_ssl    INTEGER DEFAULT 1,
            senha       TEXT    DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS email_thread_escritural (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            escritural_id INTEGER NOT NULL,
            message_id    TEXT    DEFAULT '',
            in_reply_to   TEXT    DEFAULT '',
            assunto       TEXT    DEFAULT '',
            remetente     TEXT    DEFAULT '',
            destinatario  TEXT    DEFAULT '',
            corpo_texto   TEXT    DEFAULT '',
            data_hora     TEXT    DEFAULT (datetime('now','localtime')),
            direcao       TEXT    DEFAULT 'enviado',
            lido          INTEGER DEFAULT 1,
            enviado_por   TEXT    DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS escritural (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            status                 TEXT,
            data_solicitacao       TEXT,
            empresa                TEXT,
            cnpj                   TEXT,
            responsavel             TEXT,
            fone_responsavel        TEXT,
            email_responsavel       TEXT,
            banco                  TEXT,
            conta_corrente          TEXT,
            agencia                TEXT,
            convenio               TEXT,
            servico                TEXT,
            carteira               TEXT,
            desc_carteira           TEXT,
            variacao               TEXT,
            juros                  TEXT,
            multa                  TEXT,
            protesto               TEXT,
            emissor                TEXT,
            ultima_numeracao        TEXT,
            cnab                   TEXT,
            solicitante            TEXT,
            nome_solicitante        TEXT,
            obs_emissao             TEXT,
            solicitante_pagto       TEXT,
            nome_solicitante_pagto  TEXT,
            modalidades            TEXT,
            obs_pagto              TEXT,
            tecnico                 TEXT,
            dt_status               TEXT,
            sequencial_nosso_numero TEXT,
            quantos_dias            TEXT,
            anexos                  TEXT,
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

    for s in STATUS_ESCRITURAL_INICIAIS:
        conn.execute("INSERT OR IGNORE INTO status_escritural_lista (texto) VALUES (?)", (s,))

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
        "ALTER TABLE escritural ADD COLUMN tecnico TEXT",
        "ALTER TABLE escritural ADD COLUMN dt_status TEXT",
        "ALTER TABLE escritural ADD COLUMN sequencial_nosso_numero TEXT",
        "ALTER TABLE escritural ADD COLUMN quantos_dias TEXT",
        "ALTER TABLE escritural ADD COLUMN anexos TEXT",
        "ALTER TABLE email_thread_escritural ADD COLUMN enviado_por TEXT DEFAULT ''",
        "ALTER TABLE email_thread_escritural ADD COLUMN corpo_html TEXT DEFAULT ''",
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

# ── Status (Novos Escriturais) ───────────────────────────────

def listar_status_escritural():
    conn = conectar()
    rows = conn.execute("SELECT texto FROM status_escritural_lista ORDER BY id").fetchall()
    conn.close()
    return [r['texto'] for r in rows]


def adicionar_status_escritural(texto):
    try:
        conn = conectar()
        conn.execute("INSERT INTO status_escritural_lista (texto) VALUES (?)", (texto.strip().upper(),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def remover_status_escritural(texto):
    conn = conectar()
    conn.execute("DELETE FROM status_escritural_lista WHERE texto=?", (texto,))
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
            (SELECT COUNT(*) FROM homologados_extrato)         AS extrato,
            (SELECT COUNT(*) FROM homologados_ext_bancario)    AS ext_bancario
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


# ── Escritural (planilha de uso restrito, acesso liberado via /acesso) ───

CAMPOS_ESCRITURAL = [
    'status', 'data_solicitacao', 'empresa', 'cnpj', 'responsavel',
    'fone_responsavel', 'email_responsavel', 'banco', 'conta_corrente',
    'agencia', 'convenio', 'servico', 'carteira', 'desc_carteira',
    'variacao', 'juros', 'multa', 'protesto', 'emissor', 'ultima_numeracao',
    'cnab', 'solicitante', 'nome_solicitante', 'obs_emissao',
    'solicitante_pagto', 'nome_solicitante_pagto', 'modalidades', 'obs_pagto',
    'tecnico', 'dt_status', 'sequencial_nosso_numero', 'quantos_dias', 'anexos',
]

LABELS_ESCRITURAL = {
    'status': 'Status', 'data_solicitacao': 'Data Solic.', 'empresa': 'Empresa', 'cnpj': 'CNPJ',
    'responsavel': 'Responsável', 'fone_responsavel': 'Fone Resp.', 'email_responsavel': 'E-mail Resp.',
    'banco': 'Banco', 'conta_corrente': 'Conta Corrente', 'agencia': 'Agência', 'convenio': 'Convênio',
    'servico': 'Serviço', 'carteira': 'Carteira', 'desc_carteira': 'Desc. Carteira', 'variacao': 'Variação',
    'juros': 'Juros', 'multa': 'Multa', 'protesto': 'Protesto', 'emissor': 'Emissor',
    'ultima_numeracao': 'Última Numeração', 'cnab': 'CNAB', 'solicitante': 'Solicitante',
    'nome_solicitante': 'Nome Solicitante', 'obs_emissao': 'Obs. Emissão',
    'solicitante_pagto': 'Solicitante Pagto.', 'nome_solicitante_pagto': 'Nome Sol. Pagto.',
    'modalidades': 'Modalidades', 'obs_pagto': 'Obs. Pagto.', 'tecnico': 'Técnico',
    'dt_status': 'Dt. Status', 'sequencial_nosso_numero': 'Seq. Nosso Número', 'quantos_dias': 'Quantos Dias',
    'anexos': 'Anexos',
}


def _chave_ordenacao_data_escritural(reg):
    """Converte 'dd/mm/aaaa[ HH:MM:SS]' em datetime para ordenar; registros sem
    data (ou ilegíveis) recebem a menor data possível, então caem para o final
    quando ordenado decrescente (mais recentes primeiro)."""
    valor = (reg.get('data_solicitacao') or '').strip()
    for fmt in ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y'):
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    return datetime.min


def listar_escritural():
    conn = conectar()
    rows = conn.execute("SELECT * FROM escritural").fetchall()
    conn.close()
    registros = [dict(r) for r in rows]
    registros.sort(key=_chave_ordenacao_data_escritural, reverse=True)
    return registros


def adicionar_escritural(dados, criado_por=''):
    conn = conectar()
    colunas      = ','.join(CAMPOS_ESCRITURAL)
    placeholders = ','.join('?' * len(CAMPOS_ESCRITURAL))
    cur = conn.execute(
        f"INSERT INTO escritural ({colunas},criado_por) VALUES ({placeholders},?)",
        tuple(dados.get(c, '') for c in CAMPOS_ESCRITURAL) + (criado_por,)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_escritural(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn  = conectar()
    sets  = ','.join(f"{c}=?" for c in CAMPOS_ESCRITURAL)
    conn.execute(
        f"UPDATE escritural SET {sets},atualizado_em=? WHERE id=?",
        tuple(dados.get(c, '') for c in CAMPOS_ESCRITURAL) + (agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def atualizar_status_escritural(id_registro, novo_status):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    hoje  = datetime.now().strftime('%d/%m/%Y')
    conn  = conectar()
    conn.execute(
        "UPDATE escritural SET status=?, dt_status=?, atualizado_em=? WHERE id=?",
        (novo_status, hoje, agora, id_registro)
    )
    conn.commit()
    conn.close()


def deletar_escritural(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM escritural WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


def importar_escritural(lista_registros, criado_por='importação planilha'):
    """Importa registros novos, pulando linhas que já existem (mesma empresa+cnpj+data_solicitacao)
    para permitir reenviar a mesma planilha histórica sem duplicar registros antigos."""
    conn = conectar()
    existentes = {
        (r['empresa'] or '', r['cnpj'] or '', r['data_solicitacao'] or '')
        for r in conn.execute("SELECT empresa,cnpj,data_solicitacao FROM escritural").fetchall()
    }
    colunas      = ','.join(CAMPOS_ESCRITURAL)
    placeholders = ','.join('?' * len(CAMPOS_ESCRITURAL))
    novos = 0
    for reg in lista_registros:
        chave = (reg.get('empresa', ''), reg.get('cnpj', ''), reg.get('data_solicitacao', ''))
        if chave in existentes:
            continue
        existentes.add(chave)
        conn.execute(
            f"INSERT INTO escritural ({colunas},criado_por) VALUES ({placeholders},?)",
            tuple(reg.get(c, '') for c in CAMPOS_ESCRITURAL) + (criado_por,)
        )
        novos += 1
    conn.commit()
    conn.close()
    return novos


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
    'cobranca':     'homologados_cobranca',
    'pagamentos':   'homologados_pagamentos',
    'extrato':      'homologados_extrato',
    'ext_bancario': 'homologados_ext_bancario',
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

# ── Homologados Extrato Bancário ──────────────────────────

def listar_homologados_ext_bancario():
    conn = conectar()
    rows = conn.execute("SELECT * FROM homologados_ext_bancario ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_homologado_ext_bancario(dados, criado_por=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO homologados_ext_bancario (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), criado_por)
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def atualizar_homologado_ext_bancario(id_registro, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        "UPDATE homologados_ext_bancario SET tecnico=?,empresa=?,servico=?,banco=?,dt_solicita=?,dt_status=?,status=?,obs=?,atualizado_em=? WHERE id=?",
        (dados.get('tecnico',''), dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status','HOMOLOGADO'), dados.get('obs',''), agora, id_registro)
    )
    conn.commit()
    conn.close()
    return True


def deletar_homologado_ext_bancario(id_registro):
    conn = conectar()
    conn.execute("DELETE FROM homologados_ext_bancario WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()
    return True


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


# ── Collections ──────────────────────────────────────────

def listar_collections():
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM collections ORDER BY banco, ordem, titulo"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_collections_por_banco():
    """Retorna dict {banco: [collections]} ordenado por banco."""
    from collections import defaultdict
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM collections ORDER BY banco, ordem, titulo"
    ).fetchall()
    conn.close()
    agrupado = defaultdict(list)
    for r in rows:
        agrupado[r['banco'] or 'Geral'].append(dict(r))
    return dict(agrupado)


def buscar_collection(id_col):
    conn = conectar()
    row = conn.execute("SELECT * FROM collections WHERE id=?", (id_col,)).fetchone()
    conn.close()
    return dict(row) if row else None


def adicionar_collection(dados, criado_por=''):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    cur = conn.execute(
        """INSERT INTO collections (banco,titulo,descricao,conteudo,ordem,criado_por,criado_em,atualizado_em)
           VALUES (?,?,?,?,?,?,?,?)""",
        (dados.get('banco','').strip(), dados.get('titulo','').strip(),
         dados.get('descricao','').strip(), dados.get('conteudo',''),
         int(dados.get('ordem', 99) or 99), criado_por, agora, agora)
    )
    novo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar_collection(id_col, dados):
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    conn.execute(
        """UPDATE collections SET banco=?,titulo=?,descricao=?,conteudo=?,ordem=?,atualizado_em=?
           WHERE id=?""",
        (dados.get('banco','').strip(), dados.get('titulo','').strip(),
         dados.get('descricao','').strip(), dados.get('conteudo',''),
         int(dados.get('ordem', 99) or 99), agora, id_col)
    )
    conn.commit()
    conn.close()


def remover_collection(id_col):
    conn = conectar()
    conn.execute("DELETE FROM collections WHERE id=?", (id_col,))
    conn.commit()
    conn.close()


# ── E-mail: config por usuário ────────────────────────────

def salvar_email_config(usuario_id, dados):
    conn = conectar()
    conn.execute("""
        INSERT INTO email_config_usuario
            (usuario_id, email, smtp_host, smtp_port, smtp_ssl, imap_host, imap_port, imap_ssl, senha)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(usuario_id) DO UPDATE SET
            email=excluded.email, smtp_host=excluded.smtp_host, smtp_port=excluded.smtp_port,
            smtp_ssl=excluded.smtp_ssl, imap_host=excluded.imap_host, imap_port=excluded.imap_port,
            imap_ssl=excluded.imap_ssl, senha=excluded.senha
    """, (
        usuario_id,
        dados.get('email', ''), dados.get('smtp_host', ''), int(dados.get('smtp_port', 587)),
        1 if dados.get('smtp_ssl') else 0,
        dados.get('imap_host', ''), int(dados.get('imap_port', 993)),
        1 if dados.get('imap_ssl', True) else 0,
        dados.get('senha', ''),
    ))
    conn.commit()
    conn.close()


def buscar_email_config(usuario_id):
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM email_config_usuario WHERE usuario_id=?", (usuario_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def listar_email_configs_ativos():
    """Retorna todas as configs de e-mail com host preenchido (para o IMAP polling)."""
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM email_config_usuario WHERE imap_host != '' AND email != '' AND senha != ''"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── E-mail: threads por solicitação ──────────────────────

def salvar_email_thread(escritural_id, msg):
    conn = conectar()
    try:
        cur = conn.execute("""
            INSERT INTO email_thread_escritural
                (escritural_id, message_id, in_reply_to, assunto, remetente, destinatario,
                 corpo_texto, corpo_html, data_hora, direcao, lido, enviado_por)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            escritural_id,
            msg.get('message_id', ''), msg.get('in_reply_to', ''),
            msg.get('assunto', ''), msg.get('remetente', ''), msg.get('destinatario', ''),
            msg.get('corpo_texto', ''), msg.get('corpo_html', ''),
            msg.get('data_hora', datetime.now().strftime('%d/%m/%Y %H:%M')),
            msg.get('direcao', 'enviado'),
            1 if msg.get('direcao') == 'enviado' else 0,
            msg.get('enviado_por', ''),
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def listar_thread_escritural(escritural_id):
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM email_thread_escritural WHERE escritural_id=? ORDER BY rowid ASC",
        (escritural_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def marcar_lidos_thread(escritural_id):
    conn = conectar()
    try:
        conn.execute(
            "UPDATE email_thread_escritural SET lido=1 WHERE escritural_id=? AND lido=0",
            (escritural_id,)
        )
        conn.commit()
    finally:
        conn.close()


def message_id_existe(message_id):
    """Verifica se um Message-ID já foi salvo (deduplicação do IMAP polling)."""
    if not message_id:
        return False
    conn = conectar()
    row = conn.execute(
        "SELECT id FROM email_thread_escritural WHERE message_id=?", (message_id,)
    ).fetchone()
    conn.close()
    return row is not None


def contar_nao_lidos_escritural():
    """Retorna dict {escritural_id: qtd} com não-lidos por solicitação."""
    conn = conectar()
    rows = conn.execute(
        "SELECT escritural_id, COUNT(*) as qtd FROM email_thread_escritural WHERE lido=0 GROUP BY escritural_id"
    ).fetchall()
    conn.close()
    return {r['escritural_id']: r['qtd'] for r in rows}


# ── Modelos de e-mail ─────────────────────────────────────

# Parâmetros disponíveis para interpolação nas mensagens.
# Chave = token usado na mensagem (ex: #empresa#)
# Valor = (campo_em_escritural_ou_None, descrição legível)
PARAMS_EMAIL_MODELO = [
    ('#empresa#',       ('empresa',           'Nome da empresa')),
    ('#cnpj#',          ('cnpj',              'CNPJ da empresa')),
    ('#responsavel#',   ('responsavel',       'Nome do responsável / contato')),
    ('#fone#',          ('fone_responsavel',  'Fone do responsável')),
    ('#email#',         ('email_responsavel', 'E-mail do responsável')),
    ('#banco#',         ('banco',             'Banco do registro')),
    ('#conta#',         ('conta_corrente',    'Conta corrente')),
    ('#agencia#',       ('agencia',           'Agência')),
    ('#convenio#',      ('convenio',          'Convênio')),
    ('#servico#',       ('servico',           'Serviço contratado')),
    ('#carteira#',      ('carteira',          'Carteira')),
    ('#variacao#',      ('variacao',          'Variação')),
    ('#cnab#',          ('cnab',              'CNAB')),
    ('#data_solic#',    ('data_solicitacao',  'Data de solicitação')),
    ('#status#',        ('status',            'Status atual do registro')),
    ('#tecnico#',       ('tecnico',           'Técnico responsável')),
    ('#obs#',           ('obs_emissao',       'Obs. de emissão')),
    ('#meu_nome#',      (None,               'Seu nome (usuário logado que envia o e-mail)')),
]


def listar_email_modelos():
    conn = conectar()
    rows = conn.execute("SELECT * FROM email_modelos ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_email_modelo(id_modelo):
    conn = conectar()
    row = conn.execute("SELECT * FROM email_modelos WHERE id=?", (id_modelo,)).fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_email_modelo_por_servico(servico):
    if not servico:
        return None
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM email_modelos WHERE UPPER(TRIM(servico))=UPPER(TRIM(?)) AND ativo=1 ORDER BY id LIMIT 1",
        (servico,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def adicionar_email_modelo(dados):
    conn = conectar()
    try:
        cur = conn.execute(
            "INSERT INTO email_modelos (nome, servico, assunto, corpo) VALUES (?,?,?,?)",
            (dados.get('nome', '').strip(),
             dados.get('servico', '').strip(),
             dados.get('assunto', '').strip(),
             dados.get('corpo', '').strip())
        )
        id_novo = cur.lastrowid
        conn.commit()
        return id_novo
    finally:
        conn.close()


def atualizar_email_modelo(id_modelo, dados):
    conn = conectar()
    try:
        conn.execute(
            "UPDATE email_modelos SET nome=?, servico=?, assunto=?, corpo=?, ativo=? WHERE id=?",
            (dados.get('nome', '').strip(),
             dados.get('servico', '').strip(),
             dados.get('assunto', '').strip(),
             dados.get('corpo', '').strip(),
             int(dados.get('ativo', 1)),
             id_modelo)
        )
        conn.commit()
    finally:
        conn.close()


def remover_email_modelo(id_modelo):
    conn = conectar()
    try:
        conn.execute("DELETE FROM email_modelos WHERE id=?", (id_modelo,))
        conn.commit()
    finally:
        conn.close()


def aplicar_parametros_modelo(corpo, assunto, registro, usuario_nome=''):
    """Substitui tokens #param# no corpo e assunto pelos valores do registro escritural."""
    valores = {token: (registro.get(campo) or '') for token, (campo, _) in PARAMS_EMAIL_MODELO if campo}
    valores['#meu_nome#'] = usuario_nome or ''
    for token, valor in valores.items():
        corpo   = corpo.replace(token, valor)
        assunto = assunto.replace(token, valor)
    return corpo, assunto


# ── Logs do sistema ───────────────────────────────────────

def registrar_log(usuario, tela, acao, descricao, usuario_id=None, nivel=None, ip=None):
    """Registra uma ação no log. Nunca lança exceção para não impactar o fluxo principal."""
    conn = conectar()
    try:
        conn.execute(
            "INSERT INTO logs (data_hora,usuario,usuario_id,nivel,tela,acao,descricao,ip) VALUES (?,?,?,?,?,?,?,?)",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             usuario or '', usuario_id, nivel or '', tela or '', acao or '', descricao or '', ip or '')
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def listar_logs(busca=None, usuario=None, tela=None, acao=None,
                data_ini=None, data_fim=None, pagina=1, por_pagina=100):
    conn = conectar()
    cond, params = ['1=1'], []
    if usuario:
        cond.append('LOWER(usuario) LIKE ?'); params.append(f'%{usuario.lower()}%')
    if tela:
        cond.append('tela=?'); params.append(tela)
    if acao:
        cond.append('acao=?'); params.append(acao)
    if busca:
        cond.append('(descricao LIKE ? OR usuario LIKE ?)'); params += [f'%{busca}%', f'%{busca}%']
    if data_ini:
        cond.append('data_hora >= ?'); params.append(data_ini + ' 00:00:00')
    if data_fim:
        cond.append('data_hora <= ?'); params.append(data_fim + ' 23:59:59')
    sql = ' AND '.join(cond)
    total = conn.execute(f'SELECT COUNT(*) FROM logs WHERE {sql}', params).fetchone()[0]
    offset = (pagina - 1) * por_pagina
    rows = conn.execute(
        f'SELECT * FROM logs WHERE {sql} ORDER BY id DESC LIMIT ? OFFSET ?',
        params + [por_pagina, offset]
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows], total


def buscar_empresa_log(tabela, id_registro):
    """Busca nome da empresa para usar em descrições de log antes de deletar."""
    if tabela not in {'pendentes', 'homologados_cobranca', 'homologados_pagamentos',
                      'homologados_extrato', 'homologados_ext_bancario', 'cancelados', 'escritural'}:
        return ''
    conn = conectar()
    try:
        row = conn.execute(f'SELECT empresa FROM {tabela} WHERE id=?', (id_registro,)).fetchone()
        return row['empresa'] if row else ''
    except Exception:
        return ''
    finally:
        conn.close()
