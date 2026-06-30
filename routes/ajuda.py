import re
from collections import Counter
from html import escape
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import banco
from utils import checar_tela, checar_admin

ajuda_bp = Blueprint('ajuda', __name__)


# ── Conversão de PDF para HTML ────────────────────────────

_MARCADORES_LISTA = ('-', '•', '*', '–')


def _eh_item_lista(linha: str) -> bool:
    return linha.startswith(_MARCADORES_LISTA) or bool(re.match(r'^\d+[.\)]\s', linha))


def _pdf_para_html(arquivo) -> str:
    """Extrai o texto de um PDF preservando a estrutura visual (parágrafos, títulos
    e listas) e monta um HTML simples, para servir de ponto de partida no editor —
    o usuário revisa e corrige depois.

    Usa o PyMuPDF (fitz) em vez do pypdf: ele devolve cada linha já com as
    palavras corretamente espaçadas (o pypdf, em PDFs justificados/colunados,
    pode devolver quase uma palavra por linha) e também o tamanho de fonte de
    cada trecho, o que permite detectar títulos pelo tamanho em vez de
    heurísticas frágeis de maiúsculas. Parágrafos são separados pelo próprio
    agrupamento em blocos de texto do PDF e por saltos verticais maiores que o
    normal entre linhas (indicando espaçamento entre parágrafos)."""
    import fitz
    doc = fitz.open(stream=arquivo.read(), filetype='pdf')

    try:
        tamanhos = Counter()
        for page in doc:
            for bloco in page.get_text('dict')['blocks']:
                if bloco['type'] != 0:
                    continue
                for linha in bloco['lines']:
                    for span in linha['spans']:
                        texto = span['text'].strip()
                        if texto:
                            tamanhos[round(span['size'])] += len(texto)
        tamanho_corpo = tamanhos.most_common(1)[0][0] if tamanhos else 11

        blocos_html = []  # [(tipo, texto)] tipo em 'h2'/'h3' (título), 'li' (lista) ou 'p' (parágrafo)
        buffer = []
        ultimo_y_fim = None
        ultima_altura = None

        def flush():
            if buffer:
                blocos_html.append(('p', ' '.join(buffer)))
                buffer.clear()

        for page in doc:
            for bloco in page.get_text('dict')['blocks']:
                if bloco['type'] != 0:
                    continue  # ignora imagens/figuras

                for linha in bloco['lines']:
                    spans = [s for s in linha['spans'] if s['text'].strip()]
                    if not spans:
                        continue

                    texto_linha = re.sub(r'\s+', ' ', ''.join(s['text'] for s in spans)).strip()
                    if not texto_linha:
                        continue

                    tam_linha = round(max(s['size'] for s in spans))
                    negrito = any('bold' in s['font'].lower() for s in spans)
                    y0, y1 = linha['bbox'][1], linha['bbox'][3]
                    altura = y1 - y0

                    gap_grande = (
                        ultimo_y_fim is not None and ultima_altura
                        and (y0 - ultimo_y_fim) > ultima_altura * 0.6
                    )
                    if gap_grande:
                        flush()
                    ultimo_y_fim, ultima_altura = y1, altura

                    if _eh_item_lista(texto_linha):
                        flush()
                        item = re.sub(r'^([-•*–]|\d+[.\)])\s*', '', texto_linha)
                        blocos_html.append(('li', escape(item)))
                        continue

                    eh_titulo = (
                        not buffer and len(texto_linha) <= 90
                        and (tam_linha >= tamanho_corpo + 3 or (negrito and tam_linha >= tamanho_corpo + 1))
                    )
                    if eh_titulo:
                        nivel = 'h2' if tam_linha >= tamanho_corpo + 6 else 'h3'
                        blocos_html.append((nivel, escape(texto_linha)))
                        continue

                    buffer.append(texto_linha)

                flush()  # fim do bloco do PDF -> normalmente fim do parágrafo
            flush()  # quebra de página -> fim do parágrafo

        partes_html = []
        i = 0
        while i < len(blocos_html):
            tipo, texto = blocos_html[i]
            if tipo == 'li':
                itens = []
                while i < len(blocos_html) and blocos_html[i][0] == 'li':
                    itens.append(blocos_html[i][1])
                    i += 1
                itens_html = ''.join(f'<li>{item}</li>' for item in itens)
                partes_html.append(f'<ul>{itens_html}</ul>')
            elif tipo in ('h2', 'h3'):
                partes_html.append(f'<{tipo}>{texto}</{tipo}>')
                i += 1
            else:
                partes_html.append(f'<p>{escape(texto)}</p>')
                i += 1

        return '\n'.join(partes_html) if partes_html else '<p></p>'
    finally:
        doc.close()


# ── Visualização (tela-gated) ─────────────────────────────

@ajuda_bp.route('/ajuda')
def aba_ajuda():
    bloqueio = checar_tela('ajuda')
    if bloqueio:
        return bloqueio
    topicos = banco.listar_ajuda_completo()
    return render_template('aba_ajuda.html', topicos=topicos)


