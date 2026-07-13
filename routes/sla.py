from flask import Blueprint, render_template, jsonify, session
import banco
from utils import checar_tela, usuario_logado

sla_bp = Blueprint('sla', __name__)


@sla_bp.route('/sla-dashboard')
def pagina_sla_dashboard():
    bloqueio = checar_tela('sla_dashboard')
    if bloqueio:
        return bloqueio
    tecnicos = banco.listar_tecnicos()
    servicos = banco.listar_servicos()
    sla_conf = banco.listar_sla_config()
    avisos   = banco.listar_sla_avisos(apenas_ativos=True)
    return render_template(
        'sla_dashboard.html',
        tecnicos=tecnicos,
        servicos=servicos,
        sla_conf=sla_conf,
        avisos=avisos,
    )


@sla_bp.route('/api/sla/resumo')
def api_sla_resumo():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    from utils import tem_acesso_tela
    if not tem_acesso_tela('sla_dashboard'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.resumo_sla())


@sla_bp.route('/api/sla/pendentes')
def api_sla_pendentes():
    if not usuario_logado():
        return jsonify({'erro': 'Não autenticado'}), 401
    from utils import tem_acesso_tela
    if not tem_acesso_tela('sla_dashboard'):
        return jsonify({'erro': 'Sem permissão'}), 403
    return jsonify(banco.calcular_sla_pendentes())
