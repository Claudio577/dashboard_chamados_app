import pandas as pd
import numpy as np
import re
import unicodedata

def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


def limpar_texto(texto):
    if pd.isna(texto):
        return "Não informado"
    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto if texto else "Não informado"


def encontrar_coluna(df, opcoes):
    colunas_norm = {col: normalizar_texto(col) for col in df.columns}

    # Busca exata primeiro
    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        for col, col_norm in colunas_norm.items():
            if opcao_norm == col_norm:
                return col

    # Busca parcial se não encontrar exata
    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        for col, col_norm in colunas_norm.items():
            if opcao_norm in col_norm:
                return col

    return None


def ler_arquivo(uploaded_file):
    nome = uploaded_file.name.lower()
    # Resetar ponteiro de leitura para garantir re-leitura segura
    uploaded_file.seek(0)
    
    if nome.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="utf-8")
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="latin1")

    if nome.endswith(".xls"):
        return pd.read_excel(uploaded_file, engine="xlrd")

    return pd.read_excel(uploaded_file)


def preparar_datas(df, coluna):
    if coluna and coluna in df.columns:
        df[coluna] = pd.to_datetime(df[coluna], errors="coerce", dayfirst=True)
    return df


def montar_empresa_analise(row, col_empresa, col_de):
    empresa = limpar_texto(row[col_empresa])
    de = limpar_texto(row[col_de]) if col_de else ""

    empresa_norm = normalizar_texto(empresa)
    de_norm = normalizar_texto(de)

    # Regras CBLOC e Casa do Construtor
    if "cbloc" in de_norm:
        return "CBLOC BRASIL LOCAÇÃO DE EQUIPAMENTOS LTDA"

    if "cbloc" in empresa_norm and "casa do construtor" in de_norm:
        return "CASA DO CONSTRUTOR"

    return empresa


def mapear_responsavel(df):
    """
    Identifica a coluna de responsável prioritária.
    Retorna o nome da coluna escolhida e se é uma aproximação (True se for Responsavel, etc).
    """
    col_finalizador = encontrar_coluna(df, ["Finalizado por", "Encerrado por", "Atendente finalizador"])
    if col_finalizador:
        return col_finalizador, False

    col_responsavel = encontrar_coluna(df, ["Responsável", "Responsavel", "Atendente", "Analista"])
    if col_responsavel:
        return col_responsavel, True

    return None, False


