import re
import datetime
import pandas as pd
import numpy as np

MESES_NOME = {
    "jan": (1, "Janeiro"), "fev": (2, "Fevereiro"), "mar": (3, "Março"),
    "abr": (4, "Abril"), "mai": (5, "Maio"), "jun": (6, "Junho"),
    "jul": (7, "Julho"), "ago": (8, "Agosto"), "set": (9, "Setembro"),
    "out": (10, "Outubro"), "nov": (11, "Novembro"), "dez": (12, "Dezembro")
}


def detectar_mes_arquivo(filename):
    """
    Tenta inferir o mês e o ano a partir do nome do arquivo.
    Retorna uma tupla (mês_num, ano).
    """
    if not filename:
        return None, None
    filename_lower = filename.lower()

    # 1. Procurar por padrão ISO YYYY-MM ou YYYY_MM (ex: 2026-05)
    iso_match = re.search(r"\b(20\d{2})[-_](0[1-9]|1[0-2])\b", filename)
    if iso_match:
        ano = int(iso_match.group(1))
        mes_num = int(iso_match.group(2))
        return mes_num, ano

    # Procurar por padrão MM-YYYY ou MM_YYYY (ex: 05-2026)
    iso_rev_match = re.search(r"\b(0[1-9]|1[0-2])[-_](20\d{2})\b", filename)
    if iso_rev_match:
        mes_num = int(iso_rev_match.group(1))
        ano = int(iso_rev_match.group(2))
        return mes_num, ano

    # 2. Tentar encontrar ano (2020-2030)
    ano_match = re.search(r"\b(202[0-9]|2030)\b", filename)
    ano = int(ano_match.group(1)) if ano_match else datetime.date.today().year

    # 3. Procurar por nomes de meses em português (exatas ou abreviações)
    for ref, (mes_num, mes_nome) in MESES_NOME.items():
        if re.search(r"\b" + ref + r"\w*", filename_lower):
            return mes_num, ano

    # 4. Procurar por número solto de 1 a 12
    num_match = re.search(r"\b(0?[1-9]|1[0-2])\b", filename)
    if num_match:
        return int(num_match.group(1)), ano

    # Fallback
    hoje = datetime.date.today()
    return hoje.month, hoje.year


def gerar_label_mes(mes, ano):
    """
    Gera o rótulo legível do mês/ano (ex: "Janeiro/2026").
    """
    list_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    if isinstance(mes, str):
        return f"{mes}/{ano}"
    if 1 <= mes <= 12:
        return f"{list_meses[mes-1]}/{ano}"
    return f"{mes}/{ano}"


def gerar_periodo_ordem(mes, ano):
    """
    Gera a string de ordenação cronológica (ex: "2026-05").
    """
    if isinstance(mes, str):
        list_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        try:
            mes = list_meses.index(mes) + 1
        except ValueError:
            mes = 1
    return f"{ano:04d}-{mes:02d}"


def safe_number(value, default=0):
    """
    Retorna o valor como float se for numérico, caso contrário retorna o default.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def format_int(value):
    """
    Formata um valor inteiro de forma segura.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/d"
    try:
        val = int(float(value))
        return f"{val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "n/d"

def format_diff(value):
    """
    Formata uma diferença absoluta com sinal positivo ou negativo de forma segura.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/d"
    try:
        val = float(value)
        if val > 0:
            return f"+{int(val):,}".replace(",", ".") if val.is_integer() else f"+{val:.1f}".replace(".", ",")
        elif val < 0:
            return f"{int(val):,}".replace(",", ".") if val.is_integer() else f"{val:.1f}".replace(".", ",")
        else:
            return "0"
    except (ValueError, TypeError):
        return "n/d"

def format_pct(value):
    """
    Formata um valor percentual com sinal de forma segura.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "variação percentual não disponível"
    try:
        val = float(value)
        return f"{val:+.1f}%".replace(".", ",")
    except (ValueError, TypeError):
        return "variação percentual não disponível"