@ajuda_bp.route('/ajuda/post/<int:id_post>')
def ver_ajuda_post(id_post):
    bloqueio = checar_tela('ajuda')
    if bloqueio:
        return bloqueio
    post = banco.buscar_ajuda_post(id_post)
    if not post:
        return redirect(url_for('ajuda.aba_ajuda'))
    topico = next((t for t in banco.listar_ajuda_topicos() if t['id'] == post['topico_id']), None)
    return render_template('ajuda_post_view.html', post=post, topico=topico)


# ── Gerenciamento (admin/master, tela separada) ───────────

@ajuda_bp.route('/ajuda/gerenciar')
def ajuda_gerenciar():
    bloqueio = checar_admin()
    if bloqueio:
        return bloqueio
    topicos = banco.listar_ajuda_completo()
    return render_template('ajuda_gerenciar.html', topicos=topicos)


@ajuda_bp.route('/ajuda/gerenciar/post/novo')
def ajuda_post_novo():
    bloqueio = checar_admin()
    if bloqueio:
        return bloqueio
    topico_id = request.args.get('topico_id', type=int)
    return render_template(
        'ajuda_post_form.html',
        post=None,
        topicos=banco.listar_ajuda_topicos(),
        topico_id_preselecionado=topico_id,
    )


@ajuda_bp.route('/ajuda/gerenciar/post/<int:id_post>/editar')
def ajuda_post_editar(id_post):
    bloqueio = checar_admin()
    if bloqueio:
        return bloqueio
    post = banco.buscar_ajuda_post(id_post)
    if not post:
        return redirect(url_for('ajuda.ajuda_gerenciar'))
    return render_template(
        'ajuda_post_form.html',
        post=post,
        topicos=banco.listar_ajuda_topicos(),
        topico_id_preselecionado=None,
    )


# ── API: Tópicos ───────────────────────────────────────────

@ajuda_bp.route('/api/ajuda/topicos', methods=['POST'])
def api_adicionar_topico():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'Informe o nome do tópico.'}), 400
    novo_id = banco.adicionar_ajuda_topico(nome, d.get('ordem', 99))
    return jsonify({'sucesso': True, 'id': novo_id})


@ajuda_bp.route('/api/ajuda/topicos/<int:id_topico>', methods=['PUT'])
def api_atualizar_topico(id_topico):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    nome = (d.get('nome') or '').strip()
    if not nome:
        return jsonify({'erro': 'Informe o nome do tópico.'}), 400
    banco.atualizar_ajuda_topico(id_topico, nome, d.get('ordem', 99))
    return jsonify({'sucesso': True})


@ajuda_bp.route('/api/ajuda/topicos/<int:id_topico>', methods=['DELETE'])
def api_remover_topico(id_topico):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_ajuda_topico(id_topico)
    return jsonify({'sucesso': True})


# ── API: Posts ─────────────────────────────────────────────

@ajuda_bp.route('/api/ajuda/posts', methods=['POST'])
def api_adicionar_post():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    if not (d.get('titulo') or '').strip():
        return jsonify({'erro': 'Informe o título.'}), 400
    if not d.get('topico_id'):
        return jsonify({'erro': 'Selecione um tópico.'}), 400
    novo_id = banco.adicionar_ajuda_post(d, criado_por=session.get('nome', ''))
    return jsonify({'sucesso': True, 'id': novo_id})


@ajuda_bp.route('/api/ajuda/posts/<int:id_post>', methods=['PUT'])
def api_atualizar_post(id_post):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    d = request.get_json() or {}
    if not (d.get('titulo') or '').strip():
        return jsonify({'erro': 'Informe o título.'}), 400
    if not d.get('topico_id'):
        return jsonify({'erro': 'Selecione um tópico.'}), 400
    banco.atualizar_ajuda_post(id_post, d)
    return jsonify({'sucesso': True})


@ajuda_bp.route('/api/ajuda/posts/<int:id_post>', methods=['DELETE'])
def api_remover_post(id_post):
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    banco.remover_ajuda_post(id_post)
    return jsonify({'sucesso': True})


# ── API: Upload de PDF (converte para HTML) ───────────────

@ajuda_bp.route('/api/ajuda/upload-pdf', methods=['POST'])
def api_upload_pdf():
    if checar_admin():
        return jsonify({'erro': 'Sem permissão'}), 403
    arquivo = request.files.get('arquivo')
    if not arquivo or not arquivo.filename.lower().endswith('.pdf'):
        return jsonify({'erro': 'Envie um arquivo PDF.'}), 400
    try:
        html = _pdf_para_html(arquivo)
    except Exception:
        return jsonify({'erro': 'Não foi possível ler esse PDF. Ele pode estar protegido ou ser uma imagem escaneada.'}), 400

    titulo_sugerido = re.sub(r'\.pdf$', '', arquivo.filename, flags=re.IGNORECASE).strip()
    return jsonify({'sucesso': True, 'html': html, 'titulo_sugerido': titulo_sugerido})