def tratar_planilha(uploaded_file, nome_base="Mês atual"):
    """
    Carrega a planilha, trata os dados seguindo as regras de negócio
    e retorna o DataFrame tratado contendo todas as novas colunas e metadados.
    """
    df = ler_arquivo(uploaded_file)

    # Identificar colunas
    col_empresa = encontrar_coluna(df, ["Empresa", "Cliente", "Nome Fantasia", "Razão Social", "Razao Social"])
    col_de = encontrar_coluna(df, ["De", "Solicitante", "Aberto por", "Cliente Solicitante"])
    col_abertura = encontrar_coluna(df, ["Abertura", "Data Abertura", "Data de Abertura", "Criado em", "Data de Criação"])
    col_encerramento = encontrar_coluna(df, ["Encerramento", "Data Encerramento", "Data de Encerramento", "Fechado em", "Resolvido em"])
    col_vencimento = encontrar_coluna(df, ["Vencimento", "Data Vencimento", "SLA", "Prazo", "Data SLA"])
    col_tipo = encontrar_coluna(df, ["Tipo"])
    col_item = encontrar_coluna(df, ["Item"])
    col_qualificacao = encontrar_coluna(df, ["Qualificação", "Qualificacao", "Classificação", "Classificacao"])
    col_categoria = encontrar_coluna(df, ["Categoria", "Assunto", "Serviço", "Servico"])
    col_status = encontrar_coluna(df, ["Status", "Situação", "Situacao"])
    col_numero = encontrar_coluna(df, ["N", "Número", "Numero", "Chamado", "Ticket"])

    colunas_obrigatorias = {
        "Empresa": col_empresa,
        "Abertura": col_abertura,
        "Encerramento": col_encerramento,
    }

    faltando = [nome for nome, coluna in colunas_obrigatorias.items() if coluna is None]

    if faltando:
        raise ValueError(
            f"Na base {nome_base}, não consegui identificar estas colunas obrigatórias: {faltando}. "
            f"Colunas encontradas no arquivo: {list(df.columns)}"
        )

    # Copiar e processar datas
    df_clean = df.copy()
    df_clean = preparar_datas(df_clean, col_abertura)
    df_clean = preparar_datas(df_clean, col_encerramento)
    df_clean = preparar_datas(df_clean, col_vencimento)

    # Normalizar Cliente
    df_clean["Cliente Análise"] = df_clean.apply(
        lambda row: montar_empresa_analise(row, col_empresa, col_de), axis=1
    )

    # Categoria Principal (Tipo > Categoria > Qualificação)
    if col_tipo:
        df_clean["Categoria Principal"] = df_clean[col_tipo].fillna("Não informado").astype(str).str.strip()
    elif col_categoria:
        df_clean["Categoria Principal"] = df_clean[col_categoria].fillna("Não informado").astype(str).str.strip()
    elif col_qualificacao:
        df_clean["Categoria Principal"] = df_clean[col_qualificacao].fillna("Não informado").astype(str).str.strip()
    else:
        df_clean["Categoria Principal"] = "Não informado"
    
    df_clean["Categoria Principal"] = df_clean["Categoria Principal"].replace("", "Não informado")

    # Solicitação Específica (Tipo + Item > Qualificação > Categoria)
    if col_tipo and col_item:
        df_clean["Solicitação Específica"] = (
            df_clean[col_tipo].fillna("Não informado").astype(str).str.strip()
            + " - "
            + df_clean[col_item].fillna("Não informado").astype(str).str.strip()
        )
    elif col_qualificacao:
        df_clean["Solicitação Específica"] = df_clean[col_qualificacao].fillna("Não informado").astype(str).str.strip()
    elif col_categoria:
        df_clean["Solicitação Específica"] = df_clean[col_categoria].fillna("Não informado").astype(str).str.strip()
    else:
        df_clean["Solicitação Específica"] = "Não informado"
        
    df_clean["Solicitação Específica"] = df_clean["Solicitação Específica"].replace("", "Não informado")

    # Mapeamento do Responsável
    col_resp, is_approx = mapear_responsavel(df_clean)
    if col_resp:
        df_clean["Responsável Análise"] = df_clean[col_resp].fillna("Não informado").astype(str).str.strip()
        df_clean["Responsável Análise"] = df_clean["Responsável Análise"].replace("", "Não informado")
        nome_original_resp = col_resp
    else:
        df_clean["Responsável Análise"] = "Não informado"
        nome_original_resp = "Não encontrado"
        is_approx = False

    # SLA Status
    # Se encerramento vazio -> Em aberto / Em tratamento
    df_clean["Status SLA"] = "Em aberto / Em tratamento"
    mask_finalizado = df_clean[col_encerramento].notna()

    if col_vencimento:
        # Se finalizado mas vencimento vazio -> SLA não informado
        mask_venc_vazio = df_clean[col_vencimento].isna()
        df_clean.loc[mask_finalizado & mask_venc_vazio, "Status SLA"] = "SLA não informado"

        # Se finalizado e vencimento preenchido
        mask_venc_preenchido = df_clean[col_vencimento].notna()
        df_clean.loc[mask_finalizado & mask_venc_preenchido & (df_clean[col_encerramento] <= df_clean[col_vencimento]), "Status SLA"] = "Dentro do SLA"
        df_clean.loc[mask_finalizado & mask_venc_preenchido & (df_clean[col_encerramento] > df_clean[col_vencimento]), "Status SLA"] = "Fora do SLA"
    else:
        # Se não existe coluna de vencimento na planilha
        df_clean.loc[mask_finalizado, "Status SLA"] = "SLA não informado"

    # 72 Horas Status
    df_clean["Status 72h"] = "Em aberto / Em tratamento"
    df_clean["Horas para tratamento"] = np.nan

    mask_abert_preenchido = df_clean[col_abertura].notna()
    mask_finalizado_com_abertura = mask_finalizado & mask_abert_preenchido

    df_clean.loc[mask_finalizado_com_abertura, "Horas para tratamento"] = (
        (df_clean.loc[mask_finalizado_com_abertura, col_encerramento] - 
         df_clean.loc[mask_finalizado_com_abertura, col_abertura]).dt.total_seconds() / 3600
    )

    df_clean.loc[mask_finalizado & df_clean[col_abertura].isna(), "Status 72h"] = "72h não informado"
    df_clean.loc[mask_finalizado_com_abertura & (df_clean["Horas para tratamento"] <= 72), "Status 72h"] = "Tratado até 72h"
    df_clean.loc[mask_finalizado_com_abertura & (df_clean["Horas para tratamento"] > 72), "Status 72h"] = "Tratado acima de 72h"

    # FCR 1h
    df_clean["Status FCR 1h"] = "Em aberto / Em tratamento"
    df_clean.loc[mask_finalizado_com_abertura & (df_clean["Horas para tratamento"] <= 1), "Status FCR 1h"] = "Resolvido até 1h"
    df_clean.loc[mask_finalizado_com_abertura & (df_clean["Horas para tratamento"] > 1), "Status FCR 1h"] = "Resolvido acima de 1h"
    df_clean.loc[mask_finalizado & df_clean[col_abertura].isna(), "Status FCR 1h"] = "FCR não informado"

    # Salvar dicionário de metadados das colunas encontradas
    colunas_encontradas = {
        "col_empresa": col_empresa,
        "col_de": col_de,
        "col_abertura": col_abertura,
        "col_encerramento": col_encerramento,
        "col_vencimento": col_vencimento,
        "col_tipo": col_tipo,
        "col_item": col_item,
        "col_qualificacao": col_qualificacao,
        "col_categoria": col_categoria,
        "col_status": col_status,
        "col_numero": col_numero,
        "col_responsavel": nome_original_resp,
        "is_responsavel_aproximado": is_approx
    }

    return df_clean, colunas_encontradas


