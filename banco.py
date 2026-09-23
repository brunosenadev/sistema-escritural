"""
banco.py — Camada de acesso ao banco de dados (SQLite).

Em produção (Render) define DB_PATH=/data/banco_dados.db para usar o disco persistente.
Localmente usa banco_dados.db na raiz do projeto.
"""

import os
import sqlite3
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

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

BANCOS_CADASTRO_INICIAIS = [
    # (codigo, nome, tem_api, ordem)
    ('001', 'Banco do Brasil',              1,  1),
    ('033', 'Banco Santander',              1,  2),
    ('041', 'Banrisul',                     1,  3),
    ('077', 'Banco Inter',                  0,  4),
    ('084', 'Uniprime Norte do Paraná',     0,  5),
    ('085', 'Ailos',                        1,  6),
    ('085', 'Viacredi',                     1,  7),
    ('085', 'Transpocred',                  0,  8),
    ('104', 'Caixa Econômica Federal',      0,  9),
    ('133', 'Cresol',                       0, 10),
    ('136', 'Unicred',                      0, 11),
    ('208', 'BTG Pactual',                  0, 12),
    ('218', 'BS2',                          0, 13),
    ('237', 'Banco Bradesco',               1, 14),
    ('246', 'Banco ABC',                    0, 15),
    ('260', 'Nu Pagamentos (Nubank)',        0, 16),
    ('274', 'BMP',                          0, 17),
    ('310', 'Vortx',                        0, 18),
    ('336', 'C6',                           0, 19),
    ('341', 'Banco Itaú',                   1, 20),
    ('422', 'Banco Safra',                  0, 21),
    ('461', 'Asaas',                        0, 22),
    ('469', 'Banco Original',               0, 23),
    ('637', 'Sofisa',                       0, 24),
    ('655', 'Votorantim',                   0, 25),
    ('707', 'Daycoval',                     0, 26),
    ('748', 'Sicredi',                      1, 27),
    ('756', 'Sicoob',                       1, 28),
    ('004', 'BNB',                          0, 29),
    # FIDCs e outros
    ('FIDC', 'FIDC RNX',                    0, 50),
    ('FIDC', 'FIDC OPERA',                  0, 51),
    ('FIDC', 'FIDC WALL',                   0, 52),
    ('FIDC', 'FIDC PRIME',                  0, 53),
    ('FIDC', 'FIDC CREDVALE',               0, 54),
    ('FIDC', 'FIDC BELLUNO',                0, 55),
    ('FIDC', 'FIDC',                        0, 56),
    ('---',  'Belluno',                     0, 57),
    ('---',  'Multiplike',                  0, 58),
    ('---',  'Factoring',                   0, 59),
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
        ('controle_os',            'Controle de O.S.'),
        ('sispbol',                'SispBol'),
        ('credenciais',            'Credenciais'),
        ('descriptografar',        'Descriptografar Credenciais'),
        ('conversor_certificado',  'Conversor de Certificado'),
        ('gerador_certificado_itau', 'Gerador de Certificado Itaú'),
        ('escritural',             'Novos Escriturais'),
    ]),
    ('Sistema', [
        ('notificacoes',                       'Notificações'),
        ('melhorias',                          'Melhorias'),
        ('config',                             'Configurações'),
        ('sla_dashboard',                      'Dashboard SLA'),
        ('email_modelos',                      'Modelos de E-mail'),
        ('usuarios',                           'Usuários'),
        ('importar_homologacoes_pendentes',    'Importar Homologações Pendentes'),
        ('importar_novas_homologacoes',        'Importar Novas Homologações'),
        ('logs',                               'Logs do Sistema'),
        ('editor_sql',                         'Editor SQL'),
    ]),
    ('Referência', [
        ('hub',                    'Hub Bancário'),
        ('hub_edicao',             'Hub Bancário — Edição'),
        ('api_pagamentos',         'API Pagamentos'),
        ('ajuda',                  'Ajuda'),
        ('ajuda_gerenciar',        'Gerenciar Ajuda'),
    ]),
]

TELAS_SISTEMA = [tela for _, telas in TELAS_AGRUPADAS for tela in telas]

# ── Conexão ───────────────────────────────────────────────

