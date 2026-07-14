from flask import Blueprint, render_template, jsonify, session, request
import banco
from utils import checar_tela, usuario_logado, tem_acesso_tela

sla_bp = Blueprint('sla', __name__)


@sla_bp.route('/sla-dashboard')
def pagina_sla_dashboard():
    bloqueio = checar_tela('sla_dashboard')
    if bloqueio:
        return bloqueio
    uid = session.get('id_usuario')
    banco.verificar_e_notificar_sla(uid)
    tecnicos = banco.listar_tecnicos()
    servicos = banco.listar_servicos()
    sla_conf = banco.listar_sla_config()
    notif_pref = banco.listar_notif_pref_usuario(uid)
    setores = banco.listar_setores()
    setores_notif = banco.get_sla_setores_notif()
    return render_template(
        'sla_dashboard.html',
        tecnicos=tecnicos,
        servicos=servicos,
        sla_conf=sla_conf,
        notif_pref=notif_pref,
        setores=setores,
        setores_notif=setores_notif,
    )


@sla_bp.route('/api/sla/resumo')
def api_sla_resumo():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not tem_acesso_tela('sla_dashboard'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.resumo_sla())


@sla_bp.route('/api/sla/pendentes')
def api_sla_pendentes():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    if not tem_acesso_tela('sla_dashboard'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.calcular_sla_pendentes())


@sla_bp.route('/api/sla-notif-setores', methods=['GET'])
def api_get_sla_setores():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    return jsonify({'setores': banco.get_sla_setores_notif()})


@sla_bp.route('/api/sla-notif-setores', methods=['POST'])
def api_set_sla_setores():
    if not usuario_logado() or session.get('nivel_acesso') not in ('admin', 'master'):
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    setores = [str(s).strip() for s in (d.get('setores') or []) if str(s).strip()]
    banco.set_sla_setores_notif(setores)
    return jsonify({'sucesso': True})