def calcular_indicadores(df):
    """
    Calcula um dicionário de indicadores básicos a partir de um dataframe tratado.
    Garante consistência.
    """
    total_chamados = len(df)
    total_empresas = df["Cliente Análise"].nunique() if total_chamados > 0 else 0

    # Contagem SLA
    dentro_sla = int((df["Status SLA"] == "Dentro do SLA").sum())
    fora_sla = int((df["Status SLA"] == "Fora do SLA").sum())
    sla_nao_inf = int((df["Status SLA"] == "SLA não informado").sum())
    em_aberto = int((df["Status SLA"] == "Em aberto / Em tratamento").sum())
    
    # SLA tratado = dentro + fora (não conta os sem SLA ou abertos)
    sla_tratado = dentro_sla + fora_sla
    percentual_dentro_sla = (dentro_sla / sla_tratado * 100) if sla_tratado > 0 else 0.0

    # Contagem 72h
    ate_72h = int((df["Status 72h"] == "Tratado até 72h").sum())
    acima_72h = int((df["Status 72h"] == "Tratado acima de 72h").sum())
    nao_inf_72h = int((df["Status 72h"] == "72h não informado").sum())
    
    # FCR
    fcr_1h = int((df["Status FCR 1h"] == "Resolvido até 1h").sum())
    fcr_acima_1h = int((df["Status FCR 1h"] == "Resolvido acima de 1h").sum())
    fcr_nao_inf = int((df["Status FCR 1h"] == "FCR não informado").sum())
    fcr_tratado = fcr_1h + fcr_acima_1h
    percentual_fcr_1h = (fcr_1h / fcr_tratado * 100) if fcr_tratado > 0 else 0.0

    # Líderes (Top 1)
    cliente_top = "-"
    cliente_top_qtd = 0
    if total_chamados > 0:
        c_counts = df["Cliente Análise"].value_counts()
        if not c_counts.empty:
            cliente_top = c_counts.index[0]
            cliente_top_qtd = int(c_counts.iloc[0])

    categoria_top = "-"
    categoria_top_qtd = 0
    if total_chamados > 0:
        cat_counts = df["Categoria Principal"].value_counts()
        if not cat_counts.empty:
            categoria_top = cat_counts.index[0]
            categoria_top_qtd = int(cat_counts.iloc[0])

    solicitacao_top = "-"
    solicitacao_top_qtd = 0
    if total_chamados > 0:
        sol_counts = df["Solicitação Específica"].value_counts()
        if not sol_counts.empty:
            solicitacao_top = sol_counts.index[0]
            solicitacao_top_qtd = int(sol_counts.iloc[0])

    # Causas de estouro SLA (apenas chamados Fora do SLA)
    causa_sla_vencido = "-"
    causa_sla_vencido_qtd = 0
    df_fora_sla = df[df["Status SLA"] == "Fora do SLA"]
    if not df_fora_sla.empty:
        c_sla_counts = df_fora_sla["Solicitação Específica"].value_counts()
        if not c_sla_counts.empty:
            causa_sla_vencido = c_sla_counts.index[0]
            causa_sla_vencido_qtd = int(c_sla_counts.iloc[0])

    # Causas de atraso operacional (chamados Tratado acima de 72h)
    causa_atraso = "-"
    causa_atraso_qtd = 0
    df_atraso = df[df["Status 72h"] == "Tratado acima de 72h"]
    if not df_atraso.empty:
        c_atr_counts = df_atraso["Solicitação Específica"].value_counts()
        if not c_atr_counts.empty:
            causa_atraso = c_atr_counts.index[0]
            causa_atraso_qtd = int(c_atr_counts.iloc[0])

    return {
        "total_chamados": total_chamados,
        "total_empresas": total_empresas,
        "sla_tratado": sla_tratado,
        "dentro_sla": dentro_sla,
        "fora_sla": fora_sla,
        "sla_nao_informado": sla_nao_inf,
        "em_aberto": em_aberto,
        "percentual_dentro_sla": percentual_dentro_sla,
        "ate_72h": ate_72h,
        "acima_72h": acima_72h,
        "nao_informado_72h": nao_inf_72h,
        "fcr_tratado": fcr_tratado,
        "fcr_1h": fcr_1h,
        "fcr_acima_1h": fcr_acima_1h,
        "fcr_nao_informado": fcr_nao_inf,
        "percentual_fcr_1h": percentual_fcr_1h,
        "cliente_top": cliente_top,
        "cliente_top_qtd": cliente_top_qtd,
        "categoria_top": categoria_top,
        "categoria_top_qtd": categoria_top_qtd,
        "solicitacao_top": solicitacao_top,
        "solicitacao_top_qtd": solicitacao_top_qtd,
        "causa_sla_vencido": causa_sla_vencido,
        "causa_sla_vencido_qtd": causa_sla_vencido_qtd,
        "causa_atraso": causa_atraso,
        "causa_atraso_qtd": causa_atraso_qtd,
    }