def format_raw_pct(value):
    """
    Formata uma taxa bruta (ex: 92.4%) de forma segura.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/d"
    try:
        return f"{float(value):.1f}%".replace(".", ",")
    except (ValueError, TypeError):
        return "n/d"

def format_pct_points(value):
    """
    Formata uma variação em pontos percentuais (p.p.) de forma segura.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "variação não disponível"
    try:
        val = float(value)
        return f"{val:+.1f} p.p.".replace(".", ",")
    except (ValueError, TypeError):
        return "variação não disponível"

def calcular_variacao_percentual(valor_atual, valor_anterior):
    """
    Calcula a variação percentual de forma segura contra divisões por zero ou nulos.
    """
    if valor_anterior is None or (isinstance(valor_anterior, float) and pd.isna(valor_anterior)):
        return None
    try:
        valor_anterior = float(valor_anterior)
    except (ValueError, TypeError):
        return None

    if valor_anterior == 0:
        return None

    if valor_atual is None or (isinstance(valor_atual, float) and pd.isna(valor_atual)):
        valor_atual = 0.0
    else:
        try:
            valor_atual = float(valor_atual)
        except (ValueError, TypeError):
            valor_atual = 0.0

    return ((valor_atual - valor_anterior) / valor_anterior) * 100


def gerar_resumo_executivo(ind_atual, ind_anterior, label_mes_atual, label_mes_anterior, comp_categoria, comp_cliente, comp_solicitacao):
    """
    Gera um relatório de narrativa executiva para tomada de decisões do CEO/Diretoria.
    Analisa os principais indicadores e encontra gargalos e destaques.
    """
    ia = ind_atual
    ip = ind_anterior

    # Definir diferenças básicas
    fora_sla_at = safe_number(ia.get("fora_sla", 0))
    fora_sla_ant = safe_number(ip.get("fora_sla", 0))
    diff_fora = fora_sla_at - fora_sla_ant

    # 1. Volume
    total_at = safe_number(ia.get("total_chamados", 0))
    total_ant = safe_number(ip.get("total_chamados", 0))
    diff_vol = total_at - total_ant
    pct_vol = calcular_variacao_percentual(total_at, total_ant)
    vol_dir = "aumento" if diff_vol > 0 else "redução" if diff_vol < 0 else "estabilidade"
    var_vol_text = f" passando de {format_int(total_ant)} para {format_int(total_at)} ({format_diff(diff_vol)} / {format_pct(pct_vol)})" if pct_vol is not None else f" mantendo-se em {format_int(total_at)} chamados"

    # 2. SLA Dentro
    pct_sla_at = safe_number(ia.get("percentual_dentro_sla", 0))
    pct_sla_ant = safe_number(ip.get("percentual_dentro_sla", 0))
    diff_sla_pct = pct_sla_at - pct_sla_ant
    sla_dir = "melhora" if diff_sla_pct > 0 else "queda" if diff_sla_pct < 0 else "estabilidade"
    sla_text = f" com a taxa de SLA dentro do prazo subindo de {format_raw_pct(pct_sla_ant)} para {format_raw_pct(pct_sla_at)}" if diff_sla_pct > 0 else f" com a taxa de SLA caindo de {format_raw_pct(pct_sla_ant)} para {format_raw_pct(pct_sla_at)}"
    
    # Detalhar quantidades do SLA
    sla_dentro_text = f" (os chamados dentro do prazo foram de {format_int(ip.get('dentro_sla', 0))} para {format_int(ia.get('dentro_sla', 0))})"
    sla_fora_text = f" e os chamados fora do SLA saíram de {format_int(ip.get('fora_sla', 0))} para {format_int(ia.get('fora_sla', 0))}"

    # 3. Tratamento 72h
    ate_72h_at = safe_number(ia.get("ate_72h", 0))
    ate_72h_ant = safe_number(ip.get("ate_72h", 0))
    diff_72h = ate_72h_at - ate_72h_ant
    pct_72h = calcular_variacao_percentual(ate_72h_at, ate_72h_ant)
    if diff_72h > 0:
        ate_72h_text = f" O tratamento em até 72 horas também evoluiu, passando de {format_int(ate_72h_ant)} para {format_int(ate_72h_at)} chamados ({format_diff(diff_72h)} / {format_pct(pct_72h)})."
    else:
        ate_72h_text = f" O volume de chamados resolvidos em até 72h registrou variação de {format_diff(diff_72h)} chamados (saindo de {format_int(ate_72h_ant)} para {format_int(ate_72h_at)})."

    # 4. Em aberto
    abertos_at = safe_number(ia.get("em_aberto", 0))
    abertos_ant = safe_number(ip.get("em_aberto", 0))
    diff_abertos = abertos_at - abertos_ant
    abertos_text = f" O estoque de chamados em aberto / em tratamento foi de {format_int(abertos_ant)} para {format_int(abertos_at)}."

    # FCR
    fcr_disponivel = safe_number(ia.get("fcr_tratado", 0)) > 0 and safe_number(ip.get("fcr_tratado", 0)) > 0
    diff_fcr = 0
    diff_fcr_pct = 0.0
    fcr_text = ""
    if fcr_disponivel:
        diff_fcr = safe_number(ia.get("fcr_1h", 0)) - safe_number(ip.get("fcr_1h", 0))
        diff_fcr_pct = safe_number(ia.get("percentual_fcr_1h", 0)) - safe_number(ip.get("percentual_fcr_1h", 0))
        fcr_text = f" O First Call Resolution (FCR 1h) variou {format_pct_points(diff_fcr_pct)}, registrando {format_raw_pct(ia.get('percentual_fcr_1h', 0))} no mês atual."

    # 5. Categorias que mais cresceram e reduziram
    cat_cresc = "Nenhuma"
    cat_red = "Nenhuma"
    
    if not comp_categoria.empty:
        comp_cat_c = comp_categoria.sort_values("Diferença", ascending=False)
        if not comp_cat_c.empty and safe_number(comp_cat_c.iloc[0]["Diferença"]) > 0:
            row_c = comp_cat_c.iloc[0]
            cat_cresc = f"*{row_c['Categoria Principal']}* ({format_diff(row_c['Diferença'])} chamados)"
            
        comp_cat_r = comp_categoria.sort_values("Diferença", ascending=True)
        if not comp_cat_r.empty and safe_number(comp_cat_r.iloc[0]["Diferença"]) < 0:
            row_r = comp_cat_r.iloc[0]
            cat_red = f"*{row_r['Categoria Principal']}* ({format_diff(row_r['Diferença'])} chamados)"

    # 6. Clientes que mais cresceram em volume
    cli_cresc = "Nenhum"
    if not comp_cliente.empty:
        comp_cli_c = comp_cliente.sort_values("Diferença", ascending=False)
        if not comp_cli_c.empty and safe_number(comp_cli_c.iloc[0]["Diferença"]) > 0:
            row_cl = comp_cli_c.iloc[0]
            cli_cresc = f"*{row_cl['Cliente']}* ({format_diff(row_cl['Diferença'])} chamados)"

    # 7. Principal ponto de atenção
    ponto_atencao = "Não foram identificados desvios críticos."
    fora_sla_at_val = safe_number(ia.get("fora_sla", 0))
    fora_sla_ant_val = safe_number(ip.get("fora_sla", 0))
    em_aberto_at_val = safe_number(ia.get("em_aberto", 0))
    em_aberto_ant_val = safe_number(ip.get("em_aberto", 0))
    acima_72h_at_val = safe_number(ia.get("acima_72h", 0))
    acima_72h_ant_val = safe_number(ip.get("acima_72h", 0))

    if fora_sla_at_val > fora_sla_ant_val:
        ponto_atencao = f"Aumento no número de chamados fora do SLA, somando {format_int(fora_sla_at_val)} chamados ({format_diff(fora_sla_at_val - fora_sla_ant_val)}). A principal causa de SLA vencido foi a solicitação: *{ia.get('causa_sla_vencido', '-')}*."
    elif em_aberto_at_val > em_aberto_ant_val:
        ponto_atencao = f"Aumento no backlog em aberto, passando de {format_int(em_aberto_ant_val)} para {format_int(em_aberto_at_val)} chamados. A principal causa de atraso operacional foi a solicitação: *{ia.get('causa_atraso', '-')}*."
    elif acima_72h_at_val > acima_72h_ant_val:
        ponto_atencao = f"Aumento no número de chamados resolvidos acima de 72 horas, somando {format_int(acima_72h_at_val)} chamados. A principal causa de atraso foi a solicitação: *{ia.get('causa_atraso', '-')}*."

    texto = (
        f"Em relação a {label_mes_anterior}, {label_mes_atual} apresentou {vol_dir} no volume total de chamados{var_vol_text}."
        f" Quanto ao SLA, observou-se {sla_dir}{sla_text}{sla_dentro_text}{sla_fora_text}."
        f"{ate_72h_text}{abertos_text}{fcr_text}"
        f" No recorte de categorias, a que mais cresceu em volume foi {cat_cresc}, enquanto a que mais reduziu foi {cat_red}."
        f" O cliente com maior aumento absoluto de chamados foi {cli_cresc}."
        f" O principal ponto de atenção para a gestão é: {ponto_atencao}"
    )
    
    # Gerar listas de Melhores/Piores/Atenções para os cartões
    melhoras = []
    pioras = []
    atencoes = []
    
    # Volume de chamados
    if diff_vol < 0:
        melhoras.append(f"Redução no volume de chamados: {format_diff(diff_vol)} chamados ({format_pct(pct_vol)})")
    elif diff_vol > 0:
        pioras.append(f"Aumento no volume de chamados: {format_diff(diff_vol)} chamados ({format_pct(pct_vol)})")
        
    # SLA %
    if diff_sla_pct > 0.5:
        melhoras.append(f"Melhora na taxa de SLA dentro do prazo: {format_pct_points(diff_sla_pct)} ({format_raw_pct(pct_sla_at)})")
    elif diff_sla_pct < -0.5:
        pioras.append(f"Queda na taxa de SLA dentro do prazo: {format_pct_points(diff_sla_pct)} ({format_raw_pct(pct_sla_at)})")
        
    # Fora do SLA (quantidade)
    if diff_fora < 0:
        melhoras.append(f"Redução de chamados fora do SLA: {format_diff(diff_fora)} chamados")
    elif diff_fora > 0:
        pioras.append(f"Aumento de chamados fora do SLA: {format_diff(diff_fora)} chamados")
        
    # 72h
    if diff_72h > 0:
        melhoras.append(f"Aumento de chamados tratados em até 72h: {format_diff(diff_72h)} chamados")
    elif diff_72h < 0:
        pioras.append(f"Redução de chamados tratados em até 72h: {format_diff(diff_72h)} chamados")
        
    # Em aberto
    if diff_abertos < 0:
        melhoras.append(f"Redução no estoque de chamados em aberto: {format_diff(diff_abertos)} chamados")
    elif diff_abertos > 0:
        pioras.append(f"Aumento no backlog em aberto: {format_diff(diff_abertos)} chamados")

    # FCR
    if fcr_disponivel:
        if diff_fcr_pct > 0.5:
            melhoras.append(f"Melhora no FCR 1h: {format_pct_points(diff_fcr_pct)} ({format_raw_pct(ia.get('percentual_fcr_1h', 0))})")
        elif diff_fcr_pct < -0.5:
            pioras.append(f"Queda no FCR 1h: {format_pct_points(diff_fcr_pct)} ({format_raw_pct(ia.get('percentual_fcr_1h', 0))})")
        
    # Pontos de Atenção
    fora_sla_at_int = safe_number(ia.get("fora_sla", 0))
    em_aberto_at_int = safe_number(ia.get("em_aberto", 0))
    acima_72h_at_int = safe_number(ia.get("acima_72h", 0))

    if fora_sla_at_int > 0:
        atencoes.append(f"Total de {format_int(fora_sla_at_int)} chamados estouraram o SLA no mês atual. Causa principal: *{ia.get('causa_sla_vencido', '-')}*")
    if em_aberto_at_int > 0:
        atencoes.append(f"Existem {format_int(em_aberto_at_int)} chamados em aberto / em tratamento no mês atual")
    if acima_72h_at_int > 0:
        atencoes.append(f"Total de {format_int(acima_72h_at_int)} chamados finalizados após 72h. Causa principal: *{ia.get('causa_atraso', '-')}*")
    if fcr_disponivel and safe_number(ia.get("percentual_fcr_1h", 0)) < 70:
        atencoes.append(f"FCR 1h abaixo da meta recomendada (70%): {format_raw_pct(ia.get('percentual_fcr_1h', 0))}")

    return texto, melhoras, pioras, atencoes
