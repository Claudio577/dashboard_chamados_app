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


def calcular_variacao_percentual(valor_atual, valor_anterior):
    try:
        valor_atual = float(valor_atual)
        valor_anterior = float(valor_anterior)
    except (ValueError, TypeError):
        return None

    if valor_anterior == 0:
        if valor_atual == 0:
            return 0.0
        return None

    return ((valor_atual - valor_anterior) / valor_anterior) * 100


def gerar_resumo_executivo(ind_atual, ind_anterior, label_mes_atual, label_mes_anterior, comp_categoria, comp_cliente, comp_solicitacao):
    """
    Gera um relatório de narrativa executiva para tomada de decisões do CEO/Diretoria.
    Analisa os principais indicadores e encontra gargalos e destaques.
    """
    ia = ind_atual
    ip = ind_anterior

    # Definir diferenças básicas
    diff_fora = ia["fora_sla"] - ip["fora_sla"]

    # 1. Volume
    diff_vol = ia["total_chamados"] - ip["total_chamados"]
    pct_vol = calcular_variacao_percentual(ia["total_chamados"], ip["total_chamados"])
    vol_dir = "aumento" if diff_vol > 0 else "redução" if diff_vol < 0 else "estabilidade"
    var_vol_text = f" passando de {ip['total_chamados']} para {ia['total_chamados']} ({diff_vol:+.0f} / {pct_vol:+.1f}%)" if pct_vol is not None else f" mantendo-se em {ia['total_chamados']} chamados"

    # 2. SLA Dentro
    diff_sla_pct = ia["percentual_dentro_sla"] - ip["percentual_dentro_sla"]
    sla_dir = "melhora" if diff_sla_pct > 0 else "queda" if diff_sla_pct < 0 else "estabilidade"
    sla_text = f" com a taxa de SLA dentro do prazo subindo de {ip['percentual_dentro_sla']:.1f}% para {ia['percentual_dentro_sla']:.1f}%" if diff_sla_pct > 0 else f" com a taxa de SLA caindo de {ip['percentual_dentro_sla']:.1f}% para {ia['percentual_dentro_sla']:.1f}%"
    
    # Detalhar quantidades do SLA
    sla_dentro_text = f" (os chamados dentro do prazo foram de {ip['dentro_sla']} para {ia['dentro_sla']})"
    sla_fora_text = f" e os chamados fora do SLA saíram de {ip['fora_sla']} para {ia['fora_sla']}"

    # 3. Tratamento 72h
    diff_72h = ia["ate_72h"] - ip["ate_72h"]
    pct_72h = calcular_variacao_percentual(ia["ate_72h"], ip["ate_72h"])
    if diff_72h > 0:
        ate_72h_text = f" O tratamento em até 72 horas também evoluiu, passando de {ip['ate_72h']} para {ia['ate_72h']} chamados ({diff_72h:+.0f} / {pct_72h:+.1f}%)."
    else:
        ate_72h_text = f" O volume de chamados resolvidos em até 72h registrou variação de {diff_72h:+.0f} chamados (saindo de {ip['ate_72h']} para {ia['ate_72h']})."

    # 4. Em aberto
    diff_abertos = ia["em_aberto"] - ip["em_aberto"]
    abertos_text = f" O estoque de chamados em aberto / em tratamento foi de {ip['em_aberto']} para {ia['em_aberto']}."

    # FCR
    fcr_disponivel = ia.get("fcr_tratado", 0) > 0 and ip.get("fcr_tratado", 0) > 0
    diff_fcr = 0
    diff_fcr_pct = 0.0
    fcr_text = ""
    if fcr_disponivel:
        diff_fcr = ia["fcr_1h"] - ip["fcr_1h"]
        diff_fcr_pct = ia["percentual_fcr_1h"] - ip["percentual_fcr_1h"]
        fcr_text = f" O First Call Resolution (FCR 1h) variou {diff_fcr_pct:+.1f} p.p., registrando {ia['percentual_fcr_1h']:.1f}% no mês atual."

    # 5. Categorias que mais cresceram e reduziram
    cat_cresc = "Nenhuma"
    cat_red = "Nenhuma"
    
    if not comp_categoria.empty:
        comp_cat_c = comp_categoria.sort_values("Diferença", ascending=False)
        if not comp_cat_c.empty and comp_cat_c.iloc[0]["Diferença"] > 0:
            row_c = comp_cat_c.iloc[0]
            cat_cresc = f"*{row_c['Categoria Principal']}* (+{row_c['Diferença']:.0f} chamados)"
            
        comp_cat_r = comp_categoria.sort_values("Diferença", ascending=True)
        if not comp_cat_r.empty and comp_cat_r.iloc[0]["Diferença"] < 0:
            row_r = comp_cat_r.iloc[0]
            cat_red = f"*{row_r['Categoria Principal']}* ({row_r['Diferença']:.0f} chamados)"

    # 6. Clientes que mais cresceram em volume
    cli_cresc = "Nenhum"
    if not comp_cliente.empty:
        comp_cli_c = comp_cliente.sort_values("Diferença", ascending=False)
        if not comp_cli_c.empty and comp_cli_c.iloc[0]["Diferença"] > 0:
            row_cl = comp_cli_c.iloc[0]
            cli_cresc = f"*{row_cl['Cliente']}* (+{row_cl['Diferença']:.0f} chamados)"

    # 7. Principal ponto de atenção
    ponto_atencao = "Não foram identificados desvios críticos."
    if ia["fora_sla"] > ip["fora_sla"]:
        ponto_atencao = f"Aumento no número de chamados fora do SLA, somando {ia['fora_sla']} chamados (+{ia['fora_sla'] - ip['fora_sla']}). A principal causa de SLA vencido foi a solicitação: *{ia['causa_sla_vencido']}*."
    elif ia["em_aberto"] > ip["em_aberto"]:
        ponto_atencao = f"Aumento no backlog em aberto, passando de {ip['em_aberto']} para {ia['em_aberto']} chamados. A principal causa de atraso operacional foi a solicitação: *{ia['causa_atraso']}*."
    elif ia["acima_72h"] > ip["acima_72h"]:
        ponto_atencao = f"Aumento no número de chamados resolvidos acima de 72 horas, somando {ia['acima_72h']} chamados. A principal causa de atraso foi a solicitação: *{ia['causa_atraso']}*."

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
        melhoras.append(f"Redução no volume de chamados: {diff_vol} chamados ({pct_vol:.1f}%)")
    elif diff_vol > 0:
        # Aumento de chamados é uma piora/atenção
        pioras.append(f"Aumento no volume de chamados: +{diff_vol} chamados (+{pct_vol:.1f}%)")
        
    # SLA %
    if diff_sla_pct > 0.5:
        melhoras.append(f"Melhora na taxa de SLA dentro do prazo: +{diff_sla_pct:.1f} p.p. ({ia['percentual_dentro_sla']:.1f}%)")
    elif diff_sla_pct < -0.5:
        pioras.append(f"Queda na taxa de SLA dentro do prazo: {diff_sla_pct:.1f} p.p. ({ia['percentual_dentro_sla']:.1f}%)")
        
    # Fora do SLA (quantidade)
    if diff_fora < 0:
        melhoras.append(f"Redução de chamados fora do SLA: {diff_fora} chamados")
    elif diff_fora > 0:
        pioras.append(f"Aumento de chamados fora do SLA: +{diff_fora} chamados")
        
    # 72h
    if diff_72h > 0:
        melhoras.append(f"Aumento de chamados tratados em até 72h: +{diff_72h} chamados")
    elif diff_72h < 0:
        pioras.append(f"Redução de chamados tratados em até 72h: {diff_72h} chamados")
        
    # Em aberto
    if diff_abertos < 0:
        melhoras.append(f"Redução no estoque de chamados em aberto: {diff_abertos} chamados")
    elif diff_abertos > 0:
        pioras.append(f"Aumento no backlog em aberto: +{diff_abertos} chamados")

    # FCR
    if fcr_disponivel:
        if diff_fcr_pct > 0.5:
            melhoras.append(f"Melhora no FCR 1h: +{diff_fcr_pct:.1f} p.p. ({ia['percentual_fcr_1h']:.1f}%)")
        elif diff_fcr_pct < -0.5:
            pioras.append(f"Queda no FCR 1h: {diff_fcr_pct:.1f} p.p. ({ia['percentual_fcr_1h']:.1f}%)")
        
    # Pontos de Atenção
    if ia["fora_sla"] > 0:
        atencoes.append(f"Total de {ia['fora_sla']} chamados estouraram o SLA no mês atual. Causa principal: *{ia['causa_sla_vencido']}*")
    if ia["em_aberto"] > 0:
        atencoes.append(f"Existem {ia['em_aberto']} chamados em aberto / em tratamento no mês atual")
    if ia["acima_72h"] > 0:
        atencoes.append(f"Total de {ia['acima_72h']} chamados finalizados após 72h. Causa principal: *{ia['causa_atraso']}*")
    if fcr_disponivel and ia["percentual_fcr_1h"] < 70:
        atencoes.append(f"FCR 1h abaixo da meta recomendada (70%): {ia['percentual_fcr_1h']:.1f}%")

    return texto, melhoras, pioras, atencoes