def obter_tabela_responsaveis(df):
    """
    Gera um dataframe consolidado contendo as métricas de atendimento por responsável.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "Responsável", "Atribuídos", "Finalizados", "Em Aberto", 
            "Dentro SLA", "Fora SLA", "SLA Não Inf.", "Até 72h", "Acima 72h", 
            "72h Não Inf.", "Tempo Médio (Horas)", "% Dentro SLA", "% Até 72h"
        ])

    responsaveis = df["Responsável Análise"].unique()
    linhas = []

    for resp in responsaveis:
        sub = df[df["Responsável Análise"] == resp]
        
        atribuidos = len(sub)
        
        # Chamados finalizados (tem data de encerramento, ou seja, Status SLA != Em aberto)
        finalizados = int((sub["Status SLA"] != "Em aberto / Em tratamento").sum())
        em_aberto = atribuidos - finalizados
        
        dentro_sla = int((sub["Status SLA"] == "Dentro do SLA").sum())
        fora_sla = int((sub["Status SLA"] == "Fora do SLA").sum())
        sla_nao_inf = int((sub["Status SLA"] == "SLA não informado").sum())
        
        ate_72h = int((sub["Status 72h"] == "Tratado até 72h").sum())
        acima_72h = int((sub["Status 72h"] == "Tratado acima de 72h").sum())
        nao_inf_72h = int((sub["Status 72h"] == "72h não informado").sum())
        
        # Tempo médio em horas (apenas finalizados que possuem Horas para tratamento preenchido)
        tempo_medio = sub["Horas para tratamento"].mean()
        if pd.isna(tempo_medio):
            tempo_medio = 0.0
            
        # Porcentagens
        sla_tratado_resp = dentro_sla + fora_sla
        pct_dentro_sla = (dentro_sla / sla_tratado_resp * 100) if sla_tratado_resp > 0 else 0.0
        
        finalizados_com_72h = ate_72h + acima_72h
        pct_ate_72h = (ate_72h / finalizados_com_72h * 100) if finalizados_com_72h > 0 else 0.0
        
        linhas.append({
            "Responsável": resp,
            "Atribuídos": atribuidos,
            "Finalizados": finalizados,
            "Em Aberto": em_aberto,
            "Dentro SLA": dentro_sla,
            "Fora SLA": fora_sla,
            "SLA Não Inf.": sla_nao_inf,
            "Até 72h": ate_72h,
            "Acima 72h": acima_72h,
            "72h Não Inf.": nao_inf_72h,
            "Tempo Médio (Horas)": round(tempo_medio, 1),
            "% Dentro SLA": round(pct_dentro_sla, 1),
            "% Até 72h": round(pct_ate_72h, 1)
        })

    df_resp = pd.DataFrame(linhas)
    return df_resp.sort_values("Atribuídos", ascending=False)


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


def comparar_frequencias(df_atual, df_anterior, coluna, nome_coluna):
    """
    Compara a contagem de frequência de uma coluna categórica entre o mês atual e anterior.
    """
    if df_atual.empty and df_anterior.empty:
        return pd.DataFrame(columns=[nome_coluna, "Mês anterior", "Mês atual", "Diferença", "Variação %"])

    c_counts = df_atual[coluna].value_counts().reset_index(name="Mês atual") if not df_atual.empty else pd.DataFrame(columns=[coluna, "Mês atual"])
    c_counts.columns = [nome_coluna, "Mês atual"]

    p_counts = df_anterior[coluna].value_counts().reset_index(name="Mês anterior") if not df_anterior.empty else pd.DataFrame(columns=[coluna, "Mês anterior"])
    p_counts.columns = [nome_coluna, "Mês anterior"]

    comp = pd.merge(p_counts, c_counts, on=nome_coluna, how="outer").fillna(0)
    comp["Mês anterior"] = comp["Mês anterior"].astype(int)
    comp["Mês atual"] = comp["Mês atual"].astype(int)
    comp["Diferença"] = comp["Mês atual"] - comp["Mês anterior"]
    comp["Variação %"] = comp.apply(
        lambda row: calcular_variacao_percentual(row["Mês atual"], row["Mês anterior"]),
        axis=1
    )

    return comp.sort_values("Mês atual", ascending=False)


def montar_comparativo_indicadores(ind_atual, ind_anterior):
    """
    Gera um DataFrame comparativo a partir dos dicionários de indicadores.
    """
    linhas = [
        ("Total de chamados", ind_anterior["total_chamados"], ind_atual["total_chamados"]),
        ("Empresas com chamados", ind_anterior["total_empresas"], ind_atual["total_empresas"]),
        ("SLA tratado", ind_anterior["sla_tratado"], ind_atual["sla_tratado"]),
        ("Dentro do SLA", ind_anterior["dentro_sla"], ind_atual["dentro_sla"]),
        ("Fora do SLA", ind_anterior["fora_sla"], ind_atual["fora_sla"]),
        ("SLA não informado", ind_anterior["sla_nao_informado"], ind_atual["sla_nao_informado"]),
        ("Em aberto / Em tratamento", ind_anterior["em_aberto"], ind_atual["em_aberto"]),
        ("Tratados até 72h", ind_anterior["ate_72h"], ind_atual["ate_72h"]),
        ("Tratados acima de 72h", ind_anterior["acima_72h"], ind_atual["acima_72h"]),
        ("72h não informado", ind_anterior["nao_informado_72h"], ind_atual["nao_informado_72h"]),
        ("First Call Resolution tratado", ind_anterior["fcr_tratado"], ind_atual["fcr_tratado"]),
        ("FCR até 1h", ind_anterior["fcr_1h"], ind_atual["fcr_1h"]),
        ("% dentro SLA", ind_anterior["percentual_dentro_sla"], ind_atual["percentual_dentro_sla"]),
        ("% FCR 1h", ind_anterior["percentual_fcr_1h"], ind_atual["percentual_fcr_1h"]),
    ]
    
    df_comp = pd.DataFrame(linhas, columns=["Indicador", "Mês anterior", "Mês atual"])
    df_comp["Diferença"] = df_comp["Mês atual"] - df_comp["Mês anterior"]
    
    # Diferença especial em p.p. para porcentagens
    for idx, row in df_comp.iterrows():
        ind = row["Indicador"]
        if ind.startswith("%"):
            df_comp.at[idx, "Diferença"] = row["Mês atual"] - row["Mês anterior"]
            # Variação % não faz sentido direto sobre porcentagens de taxas, mostramos NaN ou pp
            df_comp.at[idx, "Variação %"] = None
        else:
            df_comp.at[idx, "Variação %"] = calcular_variacao_percentual(row["Mês atual"], row["Mês anterior"])
            
    return df_comp

