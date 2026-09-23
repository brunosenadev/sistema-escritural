"""
exclusoes.py — Orquestra o fluxo de aprovação de exclusões por master.

Usuários master excluem direto (comportamento atual). Qualquer outro
usuário que tenha permissão de excluir numa tela vira uma solicitação
pendente, visível em /solicitacoes-exclusao, até um master aprovar ou negar.
"""

from flask import session
import banco


def eh_master() -> bool:
    return session.get('nivel_acesso') == 'master'


def processar_exclusao(tipo: str, chave, descricao: str, tela_origem: str, log_fn):
    """
    tipo: chave em banco.EXECUTORES_EXCLUSAO
    chave: id/nome/texto que a função de exclusão espera
    descricao: texto legível pro master entender o que está sendo apagado
    tela_origem: nome da tela de origem (log e link da notificação)
    log_fn: callable(acao: str, descricao: str) -> None — adaptador pro
            helper `_log` local de cada blueprint de rotas.

    Retorna (payload_json: dict, status_http: int).
    """
    if eh_master():
        banco.EXECUTORES_EXCLUSAO[tipo](chave)
        log_fn('DELETOU', descricao)
        return {'sucesso': True}, 200

    uid  = session.get('id_usuario')
    nome = session.get('nome') or session.get('usuario', '')
    id_sol = banco.criar_solicitacao_exclusao(tipo, str(chave), descricao, tela_origem, uid, nome)

    for m in banco.listar_masters():
        banco.criar_notificacao(
            m['id'],
            'Solicitação de exclusão',
            f'{nome} solicitou exclusão: {descricao}',
            'aviso',
            link='/solicitacoes-exclusao',
        )

    log_fn('SOLICITOU_EXCLUSAO', descricao)
    return {
        'sucesso': False,
        'pendente': True,
        'mensagem': 'Exclusão enviada para aprovação de um master.',
    }, 202
