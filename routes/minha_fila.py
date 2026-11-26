import threading
import time
from datetime import datetime

from flask import Blueprint, render_template, request, session
import banco
from utils import checar_tela, tem_acesso_tela

minha_fila_bp = Blueprint('minha_fila', __name__)


@minha_fila_bp.route('/minha-fila')
def aba_minha_fila():
    bloqueio = checar_tela('minha_fila')
    if bloqueio:
        return bloqueio

    ve_todos  = session.get('nivel_acesso') in ('admin', 'master')
    tec_logado = (session.get('tecnico_vinculado') or '').strip()

    # admin/master escolhe de quem ver a fila; '' na URL = todos os técnicos
    tecnico = tec_logado or None
    if ve_todos and 'tecnico' in request.args:
        tecnico = request.args.get('tecnico') or None

    sem_tecnico = not ve_todos and not tec_logado
    fila = banco.montar_minha_fila(tecnico) if not sem_tecnico else \
        {'agora': [], 'retomar': [], 'aguardando': [], 'adiados': []}

    dono = banco.buscar_usuario_por_tecnico(tecnico) if tecnico else None
    if tecnico == tec_logado:
        dono = {'id': session.get('id_usuario')}

    return render_template(
        'aba_minha_fila.html',
        fila=fila,
        tecnico=tecnico,
        ve_todos=ve_todos,
        sem_tecnico=sem_tecnico,
        lista_tecnicos=banco.listar_tecnicos() if ve_todos else [],
        lista_status=banco.listar_status(),
        lista_servicos_mapa={s['texto']: s['destino_homologado'] for s in banco.listar_servicos_completo()},
        cores_tecnicos=banco.cores_por_tecnico(),
        homologados_hoje=banco.contar_homologados_hoje(dono['id']) if dono else None,
        os_abertas=banco.contar_os_abertas(tecnico) if tecnico else banco.contar_os_abertas(),
        acesso_os=tem_acesso_tela('controle_os'),
        acesso_pendente=tem_acesso_tela('pendente'),
    )


# ── Avisos dos agendamentos (notificação do sistema: sininho, som e alerta na tela) ──
# Para cada agendamento do dia: um aviso no início do dia (config 'fila_aviso_inicio')
# e, se tiver hora, outro 30 minutos antes. O que já foi avisado fica em retomar_avisos.

def _minutos(hhmm):
    h, m = hhmm.split(':')
    return int(h) * 60 + int(m)


def checar_avisos_agenda(agora=None):
    agora = agora or datetime.now()
    hoje, hhmm = agora.date().isoformat(), agora.strftime('%H:%M')
    inicio = banco.get_config('fila_aviso_inicio', '08:00') or '08:00'
    enviados = []
    for p in banco.listar_agendamentos_do_dia(hoje):
        antes = p.get('retomar_avisos') or ''
        feitos = set(filter(None, antes.split(',')))
        hora = (p.get('retomar_hora') or '').strip()
        faltam = _minutos(hora) - _minutos(hhmm) if hora else None
        na_janela_30 = faltam is not None and faltam <= 30

        if hora and '30' not in feitos and na_janela_30:
            if faltam < 0:  # a hora já passou (servidor estava desligado): não adianta mais avisar
                banco.marcar_aviso_retomar(p['id'], antes, 'dia,30')
                continue
            tipo, depois = '30', 'dia,30'  # o aviso de 30 min substitui o do início do dia
        elif 'dia' not in feitos and hhmm >= inicio and not na_janela_30:
            tipo, depois = 'dia', ','.join(sorted(feitos | {'dia'}))
        else:
            continue
        if not banco.marcar_aviso_retomar(p['id'], antes, depois):
            continue  # outro processo já avisou

        empresa = p.get('empresa') or '—'
        detalhe = f"{p.get('banco') or '—'} · {p.get('servico') or '—'}"
        nota = (p.get('retomar_nota') or '').strip()
        if tipo == '30':
            titulo = f'⏰ Em {faltam} min ({hora}): {empresa}'
        elif hora:
            titulo = f'📅 Hoje às {hora}: {empresa}'
        else:
            titulo = f'📅 Retorno agendado para hoje: {empresa}'

        # shortcut: só avisa o usuário vinculado ao técnico do registro; sem vínculo, ninguém recebe
        obs = ' '.join((p.get('obs') or '').split())
        if len(obs) > 280:
            obs = obs[:277] + '...'
        # uma informação por linha; o alerta da tela (base.html) mostra cada linha com seu rótulo
        linhas = ([f'Lembrete: {nota}'] if nota else []) + ([f'Obs.: {obs}'] if obs else []) + [detalhe]
        dono = banco.buscar_usuario_por_tecnico(p['tecnico']) if p.get('tecnico') else None
        if dono:
            # o link "?abrir=" marca a notificação como aviso de agendamento e abre o card na Minha Fila
            banco.criar_notificacao(dono['id'], titulo, '\n'.join(linhas), 'aviso', f"/minha-fila?abrir={p['id']}")
        enviados.append((p['id'], tipo))
    return enviados


def _loop_avisos():
    time.sleep(20)
    while True:
        try:
            checar_avisos_agenda()
        except Exception:
            pass
        time.sleep(60)


def iniciar_avisos_agenda():
    threading.Thread(target=_loop_avisos, daemon=True, name='minha-fila-avisos').start()
