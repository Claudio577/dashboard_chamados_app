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


def montar_solicitacao_especifica(df, col_tipo, col_item, col_qualificacao, col_categoria):
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

    return pd.Series(["Não informado"] * len(df), index=df.index)


def montar_categoria_principal(df, col_tipo, col_categoria, col_qualificacao):
    if col_tipo:
        return df[col_tipo].fillna("Não informado").astype(str).str.strip()

    if col_categoria:
        return df[col_categoria].fillna("Não informado").astype(str).str.strip()

    if col_qualificacao:
        return df[col_qualificacao].fillna("Não informado").astype(str).str.strip()

    return pd.Series(["Não informado"] * len(df), index=df.index)


def resumo_top(df, coluna, nome_coluna, filtro=None, top=50):
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


def processar_base(arquivo, nome_base):
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
        raise ValueError(
            f"Na base {nome_base}, não consegui identificar estas colunas: {faltando}. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    df = preparar_datas(df, col_abertura)
    df = preparar_datas(df, col_encerramento)
    df = preparar_datas(df, col_vencimento)

    df["Cliente Análise"] = df.apply(lambda row: montar_empresa_analise(row, col_empresa, col_de), axis=1)

    df["Categoria Principal"] = montar_categoria_principal(df, col_tipo, col_categoria, col_qualificacao)
    df["Categoria Principal"] = df["Categoria Principal"].fillna("Não informado").astype(str).str.strip()

    df["Solicitação Específica"] = montar_solicitacao_especifica(df, col_tipo, col_item, col_qualificacao, col_categoria)
    df["Solicitação Específica"] = df["Solicitação Específica"].fillna("Não informado").astype(str).str.strip()

    total_chamados = len(df)
    total_empresas = df["Cliente Análise"].nunique()

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

    resumo_clientes = resumo_top(df, "Cliente Análise", "Cliente", top=50)
    resumo_categorias = resumo_top(df, "Categoria Principal", "Categoria Principal", top=50)
    resumo_solicitacoes = resumo_top(df, "Solicitação Específica", "Solicitação Específica", top=50)

    resumo_sla = df.groupby("Status SLA").size().reset_index(name="Chamados")
    resumo_72h = df.groupby("Status 72h").size().reset_index(name="Chamados")

    resumo_causa_sla_vencido = resumo_top(
        df,
        "Solicitação Específica",
        "Causa de SLA vencido",
        filtro=(df["Status SLA"] == "Fora do SLA"),
        top=10,
    )

    resumo_causa_atraso = resumo_top(
        df,
        "Solicitação Específica",
        "Causa de atraso operacional",
        filtro=(df["Status 72h"] != "Tratado até 72h"),
        top=10,
    )

    cliente_top = resumo_clientes.iloc[0]["Cliente"] if not resumo_clientes.empty else "-"
    cliente_top_qtd = int(resumo_clientes.iloc[0]["Chamados"]) if not resumo_clientes.empty else 0

    categoria_top = resumo_categorias.iloc[0]["Categoria Principal"] if not resumo_categorias.empty else "-"
    categoria_top_qtd = int(resumo_categorias.iloc[0]["Chamados"]) if not resumo_categorias.empty else 0

    solicitacao_top = resumo_solicitacoes.iloc[0]["Solicitação Específica"] if not resumo_solicitacoes.empty else "-"
    solicitacao_top_qtd = int(resumo_solicitacoes.iloc[0]["Chamados"]) if not resumo_solicitacoes.empty else 0

    causa_sla_vencido = resumo_causa_sla_vencido.iloc[0]["Causa de SLA vencido"] if not resumo_causa_sla_vencido.empty else "-"
    causa_sla_vencido_qtd = int(resumo_causa_sla_vencido.iloc[0]["Chamados"]) if not resumo_causa_sla_vencido.empty else 0

    causa_atraso = resumo_causa_atraso.iloc[0]["Causa de atraso operacional"] if not resumo_causa_atraso.empty else "-"
    causa_atraso_qtd = int(resumo_causa_atraso.iloc[0]["Chamados"]) if not resumo_causa_atraso.empty else 0

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

    return {
        "nome_base": nome_base,
        "df": df,
        "indicadores": indicadores,
        "resumo_clientes": resumo_clientes,
        "resumo_categorias": resumo_categorias,
        "resumo_solicitacoes": resumo_solicitacoes,
        "resumo_sla": resumo_sla,
        "resumo_72h": resumo_72h,
        "resumo_causa_sla_vencido": resumo_causa_sla_vencido,
        "resumo_causa_atraso": resumo_causa_atraso,
        "chamados_abertos": chamados_abertos,
    }


def comparar_resumos(resumo_atual, resumo_anterior, coluna):
    atual = resumo_atual[[coluna, "Chamados"]].rename(columns={"Chamados": "Mês atual"})
    anterior = resumo_anterior[[coluna, "Chamados"]].rename(columns={"Chamados": "Mês anterior"})

    comparativo = atual.merge(anterior, on=coluna, how="outer")
    comparativo["Mês atual"] = comparativo["Mês atual"].fillna(0).astype(int)
    comparativo["Mês anterior"] = comparativo["Mês anterior"].fillna(0).astype(int)
    comparativo["Diferença"] = comparativo["Mês atual"] - comparativo["Mês anterior"]

    return comparativo.sort_values("Mês atual", ascending=False)


def montar_comparativo_indicadores(atual, anterior):
    ia = atual["indicadores"]
    ip = anterior["indicadores"]

    linhas = [
        ("Total de chamados", ia["total_chamados"], ip["total_chamados"]),
        ("Empresas com chamados", ia["total_empresas"], ip["total_empresas"]),
        ("SLA tratado", ia["sla_tratado"], ip["sla_tratado"]),
        ("Dentro do SLA", ia["dentro_sla"], ip["dentro_sla"]),
        ("Fora do SLA", ia["fora_sla"], ip["fora_sla"]),
        ("Em aberto / Em tratamento", ia["em_aberto"], ip["em_aberto"]),
        ("Tratados até 72h", ia["ate_72h"], ip["ate_72h"]),
        ("Tratados acima de 72h", ia["acima_72h"], ip["acima_72h"]),
        ("Acima de 72h / abertos", ia["nao_72h"], ip["nao_72h"]),
        ("% dentro SLA", ia["percentual_dentro_sla"], ip["percentual_dentro_sla"]),
    ]

    df_comp = pd.DataFrame(linhas, columns=["Indicador", "Mês atual", "Mês anterior"])
    df_comp["Diferença"] = df_comp["Mês atual"] - df_comp["Mês anterior"]

    return df_comp


def gerar_excel_resultado(atual, anterior=None):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        indicadores_atual = pd.DataFrame(
            list(atual["indicadores"].items()),
            columns=["Indicador", "Valor"]
        )

        indicadores_atual.to_excel(writer, sheet_name="Resumo_Atual", index=False)
        atual["resumo_clientes"].to_excel(writer, sheet_name="Clientes_Atual", index=False)
        atual["resumo_categorias"].to_excel(writer, sheet_name="Categorias_Atual", index=False)
        atual["resumo_solicitacoes"].to_excel(writer, sheet_name="Solicitacoes_Atual", index=False)
        atual["resumo_sla"].to_excel(writer, sheet_name="SLA_Atual", index=False)
        atual["resumo_72h"].to_excel(writer, sheet_name="72h_Atual", index=False)
        atual["resumo_causa_sla_vencido"].to_excel(writer, sheet_name="Causa_SLA_Atual", index=False)
        atual["resumo_causa_atraso"].to_excel(writer, sheet_name="Causa_Atraso_Atual", index=False)
        atual["chamados_abertos"].to_excel(writer, sheet_name="Abertos_Atual", index=False)

        if anterior is not None:
            indicadores_anterior = pd.DataFrame(
                list(anterior["indicadores"].items()),
                columns=["Indicador", "Valor"]
            )

            comp_indicadores = montar_comparativo_indicadores(atual, anterior)
            comp_clientes = comparar_resumos(atual["resumo_clientes"], anterior["resumo_clientes"], "Cliente")
            comp_categorias = comparar_resumos(atual["resumo_categorias"], anterior["resumo_categorias"], "Categoria Principal")
            comp_solicitacoes = comparar_resumos(atual["resumo_solicitacoes"], anterior["resumo_solicitacoes"], "Solicitação Específica")

            indicadores_anterior.to_excel(writer, sheet_name="Resumo_Anterior", index=False)
            comp_indicadores.to_excel(writer, sheet_name="Comparativo_Geral", index=False)
            comp_clientes.to_excel(writer, sheet_name="Comp_Clientes", index=False)
            comp_categorias.to_excel(writer, sheet_name="Comp_Categorias", index=False)
            comp_solicitacoes.to_excel(writer, sheet_name="Comp_Solicitacoes", index=False)

    output.seek(0)
    return output


def render_dashboard(resultado):
    indicadores = resultado["indicadores"]

    st.subheader("Dashboard atualizado")

    with st.expander("Entenda os indicadores"):
        st.markdown("""
        **Cliente com maior volume de chamados:** mostra qual empresa/cliente abriu mais chamados no mês.

        **Categoria principal com maior volume:** mostra o grupo principal que mais gerou chamados. Normalmente vem da coluna **Tipo**. Exemplo: *DeskPhone JRC Computador*.

        **Solicitação específica mais recorrente:** mostra o detalhe mais repetido, juntando **Tipo + Item**. Exemplo: *DeskPhone JRC Computador - Configuração*.

        **Principal causa de SLA vencido:** mostra a solicitação específica que mais ficou fora do prazo de SLA.

        **Principal causa de atraso operacional:** mostra a solicitação específica que mais passou de 72 horas ou ficou em aberto/em tratamento.

        **Em aberto / Em tratamento:** chamados que ainda não possuem data de encerramento na planilha.
        """)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de chamados", indicadores["total_chamados"])
    k2.metric("Empresas com chamados", indicadores["total_empresas"])
    k3.metric("SLA tratado", indicadores["sla_tratado"])
    k4.metric("% dentro SLA", f"{indicadores['percentual_dentro_sla']:.1f}%")

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Dentro do SLA", indicadores["dentro_sla"])
    k6.metric("Fora do SLA", indicadores["fora_sla"])
    k7.metric("Em aberto / Em tratamento", indicadores["em_aberto"])
    k8.metric("Tratados até 72h", indicadores["ate_72h"])

    k9, k10, k11, k12 = st.columns(4)
    k9.metric("Tratados acima de 72h", indicadores["acima_72h"])
    k10.metric("Acima de 72h / abertos", indicadores["nao_72h"])
    k11.metric("Causa de SLA vencido", indicadores["causa_sla_vencido_qtd"])
    k12.metric("Causa de atraso", indicadores["causa_atraso_qtd"])

    st.info(f"Cliente com maior volume de chamados: **{indicadores['cliente_top']}** — {indicadores['cliente_top_qtd']} chamados.")
    st.info(f"Categoria principal com maior volume: **{indicadores['categoria_top']}** — {indicadores['categoria_top_qtd']} chamados.")
    st.info(f"Solicitação específica mais recorrente: **{indicadores['solicitacao_top']}** — {indicadores['solicitacao_top_qtd']} chamados.")

    g1, g2 = st.columns(2)

    with g1:
        st.write("### Tratamento em 72 horas")
        fig_72h = px.pie(
            resultado["resumo_72h"],
            names="Status 72h",
            values="Chamados",
            hole=0.35,
            title="Tratados até 72h x acima de 72h x abertos",
        )
        st.plotly_chart(fig_72h, use_container_width=True)

    with g2:
        st.write("### SLA")
        fig_sla = px.bar(
            resultado["resumo_sla"],
            x="Status SLA",
            y="Chamados",
            text="Chamados",
            title="Resumo SLA",
        )
        st.plotly_chart(fig_sla, use_container_width=True)

    g3, g4 = st.columns(2)

    with g3:
        st.write("### Clientes por volume de chamados")
        fig_clientes = px.bar(
            resultado["resumo_clientes"].head(10),
            x="Chamados",
            y="Cliente",
            orientation="h",
            text="Chamados",
            title="Clientes com mais chamados",
        )
        fig_clientes.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_clientes, use_container_width=True)

    with g4:
        st.write("### Categorias principais por volume")
        fig_categoria = px.bar(
            resultado["resumo_categorias"].head(10),
            x="Chamados",
            y="Categoria Principal",
            orientation="h",
            text="Chamados",
            title="Categorias principais com mais chamados",
        )
        fig_categoria.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_categoria, use_container_width=True)

    g5, g6 = st.columns(2)

    with g5:
        st.write("### Solicitações específicas recorrentes")
        fig_solicitacoes = px.bar(
            resultado["resumo_solicitacoes"].head(10),
            x="Chamados",
            y="Solicitação Específica",
            orientation="h",
            text="Chamados",
            title="Solicitações específicas mais recorrentes",
        )
        fig_solicitacoes.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_solicitacoes, use_container_width=True)

    with g6:
        st.write("### Causas de SLA vencido")
        if resultado["resumo_causa_sla_vencido"].empty:
            st.info("Nenhum chamado fora do SLA.")
        else:
            fig_causa_sla = px.bar(
                resultado["resumo_causa_sla_vencido"],
                x="Chamados",
                y="Causa de SLA vencido",
                orientation="h",
                text="Chamados",
                title="Solicitações que mais ficaram fora do SLA",
            )
            fig_causa_sla.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_causa_sla, use_container_width=True)

    st.write("### Causas de atraso operacional")
    if resultado["resumo_causa_atraso"].empty:
        st.info("Nenhum chamado acima de 72h ou aberto.")
    else:
        fig_causa_atraso = px.bar(
            resultado["resumo_causa_atraso"],
            x="Chamados",
            y="Causa de atraso operacional",
            orientation="h",
            text="Chamados",
            title="Solicitações acima de 72h ou em aberto/em tratamento",
        )
        fig_causa_atraso.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_causa_atraso, use_container_width=True)

    st.subheader("Tabelas de conferência")

    t1, t2 = st.columns(2)

    with t1:
        st.write("Clientes")
        st.dataframe(resultado["resumo_clientes"], use_container_width=True)

    with t2:
        st.write("Categorias principais")
        st.dataframe(resultado["resumo_categorias"], use_container_width=True)

    st.write("Solicitações específicas")
    st.dataframe(resultado["resumo_solicitacoes"], use_container_width=True)

    with st.expander("Ver os chamados em aberto / Em tratamento"):
        st.dataframe(resultado["chamados_abertos"], use_container_width=True)

    st.subheader("Conferência dos totais")

    total_resumo_72h = int(resultado["resumo_72h"]["Chamados"].sum())
    total_resumo_sla = int(resultado["resumo_sla"]["Chamados"].sum())
    total_chamados = indicadores["total_chamados"]

    if total_resumo_72h == total_chamados:
        st.success(f"Resumo 72h está batendo: {total_resumo_72h} chamados.")
    else:
        st.error(f"Resumo 72h não está batendo. Base: {total_chamados} | Resumo: {total_resumo_72h}")

    if total_resumo_sla == total_chamados:
        st.success(f"Resumo SLA está batendo: {total_resumo_sla} chamados.")
    else:
        st.error(f"Resumo SLA não está batendo. Base: {total_chamados} | Resumo: {total_resumo_sla}")