def _abrir_conn():
    conn = sqlite3.connect(CAMINHO_BANCO, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=DELETE')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


class _ConexaoComRetry:
    """Wrapper sobre sqlite3.Connection que reabre e repete em disk I/O error."""
    _MAX = 4

    def __init__(self):
        self._conn = _abrir_conn()

    def _reabrir(self):
        try:
            self._conn.close()
        except Exception:
            pass
        self._conn = _abrir_conn()

    def execute(self, sql, params=()):
        for i in range(self._MAX):
            try:
                return self._conn.execute(sql, params)
            except sqlite3.OperationalError as e:
                if 'disk I/O' in str(e) and i < self._MAX - 1:
                    time.sleep(0.4 * (i + 1))
                    self._reabrir()
                    continue
                raise

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()


def conectar():
    return _ConexaoComRetry()

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
        CREATE TABLE IF NOT EXISTS config_geral (
            chave TEXT PRIMARY KEY,
            valor TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS sla_config (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            servico         TEXT UNIQUE NOT NULL,
            prazo_total     INTEGER DEFAULT 30,
            aviso_dias      INTEGER DEFAULT 7,
            atrasado_dias   INTEGER DEFAULT 7,
            critico_dias    INTEGER DEFAULT 15
        );
        CREATE TABLE IF NOT EXISTS sla_avisos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            texto      TEXT NOT NULL,
            tipo       TEXT DEFAULT 'info',
            criado_por TEXT DEFAULT '',
            criado_em  TEXT DEFAULT (datetime('now','localtime')),
            expira_em  TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS sla_notif_pref (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL,
            faixa       TEXT NOT NULL,
            ativo       INTEGER DEFAULT 1,
            freq_dias   INTEGER DEFAULT 1,
            ultima_notif TEXT DEFAULT '',
            UNIQUE(usuario_id, faixa)
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
        CREATE TABLE IF NOT EXISTS melhorias_imagens (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            melhoria_id INTEGER NOT NULL,
            nome_arquivo TEXT    NOT NULL,
            criado_em   TEXT    DEFAULT (datetime('now','localtime'))
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
        CREATE TABLE IF NOT EXISTS hub_categorias (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            nome  TEXT    UNIQUE NOT NULL,
            ordem INTEGER DEFAULT 99
        );
        CREATE TABLE IF NOT EXISTS hub_servicos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            nome         TEXT    NOT NULL,
            cor_bg       TEXT    DEFAULT '#dbeafe',
            cor_texto    TEXT    DEFAULT '#1d4ed8',
            ordem        INTEGER DEFAULT 99,
            FOREIGN KEY (categoria_id) REFERENCES hub_categorias(id)
        );
        CREATE TABLE IF NOT EXISTS hub_banco_servicos (
            banco_id   INTEGER NOT NULL,
            servico_id INTEGER NOT NULL,
            PRIMARY KEY (banco_id, servico_id),
            FOREIGN KEY (banco_id)   REFERENCES hub_bancos(id),
            FOREIGN KEY (servico_id) REFERENCES hub_servicos(id)
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
        CREATE TABLE IF NOT EXISTS sessoes_ativas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            jti           TEXT    NOT NULL UNIQUE,
            usuario_id    INTEGER NOT NULL,
            nome          TEXT    DEFAULT '',
            nivel         TEXT    DEFAULT '',
            ip            TEXT    DEFAULT '',
            login_em      TEXT    NOT NULL,
            ultimo_acesso TEXT    NOT NULL
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
            senha       TEXT    DEFAULT '',
            assinatura  TEXT    DEFAULT ''
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
        CREATE TABLE IF NOT EXISTS bancos_cadastro (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo   TEXT    NOT NULL,
            nome     TEXT    NOT NULL,
            tem_api  INTEGER NOT NULL DEFAULT 0,
            ativo    INTEGER NOT NULL DEFAULT 1,
            ordem    INTEGER          DEFAULT 999
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
        CREATE TABLE IF NOT EXISTS notificacoes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo       TEXT    DEFAULT 'info',
            titulo     TEXT    NOT NULL DEFAULT '',
            mensagem   TEXT    DEFAULT '',
            lida       INTEGER DEFAULT 0,
            criado_em  TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_notif_usuario ON notificacoes(usuario_id);

        CREATE TABLE IF NOT EXISTS credenciais (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj           TEXT    NOT NULL DEFAULT '',
            nome           TEXT    NOT NULL DEFAULT '',
            tipo           TEXT    NOT NULL DEFAULT '',
            banco          TEXT    DEFAULT '',
            conta          TEXT    DEFAULT '',
            data_validade  TEXT    NOT NULL DEFAULT '',
            silenciado     INTEGER DEFAULT 0,
            obs            TEXT    DEFAULT '',
            criado_por     TEXT    DEFAULT '',
            criado_em      TEXT    DEFAULT (datetime('now','localtime')),
            atualizado_em  TEXT    DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_cred_validade ON credenciais(data_validade);

        CREATE TABLE IF NOT EXISTS credenciais_avisos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            credencial_id INTEGER NOT NULL,
            tipo_aviso    TEXT    NOT NULL,
            enviado_em    TEXT    DEFAULT (datetime('now','localtime')),
            UNIQUE(credencial_id, tipo_aviso)
        );

        CREATE TABLE IF NOT EXISTS os_controle (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id     INTEGER,
            tecnico        TEXT,
            empresa        TEXT,
            banco          TEXT,
            servico        TEXT,
            aba_homologado TEXT,
            id_homologado  INTEGER,
            status         TEXT DEFAULT 'PENDENTE',
            criado_em      TEXT DEFAULT (datetime('now','localtime')),
            concluido_em   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_os_controle_usuario ON os_controle(usuario_id);
        CREATE INDEX IF NOT EXISTS idx_os_controle_status  ON os_controle(status);
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

    # Bancos cadastro — seed apenas se vazio
    if conn.execute("SELECT COUNT(*) FROM bancos_cadastro").fetchone()[0] == 0:
        for b in BANCOS_CADASTRO_INICIAIS:
            conn.execute(
                "INSERT INTO bancos_cadastro (codigo,nome,tem_api,ordem) VALUES (?,?,?,?)", b
            )

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
        VALUES ('bruno', 'bruno08912', 'Bruno', 'master', 0)
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
        "ALTER TABLE email_config_usuario ADD COLUMN assinatura TEXT DEFAULT ''",
        "ALTER TABLE melhorias ADD COLUMN criado_por_id INTEGER",
        "ALTER TABLE usuarios ADD COLUMN usuario_sisplan TEXT DEFAULT ''",
        "ALTER TABLE usuarios ADD COLUMN tela_inicial TEXT DEFAULT 'home'",
        "ALTER TABLE usuarios ADD COLUMN bloqueado_usuarios INTEGER DEFAULT 0",
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


def _hash_senha(senha: str) -> str:
    return generate_password_hash(senha)

def _verificar_senha(senha_digitada: str, hash_armazenado: str) -> bool:
    # compatibilidade com senhas antigas em texto puro
    if not hash_armazenado.startswith('pbkdf2:') and not hash_armazenado.startswith('scrypt:'):
        return senha_digitada == hash_armazenado
    return check_password_hash(hash_armazenado, senha_digitada)

def buscar_usuario_por_login(usuario_digitado, senha_digitada):
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE LOWER(usuario)=LOWER(?)",
        (usuario_digitado.strip(),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    u = dict(row)
    if not _verificar_senha(senha_digitada, u.get('senha', '')):
        return None
    # migra senha plain-text para hash na primeira vez que logar
    if not u['senha'].startswith('pbkdf2:') and not u['senha'].startswith('scrypt:'):
        _migrar_senha(u['id'], senha_digitada)
    return u

def _migrar_senha(id_usuario: int, senha_plain: str):
    conn = conectar()
    try:
        conn.execute("UPDATE usuarios SET senha=? WHERE id=?", (_hash_senha(senha_plain), id_usuario))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

# ── Técnicos ──────────────────────────────────────────────

def listar_tecnicos():
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM tecnicos WHERE UPPER(TRIM(nome)) != 'SEM TEC.' ORDER BY nome"
    ).fetchall()
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
            (dados['usuario'].strip().lower(), _hash_senha(dados['senha']), dados['nome'].strip(),
             dados['nivel'], dados.get('tecnico_vinculado') or None,
             dados.get('setor') or '', dados.get('cor') or '')
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def atualizar_usuario(id_usuario, campos):
    """Edição via tela de Usuários. Não mexe em 'cor' — isso é exclusivo do
    autoatendimento em /api/minha-cor (atualizar_cor_usuario), pra não zerar
    a cor de identificação do usuário a cada edição administrativa."""
    conn = conectar()
    av_esc  = 1 if campos.get('recebe_aviso_escritural')  else 0
    av_mel  = 1 if campos.get('recebe_aviso_melhorias')   else 0
    av_cred = 1 if campos.get('recebe_aviso_credenciais') else 0
    pode_env = 1 if campos.get('pode_enviar_notificacao') else 0
    pode_dec = 1 if campos.get('pode_descriptografar')    else 0
    usuario_sisplan = (campos.get('usuario_sisplan') or '').strip()
    if campos.get('senha'):
        conn.execute(
            "UPDATE usuarios SET nome=?,nivel=?,tecnico_vinculado=?,senha=?,setor=?,"
            "recebe_aviso_escritural=?,recebe_aviso_melhorias=?,recebe_aviso_credenciais=?,"
            "pode_enviar_notificacao=?,pode_descriptografar=?,usuario_sisplan=? WHERE id=?",
            (campos.get('nome'), campos.get('nivel'), campos.get('tecnico_vinculado') or None,
             _hash_senha(campos['senha']), campos.get('setor') or '',
             av_esc, av_mel, av_cred, pode_env, pode_dec, usuario_sisplan, id_usuario)
        )
    else:
        conn.execute(
            "UPDATE usuarios SET nome=?,nivel=?,tecnico_vinculado=?,setor=?,"
            "recebe_aviso_escritural=?,recebe_aviso_melhorias=?,recebe_aviso_credenciais=?,"
            "pode_enviar_notificacao=?,pode_descriptografar=?,usuario_sisplan=? WHERE id=?",
            (campos.get('nome'), campos.get('nivel'), campos.get('tecnico_vinculado') or None,
             campos.get('setor') or '', av_esc, av_mel, av_cred, pode_env, pode_dec, usuario_sisplan, id_usuario)
        )
    conn.commit()
    conn.close()


def atualizar_cor_usuario(id_usuario, cor):
    conn = conectar()
    conn.execute("UPDATE usuarios SET cor=? WHERE id=?", (cor, id_usuario))
    conn.commit()
    conn.close()


def buscar_usuario_por_tecnico(nome_tecnico):
    """Retorna o dict do usuário cujo tecnico_vinculado == nome_tecnico, ou None."""
    if not nome_tecnico:
        return None
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE LOWER(TRIM(tecnico_vinculado))=LOWER(TRIM(?))",
        (nome_tecnico,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_usuario_por_usuario_sisplan(usuario_sisplan):
    """Retorna o dict do usuário local vinculado a esse usuário Sisplan, ou None."""
    if not usuario_sisplan:
        return None
    conn = conectar()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE usuario_sisplan<>'' AND LOWER(TRIM(usuario_sisplan))=LOWER(TRIM(?))",
        (usuario_sisplan,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_tecnico_escritural(escritural_id):
    """Retorna o nome do técnico responsável pelo registro escritural, ou None."""
    conn = conectar()
    row = conn.execute("SELECT tecnico FROM escritural WHERE id=?", (escritural_id,)).fetchone()
    conn.close()
    return row['tecnico'] if row else None




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
    try:
        conn.execute("UPDATE usuarios SET senha=?,mudar_senha=1 WHERE id=?", (_hash_senha('123456'), id_usuario))
        conn.execute("DELETE FROM sessoes_ativas WHERE usuario_id=?", (id_usuario,))
        conn.commit()
    finally:
        conn.close()


def definir_bloqueio_usuarios(id_usuario, bloqueado: bool):
    """Bloqueia/libera o acesso de um usuário master à tela de Cadastro de
    Usuários — usado pelo 'master absoluto' pra restringir outro master sem
    mexer no nível dele nem em mais nenhuma outra permissão."""
    conn = conectar()
    conn.execute("UPDATE usuarios SET bloqueado_usuarios=? WHERE id=?", (1 if bloqueado else 0, id_usuario))
    conn.commit()
    conn.close()


def encerrar_sessoes_usuario(id_usuario):
    """Derruba a(s) sessão(ões) ativa(s) de um usuário. Usado quando outra pessoa
    (admin/master) muda nível ou permissões dele — a sessão em memória (Flask
    session/JWT) não se autoatualiza sozinha, então isso força um relogin na
    próxima requisição, que já vem com o nível/telas certos do banco."""
    conn = conectar()
    try:
        conn.execute("DELETE FROM sessoes_ativas WHERE usuario_id=?", (id_usuario,))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def migrar_senhas_plaintext():
    """Hasheia senhas em texto puro deixadas por versões anteriores."""
    conn = conectar()
    try:
        rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
        for r in rows:
            s = r['senha'] or ''
            if s and not s.startswith('pbkdf2:') and not s.startswith('scrypt:'):
                conn.execute("UPDATE usuarios SET senha=? WHERE id=?", (_hash_senha(s), r['id']))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def migrar_flags_avisos():
    """Adiciona colunas de flags de aviso a usuários se ainda não existirem."""
    conn = conectar()
    try:
        existentes = {r[1] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()}
        for col in ('recebe_aviso_escritural', 'recebe_aviso_melhorias',
                    'pode_enviar_notificacao', 'recebe_aviso_credenciais',
                    'pode_descriptografar'):
            if col not in existentes:
                conn.execute(f"ALTER TABLE usuarios ADD COLUMN {col} INTEGER DEFAULT 0")
        # Tabela de solicitações de descriptografia
        conn.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes_descriptografia (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                solicitante_id    INTEGER NOT NULL,
                solicitante_nome  TEXT    NOT NULL,
                client_id_enc     TEXT    NOT NULL,
                client_secret_enc TEXT    NOT NULL,
                client_id_dec     TEXT,
                client_secret_dec TEXT,
                status            TEXT    NOT NULL DEFAULT 'pendente',
                aprovado_por      TEXT,
                criado_em         TEXT    NOT NULL,
                respondido_em     TEXT,
                expira_em         TEXT
            )
        """)
        # Coluna link em notificacoes (para navegação ao clicar na notif nativa)
        cols_notif = {r[1] for r in conn.execute("PRAGMA table_info(notificacoes)").fetchall()}
        if 'link' not in cols_notif:
            conn.execute("ALTER TABLE notificacoes ADD COLUMN link TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass
    finally:
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
    conn.execute("UPDATE usuarios SET senha=?,mudar_senha=0 WHERE id=?", (_hash_senha(nova_senha), id_usuario))
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


# ── Bancos Cadastro ───────────────────────────────────────

def listar_bancos_cadastro(apenas_ativos=False):
    conn = conectar()
    sql = "SELECT * FROM bancos_cadastro"
    if apenas_ativos:
        sql += " WHERE ativo=1"
    sql += " ORDER BY ordem, codigo"
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_banco_cadastro(codigo, nome, tem_api=0):
    conn = conectar()
    try:
        conn.execute(
            "INSERT INTO bancos_cadastro (codigo,nome,tem_api) VALUES (?,?,?)",
            (codigo.strip(), nome.strip(), int(bool(tem_api)))
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def atualizar_banco_cadastro(id_banco, codigo, nome, tem_api, ativo):
    conn = conectar()
    conn.execute(
        "UPDATE bancos_cadastro SET codigo=?,nome=?,tem_api=?,ativo=? WHERE id=?",
        (codigo.strip(), nome.strip(), int(bool(tem_api)), int(bool(ativo)), id_banco)
    )
    conn.commit()
    conn.close()


def remover_banco_cadastro(id_banco):
    conn = conectar()
    conn.execute("DELETE FROM bancos_cadastro WHERE id=?", (id_banco,))
    conn.commit()
    conn.close()


# ── Melhorias ─────────────────────────────────────────────

def listar_melhorias():
    conn = conectar()
    rows = conn.execute(
        """SELECT m.*,
               (SELECT COUNT(*) FROM melhorias_imagens WHERE melhoria_id=m.id) AS imagens_count
           FROM melhorias m ORDER BY m.criado_em DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_melhoria(dados: dict) -> int:
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')
    conn = conectar()
    cur = conn.execute(
        """INSERT INTO melhorias (titulo, descricao, prioridade, programador, solicitante, criado_por, criado_por_id, criado_em, atualizado_em)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            dados.get('titulo', ''),
            dados.get('descricao', ''),
            dados.get('prioridade', 'media'),
            dados.get('programador', ''),
            dados.get('solicitante', ''),
            dados.get('criado_por', ''),
            dados.get('criado_por_id'),
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
    arquivos = [r[0] for r in conn.execute(
        "SELECT nome_arquivo FROM melhorias_imagens WHERE melhoria_id=?", (id_melhoria,)
    ).fetchall()]
    conn.execute("DELETE FROM melhorias_imagens WHERE melhoria_id=?", (id_melhoria,))
    conn.execute("DELETE FROM melhorias WHERE id=?", (id_melhoria,))
    conn.commit()
    conn.close()
    return arquivos


def listar_imagens_melhoria(id_melhoria: int):
    conn = conectar()
    rows = conn.execute(
        "SELECT id, nome_arquivo FROM melhorias_imagens WHERE melhoria_id=? ORDER BY id",
        (id_melhoria,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adicionar_imagem_melhoria(id_melhoria: int, nome_arquivo: str) -> int:
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO melhorias_imagens (melhoria_id, nome_arquivo) VALUES (?,?)",
        (id_melhoria, nome_arquivo)
    )
    conn.commit()
    img_id = cur.lastrowid
    conn.close()
    return img_id


def remover_imagem_melhoria(img_id: int):
    conn = conectar()
    row = conn.execute(
        "SELECT nome_arquivo FROM melhorias_imagens WHERE id=?", (img_id,)
    ).fetchone()
    conn.execute("DELETE FROM melhorias_imagens WHERE id=?", (img_id,))
    conn.commit()
    conn.close()
    return row['nome_arquivo'] if row else None


def buscar_melhoria(id_melhoria: int):
    conn = conectar()
    row = conn.execute("SELECT * FROM melhorias WHERE id=?", (id_melhoria,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Config Geral ─────────────────────────────────────────

def get_config(chave, default=''):
    conn = conectar()
    row  = conn.execute("SELECT valor FROM config_geral WHERE chave=?", (chave,)).fetchone()
    conn.close()
    return row['valor'] if row else default


def set_config(chave, valor):
    conn = conectar()
    conn.execute("INSERT OR REPLACE INTO config_geral(chave, valor) VALUES(?,?)", (chave, str(valor)))
    conn.commit()
    conn.close()


# ── SLA Config ───────────────────────────────────────────

def listar_sla_config():
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM sla_config ORDER BY CASE WHEN servico='__default__' THEN 0 ELSE 1 END, servico"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def salvar_sla_servico(servico, prazo_total, aviso_dias, atrasado_dias, critico_dias):
    conn = conectar()
    conn.execute(
        """INSERT INTO sla_config(servico, prazo_total, aviso_dias, atrasado_dias, critico_dias)
           VALUES(?,?,?,?,?)
           ON CONFLICT(servico) DO UPDATE SET
               prazo_total=excluded.prazo_total,
               aviso_dias=excluded.aviso_dias,
               atrasado_dias=excluded.atrasado_dias,
               critico_dias=excluded.critico_dias""",
        (servico, int(prazo_total), int(aviso_dias), int(atrasado_dias), int(critico_dias))
    )
    conn.commit()
    conn.close()


def remover_sla_servico(id_sla):
    conn = conectar()
    conn.execute("DELETE FROM sla_config WHERE id=? AND servico != '__default__'", (id_sla,))
    conn.commit()
    conn.close()


def recalcular_vencimentos_pendentes():
    configs = listar_sla_config()
    config_map = {}
    default_prazo = 30
    for c in configs:
        if c['servico'] == '__default__':
            default_prazo = c['prazo_total'] or 30
        else:
            config_map[(c['servico'] or '').upper().strip()] = c['prazo_total'] or 30

    conn = conectar()
    rows = conn.execute(
        "SELECT id, servico, dt_solicita FROM pendentes "
        "WHERE (dt_status IS NULL OR TRIM(dt_status)='') "
        "AND dt_solicita IS NOT NULL AND TRIM(dt_solicita) != ''"
    ).fetchall()
    updated = 0
    for row in rows:
        try:
            parts = (row['dt_solicita'] or '').strip().split('/')
            if len(parts) != 3:
                continue
            dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            prazo = config_map.get((row['servico'] or '').upper().strip(), default_prazo)
            dt_venc = (dt + timedelta(days=prazo)).strftime('%d/%m/%Y')
            conn.execute("UPDATE pendentes SET dt_status=? WHERE id=?", (dt_venc, row['id']))
            updated += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return updated


# ── SLA Avisos ───────────────────────────────────────────

def listar_sla_avisos(apenas_ativos=False):
    from datetime import datetime as _dt
    conn = conectar()
    rows = conn.execute("SELECT * FROM sla_avisos ORDER BY criado_em DESC").fetchall()
    conn.close()
    hoje = _dt.now().strftime('%Y-%m-%d')
    result = []
    for r in rows:
        d = dict(r)
        if apenas_ativos and d.get('expira_em') and d['expira_em'] < hoje:
            continue
        result.append(d)
    return result


def adicionar_sla_aviso(texto, tipo, expira_em, criado_por):
    conn = conectar()
    conn.execute(
        "INSERT INTO sla_avisos(texto, tipo, expira_em, criado_por) VALUES(?,?,?,?)",
        (texto, tipo or 'info', expira_em or '', criado_por)
    )
    conn.commit()
    conn.close()


def remover_sla_aviso(id_aviso):
    conn = conectar()
    conn.execute("DELETE FROM sla_avisos WHERE id=?", (id_aviso,))
    conn.commit()
    conn.close()


# ── SLA Cálculo ──────────────────────────────────────────

def migrar_sla():
    conn = conectar()
    for col in ('cadastrado_por_tec', 'obs_interna'):
        try:
            conn.execute(f"ALTER TABLE pendentes ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass
    for col_def in (
        'prazo_total   INTEGER DEFAULT 30',
        'aviso_dias    INTEGER DEFAULT 7',
        'atrasado_dias INTEGER DEFAULT 7',
        'critico_dias  INTEGER DEFAULT 15',
    ):
        try:
            conn.execute(f"ALTER TABLE sla_config ADD COLUMN {col_def}")
            conn.commit()
        except Exception:
            pass
    conn.close()


def salvar_obs_interna(id_reg, texto):
    conn = conectar()
    conn.execute("UPDATE pendentes SET obs_interna=? WHERE id=?", ((texto or '').strip(), id_reg))
    conn.commit()
    conn.close()


def calcular_sla_pendentes():
    from datetime import datetime as _dt, date as _date
    conn = conectar()
    pendentes = conn.execute(
        "SELECT * FROM pendentes WHERE status NOT IN ('CANCELADO')"
    ).fetchall()
    sla_rows = conn.execute("SELECT * FROM sla_config").fetchall()
    conn.close()

    sla_map = {r['servico']: dict(r) for r in sla_rows}
    _DEF    = {'prazo_total': 30, 'aviso_dias': 7, 'atrasado_dias': 7, 'critico_dias': 15}
    default = sla_map.get('__default__', _DEF)
    hoje    = _date.today()
    result  = []

    for p in pendentes:
        pd = dict(p)
        try:
            dt_ini = _dt.strptime((pd.get('dt_solicita') or '').strip(), '%d/%m/%Y').date()
            dias   = (hoje - dt_ini).days
        except Exception:
            dias = 0

        servico = (pd.get('servico') or '').strip()
        sla     = sla_map.get(servico, default)

        prazo   = sla.get('prazo_total',   default.get('prazo_total',   30))
        aviso   = sla.get('aviso_dias',    default.get('aviso_dias',     7))
        atras   = sla.get('atrasado_dias', default.get('atrasado_dias',  7))
        critico = sla.get('critico_dias',  default.get('critico_dias',  15))

        if   dias < prazo - aviso:     faixa = 'ok'
        elif dias < prazo:             faixa = 'atencao'
        elif dias < prazo + atras:     faixa = 'vencido'
        elif dias < prazo + critico:   faixa = 'atrasado'
        else:                          faixa = 'critico'

        pd['dias_em_aberto'] = dias
        pd['dias_restantes'] = prazo - dias
        pd['sla_faixa']      = faixa
        pd['sla_prazo']      = sla
        result.append(pd)

    return sorted(result, key=lambda x: x['dias_em_aberto'], reverse=True)


def resumo_sla():
    pendentes = calcular_sla_pendentes()
    totais = {'total': len(pendentes), 'ok': 0, 'atencao': 0, 'vencido': 0, 'atrasado': 0, 'critico': 0}
    por_tecnico = {}
    por_servico = {}

    for p in pendentes:
        faixa = p['sla_faixa']
        totais[faixa] = totais.get(faixa, 0) + 1
        dias = p['dias_em_aberto']

        tec = (p.get('tecnico') or '—').strip() or '—'
        if tec not in por_tecnico:
            por_tecnico[tec] = {'tecnico': tec, 'total': 0, 'soma_dias': 0,
                                'ok': 0, 'atencao': 0, 'vencido': 0, 'atrasado': 0, 'critico': 0}
        por_tecnico[tec]['total']     += 1
        por_tecnico[tec]['soma_dias'] += dias
        por_tecnico[tec][faixa]       += 1

        srv = (p.get('servico') or '—').strip() or '—'
        if srv not in por_servico:
            por_servico[srv] = {'servico': srv, 'total': 0,
                                'ok': 0, 'atencao': 0, 'vencido': 0, 'atrasado': 0, 'critico': 0}
        por_servico[srv]['total'] += 1
        por_servico[srv][faixa]   += 1

    def _media(d):
        return round(d['soma_dias'] / d['total'], 1) if d['total'] else 0

    tecnicos_rank = sorted(
        [{'tecnico': k, 'total': v['total'], 'media_dias': _media(v),
          'ok': v['ok'], 'atencao': v['atencao'], 'vencido': v['vencido'],
          'atrasado': v['atrasado'], 'critico': v['critico']}
         for k, v in por_tecnico.items()],
        key=lambda x: (x['critico'] * 1000 + x['atrasado'] * 100 + x['vencido'] * 10 + x['media_dias']),
        reverse=True
    )

    taxa = round((totais['ok'] / totais['total'] * 100), 1) if totais['total'] else 0.0

    return {
        'totais':    totais,
        'taxa_ok':   taxa,
        'tecnicos':  tecnicos_rank,
        'servicos':  sorted(por_servico.values(), key=lambda x: x['critico'] * 100 + x['atrasado'] * 10 + x['vencido'], reverse=True),
        'pendentes': pendentes,
    }


# ── SLA Notificações Preferências ─────────────────────────

def listar_notif_pref_usuario(usuario_id):
    conn = conectar()
    rows = conn.execute("SELECT * FROM sla_notif_pref WHERE usuario_id=?", (usuario_id,)).fetchall()
    conn.close()
    defaults = {'critico': {'ativo': 1, 'freq_dias': 1}, 'atrasado': {'ativo': 0, 'freq_dias': 3}, 'atencao': {'ativo': 0, 'freq_dias': 7}}
    for r in rows:
        defaults[r['faixa']] = {'ativo': r['ativo'], 'freq_dias': r['freq_dias']}
    return defaults


def salvar_notif_pref(usuario_id, faixa, ativo, freq_dias):
    conn = conectar()
    conn.execute(
        """INSERT INTO sla_notif_pref(usuario_id, faixa, ativo, freq_dias)
           VALUES(?,?,?,?)
           ON CONFLICT(usuario_id, faixa) DO UPDATE SET ativo=excluded.ativo, freq_dias=excluded.freq_dias""",
        (usuario_id, faixa, int(bool(ativo)), int(freq_dias))
    )
    conn.commit()
    conn.close()


def listar_usuarios_por_setor(setor):
    """Retorna IDs de usuários ativos no setor informado."""
    conn = conectar()
    rows = conn.execute(
        "SELECT id FROM usuarios WHERE setor=? AND id IS NOT NULL", (setor,)
    ).fetchall()
    conn.close()
    return [r['id'] for r in rows]


def get_sla_setores_notif():
    """Retorna lista de setores configurados para receber alertas SLA."""
    import json
    val = get_config('sla_setores_notif', '[]')
    try:
        return json.loads(val)
    except Exception:
        return []


def set_sla_setores_notif(setores):
    import json
    set_config('sla_setores_notif', json.dumps(setores))


def verificar_e_notificar_sla(usuario_id):
    from datetime import datetime as _dt
    if not usuario_id:
        return
    prefs = listar_notif_pref_usuario(usuario_id)
    pendentes = calcular_sla_pendentes()
    hoje = _dt.now().strftime('%Y-%m-%d')
    conn = conectar()

    for faixa, pref in prefs.items():
        if not pref.get('ativo'):
            continue
        freq = int(pref.get('freq_dias', 1))
        row = conn.execute(
            "SELECT ultima_notif FROM sla_notif_pref WHERE usuario_id=? AND faixa=?",
            (usuario_id, faixa)
        ).fetchone()
        ultima = (row['ultima_notif'] if row else '') or ''
        if ultima:
            try:
                diff = (_dt.now() - _dt.strptime(ultima, '%Y-%m-%d')).days
                if diff < freq:
                    continue
            except Exception:
                pass

        items = [p for p in pendentes if p['sla_faixa'] == faixa]
        if not items:
            continue

        nomes = {'critico': 'CRÍTICO', 'atrasado': 'atrasado', 'atencao': 'em atenção'}
        titulo = f'SLA: {len(items)} pendente(s) {nomes.get(faixa, faixa)}'
        primeiro = items[0]
        msg = f"{primeiro.get('empresa','?')} — {primeiro.get('dias_em_aberto',0)} dias"
        if len(items) > 1:
            msg += f' e +{len(items)-1}'
        tipo = 'alerta' if faixa == 'critico' else 'aviso'
        criar_notificacao(usuario_id, titulo, msg, tipo)

        conn.execute(
            """INSERT INTO sla_notif_pref(usuario_id, faixa, ativo, freq_dias, ultima_notif)
               VALUES(?,?,?,?,?)
               ON CONFLICT(usuario_id, faixa) DO UPDATE SET ultima_notif=excluded.ultima_notif""",
            (usuario_id, faixa, pref.get('ativo', 1), freq, hoje)
        )
        conn.commit()

    conn.close()

    # Notificar usuários dos setores configurados (independente de quem acessou)
    setores_alvo = get_sla_setores_notif()
    if not setores_alvo:
        return
    criticos  = [p for p in pendentes if p['sla_faixa'] == 'critico']
    atrasados = [p for p in pendentes if p['sla_faixa'] in ('critico', 'atrasado', 'vencido')]
    if not atrasados:
        return
    titulo_s = f'SLA: {len(atrasados)} pendente(s) fora do prazo'
    primeiro  = atrasados[0]
    msg_s     = f"{primeiro.get('empresa','?')} — {primeiro.get('dias_em_aberto',0)} dias"
    if len(atrasados) > 1:
        msg_s += f' e +{len(atrasados)-1}'
    tipo_s = 'alerta' if criticos else 'aviso'

    notificados = {usuario_id}
    for setor in setores_alvo:
        for uid in listar_usuarios_por_setor(setor):
            if uid in notificados:
                continue
            notificados.add(uid)
            criar_notificacao(uid, titulo_s, msg_s, tipo_s)


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


# ── Hub v2: categorias, serviços dinâmicos ────────────────

def migrar_hub_v2():
    """Migra dados do hub_bancos (colunas booleanas) para o modelo de categorias/serviços."""
    conn = conectar()
    try:
        if conn.execute("SELECT COUNT(*) FROM hub_categorias").fetchone()[0] > 0:
            return
        cat_ids = {}
        for nome, ordem in [('Cobrança', 1), ('Pagamento', 2), ('Extrato', 3), ('DDA', 4)]:
            conn.execute("INSERT INTO hub_categorias (nome, ordem) VALUES (?, ?)", (nome, ordem))
            cat_ids[nome] = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        mapa = [
            (cat_ids['Cobrança'],  'Envio',            '#dbeafe', '#1d4ed8', 1, 'cobranca_envio'),
            (cat_ids['Cobrança'],  'Instrução',         '#ede9fe', '#6d28d9', 2, 'cobranca_instrucao'),
            (cat_ids['Cobrança'],  'Retorno',           '#dcfce7', '#15803d', 3, 'cobranca_retorno'),
            (cat_ids['Pagamento'], 'Boleto',            '#fef3c7', '#92400e', 1, 'pagamento_boleto'),
            (cat_ids['Pagamento'], 'PIX',               '#d1fae5', '#065f46', 2, 'pagamento_pix'),
            (cat_ids['Extrato'],   'Consulta Extrato',  '#f0fdf4', '#166534', 1, 'extrato_consulta'),
            (cat_ids['DDA'],       'Consulta DDA',      '#ecfdf5', '#065f46', 1, 'dda_consulta'),
        ]
        serv_ids = {}
        for cat_id, nome, cor_bg, cor_texto, ordem, col in mapa:
            conn.execute(
                "INSERT INTO hub_servicos (categoria_id, nome, cor_bg, cor_texto, ordem) VALUES (?,?,?,?,?)",
                (cat_id, nome, cor_bg, cor_texto, ordem)
            )
            serv_ids[col] = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        bancos = conn.execute("SELECT * FROM hub_bancos").fetchall()
        for b in bancos:
            for col, sid in serv_ids.items():
                try:
                    if b[col]:
                        conn.execute(
                            "INSERT OR IGNORE INTO hub_banco_servicos (banco_id, servico_id) VALUES (?,?)",
                            (b['id'], sid)
                        )
                except Exception:
                    pass
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def hub_listar_bancos_v2():
    conn = conectar()
    bancos = conn.execute("SELECT id, nome, ordem FROM hub_bancos ORDER BY ordem, nome").fetchall()
    resultado = []
    for b in bancos:
        servicos = conn.execute("""
            SELECT s.id, s.nome, s.cor_bg, s.cor_texto, c.nome AS categoria, c.id AS categoria_id, c.ordem AS cat_ordem
            FROM hub_banco_servicos bs
            JOIN hub_servicos s ON s.id = bs.servico_id
            JOIN hub_categorias c ON c.id = s.categoria_id
            WHERE bs.banco_id = ?
            ORDER BY c.ordem, s.ordem
        """, (b['id'],)).fetchall()
        instrucoes = conn.execute(
            "SELECT * FROM hub_instrucoes WHERE banco_id=? ORDER BY ordem", (b['id'],)
        ).fetchall()
        cats = {}
        for s in servicos:
            cat = s['categoria']
            if cat not in cats:
                cats[cat] = {'id': s['categoria_id'], 'nome': cat, 'ordem': s['cat_ordem'], 'servicos': []}
            cats[cat]['servicos'].append(dict(s))
        resultado.append({
            'id': b['id'], 'nome': b['nome'], 'ordem': b['ordem'],
            'categorias': sorted(cats.values(), key=lambda x: x['ordem']),
            'instrucoes': [dict(i) for i in instrucoes],
        })
    conn.close()
    return resultado


def hub_adicionar_banco_v2(nome: str, ordem: int = 99) -> int:
    conn = conectar()
    conn.execute("INSERT INTO hub_bancos (nome, ordem) VALUES (?, ?)", (nome, ordem))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return new_id


def hub_atualizar_banco_v2(banco_id: int, nome: str, ordem: int = 99):
    conn = conectar()
    conn.execute("UPDATE hub_bancos SET nome=?, ordem=? WHERE id=?", (nome, ordem, banco_id))
    conn.commit()
    conn.close()


def hub_sincronizar_banco_servicos(banco_id: int, servico_ids: list):
    conn = conectar()
    conn.execute("DELETE FROM hub_banco_servicos WHERE banco_id=?", (banco_id,))
    for sid in servico_ids:
        conn.execute("INSERT OR IGNORE INTO hub_banco_servicos (banco_id, servico_id) VALUES (?,?)", (banco_id, int(sid)))
    conn.commit()
    conn.close()


def hub_listar_categorias():
    conn = conectar()
    rows = conn.execute("SELECT * FROM hub_categorias ORDER BY ordem, nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def hub_adicionar_categoria(nome: str, ordem: int = 99) -> int:
    conn = conectar()
    conn.execute("INSERT INTO hub_categorias (nome, ordem) VALUES (?, ?)", (nome, ordem))
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return new_id


def hub_atualizar_categoria(cat_id: int, nome: str, ordem: int = 99):
    conn = conectar()
    conn.execute("UPDATE hub_categorias SET nome=?, ordem=? WHERE id=?", (nome, ordem, cat_id))
    conn.commit()
    conn.close()


def hub_remover_categoria(cat_id: int):
    conn = conectar()
    conn.execute("DELETE FROM hub_banco_servicos WHERE servico_id IN (SELECT id FROM hub_servicos WHERE categoria_id=?)", (cat_id,))
    conn.execute("DELETE FROM hub_servicos WHERE categoria_id=?", (cat_id,))
    conn.execute("DELETE FROM hub_categorias WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


def hub_listar_servicos():
    conn = conectar()
    rows = conn.execute("""
        SELECT s.*, c.nome AS categoria_nome
        FROM hub_servicos s
        JOIN hub_categorias c ON c.id = s.categoria_id
        ORDER BY c.ordem, s.ordem, s.nome
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def hub_adicionar_servico(categoria_id: int, nome: str, cor_bg: str, cor_texto: str, ordem: int = 99) -> int:
    conn = conectar()
    conn.execute(
        "INSERT INTO hub_servicos (categoria_id, nome, cor_bg, cor_texto, ordem) VALUES (?,?,?,?,?)",
        (categoria_id, nome, cor_bg, cor_texto, ordem)
    )
    conn.commit()
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return new_id


def hub_atualizar_servico(serv_id: int, categoria_id: int, nome: str, cor_bg: str, cor_texto: str, ordem: int = 99):
    conn = conectar()
    conn.execute(
        "UPDATE hub_servicos SET categoria_id=?, nome=?, cor_bg=?, cor_texto=?, ordem=? WHERE id=?",
        (categoria_id, nome, cor_bg, cor_texto, ordem, serv_id)
    )
    conn.commit()
    conn.close()


def hub_remover_servico(serv_id: int):
    conn = conectar()
    conn.execute("DELETE FROM hub_banco_servicos WHERE servico_id=?", (serv_id,))
    conn.execute("DELETE FROM hub_servicos WHERE id=?", (serv_id,))
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
    tec = dados.get('tecnico', '')
    cur = conn.execute(
        "INSERT INTO pendentes (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por,cadastrado_por_tec) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (tec, dados.get('empresa',''), dados.get('servico',''),
         dados.get('banco',''), dados.get('dt_solicita',''), dados.get('dt_status',''),
         dados.get('status',''), dados.get('obs',''), criado_por, tec)
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
    tabela = _TABELA_HOMOLOGADO.get(tipo)
    if not tabela:
        return False
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
    'ext-bancario': 'homologados_ext_bancario',
}

# conjunto de nomes de tabela permitidos para uso em queries dinâmicas
_TABELAS_HOMOLOGADO_VALIDAS = frozenset(_TABELA_HOMOLOGADO.values())


def buscar_registro_homologado(tabela, id_registro):
    """Busca uma linha completa de uma das 4 tabelas homologados_* pelo id.
    'tabela' é validada contra a whitelist para não permitir SQL dinâmico arbitrário."""
    if tabela not in _TABELAS_HOMOLOGADO_VALIDAS:
        return None
    conn = conectar()
    row = conn.execute(f"SELECT * FROM {tabela} WHERE id=?", (id_registro,)).fetchone()
    conn.close()
    return dict(row) if row else None


def contar_registros_homologado(tabela):
    """Conta linhas de uma das 4 tabelas homologados_*, validada contra a whitelist."""
    if tabela not in _TABELAS_HOMOLOGADO_VALIDAS:
        return 0
    conn = conectar()
    n = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
    conn.close()
    return n


def ranking_tecnicos_homologados(tabelas):
    """Soma registros por técnico entre as tabelas homologados_* informadas
    (só as que estiverem na whitelist são consideradas). Retorna dict
    {tecnico: quantidade} ordenado do maior pro menor."""
    tabelas_validas = [t for t in tabelas if t in _TABELAS_HOMOLOGADO_VALIDAS]
    if not tabelas_validas:
        return {}
    conn = conectar()
    ranking = {}
    for tabela in tabelas_validas:
        for r in conn.execute(f"SELECT tecnico, COUNT(*) as qtd FROM {tabela} GROUP BY tecnico").fetchall():
            tec = r['tecnico'] or 'SEM TEC.'
            ranking[tec] = ranking.get(tec, 0) + r['qtd']
    conn.close()
    return dict(sorted(ranking.items(), key=lambda x: x[1], reverse=True))


def atualizar_tela_inicial(usuario_id, tela):
    conn = conectar()
    conn.execute("UPDATE usuarios SET tela_inicial=? WHERE id=?", (tela, usuario_id))
    conn.commit()
    conn.close()


def mover_pendente_para_homologado(id_pendente):
    conn = conectar()
    row = conn.execute("SELECT * FROM pendentes WHERE id=?", (id_pendente,)).fetchone()
    if not row:
        conn.close()
        return None, None, None
    d      = dict(row)
    aba    = _aba_homologado(d['servico'])
    tabela = _TABELA_HOMOLOGADO[aba]
    hoje = datetime.now().strftime('%d/%m/%Y')
    cur = conn.execute(
        f"INSERT INTO {tabela} (tecnico,empresa,servico,banco,dt_solicita,dt_status,status,obs,criado_por) VALUES (?,?,?,?,?,?,?,?,?)",
        (d['tecnico'], d['empresa'], d['servico'], d['banco'],
         d['dt_solicita'], hoje, 'HOMOLOGADO', d['obs'], d.get('criado_por',''))
    )
    conn.execute("DELETE FROM pendentes WHERE id=?", (id_pendente,))
    conn.commit()
    conn.close()
    return cur.lastrowid, aba, d


# ── Controle de O.S. ──────────────────────────────────────

def criar_os(dados: dict) -> int:
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO os_controle (usuario_id,tecnico,empresa,banco,servico,aba_homologado,id_homologado,status) "
        "VALUES (?,?,?,?,?,?,?,'PENDENTE')",
        (dados.get('usuario_id'), dados.get('tecnico', ''), dados.get('empresa', ''),
         dados.get('banco', ''), dados.get('servico', ''), dados.get('aba_homologado', ''),
         dados.get('id_homologado'))
    )
    id_novo = cur.lastrowid
    conn.commit()
    conn.close()
    return id_novo


def listar_os(usuario_id=None):
    conn = conectar()
    if usuario_id is None:
        rows = conn.execute("SELECT * FROM os_controle ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM os_controle WHERE usuario_id=? ORDER BY id DESC", (usuario_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_os(id_os):
    conn = conectar()
    row = conn.execute("SELECT * FROM os_controle WHERE id=?", (id_os,)).fetchone()
    conn.close()
    return dict(row) if row else None


def atualizar_status_os(id_os, novo_status):
    conn = conectar()
    if novo_status in ('CONCLUIDA', 'BONIFICADA'):
        conn.execute(
            "UPDATE os_controle SET status=?, concluido_em=datetime('now','localtime') WHERE id=?",
            (novo_status, id_os)
        )
    else:
        conn.execute("UPDATE os_controle SET status=?, concluido_em=NULL WHERE id=?", (novo_status, id_os))
    conn.commit()
    conn.close()


def atribuir_os(id_os, usuario_id, tecnico):
    conn = conectar()
    conn.execute("UPDATE os_controle SET usuario_id=?, tecnico=? WHERE id=?", (usuario_id, tecnico, id_os))
    conn.commit()
    conn.close()


def contar_os_pendentes(usuario_id=None):
    conn = conectar()
    if usuario_id is None:
        n = conn.execute("SELECT COUNT(*) FROM os_controle WHERE status='PENDENTE'").fetchone()[0]
    else:
        n = conn.execute(
            "SELECT COUNT(*) FROM os_controle WHERE status='PENDENTE' AND usuario_id=?", (usuario_id,)
        ).fetchone()[0]
    conn.close()
    return n


def mover_homologado_para_pendente(id_registro, tipo, novo_status):
    tabela = _TABELA_HOMOLOGADO.get(tipo)
    if not tabela:
        return None
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
    tabela = _TABELA_HOMOLOGADO.get(tipo)
    if not tabela:
        return None
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
    senha_nova = (dados.get('senha') or '').strip()
    campos_base = (
        dados.get('email', ''), dados.get('smtp_host', ''), int(dados.get('smtp_port', 587)),
        1 if dados.get('smtp_ssl') else 0,
        dados.get('imap_host', ''), int(dados.get('imap_port', 993)),
        1 if dados.get('imap_ssl', True) else 0,
        dados.get('assinatura', ''),
    )
    if senha_nova:
        conn.execute("""
            INSERT INTO email_config_usuario
                (usuario_id, email, smtp_host, smtp_port, smtp_ssl, imap_host, imap_port, imap_ssl, senha, assinatura)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(usuario_id) DO UPDATE SET
                email=excluded.email, smtp_host=excluded.smtp_host, smtp_port=excluded.smtp_port,
                smtp_ssl=excluded.smtp_ssl, imap_host=excluded.imap_host, imap_port=excluded.imap_port,
                imap_ssl=excluded.imap_ssl, senha=excluded.senha, assinatura=excluded.assinatura
        """, (usuario_id,) + campos_base[:7] + (senha_nova, campos_base[7]))
    else:
        # Senha em branco → preserva a que já está no banco, não sobrescreve
        conn.execute("""
            INSERT INTO email_config_usuario
                (usuario_id, email, smtp_host, smtp_port, smtp_ssl, imap_host, imap_port, imap_ssl, senha, assinatura)
            VALUES (?,?,?,?,?,?,?,?,'',?)
            ON CONFLICT(usuario_id) DO UPDATE SET
                email=excluded.email, smtp_host=excluded.smtp_host, smtp_port=excluded.smtp_port,
                smtp_ssl=excluded.smtp_ssl, imap_host=excluded.imap_host, imap_port=excluded.imap_port,
                imap_ssl=excluded.imap_ssl, assinatura=excluded.assinatura
        """, (usuario_id,) + campos_base)
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

def registrar_sessao(jti: str, usuario_id: int, nome: str, nivel: str, ip: str):
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = conectar()
    try:
        # encerra sessões anteriores do mesmo usuário (garante sessão única)
        conn.execute("DELETE FROM sessoes_ativas WHERE usuario_id=?", (usuario_id,))
        conn.execute(
            "INSERT INTO sessoes_ativas (jti,usuario_id,nome,nivel,ip,login_em,ultimo_acesso) VALUES (?,?,?,?,?,?,?)",
            (jti, usuario_id, nome, nivel, ip, agora, agora)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def encerrar_sessao(jti: str):
    conn = conectar()
    try:
        conn.execute("DELETE FROM sessoes_ativas WHERE jti=?", (jti,))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def encerrar_sessao_por_id(id_sessao: int):
    conn = conectar()
    try:
        conn.execute("DELETE FROM sessoes_ativas WHERE id=?", (id_sessao,))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def sessao_valida(jti: str):
    """Retorna dict com info da sessão ou None se inválida/encerrada.
    O dict inclui mudar_senha/bloqueado_usuarios atuais do banco (não do JWT,
    para evitar bypass e pra revogações surtirem efeito quase na hora)."""
    conn = conectar()
    try:
        row = conn.execute(
            """SELECT s.id, u.mudar_senha, u.bloqueado_usuarios
               FROM sessoes_ativas s
               JOIN usuarios u ON u.id = s.usuario_id
               WHERE s.jti=?""",
            (jti,)
        ).fetchone()
        if row:
            agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("UPDATE sessoes_ativas SET ultimo_acesso=? WHERE jti=?", (agora, jti))
            conn.commit()
            return {
                'mudar_senha': int(row['mudar_senha'] or 0),
                'bloqueado_usuarios': int(row['bloqueado_usuarios'] or 0),
            }
        return None
    except Exception:
        return {}  # em caso de erro de I/O, não derruba o usuário
    finally:
        conn.close()


def listar_sessoes_ativas():
    conn = conectar()
    try:
        rows = conn.execute(
            "SELECT * FROM sessoes_ativas ORDER BY ultimo_acesso DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


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


# ── Notificações ──────────────────────────────────────────

def criar_notificacao(usuario_id, titulo, mensagem='', tipo='info', link=''):
    conn = conectar()
    cur = conn.execute(
        "INSERT INTO notificacoes (usuario_id, titulo, mensagem, tipo, link) VALUES (?,?,?,?,?)",
        (usuario_id, titulo, mensagem, tipo, link or '')
    )
    notif_id = cur.lastrowid
    conn.commit()
    conn.close()
    return notif_id


def criar_notificacao_todos(titulo, mensagem='', tipo='info'):
    """Cria a mesma notificação para todos os usuários ativos."""
    conn = conectar()
    ids = [r[0] for r in conn.execute("SELECT id FROM usuarios").fetchall()]
    for uid in ids:
        conn.execute(
            "INSERT INTO notificacoes (usuario_id, titulo, mensagem, tipo) VALUES (?,?,?,?)",
            (uid, titulo, mensagem, tipo)
        )
    conn.commit()
    conn.close()


def listar_notificacoes(usuario_id, limite=50):
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM notificacoes WHERE usuario_id=? ORDER BY id DESC LIMIT ?",
        (usuario_id, limite)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def contar_nao_lidas_notif(usuario_id):
    conn = conectar()
    r = conn.execute(
        "SELECT COUNT(*) FROM notificacoes WHERE usuario_id=? AND lida=0",
        (usuario_id,)
    ).fetchone()
    conn.close()
    return r[0] if r else 0


def buscar_notificacoes_novas(usuario_id, desde_id):
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM notificacoes WHERE usuario_id=? AND id>? ORDER BY id ASC",
        (usuario_id, desde_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def marcar_notificacao_lida(notif_id, usuario_id):
    conn = conectar()
    conn.execute(
        "UPDATE notificacoes SET lida=1 WHERE id=? AND usuario_id=?",
        (notif_id, usuario_id)
    )
    conn.commit()
    conn.close()


def marcar_todas_notificacoes_lidas(usuario_id):
    conn = conectar()
    conn.execute("UPDATE notificacoes SET lida=1 WHERE usuario_id=?", (usuario_id,))
    conn.commit()
    conn.close()


def deletar_notificacao(notif_id, usuario_id):
    conn = conectar()
    conn.execute(
        "DELETE FROM notificacoes WHERE id=? AND usuario_id=?",
        (notif_id, usuario_id)
    )
    conn.commit()
    conn.close()


def deletar_notificacoes_lidas(usuario_id):
    conn = conectar()
    conn.execute("DELETE FROM notificacoes WHERE usuario_id=? AND lida=1", (usuario_id,))
    conn.commit()
    conn.close()

def buscar_empresas_sistema(q: str) -> list:
    """Busca empresas em todas as tabelas do sistema que contenham q no nome ou CNPJ."""
    q_like = f'%{q}%'
    conn = conectar()
    sql = """
        SELECT nome, MAX(cnpj) AS cnpj FROM (
            SELECT empresa AS nome, COALESCE(cnpj,'') AS cnpj
              FROM escritural
             WHERE (empresa LIKE ? OR cnpj LIKE ?) AND empresa IS NOT NULL AND empresa != ''
            UNION ALL
            SELECT nome, COALESCE(cnpj,'') AS cnpj
              FROM credenciais
             WHERE (nome LIKE ? OR cnpj LIKE ?) AND nome IS NOT NULL AND nome != ''
            UNION ALL
            SELECT empresa AS nome, '' AS cnpj FROM pendentes
             WHERE empresa LIKE ? AND empresa IS NOT NULL AND empresa != ''
            UNION ALL
            SELECT empresa AS nome, '' AS cnpj FROM homologados_cobranca
             WHERE empresa LIKE ? AND empresa IS NOT NULL AND empresa != ''
            UNION ALL
            SELECT empresa AS nome, '' AS cnpj FROM homologados_pagamentos
             WHERE empresa LIKE ? AND empresa IS NOT NULL AND empresa != ''
            UNION ALL
            SELECT empresa AS nome, '' AS cnpj FROM homologados_extrato
             WHERE empresa LIKE ? AND empresa IS NOT NULL AND empresa != ''
            UNION ALL
            SELECT empresa AS nome, '' AS cnpj FROM homologados_ext_bancario
             WHERE empresa LIKE ? AND empresa IS NOT NULL AND empresa != ''
        )
        GROUP BY nome
        ORDER BY nome
        LIMIT 10
    """
    rows = conn.execute(sql, (q_like, q_like, q_like, q_like, q_like, q_like, q_like, q_like, q_like)).fetchall()
    conn.close()
    return [{'nome': (r['nome'] or '').strip(), 'cnpj': (r['cnpj'] or '').strip()} for r in rows]


def listar_credenciais():
    conn = conectar()
    rows = conn.execute(
        "SELECT * FROM credenciais ORDER BY data_validade ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_credencial(credencial_id):
    conn = conectar()
    row = conn.execute("SELECT * FROM credenciais WHERE id=?", (credencial_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def adicionar_credencial(dados):
    conn = conectar()
    cur = conn.execute(
        """INSERT INTO credenciais (cnpj, nome, tipo, banco, conta, data_validade, obs, criado_por)
           VALUES (?,?,?,?,?,?,?,?)""",
        (dados.get('cnpj',''), dados.get('nome',''), dados.get('tipo',''),
         dados.get('banco',''), dados.get('conta',''), dados.get('data_validade',''),
         dados.get('obs',''), dados.get('criado_por',''))
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def atualizar_credencial(credencial_id, dados):
    conn = conectar()
    # Se a data de validade mudou, reseta os avisos para esse ciclo
    old = conn.execute("SELECT data_validade FROM credenciais WHERE id=?", (credencial_id,)).fetchone()
    if old and old['data_validade'] != dados.get('data_validade', old['data_validade']):
        conn.execute("DELETE FROM credenciais_avisos WHERE credencial_id=?", (credencial_id,))
    conn.execute(
        """UPDATE credenciais SET cnpj=?,nome=?,tipo=?,banco=?,conta=?,data_validade=?,
           obs=?,atualizado_em=datetime('now','localtime') WHERE id=?""",
        (dados.get('cnpj',''), dados.get('nome',''), dados.get('tipo',''),
         dados.get('banco',''), dados.get('conta',''), dados.get('data_validade',''),
         dados.get('obs',''), credencial_id)
    )
    conn.commit()
    conn.close()


def deletar_credencial(credencial_id):
    conn = conectar()
    conn.execute("DELETE FROM credenciais_avisos WHERE credencial_id=?", (credencial_id,))
    conn.execute("DELETE FROM credenciais WHERE id=?", (credencial_id,))
    conn.commit()
    conn.close()


def toggle_silenciar_credencial(credencial_id):
    conn = conectar()
    conn.execute(
        "UPDATE credenciais SET silenciado = CASE WHEN silenciado=1 THEN 0 ELSE 1 END WHERE id=?",
        (credencial_id,)
    )
    conn.commit()
    silenciado = conn.execute("SELECT silenciado FROM credenciais WHERE id=?", (credencial_id,)).fetchone()
    conn.close()
    return bool(silenciado['silenciado']) if silenciado else False


def registrar_aviso_credencial(credencial_id, tipo_aviso):
    """Registra que um aviso foi enviado. Retorna True se inseriu (novo), False se já existia."""
    conn = conectar()
    try:
        conn.execute(
            "INSERT INTO credenciais_avisos (credencial_id, tipo_aviso) VALUES (?,?)",
            (credencial_id, tipo_aviso)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def listar_usuarios_com_flag(flag_col):
    """Retorna lista de {id, nome} de usuários com o flag ativo (1)."""
    _cols_validas = {
        'recebe_aviso_escritural', 'recebe_aviso_melhorias',
        'recebe_aviso_credenciais', 'pode_enviar_notificacao',
        'pode_descriptografar',
    }
    if flag_col not in _cols_validas:
        return []
    conn = conectar()
    rows = conn.execute(f"SELECT id, nome FROM usuarios WHERE {flag_col}=1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Descriptografia de credenciais ────────────────────────────────────────────

def _decrypt_raw(s: str, key: int) -> str:
    C1 = 76541
    C2 = 84529
    result = ""
    key = key % 65536
    i = 0
    while i < len(s) - 1:
        x = int(s[i:i+2], 16)
        decrypted_byte = x ^ (key >> 8)
        result += chr(decrypted_byte)
        key = ((x + key) * C1 + C2) % 65536
        i += 2
    return result


def descriptografar_valor(valor: str) -> str:
    try:
        return _decrypt_raw(valor, 45857)
    except Exception as e:
        return f"[erro: {e}]"


def _encrypt_raw(s: str, key: int) -> str:
    """Mesma cifra de _decrypt_raw, sentido inverso — porte do SZCRC32.Encrypt (Delphi)."""
    C1 = 76541
    C2 = 84529
    key = key % 65536
    result = ""
    for ch in s:
        plain_byte = ord(ch) & 0xFF
        xored = plain_byte ^ (key >> 8)
        result += format(xored & 0xFF, '02X')
        key = ((xored & 0xFF) + key) * C1 + C2
        key = key % 65536
    return result


def criptografar_valor(valor: str) -> str:
    return _encrypt_raw(valor, 45857)


def criar_solicitacao_descriptografia(solicitante_id: int, solicitante_nome: str,
                                      client_id_enc: str, client_secret_enc: str) -> int:
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = conectar()
    try:
        # Cancela solicitações anteriores pendentes do mesmo usuário
        conn.execute(
            "UPDATE solicitacoes_descriptografia SET status='cancelado' WHERE solicitante_id=? AND status='pendente'",
            (solicitante_id,)
        )
        cur = conn.execute(
            "INSERT INTO solicitacoes_descriptografia "
            "(solicitante_id,solicitante_nome,client_id_enc,client_secret_enc,status,criado_em) "
            "VALUES (?,?,?,?,?,?)",
            (solicitante_id, solicitante_nome, client_id_enc, client_secret_enc, 'pendente', agora)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def listar_solicitacoes_descriptografia(status: str | None = None) -> list:
    conn = conectar()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM solicitacoes_descriptografia WHERE status=? ORDER BY id DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM solicitacoes_descriptografia ORDER BY id DESC LIMIT 50"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def buscar_ultima_solicitacao_usuario(usuario_id: int) -> dict | None:
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT * FROM solicitacoes_descriptografia WHERE solicitante_id=? ORDER BY id DESC LIMIT 1",
            (usuario_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def aprovar_solicitacao_descriptografia(id_sol: int, aprovado_por: str):
    """Retorna dict com solicitante_id e solicitante_nome, ou None se não encontrado."""
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT * FROM solicitacoes_descriptografia WHERE id=? AND status='pendente'",
            (id_sol,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        client_id_dec     = descriptografar_valor(d['client_id_enc'])
        client_secret_dec = descriptografar_valor(d['client_secret_enc'])
        agora     = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        expira_em = (datetime.now() + timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "UPDATE solicitacoes_descriptografia SET status='aprovado',client_id_dec=?,"
            "client_secret_dec=?,aprovado_por=?,respondido_em=?,expira_em=? WHERE id=?",
            (client_id_dec, client_secret_dec, aprovado_por, agora, expira_em, id_sol)
        )
        conn.commit()
        return {'solicitante_id': d['solicitante_id'], 'solicitante_nome': d['solicitante_nome']}
    finally:
        conn.close()


def negar_solicitacao_descriptografia(id_sol: int, negado_por: str):
    """Retorna dict com solicitante_id e solicitante_nome, ou None se não encontrado."""
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT solicitante_id, solicitante_nome FROM solicitacoes_descriptografia WHERE id=? AND status='pendente'",
            (id_sol,)
        ).fetchone()
        if not row:
            return None
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "UPDATE solicitacoes_descriptografia SET status='negado',aprovado_por=?,respondido_em=? WHERE id=?",
            (negado_por, agora, id_sol)
        )
        conn.commit()
        return {'solicitante_id': row[0], 'solicitante_nome': row[1]}
    finally:
        conn.close()


def limpar_solicitacoes_expiradas():
    """Marca como expirado qualquer solicitação aprovada cujo expira_em já passou."""
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = conectar()
    try:
        conn.execute(
            "UPDATE solicitacoes_descriptografia SET status='expirado' "
            "WHERE status='aprovado' AND expira_em IS NOT NULL AND expira_em <= ?",
            (agora,)
        )
        conn.commit()
    finally:
        conn.close()


# ── Aprovação de exclusões por master ─────────────────────────────────────────

def migrar_solicitacoes_exclusao():
    conn = conectar()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes_exclusao (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo             TEXT    NOT NULL,
                chave            TEXT    NOT NULL,
                descricao        TEXT    NOT NULL,
                tela_origem      TEXT,
                solicitante_id   INTEGER NOT NULL,
                solicitante_nome TEXT    NOT NULL,
                status           TEXT    NOT NULL DEFAULT 'pendente',
                aprovado_por     TEXT,
                motivo_negacao   TEXT,
                criado_em        TEXT    NOT NULL,
                respondido_em    TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def criar_solicitacao_exclusao(tipo: str, chave: str, descricao: str, tela_origem: str,
                                solicitante_id: int, solicitante_nome: str) -> int:
    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = conectar()
    try:
        cur = conn.execute(
            "INSERT INTO solicitacoes_exclusao "
            "(tipo,chave,descricao,tela_origem,solicitante_id,solicitante_nome,status,criado_em) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (tipo, chave, descricao, tela_origem, solicitante_id, solicitante_nome, 'pendente', agora)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def listar_solicitacoes_exclusao(status: str | None = None) -> list:
    conn = conectar()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM solicitacoes_exclusao WHERE status=? ORDER BY id DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM solicitacoes_exclusao ORDER BY id DESC LIMIT 100"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def contar_solicitacoes_exclusao_pendentes() -> int:
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM solicitacoes_exclusao WHERE status='pendente'"
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def aprovar_solicitacao_exclusao(id_sol: int, aprovado_por: str):
    """Executa a exclusão de fato e marca a solicitação como aprovada.
    Retorna dict com solicitante_id, solicitante_nome e descricao, ou None se não encontrada/já respondida."""
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT * FROM solicitacoes_exclusao WHERE id=? AND status='pendente'",
            (id_sol,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        executor = EXECUTORES_EXCLUSAO.get(d['tipo'])
        if executor is None:
            return None
        executor(d['chave'])
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "UPDATE solicitacoes_exclusao SET status='aprovado',aprovado_por=?,respondido_em=? WHERE id=?",
            (aprovado_por, agora, id_sol)
        )
        conn.commit()
        return {'solicitante_id': d['solicitante_id'], 'solicitante_nome': d['solicitante_nome'],
                'descricao': d['descricao']}
    finally:
        conn.close()


def negar_solicitacao_exclusao(id_sol: int, negado_por: str, motivo: str | None = None):
    """Retorna dict com solicitante_id, solicitante_nome e descricao, ou None se não encontrada/já respondida."""
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT * FROM solicitacoes_exclusao WHERE id=? AND status='pendente'",
            (id_sol,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "UPDATE solicitacoes_exclusao SET status='negado',aprovado_por=?,motivo_negacao=?,respondido_em=? WHERE id=?",
            (negado_por, motivo, agora, id_sol)
        )
        conn.commit()
        return {'solicitante_id': d['solicitante_id'], 'solicitante_nome': d['solicitante_nome'],
                'descricao': d['descricao']}
    finally:
        conn.close()


def listar_masters() -> list:
    conn = conectar()
    try:
        rows = conn.execute("SELECT id, nome FROM usuarios WHERE nivel='master'").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# Registro de qual função executa a exclusão de fato para cada "tipo" de
# solicitação. Definido no fim do arquivo pois depende de todas as funções
# remover_*/deletar_* já estarem declaradas acima.
EXECUTORES_EXCLUSAO = {
    'tecnico':           remover_tecnico,
    'usuario':           remover_usuario,
    'status':            remover_status,
    'status_escritural': remover_status_escritural,
    'servico':           remover_servico,
    'setor':             remover_setor,
    'banco_cadastro':    remover_banco_cadastro,
    'melhoria':          remover_melhoria,
    'melhoria_imagem':   remover_imagem_melhoria,
    'sla_servico':       remover_sla_servico,
    'sla_aviso':         remover_sla_aviso,
    'pendente':          deletar_pendente,
    'escritural':        deletar_escritural,
    'cancelado':         deletar_cancelado,
    'hom_cobranca':      deletar_homologado_cobranca,
    'hom_pagamentos':    deletar_homologado_pagamentos,
    'hom_extrato':       deletar_homologado_extrato,
    'hom_ext_bancario':  deletar_homologado_ext_bancario,
    'ajuda_topico':      remover_ajuda_topico,
    'ajuda_post':        remover_ajuda_post,
    'ajuda_collection':  remover_collection,
    'hub_banco':         hub_remover_banco,
    'hub_instrucao':     hub_remover_instrucao,
    'hub_categoria':     hub_remover_categoria,
    'hub_servico':       hub_remover_servico,
    'email_modelo':      remover_email_modelo,
    'credencial':        deletar_credencial,
}
