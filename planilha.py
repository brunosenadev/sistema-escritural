"""
planilha.py — Leitura e escrita de arquivos Excel.
A planilha agora é usada apenas para importar/exportar dados.
A fonte de verdade é o banco de dados (banco.py).
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

# ── Colunas da aba Pendente (índice 1-based) ─────────────
COLUNA_TECNICO     = 1   # A
COLUNA_EMPRESA     = 2   # B
COLUNA_SERVICO     = 3   # C
COLUNA_BANCO       = 4   # D
COLUNA_DT_SOLICITA = 5   # E
COLUNA_DT_STATUS   = 6   # F
COLUNA_STATUS      = 7   # G
COLUNA_OBS         = 8   # H

LINHA_INICIO_DADOS = 3   # Linha onde os dados começam (após cabeçalho + ano)


def _encontrar_aba(workbook, *palavras_chave):
    """Localiza uma aba no workbook pelo nome (case-insensitive, múltiplas palavras-chave)."""
    for nome in workbook.sheetnames:
        n = nome.lower()
        if all(p in n for p in palavras_chave):
            return workbook[nome]
    return None


def _encontrar_aba_pendente(workbook):
    for nome in workbook.sheetnames:
        if 'pendente' in nome.lower():
            return workbook[nome]
    return None


def _formatar_data(valor_celula):
    """Converte data de célula Excel para string dd/mm/aaaa."""
    if isinstance(valor_celula, datetime):
        return valor_celula.strftime('%d/%m/%Y')
    return str(valor_celula or '').strip()


def ler_pendentes_do_excel(caminho_arquivo):
    """
    Lê a aba Pendente de um arquivo Excel e retorna uma lista de dicts.
    Linhas completamente vazias são ignoradas.
    """
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
    except Exception as e:
        print(f'[planilha] Erro ao abrir arquivo: {e}')
        return []

    aba = _encontrar_aba_pendente(wb)
    if not aba:
        print('[planilha] Aba Pendente não encontrada. Abas disponíveis:', wb.sheetnames)
        return []

    registros = []
    for num_linha in range(LINHA_INICIO_DADOS, aba.max_row + 1):
        tecnico = aba.cell(num_linha, COLUNA_TECNICO).value
        empresa = aba.cell(num_linha, COLUNA_EMPRESA).value
        servico = aba.cell(num_linha, COLUNA_SERVICO).value
        banco   = aba.cell(num_linha, COLUNA_BANCO).value
        status  = aba.cell(num_linha, COLUNA_STATUS).value

        # Ignora linhas sem nenhum campo principal
        if not any([tecnico, empresa, servico, banco, status]):
            continue

        registros.append({
            'tecnico':     str(tecnico or '').strip(),
            'empresa':     str(empresa or '').strip(),
            'servico':     str(servico or '').strip(),
            'banco':       str(banco   or '').strip(),
            'dt_solicita': _formatar_data(aba.cell(num_linha, COLUNA_DT_SOLICITA).value),
            'dt_status':   _formatar_data(aba.cell(num_linha, COLUNA_DT_STATUS).value),
            'status':      str(status  or '').strip(),
            'obs':         str(aba.cell(num_linha, COLUNA_OBS).value or '').strip(),
        })

    return registros


def exportar_pendentes_para_excel(registros, caminho_destino):
    """
    Gera um arquivo Excel com os registros da aba Pendente.
    Aplica formatação básica no cabeçalho.
    Retorna o caminho do arquivo gerado.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pendente'

    # Cabeçalho
    cabecalhos = ['TÉCNICO', 'EMPRESA', 'SERVIÇO', 'BANCO', 'DT.SOLICITA', 'DT.STATUS', 'STATUS', 'OBS']
    estilo_cab = Font(bold=True, color='FFFFFF')
    fundo_cab  = PatternFill(fill_type='solid', fgColor='0A1628')

    for col, texto in enumerate(cabecalhos, 1):
        celula = ws.cell(1, col, texto)
        celula.font      = estilo_cab
        celula.fill      = fundo_cab
        celula.alignment = Alignment(horizontal='center', vertical='center')

    # Dados
    for idx, reg in enumerate(registros, 2):
        ws.cell(idx, COLUNA_TECNICO).value     = reg.get('tecnico', '')
        ws.cell(idx, COLUNA_EMPRESA).value     = reg.get('empresa', '')
        ws.cell(idx, COLUNA_SERVICO).value     = reg.get('servico', '')
        ws.cell(idx, COLUNA_BANCO).value       = reg.get('banco', '')
        ws.cell(idx, COLUNA_DT_SOLICITA).value = reg.get('dt_solicita', '')
        ws.cell(idx, COLUNA_DT_STATUS).value   = reg.get('dt_status', '')
        ws.cell(idx, COLUNA_STATUS).value      = reg.get('status', '')
        ws.cell(idx, COLUNA_OBS).value         = reg.get('obs', '')

    # Largura das colunas
    larguras = [14, 30, 16, 20, 14, 14, 26, 40]
    for col, larg in enumerate(larguras, 1):
        ws.column_dimensions[ws.cell(1, col).column_letter].width = larg

    wb.save(caminho_destino)
    return caminho_destino