def render_comparativo(atual, anterior):
    st.subheader("Comparação entre mês atual e mês anterior")

    ia = atual["indicadores"]
    ip = anterior["indicadores"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Chamados no mês atual", ia["total_chamados"], delta=ia["total_chamados"] - ip["total_chamados"])
    c2.metric("Dentro SLA atual", ia["dentro_sla"], delta=ia["dentro_sla"] - ip["dentro_sla"])
    c3.metric("Fora SLA atual", ia["fora_sla"], delta=ia["fora_sla"] - ip["fora_sla"])
    c4.metric("% SLA atual", f"{ia['percentual_dentro_sla']:.1f}%", delta=f"{ia['percentual_dentro_sla'] - ip['percentual_dentro_sla']:.1f} p.p.")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Até 72h atual", ia["ate_72h"], delta=ia["ate_72h"] - ip["ate_72h"])
    c6.metric("Acima 72h atual", ia["acima_72h"], delta=ia["acima_72h"] - ip["acima_72h"])
    c7.metric("Em aberto atual", ia["em_aberto"], delta=ia["em_aberto"] - ip["em_aberto"])
    c8.metric("Empresas atual", ia["total_empresas"], delta=ia["total_empresas"] - ip["total_empresas"])

    comp_indicadores = montar_comparativo_indicadores(atual, anterior)

    st.write("### Comparativo geral")
    st.dataframe(comp_indicadores, use_container_width=True)

    comp_grafico = comp_indicadores[
        comp_indicadores["Indicador"].isin([
            "Total de chamados",
            "Dentro do SLA",
            "Fora do SLA",
            "Em aberto / Em tratamento",
            "Tratados até 72h",
            "Tratados acima de 72h",
        ])
    ]

    comp_grafico_melt = comp_grafico.melt(
        id_vars="Indicador",
        value_vars=["Mês atual", "Mês anterior"],
        var_name="Mês",
        value_name="Chamados",
    )

    fig_comp = px.bar(
        comp_grafico_melt,
        x="Indicador",
        y="Chamados",
        color="Mês",
        barmode="group",
        text="Chamados",
        title="Comparação geral entre os meses",
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    comp_clientes = comparar_resumos(atual["resumo_clientes"], anterior["resumo_clientes"], "Cliente")
    comp_categorias = comparar_resumos(atual["resumo_categorias"], anterior["resumo_categorias"], "Categoria Principal")
    comp_solicitacoes = comparar_resumos(atual["resumo_solicitacoes"], anterior["resumo_solicitacoes"], "Solicitação Específica")

    maior_crescimento_categoria = comp_categorias.sort_values("Diferença", ascending=False).head(1)
    maior_reducao_categoria = comp_categorias.sort_values("Diferença", ascending=True).head(1)

    if not maior_crescimento_categoria.empty:
        linha = maior_crescimento_categoria.iloc[0]
        if linha["Diferença"] > 0:
            st.info(
                f"Categoria que mais cresceu: **{linha['Categoria Principal']}** "
                f"subiu de {linha['Mês anterior']} para {linha['Mês atual']} chamados "
                f"(**+{linha['Diferença']}**)."
            )

    if not maior_reducao_categoria.empty:
        linha = maior_reducao_categoria.iloc[0]
        if linha["Diferença"] < 0:
            st.success(
                f"Categoria que mais reduziu: **{linha['Categoria Principal']}** "
                f"caiu de {linha['Mês anterior']} para {linha['Mês atual']} chamados "
                f"(**{linha['Diferença']}**)."
            )

    st.write("### Comparação por categoria principal")

    top_categorias = comp_categorias.sort_values("Mês atual", ascending=False).head(10)
    top_categorias_melt = top_categorias.melt(
        id_vars="Categoria Principal",
        value_vars=["Mês atual", "Mês anterior"],
        var_name="Mês",
        value_name="Chamados",
    )

    fig_cat = px.bar(
        top_categorias_melt,
        x="Chamados",
        y="Categoria Principal",
        color="Mês",
        orientation="h",
        barmode="group",
        text="Chamados",
        title="Categorias principais: mês atual x mês anterior",
    )
    fig_cat.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_cat, use_container_width=True)

    st.write("### Comparação por cliente")

    top_clientes = comp_clientes.sort_values("Mês atual", ascending=False).head(10)
    top_clientes_melt = top_clientes.melt(
        id_vars="Cliente",
        value_vars=["Mês atual", "Mês anterior"],
        var_name="Mês",
        value_name="Chamados",
    )

    fig_cli = px.bar(
        top_clientes_melt,
        x="Chamados",
        y="Cliente",
        color="Mês",
        orientation="h",
        barmode="group",
        text="Chamados",
        title="Clientes: mês atual x mês anterior",
    )
    fig_cli.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_cli, use_container_width=True)

    st.write("### Tabelas comparativas")

    t1, t2 = st.columns(2)

    with t1:
        st.write("Categorias principais")
        st.dataframe(comp_categorias, use_container_width=True)

    with t2:
        st.write("Clientes")
        st.dataframe(comp_clientes, use_container_width=True)

    st.write("Solicitações específicas")
    st.dataframe(comp_solicitacoes, use_container_width=True)


