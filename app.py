import io
import re
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard de Chamados",
    page_icon="📊",
    layout="wide",
)


# =========================
# FUNÇÕES AUXILIARES
# =========================

def normalizar_texto(texto):
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

    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        for col, col_norm in colunas_norm.items():
            if opcao_norm == col_norm:
                return col

    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        for col, col_norm in colunas_norm.items():
            if opcao_norm in col_norm:
                return col

    return None


def ler_arquivo(uploaded_file):
    nome = uploaded_file.name.lower()

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
    df[coluna] = pd.to_datetime(df[coluna], errors="coerce", dayfirst=True)
    return df


def montar_empresa_analise(row, col_empresa, col_de):
    empresa = limpar_texto(row[col_empresa])
    de = limpar_texto(row[col_de]) if col_de else ""

    empresa_norm = normalizar_texto(empresa)
    de_norm = normalizar_texto(de)

    if "cbloc" in de_norm:
        return "CBLOC BRASIL LOCAÇÃO DE EQUIPAMENTOS LTDA"

    if "cbloc" in empresa_norm and "casa do construtor" in de_norm:
        return "CASA DO CONSTRUTOR"

    return empresa


def montar_qualificacao(df, col_tipo, col_item, col_qualificacao, col_categoria):
    if col_tipo and col_item:
        return (
            df[col_tipo].fillna("Não informado").astype(str).str.strip()
            + " - "
            + df[col_item].fillna("Não informado").astype(str).str.strip()
        )

    if col_qualificacao:
        return df[col_qualificacao].fillna("Não informado").astype(str).str.strip()

    if col_categoria:
        return df[col_categoria].fillna("Não informado").astype(str).str.strip()

    return pd.Series(["Não informado"] * len(df))


def montar_dor_geral(df, col_tipo, col_categoria, col_qualificacao):
    """
    Maior dor geral = grupo principal da solicitação.

    Preferência:
    1. Tipo
    2. Categoria
    3. Qualificação
    """
    if col_tipo:
        return df[col_tipo].fillna("Não informado").astype(str).str.strip()

    if col_categoria:
        return df[col_categoria].fillna("Não informado").astype(str).str.strip()

    if col_qualificacao:
        return df[col_qualificacao].fillna("Não informado").astype(str).str.strip()

    return pd.Series(["Não informado"] * len(df))


def resumo_top(df, coluna, nome_coluna, filtro=None, top=10):
    base = df.copy()

    if filtro is not None:
        base = base[filtro]

    if base.empty:
        return pd.DataFrame(columns=[nome_coluna, "Chamados"])

    return (
        base.groupby(coluna)
        .size()
        .reset_index(name="Chamados")
        .rename(columns={coluna: nome_coluna})
        .sort_values("Chamados", ascending=False)
        .head(top)
    )