def ler_planilha_completa(caminho_arquivo):
    """
    Abre o workbook UMA vez e lê todas as abas relevantes.
    Retorna dict: {pendente, cobranca, pagamentos, extrato, cancelados}
    Cada valor é uma lista de dicts (vazia se a aba não for encontrada).
    """
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
    except Exception as e:
        print(f'[planilha] Erro ao abrir arquivo: {e}')
        return {}

    print('[planilha] Abas encontradas:', wb.sheetnames)

    resultado = {
        'pendente':   [],
        'cobranca':   [],
        'pagamentos': [],
        'extrato':    [],
        'cancelados': [],
    }

    aba_p = _encontrar_aba_pendente(wb)
    if aba_p:
        resultado['pendente'] = _ler_aba_pendente_sheet(aba_p)

    aba_c = _encontrar_aba(wb, 'cobran')
    if aba_c:
        resultado['cobranca'] = _ler_aba_homologados(aba_c)

    # Exige 'homolog' no nome para não cair na aba "API Pagamentos"
    aba_pg = _encontrar_aba(wb, 'homolog', 'pag')
    if aba_pg:
        resultado['pagamentos'] = _ler_aba_homologados(aba_pg)

    aba_ex = _encontrar_aba(wb, 'extrat')
    if aba_ex:
        resultado['extrato'] = _ler_aba_homologados(aba_ex)

    aba_can = _encontrar_aba(wb, 'cancel')
    if aba_can:
        resultado['cancelados'] = _ler_cancelados_sheet(aba_can)

    return resultado


def _e_linha_separadora(empresa, servico, banco):
    """Retorna True se a linha for um separador de ano/seção (sem empresa, serviço e banco)."""
    return not empresa and not servico and not banco


def _ler_aba_pendente_sheet(aba):
    """Lê uma aba já aberta com estrutura de Pendente."""
    registros = []
    for num_linha in range(LINHA_INICIO_DADOS, aba.max_row + 1):
        tecnico = aba.cell(num_linha, COLUNA_TECNICO).value
        empresa = aba.cell(num_linha, COLUNA_EMPRESA).value
        servico = aba.cell(num_linha, COLUNA_SERVICO).value
        banco   = aba.cell(num_linha, COLUNA_BANCO).value
        status  = aba.cell(num_linha, COLUNA_STATUS).value
        # Pula linhas completamente vazias ou separadores de ano/seção
        if not any([tecnico, empresa, servico, banco, status]):
            continue
        if _e_linha_separadora(empresa, servico, banco):
            continue
        registros.append({
            'tecnico':     str(tecnico or '').strip(),
            'empresa':     str(empresa or '').strip(),
            'servico':     str(servico or '').strip(),
            'banco':       str(banco   or '').strip(),
            'dt_solicita': _formatar_data(aba.cell(num_linha, COLUNA_DT_SOLICITA).value),
            'dt_status':   _formatar_data(aba.cell(num_linha, COLUNA_DT_STATUS).value),
            'status':      str(status  or '').strip(),
            'obs':         str(aba.cell(num_linha, COLUNA_OBS).value or '').strip(),
        })
    return registros


def _ler_cancelados_sheet(aba):
    """Lê uma aba já aberta com estrutura de Cancelados."""
    registros = []
    for num_linha in range(LINHA_INICIO_DADOS, aba.max_row + 1):
        row = {campo: aba.cell(num_linha, col).value for campo, col in _COL_CAN.items()}
        if not any(row[c] for c in ('tecnico', 'empresa', 'servico', 'banco', 'status')):
            continue
        if _e_linha_separadora(row['empresa'], row['servico'], row['banco']):
            continue
        registros.append({
            'tecnico':       str(row['tecnico']       or '').strip(),
            'empresa':       str(row['empresa']       or '').strip(),
            'servico':       str(row['servico']       or '').strip(),
            'banco':         str(row['banco']         or '').strip(),
            'carteira':      str(row['carteira']      or '').strip(),
            'conta':         str(row['conta']         or '').strip(),
            'dt_solicita':   _formatar_data(row['dt_solicita']),
            'dt_status':     _formatar_data(row['dt_status']),
            'status':        str(row['status']        or 'CANCELADO').strip(),
            'retorno':       str(row['retorno']       or '').strip(),
            'ordem_servico': str(row['ordem_servico'] or '').strip(),
            'obs':           str(row['obs']           or '').strip(),
        })
    return registros