# =========================
# APP
# =========================

st.title("📊 Dashboard de Chamados")
st.write("Envie a planilha do mês atual para gerar o dashboard. Na aba de comparação, envie também a planilha do mês anterior.")

arquivo_atual = st.file_uploader(
    "Faça upload da planilha do mês atual",
    type=["xls", "xlsx", "xlsm", "csv"],
    key="arquivo_atual",
)

if arquivo_atual is None:
    st.warning("Envie a planilha do mês atual para começar.")
    st.stop()

try:
    resultado_atual = processar_base(arquivo_atual, "Mês atual")
    st.success("Planilha do mês atual carregada com sucesso!")

    aba_dashboard, aba_comparativo = st.tabs([
        "Dashboard mês atual",
        "Comparação com mês anterior",
    ])

    with aba_dashboard:
        render_dashboard(resultado_atual)

        excel_atual = gerar_excel_resultado(resultado_atual)

        st.download_button(
            label="📥 Baixar dashboard do mês atual em Excel",
            data=excel_atual,
            file_name="dashboard_chamados_mes_atual.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_atual",
        )

    with aba_comparativo:
        st.write("Envie a planilha do mês anterior para comparar com o mês atual.")

        arquivo_anterior = st.file_uploader(
            "Faça upload da planilha do mês anterior",
            type=["xls", "xlsx", "xlsm", "csv"],
            key="arquivo_anterior",
        )

        if arquivo_anterior is None:
            st.info("Quando você enviar a planilha do mês anterior, a comparação aparecerá aqui.")
        else:
            resultado_anterior = processar_base(arquivo_anterior, "Mês anterior")
            st.success("Planilha do mês anterior carregada com sucesso!")

            render_comparativo(resultado_atual, resultado_anterior)

            excel_comparativo = gerar_excel_resultado(resultado_atual, resultado_anterior)

            st.download_button(
                label="📥 Baixar Excel com dashboard e comparativo",
                data=excel_comparativo,
                file_name="dashboard_chamados_comparativo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_comparativo",
            )

except Exception as e:
    st.error("Erro ao processar a planilha.")
    st.exception(e)