def gerar_excel_dashboard(
    indicadores,
    resumo_empresas,
    resumo_dor_geral,
    resumo_qualificacoes,
    resumo_sla,
    resumo_72h,
    resumo_ofensor_sla,
    resumo_ofensor_72h,
    chamados_abertos,
):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = worksheet

        fmt_titulo = workbook.add_format({
            "bold": True,
            "font_size": 20,
            "align": "center",
            "valign": "vcenter",
            "font_color": "white",
            "bg_color": "#1F4E78",
        })

        fmt_card = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "bg_color": "#D9EAF7",
        })

        fmt_card_valor = workbook.add_format({
            "bold": True,
            "font_size": 18,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "bg_color": "#F2F2F2",
        })

        fmt_secao = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "font_color": "white",
            "bg_color": "#4472C4",
            "border": 1,
        })

        fmt_header = workbook.add_format({
            "bold": True,
            "bg_color": "#B4C6E7",
            "border": 1,
            "align": "center",
        })

        fmt_cell = workbook.add_format({"border": 1})

        worksheet.set_column("A:A", 3)
        worksheet.set_column("B:B", 38)
        worksheet.set_column("C:C", 14)
        worksheet.set_column("D:D", 20)
        worksheet.set_column("E:E", 20)
        worksheet.set_column("F:F", 38)
        worksheet.set_column("G:G", 14)
        worksheet.set_column("H:H", 20)
        worksheet.set_column("I:I", 20)
        worksheet.set_column("J:J", 20)

        worksheet.merge_range("B2:J3", "DASHBOARD DE CHAMADOS", fmt_titulo)

        cards = [
            ("Total de chamados", indicadores["total_chamados"]),
            ("Empresas com chamados", indicadores["total_empresas"]),
            ("SLA tratado", indicadores["sla_tratado"]),
            ("Dentro do SLA", indicadores["dentro_sla"]),
            ("Fora do SLA", indicadores["fora_sla"]),
            ("Em aberto / Em tratamento", indicadores["em_aberto"]),
            ("Tratados até 72h", indicadores["ate_72h"]),
            ("Acima 72h / abertos", indicadores["nao_72h"]),
        ]

        posicoes = [
            ("B5", "C5", "B6", "C6"),
            ("D5", "E5", "D6", "E6"),
            ("F5", "G5", "F6", "G6"),
            ("H5", "I5", "H6", "I6"),
            ("B8", "C8", "B9", "C9"),
            ("D8", "E8", "D9", "E9"),
            ("F8", "G8", "F9", "G9"),
            ("H8", "I8", "H9", "I9"),
        ]

        for (titulo, valor), pos in zip(cards, posicoes):
            worksheet.merge_range(f"{pos[0]}:{pos[1]}", titulo, fmt_card)
            worksheet.merge_range(f"{pos[2]}}:{pos[3]}", valor, fmt_card_valor)

        worksheet.merge_range("B11:E11", "Empresa com mais chamados", fmt_secao)
        worksheet.merge_range("B12:E12", indicadores["empresa_top"], fmt_cell)
        worksheet.write("F11", "Qtd.", fmt_secao)
        worksheet.write("F12", indicadores["empresa_top_qtd"], fmt_cell)

        worksheet.merge_range("B14:E14", "Maior dor geral", fmt_secao)
        worksheet.merge_range("B15:E15", indicadores["dor_geral_top"], fmt_cell)
        worksheet.write("F14", "Qtd.", fmt_secao)
        worksheet.write("F15", indicadores["dor_geral_top_qtd"], fmt_cell)

        worksheet.merge_range("G11:J11", "Qualificação mais solicitada", fmt_secao)
        worksheet.merge_range("G12:I12", indicadores["qualificacao_top"], fmt_cell)
        worksheet.write("J12", indicadores["qualificacao_top_qtd"], fmt_cell)

        worksheet.merge_range("G14:J14", "Maior ofensor fora do SLA", fmt_secao)
        worksheet.merge_range("G15:I15", indicadores["ofensor_sla"], fmt_cell)
        worksheet.write("J15", indicadores["ofensor_sla_qtd"], fmt_cell)

        worksheet.merge_range("B17:E17", "Maior ofensor acima de 72h / aberto", fmt_secao)
        worksheet.merge_range("B18:D18", indicadores["ofensor_72h"], fmt_cell)
        worksheet.write("E18", indicadores["ofensor_72h_qtd"], fmt_cell)

        linha = 21
        worksheet.merge_range(linha, 1, linha, 3, "Top empresas por chamados", fmt_secao)
        linha += 1
        worksheet.write(linha, 1, "Empresa", fmt_header)
        worksheet.write(linha, 2, "Chamados", fmt_header)

        for _, row in resumo_empresas.head(10).iterrows():
            linha += 1
            worksheet.write(linha, 1, str(row["Empresa"]), fmt_cell)
            worksheet.write(linha, 2, int(row["Chamados"]), fmt_cell)

        linha = 21
        worksheet.merge_range(linha, 5, linha, 8, "Top maiores dores gerais", fmt_secao)
        linha += 1
        worksheet.write(linha, 5, "Dor geral", fmt_header)
        worksheet.write(linha, 6, "Chamados", fmt_header)

        for _, row in resumo_dor_geral.head(10).iterrows():
            linha += 1
            worksheet.write(linha, 5, str(row["Dor Geral"]), fmt_cell)
            worksheet.write(linha, 6, int(row["Chamados"]), fmt_cell)

        linha_sla = 35
        worksheet.merge_range(linha_sla, 1, linha_sla, 3, "Resumo SLA", fmt_secao)
        linha_sla += 1
        worksheet.write(linha_sla, 1, "Status SLA", fmt_header)
        worksheet.write(linha_sla, 2, "Chamados", fmt_header)

        for _, row in resumo_sla.iterrows():
            linha_sla += 1
            worksheet.write(linha_sla, 1, str(row["Status SLA"]), fmt_cell)
            worksheet.write(linha_sla, 2, int(row["Chamados"]), fmt_cell)

        linha_72 = 35
        worksheet.merge_range(linha_72, 5, linha_72, 8, "Resumo tratamento em 72 horas", fmt_secao)
        linha_72 += 1
        worksheet.write(linha_72, 5, "Status 72h", fmt_header)
        worksheet.write(linha_72, 6, "Chamados", fmt_header)

        for _, row in resumo_72h.iterrows():
            linha_72 += 1
            worksheet.write(linha_72, 5, str(row["Status 72h"]), fmt_cell)
            worksheet.write(linha_72, 6, int(row["Chamados"]), fmt_cell)

        resumo_empresas.to_excel(writer, sheet_name="Empresas", index=False)
        resumo_dor_geral.to_excel(writer, sheet_name="Dor_Geral", index=False)
        resumo_qualificacoes.to_excel(writer, sheet_name="Qualificações", index=False)
        resumo_sla.to_excel(writer, sheet_name="SLA", index=False)
        resumo_72h.to_excel(writer, sheet_name="72h", index=False)
        resumo_ofensor_sla.to_excel(writer, sheet_name="Ofensor_SLA", index=False)
        resumo_ofensor_72h.to_excel(writer, sheet_name="Ofensor_72h", index=False)
        chamados_abertos.to_excel(writer, sheet_name="Abertos_Em_tratamento", index=False)

    output.seek(0)
    return output