# ── Colunas comuns das abas Homologados (mesma estrutura de Pendente) ─────
_COL_HOM = {
    'tecnico':     1,   # A
    'empresa':     2,   # B
    'servico':     3,   # C
    'banco':       4,   # D
    'dt_solicita': 5,   # E
    'dt_status':   6,   # F
    'status':      7,   # G
    'obs':         8,   # H
}

# Colunas extras da aba Cancelados
_COL_CAN = {
    'tecnico':       1,
    'empresa':       2,
    'servico':       3,
    'banco':         4,
    'carteira':      5,
    'conta':         6,
    'dt_solicita':   7,
    'dt_status':     8,
    'status':        9,
    'retorno':      10,
    'ordem_servico':11,
    'obs':          12,
}


def _ler_aba_homologados(aba):
    """Lê linhas de uma aba de homologados (estrutura igual à Pendente)."""
    registros = []
    for num_linha in range(LINHA_INICIO_DADOS, aba.max_row + 1):
        row = {campo: aba.cell(num_linha, col).value for campo, col in _COL_HOM.items()}
        if not any(row[c] for c in ('tecnico', 'empresa', 'servico', 'banco', 'status')):
            continue
        if _e_linha_separadora(row['empresa'], row['servico'], row['banco']):
            continue
        registros.append({
            'tecnico':     str(row['tecnico']     or '').strip(),
            'empresa':     str(row['empresa']     or '').strip(),
            'servico':     str(row['servico']     or '').strip(),
            'banco':       str(row['banco']       or '').strip(),
            'dt_solicita': _formatar_data(row['dt_solicita']),
            'dt_status':   _formatar_data(row['dt_status']),
            'status':      str(row['status']      or 'HOMOLOGADO').strip(),
            'obs':         str(row['obs']         or '').strip(),
        })
    return registros


def ler_homologados_cobranca_do_excel(caminho_arquivo):
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
    except Exception as e:
        print(f'[planilha] Erro ao abrir arquivo: {e}')
        return []
    aba = _encontrar_aba(wb, 'cobran')
    if not aba:
        print('[planilha] Aba Homologados Cobrança não encontrada. Abas:', wb.sheetnames)
        return []
    return _ler_aba_homologados(aba)


def ler_homologados_pagamentos_do_excel(caminho_arquivo):
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
    except Exception as e:
        print(f'[planilha] Erro ao abrir arquivo: {e}')
        return []
    aba = _encontrar_aba(wb, 'pagamento') or _encontrar_aba(wb, 'pagfor') or _encontrar_aba(wb, 'pag')
    if not aba:
        print('[planilha] Aba Homologados Pagamentos não encontrada. Abas:', wb.sheetnames)
        return []
    return _ler_aba_homologados(aba)


def ler_homologados_extrato_do_excel(caminho_arquivo):
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
    except Exception as e:
        print(f'[planilha] Erro ao abrir arquivo: {e}')
        return []
    aba = _encontrar_aba(wb, 'extrat')
    if not aba:
        print('[planilha] Aba Extrato Cartão não encontrada. Abas:', wb.sheetnames)
        return []
    return _ler_aba_homologados(aba)


def ler_cancelados_do_excel(caminho_arquivo):
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
    except Exception as e:
        print(f'[planilha] Erro ao abrir arquivo: {e}')
        return []
    aba = _encontrar_aba(wb, 'cancel')
    if not aba:
        print('[planilha] Aba Cancelados não encontrada. Abas:', wb.sheetnames)
        return []
    registros = []
    for num_linha in range(LINHA_INICIO_DADOS, aba.max_row + 1):
        row = {campo: aba.cell(num_linha, col).value for campo, col in _COL_CAN.items()}
        if not any(row[c] for c in ('tecnico', 'empresa', 'servico', 'banco', 'status')):
            continue
        registros.append({
            'tecnico':       str(row['tecnico']       or '').strip(),
            'empresa':       str(row['empresa']       or '').strip(),
            'servico':       str(row['servico']       or '').strip(),
            'banco':         str(row['banco']         or '').strip(),
            'carteira':      str(row['carteira']      or '').strip(),
            'conta':         str(row['conta']         or '').strip(),
            'dt_solicita':   _formatar_data(row['dt_solicita']),
            'dt_status':     _formatar_data(row['dt_status']),
            'status':        str(row['status']        or 'CANCELADO').strip(),
            'retorno':       str(row['retorno']       or '').strip(),
            'ordem_servico': str(row['ordem_servico'] or '').strip(),
            'obs':           str(row['obs']           or '').strip(),
        })
    return registros