# =========================
# INTERFACE
# =========================

st.title("📊 Dashboard de Chamados")
st.write("Envie a planilha do mês para gerar o dashboard atualizado automaticamente.")

arquivo = st.file_uploader("Faça upload da planilha", type=["xls", "xlsx", "xlsm", "csv"])

if arquivo is None:
    st.warning("Envie uma planilha para começar.")
    st.stop()

try:
    df = ler_arquivo(arquivo)

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
    col_responsavel = encontrar_coluna(df, ["Responsável", "Responsavel", "Atendente", "Analista"])
    col_numero = encontrar_coluna(df, ["N", "Número", "Numero", "Chamado", "Ticket"])

    colunas_obrigatorias = {
        "Empresa": col_empresa,
        "Abertura": col_abertura,
        "Encerramento": col_encerramento,
        "Vencimento": col_vencimento,
    }

    faltando = [nome for nome, coluna in colunas_obrigatorias.items() if coluna is None]

    if faltando:
        st.error("Não consegui identificar automaticamente algumas colunas obrigatórias.")
        st.write("Colunas faltando:", faltando)
        st.write("Colunas encontradas na planilha:", list(df.columns))
        st.stop()

    st.success("Arquivo carregado com sucesso!")

    df = preparar_datas(df, col_abertura)
    df = preparar_datas(df, col_encerramento)
    df = preparar_datas(df, col_vencimento)

    df["Empresa Análise"] = df.apply(lambda row: montar_empresa_analise(row, col_empresa, col_de), axis=1)

    df["Dor Geral"] = montar_dor_geral(df, col_tipo, col_categoria, col_qualificacao)
    df["Dor Geral"] = df["Dor Geral"].fillna("Não informado").astype(str).str.strip()

    df["Qualificação Análise"] = montar_qualificacao(df, col_tipo, col_item, col_qualificacao, col_categoria)
    df["Qualificação Análise"] = df["Qualificação Análise"].fillna("Não informado").astype(str).str.strip()

    total_chamados = len(df)
    total_empresas = df["Empresa Análise"].nunique()

    # SLA
    df["Status SLA"] = "Em aberto / Em tratamento"
    mask_fechado_com_prazo = df[col_encerramento].notna() & df[col_vencimento].notna()

    df.loc[
        mask_fechado_com_prazo & (df[col_encerramento] <= df[col_vencimento]),
        "Status SLA",
    ] = "Dentro do SLA"

    df.loc[
        mask_fechado_com_prazo & (df[col_encerramento] > df[col_vencimento]),
        "Status SLA",
    ] = "Fora do SLA"

    sla_tratado = int(mask_fechado_com_prazo.sum())
    dentro_sla = int((df["Status SLA"] == "Dentro do SLA").sum())
    fora_sla = int((df["Status SLA"] == "Fora do SLA").sum())
    em_aberto = int((df["Status SLA"] == "Em aberto / Em tratamento").sum())
    percentual_dentro_sla = (dentro_sla / sla_tratado * 100) if sla_tratado > 0 else 0

    # 72 horas
    df["Horas para tratamento"] = None
    mask_fechado_com_abertura = df[col_abertura].notna() & df[col_encerramento].notna()

    df.loc[mask_fechado_com_abertura, "Horas para tratamento"] = (
        (
            df.loc[mask_fechado_com_abertura, col_encerramento]
            - df.loc[mask_fechado_com_abertura, col_abertura]
        ).dt.total_seconds() / 3600
    )

    df["Status 72h"] = "Em aberto / Em tratamento"

    df.loc[
        mask_fechado_com_abertura & (df["Horas para tratamento"] <= 72),
        "Status 72h",
    ] = "Tratado até 72h"

    df.loc[
        mask_fechado_com_abertura & (df["Horas para tratamento"] > 72),
        "Status 72h",
    ] = "Tratado acima de 72h"

    ate_72h = int((df["Status 72h"] == "Tratado até 72h").sum())
    acima_72h = int((df["Status 72h"] == "Tratado acima de 72h").sum())
    nao_72h = int((df["Status 72h"] != "Tratado até 72h").sum())

    # Resumos
    resumo_empresas = resumo_top(df, "Empresa Análise", "Empresa", top=50)
    resumo_dor_geral = resumo_top(df, "Dor Geral", "Dor Geral", top=50)
    resumo_qualificacoes = resumo_top(df, "Qualificação Análise", "Qualificação", top=50)

    resumo_sla = df.groupby("Status SLA").size().reset_index(name="Chamados")
    resumo_72h = df.groupby("Status 72h").size().reset_index(name="Chamados")

    resumo_ofensor_sla = resumo_top(
        df,
        "Qualificação Análise",
        "Ofensor fora do SLA",
        filtro=(df["Status SLA"] == "Fora do SLA"),
        top=10,
    )

    resumo_ofensor_72h = resumo_top(
        df,
        "Qualificação Análise",
        "Ofensor acima de 72h / aberto",
        filtro=(df["Status 72h"] != "Tratado até 72h"),
        top=10,
    )

    empresa_top = resumo_empresas.iloc[0]["Empresa"] if not resumo_empresas.empty else "-"
    empresa_top_qtd = int(resumo_empresas.iloc[0]["Chamados"]) if not resumo_empresas.empty else 0

    dor_geral_top = resumo_dor_geral.iloc[0]["Dor Geral"] if not resumo_dor_geral.empty else "-"
    dor_geral_top_qtd = int(resumo_dor_geral.iloc[0]["Chamados"]) if not resumo_dor_geral.empty else 0

    qualificacao_top = resumo_qualificacoes.iloc[0]["Qualificação"] if not resumo_qualificacoes.empty else "-"
    qualificacao_top_qtd = int(resumo_qualificacoes.iloc[0]["Chamados"]) if not resumo_qualificacoes.empty else 0

    ofensor_sla = resumo_ofensor_sla.iloc[0]["Ofensor fora do SLA"] if not resumo_ofensor_sla.empty else "-"
    ofensor_sla_qtd = int(resumo_ofensor_sla.iloc[0]["Chamados"]) if not resumo_ofensor_sla.empty else 0

    ofensor_72h = resumo_ofensor_72h.iloc[0]["Ofensor acima de 72h / aberto"] if not resumo_ofensor_72h.empty else "-"
    ofensor_72h_qtd = int(resumo_ofensor_72h.iloc[0]["Chamados"]) if not resumo_ofensor_72h.empty else 0

    indicadores = {
        "total_chamados": total_chamados,
        "total_empresas": total_empresas,
        "sla_tratado": sla_tratado,
        "dentro_sla": dentro_sla,
        "fora_sla": fora_sla,
        "em_aberto": em_aberto,
        "percentual_dentro_sla": percentual_dentro_sla,
        "ate_72h": ate_72h,
        "acima_72h": acima_72h,
        "nao_72h": nao_72h,
        "empresa_top": empresa_top,
        "empresa_top_qtd": empresa_top_qtd,
        "dor_geral_top": dor_geral_top,
        "dor_geral_top_qtd": dor_geral_top_qtd,
        "qualificacao_top": qualificacao_top,
        "qualificacao_top_qtd": qualificacao_top_qtd,
        "ofensor_sla": ofensor_sla,
        "ofensor_sla_qtd": ofensor_sla_qtd,
        "ofensor_72h": ofensor_72h,
        "ofensor_72h_qtd": ofensor_72h_qtd,
    }

    # Tabela dos chamados em aberto / em tratamento
    colunas_abertos = []

    for c in [
        col_numero,
        col_abertura,
        col_empresa,
        col_de,
        col_responsavel,
        col_tipo,
        col_item,
        col_vencimento,
        col_encerramento,
        col_status,
        col_categoria,
    ]:
        if c and c not in colunas_abertos:
            colunas_abertos.append(c)

    chamados_abertos = df.loc[df["Status SLA"] == "Em aberto / Em tratamento", colunas_abertos].copy()

    # =========================
    # DASHBOARD
    # =========================

    st.subheader("Dashboard atualizado")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de chamados", total_chamados)
    k2.metric("Empresas com chamados", total_empresas)
    k3.metric("SLA tratado", sla_tratado)
    k4.metric("% dentro SLA", f"{percentual_dentro_sla:.1f}%")

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Dentro do SLA", dentro_sla)
    k6.metric("Fora do SLA", fora_sla)
    k7.metric("Em aberto / Em tratamento", em_aberto)
    k8.metric("Tratados até 72h", ate_72h)

    k9, k10, k11, k12 = st.columns(4)
    k9.metric("Tratados acima de 72h", acima_72h)
    k10.metric("Acima de 72h / abertos", nao_72h)
    k11.metric("Ofensor fora do SLA", ofensor_sla_qtd)
    k12.metric("Ofensor 72h / aberto", ofensor_72h_qtd)

    st.info(f"Empresa com mais chamados: **{empresa_top}** — {empresa_top_qtd} chamados.")
    st.info(f"Maior dor geral: **{dor_geral_top}** — {dor_geral_top_qtd} chamados.")
    st.info(f"Qualificação mais solicitada: **{qualificacao_top}** — {qualificacao_top_qtd} chamados.")

    g1, g2 = st.columns(2)

    with g1:
        st.write("### Tratamento em 72 horas")
        fig_72h = px.pie(
            resumo_72h,
            names="Status 72h",
            values="Chamados",
            hole=0.35,
            title="Tratados até 72h x acima de 72h x abertos",
        )
        st.plotly_chart(fig_72h, use_container_width=True)

    with g2:
        st.write("### SLA")
        fig_sla = px.bar(
            resumo_sla,
            x="Status SLA",
            y="Chamados",
            text="Chamados",
            title="Resumo SLA",
        )
        st.plotly_chart(fig_sla, use_container_width=True)

    g3, g4 = st.columns(2)

    with g3:
        st.write("### Top empresas por chamados")
        fig_empresas = px.bar(
            resumo_empresas.head(10),
            x="Chamados",
            y="Empresa",
            orientation="h",
            text="Chamados",
            title="Top empresas",
        )
        fig_empresas.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_empresas, use_container_width=True)

    with g4:
        st.write("### Maiores dores gerais")
        fig_dor = px.bar(
            resumo_dor_geral.head(10),
            x="Chamados",
            y="Dor Geral",
            orientation="h",
            text="Chamados",
            title="Maiores dores gerais",
        )
        fig_dor.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_dor, use_container_width=True)

    g5, g6 = st.columns(2)

    with g5:
        st.write("### Top qualificações")
        fig_qual = px.bar(
            resumo_qualificacoes.head(10),
            x="Chamados",
            y="Qualificação",
            orientation="h",
            text="Chamados",
            title="Top qualificações solicitadas",
        )
        fig_qual.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_qual, use_container_width=True)

    with g6:
        st.write("### Ofensores fora do SLA")
        if resumo_ofensor_sla.empty:
            st.info("Nenhum chamado fora do SLA.")
        else:
            fig_ofensor_sla = px.bar(
                resumo_ofensor_sla,
                x="Chamados",
                y="Ofensor fora do SLA",
                orientation="h",
                text="Chamados",
                title="Qualificações que mais ficaram fora do SLA",
            )
            fig_ofensor_sla.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_ofensor_sla, use_container_width=True)

    st.write("### Ofensores acima de 72h / abertos")
    if resumo_ofensor_72h.empty:
        st.info("Nenhum chamado acima de 72h ou aberto.")
    else:
        fig_ofensor_72h = px.bar(
            resumo_ofensor_72h,
            x="Chamados",
            y="Ofensor acima de 72h / aberto",
            orientation="h",
            text="Chamados",
            title="Qualificações acima de 72h ou abertas",
        )
        fig_ofensor_72h.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_ofensor_72h, use_container_width=True)

    st.subheader("Tabelas de conferência")

    t1, t2 = st.columns(2)

    with t1:
        st.write("Empresas")
        st.dataframe(resumo_empresas, use_container_width=True)

    with t2:
        st.write("Maiores dores gerais")
        st.dataframe(resumo_dor_geral, use_container_width=True)

    st.write("Qualificações")
    st.dataframe(resumo_qualificacoes, use_container_width=True)

    with st.expander("Ver os chamados em aberto / Em tratamento"):
        st.dataframe(chamados_abertos, use_container_width=True)

    st.subheader("Conferência dos totais")

    total_resumo_72h = int(resumo_72h["Chamados"].sum())
    total_resumo_sla = int(resumo_sla["Chamados"].sum())

    if total_resumo_72h == total_chamados:
        st.success(f"Resumo 72h está batendo: {total_resumo_72h} chamados.")
    else:
        st.error(f"Resumo 72h não está batendo. Base: {total_chamados} | Resumo: {total_resumo_72h}")

    if total_resumo_sla == total_chamados:
        st.success(f"Resumo SLA está batendo: {total_resumo_sla} chamados.")
    else:
        st.error(f"Resumo SLA não está batendo. Base: {total_chamados} | Resumo: {total_resumo_sla}")

    excel_dashboard = gerar_excel_dashboard(
        indicadores,
        resumo_empresas,
        resumo_dor_geral,
        resumo_qualificacoes,
        resumo_sla,
        resumo_72h,
        resumo_ofensor_sla,
        resumo_ofensor_72h,
        chamados_abertos,
    )

    st.download_button(
        label="📥 Baixar dashboard em Excel",
        data=excel_dashboard,
        file_name="dashboard_chamados_atualizado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

except Exception as e:
    st.error("Erro ao processar a planilha.")
    st.exception(e)
